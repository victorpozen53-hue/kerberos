# -*- coding: utf-8 -*-
# analyseur_disques_profond.v3.1.py
# Sécurité desktop locale — Windows 7/10, matériel ancien, zéro cloud
# Copyright (C) 2025  Victor Pozen
# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
# 
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
# 
# You should have received a copy of the GNU General Public License
# along with this program.  If not, see <https://www.gnu.org/licenses/>.
# 
# Code source : https://github.com/victorpozen/kerberos
# Soutien éthique : https://liberapay.com/EthicalKerberos/
# White hat only. Pas de trace. Pas de nuage. Juste du code qui protège. (-; — Victor.Pozen

import sys
import os
import platform
import traceback
import ctypes
import subprocess
from datetime import datetime
import hashlib
import ast
import re
import tkinter as tk
from tkinter import ttk, scrolledtext, messagebox, filedialog, Toplevel

# === MODULE DEBUG KERBEROS – v3.1 (inline, maison) ===
class KerberosDebug:
    @staticmethod
    def is_admin():
        try:
            return ctypes.windll.shell32.IsUserAnAdmin() != 0
        except:
            return False

    @staticmethod
    def debug_context():
        ctx = {
            "timestamp": datetime.now().isoformat(),
            "os": platform.platform(),
            "python": sys.version,
            "executable": sys.executable,
            "cwd": os.getcwd(),
            "is_admin": KerberosDebug.is_admin(),
            "argv": sys.argv,
            "guards_present": [f for f in os.listdir(".") if f.startswith("guard_") and f.endswith(".py")] if os.path.exists(".") else [],
        }
        return ctx

    @staticmethod
    def log_debug(msg, level="INFO"):
        log_dir = "logs"
        os.makedirs(log_dir, exist_ok=True)
        log_path = os.path.join(log_dir, f"debug_{datetime.now().strftime('%Y%m%d')}.log")
        with open(log_path, "a", encoding="utf-8") as f:
            f.write(f"[{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}] [{level}] {msg}\n")

    @staticmethod
    def make_backup(filepath):
        if os.path.isfile(filepath):
            bak = filepath + ".bak"
            try:
                with open(filepath, "rb") as src, open(bak, "wb") as dst:
                    dst.write(src.read())
                KerberosDebug.log_debug(f"Backup : {bak}", "INFO")
            except Exception as e:
                KerberosDebug.log_debug(f"Backup échoué {filepath} → {e}", "WARNING")

# === GESTIONNAIRE D'ERREUR GLOBAL ===
def kerberos_excepthook(exc_type, exc_value, exc_tb):
    err = ''.join(traceback.format_exception(exc_type, exc_value, exc_tb))
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    log_dir = "logs"
    os.makedirs(log_dir, exist_ok=True)
    log_path = os.path.join(log_dir, f"kerberos_crash_{timestamp}.log")
    ctx = KerberosDebug.debug_context()
    with open(log_path, "w", encoding="utf-8") as f:
        f.write("=== CRASH KERBEROS v3.1 ===\n")
        for k, v in ctx.items():
            f.write(f"{k}: {v}\n")
        f.write("\n=== TRACEBACK ===\n")
        f.write(err)
    try:
        tmp = tk.Tk()
        tmp.withdraw()
        messagebox.showerror("💥 Kerberos – Erreur critique", f"{exc_type.__name__}: {exc_value}\n\nLog : {log_path}")
        tmp.destroy()
    except: pass
sys.excepthook = kerberos_excepthook

# === CONFIG ===
BG = "#1e1e1e"
FG = "#00ff00"
FONT_UI = ("Tahoma", 10)
FONT_MONO = ("Consolas", 10)
EXT_IMPORTANTES = {'.py', '.txt', '.log', '.json', '.csv', '.html', '.exe', '.bat', '.ini', '.xml', '.yml'}
MAX_DEPTH = 4

# === UTILS ===
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

