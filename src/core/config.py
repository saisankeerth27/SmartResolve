import os
from pathlib import Path

from dotenv import load_dotenv

BASE_DIR = Path(__file__).resolve().parent.parent.parent

# Load .env from the project root (ignored by git). Real env vars take precedence.
load_dotenv(BASE_DIR / ".env")

PORT = int(os.getenv("PORT", "8000"))
HOST = "0.0.0.0"

GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")
GEMINI_CONFIGURED = GEMINI_API_KEY is not None and len(GEMINI_API_KEY) > 0

DATABASE_DIR = BASE_DIR / "data"
DATABASE_PATH = DATABASE_DIR / "smartresolve.db"

FRONTEND_DIST = BASE_DIR / "frontend" / "dist"

SERVICE_NAME = "SmartResolve"
SERVICE_SUBTITLE = "Telecom Operations Resolution Assistant"
