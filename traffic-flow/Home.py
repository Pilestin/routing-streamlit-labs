import folium
from streamlit_folium import st_folium
import streamlit as st

# --- Streamlit page config ---
st.set_page_config(
    page_title="TomTom Traffic Flow Explorer",
    page_icon="🚦",
    layout="wide",
)

# --- Custom CSS for better UI ---
st.markdown("""
    <style>
    .main-header {
        font-size: 2.5rem;
        font-weight: 700;
        color: #1f77b4;
        margin-bottom: 0.5rem;
    }
    .subtitle {
        font-size: 1.1rem;
        color: #666;
        margin-bottom: 2rem;
    }
    .metric-container {
        background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
        padding: 1rem;
        border-radius: 10px;
        color: white;
        text-align: center;
    }
    .info-box {
        background-color: #f0f9ff;
        border-left: 4px solid #0ea5e9;
        padding: 1rem;
        border-radius: 5px;
        margin: 1rem 0;
    }
    .stButton>button {
        width: 100%;
        border-radius: 5px;
        height: 3em;
        background-color: #0ea5e9;
        color: white;
    }
    </style>
""", unsafe_allow_html=True)

st.markdown('<p class="main-header">🚦 TomTom Traffic Flow Explorer</p>', unsafe_allow_html=True)
st.markdown('<p class="subtitle">Explore live traffic flow and incidents on an interactive map</p>', unsafe_allow_html=True)

# --- Predefined regions with more cities ---
REGIONS = {
    "🌍 Global": {"lat": 20.0, "lon": 0.0, "zoom": 2},
    "🇹🇷 Turkey": {"lat": 39.0, "lon": 35.0, "zoom": 5},
    "🏙️ Istanbul": {"lat": 41.015137, "lon": 28.97953, "zoom": 11},
    "🏛️ Ankara": {"lat": 39.9334, "lon": 32.8597, "zoom": 11},
    "🌊 Izmir": {"lat": 38.4237, "lon": 27.1428, "zoom": 11},
    "🕌 Bursa": {"lat": 40.1826, "lon": 29.0665, "zoom": 11},
    "🏖️ Antalya": {"lat": 36.8969, "lon": 30.7133, "zoom": 11},
    "🇩🇪 Berlin": {"lat": 52.52, "lon": 13.405, "zoom": 11},
    "🇺🇸 New York": {"lat": 40.7128, "lon": -74.006, "zoom": 11},
    "🇯🇵 Tokyo": {"lat": 35.6762, "lon": 139.6503, "zoom": 10},
    "🇬🇧 London": {"lat": 51.5074, "lon": -0.1278, "zoom": 11},
    "🇫🇷 Paris": {"lat": 48.8566, "lon": 2.3522, "zoom": 11},
}

BASEMAP_OPTIONS = {
    "🌟 CartoDB Positron (Light)": "CartoDB positron",
    "🗺️ OpenStreetMap": "OpenStreetMap",
    "🌙 Dark Matter (Dark)": "CartoDB dark_matter",
    "🏔️ OpenTopoMap": "https://{s}.tile.opentopomap.org/{z}/{x}/{y}.png",
}

# --- Sidebar controls ---
with st.sidebar:
    st.image("https://via.placeholder.com/300x80/0ea5e9/ffffff?text=TomTom+Traffic", use_container_width=True)
    
    st.header("⚙️ Map Settings")
    
    # Region selection
    region_name = st.selectbox(
        "📍 Select Region / City",
        list(REGIONS.keys()),
        index=2  # Default to Istanbul
    )
    
    # Base map selection
    map_style = st.selectbox(
        "🗺️ Map Style",
        list(BASEMAP_OPTIONS.keys()),
        index=0,
    )
    
    st.markdown("---")
    st.header("🔑 TomTom API Settings")
    
    # API Key input
    tomtom_key = st.text_input(
        "API Key",
        help="Get a free API key at: https://developer.tomtom.com",
        type="password",
        placeholder="Enter your API key here"
    )
    
    # Show API key status
    if tomtom_key.strip():
        st.success("✅ API Key detected")
    else:
        st.warning("⚠️ No API Key entered")
    
    st.markdown("---")
    st.header("📊 Layer Settings")
    
    # Traffic flow layer (always on if API key is provided)
    show_flow = st.checkbox("🚗 Traffic Flow", value=True, disabled=not tomtom_key.strip())
    
    # Incident layer
    add_incident_layer = st.checkbox("⚠️ Traffic Incidents", value=False, disabled=not tomtom_key.strip())
    
    # Opacity control
    layer_opacity = st.slider("Layer Opacity", 0.0, 1.0, 0.7, 0.1)
    
    st.markdown("---")
    st.header("🎨 Appearance")
    
    show_marker = st.checkbox("📍 Center Marker", value=True)
    map_height = st.slider("Map Height (px)", 400, 800, 600, 50)
    
    st.markdown("---")
    st.caption("💡 **Tip:** You can toggle map layers on/off using the control panel in the top-right corner.")

