# 🎬 Movie Data Pipeline

Pipeline de dados com Python, Docker, Docker Compose, PostgreSQL, GitHub Actions e publicação no Docker Hub.

Este projeto demonstra um fluxo completo de engenharia de dados:

- coleta de dados de filmes via OMDb API
- fallback local para manter a execução estável no CI
- geração de usuários e avaliações
- armazenamento intermediário em CSV no Data Lake
- carga dos dados em PostgreSQL
- execução de consultas analíticas
- validação automatizada via GitHub Actions
- publicação automática da imagem no Docker Hub

---

## 📌 Objetivo do Projeto

O objetivo é simular um pipeline ponta a ponta de dados de filmes, usuários e avaliações, com execução local e automatizada em CI/CD.

O projeto foi estruturado para ser:

- simples de rodar localmente
- reprodutível com Docker
- robusto em ambiente de CI
- validável automaticamente no GitHub Actions
- publicável no Docker Hub após validação

---

## 🧱 Arquitetura do Pipeline

```text
OMDb API / Fallback local
        ↓
Data Lake (CSV)
        ↓
PostgreSQL (Data Warehouse)
        ↓
Consultas Analíticas (SQL)
        ↓
Logs + validações + artifacts
        ↓
Build e publicação da imagem no Docker Hub
```

---

## 📁 Estrutura do Projeto

```text
movieflix-analytics/
├── .github/
│   └── workflows/
│       └── ci.yml
├── app/
│   ├── collect_and_generate.py
│   ├── load_to_postgres.py
│   ├── requirements.txt
│   └── run_analytics.py
├── data-lake/
│   └── .gitkeep
├── .dockerignore
├── Dockerfile
├── docker-compose.yml
└── README.md
```

---

## ⚙️ Tecnologias utilizadas

- Python 3.11
- Requests
- Pandas
- SQLAlchemy
- Psycopg2
- PostgreSQL 15
- Docker
- Docker Compose
- GitHub Actions
- Docker Hub

---

## 🚀 Execução local com Docker Compose

Na raiz do projeto, execute:

```bash
docker compose up --build
```

Se quiser executar apenas o ETL com o banco já iniciado:

```bash
docker compose up -d postgres
docker compose run --rm etl
```

O pipeline irá:

1. gerar `movie.csv`, `users.csv` e `rating.csv` em `data-lake/`
2. carregar os dados no PostgreSQL
3. executar as consultas analíticas
4. exibir os resultados no terminal

---

## 🐳 Publicação automática no Docker Hub

A imagem é publicada automaticamente pelo GitHub Actions após a validação do pipeline.

### Requisitos no GitHub

Configurar no repositório:

#### Variable

```text
DOCKERHUB_USERNAME
```

#### Secret

```text
DOCKERHUB_TOKEN
```

### Tags publicadas automaticamente

O workflow publica a imagem com três tags:

- `latest`
- `sha-<7 primeiros caracteres do commit>`
- `<nome-da-branch>`

Exemplo:

```text
luizfelipecamargo/movieflix-analytics:latest
luizfelipecamargo/movieflix-analytics:sha-abc1234
luizfelipecamargo/movieflix-analytics:master
```

---

## ▶️ Executar a imagem direto do Docker Hub

A imagem publicada já pode ser baixada diretamente do Docker Hub.

### 1. Baixar a imagem

```bash
docker pull luizfelipecamargo/movieflix-analytics:latest
```

### 2. Criar uma rede Docker

```bash
docker network create movieflix-net
```

### 3. Subir o PostgreSQL

```bash
docker run -d \
  --name movieflix-postgres \
  --network movieflix-net \
  -e POSTGRES_DB=dw \
  -e POSTGRES_USER=dw_user \
  -e POSTGRES_PASSWORD=dw_pass \
  postgres:15
```

### 4. Criar a pasta local do Data Lake

```bash
mkdir -p data-lake
```

### 5. Executar a imagem publicada

```bash
docker run --rm \
  --network movieflix-net \
  -e DATABASE_URL=postgresql+psycopg2://dw_user:dw_pass@movieflix-postgres:5432/dw \
  -e POSTGRES_HOST=movieflix-postgres \
  -e POSTGRES_DB=dw \
  -e POSTGRES_USER=dw_user \
  -e POSTGRES_PASSWORD=dw_pass \
  -v "$(pwd)/data-lake:/data-lake" \
  luizfelipecamargo/movieflix-analytics:latest
```

> Em PowerShell, caso necessário, troque `$(pwd)` por `${PWD}`.

### 6. Encerrar o ambiente

```bash
docker rm -f movieflix-postgres
docker network rm movieflix-net
```

---

## ✅ Resultado esperado

Uma execução bem-sucedida exibe mensagens como:

```text
✅ CSVs gerados no Data Lake (movies=28, users=20, ratings=134)
✅ PostgreSQL disponível na tentativa 1.
✅ Dados carregados corretamente no PostgreSQL (movie=28, users=20, rating=134)
✅ Conectado ao PostgreSQL para analytics na tentativa 1.
✅ Consultas analíticas executadas com sucesso
```

---

## 📊 Resultados das queries analíticas

Abaixo estão os resultados observados em uma execução bem-sucedida do pipeline.

### 1. Top 5 filmes mais populares

| title | qtd | media |
|---|---:|---:|
| Interstellar | 45 | 2.75 |
| Inception | 42 | 3.42 |
| Joker | 36 | 3.30 |
| Fight Club | 36 | 3.23 |
| Avatar | 33 | 3.65 |

### 2. Gênero melhor avaliado

| genre | media |
|---|---:|
| Fantasy | 3.65 |

### 3. País que mais assiste filmes

| country | total |
|---|---:|
| Brazil | 50 |
| USA | 36 |
| Germany | 29 |
| Canada | 10 |
| UK | 9 |

---

## 🤖 CI/CD com GitHub Actions

O workflow está em:

```text
.github/workflows/ci.yml
```

### O que ele faz

A cada `push`, `pull_request` ou execução manual, o GitHub Actions:

1. faz checkout do código
2. builda a imagem ETL para validação
3. sobe o PostgreSQL
4. aguarda o banco ficar pronto
5. executa o pipeline ETL real
6. valida os CSVs gerados
7. valida as tabelas carregadas no PostgreSQL
8. publica os CSVs como artifact
9. verifica a configuração do Docker Hub
10. publica a imagem no Docker Hub quando a execução não for `pull_request`

### Jobs do workflow

- `validate-pipeline`
- `check-dockerhub-config`
- `publish-docker-image`

---

## 🧪 Robustez implementada no projeto

### `app/collect_and_generate.py`

- consulta a OMDb API com `timeout`
- usa fallback local quando necessário
- gera dados determinísticos para facilitar testes no CI
- cria os arquivos `movie.csv`, `users.csv` e `rating.csv`

### `app/load_to_postgres.py`

- valida a existência dos CSVs
- aguarda o PostgreSQL ficar disponível
- carrega os arquivos no banco
- exibe contagem de registros carregados

### `app/run_analytics.py`

- aguarda conexão com o banco
- executa consultas analíticas
- exibe tabelas formatadas no log

---

## 🧠 O que este projeto demonstra

- engenharia de dados ponta a ponta
- coleta de dados externos com estratégia de fallback
- geração e tratamento de dados
- Data Lake em CSV
- PostgreSQL como Data Warehouse
- SQL analítico
- Docker e Docker Compose
- validação automatizada em CI
- publicação automatizada de imagem no Docker Hub
- observabilidade por logs e artifacts

---