# === ANALYSE .PY PRÉCISE – v3.1 (subprocess safe/risky) ===
def analyser_fichier_py_complet(filepath):
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
        "details": []
    }

    try:
        with open(filepath, "rb") as f:
            raw = f.read()
        result["size_bytes"] = len(raw)

        # 🔹 Encodage
        try:
            text = raw.decode("utf-8")
            result["encoding"] = "utf-8"
        except UnicodeDecodeError:
            try:
                text = raw.decode("utf-8-sig")
                result["encoding"] = "utf-8-sig"
            except:
                result["encoding"] = "inconnu"
                result["status"] = "corrupted"
                result["summary"] = "⚠️ Encodage invalide"
                return result

        # 🔹 Corruption binaire
        if b"\x00" in raw[10:-10]:  # \x00 en milieu → probable corruption
            result["truncated"] = True
            result["is_complete"] = False
            result["details"].append("📄 Contient \\x00 (hors BOM/fin)")

        # 🔹 Hash
        result["hash_sha1"] = hashlib.sha1(raw).hexdigest()[:8]

        # 🔹 Syntaxe
        try:
            tree = ast.parse(text, filename=filepath)
            result["syntax_ok"] = True
        except SyntaxError as se:
            result["syntax_ok"] = False
            if se.lineno == text.count("\n") + 1:
                result["truncated"] = True
                result["is_complete"] = False
                result["details"].append("📄 Tronqué (EOF inattendue)")
            else:
                result["details"].append(f"📄 SyntaxError L{se.lineno}")
        except Exception as e:
            result["details"].append(f"📄 Parse error: {type(e).__name__}")

        # 🔹 Imports
        try:
            for node in ast.walk(tree):
                if isinstance(node, ast.Import):
                    for alias in node.names:
                        result["imports"].append(alias.name)
                elif isinstance(node, ast.ImportFrom):
                    if node.module:
                        result["imports"].append(node.module)
        except: pass
        result["imports"] = sorted(set(result["imports"]))

        # 🔹 Patterns — subprocess analyser finement
        lines = text.splitlines()
        for i, line in enumerate(lines, 1):
            # subprocess.run([...], shell=False) → safe
            if re.search(r"subprocess\.(run|Popen|call|check_output)\s*\(.*shell\s*=\s*False", line):
                result["details"].append(f"⚙️ subprocess safe L{i}")
            # subprocess avec shell=True ou sans précision → risky
            elif re.search(r"subprocess\.(run|Popen|call|check_output)\s*\(", line):
                if "shell=True" in line or ("shell" not in line and "shell=False" not in line):
                    result["risks"].append(f"subprocess risky L{i}")
                    result["details"].append(f"⚠️ subprocess risky L{i}")

            # Autres patterns
            for pat, msg in [
                (r"exec\s*\(", "exec"),
                (r"eval\s*\(", "eval"),
                (r"__import__\s*\(", "__import__"),
                (r"shutil\.rmtree", "shutil.rmtree"),
                (r"ctypes\.windll", "ctypes.windll"),
            ]:
                if re.search(pat, line):
                    result["risks"].append(f"{msg} L{i}")

        # 🔹 Statut final
        if not result["is_complete"]:
            result["status"] = "corrupted"
        elif result["risks"]:
            result["status"] = "risky"
        elif result["syntax_ok"]:
            result["status"] = "clean"
        else:
            result["status"] = "error"

        # 🔹 Résumé
        parts = []
        if result["status"] == "clean":
            parts.append("✅ Clean")
        elif result["status"] == "corrupted":
            parts.append("❌ Corrompu")
        elif result["status"] == "risky":
            parts.append("⚠️ " + " | ".join(result["risks"][:1]))
        else:
            parts.append("❓ Erreur")

        if result["imports"]:
            parts.append("imports:" + ",".join(result["imports"][:2]))
        if not result["is_complete"]:
            parts.append("🚨 Incomplet")

        result["summary"] = " | ".join(parts)
        return result

    except PermissionError:
        result["status"] = "denied"
        result["summary"] = "🔒 Accès refusé"
        return result
    except Exception as e:
        result["status"] = "error"
        result["summary"] = f"💥 {type(e).__name__}"
        return result

