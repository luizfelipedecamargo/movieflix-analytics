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
