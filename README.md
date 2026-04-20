# 🎬 Movie Data Pipeline

Pipeline de dados com Python, Docker, Docker Compose, PostgreSQL, GitHub Actions e publicação no Docker Hub.

Este repositório demonstra um fluxo completo de engenharia de dados:

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

O projeto implementa um pipeline ponta a ponta que simula um cenário real de dados de filmes, usuários e avaliações.

A execução foi pensada para ser:

- simples de rodar localmente
- reprodutível com Docker
- robusta em ambiente de CI
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

## ✅ Passo 1 — Criar a pasta do projeto

```bash
mkdir movieflix-analytics
cd movieflix-analytics
```

---

## ✅ Passo 2 — Criar as pastas internas

```bash
mkdir -p app data-lake .github/workflows
touch data-lake/.gitkeep
```

---

## ✅ Passo 3 — Criar e preencher os arquivos da aplicação

### 🔹 `app/requirements.txt`

```txt
requests
pandas
psycopg2-binary
sqlalchemy
tabulate
```

### 🔹 `app/collect_and_generate.py`

Responsável por:

- consultar a OMDb API com `timeout`
- usar fallback local quando necessário
- gerar dados determinísticos para facilitar testes no CI
- criar os arquivos `movie.csv`, `users.csv` e `rating.csv`

```python
import os
import random
from datetime import datetime
from pathlib import Path

import pandas as pd
import requests
from requests import RequestException

MOVIE_TITLES = [
    "Inception", "The Matrix", "Titanic", "Avatar", "Gladiator",
    "Interstellar", "Joker", "The Godfather",
    "Pulp Fiction", "Forrest Gump", "Fight Club"
]

FALLBACK_MOVIES = {
    "Inception": {
        "Title": "Inception",
        "Genre": "Action, Adventure, Sci-Fi",
        "Year": "2010",
        "Country": "USA",
        "imdbRating": "8.8",
    },
    "The Matrix": {
        "Title": "The Matrix",
        "Genre": "Action, Sci-Fi",
        "Year": "1999",
        "Country": "USA",
        "imdbRating": "8.7",
    },
    "Titanic": {
        "Title": "Titanic",
        "Genre": "Drama, Romance",
        "Year": "1997",
        "Country": "USA",
        "imdbRating": "7.9",
    },
    "Avatar": {
        "Title": "Avatar",
        "Genre": "Action, Adventure, Fantasy",
        "Year": "2009",
        "Country": "USA",
        "imdbRating": "7.9",
    },
    "Gladiator": {
        "Title": "Gladiator",
        "Genre": "Action, Adventure, Drama",
        "Year": "2000",
        "Country": "USA",
        "imdbRating": "8.5",
    },
    "Interstellar": {
        "Title": "Interstellar",
        "Genre": "Adventure, Drama, Sci-Fi",
        "Year": "2014",
        "Country": "USA",
        "imdbRating": "8.7",
    },
    "Joker": {
        "Title": "Joker",
        "Genre": "Crime, Drama, Thriller",
        "Year": "2019",
        "Country": "USA",
        "imdbRating": "8.4",
    },
    "The Godfather": {
        "Title": "The Godfather",
        "Genre": "Crime, Drama",
        "Year": "1972",
        "Country": "USA",
        "imdbRating": "9.2",
    },
    "Pulp Fiction": {
        "Title": "Pulp Fiction",
        "Genre": "Crime, Drama",
        "Year": "1994",
        "Country": "USA",
        "imdbRating": "8.9",
    },
    "Forrest Gump": {
        "Title": "Forrest Gump",
        "Genre": "Drama, Romance",
        "Year": "1994",
        "Country": "USA",
        "imdbRating": "8.8",
    },
    "Fight Club": {
        "Title": "Fight Club",
        "Genre": "Drama",
        "Year": "1999",
        "Country": "USA",
        "imdbRating": "8.8",
    },
}

DATA_LAKE_DIR = Path("/data-lake")
OMDB_API_KEY = os.getenv("OMDB_API_KEY", "155a49e")
OMDB_BASE_URL = "https://www.omdbapi.com/"

random.seed(42)


def fetch_movie(title: str) -> dict:
    try:
        response = requests.get(
            OMDB_BASE_URL,
            params={"t": title, "apikey": OMDB_API_KEY},
            timeout=10,
        )
        response.raise_for_status()
        data = response.json()
        if data.get("Response") == "True":
            return data
        print(f"⚠️ OMDb não retornou dados válidos para '{title}'. Usando fallback.")
    except RequestException as exc:
        print(f"⚠️ Falha ao consultar OMDb para '{title}': {exc}. Usando fallback.")

    fallback = FALLBACK_MOVIES.get(title)
    if not fallback:
        raise ValueError(f"Nenhum fallback configurado para o filme '{title}'.")
    return fallback


def build_movies() -> list[dict]:
    movies = []
    movie_id = 1

    for title in MOVIE_TITLES:
        data = fetch_movie(title)
        genres = [genre.strip() for genre in data["Genre"].split(",") if genre.strip()]
        for genre in genres:
            movies.append(
                {
                    "movie_id": movie_id,
                    "title": data["Title"],
                    "genre": genre,
                    "year": data["Year"],
                    "country": data["Country"],
                    "imdb_rating": data["imdbRating"],
                }
            )
        movie_id += 1

    return movies


def build_users() -> list[dict]:
    countries = ["Brazil", "USA", "UK", "Canada", "Germany"]
    return [
        {"user_id": user_id, "country": random.choice(countries)}
        for user_id in range(1, 21)
    ]


def build_ratings(users: list[dict], movie_ids: list[int]) -> list[dict]:
    ratings = []
    rating_date = datetime.utcnow().date().isoformat()

    for user in users:
        rated_movie_ids = random.sample(
            movie_ids,
            k=random.randint(3, len(movie_ids)),
        )
        for movie_id in rated_movie_ids:
            ratings.append(
                {
                    "user_id": user["user_id"],
                    "movie_id": movie_id,
                    "rating": round(random.uniform(1, 5), 1),
                    "rating_date": rating_date,
                }
            )

    return ratings


def main() -> None:
    DATA_LAKE_DIR.mkdir(parents=True, exist_ok=True)

    movies = build_movies()
    users = build_users()
    movie_ids = sorted({movie["movie_id"] for movie in movies})
    ratings = build_ratings(users, movie_ids)

    pd.DataFrame(movies).to_csv(DATA_LAKE_DIR / "movie.csv", index=False)
    pd.DataFrame(users).to_csv(DATA_LAKE_DIR / "users.csv", index=False)
    pd.DataFrame(ratings).to_csv(DATA_LAKE_DIR / "rating.csv", index=False)

    print(
        "✅ CSVs gerados no Data Lake "
        f"(movies={len(movies)}, users={len(users)}, ratings={len(ratings)})"
    )


if __name__ == "__main__":
    main()
```

