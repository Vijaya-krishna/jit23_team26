import os
from pydantic_settings import BaseSettings, SettingsConfigDict
from pydantic import Field

class Settings(BaseSettings):
    """
    Application settings loaded from environment variables or .env file.
    Follows SOLID configuration patterns.
    """
    # Database Settings
    DATABASE_URL: str = Field(
        default="sqlite:///./simulation.db",
        description="Database connection URL. Defaults to local SQLite file database."
    )

    # JWT Authentication Settings
    JWT_SECRET_KEY: str = Field(
        default="super_secret_energy_aware_scheduler_key_12345",
        description="Secret key used for signing JWT tokens."
    )
    JWT_ALGORITHM: str = Field(
        default="HS256",
        description="Algorithm used for signing JWT tokens."
    )
    ACCESS_TOKEN_EXPIRE_MINUTES: int = Field(
        default=60,
        description="Token validity duration in minutes."
    )

    # Initial Admin Credentials (for database seed)
    DEFAULT_ADMIN_USERNAME: str = Field(
        default="admin",
        description="Default administrator username."
    )
    DEFAULT_ADMIN_EMAIL: str = Field(
        default="admin@datacenter.com",
        description="Default administrator email."
    )
    DEFAULT_ADMIN_PASSWORD: str = Field(
        default="AdminPass123!",
        description="Default administrator password."
    )

    # Server Settings
    HOST: str = "0.0.0.0"
    PORT: int = 8000

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore"
    )

# Instantiate settings singleton
settings = Settings()
