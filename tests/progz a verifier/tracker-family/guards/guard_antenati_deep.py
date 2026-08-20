# ============================================================
#  guard_antenati_deep.py — 🇮🇹 Images des registres Antenati
#  - Lit le manifeste IIIF (dam-antenati.cultura.gov.it) — sans WAF
#  - Télécharge toutes les pages en pleine résolution (poli : 0,4 s)
#  - Sauvegarde dans extraits/antenati_<registre>/
#  - Compatible Python 3.8
# ============================================================
import re, time, threading
import tkinter as tk
from tkinter import messagebox
from pathlib import Path

NAME = "antenati_deep"
TYPE = "ui"
UI = False
FRONTS = None
DESCRIPTION = "🇮🇹 Télécharge les images des registres Antenati (IIIF)"

ROOT = Path(__file__).parent.parent
DEST = ROOT / "extraits" / "antenati"
DEST.mkdir(parents=True, exist_ok=True)
UA = "KerberosFamilyTrace/1.1 (recherche familiale personnelle)"

def _label(man):
    lab = man.get("label", "registre")
    if isinstance(lab, dict): lab = list(lab.values())[0]
    if isinstance(lab, list): lab = lab[0]
    return re.sub(r'[^\w\-]+', "_", str(lab))[:60]

def _service_url(canvas):
    try:
        imgs = canvas.get("images") or []
        if imgs:
            svc = imgs[0].get("resource", {}).get("service")
            if isinstance(svc, list): svc = svc[0]
            if svc and svc.get("@id"): return svc["@id"]
        items = canvas.get("items", [])
        if items:
            body = items[0].get("items", [{}])[0].get("body", {})
            svc = body.get("service", [])
            if svc: return svc[0].get("id")
    except Exception:
        pass
    return None

def telecharger_registre(url, emit=None):
    import requests
    url = url.strip()
    if "/ark:/" in url and "manifest" not in url:
        raise ValueError("Colle le lien du MANIFESTE IIIF (bas du panneau gauche du site)")
    r = requests.get(url, headers={"User-Agent": UA}, timeout=30)
    r.raise_for_status()
    man = r.json()
    seq = man.get("sequences") or []
    canvases = seq[0].get("canvases", []) if seq else man.get("items", [])
    folder = DEST / _label(man)
    folder.mkdir(parents=True, exist_ok=True)
    n = 0
    for i, c in enumerate(canvases):
        sid = _service_url(c)
        if not sid: continue
        for size in ("full", "max"):
            try:
                time.sleep(0.4)
                ir = requests.get(f"{sid}/full/{size}/0/default.jpg",
                                  headers={"User-Agent": UA}, timeout=60)
                if ir.ok and len(ir.content) > 1000:
                    (folder / f"page_{i+1:03d}.jpg").write_bytes(ir.content)
                    n += 1
                    if emit: emit(f"   📥 [antenati] page {i+1}/{len(canvases)}")
                    break
            except Exception:
                continue
    return n, folder

def _ouvrir(app):
    win = tk.Toplevel(app.root)
    win.title("🇮🇹 Registres Antenati")
    win.geometry("620x260")
    win.configure(bg='#1a1a2e')
    tk.Label(win, text="🇮🇹 TÉLÉCHARGER UN REGISTRE COMPLET", bg='#16213e', fg='#00ffcc',
             font=("Consolas", 14, "bold")).pack(pady=12, fill=tk.X)
    tk.Label(win, text="1. Sur Antenati : Search registers → Buja → Nati/Morti → ouvrir\n"
                       "2. Copier le lien IIIF manifest (bas du panneau gauche)\n3. Coller ici :",
             bg='#1a1a2e', fg='#a0a0c0', font=("Consolas", 9), justify="left").pack(padx=20)
    var = tk.StringVar()
    tk.Entry(win, textvariable=var, width=70, bg='#333333', fg='white',
             insertbackground='white').pack(padx=20, pady=8)
    def _work():
        def emit(t): app.root.after(0, lambda x=t: app._print(x))
        try:
            n, folder = telecharger_registre(var.get(), emit)
            app.root.after(0, lambda: messagebox.showinfo("✅ Antenati",
                f"{n} page(s) téléchargée(s) → {folder}"))
        except Exception as e:
            app.root.after(0, lambda: messagebox.showwarning("Antenati", str(e)))
    tk.Button(win, text="📥 Télécharger tout le registre", bg='#2d7b5a', fg='white',
              font=("Consolas", 11, "bold"),
              command=lambda: threading.Thread(target=_work, daemon=True).start()).pack(pady=8)

def inject_buttons(app):
    tb = getattr(app, "toolbar_frame", None)
    if tb is None: return
    tk.Button(tb, text="🇮 Registres", bg='#2d7b5a', fg='white',
              font=("Consolas", 10, "bold"), relief=tk.RAISED, bd=1,
              command=lambda: _ouvrir(app)).pack(side=tk.LEFT, padx=4, pady=6)

def run(cible, ctx, emit):
    return