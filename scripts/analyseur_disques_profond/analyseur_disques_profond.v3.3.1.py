# -*- coding: utf-8 -*-
# analyseur_disques_profond.v3.3.py
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
import tempfile
from datetime import datetime
import hashlib
import ast
import re
import tkinter as tk
from tkinter import ttk, scrolledtext, messagebox, filedialog, Toplevel

# === OUVRE DANS NOTEPAD/NOTEPAD++ À UNE LIGNE DONNÉE ===
def open_in_notepad_at_line(filepath, line_number):
    """Ouvre le fichier à la ligne précise — Notepad++ si présent, sinon Notepad + VBS."""
    if not os.path.isfile(filepath):
        return False

    # 🔹 Essayer Notepad++ (précis, rapide)
    for prog in [
        os.path.join(os.environ.get("ProgramFiles", "C:\\Program Files"), "Notepad++", "notepad++.exe"),
        os.path.join(os.environ.get("ProgramFiles(x86)", "C:\\Program Files (x86)"), "Notepad++", "notepad++.exe"),
    ]:
        if os.path.isfile(prog):
            try:
                subprocess.Popen([prog, f"-n{line_number}", filepath], cwd=os.path.dirname(filepath))
                return True
            except: pass

    # 🔹 Sinon, Notepad + script VBS (léger, compatible Win 7)
    try:
        vbs_content = f'''
Set WshShell = WScript.CreateObject("WScript.Shell")
WshShell.Run "notepad.exe ""{filepath}""", 1, False
WScript.Sleep 600
For i = 2 To {line_number}
    WshShell.SendKeys "^{{DOWN}}"
Next
WScript.Sleep 100
WshShell.SendKeys "^{{HOME}}"
'''
        with tempfile.NamedTemporaryFile(suffix='.vbs', delete=False, mode='w', encoding='utf-8') as f:
            f.write(vbs_content.strip())
            vbs_path = f.name
        subprocess.Popen(['wscript.exe', vbs_path], cwd=os.path.dirname(filepath))
        return True
    except Exception as e:
        try:
            os.remove(vbs_path)
        except: pass
        return False

# === MODULE DEBUG KERBEROS ===
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
        }

    @staticmethod
    def log_debug(msg, level="INFO"):
        log_dir = "logs"
        os.makedirs(log_dir, exist_ok=True)
        log_path = os.path.join(log_dir, f"debug_{datetime.now().strftime('%Y%m%d')}.log")
        with open(log_path, "a", encoding="utf-8") as f:
            f.write(f"[{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}] [{level}] {msg}\n")

# === GESTIONNAIRE D'ERREUR GLOBAL ===
def kerberos_excepthook(exc_type, exc_value, exc_tb):
    err = ''.join(traceback.format_exception(exc_type, exc_value, exc_tb))
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    log_dir = "logs"
    os.makedirs(log_dir, exist_ok=True)
    log_path = os.path.join(log_dir, f"kerberos_crash_{timestamp}.log")
    ctx = KerberosDebug.debug_context()
    with open(log_path, "w", encoding="utf-8") as f:
        f.write("=== CRASH KERBEROS v3.3 ===\n")
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
def lister_lecteurs_windows(): return [f"{c}:\\" for c in "ABCDEFGHIJKLMNOPQRSTUVWXYZ" if os.path.exists(f"{c}:\\")] or ["C:\\"]

def espace_disque_win(lecteur):
    try:
        _, total, free = ctypes.c_ulonglong(), ctypes.c_ulonglong(), ctypes.c_ulonglong()
        ctypes.windll.kernel32.GetDiskFreeSpaceExW(ctypes.c_wchar_p(lecteur), None, ctypes.pointer(total), ctypes.pointer(free))
        used = (total.value - free.value) / (1024**3)
        total_gb = total.value / (1024**3)
        return f"{used:.1f} / {total_gb:.1f} Go"
    except: return "⚠️ Indisponible"

