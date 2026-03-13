import streamlit as st
from st_gsheets_connection import GSheetsConnection
import pandas as pd
from datetime import datetime, timedelta

st.set_page_config(page_title="Turni Capitel", layout="wide")

# Connessione al Foglio Google
conn = st.connection("gsheets", type=GSheetsConnection)

STAFF = ['L', 'N', 'J', 'A', 'B', 'C', 'D', 'M', 'P', 'T', 'Z']
APERTO = {
    'Mon': ['C'], 'Tue': ['C'], 'Wed': ['C'], 'Thu': ['C'], 
    'Fri': ['C'], 'Sat': ['P', 'C'], 'Sun': ['P', 'C']
}

st.title("🗓️ Gestione Turni Capitel")

tab1, tab2 = st.tabs(["❌ Segna Impegni", "⚙️ Admin"])

with tab1:
    user = st.selectbox("Seleziona il tuo nome", STAFF)
    
    # Visualizzazione calendario (come prima)
    # ... (Codice del calendario di prima) ...
    
    # RACCOLTA DATI
    st.session_state.temp_indisp = [] # Lista temporanea per i clic correnti
    
    if st.button("SALVA DEFINITIVAMENTE NEL DATABASE", type="primary"):
        # Leggiamo i dati attuali
        existing_data = conn.read(worksheet="indisponibilita")
        
        # Creiamo le nuove righe (esempio)
        new_data = pd.DataFrame([{"Nome": user, "Data": d, "Turno": t} for d, t in lista_cliccata])
        
        # Uniamo e carichiamo
        updated_df = pd.concat([existing_data, new_data], ignore_index=True)
        conn.update(worksheet="indisponibilita", data=updated_df)
        st.success("Tutto salvato nel Foglio Google!")

with tab2:
    st.header("Controllo Admin")
    # Vediamo cosa hanno scritto i ragazzi
    df = conn.read(worksheet="indisponibilita")
    st.dataframe(df)
