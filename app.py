import streamlit as st
import pandas as pd
from datetime import datetime, timedelta

# --- CONFIGURAZIONE ---
st.set_page_config(page_title="Turni Capitel", layout="wide")

STAFF = ['L', 'N', 'J', 'A', 'B', 'C', 'D', 'M', 'P', 'T', 'Z']

# Definiamo dove il ristorante è effettivamente APERTO
# (Basato sui tuoi dati: Lun-Ven solo Cena, Sab-Dom entrambi)
APERTO = {
    'Mon': ['C'], 'Tue': ['C'], 'Wed': ['C'], 'Thu': ['C'], 
    'Fri': ['C'], 'Sat': ['P', 'C'], 'Sun': ['P', 'C']
}

def get_calendar_grid(month, year):
    first_day = datetime(year, month, 1)
    start_date = first_day - timedelta(days=first_day.weekday())
    return [start_date + timedelta(days=i) for i in range(35)] # 5 settimane

# --- INIZIALIZZAZIONE ---
if 'indisp' not in st.session_state:
    st.session_state.indisp = {name: set() for name in STAFF}

st.title("🗓️ Gestione Turni Capitel")

tab1, tab2 = st.tabs(["❌ Segna Impegni (P/C)", "⚙️ Admin"])

with tab1:
    col_u, col_m = st.columns(2)
    user = col_u.selectbox("Seleziona il tuo nome", STAFF)
    mese = 4 # Aprile 2026
    
    st.subheader(f"Disponibilità per Aprile")
    st.info("Spunta solo i turni in cui NON puoi lavorare (P = Pranzo, C = Cena)")

    days = get_calendar_grid(mese, 2026)
    weekdays = ["Lun", "Mar", "Mer", "Gio", "Ven", "Sab", "Dom"]
    
    # Intestazione
    cols = st.columns(7)
    for i, name in enumerate(weekdays):
        cols[i].markdown(f"### {name}")

    # Griglia Calendario
    for i in range(0, 35, 7): # Per ogni settimana
        week_days = days[i:i+7]
        cols = st.columns(7)
        for j, day in enumerate(week_days):
            with cols[j]:
                if day.month == mese:
                    date_str = day.strftime("%d/%m")
                    dow = day.strftime("%a") # Es: Mon, Sat...
                    st.write(f"**{date_str}**")
                    
                    # Controlla quali turni mostrare per questo giorno
                    turni_possibili = APERTO.get(dow, ['C'])
                    
                    for t in turni_possibili:
                        label = "Pranzo" if t == 'P' else "Cena"
                        key = f"{user}_{day.day}_{t}"
                        id_turno = f"{date_str}-{t}"
                        
                        # Checkbox per il singolo turno
                        is_selected = id_turno in st.session_state.indisp[user]
                        if st.checkbox(f"{t}", value=is_selected, key=key, help=label):
                            st.session_state.indisp[user].add(id_turno)
                        else:
                            st.session_state.indisp[user].discard(id_turno)
                else:
                    st.write("")

    if st.button("Salva Disponibilità", type="primary"):
        st.success(f"Impegni di {user} aggiornati correttamente!")

with tab2:
    st.header("Area Amministratore")
    if st.button("Visualizza Riepilogo Indisponibilità"):
        st.write(st.session_state.indisp)
