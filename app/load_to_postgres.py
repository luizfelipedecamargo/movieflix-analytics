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
