"""Configuration management using Pydantic Settings."""

from typing import List
from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    """Application settings with environment variable support."""

    # Database configuration
    db_host: str = "localhost"
    db_port: int = 3306
    db_user: str = "root"
    db_password: str = "password"
    db_name: str

    # API configuration
    excluded_tables: str = ""

    # FastAPI configuration
    title: str = "Dynamic Database API"
    description: str = "Automatically generated REST API for database tables"
    version: str = "1.0.0"

    @property
    def excluded_tables_list(self) -> List[str]:
        """Get excluded tables as a list."""
        if not self.excluded_tables:
            return []
        return [
            table.strip() for table in self.excluded_tables.split(",") if table.strip()
        ]

    class Config:
        env_file = ".env"
        case_sensitive = False


# Global settings instance
settings = Settings()
