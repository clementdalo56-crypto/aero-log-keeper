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
                    if (jour not in) or (heure_trans.hour >= 9):
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
        with k5: st.markdown(f'<div class="kpi-box" style="border-top-color: {"#ef4444" if non_transmis > 0 else "#6b7280"};"><div class="kpi-title">❌ Non Transmis</div><div class="kpi-value">{non_transmis}</div></div>', unsafe_allow_html=True)

        st.markdown("<br>", unsafe_allow_html=True)
        couleur_rendement = "#16a34a" if taux_rendement >= 85 else ("#f97316" if taux_rendement >= 50 else "#ef4444")
        st.markdown(f"<div style='background-color: #f9fafb; padding: 15px; border-radius: 10px; text-align: center; border-left: 6px solid {couleur_rendement};'><p style='margin:0; font-size:12px; font-weight:bold; color:#6b7280;'>🎯 TAUX DE RENDEMENT RÉGLEMENTAIRE GLOBAL</p><p style='margin:5px 0 0 0; font-size:32px; font-weight:bold; color:{couleur_rendement};'>{taux_rendement:.1f} %</p></div>", unsafe_allow_html=True)

        # =========================================================================
        # 🔐 PROTECTION ESPACE ADMINISTREUR - VERROUILLAGE DU TABLEAU BRUT
        # =========================================================================
        st.markdown("---")
        st.markdown("### 🗄️ Accès aux Registres Archivés de la Station")
        
        mode_admin = st.checkbox("🔑 Débloquer la consultation du tableau brut (Réservé à l'Administrateur)")
        
        if mode_admin:
            code_admin = st.text_input("Saisissez le mot de passe Administrateur :", type="password")
            if code_admin == MDP_ADMIN_REQUIS:
                st.success("🔓 Authentification Administrateur validée. Accès autorisé.")
                if not df_final.empty:
                    # Affiche le tableau uniquement si le mot de passe est validé
                    st.dataframe(df_final, use_container_width=True)
                else: 
                    st.info("Aucun enregistrement trouvé pour ce filtre.")
            elif code_admin != "":
                st.error("❌ Mot de passe Administrateur incorrect. Affichage masqué.")
        else:
            st.info("🔒 Le tableau récapitulatif brut est masqué pour les agents. Cochez la case ci-dessus pour vous connecter en tant qu'administrateur.")
