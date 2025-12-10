"""
Schemas Pydantic para request/response de la API.

Centralizamos todos los modelos aquí para:
1. Reutilizar entre endpoints
2. Documentación automática en /docs
3. Fácil de encontrar y mantener
"""

from typing import Literal

from pydantic import BaseModel, Field


# ========== CHAT SCHEMAS ==========


class Message(BaseModel):
    """
    Un mensaje individual en la conversación.

    Attributes:
        role: Quién envía el mensaje (system/user/assistant)
        content: El texto del mensaje
    """

    role: Literal["system", "user", "assistant"]
    content: str


class ChatRequest(BaseModel):
    """
    Request para el endpoint /chat.

    Attributes:
        messages: Historial de la conversación
        business_id: ID del negocio (para RAG multi-tenant)
    """

    messages: list[Message]
    # business_id será usado cuando implementemos RAG con ChromaDB
    # Cada negocio tendrá su propia colección de documentos
    business_id: str | None = Field(
        default=None,
        description="ID del negocio para buscar en su colección de ChromaDB",
    )


class ChatResponse(BaseModel):
    """
    Response del endpoint /chat.

    Attributes:
        reply: Respuesta generada por el LLM
        sources: Documentos usados como contexto (cuando tengamos RAG)
    """

    reply: str
    # Cuando implementemos RAG, aquí vendrán los chunks usados
    sources: list[str] | None = None


# ========== HEALTH SCHEMAS ==========


class HealthResponse(BaseModel):
    """Response del endpoint /health."""

    status: str = "ok"
    version: str


# ========== EVENT SCHEMAS (para n8n) ==========


class ConversationLog(BaseModel):
    """
    Log de conversación para enviar a n8n.

    Este schema define el formato JSON que recibirá tu webhook de n8n
    para guardar en Sheets/Notion.
    """

    business_id: str
    session_id: str
    messages: list[Message]
    timestamp: str  # ISO format


class LeadCapture(BaseModel):
    """
    Lead capturado durante la conversación.

    Cuando el chatbot detecta interés de compra o el usuario
    deja sus datos, enviamos esto a n8n.
    """

    business_id: str
    session_id: str
    name: str | None = None
    email: str | None = None
    phone: str | None = None
    interest: str  # Qué le interesó al lead
    conversation_summary: str
    timestamp: str
