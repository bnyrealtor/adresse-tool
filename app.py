import streamlit as st
import geopandas as gpd
import gdown
import os
import folium
from streamlit_folium import st_folium
from geopy.geocoders import Nominatim
import time

# Konfiguration
st.set_page_config(page_title="Immo-Finder Ammerland", layout="wide")
st.title("Immobilien-Suche: Landkreis Ammerland")

FILE_ID = '1tQmgDiC8uoksCf6NPiJx2otsg37X4SAf'
FILENAME = 'lkr_03451_Ammerland_kon.gpkg'

# Geocoder
geolocator = Nominatim(user_agent="radtke_immo_tool_v6")

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
gdf = load_data()

if 'filtered_gdf' not in st.session_state:
    st.session_state.filtered_gdf = None

# Sidebar
st.sidebar.header("Suche & Filter")
auswahl_gem = st.sidebar.selectbox("Gemeinde wählen", sorted(gdf['gem__bez'].unique().tolist()))
such_modus = st.sidebar.radio("Suchmodus", ["Mindestgröße", "Exakte Größe"])

if such_modus == "Mindestgröße":
    size_input = st.sidebar.number_input("Größe ab (qm)", min_value=0.0, step=10.0)
    tolerance = 0.0
else:
    size_input = st.sidebar.number_input("Größe genau (qm)", min_value=0.0, step=1.0)
    tolerance = st.sidebar.number_input("Toleranz (+/- qm)", min_value=0.0, value=3.0, step=1.0)

if st.sidebar.button("Suchen"):
    # Filterung
    if such_modus == "Mindestgröße":
        results = gdf[(gdf['gem__bez'] == auswahl_gem) & (gdf['flaeche_qm'] >= size_input)].head(20).copy()
    else:
        results = gdf[(gdf['gem__bez'] == auswahl_gem) & 
                      (gdf['flaeche_qm'] >= size_input - tolerance) & 
                      (gdf['flaeche_qm'] <= size_input + tolerance)].head(20).copy()
    
    # Batch-Geocoding mit Fortschrittsanzeige
    if not results.empty:
        results['adresse'] = "Wird geladen..."
        progress_bar = st.progress(0)
        total = len(results)
        
        for i, (idx, row) in enumerate(results.iterrows()):
            try:
                lat, lon = row.geometry.centroid.y, row.geometry.centroid.x
                loc = geolocator.reverse((lat, lon), language='de')
                results.at[idx, 'adresse'] = loc.address if loc else "Adresse nicht ermittelbar"
            except:
                results.at[idx, 'adresse'] = "Fehler bei Abfrage"
            progress_bar.progress((i + 1) / total)
            time.sleep(1) # Respektiert die API-Nutzungsbedingungen
        
        st.session_state.filtered_gdf = results
    else:
        st.session_state.filtered_gdf = results

# Anzeige
if st.session_state.filtered_gdf is not None:
    if not st.session_state.filtered_gdf.empty:
        st.success(f"Gefundene Objekte: {len(st.session_state.filtered_gdf)}")
        
        m = folium.Map(location=[st.session_state.filtered_gdf.geometry.centroid.y.mean(), 
                                 st.session_state.filtered_gdf.geometry.centroid.x.mean()], 
                       zoom_start=15)
        
        for idx, row in st.session_state.filtered_gdf.iterrows():
            folium.Marker(
                [row.geometry.centroid.y, row.geometry.centroid.x], 
                popup=f"<b>Adresse:</b> {row['adresse']}<br><b>Fläche:</b> {round(row['flaeche_qm'], 2)} qm<br><b>FS:</b> {row['fs_text']}",
                icon=folium.Icon(color='blue', icon='home')
            ).add_to(m)
        
        st_folium(m, width=None, height=700)
    else:
        st.warning("Keine Objekte gefunden.")
