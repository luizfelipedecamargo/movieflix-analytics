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
