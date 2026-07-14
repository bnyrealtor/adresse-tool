import streamlit as st
import folium
from streamlit_folium import st_folium

# Konfiguration
st.set_page_config(page_title="Immobilien-Tool", layout="wide")
st.title("LGLN Grundstücks-Daten-Tool")

# Liste der Gemeinden im Ammerland, alphabetisch sortiert
AMMERLAND_GEMEINDEN = sorted([
    "Apen",
    "Bad Zwischenahn",
    "Edewecht",
    "Friedrichsfehn",
    "Rastede",
    "Westerstede",
    "Wiefelstede"
])

# Sidebar für die Eingabe
with st.sidebar:
    st.header("Suche")
    # Dropdown mit sortierten Ammerland-Gemeinden
    gemarkung = st.selectbox("Gemarkung wählen", AMMERLAND_GEMEINDEN)
    flur = st.text_input("Flur")
    zaehler = st.text_input("Zähler")
    nenner = st.text_input("Nenner")
    run_button = st.button("Abfrage starten")

# Hauptbereich
if run_button:
    # Hier erfolgt deine Logik zur Verarbeitung der Auswahl
    st.write(f"Ausgewählte Gemarkung: {gemarkung}")
    st.write(f"Suche nach: Flur {flur}, Zähler {zaehler}, Nenner {nenner}")
    
    # Beispielkarte (Fokus auf Ammerland/Oldenburg)
    m = folium.Map(location=[53.25, 7.95], zoom_start=11)
    
    # Popup-HTML mit Copy-Funktion und Link
    # Hier wird die Adresse im Format "Gemeinde Flur Zähler/Nenner" für das Kopieren definiert
    adresse_fuer_copy = f"{gemarkung} {flur} {zaehler}/{nenner}"
    
    popup_html = f"""
    <div style="width: 250px; font-family: sans-serif; padding: 5px;">
        <div style="font-size: 16px; font-weight: bold; margin-bottom: 12px; border-bottom: 1px solid #ccc; padding-bottom: 5px;">
            {adresse_fuer_copy}
        </div>
        <button onclick="navigator.clipboard.writeText('{adresse_fuer_copy}'); alert('Adresse kopiert: {adresse_fuer_copy}');" 
                style="background-color: #007bff; color: white; border: none; padding: 10px; border-radius: 5px; cursor: pointer; width: 100%; font-weight: bold; margin-bottom: 8px;">
            📋 Adresse kopieren
        </button>
        <a href="https://grundsteuer-viewer.niedersachsen.de/b" target="_blank" 
           style="background-color: #28a745; color: white; border: none; padding: 10px; border-radius: 5px; cursor: pointer; width: 100%; text-align: center; display: block; text-decoration: none; font-weight: bold;">
            Zum Grundsteuer-Viewer
        </a>
    </div>
    """
    
    folium.Marker(
        [53.25, 7.95], 
        popup=folium.Popup(popup_html, max_width=300),
        icon=folium.Icon(color='blue', icon='home')
    ).add_to(m)
    
    st_folium(m, width=700, height=500)
else:
    st.info("Bitte Gemeinde wählen und Daten eingeben.")
