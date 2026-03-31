"""
ARIA — Adaptive Response Intelligence Agent
Streamlit Dashboard Entry Point
"""

import asyncio
import json
import queue
import re
import threading
import uuid
from datetime import datetime

import streamlit as st
from streamlit_folium import st_folium

# ─── Page config (must be first) ─────────────────────────────────────────────
st.set_page_config(
    page_title="ARIA — Disaster Response Agent",
    page_icon="🆘",
    layout="wide",
    initial_sidebar_state="expanded",
)

from ui.components import (
    render_header,
    render_tool_feed,
    render_severity_banner,
    render_services_checklist,
    render_history_card,
    render_empty_state,
)
from ui.map_utils import build_disaster_map
from agent.aria_agent import stream_aria
from config.settings import GOOGLE_MAPS_API_KEY


# ─── Helpers ─────────────────────────────────────────────────────────────────
def geocode_location(location: str) -> tuple[float, float]:
    try:
        import httpx
        with httpx.Client(timeout=8.0) as client:
            resp = client.get(
                "https://maps.googleapis.com/maps/api/geocode/json",
                params={"address": location, "key": GOOGLE_MAPS_API_KEY},
            )
            data = resp.json()
            if data["status"] == "OK":
                loc = data["results"][0]["geometry"]["location"]
                return loc["lat"], loc["lng"]
    except Exception:
        pass
    return 13.0827, 80.2707  # Default: Chennai


def parse_section(text: str, header: str) -> str:
    pattern = rf"##\s*{re.escape(header)}(.*?)(?=##|\Z)"
    match = re.search(pattern, text, re.DOTALL | re.IGNORECASE)
    return match.group(1).strip() if match else text


def extract_json_arrays(text: str, key: str) -> list[dict]:
    results = []
    try:
        blocks = re.findall(r'\{[^{}]*\}', text)
        for block in blocks:
            try:
                obj = json.loads(block)
                if key in obj:
                    results.append(obj)
            except Exception:
                pass
    except Exception:
        pass
    return results


def classify_disaster(text: str) -> str:
    text_lower = text.lower()
    for dtype in ["earthquake", "flood", "cyclone", "typhoon", "fire",
                  "wildfire", "tsunami", "volcano", "landslide"]:
        if dtype in text_lower:
            return dtype
    return "earthquake"


def extract_impact_metrics(text: str) -> dict:
    """Extract casualty/impact estimates from agent response."""
    metrics = {
        "population": None,
        "casualties": None,
        "buildings": None,
        "infrastructure": None,
    }
    pop_m = re.search(
        r'(\d[\d,\.]+\s*(?:million|thousand|hundred)?\s*(?:people|residents|population))',
        text, re.IGNORECASE
    )
    if pop_m:
        metrics["population"] = pop_m.group(1).strip()

    cas_m = re.search(
        r'(\d+[\d,\-–]+\d*\s*(?:possible|estimated|potential)?\s*casual(?:ties|ty))',
        text, re.IGNORECASE
    )
    if cas_m:
        metrics["casualties"] = cas_m.group(1).strip()

    bld_m = re.search(
        r'(\d[\d,\.]+\s*(?:buildings?|structures?|homes?)\s*(?:at risk|affected|damaged))',
        text, re.IGNORECASE
    )
    if bld_m:
        metrics["buildings"] = bld_m.group(1).strip()

    return metrics


LANG_FLAGS = {
    "Tamil": "🏴", "Telugu": "🏴", "Kannada": "🏴", "Malayalam": "🏴",
    "Hindi": "🇮🇳", "Marathi": "🇮🇳", "Gujarati": "🇮🇳", "Bengali": "🇧🇩",
    "Bahasa Indonesia": "🇮🇩", "Filipino": "🇵🇭", "Thai": "🇹🇭",
    "Vietnamese": "🇻🇳", "Malay": "🇲🇾",
}

