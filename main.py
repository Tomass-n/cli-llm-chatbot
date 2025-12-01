# Importa anotaciones de tipo para listas y diccionarios
from typing import List, Dict

# Importa la función que llama al modelo LLM desde llm_client.py
from llm_client import call_model


# Define la función principal del programa, no devuelve nada (None)
def main() -> None:
    # Inicializa el historial con un mensaje de sistema que configura
    # el comportamiento del asistente
    messages: List[Dict[str, str]] = [
        {
            "role": "system",
            "content": (
                "Eres un asistente útil. Responde en español de forma clara "
                "y concisa, "
                "salvo que el usuario te pida explícitamente usar otro idioma."
            ),
        }
    ]
    # Muestra mensaje de bienvenida al usuario
    print("CLI LLM Chatbot. Type 'exit' to quit.\n")

    # Inicia un bucle infinito para mantener la conversación activa
    while True:
        # Pide entrada al usuario y elimina espacios en blanco con .strip()
        user_input = input("You: ").strip()

        # Verifica si el usuario quiere salir (escribiendo "exit" o "quit")
        if user_input.lower() in {"exit", "quit"}:
            # Muestra mensaje de despedida
            print("Goodbye!")
            # Sale del bucle while y termina el programa
            break

        # Ignora entradas vacías (si el usuario solo presionó Enter)
        if not user_input:
            # Vuelve al inicio del bucle sin hacer nada
            continue

        # Agrega el mensaje del usuario al historial con formato de OpenAI
        messages.append({"role": "user", "content": user_input})

        # Inicia bloque try para capturar errores al llamar al modelo
        try:
            # Llama a la función que envía el historial al LLM y
            # recibe la respuesta
            assistant_reply = call_model(messages)
        # Captura errores de tipo RuntimeError (falta API key, fallo
        # de conexión, etc.)
        except RuntimeError as exc:
            # Muestra el error al usuario con formato [error]
            print(f"[error] {exc}")
            # Elimina el último mensaje del usuario del historial para no
            # reenviarlo
            messages.pop()
            # Vuelve al inicio del bucle para pedir nueva entrada sin agregar
            # respuesta
            continue

        # Muestra la respuesta del asistente en la consola
        print(f"Assistant: {assistant_reply}\n")
        # Agrega la respuesta del asistente al historial para mantener contexto
        messages.append({"role": "assistant", "content": assistant_reply})


# Verifica que el script se ejecute directamente (no como módulo importado)
if __name__ == "__main__":
    # Ejecuta la función principal para iniciar el chatbot
    main()
