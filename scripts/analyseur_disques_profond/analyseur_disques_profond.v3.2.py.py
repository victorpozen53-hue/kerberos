# -*- coding: utf-8 -*-
# analyseur_disques_profond.v3.2.py
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

# === TOOLTIP MAISON – LÉGER, SANS DÉPENDANCE ===
class Tooltip:
    def __init__(self, widget, text):
        self.widget = widget
        self.text = text
        self.tip_window = None
        self.id = None
        widget.bind("<Enter>", self.schedule_show)
        widget.bind("<Leave>", self.hide)
        widget.bind("<Button-1>", self.toggle)

    def schedule_show(self, event=None):
        self.id = self.widget.after(500, self.show)

    def show(self):
        if self.tip_window or not self.text:
            return
        x = self.widget.winfo_rootx() + 20
        y = self.widget.winfo_rooty() + self.widget.winfo_height() + 2
        self.tip_window = tw = tk.Toplevel(self.widget)
        tw.wm_overrideredirect(True)
        tw.wm_geometry(f"+{x}+{y}")
        tw.attributes("-topmost", True)
        label = tk.Label(
            tw, text=self.text,
            justify=tk.LEFT, background="#1a1a1a", foreground="#00ff00",
            relief=tk.SOLID, borderwidth=1, font=("Consolas", 9), padx=6, pady=4
        )
        label.pack()
        tw.bind("<Button-1>", lambda e: self.hide())
        self.widget.bind("<Button-1>", lambda e: self.hide(), add="+")

    def hide(self, event=None):
        if self.tip_window:
            self.tip_window.destroy()
            self.tip_window = None
        if self.id:
            self.widget.after_cancel(self.id)
            self.id = None

    def toggle(self, event=None):
        if self.tip_window:
            self.hide()
        else:
            self.show()

def create_help_button(parent, text, side=tk.RIGHT):
    btn = tk.Label(parent, text="?", bg="#2d2d2d", fg="#aaaaaa",
                   font=("Consolas", 9, "bold"), padx=3, pady=1,
                   cursor="hand2", relief="raised", bd=1)
    btn.pack(side=side, padx=(2, 0))
    Tooltip(btn, text)
    return btn

# === MODULE DEBUG KERBEROS – v3.2 ===
class KerberosDebug:
    @staticmethod
    def is_admin():
        try:
            return ctypes.windll.shell32.IsUserAnAdmin() != 0
        except:
            return False

    @staticmethod
    def debug_context():
        return {
            "timestamp": datetime.now().isoformat(),
            "os": platform.platform(),
            "python": sys.version,
            "executable": sys.executable,
            "cwd": os.getcwd(),
            "is_admin": KerberosDebug.is_admin(),
            "argv": sys.argv,
            "guards_present": [f for f in os.listdir(".") if f.startswith("guard_") and f.endswith(".py")] if os.path.exists(".") else [],
        }

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
        f.write("=== CRASH KERBEROS v3.2 ===\n")
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

# === ANALYSE .PY PRÉCISE – v3.2 ===
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

        if b"\x00" in raw[10:-10]:
            result["truncated"] = True
            result["is_complete"] = False
            result["details"].append("📄 \\x00 en milieu → corruption")

        result["hash_sha1"] = hashlib.sha1(raw).hexdigest()[:8]

        try:
            tree = ast.parse(text, filename=filepath)
            result["syntax_ok"] = True
        except SyntaxError as se:
            result["syntax_ok"] = False
            if se.lineno == text.count("\n") + 1:
                result["truncated"] = True
                result["is_complete"] = False
                result["details"].append("📄 Tronqué (EOF)")
            else:
                result["details"].append(f"📄 SyntaxError L{se.lineno}")
        except Exception as e:
            result["details"].append(f"📄 Parse error: {type(e).__name__}")

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

        lines = text.splitlines()
        for i, line in enumerate(lines, 1):
            if re.search(r"subprocess\.(run|Popen|call|check_output)\s*\(.*shell\s*=\s*False", line):
                result["details"].append(f"⚙️ subprocess safe L{i}")
            elif re.search(r"subprocess\.(run|Popen|call|check_output)\s*\(", line):
                if "shell=True" in line or ("shell" not in line and "shell=False" not in line):
                    result["risks"].append(f"subprocess risky L{i}")
            for pat, msg in [
                (r"exec\s*\(", "exec"), (r"eval\s*\(", "eval"),
                (r"__import__\s*\(", "__import__"), (r"shutil\.rmtree", "shutil.rmtree"),
                (r"ctypes\.windll", "ctypes.windll"),
            ]:
                if re.search(pat, line):
                    result["risks"].append(f"{msg} L{i}")

        if not result["is_complete"]:
            result["status"] = "corrupted"
        elif result["risks"]:
            result["status"] = "risky"
        elif result["syntax_ok"]:
            result["status"] = "clean"
        else:
            result["status"] = "error"

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