# === ANALYSE .PY PRÉCISE ===
def analyser_fichier_py_complet(filepath):
    result = {"filepath": filepath, "status": "unknown", "summary": "", "imports": [], "risks": [], "size_bytes": 0}
    try:
        with open(filepath, "rb") as f: raw = f.read()
        result["size_bytes"] = len(raw)
        text = raw.decode("utf-8-sig")  # gère BOM

        # Encodage / corruption
        if b"\x00" in raw[10:-10]:
            result["status"] = "corrupted"
            result["summary"] = "❌ Corrompu (\\x00 en milieu)"
            return result

        # Syntaxe
        tree = ast.parse(text, filename=filepath)
        result["syntax_ok"] = True

        # Imports
        for node in ast.walk(tree):
            if isinstance(node, ast.Import):
                result["imports"].extend(alias.name for alias in node.names)
            elif isinstance(node, ast.ImportFrom) and node.module:
                result["imports"].append(node.module)
        result["imports"] = sorted(set(result["imports"]))

        # Patterns
        lines = text.splitlines()
        for i, line in enumerate(lines, 1):
            if re.search(r"subprocess\.(run|Popen|call|check_output)\s*\(.*shell\s*=\s*False", line):
                continue
            elif re.search(r"subprocess\.(run|Popen|call|check_output)\s*\(", line):
                if "shell=True" in line or ("shell" not in line and "shell=False" not in line):
                    result["risks"].append(f"subprocess risky L{i}")
            for pat, msg in [
                (r"exec\s*\(", "exec"), (r"eval\s*\(", "eval"),
                (r"__import__\s*\(", "__import__"), (r"shutil\.rmtree", "shutil.rmtree"),
            ]:
                if re.search(pat, line):
                    result["risks"].append(f"{msg} L{i}")

        result["status"] = "risky" if result["risks"] else "clean"
        parts = ["✅ Clean" if result["status"] == "clean" else "⚠️ " + " | ".join(result["risks"][:1])]
        if result["imports"]: parts.append("imports:" + ",".join(result["imports"][:2]))
        result["summary"] = " | ".join(parts)
        return result

    except PermissionError:
        result["status"] = "denied"
        result["summary"] = "🔒 Accès refusé"
        return result
    except SyntaxError as se:
        result["status"] = "error"
        result["summary"] = f"❓ SyntaxError L{se.lineno}"
        return result
    except Exception as e:
        result["status"] = "error"
        result["summary"] = f"💥 {type(e).__name__}"
        return result

# === ARBRE — avec lignes cliquables 🔍 ===
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
                if ignore_recycle and e.upper() == "$RECYCLE.BIN": continue
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
        lines.append((f"{prefix}{mark}📁 {d}", None, None, None))
        next_prefix = prefix + ("    " if idx == total else "│   ")
        lines.extend(arbre_securise_v3(path, next_prefix, depth + 1, max_depth, ignore_recycle))

    for f, path in py_files:
        idx += 1
        mark = "└── " if idx == total else "├── "
        analysis = analyser_fichier_py_complet(path)
        display = f"{prefix}{mark}🐍 {f}  [{analysis['summary']}]"
        tag_name = handler = None

        # ➕ Ajouter 🔍 cliquable si problème détecté
        if analysis["status"] in ("risky", "error", "corrupted"):
            match = re.search(r"L(\d+)", analysis["summary"])
            if match:
                line_num = int(match.group(1))
                display += "  🔍"
                tag_name = f"click_{hash(path)}_{line_num}"
                handler = lambda fp=path, ln=line_num: (lambda e: open_in_notepad_at_line(fp, ln))

        lines.append((display, path, tag_name, handler))

    for f, path in other_files:
        idx += 1
        mark = "└── " if idx == total else "├── "
        lines.append((f"{prefix}{mark}📄 {f}", None, None, None))

    return lines

