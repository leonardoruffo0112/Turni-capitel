import streamlit as st
import pandas as pd
from datetime import datetime, timedelta

# --- IMPORTAZIONE UFFICIALE ---
try:
    from streamlit_gsheets import GSheetsConnection
except ImportError:
    st.error("⚠️ Problema di libreria. Fai Reboot dell'app.")
    st.stop()

st.set_page_config(page_title="Turni Capitel", layout="wide")

# --- DATABASE PIN E STAFF ---
# Sostituisci questi PIN con quelli che darai ai ragazzi
PIN_STAFF = {
    'L': '1111', 'N': '2222', 'J': '3333', 'A': '4444', 
    'B': '5555', 'C': '6666', 'D': '7777', 'M': '8888', 
    'P': '9999', 'T': '1234', 'Z': '4321'
}
PIN_ADMIN = "0000" # La TUA password per creare i turni

STAFF_INFO = {
    'L': {'exp': True}, 'N': {'exp': True}, 'J': {'exp': True},
    'A': {'exp': False}, 'B': {'exp': False}, 'C': {'exp': False},
    'D': {'exp': False}, 'M': {'exp': False}, 'P': {'exp': False},
    'T': {'exp': False}, 'Z': {'exp': False}
}
STAFF_NAMES = list(STAFF_INFO.keys())

REQUISITI_SETTIMANA = {
    'Mon': {'C': (3, 0)}, 'Tue': {'C': (2, 0)}, 'Wed': {'C': (3, 0)}, 
    'Thu': {'C': (4, 0)}, 'Fri': {'C': (4, 0)}, 
    'Sat': {'P': (3, 0), 'C': (6, 2)},
    'Sun': {'P': (5, 2), 'C': (4, 0)}
}

conn = st.connection("gsheets", type=GSheetsConnection)

def get_calendar_days(month, year):
    first_day = datetime(year, month, 1)
    start_date = first_day - timedelta(days=first_day.weekday())
    return [start_date + timedelta(days=i) for i in range(35)]

st.title("🗓️ Gestione Turni Capitel")

tab1, tab2 = st.tabs(["❌ Segna i tuoi impegni", "⚙️ Admin & Generatore"])

# --- TAB 1: AREA RAGAZZI (PROTETTA DA PIN) ---
with tab1:
    col1, col2 = st.columns(2)
    user = col1.selectbox("Seleziona il tuo nome", STAFF_NAMES)
    pin_inserito = col2.text_input("Inserisci il tuo PIN", type="password")
    
    # Il calendario appare SOLO se il PIN è corretto
    if pin_inserito == PIN_STAFF[user]:
        mese, anno = 4, 2026
        st.success(f"Accesso consentito. Ciao {user}!")
        
        # Mostriamo i dati già inseriti da questo utente
        try:
            df_tutti = conn.read(worksheet="indisponibilita")
            miei_dati = df_tutti[df_tutti['Nome'] == user]
            if not miei_dati.empty:
                st.info(f"Hai già segnalato {len(miei_dati)} turni di indisponibilità. Se salvi di nuovo, sovrascriverai i dati precedenti.")
        except:
            pass # Il foglio potrebbe essere vuoto la prima volta

        st.subheader(f"I tuoi impegni per Aprile")
        st.write("Spunta i turni in cui NON puoi lavorare (P=Pranzo, C=Cena).")

        days = get_calendar_days(mese, anno)
        weekdays_labels = ["Lun", "Mar", "Mer", "Gio", "Ven", "Sab", "Dom"]
        
        cols_h = st.columns(7)
        for i, name in enumerate(weekdays_labels): cols_h[i].markdown(f"**{name}**")

        current_user_nos = []
        for i in range(0, 35, 7):
            week_days = days[i:i+7]
            cols = st.columns(7)
            for j, day in enumerate(week_days):
                with cols[j]:
                    if day.month == mese:
                        date_str = day.strftime("%d/%m")
                        dow = day.strftime("%a")
                        mapping = {"Mon":"Mon", "Tue":"Tue", "Wed":"Wed", "Thu":"Thu", "Fri":"Fri", "Sat":"Sat", "Sun":"Sun"}
                        day_key = mapping[dow]
                        
                        st.write(f"**{date_str}**")
                        for t in list(REQUISITI_SETTIMANA[day_key].keys()):
                            if st.checkbox(f"{t}", key=f"{user}_{day.day}_{t}"):
                                current_user_nos.append({"Nome": user, "Data": date_str, "Turno": t})
                    else: st.write("")

        if st.button("CONFERMA E SALVA", type="primary"):
            try:
                try:
                    df_old = conn.read(worksheet="indisponibilita")
                    df_old = df_old[df_old['Nome'] != user] 
                except:
                    df_old = pd.DataFrame(columns=["Nome", "Data", "Turno"])
                
                new_rows = pd.DataFrame(current_user_nos)
                updated_df = pd.concat([df_old, new_rows], ignore_index=True)
                conn.update(worksheet="indisponibilita", data=updated_df)
                st.success("Impegni salvati con successo nel database!")
            except Exception as e:
                st.error(f"Errore di connessione: {e}")
                
    elif pin_inserito != "":
        st.error("PIN errato. Riprova.")