### 🔹 `app/load_to_postgres.py`

Responsável por:

- validar a existência dos CSVs
- aguardar o PostgreSQL ficar disponível
- carregar os arquivos no banco
- exibir contagem de registros carregados

```python
import os
import time
from pathlib import Path

import pandas as pd
from sqlalchemy import create_engine, text
from sqlalchemy.exc import OperationalError

DATABASE_URL = os.getenv(
    "DATABASE_URL",
    "postgresql+psycopg2://dw_user:dw_pass@postgres:5432/dw",
)
DATA_LAKE_DIR = Path("/data-lake")
CSV_FILES = {
    "movie": DATA_LAKE_DIR / "movie.csv",
    "users": DATA_LAKE_DIR / "users.csv",
    "rating": DATA_LAKE_DIR / "rating.csv",
}


def wait_for_database(max_attempts: int = 30, delay_seconds: int = 2):
    last_error = None

    for attempt in range(1, max_attempts + 1):
        try:
            engine = create_engine(DATABASE_URL, pool_pre_ping=True)
            with engine.connect() as connection:
                connection.execute(text("SELECT 1"))
            print(f"✅ PostgreSQL disponível na tentativa {attempt}.")
            return engine
        except OperationalError as exc:
            last_error = exc
            print(
                f"⏳ Aguardando PostgreSQL ficar disponível "
                f"({attempt}/{max_attempts})..."
            )
            time.sleep(delay_seconds)

    raise RuntimeError("Não foi possível conectar ao PostgreSQL.") from last_error


def validate_csv_files() -> None:
    missing_files = [str(path) for path in CSV_FILES.values() if not path.exists()]
    if missing_files:
        raise FileNotFoundError(
            "Os seguintes arquivos CSV não foram encontrados: "
            + ", ".join(missing_files)
        )


def main() -> None:
    validate_csv_files()
    engine = wait_for_database()

    loaded_rows = {}
    for table_name, csv_path in CSV_FILES.items():
        dataframe = pd.read_csv(csv_path)
        dataframe.to_sql(table_name, engine, if_exists="replace", index=False)
        loaded_rows[table_name] = len(dataframe)

    print(
        "✅ Dados carregados corretamente no PostgreSQL "
        f"(movie={loaded_rows['movie']}, users={loaded_rows['users']}, rating={loaded_rows['rating']})"
    )


if __name__ == "__main__":
    main()
```

