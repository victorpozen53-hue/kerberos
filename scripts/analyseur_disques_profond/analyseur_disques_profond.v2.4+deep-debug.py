# -*- coding: utf-8 -*-
# analyseur_disques_profond.v2.4+deep-debug.py
# GPLv3 – Projet Kerberos – Sécurité éthique locale pour vieux PCs (Win 7/10)
# 🛡️ https://liberapay.com/EthicalKerberos/ | Full license: https://www.gnu.org/licenses/gpl-3.0.html
# White hat only. Pas de trace. Pas de nuage. Juste du code qui protège. (-; — Victor.Pozen

# === 🔧 DEBUG MODE FORCÉ (console + log) ===
import sys
import ctypes
import traceback
import os

# Force console if not frozen
if not getattr(sys, 'frozen', False):
    try:
        ctypes.windll.kernel32.AllocConsole()
        sys.stdout = open('CONOUT$', 'w')
        sys.stderr = open('CONOUT$', 'w')
        print("✅ [DEBUG] Console forcée — erreurs affichées ici.")
    except:
        pass

# Log de démarrage
DEBUG_LOG = r"H:\kerb-startup-debug.log"
with open(DEBUG_LOG, "w", encoding="utf-8") as f:
    f.write("=== KERBEROS DEBUG START ===\n")
    f.write(f"Python: {sys.version}\n")
    f.write(f"argv[0]: {sys.argv[0]}\n")
    f.write(f"cwd: {os.getcwd()}\n")
print(f"📝 Log de démarrage : {DEBUG_LOG}")

# === IMPORTS (avec gestion d'erreur détaillée) ===
try:
    import platform
    import hashlib
    from datetime import datetime
    import ast
    import re
    print("✅ Imports de base OK")
except Exception as e:
    print(f"❌ Échec imports basiques : {e}")
    input("Appuyez sur Entrée pour quitter...")
    sys.exit(1)

try:
    import tkinter as tk
    from tkinter import ttk, scrolledtext, messagebox, filedialog
    print("✅ Tkinter OK")
except Exception as e:
    print(f"❌ Échec Tkinter : {e}")
    traceback.print_exc()
    input("Appuyez sur Entrée pour quitter...")
    sys.exit(1)

# === CONFIGURATION ===
BG = "#1e1e1e"
FG = "#00ff00"
FONT_UI = ("Tahoma", 10)
FONT_MONO = ("Consolas", 10)
EXT_IMPORTANTES = {'.py', '.txt', '.log', '.json', '.csv', '.html', '.exe', '.bat', '.ini', '.xml', '.yml'}
MAX_DEPTH = 4
MAX_DEPTH_FULL = 8
MAX_ITEMS_PER_DIR = 200

# === UTILITAIRES DISQUE (robustifiés) ===
def lister_lecteurs_windows():
    try:
        if platform.system() != "Windows":
            return ["C:\\"]
        import string
        return [f"{c}:\\" for c in string.ascii_uppercase if os.path.exists(f"{c}:\\")] or ["C:\\"]
    except Exception as e:
        print(f"⚠️ lister_lecteurs_windows() → {e}")
        return ["C:\\"]

def espace_disque_win(lecteur):
    try:
        if platform.system() != "Windows":
            return "N/A"
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
    except Exception as e:
        print(f"⚠️ espace_disque_win({lecteur}) → {e}")
        return "⚠️ Indisponible"

# === ANALYSE .PY (safe) ===
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
    try:
        with open(filepath, "r", encoding="utf-8", errors="ignore") as f:
            source = f.read(1024 * 10)
        try:
            ast.parse(source, filename=filepath)
            syntax_ok = True
        except SyntaxError:
            return "⚠️ SyntaxError"
        except:
            syntax_ok = False

        imports = []
        try:
            for node in ast.walk(ast.parse(source)):
                if isinstance(node, ast.Import):
                    imports.extend(alias.name for alias in node.names)
                elif isinstance(node, ast.ImportFrom):
                    if node.module:
                        imports.append(node.module)
        except: pass

        risks = []
        for pattern, msg in DANGEROUS_PATTERNS:
            if re.search(pattern, source):
                risks.append(msg)

        parts = []
        if not syntax_ok: parts.append("❌ Syntaxe")
        if imports: parts.append("imports:" + ",".join(imports[:2]))
        if risks: parts.append("⚠️ " + " | ".join(risks[:1]))
        return " | ".join(parts) if parts else "✅ Clean"
    except Exception as e:
        return f"❓ {type(e).__name__}"

