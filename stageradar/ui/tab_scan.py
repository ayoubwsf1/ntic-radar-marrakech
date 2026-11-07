import pandas as pd
import streamlit as st

from .helpers import wide


def _lignes_evenements(events: list) -> list[dict]:
    return [
        {
            "Date": e.date.strftime("%d/%m/%Y"), "Agence": e.agence, "Statut détecté": e.statut,
            "Sens": e.direction, "Correspondant": e.correspondant, "Objet": e.sujet, "Indice": e.indice,
        }
        for e in sorted(events, key=lambda e: e.date, reverse=True)
    ]


def render_tab_scan() -> None:
    ls = st.session_state.get("last_scan")
    if not ls:
        st.info("Aucun scan pour l'instant. Cliquez sur **Vérifier mes mails** dans la barre latérale.")
        return

    st.markdown(
        f"**{ls['when']}** · {ls['scanned']} mails analysés sur {ls['days']} jours · "
        f"dossiers : `{ls['folder']}` · **{ls['changes']}** changement(s) de statut"
    )
    if not ls["events"]:
        st.warning("Aucun mail n'a pu être relié à une agence de la liste. Astuce : la détection se fait par nom de domaine du site ou par nom d'agence dans l'expéditeur/objet.")
        return

    st.dataframe(pd.DataFrame(_lignes_evenements(ls["events"])), hide_index=True, **wide())
    st.caption("La détection repose sur des mots-clés (FR/EN). Un statut avancé n'est jamais rétrogradé par un scan ultérieur.")
