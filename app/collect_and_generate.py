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