LANG_SCRIPTS = {
    "Tamil": "தமிழ்", "Telugu": "తెలుగు", "Kannada": "ಕನ್ನಡ",
    "Malayalam": "മലയാളം", "Hindi": "हिंदी", "Marathi": "मराठी",
    "Gujarati": "ગુજરાતી", "Bengali": "বাংলা", "Odia": "ଓଡ଼ିଆ",
    "Assamese": "অসমীয়া", "Punjabi": "ਪੰਜਾਬੀ",
}


def render_translation_tab(translation_text: str):
    """Parse and display the MULTILINGUAL ALERTS section beautifully."""
    if not translation_text or len(translation_text.strip()) < 20:
        st.info("No translations available for this scenario. Translations appear for APAC region disasters.")
        return

    # Parse lines like: **Tamil (தமிழ்):** text
    entries = re.findall(
        r'\*\*([^\*]+?)\s*(?:\([^)]*\))?\s*:\*\*\s*(.+?)(?=\n\*\*|\Z)',
        translation_text, re.DOTALL
    )
    # Also try: **Tamil (தமிழ்):** text on same line
    if not entries:
        entries = re.findall(
            r'\*\*([^\*:]+?)(?:\s*\([^)]*\))?\*\*\s*[:\-]\s*(.+?)(?=\n|$)',
            translation_text
        )

    if not entries:
        # Fallback: just render raw markdown
        st.markdown(translation_text)
        return

    st.markdown("""
        <div style='color:#8892b0;font-size:0.75rem;font-weight:600;
                    letter-spacing:1.5px;text-transform:uppercase;margin-bottom:1rem;'>
            🌐 Civilian Alert — All Regional Languages
        </div>
    """, unsafe_allow_html=True)

    cols = st.columns(2)
    for i, (lang, text) in enumerate(entries):
        lang = lang.strip()
        text = text.strip()
        script = LANG_SCRIPTS.get(lang, "")
        flag = LANG_FLAGS.get(lang, "🌍")
        with cols[i % 2]:
            st.markdown(f"""
                <div style='
                    background: #080d18;
                    border: 1px solid #1e2a3a;
                    border-left: 3px solid #4a90e2;
                    border-radius: 10px;
                    padding: 1rem;
                    margin-bottom: 0.7rem;
                '>
                    <div style='
                        color: #64b5f6;
                        font-size: 0.8rem;
                        font-weight: 700;
                        letter-spacing: 0.5px;
                        margin-bottom: 0.4rem;
                    '>{flag} {lang} {f"· <span style='color:#556677'>{script}</span>" if script else ""}</div>
                    <div style='
                        color: #ccd6f6;
                        font-size: 0.95rem;
                        line-height: 1.6;
                    '>{text}</div>
                </div>
            """, unsafe_allow_html=True)


def extract_severity(text: str) -> str:
    t = text.lower()
    if any(w in t for w in ["catastrophic", "extreme", "critical", "magnitude 7", "magnitude 8", "major"]):
        return "CRITICAL"
    if any(w in t for w in ["high", "severe", "serious", "magnitude 6"]):
        return "HIGH"
    if any(w in t for w in ["moderate", "medium", "magnitude 5", "moderate"]):
        return "MODERATE"
    return "LOW"


# ─── Session state ────────────────────────────────────────────────────────────
defaults = {
    "response": "",
    "tool_calls": [],
    "shelters": [],
    "hospitals": [],
    "epicenter": (13.0827, 80.2707),
    "disaster_type": "earthquake",
    "disaster_label": "",
    "running": False,
    "session_id": str(uuid.uuid4()),
    "history": [],
    "severity": "MODERATE",
    "last_error": "",
}
for k, v in defaults.items():
    if k not in st.session_state:
        st.session_state[k] = v


