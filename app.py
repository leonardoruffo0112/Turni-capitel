import streamlit as st
import pandas as pd
import random
from datetime import datetime, timedelta

# --- IMPORTAZIONE UFFICIALE ---
try:
    from streamlit_gsheets import GSheetsConnection
except ImportError:
    st.error("⚠️ Problema di libreria. Fai Reboot dell'app.")
    st.stop()

st.set_page_config(page_title="Turni Capitel", layout="wide")

# --- DATABASE PIN E STAFF ---
PIN_STAFF = {
    'L': '1111', 'N': '2222', 'J': '3333', 'A': '4444', 
    'B': '5555', 'C': '6666', 'D': '7777', 'M': '8888', 
    'P': '9999', 'T': '1234', 'Z': '4321'
}
PIN_ADMIN = "0000" 

# Nuova classificazione: exp (esperti) e bar (baristi)
STAFF_INFO = {
    'L': {'exp': True, 'bar': True}, 
    'N': {'exp': True, 'bar': False}, 
    'J': {'exp': True, 'bar': True},
    'A': {'exp': False, 'bar': True}, 
    'B': {'exp': False, 'bar': False}, 
    'C': {'exp': False, 'bar': False},
    'D': {'exp': False, 'bar': False}, 
    'M': {'exp': False, 'bar': False}, 
    'P': {'exp': False, 'bar': False},
    'T': {'exp': False, 'bar': False}, 
    'Z': {'exp': False, 'bar': True}
}
STAFF_NAMES = list(STAFF_INFO.keys())

# Formato: (Numero Totale, Numero Esperti, Numero Baristi)
REQUISITI_SETTIMANA = {
    'Mon': {'C': (3, 1, 1)}, 
    'Tue': {'C': (2, 1, 1)}, 
    'Wed': {'C': (3, 1, 0)}, 
    'Thu': {'C': (4, 1, 1)}, 
    'Fri': {'C': (4, 2, 0)}, # 0 Baristi di Venerdì come da tua richiesta
    'Sat': {'P': (3, 2, 0), 'C': (6, 2, 1)},
    'Sun': {'P': (5, 2, 0), 'C': (4, 1, 1)}
}

# Formato Eccezioni: (Totale, Esperti, Baristi)
ECCEZIONI_GIORNI = {
    '06/04': {'P': (4, 1, 0), 'C': (4, 1, 1)} 
}

GIORNI_IT = {0: 'L', 1: 'M', 2: 'M', 3: 'G', 4: 'V', 5: 'S', 6: 'D'}

conn = st.connection("gsheets", type=GSheetsConnection)

def get_calendar_days(month, year):
    first_day = datetime(year, month, 1)
    start_date = first_day - timedelta(days=first_day.weekday())
    return [start_date + timedelta(days=i) for i in range(35)]

def highlight_dom(row):
    if 'Giorno' in row and str(row['Giorno']).startswith('D'):
        return ['background-color: #4a1515; font-weight: bold'] * len(row)
    return [''] * len(row)

st.title("🗓️ Gestione Turni Capitel")

tab1, tab2 = st.tabs(["❌ Segna i tuoi impegni", "⚙️ Admin & Generatore"])

