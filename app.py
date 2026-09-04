import streamlit as st
import pandas as pd
from datetime import datetime, timedelta
import os
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from email.mime.base import MIMEBase
from email import encoders

# --- CONFIGURATION INITIALE & DESIGN GÉNÉRAL TRICOLORE ---
st.set_page_config(page_title="QA/QC - Station de San Pedro", layout="wide", initial_sidebar_state="expanded")

st.markdown("""
    <style>
    /* 1. FOND VERT NATIONAL SUR LES ÉLÉMENTS EXTÉRIEURS */
    .stApp { 
        background-color: #134e4a !important; 
        color: #1f2937 !important; 
        z-index: 1 !important;
    }
    
    /* GRANDE ZONE CENTRALE EN ORANGE CLAIR */
    [data-testid="stHeader"], [data-testid="stAppViewBlockContainer"] {
        background-color: #fff7ed !important; 
    }
    .main .block-container {
        background-color: #fff7ed !important;
        padding-top: 20px !important;
        padding-bottom: 40px !important;
    }
    
    /* 2. STYLE DES EN-TÊTES ET ONGLETS SUPERIEURS */
    div[data-testid="stTabs"] button {
        color: #ffffff !important;
        background-color: #115e59 !important;
        border-radius: 8px 8px 0 0 !important;
        margin-right: 4px !important;
        padding: 10px 20px !important;
        font-family: 'Cambria', serif !important;
        font-weight: bold !important;
    }
    div[data-testid="stTabs"] button[aria-selected="true"] {
        background-color: #f97316 !important; /* Onglet actif en Orange */
        color: #ffffff !important;
    }
    
    /* 3. BLOCS FORMULAIRES BLANCS COMPACTS (Comme le modèle) */
    .form-container-custom {
        background-color: #ffffff !important;
        padding: 25px !important;
        border-radius: 12px !important;
        box-shadow: 0 4px 6px -1px rgba(0,0,0,0.1) !important;
        border: 2px solid #ffedd5 !important;
        margin-bottom: 20px !important;
    }
    
    /* Écritures textuelles au centre (Police Cambria en Noir Foncé) */
    div[data-testid="stMarkdownContainer"] p, label p, .stSubheader p {
        color: #111827 !important; 
        font-family: 'Cambria', serif !important;
        font-weight: bold !important;
        font-size: 14px !important;
    }
    h1, h2, h3, h4, h5, h6 { color: #111827 !important; font-family: 'Cambria', serif !important; font-weight: bold !important; }
    
    /* Champs de saisie */
    div[data-testid="stSelectbox"] div[data-baseline="true"], div[data-testid="stTextInput"] input, div[data-testid="stTextArea"] textarea {
        color: #111827 !important; background-color: #f3f4f6 !important; border: 2px solid #cbd5e1 !important;
    }
    
    /* 4. BLOCS STATISTIQUES EN BOÎTES (KPI) */
    .kpi-box {
        background-color: #ffffff; padding: 20px; border-radius: 10px;
        box-shadow: 0 4px 6px rgba(0,0,0,0.05); text-align: center; border: 1px solid #e5e7eb; border-top: 4px solid #f97316;
    }
    .kpi-title { color: #6b7280; font-size: 13px; text-transform: uppercase; font-weight: bold; }
    .kpi-value { color: #111827; font-size: 32px; font-weight: bold; margin-top: 5px; }
    
    /* 5. DESIGN DE LA BARRE LATÉRALE */
    [data-testid="stSidebar"] { background-color: #134e4a !important; border-right: 4px solid #f97316 !important; }
    [data-testid="stSidebar"] .stRadio div[role="radiogroup"] label p {
        font-family: 'Cambria', serif !important; font-size: 14px !important; font-weight: bold !important; color: #ffffff !important; 
    }
    [data-testid="stSidebar"] h2, [data-testid="stSidebar"] p { color: #ffffff !important; }
    
    /* 6. STYLE BADGES DE STATUT TABLEAU (Vert et Rouge) */
    .badge-delai { background-color: #dcfce7 !important; color: #15803d !important; padding: 4px 10px !important; border-radius: 20px !important; font-weight: bold !important; font-size: 12px !important; display: inline-block !important; }
    .badge-retard { background-color: #fee2e2 !important; color: #b91c1c !important; padding: 4px 10px !important; border-radius: 20px !important; font-weight: bold !important; font-size: 12px !important; display: inline-block !important; }
    
    .podium-box { background-color: #f0fdf4; border: 1px solid #bbf7d0; padding: 10px; border-radius: 8px; margin-bottom: 8px; }
    </style>
""", unsafe_allow_html=True)

