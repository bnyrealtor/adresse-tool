import streamlit as st
import geopandas as gpd
import gdown
import os

st.set_page_config(page_title="Immo-Finder Ammerland", layout="wide")
st.title("Immobilien-Suche: Landkreis Ammerland")

FILE_ID = '1tQmgDiC8uoksCf6NPiJx2otsg37X4SAf'
FILENAME = 'lkr_03451_Ammerland_kon.gpkg'

@st.cache_data
def load_data():
    if not os.path.exists(FILENAME):
        url = f'https://drive.google.com/uc?id={FILE_ID}'
        gdown.download(url, FILENAME, quiet=False)
    gdf = gpd.read_file(FILENAME)
    # Transformation in WGS84 (EPSG:4326), da st.map dies zwingend erfordert
    if gdf.crs != "EPSG:4326":
        gdf = gdf.to_crs("EPSG:4326")
    # Fläche berechnen (vorher kurz in metrisches System projizieren)
    gdf_area = gdf.to_crs("EPSG:25832")
    gdf['flaeche_qm'] = gdf_area.geometry.area
    return gdf

with st.spinner("Lade und berechne Flächen..."):
    gdf = load_data()
    
    st.sidebar.header("Suche & Filter")
    gemeinden = sorted(gdf['gem__bez'].unique().tolist())
    auswahl_gem = st.sidebar.selectbox("Gemeinde wählen", gemeinden)
    size_input = st.sidebar.number_input("Mindestgröße in qm", min_value=0.0, step=10.0)

    if st.sidebar.button("Suchen"):
        filtered_gdf = gdf[(gdf['gem__bez'] == auswahl_gem) & (gdf['flaeche_qm'] >= size_input)]
        
        st.success(f"Gefundene Objekte: {len(filtered_gdf)}")
        st.dataframe(filtered_gdf[['gmk__bez', 'gem__bez', 'flaeche_qm', 'fs_text']])
        
        # Karte sicher anzeigen: st.map funktioniert jetzt, da wir in EPSG:4326 sind
        if not filtered_gdf.empty:
            st.map(filtered_gdf.head(100))
        else:
            st.warning("Keine Objekte für diese Filter gefunden.")
