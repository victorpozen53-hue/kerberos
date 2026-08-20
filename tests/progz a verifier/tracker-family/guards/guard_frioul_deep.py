# ============================================================
#  guard_frioul_deep.py — 🇮🇹 Anagrafe defunti Frioul
#  - Tente le scraping POLI du formulaire ASP.NET (champs détectés auto)
#  - Repli : ouvre le navigateur si le site refuse
#  - Aucune donnée perso en dur
# ============================================================
import re, threading, webbrowser
import tkinter as tk
from tkinter import messagebox

NAME = "frioul_deep"
TYPE = "ui"
UI = False
FRONTS = None
DESCRIPTION = "🇮 Interroge l'anagrafe defunti du Frioul (scraping poli)"

URL = "https://lexview-int.regione.fvg.it/ServiziCimiteriali/Defunti.aspx"
UA = "KerberosFamilyTrace/1.1 (recherche familiale personnelle)"

def chercher(nom, prenom=""):
    """Retourne une liste de lignes texte, ou None si le site refuse."""
    import requests
    s = requests.Session()
    s.headers.update({"User-Agent": UA})
    r = s.get(URL, timeout=30)
    champs = dict(re.findall(r'<input[^>]*name="([^"]*)"[^>]*value="([^"]*)"', r.text))
    data = {k: v for k, v in champs.items() if k.startswith("__")}
    cog = [k for k in champs if "cognome" in k.lower()]
    if not cog:
        return None
    data[cog[0]] = nom
    nomc = [k for k in champs if k.lower().endswith("nome") and "cognome" not in k.lower()]
    if prenom and nomc: data[nomc[0]] = prenom
    btn = [k for k in champs if "btn" in k.lower() or "cerca" in k.lower()]
    if btn: data[btn[0]] = "Cerca"
    r2 = s.post(URL, data=data, timeout=30)
    rows = re.findall(r"<tr[^>]*>(.*?)</tr>", r2.text, re.S)
    out = []
    for row in rows:
        cells = [re.sub(r"<.*?>", "", c).strip() for c in re.findall(r"<td[^>]*>(.*?)</td>", row, re.S)]
        if cells and any(nom.lower() in c.lower() for c in cells):
            out.append(" | ".join(cells))
    return out or None

def _ouvrir(app):
    win = tk.Toplevel(app.root)
    win.title("🇮🇹 Defunti Frioul")
    win.geometry("560x220")
    win.configure(bg='#1a1a2e')
    tk.Label(win, text="🇮 RECHERCHE DEFUNTI (FRIUL)", bg='#16213e', fg='#00ffcc',
             font=("Consolas", 14, "bold")).pack(pady=12, fill=tk.X)
    f = tk.Frame(win, bg='#1a1a2e'); f.pack(pady=6)
    v1, v2 = tk.StringVar(), tk.StringVar()
    tk.Entry(f, textvariable=v1, width=20, bg='#333333', fg='white',
             insertbackground='white').pack(side=tk.LEFT, padx=4)
    tk.Entry(f, textvariable=v2, width=20, bg='#333333', fg='white',
             insertbackground='white').pack(side=tk.LEFT, padx=4)
    def _work():
        def emit(t): app.root.after(0, lambda x=t: app._print(x))
        res = chercher(v1.get().strip(), v2.get().strip())
        if res is None:
            app.root.after(0, lambda: (
                webbrowser.open(URL),
                messagebox.showinfo("Frioul", "Site ASP.NET protégé — navigateur ouvert, tape le nom à la main.")))
        else:
            for ligne in res[:15]:
                emit(f"   ⚰️ [frioul] {ligne}")
            app.root.after(0, lambda: messagebox.showinfo("✅ Frioul", f"{len(res)} ligne(s) dans la console"))
    tk.Button(win, text="🔎 Chercher les défunts", bg='#2d7b5a', fg='white',
              font=("Consolas", 11, "bold"),
              command=lambda: threading.Thread(target=_work, daemon=True).start()).pack(pady=8)

def inject_buttons(app):
    tb = getattr(app, "toolbar_frame", None)
    if tb is None: return
    tk.Button(tb, text="⚰️ Defunti", bg='#5a2d7b', fg='white',
              font=("Consolas", 10, "bold"), relief=tk.RAISED, bd=1,
              command=lambda: _ouvrir(app)).pack(side=tk.LEFT, padx=4, pady=6)

def run(cible, ctx, emit):
    return