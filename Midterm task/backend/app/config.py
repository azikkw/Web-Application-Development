import os
from sqlalchemy.engine import URL

class Settings:
    """All configuration comes from environment variables."""

    def __init__(self) -> None:
        self.database_url = URL.create(
            drivername="postgresql+psycopg2",
            username=os.getenv("POSTGRES_USER", "bounty"),
            password=os.getenv("POSTGRES_PASSWORD", "bounty_secret"),
            host=os.getenv("POSTGRES_HOST", "db"),
            port=int(os.getenv("POSTGRES_PORT", "5432")),
            database=os.getenv("POSTGRES_DB", "bounty"),
        )

settings = Settings()
