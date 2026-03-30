import os
from urllib.parse import quote_plus
from dotenv import load_dotenv

load_dotenv()

# ─── Google Cloud ────────────────────────────────────────
GOOGLE_CLOUD_PROJECT = os.getenv("GOOGLE_CLOUD_PROJECT", "")
VERTEX_AI_LOCATION = os.getenv("VERTEX_AI_LOCATION", "us-central1")
GEMINI_MODEL = "gemini-2.5-flash"

# ─── Google Maps ─────────────────────────────────────────
GOOGLE_MAPS_API_KEY = os.getenv("GOOGLE_MAPS_API_KEY", "")

# ─── Google Translate ────────────────────────────────────
GOOGLE_TRANSLATE_API_KEY = os.getenv("GOOGLE_TRANSLATE_API_KEY", "")

# ─── AlloyDB ─────────────────────────────────────────────
ALLOYDB_HOST = os.getenv("ALLOYDB_HOST", "localhost")
ALLOYDB_PORT = int(os.getenv("ALLOYDB_PORT", "5432"))
ALLOYDB_USER = os.getenv("ALLOYDB_USER", "postgres")
ALLOYDB_PASSWORD = os.getenv("ALLOYDB_PASSWORD", "")
ALLOYDB_DATABASE = os.getenv("ALLOYDB_DATABASE", "aria_db")

ALLOYDB_DSN = (
    f"postgresql://{ALLOYDB_USER}:{quote_plus(ALLOYDB_PASSWORD)}"
    f"@{ALLOYDB_HOST}:{ALLOYDB_PORT}/{ALLOYDB_DATABASE}"
)

# ─── Firebase ────────────────────────────────────────────
FIREBASE_CREDENTIALS_PATH = os.getenv(
    "FIREBASE_CREDENTIALS_PATH", "config/firebase_service_account.json"
)
FIREBASE_DATABASE_URL = os.getenv("FIREBASE_DATABASE_URL", "")

# ─── External APIs ───────────────────────────────────────
GDACS_API_URL = os.getenv(
    "GDACS_API_URL",
    "https://www.gdacs.org/gdacsapi/api/events/geteventlist/SEARCH"
)
OPENMETEO_API_URL = os.getenv(
    "OPENMETEO_API_URL",
    "https://api.open-meteo.com/v1/forecast"
)

# ─── MCP Server ports ───────────────────────────────────
WEATHER_MCP_PORT = 8001
ALERTS_MCP_PORT = 8002
SHELTER_MCP_PORT = 8003
CONTACTS_MCP_PORT = 8004
TRANSLATE_MCP_PORT = 8005
NOTIFY_MCP_PORT = 8006
