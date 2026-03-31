"""
Shelter MCP Server — queries AlloyDB AI with pgvector for intelligent shelter matching.
Uses semantic vector search to find shelters by disaster context and location.
"""

import asyncio
import asyncpg
from mcp.server import Server
from mcp.server.stdio import stdio_server
from mcp.types import Tool, TextContent
import json
import sys
import os
import math

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from config.settings import ALLOYDB_DSN, GOOGLE_CLOUD_PROJECT, VERTEX_AI_LOCATION

app = Server("shelter-mcp")


def _haversine_km(lat1, lon1, lat2, lon2) -> float:
    R = 6371
    dlat = math.radians(lat2 - lat1)
    dlon = math.radians(lon2 - lon1)
    a = math.sin(dlat / 2) ** 2 + math.cos(math.radians(lat1)) * math.cos(math.radians(lat2)) * math.sin(dlon / 2) ** 2
    return R * 2 * math.asin(math.sqrt(a))


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
            name="find_shelters",
            description=(
                "Find available shelters near a disaster location using AlloyDB AI vector search. "
                "Returns ranked shelters with capacity, facilities, and contact info."
            ),
            inputSchema={
                "type": "object",
                "properties": {
                    "latitude": {"type": "number", "description": "Disaster epicenter latitude"},
                    "longitude": {"type": "number", "description": "Disaster epicenter longitude"},
                    "disaster_type": {"type": "string", "description": "Type of disaster"},
                    "region": {"type": "string", "description": "Region or city name"},
                    "require_medical": {"type": "boolean", "description": "Filter for medical facilities", "default": False},
                    "limit": {"type": "integer", "default": 5},
                },
                "required": ["latitude", "longitude", "disaster_type"],
            },
        ),
        Tool(
            name="find_hospitals",
            description="Find nearest hospitals with emergency capacity to a disaster location.",
            inputSchema={
                "type": "object",
                "properties": {
                    "latitude": {"type": "number"},
                    "longitude": {"type": "number"},
                    "region": {"type": "string"},
                    "limit": {"type": "integer", "default": 3},
                },
                "required": ["latitude", "longitude"],
            },
        ),
        Tool(
            name="update_shelter_occupancy",
            description="Update the current occupancy of a shelter (for field responders).",
            inputSchema={
                "type": "object",
                "properties": {
                    "shelter_id": {"type": "integer"},
                    "current_occupancy": {"type": "integer"},
                },
                "required": ["shelter_id", "current_occupancy"],
            },
        ),
    ]


@app.call_tool()
async def call_tool(name: str, arguments: dict) -> list[TextContent]:
    if name == "find_shelters":
        return await _find_shelters(arguments)
    elif name == "find_hospitals":
        return await _find_hospitals(arguments)
    elif name == "update_shelter_occupancy":
        return await _update_shelter_occupancy(arguments)
    return [TextContent(type="text", text="Unknown tool")]


