import streamlit as st
import requests
import pandas as pd
from streamlit_folium import st_folium
import folium
import os 
# .env API key
from dotenv import load_dotenv

load_dotenv()

st.set_page_config(page_title="Charging Stations", layout="wide")

st.title("Electric Vehicle Charging Stations Map (Open Charge Map)")

# Allow user to enter API key (with fallback to .env)
API_KEY = st.text_input("Open Charge Map API Key", type="password")
if not API_KEY:
    API_KEY = os.getenv("API_KEY")
if not API_KEY:
    st.warning("Please provide an API key for Open Charge Map.")
    st.stop()

col1, col2, col3 = st.columns(3)
with col1:
    lat = st.number_input("Latitude", value=39.766)
with col2:
    lon = st.number_input("Longitude", value=30.525)
with col3:
    dist = st.slider("Search Radius (km)", 1, 50, 5)

url = (
    f"https://api.openchargemap.io/v3/poi/?output=json"
    f"&latitude={lat}&longitude={lon}"
    f"&distance={dist}&distanceunit=KM&key={API_KEY}"
)

response = requests.get(url)

if response.status_code != 200:
    st.error(f"API Error: {response.status_code}")
    st.stop()

data = response.json()

if data:
    # Process data in more detail
    station_list = []
    for item in data:
        addr = item.get("AddressInfo", {})
        operator = item.get("OperatorInfo", {})
        status = item.get("StatusType", {})
        usage_cost = item.get("UsageCost")
        
        # Get connection details
        connections = item.get("Connections", [])
        conn_types = []
        max_power = 0
        
        for c in connections:
            if c.get("ConnectionType"):
                conn_types.append(c["ConnectionType"].get("Title", ""))
            
            # Find maximum power (kW)
            power = c.get("PowerKW")
            if power and power > max_power:
                max_power = power
                
        conn_str = ", ".join(list(set(conn_types))) if conn_types else "-"
        
        station_list.append({
            "name": addr.get("Title", "Unknown"),
            "lat": addr.get("Latitude"),
            "lon": addr.get("Longitude"),
            "provider": operator.get("Title", "-") if operator else "-",
            "connectors": conn_str,
            "power_kw": max_power,
            "status": status.get("Title", "Unknown") if status else "-",
            "cost": usage_cost if usage_cost else "No Info",
            "distance": addr.get("Distance")
        })

    df = pd.DataFrame(station_list)

    # Summary Metrics
    m1, m2, m3 = st.columns(3)
    m1.metric("Total Stations", len(df))
    m2.metric("Max Power (kW)", f"{df['power_kw'].max()}")
    if "distance" in df.columns and not df["distance"].isnull().all():
        m3.metric("Average Distance (km)", f"{df['distance'].mean():.2f}")

    # Map
    m = folium.Map(location=[lat, lon], zoom_start=13)

    for _, row in df.iterrows():
        # Color coding by power
        icon_color = "green"  # Slow / Standard
        if row["power_kw"] >= 50:
            icon_color = "red"  # Fast (DC)
        elif row["power_kw"] >= 22:
            icon_color = "orange"  # Medium Fast (AC)
            
        popup_html = f"""
        <div style="width: 200px;">
            <b>{row['name']}</b><br>
            <hr style="margin: 5px 0;">
            <b>Provider:</b> {row['provider']}<br>
            <b>Power:</b> {row['power_kw']} kW<br>
            <b>Status:</b> {row['status']}<br>
            <b>Cost:</b> {row['cost']}<br>
            <small>{row['connectors']}</small>
        </div>
        """
        
        folium.Marker(
            [row["lat"], row["lon"]],
            popup=folium.Popup(popup_html, max_width=300),
            icon=folium.Icon(color=icon_color, icon="bolt", prefix="fa")
        ).add_to(m)

    st_folium(m, width=None, height=500, use_container_width=True)
    
    with st.expander("Detailed Data Table"):
        st.dataframe(df)
else:
    st.warning("No stations found for these criteria")
