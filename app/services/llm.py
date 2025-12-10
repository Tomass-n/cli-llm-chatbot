"""
Servicio para interactuar con el LLM (OpenAI).

Este módulo encapsula toda la lógica de llamadas a OpenAI.
Separar esto en un servicio permite:
1. Cambiar de proveedor fácilmente (OpenAI → Anthropic → local)
2. Añadir retry logic, rate limiting, etc.
3. Testear con mocks sin tocar el resto del código
"""

import logging

from openai import OpenAI, OpenAIError

from app.config import get_settings

# Logger para este módulo
logger = logging.getLogger(__name__)

# Cliente OpenAI (se inicializa lazy)
_client: OpenAI | None = None


def get_openai_client() -> OpenAI:
    """
    Retorna el cliente OpenAI (singleton).

    Lo creamos lazy (cuando se necesita) para evitar errores
    al importar el módulo si no hay API key configurada.
    """
    global _client
    if _client is None:
        settings = get_settings()
        _client = OpenAI(api_key=settings.openai_api_key)
    return _client


def call_llm(messages: list[dict[str, str]]) -> str:
    """
    Envía mensajes al LLM y retorna la respuesta.

    Args:
        messages: Lista de mensajes en formato OpenAI
                  [{"role": "user", "content": "hola"}]

    Returns:
        str: Texto de respuesta del LLM

    Raises:
        RuntimeError: Si falla la llamada a la API

    Example:
        >>> response = call_llm([
        ...     {"role": "system", "content": "Eres un asistente útil"},
        ...     {"role": "user", "content": "¿Qué es Python?"}
        ... ])
        >>> print(response)
        "Python es un lenguaje de programación..."
    """
    settings = get_settings()
    client = get_openai_client()

    logger.info(
        "Llamando a %s con %d mensajes",
        settings.openai_model_name,
        len(messages),  # noqa: E501
    )

    try:
        response = client.chat.completions.create(
            model=settings.openai_model_name,
            messages=messages,
        )

        reply = response.choices[0].message.content
        logger.info("Respuesta recibida: %d caracteres", len(reply))
        return reply

    except OpenAIError as e:
        logger.error("Error de OpenAI: %s", e)
        raise RuntimeError(f"LLM request failed: {e}") from e
    except (AttributeError, IndexError) as e:
        logger.exception("Formato de respuesta inesperado")
        raise RuntimeError("Unexpected response format from LLM") from e


def call_llm_with_context(
    messages: list[dict[str, str]], context_chunks: list[str] | None = None
) -> str:
    """
    Llama al LLM inyectando contexto RAG si hay chunks disponibles.

    Esta función será la que uses cuando implementemos RAG:
    1. Busca chunks relevantes en ChromaDB
    2. Los inyecta en el system prompt
    3. Llama al LLM

    Args:
        messages: Historial de conversación
        context_chunks: Chunks de documentos relevantes (del RAG)

    Returns:
        str: Respuesta del LLM
    """
    if not context_chunks:
        # Sin RAG, llamada normal
        return call_llm(messages)

    # Construir system prompt con contexto
    context_text = "\n\n".join(context_chunks)
    rag_system_prompt = {
        "role": "system",
        "content": (
            "Usa el siguiente contexto para responder al usuario. "
            "Si la información no está en el contexto, dilo claramente.\n\n"
            f"CONTEXTO:\n{context_text}"
        ),
    }

    # Inyectar el contexto como primer mensaje
    messages_with_context = [rag_system_prompt] + messages

    return call_llm(messages_with_context)
