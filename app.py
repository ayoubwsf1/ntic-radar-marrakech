# ==============================================================================
# Fichier : app.py
# Rôle : Point d'entrée principal de l'application Streamlit.
#        C'est le fichier qu'on lance avec la commande : streamlit run app.py
#        Il coordonne toute l'interface : connexion, onglets, filtres et affichage.
# ==============================================================================

# Bibliothèque Streamlit pour créer l'interface web interactive
import streamlit as st

# Importer le module de gestion de la base de données SQLite
from stageradar import database
# Importer la liste des statuts de candidature
from stageradar.config import STATUTS
# Importer la fonction de filtrage du tableau
from stageradar.filters import appliquer_filtres
# Importer les composants d'en-tête (titre et indicateurs clés)
from stageradar.ui.header import render_header, render_kpis
# Importer la page de connexion Gmail
from stageradar.ui.login import render_login_page
# Importer la barre latérale avec les filtres
from stageradar.ui.sidebar import render_sidebar
# Importer les styles CSS personnalisés
from stageradar.ui.styles import CSS
# Importer tous les onglets de l'application
from stageradar.ui.tab_agences import render_tab_agences
from stageradar.ui.tab_carte import render_tab_carte
from stageradar.ui.tab_cv import render_tab_cv
from stageradar.ui.tab_dashboard import render_tab_dashboard
from stageradar.ui.tab_scan import render_tab_scan
from stageradar.ui.tab_suivi import render_tab_suivi

# Configuration globale de la page Streamlit (titre, icône, mise en page large)
st.set_page_config(
    page_title="Ntic Radar Marrakech",  # Titre affiché dans l'onglet du navigateur
    page_icon="🧭",                    
    layout="wide",                       # Mise en page large pour utiliser tout l'écran
    initial_sidebar_state="expanded"     # Barre latérale ouverte par défaut
)


# ------------------------------------------------------------------------------
# Fonction : _boot (démarrage initial avec cache)
# Rôle : Initialiser la base de données et importer les agences depuis Excel.
#        Cette fonction est mise en cache (@st.cache_resource) pour ne s'exécuter
#        qu'une seule fois au démarrage de l'application.
# ------------------------------------------------------------------------------
@st.cache_resource
def _boot() -> bool:
    # 1. Créer les tables SQLite si elles n'existent pas encore
    database.init_db()
    # 2. Synchroniser les agences depuis le fichier Excel vers SQLite
    database.sync_from_excel()
    return True


# ------------------------------------------------------------------------------
# Fonction principale : main
# Rôle : Coordonner toute l'application : connexion, chargement des données,
#        affichage des onglets et gestion de l'état de la session.
# ------------------------------------------------------------------------------
def main() -> None:
    # 1. Démarrer l'application (initialiser la base de données)
    _boot()

    # 2. Appliquer les styles CSS personnalisés (couleurs Marrakech, design moderne)
    st.markdown(CSS, unsafe_allow_html=True)

    # 3. Vérifier si l'utilisateur est connecté avec Gmail ou en mode démo
    if "gmail_user" not in st.session_state and not st.session_state.get("demo"):
        # Si pas encore connecté, afficher la page de connexion/démo
        render_login_page()
        return

    # 4. Charger toutes les agences depuis la base de données SQLite
    df_all = database.load_agences()

    # 5. Afficher la barre latérale (sidebar) et récupérer les filtres choisis
    filtres = render_sidebar(df_all, STATUTS)

    # 6. Recharger les agences (au cas où un ajout manuel a eu lieu dans la sidebar)
    df_all = database.load_agences()

    # 7. Appliquer les filtres sélectionnés (ville, type, statut, recherche texte)
    df = appliquer_filtres(df_all, filtres)

    # 8. Afficher l'en-tête de l'application (logo, titre, bouton de déconnexion)
    render_header(df_all)

    # 9. Afficher les indicateurs clés de performance (KPIs : nombre d'agences, etc.)
    render_kpis(df_all)

    # 10. Ajouter un espace vertical pour la lisibilité
    st.write("")

    # 11. Créer les 6 onglets principaux de l'application
    tabs = st.tabs(["Tableau de bord", "Agences", "Carte", "Suivi", "Mon CV", "Dernier scan"])

    # Onglet 1 : Tableau de bord (statistiques et graphiques)
    with tabs[0]:
        render_tab_dashboard(df_all)

    # Onglet 2 : Liste des agences (tableau détaillé avec recherche)
    with tabs[1]:
        render_tab_agences(df)

    # Onglet 3 : Carte interactive (visualisation géographique sur Marrakech)
    with tabs[2]:
        render_tab_carte(df)

    # Onglet 4 : Suivi des candidatures (progression par statut)
    with tabs[3]:
        render_tab_suivi(df_all)

    # Onglet 5 : Génération de CV avec l'IA
    with tabs[4]:
        render_tab_cv()

    # Onglet 6 : Résultat du dernier scan Gmail (e-mails détectés)
    with tabs[5]:
        render_tab_scan()


# Point d'entrée : lancer l'application quand le fichier est exécuté directement
if __name__ == "__main__":
    main()
