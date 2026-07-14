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
    gdf['flaeche_qm'] = gdf.to_crs("EPSG:25832").geometry.area
    return gdf.to_crs("EPSG:4326")

# Daten laden
with st.spinner("Lade Kartendaten..."):
    gdf = load_data()

# Sidebar
st.sidebar.header("Suche & Filter")
auswahl_gem = st.sidebar.selectbox("Gemeinde", sorted(gdf['gem__bez'].unique().tolist()))
size_input = st.sidebar.number_input("Größe genau (qm)", value=None)
tol = st.sidebar.number_input("Toleranz (+/- qm)", value=3.0)

if st.sidebar.button("Suchen"):
    st.session_state.res = gdf[(gdf['gem__bez'] == auswahl_gem) & 
                               (gdf['flaeche_qm'] >= size_input - tol) & 
                               (gdf['flaeche_qm'] <= size_input + tol)].head(30)

# Anzeige
if 'res' in st.session_state:
    results = st.session_state.res
    if not results.empty:
        st.success(f"Gefundene Objekte: {len(results)}")
        
        m = folium.Map(location=[results.geometry.centroid.y.mean(), 
                                 results.geometry.centroid.x.mean()], 
                       zoom_start=15)
        
        for _, row in results.iterrows():
            lat, lon = row.geometry.centroid.y, row.geometry.centroid.x
            
            # Popup mit zwei Buttons für sofortige Navigation
            popup_html = f"""
            <div style="width: 250px; font-family: sans-serif;">
                <b>Fläche:</b> {round(row['flaeche_qm'], 2)} qm<br>
                <b>Flurstück:</b> {row['fs_text']}<br>
                <div style="margin-top: 10px;">
                    <a href="https://nominatim.openstreetmap.org/ui/reverse.html?lat={lat}&lon={lon}" target="_blank" 
                       style="display: block; padding: 8px; background: #f0f0f0; text-align: center; text-decoration: none; color: #333; border: 1px solid #ccc; margin-bottom: 5px;">
                       🔍 OSM Adress-Suche
                    </a>
                    <a href="https://www.google.com/maps/search/?api=1&query={lat},{lon}" target="_blank" 
                       style="display: block; padding: 8px; background: #4285f4; text-align: center; text-decoration: none; color: white; border: 1px solid #4285f4;">
                       📍 Google Maps (Satellit/SV)
                    </a>
                </div>
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
