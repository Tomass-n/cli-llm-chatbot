# Importa el módulo logging para rastrear la actividad y errores de la API
import logging
from typing import List, Literal

# Importa los componentes principales de FastAPI
from fastapi import FastAPI, HTTPException

# Importa Pydantic para validación de datos
from pydantic import BaseModel

# Importa la función del cliente LLM que llama a la API de OpenAI
from llm_client import call_model

# ========== CONFIGURACIÓN DE LOGGING ==========
# Configura un logger a nivel de módulo para rastrear peticiones y errores
# __name__ asegura que el logger se nombre según este módulo (app)
logger = logging.getLogger(__name__)


# ========== MODELOS PYDANTIC ==========
# Estos modelos definen y validan la estructura de los datos de petición/respuesta # noqa: E501


class Message(BaseModel):
    """Representa un único mensaje en la conversación."""

    # role: debe ser exactamente uno de estos tres valores
    # Literal asegura seguridad de tipos y validación
    role: Literal["system", "user", "assistant"]

    # content: el texto real del mensaje
    content: str


class ChatRequest(BaseModel):
    """Cuerpo de la petición para el endpoint /chat."""

    # messages: lista de objetos Message que representan el historial de conversación # noqa: E501
    # FastAPI valida automáticamente esta estructura desde el JSON entrante
    messages: List[Message]


class ChatResponse(BaseModel):
    """Cuerpo de la respuesta para el endpoint /chat."""

    # reply: el texto de respuesta del asistente
    reply: str


class ColdEmailRequest(BaseModel):
    """Cuerpo de la petición para generar un cold email para un freelancer."""

    # freelancer_profile: quién eres y qué haces
    freelancer_profile: str

    # client_business: de qué trata el negocio del cliente
    client_business: str

    # client_pain_point: problema principal que crees que tienen
    client_pain_point: str

    # offer: qué ofreces para resolver ese problema
    offer: str

    # goal: qué acción quieres que tomen (ej. llamar, responder)
    goal: str

    # tone: estilo de escritura del email (casual, profesional o amigable)
    # Por defecto es "professional"
    tone: Literal["casual", "professional", "friendly"] = "professional"

    # language: idioma del email (Inglés o Español)
    # Por defecto es "en" (Inglés)
    language: Literal["en", "es"] = "en"


class ColdEmailResponse(BaseModel):
    """Cuerpo de la respuesta para el endpoint de cold email."""

    # email: texto completo del cold email (asunto + cuerpo o solo cuerpo)
    email: str


# ========== APLICACIÓN FASTAPI ==========
# Crea la instancia de la aplicación FastAPI
app = FastAPI(
    # title: aparece en la documentación auto-generada en /docs
    title="CLI LLM Chatbot API",
    # description: explica qué hace esta API
    description="API wrapper around llm_client.call_model",
    # version: útil para versionado de API y seguimiento
    version="0.1.0",
)


# ========== ENDPOINT DE HEALTH CHECK ==========
@app.get("/health")
def health_check():
    """
    Endpoint de verificación de salud para comprobar que la API está funcionando. # noqa: E501

    Usado por balanceadores de carga, sistemas de monitoreo, etc.
    Siempre devuelve status "ok" con HTTP 200.
    """
    return {"status": "ok"}


# ========== ENDPOINT DE CHAT ==========
@app.post("/chat", response_model=ChatResponse)
def chat(request: ChatRequest):
    """
    Endpoint principal que procesa mensajes y devuelve la respuesta del LLM.

    Args:
        request: Objeto ChatRequest que contiene la lista de mensajes.
                 FastAPI valida automáticamente el JSON entrante.

    Returns:
        ChatResponse: objeto con el campo "reply" que contiene
        la respuesta del LLM.

    Raises:
        HTTPException 400: si la lista de mensajes está vacía (petición incorrecta). # noqa: E501
        HTTPException 500: si call_model falla (error interno del servidor).
    """
    # Valida que la lista de mensajes no esté vacía
    # Lista vacía = petición incorrecta del cliente
    if not request.messages:
        logger.warning("Se recibió petición /chat con lista de mensajes vacía")
        raise HTTPException(
            status_code=400, detail="The 'messages' list cannot be empty."
        )

    # Registra la petición entrante con el conteo de mensajes
    # Esto ayuda a rastrear el uso de la API y depurar problemas
    logger.info("Se recibió petición /chat con %d mensajes", len(request.messages))  # noqa: E501

    # Intenta procesar la petición y llamar al LLM
    try:
        # Convierte los objetos Pydantic Message a dicts de Python simples
        # call_model espera List[Dict[str, str]]
        messages_dict = [msg.model_dump() for msg in request.messages]

        # Llama a la función del cliente LLM
        # Esto hace la llamada real a la API de OpenAI
        reply = call_model(messages_dict)

        # Registra la generación exitosa de la respuesta con el conteo de caracteres # noqa: E501
        # Útil para monitorear tamaños de respuesta y uso de la API
        logger.info("Respuesta del LLM generada con %d caracteres", len(reply))

        # Devuelve la respuesta envuelta en el modelo ChatResponse
        # FastAPI convierte esto a JSON: {"reply": "..."}
        return ChatResponse(reply=reply)

    # Captura RuntimeError de call_model (ej. falta API key, fallo de API)
    except RuntimeError as e:
        # Registra el error con detalles para depuración
        logger.error("Llamada al LLM falló: %s", e)

        # Devuelve HTTP 500 Internal Server Error
        # Esto indica un problema del lado del servidor
        raise HTTPException(status_code=500, detail=str(e))


