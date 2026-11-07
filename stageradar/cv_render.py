"""Export du CV en PDF — design deux colonnes avec frames (reportlab)."""
from __future__ import annotations

from io import BytesIO
from xml.sax.saxutils import escape

LABELS = {
    "Français": {
        "resume": "Profil", "formation": "Formation", "experiences": "Expériences",
        "projets": "Projets", "competences": "Compétences", "langues": "Langues",
        "interets": "Centres d'intérêt",
    },
    "English": {
        "resume": "Profile", "formation": "Education", "experiences": "Experience",
        "projets": "Projects", "competences": "Skills", "langues": "Languages",
        "interets": "Interests",
    },
}

SIDE_BG     = "#0f172a"
SIDE_ACCENT = "#3b82f6"
MAIN_HEAD   = "#1e3a5f"
MAIN_LINE   = "#3b82f6"
MAIN_TXT    = "#1e293b"
MAIN_MUTED  = "#64748b"
NOM_COLOR   = "#ffffff"
TITRE_COLOR = "#93c5fd"
CONTACT_CLR = "#cbd5e1"
SIDE_TXT    = "#e2e8f0"
SIDE_HEAD   = "#ffffff"
SIDE_LINE   = "#334155"
BADGE_FG    = "#93c5fd"


def _labels(cv: dict) -> dict:
    return LABELS.get(cv.get("langue", "Français"), LABELS["Français"])


def _contact_items(cv: dict) -> list[tuple[str, str]]:
    out = []
    if cv.get("email"):     out.append(("@", cv["email"]))
    if cv.get("telephone"): out.append(("T", cv["telephone"]))
    if cv.get("ville"):     out.append(("V", cv["ville"]))
    for l in (cv.get("liens") or []):
        out.append(("L", l))
    return out


def nom_fichier(cv: dict, ext: str) -> str:
    base = "".join(c if c.isalnum() else "_" for c in (cv.get("nom") or "candidat")).strip("_") or "candidat"
    return f"CV_{base}.{ext}"


# ─────────────────────────────────────────────────────────────── PDF ──────────

