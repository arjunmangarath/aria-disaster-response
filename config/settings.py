import json as _json
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


def _fix_json_control_chars(s: str) -> str:
    """
    Escape literal control characters inside JSON string values.
    TOML multi-line strings convert \\n escape sequences into real newlines,
    which then break JSON parsing (control chars are not allowed in strings).
    """
    result = []
    in_string = False
    escape_next = False
    for ch in s:
        if escape_next:
            result.append(ch)
            escape_next = False
        elif ch == "\\":
            result.append(ch)
            escape_next = True
        elif ch == '"':
            in_string = not in_string
            result.append(ch)
        elif in_string and ord(ch) < 0x20:
            if ch == "\n":
                result.append("\\n")
            elif ch == "\r":
                result.append("\\r")
            elif ch == "\t":
                result.append("\\t")
            else:
                result.append(f"\\u{ord(ch):04x}")
        else:
            result.append(ch)
    return "".join(result)


def _write_sa_json(raw: str) -> str:
    """Fix, validate, and write a service account JSON string to a temp file.
    Returns the temp file path, or empty string on failure."""
    if not raw:
        return ""
    try:
        fixed = _fix_json_control_chars(raw)
        _json.loads(fixed)  # validate
        tmp = tempfile.NamedTemporaryFile(
            mode="w", suffix=".json", delete=False, encoding="utf-8"
        )
        tmp.write(fixed)
        tmp.close()
        return tmp.name
    except Exception:
        return ""


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
    f"?connect_timeout=10"
)

# ─── Firebase ────────────────────────────────────────────
FIREBASE_DATABASE_URL = _secret("FIREBASE_DATABASE_URL", "")

_firebase_path = _write_sa_json(_secret("FIREBASE_SERVICE_ACCOUNT_JSON", ""))
FIREBASE_CREDENTIALS_PATH = _firebase_path or _secret(
    "FIREBASE_CREDENTIALS_PATH", "config/firebase_service_account.json"
)

# ─── Google Service Account (Vertex AI on Streamlit Cloud) ──
_gcp_path = _write_sa_json(_secret("GOOGLE_SERVICE_ACCOUNT_JSON", ""))
if _gcp_path:
    os.environ["GOOGLE_APPLICATION_CREDENTIALS"] = _gcp_path

# ─── Push all secrets into os.environ so MCP subprocesses inherit them ───────
# MCP servers run as separate Python subprocesses; they inherit os.environ.
# Without this block, secrets from st.secrets would not reach them.
_env_exports = {
    "GOOGLE_CLOUD_PROJECT":      GOOGLE_CLOUD_PROJECT,
    "GOOGLE_CLOUD_LOCATION":     VERTEX_AI_LOCATION,
    "VERTEX_AI_LOCATION":        VERTEX_AI_LOCATION,
    "GOOGLE_MAPS_API_KEY":       GOOGLE_MAPS_API_KEY,
    "GOOGLE_TRANSLATE_API_KEY":  GOOGLE_TRANSLATE_API_KEY,
    "ALLOYDB_HOST":              ALLOYDB_HOST,
    "ALLOYDB_PORT":              str(ALLOYDB_PORT),
    "ALLOYDB_USER":              ALLOYDB_USER,
    "ALLOYDB_PASSWORD":          ALLOYDB_PASSWORD,
    "ALLOYDB_DATABASE":          ALLOYDB_DATABASE,
    "FIREBASE_DATABASE_URL":     FIREBASE_DATABASE_URL,
    "FIREBASE_CREDENTIALS_PATH": FIREBASE_CREDENTIALS_PATH,
}
for _k, _v in _env_exports.items():
    if _v:
        os.environ[_k] = _v

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
