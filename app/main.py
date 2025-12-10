"""
Entry point de la aplicación FastAPI.

Este archivo:
1. Crea la instancia de FastAPI
2. Configura CORS (crítico para que el widget web funcione)
3. Configura logging
4. Registra todos los routers
"""

import logging
from pathlib import Path

from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles

from app.config import get_settings
from app.api.routes import health, chat


# Ruta a la carpeta widget (para servir archivos estáticos)
WIDGET_DIR = Path(__file__).parent.parent / "widget"


# ========== LOGGING ==========
def setup_logging() -> None:
    """Configura logging para toda la aplicación."""
    settings = get_settings()

    logging.basicConfig(
        level=getattr(logging, settings.log_level),
        format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
        handlers=[
            logging.StreamHandler(),  # Logs a consola
            logging.FileHandler("app.log", encoding="utf-8"),  # Logs a archivo
        ],
    )


# ========== LIFESPAN ==========
@asynccontextmanager
async def lifespan(app: FastAPI):
    """
    Maneja el ciclo de vida de la aplicación.

    - startup: se ejecuta al iniciar el servidor
    - shutdown: se ejecuta al apagar el servidor

    Aquí inicializaremos ChromaDB cuando lo implementemos.
    """
    # === STARTUP ===
    setup_logging()
    logger = logging.getLogger(__name__)
    logger.info("🚀 Iniciando Chatbot Soporte API...")

    # TODO: Inicializar ChromaDB aquí
    # chroma_client = chromadb.Client()

    yield  # La aplicación corre aquí

    # === SHUTDOWN ===
    logger.info("👋 Apagando API...")


# ========== CREAR APP ==========
def create_app() -> FastAPI:
    """
    Factory function para crear la aplicación FastAPI.

    Usar una factory function permite:
    1. Crear múltiples instancias (útil para testing)
    2. Configurar diferente para dev/prod/test
    """
    settings = get_settings()

    app = FastAPI(
        title=settings.app_name,
        description=(
            "API para chatbot de soporte 24/7 con RAG.\n\n"
            "## Endpoints principales:\n"
            "- **POST /chat**: Envía mensajes y recibe respuestas del LLM\n"
            "- **GET /health**: Verifica que la API está funcionando\n\n"
            "## Próximamente:\n"
            "- POST /ingest: Subir documentos para RAG\n"
            "- POST /events: Webhooks para n8n"
        ),
        version=settings.app_version,
        lifespan=lifespan,
    )

    # ========== CORS ==========
    # CRÍTICO: Sin esto, el widget web no puede llamar a la API
    # El navegador bloquea requests cross-origin por seguridad
    app.add_middleware(
        CORSMiddleware,
        # Orígenes permitidos (dominios que pueden llamar a tu API)
        # En producción, cambia "*" por tu dominio específico
        allow_origins=settings.cors_origins,
        # Permite enviar cookies/auth headers
        allow_credentials=True,
        # Métodos HTTP permitidos
        allow_methods=["GET", "POST", "PUT", "DELETE"],
        # Headers que el cliente puede enviar
        allow_headers=["*"],
    )

    # ========== REGISTRAR ROUTERS ==========
    # Cada router agrupa endpoints relacionados
    app.include_router(health.router)
    app.include_router(chat.router)

    # ========== ARCHIVOS ESTÁTICOS (Widget) ==========
    # Sirve los archivos CSS y JS del widget
    # Accesibles en: http://localhost:8000/static/widget.js
    app.mount("/static", StaticFiles(directory=WIDGET_DIR), name="static")

    return app


# Crear la instancia de la app
# Uvicorn busca esta variable para correr el servidor
app = create_app()
