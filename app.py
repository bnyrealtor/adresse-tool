import streamlit as st
import geopandas as gpd
from owslib.wfs import WebFeatureService
from geopy.geocoders import Nominatim
from pyproj import Transformer
import folium
from streamlit_folium import st_folium

st.set_page_config(page_title="ImmoDaten-Tool NI", layout="wide")

# --- SIDEBAR ---
st.sidebar.header("Filter & Parameter")

gemeinden_ammerland = ["Apen", "Bad Zwischenahn", "Edewecht", "Rastede", "Westerstede", "Wiefelstede"]
gemeinde = st.sidebar.selectbox("Gemeinde", gemeinden_ammerland, index=2)

groesse_option = st.sidebar.radio("Größen-Modus", ["Exakt", "Mindestgröße"])
groesse_wert = st.sidebar.number_input("Größe in m²", min_value=0, value=None, placeholder="z.B. 1000")
toleranz = st.sidebar.number_input("Toleranz (+/- in m²)", min_value=0, value=3, placeholder="z.B. 3")

start_search = st.sidebar.button("Suche starten")

# --- HAUPTTEIL ---
st.title("Immobilien-Abfrage & Grundsteuer-Tool")

# --- FUNKTIONEN ---
def get_coords(gemeinde_name):
    geolocator = Nominatim(user_agent="radtke_immo_tool")
    query = f"{gemeinde_name}, Landkreis Ammerland, Niedersachsen, Germany"
    location = geolocator.geocode(query)
    return (location.latitude, location.longitude) if location else None

def fetch_wfs_data(lat, lon):
    wfs = WebFeatureService(url="https://opendata.lgln.niedersachsen.de/wfs/gds_alkis", version="2.0.0")
    transformer = Transformer.from_crs("EPSG:4326", "EPSG:25832", always_xy=True)
    e, n = transformer.transform(lon, lat)
    bbox = (e-1000, n-1000, e+1000, n+1000) 
    response = wfs.getfeature(typename='alkis:flurstueck', bbox=bbox, outputFormat='json')
    return gpd.read_file(response)

# --- LOGIK ---
if start_search:
    if groesse_wert is None:
        st.sidebar.error("Bitte Größe eingeben!")
    else:
        with st.spinner(f"Suche Flurstücke in {gemeinde}..."):
            coords = get_coords(gemeinde)
            if coords:
                lat, lon = coords
                gdf = fetch_wfs_data(lat, lon)
                
                if not gdf.empty:
                    # Spalten-Erkennung
                    size_col = next((col for col in ['flaeche', 'flaeche_qm', 'amtliche_flaeche', 'area'] if col in gdf.columns), None)
                    
                    t = toleranz if toleranz is not None else 0
                    if size_col:
                        if groesse_option == "Exakt":
                            filtered_gdf = gdf[(gdf[size_col] >= (groesse_wert - t)) & (gdf[size_col] <= (groesse_wert + t))]
                        else:
                            filtered_gdf = gdf[gdf[size_col] >= groesse_wert]
                    else:
                        filtered_gdf = gdf
                    
                    if not filtered_gdf.empty:
                        st.success(f"{len(filtered_gdf)} Flurstücke gefunden!")
                        m = folium.Map(location=[lat, lon], zoom_start=14)
                        
                        for _, row in filtered_gdf.iterrows():
                            adresse = row.get('lagebezeichnung', 'Adresse unbekannt')
                            popup_html = f"""
                                <div style="font-family: sans-serif; width: 220px;">
                                    <b>Adresse:</b><br>
                                    <div style="background-color: #f0f0f0; padding: 5px; border: 1px solid #ccc; border-radius: 3px; font-weight: bold;">
                                        {adresse}
                                    </div>
                                    <p style="font-size: 10px; color: #666; margin-top: 5px;">(Doppelklick zum Kopieren)</p>
                                    <a href="https://grundsteuer-viewer.niedersachsen.de/b" target="_blank" 
                                       style="display: block; background-color: #28a745; color: white; padding: 10px; text-align: center; text-decoration: none; border-radius: 5px; font-weight: bold;">
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
                    st.warning("Keine Daten vom Katasteramt erhalten.")
            else:
                st.error("Koordinaten für Gemeinde nicht gefunden.")
