import os
from pathlib import Path

from dotenv import load_dotenv

BASE_DIR = Path(__file__).parent
load_dotenv(BASE_DIR / ".env")

TG_API_ID = int(os.getenv("TG_API_ID", "0"))
TG_API_HASH = os.getenv("TG_API_HASH", "")
DEEPSEEK_API_KEY = os.getenv("DEEPSEEK_API_KEY", "")

# any openai-compatible api works, deepseek by default
MODEL = os.getenv("LLM_MODEL", "deepseek-chat")
MODEL_BASE_URL = os.getenv("LLM_BASE_URL", "https://api.deepseek.com")
MODEL_API_KEY = os.getenv("LLM_API_KEY", DEEPSEEK_API_KEY)

ALLOWED_CHATS = [
    "демо груп",
]

MAX_STEPS = 12
MAX_NOTIFICATIONS_PER_RUN = 2
FIRST_RUN_LIMIT = 100
MAX_MESSAGES_PER_CALL = 100

SKILLS_DIR = BASE_DIR / "skills"
LOGS_DIR = BASE_DIR / "logs"
STATE_FILE = BASE_DIR / "state.json"
SESSION_FILE = BASE_DIR / "uni_agent"
