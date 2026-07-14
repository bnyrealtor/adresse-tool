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
    # Lade Daten und transformiere in ein flächenberechenbares Koordinatensystem (UTM 32N / EPSG:25832)
    gdf = gpd.read_file(FILENAME)
    if gdf.crs != "EPSG:25832":
        gdf = gdf.to_crs("EPSG:25832")
    # Fläche in qm berechnen
    gdf['flaeche_qm'] = gdf.geometry.area
    return gdf

with st.spinner("Lade und berechne Flächen..."):
    gdf = load_data()
    
    st.sidebar.header("Suche & Filter")
    
    # Gemeinde-Auswahl statt PLZ
    gemeinden = sorted(gdf['gem__bez'].unique().tolist())
    auswahl_gem = st.sidebar.selectbox("Gemeinde wählen", gemeinden)
    
    size_input = st.sidebar.number_input("Mindestgröße in qm", min_value=0.0, step=10.0)

    if st.sidebar.button("Suchen"):
        filtered_gdf = gdf[(gdf['gem__bez'] == auswahl_gem) & (gdf['flaeche_qm'] >= size_input)]
        
        st.success(f"Gefundene Objekte: {len(filtered_gdf)}")
        
        # Zeige relevante Spalten an
        st.dataframe(filtered_gdf[['gmk__bez', 'gem__bez', 'flaeche_qm', 'fs_text']])
        
        st.map(filtered_gdf.head(100))
