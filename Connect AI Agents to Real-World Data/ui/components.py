"""
Reusable Streamlit UI components for the ARIA dashboard.
"""

import streamlit as st
from datetime import datetime

SEVERITY_CONFIG = {
    "CRITICAL": {"color": "#FF2244", "glow": "#FF224466", "icon": "🔴", "bg": "#2a0a0f"},
    "HIGH":     {"color": "#FF6600", "glow": "#FF660066", "icon": "🟠", "bg": "#2a1500"},
    "MODERATE": {"color": "#FFA500", "glow": "#FFA50066", "icon": "🟡", "bg": "#2a1e00"},
    "LOW":      {"color": "#00CC66", "glow": "#00CC6666", "icon": "🟢", "bg": "#0a2a15"},
}

TOOL_ICONS = {
    "maps_geocode": "🗺️",
    "get_active_alerts": "🚨",
    "get_weather": "🌤️",
    "get_hazard_conditions": "⚠️",
    "find_shelters": "🏠",
    "find_hospitals": "🏥",
    "get_emergency_contacts": "📞",
    "get_global_emergency_numbers": "🆘",
    "translate_for_region": "🌐",
    "translate_alert": "🌐",
    "push_alert": "📡",
}

GLOBAL_CSS = """
<style>
@import url('https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700&family=JetBrains+Mono:wght@400;600&display=swap');

html, body, [class*="css"] {
    font-family: 'Inter', sans-serif;
}

/* Dark base */
.stApp { background: #0a0e1a; }

/* Hide default header */
header[data-testid="stHeader"] { background: transparent; }

/* Sidebar */
section[data-testid="stSidebar"] {
    background: linear-gradient(180deg, #0d1117 0%, #0a0e1a 100%);
    border-right: 1px solid #1e2a3a;
}
section[data-testid="stSidebar"] .stMarkdown { color: #ccd6f6; }

/* Tab styling */
.stTabs [data-baseweb="tab-list"] {
    background: #0d1117;
    border-radius: 10px;
    padding: 4px;
    gap: 4px;
    border: 1px solid #1e2a3a;
}
.stTabs [data-baseweb="tab"] {
    background: transparent;
    color: #8892b0;
    border-radius: 8px;
    font-weight: 500;
    padding: 8px 16px;
}
.stTabs [aria-selected="true"] {
    background: linear-gradient(135deg, #1e2a4a, #162040) !important;
    color: #64b5f6 !important;
    border: 1px solid #2a3a5a !important;
}

/* Button */
.stButton button {
    background: linear-gradient(135deg, #1565c0, #0d47a1);
    color: white;
    border: none;
    border-radius: 8px;
    font-weight: 600;
    transition: all 0.2s;
}
.stButton button:hover {
    background: linear-gradient(135deg, #1976d2, #1565c0);
    box-shadow: 0 0 20px #1565c044;
    transform: translateY(-1px);
}
button[kind="primary"] {
    background: linear-gradient(135deg, #e94560, #c62828) !important;
    box-shadow: 0 0 20px #e9456044;
}
button[kind="primary"]:hover {
    box-shadow: 0 0 30px #e9456088 !important;
}

/* Expander */
.streamlit-expanderHeader {
    background: #0d1117;
    border: 1px solid #1e2a3a;
    border-radius: 8px;
    color: #8892b0 !important;
}

/* Spinner */
.stSpinner > div { border-top-color: #e94560 !important; }

/* Metrics */
[data-testid="metric-container"] {
    background: #0d1117;
    border: 1px solid #1e2a3a;
    border-radius: 10px;
    padding: 12px;
}

/* Text area & input */
.stTextArea textarea, .stTextInput input {
    background: #0d1117 !important;
    color: #ccd6f6 !important;
    border: 1px solid #1e2a3a !important;
    border-radius: 8px !important;
}
.stSelectbox select, [data-baseweb="select"] {
    background: #0d1117 !important;
    color: #ccd6f6 !important;
}

/* Download button */
.stDownloadButton button {
    background: linear-gradient(135deg, #00695c, #004d40) !important;
    color: white !important;
    border: none !important;
    border-radius: 8px !important;
}

/* Scrollbar */
::-webkit-scrollbar { width: 6px; }
::-webkit-scrollbar-track { background: #0a0e1a; }
::-webkit-scrollbar-thumb { background: #1e2a3a; border-radius: 3px; }

@keyframes pulse-ring {
    0% { box-shadow: 0 0 0 0 var(--pulse-color); }
    70% { box-shadow: 0 0 0 10px transparent; }
    100% { box-shadow: 0 0 0 0 transparent; }
}
@keyframes fade-in {
    from { opacity: 0; transform: translateY(8px); }
    to { opacity: 1; transform: translateY(0); }
}
@keyframes slide-in {
    from { opacity: 0; transform: translateX(-10px); }
    to { opacity: 1; transform: translateX(0); }
}
</style>
"""


