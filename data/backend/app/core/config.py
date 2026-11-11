import os
from typing import List
from sqlalchemy.engine import URL
from pydantic_settings import BaseSettings
from pydantic import Field, AnyHttpUrl, validator

class Settings(BaseSettings):
    APP_ENV: str = "development"
    APP_DEBUG: bool = True
    API_V1_STR: str = "/api/v1"
    PROJECT_NAME: str = "Cold Chain Monitoring System"
    
    # Database
    DB_HOST: str = "localhost"
    DB_PORT: int = 5432
    DB_USER: str = "postgres"
    DB_PASSWORD: str = ""
    DB_NAME: str = "cold_chain_monitoring_db"
    
    # Security
    SECRET_KEY: str = "default-insecure-secret-key-32-chars-long"
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 480
    
    # CORS
    CORS_ORIGINS: List[str] = ["http://localhost:3000", "http://localhost:5173"]

    # Simulation defaults
    SIMULATION_RANDOM_SEED: int = 20261022
    SIMULATION_INTERVAL_MINUTES: int = 5
    SIMULATION_DEFAULT_SHIPMENT_COUNT: int = 1000
    SIMULATION_DEFAULT_CONTAINER_COUNT: int = 300

    @property
    def database_url(self) -> str:
        # URL.create safely handles reserved characters (including @ and /) in passwords.
        return URL.create(
            "postgresql+psycopg2",
            username=self.DB_USER,
            password=self.DB_PASSWORD or None,
            host=self.DB_HOST,
            port=self.DB_PORT,
            database=self.DB_NAME,
        )

    class Config:
        env_file = ".env"
        extra = "ignore"

settings = Settings()
