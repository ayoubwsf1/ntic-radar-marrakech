"""Onglet CV : profil → génération PDF (avec IA si clé dispo, sinon local)."""
import streamlit as st  # pour afficher les champs et les boutons

from ..ai.cv import cv_local, generer_cv  # pour générer le CV
from ..ai.llm import get_client  # pour avoir le client IA
from ..ai.profile import Profil, charger, parse_competences, sauver  # pour le profil de l'utilisateur
from ..config import CONTRATS, VILLE_CIBLE  # pour les types de candidature et la ville
from ..cv_render import cv_pdf, nom_fichier  # pour créer le fichier PDF
from .helpers import wide  # pour un bouton qui prend toute la largeur


# ─────────────────────────────────────── onglet profil ───────────────────────

def _profil() -> None:
    # Affiche le formulaire pour le profil de l'utilisateur
    p = charger()  # on charge le profil enregistré en base
    st.markdown("Ces informations alimentent votre CV. Elles restent dans votre base locale.")  # petit texte d'aide
    with st.form("profil_form"):  # un formulaire, pour ne sauvegarder qu'au clic sur le bouton
        c1, c2 = st.columns(2)  # deux colonnes
        nom    = c1.text_input("Nom complet", p.nom)  # le nom complet
        email  = c2.text_input("E-mail", p.email)  # l'adresse e-mail
        c1, c2 = st.columns(2)  # deux colonnes
        tel    = c1.text_input("Téléphone", p.telephone)  # le téléphone
        liens  = c2.text_input("Liens (LinkedIn, GitHub, portfolio…)", p.liens,  # les liens
                               placeholder="linkedin.com/in/…, github.com/…")
        formation = st.text_area(  # la formation, une par ligne
            "Formation (une par ligne)", p.formation, height=90,
            placeholder="Technicien spécialisé en développement digital, OFPPT Marrakech, 2024-2026\nBaccalauréat sciences, 2024",
        )
        comp = st.text_area(  # les compétences, séparées par des virgules
            "Compétences (séparées par des virgules)", ", ".join(p.competences), height=70,
            placeholder="Python, React, SQL, Photoshop, SEO…",
        )
        exp = st.text_area(
            "Expériences (blocs séparés par une ligne vide)", p.experiences, height=150,
            placeholder=(
                "Stagiaire développeur web — Agence X (juillet 2025)\n"
                "Intégration de maquettes en HTML/CSS\n"
                "Correction de bugs sur un site WordPress\n\n"
                "Vendeur saisonnier — Magasin Y (été 2024)\n"
                "Accueil et conseil clients"
            ),
        )
        proj = st.text_area(
            "Projets (blocs séparés par une ligne vide)", p.projets, height=110,
            placeholder="Ntic Radar Marrakech\nPlateforme Streamlit de suivi des candidatures",
        )
        interets = st.text_input("Centres d'intérêt", p.interets)  # les centres d'intérêt
        c1, c2, c3 = st.columns(3)  # trois colonnes
        type_stage = c1.selectbox(  # le type de candidature, dans une liste
            "Type de candidature", CONTRATS,
            index=CONTRATS.index(p.type_stage) if p.type_stage in CONTRATS else 0,
        )
        duree   = c2.text_input("Durée souhaitée", p.duree, placeholder="2 mois, à partir de juin")  # la durée
        langues = c3.text_input("Langues", p.langues)  # les langues parlées

        if st.form_submit_button("Enregistrer le profil", type="primary"):  # bouton pour sauvegarder
            sauver(Profil(
                nom=nom, email=email, telephone=tel, liens=liens, formation=formation,
                competences=parse_competences(comp), experiences=exp, projets=proj,
                interets=interets, type_stage=type_stage, duree=duree,
                langues=langues, ville=VILLE_CIBLE,
            ))
            st.success("Profil enregistré.")
            st.rerun()


# ─────────────────────────────────────── onglet génération ───────────────────

