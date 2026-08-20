# kerberos_dependency_scanner.py
# 🔧 Scanner & réparateur de dépendances locales — Projet Kerberos
# 🧠 Par Mirko & Victor.pozen
# 📄 GPLv3 — https://www.gnu.org/licenses/gpl-3.0.html
# 💀 Pas de trace. Pas de nuage. Juste du code qui protège. `(-;`
#
# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# You should have received a copy of the GNU General Public License
# along with this program.  If not, see <https://www.gnu.org/licenses/>.
#
# 🧑‍💻 Victor.Pozen — White hat depuis 1989. Passionné de vieux PCs (Win7/10).
# 🐍 Ce scanner ne contacte AUCUN serveur. Tout reste local.

import tkinter as tk
from tkinter import scrolledtext, filedialog, messagebox, ttk
import ast
import os
import sys
import zipfile
import shutil
from pathlib import Path
import time

# === CONFIG PORTABLE ===
BASE_DIR = Path(__file__).parent.resolve()
REPAIRED_DIR = BASE_DIR / "repaired"
CACHE_DEPS_DIR = BASE_DIR / "cache" / "deps"
os.makedirs(REPAIRED_DIR, exist_ok=True)
os.makedirs(CACHE_DEPS_DIR, exist_ok=True)

# === STYLE KERBEROS-BRIDGE ===
BG_DARK = "#0d0d15"
BG_DARKER = "#0a0a12"
FG_LIGHT = "#e0e0ff"
FG_GREEN = "#a0ffa0"
FG_YELLOW = "#ffd700"
BTN_COLOR = "#2a2a2a"
BTN_TEXT = "#c0c0ff"
BTN_SAFE = "#2e7d32"
LINK_COLOR = "#a0a0ff"

DEBUG_MODE = False

def log(msg, level="info"):
    stamp = f"[{time.strftime('%H:%M:%S')}]"
    icons = {"info": "ℹ️", "warn": "⚠️", "error": "❌", "debug": "🐞", "ok": "✅"}
    icon = icons.get(level, "ℹ️")
    line = f"{stamp} {icon} {msg}\n"
    log_text.configure(state='normal')
    log_text.insert(tk.END, line)
    log_text.see(tk.END)
    log_text.configure(state='disabled')
    if level == "debug" and not DEBUG_MODE:
        return

def toggle_debug(event=None):
    global DEBUG_MODE
    DEBUG_MODE = not DEBUG_MODE
    log(f"Mode DEBUG {'activé' if DEBUG_MODE else 'désactivé'}", "debug")

# === ANALYSE DES IMPORTS ===
def scan_imports(py_path: Path):
    log(f"Scan de : {py_path.name}", "info")
    imports = set()
    try:
        with open(py_path, "r", encoding="utf-8") as f:
            tree = ast.parse(f.read(), filename=py_path.name)
        for node in ast.walk(tree):
            if isinstance(node, ast.Import):
                for alias in node.names:
                    top = alias.name.split('.')[0]
                    imports.add(top)
            elif isinstance(node, ast.ImportFrom):
                if node.module:
                    top = node.module.split('.')[0]
                    imports.add(top)
    except Exception as e:
        log(f"❌ Erreur AST : {e}", "error")
        return set()
    log(f"→ {len(imports)} imports détectés", "debug")
    return imports

# === CLASSIFICATION ===
ALLOWED_EXTERNAL = {
    "PIL": ("Pillow.zip", "PIL"),
    "psutil": ("psutil.zip", "psutil"),
}

STDLIB_MODULES = set(sys.stdlib_module_names) if hasattr(sys, 'stdlib_module_names') else {
    'os', 'sys', 'tkinter', 'subprocess', 'ctypes', 'time', 'datetime', 'pathlib',
    'shutil', 'zipfile', 'glob', 're', 'json', 'csv', 'ast', 'importlib', 'webbrowser'
}

def classify_imports(imports):
    stdlib = []
    external = []
    forbidden = []
    for imp in imports:
        if imp in STDLIB_MODULES:
            stdlib.append(imp)
        elif imp in ALLOWED_EXTERNAL:
            external.append(imp)
        else:
            forbidden.append(imp)
    return stdlib, external, forbidden

