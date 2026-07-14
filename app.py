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
    
    # Projektion für Flächenberechnung
    gdf_area = gdf.to_crs("EPSG:25832")
    gdf['flaeche_qm'] = gdf_area.geometry.area
    
    # Transformation in WGS84 für die Karte
    gdf = gdf.to_crs("EPSG:4326")
    
    # HIER DIE KORREKTUR: Explizite lat/lon Spalten für st.map erstellen
    # Wir nehmen den Centroid (Mittelpunkt) des Grundstücks als Koordinatenpunkt
    gdf['lat'] = gdf.geometry.centroid.y
    gdf['lon'] = gdf.geometry.centroid.x
    
    return gdf

with st.spinner("Lade und berechne Flächen..."):
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
        if such_modus == "Mindestgröße":
            filtered_gdf = gdf[(gdf['gem__bez'] == auswahl_gem) & (gdf['flaeche_qm'] >= size_input)]
        else:
            filtered_gdf = gdf[(gdf['gem__bez'] == auswahl_gem) & 
                               (gdf['flaeche_qm'] >= size_input - tolerance) & 
                               (gdf['flaeche_qm'] <= size_input + tolerance)]
        
        st.success(f"Gefundene Objekte: {len(filtered_gdf)}")
        
        if not filtered_gdf.empty:
            st.dataframe(filtered_gdf[['gmk__bez', 'gem__bez', 'flaeche_qm', 'fs_text']])
            # st.map nutzt jetzt die neuen 'lat' und 'lon' Spalten automatisch!
            st.map(filtered_gdf.head(100))
        else:
            st.warning("Keine Objekte für diese Filter gefunden.")
