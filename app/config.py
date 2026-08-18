from functools import lru_cache

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
      app_name: str = "AI-Driven Game Economy Optimizer"
      database_url: str = "sqlite:///./game_economy.db"
      anomaly_contamination: float = 0.08
      inflation_alert_threshold: float = 0.18
      api_base_url: str = "http://127.0.0.1:8000"

    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8")


@lru_cache
def get_settings() -> Settings:
      return Settings()
  