# === ARBRE ===
def arbre_securise_v3(root_path, prefix="", depth=0, max_depth=4, ignore_recycle=True):
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

    for d, path in dirs:
        idx += 1
        mark = "└── " if idx == total else "├── "
        lines.append((f"{prefix}{mark}📁 {d}", None, path))
        next_prefix = prefix + ("    " if idx == total else "│   ")
        lines.extend(arbre_securise_v3(path, next_prefix, depth + 1, max_depth, ignore_recycle))

    for f, path in py_files:
        idx += 1
        mark = "└── " if idx == total else "├── "
        analysis = analyser_fichier_py_complet(path)
        lines.append((f"{prefix}{mark}🐍 {f}  [{analysis['summary']}]", path, None))

    for f, path in other_files:
        idx += 1
        mark = "└── " if idx == total else "├── "
        lines.append((f"{prefix}{mark}📄 {f}", None, None))

    return lines

# === INTERFACE PRINCIPALE ===
class KerberosDiskAnalyzer:
    def __init__(self, root):
        self.root = root
        root.title("🔍 Kerberos – Analyseur de Disques v3.2 (GPLv3 – DEV)")
        root.geometry("1000x760")
        root.configure(bg=BG)

        # Titre cliquable (à propos)
        self.title_label = tk.Label(root, text="KERBEROS v3.2", fg=FG, bg=BG, font=("Consolas", 14, "bold"))
        self.title_label.pack(pady=5)
        self.title_label.bind("<Button-3>", self.show_about)  # clic droit → À propos

        tk.Label(root, text="Sécurité desktop locale — Windows 7/10 — zéro cloud", fg="#aaaaaa", bg=BG, font=("Tahoma", 9)).pack()

        # Options
        opt_frame = tk.Frame(root, bg=BG)
        opt_frame.pack(pady=5, padx=12, fill=tk.X)

        tk.Label(opt_frame, text="✅ Sélectionnez :", fg=FG, bg=BG, font=FONT_UI).pack(anchor="w")

        tk.Label(opt_frame, text=" ▸ Lecteurs :", bg=BG, fg="#aaaaaa", font=("Consolas", 9)).pack(anchor="w", pady=(3,0))
        drv_frame = tk.Frame(opt_frame, bg=BG)
        drv_frame.pack(anchor="w")
        self.vars = {}
        self.lecteurs = lister_lecteurs_windows()
        for drv in self.lecteurs[:6]:
            var = tk.BooleanVar(value=(drv == "C:\\"))
            self.vars[drv] = var
            tk.Checkbutton(drv_frame, text=drv, variable=var,
                           bg=BG, fg=FG, selectcolor="#333", font=FONT_UI).pack(side=tk.LEFT, padx=3)

        # Options avancées + ?
        tk.Label(opt_frame, text=" ▸ Options :", bg=BG, fg="#aaaaaa", font=("Consolas", 9)).pack(anchor="w", pady=(5,0))
        recycle_frame = tk.Frame(opt_frame, bg=BG)
        recycle_frame.pack(anchor="w")
        self.ignore_recycle = tk.BooleanVar(value=True)
        tk.Checkbutton(recycle_frame, text="🗑️ Ignorer $RECYCLE.BIN", variable=self.ignore_recycle,
                       bg=BG, fg=FG, selectcolor="#333", font=FONT_UI).pack(side=tk.LEFT)
        create_help_button(
            recycle_frame,
            "$RECYCLE.BIN est ignoré par défaut pour :\n"
            "• Performance (accès souvent lents ou refusés)\n"
            "• Sécurité (pas de scan de fichiers supprimés)\n"
            "• Éthique (pas de récupération non sollicitée)"
        )

        # Boutons + ?
        btn_frame = tk.Frame(root, bg=BG)
        btn_frame.pack(pady=5)

        analyse_btn = tk.Button(btn_frame, text="🚀 Analyser", command=self.analyser,
                                bg="#8b0000", fg="white", font=("Consolas", 11, "bold"), width=16)
        analyse_btn.pack(side=tk.LEFT, padx=4)
        create_help_button(
            btn_frame,
            "Lance l'analyse des lecteurs cochés.\n"
            "• Profondeur max : 4 niveaux\n"
            "• Rapport sauvegardé → ouvert automatiquement dans Notepad"
        )

        dossier_btn = tk.Button(btn_frame, text="🔍 Analyser un dossier", 
                                command=self.choisir_dossier,
                                bg="#2d2d2d", fg="white", font=FONT_UI, width=20)
        dossier_btn.pack(side=tk.LEFT, padx=4)
        create_help_button(
            btn_frame,
            "Sélectionne un dossier spécifique (ex: I:\\KERBEROS).\n"
            "→ Pré-scan rapide (taille, nb .py)\n"
            "→ Double-clique sur un .py → exécution en dry-run (--dry-run)"
        )

        if not KerberosDebug.is_admin():
            admin_btn = tk.Button(btn_frame, text="🛡️ Relancer en Admin", 
                                  command=self.relancer_en_admin,
                                  bg="#553300", fg="white", font=FONT_UI, width=16)
            admin_btn.pack(side=tk.LEFT, padx=4)
            create_help_button(admin_btn, "Relance ce script avec droits administrateur (ShellExecuteW).")

        # Barre de progression
        self.progress_var = tk.DoubleVar()
        style = ttk.Style()
        style.theme_use('default')
        style.configure("TProgressbar", thickness=12, background="#00aa00", troughcolor="#2d2d2d")
        self.progress_bar = ttk.Progressbar(root, variable=self.progress_var, maximum=100, style="TProgressbar")
        self.progress_bar.pack(fill=tk.X, padx=12, pady=(0, 6))
        self.progress_bar.pack_forget()

        # Console
        self.console = scrolledtext.ScrolledText(
            root, wrap=tk.WORD, font=FONT_MONO,
            bg="#0a0a0a", fg=FG, insertbackground=FG
        )
        self.console.pack(fill=tk.BOTH, expand=True, padx=12, pady=(0,8))
        self.console.bind("<Key>", lambda e: "break")
        self.console.tag_configure("exec", foreground="#ffcc00")
        self.console.tag_configure("error", foreground="#ff5555")

        self.console.insert(tk.END, "ℹ️ Kerberos v3.2 – GPLv3\n")
        self.console.insert(tk.END, "   • Analyse .py complète + vérif intégrité\n")
        self.console.insert(tk.END, "   • Double-clique → dry-run | Barre de progression\n")
        self.console.insert(tk.END, "   • Conforme GPLv3 — logs/debug_*.log\n\n")

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

        KerberosDebug.log_debug("Kerberos v3.2 lancé", "INFO")

    def show_about(self, event=None):
        about = Toplevel(self.root)
        about.title("ℹ️ À propos — Kerberos")
        about.geometry("520x360")
        about.configure(bg=BG)
        about.transient(self.root)
        about.grab_set()

        tk.Label(about, text="KERBEROS", fg=FG, bg=BG, font=("Consolas", 16, "bold")).pack(pady=(15,5))
        tk.Label(about, text="Sécurité desktop locale — Windows 7/10", fg="#aaaaaa", bg=BG, font=FONT_UI).pack()
        tk.Label(about, text="White hat only. GPLv3. Zéro cloud.", fg="#aaaaaa", bg=BG, font=FONT_UI).pack(pady=(0,10))

        info = (
            "🚀 Fonctionnalités :\n"
            " • Analyse statique .py (syntaxe, subprocess safe/risky)\n"
            " • Vérif intégrité (troncature, \\x00, encodage)\n"
            " • Double-clique sur .py → dry-run (--dry-run)\n"
            " • Barre de progression + ouverture auto du rapport\n"
            "\n"
            "🛡️ Éthique :\n"
            " • Zéro cloud — tout local\n"
            " • Pas de trace — pas de telemetry\n"
            " • Code ouvert — GitHub + GPLv3\n"
            " • Soutien discret — Liberapay (pas de tracking)\n"
            "\n"
            "📜 Licence : GNU GPLv3\n"
            "   https://www.gnu.org/licenses/gpl-3.0.html\n"
            "📦 Code : https://github.com/victorpozen/kerberos\n"
            "❤️ Soutien : https://liberapay.com/EthicalKerberos/"
        )
        txt = tk.Text(about, wrap=tk.WORD, font=("Consolas", 9), bg="#0a0a0a", fg=FG, height=15)
        txt.insert(tk.END, info)
        txt.config(state=tk.DISABLED)
        txt.pack(padx=15, pady=10, fill=tk.BOTH, expand=True)
        tk.Button(about, text="Fermer", command=about.destroy, bg="#2d2d2d", fg="white", font=FONT_UI).pack(pady=5)

    def relancer_en_admin(self):
        if not KerberosDebug.is_admin():
            try:
                ctypes.windll.shell32.ShellExecuteW(None, "runas", sys.executable, " ".join(sys.argv), None, 1)
                sys.exit()
            except Exception as e:
                messagebox.showerror("Admin", f"Échec relance : {e}")

    def choisir_dossier(self):
        dossier = filedialog.askdirectory()
        if dossier:
            self.generer_rapport([dossier])

    def analyser(self):
        cibles = [d for d, v in self.vars.items() if v.get()]
        if not cibles:
            messagebox.showwarning("Sélection", "Cochez au moins un lecteur ou choisissez un dossier.")
            return
        self.generer_rapport(cibles)

    def generer_rapport(self, cibles):
        self.console.delete(1.0, tk.END)
        self.console.insert(tk.END, "🔍 Initialisation du scan…\n\n")

        self.progress_bar.pack(fill=tk.X, padx=12, pady=(0, 6))
        self.progress_var.set(0)
        self.root.update_idletasks()

        # Double-clic sur ligne → dry-run
        def on_double_click(event):
            index = self.console.index(f"@{event.x},{event.y}")
            line = self.console.get(f"{index} linestart", f"{index} lineend")
            if "🐍 " in line and "[" in line:
                start = line.find("🐍 ") + 2
                end = line.find("  [") if "  [" in line else len(line)
                filename = line[start:end].strip()
                for cible in cibles:
                    for root_dir, _, files in os.walk(cible):
                        if filename in files:
                            self.executer_dry_run(os.path.join(root_dir, filename))
                            return
        self.console.bind("<Double-1>", on_double_click)

        try:
            total_py = 0
            for cible in cibles:
                try:
                    for root_dir, _, files in os.walk(cible):
                        total_py += sum(1 for f in files if f.endswith('.py'))
                except: pass

            processed = 0
            lignes = []
            lignes.append("=" * 72)
            lignes.append("RAPPORT KERBEROS v3.2 – ANALYSE PROFONDE")
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
                for line, filepath, _ in arbre_securise_v3(cible, max_depth=MAX_DEPTH, ignore_recycle=self.ignore_recycle.get()):
                    lignes.append(line)
                    if filepath and filepath.endswith('.py'):
                        processed += 1
                        if total_py > 0:
                            pct = 10 + (processed / total_py) * 80
                            self.progress_var.set(pct)
                            self.root.title(f"🔍 Kerberos – {processed}/{total_py} .py analysés…")
                            self.root.update_idletasks()

                lignes.append("")

            lignes.append("✅ Rapport généré – Kerberos v3.2 (GPLv3)")
            rapport = "\n".join(lignes)
            self.console.insert(tk.END, rapport)

            try:
                out_path = "rapport_disques_v3.2.txt"
                with open(out_path, "w", encoding="utf-8") as f:
                    f.write(rapport)
                self.console.insert(tk.END, f"\n\n💾 Sauvegardé : {out_path}\n", "exec")
                KerberosDebug.log_debug(f"Rapport sauvegardé : {out_path}", "INFO")

                # ➕ ✅ OUVERTURE AUTO DANS NOTEPAD
                self.console.insert(tk.END, "🖨️ Ouverture du rapport dans Notepad…\n", "exec")
                self.root.update_idletasks()
                os.startfile(out_path)

            except Exception as e:
                self.console.insert(tk.END, f"\n⚠️ Impossible d'ouvrir le rapport : {e}\n", "error")

        finally:
            self.root.after(800, lambda: self.progress_bar.pack_forget())
            self.root.title("🔍 Kerberos – Analyseur de Disques v3.2 (GPLv3 – DEV)")

    def executer_dry_run(self, filepath):
        if not os.path.isfile(filepath):
            return
        self.console.insert(tk.END, f"\n▶️ Dry-run : {os.path.basename(filepath)}\n", "exec")
        try:
            result = subprocess.run(
                [sys.executable, filepath, "--dry-run"],
                capture_output=True, text=True, timeout=10,
                cwd=os.path.dirname(filepath)
            )
            if result.stdout.strip():
                self.console.insert(tk.END, result.stdout.strip() + "\n", "exec")
            if result.stderr.strip():
                self.console.insert(tk.END, "STDERR:\n" + result.stderr.strip() + "\n", "error")
            msg = "✅ Exit 0" if result.returncode == 0 else f"⚠️ Exit {result.returncode}"
            self.console.insert(tk.END, f"{msg}\n", "exec" if result.returncode == 0 else "error")
        except subprocess.TimeoutExpired:
            self.console.insert(tk.END, "⏱️ Timeout (10s)\n", "error")
        except Exception as e:
            self.console.insert(tk.END, f"💥 Erreur : {e}\n", "error")
        self.console.see(tk.END)

# === LANCEMENT ===
if __name__ == "__main__":
    root = tk.Tk()
    app = KerberosDiskAnalyzer(root)
    root.mainloop()