# --- TAB 1: AREA RAGAZZI ---
with tab1:
    col1, col2 = st.columns(2)
    user = col1.selectbox("Seleziona il tuo nome", STAFF_NAMES)
    pin_inserito = col2.text_input("Inserisci il tuo PIN", type="password")
    
    if pin_inserito == PIN_STAFF[user]:
        mese, anno = 4, 2026
        st.success(f"Accesso consentito. Ciao {user}!")
        
        miei_turni_salvati = set()
        try:
            df_tutti = conn.read(worksheet="indisponibilita", ttl=0)
            df_miei = df_tutti[df_tutti['Nome'] == user]
            
            for _, row in df_miei.iterrows():
                data_pulita = str(row['Data']).strip()
                turno_pulito = str(row['Turno']).strip()
                miei_turni_salvati.add(f"{data_pulita}-{turno_pulito}")
                
            if not df_miei.empty:
                st.info("Abbiamo caricato le tue indisponibilità precedenti. Puoi modificarle togliendo o mettendo le spunte.")
        except Exception as e:
            pass 

        st.subheader(f"I tuoi impegni per Aprile")

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
                        
                        if date_str in ECCEZIONI_GIORNI:
                            config_giorno = ECCEZIONI_GIORNI[date_str]
                            st.write(f"**{date_str}** ⚠️") 
                        else:
                            config_giorno = REQUISITI_SETTIMANA[day_key]
                            st.write(f"**{date_str}**")
                            
                        for t in list(config_giorno.keys()):
                            id_turno_corrente = f"{date_str}-{t}"
                            gia_selezionato = id_turno_corrente in miei_turni_salvati
                            
                            if st.checkbox(f"{t}", value=gia_selezionato, key=f"{user}_{day.day}_{t}"):
                                current_user_nos.append({"Nome": user, "Data": date_str, "Turno": t})
                    else: st.write("")

        if st.button("CONFERMA MODIFICHE E SALVA", type="primary"):
            try:
                try:
                    df_old = conn.read(worksheet="indisponibilita", ttl=0)
                    df_old = df_old[df_old['Nome'] != user] 
                except:
                    df_old = pd.DataFrame(columns=["Nome", "Data", "Turno"])
                
                new_rows = pd.DataFrame(current_user_nos)
                updated_df = pd.concat([df_old, new_rows], ignore_index=True)
                conn.update(worksheet="indisponibilita", data=updated_df)
                
                st.cache_data.clear() 
                st.success("Tutto aggiornato correttamente nel database!")
            except Exception as e:
                st.error(f"Errore durante il salvataggio: {e}")
                
    elif pin_inserito != "":
        st.error("PIN errato. Riprova.")

