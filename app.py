import streamlit as st
import pandas as pd
from datetime import datetime, timedelta
import os
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from email.mime.base import MIMEBase
from email import encoders

# --- CONFIGURATION INITIALE & DESIGN GÉNÉRAL CORRIGÉ TRICOLORE ---
st.set_page_config(page_title="SODEXAM - Station de San Pedro", layout="wide", initial_sidebar_state="expanded")

st.markdown("""
    <style>
    /* 1. CORRECTION DU FOND ET DES FORMULAIRES */
    .stApp { background-color: #ffffff !important; color: #1f2937 !important; }
    
    /* Ajustement de la largeur des formulaires */
    [data-testid="stForm"] { max-width: 850px !important; margin: 0 auto !important; padding: 20px !important; }
    
    /* 2. CORRECTION DE LA BARRE LATÉRALE (Zone Jaune de Gauche) */
    [data-testid="stSidebar"] { background-color: #f3f4f6 !important; border-right: 3px solid #f97316 !important; }
    
    /* FORCE l'écriture des sous-menus à être en NOIR et en Cambria */
    [data-testid="stSidebar"] .stRadio div[role="radiogroup"] label p {
        font-family: 'Cambria', serif !important;
        font-size: 13px !important;
        font-weight: bold !important;
        color: #111827 !important; /* NOIR TRÈS FONCÉ INVERTI */
    }
    
    /* Ajustement des puces/boutons radio */
    [data-testid="stSidebar"] .stRadio div[role="radiogroup"] input[type="radio"] {
        border-color: #f97316 !important;
    }
    
    /* 3. CORRECTION DU BOUTON VALIDATION (Zone Jaune du Bas) */
    div.stButton > button {
        background-color: #f97316 !important; 
        border-radius: 8px !important; 
        border: none !important; 
        padding: 10px 24px !important;
    }
    
    /* FORCE le texte à l'intérieur du bouton à s'écrire en BLANC */
    div.stButton > button p {
        color: #ffffff !important; /* BLANC ÉCLATANT */
        font-weight: bold !important;
        font-size: 14px !important;
    }
    
    /* Effet au survol de la souris */
    div.stButton > button:hover { background-color: #ea580c !important; }
    div.stButton > button:hover p { color: #ffffff !important; }
    
    /* Style pour les messages de succès (Vert) */
    .stAlert { border-left-color: #16a34a !important; background-color: #f0fdf4 !important; }
    </style>
""", unsafe_allow_html=True)


MOT_DE_PASSE_REQUIS = "sanpedro2026"
FICHIER_BDD = "donnees_meteo_sanpedro.csv"

# =========================================================================
# 🎛️ CONFIGURATION DU SERVEUR DE MESSAGERIE SODEXAM
# =========================================================================
SMTP_SERVEUR = "://office365.com"  
SMTP_PORT = 587
COMPTE_MAIL_STATION = "meteo.sanpedro@sodexam.ci" 
COMPTE_MOT_DE_PASSE = "VotreMotDePasseIci"  

def envoyer_email_sodexam(sujet, corps, destinataires, fichier_joint=None):
    """Fonction sécurisée : tente l'envoi mais ne bloque jamais l'application"""
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
            st.warning(f"⚠️ Impossible de joindre le fichier à l'e-mail : {e}")
            return False

    try:
        serveur = smtplib.SMTP(SMTP_SERVEUR, SMTP_PORT, timeout=5)
        serveur.starttls()
        serveur.login(COMPTE_MAIL_STATION, COMPTE_MOT_DE_PASSE)
        serveur.sendmail(COMPTE_MAIL_STATION, tous_les_destinataires, msg.as_string())
        serveur.quit()
        return True
    except Exception as e:
        st.warning(f"📢 Connexion réseau impossible pour le courriel ({e}).")
        st.info("ℹ️ Données sauvegardées localement sur la machine de la station.")
        return False

# --- CRÉATION DE LA BASE DE DONNÉES ---
if not os.path.exists(FICHIER_BDD):
    colonnes = ["Date_Saisie", "Date_Donnees", "Mois", "Annee", "Agent", "Categorie", "Type_Message_Fichier", "Heure_Saisie", "Statut_Delai", "Details"]
    df_init = pd.DataFrame(columns=colonnes)
    df_init.to_csv(FICHIER_BDD, index=False)