MOT_DE_PASSE_REQUIS = "sanpedro2026"
FICHIER_BDD = "donnees_meteo_sanpedro.csv"
FICHIER_AGENTS = "presence_agents_sanpedro.csv"
FICHIER_OBS = "observations_qualite_sanpedro.csv"

# --- TRANSMISSION OUTLOOK ---
SMTP_SERVEUR = "://office365.com"  
SMTP_PORT = 587
COMPTE_MAIL_STATION = "meteo.sanpedro@sodexam.ci" 
COMPTE_MOT_DE_PASSE = "VotreMotDePasseOutlookIci"  

def transmettre_message_outlook(sujet, corps, destinataires, fichier_joint=None):
    tous_les_destinataires = list(set(destinataires + ["meteo.sanpedro@sodexam.ci"]))
    msg = MIMEMultipart()
    msg['From'] = COMPTE_MAIL_STATION
    msg['To'] = ", ".join(tous_les_destinataires)
    msg['Subject'] = sujet
    msg.attach(MIMEText(corps, 'plain'))
    if fichier_joint is not None:
        try:
            part = MIMEBase('application', "octet-stream")
            part.set_payload(fichier_joint.read())
            encoders.encode_base64(part)
            part.add_header('Content-Disposition', f'attachment; filename="{fichier_joint.name}"')
            msg.attach(part)
            fichier_joint.seek(0)
        except: pass
    try:
        serveur = smtplib.SMTP(SMTP_SERVEUR, SMTP_PORT, timeout=5)
        serveur.starttls()
        serveur.login(COMPTE_MAIL_STATION, COMPTE_MOT_DE_PASSE)
        serveur.sendmail(COMPTE_MAIL_STATION, tous_les_destinataires, msg.as_string())
        serveur.quit()
        return True
    except: return False

# --- ARCHIVES CONFIGURATION ---
colonnes_principales = ["Date_Saisie", "Heure_Saisie", "Date_Donnees", "Mois", "Annee", "Agent", "Categorie", "Type_Message_Fichier", "Heure_Transmission", "Statut_Delai", "Details"]
if not os.path.exists(FICHIER_BDD): pd.DataFrame(columns=colonnes_principales).to_csv(FICHIER_BDD, index=False)
if not os.path.exists(FICHIER_AGENTS): pd.DataFrame(columns=["Date", "Agent", "Action", "Heure"]).to_csv(FICHIER_AGENTS, index=False)
if not os.path.exists(FICHIER_OBS): pd.DataFrame(columns=["Date", "Heure", "Agent", "Type_Observation", "Message_Concerne", "Raison_Retard_Ou_Qualite"]).to_csv(FICHIER_OBS, index=False)

def verifier_si_agent_descendu(agent, date_du_jour):
    df_p = pd.read_csv(FICHIER_AGENTS)
    if not df_p.empty:
        descente = df_p[(df_p["Date"] == date_du_jour) & (df_p["Agent"] == agent) & (df_p["Action"] == "Fin de service (Descente)")]
        if not descente.empty: return True
    return False

def verifier_doublon_message(type_msg, date_data, heure_str):
    df_b = pd.read_csv(FICHIER_BDD)
    if not df_b.empty:
        doublon = df_b[(df_b["Type_Message_Fichier"] == type_msg) & (df_b["Date_Donnees"] == date_data) & (df_b["Heure_Transmission"] == heure_str)]
        if not doublon.empty: return True
    return False

# --- SYSTEME BIP ET RAPPEL ---
maintenant = datetime.now()
minute_actuelle = maintenant.minute
if 50 <= minute_actuelle <= 59 or minute_actuelle == 0:
    st.warning(f"⚠️ RAPPEL DE SERVICE : Il est {maintenant.strftime('%H:%M')}. Fenêtre de saisie météo active !")
    st.markdown("""<audio autoplay><source src="https://mixkit.co" type="audio/mpeg"></audio>""", unsafe_allow_html=True)

