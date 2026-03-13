import streamlit as st
import pandas as pd
import random
from datetime import datetime, timedelta

# --- CONFIGURAZIONE BASE ---
st.set_page_config(page_title="Gestore Turni Ristorante", layout="wide")

STAFF = {
    'L': {'expert': True, 'max': 16},
    'N': {'expert': True, 'max': 16},
    'J': {'expert': True, 'max': 20}, # J ha il bonus
    'A': {'expert': False, 'max': 16},
    'B': {'expert': False, 'max': 16},
    'C': {'expert': False, 'max': 16},
    'D': {'expert': False, 'max': 16},
    'M': {'expert': False, 'max': 16},
    'P': {'expert': False, 'max': 16},
    'T': {'expert': False, 'max': 16},
    'Z': {'expert': False, 'max': 16}
}

REQUISITI = {
    'Lun': {'P': 0, 'C': 3, 'exp_C': 0},
    'Mar': {'P': 0, 'C': 2, 'exp_C': 0},
    'Mer': {'P': 0, 'C': 3, 'exp_C': 0},
    'Gio': {'P': 0, 'C': 4, 'exp_C': 0},
    'Ven': {'P': 0, 'C': 4, 'exp_C': 0},
    'Sab': {'P': 3, 'C': 6, 'exp_P': 0, 'exp_C': 2}, # Sabato sera: 2 esperti
    'Dom': {'P': 5, 'C': 4, 'exp_P': 2, 'exp_C': 0}  # Domenica pranzo: 2 esperti
}

def get_days_in_month(month, year):
    d = datetime(year, month, 1)
    days = []
    while d.month == month:
        days.append(d)
        d += timedelta(days=1)
    return days

# --- INTERFACCIA ---
st.title("🗓️ Generatore Turni Intelligente")

tab1, tab2 = st.tabs(["❌ Inserisci Indisponibilità", "⚙️ Genera Turni"])

with tab1:
    st.header("Segna quando NON puoi lavorare")
    col1, col2 = st.columns(2)
    user = col1.selectbox("Chi sei?", list(STAFF.keys()))
    mese_scelto = col2.selectbox("Mese", [4, 5], format_func=lambda x: "Aprile" if x==4 else "Maggio")
    
    st.info("Seleziona i giorni in cui sei impegnato. Questa versione è dimostrativa: in quella finale i dati verranno salvati su un database.")
    # Per ora usiamo la session_state per simulare il salvataggio
    if 'indisp' not in st.session_state:
        st.session_state.indisp = {name: [] for name in STAFF}
    
    days = get_days_in_month(mese_scelto, 2026)
    selected_days = st.multiselect("Giorni NO", [d.strftime("%d/%m (%a)") for d in days])
    
    if st.button("Salva le mie disponibilità"):
        st.session_state.indisp[user] = selected_days
        st.success(f"Disponibilità salvate per {user}!")

with tab2:
    st.header("Area Amministratore")
    if st.button("CALCOLA TURNI OTTIMIZZATI"):
        # Logica di calcolo
        all_days = get_days_in_month(mese_scelto, 2026)
        calendario = []
        carico_lavoro = {name: 0 for name in STAFF}
        esperti = [n for n, v in STAFF.items() if v['expert']]
        base = [n for n, v in STAFF.items() if not v['expert']]
        
        for d in all_days:
            giorno_sett = d.strftime("%a")[:3]
            # Traduzione rapida per i requisiti
            mapping = {"Mon":"Lun", "Tue":"Mar", "Wed":"Mer", "Thu":"Gio", "Fri":"Ven", "Sat":"Sab", "Sun":"Dom"}
            key = mapping[giorno_sett]
            req = REQUISITI[key]
            
            for fascia in ['P', 'C']:
                n_serve = req[fascia]
                if n_serve == 0: continue
                
                exp_serve = req.get(f'exp_{fascia}', 0)
                
                # Chi è disponibile? (non ha segnato NO)
                string_giorno = d.strftime("%d/%m (%a)")
                disponibili = [n for n in STAFF if string_giorno not in st.session_state.indisp[n]]
                
                # Selezione
                scelti = []
                
                # 1. Esperti necessari
                disp_exp = [n for n in disponibili if n in esperti]
                # Ordina per chi ha lavorato meno
                disp_exp.sort(key=lambda x: carico_lavoro[x])
                scelti_exp = disp_exp[:exp_serve]
                scelti.extend(scelti_exp)
                
                # 2. Resto dello staff
                restanti_disp = [n for n in disponibili if n not in scelti]
                # Ordina per carico lavoro
                restanti_disp.sort(key=lambda x: carico_lavoro[x])
                scelti_altri = restanti_disp[:(n_serve - len(scelti))]
                scelti.extend(scelti_altri)
                
                for s in scelti: carico_lavoro[s] += 1
                
                calendario.append({
                    "Giorno": string_giorno,
                    "Fascia": "Pranzo" if fascia == 'P' else "Cena",
                    "Staff": ", ".join(scelti)
                })
        
        st.table(pd.DataFrame(calendario))
        st.subheader("Riepilogo Carico Turni")
        st.write(carico_lavoro)
