import streamlit as st
import geopandas as gpd
from owslib.wfs import WebFeatureService
from geopy.geocoders import Nominatim
from pyproj import Transformer
import folium
from streamlit_folium import st_folium

st.set_page_config(page_title="Immobilien-Tool NI", layout="wide")
st.title("Immobilien-Abfrage & Grundsteuer-Tool")

# 1. Geocoding
def get_coords(address):
    geolocator = Nominatim(user_agent="radtke_immo_tool")
    location = geolocator.geocode(address)
    if location:
        return location.latitude, location.longitude
    return None

# 2. WFS Abfrage
def fetch_wfs_data(lat, lon):
    wfs = WebFeatureService(url="https://opendata.lgln.niedersachsen.de/wfs/gds_alkis", version="2.0.0")
    transformer = Transformer.from_crs("EPSG:4326", "EPSG:25832", always_xy=True)
    e, n = transformer.transform(lon, lat)
    bbox = (e-50, n-50, e+50, n+50)
    
    # Abfrage der Flurstücke
    response = wfs.getfeature(typename='alkis:flurstueck', bbox=bbox, outputFormat='json')
    return gpd.read_file(response)

# UI Eingabe
address_input = st.text_input("Adresse eingeben (Straße, PLZ, Ort)")

if st.button("Abfrage starten"):
    with st.spinner("Suche Flurstück..."):
        coords = get_coords(address_input)
        if coords:
            lat, lon = coords
            gdf = fetch_wfs_data(lat, lon)
            
            if not gdf.empty:
                # Annahme: Deine Daten enthalten eine Spalte 'lagebezeichnung'
                # Falls nicht, prüfe mit st.write(gdf.columns) die verfügbaren Spalten
                adresse_text = gdf.iloc[0].get('lagebezeichnung', address_input)
                
                # HTML Popup
                popup_html = f"""
                    <div style="font-family: sans-serif; width: 220px;">
                        <div style="margin-bottom: 10px;">
                            <b>Adresse:</b><br>
                            <div style="background-color: #f0f0f0; padding: 5px; border: 1px solid #ccc; border-radius: 3px; font-weight: bold;">
                                {adresse_text}
                            </div>
                            <p style="font-size: 10px; color: #666; margin-top: 5px;">
                                (Doppelklick zum Kopieren)
                            </p>
                        </div>
                        <a href="https://grundsteuer-viewer.niedersachsen.de/b" target="_blank" 
                           style="display: block; background-color: #28a745; color: white; padding: 10px; 
                                  text-align: center; text-decoration: none; border-radius: 5px; font-weight: bold;">
                            Zum Grundsteuer-Viewer
                        </a>
                    </div>
                """
                
                # Karte erstellen
                m = folium.Map(location=[lat, lon], zoom_start=19)
                folium.Marker(
                    [lat, lon], 
                    popup=folium.Popup(popup_html, max_width=250)
                ).add_to(m)
                
                st.success("Flurstück gefunden!")
                st_folium(m, width=700, height=500)
            else:
                st.warning("Keine Flurstücksdaten an diesem Punkt gefunden.")
        else:
            st.error("Adresse konnte nicht gefunden werden.")
