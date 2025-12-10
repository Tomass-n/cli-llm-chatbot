"""
Configuración centralizada de la aplicación.

Usa pydantic-settings para cargar variables de entorno de forma tipada.
Esto es mejor que usar os.getenv() disperso por el código porque:
1. Validación automática de tipos
2. Valores por defecto documentados en un solo lugar
3. Fácil de testear (puedes crear Settings con valores custom)
"""

from functools import lru_cache

from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    """
    Configuración de la aplicación cargada desde variables de entorno.

    Attributes:
        openai_api_key: Tu API key de OpenAI (requerida)
        openai_model_name: Modelo a usar (default: gpt-4o-mini)
        log_level: Nivel de logging (default: INFO)
        cors_origins: Orígenes permitidos para CORS (default: todos)
    """

    # OpenAI
    openai_api_key: str
    openai_model_name: str = "gpt-4o-mini"

    # Logging
    log_level: str = "INFO"

    # CORS - para el widget web
    # En producción, cambia esto a tu dominio específico
    cors_origins: list[str] = ["*"]

    # App info
    app_name: str = "Chatbot Soporte API"
    app_version: str = "0.1.0"

    class Config:
        # Busca el archivo .env en el directorio raíz del proyecto
        env_file = ".env"
        # Case insensitive: OPENAI_API_KEY = openai_api_key
        case_sensitive = False


@lru_cache
def get_settings() -> Settings:
    """
    Retorna la configuración cacheada (singleton).

    Usamos lru_cache para que solo se cargue una vez,
    no en cada request.
    """
    return Settings()
