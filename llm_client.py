# Importa el módulo os para acceder a variables de entorno del sistema
import os

# Importa el módulo logging para registrar eventos en archivos
import logging

# Importa anotaciones de tipo para listas y diccionarios
from typing import List, Dict

# Importa la función que lee archivos .env
from dotenv import load_dotenv

# Importa el cliente de OpenAI y su excepción base para manejar errores
from openai import OpenAI, OpenAIError

# Lee el archivo .env y carga las variables de entorno (como OPENAI_API_KEY)
load_dotenv()

# Lee la API key desde las variables de entorno
API_KEY = os.getenv("OPENAI_API_KEY")
# Lee el nombre del modelo, usa "gpt-4o-mini" si no está definido
MODEL_NAME = os.getenv("OPENAI_MODEL_NAME", "gpt-4o-mini")

# Crea una instancia del cliente OpenAI usando la API key del entorno
# El _ indica que es una variable privada (solo se usa en este archivo)
_client = OpenAI(api_key=API_KEY)

# Configura el logger de este módulo con nivel INFO
logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)

# Evita añadir múltiples handlers si el módulo se importa varias veces
if not logger.handlers:
    # Crea un handler que escribe logs en el archivo app.log con codificación
    # UTF-8
    file_handler = logging.FileHandler("app.log", encoding="utf-8")
    # Define el formato del log: timestamp - nombre del logger - nivel -
    # mensaje
    formatter = logging.Formatter(
        "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
    )
    # Aplica el formato al handler
    file_handler.setFormatter(formatter)
    # Añade el handler al logger
    logger.addHandler(file_handler)


# Define la función que envía mensajes al LLM y devuelve la respuesta como
# string
def call_model(messages: List[Dict[str, str]]) -> str:
    """
    Envía el historial del chat al LLM y devuelve la respuesta del asistente.
    Lanza RuntimeError si falla la configuración o la llamada a la API.
    """
    # Verifica si existe una API key configurada antes de hacer la petición
    if not _client.api_key:
        # Si no hay API key, lanza un error y detiene la ejecución
        raise RuntimeError("OpenAI API key is not configured.")

    # Registra en el log que se va a llamar al modelo, incluyendo nombre y
    # cantidad de mensajes
    logger.info(
        f"Llamando al modelo {MODEL_NAME} con {len(messages)} mensajes en el historial"  # noqa: E501
    )

    # Inicia un bloque try para capturar errores durante la llamada a la API
    try:
        # Hace la petición al modelo de OpenAI con el historial de mensajes
        response = _client.chat.completions.create(
            # Usa el modelo configurado en la variable de entorno
            model=MODEL_NAME,
            # Envía la lista completa de mensajes (historial del chat)
            messages=messages,
        )
    # Captura cualquier error específico de la API de OpenAI
    except OpenAIError as exc:
        # Registra el error en el log antes de relanzarlo
        logger.error(f"Error en la llamada a la API de OpenAI: {exc}")
        # Convierte el error en RuntimeError con mensaje claro, mantiene
        # error original
        raise RuntimeError(f"LLM request failed: {exc}") from exc

    # Comentario explicativo sobre la estructura de la respuesta de OpenAI
    # La respuesta tiene la estructura: response.choices[0].message.content
    # Inicia bloque try para extraer el texto de la respuesta de forma segura
    try:
        # Accede a la primera respuesta de la lista choices
        # Luego toma el mensaje y finalmente extrae el contenido (texto)
        reply_text = response.choices[0].message.content
        # Registra en el log la longitud de la respuesta recibida
        logger.info(f"Respuesta recibida con {len(reply_text)} caracteres")
        # Devuelve el texto de la respuesta
        return reply_text
    # Captura errores si la estructura de la respuesta no es la esperada
    except (AttributeError, IndexError) as exc:
        # Registra la excepción completa con el traceback en el log
        logger.exception("Formato de respuesta inesperado del LLM")
        # Lanza error indicando formato inesperado, mantiene error original
        raise RuntimeError("Unexpected response format from LLM.") from exc
