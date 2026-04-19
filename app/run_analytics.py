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
