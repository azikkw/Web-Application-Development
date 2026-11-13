import os
from sqlalchemy.engine import URL

class Settings:
    def __init__(self) -> None:
        self.database_url = URL.create(
            drivername="postgresql+psycopg2",
            username=os.getenv("POSTGRES_USER", "football"),
            password=os.getenv("POSTGRES_PASSWORD", "football_secret"),
            host=os.getenv("POSTGRES_HOST", "db"),
            port=int(os.getenv("POSTGRES_PORT", "5432")),
            database=os.getenv("POSTGRES_DB", "football"),
        )

settings = Settings()