# === RÉPARATION AVEC PROGRESSION ===
def repair_script(py_path: Path, progress_var, root):
    filename = py_path.stem
    target_dir = REPAIRED_DIR / filename
    deps_dir = target_dir / "deps"

    # Étape 1/5 : préparation
    progress_var.set(0); root.update_idletasks()
    log("🔧 Étape 1/5 : Préparation du dossier…", "info")
    if target_dir.exists():
        shutil.rmtree(target_dir)
    os.makedirs(deps_dir, exist_ok=True)
    shutil.copy(py_path, target_dir / py_path.name)
    progress_var.set(20); root.update_idletasks()

    # Étape 2/5 : analyse
    log("🔍 Étape 2/5 : Analyse des imports…", "info")
    imports = scan_imports(py_path)
    stdlib, external, forbidden = classify_imports(imports)
    progress_var.set(40); root.update_idletasks()

    # Étape 3/5 : stdlib
    log(f"✅ Stdlib : {len(stdlib)} modules", "ok")
    progress_var.set(50); root.update_idletasks()

    # Étape 4/5 : dépendances externes
    if external:
        log(f"📦 Décompression de {len(external)} dépendances…", "info")
        for i, imp in enumerate(external):
            zip_name, target_sub = ALLOWED_EXTERNAL[imp]
            zip_path = CACHE_DEPS_DIR / zip_name
            if not zip_path.exists():
                log(f"❌ Manquant : {zip_name}", "error")
                messagebox.showerror("Erreur", f"Placez {zip_name} dans :\n{CACHE_DEPS_DIR}")
                progress_var.set(0)
                return False
            try:
                with zipfile.ZipFile(zip_path, 'r') as zf:
                    members = [m for m in zf.namelist() if m.startswith(target_sub + "/")]
                    for j, member in enumerate(members):
                        zf.extract(member, deps_dir)
                        # Mini-progression dans l’étape
                        sub_prog = 60 + (i * 20 / len(external)) + (j * 20 / (len(members) * len(external) + 1))
                        progress_var.set(sub_prog); root.update_idletasks()
                log(f"   → {imp} installé", "ok")
            except Exception as e:
                log(f"   ❌ {imp} : {e}", "error")
                progress_var.set(0)
                return False
    else:
        log("📦 Aucune dépendance externe.", "ok")
    progress_var.set(80); root.update_idletasks()

    # Étape 5/5 : rapport
    log("📝 Étape 5/5 : Génération du rapport…", "info")
    log_path = target_dir / "repair_log.txt"
    with open(log_path, "w", encoding="utf-8") as f:
        f.write(f"Kerberos Dependency Repair Log\n")
        f.write(f"Date : {time.strftime('%Y-%m-%d %H:%M:%S')}\n")
        f.write(f"Fichier : {py_path.name}\n")
        f.write(f"\n✅ Stdlib ({len(stdlib)}) : {', '.join(sorted(stdlib))}\n")
        f.write(f"📦 Externes ({len(external)}) : {', '.join(sorted(external)) if external else '—'}\n")
        f.write(f"🚫 Bloqués ({len(forbidden)}) : {', '.join(sorted(forbidden)) if forbidden else '—'}\n")
        f.write(f"\n➡️ Utilisez :\nimport sys\nsys.path.insert(0, 'deps')\n")
    progress_var.set(100); root.update_idletasks()
    time.sleep(0.3)

    log(f"✅ Terminé : {target_dir.relative_to(BASE_DIR)}", "ok")
    messagebox.showinfo("✅ Succès", f"Dossier créé :\n{target_dir}")
    progress_var.set(0)
    return True

