import streamlit as st
import geopandas as gpd
import gdown
import os
import folium
from streamlit_folium import st_folium
from geopy.geocoders import Nominatim
from geopy.extra.rate_limiter import RateLimiter

st.set_page_config(page_title="Immo-Finder Ammerland", layout="wide")
st.title("Immobilien-Suche: Landkreis Ammerland")

FILE_ID = '1tQmgDiC8uoksCf6NPiJx2otsg37X4SAf'
FILENAME = 'lkr_03451_Ammerland_kon.gpkg'

# Geocoder initialisieren
geolocator = Nominatim(user_agent="radtke_immo_tool_v3")
geocode = RateLimiter(geolocator.reverse, min_delay_seconds=1)

@st.cache_data
def load_data():
    if not os.path.exists(FILENAME):
        url = f'https://drive.google.com/uc?id={FILE_ID}'
        gdown.download(url, FILENAME, quiet=False)
    gdf = gpd.read_file(FILENAME)
    
    # Projektion für exakte Flächenberechnung
    gdf_area = gdf.to_crs("EPSG:25832")
    gdf['flaeche_qm'] = gdf_area.geometry.area
    
    # Zurück zu WGS84 für Kartenanzeige
    gdf = gdf.to_crs("EPSG:4326")
    return gdf

with st.spinner("Lade Daten..."):
    gdf = load_data()

st.sidebar.header("Suche & Filter")
gemeinden = sorted(gdf['gem__bez'].unique().tolist())
auswahl_gem = st.sidebar.selectbox("Gemeinde wählen", gemeinden)

such_modus = st.sidebar.radio("Suchmodus", ["Mindestgröße", "Exakte Größe"])
if such_modus == "Mindestgröße":
    size_input = st.sidebar.number_input("Größe ab (qm)", min_value=0.0, step=10.0)
else:
    size_input = st.sidebar.number_input("Größe genau (qm)", min_value=0.0, step=1.0)
    tolerance = st.sidebar.slider("Toleranz (+/- qm)", 0.0, 50.0, 5.0)

if st.sidebar.button("Suchen"):
    # Filtern
    if such_modus == "Mindestgröße":
        filtered_gdf = gdf[(gdf['gem__bez'] == auswahl_gem) & (gdf['flaeche_qm'] >= size_input)]
    else:
        filtered_gdf = gdf[(gdf['gem__bez'] == auswahl_gem) & 
                           (gdf['flaeche_qm'] >= size_input - tolerance) & 
                           (gdf['flaeche_qm'] <= size_input + tolerance)]
    
    st.success(f"Gefundene Objekte: {len(filtered_gdf)}")
    
    if not filtered_gdf.empty:
        # Karte zentrieren auf den Mittelwert der Ergebnisse
        m = folium.Map(location=[filtered_gdf.geometry.centroid.y.mean(), 
                                 filtered_gdf.geometry.centroid.x.mean()], 
                       zoom_start=15)
        
        # Marker hinzufügen (begrenzt auf 20, um Geocoding-Limits zu schonen)
        for idx, row in filtered_gdf.head(20).iterrows():
            lat = row.geometry.centroid.y
            lon = row.geometry.centroid.x
            
            # Adresse auflösen
            try:
                location = geocode((lat, lon))
                adresse = location.address if location else "Adresse nicht gefunden"
            except:
                adresse = "Geocoding Fehler"
                
            popup_text = f"<b>Adresse:</b> {adresse}<br><b>Fläche:</b> {round(row['flaeche_qm'], 2)} qm<br><b>FS:</b> {row['fs_text']}"
            
            folium.Marker(
                [lat, lon], 
                popup=folium.Popup(popup_text, max_width=300),
                icon=folium.Icon(color='blue', icon='home')
            ).add_to(m)
        
        st_folium(m, width=None, height=700)
    else:
        st.warning("Keine Objekte gefunden.")
