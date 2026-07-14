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

# Dropdown für die Gemeinden im Landkreis Ammerland
gemeinden_ammerland = [
    "Apen",
    "Bad Zwischenahn",
    "Edewecht",
    "Rastede",
    "Westerstede",
    "Wiefelstede"
]

# Standardmäßig auf Edewecht gesetzt
gemeinde = st.sidebar.selectbox("Gemeinde", gemeinden_ammerland, index=2)

groesse_option = st.sidebar.radio("Größen-Modus", ["Exakt", "Mindestgröße"])
groesse_wert = st.sidebar.number_input("Größe in m²", min_value=0, value=None)
toleranz = st.sidebar.number_input("Toleranz (+/- in m²)", min_value=0, value=None)

st.title("Immobilien-Abfrage & Grundsteuer-Tool")

# --- FUNKTIONEN ---
def get_coords(gemeinde_name):
    # Fokussiert die Suche auf den Landkreis Ammerland in Niedersachsen
    geolocator = Nominatim(user_agent="radtke_immo_tool")
    query = f"{gemeinde_name}, Landkreis Ammerland, Niedersachsen, Germany"
    location = geolocator.geocode(query)
    return (location.latitude, location.longitude) if location else None

def fetch_wfs_data(lat, lon):
    wfs = WebFeatureService(url="https://opendata.lgln.niedersachsen.de/wfs/gds_alkis", version="2.0.0")
    transformer = Transformer.from_crs("EPSG:4326", "EPSG:25832", always_xy=True)
    e, n = transformer.transform(lon, lat)
    
    # Radius für die Umgebungssuche (1000m um den Gemeinde-Mittelpunkt)
    bbox = (e-1000, n-1000, e+1000, n+1000) 
    response = wfs.getfeature(typename='alkis:flurstueck', bbox=bbox, outputFormat='json')
    return gpd.read_file(response)

# --- HAUPTTEIL ---
if st.button("Suche starten"):
    with st.spinner(f"Suche Flurstücke in {gemeinde}..."):
        coords = get_coords(gemeinde)
        if coords:
            lat, lon = coords
            gdf = fetch_wfs_data(lat, lon)
            
            if not gdf.empty:
                # Dynamische Erkennung der Flächenspalte in den ALKIS-Daten
                size_col = None
                for col in ['flaeche', 'flaeche_qm', 'amtliche_flaeche', 'area']:
                    if col in gdf.columns:
                        size_col = col
                        break
                
                # Filterung anwenden
                if size_col:
                    if groesse_option == "Exakt":
                        filtered_gdf = gdf[(gdf[size_col] >= (groesse_wert - toleranz)) & (gdf[size_col] <= (groesse_wert + toleranz))]
                    else:
                        filtered_gdf = gdf[gdf[size_col] >= groesse_wert]
                else:
                    st.warning("Flächenspalte im ALKIS-Datensatz nicht automatisch erkannt. Zeige alle Flurstücke.")
                    filtered_gdf = gdf
                
                if not filtered_gdf.empty:
                    st.success(f"{len(filtered_gdf)} Flurstücke in {gemeinde} gefunden!")
                    
                    # Karte initialisieren
                    m = folium.Map(location=[lat, lon], zoom_start=14)
                    
                    for _, row in filtered_gdf.iterrows():
                        # Adress-Zusammensetzung
                        adresse = row.get('lagebezeichnung', None)
                        if not adresse:
                            # Ausweichlösung für getrennte Tabellenspalten
                            strasse = row.get('strasse', row.get('strname', ''))
                            hausnummer = row.get('hausnummer', row.get('hsnr', ''))
                            adresse = f"{strasse} {hausnummer}".strip() if strasse else f"Flurstück {row.get('gemarkung', '')}"
                        
                        # Formatierung vervollständigen
                        if adresse and gemeinde not in adresse:
                            adresse = f"{adresse}, {gemeinde}"
                            
                        popup_html = f"""
                            <div style="font-family: sans-serif; width: 220px;">
                                <b>Adresse:</b><br>
                                <div style="background-color: #f0f0f0; padding: 5px; border: 1px solid #ccc; border-radius: 3px; font-weight: bold;">
                                    {adresse}
                                </div>
                                <p style="font-size: 10px; color: #666; margin-top: 5px;">
                                    (Doppelklick zum Kopieren)
                                </p>
                                <br>
                                <a href="https://grundsteuer-viewer.niedersachsen.de/b" target="_blank" 
                                   style="display: block; background-color: #28a745; color: white; padding: 10px; 
                                          text-align: center; text-decoration: none; border-radius: 5px; font-weight: bold;">
                                    Zum Grundsteuer-Viewer
                                </a>
                            </div>
                        """
                        # Verwende den geografischen Mittelpunkt des Grundstücks für den Marker
                        centroid = row.geometry.centroid
                        folium.Marker(
                            [centroid.y, centroid.x], 
                            popup=folium.Popup(popup_html, max_width=250)
                        ).add_to(m)
                    
                    st_folium(m, width=1000, height=600)
                else:
                    st.warning(f"Keine passenden Flurstücke mit der gewünschten Größe in {gemeinde} gefunden.")
            else:
                st.warning("Keine Flurstücksdaten vom Katasteramt für diesen Bereich erhalten.")
        else:
            st.error(f"Koordinaten für {gemeinde} konnten nicht ermittelt werden.")
