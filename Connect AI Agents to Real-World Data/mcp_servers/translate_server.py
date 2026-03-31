"""
Translate MCP Server — wraps Google Cloud Translation API.
Critical for APAC multilingual disaster communication.
"""

import asyncio
from mcp.server import Server
from mcp.server.stdio import stdio_server
from mcp.types import Tool, TextContent
import json
import sys
import os

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from config.settings import GOOGLE_TRANSLATE_API_KEY

app = Server("translate-mcp")

# APAC languages relevant to this hackathon
APAC_LANGUAGES = {
    # South Indian (Dravidian family)
    "ta": "Tamil",
    "te": "Telugu",
    "kn": "Kannada",
    "ml": "Malayalam",
    # North Indian
    "hi": "Hindi",
    "mr": "Marathi",
    "gu": "Gujarati",
    "pa": "Punjabi",
    "bn": "Bengali",
    "or": "Odia",
    "as": "Assamese",
    # Southeast Asia
    "id": "Bahasa Indonesia",
    "tl": "Filipino (Tagalog)",
    "th": "Thai",
    "vi": "Vietnamese",
    "ms": "Malay",
    # East Asia
    "zh": "Chinese (Simplified)",
    "ja": "Japanese",
    "ko": "Korean",
    # South Asia
    "ne": "Nepali",
    "si": "Sinhala",
    "my": "Burmese",
}


@app.list_tools()
async def list_tools() -> list[Tool]:
    return [
        Tool(
            name="translate_alert",
            description=(
                "Translate a disaster alert or message into one or more APAC languages "
                "using Google Cloud Translation API. Returns translations for civilian use."
            ),
            inputSchema={
                "type": "object",
                "properties": {
                    "text": {"type": "string", "description": "Text to translate"},
                    "target_languages": {
                        "type": "array",
                        "items": {"type": "string"},
                        "description": "List of language codes (e.g. ['hi', 'ta', 'id'])",
                    },
                    "source_language": {
                        "type": "string",
                        "description": "Source language code (default: en)",
                        "default": "en",
                    },
                },
                "required": ["text", "target_languages"],
            },
        ),
        Tool(
            name="get_supported_languages",
            description="List all supported APAC languages for disaster communication.",
            inputSchema={"type": "object", "properties": {}, "required": []},
        ),
        Tool(
            name="translate_for_region",
            description=(
                "Auto-select and translate a message into the primary language(s) "
                "of a specific APAC country or region."
            ),
            inputSchema={
                "type": "object",
                "properties": {
                    "text": {"type": "string"},
                    "country": {"type": "string", "description": "Country name (e.g. India, Indonesia)"},
                },
                "required": ["text", "country"],
            },
        ),
    ]


@app.call_tool()
async def call_tool(name: str, arguments: dict) -> list[TextContent]:
    if name == "translate_alert":
        return await _translate_alert(arguments)
    elif name == "get_supported_languages":
        return [TextContent(type="text", text=json.dumps(APAC_LANGUAGES, indent=2))]
    elif name == "translate_for_region":
        return await _translate_for_region(arguments)
    return [TextContent(type="text", text="Unknown tool")]


COUNTRY_LANGUAGES = {
    # All 4 Dravidian + major North Indian languages for India
    "india": ["ta", "te", "kn", "ml", "hi", "mr", "gu", "bn"],
    "indonesia": ["id"],
    "philippines": ["tl"],
    "thailand": ["th"],
    "vietnam": ["vi"],
    "malaysia": ["ms"],
    "china": ["zh"],
    "japan": ["ja"],
    "south korea": ["ko"],
    "nepal": ["ne"],
    "sri lanka": ["si"],
    "myanmar": ["my"],
    "bangladesh": ["bn"],
}


async def _call_translate_api(text: str, target_lang: str, source_lang: str = "en") -> str:
    import httpx
    url = "https://translation.googleapis.com/language/translate/v2"
    params = {
        "q": text,
        "target": target_lang,
        "source": source_lang,
        "key": GOOGLE_TRANSLATE_API_KEY,
        "format": "text",
    }
    last_err = None
    for attempt in range(3):
        try:
            async with httpx.AsyncClient(timeout=15.0) as client:
                resp = await client.post(url, params=params)
                resp.raise_for_status()
                data = resp.json()
                return data["data"]["translations"][0]["translatedText"]
        except Exception as e:
            last_err = e
            await asyncio.sleep(1.5 * (attempt + 1))
    raise last_err


async def _translate_alert(args: dict) -> list[TextContent]:
    text = args["text"]
    target_langs = args["target_languages"]
    source = args.get("source_language", "en")

    results = {"original": text, "source_language": source, "translations": {}}

    for lang_code in target_langs:
        lang_name = APAC_LANGUAGES.get(lang_code, lang_code)
        try:
            translated = await _call_translate_api(text, lang_code, source)
            results["translations"][lang_name] = {
                "code": lang_code,
                "text": translated,
            }
        except Exception:
            results["translations"][lang_name] = {"code": lang_code, "text": text}

    return [TextContent(type="text", text=json.dumps(results, indent=2, ensure_ascii=False))]


async def _translate_for_region(args: dict) -> list[TextContent]:
    text = args["text"]
    country = args["country"].lower().strip()
    lang_codes = COUNTRY_LANGUAGES.get(country, ["en"])

    results = {
        "original": text,
        "country": args["country"],
        "languages": [],
    }

    for lang_code in lang_codes:
        lang_name = APAC_LANGUAGES.get(lang_code, lang_code)
        try:
            translated = await _call_translate_api(text, lang_code)
            results["languages"].append({
                "language": lang_name,
                "code": lang_code,
                "text": translated,
            })
        except Exception:
            results["languages"].append({
                "language": lang_name,
                "code": lang_code,
                "text": text,
            })

    return [TextContent(type="text", text=json.dumps(results, indent=2, ensure_ascii=False))]


async def main():
    async with stdio_server() as (read_stream, write_stream):
        await app.run(read_stream, write_stream, app.create_initialization_options())


if __name__ == "__main__":
    asyncio.run(main())
