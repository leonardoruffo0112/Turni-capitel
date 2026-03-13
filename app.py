import streamlit as st
import subprocess
import sys

# --- FORZA INSTALLAZIONE (SOLUZIONE ERRORE) ---
try:
    from st_gsheets_connection import GSheetsConnection
except ImportError:
    subprocess.check_call([sys.executable, "-m", "pip", "install", "st-gsheets-connection"])
    from st_gsheets_connection import GSheetsConnection

import pandas as pd
import random
from datetime import datetime, timedelta

# --- CONFIGURAZIONE ---
st.set_page_config(page_title="Turni Capitel", layout="wide")

# Parametri Staff e Regole
STAFF_INFO = {
    'L': {'exp': True}, 'N': {'exp': True}, 'J': {'exp': True},
    'A': {'exp': False}, 'B': {'exp': False}, 'C': {'exp': False},
    'D': {'exp': False}, 'M': {'exp': False}, 'P': {'exp': False},
    'T': {'exp': False}, 'Z': {'exp': False}
}
STAFF_NAMES = list(STAFF_INFO.keys())

# Fabbisogno (Persone Totali, Esperti Minimi)
REQUISITI = {
    'Mon': {'C': (3, 0)}, 'Tue': {'C': (2, 0)}, 'Wed': {'C': (3, 0)}, 
    'Thu': {'C': (4, 0)}, 'Fri': {'C': (4, 0)}, 
    'Sat': {'P': (3, 0), 'C': (6, 2)}, # 2 Esperti Sabato sera
    'Sun': {'P': (5, 2), 'C': (4, 0)}  # 2 Esperti Domenica pranzo
}

# Connessione
conn = st.connection("gsheets", type=GSheetsConnection)

def get_calendar_grid(month, year):
    first_day = datetime(year, month, 1)
    start_date = first_day - timedelta(days=first_day.weekday())
    return [start_date + timedelta(days=i) for i in range(35)]

st.title("🗓️ Gestione Turni Capitel")

tab1, tab2 = st.tabs(["❌ Segna Impegni", "⚙️ Admin & Generazione"])

# --- TABELLA 1: INSERIMENTO ---
with tab1:
    user = st.selectbox("Seleziona il tuo nome", STAFF_NAMES)
    mese, anno = 4, 2026 # Aprile
    
    st.subheader(f"Disponibilità per Aprile")
    days = get_calendar_grid(mese, anno)
    
    current_nos = []
    cols_h = st.columns(7)
    weekdays_labels = ["Lun", "Mar", "Mer", "Gio", "Ven", "Sab", "Dom"]
    for i, name in enumerate(weekdays_labels): cols_h[i].markdown(f"**{name}**")

    for i in range(0, 35, 7):
        week_days = days[i:i+7]
        cols = st.columns(7)
        for j, day in enumerate(week_days):
            with cols[j]:
                if day.month == mese:
                    date_str = day.strftime("%d/%m")
                    dow = day.strftime("%a")
                    # Mappa nomi giorni in inglese -> chiavi REQUISITI
                    mapping = {"Mon":"Mon", "Tue":"Tue", "Wed":"Wed", "Thu":"Thu", "Fri":"Fri", "Sat":"Sat", "Sun":"Sun"}
                    day_key = mapping[dow]
                    
                    st.write(f"**{date_str}**")
                    turni_possibili = list(REQUISITI[day_key].keys())
                    for t in turni_possibili:
                        if st.checkbox(f"{t}", key=f"{user}_{day.day}_{t}"):
                            current_nos.append({"Nome": user, "Data": date_str, "Turno": t})
                else: st.write("")

    if st.button("SALVA DEFINITIVAMENTE", type="primary"):
        try:
            existing_df = conn.read(worksheet="indisponibilita")
            existing_df = existing_df[existing_df['Nome'] != user]
            updated_df = pd.concat([existing_df, pd.DataFrame(current_nos)], ignore_index=True)
            conn.update(worksheet="indisponibilita", data=updated_df)
            st.success(f"Dati salvati per {user}!")
        except:
            conn.update(worksheet="indisponibilita", data=pd.DataFrame(current_nos))
            st.success("Primo salvataggio effettuato!")

# --- TABELLA 2: ADMIN E LOGICA ---
with tab2:
    st.header("Cervello dell'App")
    
    try:
        df_indisp = conn.read(worksheet="indisponibilita")
        st.write("Indisponibilità caricate:", df_indisp.shape[0])
    except:
        df_indisp = pd.DataFrame(columns=["Nome", "Data", "Turno"])

    if st.button("🚀 GENERA TABELLONE TURNI"):
        results = []
        carico_lavoro = {name: 0 for name in STAFF_NAMES}
        
        # Iterazione giorni del mese
        month_days = [d for d in get_calendar_grid(mese, anno) if d.month == mese]
        
        for d in month_days:
            date_str = d.strftime("%d/%m")
            day_key = d.strftime("%a") # Es: 'Sat'
            config = REQUISITI.get(day_key, {})
            
            for fascia, (n_tot, n_exp) in config.items():
                # Chi non ha dato il "NO"?
                occupati = df_indisp[(df_indisp['Data'] == date_str) & (df_indisp['Turno'] == fascia)]['Nome'].tolist()
                disponibili = [n for n in STAFF_NAMES if n not in occupati]
                
                # Scegliamo prima gli esperti necessari
                esperti_disp = [n for n in disponibili if STAFF_INFO[n]['exp']]
                esperti_disp.sort(key=lambda x: carico_lavoro[x]) # Prendi chi ha lavorato meno
                
                scelti = esperti_disp[:n_exp]
                
                # Riempire il resto (Esperti restanti + Base)
                restanti_disp = [n for n in disponibili if n not in scelti]
                restanti_disp.sort(key=lambda x: carico_lavoro[x])
                
                posti_mancanti = n_tot - len(scelti)
                scelti.extend(restanti_disp[:posti_mancanti])
                
                for s in scelti: carico_lavoro[s] += 1
                
                results.append({"Data": date_str, "Giorno": day_key, "Turno": fascia, "Chi": ", ".join(scelti)})
        
        st.subheader("Tabellone Risultante")
        st.table(pd.DataFrame(results))
        st.write("Bilanciamento finale:", carico_lavoro)

    st.divider()
    if st.button("🗑️ AZZERA TUTTO"):
        conn.update(worksheet="indisponibilita", data=pd.DataFrame(columns=["Nome", "Data", "Turno"]))
        st.warning("Database pulito.")