# --- TAB 2: AREA ADMIN (PROTETTA DA PIN MASTER) ---
with tab2:
    admin_pin_inserito = st.text_input("Inserisci PIN Amministratore per accedere", type="password")
    
    if admin_pin_inserito == PIN_ADMIN:
        st.header("Area Amministratore (Sbloccata)")
        
        try:
            df_indisp = conn.read(worksheet="indisponibilita")
            st.write(f"Dati raccolti: {len(df_indisp)} impegni segnati dallo staff.")
            # L'admin può vedere tutto
            st.dataframe(df_indisp, use_container_width=True)
        except:
            df_indisp = pd.DataFrame(columns=["Nome", "Data", "Turno"])
            st.write("Database attualmente vuoto.")

        if st.button("🚀 GENERA TURNI DEL MESE"):
            results = []
            carico_lavoro = {name: 0 for name in STAFF_NAMES}
            month_days = [d for d in get_calendar_days(mese, anno) if d.month == mese] # Usa mese corrente dal tab1

            for d in month_days:
                date_str = d.strftime("%d/%m")
                day_key = d.strftime("%a")
                config = REQUISITI_SETTIMANA.get(day_key, {})

                for fascia, (n_tot, n_exp) in config.items():
                    occupati = df_indisp[(df_indisp['Data'] == date_str) & (df_indisp['Turno'] == fascia)]['Nome'].tolist() if not df_indisp.empty else []
                    disponibili = [n for n in STAFF_NAMES if n not in occupati]
                    
                    esperti_disp = [n for n in disponibili if STAFF_INFO[n]['exp']]
                    esperti_disp.sort(key=lambda x: carico_lavoro[x]) 
                    
                    scelti = esperti_disp[:n_exp]
                    
                    restanti_disp = [n for n in disponibili if n not in scelti]
                    restanti_disp.sort(key=lambda x: carico_lavoro[x])
                    
                    mancanti = n_tot - len(scelti)
                    scelti.extend(restanti_disp[:mancanti])
                    
                    for s in scelti: carico_lavoro[s] += 1
                    results.append({"Data": date_str, "Turno": fascia, "Staff": ", ".join(scelti)})
            
            st.subheader("Tabellone Generato")
            st.table(pd.DataFrame(results))
            st.write("Totale turni assegnati per persona:", carico_lavoro)

        st.divider()
        if st.button("🗑️ RESET DATABASE (NUOVO MESE)"):
            conn.update(worksheet="indisponibilita", data=pd.DataFrame(columns=["Nome", "Data", "Turno"]))
            st.warning("Database pulito. I colleghi possono inserire i dati per il nuovo mese.")
            
    elif admin_pin_inserito != "":
        st.error("Accesso negato.")
