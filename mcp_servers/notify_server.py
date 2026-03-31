"""
Notify MCP Server — pushes real-time alerts to Firebase Realtime Database.
Streamlit polls Firebase to display live notifications on the dashboard.
"""

import asyncio
from mcp.server import Server
from mcp.server.stdio import stdio_server
from mcp.types import Tool, TextContent
import json
import sys
import os
from datetime import datetime

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from config.settings import FIREBASE_CREDENTIALS_PATH, FIREBASE_DATABASE_URL

app = Server("notify-mcp")
_firebase_initialized = False


def _init_firebase():
    global _firebase_initialized
    if not _firebase_initialized:
        import firebase_admin
        from firebase_admin import credentials
        if not firebase_admin._apps:
            cred = credentials.Certificate(FIREBASE_CREDENTIALS_PATH)
            firebase_admin.initialize_app(cred, {"databaseURL": FIREBASE_DATABASE_URL})
        _firebase_initialized = True


@app.list_tools()
async def list_tools() -> list[Tool]:
    return [
        Tool(
            name="push_alert",
            description=(
                "Push a disaster alert notification to the Firebase Realtime Database. "
                "The Streamlit dashboard reads this in real-time to display updates."
            ),
            inputSchema={
                "type": "object",
                "properties": {
                    "title": {"type": "string", "description": "Alert title"},
                    "message": {"type": "string", "description": "Alert message body"},
                    "severity": {
                        "type": "string",
                        "enum": ["INFO", "WARNING", "CRITICAL"],
                        "description": "Alert severity level",
                    },
                    "disaster_type": {"type": "string"},
                    "location": {"type": "string"},
                    "target_roles": {
                        "type": "array",
                        "items": {"type": "string"},
                        "description": "Roles to notify: command, responder, civilian",
                        "default": ["command", "responder", "civilian"],
                    },
                },
                "required": ["title", "message", "severity"],
            },
        ),
        Tool(
            name="push_resource_update",
            description="Push shelter/hospital resource status update to Firebase.",
            inputSchema={
                "type": "object",
                "properties": {
                    "resource_name": {"type": "string"},
                    "resource_type": {"type": "string", "enum": ["shelter", "hospital"]},
                    "available_capacity": {"type": "integer"},
                    "location": {"type": "string"},
                    "contact_phone": {"type": "string"},
                },
                "required": ["resource_name", "resource_type", "available_capacity"],
            },
        ),
        Tool(
            name="get_recent_alerts",
            description="Retrieve the most recent alerts from Firebase.",
            inputSchema={
                "type": "object",
                "properties": {
                    "limit": {"type": "integer", "default": 10},
                },
                "required": [],
            },
        ),
    ]


@app.call_tool()
async def call_tool(name: str, arguments: dict) -> list[TextContent]:
    if name == "push_alert":
        return await _push_alert(arguments)
    elif name == "push_resource_update":
        return await _push_resource_update(arguments)
    elif name == "get_recent_alerts":
        return await _get_recent_alerts(arguments)
    return [TextContent(type="text", text="Unknown tool")]


async def _push_alert(args: dict) -> list[TextContent]:
    try:
        _init_firebase()
        from firebase_admin import db
        ref = db.reference("alerts")
        alert_data = {
            "title": args["title"],
            "message": args["message"],
            "severity": args["severity"],
            "disaster_type": args.get("disaster_type", ""),
            "location": args.get("location", ""),
            "target_roles": args.get("target_roles", ["command", "responder", "civilian"]),
            "timestamp": datetime.utcnow().isoformat(),
        }
        new_ref = ref.push(alert_data)
        return [TextContent(type="text", text=json.dumps({
            "status": "pushed",
            "alert_id": new_ref.key,
            "data": alert_data,
        }, indent=2))]
    except Exception as e:
        return [TextContent(type="text", text=json.dumps({"error": str(e)}))]


async def _push_resource_update(args: dict) -> list[TextContent]:
    try:
        _init_firebase()
        from firebase_admin import db
        ref = db.reference("resources")
        data = {
            "name": args["resource_name"],
            "type": args["resource_type"],
            "available_capacity": args["available_capacity"],
            "location": args.get("location", ""),
            "contact_phone": args.get("contact_phone", ""),
            "timestamp": datetime.utcnow().isoformat(),
        }
        new_ref = ref.push(data)
        return [TextContent(type="text", text=json.dumps({
            "status": "updated",
            "resource_id": new_ref.key,
        }, indent=2))]
    except Exception as e:
        return [TextContent(type="text", text=json.dumps({"error": str(e)}))]


async def _get_recent_alerts(args: dict) -> list[TextContent]:
    try:
        _init_firebase()
        from firebase_admin import db
        limit = args.get("limit", 10)
        ref = db.reference("alerts")
        data = ref.order_by_child("timestamp").limit_to_last(limit).get()
        alerts = list(data.values()) if data else []
        alerts.sort(key=lambda x: x.get("timestamp", ""), reverse=True)
        return [TextContent(type="text", text=json.dumps({
            "count": len(alerts),
            "alerts": alerts,
        }, indent=2))]
    except Exception as e:
        return [TextContent(type="text", text=json.dumps({"error": str(e)}))]


async def main():
    async with stdio_server() as (read_stream, write_stream):
        await app.run(read_stream, write_stream, app.create_initialization_options())


if __name__ == "__main__":
    asyncio.run(main())
