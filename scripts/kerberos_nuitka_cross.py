# -*- coding: utf-8 -*-
# kerberos_nuitka_cross.v1.2.py
# ✅ GUI 100 % responsive • MinGW scan • Rapports HTML • Copier/coller actif
# 💀 Rien n’est caché — GPLv3 — https://liberapay.com/EthicalKerberos/

import os
import sys
import shutil
import subprocess
import threading
import queue
import time
import webbrowser
import tkinter as tk
from tkinter import ttk, filedialog, scrolledtext, messagebox

# === CONFIG — adaptée à ta structure H:\ ===
SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))

PYTHON_32 = r"H:\PYTHON\python.32.bits\python.exe"
PYTHON_64 = r"H:\PYTHON\python.64.bits\python.exe"
MINGW32 = r"H:\PYTHON\mingw32\bin"
MINGW64 = r"H:\PYTHON\mingw64\bin"
BUILD_DIR = os.path.join(SCRIPT_DIR, "build")

class NuitkaCrossBuilder:
    def __init__(self, root):
        self.root = root
        root.title("🛠️ Kerberos – Nuitka Cross 32/64 bits v1.2")
        root.geometry("860x760")
        root.configure(bg="#0d0d15")

        title = tk.Label(root, text="Nuitka → 32 & 64 bits — Mode Kerberos Pure",
                         fg="#a0ffa0", bg="#0d0d15", font=("Consolas", 14, "bold"))
        title.pack(pady=10)

        # === Sélection script/icône ===
        file_frame = tk.Frame(root, bg="#0d0d15")
        file_frame.pack(pady=5)

        tk.Label(file_frame, text="Script Python :", fg="#a0ffa0", bg="#0d0d15", font=("Consolas", 10)).pack(anchor=tk.W)
        self.script_var = tk.StringVar()
        tk.Entry(file_frame, textvariable=self.script_var, width=70, font=("Consolas", 10)).pack(pady=2)
        tk.Button(file_frame, text="📂 Choisir .py", command=self.select_script,
                  bg="#2d2d2d", fg="white", font=("Consolas", 10)).pack(pady=2)

        tk.Label(file_frame, text="Icône (optionnel) :", fg="#a0ffa0", bg="#0d0d15", font=("Consolas", 10)).pack(anchor=tk.W)
        self.icon_var = tk.StringVar()
        tk.Entry(file_frame, textvariable=self.icon_var, width=70, font=("Consolas", 10)).pack(pady=2)
        tk.Button(file_frame, text="📂 Choisir .ico", command=self.select_icon,
                  bg="#2d2d2d", fg="white", font=("Consolas", 10)).pack(pady=2)

        # === Options ===
        opt_frame = tk.Frame(root, bg="#0d0d15")
        opt_frame.pack(pady=10)
        self.build_32_var = tk.BooleanVar(value=True)
        self.build_64_var = tk.BooleanVar(value=True)
        self.no_console_var = tk.BooleanVar(value=True)
        self.clean_build_var = tk.BooleanVar(value=True)

        tk.Checkbutton(opt_frame, text="📦 Compiler 32 bits (Win7/10 32)", variable=self.build_32_var,
                       bg="#0d0d15", fg="#a0ffa0", selectcolor="#333").pack(anchor=tk.W)
        tk.Checkbutton(opt_frame, text="📦 Compiler 64 bits (Win10 64)", variable=self.build_64_var,
                       bg="#0d0d15", fg="#a0ffa0", selectcolor="#333").pack(anchor=tk.W)
        tk.Checkbutton(opt_frame, text="🖥️ Désactiver la console", variable=self.no_console_var,
                       bg="#0d0d15", fg="#a0ffa0", selectcolor="#333").pack(anchor=tk.W)
        tk.Checkbutton(opt_frame, text="🗑️ Nettoyer après compilation", variable=self.clean_build_var,
                       bg="#0d0d15", fg="#a0ffa0", selectcolor="#333").pack(anchor=tk.W)

        # === Boutons d'action ===
        btn_frame = tk.Frame(root, bg="#0d0d15")
        btn_frame.pack(pady=10)

        self.btn_verify = tk.Button(btn_frame, text="🔍 Vérifier toolchain", command=self.verify_toolchain,
                                    bg="#3a5fcd", fg="white", font=("Consolas", 10))
        self.btn_verify.pack(side=tk.LEFT, padx=5)

        self.btn_compile = tk.Button(btn_frame, text="🚀 Compiler 32/64 bits", command=self.compile_both,
                                     bg="#8b0000", fg="white", font=("Consolas", 12))
        self.btn_compile.pack(side=tk.LEFT, padx=5)

        self.btn_open_build = tk.Button(btn_frame, text="📂 Ouvrir build/", command=self.open_build_dir,
                                        bg="#006400", fg="white", font=("Consolas", 10), state="disabled")
        self.btn_open_build.pack(side=tk.LEFT, padx=5)

        self.btn_open_toolchain_report = tk.Button(btn_frame, text="📄 Rapport toolchain", command=self.open_toolchain_report,
                                                   bg="#5d3a8c", fg="white", font=("Consolas", 10), state="disabled")
        self.btn_open_toolchain_report.pack(side=tk.LEFT, padx=5)

        self.btn_open_final_report = tk.Button(btn_frame, text="📄 Rapport final", command=self.open_final_report,
                                               bg="#2e7d32", fg="white", font=("Consolas", 10), state="disabled")
        self.btn_open_final_report.pack(side=tk.LEFT, padx=5)

        # === Barre de progression ===
        progress_frame = tk.Frame(root, bg="#0d0d15")
        progress_frame.pack(pady=8, padx=20, fill=tk.X)
        self.progress_label = tk.Label(progress_frame, text="Attente...", fg="#a0ffa0", bg="#0d0d15", font=("Consolas", 10))
        self.progress_label.pack()
        self.progress_bar = ttk.Progressbar(progress_frame, orient="horizontal", length=820, mode="determinate")
        self.progress_bar.pack(pady=5)

        # === Console (copiable) ===
        self.console = scrolledtext.ScrolledText(
            root, wrap=tk.WORD, font=("Consolas", 10),
            bg="#0a0a0a", fg="#a0ffa0", height=14,
            selectbackground="#00ff88", selectforeground="#000000",
            exportselection=True
        )
        self.console.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)
        self.console.bind("<Key>", lambda e: "break")  # lecture seule mais sélectionnable

        # Stockage
        self.toolchain_ok = {"32": False, "64": False}
        self.results = {"32": {}, "64": {}}
        sys.stdout = self

    def write(self, msg):
        if msg.strip():
            self.console.insert(tk.END, msg)
            self.console.see(tk.END)
        self.root.update_idletasks()

    def flush(self): pass

    def select_script(self):
        path = filedialog.askopenfilename(title="Sélectionner un script Python", filetypes=[("Python", "*.py")])
        if path:
            self.script_var.set(path)

    def select_icon(self):
        path = filedialog.askopenfilename(title="Sélectionner une icône", filetypes=[("Icon", "*.ico")])
        if path:
            self.icon_var.set(path)

    def update_progress(self, percent, msg):
        self.progress_bar["value"] = percent
        self.progress_label.config(text=f"{msg} ({int(percent)}%)")
        self.root.update_idletasks()

    def open_build_dir(self):
        if os.path.exists(BUILD_DIR):
            os.startfile(BUILD_DIR)
        else:
            messagebox.showwarning("⚠️ Dossier introuvable", f"Le dossier build n'existe pas :\n{BUILD_DIR}")

    def open_toolchain_report(self):
        report = os.path.join(BUILD_DIR, "toolchain_report.html")
        if os.path.exists(report):
            webbrowser.open("file://" + os.path.abspath(report))
        else:
            messagebox.showwarning("📄 Rapport introuvable", "Aucun rapport toolchain généré.")

    def open_final_report(self):
        report = os.path.join(BUILD_DIR, "kerberos_report.html")
        if os.path.exists(report):
            webbrowser.open("file://" + os.path.abspath(report))
        else:
            messagebox.showwarning("📄 Rapport introuvable", "Aucun rapport final généré.")

    # ========== TOOLCHAIN CHECK ==========
    def check_exe(self, name, exe_path, args=None):
        if not os.path.exists(exe_path):
            self.write(f"❌ {name} : introuvable → {exe_path}\n")
            return False, ""
        try:
            cmd = [exe_path] + (args or ["--version"])
            result = subprocess.run(cmd, capture_output=True, text=True, timeout=10,
                                   creationflags=subprocess.CREATE_NO_WINDOW)
            if result.returncode == 0:
                ver = (result.stdout or result.stderr).strip().split("\n")[0]
                self.write(f"✅ {name} : {ver}\n")
                return True, ver
            else:
                self.write(f"⚠️ {name} : échec ({result.stderr.strip()})\n")
                return False, ""
        except Exception as e:
            self.write(f"💥 {name} : erreur → {e}\n")
            return False, str(e)

    def check_mingw(self, mingw_path):
        required = ["gcc.exe", "ld.exe", "ar.exe", "dlltool.exe"]
        missing = [f for f in required if not os.path.exists(os.path.join(mingw_path, f))]
        if missing:
            self.write(f"❌ MinGW incomplet dans {mingw_path} → manque : {', '.join(missing)}\n")
            return False
        self.write(f"✅ MinGW complet : {mingw_path}\n")
        return True

    def verify_toolchain(self):
        self.write("\n🔍 Vérification complète du toolchain Kerberos...\n")
        os.makedirs(BUILD_DIR, exist_ok=True)

        # Tests
        py32_ok, py32_ver = self.check_exe("Python 32-bit", PYTHON_32)
        py64_ok, py64_ver = self.check_exe("Python 64-bit", PYTHON_64)
        mingw32_ok = self.check_mingw(MINGW32)
        mingw64_ok = self.check_mingw(MINGW64)

        self.toolchain_ok = {"32": py32_ok and mingw32_ok, "64": py64_ok and mingw64_ok}

        # Génération rapport HTML
        self.generate_toolchain_report(py32_ok, py32_ver, py64_ok, py64_ver, mingw32_ok, mingw64_ok)

        all_ok = all(self.toolchain_ok.values())
        self.write(f"\n{'🟢 Toolchain OK — prêt à compiler.' if all_ok else '🔴 Problème détecté — voir rapport.'}\n")
        self.btn_open_toolchain_report.config(state="normal")
        self.btn_compile.config(state="normal" if all_ok else "disabled")

    def generate_toolchain_report(self, py32_ok, py32_ver, py64_ok, py64_ver, mingw32_ok, mingw64_ok):
        report_path = os.path.join(BUILD_DIR, "toolchain_report.html")
        html = f"""<!DOCTYPE html>
<html lang="fr">
<head><meta charset="UTF-8"><title>🔧 Kerberos — Rapport Toolchain</title>
<style>
body {{ background:#0d0d15; color:#e0e0ff; font-family:'Consolas', monospace; margin:30px; }}
h1 {{ color:#00ff88; text-align:center; }}
.ok {{ color:#81c784; }}
.err {{ color:#ff5252; }}
table {{ width:100%; border-collapse:collapse; margin:20px 0; }}
th, td {{ padding:12px; text-align:left; border-bottom:1px solid #333; }}
th {{ background:#1a1a25; }}
.footer {{ margin-top:40px; font-size:0.9em; color:#707090; }}
</style>
</head>
<body>
<h1>🔧 Rapport Toolchain Kerberos</h1>
<p>Généré le : {time.strftime('%Y-%m-%d %H:%M:%S')}</p>

<table>
  <tr><th>Composant</th><th>Statut</th><th>Détails</th></tr>
  <tr><td>Python 32-bit</td><td class="{'ok' if py32_ok else 'err'}">{'✅ OK' if py32_ok else '❌ Échec'}</td><td>{py32_ver or '—'}</td></tr>
  <tr><td>MinGW 32-bit</td><td class="{'ok' if mingw32_ok else 'err'}">{'✅ OK' if mingw32_ok else '❌ Échec'}</td><td>{MINGW32}</td></tr>
  <tr><td>Python 64-bit</td><td class="{'ok' if py64_ok else 'err'}">{'✅ OK' if py64_ok else '❌ Échec'}</td><td>{py64_ver or '—'}</td></tr>
  <tr><td>MinGW 64-bit</td><td class="{'ok' if mingw64_ok else 'err'}">{'✅ OK' if mingw64_ok else '❌ Échec'}</td><td>{MINGW64}</td></tr>
</table>

<div class="footer">
  💀 Kerberos — Rien n’est caché — GPLv3<br>
  📌 Si échec : vérifie les chemins dans le script ou relance setup_mingw_*.bat
</div>
</body>
</html>"""

        with open(report_path, "w", encoding="utf-8") as f:
            f.write(html)

    # ========== COMPILATION ==========
    def compile_with_live_output(self, cmd, env, cwd, log_path, arch):
        q = queue.Queue()

        def reader():
            try:
                with open(log_path, "w", encoding="utf-8") as logf:
                    logf.write(f"=== Compilation {arch}-bit ===\nCommande : {' '.join(cmd)}\n{'='*60}\n\n")
                    proc = subprocess.Popen(
                        cmd, env=env, cwd=cwd,
                        stdout=subprocess.PIPE, stderr=subprocess.STDOUT,
                        text=True, encoding="utf-8", errors="replace",
                        creationflags=subprocess.CREATE_NO_WINDOW
                    )
                    for line in iter(proc.stdout.readline, ''):
                        if line:
                            q.put(line.strip())
                            logf.write(line)
                            logf.flush()
                    proc.wait()
                    q.put(("DONE", proc.returncode))
            except Exception as e:
                q.put(("ERROR", str(e)))

        threading.Thread(target=reader, daemon=True).start()

        def updater():
            try:
                while True:
                    item = q.get_nowait()
                    if isinstance(item, tuple):
                        status, code = item
                        if status == "DONE":
                            success = (code == 0)
                            self.results[arch] = {
                                "success": success,
                                "log": log_path,
                                "exe_path": self.find_exe_path(arch)
                            }
                            self.write(f"\n{'✅' if success else '❌'} Compilation {arch}-bit terminée (code {code})\n")
                        else:
                            self.write(f"\n💥 Erreur {arch}-bit : {code}\n")
                        return
                    else:
                        self.write(item + "\n")
            except queue.Empty:
                self.root.after(50, updater)

        updater()

    def find_exe_path(self, arch):
        script = self.script_var.get()
        if not script:
            return ""
        base = os.path.splitext(os.path.basename(script))[0]
        for suffix in [".dist", f".{arch}.dist", "_dist"]:
            dist = os.path.join(BUILD_DIR, base + suffix)
            exe = os.path.join(dist, base + ".exe")
            if os.path.exists(exe):
                return exe
        return ""

    def compile_single(self, arch):
        python_exe = PYTHON_32 if arch == "32" else PYTHON_64
        mingw_path = MINGW32 if arch == "32" else MINGW64

        if not self.toolchain_ok[arch]:
            self.write(f"⚠️ Compilation {arch}-bit annulée : toolchain invalide.\n")
            self.results[arch] = {"success": False, "log": "", "exe_path": ""}
            return

        script = self.script_var.get()
        if not script or not script.endswith(".py") or not os.path.exists(script):
            self.write(f"❌ Script invalide ({arch}-bit).\n")
            return

        os.makedirs(BUILD_DIR, exist_ok=True)
        log_path = os.path.join(BUILD_DIR, f"compilation_{arch}.log")

        cmd = [
            python_exe, "-m", "nuitka",
            "--standalone",
            "--onefile",
            "--mingw64",
            "--enable-plugin=tk-inter",
            "--assume-yes-for-downloads",
            "--output-dir=" + BUILD_DIR
        ]
        if self.no_console_var.get():
            cmd.append("--windows-disable-console")
        icon = self.icon_var.get().strip()
        if icon and os.path.exists(icon):
            cmd.append(f"--windows-icon-from-ico={icon}")
        cmd.append(script)

        env = os.environ.copy()
        env["PATH"] = mingw_path + os.pathsep + env["PATH"]
        env["NO_COLOR"] = "1"

        self.write(f"\n📦 Démarrage compilation {arch}-bit...\n→ Log : {log_path}\n")
        self.compile_with_live_output(cmd, env, SCRIPT_DIR, log_path, arch)

    def cleanup_dist(self, arch):
        if not self.clean_build_var.get():
            return
        script = self.script_var.get()
        if not script:
            return
        base = os.path.splitext(os.path.basename(script))[0]
        for suffix in [".dist", f".{arch}.dist"]:
            dist_dir = os.path.join(BUILD_DIR, base + suffix)
            if os.path.exists(dist_dir):
                log_clean = os.path.join(BUILD_DIR, f"cleanup_{arch}.log")
                kept = removed = 0
                try:
                    with open(log_clean, "w", encoding="utf-8") as f:
                        f.write(f"=== Nettoyage {arch}-bit ===\n")
                        for item in os.listdir(dist_dir):
                            path = os.path.join(dist_dir, item)
                            if item == base + ".exe":
                                kept += 1
                                f.write(f"[GARDÉ] {item}\n")
                            else:
                                try:
                                    if os.path.isdir(path):
                                        shutil.rmtree(path)
                                    else:
                                        os.remove(path)
                                    removed += 1
                                    f.write(f"[SUPPRIMÉ] {item}\n")
                                except Exception as e:
                                    f.write(f"[ERREUR] {item} → {e}\n")
                        f.write(f"\n✅ {kept} gardé(s), {removed} supprimé(s).\n")
                    self.write(f"🧹 Nettoyage {arch}-bit terminé. Log : {log_clean}\n")
                except Exception as e:
                    self.write(f"⚠️ Échec nettoyage {arch} : {e}\n")
                break

    def generate_final_report(self):
        report_path = os.path.join(BUILD_DIR, "kerberos_report.html")
        script = os.path.basename(self.script_var.get() or "inconnu.py")
        html = f"""<!DOCTYPE html>
<html lang="fr">
<head><meta charset="UTF-8"><title>🛡️ Kerberos — Rapport Compilation</title>
<style>
body {{ background:#0d0d15; color:#e0e0ff; font-family:'Consolas', monospace; margin:30px; }}
h1 {{ color:#00ff88; text-align:center; }}
.ok {{ color:#81c784; }}
.err {{ color:#ff5252; }}
table {{ width:100%; border-collapse:collapse; margin:20px 0; }}
th, td {{ padding:12px; text-align:left; border-bottom:1px solid #333; }}
th {{ background:#1a1a25; }}
.footer {{ margin-top:40px; font-size:0.9em; color:#707090; }}
</style>
</head>
<body>
<h1>🛡️ Rapport Kerberos — Compilation</h1>
<p>Script : <code>{script}</code><br>
Généré le : {time.strftime('%Y-%m-%d %H:%M:%S')}</p>

<table>
  <tr><th>Architecture</th><th>Résultat</th><th>.exe</th><th>Log</th></tr>
"""
        for arch in ["32", "64"]:
            res = self.results.get(arch, {})
            success = res.get("success", False)
            exe = res.get("exe_path", "")
            log = res.get("log", "")
            status = "✅ Succès" if success else "❌ Échec"
            cls = "ok" if success else "err"
            exe_link = f'<a href="file:///{exe}" style="color:#a0ffa0;">{os.path.basename(exe)}</a>' if exe else "—"
            log_link = f'<a href="file:///{log}" style="color:#70a0ff;">📄 log</a>' if log else "—"
            html += f'  <tr><td>{arch}-bit</td><td class="{cls}">{status}</td><td>{exe_link}</td><td>{log_link}</td></tr>\n'

        html += f"""
</table>

<div class="footer">
  💀 Kerberos — Rien n’est caché — GPLv3<br>
  🔗 <a href="https://liberapay.com/EthicalKerberos/" style="color:#00ff88;">→ Soutenir le projet</a>
</div>
</body>
</html>"""

        with open(report_path, "w", encoding="utf-8") as f:
            f.write(html)

        self.btn_open_final_report.config(state="normal")

    def compile_both(self):
        script = self.script_var.get()
        if not script or not script.endswith(".py"):
            messagebox.showerror("Erreur", "Veuillez choisir un fichier .py valide.")
            return

        self.results = {"32": {}, "64": {}}
        self.btn_open_build.config(state="disabled")

        if self.build_32_var.get():
            self.update_progress(0, "Compilation 32-bit…")
            self.compile_single("32")
        if self.build_64_var.get():
            self.update_progress(50, "Compilation 64-bit…")
            self.compile_single("64")

        # Lancement asynchrone de finalisation
        def finalize():
            time.sleep(2)  # attendre fin des threads
            for arch in ["32", "64"]:
                if self.results.get(arch, {}).get("success"):
                    self.cleanup_dist(arch)
            self.generate_final_report()
            any_success = any(r.get("success") for r in self.results.values())
            if any_success:
                self.btn_open_build.config(state="normal")
            self.update_progress(100, "✅ Terminé")
            self.write("\n✨ Compilation terminée. Rapports disponibles.\n")

        threading.Thread(target=finalize, daemon=True).start()

# === Lancement ===
if __name__ == "__main__":
    root = tk.Tk()
    app = NuitkaCrossBuilder(root)
    root.mainloop()