# ─── Streaming agent runner ───────────────────────────────────────────────────
def run_agent(disaster_input: str, label: str = "") -> str:
    """Run ARIA with live streaming updates to Streamlit UI."""
    st.session_state.tool_calls = []
    st.session_state.response = ""
    st.session_state.running = True

    output_queue: queue.Queue = queue.Queue()
    session_id = st.session_state.session_id

    def _thread():
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)

        async def _collect():
            async for event_type, content in stream_aria(disaster_input, session_id):
                output_queue.put((event_type, content))
            output_queue.put(("done", None))

        try:
            loop.run_until_complete(_collect())
        except Exception as exc:
            output_queue.put(("error", exc))
        finally:
            loop.close()

    t = threading.Thread(target=_thread, daemon=True)
    t.start()

    # Live streaming UI
    st.markdown("---")
    tool_placeholder = st.empty()
    st.markdown("#### 📡 Live Agent Response")
    response_placeholder = st.empty()

    full_response = ""
    tool_calls: list[str] = []

    while True:
        try:
            event_type, content = output_queue.get(timeout=0.3)
        except queue.Empty:
            continue

        if event_type == "done":
            break
        elif event_type == "error":
            st.session_state.running = False
            st.session_state.last_error = str(content)
            return ""
        elif event_type == "tool_call":
            tool_calls.append(content)
            st.session_state.tool_calls = tool_calls.copy()
            with tool_placeholder.container():
                render_tool_feed(tool_calls, active=True)
        elif event_type == "response":
            full_response += content
            st.session_state.response = full_response
            response_placeholder.markdown(
                f"""<div style='background:#080d18;border:1px solid #1e2a3a;border-radius:12px;
                              padding:1.2rem;color:#ccd6f6;line-height:1.7;font-size:0.88rem;'>
                    {full_response.replace(chr(10), '<br>')}
                </div>""",
                unsafe_allow_html=True,
            )

    # Final tool feed (all done)
    with tool_placeholder.container():
        render_tool_feed(tool_calls, active=False)

    t.join(timeout=5)
    st.session_state.running = False

    # Save to history
    severity = extract_severity(full_response)
    st.session_state.severity = severity
    hist = {
        "label": label or disaster_input[:60],
        "response": full_response,
        "tool_calls": tool_calls,
        "severity": severity,
        "timestamp": datetime.now().strftime("%H:%M"),
        "disaster_type": st.session_state.disaster_type,
    }
    history = st.session_state.history
    history.append(hist)
    st.session_state.history = history[-3:]  # keep last 3

    return full_response


# ─── Layout ───────────────────────────────────────────────────────────────────
render_header()

# ─── Sidebar ─────────────────────────────────────────────────────────────────
with st.sidebar:
    st.markdown("""
        <div style='color:#e94560;font-weight:700;font-size:0.8rem;
                    letter-spacing:2px;text-transform:uppercase;margin-bottom:0.5rem;'>
            🚨 Incident Report
        </div>
    """, unsafe_allow_html=True)

    disaster_text = st.text_area(
        "Describe the disaster",
        placeholder="e.g. Earthquake magnitude 6.2 in Chennai, India. Multiple buildings collapsed.",
        height=110,
        key="disaster_input",
    )

    location_input = st.text_input(
        "📍 Primary location",
        placeholder="e.g. Chennai, India",
        key="location_input",
    )

    col1, col2 = st.columns(2)
    with col1:
        disaster_type_input = st.selectbox(
            "Type",
            ["earthquake", "flood", "cyclone", "typhoon",
             "wildfire", "tsunami", "volcano", "landslide"],
            key="disaster_type_select",
        )
    with col2:
        language_input = st.selectbox(
            "Language",
            ["Tamil", "Hindi", "Bahasa Indonesia", "Filipino", "Thai", "Vietnamese"],
            key="language_select",
        )

    trigger_btn = st.button(
        "🆘 Activate ARIA Response",
        type="primary",
        use_container_width=True,
        disabled=st.session_state.running,
    )

    # History
    if st.session_state.history:
        st.markdown("---")
        st.markdown("""
            <div style='color:#8892b0;font-weight:600;font-size:0.75rem;
                        letter-spacing:1.5px;text-transform:uppercase;margin-bottom:0.5rem;'>
                📋 Recent Scenarios
            </div>
        """, unsafe_allow_html=True)
        for i, hist in enumerate(reversed(st.session_state.history)):
            render_history_card(hist)
            if st.button(f"Load #{len(st.session_state.history) - i}", key=f"load_hist_{i}",
                         use_container_width=True):
                st.session_state.response = hist["response"]
                st.session_state.tool_calls = hist["tool_calls"]
                st.session_state.severity = hist["severity"]
                st.session_state.disaster_type = hist["disaster_type"]
                st.rerun()

    st.markdown("---")
    st.markdown("""
        <div style='color:#8892b0;font-weight:600;font-size:0.72rem;
                    letter-spacing:1.5px;text-transform:uppercase;margin-bottom:0.5rem;'>
            ☁️ Google Cloud Stack
        </div>
    """, unsafe_allow_html=True)
    for svc in [
        "Vertex AI · Gemini 2.5 Flash",
        "Google ADK · MCP × 7",
        "Google Maps Platform",
        "AlloyDB AI · pgvector",
        "Google Translate API",
        "Firebase Realtime DB",
        "GDACS · Open-Meteo",
    ]:
        st.markdown(f"<small style='color:#445566;'>✦ {svc}</small>", unsafe_allow_html=True)