# ========== ENDPOINT DE COLD EMAIL ==========
@app.post("/cold-email", response_model=ColdEmailResponse)
def generate_cold_email(request: ColdEmailRequest):
    """
    Endpoint que genera un cold email para freelancers para contactar clientes.

    Args:
        request: Objeto ColdEmailRequest con info del freelancer,
        info del cliente,
                 y parámetros del email (tono, idioma, etc.).

    Returns:
        ColdEmailResponse: objeto con el campo "email" que contiene el
                           texto del cold email generado.

    Raises:
        HTTPException 500: si call_model falla (error interno del servidor).
    """
    # Registra la petición entrante con los parámetros de tono e idioma
    # Esto ayuda a rastrear qué tipo de emails se están generando
    logger.info(
        "Se recibió petición /cold-email con tone=%s, language=%s",
        request.tone,
        request.language,
    )

    # Construye el prompt del sistema para instruir al LLM sobre su rol
    # Esto establece el contexto para que el modelo actúe como experto en cold emails # noqa: E501
    system_prompt = (
        "Eres un copywriter experto que escribe cold emails efectivos "
        "para freelancers que quieren conseguir nuevos clientes. "
        "Escribe emails claros, concisos que suenen humanos y respetuosos. "
        "Siempre adáptate al idioma y tono solicitados. "
        "No inventes datos sobre el freelancer o el cliente."
    )

    # Construye el prompt del usuario con todos los detalles de la petición
    # Esto le da al LLM toda la información que necesita para escribir el email
    user_prompt = (
        f"Perfil del freelancer: {request.freelancer_profile}\n"
        f"Negocio del cliente: {request.client_business}\n"
        f"Punto de dolor del cliente: {request.client_pain_point}\n"
        f"Oferta: {request.offer}\n"
        f"Objetivo del email: {request.goal}\n"
        f"Tono: {request.tone}\n"
        f"Idioma: {request.language}\n\n"
        "Escribe un cold email que el freelancer pueda enviar a este cliente. "
        "Si el idioma es 'en', escribe en Inglés. Si es 'es', escribe en Español. "  # noqa: E501
        "El email debe estar listo para copiar y pegar."
    )

    # Prepara la lista de mensajes para call_model
    # Formato: [{"role": "system", "content": "..."}, {"role": "user", "content": "..."}] # noqa: E501
    messages = [
        {"role": "system", "content": system_prompt},
        {"role": "user", "content": user_prompt},
    ]

    # Intenta generar el cold email llamando al LLM
    try:
        # Llama a la función del cliente LLM con los mensajes preparados
        # Esto hace la llamada real a la API de OpenAI
        reply = call_model(messages)

        # Registra la generación exitosa del email con el conteo de caracteres
        # Útil para monitorear longitudes de emails y uso de la API
        logger.info("Cold email generado con %d caracteres", len(reply))

        # Devuelve la respuesta envuelta en el modelo ColdEmailResponse
        # FastAPI convierte esto a JSON: {"email": "..."}
        return ColdEmailResponse(email=reply)

    # Captura RuntimeError de call_model (ej. falta API key, fallo de API)
    except RuntimeError as e:
        # Registra el error con detalles para depuración
        logger.error("Generación de cold email falló: %s", e)

        # Devuelve HTTP 500 Internal Server Error
        # Esto indica un problema del lado del servidor
        raise HTTPException(status_code=500, detail=str(e))
