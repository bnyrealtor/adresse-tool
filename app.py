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

# Session State initialisieren, damit die Anzeige bleibt
if 'show_map' not in st.session_state:
    st.session_state.show_map = False

# Sidebar für die Eingabe
with st.sidebar:
    st.header("Suche")
    gemarkung = st.selectbox("Gemarkung wählen", AMMERLAND_GEMEINDEN)
    
    such_modus = st.radio("Modus", ["Exakte Größe", "Minimale Größe"])
    ziel_groesse = st.number_input("Grundstücksgröße (m²)", min_value=0, value=500)
    toleranz = st.number_input("Toleranz (+/- in %)", min_value=0, max_value=100, value=10)
    
    if st.button("Abfrage starten"):
        st.session_state.show_map = True

# Hauptbereich
if st.session_state.show_map:
    st.write(f"Suche in {gemarkung}: {such_modus} {ziel_groesse}m² (Toleranz: {toleranz}%)")
    
    # Karte mit voller Breite erstellen
    m = folium.Map(location=[53.25, 7.95], zoom_start=11)
    
    # Beispiel-Marker
    folium.Marker(
        [53.25, 7.95], 
        popup="Grundstücks-Details",
        icon=folium.Icon(color='blue', icon='home')
    ).add_to(m)
    
    # st_folium mit height und width für volle Größe
    st_folium(m, width=None, height=700)
else:
    st.info("Bitte Parameter in der Sidebar festlegen und Suche starten.")
