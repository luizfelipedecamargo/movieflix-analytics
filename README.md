# Projeto Final, explicando:

- 📁 como criar a estrutura do projeto do zero
- 📄 como criar cada arquivo e colar o conteúdo correto
- 🐳 como subir tudo com Docker Compose
- 📊 o que o pipeline faz e quais resultados esperar
- ⚙️ como automatizar a execução do pipeline
- 🚀 como publicar a imagem no Docker Hub

Você pode copiar e colar este `README.md` diretamente no GitHub.

# 🎬 Movie Data Pipeline

Pipeline de Dados com Python, Docker e PostgreSQL

## 📌 Objetivo do Projeto

Este projeto implementa um **pipeline de engenharia de dados completo**, desde a **coleta de dados externos** até a execução de **consultas analíticas**, utilizando:

- Python
- Docker
- Docker Compose
- PostgreSQL
- SQL Analítico

O pipeline simula um cenário real de dados de filmes, usuários e avaliações, e pode ser executado com **um único comando**.

## 🧱 Arquitetura do Pipeline

O fluxo de dados segue o padrão clássico:

```text
OMDb API
  ↓
Data Lake (CSV)
  ↓
PostgreSQL (Data Warehouse)
  ↓
Consultas Analíticas (SQL)
  ↓
Resultados exibidos no log
```

## 📁 Estrutura do Projeto

Crie uma pasta para o projeto e organize os arquivos conforme abaixo:

```text
movie-data-pipeline/
├── app/
│   ├── collect_and_generate.py
│   ├── load_to_postgres.py
│   ├── run_analytics.py
│   └── requirements.txt
├── data-lake/
├── Dockerfile
├── docker-compose.yml
└── README.md
```

## ✅ Passo 1 — Criar a pasta do projeto

No terminal:

```bash
mkdir movie-data-pipeline
cd movie-data-pipeline
```

## ✅ Passo 2 — Criar as pastas internas

```bash
mkdir app data-lake
```

## ✅ Passo 3 — Criar e preencher os arquivos da aplicação

### 🔹 `app/requirements.txt`

Crie o arquivo:

```bash
touch app/requirements.txt
```

Conteúdo:

```txt
requests
pandas
psycopg2-binary
sqlalchemy
tabulate
```

### 🔹 `app/collect_and_generate.py`

(Coleta de filmes, geração de usuários e avaliações — Data Lake)

Crie o arquivo:

```bash
touch app/collect_and_generate.py
```

Cole o conteúdo:

```python
import requests
import pandas as pd
import random
from datetime import datetime

MOVIE_TITLES = [
    "Inception", "The Matrix", "Titanic", "Avatar", "Gladiator",
    "Interstellar", "Joker", "The Godfather",
    "Pulp Fiction", "Forrest Gump", "Fight Club"
]

movies = []
movie_id = 1

for title in MOVIE_TITLES:
    url = f"http://www.omdbapi.com/?t={title}&apikey=155a49e"
    data = requests.get(url).json()

    if data.get("Response") == "True":
        for genre in data["Genre"].split(","):
            movies.append({
                "movie_id": movie_id,
                "title": data["Title"],
                "genre": genre.strip(),
                "year": data["Year"],
                "country": data["Country"],
                "imdb_rating": data["imdbRating"]
            })
        movie_id += 1

pd.DataFrame(movies).to_csv("/data-lake/movie.csv", index=False)

users = []
countries = ["Brazil", "USA", "UK", "Canada", "Germany"]

for i in range(1, 21):
    users.append({"user_id": i, "country": random.choice(countries)})

pd.DataFrame(users).to_csv("/data-lake/users.csv", index=False)

ratings = []

for user in users:
    for movie in set([m["movie_id"] for m in movies]):
        if random.choice([True, False]):
            ratings.append({
                "user_id": user["user_id"],
                "movie_id": movie,
                "rating": round(random.uniform(1, 5), 1),
                "rating_date": datetime.now().date()
            })

pd.DataFrame(ratings).to_csv("/data-lake/rating.csv", index=False)

print("✅ CSVs gerados no Data Lake")
```

### 🔹 `app/load_to_postgres.py`