# === INTERFACE PRINCIPALE ===
class KerberosDiskAnalyzer:
    def __init__(self, root):
        self.root = root
        root.title("🔍 Kerberos – Analyseur de Disques v3.3 (GPLv3)")
        root.geometry("1000x780")
        root.configure(bg=BG)

        # Titre (clic droit → À propos)
        self.title_label = tk.Label(root, text="KERBEROS v3.3", fg=FG, bg=BG, font=("Consolas", 14, "bold"))
        self.title_label.pack(pady=5)
        self.title_label.bind("<Button-3>", self.show_about)

        tk.Label(root, text="Sécurité locale — Windows 7/10 — GPLv3", fg="#aaaaaa", bg=BG, font=("Tahoma", 9)).pack()

        # Options
        opt_frame = tk.Frame(root, bg=BG)
        opt_frame.pack(pady=5, padx=12, fill=tk.X)
        tk.Label(opt_frame, text="✅ Sélectionnez :", fg=FG, bg=BG, font=FONT_UI).pack(anchor="w")
        tk.Label(opt_frame, text=" ▸ Lecteurs :", bg=BG, fg="#aaaaaa", font=("Consolas", 9)).pack(anchor="w", pady=(3,0))

        drv_frame = tk.Frame(opt_frame, bg=BG)
        drv_frame.pack(anchor="w")
        self.vars = {}
        for drv in lister_lecteurs_windows()[:6]:
            var = tk.BooleanVar(value=(drv == "C:\\"))
            self.vars[drv] = var
            tk.Checkbutton(drv_frame, text=drv, variable=var, bg=BG, fg=FG, selectcolor="#333", font=FONT_UI).pack(side=tk.LEFT, padx=3)

        recycle_frame = tk.Frame(opt_frame, bg=BG)
        recycle_frame.pack(anchor="w", pady=(5,0))
        self.ignore_recycle = tk.BooleanVar(value=True)
        tk.Checkbutton(recycle_frame, text="🗑️ Ignorer $RECYCLE.BIN", variable=self.ignore_recycle,
                       bg=BG, fg=FG, selectcolor="#333", font=FONT_UI).pack(side=tk.LEFT)

        # Boutons
        btn_frame = tk.Frame(root, bg=BG)
        btn_frame.pack(pady=5)
        tk.Button(btn_frame, text="🚀 Analyser", command=self.analyser,
                  bg="#8b0000", fg="white", font=("Consolas", 11, "bold"), width=16).pack(side=tk.LEFT, padx=4)
        tk.Button(btn_frame, text="🔍 Analyser un dossier", command=self.choisir_dossier,
                  bg="#2d2d2d", fg="white", font=FONT_UI, width=20).pack(side=tk.LEFT, padx=4)
        if not KerberosDebug.is_admin():
            tk.Button(btn_frame, text="🛡️ Relancer en Admin", command=self.relancer_en_admin,
                      bg="#553300", fg="white", font=FONT_UI, width=16).pack(side=tk.LEFT, padx=4)

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

        self.console.insert(tk.END, "ℹ️ Kerberos v3.3 – GPLv3\n")
        self.console.insert(tk.END, "   • Clic sur 🔍 → ouvre fichier à la ligne problématique\n")
        self.console.insert(tk.END, "   • Rapport auto-ouvert dans Notepad\n\n")

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

        KerberosDebug.log_debug("Kerberos v3.3 lancé", "INFO")

    def show_about(self, event=None):
        about = Toplevel(self.root)
        about.title("ℹ️ À propos — Kerberos")
        about.geometry("500x320")
        about.configure(bg=BG)
        about.transient(self.root)
        about.grab_set()
        tk.Label(about, text="KERBEROS", fg=FG, bg=BG, font=("Consolas", 16, "bold")).pack(pady=(15,5))
        tk.Label(about, text="Sécurité desktop locale — Windows 7/10", fg="#aaaaaa", bg=BG, font=FONT_UI).pack()
        tk.Label(about, text="GPLv3 · Zéro cloud · Pas de trace", fg="#aaaaaa", bg=BG, font=FONT_UI).pack(pady=(0,10))
        info = (
            "✅ Clic sur 🔍 dans le rapport → ouvre le fichier à la ligne exacte\n"
            "📂 Double-clique sur un .py → dry-run (--dry-run)\n"
            "🖨️ Rapport auto-ouvert dans Notepad\n"
            "🛡️ Conforme GPLv3 — https://www.gnu.org/licenses/gpl-3.0.html\n"
            "📦 Code : https://github.com/victorpozen/kerberos\n"
            "❤️ Soutien : https://liberapay.com/EthicalKerberos/"
        )
        txt = tk.Text(about, wrap=tk.WORD, font=("Consolas", 9), bg="#0a0a0a", fg=FG, height=12)
        txt.insert(tk.END, info)
        txt.config(state=tk.DISABLED)
        txt.pack(padx=15, pady=10, fill=tk.BOTH, expand=True)
        tk.Button(about, text="Fermer", command=about.destroy, bg="#2d2d2d", fg="white", font=FONT_UI).pack(pady=5)

    def relancer_en_admin(self):
        if not KerberosDebug.is_admin():
            try:
                ctypes.windll.shell32.ShellExecuteW(None, "runas", sys.executable, " ".join(sys.argv), None, 1)
                sys.exit()
            except: pass

    def choisir_dossier(self):
        dossier = filedialog.askdirectory()
        if dossier: self.generer_rapport([dossier])

    def analyser(self):
        cibles = [d for d, v in self.vars.items() if v.get()]
        if not cibles: messagebox.showwarning("Sélection", "Cochez un lecteur ou choisissez un dossier."); return
        self.generer_rapport(cibles)

    def generer_rapport(self, cibles):
        self.console.delete(1.0, tk.END)
        self.console.insert(tk.END, "🔍 Initialisation…\n\n")

        self.progress_bar.pack(fill=tk.X, padx=12, pady=(0, 6))
        self.progress_var.set(0)
        self.root.update_idletasks()

        # Double-clic → dry-run
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
            total_py = sum(1 for cible in cibles for _, _, files in os.walk(cible) for f in files if f.endswith('.py'))
            processed = 0
            lignes = []
            lignes.append("=" * 70)
            lignes.append("RAPPORT KERBEROS v3.3 – ANALYSE PROFONDE")
            lignes.append("=" * 70)
            lignes.append(f"Date : {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
            lignes.append(f"Système : {platform.platform()}")
            lignes.append(f"Admin : {'Oui' if KerberosDebug.is_admin() else 'Non'}")
            lignes.append("Licence : https://www.gnu.org/licenses/gpl-3.0.html")
            lignes.append("Code source : https://github.com/victorpozen/kerberos")
            lignes.append("Soutien éthique : https://liberapay.com/EthicalKerberos/")
            lignes.append("=" * 70)
            lignes.append("")

            for cible in cibles:
                lignes.append(f"\n{'='*70}\nCIBLE : {cible}\n{'='*70}")
                if os.path.exists(cible) and len(cible) == 3 and cible[1:] == ":\\": 
                    lignes.append(f"📊 Espace : {espace_disque_win(cible)}")
                else:
                    try:
                        size = sum(os.path.getsize(os.path.join(dp, f)) for dp, _, fn in os.walk(cible) for f in fn)
                        lignes.append(f"📊 Taille : {size / (1024**2):.1f} Mo")
                    except: pass
                lignes.append("\nArborescence (prof ≤4) :")

                tree_lines = arbre_securise_v3(cible, max_depth=MAX_DEPTH, ignore_recycle=self.ignore_recycle.get())
                for display, filepath, tag_name, handler in tree_lines:
                    self.console.insert(tk.END, display + "\n")
                    if tag_name and handler:
                        # Trouver la position de "🔍"
                        if "🔍" in display:
                            pos = display.rfind("🔍")
                            start = f"{float(self.console.index(tk.END)) - 1}.{pos}"
                            end = f"{start}+1c"
                            self.console.tag_add(tag_name, start, end)
                            self.console.tag_config(tag_name, foreground="#66ccff", underline=True)
                            self.console.tag_bind(tag_name, "<Button-1>", handler())
                            self.console.tag_bind(tag_name, "<Enter>", lambda e: self.console.config(cursor="hand2"))
                            self.console.tag_bind(tag_name, "<Leave>", lambda e: self.console.config(cursor=""))
                lignes.append("")

            lignes.append("✅ Rapport généré – Kerberos v3.3 (GPLv3)")
            rapport = "\n".join(lignes)
            with open("rapport_disques_v3.3.txt", "w", encoding="utf-8") as f:
                f.write(rapport)
            self.console.insert(tk.END, rapport + f"\n\n💾 Sauvegardé : rapport_disques_v3.3.txt\n", "exec")

            # ➕ OUVERTURE AUTO DU RAPPORT
            try:
                os.startfile("rapport_disques_v3.3.txt")
                self.console.insert(tk.END, "🖨️ Rapport ouvert dans Notepad.\n", "exec")
            except: pass

        finally:
            self.root.after(800, lambda: self.progress_bar.pack_forget())
            self.root.title("🔍 Kerberos – Analyseur de Disques v3.3 (GPLv3)")

    def executer_dry_run(self, filepath):
        if not os.path.isfile(filepath): return
        self.console.insert(tk.END, f"\n▶️ Dry-run : {os.path.basename(filepath)}\n", "exec")
        try:
            result = subprocess.run([sys.executable, filepath, "--dry-run"],
                                    capture_output=True, text=True, timeout=10,
                                    cwd=os.path.dirname(filepath))
            if result.stdout.strip(): self.console.insert(tk.END, result.stdout.strip() + "\n", "exec")
            if result.stderr.strip(): self.console.insert(tk.END, "STDERR:\n" + result.stderr.strip() + "\n", "error")
            msg = "✅ Exit 0" if result.returncode == 0 else f"⚠️ Exit {result.returncode}"
            self.console.insert(tk.END, f"{msg}\n", "exec" if result.returncode == 0 else "error")
        except: self.console.insert(tk.END, "💥 Erreur dry-run\n", "error")
        self.console.see(tk.END)

# === LANCEMENT ===
if __name__ == "__main__":
    root = tk.Tk()
    app = KerberosDiskAnalyzer(root)
    root.mainloop()