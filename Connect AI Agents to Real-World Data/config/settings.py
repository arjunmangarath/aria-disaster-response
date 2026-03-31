import os
import tempfile
from urllib.parse import quote_plus
from dotenv import load_dotenv

load_dotenv()


def _secret(key: str, default: str = "") -> str:
    """Read from st.secrets (Streamlit Cloud) or os.environ (local)."""
    try:
        import streamlit as st
        return st.secrets.get(key, os.getenv(key, default))
    except Exception:
        return os.getenv(key, default)


# ─── Google Cloud ────────────────────────────────────────
GOOGLE_CLOUD_PROJECT = _secret("GOOGLE_CLOUD_PROJECT", "aria-disaster-response")
VERTEX_AI_LOCATION   = _secret("VERTEX_AI_LOCATION", "us-central1")
GEMINI_MODEL         = "gemini-2.5-flash"

# ─── Google Maps ─────────────────────────────────────────
GOOGLE_MAPS_API_KEY = _secret("GOOGLE_MAPS_API_KEY", "")

# ─── Google Translate ────────────────────────────────────
GOOGLE_TRANSLATE_API_KEY = _secret("GOOGLE_TRANSLATE_API_KEY", "")

# ─── AlloyDB ─────────────────────────────────────────────
ALLOYDB_HOST     = _secret("ALLOYDB_HOST", "localhost")
ALLOYDB_PORT     = int(_secret("ALLOYDB_PORT", "5432"))
ALLOYDB_USER     = _secret("ALLOYDB_USER", "postgres")
ALLOYDB_PASSWORD = _secret("ALLOYDB_PASSWORD", "")
ALLOYDB_DATABASE = _secret("ALLOYDB_DATABASE", "aria_db")

ALLOYDB_DSN = (
    f"postgresql://{ALLOYDB_USER}:{quote_plus(ALLOYDB_PASSWORD)}"
    f"@{ALLOYDB_HOST}:{ALLOYDB_PORT}/{ALLOYDB_DATABASE}"
)

# ─── Firebase ────────────────────────────────────────────
FIREBASE_DATABASE_URL = _secret("FIREBASE_DATABASE_URL", "")

# Write Firebase service account JSON from secret to a temp file
_firebase_json = _secret("FIREBASE_SERVICE_ACCOUNT_JSON", "")
if _firebase_json:
    try:
        _tmp = tempfile.NamedTemporaryFile(
            mode="w", suffix=".json", delete=False, encoding="utf-8"
        )
        _tmp.write(_firebase_json)
        _tmp.close()
        FIREBASE_CREDENTIALS_PATH = _tmp.name
    except Exception:
        FIREBASE_CREDENTIALS_PATH = _secret(
            "FIREBASE_CREDENTIALS_PATH", "config/firebase_service_account.json"
        )
else:
    FIREBASE_CREDENTIALS_PATH = _secret(
        "FIREBASE_CREDENTIALS_PATH", "config/firebase_service_account.json"
    )

# ─── Google Service Account (Vertex AI on Streamlit Cloud) ──
_gcp_sa_json = _secret("GOOGLE_SERVICE_ACCOUNT_JSON", "")
if _gcp_sa_json:
    try:
        _sa_tmp = tempfile.NamedTemporaryFile(
            mode="w", suffix=".json", delete=False, encoding="utf-8"
        )
        _sa_tmp.write(_gcp_sa_json)
        _sa_tmp.close()
        os.environ["GOOGLE_APPLICATION_CREDENTIALS"] = _sa_tmp.name
    except Exception:
        pass

# ─── External APIs ───────────────────────────────────────
GDACS_API_URL = _secret(
    "GDACS_API_URL",
    "https://www.gdacs.org/gdacsapi/api/events/geteventlist/SEARCH",
)
OPENMETEO_API_URL = _secret(
    "OPENMETEO_API_URL",
    "https://api.open-meteo.com/v1/forecast",
)

# ─── MCP Server ports ───────────────────────────────────
WEATHER_MCP_PORT   = 8001
ALERTS_MCP_PORT    = 8002
SHELTER_MCP_PORT   = 8003
CONTACTS_MCP_PORT  = 8004
TRANSLATE_MCP_PORT = 8005
NOTIFY_MCP_PORT    = 8006
