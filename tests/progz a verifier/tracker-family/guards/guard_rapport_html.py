# ============================================================
#  guard_rapport_html.py — 📄 v3 : liens CLIQUABLES dans le rapport
#  - _linkify() transforme chaque URL en <a href> cliquable
#  - Cibles + résultats + captures + extraits
# ============================================================
import webbrowser
import html
import re
import tkinter as tk
from pathlib import Path
from datetime import datetime

NAME = "rapport_html"
TYPE = "ui"
UI = False
FRONTS = None
DESCRIPTION = "📄 Rapports HTML avec liens cliquables"

ROOT = Path(__file__).parent.parent
RAPPORTS_DIR = ROOT / "rapports"
CAPTURES_DIR = ROOT / "captures"
EXTRAITS_DIR = ROOT / "extraits"
RAPPORTS_DIR.mkdir(exist_ok=True)
EXTRAITS_DIR.mkdir(exist_ok=True)

def _linkify(txt):
    """Échappe le texte puis rend chaque URL cliquable."""
    escaped = html.escape(txt)
    return re.sub(r"(https?://[^\s<]+)", r'<a href="\1" target="_blank">\1</a>', escaped)

def generer(app):
    cfg = app.config
    now = datetime.now()
    fname = RAPPORTS_DIR / f"rapport_{now:%Y%m%d_%H%M}.html"

    cibles = []
    for c in cfg.get("cibles", []):
        cibles.append("<div class='cible'>🎯 <b>%s %s</b> (%s) — front %s — %s</div>" % (
            html.escape(str(c.get("prenom", ""))), html.escape(str(c.get("nom", ""))),
            html.escape(str(c.get("naissance", "?"))), html.escape(str(c.get("front", "?"))),
            html.escape(str(c.get("lieu", "")))))

    # ✅ Résultat : URLs rendues CLIQUABLES
    res = "".join("<li>%s</li>" % _linkify(r) for r in app.results) \
          or "<li>(aucun résultat pour l'instant)</li>"

    caps = sorted([p for p in CAPTURES_DIR.rglob("*") if p.is_file()],
                  key=lambda f: f.stat().st_mtime, reverse=True)[:12]
    cap_html = ""
    for p in caps:
        rel = p.relative_to(ROOT).as_posix()
        cap_html += "<div class='cap'><img src='../%s'/><p>%s</p></div>" % (rel, html.escape(p.name))
    if not cap_html: cap_html = "<p>(aucune capture)</p>"

    ext_html = ""
    for cat_dir in sorted([d for d in EXTRAITS_DIR.iterdir() if d.is_dir()]):
        files = [f for f in sorted(cat_dir.rglob("*")) if f.is_file()][:10]
        if not files: continue
        ext_html += "<h3>📁 %s</h3><ul>" % html.escape(cat_dir.name)
        for f in files:
            rel = f.relative_to(ROOT).as_posix()
            ext_html += "<li><a href='../%s' target='_blank'>%s</a></li>" % (rel, html.escape(f.name))
        ext_html += "</ul>"
    if not ext_html: ext_html = "<p>(aucun extrait classé pour l'instant)</p>"

    doc = """<!DOCTYPE html>
<html lang='fr'><head><meta charset='utf-8'/>
<title>Rapport Family Trace — %s</title>
<style>
body{background:#1e1e1e;color:#e0e0e0;font-family:Consolas,monospace;margin:0;padding:30px}
h1{color:#00ffcc} h2{color:#bb86fc;border-bottom:1px solid #333;padding-bottom:6px}
h3{color:#00ffcc}
a{color:#00ccff;text-decoration:none} a:hover{text-decoration:underline}
.cible{background:#161a2e;border-left:4px solid #00ffcc;padding:10px;margin:8px 0}
ul{line-height:1.8}
.cap{display:inline-block;margin:8px;text-align:center}
.cap img{max-width:180px;max-height:120px;border:1px solid #444}
.cap p{font-size:11px;color:#a0a0c0}
footer{margin-top:30px;color:#666;font-size:11px}
</style></head><body>
<h1>🛡️ RAPPORT KERBEROS FAMILY TRACE</h1>
<p>Généré le %s</p>
<h2>🎯 Cibles du dossier</h2>
%s
<h2>🔎 Résultats du scan (liens cliquables)</h2>
<ul>%s</ul>
<h2>📸 Captures & preuves</h2>
%s
<h2>📂 Actes classés (/extraits)</h2>
%s
<footer>KERBEROS FAMILY TRACE — recherche généalogique open-source</footer>
</body></html>""" % (
        now.strftime("%d/%m/%Y %H:%M"), now.strftime("%d/%m/%Y %H:%M"),
        "".join(cibles) or "<p>(aucune cible)</p>", res, cap_html, ext_html)
    fname.write_text(doc, encoding="utf-8")
    return fname

def inject_buttons(app):
    tb = getattr(app, "toolbar_frame", None)
    if tb is None: return
    def _go():
        p = generer(app)
        webbrowser.open(p.as_uri())
        app._print(f"📄 Rapport HTML généré : {p.name}")
    tk.Button(tb, text="📄 HTML", bg='#2d7b7b', fg='white',
              font=("Consolas", 10, "bold"), relief=tk.RAISED, bd=1,
              command=_go).pack(side=tk.LEFT, padx=4, pady=6)

def run(cible, ctx, emit):
    return