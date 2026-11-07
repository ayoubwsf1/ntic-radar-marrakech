"""Onglet CV : profil → génération PDF (avec IA si clé dispo, sinon local)."""
import streamlit as st

from ..ai.cv import cv_local, generer_cv
from ..ai.llm import get_client
from ..ai.profile import Profil, charger, parse_competences, sauver
from ..config import CONTRATS, VILLE_CIBLE
from ..cv_render import cv_pdf, nom_fichier
from .helpers import wide


# ─────────────────────────────────────── onglet profil ───────────────────────

def _profil() -> None:
    p = charger()
    st.markdown("Ces informations alimentent votre CV. Elles restent dans votre base locale.")
    with st.form("profil_form"):
        c1, c2 = st.columns(2)
        nom    = c1.text_input("Nom complet", p.nom)
        email  = c2.text_input("E-mail", p.email)
        c1, c2 = st.columns(2)
        tel    = c1.text_input("Téléphone", p.telephone)
        liens  = c2.text_input("Liens (LinkedIn, GitHub, portfolio…)", p.liens,
                               placeholder="linkedin.com/in/…, github.com/…")
        formation = st.text_area(
            "Formation (une par ligne)", p.formation, height=90,
            placeholder="Technicien spécialisé en développement digital, OFPPT Marrakech, 2024-2026\nBaccalauréat sciences, 2024",
        )
        comp = st.text_area(
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
        interets = st.text_input("Centres d'intérêt", p.interets)
        c1, c2, c3 = st.columns(3)
        type_stage = c1.selectbox(
            "Type de candidature", CONTRATS,
            index=CONTRATS.index(p.type_stage) if p.type_stage in CONTRATS else 0,
        )
        duree   = c2.text_input("Durée souhaitée", p.duree, placeholder="2 mois, à partir de juin")
        langues = c3.text_input("Langues", p.langues)

        if st.form_submit_button("Enregistrer le profil", type="primary"):
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
    p = charger()
    if p.vide:
        st.warning("Renseignez d'abord votre profil (onglet « Mon profil »).")
        return

    # bannière statut IA
    if llm.available:
        st.success(f"IA active — le CV sera rédigé et amélioré par `{llm.model}`.")
    else:
        st.info("Sans clé **ANTHROPIC_API_KEY**, le CV est généré directement depuis votre profil (pas de reformulation).")

    langue = st.radio("Langue du CV", ["Français", "English"], horizontal=True)

    label_btn = "Générer mon CV avec l'IA" if llm.available else "Générer mon CV (PDF)"

    if st.button(label_btn, type="primary", **wide()):
        if llm.available:
            with st.status("L'IA rédige votre CV…", expanded=True) as status:
                res = generer_cv(p, None, langue, llm, etape=lambda t: st.write(t))
                status.update(label="CV prêt ✅", state="complete", expanded=False)
            cv = res["cv"]
            for alerte in res.get("alertes", []):
                st.warning(alerte)
        else:
            cv = cv_local(p)

        cv.update({
            "nom":      p.nom,
            "email":    p.email,
            "telephone": p.telephone,
            "ville":    p.ville,
            "liens":    [x.strip() for x in (p.liens or "").split(",") if x.strip()],
            "langue":   langue,
        })
        st.session_state["cv_data"] = cv

    cv = st.session_state.get("cv_data")
    if not cv:
        return

    # bouton téléchargement
    st.download_button(
        "Télécharger le CV (PDF)",
        cv_pdf(cv),
        nom_fichier(cv, "pdf"),
        mime="application/pdf",
        type="primary",
        **wide(),
    )

    # aperçu dans l'interface
    st.markdown("---")
    st.markdown("#### Aperçu")
    with st.container(border=True):
        col_info, col_comp = st.columns([3, 1])

        with col_info:
            st.markdown(f"## {cv.get('nom') or 'Candidat'}")
            if cv.get("titre"):
                st.markdown(f"**{cv['titre']}**")
            contact = " · ".join(x for x in [
                cv.get("email"), cv.get("telephone"), cv.get("ville"),
                *(cv.get("liens") or []),
            ] if x)
            if contact:
                st.caption(contact)

            if cv.get("resume"):
                st.markdown("> " + cv["resume"])

            for titre, cle in (("Expériences", "experiences"), ("Projets", "projets")):
                if cv.get(cle):
                    st.markdown(f"#### {titre}")
                    for e in cv[cle]:
                        tete = " — ".join(x for x in [
                            e.get("poste") or e.get("nom"), e.get("organisation"),
                        ] if x)
                        periode = f" *· {e['periode']}*" if e.get("periode") else ""
                        st.markdown(f"**{tete}**{periode}")
                        for pt in (e.get("points") or []):
                            st.markdown(f"  - {pt}")

            if cv.get("formation"):
                st.markdown("#### Formation")
                for fo in cv["formation"]:
                    det = f" — {fo['details']}" if fo.get("details") else ""
                    st.markdown(f"- **{fo.get('intitule', '')}**{det}")

        with col_comp:
            if cv.get("competences"):
                st.markdown("**Compétences**")
                for skill in cv["competences"]:
                    st.markdown(
                        f'<span style="display:inline-block;background:#dbeafe;color:#1e40af;'
                        f'padding:2px 8px;border-radius:12px;font-size:0.82em;margin:2px">'
                        f'{skill}</span>',
                        unsafe_allow_html=True,
                    )
            if cv.get("langues"):
                st.markdown("**Langues**")
                for lang in cv["langues"]:
                    st.markdown(f"- {lang}")
            if cv.get("interets"):
                st.markdown("**Intérêts**")
                st.caption(cv["interets"])


# ─────────────────────────────────────── point d'entrée ──────────────────────

def render_tab_cv() -> None:
    llm = get_client()
    t1, t2 = st.tabs(["Mon profil", "Générer mon CV"])
    with t1:
        _profil()
    with t2:
        _generer(llm)
