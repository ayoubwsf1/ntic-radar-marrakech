"""Génère la présentation PowerPoint officielle pour le projet Ntic Radar Marrakech.
Respecte les 12 points obligatoires demandés par l'encadrant(e).
"""
import sys
from pathlib import Path
from pptx import Presentation
from pptx.util import Inches, Pt
from pptx.dml.color import RGBColor
from pptx.enum.text import PP_ALIGN
from pptx.enum.shapes import MSO_SHAPE

BASE_DIR = Path(__file__).resolve().parent.parent
FIG_DIR = BASE_DIR / "docs" / "figures"

# Couleurs du thème
COLOR_BG = RGBColor(15, 23, 42)       # Slate 900
COLOR_PRIMARY = RGBColor(59, 130, 246) # Blue 500
COLOR_TEXT_WHITE = RGBColor(255, 255, 255)
COLOR_TEXT_DARK = RGBColor(30, 41, 59)
COLOR_MUTED = RGBColor(100, 116, 139)
COLOR_CARD_BG = RGBColor(241, 245, 249)
COLOR_ACCENT = RGBColor(184, 80, 66)   # #B85042


def create_slide_title(prs, title_text, subtitle_text=""):
    slide_layout = prs.slide_layouts[6] # blank
    slide = prs.slides.add_slide(slide_layout)

    # Header banner
    top_bar = slide.shapes.add_shape(MSO_SHAPE.RECTANGLE, 0, 0, Inches(13.333), Inches(1.1))
    top_bar.fill.solid()
    top_bar.fill.fore_color.rgb = COLOR_BG
    top_bar.line.fill.background()

    # Title text
    txBox = slide.shapes.add_textbox(Inches(0.8), Inches(0.15), Inches(11.7), Inches(0.8))
    tf = txBox.text_frame
    tf.word_wrap = True
    p = tf.paragraphs[0]
    p.text = title_text
    p.font.size = Pt(26)
    p.font.bold = True
    p.font.color.rgb = COLOR_TEXT_WHITE

    if subtitle_text:
        p2 = tf.add_paragraph()
        p2.text = subtitle_text
        p2.font.size = Pt(13)
        p2.font.color.rgb = COLOR_PRIMARY

    return slide


