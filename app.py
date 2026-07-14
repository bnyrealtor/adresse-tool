import streamlit as st
import geopandas as gpd
import gdown
import os

# 1. Konfiguration
st.set_page_config(page_title="Immo-Finder Ammerland", layout="wide")
st.title("Immobilien-Suche: Landkreis Ammerland")

# ID der Datei aus deinem Link
FILE_ID = '1tQmgDiC8uoksCf6NPiJx2otsg37X4SAf'
FILENAME = 'lkr_03451_Ammerland_kon.gpkg'

# 2. Daten laden
@st.cache_data
def load_data():
    # Lädt die Datei aus Google Drive, wenn sie noch nicht lokal vorhanden ist
    if not os.path.exists(FILENAME):
        url = f'https://drive.google.com/uc?id={FILE_ID}'
        gdown.download(url, FILENAME, quiet=False)
    return gpd.read_file(FILENAME)

with st.spinner("Lade Katasterdaten aus Drive..."):
    try:
        gdf = load_data()
        
        # 3. UI: Filter
        st.sidebar.header("Filter")
        st.write("Verfügbare Spalten zur Orientierung:", gdf.columns.tolist())
        
        # Wir lassen dich hier die Spalte auswählen, da wir den Namen noch nicht sicher wissen
        spalten_auswahl = st.sidebar.selectbox("Welche Spalte enthält die Größe?", gdf.columns.tolist())
        size_input = st.sidebar.number_input("Mindestgröße in qm", min_value=0.0, step=10.0)

        if st.sidebar.button("Suchen"):
            # Filterung
            filtered_gdf = gdf[gdf[spalten_auswahl] >= size_input]
            
            st.success(f"Gefundene Flurstücke: {len(filtered_gdf)}")
            st.dataframe(filtered_gdf.head(100))
            
            # Karte anzeigen (falls Geometrien vorhanden sind)
            st.map(filtered_gdf.head(100))
            
    except Exception as e:
        st.error(f"Ein Fehler ist aufgetreten: {e}")
