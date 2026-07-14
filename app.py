import streamlit as st
import geopandas as gpd
from owslib.wfs import WebFeatureService
from geopy.geocoders import Nominatim
from pyproj import Transformer
import folium
from streamlit_folium import st_folium

st.set_page_config(page_title="ImmoDaten-Tool NI", layout="wide")

# --- SIDEBAR KONFIGURATION ---
st.sidebar.header("Filter & Parameter")
ort = st.sidebar.text_input("Ort oder Gemeinde", value="Oldenburg")
groesse_option = st.sidebar.radio("Größen-Modus", ["Exakt", "Mindestgröße"])
groesse_wert = st.sidebar.number_input("Größe in m²", min_value=0, value=500)
toleranz = st.sidebar.number_input("Toleranz (+/- in m²)", min_value=0, value=50)

st.title("Immobilien-Abfrage & Grundsteuer-Tool")

# --- FUNKTIONEN ---
def get_coords(address):
    geolocator = Nominatim(user_agent="radtke_immo_tool")
    location = geolocator.geocode(address)
    return (location.latitude, location.longitude) if location else None

def fetch_wfs_data(lat, lon):
    wfs = WebFeatureService(url="https://opendata.lgln.niedersachsen.de/wfs/gds_alkis", version="2.0.0")
    transformer = Transformer.from_crs("EPSG:4326", "EPSG:25832", always_xy=True)
    e, n = transformer.transform(lon, lat)
    bbox = (e-500, n-500, e+500, n+500) # Erhöhter Radius für Suche
    response = wfs.getfeature(typename='alkis:flurstueck', bbox=bbox, outputFormat='json')
    return gpd.read_file(response)

# --- HAUPTTEIL ---
if st.button("Suche starten"):
    with st.spinner("Suche Flurstücke..."):
        coords = get_coords(ort)
        if coords:
            lat, lon = coords
            gdf = fetch_wfs_data(lat, lon)
            
            if not gdf.empty:
                # Filterung nach Grundstücksgröße
                # WICHTIG: Ersetze 'flaeche' durch den tatsächlichen Spaltennamen deines GDF
                if groesse_option == "Exakt":
                    filtered_gdf = gdf[(gdf['flaeche'] >= (groesse_wert - toleranz)) & (gdf['flaeche'] <= (groesse_wert + toleranz))]
                else:
                    filtered_gdf = gdf[gdf['flaeche'] >= groesse_wert]
                
                st.success(f"{len(filtered_gdf)} Flurstücke gefunden!")
                
                # Karte anzeigen
                m = folium.Map(location=[lat, lon], zoom_start=15)
                
                for _, row in filtered_gdf.iterrows():
                    # Popup-HTML
                    adresse = row.get('lagebezeichnung', 'Adresse unbekannt')
                    popup_html = f"""
                        <div style="font-family: sans-serif; width: 220px;">
                            <b>Adresse:</b><br>
                            <div style="background-color: #f0f0f0; padding: 5px; border: 1px solid #ccc; border-radius: 3px; font-weight: bold;">
                                {adresse}
                            </div>
                            <br>
                            <a href="https://grundsteuer-viewer.niedersachsen.de/b" target="_blank" 
                               style="display: block; background-color: #28a745; color: white; padding: 10px; 
                                      text-align: center; text-decoration: none; border-radius: 5px; font-weight: bold;">
                                Zum Grundsteuer-Viewer
                            </a>
                        </div>
                    """
                    folium.Marker([row.geometry.centroid.y, row.geometry.centroid.x], 
                                  popup=folium.Popup(popup_html, max_width=250)).add_to(m)
                
                st_folium(m, width=1000, height=600)
            else:
                st.warning("Keine passenden Flurstücke gefunden.")
        else:
            st.error("Ort nicht gefunden.")
