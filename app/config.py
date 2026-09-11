from __future__ import annotations

import os
from pathlib import Path

from dotenv import load_dotenv

BASE_DIR = Path(__file__).resolve().parents[1]
load_dotenv(BASE_DIR / ".env")


class Settings:
    # --- Database -----------------------------------------------------
    # Full connection string takes priority if provided, e.g.:
    #   postgresql+psycopg2://user:password@host:5432/dbname
    DATABASE_URL: str = os.getenv("DATABASE_URL", "")

    # Otherwise assembled from individual parts.
    PG_HOST: str = os.getenv("PG_HOST", "localhost")
    PG_PORT: str = os.getenv("PG_PORT", "5432")
    PG_DB: str = os.getenv("PG_DB", "fake_id_screening")
    PG_USER: str = os.getenv("PG_USER", "postgres")
    PG_PASSWORD: str = os.getenv("PG_PASSWORD", "postgres")

    @property
    def database_url(self) -> str:
        if self.DATABASE_URL:
            return self.DATABASE_URL
        return (
            f"postgresql+psycopg2://{self.PG_USER}:{self.PG_PASSWORD}"
            f"@{self.PG_HOST}:{self.PG_PORT}/{self.PG_DB}"
        )

    # --- Auth -----------------------------------------------------------
    JWT_SECRET: str = os.getenv("JWT_SECRET", "dev-secret-change-me")
    JWT_ALGORITHM: str = "HS256"
    JWT_EXPIRE_MINUTES: int = int(os.getenv("JWT_EXPIRE_MINUTES", "480"))

    # --- Blockchain -------------------------------------------------
    BLOCKCHAIN_RPC_URL: str = os.getenv("BLOCKCHAIN_RPC_URL", "http://127.0.0.1:8545")
    BLOCKCHAIN_PRIVATE_KEY: str | None = os.getenv("BLOCKCHAIN_PRIVATE_KEY")

    # --- Storage ------------------------------------------------------
    UPLOAD_DIR: Path = BASE_DIR / "data" / "uploads"


settings = Settings()
settings.UPLOAD_DIR.mkdir(parents=True, exist_ok=True)
