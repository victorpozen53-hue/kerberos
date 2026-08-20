# ============================================================
#  guard_comptes.py — 🔐 v2 : cookie AUTO depuis Brave
#  - 🤖 Auto : lit le cookie geneanet.org dans ton profil Brave
#  - Manuel : collage possible aussi (repli)
#  - SÉCURITÉ : lecture LOCALE uniquement (ton PC, ta session),
#    seul le domaine du site est lu, jamais envoyé ailleurs
#    (le cookie part uniquement vers geneanet.org pour la requête)
#  - Nécessite : pip install browser_cookie3
# ============================================================
import json
import tkinter as tk
from tkinter import messagebox
from pathlib import Path

NAME = "comptes"
TYPE = "ui"
UI = False
FRONTS = None
DESCRIPTION = "🔐 Comptes — cookie auto depuis Brave, recherche profonde si ouvert"

ROOT = Path(__file__).parent.parent
SESSIONS_FILE = ROOT / "sessions.json"
UA = "KerberosFamilyTrace/1.1 (recherche familiale personnelle)"

SITES = {
    "geneanet": {
        "label": "🌳 Geneanet",
        "domaine": "geneanet.org",
        "test_url": "https://www.geneanet.org/fonds/individus/",
        "markers": ["déconnexion", "mon compte", "mon arbre", "logout"],
    },
    "myheritage": {
        "label": "🧬 MyHeritage",
        "domaine": "myheritage.fr",
        "test_url": "https://www.myheritage.fr/",
        "markers": ["déconnexion", "logout", "mon arbre"],
    },
}

def _load():
    if SESSIONS_FILE.exists():
        try:
            return json.loads(SESSIONS_FILE.read_text(encoding="utf-8"))
        except Exception:
            pass
    return {}

def _save(data):
    SESSIONS_FILE.write_text(json.dumps(data, indent=2), encoding="utf-8")

def get_cookie(site):
    return (_load().get(site) or "").strip()

def compte_ouvert(site):
    """True si un cookie existe ET que le site reconnaît la session."""
    cookie = get_cookie(site)
    if not cookie:
        return False
    import requests
    cfg = SITES.get(site, {})
    try:
        r = requests.get(cfg.get("test_url", "https://www.geneanet.org/"),
                         headers={"User-Agent": UA, "Cookie": cookie}, timeout=20)
        txt = r.text.lower()
        return any(m in txt for m in cfg.get("markers", []))
    except Exception:
        return False

def auto_cookie(site):
    """🤖 Lit le cookie de session directement dans le profil Brave LOCAL."""
    try:
        import browser_cookie3
    except ImportError:
        return None, "Bibliothèque absente — tape dans cmd : pip install browser_cookie3"
    cfg = SITES.get(site, {})
    dom = cfg.get("domaine", site)
    loader = getattr(browser_cookie3, "brave", None)
    if loader is None:
        return None, "browser_cookie3 sans support Brave — mets à jour : pip install -U browser_cookie3"
    try:
        jar = loader(domain_name=dom)
        parts = []
        for c in jar:
            parts.append(f"{c.name}={c.value}")
        if not parts:
            return None, f"Aucun cookie {dom} trouvé — connecte-toi d'abord dans Brave"
        return "; ".join(parts), None
    except Exception as e:
        return None, f"Erreur lecture Brave : {e}"

def _ouvrir(app):
    win = tk.Toplevel(app.root)
    win.title("🔐 Comptes")
    win.geometry("660x480")
    win.configure(bg='#1a1a2e')
    tk.Label(win, text="🔐 COMPTES — RECHERCHE PROFONDE", bg='#16213e', fg='#00ffcc',
             font=("Consolas", 14, "bold")).pack(pady=10, fill=tk.X)
    tk.Label(win, text="🤖 Auto = lit ton cookie de session dans Brave (local, rien n'est envoyé)\n"
                       "Manuel = F12 → Réseau → 1ère requête → en-tête « Cookie: » → coller\n"
                       "⚠️ Jamais ton mot de passe — seulement le cookie (il expire tout seul).",
             bg='#1a1a2e', fg='#a0a0c0', font=("Consolas", 9), justify="left").pack(padx=20)
    data = _load()
    widgets = {}
    for site, cfg in SITES.items():
        f = tk.LabelFrame(win, text=f" {cfg['label']} ", bg='#1e1e2e', fg='#00ffcc',
                          font=("Consolas", 10, "bold"))
        f.pack(fill=tk.X, padx=15, pady=6)
        t = tk.Text(f, height=3, bg='#333333', fg='white', insertbackground='white',
                    font=("Consolas", 8))
        t.pack(padx=8, pady=4)
        if data.get(site):
            t.insert("1.0", data[site])
        widgets[site] = t
        bf = tk.Frame(f, bg='#1e1e2e'); bf.pack(pady=4)
        tk.Button(bf, text="🤖 Auto (Brave)", bg='#2d7b7b', fg='white',
                  command=lambda s=site: _auto(s, widgets[s])).pack(side=tk.LEFT, padx=4)
        tk.Button(bf, text="💾 Enregistrer", bg='#2d7b5a', fg='white',
                  command=lambda s=site: _enregistrer(s, widgets[s])).pack(side=tk.LEFT, padx=4)
        tk.Button(bf, text="🔓 Tester", bg='#2d5a7b', fg='white',
                  command=lambda s=site: _tester(s)).pack(side=tk.LEFT, padx=4)
        tk.Button(bf, text="🗑", bg='#7b2d2d', fg='white', width=3,
                  command=lambda s=site: _effacer(s, widgets[s])).pack(side=tk.LEFT, padx=4)

def _auto(site, widget):
    cookie, err = auto_cookie(site)
    if err:
        messagebox.showwarning("🤖 Auto", err)
        return
    widget.delete("1.0", tk.END)
    widget.insert("1.0", cookie)
    data = _load()
    data[site] = cookie
    _save(data)
    if compte_ouvert(site):
        messagebox.showinfo("🔓", f"{site} : compte OUVERT via Brave !\nRecherche profonde activée.")
    else:
        messagebox.showwarning("🔒", f"Cookie trouvé mais session non reconnue.\n"
                                      f"Connecte-toi à {site} dans Brave puis re-clique 🤖 Auto.")

def _enregistrer(site, widget):
    data = _load()
    data[site] = widget.get("1.0", "end-1c").strip()
    _save(data)
    messagebox.showinfo("✅", f"Cookie {site} enregistré (local uniquement).")

def _tester(site):
    if compte_ouvert(site):
        messagebox.showinfo("🔓", f"{site} : compte OUVERT — recherche profonde activée !")
    else:
        messagebox.showwarning("🔒", f"{site} : compte FERMÉ ou session expirée.")

def _effacer(site, widget):
    widget.delete("1.0", tk.END)
    data = _load()
    data.pop(site, None)
    _save(data)
    messagebox.showinfo("🗑", f"Cookie {site} effacé.")

def inject_buttons(app):
    tb = getattr(app, "toolbar_frame", None)
    if tb is None:
        return
    tk.Button(tb, text="🔐 Comptes", bg='#5a2d7b', fg='white',
              font=("Consolas", 10, "bold"), relief=tk.RAISED, bd=1,
              command=lambda: _ouvrir(app)).pack(side=tk.LEFT, padx=4, pady=6)

def run(cible, ctx, emit):
    return