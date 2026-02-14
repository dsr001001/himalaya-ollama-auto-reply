# Himalaya Ollama Auto-Reply

An AI-powered auto-reply bot for emails using [Himalaya](https://github.com/soywod/himalaya) and [Ollama](https://ollama.com/).

## Features

- Scans for new emails using Himalaya CLI.
- Generates professional and polite replies using local LLMs (Ollama/Llama 3.2).
- Automatically sends replies back to the sender.
- Configurable target email addresses.

## Requirements

- **Himalaya CLI**: Configured with your email account.
- **Ollama**: Installed and running.
- **Python 3**: For running the auto-reply script.

## Setup

1. **Install Ollama**:
   You can use the provided script:
   ```bash
   ./install_ollama.sh
   ```

2. **Pull the Model**:
   ```bash
   ollama pull llama3.2:3b
   ```

3. **Configure Himalaya**:
   Ensure `himalaya` is configured and you can list your emails:
   ```bash
   himalaya envelope list
   ```

4. **Run the Script**:
   Edit `auto_reply.py` to update the `TARGET_EMAILS` list, then run:
   ```bash
   python3 auto_reply.py
   ```

## Files

- `auto_reply.py`: The main Python script for the bot.
- `install_ollama.sh`: Script to install Ollama on Linux.
- `Modelfile`: Ollama model configuration.
- `check_ollam.txt`: Installation notes/check.