def inject_css():
    st.markdown(GLOBAL_CSS, unsafe_allow_html=True)


def render_header():
    inject_css()
    st.markdown("""
        <div style='
            background: linear-gradient(135deg, #0d1117 0%, #0a0e1a 50%, #0d1117 100%);
            padding: 1.8rem 2rem;
            border-radius: 16px;
            margin-bottom: 1.5rem;
            border: 1px solid #1e2a3a;
            position: relative;
            overflow: hidden;
        '>
            <div style='
                position: absolute; top: 0; left: 0; right: 0; height: 3px;
                background: linear-gradient(90deg, #e94560, #4a90e2, #00cc66, #e94560);
                background-size: 200% 100%;
            '></div>
            <div style='display: flex; align-items: center; gap: 1.2rem;'>
                <div style='
                    font-size: 3rem;
                    filter: drop-shadow(0 0 12px #e94560);
                '>🆘</div>
                <div>
                    <h1 style='
                        color: #e6f1ff;
                        margin: 0;
                        font-size: 2.2rem;
                        font-weight: 700;
                        letter-spacing: -0.5px;
                    '>ARIA</h1>
                    <p style='
                        color: #8892b0;
                        margin: 0.2rem 0 0;
                        font-size: 0.9rem;
                        letter-spacing: 0.5px;
                    '>
                        Adaptive Response Intelligence Agent &nbsp;·&nbsp;
                        <span style='color: #4a90e2; font-weight: 500;'>Google ADK</span> &nbsp;·&nbsp;
                        <span style='color: #00cc66; font-weight: 500;'>MCP × 7</span> &nbsp;·&nbsp;
                        <span style='color: #e94560; font-weight: 500;'>AlloyDB AI</span> &nbsp;·&nbsp;
                        <span style='color: #ffa500; font-weight: 500;'>Gemini 2.5</span>
                    </p>
                </div>
            </div>
        </div>
    """, unsafe_allow_html=True)


def render_severity_banner(severity: str, disaster_type: str, location: str = ""):
    cfg = SEVERITY_CONFIG.get(severity, SEVERITY_CONFIG["MODERATE"])
    ts = datetime.now().strftime("%Y-%m-%d %H:%M UTC")
    st.markdown(f"""
        <div style='
            background: {cfg["bg"]};
            border: 1px solid {cfg["color"]}44;
            border-left: 4px solid {cfg["color"]};
            border-radius: 12px;
            padding: 1rem 1.5rem;
            margin-bottom: 1rem;
            animation: fade-in 0.4s ease;
            display: flex;
            align-items: center;
            justify-content: space-between;
        '>
            <div style='display: flex; align-items: center; gap: 1rem;'>
                <span style='font-size: 1.8rem; filter: drop-shadow(0 0 8px {cfg["color"]});'>{cfg["icon"]}</span>
                <div>
                    <div style='color: {cfg["color"]}; font-weight: 700; font-size: 1.1rem; letter-spacing: 1px;'>
                        {severity} ALERT
                    </div>
                    <div style='color: #8892b0; font-size: 0.85rem; margin-top: 2px;'>
                        {disaster_type.title()} · {location}
                    </div>
                </div>
            </div>
            <div style='
                color: #8892b0;
                font-size: 0.75rem;
                font-family: "JetBrains Mono", monospace;
                text-align: right;
            '>
                <div style='color: {cfg["color"]}; font-weight: 600;'>● LIVE</div>
                <div>{ts}</div>
            </div>
        </div>
    """, unsafe_allow_html=True)


def render_tool_feed(tool_calls: list[str], active: bool = False):
    """Render real-time tool call badges."""
    if not tool_calls:
        return

    badges = ""
    for i, tool in enumerate(tool_calls):
        icon = TOOL_ICONS.get(tool, "⚙️")
        is_last = i == len(tool_calls) - 1
        pulse = f"animation: pulse-ring 1.2s ease infinite; --pulse-color: #4a90e244;" if (is_last and active) else ""
        opacity = "1" if not (is_last and active) else "1"
        badges += f"""
            <span style='
                background: #0d1a2e;
                color: #64b5f6;
                border: 1px solid {"#4a90e2" if is_last and active else "#1e3a5a"};
                border-radius: 20px;
                padding: 5px 12px;
                font-size: 0.78rem;
                font-weight: 500;
                display: inline-flex;
                align-items: center;
                gap: 5px;
                margin: 3px;
                opacity: {opacity};
                {pulse}
                animation: slide-in 0.3s ease;
            '>
                {icon} {tool}{"  ⟳" if is_last and active else " ✓"}
            </span>
        """

    label = "⚡ Agent Tools Active" if active else f"⚡ {len(tool_calls)} Tools Executed"
    st.markdown(f"""
        <div style='
            background: #080d18;
            border: 1px solid #1e2a3a;
            border-radius: 12px;
            padding: 0.8rem 1rem;
            margin-bottom: 0.8rem;
        '>
            <div style='color: #8892b0; font-size: 0.75rem; font-weight: 600;
                        letter-spacing: 1px; margin-bottom: 6px; text-transform: uppercase;'>
                {label}
            </div>
            <div style='line-height: 2;'>{badges}</div>
        </div>
    """, unsafe_allow_html=True)


