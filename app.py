import streamlit as st
import geopandas as gpd
import gdown
import os
import folium
from streamlit_folium import st_folium

# Konfiguration
st.set_page_config(layout="wide")
st.title("Immobilien-Suche: Landkreis Ammerland")

FILE_ID = '1tQmgDiC8uoksCf6NPiJx2otsg37X4SAf'
FILENAME = 'lkr_03451_Ammerland_kon.gpkg'

@st.cache_data
def load_data():
    if not os.path.exists(FILENAME):
        gdown.download(f'https://drive.google.com/uc?id={FILE_ID}', FILENAME, quiet=False)
    gdf = gpd.read_file(FILENAME)
    # Projektion für Flächenberechnung
    gdf_area = gdf.to_crs("EPSG:25832")
    gdf['flaeche_qm'] = gdf_area.geometry.area
    # Zurück für die Karte
    return gdf.to_crs("EPSG:4326")

# Daten laden
with st.spinner("Lade Daten..."):
    gdf = load_data()

# Sidebar UI
st.sidebar.header("Suche & Filter")
auswahl_gem = st.sidebar.selectbox("Gemeinde", sorted(gdf['gem__bez'].unique().tolist()))
size_input = st.sidebar.number_input("Größe genau (qm)", value=None)
tol = st.sidebar.number_input("Toleranz (+/- qm)", value=3.0)

# Suche (nur Filtern)
if st.sidebar.button("Suchen"):
    st.session_state.res = gdf[(gdf['gem__bez'] == auswahl_gem) & 
                               (gdf['flaeche_qm'] >= size_input - tol) & 
                               (gdf['flaeche_qm'] <= size_input + tol)].head(30)

# Anzeige
if 'res' in st.session_state:
    results = st.session_state.res
    if not results.empty:
        st.success(f"Gefundene Objekte: {len(results)}")
        
        # Karte zentrieren
        m = folium.Map(location=[results.geometry.centroid.y.mean(), 
                                 results.geometry.centroid.x.mean()], 
                       zoom_start=15)
        
        for _, row in results.iterrows():
            lat, lon = row.geometry.centroid.y, row.geometry.centroid.x
            
            # Popup mit 300px Breite
            popup_html = f"""
            <div style="width: 300px;">
                <b>Fläche:</b> {round(row['flaeche_qm'], 2)} qm<br>
                <b>Flurstück:</b> {row['fs_text']}<br>
                <hr>
                <a href="https://nominatim.openstreetmap.org/ui/reverse.html?lat={lat}&lon={lon}" target="_blank" style="text-decoration: none; color: #007bff; font-weight: bold;">
                📍 Adresse auf Karte abrufen</a>
            </div>
            """
            
            folium.Marker(
                [lat, lon], 
                popup=folium.Popup(popup_html, max_width=300), 
                icon=folium.Icon(color='blue', icon='home')
            ).add_to(m)
            
        st_folium(m, width=None, height=700)
    else:
        st.warning("Keine Objekte gefunden.")