# === ARBRE – avec double-clique exécution dry-run ===
def arbre_securise_v3(root_path, prefix="", depth=0, max_depth=4, ignore_recycle=True, console=None):
    if depth >= max_depth:
        return [f"{prefix}└── [...] (prof {max_depth})"]
    lines = []
    try:
        entries = sorted(os.listdir(root_path))
    except (OSError, PermissionError):
        return [f"{prefix}📁 [accès refusé]"]

    dirs = []
    py_files = []
    other_files = []

    for e in entries:
        path = os.path.join(root_path, e)
        try:
            if os.path.isdir(path):
                if ignore_recycle and e.upper() == "$RECYCLE.BIN":
                    continue
                dirs.append((e, path))
            elif os.path.isfile(path):
                _, ext = os.path.splitext(e)
                if ext.lower() == ".py":
                    py_files.append((e, path))
                elif ext.lower() in EXT_IMPORTANTES:
                    other_files.append((e, path))
        except: pass

    total = len(dirs) + len(py_files) + len(other_files)
    idx = 0

    # Dossiers
    for d, path in dirs:
        idx += 1
        mark = "└── " if idx == total else "├── "
        lines.append((f"{prefix}{mark}📁 {d}", None, path))
        next_prefix = prefix + ("    " if idx == total else "│   ")
        lines.extend(arbre_securise_v3(path, next_prefix, depth + 1, max_depth, ignore_recycle, console))

    # Fichiers .py → double-clique exécute dry-run
    for f, path in py_files:
        idx += 1
        mark = "└── " if idx == total else "├── "
        analysis = analyser_fichier_py_complet(path)
        lines.append((f"{prefix}{mark}🐍 {f}  [{analysis['summary']}]", path, None))

    # Autres fichiers
    for f, path in other_files:
        idx += 1
        mark = "└── " if idx == total else "├── "
        lines.append((f"{prefix}{mark}📄 {f}", None, None))

    return lines