# === ARBRE SÉCURISÉ (robuste) ===
def arbre_securise(racine, prefix="", prof=0, max_prof=4, ignore_recycle=True, limit_per_dir=MAX_ITEMS_PER_DIR):
    try:
        if prof >= max_prof:
            return [f"{prefix}└── [...] (limite profondeur {prof}/{max_prof})"]
        lignes = []
        elements = sorted(os.listdir(racine))
        if ignore_recycle and os.path.basename(racine).startswith("$RECYCLE.BIN"):
            return [f"{prefix}📁 $RECYCLE.BIN (exclu)"]

        elements = elements[:limit_per_dir]
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
            except: pass

        total = len(dossiers) + len(fichiers_imp) + (1 if autres > 0 else 0)
        idx = 0

        for d in dossiers:
            if ignore_recycle and d.upper() == "$RECYCLE.BIN":
                idx += 1
                marque = "└── " if idx == total else "├── "
                lignes.append(f"{prefix}{marque}📁 $RECYCLE.BIN (exclu)")
                continue
            idx += 1
            marque = "└── " if idx == total else "├── "
            lignes.append(f"{prefix}{marque}📁 {d}")
            suite = prefix + ("    " if idx == total else "│   ")
            sous = arbre_securise(os.path.join(racine, d), suite, prof+1, max_prof, ignore_recycle, limit_per_dir)
            lignes.extend(sous)

        for f in sorted(fichiers_imp):
            idx += 1
            marque = "└── " if idx == total else "├── "
            if f.endswith('.py'):
                analyse = analyser_fichier_py(os.path.join(racine, f))
                lignes.append(f"{prefix}{marque}🐍 {f}  [{analyse}]")
            else:
                lignes.append(f"{prefix}{marque}📄 {f}")

        if autres > 0:
            idx += 1
            marque = "└── " if idx == total else "├── "
            lignes.append(f"{prefix}{marque}📄 [{autres} autre(s) fichier(s)]")

        return lignes
    except Exception as e:
        return [f"{prefix}💥 Erreur arbre : {e}"]