def _generer(llm) -> None:
    # Affiche le bouton pour générer le CV et l'aperçu
    p = charger()  # on charge le profil
    if p.vide:  # si le profil est vide
        st.warning("Renseignez d'abord votre profil (onglet « Mon profil »).")  # message d'avertissement
        return  # on arrête

    # bannière statut IA
    if llm.available:  # si l'IA est disponible
        st.success(f"IA active — le CV sera rédigé et amélioré par `{llm.model}`.")  # message de succès
    else:
        st.info("Sans clé **ANTHROPIC_API_KEY**, le CV est généré directement depuis votre profil (pas de reformulation).")  # message d'information

    langue = st.radio("Langue du CV", ["Français", "English"], horizontal=True)  # choix de la langue

    label_btn = "Générer mon CV avec l'IA" if llm.available else "Générer mon CV (PDF)"  # le texte du bouton

    if st.button(label_btn, type="primary", **wide()):  # bouton pour générer le CV
        if llm.available:  # si l'IA est disponible, elle rédige le CV
            with st.status("L'IA rédige votre CV…", expanded=True) as status:  # animation pendant la génération
                res = generer_cv(p, None, langue, llm, etape=lambda t: st.write(t))  # on génère le CV avec l'IA
                status.update(label="CV prêt ✅", state="complete", expanded=False)  # message quand c'est fini
            cv = res["cv"]  # le CV généré
            for alerte in res.get("alertes", []):  # pour chaque alerte de l'IA
                st.warning(alerte)  # on affiche l'alerte
        else:
            cv = cv_local(p)  # sans IA, on génère le CV directement depuis le profil

        cv.update({  # on ajoute les informations du profil au CV
            "nom":      p.nom,
            "email":    p.email,
            "telephone": p.telephone,
            "ville":    p.ville,
            "liens":    [x.strip() for x in (p.liens or "").split(",") if x.strip()],
            "langue":   langue,
        })
        st.session_state["cv_data"] = cv  # on garde le CV en mémoire

    cv = st.session_state.get("cv_data")  # on récupère le CV gardé en mémoire
    if not cv:  # si aucun CV n'a été généré
        return  # on arrête

    # bouton téléchargement
    st.download_button(  # bouton pour télécharger le PDF
        "Télécharger le CV (PDF)",
        cv_pdf(cv),
        nom_fichier(cv, "pdf"),
        mime="application/pdf",
        type="primary",
        **wide(),
    )

    # aperçu dans l'interface
    st.markdown("---")  # une ligne de séparation
    st.markdown("#### Aperçu")  # le titre de l'aperçu
    with st.container(border=True):  # une boîte avec une bordure
        col_info, col_comp = st.columns([3, 1])  # deux colonnes : infos et compétences

        with col_info:  # la colonne des informations
            st.markdown(f"## {cv.get('nom') or 'Candidat'}")  # le nom
            if cv.get("titre"):  # si il y a un titre
                st.markdown(f"**{cv['titre']}**")  # on affiche le titre
            contact = " · ".join(x for x in [  # on met les contacts ensemble
                cv.get("email"), cv.get("telephone"), cv.get("ville"),
                *(cv.get("liens") or []),
            ] if x)
            if contact:  # si il y a des contacts
                st.caption(contact)  # on affiche les contacts

            if cv.get("resume"):  # si il y a un résumé
                st.markdown("> " + cv["resume"])  # on affiche le résumé

            for titre, cle in (("Expériences", "experiences"), ("Projets", "projets")):  # pour les expériences et les projets
                if cv.get(cle):  # si il y en a
                    st.markdown(f"#### {titre}")  # le titre
                    for e in cv[cle]:  # pour chaque élément
                        tete = " — ".join(x for x in [  # le poste et l'organisation
                            e.get("poste") or e.get("nom"), e.get("organisation"),
                        ] if x)
                        periode = f" *· {e['periode']}*" if e.get("periode") else ""  # la période
                        st.markdown(f"**{tete}**{periode}")  # on affiche le poste et la période
                        for pt in (e.get("points") or []):  # pour chaque point
                            st.markdown(f"  - {pt}")  # on affiche le point

            if cv.get("formation"):  # si il y a une formation
                st.markdown("#### Formation")  # le titre
                for fo in cv["formation"]:  # pour chaque formation
                    det = f" — {fo['details']}" if fo.get("details") else ""  # les détails, si il y en a
                    st.markdown(f"- **{fo.get('intitule', '')}**{det}")  # on affiche la formation

        with col_comp:  # la colonne des compétences
            if cv.get("competences"):  # si il y a des compétences
                st.markdown("**Compétences**")  # le titre
                for skill in cv["competences"]:  # pour chaque compétence
                    st.markdown(  # on affiche la compétence dans une étiquette
                        f'<span style="display:inline-block;background:#dbeafe;color:#1e40af;'
                        f'padding:2px 8px;border-radius:12px;font-size:0.82em;margin:2px">'
                        f'{skill}</span>',
                        unsafe_allow_html=True,
                    )
            if cv.get("langues"):  # si il y a des langues
                st.markdown("**Langues**")  # le titre
                for lang in cv["langues"]:  # pour chaque langue
                    st.markdown(f"- {lang}")  # on affiche la langue
            if cv.get("interets"):  # si il y a des intérêts
                st.markdown("**Intérêts**")  # le titre
                st.caption(cv["interets"])  # on affiche les intérêts


# ─────────────────────────────────────── point d'entrée ──────────────────────

def render_tab_cv() -> None:
    # Affiche les deux onglets : profil et génération
    llm = get_client()  # on prend le client IA
    t1, t2 = st.tabs(["Mon profil", "Générer mon CV"])  # les deux onglets
    with t1:  # premier onglet
        _profil()  # le formulaire du profil
    with t2:  # deuxième onglet
        _generer(llm)  # la génération du CV
