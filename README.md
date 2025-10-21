# Gemini_beta_bot

Pequeño bot de Telegram de ejemplo.

Requisitos

- Python 3.11+ (el proyecto usa un venv)

Instalación

1. Crear y activar un virtualenv en el directorio del proyecto (Windows PowerShell):

```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
```

2. Instalar dependencias:

```powershell
pip install -r requirements.txt
```

Configuración del token

- Exporta tu token de BotFather a la variable de entorno `TELEGRAM_BOT_TOKEN` antes de ejecutar el bot, por ejemplo en PowerShell:

```powershell
$env:TELEGRAM_BOT_TOKEN = "<tu_token_aqui>"
```

- Alternativamente crea un archivo `.env` con:

```
TELEGRAM_BOT_TOKEN=<tu_token_aqui>
```

Integración con Gemini

- Define las variables de entorno `GEMINI_API_KEY` y `GEMINI_API_URL` para que el bot reenvíe los mensajes a tu endpoint de Gemini y use la respuesta como respuesta en Telegram.

Ejemplo `.env`:

```
TELEGRAM_BOT_TOKEN=<tu_token_aqui>
GEMINI_API_KEY=<tu_gemini_api_key>
GEMINI_API_URL=https://api.ejemplo.com/v1/gemini
```

El bot intentará usar Gemini si ambas variables están presentes; si no, volverá al comportamiento local (eco simple).

Ejecución

```powershell
C:/Users/tu_usuario/path/to/.venv/Scripts/python.exe bot.py
```

Notas

- El token no debe estar en el repositorio. El código usa la variable de entorno y mantiene un fallback solo por compatibilidad.
- Comprueba `bot.out.log` y `bot.err.log` si ejecutas en background.
