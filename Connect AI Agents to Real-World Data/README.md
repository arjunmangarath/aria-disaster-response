# 🆘 ARIA — Adaptive Response Intelligence Agent

> **Gen AI Academy APAC Edition — Track 2: Connect AI Agents to Real-World Data**

[![Streamlit App](https://static.streamlit.io/badges/streamlit_badge_black_white.svg)](https://aria-disaster-response.streamlit.app)
[![Python 3.11](https://img.shields.io/badge/python-3.11-blue.svg)](https://www.python.org)
[![Google ADK](https://img.shields.io/badge/Google%20ADK-MCP-4285F4?logo=google)](https://google.github.io/adk-docs)
[![Vertex AI](https://img.shields.io/badge/Vertex%20AI-Gemini%202.5-34A853?logo=google-cloud)](https://cloud.google.com/vertex-ai)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](LICENSE)

---

## The Problem

During natural disasters in the APAC region, **critical minutes are lost** because:
- Emergency command centers, field responders, and civilians use **fragmented, siloed systems**
- Real-time shelter capacity, hospital availability, and emergency contacts are **scattered across agencies**
- Civilian alerts are **only in English** — unreachable for hundreds of millions of people
- Weather and hazard conditions require **manual cross-checking** across multiple platforms

These delays cost lives.

---

## The Solution

**ARIA** is a unified AI disaster response platform — one agent, three stakeholder roles, seven real-world data sources connected via the **Model Context Protocol (MCP)**.

Report any disaster → ARIA automatically:
- Geocodes the location and pulls active GDACS alerts
- Assesses weather and hazard conditions in real time
- Finds nearest shelters and hospitals with live capacity (AlloyDB AI vector search)
- Retrieves agency emergency contacts for the specific disaster type
- Translates the civilian alert into **8+ regional languages** including all 4 South Indian languages
- Pushes a live alert to Firebase for field dashboard sync
- Generates role-specific briefs for command centers, field responders, and civilians

All in under 60 seconds.

---

## Architecture

```
┌─────────────────────────────────────────────────────────────────┐
│                     Streamlit Dashboard                         │
│        Dark UI · Live Streaming · Folium Map · 4 Role Tabs      │
└──────────────────────────┬──────────────────────────────────────┘
                           │ Disaster Report
                           ▼
┌─────────────────────────────────────────────────────────────────┐
│              Google ADK Agent (Gemini 2.5 Flash)                │
│                    Vertex AI · us-central1                      │
│                                                                 │
│  SYSTEM PROMPT: ARIA — Role-aware disaster response coordinator │
└──┬────────┬────────┬────────┬────────┬────────┬────────┬───────┘
   │        │        │        │        │        │        │
   ▼        ▼        ▼        ▼        ▼        ▼        ▼
 Maps    Weather  Alerts  Shelter  Contacts Translate Notify
  MCP     MCP      MCP     MCP      MCP      MCP      MCP
   │        │        │        │        │        │        │
   ▼        ▼        ▼        ▼        ▼        ▼        ▼
Google   Open-   GDACS   AlloyDB  AlloyDB  Google   Firebase
 Maps    Meteo    API    AI+vec   AI+vec  Translate Realtime
Platform  API    (free)  Search   Search    API       DB
```

---

## Google Cloud Services

| Service | Purpose |
|---|---|
| **Vertex AI — Gemini 2.5 Flash** | LLM backbone powering the ADK agent |
| **Google ADK** | Agent framework — orchestrates all MCP tool calls |
| **MCP Protocol (×7 servers)** | Connects agent to real-world data sources |
| **Google Maps Platform** | Geocoding, routing, place search |
| **AlloyDB AI + pgvector** | Semantic vector search for shelters, hospitals, contacts |
| **Google Cloud Translation API** | Multilingual civilian alerts (8+ APAC languages) |
| **Firebase Realtime Database** | Live alert push for field dashboard sync |
| **GDACS API** | Free real-time global disaster alert feed |
| **Open-Meteo API** | Free weather & hazard condition data |

---

## Key Features

### 🤖 Real-World Agent Intelligence
- **10 MCP tool calls** per disaster response — all automated
- Gemini 2.5 Flash reasons across all tool outputs to synthesize a coherent response
- Structured 4-section output: Command Center · Field Responder · Civilian · Translations

### 🗺️ Live Disaster Map
- Dark-theme folium map with disaster epicenter, affected zone ring
- Shelter markers (color-coded by available capacity)
- Hospital markers with emergency bed count
- Built from live AlloyDB AI vector search results

### 📊 Impact Estimation
- Population affected (regional density)
- Casualty range estimate
- Structures at risk
- Critical infrastructure assessment

### 🌐 Multilingual Alerts (South India Focus)
Translates civilian alerts into:
**Tamil · Telugu · Kannada · Malayalam** · Hindi · Marathi · Gujarati · Bengali · Bahasa Indonesia · Filipino · Thai · Vietnamese

### 📡 Live Streaming UI
- Response streams token-by-token as Gemini generates it
- Tool call badges appear in real time as each MCP server is called
- No blank waiting screen

### 📋 History & Export
- Last 3 scenarios saved with one-click reload
- Download full report as `.txt`
- Google Cloud services checklist shows what fired per run

---

## Demo Scenarios

| Scenario | Disaster | Location |
|---|---|---|
| 🌊 Chennai Earthquake | Magnitude 6.2 | Chennai, India |
| 🌀 Jakarta Flood | Category 5 monsoon flooding | Jakarta, Indonesia |
| 🌪️ Manila Typhoon | Category 4 landfall | Manila, Philippines |

---

## Project Structure

```
├── main.py                      # Streamlit app — UI, streaming, layout
├── requirements.txt
├── runtime.txt                  # Python 3.11 for Streamlit Cloud
├── packages.txt                 # Node.js for Maps MCP server
├── agent/
│   └── aria_agent.py            # Google ADK agent + 7 MCP toolsets
├── mcp_servers/
│   ├── weather_server.py        # Open-Meteo weather & hazard MCP
│   ├── alerts_server.py         # GDACS real-time disaster alerts MCP
│   ├── shelter_server.py        # AlloyDB AI shelter + hospital MCP
│   ├── contacts_server.py       # AlloyDB AI emergency contacts MCP
│   ├── translate_server.py      # Google Translate API MCP (8+ langs)
│   └── notify_server.py         # Firebase Realtime DB push MCP
├── db/
│   ├── schema.sql               # AlloyDB schema with pgvector indexes
│   └── seed_data.py             # Seeds shelters, hospitals, contacts
├── ui/
│   ├── components.py            # Dark-theme Streamlit components
│   └── map_utils.py             # Folium map builder
├── config/
│   └── settings.py              # Env config — local .env + st.secrets
└── .streamlit/
    └── config.toml              # Dark theme config
```

---

## Local Setup

### Prerequisites
- Python 3.11+
- Node.js (for Google Maps MCP server)
- Google Cloud project with Vertex AI, Maps, Translate, AlloyDB, Firebase enabled
- AlloyDB cluster with public IP

### 1. Clone & install

```bash
git clone https://github.com/arjunmangarath/aria-disaster-response.git
cd "aria-disaster-response/Connect AI Agents to Real-World Data"
pip install -r requirements.txt
```

### 2. Configure credentials

```bash
cp .env.example .env
# Fill in your values in .env
```

### 3. Setup AlloyDB

```bash
# Create schema
psql $ALLOYDB_DSN -f db/schema.sql

# Seed shelters, hospitals, emergency contacts
python db/seed_data.py
```

### 4. Authenticate

```bash
gcloud auth application-default login
gcloud config set project aria-disaster-response
```

### 5. Run

```bash
python -m streamlit run main.py
```

---

## Streamlit Cloud Deployment

All secrets are stored in Streamlit Cloud's Secrets Manager (never committed):

```
GOOGLE_CLOUD_PROJECT
GOOGLE_MAPS_API_KEY
GOOGLE_TRANSLATE_API_KEY
ALLOYDB_HOST / PORT / USER / PASSWORD / DATABASE
FIREBASE_DATABASE_URL
GOOGLE_SERVICE_ACCOUNT_JSON   ← Vertex AI credentials
FIREBASE_SERVICE_ACCOUNT_JSON ← Firebase Admin credentials
```

---

## How It Works — Step by Step

1. User describes a disaster and location in the sidebar
2. ARIA geocodes the location via **Google Maps Platform**
3. ADK agent calls all 10 MCP tools in sequence:
   - `maps_geocode` → precise coordinates
   - `get_active_alerts` → live GDACS feed
   - `get_weather` + `get_hazard_conditions` → Open-Meteo
   - `find_shelters` + `find_hospitals` → **AlloyDB AI pgvector semantic search**
   - `get_emergency_contacts` + `get_global_emergency_numbers` → AlloyDB AI
   - `translate_for_region` → **Google Translate** into 8+ languages
   - `push_alert` → **Firebase Realtime Database**
4. Gemini 2.5 synthesizes all tool outputs into 4 structured sections
5. Response streams live into the Streamlit UI
6. Map renders shelter/hospital pins from AlloyDB results

---

## Built For

**Gen AI Academy APAC Edition**
Track 2: Connect AI Agents to Real-World Data
Google Cloud × Hack2Skill

---

## License

MIT
