"""Les styles CSS de l'interface : les couleurs, les cartes, les barres."""
# CSS = le code pour les couleurs et la mise en forme de la page
CSS = """
<style>
@import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700;800&display=swap');
html, body, [class*="css"], .stMarkdown, button, input, textarea { font-family: 'Inter', system-ui, sans-serif; }
.block-container { padding-top: 1.6rem; padding-bottom: 3rem; max-width: 1320px; }
header[data-testid="stHeader"] { background: transparent; }

.hero { background: linear-gradient(120deg, #4f46e5 0%, #7c3aed 45%, #0ea5e9 100%);
        border-radius: 22px; padding: 30px 34px; color: #fff; margin-bottom: 18px;
        box-shadow: 0 14px 40px -14px rgba(79,70,229,.55); position: relative; overflow: hidden; }
.hero:after { content: ""; position: absolute; right: -60px; top: -60px; width: 240px; height: 240px;
              border-radius: 50%; background: rgba(255,255,255,.10); }
.hero-title { font-size: 2.1rem; font-weight: 800; letter-spacing: -.02em; line-height: 1.1; }
.hero-title span { opacity: .85; font-weight: 600; }
.hero-sub { margin-top: 8px; font-size: 1.02rem; opacity: .92; max-width: 640px; }
.hero-badges { margin-top: 16px; display: flex; gap: 8px; flex-wrap: wrap; }
.hero-badges b { background: rgba(255,255,255,.18); border: 1px solid rgba(255,255,255,.28);
                 padding: 5px 12px; border-radius: 999px; font-size: .8rem; font-weight: 600; }

.kpi { border: 1px solid rgba(127,127,127,.22); background: rgba(127,127,127,.06);
       border-radius: 16px; padding: 14px 16px; }
.kpi-n { font-size: 1.9rem; font-weight: 800; line-height: 1; letter-spacing: -.02em; }
.kpi-l { margin-top: 6px; font-size: .78rem; font-weight: 600; opacity: .7; text-transform: uppercase; letter-spacing: .04em; }

.ag-head { display: flex; justify-content: space-between; align-items: flex-start; gap: 10px; }
.ag-name { font-size: 1.08rem; font-weight: 700; letter-spacing: -.01em; }
.ag-meta { font-size: .84rem; opacity: .7; margin-top: 2px; }
.ag-serv { font-size: .86rem; opacity: .85; margin: 8px 0 4px; line-height: 1.45; }
.pill { color: #fff; font-size: .72rem; font-weight: 700; padding: 4px 11px; border-radius: 999px; white-space: nowrap; }
.chip { display: inline-block; font-size: .72rem; font-weight: 600; padding: 3px 10px; border-radius: 8px;
        background: rgba(99,102,241,.14); color: #6366f1; margin-top: 8px; }
.chip-source { background: rgba(100,116,139,.14); color: #64748b; margin-left: 6px; }
.proof { font-size: .76rem; opacity: .65; margin-top: 4px; }

.bar-row { display: flex; align-items: center; gap: 10px; margin: 7px 0; font-size: .88rem; }
.bar-label { width: 150px; font-weight: 600; }
.bar-track { flex: 1; height: 12px; background: rgba(127,127,127,.16); border-radius: 999px; overflow: hidden; }
.bar-fill { height: 100%; border-radius: 999px; }
.bar-n { width: 34px; text-align: right; font-weight: 700; }

.legend { display: flex; gap: 16px; flex-wrap: wrap; font-size: .85rem; margin-top: 8px; }
.legend i { display: inline-block; width: 11px; height: 11px; border-radius: 50%; margin-right: 6px; vertical-align: -1px; }
button[data-testid="stBaseButton-primary"] { background: #4f46e5; border-color: #4f46e5; font-weight: 600; }
button[data-testid="stBaseButton-primary"]:hover { background: #4338ca; border-color: #4338ca; }
section[data-testid="stSidebar"] { border-right: 1px solid rgba(127,127,127,.2); }
div[data-testid="stVerticalBlockBorderWrapper"] { border-radius: 18px; }
</style>
"""
