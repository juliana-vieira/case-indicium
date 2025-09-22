# 💚 Case Indicium - Programa Lighthouse

## 📋 Sobre o Projeto

Este repositório contém o código da minha solução para o desafio técnico do **Programa Lighthouse** da empresa **Indicium**, focado em Engenharia de Dados. O projeto demonstra a implementação de um pipeline completo de dados: extração dos dados do banco relacional do cliente Banco Vitória, modelagem dimensional de um Data Warehouse e ingestão dos dados no mesmo.

### 🎯 Objetivo
Desenvolver uma solução de dados focada em **extração e ingestão** que demonstre competências técnicas em:
- Engenharia de Dados
- Modelagem Dimensional
- Pipeline ETL
- Data Warehouse
- Orquestração de processos com Apache Airflow
  
---

## 🏗️ Arquitetura do Projeto

### Diagrama de Fluxo de Dados

```mermaid
flowchart LR
    subgraph "Fontes de Dados"
        A1[CSV]
        A2[SQL]
    end

    subgraph "Apache Airflow"
        B1[Extração]
        B2[FileSystem Local<br/>Data Lake]
        B3[Carregamento]
        B4[PostgreSQL Local<br/>Data Warehouse]
        
        B1 --> B2
        B2 --> B3
        B3 --> B4
    end

    A1 --> B1
    A2 --> B1
```

---

## 🗄️ Modelagem do Data Warehouse

### Diagrama de Relacionamento

```mermaid
erDiagram
    DIM_AGENCIAS ||--o{ DIM_COLABORADOR_AGENCIA : "cod_agencia"
    DIM_COLABORADORES ||--o{ DIM_COLABORADOR_AGENCIA : "cod_colaborador"
    DIM_COLABORADORES ||--o{ FATO_PROPOSTAS : "cod_colaborador"
    DIM_CLIENTES ||--o{ FATO_PROPOSTAS : "cod_cliente"
    FATO_CONTAS ||--o{ FATO_TRANSACOES : "num_conta"
    DIM_CONTAS ||--o{ FATO_TRANSACOES : "num_conta"
    DIM_CONTAS ||--o{ FATO_CONTAS : "num_conta"

    DIM_AGENCIAS {
        int cod_agencia PK
        string nome
        string endereco
        string cidade
        string uf
        date data_abertura
        string tipo_agencia
        timestamp ultima_atualizacao
    }

    DIM_COLABORADOR_AGENCIA {
        int cod_colaborador PK
        int cod_agencia FK
        timestamp ultima_atualizacao
    }

    DIM_COLABORADORES {
        int cod_colaborador PK
        string primeiro_nome
        string ultimo_nome
        string email
        string cpf
        date data_nascimento
        string endereco
        string cep
        timestamp ultima_atualizacao
    }

    FATO_PROPOSTAS {
        int cod_proposta PK
        int cod_cliente FK
        int cod_colaborador FK
        date data_entrada_proposta
        decimal taxa_juros_mensal
        decimal valor_proposta
        decimal valor_financiamento
        decimal valor_entrada
        decimal valor_prestacao
        int quantidade_parcelas
        string carencia
        string status_proposta
        timestamp ultima_atualizacao
    }

    DIM_CLIENTES {
        int cod_cliente PK
        string primeiro_nome
        string ultimo_nome
        string email
        string tipo_cliente
        date data_inclusao
        string cpfcnpj
        date data_nascimento
        string endereco
        string cep
        timestamp ultima_atualizacao
    }

    FATO_TRANSACOES {
        int cod_transacao PK
        int num_conta FK
        date data_transacao
        string nome_transacao
        decimal valor_transacao
        timestamp ultima_atualizacao
    }

    FATO_CONTAS {
        int num_conta PK
        decimal saldo_total
        decimal saldo_disponivel
        date data_ultimo_lancamento
        timestamp ultima_atualizacao
    }

    DIM_CONTAS {
        int num_conta PK
        string tipo_conta
        date data_abertura
        int cod_cliente FK
        int cod_agencia FK
        int cod_colaborador FK
        timestamp ultima_atualizacao
    }
```

---

## 🛠️ Tecnologias Utilizadas

- **Docker** - Containerização da aplicação e dependências
- **Apache Airflow** - Orquestração e agendamento de pipelines
- **PostgreSQL** - Banco de dados para Data Warehouse
- **Python** - Linguagem principal para ETL e processamento
- **SQL** - Manipulação e consulta de dados
  
---

## 📊 Pipeline de Dados

### Funcionalidades Implementadas:
- **Extração automatizada** de dados de múltiplas fontes
- **Armazenamento** de dados brutos em um Data Lake
- **Carregamento estruturado** no Data Warehouse PostgreSQL
- **Orquestração com Airflow** para agendamento e monitoramento
- **Modelagem dimensional** para análises otimizadas

---

## ⚠️ Limitações Conhecidas

Este projeto foi desenvolvido para fins de **demonstração técnica** e possui as seguintes limitações:

### 🔴 Data Lake Simulado
- Utiliza sistema de arquivos local para simular um Data Lake em vez de uma solução cloud (AWS S3, Azure Data Lake, etc.)

### 🔴 Ausência de CDC (Change Data Capture)
- Os dados mais atualizados são determinados de acordo com a data do diretório do Data Lake
- Não captura mudanças em tempo real 
- Dados podem ficar desatualizados entre execuções

### 🔴 Ambiente de Desenvolvimento
- Configuração simplificada para demonstração
- Execução em containers locais via Docker
- Sem pipeline CI/CD implementado
- Logs e monitoramento básicos

---

## 🎯 Melhorias Futuras

Para uma implementação em produção, seria necessário:

1. **Implementar CDC** para captura de mudanças em tempo real
2. **Migrar para Data Lake real** (AWS S3, Azure Data Lake, GCP Cloud Storage)
3. **Adicionar orquestração avançada** com recursos enterprise do Airflow
4. **Implementar data quality** e validações automáticas robustas
5. **Adicionar monitoramento** e alertas avançados
6. **Configurar pipeline CI/CD** para automação de deploys
7. **Implementar data lineage** e catalogação de dados
8. **Adicionar testes automatizados** para os pipelines
9. **Configurar backup e recovery** dos dados
10. **Implementar segurança** e controle de acesso

---

## 👥 Contato

**Juliana Vieira**
- LinkedIn: [linkedin.com/in/juliana-vieira](https://linkedin.com/in/juliana-vieira)
- Email: julianasalustianovieira@gmail.com

---

*Projeto desenvolvido com 💚 para o Programa Lighthouse 2025*
