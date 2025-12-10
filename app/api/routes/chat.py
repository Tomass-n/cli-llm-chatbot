"""
Endpoint de chat - el corazón de tu producto.

Este endpoint:
1. Recibe el historial de conversación del widget
2. (Próximamente) Busca contexto relevante en ChromaDB
3. Llama al LLM con el contexto
4. Retorna la respuesta
"""

import logging

from fastapi import APIRouter, HTTPException

from app.models.schemas import ChatRequest, ChatResponse
from app.services.llm import call_llm

# Logger para este módulo
logger = logging.getLogger(__name__)

# Router con prefijo - todos los endpoints aquí empiezan con /chat
router = APIRouter(prefix="/chat", tags=["Chat"])


@router.post("", response_model=ChatResponse)
def chat(request: ChatRequest) -> ChatResponse:
    """
    Procesa un mensaje del usuario y retorna la respuesta del LLM.

    Este es el endpoint que llamará tu widget de chat.

    Args:
        request: ChatRequest con messages y opcionalmente business_id

    Returns:
        ChatResponse con reply y sources (cuando haya RAG)

    Raises:
        400: Si messages está vacío
        500: Si falla la llamada al LLM

    Example request:
        POST /chat
        {
            "messages": [
                {"role": "user", "content": "¿Cuál es el horario de atención?"}
            ],
            "business_id": "restaurant_123"
        }

    Example response:
        {
            "reply": "Nuestro horario es de 9am a 9pm de lunes a sábado.",
            "sources": ["documento_horarios.txt"]
        }
    """
    # Validación: no aceptamos conversaciones vacías
    if not request.messages:
        logger.warning("Request con messages vacío")
        raise HTTPException(
            status_code=400, detail="La lista 'messages' no puede estar vacía"
        )

    logger.info(
        "POST /chat - %d mensajes, business_id=%s",
        len(request.messages),
        request.business_id,
    )

    try:
        # Convertir Pydantic models a dicts para OpenAI
        messages_dict = [msg.model_dump() for msg in request.messages]

        # TODO: Cuando implementemos RAG:
        # 1. if request.business_id:
        # 2.     chunks = search_chroma(business_id, user_query)
        # 3.     reply = call_llm_with_context(messages_dict, chunks)
        # Por ahora, llamada directa sin RAG

        reply = call_llm(messages_dict)

        logger.info("Respuesta generada: %d caracteres", len(reply))

        return ChatResponse(
            reply=reply,
            sources=None,  # Será poblado cuando tengamos RAG
        )

    except RuntimeError as e:
        logger.error("Error en LLM: %s", e)
        raise HTTPException(
            status_code=500, detail=f"Error al procesar el mensaje: {e}"
        )
