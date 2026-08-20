# -*- coding: utf-8 -*-
# analyseur_disques_profond.v3.0.py
# GPLv3 – Projet Kerberos – Sécurité éthique locale pour vieux PCs (Win 7/10)
# 🛡️ https://liberapay.com/EthicalKerberos/ | Code: https://github.com/victorpozen/kerberos
# White hat only. Pas de trace. Pas de nuage. Juste du code qui protège. (-; — Victor.Pozen

import sys
import os
import platform
import traceback
import ctypes
from datetime import datetime
import hashlib
import ast
import re
import tkinter as tk
from tkinter import ttk, scrolledtext, messagebox, filedialog, Toplevel

# === MODULE DEBUG KERBEROS – v3.0 (inline, pas de fichier externe) ===
class KerberosDebug:
    @staticmethod
    def is_admin():
        try:
            return ctypes.windll.shell32.IsUserAnAdmin() != 0
        except:
            return False

    @staticmethod
    def debug_context():
        """Capture l'état complet du système — pour logs/debug."""
        ctx = {
            "timestamp": datetime.now().isoformat(),
            "os": platform.platform(),
            "python": sys.version,
            "executable": sys.executable,
            "cwd": os.getcwd(),
            "is_admin": KerberosDebug.is_admin(),
            "argv": sys.argv,
            "guards_present": [f for f in os.listdir(".") if f.startswith("guard_") and f.endswith(".py")] if os.path.exists(".") else [],
            "env_keys": list(os.environ.keys())[:10]  # seulement les noms, pas les valeurs sensibles
        }
        return ctx

    @staticmethod
    def log_debug(msg, level="INFO"):
        log_dir = "logs"
        os.makedirs(log_dir, exist_ok=True)
        log_path = os.path.join(log_dir, f"debug_{datetime.now().strftime('%Y%m%d')}.log")
        ctx = KerberosDebug.debug_context()
        with open(log_path, "a", encoding="utf-8") as f:
            f.write(f"[{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}] [{level}] {msg}\n")
            if level == "CRITICAL":
                f.write(f"  CONTEXT: {ctx}\n")

    @staticmethod
    def make_backup(filepath):
        if os.path.isfile(filepath):
            bak = filepath + ".bak"
            try:
                with open(filepath, "rb") as src, open(bak, "wb") as dst:
                    dst.write(src.read())
                KerberosDebug.log_debug(f"Backup créé : {bak}", "INFO")
            except Exception as e:
                KerberosDebug.log_debug(f"Échec backup {filepath} → {e}", "WARNING")

# === GESTIONNAIRE D'ERREUR GLOBAL – KERBEROS v3.0 (amélioré) ===
def kerberos_excepthook(exc_type, exc_value, exc_tb):
    err = ''.join(traceback.format_exception(exc_type, exc_value, exc_tb))
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    log_dir = "logs"
    os.makedirs(log_dir, exist_ok=True)
    log_path = os.path.join(log_dir, f"kerberos_crash_{timestamp}.log")
    ctx = KerberosDebug.debug_context()
    with open(log_path, "w", encoding="utf-8") as f:
        f.write("=== CRASH KERBEROS v3.0 ===\n")
        for k, v in ctx.items():
            f.write(f"{k}: {v}\n")
        f.write("\n=== TRACEBACK ===\n")
        f.write(err)
    print("💥 ERREUR KERBEROS :\n" + err, file=sys.stderr)
    print(f"📝 Log sauvegardé : {log_path}", file=sys.stderr)
    try:
        tmp = tk.Tk()
        tmp.withdraw()
        msg = f"{exc_type.__name__}: {exc_value}\n\nContexte détaillé dans :\n{log_path}"
        messagebox.showerror("💥 Kerberos – Erreur critique", msg)
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

# === UTILS KERNEL ===
def lister_lecteurs_windows():
    if platform.system() != "Windows":
        return []
    try:
        import string
        return [f"{c}:\\" for c in string.ascii_uppercase if os.path.exists(f"{c}:\\")] or ["C:\\"]
    except:
        return ["C:\\"]

def espace_disque_win(lecteur):
    if platform.system() != "Windows":
        return "N/A"
    try:
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

# === ANALYSE COMPLÈTE D’UN FICHIER PYTHON (v3.0) ===
DANGEROUS_PATTERNS = [
    (r"exec\s*\(", "exec détecté"),
    (r"eval\s*\(", "eval détecté"),
    (r"__import__\s*\(", "__import__ détecté"),
    (r"subprocess\.(run|Popen|call|check_output)", "subprocess utilisé"),
    (r"import\s+os\s*,\s*sys", "os + sys ensemble → système"),
    (r"shutil\.rmtree", "shutil.rmtree → suppression récursive"),
    (r"ctypes\.windll", "ctypes.windll → accès bas niveau"),
    (r"socket\.", "accès réseau → vérifier usage"),
]

