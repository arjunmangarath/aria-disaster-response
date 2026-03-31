"""
Emergency Contacts MCP Server — queries AlloyDB AI for region + disaster-specific contacts.
Uses vector similarity to match the best contacts for the situation.
"""

import asyncio
import asyncpg
from mcp.server import Server
from mcp.server.stdio import stdio_server
from mcp.types import Tool, TextContent
import json
import sys
import os

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from config.settings import ALLOYDB_DSN, GOOGLE_CLOUD_PROJECT, VERTEX_AI_LOCATION

app = Server("contacts-mcp")


async def _get_query_embedding(query: str) -> list[float]:
    loop = asyncio.get_event_loop()

    def _embed():
        from vertexai.language_models import TextEmbeddingModel
        from google.cloud import aiplatform
        aiplatform.init(project=GOOGLE_CLOUD_PROJECT, location=VERTEX_AI_LOCATION)
        model = TextEmbeddingModel.from_pretrained("text-embedding-004")
        return model.get_embeddings([query])[0].values

    return await asyncio.wait_for(loop.run_in_executor(None, _embed), timeout=30.0)


@app.list_tools()
async def list_tools() -> list[Tool]:
    return [
        Tool(
            name="get_emergency_contacts",
            description=(
                "Get relevant emergency contacts for a specific disaster type and region. "
                "Uses AlloyDB AI vector search to find the most relevant agencies. "
                "Returns agency name, phone, email, and role (command/responder/civilian)."
            ),
            inputSchema={
                "type": "object",
                "properties": {
                    "region": {"type": "string", "description": "Affected region or city"},
                    "country": {"type": "string", "description": "Affected country"},
                    "disaster_type": {"type": "string", "description": "Type of disaster"},
                    "role": {
                        "type": "string",
                        "description": "Stakeholder role: command / responder / civilian / all",
                        "enum": ["command", "responder", "civilian", "all"],
                        "default": "all",
                    },
                    "limit": {"type": "integer", "default": 6},
                },
                "required": ["region", "country", "disaster_type"],
            },
        ),
        Tool(
            name="get_global_emergency_numbers",
            description="Get universal emergency numbers (ambulance, police, fire) for a country.",
            inputSchema={
                "type": "object",
                "properties": {
                    "country": {"type": "string", "description": "Country name"},
                },
                "required": ["country"],
            },
        ),
    ]


@app.call_tool()
async def call_tool(name: str, arguments: dict) -> list[TextContent]:
    if name == "get_emergency_contacts":
        return await _get_emergency_contacts(arguments)
    elif name == "get_global_emergency_numbers":
        return await _get_global_emergency_numbers(arguments)
    return [TextContent(type="text", text="Unknown tool")]


# Role mapping — which agencies serve which roles
ROLE_KEYWORDS = {
    "command": ["NDRF", "BNPB", "NDRRMC", "DDPM", "DEOC", "disaster management", "emergency operations"],
    "responder": ["ambulance", "fire", "rescue", "hospital", "medical", "police", "Red Cross"],
    "civilian": ["helpline", "ambulance", "police", "Red Cross", "UNHCR", "relief"],
}


def _assign_roles(agency: str, description: str) -> list[str]:
    text = (agency + " " + description).lower()
    roles = []
    for role, keywords in ROLE_KEYWORDS.items():
        if any(kw.lower() in text for kw in keywords):
            roles.append(role)
    return roles if roles else ["all"]


async def _get_emergency_contacts(args: dict) -> list[TextContent]:
    region = args["region"]
    country = args["country"]
    disaster_type = args["disaster_type"]
    role = args.get("role", "all")
    limit = args.get("limit", 6)

    try:
        query_text = (
            f"emergency contacts for {disaster_type} in {region}, {country} "
            f"disaster response agencies helpline"
        )
        embedding = await _get_query_embedding(query_text)
        embedding_str = "[" + ",".join(str(v) for v in embedding) + "]"

        conn = await asyncio.wait_for(asyncpg.connect(ALLOYDB_DSN), timeout=15.0)
        try:
            sql = f"""
                SELECT agency, region, country, disaster_types,
                       phone, email, description,
                       1 - (embedding <=> '{embedding_str}'::vector) AS similarity
                FROM emergency_contacts
                WHERE (
                    LOWER(country) = LOWER('{country}')
                    OR LOWER(region) = LOWER('{region}')
                    OR LOWER(country) = 'global'
                )
                ORDER BY embedding <=> '{embedding_str}'::vector
                LIMIT {limit * 2}
            """
            rows = await conn.fetch(sql)

            contacts = []
            for row in rows:
                assigned_roles = _assign_roles(row["agency"], row["description"] or "")
                if role != "all" and role not in assigned_roles:
                    continue
                contacts.append({
                    "agency": row["agency"],
                    "phone": row["phone"],
                    "email": row["email"],
                    "description": row["description"],
                    "region": row["region"],
                    "roles": assigned_roles,
                    "relevance_score": round(float(row["similarity"]), 3),
                })
                if len(contacts) >= limit:
                    break

        finally:
            await conn.close()

        return [TextContent(type="text", text=json.dumps({
            "region": region,
            "country": country,
            "disaster_type": disaster_type,
            "role_filter": role,
            "contacts_found": len(contacts),
            "contacts": contacts,
        }, indent=2))]

    except Exception as e:
        return [TextContent(type="text", text=json.dumps({"error": str(e)}))]


# Static universal numbers — no DB needed
UNIVERSAL_NUMBERS = {
    "india": {"ambulance": "108", "police": "100", "fire": "101", "disaster": "1070"},
    "indonesia": {"ambulance": "119", "police": "110", "fire": "113", "disaster": "117"},
    "philippines": {"ambulance": "911", "police": "911", "fire": "911", "disaster": "+63-2-911-5061"},
    "thailand": {"ambulance": "1669", "police": "191", "fire": "199", "disaster": "1784"},
    "malaysia": {"ambulance": "999", "police": "999", "fire": "994", "disaster": "999"},
    "vietnam": {"ambulance": "115", "police": "113", "fire": "114", "disaster": "1800-599-920"},
    "bangladesh": {"ambulance": "199", "police": "999", "fire": "199", "disaster": "1090"},
    "nepal": {"ambulance": "102", "police": "100", "fire": "101", "disaster": "1100"},
}


async def _get_global_emergency_numbers(args: dict) -> list[TextContent]:
    country = args["country"].lower().strip()
    numbers = UNIVERSAL_NUMBERS.get(country, {
        "ambulance": "112 (international)",
        "police": "112 (international)",
        "fire": "112 (international)",
        "note": "Country-specific numbers not found. Use 112 (international emergency).",
    })
    return [TextContent(type="text", text=json.dumps({
        "country": args["country"],
        "emergency_numbers": numbers,
    }, indent=2))]


async def main():
    async with stdio_server() as (read_stream, write_stream):
        await app.run(read_stream, write_stream, app.create_initialization_options())


if __name__ == "__main__":
    asyncio.run(main())
