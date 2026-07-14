import streamlit as st
import geopandas as gpd
import gdown
import os
import folium
from streamlit_folium import st_folium

st.set_page_config(page_title="Immo-Finder Ammerland", layout="wide")
st.title("Immobilien-Suche: Landkreis Ammerland")

FILE_ID = '1tQmgDiC8uoksCf6NPiJx2otsg37X4SAf'
FILENAME = 'lkr_03451_Ammerland_kon.gpkg'

# Session State initialisieren, um Ergebnisse zu speichern
if 'search_results' not in st.session_state:
    st.session_state.search_results = None

@st.cache_data
def load_data():
    if not os.path.exists(FILENAME):
        url = f'https://drive.google.com/uc?id={FILE_ID}'
        gdown.download(url, FILENAME, quiet=False)
    gdf = gpd.read_file(FILENAME)
    gdf_area = gdf.to_crs("EPSG:25832")
    gdf['flaeche_qm'] = gdf_area.geometry.area
    return gdf.to_crs("EPSG:4326")

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
        tolerance = st.sidebar.number_input("Toleranz (+/- qm)", min_value=0.0, max_value=500.0, value=5.0, step=1.0)

    # Button-Logik mit Session State
    if st.sidebar.button("Suchen"):
        if such_modus == "Mindestgröße":
            st.session_state.search_results = gdf[(gdf['gem__bez'] == auswahl_gem) & (gdf['flaeche_qm'] >= size_input)]
        else:
            st.session_state.search_results = gdf[(gdf['gem__bez'] == auswahl_gem) & 
                                                  (gdf['flaeche_qm'] >= size_input - tolerance) & 
                                                  (gdf['flaeche_qm'] <= size_input + tolerance)]

    # Ergebnisse anzeigen, falls sie im Session State gespeichert sind
    if st.session_state.search_results is not None:
        filtered_gdf = st.session_state.search_results
        st.success(f"Gefundene Objekte: {len(filtered_gdf)}")
        
        if not filtered_gdf.empty:
            m = folium.Map(location=[filtered_gdf.geometry.centroid.y.mean(), 
                                     filtered_gdf.geometry.centroid.x.mean()], zoom_start=13)
            
            for _, row in filtered_gdf.head(100).iterrows():
                popup_content = f"""
                <b>Flurstück:</b> {row['fs_text']}<br>
                <b>Größe:</b> {row['flaeche_qm']:.2f} qm<br>
                <a href='https://immobilienmarkt.niedersachsen.de' target='_blank'>Zum Immobilienmarkt</a>
                """
                folium.Marker(
                    [row.geometry.centroid.y, row.geometry.centroid.x],
                    popup=folium.Popup(popup_content, max_width=250),
                    icon=folium.Icon(color="red", icon="info-sign")
                ).add_to(m)
            
            st_folium(m, width=1200, height=600)
            st.dataframe(filtered_gdf[['gmk__bez', 'gem__bez', 'flaeche_qm', 'fs_text']])
        else:
            st.warning("Keine Objekte für diese Filter gefunden.")