(Carga dos CSVs no PostgreSQL — Data Warehouse)

Crie o arquivo:

```bash
touch app/load_to_postgres.py
```

Conteúdo:

```python
import pandas as pd
from sqlalchemy import create_engine

engine = create_engine(
    "postgresql+psycopg2://dw_user:dw_pass@postgres:5432/dw"
)

pd.read_csv("/data-lake/movie.csv").to_sql(
    "movie", engine, if_exists="replace", index=False
)

pd.read_csv("/data-lake/users.csv").to_sql(
    "users", engine, if_exists="replace", index=False
)

pd.read_csv("/data-lake/rating.csv").to_sql(
    "rating", engine, if_exists="replace", index=False
)

print("✅ Dados carregados corretamente no PostgreSQL")
```

### 🔹 `app/run_analytics.py`

(Consultas analíticas e saída no log)

Crie o arquivo:

```bash
touch app/run_analytics.py
```

Conteúdo:

```python
import psycopg2
from tabulate import tabulate

conn = psycopg2.connect(
    host="postgres",
    database="dw",
    user="dw_user",
    password="dw_pass"
)

queries = {
    "Top 5 filmes mais populares": """
        SELECT
            m.title,
            COUNT(*) AS qtd,
            ROUND(AVG(r.rating)::numeric, 2) AS media
        FROM rating r
        JOIN movie m ON r.movie_id = m.movie_id
        GROUP BY m.title
        ORDER BY qtd DESC, media DESC
        LIMIT 5;
    """,

    "Gênero melhor avaliado": """
        SELECT
            m.genre,
            ROUND(AVG(r.rating)::numeric, 2) AS media
        FROM rating r
        JOIN movie m ON r.movie_id = m.movie_id
        GROUP BY m.genre
        ORDER BY media DESC
        LIMIT 1;
    """,

    "País que mais assiste filmes": """
        SELECT
            u.country,
            COUNT(*) AS total
        FROM rating r
        JOIN users u ON r.user_id = u.user_id
        GROUP BY u.country
        ORDER BY total DESC;
    """
}

cursor = conn.cursor()

for title, sql in queries.items():
    print("\n" + title.upper())
    cursor.execute(sql)
    rows = cursor.fetchall()
    headers = [d[0] for d in cursor.description]
    print(tabulate(rows, headers=headers))

conn.close()
```

## ✅ Passo 4 — Dockerização da aplicação

### 🔹 `Dockerfile`

Na raiz do projeto:

```bash
touch Dockerfile
```

Conteúdo:

```dockerfile
FROM python:3.11-alpine

WORKDIR /app

COPY app/requirements.txt .
RUN pip install -r requirements.txt

COPY app/ .

CMD ["sh", "-c",
"python collect_and_generate.py && \
python load_to_postgres.py && \
python run_analytics.py"]
```

## ✅ Passo 5 — Orquestração com Docker Compose

### 🔹 `docker-compose.yml`

Crie o arquivo:

```bash
touch docker-compose.yml
```

Conteúdo:

```yaml
version: "3.9"

services:
  postgres:
    image: postgres:15
    environment:
      POSTGRES_DB: dw
      POSTGRES_USER: dw_user
      POSTGRES_PASSWORD: dw_pass

  etl:
    build: .
    volumes:
      - ./data-lake:/data-lake
    depends_on:
      - postgres
```

## 🚀 Passo 6 — Executar o Pipeline Completo

Na raiz do projeto, execute:

```bash
docker compose up --build
```

## ✅ Resultado Esperado

No terminal, você verá:

```text
✅ CSVs gerados no Data Lake
✅ Dados carregados corretamente no PostgreSQL

TOP 5 FILMES MAIS POPULARES
...

GÊNERO MELHOR AVALIADO
...

PAÍS QUE MAIS ASSISTE FILMES
...
```

Isso confirma que:

- ✅ Dados foram coletados
- ✅ Data Lake foi criado
- ✅ Data Warehouse foi populado
- ✅ Consultas analíticas foram executadas

## 🧠 O que este projeto demonstra