### 🔹 `app/run_analytics.py`

Responsável por:

- aguardar conexão com o banco
- executar consultas analíticas
- exibir tabelas formatadas no log

```python
import os
import time

import psycopg2
from tabulate import tabulate

DATABASE_CONFIG = {
    "host": os.getenv("POSTGRES_HOST", "postgres"),
    "database": os.getenv("POSTGRES_DB", "dw"),
    "user": os.getenv("POSTGRES_USER", "dw_user"),
    "password": os.getenv("POSTGRES_PASSWORD", "dw_pass"),
}

QUERIES = {
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
    """,
}


def connect_with_retry(max_attempts: int = 30, delay_seconds: int = 2):
    last_error = None

    for attempt in range(1, max_attempts + 1):
        try:
            connection = psycopg2.connect(**DATABASE_CONFIG)
            print(f"✅ Conectado ao PostgreSQL para analytics na tentativa {attempt}.")
            return connection
        except psycopg2.OperationalError as exc:
            last_error = exc
            print(
                f"⏳ Aguardando conexão para analytics "
                f"({attempt}/{max_attempts})..."
            )
            time.sleep(delay_seconds)

    raise RuntimeError("Não foi possível conectar ao PostgreSQL para analytics.") from last_error


def main() -> None:
    with connect_with_retry() as connection:
        with connection.cursor() as cursor:
            for title, sql in QUERIES.items():
                print("\n" + title.upper())
                cursor.execute(sql)
                rows = cursor.fetchall()
                headers = [description[0] for description in cursor.description]
                print(tabulate(rows, headers=headers, tablefmt="github"))

    print("✅ Consultas analíticas executadas com sucesso")


if __name__ == "__main__":
    main()
```

---

## ✅ Passo 4 — Dockerização da aplicação

### 🔹 `Dockerfile`

A imagem foi ajustada para ficar mais confiável no CI, usando `python:3.11-slim` em vez de Alpine.

```dockerfile
FROM python:3.11-slim

ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1
ENV PIP_NO_CACHE_DIR=1

WORKDIR /app

COPY app/requirements.txt ./requirements.txt
RUN pip install --upgrade pip && pip install -r requirements.txt

COPY app/ /app/

CMD ["sh", "-c", "python collect_and_generate.py && python load_to_postgres.py && python run_analytics.py"]
```

### 🔹 `.dockerignore`

Esse arquivo evita enviar arquivos desnecessários para o contexto de build, o que ajuda no build local e também na publicação da imagem no Docker Hub.

```dockerignore
.git
.github
__pycache__/
*.pyc
*.pyo
*.pyd
*.log
.env
.venv/
venv/
data-lake/*.csv
```

---

## ✅ Passo 5 — Orquestração com Docker Compose

### 🔹 `docker-compose.yml`

O `docker-compose.yml` atual inclui:

- healthcheck no PostgreSQL
- variáveis de ambiente para a aplicação ETL
- dependência condicionada ao serviço saudável

```yaml
services:
  postgres:
    image: postgres:15
    environment:
      POSTGRES_DB: dw
      POSTGRES_USER: dw_user
      POSTGRES_PASSWORD: dw_pass
    healthcheck:
      test: ["CMD-SHELL", "pg_isready -U dw_user -d dw"]
      interval: 5s
      timeout: 5s
      retries: 10
      start_period: 5s

  etl:
    build: .
    environment:
      DATABASE_URL: postgresql+psycopg2://dw_user:dw_pass@postgres:5432/dw
      POSTGRES_HOST: postgres
      POSTGRES_DB: dw
      POSTGRES_USER: dw_user
      POSTGRES_PASSWORD: dw_pass
    volumes:
      - ./data-lake:/data-lake
    depends_on:
      postgres:
        condition: service_healthy
```

---

## 🚀 Passo 6 — Executar o Pipeline Completo

Na raiz do projeto:

```bash
docker compose up --build
```

Se quiser executar apenas o ETL com o banco separado:

```bash
docker compose up -d postgres
docker compose run --rm etl
```

---

## ✅ Resultado Esperado

Você verá no terminal algo semelhante a:

