# CLI LLM Chatbot

A simple command-line chatbot powered by OpenAI's API. This project demonstrates how to build an interactive chat interface in the terminal with conversation history, error handling, and logging.

## Features

- **Interactive CLI**: Clean terminal interface with `You:` / `Assistant:` prompts
- **Conversation History**: Maintains full message context across the session
- **System Prompt**: Pre-configured to respond in Spanish by default
- **Error Handling**: Graceful error management with user-friendly messages
- **Logging**: Automatic logging of API calls and responses to `app.log`
- **Configurable Model**: Easily switch between OpenAI models via environment variables

## Requirements

- Python 3.11+
- OpenAI API key ([Get one here](https://platform.openai.com/api-keys))

## Installation

1. **Clone or download this project**

2. **Create a virtual environment**
   ```powershell
   python -m venv .venv