# === INTERFACE AVEC BARRE DE PROGRESSION ===
def create_gui():
    global root, log_text, progress_var
    root = tk.Tk()
    root.title("🔧 KERBEROS — Réparateur de Dépendances Locales")
    root.geometry("840x580")
    root.configure(bg=BG_DARK)
    root.resizable(False, False)

    # En-tête
    tk.Label(root, text="🔧 KERBEROS — Réparateur Local", font=("Consolas", 14, "bold"), fg="#a0ffa0", bg="#080810").pack(fill=tk.X, ipady=8)
    tk.Label(root, text="DRAG & DROP • ZÉRO RÉSEAU • GPLv3", font=("Consolas", 8), fg="#7070a0", bg="#080810").pack(fill=tk.X)

    # Zone de drop
    drop_frame = tk.Frame(root, bg="#2a2a2a", relief="groove", bd=1)
    drop_frame.pack(pady=15, padx=40, fill=tk.X)
    drop_label = tk.Label(drop_frame, text="📁 Glissez un fichier .py ici", 
                          font=("Consolas", 12), fg=FG_LIGHT, bg=drop_frame["bg"])
    drop_label.pack(pady=20)

    def on_drop(event):
        files = root.tk.splitlist(event.data)
        for f in files:
            if f.endswith('.py'):
                global current_py
                current_py = Path(f)
                drop_label.config(text=f"✅ Sélectionné : {current_py.name}", fg=FG_GREEN)
                repair_btn.config(state="normal")
                log(f"Fichier chargé : {current_py}", "ok")
                return
        log("⚠️ Seuls les .py sont acceptés.", "warn")

    try:
        from tkinterdnd2 import TkinterDnD, DND_FILES
        root = TkinterDnD.Tk()
        root.geometry("840x580")
        root.configure(bg=BG_DARK)
        drop_frame = tk.Frame(root, bg="#2a2a2a", relief="groove", bd=1)
        drop_frame.pack(pady=15, padx=40, fill=tk.X)
        drop_label = tk.Label(drop_frame, text="📁 Glissez un fichier .py ici", 
                              font=("Consolas", 12), fg=FG_LIGHT, bg=drop_frame["bg"])
        drop_label.pack(pady=20)
        drop_frame.drop_target_register(DND_FILES)
        drop_frame.dnd_bind('<<Drop>>', on_drop)
    except ImportError:
        root = tk.Tk()
        root.geometry("840x580")
        root.configure(bg=BG_DARK)
        tk.Label(root, text="🔧 KERBEROS — Réparateur (sans DnD)", font=("Consolas", 14, "bold"), fg="#a0ffa0", bg="#080810").pack(fill=tk.X, ipady=8)
        def select_file():
            f = filedialog.askopenfilename(filetypes=[("Python", "*.py")])
            if f:
                global current_py
                current_py = Path(f)
                drop_label.config(text=f"✅ {current_py.name}", fg=FG_GREEN)
                repair_btn.config(state="normal")
        drop_label = tk.Label(root, text="📂 Cliquez pour ouvrir un .py", font=("Consolas", 12), fg=FG_LIGHT, bg=BG_DARK)
        drop_label.pack(pady=20)
        tk.Button(root, text="📂 Ouvrir…", command=select_file, bg=BTN_COLOR, fg=BTN_TEXT).pack()

    # Barre de progression (toujours présente)
    progress_var = tk.DoubleVar(value=0)
    progress_bar = ttk.Progressbar(root, variable=progress_var, maximum=100, style="Kerberos.Horizontal.TProgressbar")
    progress_bar.pack(padx=40, fill=tk.X, pady=(5,15))

    # Style barre (sombre, verte quand active)
    style = ttk.Style()
    style.theme_use('clam')
    style.configure("Kerberos.Horizontal.TProgressbar",
                    troughcolor=BG_DARKER,
                    background=BTN_SAFE,
                    thickness=8)

    # Bouton
    repair_btn = tk.Button(root, text="🔧 Réparer localement", 
                           command=lambda: repair_script(current_py, progress_var, root) if 'current_py' in globals() else None,
                           width=48, height=2, bg=BTN_SAFE, fg="white",
                           font=("Consolas", 10, "bold"), state="disabled")
    repair_btn.pack(pady=5)

    # Journal
    log_frame = tk.LabelFrame(root, text=" 📜 Journal (Ctrl+D → debug)", bg=BG_DARK, fg=FG_YELLOW, font=("Consolas", 9))
    log_frame.pack(padx=15, pady=(10,8), fill=tk.X)
    log_text = scrolledtext.ScrolledText(log_frame, height=8, bg=BG_DARKER, fg=FG_GREEN, font=("Consolas", 9))
    log_text.pack(fill=tk.BOTH, expand=True)
    log_text.configure(state='disabled')

    # À propos
    tk.Label(root, text="🧑‍💻 Victor.Pozen — White hat depuis 1989. Pas de trace. Pas de nuage.", 
             fg=FG_LIGHT, bg=BG_DARK, font=("Consolas", 9)).pack(pady=5)

    root.bind("<Control-d>", toggle_debug)
    log("✅ Prêt. Glissez (ou ouvrez) un .py.", "info")
    root.mainloop()

if __name__ == "__main__":
    create_gui()