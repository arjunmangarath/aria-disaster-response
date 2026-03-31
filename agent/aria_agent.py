"""
ARIA — Adaptive Response Intelligence Agent
Built with Google ADK, connecting to 7 MCP servers for real-world disaster data.
"""

import asyncio
import os
import subprocess
import sys
from pathlib import Path

from google.adk.agents import Agent
from google.adk.runners import Runner
from google.adk.sessions import InMemorySessionService
from google.adk.tools.mcp_tool.mcp_toolset import McpToolset, StdioConnectionParams
from mcp.client.stdio import StdioServerParameters as McpStdioParams
from google.genai import types as genai_types

sys.path.append(str(Path(__file__).parent.parent))
from dotenv import load_dotenv
load_dotenv()

from config.settings import GEMINI_MODEL, GOOGLE_CLOUD_PROJECT, VERTEX_AI_LOCATION

# Force ADK to use Vertex AI backend (not Google AI Studio)
os.environ.setdefault("GOOGLE_GENAI_USE_VERTEXAI", "1")
os.environ.setdefault("GOOGLE_CLOUD_PROJECT", GOOGLE_CLOUD_PROJECT)
os.environ.setdefault("GOOGLE_CLOUD_LOCATION", VERTEX_AI_LOCATION)

MCP_DIR = str(Path(__file__).parent.parent / "mcp_servers")
PYTHON = sys.executable

# Pre-install Maps MCP package so npx doesn't download it on every agent call
try:
    subprocess.run(
        ["npm", "install", "-g", "@modelcontextprotocol/server-google-maps"],
        capture_output=True, timeout=120, check=False,
    )
except Exception:
    pass

_MCP_TIMEOUT = 120.0

SYSTEM_PROMPT = """
You are ARIA (Adaptive Response Intelligence Agent), an AI-powered disaster response coordinator
built on Google ADK for the APAC region.

When a disaster is reported, you MUST:
1. Classify the disaster type and severity from the input
2. Extract the location (region, country, coordinates if possible)
3. Call ALL relevant MCP tools to gather real-world data:
   - get_active_alerts: Check GDACS for active disaster alerts in the region
   - get_weather / get_hazard_conditions: Assess current weather and hazard level
   - find_shelters: Locate nearby shelters with capacity using AlloyDB AI
   - find_hospitals: Find nearest hospitals with emergency beds
   - get_emergency_contacts: Get agency contacts (NDRF, police, ambulance, etc.)
   - get_global_emergency_numbers: Get universal emergency numbers for the country
   - translate_for_region: Translate the key alert into ALL regional languages for that country.
     For India, this means Tamil, Telugu, Kannada, Malayalam, Hindi, Marathi, Gujarati, Bengali.
   - push_alert: Push a structured alert to Firebase for the dashboard

4. Synthesize a ROLE-AWARE response with FOUR clearly labeled sections:

   ## COMMAND CENTER BRIEFING
   - Situation summary with severity level (CRITICAL / HIGH / MODERATE / LOW)
   - **Impact Estimate**: estimated population affected (use regional population density),
     estimated buildings at risk, estimated casualties range (e.g. "50–200 possible casualties"),
     and critical infrastructure at risk (hospitals, bridges, power). Mark these as ESTIMATES.
   - Active GDACS alerts
   - Resource overview (shelter capacity, hospital beds)
   - Agency contacts for coordination
   - Weather/hazard assessment

   ## FIELD RESPONDER GUIDE
   - Top 3 shelters with capacity, distance, and contact
   - Nearest hospitals with emergency lines
   - Optimal action priority list
   - Hazard advisories for field teams

   ## CIVILIAN INFORMATION
   - Nearest shelter with directions hint
   - Emergency numbers (ambulance, police, fire)
   - Safety instructions (keep short and clear)

   ## MULTILINGUAL ALERTS
   Show the key evacuation alert translated into EVERY language returned by translate_for_region.
   Format EXACTLY as:
   **Tamil (தமிழ்):** [translation]
   **Telugu (తెలుగు):** [translation]
   **Kannada (ಕನ್ನಡ):** [translation]
   **Malayalam (മലയാളം):** [translation]
   **Hindi (हिंदी):** [translation]
   **Marathi (मराठी):** [translation]
   **Gujarati (ગુજરાતી):** [translation]
   **Bengali (বাংলা):** [translation]
   (Include only languages returned by the translation tool. Use native script names in parentheses.)

Always be calm, factual, and actionable. Lives depend on accuracy.
If data is unavailable from a tool, note it and proceed with available data.
"""


def _make_toolset(script_name: str) -> McpToolset:
    return McpToolset(
        connection_params=StdioConnectionParams(
            server_params=McpStdioParams(
                command=PYTHON,
                args=[os.path.join(MCP_DIR, script_name)],
                env={**os.environ},
            ),
            timeout=_MCP_TIMEOUT,
        )
    )


def _build_agent() -> Agent:
    """Build the ARIA agent with all MCP toolsets."""
    return Agent(
        name="ARIA",
        model=GEMINI_MODEL,
        description="Adaptive Response Intelligence Agent for natural disaster coordination",
        instruction=SYSTEM_PROMPT,
        tools=[
            McpToolset(
                connection_params=StdioConnectionParams(
                    server_params=McpStdioParams(
                        command="npx",
                        args=["-y", "@modelcontextprotocol/server-google-maps"],
                        env={**os.environ, "GOOGLE_MAPS_API_KEY": os.getenv("GOOGLE_MAPS_API_KEY", "")},
                    ),
                    timeout=_MCP_TIMEOUT,
                )
            ),
            _make_toolset("weather_server.py"),
            _make_toolset("alerts_server.py"),
            _make_toolset("shelter_server.py"),
            _make_toolset("contacts_server.py"),
            _make_toolset("translate_server.py"),
            _make_toolset("notify_server.py"),
        ],
    )


async def stream_aria(disaster_input: str, session_id: str = "default"):
    """
    Stream ARIA events. Yields (event_type, content) tuples.
    """
    session_service = InMemorySessionService()
    await session_service.create_session(
        app_name="ARIA",
        user_id="operator",
        session_id=session_id,
    )

    agent = _build_agent()

    runner = Runner(
        agent=agent,
        app_name="ARIA",
        session_service=session_service,
    )

    message = genai_types.Content(
        role="user",
        parts=[genai_types.Part(text=disaster_input)],
    )

    async for event in runner.run_async(
        user_id="operator",
        session_id=session_id,
        new_message=message,
    ):
        if event.content and event.content.parts:
            for part in event.content.parts:
                if hasattr(part, "function_call") and part.function_call:
                    yield ("tool_call", part.function_call.name)
                elif hasattr(part, "text") and part.text:
                    if event.is_final_response():
                        yield ("response", part.text)
                    else:
                        yield ("thinking", part.text)


async def run_aria(disaster_input: str, session_id: str = "default") -> str:
    """Run ARIA and return the full response string."""
    full_response = ""
    async for event_type, content in stream_aria(disaster_input, session_id):
        if event_type == "response":
            full_response += content
    return full_response


if __name__ == "__main__":
    async def test():
        print("Testing ARIA agent...")
        response = await run_aria(
            "Earthquake magnitude 6.2 reported in Chennai, India."
        )
        print(response)

    asyncio.run(test())
