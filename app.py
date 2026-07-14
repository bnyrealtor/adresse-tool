import streamlit as st
import geopandas as gpd
from owslib.wfs import WebFeatureService
from geopy.geocoders import Nominatim
from pyproj import Transformer
import folium
from streamlit_folium import st_folium

# Konfiguration
st.set_page_config(page_title="Immobilien-Tool", layout="wide")
st.title("LGLN Immobilien-Daten-Tool")

# Funktionen
def get_coords(address):
    geolocator = Nominatim(user_agent="radtke_immo_tool_v2")
    location = geolocator.geocode(address)
    return (location.latitude, location.longitude) if location else None

def fetch_wfs_data(lat, lon):
    try:
        wfs = WebFeatureService(url="https://opendata.lgln.niedersachsen.de/wfs/gds_alkis", version="2.0.0")
        transformer = Transformer.from_crs("EPSG:4326", "EPSG:25832", always_xy=True)
        e, n = transformer.transform(lon, lat)
        bbox = (e-50, n-50, e+50, n+50)
        response = wfs.getfeature(typename='alkis:flurstueck', bbox=bbox, outputFormat='json')
        return gpd.read_file(response)
    except:
        return None

# Sidebar für die Eingabe
with st.sidebar:
    st.header("Suche")
    address_input = st.text_input("Adresse eingeben (Straße, PLZ, Ort)")
    run_button = st.button("Abfrage starten")

# Hauptbereich
if run_button:
    coords = get_coords(address_input)
    if coords:
        lat, lon = coords
        gdf = fetch_wfs_data(lat, lon)
        
        if gdf is not None and not gdf.empty:
            # Marker-Popup mit Grundsteuer-Viewer Button
            m = folium.Map(location=[lat, lon], zoom_start=19)
            
            popup_html = """
            <a href="https://grundsteuer-viewer.niedersachsen.de/b" target="_blank" 
               style="background-color: #28a745; color: white; border: none; padding: 10px 20px; border-radius: 5px; text-decoration: none; font-weight: bold;">
                Zum Grundsteuer-Viewer
            </a>
            """
            
            folium.Marker(
                [lat, lon], 
                popup=folium.Popup(popup_html, max_width=200),
                icon=folium.Icon(color='blue', icon='home')
            ).add_to(m)
            
            st_folium(m, width=700, height=500)
        else:
            st.warning("Keine Daten gefunden.")
    else:
        st.error("Adresse nicht gefunden.")
