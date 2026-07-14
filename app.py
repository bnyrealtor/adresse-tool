import streamlit as st
import pandas as pd

st.set_page_config(page_title="Immo-Finder", layout="centered")
st.title("Immobilien-Suche (Lokal)")

# 1. Datenbank laden
@st.cache_data
def load_data():
    return pd.read_csv('alkis_local_database.csv')

df = load_data()

# 2. UI: PLZ und Grundstücksgröße
plz_input = st.text_input("Postleitzahl")
groesse_input = st.number_input("Grundstücksgröße (in qm)", min_value=0)

if st.button("Adresse finden"):
    # Filterung
    mask = (df['plz'] == plz_input) & (df['grundstuecksgroesse_qm'] == groesse_input)
    result = df[mask]
    
    if not result.empty:
        st.success(f"Gefundene Objekte: {len(result)}")
        st.table(result[['strasse_hausnummer', 'grundstuecksgroesse_qm']])
    else:
        st.warning("Kein Objekt gefunden.")
