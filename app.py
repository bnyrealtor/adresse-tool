import streamlit as st
import geopandas as gpd
from owslib.wfs import WebFeatureService
from geopy.geocoders import Nominatim
from pyproj import Transformer
import folium
from streamlit_folium import st_folium

# Konfiguration
st.set_page_config(page_title="Immobilien-Tool", layout="wide")
st.title("LGLN Immobilien-Daten-Tool")

# 1. Geocoding: Adresse zu Koordinaten
def get_coords(address):
    geolocator = Nominatim(user_agent="radtke_immo_tool_v2")
    location = geolocator.geocode(address)
    if location:
        return location.latitude, location.longitude
    return None

# 2. WFS-Abfrage
def fetch_wfs_data(lat, lon):
    try:
        wfs = WebFeatureService(url="https://opendata.lgln.niedersachsen.de/wfs/gds_alkis", version="2.0.0")
        transformer = Transformer.from_crs("EPSG:4326", "EPSG:25832", always_xy=True)
        e, n = transformer.transform(lon, lat)
        bbox = (e-50, n-50, e+50, n+50)
        
        # 'alkis:flurstueck' ist der Standard-Layer. Ggf. anpassen!
        response = wfs.getfeature(typename='alkis:flurstueck', bbox=bbox, outputFormat='json')
        return gpd.read_file(response)
    except Exception as e:
        st.error(f"Fehler bei der WFS-Abfrage: {e}")
        return None

# UI
address_input = st.text_input("Adresse eingeben (Straße, PLZ, Ort)")

if st.button("Abfrage starten"):
    coords = get_coords(address_input)
    if coords:
        lat, lon = coords
        gdf = fetch_wfs_data(lat, lon)
        
        if gdf is not None and not gdf.empty:
            # Hier Spaltennamen anpassen, falls die Adressdaten anders heißen
            # Falls deine Daten eine Spalte 'lagebezeichnung' haben:
            adresse_text = gdf.iloc[0].get('lagebezeichnung', 'Adresse nicht verfügbar')
            
            # Popup-HTML (Dein gewünschtes Format)
            popup_html = f"""
            <div style="width: 250px; font-family: sans-serif; padding: 5px;">
                <div style="font-size: 16px; font-weight: bold; margin-bottom: 12px; border-bottom: 1px solid #ccc; padding-bottom: 5px;">
                    {adresse_text}
                </div>
                <button onclick="navigator.clipboard.writeText('{adresse_text}'); alert('Kopiert: {adresse_text}');" 
                        style="background-color: #007bff; color: white; border: none; padding: 10px; border-radius: 5px; cursor: pointer; width: 100%; font-weight: bold; margin-bottom: 8px;">
                    📋 Adresse kopieren
                </button>
                <a href="https://grundsteuer-viewer.niedersachsen.de/b" target="_blank" 
                   style="background-color: #28a745; color: white; border: none; padding: 10px; border-radius: 5px; cursor: pointer; width: 100%; text-align: center; display: block; text-decoration: none; font-weight: bold;">
                    Zum Grundsteuer-Viewer
                </a>
            </div>
            """
            
            # Karte erstellen
            m = folium.Map(location=[lat, lon], zoom_start=19)
            folium.Marker(
                [lat, lon],
                popup=folium.Popup(popup_html, max_width=300),
                icon=folium.Icon(color='blue', icon='home')
            ).add_to(m)
            
            st_folium(m, width=700, height=500)
        else:
            st.warning("Keine Daten gefunden.")
    else:
        st.error("Adresse nicht gefunden.")
