import streamlit as st
import pandas as pd
from datetime import datetime, timedelta
import os

# --- CONFIGURATION INITIALE & DESIGN GÉNÉRAL TRICOLORE ---
st.set_page_config(page_title="QA/QC - Station de San Pedro", layout="wide", initial_sidebar_state="expanded")

st.markdown("""
    <style>
    .stApp { background-color: #ffffff !important; color: #1f2937 !important; }
    [data-testid="stForm"] { max-width: 850px !important; margin: 0 auto !important; padding: 20px !important; }
    
    div[data-testid="stTextInput"] input, div[data-testid="stTextArea"] textarea, div[data-testid="stNumberInput"] input {
        color: #111827 !important; background-color: #f3f4f6 !important; border: 2px solid #d1d5db !important;
    }
    
    div[data-testid="stMarkdownContainer"] p, label p {
        color: #111827 !important; font-family: 'Cambria', serif !important;
    }
    
    [data-testid="stSidebar"] { background-color: #f3f4f6 !important; border-right: 3px solid #f97316 !important; }
    [data-testid="stSidebar"] .stRadio div[role="radiogroup"] label p {
        font-family: 'Cambria', serif !important; font-size: 13px !important; font-weight: bold !important; color: #111827 !important;
    }
    [data-testid="stSidebar"] .stRadio div[role="radiogroup"] input[type="radio"] { border-color: #f97316 !important; }
    
    div.stButton > button { background-color: #f97316 !important; border-radius: 8px !important; border: none !important; padding: 10px 24px !important; }
    div.stButton > button p { color: #ffffff !important; font-weight: bold !important; font-size: 14px !important; }
    div.stButton > button:hover { background-color: #ea580c !important; }
    
    div[data-testid="stNotification"] { background-color: #f0fdf4 !important; border-left: 5px solid #16a34a !important; }
    .stAlert { background-color: #fff7ed !important; border-left: 5px solid #f97316 !important; }
    .stAlert p, .stAlert div, [data-testid="stNotification"] p { color: #1a1a1a !important; font-weight: 600 !important; font-size: 14px !important; }
    
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

# --- INITIALISATION COMPLÈTE ET SÉCURISÉE DES BASES DE DONNÉES ---
# Réinitialisation propre des colonnes pour éviter tout conflit d'ancienne version (KeyError)
colonnes_principales = ["Date_Saisie", "Heure_Saisie", "Date_Donnees", "Mois", "Annee", "Agent", "Categorie", "Type_Message_Fichier", "Heure_Transmission", "Statut_Delai", "Details"]

if os.path.exists(FICHIER_BDD):
    try:
        df_verif = pd.read_csv(FICHIER_BDD)
        # Si une colonne moderne est manquante, on recrée proprement le fichier pour purger les erreurs
        if "Heure_Transmission" not in df_verif.columns:
            pd.DataFrame(columns=colonnes_principales).to_csv(FICHIER_BDD, index=False)
    except:
        pd.DataFrame(columns=colonnes_principales).to_csv(FICHIER_BDD, index=False)
else:
    pd.DataFrame(columns=colonnes_principales).to_csv(FICHIER_BDD, index=False)

if not os.path.exists(FICHIER_AGENTS):
    pd.DataFrame(columns=["Date", "Agent", "Action", "Heure"]).to_csv(FICHIER_AGENTS, index=False)

if not os.path.exists(FICHIER_OBS):
    pd.DataFrame(columns=["Date", "Heure", "Agent", "Type_Observation", "Message_Concerne", "Raison_Retard_Ou_Qualite"]).to_csv(FICHIER_OBS, index=False)

# --- PROTECTION PAR MOT DE PASSE ---
if "authentifie" not in st.session_state:
    st.session_state["authentifie"] = False

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
            else:
                st.error("❌ Mot de passe incorrect")
else:
    # --- NAVIGATION PRINCIPALE PAR SOUS-MENUS ---
    st.sidebar.markdown("<h2 style='color:#f97316; margin-bottom:0;'>🏢 SODEXAM</h2><p style='color:#16a34a; font-weight:bold; margin-top:0;'>Station de San Pedro</p>", unsafe_allow_html=True)
    
    liste_agents = ["Dalo Clement", "Dao lea", "Adoh Bouet", "Koffi Gisele", "Djagba Aka", "Ote Armande"]
    agent_actif = st.sidebar.selectbox("👨‍💼 Agent de service :", liste_agents)
    
    st.sidebar.markdown("---")
    st.sidebar.markdown("<p style='font-weight:bold; color:#f97316; font-size:13px;'>🗂️ MENUS DE LA STATION</p>", unsafe_allow_html=True)
    choix_menu = st.sidebar.radio(
        "Sélectionnez votre tâche :",
        [
            "📡 SYNOP & METAR",
            "🌡️ Données Extrêmes",
            "🛠️ Point Instrument & Correction",
            "🌱 AGROMET & CLIMAT",
            "📂 Tableau Climatologique (TCM)",
            "⏰ Prise & Fin de Service",
            "📝 Qualité & Justifications Hors Délai",
            "📈 Tableau de bord & Décomptes"
        ]
    )

    maintenant = datetime.now()
    date_saisie = maintenant.strftime("%Y-%m-%d")
    heure_informatique = maintenant.strftime("%H:%M")

    # --- SOUS-MENU 1 : SYNOP & METAR ---
    if choix_menu == "📡 SYNOP & METAR":
        st.subheader("📡 Saisie des Messages Réguliers (SYNOP / METAR)")
        with st.form("form_synop_metar"):
            type_msg = st.selectbox("Type de message :", ["SYNOP Horaire", "SYNOP Principal", "METAR", "METREPORT", "SPECI"])
            heure_trans = st.time_input("⏱️ Heure réelle de transmission du message :", maintenant.time())
            corps_msg = st.text_area("Texte réglementaire du message :", height=150)
            
            if st.form_submit_button("🚀 Valider et Enregistrer"):
                # Qualification réglementaire basée sur l'Heure de Transmission saisie
                statut = "Transmis dans le délai" if heure_trans.minute <= 5 else "Transmis hors délai"
                
                df = pd.read_csv(FICHIER_BDD)
                nouvelle_ligne = {
                    "Date_Saisie": date_saisie, "Heure_Saisie": heure_informatique, "Date_Donnees": date_saisie,
                    "Mois": maintenant.strftime("%B"), "Annee": maintenant.strftime("%Y"), "Agent": agent_actif,
                    "Categorie": "SYNOP & METAR", "Type_Message_Fichier": type_msg, "Heure_Transmission": heure_trans.strftime("%H:%M"),
                    "Statut_Delai": statut, "Details": corps_msg
                }
                pd.concat([df, pd.DataFrame([nouvelle_ligne])], ignore_index=True).to_csv(FICHIER_BDD, index=False)
                st.success(f"💾 Message enregistré localement avec succès ! Statut qualifié : **{statut}**")

    # --- SOUS-MENU 2 : DONNÉES EXTRÊMES ---
    elif choix_menu == "🌡️ Données Extrêmes":
        st.subheader("🌡️ Saisie des Données Extrêmes")
        with st.form("form_extremes"):
            heure_trans = st.time_input("⏱️ Heure réelle de transmission du message :", maintenant.time())
            t_max = st.number_input("Température Maximale (T MAXI) en °C :", value=28.0, step=0.1)
            t_min = st.number_input("Température Minimale (T MINI) en °C :", value=22.0, step=0.1)
            pluie = st.number_input("Quantité de pluie (P) en mm :", value=0.0, step=0.1)
            
            if st.form_submit_button("🚀 Enregistrer les Extrêmes"):
                date_donnees = (maintenant - timedelta(days=1)).strftime("%Y-%m-%d")
                # Entre 06h00 et 08h00 max
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
                st.success(f"💾 Données Extrêmes enregistrées localement ! Statut qualifié : **{statut}**")

    # --- SOUS-MENU 3 : POINT INSTRUMENT & CORRECTION ---
    elif choix_menu == "🛠️ Point Instrument & Correction":
        st.subheader("🛠️ Point Hebdomadaire des Instruments et Chiffrement")
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
                    st.success("💾 Rapport archivé localement avec succès.")
                else:
                    st.warning("Veuillez charger le fichier Word.")

    # --- SOUS-MENU 4 : AGROMET & CLIMAT ---
    elif choix_menu == "🌱 AGROMET & CLIMAT":
        st.subheader("🌱 Saisie des Rapports Décadaires AGROMET & Mensuels CLIMAT")
        with st.form("form_agromet_climat"):
            type_clima = st.selectbox("Type de rapport :", ["AGROMET (Décadaire)", "CLIMAT (Mensuel)"])
            heure_trans = st.time_input("⏱️ Heure réelle de transmission du message :", maintenant.time())
            corps_clima = st.text_area("Contenu textuel du message :", height=150)
            
            if st.form_submit_button("🚀 Transmettre le Rapport"):
                jour = maintenant.day
                statut = "Transmis dans le délai"
                
                # Sécurisation réglementaire des conditions temporelles (AGROMET décades 1, 11, 21 avant 09h00)
                if type_clima == "AGROMET (Décadaire)":
                    if (jour not in 1,11,21) or (heure_trans.hour >= 9):
                        statut = "Transmis hors délai"
                elif type_clima == "CLIMAT (Mensuel)" and jour > 4:
                    statut = "Transmis hors délai"
                    
                df = pd.read_csv(FICHIER_BDD)
                nouvelle_ligne = {
                    "Date_Saisie": date_saisie, "Heure_Saisie": heure_informatique, "Date_Donnees": date_saisie,
                    "Mois": maintenant.strftime("%B"), "Annee": maintenant.strftime("%Y"), "Agent": agent_actif,
                    "Categorie": "Agromet/Climat", "Type_Message_Fichier": type_clima, "Heure_Transmission": heure_trans.strftime("%H:%M"),
                    "Statut_Delai": statut, "Details": corps_clima
                }
                pd.concat([df, pd.DataFrame([nouvelle_ligne])], ignore_index=True).to_csv(FICHIER_BDD, index=False)
                st.success(f"💾 Rapport '{type_clima}' enregistré ! Statut qualifié : **{statut}**")

    # --- SOUS-MENU 5 : TABLEAU CLIMATOLOGIQUE (TCM) ---
    elif choix_menu == "📂 Tableau Climatologique (TCM)":
        st.subheader("📂 Suivi du Fichier Excel TCM Renseigné à Part")
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
                    st.success(f"💾 Fichier Excel '{fichier_excel_tcm.name}' enregistré localement dans la base.")
                else:
                    st.warning("Veuillez charger un fichier Excel valide.")

    # --- SOUS-MENU 6 : PRISE & FIN DE SERVICE ---
    elif choix_menu == "⏰ Prise & Fin de Service":
        st.subheader("⏰ Enregistrement des Heures de Prise et Fin de Service (Montée / Descente)")
        with st.form("form_presence"):
            action = st.radio("Action à effectuer :", ["Prise de service (Montée)", "Fin de service (Descente)"])
            heure_action = st.time_input("Heure officielle de l'action :", maintenant.time())
            
            if st.form_submit_button("💾 Valider l'heure de présence"):
                df_p = pd.read_csv(FICHIER_AGENTS)
                nouvelle_p = {"Date": date_saisie, "Agent": agent_actif, "Action": action, "Heure": heure_action.strftime("%H:%M")}
                pd.concat([df_p, pd.DataFrame([nouvelle_p])], ignore_index=True).to_csv(FICHIER_AGENTS, index=False)
                st.success(f"✅ Présence enregistrée pour {agent_actif}.")
        
        st.markdown("### 📅 Registre des présences du jour")
        df_p_lecture = pd.read_csv(FICHIER_AGENTS)
        st.dataframe(df_p_lecture[df_p_lecture["Date"] == date_saisie], use_container_width=True)

    # --- SOUS-MENU 7 : QUALITÉ & JUSTIFICATIONS ---
    elif choix_menu == "📝 Qualité & Justifications Hors Délai":
        st.subheader("📝 Cahier d'Observations, Qualité et Raisons des Hors Délais / Manquants")
        with st.form("form_obs"):
            type_obs = st.selectbox("Nature de l'observation :", ["Raison de transmission Hors Délai", "Message non transmis (Manquant)", "Note sur la Qualité / Erreur de chiffrement", "Panne d'instrument / Coupure Internet"])
            msg_concerne = st.text_input("Message concerné (Ex: SYNOP 12h, METAR 07h30) :")
            explications = st.text_area("Description détaillée des raisons :")
            
            if st.form_submit_button("🚀 Enregistrer l'observation"):
                df_o = pd.read_csv(FICHIER_OBS)
                nouvelle_o = {
                    "Date": date_saisie, "Heure": heure_informatique, "Agent": agent_actif,
                    "Type_Observation": type_obs, "Message_Concerne": msg_concerne, "Raison_Retard_Ou_Qualite": explications
                }
                pd.concat([df_o, pd.DataFrame([nouvelle_o])], ignore_index=True).to_csv(FICHIER_OBS, index=False)
                st.success("💾 Observation officiellement consignée dans le registre.")
        
        st.markdown("### 🗂️ Historique des observations de la station")
        st.dataframe(pd.read_csv(FICHIER_OBS), use_container_width=True)

    # --- SOUS-MENU 8 : TABLEAU DE BORD & RENDEMENT ---
    elif choix_menu == "📈 Tableau de bord & Décomptes":
        st.subheader("📊 Tableau de Bord Réglementaire & Rendement des Transmissions")
        df_stats = pd.read_csv(FICHIER_BDD)
        
        # FILTRES EN HAUT
        col_t1, col_t2, col_t3 = st.columns(3)
        with col_t1:
            periode_filtre = st.selectbox("⏳ Échelle temporelle à analyser :", ["Journalier (Aujourd'hui)", "Mensuel (Mois en cours)", "Annuel (Année en cours)"])
        with col_t2:
            type_msg_filtre = st.selectbox("📡 Filtrer par Type de Message :", ["Tous", "SYNOP Horaire", "SYNOP Principal", "METAR", "METREPORT", "SPECI"])
        with col_t3:
            str_annee = maintenant.strftime("%Y")
            st.markdown(f"<p style='margin-top:25px; font-weight:bold; color:#f97316;'>📅 Date Saisie : {date_saisie} | Heure : {heure_informatique}</p>", unsafe_allow_html=True)

        # LOGIQUE DE TRITEMENT ET DE FILTRAGE DES DONNÉES
        if not df_stats.empty:
            if "Journalier" in periode_filtre:
                df_temp = df_stats[df_stats["Date_Saisie"] == date_saisie]
                facteur_jours = 1
            elif "Mensuel" in periode_filtre:
                df_temp = df_stats[(df_stats["Mois"] == maintenant.strftime("%B")) & (df_stats["Annee"] == str_annee)]
                facteur_jours = maintenant.day
            else:
                df_temp = df_stats[df_stats["Annee"] == str_annee]
                facteur_jours = maintenant.timetuple().tm_yday
                
            if type_msg_filtre != "Tous":
                df_final = df_temp[df_temp["Type_Message_Fichier"] == type_msg_filtre]
            else:
                df_final = df_temp
        else:
            df_final = pd.DataFrame()
            facteur_jours = 1

        # QUOTAS RÉGLEMENTAIRES SODEXAM
        quotas_par_jour = {"SYNOP Horaire": 24, "SYNOP Principal": 8, "METAR": 14, "METREPORT": 14, "SPECI": 0}
        
        if type_msg_filtre != "Tous":
            attendus = quotas_par_jour.get(type_msg_filtre, 0) * facteur_jours
        else:
            attendus = sum([quotas_par_jour["SYNOP Horaire"], quotas_par_jour["SYNOP Principal"], quotas_par_jour["METAR"], quotas_par_jour["METREPORT"]]) * facteur_jours

        transmis = len(df_final)
        dans_delai = len(df_final[df_final["Statut_Delai"] == "Transmis dans le délai"]) if not df_final.empty else 0
        hors_delai = len(df_final[df_final["Statut_Delai"] == "Transmis hors délai"]) if not df_final.empty else 0
        
        if type_msg_filtre == "SPECI":
            non_transmis = 0
            taux_rendement = 100.0 if transmis > 0 else 0.0
        else:
            non_transmis = max(0, attendus - transmis)
            taux_rendement = (dans_delai / attendus) * 100 if attendus > 0 else 0.0

        # AFFICHAGE DES VALEURS (KPI)
        st.markdown(f"#### 📈 Indicateurs : **{periode_filtre}** | Message : **{type_msg_filtre}**")
        k1, k2, k3, k4, k5 = st.columns(5)
        with k1: st.markdown(f'<div class="kpi-box"><div class="kpi-title">📋 Attendus</div><div class="kpi-value">{attendus}</div></div>', unsafe_allow_html=True)
        with k2: st.markdown(f'<div class="kpi-box" style="border-top-color: #3b82f6;"><div class="kpi-title">📤 Transmis</div><div class="kpi-value">{transmis}</div></div>', unsafe_allow_html=True)
        with k3: st.markdown(f'<div class="kpi-box" style="border-top-color: #16a34a;"><div class="kpi-title">⏱️ Dans les Délais</div><div class="kpi-value">{dans_delai}</div></div>', unsafe_allow_html=True)
        with k4: st.markdown(f'<div class="kpi-box" style="border-top-color: #f97316;"><div class="kpi-title">⚠️ Hors Délais</div><div class="kpi-value">{hors_delai}</div></div>', unsafe_allow_html=True)
        with k5:
            couleur_manquant = "#ef4444" if non_transmis > 0 else "#6b7280"
            st.markdown(f'<div class="kpi-box" style="border-top-color: {couleur_manquant};"><div class="kpi-title">❌ Non Transmis</div><div class="kpi-value">{non_transmis}</div></div>', unsafe_allow_html=True)

        st.markdown("<br>", unsafe_allow_html=True)
        couleur_rendement = "#16a34a" if taux_rendement >= 85 else ("#f97316" if taux_rendement >= 50 else "#ef4444")
        st.markdown(f"""
            <div style='background-color: #f9fafb; padding: 20px; border-radius: 10px; text-align: center; border: 1px solid #e5e7eb; border-left: 6px solid {couleur_rendement};'>
                <p style='margin:0; font-size:14px; text-transform:uppercase; font-weight:bold; color:#6b7280;'>🎯 Taux de Rendement Réglementaire Global</p>
                <p style='margin:5px 0 0 0; font-size:36px; font-weight:bold; color:{couleur_rendement};'>{taux_rendement:.1f} %</p>
                <small style='color:#9ca3af;'>Formule : (Transmis dans les Délais / Attendus Réglementaires) × 100</small>
            </div>
        """, unsafe_allow_html=True)

        st.markdown("---")
        if not df_final.empty:
            st.markdown("### 🗂️ Tableau récapitulatif complet de l'activité (Tri temporel appliqué)")
            st.dataframe(df_final[["Date_Saisie", "Heure_Saisie", "Agent", "Type_Message_Fichier", "Heure_Transmission", "Statut_Delai", "Details"]], use_container_width=True)
        else:
            st.info("ℹ️ Aucun message enregistré ne correspond à ce filtre pour le moment.")