def analyser_fichier_py_complet(filepath):
    """
    Analyse complète d’un .py — lecture entière + vérif intégrité.
    Retourne dict avec status, résumé, risques, et info technique.
    """
    result = {
        "filepath": filepath,
        "status": "unknown",
        "summary": "",
        "imports": [],
        "risks": [],
        "size_bytes": 0,
        "is_complete": True,
        "encoding": "utf-8",
        "hash_sha1": "",
        "syntax_ok": False,
        "truncated": False,
    }

    try:
        # 🔹 Lecture entière (pas de 10 Ko)
        with open(filepath, "rb") as f:
            raw = f.read()
        result["size_bytes"] = len(raw)

        # 🔹 Détection encodage simple
        try:
            text = raw.decode("utf-8")
            result["encoding"] = "utf-8"
        except UnicodeDecodeError:
            try:
                text = raw.decode("utf-8-sig")  # pour BOM Windows
                result["encoding"] = "utf-8-sig"
            except:
                result["encoding"] = "inconnu"
                result["status"] = "corrupted"
                result["summary"] = "⚠️ Encodage invalide"
                return result

        # 🔹 Hash rapide (pour détection corruption binaire)
        result["hash_sha1"] = hashlib.sha1(raw).hexdigest()[:8]

        # 🔹 Vérif troncature : si finit par '\x00' ou coupure brutale
        if b"\x00" in raw[-16:] or (len(raw) > 10 and raw[-10:].count(b"\x00") > 3):
            result["truncated"] = True
            result["is_complete"] = False

        # 🔹 Syntaxe complète (ast.parse sur tout le texte)
        try:
            tree = ast.parse(text, filename=filepath)
            result["syntax_ok"] = True
        except SyntaxError as se:
            result["syntax_ok"] = False
            if se.lineno == text.count("\n") + 1:  # dernière ligne
                result["truncated"] = True
                result["is_complete"] = False
                result["summary"] = "⚠️ Tronqué (SyntaxError à EOF)"
                result["status"] = "corrupted"
                return result
            else:
                result["summary"] = f"⚠️ SyntaxError L{se.lineno}"
                result["status"] = "error"
                return result
        except Exception:
            result["syntax_ok"] = False

        # 🔹 Imports
        try:
            for node in ast.walk(tree):
                if isinstance(node, ast.Import):
                    result["imports"].extend(alias.name for alias in node.names)
                elif isinstance(node, ast.ImportFrom):
                    if node.module:
                        result["imports"].append(node.module)
        except: pass
        result["imports"] = list(set(result["imports"]))

        # 🔹 Recherche de motifs risqués
        for pattern, msg in DANGEROUS_PATTERNS:
            if re.search(pattern, text):
                result["risks"].append(msg)

        # 🔹 Décision finale
        if not result["is_complete"]:
            result["status"] = "corrupted"
        elif result["risks"]:
            result["status"] = "risky"
        elif result["syntax_ok"]:
            result["status"] = "clean"
        else:
            result["status"] = "error"

        # 🔹 Résumé lisible
        parts = []
        if result["status"] == "clean":
            parts.append("✅ Clean")
        elif result["status"] == "corrupted":
            parts.append("❌ Tronqué / corrompu")
        elif result["status"] == "risky":
            parts.append("⚠️ " + " | ".join(result["risks"][:1]))
        else:
            parts.append("❓ Erreur syntaxe")

        if result["imports"]:
            parts.append("imports:" + ",".join(sorted(result["imports"])[:2]))
        if not result["is_complete"]:
            parts.append("🚨 Incomplet")

        result["summary"] = " | ".join(parts) if parts else "✅ Clean"
        return result

    except PermissionError:
        result["status"] = "denied"
        result["summary"] = "🔒 Accès refusé"
        return result
    except Exception as e:
        result["status"] = "error"
        result["summary"] = f"💥 {type(e).__name__}"
        return result

