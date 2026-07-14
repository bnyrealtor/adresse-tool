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
    size_input = st.sidebar.number_input("Mindestgröße in qm", min_value=0.0, step=10.0)

    if st.sidebar.button("Suchen"):
        filtered_gdf = gdf[(gdf['gem__bez'] == auswahl_gem) & (gdf['flaeche_qm'] >= size_input)]
        
        st.success(f"Gefundene Objekte: {len(filtered_gdf)}")
        
        if not filtered_gdf.empty:
            # Karte zentrieren
            m = folium.Map(location=[filtered_gdf.geometry.centroid.y.mean(), 
                                     filtered_gdf.geometry.centroid.x.mean()], zoom_start=13)
            
            # Punkte hinzufügen
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
            st.warning("Keine Objekte gefunden.")
