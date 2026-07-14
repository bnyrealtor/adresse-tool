import streamlit as st
import geopandas as gpd
import gdown
import os
import folium
from streamlit_folium import st_folium
from geopy.geocoders import Nominatim

# Konfiguration
st.set_page_config(page_title="Immo-Finder Ammerland", layout="wide")
st.title("Immobilien-Suche: Landkreis Ammerland")

FILE_ID = '1tQmgDiC8uoksCf6NPiJx2otsg37X4SAf'
FILENAME = 'lkr_03451_Ammerland_kon.gpkg'

# Geocoder initialisieren (wird später in der Funktion genutzt)
geolocator = Nominatim(user_agent="radtke_immo_tool_v5")

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

# Daten laden
with st.spinner("Lade und berechne Flächen..."):
    gdf = load_data()

# Session State
if 'filtered_gdf' not in st.session_state:
    st.session_state.filtered_gdf = None

# Sidebar
st.sidebar.header("Suche & Filter")
gemeinden = sorted(gdf['gem__bez'].unique().tolist())
auswahl_gem = st.sidebar.selectbox("Gemeinde wählen", gemeinden)
such_modus = st.sidebar.radio("Suchmodus", ["Mindestgröße", "Exakte Größe"])

if such_modus == "Mindestgröße":
    size_input = st.sidebar.number_input("Größe ab (qm)", min_value=0.0, step=10.0)
    tolerance = 0.0
else:
    size_input = st.sidebar.number_input("Größe genau (qm)", min_value=0.0, step=1.0)
    tolerance = st.sidebar.number_input("Toleranz (+/- qm)", min_value=0.0, value=3.0, step=1.0)

if st.sidebar.button("Suchen"):
    if such_modus == "Mindestgröße":
        st.session_state.filtered_gdf = gdf[(gdf['gem__bez'] == auswahl_gem) & (gdf['flaeche_qm'] >= size_input)]
    else:
        st.session_state.filtered_gdf = gdf[(gdf['gem__bez'] == auswahl_gem) & 
                                           (gdf['flaeche_qm'] >= size_input - tolerance) & 
                                           (gdf['flaeche_qm'] <= size_input + tolerance)]

# Anzeige
if st.session_state.filtered_gdf is not None:
    st.success(f"Gefundene Objekte: {len(st.session_state.filtered_gdf)}")
    
    if not st.session_state.filtered_gdf.empty:
        # Karte erstellen
        m = folium.Map(location=[st.session_state.filtered_gdf.geometry.centroid.y.mean(), 
                                 st.session_state.filtered_gdf.geometry.centroid.x.mean()], 
                       zoom_start=14)
        
        # Marker ohne blockierendes Geocoding hinzufügen
        for idx, row in st.session_state.filtered_gdf.head(50).iterrows():
            lat = row.geometry.centroid.y
            lon = row.geometry.centroid.x
            
            # Popup zeigt grundlegende Daten direkt
            popup_text = f"<b>Flurstück:</b> {row['fs_text']}<br><b>Fläche:</b> {round(row['flaeche_qm'], 2)} qm"
            
            folium.Marker(
                [lat, lon], 
                popup=popup_text,
                icon=folium.Icon(color='blue', icon='home')
            ).add_to(m)
        
        st_folium(m, width=None, height=700)
    else:
        st.warning("Keine Objekte gefunden.")