def cv_pdf(cv: dict) -> bytes:  # noqa: C901
    from reportlab.lib import colors
    from reportlab.lib.enums import TA_LEFT
    from reportlab.lib.pagesizes import A4
    from reportlab.lib.styles import ParagraphStyle
    from reportlab.lib.units import mm
    from reportlab.platypus import (
        BaseDocTemplate, Frame, HRFlowable, KeepTogether,
        PageTemplate, Paragraph, Spacer,
    )

    L     = _labels(cv)
    W, H  = A4
    is_en = cv.get("langue") == "English"

    def hx(s): return colors.HexColor(s)

    # ── styles ────────────────────────────────────────────────────────────────
    def S(name, **kw): return ParagraphStyle(name, **kw)

    # sidebar styles
    s_nom   = S("nom",   fontName="Helvetica-Bold",    fontSize=17, leading=21, textColor=hx(NOM_COLOR))
    s_titre = S("titre", fontName="Helvetica-Oblique", fontSize=9.5, leading=13, textColor=hx(TITRE_COLOR), spaceAfter=4)
    s_sh    = S("sh",    fontName="Helvetica-Bold",    fontSize=8,  leading=11, textColor=hx(SIDE_HEAD), spaceBefore=8, spaceAfter=2)
    s_sc    = S("sc",    fontName="Helvetica",         fontSize=8,  leading=12, textColor=hx(SIDE_TXT))
    s_ct    = S("ct",    fontName="Helvetica",         fontSize=7.5, leading=11, textColor=hx(CONTACT_CLR))
    s_sk    = S("sk",    fontName="Helvetica-Bold",    fontSize=8,  leading=12, textColor=hx(BADGE_FG))

    # main styles
    s_mh = S("mh", fontName="Helvetica-Bold",    fontSize=10.5, leading=13, textColor=hx(MAIN_HEAD), spaceBefore=8, spaceAfter=2)
    s_mb = S("mb", fontName="Helvetica",         fontSize=9.2,  leading=13.5, textColor=hx(MAIN_TXT))
    s_mg = S("mg", fontName="Helvetica-Bold",    fontSize=9.5,  leading=13, textColor=hx(MAIN_TXT), spaceBefore=5)
    s_mo = S("mo", fontName="Helvetica-Oblique", fontSize=8.8,  leading=12, textColor=hx(MAIN_HEAD))
    s_md = S("md", fontName="Helvetica",         fontSize=8,    leading=11, textColor=hx(MAIN_MUTED))
    s_mp = S("mp", fontName="Helvetica",         fontSize=9,    leading=13, textColor=hx(MAIN_TXT),
             leftIndent=8, bulletIndent=1, spaceBefore=1)

    def P(txt, style): return Paragraph(escape(str(txt)), style)

    def side_hr():
        return HRFlowable(width="100%", thickness=0.4, color=hx(SIDE_LINE), spaceAfter=3)

    def main_hr():
        return HRFlowable(width="100%", thickness=1.5, color=hx(MAIN_LINE), spaceAfter=4)

    # ── dimensions ────────────────────────────────────────────────────────────
    SIDE_W  = 62 * mm
    PAD_S   = 5 * mm
    PAD_M   = 7 * mm
    TOP     = 6 * mm
    BOT     = 6 * mm

    # ── canvas background ─────────────────────────────────────────────────────
    def draw_bg(canvas, doc):
        canvas.saveState()
        # sidebar background
        canvas.setFillColor(hx(SIDE_BG))
        canvas.rect(0, 0, SIDE_W, H, fill=1, stroke=0)
        # accent top bar full width
        canvas.setFillColor(hx(SIDE_ACCENT))
        canvas.rect(0, H - 4 * mm, W, 4 * mm, fill=1, stroke=0)
        # accent vertical line between columns
        canvas.setFillColor(hx(SIDE_ACCENT))
        canvas.rect(SIDE_W - 1.5, 0, 3, H, fill=1, stroke=0)
        canvas.restoreState()

    # ── frames ────────────────────────────────────────────────────────────────
    frame_side = Frame(
        PAD_S,              # x
        BOT,                # y
        SIDE_W - 2 * PAD_S, # width
        H - 4 * mm - TOP - BOT,  # height (skip accent bar at top)
        leftPadding=0, rightPadding=0,
        topPadding=0, bottomPadding=0,
        id="sidebar",
    )
    frame_main = Frame(
        SIDE_W + PAD_M,            # x
        BOT,                        # y
        W - SIDE_W - PAD_M - PAD_S, # width
        H - 4 * mm - TOP - BOT,    # height
        leftPadding=0, rightPadding=0,
        topPadding=0, bottomPadding=0,
        id="main",
    )

    buf = BytesIO()
    doc = BaseDocTemplate(
        buf, pagesize=A4,
        leftMargin=0, rightMargin=0, topMargin=0, bottomMargin=0,
        title=f"CV {cv.get('nom', '')}".strip(),
        author=cv.get("nom", ""),
    )
    doc.addPageTemplates([
        PageTemplate(id="cv", frames=[frame_side, frame_main], onPage=draw_bg)
    ])

    # ── SIDEBAR story ─────────────────────────────────────────────────────────
    side: list = []
    side.append(Spacer(1, TOP))
    side.append(P(cv.get("nom") or "Candidat", s_nom))
    if cv.get("titre"):
        side.append(P(cv["titre"], s_titre))
    side.append(HRFlowable(width="100%", thickness=1, color=hx(SIDE_ACCENT), spaceAfter=5))

    # contact
    contacts = _contact_items(cv)
    if contacts:
        side.append(P("CONTACT", s_sh))
        side.append(side_hr())
        for _, val in contacts:
            side.append(P(val, s_ct))
            side.append(Spacer(1, 1.5))

    # compétences
    if cv.get("competences"):
        lbl = "SKILLS" if is_en else "COMPETENCES"
        side.append(P(lbl, s_sh))
        side.append(side_hr())
        for skill in cv["competences"]:
            side.append(P(f"> {skill}", s_sk))
            side.append(Spacer(1, 2))

    # langues
    if cv.get("langues"):
        lbl = "LANGUAGES" if is_en else "LANGUES"
        side.append(P(lbl, s_sh))
        side.append(side_hr())
        for lang in cv["langues"]:
            side.append(P(f"- {lang}", s_sc))

    # intérêts
    if cv.get("interets"):
        lbl = "INTERESTS" if is_en else "INTERETS"
        side.append(P(lbl, s_sh))
        side.append(side_hr())
        side.append(P(cv["interets"], s_sc))

    # ── MAIN story ────────────────────────────────────────────────────────────
    main: list = []
    main.append(Spacer(1, TOP))

    def section(cle):
        main.append(P(L[cle].upper(), s_mh))
        main.append(main_hr())

    if cv.get("resume"):
        section("resume")
        main.append(P(cv["resume"], s_mb))

    if cv.get("experiences"):
        main.append(Spacer(1, 2 * mm))
        section("experiences")
        for e in cv["experiences"]:
            bloc = []
            if e.get("poste"):
                bloc.append(P(e["poste"], s_mg))
            if e.get("organisation"):
                bloc.append(P(e["organisation"], s_mo))
            if e.get("periode"):
                bloc.append(P(e["periode"], s_md))
            for pt in (e.get("points") or []):
                bloc.append(Paragraph(escape(str(pt)), s_mp, bulletText=">"))
            if bloc:
                main.append(KeepTogether(bloc))
                main.append(Spacer(1, 3))

    if cv.get("projets"):
        main.append(Spacer(1, 2 * mm))
        section("projets")
        for pr in cv["projets"]:
            bloc = [P(pr.get("nom", ""), s_mg)]
            for pt in (pr.get("points") or []):
                bloc.append(Paragraph(escape(str(pt)), s_mp, bulletText=">"))
            main.append(KeepTogether(bloc))
            main.append(Spacer(1, 3))

    if cv.get("formation"):
        main.append(Spacer(1, 2 * mm))
        section("formation")
        for fo in cv["formation"]:
            bloc = [P(fo.get("intitule", ""), s_mg)]
            if fo.get("details"):
                bloc.append(P(fo["details"], s_md))
            main.append(KeepTogether(bloc))
            main.append(Spacer(1, 3))

    # ── build : sidebar en premier, FrameBreak, puis main ─────────────────────
    from reportlab.platypus import FrameBreak
    story = side + [FrameBreak()] + main

    doc.build(story)
    return buf.getvalue()
