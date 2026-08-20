# ============================================================
#  guard_extraction.py — 📦 Extraction & classement des actes
#  v2 GÉNÉALOGIE :
#   - 📦 Décompresse zip/tar vers /extraits
#   - 🗂️ Classe les fichiers (PDF, images) par catégorie :
#     naissance / mariage / deces / autre
#   -  Détection AUTO par mots-clés du nom de fichier
#  - Sécurisé (bloque chemins ".." et absolus)
#  - Aucune donnée personnelle en dur
# ============================================================
import tkinter as tk
from tkinter import ttk, messagebox, filedialog
from pathlib import Path
import zipfile, tarfile, shutil

NAME = "extraction"
TYPE = "ui"
UI = False
FRONTS = None
DESCRIPTION = "📦 Extraction & classement des actes (naissance, mariage…)"

ROOT = Path(__file__).parent.parent
DOWNLOAD_DIR = ROOT / "telechargements"
EXTRAITS_DIR = ROOT / "extraits"
DOWNLOAD_DIR.mkdir(exist_ok=True)
EXTRAITS_DIR.mkdir(exist_ok=True)

SUPPORTED = (".zip", ".tar", ".tar.gz", ".tgz", ".tar.bz2", ".tbz2")
CATEGORIES = ["naissance", "mariage", "deces", "autre"]

KEYWORDS = {
    "naissance": ["naissance", "birth", "bapteme", "baptism", "ne_"],
    "mariage":  ["mariage", "marriage", "epoux", "wedding", "union"],
    "deces":    ["deces", "death", "obituaire", "decede", "mort"],
}

def detecter_cat(nom):
    n = nom.lower()
    for cat, mots in KEYWORDS.items():
        if any(m in n for m in mots): return cat
    return "autre"

def _dossier(cat):
    d = EXTRAITS_DIR / cat
    d.mkdir(parents=True, exist_ok=True)
    return d

def extraire_archive(archive, dest=None):
    archive = Path(archive)
    if not archive.exists(): return False, None, "fichier introuvable"
    dest = Path(dest) if dest else EXTRAITS_DIR / "archives" / archive.stem
    dest.mkdir(parents=True, exist_ok=True)
    n = archive.name.lower()
    try:
        if n.endswith(".zip"):
            with zipfile.ZipFile(archive) as z:
                z.extractall(dest); return True, dest, f"{len(z.namelist())} fichier(s)"
        if n.endswith(SUPPORTED[1:]):
            with tarfile.open(archive) as t:
                members = [m for m in t.getmembers()
                           if not m.name.startswith("/") and ".." not in m.name]
                t.extractall(dest, members=members); return True, dest, f"{len(members)} fichier(s)"
        return False, None, "format non supporté"
    except Exception as e:
        return False, None, str(e)

def classer_fichier(path, cat=None):
    """Copie un acte (PDF/image) dans le bon dossier de catégorie."""
    path = Path(path)
    cat = cat or detecter_cat(path.name)
    dest = _dossier(cat) / path.name
    shutil.copy2(path, dest)
    return dest, cat

def trier_telechargements():
    """Trie tout /telechargements : archives extraites, actes classés."""
    results = []
    for f in sorted(DOWNLOAD_DIR.glob("*")):
        if not f.is_file(): continue
        if f.name.lower().endswith(SUPPORTED):
            ok, dest, msg = extraire_archive(f)
            results.append((f.name, ok, msg))
        else:
            dest, cat = classer_fichier(f)
            results.append((f.name, True, f"classé → {cat}"))
    return results

def _ouvrir(app):
    win = tk.Toplevel(app.root)
    win.title("📦 Extraction des actes")
    win.geometry("560x420")
    win.configure(bg='#1a1a2e')
    tk.Label(win, text="📦 EXTRACTION & CLASSEMENT DES ACTES", bg='#16213e', fg='#00ffcc',
             font=("Consolas", 14, "bold")).pack(pady=12, fill=tk.X)

    fcat = tk.Frame(win, bg='#1a1a2e'); fcat.pack(pady=4)
    tk.Label(fcat, text="Catégorie :", bg='#1a1a2e', fg='#bb86fc',
             font=("Consolas", 10, "bold")).pack(side=tk.LEFT)
    var_cat = tk.StringVar(value="auto")
    ttk.Combobox(fcat, textvariable=var_cat, values=["auto"]+CATEGORIES, width=12).pack(side=tk.LEFT, padx=6)

    var = tk.StringVar()
    tk.Label(win, textvariable=var, bg='#161a2e', fg='white', font=("Consolas", 9),
             wraplength=500, justify="left").pack(fill=tk.X, padx=20, pady=6)
    bf = tk.Frame(win, bg='#1a1a2e'); bf.pack(pady=6)
    def _choisir():
        p = filedialog.askopenfilename(filetypes=[("Actes/Archives", "*.pdf *.jpg *.jpeg *.png *.zip *.tar *.tar.gz"), ("Tous", "*.*")])
        if p: var.set(p)
    tk.Button(bf, text="📂 Choisir", bg='#2d5a7b', fg='white', command=_choisir).pack(side=tk.LEFT, padx=4)
    def _traiter():
        if not var.get(): return
        p = Path(var.get())
        if p.name.lower().endswith(SUPPORTED):
            ok, dest, msg = extraire_archive(p)
            messagebox.showinfo("✅ Extraction", f"{msg} → {dest}" if ok else str(msg))
        else:
            cat = None if var_cat.get() == "auto" else var_cat.get()
            dest, c = classer_fichier(p, cat)
            messagebox.showinfo("✅ Classé", f"{p.name} → {c}/")
    tk.Button(bf, text="🗂️ Extraire / Classer", bg='#2d7b5a', fg='white', command=_traiter).pack(side=tk.LEFT, padx=4)
    tk.Button(win, text="🔄 Trier tout /telechargements (auto)", bg='#7b5a2d', fg='white',
              command=lambda: _trier()).pack(pady=6)

    lf = tk.LabelFrame(win, text=" Dossiers d'actes ", bg='#1e1e2e', fg='#00ffcc',
                       font=("Consolas", 10, "bold"))
    lf.pack(fill=tk.BOTH, expand=True, padx=15, pady=10)
    _rafraichir(lf)

def _trier():
    res = trier_telechargements()
    if not res: messagebox.showinfo("Info", "Rien à trier dans /telechargements")
    else:
        txt = "\n".join(f"{'✅' if ok else '❌'} {n} : {m}" for n, ok, m in res)
        messagebox.showinfo("Tri terminé", txt)

def _rafraichir(frame):
    for w in frame.winfo_children(): w.destroy()
    for cat in CATEGORIES:
        d = EXTRAITS_DIR / cat
        n = len([f for f in d.glob("*") if f.is_file()]) if d.exists() else 0
        tk.Label(frame, text=f"📁 {cat} : {n} fichier(s)", bg='#1e1e2e', fg='white',
                 font=("Consolas", 10)).pack(anchor="w", padx=8, pady=2)

def inject_buttons(app):
    tb = getattr(app, "toolbar_frame", None)
    if tb is None: return
    tk.Button(tb, text="📦 Actes", bg='#7b5a2d', fg='white',
              font=("Consolas", 10, "bold"), relief=tk.RAISED, bd=1,
              command=lambda: _ouvrir(app)).pack(side=tk.LEFT, padx=4, pady=6)

def run(cible, ctx, emit):
    return