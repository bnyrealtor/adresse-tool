import streamlit as st
import geopandas as gpd
import requests
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
groesse_wert = st.sidebar.number_input("Größe in m²", min_value=0, value=None, placeholder="z.B. 500")
toleranz = st.sidebar.number_input("Toleranz (+/- in m²)", min_value=0, value=None, placeholder="z.B. 50")

start_search = st.sidebar.button("Suche starten")

# --- HAUPTTEIL ---
st.title("Immobilien-Abfrage & Grundsteuer-Tool")

def fetch_wfs_data(lat, lon):
    transformer = Transformer.from_crs("EPSG:4326", "EPSG:25832", always_xy=True)
    e, n = transformer.transform(lon, lat)
    
    # Korrigierte URL: Das LGLN nutzt für ALKIS oft einen anderen Dienst-Pfad
    # Wir nutzen hier den WFS-Dienst für "Gemarkungen/Flurstücke"
    url = "https://opendata.lgln.niedersachsen.de/wfs/gds_alkis"
    
    # Viele WFS-Dienste erlauben kein application/json direkt. 
    # Wir fordern GML an, da Geopandas das lesen kann.
    params = {
        "service": "WFS",
        "version": "2.0.0",
        "request": "GetFeature",
        "typeName": "alkis:Flurstueck", # Beachte das große F bei Flurstueck
        "bbox": f"{e-1000},{n-1000},{e+1000},{n+1000}",
        "srsName": "EPSG:4326"
    }
    
    try:
        response = requests.get(url, params=params, timeout=30)
        response.raise_for_status()
        return gpd.read_file(response.text)
    except Exception as e:
        st.error(f"Datenabruf fehlgeschlagen: {e}")
        return gpd.GeoDataFrame()

if start_search:
    if groesse_wert is None:
        st.sidebar.error("Bitte Größe eingeben!")
    else:
        with st.spinner(f"Suche Flurstücke in {gemeinde}..."):
            geolocator = Nominatim(user_agent="radtke_immo_tool")
            location = geolocator.geocode(f"{gemeinde}, Landkreis Ammerland, Germany")
            
            if location:
                gdf = fetch_wfs_data(location.latitude, location.longitude)
                
                if not gdf.empty:
                    # Spalten-Erkennung (ALKIS-Standard ist oft 'flaeche')
                    size_col = next((col for col in ['flaeche', 'flaechenmass'] if col in gdf.columns), None)
                    
                    t = toleranz if toleranz is not None else 0
                    if size_col:
                        if groesse_option == "Exakt":
                            filtered_gdf = gdf[(gdf[size_col] >= (groesse_wert - t)) & (gdf[size_col] <= (groesse_wert + t))]
                        else:
                            filtered_gdf = gdf[gdf[size_col] >= groesse_wert]
                    else:
                        filtered_gdf = gdf
                    
                    if not filtered_gdf.empty:
                        st.success(f"{len(filtered_gdf)} Flurstücke in {gemeinde} gefunden!")
                        m = folium.Map(location=[location.latitude, location.longitude], zoom_start=14)
                        
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
                            centroid = row.geometry.centroid
                            folium.Marker([centroid.y, centroid.x], popup=folium.Popup(popup_html, max_width=250)).add_to(m)
                        
                        st_folium(m, width=1000, height=600)
                    else:
                        st.warning("Keine Flurstücke in dieser Größe gefunden.")
                else:
                    st.warning("Keine Daten erhalten. Prüfe die Layer-Eigenschaften.")
            else:
                st.error("Gemeinde nicht gefunden.")
