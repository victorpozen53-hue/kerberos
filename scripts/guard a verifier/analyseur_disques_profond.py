# -*- coding: utf-8 -*-
# analyseur_disques_profond.v2.3.py
# GPLv3 – Projet Kerberos – Sécurité éthique locale pour vieux PCs (Win 7/10)
# 🛡️ https://liberapay.com/EthicalKerberos/ | Full license: https://www.gnu.org/licenses/gpl-3.0.html
# White hat only. Pas de trace. Pas de nuage. Juste du code qui protège. (-; — Victor.Pozen

import sys
import os
import platform
import traceback
from datetime import datetime
import ast
import re
import tkinter as tk
from tkinter import ttk, scrolledtext, messagebox, filedialog

# === GESTIONNAIRE D'ERREUR GLOBAL – KERBEROS v2 ===
def kerberos_excepthook(exc_type, exc_value, exc_tb):
    err = ''.join(traceback.format_exception(exc_type, exc_value, exc_tb))
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    log_dir = "logs"
    os.makedirs(log_dir, exist_ok=True)
    log_path = os.path.join(log_dir, f"kerberos_crash_{timestamp}.log")
    with open(log_path, "w", encoding="utf-8") as f:
        f.write("=== CRASH KERBEROS ===\n")
        f.write(f"Système : {platform.platform()}\n")
        f.write(f"Date : {datetime.now()}\n")
        f.write(err)
    print("💥 ERREUR KERBEROS :\n" + err, file=sys.stderr)
    print(f"📝 Log sauvegardé : {log_path}", file=sys.stderr)
    try:
        tmp = tk.Tk()
        tmp.withdraw()
        messagebox.showerror("💥 Kerberos – Erreur critique",
                             f"{exc_type.__name__}: {exc_value}\n\nLog détaillé dans :\n{log_path}")
        tmp.destroy()
    except: pass
    if not getattr(sys, 'frozen', False):
        try:
            input("\n🔴 Appuyez sur Entrée pour quitter...")
        except: pass
sys.excepthook = kerberos_excepthook
# ==============================================

# === CONFIGURATION ===
BG = "#1e1e1e"
FG = "#00ff00"
FONT_UI = ("Tahoma", 10)
FONT_MONO = ("Consolas", 10)
EXT_IMPORTANTES = {'.py', '.txt', '.log', '.json', '.csv', '.html', '.exe', '.bat', '.ini', '.xml', '.yml'}
MAX_DEPTH = 4

# === DÉTECTION DES LECTEURS (WINDOWS SEULEMENT – SANS PSUTIL) ===
def lister_lecteurs_windows():
    if platform.system() != "Windows":
        return []
    try:
        import string
        return [f"{c}:\\" for c in string.ascii_uppercase if os.path.exists(f"{c}:\\")] or ["C:\\"]
    except:
        return ["C:\\"]

# === LECTURE SÉCURISÉE DE L'ESPACE DISQUE (WINDOWS) ===
def espace_disque_win(lecteur):
    if platform.system() != "Windows":
        return "N/A"
    try:
        import ctypes
        _, total, free = ctypes.c_ulonglong(), ctypes.c_ulonglong(), ctypes.c_ulonglong()
        ctypes.windll.kernel32.GetDiskFreeSpaceExW(
            ctypes.c_wchar_p(lecteur),
            ctypes.pointer(_),
            ctypes.pointer(total),
            ctypes.pointer(free)
        )
        used = (total.value - free.value) / (1024**3)
        total_gb = total.value / (1024**3)
        return f"{used:.1f} / {total_gb:.1f} Go"
    except:
        return "⚠️ Indisponible"

# === ANALYSE SÉCURISÉE D'UN FICHIER PYTHON (v2.3) ===
DANGEROUS_PATTERNS = [
    (r"exec\s*\(", "exec détecté"),
    (r"eval\s*\(", "eval détecté"),
    (r"__import__\s*\(", "__import__ détecté"),
    (r"subprocess\.(run|Popen|call|check_output)", "subprocess utilisé"),
    (r"import\s+os\s*,\s*sys", "os + sys ensemble → système"),
    (r"shutil\.rmtree", "shutil.rmtree → suppression récursive"),
    (r"ctypes\.windll", "ctypes.windll → accès bas niveau"),
]

