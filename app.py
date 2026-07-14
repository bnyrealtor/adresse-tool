import streamlit as st
import geopandas as gpd
import requests
import io

st.set_page_config(page_title="Ammerland Immobilien-Finder", layout="wide")
st.title("Immobilien-Suche: Landkreis Ammerland")

# 1. Google Drive File-ID (HIER DEINE ID EINTRAGEN!)
FILE_ID = "HIER_DEINE_FILE_ID_VON_GOOGLE_DRIVE_EINFUEGEN"
DOWNLOAD_URL = f"https://drive.google.com/uc?export=download&id={FILE_ID}"

@st.cache_resource
def load_data_from_drive():
    response = requests.get(DOWNLOAD_URL)
    if response.status_code == 200:
        # Laden als Bytes
        return gpd.read_file(io.BytesIO(response.content))
    else:
        st.error("Datei konnte nicht von Google Drive geladen werden.")
        return None

with st.spinner("Lade große Datenmenge aus Drive..."):
    gdf = load_data_from_drive()

if gdf is not None:
    # DEBUG: Spaltennamen anzeigen, damit wir wissen, wonach wir filtern
    st.write("Spalten in der Datei:", gdf.columns.tolist())
    
    # 2. UI: Suche
    size_input = st.number_input("Grundstücksgröße mindestens (in qm)", min_value=0.0)
    
    if st.button("Suchen"):
        # HIER MUSS DER RICHTIGE SPALTENNAME REIN (statt 'flaechenmass')
        # Sobald du mir die Spaltenliste gibst, passe ich das an!
        try:
            filtered_gdf = gdf[gdf['flaechenmass'] >= size_input]
            st.write(f"Gefundene Flurstücke: {len(filtered_gdf)}")
            st.dataframe(filtered_gdf.head(20))
        except Exception as e:
            st.error(f"Fehler: {e}")