# Get selected region
region = REGIONS[region_name]

# --- Create base Folium map ---
folium_map = folium.Map(
    location=(region["lat"], region["lon"]),
    zoom_start=region["zoom"],
    control_scale=True,
    tiles=None,
    prefer_canvas=True,
)

# --- Add selected base map layer ---
selected_map = BASEMAP_OPTIONS[map_style]
if selected_map.startswith("http"):
    folium.TileLayer(
        tiles=selected_map,
        name=map_style,
        attr="&copy; OpenTopoMap contributors",
    ).add_to(folium_map)
else:
    folium.TileLayer(
        selected_map,
        name=map_style,
    ).add_to(folium_map)

# --- Marker for the selected region center ---
if show_marker:
    folium.Marker(
        location=(region["lat"], region["lon"]),
        popup=folium.Popup(f"<b>{region_name}</b><br>Lat: {region['lat']}<br>Lon: {region['lon']}", max_width=200),
        tooltip=region_name,
        icon=folium.Icon(color="red", icon="info-sign")
    ).add_to(folium_map)

# --- TomTom traffic layers ---
clean_key = tomtom_key.strip()

if clean_key:
    # Traffic Flow Layer
    if show_flow:
        flow_url = f"https://api.tomtom.com/traffic/map/4/tile/flow/relative/{{z}}/{{x}}/{{y}}.png?key={clean_key}"
        folium.raster_layers.TileLayer(
            tiles=flow_url,
            name="🚗 Traffic Flow",
            attr="TomTom Traffic",
            overlay=True,
            control=True,
            opacity=layer_opacity,
            show=True,
        ).add_to(folium_map)
    
    # Incident Layer
    if add_incident_layer:
        incident_url = f"https://api.tomtom.com/traffic/map/4/tile/incidents/s3/{{z}}/{{x}}/{{y}}.png?key={clean_key}"
        folium.raster_layers.TileLayer(
            tiles=incident_url,
            name="⚠️ Traffic Incidents",
            attr="TomTom Traffic",
            overlay=True,
            control=True,
            opacity=layer_opacity,
            show=True,
        ).add_to(folium_map)
    
    # Success message
    col1, col2, col3 = st.columns(3)
    with col1:
        st.metric("🗺️ Map Style", map_style.split(" ")[1] if " " in map_style else map_style)
    with col2:
        st.metric("📍 Location", region_name.split(" ")[1] if " " in region_name else region_name)
    with col3:
        layers_active = sum([show_flow, add_incident_layer])
        st.metric("📊 Active Layers", f"{layers_active}/2")

else:
    # Info message when no API key
    st.info(
        "🔑 **TomTom API Key Required**\n\n"
        "To view live traffic flow and incident layers, enter your API key in the sidebar.\n\n"
        "Get a free API key at: [TomTom Developer Portal](https://developer.tomtom.com)"
    )

# --- Layer control ---
folium.LayerControl(position='topright', collapsed=False).add_to(folium_map)

# --- Display map ---
st.markdown("### 🗺️ Interactive Map")

with st.spinner("Loading map..."):
    map_data = st_folium(
        folium_map, 
        height=map_height, 
        width=None,
        returned_objects=["last_clicked", "last_object_clicked", "bounds", "zoom"]
    )

# --- Map interaction details ---
with st.expander("📊 Map Interaction Details", expanded=False):
    st.write("Your map interactions (zoom, pan, click) will appear here.")
    
    if map_data:
        col1, col2 = st.columns(2)
        
        with col1:
            if map_data.get("zoom"):
                st.metric("🔍 Zoom Level", map_data["zoom"])
            if map_data.get("center"):
                st.write("**📍 Center Coordinates:**")
                st.code(f"Lat: {map_data['center']['lat']:.4f}\nLon: {map_data['center']['lng']:.4f}")
        
        with col2:
            if map_data.get("bounds"):
                st.write("**🗺️ Map Bounds:**")
                bounds = map_data["bounds"]
                st.code(f"NE: [{bounds['_northEast']['lat']:.4f}, {bounds['_northEast']['lng']:.4f}]\nSW: [{bounds['_southWest']['lat']:.4f}, {bounds['_southWest']['lng']:.4f}]")
        
        st.json(map_data)

# --- Footer ---
st.markdown("---")
st.markdown("""
<div style='text-align: center; color: #666;'>
    <p>🚦 TomTom Traffic Flow Explorer | Powered by Claude | 
    <a href='https://developer.tomtom.com' target='_blank'>TomTom API Documentation</a></p>
</div>
""", unsafe_allow_html=True)