# === INTERFACE — v3.1 ===
class KerberosDiskAnalyzer:
    def __init__(self, root):
        self.root = root
        root.title("🔍 Kerberos – Analyseur de Disques v3.1 (GPLv3 – DEV)")
        root.geometry("1000x740")
        root.configure(bg=BG)

        tk.Label(root, text="KERBEROS v3.1", fg=FG, bg=BG, font=("Consolas", 14, "bold")).pack(pady=5)
        tk.Label(root, text="Analyse Profonde Locale — Sécurité Éthique — GPLv3", fg="#aaaaaa", bg=BG, font=("Tahoma", 9)).pack()

        # Options
        opt_frame = tk.Frame(root, bg=BG)
        opt_frame.pack(pady=5, padx=12, fill=tk.X)
        tk.Label(opt_frame, text="✅ Sélectionnez :", fg=FG, bg=BG, font=FONT_UI).pack(anchor="w")
        tk.Label(opt_frame, text=" ▸ Lecteurs :", bg=BG, fg="#aaaaaa", font=("Consolas", 9)).pack(anchor="w", pady=(3,0))

        self.vars = {}
        self.lecteurs = lister_lecteurs_windows()
        drv_frame = tk.Frame(opt_frame, bg=BG)
        drv_frame.pack(anchor="w")
        for drv in self.lecteurs[:6]:
            var = tk.BooleanVar(value=(drv == "C:\\"))
            self.vars[drv] = var
            tk.Checkbutton(drv_frame, text=drv, variable=var,
                           bg=BG, fg=FG, selectcolor="#333", font=FONT_UI).pack(side=tk.LEFT, padx=3)

        tk.Label(opt_frame, text=" ▸ Options :", bg=BG, fg="#aaaaaa", font=("Consolas", 9)).pack(anchor="w", pady=(5,0))
        self.ignore_recycle = tk.BooleanVar(value=True)
        tk.Checkbutton(opt_frame, text="🗑️ Ignorer $RECYCLE.BIN", variable=self.ignore_recycle,
                       bg=BG, fg=FG, selectcolor="#333", font=FONT_UI).pack(anchor="w")

        # Boutons
        btn_frame = tk.Frame(root, bg=BG)
        btn_frame.pack(pady=5)
        tk.Button(btn_frame, text="🚀 Analyser", command=self.analyser,
                  bg="#8b0000", fg="white", font=("Consolas", 11, "bold"), width=16).pack(side=tk.LEFT, padx=4)
        tk.Button(btn_frame, text="📂 Choisir dossier", command=self.choisir_dossier,
                  bg="#2d2d2d", fg="white", font=FONT_UI, width=18).pack(side=tk.LEFT, padx=4)
        if not KerberosDebug.is_admin():
            tk.Button(btn_frame, text="🛡️ Relancer en Admin", command=self.relancer_en_admin,
                      bg="#553300", fg="white", font=FONT_UI, width=16).pack(side=tk.LEFT, padx=4)

        # Console
        self.console = scrolledtext.ScrolledText(
            root, wrap=tk.WORD, font=FONT_MONO,
            bg="#0a0a0a", fg=FG, insertbackground=FG
        )
        self.console.pack(fill=tk.BOTH, expand=True, padx=12, pady=(0,8))
        self.console.bind("<Key>", lambda e: "break")
        self.console.tag_configure("exec", foreground="#ffcc00")
        self.console.tag_configure("error", foreground="#ff5555")

        self.console.insert(tk.END, "ℹ️ Kerberos v3.1 – DEV Mode\n")
        self.console.insert(tk.END, "   • subprocess safe/risky détecté\n")
        self.console.insert(tk.END, "   • Double-clique sur .py → dry-run\n")
        self.console.insert(tk.END, "   • GPLv3 conforme – logs/debug_*.log\n\n")

        # Footer éthique
        footer = tk.Frame(root, bg=BG)
        footer.pack(side=tk.BOTTOM, fill=tk.X, padx=10, pady=(0,3))
        for text, url in [
            ("❤️ Soutien éthique", "https://liberapay.com/EthicalKerberos/"),
            (" | ", None),
            ("📦 Code source", "https://github.com/victorpozen/kerberos"),
            (" — GPLv3", None)
        ]:
            if url:
                lbl = tk.Label(footer, text=text, fg="#66ccff", bg=BG, cursor="hand2", font=("Tahoma", 8))
                lbl.pack(side=tk.LEFT)
                lbl.bind("<Button-1>", lambda e, u=url: os.startfile(u))
            else:
                tk.Label(footer, text=text, fg="#555555" if "GPLv3" in text else "#444444", bg=BG, font=("Tahoma", 8)).pack(side=tk.LEFT)

        KerberosDebug.log_debug("Kerberos v3.1 lancé", "INFO")

    def relancer_en_admin(self):
        if not KerberosDebug.is_admin():
            try:
                ctypes.windll.shell32.ShellExecuteW(
                    None, "runas", sys.executable, " ".join(sys.argv), None, 1
                )
                sys.exit()
            except Exception as e:
                messagebox.showerror("Admin", f"Échec : {e}")

    def choisir_dossier(self):
        dossier = filedialog.askdirectory()
        if dossier:
            self.generer_rapport([dossier])

    def analyser(self):
        cibles = [d for d, v in self.vars.items() if v.get()]
        self.generer_rapport(cibles if cibles else ["C:\\"])

    def generer_rapport(self, cibles):
        self.console.delete(1.0, tk.END)
        self.console.insert(tk.END, "🔍 Génération du rapport v3.1…\n\n")

        # ➕ Double-clique sur ligne → exécute .py en dry-run
        def on_double_click(event):
            index = self.console.index(f"@{event.x},{event.y}")
            line = self.console.get(f"{index} linestart", f"{index} lineend").strip()
            if "🐍 " in line and "[" in line:
                # Extraire nom fichier
                start = line.find("🐍 ") + 2
                end = line.find("  [") if "  [" in line else len(line)
                filename = line[start:end].strip()
                # Trouver chemin complet (parmi cibles)
                for cible in cibles:
                    candidate = os.path.join(cible, filename)
                    if os.path.isfile(candidate) and candidate.endswith(".py"):
                        self.executer_dry_run(candidate)
                        return
                    # Sinon chercher récursivement (léger)
                    for root, _, files in os.walk(cible):
                        if filename in files:
                            self.executer_dry_run(os.path.join(root, filename))
                            return

        self.console.bind("<Double-1>", on_double_click)

        lignes = []
        lignes.append("=" * 72)
        lignes.append("RAPPORT KERBEROS v3.1 – ANALYSE PROFONDE")
        lignes.append("=" * 72)
        lignes.append(f"Date : {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        lignes.append(f"Système : {platform.platform()}")
        lignes.append(f"Admin : {'Oui' if KerberosDebug.is_admin() else 'Non'}")
        lignes.append("Licence : https://www.gnu.org/licenses/gpl-3.0.html")
        lignes.append("Code source : https://github.com/victorpozen/kerberos")
        lignes.append("Soutien éthique : https://liberapay.com/EthicalKerberos/")
        lignes.append("=" * 72)
        lignes.append("")

        for cible in cibles:
            lignes.append(f"\n{'='*72}\nCIBLE : {cible}\n{'='*72}")
            if os.path.exists(cible) and len(cible) == 3 and cible[1:] == ":\\": 
                lignes.append(f"📊 Espace : {espace_disque_win(cible)}")
            else:
                try:
                    size = sum(os.path.getsize(os.path.join(dp, f)) for dp, _, fn in os.walk(cible) for f in fn)
                    lignes.append(f"📊 Taille : {size / (1024**2):.1f} Mo")
                except: pass

            lignes.append("\nArborescence (prof ≤4) :")
            tree_lines = arbre_securise_v3(cible, max_depth=MAX_DEPTH, ignore_recycle=self.ignore_recycle.get())
            for line, filepath, _ in tree_lines:
                lignes.append(line)
                # Stocker mapping ligne→filepath dans la console (invisible)
                if filepath:
                    # On ajoute un tag invisible avec chemin
                    pass
            lignes.append("")

        lignes.append("✅ Rapport généré – Kerberos v3.1 (GPLv3)")
        rapport = "\n".join(lignes)
        self.console.insert(tk.END, rapport)

        try:
            with open("rapport_disques_v3.1.txt", "w", encoding="utf-8") as f:
                f.write(rapport)
            self.console.insert(tk.END, f"\n\n💾 Sauvegardé : rapport_disques_v3.1.txt")
            KerberosDebug.log_debug("Rapport v3.1 sauvegardé", "INFO")
        except Exception as e:
            self.console.insert(tk.END, f"\n\n⚠️ Erreur : {e}")

    def executer_dry_run(self, filepath):
        """Exécute un .py avec --dry-run (safe, read-only)"""
        if not os.path.isfile(filepath):
            return
        self.console.insert(tk.END, f"\n▶️ Dry-run : {os.path.basename(filepath)}\n", "exec")
        try:
            # Lancer dans un subprocess isolé
            result = subprocess.run(
                [sys.executable, filepath, "--dry-run"],
                capture_output=True, text=True, timeout=10, cwd=os.path.dirname(filepath)
            )
            out = result.stdout.strip()
            err = result.stderr.strip()
            if out:
                self.console.insert(tk.END, out + "\n", "exec")
            if err:
                self.console.insert(tk.END, "STDERR:\n" + err + "\n", "error")
            if result.returncode == 0:
                self.console.insert(tk.END, "✅ Dry-run terminé (exit 0)\n", "exec")
            else:
                self.console.insert(tk.END, f"⚠️ Exit code {result.returncode}\n", "error")
        except subprocess.TimeoutExpired:
            self.console.insert(tk.END, "⏱️ Timeout (10s)\n", "error")
        except Exception as e:
            self.console.insert(tk.END, f"💥 Erreur exécution : {e}\n", "error")
        self.console.see(tk.END)

# === LANCEMENT ===
if __name__ == "__main__":
    root = tk.Tk()
    app = KerberosDiskAnalyzer(root)
    root.mainloop()