import datetime
import pendulum
import os
import shutil
import logging

from airflow.decorators import dag, task
from airflow.providers.postgres.hooks.postgres import PostgresHook
from airflow.operators.trigger_dagrun import TriggerDagRunOperator

@dag(
    dag_id="dag_extracao",
    schedule="35 4 * * *",
    start_date=pendulum.datetime(2025, 8, 27, tz="America/Sao_Paulo"),
    catchup=False,
    dagrun_timeout=datetime.timedelta(minutes=60),
)

def dag_extrair_dados():
        
    @task
    def extrair_dados_db():

        # Task para extrair dados do banco de dados Postgres.

        import pandas as pd

        try:
            # Conexão com o banco e obtenção da engine do SQLAlchemy para usar no método pd.read_sql
            postgres_hook = PostgresHook(postgres_conn_id="db_banvic")
            engine = postgres_hook.get_sqlalchemy_engine()
            
            # Query que permite consultar o nome das tabelas utilizando a information_schema do Postgres
            query_nomes_tabelas = """
                SELECT table_name
                FROM information_schema.tables
                WHERE table_schema = current_schema();
            """
            
            # Execução da query que extrai o nome das tabelas.
            # O nome das tabelas é salvo em "nomes_tabelas" como uma Series pandas
            nomes_tabelas = pd.read_sql(query_nomes_tabelas, engine)
            nomes_tabelas = nomes_tabelas['table_name']

            # Obtém a data atual para definir o nome do diretório no Data Lake
            # Um sub-diretório também será criado para indicar a origem dos dados (nesse caso, banco de dados)
            data_atual = datetime.datetime.now().strftime("%Y-%m-%d")
            caminho_datalake = f"/opt/airflow/datalake/{data_atual}/banco_de_dados/"

            # Cria os diretórios. Se existirem, ignora.
            os.makedirs(caminho_datalake, exist_ok=True)

            # Define uma query para cada nome de tabela armazenado em "nomes_tabelas"
            for nome_tabela in nomes_tabelas:
                query = f"""
                    SELECT *
                    FROM {nome_tabela};
                """
                
                # Executa cada query no banco, cria um dataframe Pandas para cada tabela da iteração e armazena em "df"
                df = pd.read_sql(query, engine)
                
                # Salva os dados em CSV no "caminho_datalake" definido anteriormente com o nome da tabela sendo o nome do arquivo.
                df.to_csv(f"{caminho_datalake}/{nome_tabela}.csv", index=False)

            logging.info("Dados extraídos com sucesso para o datalake!")
        
        except Exception as e:
            logging.error("Ocorreu um erro na extração dos dados do banco:", e)
        
    @task
    def extrair_dados_csv():

        # Task para extrair os dados de um diretório com arquivos CSV.

        # Definição do caminho em que o dado em CSV está salvo.
        arquivo_csv = "/opt/airflow/dados_csv/transacoes.csv"

        # Obtém a data atual para definir o nome do diretório no Data Lake
        # Um sub-diretório também será criado para indicar a origem dos dados (nesse caso, dados em CSV)
        data_atual = datetime.datetime.now().strftime("%Y-%m-%d")
        caminho_datalake = f"/opt/airflow/datalake/{data_atual}/dados_csv/"

        # Cria os diretórios. Se existirem, ignora.
        os.makedirs(caminho_datalake, exist_ok=True)

        try:
            # Método que copia o arquivo da pasta atual para a pasta do Data Lake mantendo os metadados originais
            shutil.copy2(arquivo_csv, caminho_datalake)

            logging.info("CSV extraído com sucesso para o datalake!")
        
        except Exception as e:
            logging.error('Ocorreu um erro na extração dos dados em CSV:', e)

    # Task que cria o Trigger para o DAG de ingestão
    trigger_dag_ingestao = TriggerDagRunOperator(
        task_id="trigger_dag_ingestao",
        trigger_dag_id="dag_ingestao"
    )

    # Instanciando as tasks para que sejam executadas em paralelo
    extrair_db = extrair_dados_db() 
    extrair_csv = extrair_dados_csv()

    # A task de Trigger só é acionada quando ambas as tasks de extração são finalizadas
    extrair_db >> trigger_dag_ingestao
    extrair_csv >> trigger_dag_ingestao   

extracao_dag = dag_extrair_dados()