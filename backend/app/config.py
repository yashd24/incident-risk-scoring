import os

DATABASE_URL = os.environ.get(
    "DATABASE_URL",
    "postgresql+psycopg2://risk:risk@localhost:5432/risk",
)
