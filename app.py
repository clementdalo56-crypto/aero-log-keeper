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
        padding-top: 40px !important;
        padding-bottom: 40px !important;
    }
    
    /* 2. LE FORMULAIRE BLANC ÉPURÉ */
    [data-testid="stForm"] { 
        max-width: 850px !important; 
        margin: 0 auto !important; 
        padding: 30px !important; 
        background-color: #ffffff !important; 
        border-radius: 15px !important;
        box-shadow: 0 10px 15px -3px rgba(0, 0, 0, 0.1) !important;
        border: 2px solid #ffedd5 !important;
    }
    
    div[data-testid="stSelectbox"], div[data-testid="stTimeInput"] {
        max-width: 750px !important;
        margin: 0 auto 15px auto !important;
    }
    
    div[data-testid="stTextInput"] input, div[data-testid="stTextArea"] textarea, div[data-testid="stNumberInput"] input {
        color: #111827 !important; background-color: #ffffff !important; border: 2px solid #cbd5e1 !important;
    }
    
    div[data-testid="stTimeInput"] input {
        color: #111827 !important; background-color: #ffffff !important; font-weight: bold !important;
    }
    
    div[data-testid="stMarkdownContainer"] p, label p, .stSubheader p {
        color: #111827 !important; font-family: 'Cambria', serif !important; font-weight: 500 !important;
    }
    
    /* 3. DESIGN DE LA BARRE LATÉRALE (Vert foncé) */
    [data-testid="stSidebar"] { background-color: #134e4a !important; border-right: 4px solid #f97316 !important; }
    [data-testid="stSidebar"] .stRadio div[role="radiogroup"] label p {
        font-family: 'Cambria', serif !important; font-size: 14px !important; font-weight: bold !important; color: #ffffff !important; 
    }
    [data-testid="stSidebar"] h2, [data-testid="stSidebar"] p { color: #ffffff !important; }
    [data-testid="stSidebar"] .stRadio div[role="radiogroup"] input[type="radio"] { border-color: #f97316 !important; }
    
    /* 4. DESIGN DES BOUTONS DE VALIDATION */
    div.stButton > button { background-color: #f97316 !important; border-radius: 8px !important; border: none !important; padding: 12px 30px !important; }
    div.stButton > button p { color: #ffffff !important; font-weight: bold !important; font-size: 15px !important; }
    div.stButton > button:hover { background-color: #ea580c !important; }
    
    div[data-testid="stNotification"] { background-color: #f0fdf4 !important; border-left: 5px solid #16a34a !important; }
    .stAlert { background-color: #ffedd5 !important; border-left: 5px solid #f97316 !important; }
    .stAlert p, .stAlert div, [data-testid="stNotification"] p { color: #1a1a1a !important; font-weight: 600 !important; font-size: 14px !important; }
    
    .kpi-box {
        background-color: #ffffff; padding: 15px; border-radius: 10px;
        box-shadow: 0 4px 6px rgba(0,0,0,0.05); text-align: center; border: 1px solid #e5e7eb; border-top: 4px solid #f97316;
    }
    .kpi-title { color: #6b7280; font-size: 12px; text-transform: uppercase; font-weight: bold; }
    .kpi-value { color: #111827; font-size: 24px; font-weight: bold; margin-top: 5px; }
    
    /* Style pour le tableau de classement */
    .podium-box { background-color: #f0fdf4; border: 1px solid #bbf7d0; padding: 10px; border-radius: 8px; margin-bottom: 8px; }
    </style>
""", unsafe_allow_html=True)

MOT_DE_PASSE_REQUIS = "sanpedro2026"
FICHIER_BDD = "donnees_meteo_sanpedro.csv"
FICHIER_AGENTS = "presence_agents_sanpedro.csv"
FICHIER_OBS = "observations_qualite_sanpedro.csv"

# =========================================================================
# 🎛️ CONFIGURATION DU SERVEUR OUTLOOK / OFFICE 365 DE LA SODEXAM
# =========================================================================
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
        except Exception as e: pass
    try:
        serveur = smtplib.SMTP(SMTP_SERVEUR, SMTP_PORT, timeout=5)
        serveur.starttls()
        serveur.login(COMPTE_MAIL_STATION, COMPTE_MOT_DE_PASSE)
        serveur.sendmail(COMPTE_MAIL_STATION, tous_les_destinataires, msg.as_string())
        serveur.quit()
        return True
    except: return False

# --- INITIALISATION DES ARCHIVES ---
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

# =========================================================================
# 🔔 ALERTE ET BIP DE L'HEURE RONDE (ENTRE :50 ET :00)
# =========================================================================
maintenant = datetime.now()
minute_actuelle = maintenant.minute

if 50 <= minute_actuelle <= 59 or minute_actuelle == 0:
    # Affiche un bandeau d'alerte clignotant chaleureux
    st.markdown(f"### 🔔 RAPPEL RÉGLEMENTAIRE : Il est {maintenant.strftime('%H:%M')}. Fenêtre d'observation en cours ! N'oubliez pas d'enregistrer vos transmissions.")
    # Injection d'un son d'alerte (Bip) via le navigateur de l'agent
    st.markdown("""
        <audio autoplay>
            <source src="https://mixkit.co" type="audio/mpeg">
        </audio>
    """, unsafe_allow_html=True)

# --- ACCÈS SÉCURISÉ ---
if "authentifie" not in st.session_state: st.session_state["authentifie"] = False

if not st.session_state["authentifie"]:
    col_gauche, col_centre, col_droite = st.columns(3)
    with col_centre:
        st.markdown("<br><br>", unsafe_allow_html=True)
        st.markdown("<h1 style='text-align: center; color: #f97316; margin-bottom:0;'>🏢 SODEXAM</h1>", unsafe_allow_html=True)
        st.markdown("<h3 style='text-align: center; color: #16a34a; margin-top:0;'>Station de San Pedro</h3>", unsafe_allow_html=True)
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
            "📡 Saisie des Messages Réguliers", "🌡️ Données Extrêmes", "🛠️ Point Instrument & Correction",
            "🌱 AGROMET & CLIMAT", "📂 Tableau Climatologique (TCM)",
            "⏰ Prise & Fin de Service", "📝 Qualité & Justifications Hors Délai",
            "📈 Tableau de bord & Décomptes"
        ]
    )

    date_saisie = maintenant.strftime("%Y-%m-%d")
    heure_informatique = maintenant.strftime("%H:%M")
    agent_bloque = verifier_si_agent_descendu(agent_actif, date_saisie)

    # --- SOUS-MENU 1 : SAISIE DES MESSAGES RÉGULIERS ---
    if choix_menu == "📡 Saisie des Messages Réguliers":
        st.subheader("📡 Saisie des Messages Réguliers")
        if agent_bloque: st.error(f"🛑 Accès refusé : L'agent **{agent_actif}** a déjà enregistré sa fin de service pour aujourd'hui.")
        else:
            with st.form("form_synop_metar"):
                type_msg = st.selectbox("Type de message :", ["SYNOP Horaire", "SYNOP Principal", "METAR", "METREPORT", "SPECI"])
                heures_observations = [f"{h:02d}:00" for h in range(24)]
                heure_nominale_str = st.selectbox("🕒 Heure officielle de l'observation (H UTC) :", heures_observations, index=maintenant.hour)
                heure_trans = st.time_input("⏱️ Heure réelle de transmission du message (Saisie Manuelle Agent) :", maintenant.time())
                corps_msg = st.text_area("Texte réglementaire du message :", height=150)
                
                if st.form_submit_button("🚀 Valider, Archiver et Transmettre"):
                    heure_definitive_str = heure_trans.strftime("%H:%M")
                    if type_msg != "SPECI" and verifier_doublon_message(type_msg, date_saisie, heure_definitive_str):
                        st.error(f"❌ Doublon interdit : Un message {type_msg} existe déjà à cette heure.")
                    else:
                        heure_nominale_dt = datetime.strptime(f"{date_saisie} {heure_nominale_str}", "%Y-%m-%d %H:%M")
                        heure_transmission_dt = datetime.strptime(f"{date_saisie} {heure_definitive_str}", "%Y-%m-%d %H:%M")
                        borne_inferieure = heure_nominale_dt - timedelta(minutes=10)
                        borne_superieure = heure_nominale_dt + timedelta(minutes=5)
                        
                        statut = "Transmis dans le délai" if borne_inferieure <= heure_transmission_dt <= borne_superieure else "Transmis hors délai"
                        df = pd.read_csv(FICHIER_BDD)
                        nouvelle_ligne = {
                            "Date_Saisie": date_saisie, "Heure_Saisie": heure_informatique, "Date_Donnees": date_saisie,
                            "Mois": maintenant.strftime("%B"), "Annee": maintenant.strftime("%Y"), "Agent": agent_actif,
                            "Categorie": "SYNOP & METAR", "Type_Message_Fichier": type_msg, "Heure_Transmission": heure_definitive_str,
                            "Statut_Delai": statut, "Details": f"[Obs: {heure_nominale_str}] {corps_msg}"
                        }
                        pd.concat([df, pd.DataFrame([nouvelle_ligne])], ignore_index=True).to_csv(FICHIER_BDD, index=False)
                        st.success(f"💾 Enregistré localement ! Heure : **{heure_definitive_str}** | Statut : **{statut}**")
                        
                        sujet_mail = f"[{type_msg}] Station San Pedro - Obs de {heure_nominale_str}"
                        transmettre_message_outlook(sujet_mail, corps_msg, ["beta@sodexam.ci"])

    # --- SOUS-MENU 2 : DONNÉES EXTRÊMES ---
    elif choix_menu == "🌡️ Données Extrêmes":
        st.subheader("🌡️ Saisie des Données Extrêmes")
        if agent_bloque: st.error("🛑 Saisie bloquée : Vous avez déjà signé votre fin de service.")
        else:
            with st.form("form_extremes"):
                heure_trans = st.time_input("⏱️ Heure réelle de transmission du message :", maintenant.time())
                t_max = st.number_input("Température Maximale (T MAXI) en °C :", value=28.0, step=0.1)
                t_min = st.number_input("Température Minimale (T MINI) en °C :", value=22.0, step=0.1)
                pluie = st.number_input("Quantité de pluie (P) en mm :", value=0.0, step=0.1)
                if st.form_submit_button("🚀 Enregistrer les Extrêmes"):
                    date_donnees = (maintenant - timedelta(days=1)).strftime("%Y-%m-%d")
                    heure_str = heure_trans.strftime("%H:%M")
                    if verifier_doublon_message("DONNEES EXTREMES", date_donnees, heure_str):
                        st.error("❌ Erreur : Données déjà enregistrées pour cette journée.")
                    else:
                        statut = "Transmis dans le délai" if (6 <= heure_trans.hour < 8) or (heure_trans.hour == 8 and heure_trans.minute == 0) else "Transmis hors délai"
                        df = pd.read_csv(FICHIER_BDD)
                        contenu_texte = f"Données du {date_donnees} | TMAX: {t_max}°C | TMIN: {t_min}°C | Pluie: {pluie}mm"
                        nouvelle_ligne = {
                            "Date_Saisie": date_saisie, "Heure_Saisie": heure_informatique, "Date_Donnees": date_donnees,
                            "Mois": maintenant.strftime("%B"), "Annee": maintenant.strftime("%Y"), "Agent": agent_actif,
                            "Categorie": "Données Extrêmes", "Type_Message_Fichier": "DONNEES EXTREMES", "Heure_Transmission": heure_str,
                            "Statut_Delai": statut, "Details": contenu_texte
                        }
                        pd.concat([df, pd.DataFrame([nouvelle_ligne])], ignore_index=True).to_csv(FICHIER_BDD, index=False)
                        st.success(f"💾 Enregistré localement ! Statut : **{statut}**")
                        transmettre_message_outlook(f"[DONNEES EXTREMES] San Pedro - {date_donnees}", contenu_texte, ["service.prevision@sodexam.com"])

    # --- SOUS-MENU 3 : POINT INSTRUMENT ---
    elif choix_menu == "🛠️ Point Instrument & Correction":
        st.subheader("🛠️ Point Hebdomadaire des Instruments")
        if agent_bloque: st.error("🛑 Action impossible en fin de service.")
        else:
            with st.form("form_instruments"):
                fichier_word = st.file_uploader("Téléverser le rapport (Fichier Word) :", type=["docx", "doc"])
                commentaires = st.text_area("Notes des corrections de messages :")
                if st.form_submit_button("🚀 Enregistrer le Rapport"):
                    if fichier_word is not None:
                        df = pd.read_csv(FICHIER_BDD)
                        nouvelle_ligne = {
                            "Date_Saisie": date_saisie, "Heure_Saisie": heure_informatique, "Date_Donnees": date_saisie,
                            "Mois": maintenant.strftime("%B"), "Annee": maintenant.strftime("%Y"), "Agent": agent_actif,
                            "Categorie": "Instruments", "Type_Message_Fichier": "Rapport WORD", "Heure_Transmission": heure_informatique,
                            "Statut_Delai": "Transmis dans le délai", "Details": f"Fichier: {fichier_word.name} | Notes: {commentaires}"
                        }
                        pd.concat([df, pd.DataFrame([nouvelle_ligne])], ignore_index=True).to_csv(FICHIER_BDD, index=False)
                        st.success("💾 Rapport archivé localement.")
                    else: st.warning("Veuillez charger le fichier Word.")

    # --- SOUS-MENU 4 : AGROMET & CLIMAT ---
    elif choix_menu == "🌱 AGROMET & CLIMAT":
        st.subheader("🌱 Rapports Décadaires AGROMET & Mensuels CLIMAT")
        if agent_bloque: st.error("🛑 Saisie bloquée en fin de service.")
        else:
            with st.form("form_agromet_climat"):
                type_clima = st.selectbox("Type de rapport :", ["AGROMET (Décadaire)", "CLIMAT (Mensuel)"])
                heure_trans = st.time_input("⏱️ Heure réelle de transmission :", maintenant.time())
                corps_clima = st.text_area("Contenu du message :", height=150)
                if st.form_submit_button("🚀 Transmettre le Rapport"):
                    heure_str = heure_trans.strftime("%H:%M")
                    if verifier_doublon_message(type_clima, date_saisie, heure_str): st.error("❌ Doublon détecté.")
                    else:
                        jour = maintenant.day
                        statut = "Transmis dans le délai"
                        if type_clima == "AGROMET (Décadaire)" and (heure_trans.hour >= 9): statut = "Transmis hors délai"
                        elif type_clima == "CLIMAT (Mensuel)" and jour > 4: statut = "Transmis hors délai"
                        df = pd.read_csv(FICHIER_BDD)
                        nouvelle_ligne = {
                            "Date_Saisie": date_saisie, "Heure_Saisie": heure_informatique, "Date_Donnees": date_saisie,
                            "Mois": maintenant.strftime("%B"), "Annee": maintenant.strftime("%Y"), "Agent": agent_actif,
                            "Categorie": "Agromet/Climat", "Type_Message_Fichier": type_clima, "Heure_Transmission": heure_str,
                            "Statut_Delai": statut, "Details": corps_clima
                        }
                        pd.concat([df, pd.DataFrame([nouvelle_ligne])], ignore_index=True).to_csv(FICHIER_BDD, index=False)
                        st.success(f"💾 Rapport enregistré ! Statut : **{statut}**")

    # --- SOUS-MENU 5 : TABLEAU CLIMATOLOGIQUE ---
    elif choix_menu == "📂 Tableau Climatologique (TCM)":
        st.subheader("📂 Fichier Excel TCM")
        if agent_bloque: st.error("🛑 Dépôt bloqué en fin de service.")
        else:
            with st.form("form_tcm"):
                fichier_excel_tcm = st.file_uploader("Sélectionnez votre classeur Excel TCM :", type=["xlsx", "xls"])
                if st.form_submit_button("📨 Valider le dépôt"):
                    if fichier_excel_tcm is not None:
                        df = pd.read_csv(FICHIER_BDD)
                        nouvelle_ligne = {
                            "Date_Saisie": date_saisie, "Heure_Saisie": heure_informatique, "Date_Donnees": date_saisie,
                            "Mois": maintenant.strftime("%B"), "Annee": maintenant.strftime("%Y"), "Agent": agent_actif,
                            "Categorie": "TCM", "Type_Message_Fichier": "Fichier Excel TCM", "Heure_Transmission": heure_informatique,
                            "Statut_Delai": "Transmis dans le délai", "Details": f"Fichier TCM: {fichier_excel_tcm.name}"
                        }
                        pd.concat([df, pd.DataFrame([nouvelle_ligne])], ignore_index=True).to_csv(FICHIER_BDD, index=False)
                        st.success("💾 Fichier enregistré localement.")
                        
                        sujet_mail = f"[TCM EXCEL] Envoi Périodique - San Pedro"
                        corps_mail = "Bonjour,\nVeuillez trouver ci-joint le fichier Excel TCM de San Pedro."
                        transmettre_message_outlook(sujet_mail, corps_mail, ["juliette.assi@sodexam.ci"], fichier_joint=fichier_excel_tcm)
                    else: st.warning("Veuillez charger un fichier Excel valide.")

    # --- SOUS-MENU 6 : PRISE & FIN DE SERVICE ---
    elif choix_menu == "⏰ Prise & Fin de Service":
        st.subheader("⏰ Registre de Présence (Montée / Descente)")
        with st.form("form_presence"):
            action = st.radio("Action :", ["Prise de service (Montée)", "Fin de service (Descente)"])
            heure_action = st.time_input("Heure officielle :", maintenant.time())
            if st.form_submit_button("💾 Valider"):
                df_p = pd.read_csv(FICHIER_AGENTS)
                deja_signe = df_p[(df_p["Date"] == date_saisie) & (df_p["Agent"] == agent_actif) & (df_p["Action"] == action)]
                if not deja_signe.empty: st.error(f"❌ Déjà enregistré aujourd'hui.")
                else:
                    nouvelle_p = {"Date": date_saisie, "Agent": agent_actif, "Action": action, "Heure": heure_action.strftime("%H:%M")}
                    pd.concat([df_p, pd.DataFrame([nouvelle_p])], ignore_index=True).to_csv(FICHIER_AGENTS, index=False)
                    st.success(f"✅ Validé pour {agent_actif} ({action}).")

    # --- SOUS-MENU 7 : CAHIER D'OBSERVATIONS ---
    elif choix_menu == "📝 Qualité & Justifications Hors Délai":
        st.subheader("📝 Cahier d'Observations de la Station")
        with st.form("form_obs"):
            type_obs = st.selectbox("Nature :", ["Raison de transmission Hors Délai", "Message non transmis (Manquant)", "Note sur la Qualité", "Panne / Coupure Internet"])
            msg_concerne = st.text_input("Message concerné (Ex: SYNOP 12h) :")
            explications = st.text_area("Explications détaillées :")
            if st.form_submit_button("🚀 Enregistrer"):
                df_o = pd.read_csv(FICHIER_OBS)
                nouvelle_o = {"Date": date_saisie, "Heure": heure_informatique, "Agent": agent_actif, "Type_Observation": type_obs, "Message_Concerne": msg_concerne, "Raison_Retard_Ou_Qualite": explications}
                pd.concat([df_o, pd.DataFrame([nouvelle_o])], ignore_index=True).to_csv(FICHIER_OBS, index=False)
                st.success("💾 Observation consignée dans le registre.")

    # --- SOUS-MENU 8 : TABLEAU DE BORD, HISTORIQUES ET CLASSEMENT AGENTS ---
    elif choix_menu == "📈 Tableau de bord & Décomptes":
        st.subheader("📊 Rendement, Historique Temporel Total et Classement")
        df_stats = pd.read_csv(FICHIER_BDD)
        
                # --- FILTRES AVANCÉS MULTI-ANNÉES ---
        col_t1, col_t2, col_t3 = st.columns(3)
        with col_t1:
            if not df_stats.empty:
                liste_annees = sorted([str(a) for a in df_stats['Annee'].dropna().unique().tolist()])
            else:
                liste_annees = [maintenant.strftime("%Y")]
                
            if maintenant.strftime("%Y") not in liste_annees: 
                liste_annees.append(maintenant.strftime("%Y"))
                
            annee_sel = st.selectbox("📅 Sélectionner l'Année (Suivi historique complet) :", sorted(liste_annees, reverse=True))


        with col_t2:
            liste_mois = ["Tous", "January", "February", "March", "April", "May", "June", "July", "August", "September", "October", "November", "December"]
            mois_sel = st.selectbox("⏳ Sélectionner le Mois :", liste_mois, index=maintenant.month)
        with col_t3:
            type_msg_filtre = st.selectbox("📡 Filtrer par Type de Message :", ["Tous", "SYNOP Horaire", "SYNOP Principal", "METAR", "METREPORT", "SPECI"])

        # LOGIQUE DE FILTRAGE HISTORIQUE
        if not df_stats.empty:
            df_temp = df_stats[df_stats["Annee"] == str(annee_sel)]
            if mois_sel != "Tous":
                df_temp = df_temp[df_temp["Mois"] == mois_sel]
            if type_msg_filtre != "Tous":
                df_final = df_temp[df_temp["Type_Message_Fichier"] == type_msg_filtre]
            else:
                df_final = df_temp
        else:
            df_final = pd.DataFrame()

        # Calcul des quotas théoriques attendus
        facteur_jours = maintenant.day if (mois_sel == maintenant.strftime("%B") and str(annee_sel) == maintenant.strftime("%Y")) else 30
        if mois_sel == "Tous": facteur_jours = 365
        
        quotas_par_jour = {"SYNOP Horaire": 24, "SYNOP Principal": 8, "METAR": 14, "METREPORT": 14, "SPECI": 0}
        attendus = quotas_par_jour.get(type_msg_filtre, sum([quotas_par_jour["SYNOP Horaire"], quotas_par_jour["SYNOP Principal"], quotas_par_jour["METAR"], quotas_par_jour["METREPORT"]])) * facteur_jours

        transmis = len(df_final)
        dans_delai = len(df_final[df_final["Statut_Delai"] == "Transmis dans le délai"]) if not df_final.empty else 0
        hors_delai = len(df_final[df_final["Statut_Delai"] == "Transmis hors délai"]) if not df_final.empty else 0
        non_transmis = 0 if type_msg_filtre == "SPECI" else max(0, attendus - transmis)
        taux_rendement = (dans_delai / attendus) * 100 if attendus > 0 else 0.0

        # Affichage des boîtes de statistiques (KPI)
        k1, k2, k3, k4, k5 = st.columns(5)
        with k1: st.markdown(f'<div class="kpi-box"><div class="kpi-title">📋 Attendus ({annee_sel})</div><div class="kpi-value">{attendus}</div></div>', unsafe_allow_html=True)
        with k2: st.markdown(f'<div class="kpi-box" style="border-top-color: #3b82f6;"><div class="kpi-title">📤 Transmis</div><div class="kpi-value">{transmis}</div></div>', unsafe_allow_html=True)
        with k3: st.markdown(f'<div class="kpi-box" style="border-top-color: #16a34a;"><div class="kpi-title">⏱️ Dans les Délais</div><div class="kpi-value">{dans_delai}</div></div>', unsafe_allow_html=True)
        with k4: st.markdown(f'<div class="kpi-box" style="border-top-color: #f97316;"><div class="kpi-title">⚠️ Hors Délais</div><div class="kpi-value">{hors_delai}</div></div>', unsafe_allow_html=True)
        with k5: st.markdown(f'<div class="kpi-box" style="border-top-color: {"#ef4444" if non_transmis > 0 else "#6b7280"};"><div class="kpi-title">❌ Non Transmis</div><div class="kpi-value">{non_transmis}</div></div>', unsafe_allow_html=True)

        st.markdown("<br>", unsafe_allow_html=True)
        couleur_rendement = "#16a34a" if taux_rendement >= 85 else ("#f97316" if taux_rendement >= 50 else "#ef4444")
        st.markdown(f"<div style='background-color: #ffffff; padding: 15px; border-radius: 10px; text-align: center; border-left: 6px solid {couleur_rendement}; border-top: 1px solid #e5e7eb;'><p style='margin:0; font-size:12px; font-weight:bold; color:#6b7280;'>🎯 RENDEMENT DES TRANSMISSIONS SUR LA PÉRIODE SÉLECTIONNÉE</p><p style='margin:5px 0 0 0; font-size:32px; font-weight:bold; color:{couleur_rendement};'>{taux_rendement:.1f} %</p></div>", unsafe_allow_html=True)

        # Onglets de séparation pour clarifier l'espace des données
        tab_data, tab_agents = st.tabs(["🗄️ Registre et Corrections", "🏆 Performances & Classement des Agents"])
        
        with tab_data:
            if not df_final.empty:
                df_final['ID'] = df_final.index
                st.dataframe(df_final[["ID", "Date_Saisie", "Heure_Saisie", "Agent", "Type_Message_Fichier", "Heure_Transmission", "Statut_Delai", "Details"]], use_container_width=True)
                
                # Formulaires de modification libre intégrés sous la table
                col_c1, col_c2 = st.columns(2)
                with col_c1:
                    st.markdown("#### 📝 Corriger un message erroné")
                    id_m = st.number_input("Entrez l'ID du message à éditer :", min_value=0, max_value=len(df_stats)-1, step=1, key="admin_id_modif")
                    if not df_stats.empty:
                        with st.form("form_agent_correction"):
                            n_agent = st.selectbox("Auteur de la correction :", liste_agents, index=liste_agents.index(df_stats.at[id_m, 'Agent']) if df_stats.at[id_m, 'Agent'] in liste_agents else 0)
                            n_heure = st.text_input("Ajuster l'heure (HH:MM) :", value=str(df_stats.at[id_m, 'Heure_Transmission']))
                            n_statut = st.selectbox("Délai :", ["Transmis dans le délai", "Transmis hors délai"], index=0 if df_stats.at[id_m, 'Statut_Delai'] == "Transmis dans le délai" else 1)
                            n_details = st.text_area("Ajuster le corps :", value=str(df_stats.at[id_m, 'Details']))
                            if st.form_submit_button("💾 Sauvegarder la correction"):
                                df_stats.at[id_m, 'Agent'] = n_agent
                                df_stats.at[id_m, 'Heure_Transmission'] = n_heure
                                df_stats.at[id_m, 'Statut_Delai'] = n_statut
                                df_stats.at[id_m, 'Details'] = n_details
                                df_stats.to_csv(FICHIER_BDD, index=False)
                                st.success("Correction enregistrée !")
                                st.rerun()
                with col_c2:
                    st.markdown("#### 🗑️ Supprimer une ligne")
                    id_s = st.number_input("Entrez l'ID du message à détruire :", min_value=0, max_value=len(df_stats)-1, step=1, key="admin_id_suppr")
                    if st.button("🗑️ Confirmer l'effacement définitif", use_container_width=True):
                        df_stats.drop(index=id_s).to_csv(FICHIER_BDD, index=False)
                        st.success("Ligne supprimée !")
                        st.rerun()
            else: st.info("Aucun message enregistré pour cette période.")

        with tab_agents:
            st.markdown(f"### 🏆 Rendement et Classement des Agents de la Station ({mois_sel} {annee_sel})")
            if not df_final.empty:
                # Calcul des statistiques de performance par agent
                stats_agents = []
                for agent in df_final["Agent"].unique():
                    df_agent = df_final[df_final["Agent"] == agent]
                    total_agent = len(df_agent)
                    delai_agent = len(df_agent[df_agent["Statut_Delai"] == "Transmis dans le délai"])
                    retard_agent = len(df_agent[df_agent["Statut_Delai"] == "Transmis hors délai"])
                    taux_agent = (delai_agent / total_agent) * 100 if total_agent > 0 else 0
                    stats_agents.append({
                        "Agent": agent, 
                        "Messages Transmis": total_agent,
                        "Dans les Délais": delai_agent, 
                        "Hors Délais": retard_agent, 
                        "Taux de Réussite (%)": round(taux_agent, 1)
                    })
                
                # Tri automatique pour obtenir le classement officiel
                df_classement = pd.DataFrame(stats_agents).sort_values(by=["Taux de Réussite (%)", "Messages Transmis"], ascending=False).reset_index(drop=True)
                df_classement.index += 1 # Ajuste l'index pour démarrer à 1 au lieu de 0
                
                # Affichage du tableau de statistiques des agents
                st.dataframe(df_classement, use_container_width=True)
                
                st.markdown("#### 🎖️ Félicitations aux Agents en tête du classement :")
                for index, row in df_classement.iterrows():
                    medaille = "🥇 1er Place" if index == 1 else ("🥈 2ème Place" if index == 2 else "🥉 3ème Place")
                    st.markdown(f'<div class="podium-box"><b>{medaille} : {row["Agent"]}</b> avec un taux d\'efficacité de <b>{row["Taux de Réussite (%)"]}%</b> ({row["Dans les Délais"]} messages transmis à temps)</div>', unsafe_allow_html=True)
            else:
                st.info("Aucune donnée disponible pour établir le classement des agents sur cette période.")
