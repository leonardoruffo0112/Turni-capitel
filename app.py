import streamlit as st
import pandas as pd
from datetime import datetime, timedelta

# Importazione corretta per il codice
from streamlit_gsheets import GSheetsConnection

# ... il resto del tuo codice da qui in poi ...

# --- 2. CONFIGURAZIONE E REGOLE ---
st.set_page_config(page_title="Turni Capitel", layout="wide")

# Lista Staff: L, N, J sono esperti. J può fare più turni.
STAFF_INFO = {
    'L': {'exp': True, 'max': 16}, 'N': {'exp': True, 'max': 16}, 'J': {'exp': True, 'max': 20},
    'A': {'exp': False, 'max': 16}, 'B': {'exp': False, 'max': 16}, 'C': {'exp': False, 'max': 16},
    'D': {'exp': False, 'max': 16}, 'M': {'exp': False, 'max': 16}, 'P': {'exp': False, 'max': 16},
    'T': {'exp': False, 'max': 16}, 'Z': {'exp': False, 'max': 16}
}
STAFF_NAMES = list(STAFF_INFO.keys())

# Fabbisogno settimanale: (Persone Totali, Esperti Minimi)
REQUISITI_SETTIMANA = {
    'Mon': {'C': (3, 0)}, 'Tue': {'C': (2, 0)}, 'Wed': {'C': (3, 0)}, 
    'Thu': {'C': (4, 0)}, 'Fri': {'C': (4, 0)}, 
    'Sat': {'P': (3, 0), 'C': (6, 2)}, # Sabato cena: 2 esperti
    'Sun': {'P': (5, 2), 'C': (4, 0)}  # Domenica pranzo: 2 esperti
}

# --- 3. CONNESSIONE ---
conn = st.connection("gsheets", type=GSheetsConnection)

def get_calendar_days(month, year):
    first_day = datetime(year, month, 1)
    # Partiamo dal lunedì della prima settimana
    start_date = first_day - timedelta(days=first_day.weekday())
    return [start_date + timedelta(days=i) for i in range(35)]

# --- 4. INTERFACCIA ---
st.title("🗓️ Gestione Turni Capitel")

tab1, tab2 = st.tabs(["❌ Segna i tuoi impegni", "⚙️ Admin & Generatore"])

# --- TAB 1: INSERIMENTO DISPONIBILITÀ ---
with tab1:
    user = st.selectbox("Seleziona il tuo nome", STAFF_NAMES)
    mese, anno = 4, 2026 # Impostato su Aprile
    
    st.subheader(f"I tuoi impegni per Aprile")
    st.info("Spunta i turni in cui NON puoi lavorare (P=Pranzo, C=Cena). Se sei libero, non segnare nulla.")

    days = get_calendar_days(mese, anno)
    weekdays_labels = ["Lun", "Mar", "Mer", "Gio", "Ven", "Sab", "Dom"]
    
    # Intestazione giorni
    cols_h = st.columns(7)
    for i, name in enumerate(weekdays_labels): cols_h[i].markdown(f"**{name}**")

    # Griglia calendario
    current_user_nos = []
    for i in range(0, 35, 7):
        week_days = days[i:i+7]
        cols = st.columns(7)
        for j, day in enumerate(week_days):
            with cols[j]:
                if day.month == mese:
                    date_str = day.strftime("%d/%m")
                    dow = day.strftime("%a")
                    # Mappa nomi giorni per requisiti
                    mapping = {"Mon":"Mon", "Tue":"Tue", "Wed":"Wed", "Thu":"Thu", "Fri":"Fri", "Sat":"Sat", "Sun":"Sun"}
                    day_key = mapping[dow]
                    
                    st.write(f"**{date_str}**")
                    turni_possibili = list(REQUISITI_SETTIMANA[day_key].keys())
                    for t in turni_possibili:
                        if st.checkbox(f"{t}", key=f"{user}_{day.day}_{t}"):
                            current_user_nos.append({"Nome": user, "Data": date_str, "Turno": t})
                else: st.write("")

    if st.button("CONFERMA E SALVA", type="primary"):
        try:
            # Carica dati esistenti per non sovrascrivere altri colleghi
            try:
                df_old = conn.read(worksheet="indisponibilita")
                df_old = df_old[df_old['Nome'] != user] # Rimuovi vecchi dati di questo utente
            except:
                df_old = pd.DataFrame(columns=["Nome", "Data", "Turno"])
            
            # Unisci e aggiorna
            new_rows = pd.DataFrame(current_user_nos)
            updated_df = pd.concat([df_old, new_rows], ignore_index=True)
            conn.update(worksheet="indisponibilita", data=updated_df)
            st.success(f"Perfetto {user}, impegni salvati!")
        except Exception as e:
            st.error(f"Errore di connessione: {e}")

# --- TAB 2: AMMINISTRATORE ---
with tab2:
    st.header("Area Amministratore")
    
    # Leggi tutti i NO
    try:
        df_indisp = conn.read(worksheet="indisponibilita")
        st.write(f"Dati raccolti: {len(df_indisp)} impegni segnati dallo staff.")
    except:
        df_indisp = pd.DataFrame(columns=["Nome", "Data", "Turno"])

    if st.button("🚀 GENERA TURNI DEL MESE"):
        if df_indisp.empty:
            st.warning("Nessun impegno caricato. Genererò i turni presumendo che tutti siano sempre liberi.")
        
        results = []
        carico_lavoro = {name: 0 for name in STAFF_NAMES}
        month_days = [d for d in get_calendar_days(mese, anno) if d.month == mese]

        for d in month_days:
            date_str = d.strftime("%d/%m")
            day_key = d.strftime("%a")
            config = REQUISITI_SETTIMANA.get(day_key, {})

            for fascia, (n_tot, n_exp) in config.items():
                # Chi è disponibile (non è nei NO)?
                occupati = df_indisp[(df_indisp['Data'] == date_str) & (df_indisp['Turno'] == fascia)]['Nome'].tolist()
                disponibili = [n for n in STAFF_NAMES if n not in occupati]
                
                # Scegliamo gli esperti necessari
                esperti_disp = [n for n in disponibili if STAFF_INFO[n]['exp']]
                esperti_disp.sort(key=lambda x: carico_lavoro[x]) # Priorità a chi ha lavorato meno
                
                scelti = esperti_disp[:n_exp]
                
                # Completiamo il resto dello staff
                restanti_disp = [n for n in disponibili if n not in scelti]
                restanti_disp.sort(key=lambda x: carico_lavoro[x])
                
                mancanti = n_tot - len(scelti)
                scelti.extend(restanti_disp[:mancanti])
                
                # Aggiorna carico e salva
                for s in scelti: carico_lavoro[s] += 1
                results.append({"Data": date_str, "Turno": fascia, "Staff": ", ".join(scelti)})
        
        st.subheader("Tabellone di Aprile")
        st.table(pd.DataFrame(results))
        st.write("Totale turni per persona:", carico_lavoro)

    st.divider()
    if st.button("🗑️ RESET DATABASE (NUOVO MESE)"):
        conn.update(worksheet="indisponibilita", data=pd.DataFrame(columns=["Nome", "Data", "Turno"]))
        st.info("Database pulito. I colleghi possono inserire i dati per il nuovo mese.")
