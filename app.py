import streamlit as st
import geopandas as gpd
import gdown
import os
import folium
from streamlit_folium import st_folium
from geopy.geocoders import Nominatim
from concurrent.futures import ThreadPoolExecutor

st.set_page_config(page_title="Immo-Finder Ammerland", layout="wide")
st.title("Immobilien-Suche: Landkreis Ammerland")

FILE_ID = '1tQmgDiC8uoksCf6NPiJx2otsg37X4SAf'
FILENAME = 'lkr_03451_Ammerland_kon.gpkg'

# Geocoder
geolocator = Nominatim(user_agent="radtke_immo_tool_v7")

@st.cache_data
def load_data():
    if not os.path.exists(FILENAME):
        gdown.download(f'https://drive.google.com/uc?id={FILE_ID}', FILENAME, quiet=False)
    gdf = gpd.read_file(FILENAME)
    gdf['flaeche_qm'] = gdf.to_crs("EPSG:25832").geometry.area
    return gdf.to_crs("EPSG:4326")

gdf = load_data()

# Hilfsfunktion für Parallelisierung
def get_single_address(row):
    try:
        lat, lon = row.geometry.centroid.y, row.geometry.centroid.x
        loc = geolocator.reverse((lat, lon), language='de', timeout=5)
        return loc.address if loc else "Keine Adresse gefunden"
    except:
        return "Fehler bei Abfrage"

# UI
auswahl_gem = st.sidebar.selectbox("Gemeinde", sorted(gdf['gem__bez'].unique().tolist()))
size_input = st.sidebar.number_input("Größe genau (qm)", value=500.0)
tol = st.sidebar.number_input("Toleranz (+/- qm)", value=3.0)

if st.sidebar.button("Suchen"):
    res = gdf[(gdf['gem__bez'] == auswahl_gem) & 
              (gdf['flaeche_qm'] >= size_input - tol) & 
              (gdf['flaeche_qm'] <= size_input + tol)].head(30).copy()
    
    # Adressen parallel laden
    with st.spinner("Lade Objektdaten..."):
        with ThreadPoolExecutor(max_workers=5) as executor:
            addresses = list(executor.map(get_single_address, [row for _, row in res.iterrows()]))
        res['adresse'] = addresses
    
    st.session_state.res = res

if 'res' in st.session_state:
    results = st.session_state.res
    m = folium.Map(location=[results.geometry.centroid.y.mean(), results.geometry.centroid.x.mean()], zoom_start=15)
    for _, row in results.iterrows():
        folium.Marker(
            [row.geometry.centroid.y, row.geometry.centroid.x],
            popup=f"<b>Adresse:</b> {row['adresse']}<br><b>Fläche:</b> {round(row['flaeche_qm'], 2)} qm",
            icon=folium.Icon(color='blue', icon='home')
        ).add_to(m)
    st_folium(m, width=None, height=700)
