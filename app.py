import streamlit as st
import geopandas as gpd
from owslib.wfs import WebFeatureService
from pyproj import Transformer
import folium
from streamlit_folium import st_folium

# Konfiguration
st.set_page_config(page_title="Immobilien-Tool", layout="wide")
st.title("LGLN Immobilien-Daten-Tool")

# Gemarkungs-Liste (Beispiel: Hier müsstest du deine Liste ergänzen)
# Für den Workflow: Gemarkung -> WFS-Filter
GEMARKUNGEN = ["Oldenburg", "Edewecht", "Westerstede", "Bad Zwischenahn"]

# Sidebar für die Auswahl
with st.sidebar:
    st.header("Suche")
    # Dropdown statt Texteingabe
    gemarkung = st.selectbox("Gemarkung wählen", GEMARKUNGEN)
    flur = st.text_input("Flur")
    zaehler = st.text_input("Zähler")
    nenner = st.text_input("Nenner")
    run_button = st.button("Abfrage starten")

# Hauptbereich
if run_button:
    # Hier würde die Logik folgen, um aus Gemarkung/Flur/Zähler/Nenner 
    # die Geometrie vom WFS-Dienst zu ziehen.
    
    st.write(f"Suche in Gemarkung: {gemarkung}, Flur: {flur}, Zähler: {zaehler}, Nenner: {nenner}")
    
    # Beispiel-Marker (Platzhalter für die Datenabfrage)
    # Sobald die Daten geladen sind, wird hier die Karte gerendert
    m = folium.Map(location=[53.1435, 8.2140], zoom_start=15)
    
    popup_html = """
    <a href="https://grundsteuer-viewer.niedersachsen.de/b" target="_blank" 
       style="background-color: #28a745; color: white; border: none; padding: 10px 20px; border-radius: 5px; text-decoration: none; font-weight: bold;">
        Zum Grundsteuer-Viewer
    </a>
    """
    
    folium.Marker(
        [53.1435, 8.2140], 
        popup=folium.Popup(popup_html, max_width=200),
        icon=folium.Icon(color='blue', icon='home')
    ).add_to(m)
    
    st_folium(m, width=700, height=500)
