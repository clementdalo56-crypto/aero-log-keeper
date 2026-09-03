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
    /* Fond principal blanc */
    .stApp { background-color: #ffffff !important; color: #1f2937 !important; }
    [data-testid="stForm"] { max-width: 850px !important; margin: 0 auto !important; padding: 20px !important; }
    
    /* Correction des zones de saisie et textes de formulaires */
    div[data-testid="stTextInput"] input, div[data-testid="stTextArea"] textarea, div[data-testid="stNumberInput"] input {
        color: #111827 !important; background-color: #f3f4f6 !important; border: 2px solid #d1d5db !important;
    }
        /* Force l'heure saisie par l'agent à s'afficher en Noir Foncé sur fond clair */
    div[data-testid="stTimeInput"] input {
        color: #111827 !important;
        background-color: #f3f4f6 !important;
        font-weight: bold !important;
    }

    /* FORCE l'écriture de TOUS les paragraphes de texte centraux en NOIR pour éviter le texte invisible */
    div[data-testid="stMarkdownContainer"] p, label p {
        color: #111827 !important;
        font-family: 'Cambria', serif !important;
    }
    
    /* Design de la barre latérale */
    [data-testid="stSidebar"] { background-color: #f3f4f6 !important; border-right: 3px solid #f97316 !important; }
    
    /* MODIFICATION : FORCE l'écriture des sous-menus à être en TAILLE 14 et en Cambria */
    [data-testid="stSidebar"] .stRadio div[role="radiogroup"] label p {
        font-family: 'Cambria', serif !important;
        font-size: 14px !important; /* TAILLE AUGMENTÉE À 14 */
        font-weight: bold !important;
        color: #111827 !important;
    }
    [data-testid="stSidebar"] .stRadio div[role="radiogroup"] input[type="radio"] { border-color: #f97316 !important; }
    
    /* Design du bouton de validation */
    div.stButton > button { background-color: #f97316 !important; border-radius: 8px !important; border: none !important; padding: 10px 24px !important; }
    div.stButton > button p { color: #ffffff !important; font-weight: bold !important; font-size: 14px !important; }
    div.stButton > button:hover { background-color: #ea580c !important; }
    
    /* Bandeaux d'alertes */
    div[data-testid="stNotification"] { background-color: #f0fdf4 !important; border-left: 5px solid #16a34a !important; }
    .stAlert { background-color: #fff7ed !important; border-left: 5px solid #f97316 !important; }
    .stAlert p, .stAlert div, [data-testid="stNotification"] p { color: #1a1a1a !important; font-weight: 600 !important; font-size: 14px !important; }
    
    /* Blocs statistiques (KPI) */
    .kpi-box {
        background-color: #ffffff; padding: 15px; border-radius: 10px;
        box-shadow: 0 4px 6px rgba(0,0,0,0.05); text-align: center; border: 1px solid #e5e7eb; border-top: 4px solid #f97316;
    }
    .kpi-title { color: #6b7280; font-size: 12px; text-transform: uppercase; font-weight: bold; }
    .kpi-value { color: #111827; font-size: 24px; font-weight: bold; margin-top: 5px; }
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
COMPTE_MOT_DE_PASSE = "Sp2022met"  

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
        except Exception as e:
            st.warning(f"⚠️ Impossible de lier la pièce jointe : {e}")

    try:
        serveur = smtplib.SMTP(SMTP_SERVEUR, SMTP_PORT, timeout=5)
        serveur.starttls()
        serveur.login(COMPTE_MAIL_STATION, COMPTE_MOT_DE_PASSE)
        serveur.sendmail(COMPTE_MAIL_STATION, tous_les_destinataires, msg.as_string())
        serveur.quit()
        return True
    except Exception as e:
        st.warning("📢 Avis : Message stocké en base locale. L'envoi direct Outlook a échoué.")
        return False

# --- INITIALISATION DES ARCHIVES COMPLÈTES ---
colonnes_principales = ["Date_Saisie", "Heure_Saisie", "Date_Donnees", "Mois", "Annee", "Agent", "Categorie", "Type_Message_Fichier", "Heure_Transmission", "Statut_Delai", "Details"]
if not os.path.exists(FICHIER_BDD):
    pd.DataFrame(columns=colonnes_principales).to_csv(FICHIER_BDD, index=False)
if not os.path.exists(FICHIER_AGENTS):
    pd.DataFrame(columns=["Date", "Agent", "Action", "Heure"]).to_csv(FICHIER_AGENTS, index=False)
if not os.path.exists(FICHIER_OBS):
    pd.DataFrame(columns=["Date", "Heure", "Agent", "Type_Observation", "Message_Concerne", "Raison_Retard_Ou_Qualite"]).to_csv(FICHIER_OBS, index=False)

# --- FONCTIONS DE CONTRÔLE QA/QC ---
def verifier_si_agent_descendu(agent, date_du_jour):
    df_p = pd.read_csv(FICHIER_AGENTS)
    if not df_p.empty:
        descente = df_p[(df_p["Date"] == date_du_jour) & (df_p["Agent"] == agent) & (df_p["Action"] == "Fin de service (Descente)")]
        if not descente.empty: return True
    return False

def verifier_doublon_message(type_msg, date_data, heure_trans):
    df_b = pd.read_csv(FICHIER_BDD)
    if not df_b.empty:
        heure_str = heure_trans.strftime("%H:%M") if hasattr(heure_trans, 'strftime') else str(heure_trans)[:5]
        doublon = df_b[(df_b["Type_Message_Fichier"] == type_msg) & (df_b["Date_Donnees"] == date_data) & (df_b["Heure_Transmission"] == heure_str)]
        if not doublon.empty: return True
    return False

# --- ACCÈS SÉCURISÉ AGENTS ---
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
            "📡 SYNOP & METAR", "🌡️ Données Extrêmes", "🛠️ Point Instrument & Correction",
            "🌱 AGROMET & CLIMAT", "📂 Tableau Climatologique (TCM)",
            "⏰ Prise & Fin de Service", "📝 Qualité & Justifications Hors Délai",
            "📈 Tableau de bord & Décomptes"
        ]
    )

    maintenant = datetime.now()
    date_saisie = maintenant.strftime("%Y-%m-%d")
    heure_informatique = maintenant.strftime("%H:%M")

    # --- SÉCURITÉ : BLOCAGE AVANT SAISIE SI DESCENTE VALIDÉE ---
    agent_bloque = verifier_si_agent_descendu(agent_actif, date_saisie)

    # --- SOUS-MENU 1 : SYNOP & METAR ---
    if choix_menu == "📡 SYNOP & METAR":
        st.subheader("📡 Saisie des Messages Réguliers (SYNOP / METAR)")
        if agent_bloque:
            st.error(f"🛑 Accès refusé : L'agent **{agent_actif}** a déjà enregistré sa fin de service pour aujourd'hui.")
        else:
            with st.form("form_synop_metar"):
                type_msg = st.selectbox("Type de message :", ["SYNOP Horaire", "SYNOP Principal", "METAR", "METREPORT", "SPECI"])
                heures_observations = [f"{h:02d}:00" for h in range(24)]
                heure_nominale_str = st.selectbox("🕒 Heure officielle de l'observation (H UTC) :", heures_observations, index=maintenant.hour)
                heure_trans = st.time_input("⏱️ Heure réelle de transmission du message :", maintenant.time())
                corps_msg = st.text_area("Texte réglementaire du message :", height=150)
                
                if st.form_submit_button("🚀 Valider, Archiver et Transmettre"):
                    if type_msg != "SPECI" and verifier_doublon_message(type_msg, date_saisie, heure_trans):
                        st.error(f"❌ Enregistrement impossible : Un message {type_msg} a déjà été transmis à cette heure aujourd'hui.")
                    else:
                        # --- FENÊTRE RÉGLEMENTAIRE (H-10 min à H+5 min inclus) ---
                        heure_nominale_dt = datetime.strptime(f"{date_saisie} {heure_nominale_str}", "%Y-%m-%d %H:%M")
                        heure_transmission_dt = datetime.strptime(f"{date_saisie} {heure_trans.strftime('%H:%M')}", "%Y-%m-%d %H:%M")
                        
                        borne_inferieure = heure_nominale_dt - timedelta(minutes=10)
                        borne_superieure = heure_nominale_dt + timedelta(minutes=5)
                        
                        
                        # Validation de la plage horaire stricte (H-10 à H+5 inclus)
                        statut = "Transmis dans le délai" if borne_inferieure <= heure_transmission_dt <= borne_superieure else "Transmis hors délai"
                        
                        # Archivage en base de données locale
                        df = pd.read_csv(FICHIER_BDD)
                        nouvelle_ligne = {
                            "Date_Saisie": date_saisie, "Heure_Saisie": heure_informatique, "Date_Donnees": date_saisie,
                            "Mois": maintenant.strftime("%B"), "Annee": maintenant.strftime("%Y"), "Agent": agent_actif,
                            "Categorie": "SYNOP & METAR", "Type_Message_Fichier": type_msg, "Heure_Transmission": heure_trans.strftime("%H:%M"),
                            "Statut_Delai": statut, "Details": f"[Obs: {heure_nominale_str}] {corps_msg}"
                        }
                        pd.concat([df, pd.DataFrame([nouvelle_ligne])], ignore_index=True).to_csv(FICHIER_BDD, index=False)
                        st.success(f"💾 Message enregistré localement ! Statut : **{statut}**")
                        
                        sujet_mail = f"[{type_msg}] Station San Pedro - Obs de {heure_nominale_str} (Transmis à {heure_trans.strftime('%H:%M')} UTC)"
                        if transmettre_message_outlook(sujet_mail, corps_msg, ["beta@sodexam.ci"]):
                            st.success("✉️ Message envoyé automatiquement par e-mail à beta@sodexam.ci")

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
                    if verifier_doublon_message("DONNEES EXTREMES", date_donnees, heure_trans):
                        st.error("❌ Erreur : Les données extrêmes de la veille ont déjà été enregistrées.")
                    else:
                        statut = "Transmis dans le délai" if (6 <= heure_trans.hour < 8) or (heure_trans.hour == 8 and heure_trans.minute == 0) else "Transmis hors délai"
                        df = pd.read_csv(FICHIER_BDD)
                        contenu_texte = f"Données du {date_donnees} | TMAX: {t_max}°C | TMIN: {t_min}°C | Pluie: {pluie}mm"
                        nouvelle_ligne = {
                            "Date_Saisie": date_saisie, "Heure_Saisie": heure_informatique, "Date_Donnees": date_donnees,
                            "Mois": maintenant.strftime("%B"), "Annee": maintenant.strftime("%Y"), "Agent": agent_actif,
                            "Categorie": "Données Extrêmes", "Type_Message_Fichier": "DONNEES EXTREMES", "Heure_Transmission": heure_trans.strftime("%H:%M"),
                            "Statut_Delai": statut, "Details": contenu_texte
                        }
                        pd.concat([df, pd.DataFrame([nouvelle_ligne])], ignore_index=True).to_csv(FICHIER_BDD, index=False)
                        st.success(f"💾 Enregistré localement ! Statut : **{statut}**")
                        
                        sujet_mail = f"[DONNEES EXTREMES] Station San Pedro - Obs du {date_donnees}"
                        if transmettre_message_outlook(sujet_mail, contenu_texte, ["service.prevision@sodexam.com"]):
                            st.success("✉️ Données transmises par e-mail au service prévision.")

    # --- SOUS-MENU 3 : POINT INSTRUMENT & CORRECTION ---
    elif choix_menu == "🛠️ Point Instrument & Correction":
        st.subheader("🛠️ Point Hebdomadaire des Instruments et Chiffrement")
        if agent_bloque: st.error("🛑 Action impossible en fin de service.")
        else:
            with st.form("form_instruments"):
                fichier_word = st.file_uploader("Téléverser le rapport d'instrumentation (Fichier Word) :", type=["docx", "doc"])
                commentaires = st.text_area("Notes ou détails des corrections de messages :")
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
                        
                        sujet_mail = f"[INSTRUMENTS] Point Hebdomadaire - Station San Pedro"
                        corps_mail = f"Bonjour,\nVeuillez trouver ci-joint le point des instruments.\nNotes: {commentaires}"
                        transmettre_message_outlook(sujet_mail, corps_mail, ["alain.gnayoro@sodexam.ci"], fichier_joint=fichier_word)
                    else: st.warning("Veuillez charger le fichier Word.")

    # --- SOUS-MENU 4 : AGROMET & CLIMAT ---
    elif choix_menu == "🌱 AGROMET & CLIMAT":
        st.subheader("🌱 Saisie des Rapports Décadaires AGROMET & Mensuels CLIMAT")
        if agent_bloque: st.error("🛑 Saisie bloquée en fin de service.")
        else:
            with st.form("form_agromet_climat"):
                type_clima = st.selectbox("Type de rapport :", ["AGROMET (Décadaire)", "CLIMAT (Mensuel)"])
                heure_trans = st.time_input("⏱️ Heure réelle de transmission du message :", maintenant.time())
                corps_clima = st.text_area("Contenu textuel du message :", height=150)
                
                if st.form_submit_button("🚀 Transmettre le Rapport"):
                    if verifier_doublon_message(type_clima, date_saisie, heure_trans):
                        st.error("❌ Un rapport identique existe déjà pour aujourd'hui.")
                    else:
                        jour = maintenant.day
                        statut = "Transmis dans le délai"
                        if type_clima == "AGROMET (Décadaire)":
                            if (jour not in 1,11,21) or (heure_trans.hour >= 9): statut = "Transmis hors délai"
                        elif type_clima == "CLIMAT (Mensuel)" and jour > 4: statut = "Transmis hors délai"
                            
                        df = pd.read_csv(FICHIER_BDD)
                        nouvelle_ligne = {
                            "Date_Saisie": date_saisie, "Heure_Saisie": heure_informatique, "Date_Donnees": date_saisie,
                            "Mois": maintenant.strftime("%B"), "Annee": maintenant.strftime("%Y"), "Agent": agent_actif,
                            "Categorie": "Agromet/Climat", "Type_Message_Fichier": type_clima, "Heure_Transmission": heure_trans.strftime("%H:%M"),
                            "Statut_Delai": statut, "Details": corps_clima
                        }
                        pd.concat([df, pd.DataFrame([nouvelle_ligne])], ignore_index=True).to_csv(FICHIER_BDD, index=False)
                        st.success(f"💾 Rapport enregistré ! Statut : **{statut}**")
                        
                        sujet_mail = f"[{type_clima}] Transmission Station San Pedro - {date_saisie}"
                        transmettre_message_outlook(sujet_mail, corps_clima, ["augustin.mian@sodexam.ci"])

    # --- SOUS-MENU 5 : TABLEAU CLIMATOLOGIQUE (TCM) ---
    elif choix_menu == "📂 Tableau Climatologique (TCM)":
        st.subheader("📂 Suivi du Fichier Excel TCM Renseigné à Part")
        if agent_bloque: st.error("🛑 Dépôt bloqué en fin de service.")
        else:
            with st.form("form_tcm"):
                fichier_excel_tcm = st.file_uploader("Sélectionnez votre classeur Excel TCM :", type=["xlsx", "xls"])
                if st.form_submit_button("📨 Valider le dépôt de dossier"):
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
            action = st.radio("Action à effectuer :", ["Prise de service (Montée)", "Fin de service (Descente)"])
            heure_action = st.time_input("Heure officielle de l'action :", maintenant.time())
            if st.form_submit_button("💾 Valider l'heure"):
                df_p = pd.read_csv(FICHIER_AGENTS)
                deja_signe = df_p[(df_p["Date"] == date_saisie) & (df_p["Agent"] == agent_actif) & (df_p["Action"] == action)]
                if not deja_signe.empty:
                    st.error(f"❌ Action refusée : Vous avez déjà enregistré une {action} aujourd'hui.")
                else:
                    nouvelle_p = {"Date": date_saisie, "Agent": agent_actif, "Action": action, "Heure": heure_action.strftime("%H:%M")}
                    pd.concat([df_p, pd.DataFrame([nouvelle_p])], ignore_index=True).to_csv(FICHIER_AGENTS, index=False)
                    st.success(f"✅ Présence validée pour {agent_actif} ({action}).")

    # --- SOUS-MENU 7 : QUALITÉ & JUSTIFICATIONS ---
    elif choix_menu == "📝 Qualité & Justifications Hors Délai":
        st.subheader("📝 Cahier d'Observations de la Station")
        with st.form("form_obs"):
            type_obs = st.selectbox("Nature de l'observation :", ["Raison de transmission Hors Délai", "Message non transmis (Manquant)", "Note sur la Qualité / Erreur de chiffrement", "Panne d'instrument / Coupure Internet"])
            msg_concerne = st.text_input("Message concerné (Ex: SYNOP 12h, METAR 07h30) :")
            explications = st.text_area("Description détaillée des raisons :")
            if st.form_submit_button("🚀 Enregistrer l'observation"):
                df_o = pd.read_csv(FICHIER_OBS)
                nouvelle_o = {"Date": date_saisie, "Heure": heure_informatique, "Agent": agent_actif, "Type_Observation": type_obs, "Message_Concerne": msg_concerne, "Raison_Retard_Ou_Qualite": explications}
                pd.concat([df_o, pd.DataFrame([nouvelle_o])], ignore_index=True).to_csv(FICHIER_OBS, index=False)
                st.success("💾 Observation consignée dans le registre.")
                
                sujet_mail = f"[ALERTE QUALITE] {type_obs} - Station San Pedro"
                corps_mail = f"Message : {msg_concerne}\nExplications : {explications}\nSaisi par : {agent_actif}"
                transmettre_message_outlook(sujet_mail, corps_mail, ["service.prevision@sodexam.com", "alain.gnayoro@sodexam.ci"])

    # --- SOUS-MENU 8 : TABLEAU DE BORD & MODIFICATION DES SAISIES ---
    elif choix_menu == "📈 Tableau de bord & Décomptes":
        st.subheader("📊 Rendement, Efficacité Règlementaire & Gestion du Registre")
        df_stats = pd.read_csv(FICHIER_BDD)
        
        col_t1, col_t2, col_t3 = st.columns(3)
        with col_t1: periode_filtre = st.selectbox("⏳ Échelle temporelle :", ["Journalier (Aujourd'hui)", "Mensuel (Mois en cours)", "Annuel (Année en cours)"])
        with col_t2: type_msg_filtre = st.selectbox("📡 Filtrer par Type de Message :", ["Tous", "SYNOP Horaire", "SYNOP Principal", "METAR", "METREPORT", "SPECI"])
        with col_t3: st.markdown(f"<p style='margin-top:25px; font-weight:bold; color:#f97316;'>📅 Date : {date_saisie} | {heure_informatique}</p>", unsafe_allow_html=True)

        if not df_stats.empty:
            if "Journalier" in periode_filtre:
                df_temp = df_stats[df_stats["Date_Saisie"] == date_saisie]
                facteur_jours = 1
            elif "Mensuel" in periode_filtre:
                df_temp = df_stats[(df_stats["Mois"] == maintenant.strftime("%B")) & (df_stats["Annee"] == maintenant.strftime("%Y"))]
                facteur_jours = maintenant.day
            else:
                df_temp = df_stats[df_stats["Annee"] == maintenant.strftime("%Y")]
                facteur_jours = maintenant.timetuple().tm_yday
            df_final = df_temp[df_temp["Type_Message_Fichier"] == type_msg_filtre] if type_msg_filtre != "Tous" else df_temp
        else:
            df_final = pd.DataFrame(); facteur_jours = 1

        quotas_par_jour = {"SYNOP Horaire": 24, "SYNOP Principal": 8, "METAR": 14, "METREPORT": 14, "SPECI": 0}
        attendus = quotas_par_jour.get(type_msg_filtre, sum([quotas_par_jour["SYNOP Horaire"], quotas_par_jour["SYNOP Principal"], quotas_par_jour["METAR"], quotas_par_jour["METREPORT"]])) * facteur_jours

        transmis = len(df_final)
        dans_delai = len(df_final[df_final["Statut_Delai"] == "Transmis dans le délai"]) if not df_final.empty else 0
        hors_delai = len(df_final[df_final["Statut_Delai"] == "Transmis hors délai"]) if not df_final.empty else 0
        non_transmis = 0 if type_msg_filtre == "SPECI" else max(0, attendus - transmis)
        taux_rendement = (dans_delai / attendus) * 100 if attendus > 0 else 0.0

        k1, k2, k3, k4, k5 = st.columns(5)
        with k1: st.markdown(f'<div class="kpi-box"><div class="kpi-title">📋 Attendus</div><div class="kpi-value">{attendus}</div></div>', unsafe_allow_html=True)
        with k2: st.markdown(f'<div class="kpi-box" style="border-top-color: #3b82f6;"><div class="kpi-title">📤 Transmis</div><div class="kpi-value">{transmis}</div></div>', unsafe_allow_html=True)
        with k3: st.markdown(f'<div class="kpi-box" style="border-top-color: #16a34a;"><div class="kpi-title">⏱️ Dans les Délais</div><div class="kpi-value">{dans_delai}</div></div>', unsafe_allow_html=True)
        with k4: st.markdown(f'<div class="kpi-box" style="border-top-color: #f97316;"><div class="kpi-title">⚠️ Hors Délais</div><div class="kpi-value">{hors_delai}</div></div>', unsafe_allow_html=True)
        with k5: st.markdown(f'<div class="kpi-box" style="border-top-color: {"#ef4444" if non_transmis > 0 else "#6b7280"};"><div class="kpi-title">❌ Non Transmis</div><div class="kpi-value">{non_transmis}</div></div>', unsafe_allow_html=True)

        st.markdown("<br>", unsafe_allow_html=True)
        couleur_rendement = "#16a34a" if taux_rendement >= 85 else ("#f97316" if taux_rendement >= 50 else "#ef4444")
        st.markdown(f"<div style='background-color: #f9fafb; padding: 15px; border-radius: 10px; text-align: center; border-left: 6px solid {couleur_rendement};'><p style='margin:0; font-size:12px; font-weight:bold; color:#6b7280;'>🎯 TAUX DE RENDEMENT RÉGLEMENTAIRE GLOBAL</p><p style='margin:5px 0 0 0; font-size:32px; font-weight:bold; color:{couleur_rendement};'>{taux_rendement:.1f} %</p></div>", unsafe_allow_html=True)

               # Outils d'édition libres
        st.markdown("---")
        st.markdown("### 🗄️ Registre Complet & Outils de Correction Rapide")
        
        df_global = pd.read_csv(FICHIER_BDD)
        
        if not df_global.empty:
            df_global['ID'] = df_global.index
            st.markdown("#### 1. Liste de tous les messages archivés :")
            st.dataframe(df_global[["ID", "Date_Saisie", "Heure_Saisie", "Agent", "Type_Message_Fichier", "Heure_Transmission", "Statut_Delai", "Details"]], use_container_width=True)
            
            st.markdown("---")
            col_action1, col_action2 = st.columns(2)
            
            with col_action1:
                st.markdown("#### 📝 Corriger une Saisie")
                id_modif = st.number_input("Sélectionnez l'ID du message à corriger :", min_value=0, max_value=len(df_global)-1, step=1)
                ligne_a_modifier = df_global.iloc[id_modif]
                
                with st.form("form_edition_agent"):
                    new_agent = st.selectbox("Auteur de la correction :", liste_agents, index=liste_agents.index(ligne_a_modifier['Agent']) if ligne_a_modifier['Agent'] in liste_agents else 0)
                    new_heure_trans = st.text_input("Ajuster l'Heure réelle de transmission (HH:MM) :", value=str(ligne_a_modifier['Heure_Transmission']))
                    new_statut = st.selectbox("Re-qualifier le délai :", ["Transmis dans le délai", "Transmis hors délai"], index=0 if ligne_a_modifier['Statut_Delai'] == "Transmis dans le délai" else 1)
                    new_details = st.text_area("Ajuster le texte du message :", value=str(ligne_a_modifier['Details']))
                    
                    if st.form_submit_button("💾 Enregistrer les Corrections"):
                        df_global.at[id_modif, 'Agent'] = new_agent
                        df_global.at[id_modif, 'Heure_Transmission'] = new_heure_trans
                        df_global.at[id_modif, 'Statut_Delai'] = new_statut
                        df_global.at[id_modif, 'Details'] = new_details
                        
                        df_global.drop(columns=['ID']).to_csv(FICHIER_BDD, index=False)
                        st.success(f"✅ Le message ID {id_modif} a été corrigé avec succès !")
                        st.rerun()
                        
            with col_action2:
                st.markdown("#### ❌ Supprimer un Message erroné")
                id_suppr = st.number_input("Sélectionnez l'ID du message à effacer :", min_value=0, max_value=len(df_global)-1, step=1)
                st.warning(f"⚠️ Attention : Vous allez retirer définitivement le message {df_global.iloc[id_suppr]['Type_Message_Fichier']} du {df_global.iloc[id_suppr]['Date_Saisie']}.")
                
                if st.button("🗑️ Confirmer la Suppression", use_container_width=True):
                    df_nettoye = df_global.drop(index=id_suppr)
                    df_nettoye.drop(columns=['ID']).to_csv(FICHIER_BDD, index=False)
                    st.success("💥 Message supprimé du registre avec succès.")
                    st.rerun()
        else:
            st.info("ℹ️ Aucun message enregistré pour le moment.")
