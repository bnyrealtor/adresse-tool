import streamlit as st
import geopandas as gpd
import gdown
import os
import folium
from streamlit_folium import st_folium

# --- KONFIGURATION ---
FILE_ID = '1tQmgDiC8uoksCf6NPiJx2otsg37X4SAf'
FILENAME = 'lkr_03451_Ammerland_kon.gpkg'

st.set_page_config(page_title="Immo-Finder Ammerland", layout="wide")
st.title("Immobilien-Suche: Landkreis Ammerland")

@st.cache_data
def load_data():
    # Lädt die Datei vom Drive, falls noch nicht vorhanden
    if not os.path.exists(FILENAME):
        url = f'https://drive.google.com/uc?id={FILE_ID}'
        gdown.download(url, FILENAME, quiet=False)
    
    gdf = gpd.read_file(FILENAME)
    
    # Projektion für exakte Flächenberechnung (in m²)
    gdf_area = gdf.to_crs("EPSG:25832")
    gdf['flaeche_qm'] = gdf_area.geometry.area
    
    # Transformation für die Karte
    gdf = gdf.to_crs("EPSG:4326")
    return gdf

# --- DATEN LADEN ---
with st.spinner("Lade Geodaten aus Drive..."):
    gdf = load_data()

# --- SIDEBAR ---
st.sidebar.header("Suche & Filter")
gemeinden = sorted(gdf['gem__bez'].unique().tolist())
auswahl_gem = st.sidebar.selectbox("Gemeinde wählen", gemeinden)

such_modus = st.sidebar.radio("Suchmodus", ["Mindestgröße", "Exakte Größe"])

if such_modus == "Mindestgröße":
    size_input = st.sidebar.number_input("Größe ab (qm)", min_value=0.0, step=10.0)
else:
    size_input = st.sidebar.number_input("Größe genau (qm)", min_value=0.0, step=1.0)
    tolerance = st.sidebar.slider("Toleranz (+/- qm)", 0.0, 50.0, 5.0)

suchen_button = st.sidebar.button("Suchen")

# --- LOGIK & KARTE ---
if suchen_button:
    if such_modus == "Mindestgröße":
        filtered_gdf = gdf[(gdf['gem__bez'] == auswahl_gem) & (gdf['flaeche_qm'] >= size_input)]
    else:
        filtered_gdf = gdf[(gdf['gem__bez'] == auswahl_gem) & 
                           (gdf['flaeche_qm'] >= size_input - tolerance) & 
                           (gdf['flaeche_qm'] <= size_input + tolerance)]
    
    st.success(f"Gefundene Objekte: {len(filtered_gdf)}")
    
    if not filtered_gdf.empty:
        # Karte auf den ersten Treffer zentrieren
        center = [filtered_gdf.geometry.centroid.y.iloc[0], filtered_gdf.geometry.centroid.x.iloc[0]]
        m = folium.Map(location=center, zoom_start=15)
        
        for _, row in filtered_gdf.iterrows():
            # Adresse aus den Attributen (passe 'fs_text' oder 'lagebezeichnung' an, falls nötig)
            adresse = row.get('fs_text', 'Adresse unbekannt')
            
            popup_html = f"""
                <div style="font-family: sans-serif; width: 220px;">
                    <b>Adresse:</b><br>
                    <div style="background-color: #f0f0f0; padding: 5px; border: 1px solid #ccc; border-radius: 3px; font-weight: bold;">
                        {adresse}
                    </div>
                    <p style="font-size: 10px; color: #666; margin-top: 5px;">(Markieren & kopieren)</p>
                    <a href="https://grundsteuer-viewer.niedersachsen.de/b" target="_blank" 
                       style="display: block; background-color: #28a745; color: white; padding: 10px; 
                              text-align: center; text-decoration: none; border-radius: 5px; font-weight: bold;">
                        Zum Grundsteuer-Viewer
                    </a>
                </div>
            """
            folium.Marker(
                [row.geometry.centroid.y, row.geometry.centroid.x], 
                popup=folium.Popup(popup_html, max_width=250)
            ).add_to(m)
        
        st_folium(m, width=1000, height=600)
    else:
        st.warning("Keine Objekte für diese Filter gefunden.")