def main():
    prs = Presentation()
    prs.slide_width = Inches(13.333)
    prs.slide_height = Inches(7.5)

    # ==========================================
    # SLIDE 1 : Titre / Page de garde
    # ==========================================
    s1 = prs.slides.add_slide(prs.slide_layouts[6])
    # Background
    bg = s1.shapes.add_shape(MSO_SHAPE.RECTANGLE, 0, 0, Inches(13.333), Inches(7.5))
    bg.fill.solid()
    bg.fill.fore_color.rgb = COLOR_BG
    bg.line.fill.background()

    # Title Box
    t_box = s1.shapes.add_textbox(Inches(1.2), Inches(1.8), Inches(11), Inches(3.5))
    tf = t_box.text_frame
    p = tf.paragraphs[0]
    p.text = "🧭 Ntic Radar Marrakech"
    p.font.size = Pt(44)
    p.font.bold = True
    p.font.color.rgb = COLOR_PRIMARY

    p_sub = tf.add_paragraph()
    p_sub.text = "Plateforme d'Analyse, Visualisation et Suivi des Opportunités de Stage"
    p_sub.font.size = Pt(22)
    p_sub.font.color.rgb = COLOR_TEXT_WHITE
    p_sub.space_before = Pt(12)

    p_author = tf.add_paragraph()
    p_author.text = "Présenté par : Ayoub Aamire — Filière Développement Digital (OFPPT)"
    p_author.font.size = Pt(16)
    p_author.font.color.rgb = RGBColor(147, 197, 253)
    p_author.space_before = Pt(30)

    p_links = tf.add_paragraph()
    p_links.text = "URL Déploiement : https://ntic-radar-marrakech-production.up.railway.app\nGitHub : https://github.com/ayoubwsf1/ntic-radar-marrakech"
    p_links.font.size = Pt(13)
    p_links.font.color.rgb = COLOR_MUTED
    p_links.space_before = Pt(15)

    # ==========================================
    # SLIDE 2 : Problématique et Objectifs
    # ==========================================
    s2 = create_slide_title(prs, "1. Problématique & Objectifs du Projet", "Pourquoi cette plateforme ?")
    b2 = s2.shapes.add_textbox(Inches(0.8), Inches(1.5), Inches(11.7), Inches(5.5))
    tf2 = b2.text_frame
    tf2.word_wrap = True

    items_s2 = [
        ("🔴 La Problématique :", [
            "Difficulté pour les étudiants en développement digital / NTIC à trouver des stages qualifiés à Marrakech.",
            "Données éparpillées sur le web (Google Maps, Clutch, annuaires, sites d'agences) sans vue d'ensemble.",
            "Absence d'un outil centralisé pour cartographier le marché, adapter son CV et suivre l'avancement des candidatures."
        ]),
        ("🎯 Les Objectifs :", [
            "Collecter et consolider un dataset exhaustif des agences NTIC au Maroc avec focus sur Marrakech.",
            "Nettoyer et structurer la donnée brute (normalisation, dédoublonnage, complétude).",
            "Visualiser et analyser le marché (répartition géographique, expertises, parts de marché).",
            "Automatiser le cycle de candidature : génération de CV sur-mesure par IA, scan des réponses e-mails, tableau de suivi."
        ])
    ]
    for section_title, bullets in items_s2:
        p = tf2.add_paragraph()
        p.text = section_title
        p.font.size = Pt(18)
        p.font.bold = True
        p.font.color.rgb = COLOR_ACCENT if "🔴" in section_title else COLOR_PRIMARY
        p.space_before = Pt(14)
        for bullet in bullets:
            pb = tf2.add_paragraph()
            pb.text = f"  •  {bullet}"
            pb.font.size = Pt(15)
            pb.font.color.rgb = COLOR_TEXT_DARK
            pb.space_before = Pt(4)

    # ==========================================
    # SLIDE 3 : Architecture Globale
    # ==========================================
    s3 = create_slide_title(prs, "2. Architecture Globale de la Solution", "Flux de données de la collecte à l'interface utilisateur")
    b3 = s3.shapes.add_textbox(Inches(0.8), Inches(1.5), Inches(11.7), Inches(5.5))
    tf3 = b3.text_frame
    tf3.word_wrap = True

    arch_steps = [
        ("1. Collecte Web", "Recherche via l'API Tavily + web scraping pour agréger les agences dans data/raw."),
        ("2. Pipeline de Nettoyage (Python/Pandas)", "Normalisation des colonnes, villes, URL, typologies, suppression des doublons -> data/cleaned."),
        ("3. Base de Données (SQLite)", "Stockage local persistant dans stages.db avec synchronisation depuis Excel au démarrage."),
        ("4. Logique Métier & IA Hybride", "Moteur de classification e-mails (regex + LLM OpenRouter/Mistral), agent CV et vérificateur anti-hallucination."),
        ("5. Interface Utilisateur (Streamlit)", "Frontend interactif en 6 onglets modulaires (Dashboard, Agences, Carte, Suivi, Mon CV, Scan).")
    ]
    for step_title, step_desc in arch_steps:
        p = tf3.add_paragraph()
        p.text = f"🔹 {step_title}"
        p.font.size = Pt(17)
        p.font.bold = True
        p.font.color.rgb = COLOR_PRIMARY
        p.space_before = Pt(10)
        p_desc = tf3.add_paragraph()
        p_desc.text = f"     {step_desc}"
        p_desc.font.size = Pt(14)
        p_desc.font.color.rgb = COLOR_TEXT_DARK

    # ==========================================
    # SLIDE 4 : Stack Technique
    # ==========================================
    s4 = create_slide_title(prs, "3. Stack Technique et Outils Utilisés", "Des technologies modernes, robustes et 100% Python")
    b4 = s4.shapes.add_textbox(Inches(0.8), Inches(1.5), Inches(11.7), Inches(5.5))
    tf4 = b4.text_frame
    tf4.word_wrap = True

    tech_table = [
        ("Frontend & Dashboard", "Streamlit 1.40+", "Interface réactive, composants interactifs, CSS sur-mesure"),
        ("Gestion & Traitement Data", "Pandas, OpenPyXL, SQLite3", "Manipulation de DataFrames, imports/exports Excel, persistance relationnelle"),
        ("Visualisations & Cartographie", "Plotly, PyDeck", "Graphiques interactifs (camemberts, barres), carte 3D Mapbox"),
        ("Intelligence Artificielle", "OpenRouter (Mistral / Gemma)", "Génération de CV contextuel, analyse sémantique des e-mails"),
        ("Génération de Documents", "ReportLab, Python-Docx", "Moteur de composition de CV deux colonnes PDF / Word"),
        ("Collecte & Intégrations", "Tavily Search API, IMAPlib", "Recherche ciblée d'agences et lecture automatisée des réponses Gmail"),
        ("Déploiement & DevOps", "Docker, Railway, GitHub Actions", "Conteneurisation, CI/CD automatique, hébergement cloud haute disponibilité")
    ]
    for cat, tech, role in tech_table:
        p = tf4.add_paragraph()
        p.text = f"• {cat} : "
        p.font.size = Pt(15)
        p.font.bold = True
        p.font.color.rgb = COLOR_BG
        p.space_before = Pt(6)

        # Add run for tech
        run_t = p.add_run()
        run_t.text = tech
        run_t.font.bold = True
        run_t.font.color.rgb = COLOR_PRIMARY

        # Add role
        run_r = p.add_run()
        run_r.text = f" — {role}"
        run_r.font.bold = False
        run_r.font.color.rgb = COLOR_TEXT_DARK

    # ==========================================
    # SLIDE 5 : Backend & Organisation
    # ==========================================
    s5 = create_slide_title(prs, "4. Backend, API, Logique Métier & Données", "Architecture modulaire et séparation stricte des responsabilités")
    b5 = s5.shapes.add_textbox(Inches(0.8), Inches(1.5), Inches(11.7), Inches(5.5))
    tf5 = b5.text_frame
    tf5.word_wrap = True

    backend_pts = [
        ("Architecture de fichiers stageradar/", "database.py (CRUD SQLite), config.py (constantes/secrets), events.py (audit trail)."),
        ("Sécurité et gestion des secrets", "Lecture hiérarchique : variables d'environnement OS -> secrets Streamlit -> .env. Jamais de credentials en clair."),
        ("Logique de suivi d'états (State Machine)", "Statuts stricts : Non encore postulé -> Entretien -> Accepté -> Refusé. Protection contre les régressions d'état."),
        ("Module IMAP / Gmail sécurisé", "Lecture en lecture seule (BODY.PEEK) sans altérer la boîte de réception. Mot de passe d'application en mémoire vive uniquement."),
        ("API LLM HTTP native (stageradar/ai/llm.py)", "Appels REST directs sans SDK lourd, avec timeout, gestion des quotas et fallback local garanti.")
    ]
    for tit, desc in backend_pts:
        p = tf5.add_paragraph()
        p.text = f"⚙️  {tit}"
        p.font.size = Pt(16)
        p.font.bold = True
        p.font.color.rgb = COLOR_PRIMARY
        p.space_before = Pt(8)
        pb = tf5.add_paragraph()
        pb.text = f"      {desc}"
        pb.font.size = Pt(14)
        pb.font.color.rgb = COLOR_TEXT_DARK

    # ==========================================
    # SLIDE 6 : Collecte & Sources
    # ==========================================
    s6 = create_slide_title(prs, "5. Sources de Données et Méthodologie de Collecte", "Recherche web ciblée avec l'API Tavily")
    b6 = s6.shapes.add_textbox(Inches(0.8), Inches(1.5), Inches(6.5), Inches(5.5))
    tf6 = b6.text_frame
    tf6.word_wrap = True

    collect_pts = [
        ("Sources exploitées :", "Recherches ciblées d'agences digitales sur Google / Tavily, profils Clutch.co Maroc, et annuaires professionnels."),
        ("Script de collecte automatique (scripts/collect_agences.py) :", "Génération automatique de requêtes ciblées ('agence web Marrakech', 'marketing digital Marrakech', etc.)."),
        ("Agrégation et déduplication initiale :", "Filtrage des résultats non pertinents et normalisation précoce des noms et domaines web."),
        ("Stratégie multi-villes :", "Base de référence sur 20 villes marocaines avec un focus approfondi sur Marrakech (26 agences identifiées).")
    ]
    for tit, desc in collect_pts:
        p = tf6.add_paragraph()
        p.text = f"📍 {tit}"
        p.font.size = Pt(16)
        p.font.bold = True
        p.font.color.rgb = COLOR_BG
        p.space_before = Pt(8)
        pb = tf6.add_paragraph()
        pb.text = f"    {desc}"
        pb.font.size = Pt(14)
        pb.font.color.rgb = COLOR_TEXT_DARK

    # Image source
    if (FIG_DIR / "sources.png").exists():
        s6.shapes.add_picture(str(FIG_DIR / "sources.png"), Inches(7.5), Inches(1.8), width=Inches(5.2))

    # ==========================================
    # SLIDE 7 : Exploration & Compréhension Dataset
    # ==========================================
    s7 = create_slide_title(prs, "6. Data Exploration & Compréhension du Dataset", "Analyse statistique de 229 agences au Maroc")
    b7 = s7.shapes.add_textbox(Inches(0.8), Inches(1.5), Inches(6.5), Inches(5.5))
    tf7 = b7.text_frame
    tf7.word_wrap = True

    stats_pts = [
        ("Dataset global :", "229 agences réparties sur 20 villes marocaines."),
        ("Focus Marrakech :", "26 agences (11,4% du total national), ce qui place Marrakech en 2e position après Casablanca (54 agences)."),
        ("Répartition par domaine d'activité :", "4 pôles majeurs : Web & Développement, Marketing digital, Design & Créa, Publicité & Com."),
        ("Qualité et complétude :", "100% de complétude sur les colonnes Nom, Type, Ville, Statut et Coordonnées GPS."),
        ("Génération automatisée (scripts/explore.py) :", "Génération des indicateurs et graphiques pour documentation et reporting.")
    ]
    for tit, desc in stats_pts:
        p = tf7.add_paragraph()
        p.text = f"📊 {tit}"
        p.font.size = Pt(16)
        p.font.bold = True
        p.font.color.rgb = COLOR_PRIMARY
        p.space_before = Pt(8)
        pb = tf7.add_paragraph()
        pb.text = f"    {desc}"
        pb.font.size = Pt(14)
        pb.font.color.rgb = COLOR_TEXT_DARK

    if (FIG_DIR / "agences_par_ville.png").exists():
        s7.shapes.add_picture(str(FIG_DIR / "agences_par_ville.png"), Inches(7.5), Inches(1.8), width=Inches(5.2))

    # ==========================================
    # SLIDE 8 : Nettoyage & Préparation des Données
    # ==========================================
    s8 = create_slide_title(prs, "7. Nettoyage et Préparation des Données (Python / Pandas)", "Traitement rigoureux des anomalies détectées sur les données brutes")
    b8 = s8.shapes.add_textbox(Inches(0.8), Inches(1.4), Inches(11.7), Inches(5.7))
    tf8 = b8.text_frame
    tf8.word_wrap = True

    clean_table = [
        ("En-têtes hétérogènes ('nom ', 'TYPE')", "normaliser_colonnes() : suppression des espaces et mise en casse standard", "5 anomalies"),
        ("Villes non standardisées ('casablanca', 'fes')", "Table de correspondance _VILLES pour corriger l'orthographe et les accents", "11 corrections"),
        ("Typologies d'agences multiples", "Harmonisation vers 4 catégories métier strictes", "8 corrections"),
        ("URL de sites mal formées (majuscules, www, paths)", "normaliser_site() : extraction du domaine et forçage https://", "42 corrections"),
        ("Statuts invalides ('NON POSTULE', 'test', vides)", "Ramenés au statut propre 'Non encore postulé'", "30 corrections"),
        ("Doublons détectés", "drop_duplicates() sur le nom normalisé et le domaine web", "6 doublons supprimés"),
        ("Coordonnées GPS absentes", "Injection des coordonnées des centres-villes (CITY_COORDS) pour affichage cartographique", "67 imputations")
    ]
    p_lead = tf8.add_paragraph()
    p_lead.text = "Résultat du pipeline de nettoyage : Données nettoyées, standardisées et 0 doublon résiduel."
    p_lead.font.size = Pt(15)
    p_lead.font.bold = True
    p_lead.font.color.rgb = COLOR_ACCENT

    for pb, sol, count in clean_table:
        p = tf8.add_paragraph()
        p.text = f"• {pb} -> Solution : "
        p.font.size = Pt(13)
        p.font.bold = True
        p.font.color.rgb = COLOR_TEXT_DARK
        p.space_before = Pt(4)

        run_s = p.add_run()
        run_s.text = f"{sol} ({count})"
        run_s.font.bold = False
        run_s.font.color.rgb = COLOR_PRIMARY

    # ==========================================
    # SLIDE 9 : Analyses et Visualisations
    # ==========================================
    s9 = create_slide_title(prs, "8. Méthodes d'Analyse et Visualisations Réalisées", "Indicateurs clés et restitutions graphiques dynamiques")
    b9 = s9.shapes.add_textbox(Inches(0.8), Inches(1.5), Inches(6.0), Inches(5.5))
    tf9 = b9.text_frame
    tf9.word_wrap = True

    viz_items = [
        ("Indicateurs globaux (KPIs) :", "Nombre total d'agences, part de Marrakech, candidatures en cours, taux de conversion."),
        ("Graphiques interactifs Plotly :", "Camembert de répartition géographique (Marrakech vs reste du Maroc), barres par catégorie métier."),
        ("Carte interactive PyDeck (3D) :", "Visualisation géolocalisée avec pastilles de couleur selon le statut de candidature."),
        ("Analyse sémantique des expertises :", "Extraction des mots-clés les plus récurrents dans les descriptions des services."),
        ("Export des résultats :", "Téléchargement instantané des données filtrées au format Excel (XLSX).")
    ]
    for tit, desc in viz_items:
        p = tf9.add_paragraph()
        p.text = f"📈 {tit}"
        p.font.size = Pt(15)
        p.font.bold = True
        p.font.color.rgb = COLOR_PRIMARY
        p.space_before = Pt(8)
        pb = tf9.add_paragraph()
        pb.text = f"    {desc}"
        pb.font.size = Pt(13)
        pb.font.color.rgb = COLOR_TEXT_DARK

    if (FIG_DIR / "marrakech_par_type.png").exists():
        s9.shapes.add_picture(str(FIG_DIR / "marrakech_par_type.png"), Inches(7.2), Inches(1.8), width=Inches(5.5))

    # ==========================================
    # SLIDE 10 : Frontend & Intégration
    # ==========================================
    s10 = create_slide_title(prs, "9. Frontend & Intégration avec Backend / Données", "Interface utilisateur Streamlit moderne et ergonomique")
    b10 = s10.shapes.add_textbox(Inches(0.8), Inches(1.5), Inches(11.7), Inches(5.5))
    tf10 = b10.text_frame
    tf10.word_wrap = True

    front_pts = [
        ("Sidebar & Filtrage multi-critères :", "Filtres combinés par ville, secteur d'activité, statut de candidature et recherche textuelle instantanée."),
        ("Header & Bandeau de bord :", "Affichage réactif des métriques clés synchronisées avec la sélection utilisateur."),
        ("Système à 6 onglets modulaires :", "1. Tableau de bord  ·  2. Agences  ·  3. Carte interactive  ·  4. Suivi  ·  5. Mon CV  ·  6. Scan e-mails."),
        ("CSS personnalisé (stageradar/ui/styles.py) :", "Design soigné, badges d'état colorés, typographie professionnelle, mode sombre/clair."),
        ("Communication bidirectionnelle :", "Mise à jour en temps réel de la base SQLite suite aux actions utilisateurs (changement de statut, notes, profil).")
    ]
    for tit, desc in front_pts:
        p = tf10.add_paragraph()
        p.text = f"💻 {tit}"
        p.font.size = Pt(16)
        p.font.bold = True
        p.font.color.rgb = COLOR_PRIMARY
        p.space_before = Pt(8)
        pb = tf10.add_paragraph()
        pb.text = f"    {desc}"
        pb.font.size = Pt(14)
        pb.font.color.rgb = COLOR_TEXT_DARK

    # ==========================================
    # SLIDE 11 : Intégration de l'IA
    # ==========================================
    s11 = create_slide_title(prs, "10. Intégration de l'Intelligence Artificielle", "Agent CV intelligent et classification automatique des e-mails")
    b11 = s11.shapes.add_textbox(Inches(0.8), Inches(1.5), Inches(11.7), Inches(5.5))
    tf11 = b11.text_frame
    tf11.word_wrap = True

    ai_pts = [
        ("🤖 Agent de rédaction de CV sur-mesure (stageradar/ai/cv.py) :",
         "Analyse le profil du candidat et la fiche de l'agence ciblée pour reformuler le CV afin de maximiser la pertinence."),
        ("🛡️ Garde-fou anti-hallucination (Anti-invention) :",
         "Contrôle algorithmique strict : le système vérifie que l'IA n'invente aucun diplôme, entreprise ou compétence absente du profil réel."),
        ("📄 Double moteur d'exportation :",
         "Génération d'un PDF professionnel deux colonnes via ReportLab et d'un document Word éditable via Python-Docx."),
        ("📧 Classification intelligente des retours e-mails (stageradar/ai/email_ai.py) :",
         "Détection automatique de la nature des réponses (Entretien proposé, Refus courtois, Demande d'informations) pour mise à jour du statut."),
        ("🔄 Mode hybride avec repli local sans coût :",
         "Fonctionne 100% hors-ligne et gratuitement par règles heuristiques en cas d'absence de clé API LLM.")
    ]
    for tit, desc in ai_pts:
        p = tf11.add_paragraph()
        p.text = tit
        p.font.size = Pt(16)
        p.font.bold = True
        p.font.color.rgb = COLOR_PRIMARY
        p.space_before = Pt(8)
        pb = tf11.add_paragraph()
        pb.text = f"    {desc}"
        pb.font.size = Pt(14)
        pb.font.color.rgb = COLOR_TEXT_DARK

    # ==========================================
    # SLIDE 12 : Résultats & Perspectives
    # ==========================================
    s12 = create_slide_title(prs, "11 & 12. Résultats Obtenus & Perspectives d'Amélioration", "Bilan du projet et évolutions futures")
    b12 = s12.shapes.add_textbox(Inches(0.8), Inches(1.5), Inches(11.7), Inches(5.5))
    tf12 = b12.text_frame
    tf12.word_wrap = True

    items_s12 = [
        ("✅ Résultats Obtenus :", [
            "Plateforme 100% fonctionnelle, déployée sur le cloud et accessible publiquement.",
            "Pipeline de données complet : de la collecte brute à l'exploration et au reporting interactif.",
            "Gain de temps majeur pour les étudiants : cartographie claire de 26 agences à Marrakech et 229 au Maroc.",
            "Automatisation réussie du suivi des candidatures et de la création de CV ciblés."
        ]),
        ("🚀 Perspectives d'Amélioration :", [
            "Envoi direct des candidatures par e-mail depuis la plateforme avec lettre de motivation personnalisée.",
            "Système d'alertes automatiques (WhatsApp / Telegram / E-mail) lors de nouvelles offres détectées.",
            "Extension de la collecte à LinkedIn Jobs et aux offres publiées sur les réseaux sociaux.",
            "Migration vers une base PostgreSQL multi-utilisateurs pour permettre à chaque étudiant d'avoir son compte."
        ])
    ]
    for section_title, bullets in items_s12:
        p = tf12.add_paragraph()
        p.text = section_title
        p.font.size = Pt(17)
        p.font.bold = True
        p.font.color.rgb = COLOR_ACCENT if "✅" in section_title else COLOR_PRIMARY
        p.space_before = Pt(12)
        for bullet in bullets:
            pb = tf12.add_paragraph()
            pb.text = f"  •  {bullet}"
            pb.font.size = Pt(14)
            pb.font.color.rgb = COLOR_TEXT_DARK
            pb.space_before = Pt(3)

    out_file = BASE_DIR / "GROUPE_AAMIRE_AYOUB_VF.pptx"
    prs.save(str(out_file))
    print(f"Presentation saved successfully to: {out_file}")


if __name__ == "__main__":
    main()