```text
✅ CSVs gerados no Data Lake (movies=28, users=20, ratings=134)
✅ PostgreSQL disponível na tentativa 1.
✅ Dados carregados corretamente no PostgreSQL (movie=28, users=20, rating=134)
✅ Conectado ao PostgreSQL para analytics na tentativa 1.

TOP 5 FILMES MAIS POPULARES
...

GÊNERO MELHOR AVALIADO
...

PAÍS QUE MAIS ASSISTE FILMES
...

✅ Consultas analíticas executadas com sucesso
```

Isso confirma que:

- os dados foram coletados ou recuperados via fallback
- o Data Lake foi gerado
- o PostgreSQL foi populado
- as consultas analíticas rodaram corretamente

---

## 🤖 CI/CD com GitHub Actions

O projeto possui um workflow de validação e publicação automática em:

```text
.github/workflows/ci.yml
```

### O que esse workflow faz

A cada `push`, `pull_request` ou execução manual, o GitHub Actions:

1. faz checkout do código
2. exibe a versão do Docker e Docker Compose
3. builda a imagem ETL para validação
4. sobe o PostgreSQL
5. aguarda o banco ficar pronto
6. executa o pipeline ETL real
7. valida os arquivos CSV gerados
8. valida as tabelas carregadas no PostgreSQL
9. exibe prévia dos CSVs no log
10. publica os CSVs como artifact
11. publica a imagem no Docker Hub quando a execução não for `pull_request` e as credenciais estiverem configuradas
12. exibe logs dos containers
13. encerra os containers ao final

### 🔹 `.github/workflows/ci.yml`

```yaml
# Workflow de validação e publicação do pipeline
name: CI/CD - Movie Data Pipeline

on:
  push:
    branches: ["master", "main"]
  pull_request:
    branches: ["master", "main"]
  workflow_dispatch:

env:
  IMAGE_REPOSITORY: movieflix-analytics

jobs:
  validate-pipeline:
    runs-on: ubuntu-latest

    steps:
      - name: Checkout do código
        uses: actions/checkout@v6

      - name: Exibir versões do Docker
        run: |
          docker --version
          docker compose version

      - name: Buildar imagem ETL
        run: docker compose build etl

      - name: Subir PostgreSQL
        run: docker compose up -d postgres

      - name: Aguardar PostgreSQL ficar pronto
        run: |
          CONTAINER_ID=$(docker compose ps -q postgres)
          for i in {1..30}; do
            if docker exec "$CONTAINER_ID" pg_isready -U dw_user -d dw; then
              echo "PostgreSQL pronto para uso."
              exit 0
            fi
            echo "Aguardando PostgreSQL... tentativa $i/30"
            sleep 2
          done
          echo "PostgreSQL não ficou pronto a tempo."
          docker compose logs postgres
          exit 1

      - name: Executar pipeline ETL
        run: docker compose run --rm etl

      - name: Validar arquivos gerados no Data Lake
        run: |
          test -f data-lake/movie.csv
          test -f data-lake/users.csv
          test -f data-lake/rating.csv
          echo "Arquivos gerados com sucesso:"
          ls -lah data-lake

      - name: Validar tabelas carregadas no PostgreSQL
        run: |
          docker compose exec -T postgres psql -U dw_user -d dw -c "SELECT COUNT(*) AS movie_rows FROM movie;"
          docker compose exec -T postgres psql -U dw_user -d dw -c "SELECT COUNT(*) AS users_rows FROM users;"
          docker compose exec -T postgres psql -U dw_user -d dw -c "SELECT COUNT(*) AS rating_rows FROM rating;"

      - name: Mostrar prévia dos CSVs
        run: |
          echo "--- movie.csv ---"
          head -n 5 data-lake/movie.csv
          echo "--- users.csv ---"
          head -n 5 data-lake/users.csv
          echo "--- rating.csv ---"
          head -n 5 data-lake/rating.csv

      - name: Publicar artefatos do Data Lake
        uses: actions/upload-artifact@v7
        with:
          name: data-lake-csvs
          path: data-lake/*.csv
          if-no-files-found: error

      - name: Exibir logs dos containers
        if: always()
        run: docker compose logs --no-color

      - name: Encerrar containers
        if: always()
        run: docker compose down -v

  publish-docker-image:
    name: Publicar imagem no Docker Hub
    runs-on: ubuntu-latest
    needs: validate-pipeline
    if: >
      vars.DOCKERHUB_USERNAME != '' &&
      secrets.DOCKERHUB_TOKEN != '' &&
      github.event_name != 'pull_request'

    steps:
      - name: Checkout do código
        uses: actions/checkout@v6

      - name: Definir tags da imagem
        id: meta
        run: |
          SHORT_SHA="${GITHUB_SHA::7}"
          BRANCH_TAG="${GITHUB_REF_NAME//\//-}"
          IMAGE_NAME="${{ vars.DOCKERHUB_USERNAME }}/${{ env.IMAGE_REPOSITORY }}"
          echo "image_name=${IMAGE_NAME}" >> "$GITHUB_OUTPUT"
          echo "latest_tag=${IMAGE_NAME}:latest" >> "$GITHUB_OUTPUT"
          echo "sha_tag=${IMAGE_NAME}:sha-${SHORT_SHA}" >> "$GITHUB_OUTPUT"
          echo "branch_tag=${IMAGE_NAME}:${BRANCH_TAG}" >> "$GITHUB_OUTPUT"

      - name: Login no Docker Hub
        uses: docker/login-action@v4
        with:
          username: ${{ vars.DOCKERHUB_USERNAME }}
          password: ${{ secrets.DOCKERHUB_TOKEN }}

      - name: Build e push da imagem
        uses: docker/build-push-action@v7
        with:
          context: .
          push: true
          tags: |
            ${{ steps.meta.outputs.latest_tag }}
            ${{ steps.meta.outputs.sha_tag }}
            ${{ steps.meta.outputs.branch_tag }}
          labels: |
            org.opencontainers.image.title=movieflix-analytics
            org.opencontainers.image.source=https://github.com/${{ github.repository }}
            org.opencontainers.image.revision=${{ github.sha }}

      - name: Resumo da publicação
        run: |
          echo "Imagem publicada com sucesso:"
          echo "- ${{ steps.meta.outputs.latest_tag }}"
          echo "- ${{ steps.meta.outputs.sha_tag }}"
          echo "- ${{ steps.meta.outputs.branch_tag }}"
```