# === INTERFACE KERBEROS (avec safeguard) ===
class KerberosDiskAnalyzer:
    def __init__(self, root):
        self.root = root
        self.selected_path = None
        root.title("🔍 Kerberos – v2.4+deep-debug (GPLv3)")
        root.geometry("920x740")
        root.configure(bg=BG)

        try:
            tk.Label(root, text="KERBEROS – Analyse Profonde (DEBUG MODE)",
                     fg=FG, bg=BG, font=("Consolas", 13, "bold")).pack(pady=8)

            opt_frame = tk.Frame(root, bg=BG)
            opt_frame.pack(pady=5, padx=15, fill=tk.X)

            tk.Label(opt_frame, text="✅ Mode debug actif", fg="#ffaa00", bg=BG, font=("Consolas", 10, "bold")).pack(anchor="w")
            tk.Label(opt_frame, text=f"   Log : {DEBUG_LOG}", fg="#aaaaaa", bg=BG, font=("Consolas", 9)).pack(anchor="w")

            # Options
            self.vars = {}
            self.lecteurs = lister_lecteurs_windows()
            drv_frame = tk.Frame(opt_frame, bg=BG)
            drv_frame.pack(anchor="w")
            for drv in self.lecteurs:
                var = tk.BooleanVar(value=(drv == "C:\\"))
                self.vars[drv] = var
                tk.Checkbutton(drv_frame, text=drv, variable=var,
                               bg=BG, fg=FG, selectcolor="#333", font=FONT_UI).pack(side=tk.LEFT, padx=3)

            self.ignore_recycle = tk.BooleanVar(value=True)
            self.deep_scan = tk.BooleanVar(value=False)
            tk.Checkbutton(opt_frame, text="🗑️ Ignorer $RECYCLE.BIN", variable=self.ignore_recycle,
                           bg=BG, fg=FG, selectcolor="#333", font=FONT_UI).pack(anchor="w")
            tk.Checkbutton(opt_frame, text="🔍 Profondeur étendue (max 8 niveaux)", variable=self.deep_scan,
                           bg=BG, fg="#88ccff", selectcolor="#333", font=FONT_UI).pack(anchor="w")

            # Boutons
            btn_frame1 = tk.Frame(root, bg=BG)
            btn_frame1.pack(pady=6)
            tk.Button(btn_frame1, text="📂 Choisir dossier", command=self.choisir_dossier,
                      bg="#2d2d2d", fg="white", font=FONT_UI).pack(side=tk.LEFT, padx=4)
            tk.Button(btn_frame1, text="🔍 Prescan", command=self.prescan,
                      bg="#3a3a3a", fg="#00ccff", font=FONT_UI).pack(side=tk.LEFT, padx=4)
            tk.Button(btn_frame1, text="📸 Créer image", command=self.creer_image,
                      bg="#004d00", fg="white", font=FONT_UI).pack(side=tk.LEFT, padx=4)

            btn_frame2 = tk.Frame(root, bg=BG)
            btn_frame2.pack(pady=4)
            tk.Button(btn_frame2, text="🚀 Analyser TOUT", command=self.analyser,
                      bg="#8b0000", fg="white", font=("Consolas", 11, "bold")).pack(side=tk.LEFT, padx=4)
            tk.Button(btn_frame2, text="🔍 Full scan (tous les fichiers)", command=self.full_scan,
                      bg="#0066aa", fg="white", font=("Consolas", 10)).pack(side=tk.LEFT, padx=4)

            # Console
            self.console = scrolledtext.ScrolledText(
                root, wrap=tk.WORD, font=FONT_MONO,
                bg="#0a0a0a", fg=FG, insertbackground=FG
            )
            self.console.pack(fill=tk.BOTH, expand=True, padx=14, pady=(8,12))
            self.console.bind("<Key>", lambda e: "break")

            self.console.insert(tk.END, "== KERBEROS DEBUG MODE ==\n")
            self.console.insert(tk.END, "✅ Interface chargée avec succès.\n")
            self.console.insert(tk.END, "➡️ Cochez un lecteur et cliquez [🚀 Analyser TOUT].\n")

        except Exception as e:
            print(f"❌ Erreur création UI : {e}")
            traceback.print_exc()
            messagebox.showerror("💥 Erreur UI", f"{e}\nVoir {DEBUG_LOG}")

    def prescan(self):
        try:
            dossier = filedialog.askdirectory(title="🔍 Prescan")
            if not dossier: return
            self.console.delete(1.0, tk.END)
            self.console.insert(tk.END, f"🔍 Prescan : {dossier}\n")
            self.console.insert(tk.END, "\n".join(arbre_securise(dossier, max_prof=2, limit_per_dir=50)))
        except Exception as e:
            self.console.insert(tk.END, f"\n❌ Prescan échoué : {e}\n")
            print(f"❌ Prescan : {e}")

    def creer_image(self):
        try:
            if not self.selected_path:
                messagebox.showwarning("⚠️", "Choisissez d’abord un dossier.")
                return
            sortie = f"kerb_image_debug.kbi"
            lignes = [f"KERBEROS DEBUG IMAGE — {datetime.now()}"]
            with open(sortie, "w", encoding="utf-8") as f:
                f.write("\n".join(lignes))
            self.console.insert(tk.END, f"\n📸 Image debug : {sortie}\n")
        except Exception as e:
            self.console.insert(tk.END, f"\n❌ Image échouée : {e}\n")

    def analyser(self):
        self._lancer_rapport(full=False)

    def full_scan(self):
        self._lancer_rapport(full=True)

    def _lancer_rapport(self, full=False):
        try:
            cibles = [d for d, v in self.vars.items() if v.get()] or ["C:\\"]
            self.console.delete(1.0, tk.END)
            self.console.insert(tk.END, f"🚀 Rapport {'FULL' if full else 'standard'}…\n")

            lignes = [
                "="*60,
                "RAPPORT KERBEROS — v2.4+deep-debug",
                "="*60,
                f"Date : {datetime.now()}",
                f"Système : {platform.platform()}",
                f"Profondeur : {MAX_DEPTH_FULL if full or self.deep_scan.get() else MAX_DEPTH}",
                "Licence : GNU GPLv3",
                "="*60, ""
            ]

            for cible in cibles:
                lignes.append(f"\n{'='*60}\nCIBLE : {cible}\n{'='*60}")
                lignes.append(f"📊 Espace : {espace_disque_win(cible)}")
                lignes.extend(arbre_securise(cible, max_prof=MAX_DEPTH_FULL if full else MAX_DEPTH))

            lignes.append("\n✅ Rapport généré — Mode debug actif.")
            self.console.insert(tk.END, "\n".join(lignes))
        except Exception as e:
            msg = f"❌ Génération rapport échouée : {e}"
            self.console.insert(tk.END, f"\n{msg}\n")
            print(msg)
            traceback.print_exc()

    def choisir_dossier(self):
        try:
            dossier = filedialog.askdirectory()
            if dossier:
                self.selected_path = dossier
                self.console.insert(tk.END, f"\n🎯 Dossier : {dossier}\n")
        except Exception as e:
            print(f"❌ Choisir dossier : {e}")

# === LANCEMENT (try/except final) ===
if __name__ == "__main__":
    try:
        print("🔧 Démarrage de Tk…")
        root = tk.Tk()
        print("✅ Tk root créé")
        app = KerberosDiskAnalyzer(root)
        print("✅ App initialisée")
        root.mainloop()
        print("✅ Mainloop terminé")
    except Exception as e:
        err = "".join(traceback.format_exception(type(e), e, e.__traceback__))
        print("💥 ERREUR FATALE :\n" + err)
        with open(DEBUG_LOG, "a", encoding="utf-8") as f:
            f.write("\n=== ERREUR FATALE ===\n")
            f.write(err)
        try:
            messagebox.showerror("💥 Kerberos – Erreur fatale", f"{e}\nLog : {DEBUG_LOG}")
        except:
            pass
        input("\n🔴 Appuyez sur Entrée pour quitter…")