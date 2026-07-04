import os
from pydantic_settings import BaseSettings
from pydantic import Field

class Settings(BaseSettings):
    """
    Centralized configuration management for the AI Farmer Assistant app.
    Integrates environment variables and safe defaults.
    """
    # LLM Settings
    gemini_api_key: str = Field(default="mock_key", alias="GEMINI_API_KEY")
    gemini_model_pro: str = Field(default="gemini-2.5-pro", alias="GEMINI_MODEL_PRO")
    gemini_model_flash: str = Field(default="gemini-2.5-flash", alias="GEMINI_MODEL_FLASH")
    
    # App Settings
    log_level: str = Field(default="INFO", alias="LOG_LEVEL")
    app_port: int = Field(default=8501, alias="APP_PORT")
    secret_key: str = Field(default="3dfa82c4f828ef05b452e896472288cd72365287e0298a09995156eeea8ccdb3", alias="SECRET_KEY")
    
    # DB Configuration
    sql_database_url: str = Field(default="sqlite:///farming.db", alias="SQL_DATABASE_URL")
    
    # Third-party Integrations
    maps_api_key: str = Field(default="", alias="MAPS_API_KEY")
    weather_api_key: str = Field(default="", alias="WEATHER_API_KEY")
    market_api_key: str = Field(default="", alias="MARKET_API_KEY")
    
    model_config = {
        "env_file": ".env",
        "env_file_encoding": "utf-8",
        "extra": "ignore"
    }

settings = Settings()
