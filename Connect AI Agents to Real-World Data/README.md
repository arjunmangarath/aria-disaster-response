# ARIA — Adaptive Response Intelligence Agent

> **Gen AI Academy APAC Edition — Track 2: Connect AI Agents to Real-World Data**
> Built with Google ADK · MCP · AlloyDB AI · Vertex AI · Google Maps · Streamlit

---

## Problem Statement

During natural disasters in APAC, emergency responders, command centers, and civilians operate with fragmented, delayed information across siloed systems. Critical minutes are lost coordinating resources, locating shelters, and reaching the right emergency contacts — leading to preventable casualties.

## Solution

ARIA is a unified AI-powered disaster response platform. One agent. Three stakeholder roles. Seven real-world data sources connected via MCP.

Report any disaster → ARIA instantly coordinates routes, shelters, hospitals, emergency contacts, weather alerts, and multilingual civilian notifications.

---

## Architecture

```
User Input (Streamlit)
        │
        ▼
Google ADK Agent (Gemini 1.5 Flash / Vertex AI)
        │
        ├── Google Maps MCP     → Evacuation routing, place search
        ├── Weather MCP         → Open-Meteo hazard assessment
        ├── Alerts MCP          → GDACS real-time disaster feed
        ├── Shelter MCP         → AlloyDB AI vector search (shelters)
        ├── Contacts MCP        → AlloyDB AI vector search (emergency contacts)
        ├── Translate MCP       → Google Translate API (APAC languages)
        └── Notify MCP          → Firebase Realtime DB push
                │
                ▼
        Streamlit Dashboard (3 role views + live map)
```

---

## Google Cloud Services Used

| Service | Role |
|---|---|
| **Vertex AI (Gemini 1.5 Flash)** | LLM backbone for the ADK agent |
| **Google ADK** | Agent framework with MCPToolset |
| **Google Maps Platform** | Routing, geocoding, place search |
| **AlloyDB AI + pgvector** | Shelter & contacts semantic search |
| **Google Cloud Translation API** | APAC multilingual alerts |
| **Firebase Realtime Database** | Live notification push |
| **Google Cloud Run** | MCP server hosting |
| **GDACS API** | Free global disaster alert feed |
| **Open-Meteo API** | Free weather & hazard data |

---

## Quick Start

### 1. Clone & Setup

```bash
git clone https://github.com/YOUR_USERNAME/aria-disaster-agent.git
cd aria-disaster-agent
python -m venv venv
source venv/bin/activate  # Windows: venv\Scripts\activate
pip install -r requirements.txt
```

### 2. Configure Environment

```bash
cp .env.example .env
# Edit .env with your Google Cloud credentials
```

### 3. Setup AlloyDB

```bash
# Run schema
psql $ALLOYDB_DSN -f db/schema.sql

# Seed data
python db/seed_data.py
```

### 4. Auth

```bash
gcloud auth application-default login
gcloud config set project YOUR_PROJECT_ID
```

### 5. Run

```bash
streamlit run main.py
```

---

## Project Structure

```
aria-disaster-agent/
├── main.py                    # Streamlit app
├── requirements.txt
├── .env.example
├── agent/
│   └── aria_agent.py          # ADK agent + MCPToolset wiring
├── mcp_servers/
│   ├── weather_server.py      # Open-Meteo MCP
│   ├── alerts_server.py       # GDACS MCP
│   ├── shelter_server.py      # AlloyDB AI shelter MCP
│   ├── contacts_server.py     # AlloyDB AI contacts MCP
│   ├── translate_server.py    # Google Translate MCP
│   └── notify_server.py       # Firebase MCP
├── db/
│   ├── schema.sql             # AlloyDB AI schema + pgvector indexes
│   └── seed_data.py           # Seed shelters, hospitals, contacts
├── ui/
│   ├── components.py          # Streamlit UI components
│   └── map_utils.py           # Folium map builder
└── config/
    └── settings.py            # Environment config
```

---

## Demo Scenarios

- **Chennai Earthquake** — 6.2 magnitude, multi-agency coordination
- **Jakarta Flood** — Monsoon flooding, mass evacuation routing
- **Manila Typhoon** — Category 4 landfall, civilian sheltering

---

## Team

Built for **Gen AI Academy APAC Edition** — Google Cloud × H2S
