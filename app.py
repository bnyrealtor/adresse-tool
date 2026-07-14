import streamlit as st
import folium
from streamlit_folium import st_folium

# Konfiguration
st.set_page_config(page_title="Immobilien-Tool", layout="wide")
st.title("LGLN Grundstücks-Daten-Tool")

# Liste der Gemeinden im Ammerland
AMMERLAND_GEMEINDEN = sorted([
    "Apen", "Bad Zwischenahn", "Edewecht", "Friedrichsfehn", 
    "Rastede", "Westerstede", "Wiefelstede"
])

# Sidebar für die Eingabe
with st.sidebar:
    st.header("Suche")
    gemarkung = st.selectbox("Gemeinde wählen", AMMERLAND_GEMEINDEN)
    
    such_modus = st.radio("Modus", ["Exakte Größe", "Minimale Größe"])
    ziel_groesse = st.number_input("Grundstücksgröße (m²)", min_value=0, value=None)
    toleranz = st.number_input("Toleranz (+/- in %)", min_value=0, max_value=1000, value=3)
    
    run_button = st.button("Abfrage starten")

# Hauptbereich
if run_button:
    st.write(f"Suche in {gemarkung}: {such_modus} {ziel_groesse}m² (Toleranz: {toleranz}%)")
    
    # Beispielkarte
    m = folium.Map(location=[53.25, 7.95], zoom_start=11)
    
    # Platzhalter für die gefundenen Symbole
    # Hier werden später die berechneten Marker platziert
    folium.Marker(
        [53.25, 7.95], 
        popup="Grundstücks-Details",
        icon=folium.Icon(color='blue', icon='home')
    ).add_to(m)
    
    st_folium(m, width=700, height=500)
else:
    st.info("Bitte Parameter in der Sidebar festlegen und Suche starten.")