def render_services_checklist(tool_calls: list[str]):
    """Show which Google Cloud services were used."""
    tools_set = set(tool_calls)
    services = [
        ("✅" if "maps_geocode" in tools_set or "maps_directions" in tools_set else "⬜",
         "Google Maps Platform", "#4a90e2"),
        ("✅" if "get_weather" in tools_set or "get_hazard_conditions" in tools_set else "⬜",
         "Open-Meteo Weather", "#00cc66"),
        ("✅" if "get_active_alerts" in tools_set else "⬜",
         "GDACS Disaster Alerts", "#e94560"),
        ("✅" if "find_shelters" in tools_set or "find_hospitals" in tools_set else "⬜",
         "AlloyDB AI + pgvector", "#ffa500"),
        ("✅" if "translate_for_region" in tools_set or "translate_alert" in tools_set else "⬜",
         "Google Translate API", "#ab47bc"),
        ("✅" if "push_alert" in tools_set else "⬜",
         "Firebase Realtime DB", "#ff7043"),
        ("✅", "Vertex AI (Gemini 2.5)", "#26c6da"),
        ("✅", "Google ADK + MCP", "#66bb6a"),
    ]
    items_html = "".join([
        f"<div style='display:flex;align-items:center;gap:8px;padding:4px 0;'>"
        f"<span style='font-size:0.9rem;'>{icon}</span>"
        f"<span style='color:{'#ccd6f6' if icon=='✅' else '#445566'};font-size:0.82rem;'>{name}</span>"
        f"</div>"
        for icon, name, _ in services
    ])
    st.markdown(f"""
        <div style='
            background: #080d18;
            border: 1px solid #1e2a3a;
            border-radius: 12px;
            padding: 1rem;
        '>
            <div style='color: #8892b0; font-size: 0.72rem; font-weight: 600;
                        letter-spacing: 1px; margin-bottom: 8px; text-transform: uppercase;'>
                Google Cloud Services Used
            </div>
            {items_html}
        </div>
    """, unsafe_allow_html=True)


def render_history_card(hist: dict):
    sev = hist.get("severity", "MODERATE")
    cfg = SEVERITY_CONFIG.get(sev, SEVERITY_CONFIG["MODERATE"])
    ts = hist.get("timestamp", "")
    label = hist.get("label", "Scenario")[:35]
    tools_count = len(hist.get("tool_calls", []))
    st.markdown(f"""
        <div style='
            background: #080d18;
            border: 1px solid {cfg["color"]}33;
            border-left: 3px solid {cfg["color"]};
            border-radius: 8px;
            padding: 0.7rem 0.9rem;
            margin-bottom: 0.5rem;
        '>
            <div style='color: #ccd6f6; font-size: 0.82rem; font-weight: 600;'>{cfg["icon"]} {label}...</div>
            <div style='color: #556677; font-size: 0.72rem; margin-top: 3px;'>
                {ts} · {tools_count} tools · {sev}
            </div>
        </div>
    """, unsafe_allow_html=True)


def render_alert_card(title: str, message: str, severity: str, location: str = ""):
    cfg = SEVERITY_CONFIG.get(severity.upper(), SEVERITY_CONFIG["MODERATE"])
    st.markdown(f"""
        <div style='
            border-left: 4px solid {cfg["color"]};
            background: {cfg["bg"]};
            padding: 0.9rem 1.1rem;
            border-radius: 8px;
            margin: 0.5rem 0;
            animation: fade-in 0.3s ease;
        '>
            <div style='display:flex;justify-content:space-between;align-items:center;'>
                <b style='color:#e6f1ff;'>{cfg["icon"]} {title}</b>
                <span style='
                    background:{cfg["color"]}22;
                    color:{cfg["color"]};
                    border:1px solid {cfg["color"]}55;
                    padding:2px 10px;
                    border-radius:12px;
                    font-size:0.72rem;
                    font-weight:600;
                '>{severity.upper()}</span>
            </div>
            {f"<p style='color:#8892b0;margin:0.3rem 0 0;font-size:0.8rem;'>📍 {location}</p>" if location else ""}
            <p style='color:#ccd6f6;margin:0.5rem 0 0;font-size:0.85rem;line-height:1.5;'>{message}</p>
        </div>
    """, unsafe_allow_html=True)