# === ARBRE AMÉLIORÉ (v3.0) – utilise analyser_fichier_py_complet ===
def arbre_securise_v3(root_path, prefix="", depth=0, max_depth=4, ignore_recycle=True):
    if depth >= max_depth:
        return [f"{prefix}└── [...] (limite profondeur {max_depth})"]
    lines = []
    try:
        entries = sorted(os.listdir(root_path))
    except (OSError, PermissionError, FileNotFoundError):
        return [f"{prefix}📁 [accès refusé]"]

    # 🔒 Exclure $RECYCLE.BIN
    if ignore_recycle and os.path.basename(root_path).upper() == "$RECYCLE.BIN":
        return []

    dirs = []
    important_files = []
    other_count = 0

    for e in entries:
        path = os.path.join(root_path, e)
        try:
            if os.path.isdir(path):
                dirs.append(e)
            elif os.path.isfile(path):
                _, ext = os.path.splitext(e)
                if ext.lower() in EXT_IMPORTANTES:
                    important_files.append(e)
                else:
                    other_count += 1
        except (OSError, ValueError):
            continue

    total = len(dirs) + len(important_files) + (1 if other_count > 0 else 0)
    idx = 0

    # ➕ Dossiers
    for d in dirs:
        if ignore_recycle and d.upper() == "$RECYCLE.BIN":
            continue
        idx += 1
        mark = "└── " if idx == total else "├── "
        lines.append(f"{prefix}{mark}📁 {d}")
        next_prefix = prefix + ("    " if idx == total else "│   ")
        lines.extend(arbre_securise_v3(os.path.join(root_path, d), next_prefix, depth + 1, max_depth, ignore_recycle))

    # ➕ Fichiers importants
    for f in sorted(important_files):
        idx += 1
        mark = "└── " if idx == total else "├── "
        if f.endswith('.py'):
            analysis = analyser_fichier_py_complet(os.path.join(root_path, f))
            lines.append(f"{prefix}{mark}🐍 {f}  [{analysis['summary']}]")
        else:
            lines.append(f"{prefix}{mark}📄 {f}")

    # ➕ Autres fichiers
    if other_count > 0:
        idx += 1
        mark = "└── " if idx == total else "├── "
        lines.append(f"{prefix}{mark}📄 [{other_count} autre(s)]")

    return lines

# === PRÉ-ANALYSE DOSSIER (DEV-FRIENDLY) ===
def preanalyse_dossier(dossier):
    stats = {
        "total_files": 0,
        "total_dirs": 0,
        "py_files": 0,
        "py_bytes": 0,
        "risky_files": 0,
        "corrupted_files": 0,
        "total_bytes": 0,
        "sample_py": []
    }

    try:
        for root, dirs, files in os.walk(dossier):
            stats["total_dirs"] += len(dirs)
            stats["total_files"] += len(files)
            for f in files:
                path = os.path.join(root, f)
                try:
                    size = os.path.getsize(path)
                    stats["total_bytes"] += size
                    _, ext = os.path.splitext(f)
                    if ext.lower() == ".py":
                        stats["py_files"] += 1
                        stats["py_bytes"] += size
                        if len(stats["sample_py"]) < 3:
                            stats["sample_py"].append(f)
                        # Analyse rapide (sans arbre complet)
                        res = analyser_fichier_py_complet(path)
                        if res["status"] == "risky":
                            stats["risky_files"] += 1
                        elif res["status"] == "corrupted":
                            stats["corrupted_files"] += 1
                except: pass
    except: pass
    return stats

