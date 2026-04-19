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
