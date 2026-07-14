import os
import subprocess
import sys

# Sicherstellung, dass notwendige Pakete installiert sind
try:
    import gdown
    from geopy.geocoders import Nominatim
except ImportError:
    subprocess.check_call([sys.executable, "-m", "pip", "install", "gdown", "geopy"])
    import gdown
    from geopy.geocoders import Nominatim

import streamlit as st
import geopandas as gpd
import folium
from streamlit_folium import st_folium

# --- KONFIGURATION ---
FILE_ID = '1tQmgDiC8uoksCf6NPiJx2otsg37X4SAf'
FILENAME = 'lkr_03451_Ammerland_kon.gpkg'

# --- FUNKTIONEN ---
@st.cache_data
def load_data():
    if not os.path.exists(FILENAME):
        url = f'https://drive.google.com/uc?id={FILE_ID}'
        gdown.download(url, FILENAME, quiet=False)
    gdf = gpd.read_file(FILENAME)
    gdf_area = gdf.to_crs("EPSG:25832")
    gdf['flaeche_qm'] = gdf_area.geometry.area
    gdf = gdf.to_crs("EPSG:4326")
    return gdf

@st.cache_data
def get_address(lat, lon):
    geolocator = Nominatim(user_agent="radtke_immo_tool_v2")
    try:
        location = geolocator.reverse((lat, lon), language='de', addressdetails=True)
        if location:
            addr = location.raw.get('address', {})
            return f"{addr.get('road', 'Unbekannt')} {addr.get('house_number', '')}".strip()
    except:
        pass
    return "Adresse nicht ladbar"

# --- UI ---
st.set_page_config(page_title="Immo-Finder Ammerland", layout="wide")
st.title("Immobilien-Suche: Landkreis Ammerland")

gdf = load_data()

if 'search_clicked' not in st.session_state:
    st.session_state.search_clicked = False

st.sidebar.header("Suche & Filter")
auswahl_gem = st.sidebar.selectbox("Gemeinde wählen", sorted(gdf['gem__bez'].unique().tolist()))
such_modus = st.sidebar.radio("Suchmodus", ["Mindestgröße", "Exakte Größe"])

if such_modus == "Mindestgröße":
    size_input = st.sidebar.number_input("Größe ab (qm)", min_value=0.0, step=10.0)
    tolerance = 0.0
else:
    size_input = st.sidebar.number_input("Größe genau (qm)", min_value=0.0, step=1.0)
    tolerance = st.sidebar.number_input("Toleranz (+/- qm)", min_value=0.0, max_value=500.0, value=5.0, step=1.0)

if st.sidebar.button("Suchen"):
    st.session_state.search_clicked = True

# --- KARTE ---
if st.session_state.search_clicked:
    filtered_gdf = gdf[(gdf['gem__bez'] == auswahl_gem) & 
                       (gdf['flaeche_qm'] >= (size_input - tolerance)) & 
                       (gdf['flaeche_qm'] <= (size_input + (tolerance if such_modus == "Exakte Größe" else 999999)))]
    
    st.success(f"Gefundene Objekte: {len(filtered_gdf)}")
    
    if not filtered_gdf.empty:
        # Begrenzung auf 20 Marker, um API-Limits zu vermeiden
        display_gdf = filtered_gdf.head(20)
        
        center = [display_gdf.geometry.centroid.y.iloc[0], display_gdf.geometry.centroid.x.iloc[0]]
        m = folium.Map(location=center, zoom_start=15)
        
        for _, row in display_gdf.iterrows():
            lat, lon = row.geometry.centroid.y, row.geometry.centroid.x
            adresse = get_address(lat, lon)
            
            popup_html = f"""
                <div style="font-family: sans-serif; width: 220px;">
                    <b style="color: #333;">Adresse via Geocoding:</b><br>
                    <div style="background-color: #eef; padding: 8px; border: 1px solid #ccd; border-radius: 4px; margin: 5px 0;">
                        {adresse}
                    </div>
                    <a href="https://grundsteuer-viewer.niedersachsen.de/b" target="_blank" 
                       style="display: block; background-color: #28a745; color: white; padding: 10px; 
                              text-align: center; text-decoration: none; border-radius: 5px; font-weight: bold; margin-top: 10px;">
                        Zum Grundsteuer-Viewer
                    </a>
                </div>
            """
            folium.Marker([lat, lon], popup=folium.Popup(popup_html, max_width=250),
                          icon=folium.Icon(color='blue', icon='home', prefix='fa')).add_to(m)
        
        st_folium(m, width=1000, height=600)
    else:
        st.warning("Keine Ergebnisse gefunden.")