# --- TAB 2: AREA ADMIN ---
with tab2:
    admin_pin_inserito = st.text_input("Inserisci PIN Amministratore per accedere", type="password")
    
    if admin_pin_inserito == PIN_ADMIN:
        st.header("Area Amministratore (Sbloccata)")
        
        mese, anno = 4, 2026
        month_days = [d for d in get_calendar_days(mese, anno) if d.month == mese]
        
        try:
            df_indisp = conn.read(worksheet="indisponibilita", ttl=0)
        except:
            df_indisp = pd.DataFrame(columns=["Nome", "Data", "Turno"])
            
        try:
            df_tabellone = conn.read(worksheet="Tabellone", ttl=0)
        except:
            df_tabellone = pd.DataFrame()

        with st.expander("Vedi Dettaglio Disponibilità Staff", expanded=False):
            dati_disponibili = []
            conteggio_disp = {n: 0 for n in STAFF_NAMES}
            
            for d in month_days:
                date_str = d.strftime("%d/%m")
                day_key = d.strftime("%a")
                
                if date_str in ECCEZIONI_GIORNI:
                    config = ECCEZIONI_GIORNI[date_str]
                else:
                    config = REQUISITI_SETTIMANA.get(day_key, {})
                
                for fascia in config.keys():
                    if not df_indisp.empty:
                        occupati = df_indisp[(df_indisp['Data'] == date_str) & (df_indisp['Turno'] == fascia)]['Nome'].tolist()
                    else:
                        occupati = []
                        
                    disponibili = [n for n in STAFF_NAMES if n not in occupati]
                    for n in disponibili:
                        conteggio_disp[n] += 1
                        
                    dati_disponibili.append({"Data": date_str, "Turno": fascia, "Staff Disponibile": ", ".join(disponibili)})
                    
            df_disp = pd.DataFrame(dati_disponibili)
            df_conteggio_disp = pd.DataFrame(list(conteggio_disp.items()), columns=['Lettera', 'Turni Liberi']).sort_values(by='Turni Liberi', ascending=False)
            
            col_tab_disp, col_count_disp = st.columns([3, 1])
            with col_tab_disp:
                st.dataframe(df_disp, use_container_width=True, height=250)
            with col_count_disp:
                st.dataframe(df_conteggio_disp, use_container_width=True, hide_index=True)

        st.divider()

        st.subheader("Tabellone Attuale e Riepilogo Assegnazioni")
        
        if not df_tabellone.empty and "Giorno" in df_tabellone.columns:
            conteggio_assegnati = {n: 0 for n in STAFF_NAMES}
            for _, row in df_tabellone.iterrows():
                for col in ["CENA", "PRANZO"]:
                    valore_cella = str(row[col]) if pd.notna(row[col]) else ""
                    for lettera in valore_cella:
                        if lettera in conteggio_assegnati:
                            conteggio_assegnati[lettera] += 1
                            
            df_assegnati = pd.DataFrame(list(conteggio_assegnati.items()), columns=['Lettera', 'Assegnati']).sort_values(by='Assegnati', ascending=False)
            
            col_tab_perm, col_riep_perm = st.columns([3, 1])
            with col_tab_perm:
                st.dataframe(df_tabellone.style.apply(highlight_dom, axis=1), use_container_width=True, hide_index=True)
            with col_riep_perm:
                st.write("Turni Effettivi")
                st.dataframe(df_assegnati, use_container_width=True, hide_index=True)
        else:
            st.info("Nessun tabellone generato. Premi il tasto qui sotto per crearne uno nuovo.")

        if st.button("🚀 RIGENERA E SALVA TURNI DEL MESE", type="primary"):
            carico_lavoro = {name: 0 for name in STAFF_NAMES}
            tabellone_mese = {}
            for d in month_days:
                iniziale_giorno = GIORNI_IT[d.weekday()]
                etichetta_giorno = f"{iniziale_giorno} {d.day}"
                tabellone_mese[d.day] = {"Giorno": etichetta_giorno, "CENA": "", "PRANZO": ""}

            for d in month_days:
                date_str = d.strftime("%d/%m")
                day_key = d.strftime("%a")
                
                if date_str in ECCEZIONI_GIORNI:
                    config = ECCEZIONI_GIORNI[date_str]
                else:
                    config = REQUISITI_SETTIMANA.get(day_key, {})

                for fascia, (n_tot, n_exp, n_bar) in config.items():
                    occupati = df_indisp[(df_indisp['Data'] == date_str) & (df_indisp['Turno'] == fascia)]['Nome'].tolist() if not df_indisp.empty else []
                    disponibili = [n for n in STAFF_NAMES if n not in occupati]
                    scelti = []
                    
                    # 1. Scelta Esperti
                    esperti_disp = [n for n in disponibili if STAFF_INFO[n]['exp']]
                    random.shuffle(esperti_disp)
                    esperti_disp.sort(key=lambda x: carico_lavoro[x]) 
                    scelti_exp = esperti_disp[:n_exp]
                    scelti.extend(scelti_exp)
                    
                    # 2. Scelta Baristi (verificando quanti baristi sono già stati scelti tra gli esperti)
                    bar_attuali = sum(1 for x in scelti if STAFF_INFO[x]['bar'])
                    bar_mancanti = max(0, n_bar - bar_attuali)
                    
                    bar_disp = [n for n in disponibili if n not in scelti and STAFF_INFO[n]['bar']]
                    random.shuffle(bar_disp)
                    bar_disp.sort(key=lambda x: carico_lavoro[x])
                    scelti_bar = bar_disp[:bar_mancanti]
                    scelti.extend(scelti_bar)
                    
                    # 3. Riempimento turni rimanenti e blocco T/B
                    mancanti = n_tot - len(scelti)
                    restanti_disp = [n for n in disponibili if n not in scelti]
                    random.shuffle(restanti_disp)
                    restanti_disp.sort(key=lambda x: carico_lavoro[x])
                    
                    for r in restanti_disp:
                        if mancanti <= 0:
                            break
                            
                        # BLOCCO T e B: Se c'è uno, l'altro salta il turno
                        if r == 'T' and 'B' in scelti:
                            continue
                        if r == 'B' and 'T' in scelti:
                            continue
                            
                        scelti.append(r)
                        mancanti -= 1
                    
                    for s in scelti: carico_lavoro[s] += 1
                    
                    colonna_destinazione = "CENA" if fascia == 'C' else "PRANZO"
                    tabellone_mese[d.day][colonna_destinazione] = "".join(scelti)
            
            df_risultato_finale = pd.DataFrame(list(tabellone_mese.values()))
            
            try:
                conn.update(worksheet="Tabellone", data=df_risultato_finale)
                st.cache_data.clear()
                st.rerun() 
            except Exception as e:
                st.error(f"❌ Errore di esportazione: {e}")

        st.divider()
        if st.button("🗑️ RESET DATABASE (NUOVO MESE)"):
            conn.update(worksheet="indisponibilita", data=pd.DataFrame(columns=["Nome", "Data", "Turno"]))
            conn.update(worksheet="Tabellone", data=pd.DataFrame(columns=["Giorno", "CENA", "PRANZO"]))
            st.cache_data.clear()
            st.rerun()
            
    elif admin_pin_inserito != "":
        st.error("Accesso negato.")
