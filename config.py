"""
Configuration management using Pydantic Settings
"""

from pydantic_settings import BaseSettings
from functools import lru_cache


class Settings(BaseSettings):
    """Application settings"""
    
    # API Configuration
    api_host: str = "0.0.0.0"
    api_port: int = 8000
    debug: bool = True
    
    # API Keys
    openai_api_key: str = ""
    anthropic_api_key: str = ""
    gemini_api_key: str = ""
    groq_api_key: str = ""
    huggingface_api_key: str = ""
    
    # Authentication
    api_key_secret: str = "dev_secret_key"
    jwt_secret: str = "dev_jwt_secret"
    
    # LLM Configuration
    default_llm_provider: str = "openai"
    openai_model: str = "gpt-4o"
    anthropic_model: str = "claude-3-opus-20240229"
    gemini_model: str = "gemini-1.5-pro"
    groq_model: str = "llama-3.3-70b-versatile"
    llm_temperature: float = 0.7
    llm_max_tokens: int = 2000
    
    # Qdrant Configuration
    qdrant_host: str = "localhost"
    qdrant_port: int = 6333
    qdrant_api_key: str = ""
    qdrant_use_https: bool = False
    
    # Collection Names
    chandas_collection: str = "chandas_patterns"
    shlokas_collection: str = "example_shlokas"
    grammar_collection: str = "grammar_rules"
    branding_collection: str = "branding_vocab"
    
    # Logging
    log_level: str = "INFO"
    log_format: str = "json"
    
    # CORS
    allowed_origins: str = "*"
    
    class Config:
        env_file = ".env"
        case_sensitive = False


@lru_cache()
def get_settings() -> Settings:
    """Get cached settings instance"""
    return Settings()
