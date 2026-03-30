"""
Weather MCP Server — wraps Open-Meteo API (free, no key required).
Provides current conditions and forecasts for disaster-affected regions.
"""

import asyncio
import httpx
from mcp.server import Server
from mcp.server.stdio import stdio_server
from mcp.types import Tool, TextContent
import json
import sys
import os

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from config.settings import OPENMETEO_API_URL

app = Server("weather-mcp")


@app.list_tools()
async def list_tools() -> list[Tool]:
    return [
        Tool(
            name="get_weather",
            description=(
                "Get current weather conditions and forecast for a disaster-affected location. "
                "Returns temperature, precipitation, wind speed, and weather code."
            ),
            inputSchema={
                "type": "object",
                "properties": {
                    "latitude": {"type": "number", "description": "Latitude of the location"},
                    "longitude": {"type": "number", "description": "Longitude of the location"},
                    "location_name": {"type": "string", "description": "Human-readable location name"},
                },
                "required": ["latitude", "longitude"],
            },
        ),
        Tool(
            name="get_hazard_conditions",
            description=(
                "Assess weather hazard level for a disaster zone. "
                "Returns severity rating (LOW/MEDIUM/HIGH/EXTREME) and advisory."
            ),
            inputSchema={
                "type": "object",
                "properties": {
                    "latitude": {"type": "number"},
                    "longitude": {"type": "number"},
                    "disaster_type": {
                        "type": "string",
                        "description": "Type of disaster (flood, earthquake, cyclone, etc.)",
                    },
                },
                "required": ["latitude", "longitude", "disaster_type"],
            },
        ),
    ]


@app.call_tool()
async def call_tool(name: str, arguments: dict) -> list[TextContent]:
    if name == "get_weather":
        return await _get_weather(arguments)
    elif name == "get_hazard_conditions":
        return await _get_hazard_conditions(arguments)
    return [TextContent(type="text", text="Unknown tool")]


async def _fetch_weather(lat: float, lon: float) -> dict:
    params = {
        "latitude": lat,
        "longitude": lon,
        "current": [
            "temperature_2m", "relative_humidity_2m", "precipitation",
            "weather_code", "wind_speed_10m", "wind_gusts_10m",
        ],
        "hourly": ["precipitation_probability", "visibility"],
        "forecast_days": 2,
    }
    async with httpx.AsyncClient(timeout=10.0) as client:
        resp = await client.get(OPENMETEO_API_URL, params=params)
        resp.raise_for_status()
        return resp.json()


def _weather_code_description(code: int) -> str:
    codes = {
        0: "Clear sky", 1: "Mainly clear", 2: "Partly cloudy", 3: "Overcast",
        45: "Foggy", 48: "Icy fog", 51: "Light drizzle", 53: "Moderate drizzle",
        61: "Slight rain", 63: "Moderate rain", 65: "Heavy rain",
        71: "Slight snow", 73: "Moderate snow", 75: "Heavy snow",
        80: "Slight showers", 81: "Moderate showers", 82: "Violent showers",
        95: "Thunderstorm", 96: "Thunderstorm with hail", 99: "Thunderstorm with heavy hail",
    }
    return codes.get(code, f"Weather code {code}")


async def _get_weather(args: dict) -> list[TextContent]:
    lat, lon = args["latitude"], args["longitude"]
    name = args.get("location_name", f"{lat},{lon}")
    try:
        data = await _fetch_weather(lat, lon)
        current = data.get("current", {})
        result = {
            "location": name,
            "temperature_celsius": current.get("temperature_2m"),
            "humidity_percent": current.get("relative_humidity_2m"),
            "precipitation_mm": current.get("precipitation"),
            "wind_speed_kmh": current.get("wind_speed_10m"),
            "wind_gusts_kmh": current.get("wind_gusts_10m"),
            "conditions": _weather_code_description(current.get("weather_code", 0)),
        }
        return [TextContent(type="text", text=json.dumps(result, indent=2))]
    except Exception as e:
        return [TextContent(type="text", text=json.dumps({"error": str(e)}))]


async def _get_hazard_conditions(args: dict) -> list[TextContent]:
    lat, lon = args["latitude"], args["longitude"]
    disaster_type = args["disaster_type"].lower()
    try:
        data = await _fetch_weather(lat, lon)
        current = data.get("current", {})
        precip = current.get("precipitation", 0) or 0
        wind = current.get("wind_speed_10m", 0) or 0
        gusts = current.get("wind_gusts_10m", 0) or 0
        code = current.get("weather_code", 0) or 0

        severity = "LOW"
        advisories = []

        if disaster_type in ("flood", "cyclone", "typhoon"):
            if precip > 20 or code in (82, 95, 96, 99):
                severity = "EXTREME"
                advisories.append("Extreme precipitation — immediate evacuation advised.")
            elif precip > 10:
                severity = "HIGH"
                advisories.append("Heavy rainfall — avoid low-lying areas.")
            elif precip > 3:
                severity = "MEDIUM"
                advisories.append("Moderate rainfall — monitor water levels.")

        if disaster_type in ("cyclone", "typhoon"):
            if gusts > 120:
                severity = "EXTREME"
                advisories.append("Extreme wind gusts — seek reinforced shelter immediately.")
            elif gusts > 60:
                severity = max(severity, "HIGH") if severity != "EXTREME" else severity
                advisories.append("Strong gusts — secure loose objects.")

        if not advisories:
            advisories.append("Conditions stable — continue monitoring.")

        result = {
            "disaster_type": disaster_type,
            "severity": severity,
            "advisories": advisories,
            "current_precipitation_mm": precip,
            "wind_speed_kmh": wind,
            "wind_gusts_kmh": gusts,
            "conditions": _weather_code_description(code),
        }
        return [TextContent(type="text", text=json.dumps(result, indent=2))]
    except Exception as e:
        return [TextContent(type="text", text=json.dumps({"error": str(e)}))]


async def main():
    async with stdio_server() as (read_stream, write_stream):
        await app.run(read_stream, write_stream, app.create_initialization_options())


if __name__ == "__main__":
    asyncio.run(main())
