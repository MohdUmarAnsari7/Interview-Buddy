import os
from pathlib import Path
from dotenv import load_dotenv

# Load environment variables from .env file
env_path = Path(__file__).resolve().parent / ".env"
load_dotenv(dotenv_path=env_path)

# ============================================================
# AI configuration
# ============================================================

# Working API
AI_API_KEY = os.getenv("AI_API_KEY", "")
AI_BASE_URL = os.getenv(
    "AI_BASE_URL", "https://integrate.api.nvidia.com/v1"
)
AI_MODEL = os.getenv(
    "AI_MODEL", "nvidia/nemotron-3.5-lightning-30b-a3b"
)

# ============================================================
# ollam Model Config
#AI_API_KEY = ""
#AI_BASE_URL = (
#    "http://localhost:11434/v1"
#)
#
#AI_MODEL = "frob/qwen3.5-instruct:4b"
# ============================================================



# ============================================================
# Whisper configuration
# ============================================================

RATE = 16000
CHUNK_SECONDS = 2

MODEL_SIZE = "base.en"
DEVICE = "cpu"
COMPUTE = "int8"