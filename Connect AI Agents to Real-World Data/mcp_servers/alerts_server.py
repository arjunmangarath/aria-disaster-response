"""
Disaster Alerts MCP Server — wraps GDACS (Global Disaster Alert & Coordination System).
Free public API, no key required.
"""

import asyncio
import httpx
from mcp.server import Server
from mcp.server.stdio import stdio_server
from mcp.types import Tool, TextContent
import json
import sys
import os
from datetime import datetime

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from config.settings import GDACS_API_URL

app = Server("alerts-mcp")

ALERT_LEVEL_MAP = {"Green": 1, "Orange": 2, "Red": 3}


@app.list_tools()
async def list_tools() -> list[Tool]:
    return [
        Tool(
            name="get_active_alerts",
            description=(
                "Fetch active disaster alerts from GDACS for a specific region or globally. "
                "Returns event type, severity, affected country, and coordinates."
            ),
            inputSchema={
                "type": "object",
                "properties": {
                    "country": {
                        "type": "string",
                        "description": "Country name or ISO code to filter alerts (optional)",
                    },
                    "disaster_type": {
                        "type": "string",
                        "description": "Type: EQ (earthquake), FL (flood), TC (tropical cyclone), VO (volcano), DR (drought)",
                    },
                    "limit": {
                        "type": "integer",
                        "description": "Max number of alerts to return (default 5)",
                        "default": 5,
                    },
                },
                "required": [],
            },
        ),
        Tool(
            name="get_alert_severity_summary",
            description="Get a summary of current global disaster severity levels.",
            inputSchema={"type": "object", "properties": {}, "required": []},
        ),
    ]


@app.call_tool()
async def call_tool(name: str, arguments: dict) -> list[TextContent]:
    if name == "get_active_alerts":
        return await _get_active_alerts(arguments)
    elif name == "get_alert_severity_summary":
        return await _get_alert_severity_summary()
    return [TextContent(type="text", text="Unknown tool")]


async def _fetch_gdacs_events(event_type: str = None, limit: int = 10) -> list[dict]:
    params = {"limit": limit, "alertlevel": "Orange,Red"}
    if event_type:
        params["eventtype"] = event_type

    async with httpx.AsyncClient(timeout=15.0) as client:
        resp = await client.get(GDACS_API_URL, params=params)
        resp.raise_for_status()
        data = resp.json()
        return data.get("features", [])


async def _get_active_alerts(args: dict) -> list[TextContent]:
    country = args.get("country", "").lower()
    disaster_type = args.get("disaster_type")
    limit = args.get("limit", 5)

    try:
        features = await _fetch_gdacs_events(event_type=disaster_type, limit=20)
        alerts = []

        for f in features:
            props = f.get("properties", {})
            geom = f.get("geometry", {})
            coords = geom.get("coordinates", [None, None])

            event_country = props.get("country", "").lower()
            if country and country not in event_country:
                continue

            alerts.append({
                "event_id": props.get("eventid"),
                "type": props.get("eventtype"),
                "name": props.get("name"),
                "country": props.get("country"),
                "alert_level": props.get("alertlevel"),
                "severity": props.get("severitydata", {}).get("severity"),
                "latitude": coords[1] if len(coords) > 1 else None,
                "longitude": coords[0] if coords else None,
                "date": props.get("fromdate"),
                "description": props.get("description", "")[:200],
                "url": props.get("url", {}).get("report"),
            })

            if len(alerts) >= limit:
                break

        if not alerts:
            return [TextContent(type="text", text=json.dumps({
                "message": "No active alerts found for the specified criteria.",
                "alerts": []
            }))]

        return [TextContent(type="text", text=json.dumps({
            "total": len(alerts),
            "alerts": alerts
        }, indent=2))]

    except Exception as e:
        return [TextContent(type="text", text=json.dumps({"error": str(e)}))]


async def _get_alert_severity_summary() -> list[TextContent]:
    try:
        features = await _fetch_gdacs_events(limit=50)
        summary = {"Red": 0, "Orange": 0, "Green": 0, "by_type": {}}

        for f in features:
            props = f.get("properties", {})
            level = props.get("alertlevel", "Green")
            etype = props.get("eventtype", "Unknown")
            summary[level] = summary.get(level, 0) + 1
            summary["by_type"][etype] = summary["by_type"].get(etype, 0) + 1

        summary["overall_risk"] = (
            "CRITICAL" if summary["Red"] > 3
            else "HIGH" if summary["Red"] > 0 or summary["Orange"] > 5
            else "MODERATE" if summary["Orange"] > 0
            else "LOW"
        )
        summary["timestamp"] = datetime.utcnow().isoformat()

        return [TextContent(type="text", text=json.dumps(summary, indent=2))]
    except Exception as e:
        return [TextContent(type="text", text=json.dumps({"error": str(e)}))]


async def main():
    async with stdio_server() as (read_stream, write_stream):
        await app.run(read_stream, write_stream, app.create_initialization_options())


if __name__ == "__main__":
    asyncio.run(main())
