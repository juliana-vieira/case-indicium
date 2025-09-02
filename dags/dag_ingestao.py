import datetime
import pendulum
import os
import logging

from airflow.decorators import dag, task
from airflow.providers.postgres.hooks.postgres import PostgresHook

@dag(
    dag_id="dag_ingestao",
    schedule=None,
    start_date=pendulum.datetime(2025, 8, 27, tz="America/Sao_Paulo"),
    catchup=False,
    dagrun_timeout=datetime.timedelta(minutes=60),
)

def inserir_dados_dw():

    @task
    def obter_caminho_arquivos()-> list:
        
        # Task para obter o caminho dos arquivos no Data Lake

        try:
            # Definição do caminho padrão
            caminho_lake = "/opt/airflow/datalake"

            # Lista que armazena o caminho completo dos diretórios em que os dados estão salvos
            # o os.walk() lê os diretórios recursivamente
            # o join() junta o diretório root com o nome do arquivo, montando um path completo
            # "arquivos" é uma lista, pois existem vários arquivos nos diretórios, por isso a necessidade de iterar em "arquivos" também
            caminho_arquivos = [os.path.join(root, arquivo) 
                        for root, dirs, arquivos in os.walk(caminho_lake) 
                        for arquivo in arquivos]

            logging.info("Caminhos do Data Lake salvos com sucesso.")

            # A lista é retornada para que a próxima task possa ler os arquivos.
            return caminho_arquivos
        
        except Exception as e:
            logging.error("Erro ao extrair o caminho dos arquivos do Data Lake:", e)

    @task
    def preparar_dados(caminho_arquivos: list)-> tuple:

        import pandas as pd
        
        try:   
            # Definindo um dicionário de listas de DataFrames para cada arquivo do Data Lake
            # Existem vários arquivos com o mesmo nome, porém em diretórios de diferentes datas
            # Nenhum DataFrame é perdido, todos serão armazenados nas listas

            dfs = {
                    'transacoes': [],
                    'contas': [],
                    'agencias': [],
                    'clientes': [],
                    'colaboradores': [],
                    'propostas_credito' : [],
                    'colaborador_agencia': []
                }

            # Para cada caminho na lista de caminhos, o nome do arquivo é extraído
            for path in caminho_arquivos:
                tabela = os.path.basename(path).replace('.csv', '')
                
                # Pandas faz a leitura de cada arquivo e guarda em um DataFrame "df"
                df = pd.read_csv(path)

                # A data do diretório é extraída do path e armazenada em uma coluna do DataFrame
                # Isso permite consultar o quão recente é o dado
                df['ultima_atualizacao'] = path.split("/")[4]

                # Armazena o dataframe "df" na lista do dicionário de DataFrames "dfs" utilizando o nome do arquivo como chave
                dfs[tabela].append(df)

            # Existem vários arquivos com o mesmo nome e, consequentemente, dados duplicados, é necessário remover duplicatas e
            # manter os registros mais atualizados para inserir no Data Warehouse

            # As chaves primárias de cada tabela são armazenadas em um dicionário, tendo como chave o nome do arquivo
            chaves_primarias = {
                    "transacoes": "cod_transacao",
                    "contas": "num_conta",
                    "agencias": "cod_agencia",
                    "clientes": "cod_cliente",
                    "colaboradores": "cod_colaborador",
                    "propostas_credito": "cod_proposta",
                    "colaborador_agencia": "cod_colaborador" 
                }

            # Um dicionário de DataFrames atualizados é iniciado
            # Esse dicionário é semelhante a "dfs", porém irá armazenar somente um DataFrame com dados mais atualizados
            dfs_atualizados = {}

            # Iterando no dicionário de chaves primárias, é possível usar o nome do arquivo para acessar os DataFrames de "dfs"
            # e a chave primária para concatenar cada DataFrame
            for nome_arquivo, chave_primaria in chaves_primarias.items():
                
                # Concatenação dos DataFrames que possuem o mesmo "nome_arquivo"
                df_concat = pd.concat(dfs[nome_arquivo], ignore_index=True)

                # Conversão da coluna de "ultima_atualizacao" em tipo "datetime"
                df_concat["ultima_atualizacao"] = pd.to_datetime(df_concat["ultima_atualizacao"])
                
                # Criação de um novo DataFrame atualizado que ordena as linhas pela coluna "ultima_atualizacao" de maneira decrescente
                # Remove duplicatas usando a coluna de chave primária e mantém os primeiros registros (por conta da ordenação decrescente)
                # Reseta e dropa os índices desordenados
                df_atualizado = (
                    df_concat
                        .sort_values(by=["ultima_atualizacao"], ascending=False)
                        .drop_duplicates(subset=[chave_primaria], keep="first")
                        .reset_index(drop=True)
                    )

                # Após as transformações, armazena o DataFrame atualizado no dicionário de DataFrames atualizados com o nome do arquivo como chave
                dfs_atualizados[nome_arquivo] = df_atualizado

            logging.info("DataFrames unificados e atualizados com sucesso.")
            
        except Exception as e:
            logging.error("Ocorreu um erro na preparação dos DataFrames: ", e)

        try:
            # Devido a estrutura do Data Warehouse, é necessário filtrar alguns DataFrames para que tenham as mesmas colunas do DataWarehouse
            dim_contas = dfs_atualizados['contas'][['num_conta',
                                            'tipo_conta',
                                            'data_abertura',
                                            'cod_cliente',
                                            'cod_agencia',
                                            'cod_colaborador',
                                            'ultima_atualizacao'
                                            ]]
            
            fato_contas = dfs_atualizados['contas'][['num_conta',
                                            'saldo_total',
                                            'saldo_disponivel',
                                            'data_ultimo_lancamento',
                                            'ultima_atualizacao',
                                            ]]

            # Definição de dois dicionários mapeados para os nomes das tabelas do DW, um com tabelas sem chave estrangeira e outro com tabelas que possuem chave estrangeira
            # Na task seguinte, os dados desses dicionários serão inseridos no banco em ordem para garantir que as tabelas que são referenciadas sejam inseridas primeiro
            tabelas_iniciais = {
                                'dim_agencias': dfs_atualizados['agencias'],
                                'dim_clientes': dfs_atualizados['clientes'],
                                'dim_colaboradores': dfs_atualizados['colaboradores'],
                                }
            
            tabelas_fk = {
                        'dim_colaborador_agencia': dfs_atualizados['colaborador_agencia'],
                        'dim_contas' : dim_contas,
                        'fato_contas': fato_contas,
                        'fato_propostas_credito' : dfs_atualizados['propostas_credito'],
                        'fato_transacoes' : dfs_atualizados['transacoes']
                        }
            
            # Retorna uma tupla com os dois dicionários
            logging.info("Dados mapeados e prontos para a ingestão.")

            return tabelas_iniciais, tabelas_fk
    
        except Exception as e:
           logging.error("Ocorreu um erro no mapeamento para as tabelas: ", e)

    @task
    def ingestao_dw(dados_mapeados: tuple):

        import pandas as pd

        try:
            # Conecta ao Data Warehouse
            postgres_hook = PostgresHook(postgres_conn_id="dw_banvic")
            
            # Descompacta a tupla em duas variáveis
            tabelas_iniciais, tabelas_fk = dados_mapeados

            # Itera no dicionário de tabelas iniciais (tabelas que não possuem chave estrangeira)
            for chave, df in tabelas_iniciais.items():

                # Obtém o nome das colunas e define os placeholders de acordo com a quantidade de colunas para montar a query
                colunas = tuple(df.columns)
                colunas_query = ', '.join(colunas)
                placeholders = ', '.join(['%s'] * len(colunas))

                # Define uma lista de tuplas com os dados do DataFrame
                lista_dados = [tuple(row) for row in df.values]
                
                # Monta a query com as informações definidas acima
                query = f"""
                        INSERT INTO {chave} ({colunas_query})
                        VALUES ({placeholders})
                        ON CONFLICT DO NOTHING
                        """
                
                # Obtém a conexão, cria um cursor e executa a query
                # A conexão só é aberta dentro do contexto do bloco with
                with postgres_hook.get_conn() as conn:
                    cursor = conn.cursor()
                    cursor.executemany(query, lista_dados)
                    conn.commit()
                
            logging.info("Tabelas iniciais inseridas com sucesso!")

        except Exception as e:
            logging.error("Ocorreu um erro na inserção das tabelas iniciais: ", e)

        try:
            # Realiza a mesma operação anterior, porém com as tabelas que possuem chave estrangeira
            for chave, df in tabelas_fk.items():

                colunas = tuple(df.columns)
                colunas_query = ', '.join(colunas)
                placeholders = ', '.join(['%s'] * len(colunas))

                lista_dados = [tuple(row) for row in df.values]
                
                query = f"""
                        INSERT INTO {chave} ({colunas_query})
                        VALUES ({placeholders})
                        ON CONFLICT DO NOTHING
                        """
                with postgres_hook.get_conn() as conn:
                    cursor = conn.cursor()
                    cursor.executemany(query, lista_dados)
                    conn.commit()
                
            logging.info("Tabelas com relacionamento inseridas com sucesso!")

        except Exception as e:
            logging.error("Ocorreu um erro na inserção das tabelas com relacionamento: ", e)

    # Definição do fluxo do DAG
    caminho_arquivo = obter_caminho_arquivos()
    dados_mapeados =  preparar_dados(caminho_arquivo)
    ingestao_dw(dados_mapeados)

dag_extracao = inserir_dados_dw()
                    



