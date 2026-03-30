"""
Map utilities for ARIA Streamlit dashboard.
"""

import folium
from folium.plugins import MarkerCluster


DISASTER_CONFIG = {
    "earthquake": {"color": "#FF2244", "emoji": "🔴", "radius": 20000},
    "flood":      {"color": "#2196F3", "emoji": "🔵", "radius": 25000},
    "cyclone":    {"color": "#9C27B0", "emoji": "🟣", "radius": 30000},
    "typhoon":    {"color": "#9C27B0", "emoji": "🟣", "radius": 30000},
    "fire":       {"color": "#FF6600", "emoji": "🟠", "radius": 15000},
    "wildfire":   {"color": "#FF6600", "emoji": "🟠", "radius": 20000},
    "tsunami":    {"color": "#00BCD4", "emoji": "🔵", "radius": 35000},
    "volcano":    {"color": "#FF3300", "emoji": "🔴", "radius": 15000},
    "landslide":  {"color": "#795548", "emoji": "🟤", "radius": 10000},
}


def _div_icon(emoji: str, bg: str, size: int = 36) -> folium.DivIcon:
    return folium.DivIcon(
        html=f"""
            <div style='
                width:{size}px;height:{size}px;
                background:{bg};
                border-radius:50%;
                display:flex;align-items:center;justify-content:center;
                font-size:{size//2}px;
                box-shadow:0 0 12px {bg}88, 0 0 24px {bg}44;
                border:2px solid white;
                cursor:pointer;
            '>{emoji}</div>
        """,
        icon_size=(size, size),
        icon_anchor=(size // 2, size // 2),
    )


def build_disaster_map(
    epicenter_lat: float,
    epicenter_lon: float,
    disaster_type: str,
    shelters: list = None,
    hospitals: list = None,
    zoom_start: int = 10,
) -> folium.Map:

    cfg = DISASTER_CONFIG.get(disaster_type.lower(), DISASTER_CONFIG["earthquake"])

    m = folium.Map(
        location=[epicenter_lat, epicenter_lon],
        zoom_start=zoom_start,
        tiles="CartoDB dark_matter",
    )

    # Pulsing outer ring
    folium.Circle(
        location=[epicenter_lat, epicenter_lon],
        radius=cfg["radius"] * 1.5,
        color=cfg["color"],
        fill=False,
        weight=1,
        opacity=0.3,
        tooltip="Outer warning zone",
    ).add_to(m)

    # Affected zone
    folium.Circle(
        location=[epicenter_lat, epicenter_lon],
        radius=cfg["radius"],
        color=cfg["color"],
        fill=True,
        fill_opacity=0.12,
        weight=2,
        tooltip=f"Estimated affected zone ({cfg['radius']//1000}km radius)",
    ).add_to(m)

    # Epicenter marker
    folium.Marker(
        location=[epicenter_lat, epicenter_lon],
        popup=folium.Popup(
            f"""<div style='font-family:sans-serif;padding:6px;'>
                <b style='color:{cfg['color']};font-size:14px;'>⚠️ DISASTER EPICENTER</b><br>
                <span style='color:#333;'>{disaster_type.upper()}</span><br>
                <small style='color:#666;'>{epicenter_lat:.4f}, {epicenter_lon:.4f}</small>
            </div>""",
            max_width=220,
        ),
        tooltip=f"⚠️ Epicenter: {disaster_type.title()}",
        icon=_div_icon("⚠️", cfg["color"], size=44),
    ).add_to(m)

    # Shelters
    if shelters:
        shelter_cluster = MarkerCluster(
            name="Shelters",
            options={"maxClusterRadius": 40},
        ).add_to(m)

        for s in shelters:
            if not (s.get("latitude") and s.get("longitude")):
                continue
            available = s.get("available_capacity", 0)
            total = s.get("total_capacity", 1)
            pct = (available / total * 100) if total > 0 else 0
            icon_color = "#00CC66" if pct > 30 else "#FFA500" if pct > 10 else "#FF2244"
            amenities = " ".join(filter(None, [
                "🏥" if s.get("has_medical") else "",
                "🍽️" if s.get("has_food") else "",
                "💧" if s.get("has_water") else "",
            ]))
            popup_html = f"""
                <div style='font-family:sans-serif;padding:8px;min-width:180px;'>
                    <b style='color:#1a237e;font-size:13px;'>🏠 {s.get('name','Shelter')}</b><br>
                    <div style='background:#eee;border-radius:4px;height:6px;margin:6px 0;'>
                        <div style='background:{icon_color};width:{pct:.0f}%;height:6px;border-radius:4px;'></div>
                    </div>
                    <span style='color:#333;font-size:12px;'>
                        <b>{available}</b>/{total} spots · {s.get('distance_km','?')} km<br>
                        {amenities}<br>
                        📞 {s.get('contact_phone','N/A')}
                    </span>
                </div>
            """
            folium.Marker(
                location=[s["latitude"], s["longitude"]],
                popup=folium.Popup(popup_html, max_width=240),
                tooltip=f"🏠 {s.get('name','Shelter')} — {available} spots",
                icon=_div_icon("🏠", icon_color, size=32),
            ).add_to(shelter_cluster)

    # Hospitals
    if hospitals:
        for h in hospitals:
            if not (h.get("latitude") and h.get("longitude")):
                continue
            popup_html = f"""
                <div style='font-family:sans-serif;padding:8px;min-width:180px;'>
                    <b style='color:#b71c1c;font-size:13px;'>🏥 {h.get('name','Hospital')}</b><br>
                    <span style='color:#333;font-size:12px;'>
                        Emergency beds: <b>{h.get('emergency_beds','N/A')}</b><br>
                        Distance: {h.get('distance_km','?')} km<br>
                        📞 {h.get('contact_phone','N/A')}
                    </span>
                </div>
            """
            folium.Marker(
                location=[h["latitude"], h["longitude"]],
                popup=folium.Popup(popup_html, max_width=240),
                tooltip=f"🏥 {h.get('name','Hospital')} — {h.get('emergency_beds','?')} beds",
                icon=_div_icon("🏥", "#E53935", size=32),
            ).add_to(m)

    folium.LayerControl(collapsed=False).add_to(m)
    return m