# --- SÉCURITÉ CONNEXION ---
if "authentifie" not in st.session_state:
    st.session_state["authentifie"] = False

if not st.session_state["authentifie"]:
    col_gauche, col_centre, col_droite = st.columns(3)
    with col_centre:
        st.markdown("<br><br>", unsafe_allow_html=True)
        if os.path.exists("logo_sodexam.png"):
            st.image("logo_sodexam.png", use_container_width=True)
        else:
            st.markdown("<h1 style='text-align: center; color: #f97316;'>🏢 SODEXAM</h1>", unsafe_allow_html=True)
            
        st.markdown("<h3 style='text-align: center; color: #16a34a;'>Station de San Pedro</h3>", unsafe_allow_html=True)
        st.markdown("---")
        mdp_saisi = st.text_input("🔑 Entrez le code d'accès de la station :", type="password")
        if st.button("Se connecter à l'application", use_container_width=True):
            if mdp_saisi == MOT_DE_PASSE_REQUIS:
                st.session_state["authentifie"] = True
                st.rerun()
            else:
                st.error("❌ Mot de passe incorrect")
else:
    # --- NAVIGATION PRINCIPALE PAR SOUS-MENUS ---
    st.sidebar.markdown("<h2 style='color:#f97316; margin-bottom:0;'>🏢 SODEXAM</h2><p style='color:#16a34a; font-weight:bold; margin-top:0;'>Station de San Pedro</p>", unsafe_allow_html=True)
    
    liste_agents = ["Dalo Clement", "Dao lea", "Adoh Bouet", "Koffi Gisele", "Djagba Aka", "Ote Armande"]
    agent_actif = st.sidebar.selectbox("👨‍💼 Agent de service :", liste_agents)
    
    st.sidebar.markdown("---")
    st.sidebar.markdown("<p style='font-weight:bold; color:#f97316; font-size:13px;'>🗂️ SOUS-MENUS DE TRANSMISSION</p>", unsafe_allow_html=True)
    choix_menu = st.sidebar.radio(
        "Sélectionnez votre tâche :",
        [
            "📡 SYNOP & METAR",
            "🌡️ Données Extrêmes",
            "🛠️ Point Instrument & Correction",
            "🌱 AGROMET & CLIMAT",
            "📂 Tableau Climatologique (TCM)",
            "📈 Tableau de bord & Statistiques"
        ]
    )

    maintenant = datetime.now()
    date_saisie = maintenant.strftime("%Y-%m-%d")

    # --- SOUS-MENU 1 : SYNOP & METAR ---
    if choix_menu == "📡 SYNOP & METAR":
        st.subheader("📡 Transmission des Messages Réguliers (SYNOP / METAR)")
        with st.form("form_synop_metar"):
            type_msg = st.selectbox("Type de message :", ["SYNOP Horaire", "SYNOP Principal", "METAR", "METREPORT", "SPECI"])
            heure_saisie = st.time_input("Heure réelle d'envoi :", maintenant.time())
            corps_msg = st.text_area("Texte réglementaire du message :", height=150)
            
            if st.form_submit_button("🚀 Valider et Acheminer"):
                statut = "Transmis dans le délai" if heure_saisie.minute <= 5 else "Transmis hors délai"
                
                df = pd.read_csv(FICHIER_BDD)
                nouvelle_ligne = {
                    "Date_Saisie": date_saisie, "Date_Donnees": date_saisie, "Mois": maintenant.strftime("%B"), "Annee": maintenant.strftime("%Y"),
                    "Agent": agent_actif, "Categorie": "SYNOP & METAR", "Type_Message_Fichier": type_msg, "Heure_Saisie": heure_saisie.strftime("%H:%M"),
                    "Statut_Delai": statut, "Details": corps_msg
                }
                pd.concat([df, pd.DataFrame([nouvelle_ligne])], ignore_index=True).to_csv(FICHIER_BDD, index=False)
                st.success(f"💾 Données enregistrées en local ! Statut : **{statut}**")
                
                sujet_mail = f"[{type_msg}] Station San Pedro - {date_saisie}"
                destins = ["beta@sodexam.ci"]
                if envoyer_email_sodexam(sujet_mail, corps_msg, destins):
                    st.success("✉️ E-mail transmis avec succès à Beta.")

        # --- SOUS-MENU 2 : DONNÉES EXTRÊMES ---
    elif choix_menu == "🌡️ Données Extrêmes":
        st.subheader("🌡️ Saisie des Données Extrêmes (H+24 à 06h00)")
        st.info("Rappel : Les données extrêmes de la veille doivent être envoyées le lendemain entre 06h00 et 08h00 au plus tard.")
        with st.form("form_extremes"):
            heure_saisie = st.time_input("Heure réelle d'envoi :", maintenant.time())
            t_max = st.number_input("Température Maximale (T MAXI) en °C :", value=28.0, step=0.1)
            t_min = st.number_input("Température Minimale (T MINI) en °C :", value=22.0, step=0.1)
            pluie = st.number_input("Quantité de pluie (P) en mm :", value=0.0, step=0.1)
            
            if st.form_submit_button("🚀 Enregistrer les Extrêmes"):
                date_donnees = (maintenant - timedelta(days=1)).strftime("%Y-%m-%d")
                statut = "Transmis dans le délai" if (6 <= heure_saisie.hour < 8) or (heure_saisie.hour == 8 and heure_saisie.minute == 0) else "Transmis hors délai"
                
                # ÉTAPE 1 : TOUJOURS SAUVEGARDER EN LOCAL
                df = pd.read_csv(FICHIER_BDD)
                contenu_texte = f"Données du {date_donnees} | TMAX: {t_max}°C | TMIN: {t_min}°C | Pluie: {pluie}mm"
                nouvelle_ligne = {
                    "Date_Saisie": date_saisie, 
                    "Date_Donnees": date_donnees, 
                    "Mois": maintenant.strftime("%B"), 
                    "Annee": maintenant.strftime("%Y"),
                    "Agent": agent_actif, 
                    "Categorie": "Données Extrêmes", 
                    "Type_Message_Fichier": "DONNEES EXTREMES", 
                    "Heure_Saisie": heure_saisie.strftime("%H:%M"),
                    "Statut_Delai": statut, 
                    "Details": contenu_texte
                }
                pd.concat([df, pd.DataFrame([nouvelle_ligne])], ignore_index=True).to_csv(FICHIER_BDD, index=False)
                st.success(f"💾 Données du {date_donnees} enregistrées en local ! Statut : **{statut}**")
                
                # ÉTAPE 2 : TENTER L'ENVOI EMAIL
                sujet_mail = f"[DONNEES EXTREMES] Station San Pedro - Obs du {date_donnees}"
                destins = ["service.prevision@sodexam.com"]
                if envoyer_email_sodexam(sujet_mail, contenu_texte, destins):
                    st.success("✉️ E-mail transmis avec succès au Service Prévision.")

    # --- SOUS-MENU 3 : POINT INSTRUMENT & CORRECTION ---
    elif choix_menu == "🛠️ Point Instrument & Correction":
        st.subheader("🛠️ Point Hebdomadaire des Instruments et Chiffrement")
        with st.form("form_instruments"):
            fichier_word = st.file_uploader("Téléverser le rapport d'instrumentation ou de chiffrement (Fichier Word) :", type=["docx", "doc"])
            commentaires = st.text_area("Notes ou détails des corrections de messages :")
            
            if st.form_submit_button("🚀 Envoyer le Rapport Hebdomadaire"):
                if fichier_word is not None:
                    df = pd.read_csv(FICHIER_BDD)
                    nouvelle_ligne = {
                        "Date_Saisie": date_saisie, "Date_Donnees": date_saisie, "Mois": maintenant.strftime("%B"), "Annee": maintenant.strftime("%Y"),
                        "Agent": agent_actif, "Categorie": "Instruments", "Type_Message_Fichier": "Rapport WORD", "Heure_Saisie": maintenant.strftime("%H:%M"),
                        "Statut_Delai": "Transmis", "Details": f"Fichier: {fichier_word.name} | Notes: {commentaires}"
                    }
                    pd.concat([df, pd.DataFrame([nouvelle_ligne])], ignore_index=True).to_csv(FICHIER_BDD, index=False)
                    st.success(f"💾 Rapport enregistré localement.")
                    
                    sujet_mail = f"[INSTRUMENTS/CHIFFREMENT] Point Hebdo - Station San Pedro"
                    corps_mail = f"Bonjour,\nVeuillez trouver ci-joint le point hebdomadaire des instruments et chiffrement.\nNotes: {commentaires}"
                    destins = ["alain.gnayoro@sodexam.ci"]
                    if envoyer_email_sodexam(sujet_mail, corps_mail, destins, fichier_joint=fichier_word):
                        st.success(f"✉️ Fichier '{fichier_word.name}' transmis à Alain Gnayoro.")
                else:
                    st.warning("Veuillez joindre le fichier Word avant de valider.")

    # --- SOUS-MENU 4 : AGROMET & CLIMAT ---
    elif choix_menu == "🌱 AGROMET & CLIMAT":
        st.subheader("🌱 Rapports Décadaires AGROMET & Mensuels CLIMAT")
        st.info("Rappels : AGROMET attendu les 1, 11, 21 avant 09h00. CLIMAT attendu au plus tard le 4 du mois.")
        with st.form("form_agromet_climat"):
            type_clima = st.selectbox("Type de rapport :", ["AGROMET (Décadaire)", "CLIMAT (Mensuel)"])
            heure_saisie = st.time_input("Heure réelle d'envoi :", maintenant.time())
            corps_clima = st.text_area("Contenu textuel du message :", height=150)
            
            if st.form_submit_button("🚀 Transmettre le Rapport"):
                jour = maintenant.day
                statut = "Transmis dans le délai"
                
                if type_clima == "AGROMET (Décadaire)":
                    if (jour not in 1,11,21) or (heure_saisie.hour >= 9):
                        statut = "Transmis hors délai"
                elif type_clima == "CLIMAT (Mensuel)" and jour > 4:
                    statut = "Transmis hors délai"
                    
                df = pd.read_csv(FICHIER_BDD)
                nouvelle_ligne = {
                    "Date_Saisie": date_saisie, "Date_Donnees": date_saisie, "Mois": maintenant.strftime("%B"), "Annee": maintenant.strftime("%Y"),
                    "Agent": agent_actif, "Categorie": "Agromet/Climat", "Type_Message_Fichier": type_clima, "Heure_Saisie": heure_saisie.strftime("%H:%M"),
                    "Statut_Delai": statut, "Details": corps_clima
                }
                pd.concat([df, pd.DataFrame([nouvelle_ligne])], ignore_index=True).to_csv(FICHIER_BDD, index=False)
                st.success(f"💾 Rapport '{type_clima}' enregistré avec succès en local ! Statut : **{statut}**")
                
                sujet_mail = f"[{type_clima}] Rapport Station San Pedro - {date_saisie}"
                destins = ["augustin.mian@sodexam.ci"]
                if envoyer_email_sodexam(sujet_mail, corps_clima, destins):
                    st.success("✉️ E-mail transmis avec succès à Augustin Mian.")

    # --- SOUS-MENU 5 : TABLEAU CLIMATOLOGIQUE (TCM) ---
    elif choix_menu == "📂 Tableau Climatologique (TCM)":
        st.subheader("📂 Expédition du Fichier Excel TCM Renseigné à Part")
        st.markdown("Importez votre fichier Excel externe compilé pour l'envoyer à la fin de la décade.")
        
        with st.form("form_tcm"):
            fichier_excel_tcm = st.file_uploader("Sélectionnez votre classeur Excel TCM :", type=["xlsx", "xls"])
            
            if st.form_submit_button("📨 Acheminer le fichier Excel TCM"):
                if fichier_excel_tcm is not None:
                    df = pd.read_csv(FICHIER_BDD)
                    nouvelle_ligne = {
                        "Date_Saisie": date_saisie, "Date_Donnees": date_saisie, "Mois": maintenant.strftime("%B"), "Annee": maintenant.strftime("%Y"),
                        "Agent": agent_actif, "Categorie": "TCM", "Type_Message_Fichier": "Fichier Excel TCM", "Heure_Saisie": maintenant.strftime("%H:%M"),
                        "Statut_Delai": "Transmis", "Details": f"Fichier TCM: {fichier_excel_tcm.name}"
                    }
                    pd.concat([df, pd.DataFrame([nouvelle_ligne])], ignore_index=True).to_csv(FICHIER_BDD, index=False)
                    st.success(f"💾 Enregistrement local effectué.")
                    
                    sujet_mail = f"[TCM EXCEL] Expédition Décadaire/Mensuelle - San Pedro"
                    corps_mail = f"Bonjour,\nVeuillez trouver ci-joint le classeur Excel du Tableau Climatologique Mensuel (TCM) de San Pedro."
                    destins = ["juliette.assi@sodexam.ci"]
                    if envoyer_email_sodexam(sujet_mail, corps_mail, destins, fichier_joint=fichier_excel_tcm):
                        st.success(f"✉️ Classeur Excel '{fichier_excel_tcm.name}' transmis à Juliette Assi.")
                else:
                    st.warning("Veuillez charger un fichier Excel valide.")

    # --- SOUS-MENU 6 : STATISTIQUES GLOBALES ---
    elif choix_menu == "📈 Tableau de bord & Statistiques":
        st.subheader("📊 Tableau de Bord Mensuel et Annuel de la Station")
        df_stats = pd.read_csv(FICHIER_BDD)
        
        if not df_stats.empty:
            col_f1, col_f2 = st.columns(2)
            with col_f1:
                annee_sel = st.selectbox("Sélectionnez l'Année :", sorted(df_stats['Annee'].unique().tolist()))
            with col_f2:
                mois_sel = st.selectbox("Sélectionnez le Mois :", ["Tous"] + sorted(df_stats[df_stats['Annee'] == annee_sel]['Mois'].unique().tolist()))
            
            df_filtre = df_stats[df_stats['Annee'] == annee_sel]
            if mois_sel != "Tous":
                df_filtre = df_filtre[df_filtre['Mois'] == mois_sel]
                
            kpi1, kpi2, kpi3 = st.columns(3)
            with kpi1:
                st.markdown(f'<div class="kpi-box"><div class="kpi-title">Total Messages & Fichiers</div><div class="kpi-value">{len(df_filtre)}</div></div>', unsafe_allow_html=True)
            with kpi2:
                dans_delai = len(df_filtre[df_filtre['Statut_Delai'] == "Transmis dans le délai"])
                st.markdown(f'<div class="kpi-box" style="border-left-color: #16a34a;"><div class="kpi-title">Dans les Délais</div><div class="kpi-value">{dans_delai}</div></div>', unsafe_allow_html=True)
            with kpi3:
                hors_delai = len(df_filtre[df_filtre['Statut_Delai'] == "Transmis hors délai"])
                st.markdown(f'<div class="kpi-box" style="border-left-color: #f97316;"><div class="kpi-title">Hors Délais</div><div class="kpi-value">{hors_delai}</div></div>', unsafe_allow_html=True)
            
            st.markdown("### 📅 Synthèse Mensuelle de l'Activité")
            tab_croise = pd.crosstab(df_filtre['Type_Message_Fichier'], df_filtre['Mois'], margins=True, margins_name="Total Général")
            st.dataframe(tab_croise, use_container_width=True)
            
            col_g1, col_g2 = st.columns(2)
            with col_g1:
                st.markdown("**📈 Volumes par type de message/fichier**")
                st.bar_chart(df_filtre['Type_Message_Fichier'].value_counts())
            with col_g2:
                st.markdown("**📉 Répartition du respect des délais**")
                st.bar_chart(df_filtre['Statut_Delai'].value_counts())
                
            st.markdown("### 🗄️ Historique brut de la Base de Données")
            st.dataframe(df_filtre, use_container_width=True)
        else:
            st.info("Aucune donnée enregistrée pour le moment. Les statistiques apparaîtront après vos premières saisies.")