# === INTERFACE KERBEROS v3.0 – DEV MODE ===
class KerberosDiskAnalyzer:
    def __init__(self, root):
        self.root = root
        root.title("🔍 Kerberos – Analyseur de Disques v3.0 (GPLv3 – DEV Mode)")
        root.geometry("980x720")
        root.configure(bg=BG)

        # Entête
        tk.Label(root, text="KERBEROS v3.0", fg=FG, bg=BG, font=("Consolas", 14, "bold")).pack(pady=6)
        tk.Label(root, text="Analyse Profonde Locale – Sécurité Éthique – GPLv3", 
                 fg="#aaaaaa", bg=BG, font=("Tahoma", 9)).pack()

        # Options
        opt_frame = tk.Frame(root, bg=BG)
        opt_frame.pack(pady=6, padx=12, fill=tk.X)

        tk.Label(opt_frame, text="✅ Sélectionnez :", fg=FG, bg=BG, font=FONT_UI).pack(anchor="w")
        tk.Label(opt_frame, text=" ▸ Lecteurs :", bg=BG, fg="#aaaaaa", font=("Consolas", 9)).pack(anchor="w", pady=(4,0))

        self.vars = {}
        self.lecteurs = lister_lecteurs_windows()
        drv_frame = tk.Frame(opt_frame, bg=BG)
        drv_frame.pack(anchor="w")
        for drv in self.lecteurs[:6]:  # éviter débordement
            var = tk.BooleanVar(value=(drv == "C:\\"))
            self.vars[drv] = var
            tk.Checkbutton(drv_frame, text=drv, variable=var,
                           bg=BG, fg=FG, selectcolor="#333", font=FONT_UI).pack(side=tk.LEFT, padx=3)

        # Options avancées
        tk.Label(opt_frame, text=" ▸ Options :", bg=BG, fg="#aaaaaa", font=("Consolas", 9)).pack(anchor="w", pady=(6,0))
        self.ignore_recycle = tk.BooleanVar(value=True)
        tk.Checkbutton(opt_frame, text="🗑️ Ignorer $RECYCLE.BIN", variable=self.ignore_recycle,
                       bg=BG, fg=FG, selectcolor="#333", font=FONT_UI).pack(anchor="w")

        # Boutons
        btn_frame = tk.Frame(root, bg=BG)
        btn_frame.pack(pady=6)

        tk.Button(btn_frame, text="🚀 Analyser sélection", command=self.analyser,
                  bg="#8b0000", fg="white", font=("Consolas", 11, "bold"), width=18).pack(side=tk.LEFT, padx=4)
        tk.Button(btn_frame, text="📂 Choisir dossier (pré-scan)", command=self.choisir_dossier,
                  bg="#2d2d2d", fg="white", font=FONT_UI, width=20).pack(side=tk.LEFT, padx=4)

        # 🔹 Bouton Admin (seulement si nécessaire)
        self.btn_admin = tk.Button(btn_frame, text="🛡️ Relancer en Admin", 
                                   command=self.relancer_en_admin,
                                   bg="#553300", fg="white", font=FONT_UI, width=16)
        if not KerberosDebug.is_admin():
            self.btn_admin.pack(side=tk.LEFT, padx=4)
        else:
            self.btn_admin.config(state="disabled", text="🛡️ Admin (actif)")

        # Console
        self.console = scrolledtext.ScrolledText(
            root, wrap=tk.WORD, font=FONT_MONO,
            bg="#0a0a0a", fg=FG, insertbackground=FG
        )
        self.console.pack(fill=tk.BOTH, expand=True, padx=12, pady=(0,10))
        self.console.bind("<Key>", lambda e: "break")

        self.console.insert(tk.END, "ℹ️ Kerberos v3.0 – Mode DEV activé\n")
        self.console.insert(tk.END, "   • Analyse .py complète + vérif intégrité\n")
        self.console.insert(tk.END, "   • Pré-scan dossier | Relance admin safe\n")
        self.console.insert(tk.END, "   • Debug automatique → logs/debug_*.log\n")
        self.console.insert(tk.END, "   🛡️ GPLv3 – https://liberapay.com/EthicalKerberos/\n\n")

        # 🔗 Lien Liberapay (discret, pas de tracking)
        link_label = tk.Label(root, text="❤️ Soutien éthique (Liberapay)", 
                              fg="#66ccff", bg=BG, cursor="hand2", font=("Tahoma", 8))
        link_label.pack(side=tk.BOTTOM, pady=(0,4))
        link_label.bind("<Button-1>", lambda e: self.open_liberapay())

        # Log de démarrage
        KerberosDebug.log_debug("Kerberos v3.0 lancé", "INFO")

    def open_liberapay(self):
        try:
            os.startfile("https://liberapay.com/EthicalKerberos/")
        except:
            messagebox.showinfo("Liberapay", "Ouvrez manuellement :\nhttps://liberapay.com/EthicalKerberos/")

    def relancer_en_admin(self):
        if not KerberosDebug.is_admin():
            try:
                ctypes.windll.shell32.ShellExecuteW(
                    None, "runas", sys.executable, " ".join(sys.argv), None, 1
                )
                sys.exit()
            except Exception as e:
                messagebox.showerror("Admin", f"Échec relance : {e}")

    def choisir_dossier(self):
        dossier = filedialog.askdirectory(title="Sélectionner un dossier à analyser")
        if not dossier:
            return

        # ➕ PRÉ-SCAN : fenêtre modale avec stats
        preview = Toplevel(self.root)
        preview.title("🔍 Pré-analyse – Kerberos v3.0")
        preview.geometry("500x320")
        preview.configure(bg=BG)
        preview.transient(self.root)
        preview.grab_set()

        tk.Label(preview, text=f"Dossier sélectionné :", fg=FG, bg=BG, font=("Consolas", 10, "bold")).pack(pady=(10,4))
        tk.Label(preview, text=dossier, fg="#66ccff", bg=BG, font=("Consolas", 9), wraplength=460).pack(padx=10)

        stats = preanalyse_dossier(dossier)

        # Stats
        info = f"""
Taille totale : {stats['total_bytes'] / (1024**2):.1f} Mo
Fichiers : {stats['total_files']} | Dossiers : {stats['total_dirs']}
.py trouvés : {stats['py_files']} ({stats['py_bytes'] / (1024**2):.1f} Mo)
⚠️ Risqués : {stats['risky_files']} | ❌ Corrompus : {stats['corrupted_files']}
Exemples .py : {', '.join(stats['sample_py']) if stats['sample_py'] else '—'}
        """.strip()
        tk.Label(preview, text=info, fg=FG, bg=BG, font=("Consolas", 9), justify=tk.LEFT, anchor="w").pack(pady=10, padx=15)

        btn_frame = tk.Frame(preview, bg=BG)
        btn_frame.pack(pady=10)

        def lancer():
            preview.destroy()
            self.generer_rapport([dossier])

        tk.Button(btn_frame, text="✅ Lancer l'analyse complète", command=lancer,
                  bg="#006600", fg="white", font=FONT_UI, width=22).pack(side=tk.LEFT, padx=5)
        tk.Button(btn_frame, text="❌ Annuler", command=preview.destroy,
                  bg="#444444", fg="white", font=FONT_UI, width=12).pack(side=tk.LEFT, padx=5)

    def analyser(self):
        cibles = [d for d, v in self.vars.items() if v.get()]
        if not cibles and self.lecteurs:
            messagebox.showwarning("Sélection", "Cochez au moins un lecteur ou choisissez un dossier.")
            return
        self.generer_rapport(cibles if cibles else ["C:\\"])

    def generer_rapport(self, cibles):
        self.console.delete(1.0, tk.END)
        self.console.insert(tk.END, "🔍 Génération du rapport v3.0… (patientez)\n\n")

        lignes = []
        lignes.append("=" * 70)
        lignes.append("RAPPORT KERBEROS v3.0 – ANALYSE PROFONDE")
        lignes.append("=" * 70)
        lignes.append(f"Date : {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        lignes.append(f"Système : {platform.platform()}")
        lignes.append(f"Admin : {'Oui' if KerberosDebug.is_admin() else 'Non'}")
        lignes.append(f"Profondeur : {MAX_DEPTH}")
        lignes.append("Corbeille exclue : " + ("Oui" if self.ignore_recycle.get() else "Non"))
        lignes.append("Licence : GNU GPLv3 – https://liberapay.com/EthicalKerberos/")
        lignes.append("Code source : https://github.com/victorpozen/kerberos")
        lignes.append("=" * 70)
        lignes.append("")

        for cible in cibles:
            lignes.append(f"\n{'='*70}\nCIBLE : {cible}\n{'='*70}")
            if os.path.exists(cible) and len(cible) == 3 and cible[1:] == ":\\": 
                lignes.append(f"📊 Espace : {espace_disque_win(cible)}")
            else:
                try:
                    size = sum(os.path.getsize(os.path.join(dp, f)) for dp, _, fn in os.walk(cible) for f in fn)
                    lignes.append(f"📊 Taille estimée : {size / (1024**2):.1f} Mo")
                except:
                    lignes.append("📊 Taille : N/A")

            lignes.append("\nArborescence (profondeur limitée) :")
            lignes.extend(arbre_securise_v3(cible, max_depth=MAX_DEPTH, ignore_recycle=self.ignore_recycle.get()))
            lignes.append("")

        lignes.append("✅ Rapport généré – Kerberos v3.0 (GPLv3)")
        rapport = "\n".join(lignes)

        self.console.insert(tk.END, rapport)

        try:
            out_path = "rapport_disques_v3.0.txt"
            with open(out_path, "w", encoding="utf-8") as f:
                f.write(rapport)
            self.console.insert(tk.END, f"\n\n💾 Sauvegardé : {out_path}")
            KerberosDebug.log_debug(f"Rapport sauvegardé : {out_path}", "INFO")
            messagebox.showinfo("✅ Succès", "Analyse terminée !\nRapport et logs générés.")
        except Exception as e:
            err_msg = f"⚠️ Erreur sauvegarde : {e}"
            self.console.insert(tk.END, f"\n\n{err_msg}")
            KerberosDebug.log_debug(err_msg, "ERROR")

# === LANCEMENT ===
if __name__ == "__main__":
    root = tk.Tk()
    app = KerberosDiskAnalyzer(root)
    root.mainloop()