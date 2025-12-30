import os
from dotenv import load_dotenv

load_dotenv()

# Database Configuration
DATABASE_URL = os.getenv("DATABASE_URL")

# Discord Configuration
DISCORD_TOKEN = os.getenv("DISCORD_TOKEN")
DISCORD_SERVER_ID = os.getenv("DISCORD_SERVER_ID")

# LLM Configuration
LLM_PROVIDER = os.getenv("LLM_PROVIDER", "ollama")
LLM_MODEL = os.getenv("LLM_MODEL", "mistral:7b")
LLM_API_URL = os.getenv("LLM_API_URL", "http://localhost:11434")
