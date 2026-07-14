import os
import subprocess
import sys

# Sicherstellung, dass gdown installiert ist
try:
    import gdown
except ImportError:
    subprocess.check_call([sys.executable, "-m", "pip", "install", "gdown"])
    import gdown

import streamlit as st
import geopandas as gpd
import folium
from streamlit_folium import st_folium

# --- SESSION STATE INITIALISIERUNG ---
if 'search_clicked' not in st.session_state:
    st.session_state.search_clicked = False

# --- KONFIGURATION & DATEN ---
FILE_ID = '1tQmgDiC8uoksCf6NPiJx2otsg37X4SAf'
FILENAME = 'lkr_03451_Ammerland_kon.gpkg'

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

st.set_page_config(page_title="Immo-Finder Ammerland", layout="wide")
st.title("Immobilien-Suche: Landkreis Ammerland")

with st.spinner("Lade Geodaten..."):
    gdf = load_data()

# --- SIDEBAR ---
st.sidebar.header("Suche & Filter")
gemeinden = sorted(gdf['gem__bez'].unique().tolist())
auswahl_gem = st.sidebar.selectbox("Gemeinde wählen", gemeinden)
such_modus = st.sidebar.radio("Suchmodus", ["Mindestgröße", "Exakte Größe"])

if such_modus == "Mindestgröße":
    size_input = st.sidebar.number_input("Größe ab (qm)", min_value=0.0, step=10.0)
    tolerance = 0.0
else:
    size_input = st.sidebar.number_input("Größe genau (qm)", min_value=0.0, step=1.0)
    tolerance = st.sidebar.number_input("Toleranz (+/- qm)", min_value=0.0, max_value=500.0, value=5.0, step=1.0)

# Wenn Button gedrückt, setze Session State auf True
if st.sidebar.button("Suchen"):
    st.session_state.search_clicked = True

# --- LOGIK (Läuft jetzt, wenn state True ist) ---
if st.session_state.search_clicked:
    if such_modus == "Mindestgröße":
        filtered_gdf = gdf[(gdf['gem__bez'] == auswahl_gem) & (gdf['flaeche_qm'] >= size_input)]
    else:
        filtered_gdf = gdf[(gdf['gem__bez'] == auswahl_gem) & 
                           (gdf['flaeche_qm'] >= size_input - tolerance) & 
                           (gdf['flaeche_qm'] <= size_input + tolerance)]
    
    st.success(f"Gefundene Objekte: {len(filtered_gdf)}")
    
    if not filtered_gdf.empty:
        center = [filtered_gdf.geometry.centroid.y.iloc[0], filtered_gdf.geometry.centroid.x.iloc[0]]
        m = folium.Map(location=center, zoom_start=15)
        for _, row in filtered_gdf.iterrows():
            adresse = row.get('fs_text', 'Adresse unbekannt')
            popup_html = f"<div><b>Adresse:</b><br>{adresse}<br><br><a href='https://grundsteuer-viewer.niedersachsen.de/b' target='_blank'>Zum Grundsteuer-Viewer</a></div>"
            folium.Marker([row.geometry.centroid.y, row.geometry.centroid.x], 
                          popup=folium.Popup(popup_html, max_width=250)).add_to(m)
        st_folium(m, width=1000, height=600)
    else:
        st.warning("Keine Objekte für diese Filter gefunden.")