async def _find_shelters(args: dict) -> list[TextContent]:
    lat, lon = args["latitude"], args["longitude"]
    disaster_type = args["disaster_type"]
    region = args.get("region", "")
    require_medical = args.get("require_medical", False)
    limit = args.get("limit", 5)

    try:
        query_text = f"shelter near {region} for {disaster_type} disaster with capacity"
        embedding = await _get_query_embedding(query_text)
        embedding_str = "[" + ",".join(str(v) for v in embedding) + "]"

        conn = await asyncio.wait_for(asyncpg.connect(ALLOYDB_DSN), timeout=15.0)
        try:
            sql = f"""
                SELECT id, name, region, country, latitude, longitude,
                       capacity, current_occupancy, has_medical, has_food,
                       has_water, disaster_types, contact_phone,
                       1 - (embedding <=> '{embedding_str}'::vector) AS similarity
                FROM shelters
                WHERE capacity > current_occupancy
                {"AND has_medical = TRUE" if require_medical else ""}
                ORDER BY embedding <=> '{embedding_str}'::vector
                LIMIT {limit * 2}
            """
            rows = await conn.fetch(sql)

            shelters = []
            for row in rows:
                distance_km = _haversine_km(lat, lon, row["latitude"], row["longitude"])
                available = row["capacity"] - row["current_occupancy"]
                shelters.append({
                    "id": row["id"],
                    "name": row["name"],
                    "region": row["region"],
                    "country": row["country"],
                    "latitude": row["latitude"],
                    "longitude": row["longitude"],
                    "distance_km": round(distance_km, 1),
                    "available_capacity": available,
                    "total_capacity": row["capacity"],
                    "has_medical": row["has_medical"],
                    "has_food": row["has_food"],
                    "has_water": row["has_water"],
                    "contact_phone": row["contact_phone"],
                    "similarity_score": round(float(row["similarity"]), 3),
                })

            shelters.sort(key=lambda x: x["distance_km"])
            shelters = shelters[:limit]

        finally:
            await conn.close()

        return [TextContent(type="text", text=json.dumps({
            "disaster_type": disaster_type,
            "shelters_found": len(shelters),
            "shelters": shelters,
        }, indent=2))]

    except Exception as e:
        return [TextContent(type="text", text=json.dumps({"error": str(e)}))]


async def _find_hospitals(args: dict) -> list[TextContent]:
    lat, lon = args["latitude"], args["longitude"]
    region = args.get("region", "")
    limit = args.get("limit", 3)

    try:
        query_text = f"hospital emergency care near {region}"
        embedding = await _get_query_embedding(query_text)
        embedding_str = "[" + ",".join(str(v) for v in embedding) + "]"

        conn = await asyncio.wait_for(asyncpg.connect(ALLOYDB_DSN), timeout=15.0)
        try:
            sql = f"""
                SELECT id, name, region, country, latitude, longitude,
                       emergency_beds, contact_phone, contact_email
                FROM hospitals
                ORDER BY embedding <=> '{embedding_str}'::vector
                LIMIT {limit * 2}
            """
            rows = await conn.fetch(sql)

            hospitals = []
            for row in rows:
                distance_km = _haversine_km(lat, lon, row["latitude"], row["longitude"])
                hospitals.append({
                    "id": row["id"],
                    "name": row["name"],
                    "region": row["region"],
                    "distance_km": round(distance_km, 1),
                    "emergency_beds": row["emergency_beds"],
                    "contact_phone": row["contact_phone"],
                    "contact_email": row["contact_email"],
                    "latitude": row["latitude"],
                    "longitude": row["longitude"],
                })

            hospitals.sort(key=lambda x: x["distance_km"])
            hospitals = hospitals[:limit]

        finally:
            await conn.close()

        return [TextContent(type="text", text=json.dumps({
            "hospitals_found": len(hospitals),
            "hospitals": hospitals,
        }, indent=2))]

    except Exception as e:
        return [TextContent(type="text", text=json.dumps({"error": str(e)}))]


async def _update_shelter_occupancy(args: dict) -> list[TextContent]:
    try:
        conn = await asyncio.wait_for(asyncpg.connect(ALLOYDB_DSN), timeout=15.0)
        try:
            await conn.execute(
                "UPDATE shelters SET current_occupancy=$1, updated_at=NOW() WHERE id=$2",
                args["current_occupancy"], args["shelter_id"]
            )
        finally:
            await conn.close()
        return [TextContent(type="text", text=json.dumps({"status": "updated", "shelter_id": args["shelter_id"]}))]
    except Exception as e:
        return [TextContent(type="text", text=json.dumps({"error": str(e)}))]


async def main():
    async with stdio_server() as (read_stream, write_stream):
        await app.run(read_stream, write_stream, app.create_initialization_options())


if __name__ == "__main__":
    asyncio.run(main())