# ─── Trigger ─────────────────────────────────────────────────────────────────
if trigger_btn and disaster_text.strip():
    st.session_state.disaster_type = disaster_type_input
    st.session_state.disaster_label = disaster_text.strip()[:60]

    full_input = (
        f"{disaster_text.strip()}. Location: {location_input.strip()}. "
        f"Primary local language for civilian alerts: {language_input}."
        if location_input.strip()
        else disaster_text.strip()
    )

    lat, lon = geocode_location(location_input or disaster_text)
    st.session_state.epicenter = (lat, lon)

    with st.spinner("ARIA is coordinating disaster response..."):
        run_agent(full_input, label=disaster_text.strip()[:60])

    st.rerun()

elif trigger_btn:
    st.warning("Please describe the disaster before activating ARIA.")


# ─── Main content ─────────────────────────────────────────────────────────────
if st.session_state.response:
    response = st.session_state.response
    severity = st.session_state.severity
    location_label = st.session_state.get("disaster_label", "")

    # Severity banner
    render_severity_banner(
        severity,
        st.session_state.disaster_type,
        location_label,
    )

    # Impact metrics row
    metrics = extract_impact_metrics(response)
    if any(metrics.values()):
        m1, m2, m3, m4 = st.columns(4)
        with m1:
            st.metric("👥 Population Affected",
                      metrics["population"] or "Assessing...",
                      help="Estimated from regional population density")
        with m2:
            st.metric("⚠️ Casualty Estimate",
                      metrics["casualties"] or "Assessing...",
                      help="Model estimate — verify with ground teams")
        with m3:
            st.metric("🏢 Structures at Risk",
                      metrics["buildings"] or "Assessing...",
                      help="Based on affected zone radius")
        with m4:
            st.metric("🔧 Tools Activated",
                      f"{len(st.session_state.tool_calls)} / 7",
                      help="MCP servers called during this response")

    # Two-column layout
    left_col, right_col = st.columns([3, 2], gap="medium")

    with left_col:
        # Role tabs
        tab1, tab2, tab3, tab4 = st.tabs(
            ["👮 Command Center", "🦺 Field Responder", "👥 Civilian", "🌐 Translations"]
        )
        with tab1:
            st.markdown(parse_section(response, "COMMAND CENTER BRIEFING"))
        with tab2:
            st.markdown(parse_section(response, "FIELD RESPONDER GUIDE"))
        with tab3:
            st.markdown(parse_section(response, "CIVILIAN INFORMATION"))
        with tab4:
            render_translation_tab(parse_section(response, "MULTILINGUAL ALERTS"))

        # Action row
        col_dl, col_new = st.columns(2)
        with col_dl:
            ts = datetime.now().strftime("%Y%m%d_%H%M%S")
            st.download_button(
                "📥 Download Report",
                data=response.encode("utf-8"),
                file_name=f"aria_report_{ts}.txt",
                mime="text/plain",
                use_container_width=True,
            )
        with col_new:
            if st.button("🔄 New Incident", use_container_width=True):
                for key in ["response", "tool_calls", "severity", "disaster_label"]:
                    st.session_state[key] = defaults[key]
                st.session_state.session_id = str(uuid.uuid4())
                st.rerun()

        # Full response expander
        with st.expander("📄 Full Raw Agent Response"):
            st.code(response, language="markdown")

    with right_col:
        # Map
        st.markdown("""
            <div style='color:#8892b0;font-size:0.75rem;font-weight:600;
                        letter-spacing:1.5px;text-transform:uppercase;margin-bottom:0.5rem;'>
                🗺️ Live Disaster Map
            </div>
        """, unsafe_allow_html=True)

        shelters = extract_json_arrays(response, "available_capacity") or st.session_state.shelters
        hospitals = extract_json_arrays(response, "emergency_beds") or st.session_state.hospitals

        m = build_disaster_map(
            epicenter_lat=st.session_state.epicenter[0],
            epicenter_lon=st.session_state.epicenter[1],
            disaster_type=st.session_state.disaster_type,
            shelters=shelters,
            hospitals=hospitals,
        )
        st_folium(m, height=380, width=None, returned_objects=[])

        st.markdown("<div style='margin-top:0.8rem;'>", unsafe_allow_html=True)

        # Tool feed summary
        if st.session_state.tool_calls:
            render_tool_feed(st.session_state.tool_calls, active=False)

        # Services checklist
        render_services_checklist(st.session_state.tool_calls)

        st.markdown("</div>", unsafe_allow_html=True)