- Engenharia de dados ponta-a-ponta
- Consumo de API externa
- Geração e tratamento de dados
- Uso de Docker e Docker Compose
- PostgreSQL como Data Warehouse
- SQL analítico realista
- Observabilidade via logs

# 🤖 CI/CD com GitHub Actions

Esta seção descreve como **automatizar a execução do pipeline** a cada alteração no código, utilizando **GitHub Actions**.

O objetivo da automação é:

- Executar o pipeline automaticamente a cada `push` na branch `main`
- Construir a imagem Docker
- Publicar a imagem no Docker Hub
- Garantir reprodutibilidade e boas práticas de DevOps

## ✅ Passo 1 — Criar o repositório no GitHub

1. Acesse: `https://github.com`
2. Clique em **New repository**
3. Nome sugerido: `movie-data-pipeline`
4. Escolha **Public**
5. Clique em **Create repository**

## ✅ Passo 2 — Inicializar Git localmente e subir o código

Na pasta raiz do projeto:

```bash
git init
git add .
git commit -m "Pipeline de dados com Docker e PostgreSQL"
```

Conecte ao repositório remoto (substitua `SEU_USUARIO`):

```bash
git branch -M main
git remote add origin https://github.com/SEU_USUARIO/movie-data-pipeline.git
git push -u origin main
```

## ✅ Passo 3 — Estrutura do GitHub Actions

Crie a seguinte estrutura:

```text
.github/
└── workflows/
    └── ci.yml
```

### 🔹 Criar o workflow

Arquivo: `.github/workflows/ci.yml`

```yaml
name: CI/CD - Movie Data Pipeline

on:
  push:
    branches: ["main"]

jobs:
  build-and-push:
    runs-on: ubuntu-latest

    steps:
      - name: Checkout do código
        uses: actions/checkout@v4

      - name: Login no Docker Hub
        uses: docker/login-action@v3
        with:
          username: ${{ secrets.DOCKERHUB_USERNAME }}
          password: ${{ secrets.DOCKERHUB_TOKEN }}

      - name: Build e Push da imagem Docker
        uses: docker/build-push-action@v5
        with:
          context: .
          push: true
          tags: ${{ secrets.DOCKERHUB_USERNAME }}/movie-etl:latest
```

✅ Esse workflow será executado automaticamente a cada `push` na branch `main`.

## 🔐 Configuração dos Secrets no GitHub

Para que o pipeline funcione corretamente, é necessário configurar **Secrets** no repositório.

### Caminho no GitHub

```text
Settings → Secrets and variables → Actions → New repository secret
```

### ✅ Secrets obrigatórios

#### 1️⃣ Docker Hub — Usuário

- **Name:** `DOCKERHUB_USERNAME`
- **Value:** `seu_usuario_dockerhub`

#### 2️⃣ Docker Hub — Token

1. Acesse `https://hub.docker.com`
2. Vá em **Account Settings → Security**
3. Crie um **New Access Token**
4. Copie o token

No GitHub:

- **Name:** `DOCKERHUB_TOKEN`
- **Value:** `<token_gerado>`

✅ Após isso, o GitHub Actions conseguirá publicar imagens automaticamente no Docker Hub.

# 🐳 Publicação da Imagem no Docker Hub

Com o CI/CD configurado, o processo de publicação é automático.

Sempre que você executar:

```bash
git push
```

O GitHub Actions irá:

1. Buildar a imagem Docker
2. Criar a tag: `usuario_dockerhub/movie-etl:latest`
3. Publicar no Docker Hub

## ✅ Conferir a imagem publicada

1. Acesse: `https://hub.docker.com`
2. Abra seu perfil
3. Vá em **Repositories**
4. Veja o repositório: `movie-etl`

## ▶️ Executar a imagem diretamente do Docker Hub

Qualquer pessoa pode executar o pipeline com:

```bash
docker run --rm \
SEU_USUARIO_DOCKERHUB/movie-etl:latest
```

✅ Isso demonstra que o projeto é **totalmente reprodutível**.

## 🧠 O que este CI/CD demonstra

- Integração contínua (CI)
- Entrega contínua (CD)
- Versionamento de imagens Docker
- Boas práticas de segurança (Secrets)
- Automação completa de pipeline de dados