---

## 🔐 Configuração do Docker Hub no GitHub

Para a publicação funcionar, configure no repositório GitHub:

### 1. Variável do repositório

Caminho:

```text
Settings → Secrets and variables → Actions → Variables → New repository variable
```

Crie:

- **Name:** `DOCKERHUB_USERNAME`
- **Value:** seu usuário do Docker Hub

### 2. Secret do repositório

Caminho:

```text
Settings → Secrets and variables → Actions → Secrets → New repository secret
```

Crie:

- **Name:** `DOCKERHUB_TOKEN`
- **Value:** token de acesso pessoal do Docker Hub

---

## 🐳 Preparar o Docker Hub

Antes do primeiro push automático:

1. acesse o Docker Hub
2. crie o repositório `movieflix-analytics`
3. defina se ele será público ou privado
4. gere um token com permissão de leitura e escrita

---

## 🏷️ Tags publicadas automaticamente

Quando o job de publicação roda com sucesso, ele envia a imagem com três tags:

- `latest`
- `sha-<7 primeiros caracteres do commit>`
- `<nome-da-branch>`

Exemplo:

```text
seu_usuario/movieflix-analytics:latest
seu_usuario/movieflix-analytics:sha-abc1234
seu_usuario/movieflix-analytics:master
```

---

## ▶️ Como publicar a imagem automaticamente

A publicação acontece automaticamente quando:

- o workflow valida o pipeline com sucesso
- o evento não é `pull_request`
- `DOCKERHUB_USERNAME` está configurado como variável
- `DOCKERHUB_TOKEN` está configurado como secret

Na prática, um `push` em `master` ou `main` já pode disparar a publicação.

---

## ▶️ Como baixar e executar a imagem publicada

Depois da publicação no Docker Hub, a imagem pode ser baixada com:

```bash
docker pull SEU_USUARIO/movieflix-analytics:latest
```

E executada com:

```bash
docker run --rm SEU_USUARIO/movieflix-analytics:latest
```

> Observação: a imagem executa os scripts ETL e analytics, mas para a carga e consultas funcionarem corretamente ela precisa alcançar um PostgreSQL disponível conforme a configuração do projeto.

---

## ✅ Como disparar o workflow

### Pelo GitHub automaticamente

O workflow roda quando houver:

- `push` em `master` ou `main`
- `pull_request` para `master` ou `main`

### Manualmente

Na aba **Actions** do GitHub, selecione o workflow e use **Run workflow**.

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

## 📦 Próximos passos possíveis

Evoluções naturais para este projeto:

- versionar esquema do banco
- separar camadas raw / trusted / analytics
- adicionar testes unitários para os scripts Python
- agendar execução recorrente do pipeline
- publicar também imagens versionadas por release
- adicionar monitoramento e alertas