# --- SECURITE MOT DE PASSE ---
if "authentifie" not in st.session_state: st.session_state["authentifie"] = False

if not st.session_state["authentifie"]:
    col_gauche, col_centre, col_droite = st.columns(3)
    with col_centre:
        st.markdown("<br><br>", unsafe_allow_html=True)
        st.markdown("<h1 style='text-align: center; color: #f97316;'>🏢 SODEXAM</h1>", unsafe_allow_html=True)
        st.markdown("<h3 style='text-align: center; color: #16a34a;'>Station de San Pedro</h3>", unsafe_allow_html=True)
        st.markdown("---")
        mdp_saisi = st.text_input("🔑 Entrez le code d'accès de la station :", type="password")
        if st.button("Se connecter à l'application", use_container_width=True):
            if mdp_saisi == MOT_DE_PASSE_REQUIS:
                st.session_state["authentifie"] = True
                st.rerun()
            else: st.error("❌ Mot de passe incorrect")
else:
    # --- MENUS LATÉRAUX ---
    st.sidebar.markdown("<h2 style='color:#f97316; margin-bottom:0;'>🏢 SODEXAM</h2><p style='color:#16a34a; font-weight:bold; margin-top:0;'>Station de San Pedro</p>", unsafe_allow_html=True)
    liste_agents = ["Dalo Clement", "Dao lea", "Adoh Bouet", "Koffi Gisele", "Djagba Aka", "Ote Armande"]
    agent_actif = st.sidebar.selectbox("👨‍💼 Agent de service :", liste_agents)
    
    st.sidebar.markdown("---")
    st.sidebar.markdown("<p style='font-weight:bold; color:#f97316; font-size:13px;'>🗂️ MENUS DE LA STATION</p>", unsafe_allow_html=True)
    choix_menu = st.sidebar.radio(
        "Sélectionnez votre tâche :",
        [
            "⏰ Prise & Fin de Service",
            "📡 Saisie des Messages Réguliers", 
            "🌡️ Données Extrêmes", 
            "🛠️ Point Instrument & Correction",
            "🌱 AGROMET & CLIMAT", 
            "📂 Tableau Climatologique (TCM)",
            "📝 Qualité & Justifications Hors Délai",
            "📈 Tableau de bord & Décomptes"
        ]
    )

    date_saisie = maintenant.strftime("%Y-%m-%d")
    heure_informatique = maintenant.strftime("%H:%M")
    agent_bloque = verifier_si_agent_descendu(agent_actif, date_saisie)

    # --- SOUS-MENU : PRISE & FIN DE SERVICE ---
    if choix_menu == "⏰ Prise & Fin de Service":
        st.subheader("⏰ Registre de Présence (Montée / Descente)")
        with st.form("form_presence"):
            action = st.radio("Action :", ["Prise de service (Montée)", "Fin de service (Descente)"])
            heure_action = st.time_input("Heure officielle :", maintenant.time())
            if st.form_submit_button("💾 Valider l'Heure"):
                df_p = pd.read_csv(FICHIER_AGENTS)
                deja_signe = df_p[(df_p["Date"] == date_saisie) & (df_p["Agent"] == agent_actif) & (df_p["Action"] == action)]
                if not deja_signe.empty: st.error(f"❌ Action refusée : Déjà enregistré aujourd'hui.")
                else:
                    nouvelle_p = {"Date": date_saisie, "Agent": agent_actif, "Action": action, "Heure": heure_action.strftime("%H:%M")}
                    pd.concat([df_p, pd.DataFrame([nouvelle_p])], ignore_index=True).to_csv(FICHIER_AGENTS, index=False)
                    st.success(f"✅ Présence enregistrée.")
        df_p_l = pd.read_csv(FICHIER_AGENTS)
        st.dataframe(df_p_l[df_p_l["Date"] == date_saisie], use_container_width=True)

    # --- SOUS-MENU : SAISIE DES MESSAGES RÉGULIERS ---
    elif choix_menu == "📡 Saisie des Messages Réguliers":

            col1, col2, col3, col4 = st.columns(4)
            with col1: n_agent_s = st.selectbox("Agent", [agent_actif])
            with col2: type_msg = st.selectbox("Type de message", ["SYNOP Horaire", "SYNOP Principal", "METAR", "METREPORT", "SPECI"])
            with col3:
                heures_obs = [f"{h:02d}:00" for h in range(24)]
                heure_nom_str = st.selectbox("Heure du message (H UTC)", heures_obs, index=maintenant.hour)
            with col4: heure_tr_txt = st.text_input("Heure réelle transmission (HH:MM)", value=maintenant.strftime("%H:%M"))
            
            corps_msg = st.text_area("Texte réglementaire du message :", height=120)
            
            if st.button("Transmettre le Message", use_container_width=True):
                heure_def_str = heure_tr_txt.strip()
                try: 
                    datetime.strptime(heure_def_str, "%H:%M")
                except: 
                    st.error("❌ Format d'heure invalide (HH:MM)"); st.stop()
                
                if type_msg != "SPECI" and verifier_doublon_message(type_msg, date_saisie, heure_def_str):
                    st.error("❌ Un message identique existe déjà.")
                else:
                    h_nom_dt = datetime.strptime(f"{date_saisie} {heure_nom_str}", "%Y-%m-%d %H:%M")
                    h_tr_dt = datetime.strptime(f"{date_saisie} {heure_def_str}", "%Y-%m-%d %H:%M")
                    statut = "Transmis dans le délai" if (h_nom_dt - timedelta(minutes=10)) <= h_tr_dt <= (h_nom_dt + timedelta(minutes=5)) else "Transmis hors délai"
                    
                    df = pd.read_csv(FICHIER_BDD)
                    nouvelle_ligne = {
                        "Date_Saisie": date_saisie, "Heure_Saisie": heure_informatique, "Date_Donnees": date_saisie,
                        "Mois": maintenant.strftime("%B"), "Annee": maintenant.strftime("%Y"), "Agent": agent_actif,
                        "Categorie": "SYNOP & METAR", "Type_Message_Fichier": type_msg, "Heure_Transmission": heure_def_str,
                        "Statut_Delai": statut, "Details": f"[Obs: {heure_nom_str}] {corps_msg}"
                    }
                    pd.concat([df, pd.DataFrame([nouvelle_ligne])], ignore_index=True).to_csv(FICHIER_BDD, index=False)
                    st.success(f"💾 Message enregistré avec succès sous le statut : **{statut}**")
                    transmettre_message_outlook(f"[{type_msg}] San Pedro", corps_msg, ["beta@sodexam.ci"])
            st.markdown('</div>', unsafe_allow_html=True)

    # --- SOUS-MENU : DONNÉES EXTRÊMES ---
    elif choix_menu == "🌡️ Données Extrêmes":
        st.subheader("🌡️ Saisie des Données Extrêmes")
        if agent_bloque: 
            st.error("🛑 Action bloquée.")
        else:
            with st.form("form_ex"):
                h_tr = st.text_input("Heure réelle transmission (HH:MM)", value=maintenant.strftime("%H:%M"))
                t_max = st.number_input("T MAX (°C)", value=28.0)
                t_min = st.number_input("T MINI (°C)", value=22.0)
                p_mm = st.number_input("Pluie (mm)", value=0.0)
                if st.form_submit_button("Enregistrer"):
                    dt_d = (maintenant - timedelta(days=1)).strftime("%Y-%m-%d")
                    statut = "Transmis dans le délai" if "06:00" <= h_tr.strip() <= "08:00" else "Transmis hors délai"
                    df = pd.read_csv(FICHIER_BDD)
                    nouvelle_ligne = {
                        "Date_Saisie": date_saisie, "Heure_Saisie": heure_informatique, "Date_Donnees": dt_d,
                        "Mois": maintenant.strftime("%B"), "Annee": maintenant.strftime("%Y"), "Agent": agent_actif,
                        "Categorie": "Données Extrêmes", "Type_Message_Fichier": "DONNEES EXTREMES", "Heure_Transmission": h_tr.strip(),
                        "Statut_Delai": statut, "Details": f"TMAX: {t_max} | TMIN: {t_min} | P: {p_mm}"
                    }
                    pd.concat([df, pd.DataFrame([nouvelle_ligne])], ignore_index=True).to_csv(FICHIER_BDD, index=False)
                    st.success("Données enregistrées.")

    # --- SOUS-MENU : INSTRUMENTS ---
    elif choix_menu == "🛠️ Point Instrument & Correction":
        st.subheader("🛠️ Point Hebdomadaire des Instruments")
        with st.form("form_i"):
            f_word = st.file_uploader("Fichier Word", type=["docx"])
            notes = st.text_area("Notes")
            if st.form_submit_button("Sauvegarder"):
                df = pd.read_csv(FICHIER_BDD)
                nouvelle_ligne = {
                    "Date_Saisie": date_saisie, "Heure_Saisie": heure_informatique, "Date_Donnees": date_saisie,
                    "Mois": maintenant.strftime("%B"), "Annee": maintenant.strftime("%Y"), "Agent": agent_actif,
                    "Categorie": "Instruments", "Type_Message_Fichier": "Rapport WORD", "Heure_Transmission": heure_informatique,
                    "Statut_Delai": "Transmis dans le délai", "Details": notes
                }
                pd.concat([df, pd.DataFrame([nouvelle_ligne])], ignore_index=True).to_csv(FICHIER_BDD, index=False)
                st.success("Rapport archivé.")

    # --- SOUS-MENU : AGROMET & CLIMAT ---
    elif choix_menu == "🌱 AGROMET & CLIMAT":
        st.subheader("🌱 Rapports Décadaires AGROMET & Mensuels CLIMAT")
        with st.form("form_agro"):
            t_rep = st.selectbox("Type", ["AGROMET (Décadaire)", "CLIMAT (Mensuel)"])
            h_tr = st.text_input("Heure transmission", value=maintenant.strftime("%H:%M"))
            c_rep = st.text_area("Contenu")
            if st.form_submit_button("Transmettre"):
                df = pd.read_csv(FICHIER_BDD)
                nouvelle_ligne = {
                    "Date_Saisie": date_saisie, "Heure_Saisie": heure_informatique, "Date_Donnees": date_saisie,
                    "Mois": maintenant.strftime("%B"), "Annee": maintenant.strftime("%Y"), "Agent": agent_actif,
                    "Categorie": "Agromet/Climat", "Type_Message_Fichier": t_rep, "Heure_Transmission": h_tr.strip(),
                    "Statut_Delai": "Transmis dans le délai", "Details": c_rep
                }
                pd.concat([df, pd.DataFrame([nouvelle_ligne])], ignore_index=True).to_csv(FICHIER_BDD, index=False)
                st.success("Rapport validé.")

    # --- SOUS-MENU : TCM ---
    elif choix_menu == "📂 Tableau Climatologique (TCM)":
        st.subheader("📂 Fichier Excel TCM")
        with st.form("form_tcm"):
            f_excel = st.file_uploader("Fichier Excel TCM", type=["xlsx"])
            if st.form_submit_button("Déposer"):
                df = pd.read_csv(FICHIER_BDD)
                nouvelle_ligne = {
                    "Date_Saisie": date_saisie, "Heure_Saisie": heure_informatique, "Date_Donnees": date_saisie,
                    "Mois": maintenant.strftime("%B"), "Annee": maintenant.strftime("%Y"), "Agent": agent_actif,
                    "Categorie": "TCM", "Type_Message_Fichier": "Fichier Excel TCM", "Heure_Transmission": heure_informatique,
                    "Statut_Delai": "Transmis dans le délai", "Details": "Fichier Excel TCM déposé"
                }
                pd.concat([df, pd.DataFrame([nouvelle_ligne])], ignore_index=True).to_csv(FICHIER_BDD, index=False)
                st.success("Excel archivé.")

    # --- SOUS-MENU : OBSERVATIONS ---
    elif choix_menu == "📝 Qualité & Justifications Hors Délai":
        st.subheader("📝 Cahier d'Observations de la Station")
        with st.form("form_obs"):
            t_obs = st.selectbox("Nature", ["Raison de transmission Hors Délai", "Message non transmis (Manquant)", "Note sur la Qualité"])
            msg_c = st.text_input("Message concerné")
            expl = st.text_area("Explications")
            if st.form_submit_button("Enregistrer l'Observation"):
                df_o = pd.read_csv(FICHIER_OBS)
                nouvelle_o = {"Date": date_saisie, "Heure": heure_informatique, "Agent": agent_actif, "Type_Observation": t_obs, "Message_Concerne": msg_c, "Raison_Retard_Ou_Qualite": expl}
                pd.concat([df_o, pd.DataFrame([nouvelle_o])], ignore_index=True).to_csv(FICHIER_OBS, index=False)
                st.success("💾 Observation consignée dans le registre.")

    # --- SOUS-MENU : TABLEAU DE BORD & DÉCOMPTES ---
    elif choix_menu == "📈 Tableau de bord & Décomptes":
        st.subheader("📊 Décompte des Messages Météo & Performance")
        df_stats = pd.read_csv(FICHIER_BDD)
        
        col_f1, col_f2, col_f3 = st.columns(3)
        with col_f1:
            liste_annees = sorted([str(a) for a in df_stats['Annee'].dropna().unique().tolist()]) if not df_stats.empty else [maintenant.strftime("%Y")]
            if maintenant.strftime("%Y") not in liste_annees: 
                liste_annees.append(maintenant.strftime("%Y"))
            annee_sel = st.selectbox("📅 Année", sorted(liste_annees, reverse=True))
            
        with col_f2:
            liste_m = ["Tous", "January", "February", "March", "April", "May", "June", "July", "August", "September", "October", "November", "December"]
            mois_sel = st.selectbox("⏳ Mois", liste_m, index=maintenant.month)
            
        with col_f3:
            agent_filtre = st.selectbox("👨‍💼 Filtrer par agent", ["Tous les agents"] + liste_agents)

        if not df_stats.empty:
            df_temp = df_stats[df_stats["Annee"].astype(str) == str(annee_sel)]
            if mois_sel != "Tous": 
                df_temp = df_temp[df_temp["Mois"] == mois_sel]
            if agent_filtre != "Tous les agents": 
                df_temp = df_temp[df_temp["Agent"] == agent_filtre]
        else:
            df_temp = pd.DataFrame()

        transmis = len(df_temp)
        dans_delai = len(df_temp[df_temp["Statut_Delai"] == "Transmis dans le délai"]) if not df_temp.empty else 0
        hors_delai = len(df_temp[df_temp["Statut_Delai"] == "Transmis hors délai"]) if not df_temp.empty else 0
        taux_ponct = (dans_delai / transmis * 100) if transmis > 0 else 0.0

        k1, k2, k3, k4 = st.columns(4)
        with k1: st.markdown(f'<div class="kpi-box"><div class="kpi-title">MESSAGES TRANSMIS</div><div class="kpi-value">{transmis}</div></div>', unsafe_allow_html=True)
        with k2: st.markdown(f'<div class="kpi-box" style="border-top-color:#16a34a;"><div class="kpi-title">DANS LE DÉLAI</div><div class="kpi-value" style="color:#16a34a;">{dans_delai}</div></div>', unsafe_allow_html=True)
        with k3: st.markdown(f'<div class="kpi-box" style="border-top-color:#ef4444;"><div class="kpi-title">HORS DÉLAI</div><div class="kpi-value" style="color:#ef4444;">{hors_delai}</div></div>', unsafe_allow_html=True)
        with k4: st.markdown(f'<div class="kpi-box" style="border-top-color:#06b6d4;"><div class="kpi-title">TAUX DE PONCTUALITÉ</div><div class="kpi-value" style="color:#06b6d4;">{taux_ponct:.0f}%</div></div>', unsafe_allow_html=True)
        
        
        
        
        tab_decompte, tab_recap, tab_podium = st.tabs(["📝 Décompte Réglementaire par type", "📊 Tableau Récapitulatif", "🏆 Classement des Agents"])
        



        with tab_decompte:
            types_meteo = ["METAR", "METREPORT", "SPECI", "SYNOP Horaire", "SYNOP Principal"]
            quotas_reels = {"METAR": 14, "METREPORT": 14, "SPECI": 0, "SYNOP Horaire": 24, "SYNOP Principal": 8}
            lignes_decompte = []

        for tm in types_meteo:
            if not df_temp.empty:
                df_type = df_temp[df_temp["Type_Message_Fichier"] == tm]
            else:
                df_type = pd.DataFrame()

            cnt_transmis = len(df_type)
            cnt_delai = len(df_type[df_type["Statut_Delai"] == "Transmis dans le délai"]) if not df_type.empty else 0
            cnt_hors = len(df_type[df_type["Statut_Delai"] == "Transmis hors délai"]) if not df_type.empty else 0

            quota_th = quotas_reels[tm]
            cnt_manquant = max(0, quota_th - cnt_transmis) if quota_th > 0 else 0

            pct_delai = f"{cnt_delai} ({(cnt_delai/quota_th*100):.1f}%)" if quota_th > 0 else f"{cnt_delai}"
            pct_hors = f"{cnt_hors} ({(cnt_hors/quota_th*100):.1f}%)" if quota_th > 0 else f"{cnt_hors}"
            pct_manq = f"{cnt_manquant} ({(cnt_manquant/quota_th*100):.1f}%)" if quota_th > 0 else "0"

            lignes_decompte.append({
                "Type de message": tm, "Attendus": quota_th,
                "Dans le délai": pct_delai, "Hors délai": pct_hors, "Non transmis": pct_manq
            })

                # Génération du tableau au format HTML pour forcer la couleur jaune
                # Affichage du tableau natif avec style jaune or forcé
        df_affichage = pd.DataFrame(lignes_decompte)
        st.dataframe(
            df_affichage.style.map(lambda x: 'color: #FFD700; font-weight: bold;'),
            use_container_width=True,
            hide_index=True
        )


        st.markdown("### 📊 Ventilation Visuelle")
        
        c_g1, c_g2 = st.columns(2)
        if not df_temp.empty:
            with c_g1: 
                st.bar_chart(df_temp['Type_Message_Fichier'].value_counts())
            with c_g2: 
                st.bar_chart(df_temp['Statut_Delai'].value_counts())



        with tab_recap:
            st.markdown("#### Tableau récapitulatif complet de la station")
            if not df_temp.empty:
                df_temp['ID'] = df_temp.index
                st.dataframe(df_temp[["ID", "Date_Saisie", "Agent", "Type_Message_Fichier", "Heure_Transmission", "Statut_Delai"]])

                col_e1, col_e2 = st.columns(2)
                with col_e1:
                    st.markdown("##### 📝 Corriger une ligne")
                    id_m = st.number_input("ID message :", min_value=0, max_value=10000, step=1)
                    if id_m in df_stats.index:
                        with st.form("f_ed"):
                            n_h = st.text_input("Heure transmission", value=str(df_stats.at[id_m, 'Heure_Transmission']))
                            n_s = st.selectbox("Statut", ["Transmis dans le délai", "Transmis hors délai"])
                            if st.form_submit_button("Sauvegarder"):
                                df_stats.at[id_m, 'Heure_Transmission'] = n_h
                                df_stats.at[id_m, 'Statut_Delai'] = n_s
                                st.success("Ligne modifiée !")
                                st.rerun()
                with col_e2:
                    st.markdown("##### 🗑️ Supprimer une ligne")
                    id_s = st.number_input("ID à supprimer :", min_value=0, max_value=10000, step=1)
                    if st.button("Confirmer l'effacement", use_container_width=True):
                        if id_s in df_stats.index:
                            df_stats.drop(index=id_s).to_csv(FICHIER_BDD, index=False)
                            st.success("Ligne retirée !")
                            st.rerun()
            else:
                st.info("Aucun message enregistré pour cette période.")

        with tab_podium:
            st.markdown(f"### 🏆 Performances et Classement des Agents ({mois_sel} {annee_sel})")
            if not df_temp.empty:
                stats_ag = []
                for ag in df_temp["Agent"].unique():
                    df_ag = df_temp[df_temp["Agent"] == ag]
                    t_ag = len(df_ag)
                    d_ag = len(df_ag[df_ag["Statut_Delai"] == "Transmis dans le délai"])
                    tx = (d_ag / t_ag * 100) if t_ag > 0 else 0
                    stats_ag.append({"Agent": ag, "Messages Transmis": t_ag, "Dans les délais": d_ag, "Taux de réussite (%)": tx})
                
                df_cl = pd.DataFrame(stats_ag).sort_values(by="Taux de réussite (%)", ascending=False).reset_index(drop=True)
                df_cl.index += 1
                st.dataframe(df_cl, use_container_width=True)
                
                for idx, row in df_cl.iterrows():
                    med = "🥇 1ère Place" if idx == 1 else ("🥈 2ème Place" if idx == 2 else "🥉 3ème Place")
                    st.markdown(f"<div class='podium-box'><b>{med}</b> : {row['Agent']} - Efficacité : {row['Taux de réussite (%)']:.1f}%</div>", unsafe_allow_html=True)
            else:
                st.info("Aucune donnée d'agent sur cette période.")

