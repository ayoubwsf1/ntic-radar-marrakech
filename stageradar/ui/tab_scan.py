"""Onglet Scan : affiche le résultat du dernier scan des mails."""
import pandas as pd  # pour afficher le tableau
import streamlit as st  # pour afficher

from .helpers import wide  # pour un tableau qui prend toute la largeur


def _lignes_evenements(events: list) -> list[dict]:
    # Convertit les événements en lignes pour le tableau
    return [
        {
            "Date": e.date.strftime("%d/%m/%Y"), "Agence": e.agence, "Statut détecté": e.statut,
            "Sens": e.direction, "Correspondant": e.correspondant, "Objet": e.sujet, "Indice": e.indice,
        }
        for e in sorted(events, key=lambda e: e.date, reverse=True)  # tri du plus récent au plus ancien
    ]


def render_tab_scan() -> None:
    # Affiche le résultat du dernier scan
    ls = st.session_state.get("last_scan")  # le dernier résultat gardé en mémoire
    if not ls:  # si il n'y a pas encore de scan
        st.info("Aucun scan pour l'instant. Cliquez sur **Vérifier mes mails** dans la barre latérale.")  # message d'information
        return  # on arrête

    st.markdown(
        f"**{ls['when']}** · {ls['scanned']} mails analysés sur {ls['days']} jours · "
        f"dossiers : `{ls['folder']}` · **{ls['changes']}** changement(s) de statut"
    )  # le résumé du scan
    if not ls["events"]:  # si aucun mail n'a été relié à une agence
        st.warning("Aucun mail n'a pu être relié à une agence de la liste. Astuce : la détection se fait par nom de domaine du site ou par nom d'agence dans l'expéditeur/objet.")  # conseil
        return  # on arrête

    st.dataframe(pd.DataFrame(_lignes_evenements(ls["events"])), hide_index=True, **wide())  # le tableau des événements
    st.caption("La détection repose sur des mots-clés (FR/EN). Un statut avancé n'est jamais rétrogradé par un scan ultérieur.")  # petit texte d'aide