def render_contact_card(agency: str, phone: str, email: str = "", description: str = ""):
    st.markdown(f"""
        <div style='
            background: #0d1a2e;
            border-radius: 10px;
            padding: 0.9rem 1.1rem;
            margin: 0.4rem 0;
            border: 1px solid #1e3a5a;
            animation: fade-in 0.3s ease;
        '>
            <b style='color:#64b5f6;font-size:0.9rem;'>{agency}</b><br>
            <span style='color:#e6f1ff;font-size:1.05rem;font-weight:600;'>📞 {phone}</span>
            {f"<br><span style='color:#8892b0;font-size:0.8rem;'>✉️ {email}</span>" if email else ""}
            {f"<br><span style='color:#556677;font-size:0.78rem;margin-top:4px;display:block;'>{description}</span>" if description else ""}
        </div>
    """, unsafe_allow_html=True)


def render_shelter_card(shelter: dict):
    available = shelter.get("available_capacity", 0)
    total = shelter.get("total_capacity", 1)
    pct = (available / total * 100) if total > 0 else 0
    bar_color = "#00cc66" if pct > 30 else "#ffa500" if pct > 10 else "#e94560"
    amenities = "".join([
        "🏥 Medical &nbsp;" if shelter.get("has_medical") else "",
        "🍽️ Food &nbsp;" if shelter.get("has_food") else "",
        "💧 Water" if shelter.get("has_water") else "",
    ])
    st.markdown(f"""
        <div style='
            background: #0a1a0a;
            border-radius: 10px;
            padding: 0.9rem 1.1rem;
            margin: 0.4rem 0;
            border: 1px solid #1a3a1a;
            animation: fade-in 0.3s ease;
        '>
            <div style='display:flex;justify-content:space-between;align-items:center;'>
                <b style='color:#66cc66;'>🏠 {shelter.get("name", "Unknown")}</b>
                <span style='color:#8892b0;font-size:0.78rem;'>
                    {shelter.get("distance_km", "?")} km away
                </span>
            </div>
            <div style='background:#1a2a1a;border-radius:4px;height:5px;margin:0.6rem 0;overflow:hidden;'>
                <div style='background:{bar_color};width:{pct:.0f}%;height:5px;
                            border-radius:4px;transition:width 0.5s ease;'></div>
            </div>
            <div style='display:flex;justify-content:space-between;align-items:center;'>
                <span style='color:#ccd6f6;font-size:0.85rem;'>
                    <b style='color:white;'>{available}</b>/{total} spots free
                </span>
                <span style='color:#8892b0;font-size:0.78rem;'>{amenities}</span>
            </div>
            <div style='color:#4a90e2;font-size:0.82rem;margin-top:0.4rem;'>
                📞 {shelter.get("contact_phone", "N/A")}
            </div>
        </div>
    """, unsafe_allow_html=True)


def render_tool_call_badge(tool_name: str):
    icon = TOOL_ICONS.get(tool_name, "⚙️")
    st.markdown(f"""
        <span style='
            background:#0d1a2e;color:#64b5f6;
            border:1px solid #1e3a5a;
            border-radius:20px;padding:4px 12px;
            font-size:0.75rem;font-weight:500;
            display:inline-flex;align-items:center;gap:5px;margin:2px;
        '>{icon} {tool_name} ✓</span>
    """, unsafe_allow_html=True)


def render_translation_block(translations: dict):
    if not translations:
        return
    st.markdown("**🌐 Multilingual Alert**")
    for lang, data in translations.items():
        if isinstance(data, dict) and "text" in data:
            with st.expander(f"🌍 {lang}"):
                st.markdown(f"""
                    <div style='
                        background:#0d1117;border-radius:8px;padding:0.8rem;
                        border-left:3px solid #4a90e2;color:#ccd6f6;font-size:0.9rem;
                        line-height:1.6;
                    '>{data["text"]}</div>
                """, unsafe_allow_html=True)


def render_empty_state():
    st.markdown("""
        <div style='
            text-align: center;
            padding: 4rem 2rem;
            background: #080d18;
            border: 1px solid #1e2a3a;
            border-radius: 16px;
            margin-top: 1rem;
        '>
            <div style='font-size: 4rem; margin-bottom: 1rem; filter: drop-shadow(0 0 20px #e94560);'>🆘</div>
            <h2 style='color: #ccd6f6; margin: 0 0 0.5rem; font-weight: 600;'>ARIA is Standing By</h2>
            <p style='color: #556677; margin: 0; font-size: 0.95rem;'>
                Report a disaster in the sidebar to activate the response agent.
            </p>
            <p style='color: #2a3a4a; margin: 1rem 0 0; font-size: 0.8rem;'>
                Google ADK · MCP · AlloyDB AI · Vertex AI · Gemini 2.5 · Firebase
            </p>
        </div>
    """, unsafe_allow_html=True)
