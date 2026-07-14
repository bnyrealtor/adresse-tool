import streamlit as st
import folium
from streamlit_folium import st_folium
import geopandas as gpd
from owslib.wfs import WebFeatureService

# Konfiguration
st.set_page_config(page_title="Immobilien-Tool", layout="wide")
st.title("LGLN Grundstücks-Daten-Tool")

# Gemarkungen
AMMERLAND_GEMEINDEN = sorted([
    "Apen", "Bad Zwischenahn", "Edewecht", "Friedrichsfehn", 
    "Rastede", "Westerstede", "Wiefelstede"
])

if 'show_map' not in st.session_state:
    st.session_state.show_map = False

with st.sidebar:
    st.header("Suche")
    gemarkung = st.selectbox("Gemeinde wählen", AMMERLAND_GEMEINDEN)
    such_modus = st.radio("Modus", ["Exakte Größe", "Minimale Größe"])
    ziel_groesse = st.number_input("Grundstücksgröße (m²)", min_value=0, value=500)
    toleranz = st.number_input("Toleranz (+/- in %)", min_value=0, max_value=100, value=3)
    
    if st.button("Abfrage starten"):
        st.session_state.show_map = True

if st.session_state.show_map:
    st.write(f"Suche in {gemarkung}...")
    
    try:
        # LGLN OGC Dienst URL
        wfs_url = "https://opendata.lgln.niedersachsen.de/wfs/gds_alkis"
        wfs = WebFeatureService(url=wfs_url, version="2.0.0")
        
        # HILFE ZUR FEHLERSUCHE: 
        # Wenn hier ein Fehler kommt, zeigt diese Zeile uns die korrekten Namen an:
        st.write("Verfügbare Layer auf dem Server:", list(wfs.contents.keys()))
        
        # Abfrage Logik
        # Hinweis: 'alkis:flurstueck' muss ggf. durch einen der Namen aus der Liste oben ersetzt werden
        typename = 'alkis:flurstueck' 
        
        # Filter (CQL)
        cql_filter = f"flaeche >= {ziel_groesse * (1 - toleranz/100)}"
        
        response = wfs.getfeature(typename=typename, cql_filter=cql_filter, maxFeatures=20, outputFormat='json')
        gdf = gpd.read_file(response)
        
        if not gdf.empty:
            m = folium.Map(location=[53.25, 7.95], zoom_start=12)
            for _, row in gdf.iterrows():
                folium.Marker(
                    location=[row.geometry.centroid.y, row.geometry.centroid.x],
                    popup=f"Größe: {row.get('flaeche', 'N/A')} m²",
                    icon=folium.Icon(color='blue', icon='home')
                ).add_to(m)
            st_folium(m, width=None, height=700)
        else:
            st.warning("Keine Daten gefunden. Überprüfe die Layer-Namen oben.")
            
    except Exception as e:
        st.error(f"Fehler: {e}")
        st.info("Hinweis: Falls der Fehler '404' bleibt, ist die URL des WFS-Dienstes beim LGLN veraltet.")
else:
    st.info("Bitte Parameter wählen und Suche starten.")
