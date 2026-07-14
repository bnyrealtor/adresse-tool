import streamlit as st
import geopandas as gpd
import gdown
import os
import folium
from streamlit_folium import st_folium
from geopy.geocoders import Nominatim

st.set_page_config(layout="wide")

FILE_ID = '1tQmgDiC8uoksCf6NPiJx2otsg37X4SAf'
FILENAME = 'lkr_03451_Ammerland_kon.gpkg'
geolocator = Nominatim(user_agent="radtke_immo_tool_v8")

@st.cache_data
def load_data():
    if not os.path.exists(FILENAME):
        gdown.download(f'https://drive.google.com/uc?id={FILE_ID}', FILENAME, quiet=False)
    gdf = gpd.read_file(FILENAME)
    gdf['flaeche_qm'] = gdf.to_crs("EPSG:25832").geometry.area
    return gdf.to_crs("EPSG:4326")

gdf = load_data()

# Sidebar UI
auswahl_gem = st.sidebar.selectbox("Gemeinde", sorted(gdf['gem__bez'].unique().tolist()))
size_input = st.sidebar.number_input("Größe genau (qm)", value=500.0)
tol = st.sidebar.number_input("Toleranz (+/- qm)", value=3.0)

# Suche (nur Filtern, kein Geocoding!)
if st.sidebar.button("Suchen"):
    st.session_state.res = gdf[(gdf['gem__bez'] == auswahl_gem) & 
                               (gdf['flaeche_qm'] >= size_input - tol) & 
                               (gdf['flaeche_qm'] <= size_input + tol)].head(30)

if 'res' in st.session_state:
    results = st.session_state.res
    m = folium.Map(location=[results.geometry.centroid.y.mean(), results.geometry.centroid.x.mean()], zoom_start=15)
    
    for _, row in results.iterrows():
        lat, lon = row.geometry.centroid.y, row.geometry.centroid.x
        
        # Geocoding-Link direkt in das Popup integrieren
        # Wir lösen die Adresse NICHT vorab auf.
        popup_html = f"""
        <b>Fläche:</b> {round(row['flaeche_qm'], 2)} qm<br>
        <b>FS:</b> {row['fs_text']}<br>
        <a href="https://nominatim.openstreetmap.org/ui/reverse.html?lat={lat}&lon={lon}" target="_blank">
        Adresse auf Karte ansehen</a>
        """
        
        folium.Marker([lat, lon], popup=popup_html, icon=folium.Icon(color='blue', icon='home')).add_to(m)
        
    st_folium(m, width=None, height=700)
