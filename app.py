import streamlit as st
from st_gsheets_connection import GSheetsConnection
import pandas as pd
from datetime import datetime, timedelta

# --- CONFIGURAZIONE ---
st.set_page_config(page_title="Turni Capitel", layout="wide")

# Connessione (usa i Secrets che hai impostato)
conn = st.connection("gsheets", type=GSheetsConnection)

STAFF = ['L', 'N', 'J', 'A', 'B', 'C', 'D', 'M', 'P', 'T', 'Z']
APERTO = {
    'Mon': ['C'], 'Tue': ['C'], 'Wed': ['C'], 'Thu': ['C'], 
    'Fri': ['C'], 'Sat': ['P', 'C'], 'Sun': ['P', 'C']
}

# --- FUNZIONI ---
def get_calendar_grid(month, year):
    first_day = datetime(year, month, 1)
    start_date = first_day - timedelta(days=first_day.weekday())
    return [start_date + timedelta(days=i) for i in range(35)]

st.title("🗓️ Gestione Turni Capitel")

tab1, tab2 = st.tabs(["❌ Segna Impegni", "⚙️ Admin"])

with tab1:
    user = st.selectbox("Seleziona il tuo nome", STAFF)
    mese = 4 # Aprile 2026
    
    st.subheader(f"Disponibilità per Aprile")
    st.info("Spunta i turni in cui NON puoi lavorare (P=Pranzo, C=Cena)")

    days = get_calendar_grid(mese, 2026)
    weekdays = ["Lun", "Mar", "Mer", "Gio", "Ven", "Sab", "Dom"]
    
    # Visualizzazione Calendario
    cols_h = st.columns(7)
    for i, name in enumerate(weekdays): cols_h[i].markdown(f"**{name}**")

    # Inizializziamo una lista temporanea per i NO di questa sessione
    current_nos = []

    for i in range(0, 35, 7):
        week_days = days[i:i+7]
        cols = st.columns(7)
        for j, day in enumerate(week_days):
            with cols[j]:
                if day.month == mese:
                    date_str = day.strftime("%d/%m")
                    dow = day.strftime("%a")
                    st.write(f"**{date_str}**")
                    turni_possibili = APERTO.get(dow, ['C'])
                    for t in turni_possibili:
                        if st.checkbox(f"{t}", key=f"{user}_{day.day}_{t}"):
                            current_nos.append({"Nome": user, "Data": date_str, "Turno": t})
                else: st.write("")

    if st.button("SALVA DEFINITIVAMENTE", type="primary"):
        if current_nos:
            try:
                # Leggi i dati esistenti
                existing_df = conn.read(worksheet="indisponibilita")
                # Rimuovi eventuali vecchi dati dello stesso utente per evitare duplicati
                existing_df = existing_df[existing_df['Nome'] != user]
                # Aggiungi i nuovi
                new_df = pd.DataFrame(current_nos)
                updated_df = pd.concat([existing_df, new_df], ignore_index=True)
                # Carica su Google
                conn.update(worksheet="indisponibilita", data=updated_df)
                st.success(f"Bravo {user}! I tuoi impegni sono stati salvati.")
            except Exception as e:
                st.error(f"Errore nel salvataggio: {e}")
        else:
            st.warning("Non hai selezionato alcun impegno (NO).")

with tab2:
    st.header("Controllo Amministratore")
    
    # 1. Visualizza dati correnti
    try:
        df_admin = conn.read(worksheet="indisponibilita")
        st.write("Indisponibilità raccolte finora:")
        st.dataframe(df_admin, use_container_width=True)
    except:
        st.write("Nessun dato presente nel foglio.")

    st.divider()
    
    # 2. Tasto di Pulizia (IL RESET)
    st.subheader("danger zone")
    st.write("Attenzione: questa operazione cancellerà tutte le indisponibilità salvate per iniziare un nuovo mese.")
    
    if st.button("🗑️ AZZERA TUTTO IL DATABASE", type="secondary"):
        # Creiamo un dataframe vuoto con solo le intestazioni
        empty_df = pd.DataFrame(columns=["Nome", "Data", "Turno"])
        conn.update(worksheet="indisponibilita", data=empty_df)
        st.warning("Database svuotato. Ora puoi iniziare a raccogliere i dati per il nuovo mese!")