else:
    # Show any error that survived the rerun
    if st.session_state.get("last_error"):
        st.error(f"Agent error: {st.session_state.last_error}")
        st.session_state.last_error = ""

    # Empty state + demo buttons
    render_empty_state()

    st.markdown("---")
    st.markdown("""
        <div style='color:#8892b0;font-size:0.75rem;font-weight:600;
                    letter-spacing:1.5px;text-transform:uppercase;margin-bottom:1rem;'>
            ⚡ Quick Demo Scenarios
        </div>
    """, unsafe_allow_html=True)

    demos = [
        ("🌊 Chennai Earthquake", "Earthquake magnitude 6.2 reported in Chennai, India. Multiple buildings collapsed near the city centre.", "Chennai, India", "earthquake"),
        ("🌀 Jakarta Flood",      "Severe flooding in Jakarta, Indonesia following heavy monsoon rains. Multiple districts submerged.",       "Jakarta, Indonesia",  "flood"),
        ("🌪️ Manila Typhoon",    "Category 4 typhoon making landfall near Manila, Philippines. Evacuation orders in effect.",               "Manila, Philippines", "typhoon"),
    ]

    demo_cols = st.columns(3)
    for col, (label, text, loc, dtype) in zip(demo_cols, demos):
        with col:
            st.markdown(f"""
                <div style='
                    background:#080d18;border:1px solid #1e2a3a;border-radius:12px;
                    padding:1rem;text-align:center;margin-bottom:0.5rem;
                '>
                    <div style='font-size:1.8rem;margin-bottom:0.3rem;'>{label.split()[0]}</div>
                    <div style='color:#8892b0;font-size:0.78rem;'>{loc}</div>
                </div>
            """, unsafe_allow_html=True)
            if st.button(label, use_container_width=True, key=f"demo_{dtype}"):
                st.session_state.disaster_type = dtype
                st.session_state.disaster_label = label
                lat, lon = geocode_location(loc)
                st.session_state.epicenter = (lat, lon)
                with st.spinner(f"ARIA responding to {label}..."):
                    run_agent(f"{text} Location: {loc}.", label=label)
                st.rerun()
