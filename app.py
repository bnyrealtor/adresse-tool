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
    gdf = gdf.to_crs("EPSG:4326")
    return gdf

gdf = load_data()

# Suche
st.sidebar.header("Suche & Filter")
auswahl_gem = st.sidebar.selectbox("Gemeinde wählen", sorted(gdf['gem__bez'].unique().tolist()))
size_input = st.sidebar.number_input("Größe genau (qm)", min_value=0.0, value=500.0)
tolerance = st.sidebar.number_input("Toleranz (+/- qm)", min_value=0.0, value=3.0)

if st.sidebar.button("Suchen"):
    filtered_gdf = gdf[(gdf['gem__bez'] == auswahl_gem) & 
                       (gdf['flaeche_qm'] >= size_input - tolerance) & 
                       (gdf['flaeche_qm'] <= size_input + tolerance)].head(50)
    
    st.session_state.map_data = filtered_gdf

if 'map_data' in st.session_state:
    results = st.session_state.map_data
    st.success(f"Gefundene Objekte: {len(results)}")
    
    m = folium.Map(location=[results.geometry.centroid.y.mean(), 
                             results.geometry.centroid.x.mean()], 
                   zoom_start=15)
    
    for idx, row in results.iterrows():
        # Wir fügen einen JS-Aufruf hinzu, der die Adresse erst bei Klick von Nominatim holt
        # Das Popup enthält einen Platzhalter
        html = f"""
        <div id="popup_{idx}">
            <b>Flurstück:</b> {row['fs_text']}<br>
            <b>Fläche:</b> {round(row['flaeche_qm'], 2)} qm<br>
            <div id="addr_{idx}"><i>Klicke hier für Adresse...</i></div>
        </div>
        <script>
            // Diese Funktion wird aufgerufen, wenn der Marker geklickt wird
            async function getAddr_{idx}() {{
                let el = document.getElementById('addr_{idx}');
                el.innerHTML = "Lade Adresse...";
                try {{
                    let resp = await fetch('https://nominatim.openstreetmap.org/reverse?lat={row.geometry.centroid.y}&lon={row.geometry.centroid.x}&format=json');
                    let data = await resp.json();
                    el.innerHTML = "<b>Adresse:</b> " + data.display_name;
                }} catch(e) {{ el.innerHTML = "Nicht gefunden"; }}
            }}
            // Trigger bei Klick auf den Marker
        </script>
        """
        
        folium.Marker(
            [row.geometry.centroid.y, row.geometry.centroid.x], 
            popup=folium.Popup(html, max_width=300),
            icon=folium.Icon(color='blue', icon='home')
        ).add_to(m)
        
    st_folium(m, width=None, height=700)