def analyser_fichier_py(filepath):
    """Analyse statique d’un .py — sans exécution. Retourne résumé ou '⚠️'."""
    try:
        with open(filepath, "r", encoding="utf-8", errors="ignore") as f:
            source = f.read(1024 * 10)  # Limité à 10 Ko pour perf
        
        # Syntaxe OK ?
        try:
            ast.parse(source, filename=filepath)
            syntax_ok = True
        except SyntaxError:
            return "⚠️ SyntaxError"
        except:
            syntax_ok = False

        # Imports
        imports = []
        try:
            for node in ast.walk(ast.parse(source)):
                if isinstance(node, ast.Import):
                    imports.extend(alias.name for alias in node.names)
                elif isinstance(node, ast.ImportFrom):
                    if node.module:
                        imports.append(node.module)
        except: pass

        # Recherche de motifs risqués
        risks = []
        for pattern, msg in DANGEROUS_PATTERNS:
            if re.search(pattern, source):
                risks.append(msg)

        # Format court
        parts = []
        if not syntax_ok: parts.append("❌ Syntaxe")
        if imports: parts.append("imports:" + ",".join(imports[:2]))
        if risks: parts.append("⚠️ " + " | ".join(risks[:1]))
        return " | ".join(parts) if parts else "✅ Clean"
    except:
        return "❓ Lecture impossible"

# === ARBRE DE FICHIERS AMÉLIORÉ (v2.3) ===
def arbre_securise(racine, prefix="", prof=0, max_prof=4, ignore_recycle=True):
    if prof >= max_prof:
        return [f"{prefix}└── [...] (limite profondeur)"]
    lignes = []
    try:
        elements = sorted(os.listdir(racine))
    except (OSError, PermissionError, FileNotFoundError):
        return [f"{prefix}📁 [accès refusé]"]

    # 🔒 Filtre $RECYCLE.BIN
    if ignore_recycle and os.path.basename(racine).startswith("$RECYCLE.BIN"):
        return [f"{prefix}📁 $RECYCLE.BIN (exclu)"]

    dossiers = []
    fichiers_imp = []
    autres = 0

    for e in elements:
        chemin = os.path.join(racine, e)
        try:
            if os.path.isdir(chemin):
                dossiers.append(e)
            elif os.path.isfile(chemin):
                _, ext = os.path.splitext(e)
                if ext.lower() in EXT_IMPORTANTES:
                    fichiers_imp.append(e)
                else:
                    autres += 1
        except (OSError, ValueError):
            continue

    total = len(dossiers) + len(fichiers_imp) + (1 if autres > 0 else 0)
    idx = 0

    # Dossiers
    for d in dossiers:
        # 🔒 Skip complet de $RECYCLE.BIN si demandé
        if ignore_recycle and d.upper() == "$RECYCLE.BIN":
            idx += 1
            marque = "└── " if idx == total else "├── "
            lignes.append(f"{prefix}{marque}📁 $RECYCLE.BIN (exclu)")
            continue
        idx += 1
        marque = "└── " if idx == total else "├── "
        lignes.append(f"{prefix}{marque}📁 {d}")
        suite = prefix + ("    " if idx == total else "│   ")
        lignes.extend(arbre_securise(os.path.join(racine, d), suite, prof + 1, max_prof, ignore_recycle))

    # Fichiers importants (avec analyse .py)
    for f in sorted(fichiers_imp):
        idx += 1
        marque = "└── " if idx == total else "├── "
        if f.endswith('.py'):
            analyse = analyser_fichier_py(os.path.join(racine, f))
            lignes.append(f"{prefix}{marque}🐍 {f}  [{analyse}]")
        else:
            lignes.append(f"{prefix}{marque}📄 {f}")

    # Autres fichiers
    if autres > 0:
        idx += 1
        marque = "└── " if idx == total else "├── "
        lignes.append(f"{prefix}{marque}📄 [{autres} autre(s) fichier(s)]")

    return lignes

# === INTERFACE KERBEROS – v2.3 ===
class KerberosDiskAnalyzer:
    def __init__(self, root):
        self.root = root
        root.title("🔍 Kerberos – Analyseur de Disques v2.3 (GPLv3)")
        root.geometry("900x700")
        root.configure(bg=BG)

        tk.Label(root, text="KERBEROS – Analyse Profonde Locale", 
                 fg=FG, bg=BG, font=("Consolas", 13, "bold")).pack(pady=8)

        # Options de scan
        opt_frame = tk.Frame(root, bg=BG)
        opt_frame.pack(pady=5, padx=15, fill=tk.X)

        tk.Label(opt_frame, text="✅ Sélectionnez :", fg=FG, bg=BG, font=FONT_UI).pack(anchor="w")
        tk.Label(opt_frame, text=" ▸ Lecteurs :", bg=BG, fg="#aaaaaa", font=("Consolas", 9)).pack(anchor="w", pady=(5,0))

        self.vars = {}
        self.lecteurs = lister_lecteurs_windows()
        drv_frame = tk.Frame(opt_frame, bg=BG)
        drv_frame.pack(anchor="w")
        for drv in self.lecteurs:
            var = tk.BooleanVar(value=(drv == "C:\\"))
            self.vars[drv] = var
            tk.Checkbutton(drv_frame, text=drv, variable=var,
                           bg=BG, fg=FG, selectcolor="#333", font=FONT_UI).pack(side=tk.LEFT, padx=3)

        # 🔘 Nouveau bouton : ignorer corbeille
        tk.Label(opt_frame, text=" ▸ Options :", bg=BG, fg="#aaaaaa", font=("Consolas", 9)).pack(anchor="w", pady=(5,0))
        self.ignore_recycle = tk.BooleanVar(value=True)
        tk.Checkbutton(opt_frame, text="🗑️ Ignorer $RECYCLE.BIN", variable=self.ignore_recycle,
                       bg=BG, fg=FG, selectcolor="#333", font=FONT_UI).pack(anchor="w")

        # Boutons
        btn_frame = tk.Frame(root, bg=BG)
        btn_frame.pack(pady=8)
        tk.Button(btn_frame, text="🚀 Analyser", command=self.analyser,
                  bg="#8b0000", fg="white", font=("Consolas", 11, "bold")).pack(side=tk.LEFT, padx=5)
        tk.Button(btn_frame, text="📂 Choisir un dossier", command=self.choisir_dossier,
                  bg="#2d2d2d", fg="white", font=FONT_UI).pack(side=tk.LEFT, padx=5)

        # Console
        self.console = scrolledtext.ScrolledText(
            root, wrap=tk.WORD, font=FONT_MONO,
            bg="#0a0a0a", fg=FG, insertbackground=FG
        )
        self.console.pack(fill=tk.BOTH, expand=True, padx=10, pady=(0,10))
        self.console.bind("<Key>", lambda e: "break")

        self.console.insert(tk.END, "ℹ️ Kerberos v2.3 – GPLv3\n")
        self.console.insert(tk.END, "   Analyse locale sécurisée – Compatible Windows 7/10\n")
        self.console.insert(tk.END, "   🐍 Analyse .py statique | 🗑️ Corbeille optionnelle\n\n")

    def analyser(self):
        cibles = [d for d, v in self.vars.items() if v.get()] if self.lecteurs else []
        if not cibles and self.lecteurs:
            messagebox.showwarning("Sélection requise", "Cochez au moins un lecteur.")
            return
        self.generer_rapport(cibles if cibles else ["C:\\"] if self.lecteurs else [])

    def choisir_dossier(self):
        dossier = filedialog.askdirectory(title="Sélectionner un dossier à analyser")
        if dossier:
            self.generer_rapport([dossier])

    def generer_rapport(self, cibles):
        self.console.delete(1.0, tk.END)
        self.console.insert(tk.END, "🔍 Génération du rapport en cours… (patientez)\n\n")

        # ✅ Construction hors UI → rapport complet à la fin
        lignes = []
        lignes.append("=" * 60)
        lignes.append("RAPPORT KERBEROS – ANALYSE DE DISQUES v2.3")
        lignes.append("=" * 60)
        lignes.append(f"Date : {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        lignes.append(f"Système : {platform.system()} {platform.release()}")
        lignes.append(f"Profondeur : {MAX_DEPTH}")
        lignes.append("Corbeille exclue : " + ("Oui" if self.ignore_recycle.get() else "Non"))
        lignes.append("Licence : GNU GPLv3 – https://liberapay.com/EthicalKerberos/  ")
        lignes.append("Code : https://github.com/victorpozen/kerberos")
        lignes.append("=" * 60)
        lignes.append("")

        for cible in cibles:
            lignes.append(f"\n{'='*60}\nCIBLE : {cible}\n{'='*60}")
            if os.path.exists(cible) and len(cible) == 3 and cible[1:] == ":\\":  # ex: "C:\\"
                lignes.append(f"📊 Espace : {espace_disque_win(cible)}")
            else:
                lignes.append("📊 Espace : N/A (dossier personnalisé)")
            lignes.append("\nArborescence :")
            lignes.extend(arbre_securise(cible, max_prof=MAX_DEPTH, ignore_recycle=self.ignore_recycle.get()))
            lignes.append("")

        lignes.append("✅ Rapport généré – Projet Kerberos (GPLv3)")
        rapport = "\n".join(lignes)

        # ✅ Insertion UNIQUE à la fin
        self.console.insert(tk.END, rapport)

        try:
            with open("rapport_disques_profond.txt", "w", encoding="utf-8") as f:
                f.write(rapport)
            self.console.insert(tk.END, f"\n\n💾 Sauvegardé : rapport_disques_profond.txt")
            messagebox.showinfo("✅ Succès", "Analyse terminée !\nRapport sauvegardé.")
        except Exception as e:
            self.console.insert(tk.END, f"\n\n⚠️ Erreur sauvegarde : {e}")

# === LANCEMENT ===
if __name__ == "__main__":
    root = tk.Tk()
    app = KerberosDiskAnalyzer(root)
    root.mainloop()