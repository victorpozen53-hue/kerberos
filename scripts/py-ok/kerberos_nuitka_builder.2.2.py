# -*- coding: utf-8 -*-
# kerberos_nuitka_builder.py
# Compilateur Nuitka 32/64 bits – Kerberos v1.0
# 🛡️ Sécurité éthique locale pour vieux PCs (Win 7/10)
# 📄 Licence : GNU GPLv3 – https://liberapay.com/EthicalKerberos/

import os
import sys
import shutil
import subprocess
import threading
import tkinter as tk
from tkinter import ttk, filedialog, scrolledtext, messagebox
import time

# === Chemins configurés ===
SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))

# Python 32/64 bits
PYTHON_32 = r"H:\PYTHON\python.32.bits\python.exe"
PYTHON_64 = r"H:\PYTHON\python.64.bits\python.exe"

# MinGW
MINGW32 = r"I:\mingw32\bin"
MINGW64 = r"I:\mingw64\bin"

# Nuitka develop (nécessaire pour Python 3.13 + MinGW64)
NUITKA_DEV = r"I:\Nuitka-develop\bin\nuitka-run.py"

class KerberosNuitkaBuilder:
    def __init__(self, root):
        self.root = root
        self.root.title("Kerberos – Nuitka 32/64 bits")
        self.root.geometry("860x720")
        self.root.configure(bg="#1e1e1e")

        title = tk.Label(
            root,
            text="Nuitka → 32 & 64 bits – Mode Kerberos",
            fg="#00ff00",
            bg="#1e1e1e",
            font=("Consolas", 14, "bold")
        )
        title.pack(pady=10)

        # === Sélection du script et de l'icône ===
        file_frame = tk.Frame(root, bg="#1e1e1e")
        file_frame.pack(pady=5)

        tk.Label(file_frame, text="Script Python (.py) :", fg="#00ff00", bg="#1e1e1e", font=("Consolas", 10)).pack(anchor=tk.W)
        self.script_var = tk.StringVar()
        tk.Entry(file_frame, textvariable=self.script_var, width=72, font=("Consolas", 10)).pack(pady=2)
        tk.Button(file_frame, text="📂 Choisir script", command=self.select_script, bg="#2d2d2d", fg="white", font=("Consolas", 10)).pack(pady=2)

        tk.Label(file_frame, text="Icône (.ico) :", fg="#00ff00", bg="#1e1e1e", font=("Consolas", 10)).pack(anchor=tk.W)
        self.icon_var = tk.StringVar()
        tk.Entry(file_frame, textvariable=self.icon_var, width=72, font=("Consolas", 10)).pack(pady=2)
        tk.Button(file_frame, text="📂 Choisir icône", command=self.select_icon, bg="#2d2d2d", fg="white", font=("Consolas", 10)).pack(pady=2)

        # === Options ===
        opt_frame = tk.Frame(root, bg="#1e1e1e")
        opt_frame.pack(pady=8)
        self.build_32 = tk.BooleanVar(value=True)
        self.build_64 = tk.BooleanVar(value=True)
        self.no_console = tk.BooleanVar(value=True)
        self.clean_dist = tk.BooleanVar(value=True)

        tk.Checkbutton(opt_frame, text="📦 Compiler en 32 bits (Win 7/10)", variable=self.build_32, bg="#1e1e1e", fg="#00ff00", selectcolor="#333").pack(anchor=tk.W)
        tk.Checkbutton(opt_frame, text="📦 Compiler en 64 bits (Win 10)", variable=self.build_64, bg="#1e1e1e", fg="#00ff00", selectcolor="#333").pack(anchor=tk.W)
        tk.Checkbutton(opt_frame, text="🖥️ Sans console", variable=self.no_console, bg="#1e1e1e", fg="#00ff00", selectcolor="#333").pack(anchor=tk.W)
        tk.Checkbutton(opt_frame, text="🧹 Nettoyer le .dist (garder .exe)", variable=self.clean_dist, bg="#1e1e1e", fg="#00ff00", selectcolor="#333").pack(anchor=tk.W)

        # === Progression ===
        self.progress_label = tk.Label(root, text="Prêt à compiler.", fg="#00ff00", bg="#1e1e1e", font=("Consolas", 10))
        self.progress_label.pack(pady=5)
        self.progress = ttk.Progressbar(root, length=800, mode="determinate")
        self.progress.pack(pady=5)

        # === Boutons ===
        btn_frame = tk.Frame(root, bg="#1e1e1e")
        btn_frame.pack(pady=8)
        self.btn_compile = tk.Button(btn_frame, text="🚀 Compiler", command=self.start_compile, bg="#8b0000", fg="white", font=("Consolas", 12))
        self.btn_compile.pack(side=tk.LEFT, padx=5)
        self.btn_open = tk.Button(btn_frame, text="📂 Ouvrir build/", command=self.open_build, bg="#006400", fg="white", font=("Consolas", 10), state="disabled")
        self.btn_open.pack(side=tk.LEFT, padx=5)

        # === Console ===
        self.console = scrolledtext.ScrolledText(
            root, wrap=tk.WORD, font=("Consolas", 9),
            bg="#0a0a0a", fg="#00ff00", height=14, state="normal"
        )
        self.console.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)
        self.console.bind("<Key>", lambda e: "break")  # lecture seule mais sélectionnable

        sys.stdout = self

    def write(self, msg):
        if msg.strip():
            self.console.insert(tk.END, msg)
            self.console.see(tk.END)
        self.root.update_idletasks()

    def flush(self):
        pass

    def select_script(self):
        f = filedialog.askopenfilename(filetypes=[("Python", "*.py")])
        if f:
            self.script_var.set(f)

    def select_icon(self):
        f = filedialog.askopenfilename(filetypes=[("Icon", "*.ico")])
        if f:
            self.icon_var.set(f)

    def open_build(self):
        build = os.path.join(SCRIPT_DIR, "build")
        if os.path.exists(build):
            os.startfile(build)
        else:
            messagebox.showwarning("⚠️", "Dossier 'build' non trouvé.")

    def build_single(self, python_exe, mingw_bin, arch):
        script = self.script_var.get().strip()
        if not script or not script.endswith(".py") or not os.path.isfile(script):
            self.write(f"❌ Script invalide ({arch} bits)\n")
            return False

        # Vérif dépendances
        for path, name in [(python_exe, "Python"), (mingw_bin, "MinGW")]:
            if not os.path.exists(path):
                self.write(f"❌ {name} {arch} bits introuvable : {path}\n")
                return False

        base_name = os.path.splitext(os.path.basename(script))[0]
        dist_dir = os.path.join(SCRIPT_DIR, "build", f"{base_name}.dist")

        # === Construction de la commande ===
        cmd = [
            python_exe,
            NUITKA_DEV,  # Utilise la version dev pour Python 3.13
            "--standalone",
            "--mingw64",
            "--assume-yes-for-downloads",
            "--output-dir=build",
            "--enable-plugin=tk-inter",  # 🔑 Obligatoire pour Tkinter
        ]

        if self.no_console.get():
            cmd.append("--windows-console-mode=disable")  # ✅ Option moderne

        icon = self.icon_var.get().strip()
        if icon and os.path.isfile(icon):
            cmd.append(f"--windows-icon-from-ico={icon}")

        # Protéger le chemin du script s'il contient des espaces
        cmd.append(script)

        # === Environnement ===
        env = os.environ.copy()
        env["PATH"] = mingw_bin + os.pathsep + env["PATH"]
        env["NO_COLOR"] = "1"

        # === Logs ===
        log_path = os.path.join(SCRIPT_DIR, "build", f"kerberos_compilation_{arch}.log")
        os.makedirs(os.path.dirname(log_path), exist_ok=True)

        self.write(f"\n🔬 Compilation {arch} bits en cours…\n")
        self.write(f"➡️ Exécution : {' '.join(cmd)}\n\n")

        try:
            with open(log_path, "w", encoding="utf-8") as logf:
                logf.write(f"=== LOG COMPILATION KERBEROS – {arch} ===\n")
                logf.write(f"Date : {time.strftime('%Y-%m-%d %H:%M:%S')}\n")
                logf.write(f"Commande : {' '.join(cmd)}\n")
                logf.write("-" * 50 + "\n\n")

                proc = subprocess.Popen(
                    cmd, env=env, cwd=SCRIPT_DIR,
                    stdout=subprocess.PIPE, stderr=subprocess.STDOUT,
                    text=True, encoding="utf-8", errors="replace"
                )

                for line in proc.stdout:
                    logf.write(line)
                    logf.flush()
                    self.write(line)

                proc.wait()
                if proc.returncode == 0:
                    self.write(f"✅ {arch} bits : Compilation réussie.\n")
                    if self.clean_dist.get():
                        self._clean_dist(dist_dir, arch, base_name)
                    return True
                else:
                    self.write(f"❌ {arch} bits : Échec de compilation (code {proc.returncode}).\n")
                    return False

        except Exception as e:
            self.write(f"💥 Erreur {arch} bits : {e}\n")
            return False

    def _clean_dist(self, dist_dir, arch, base_name):
        if not os.path.isdir(dist_dir):
            self.write(f"⚠️ Dossier .dist absent pour {arch} bits.\n")
            return

        log_path = os.path.join(SCRIPT_DIR, "build", f"kerberos_cleanup_{arch}.log")
        kept = 0
        removed = 0

        with open(log_path, "w", encoding="utf-8") as logf:
            logf.write(f"=== NETTOYAGE KERBEROS – {arch} ===\n")
            exe_name = base_name + ".exe"
            for item in os.listdir(dist_dir):
                src = os.path.join(dist_dir, item)
                if item == exe_name:
                    logf.write(f"[GARDÉ] {item}\n")
                    kept += 1
                else:
                    try:
                        if os.path.isdir(src):
                            shutil.rmtree(src)
                        else:
                            os.unlink(src)
                        logf.write(f"[SUPPRIMÉ] {item}\n")
                        removed += 1
                    except Exception as e:
                        logf.write(f"[ERREUR] {item} → {e}\n")

            logf.write(f"\n✅ Nettoyage terminé : {kept} gardé(s), {removed} supprimé(s).\n")

        self.write(f"🧹 Nettoyage {arch} bits terminé. Rapport : {os.path.basename(log_path)}\n")

    def start_compile(self):
        if not self.script_var.get().strip().endswith(".py"):
            messagebox.showerror("❌ Erreur", "Veuillez sélectionner un fichier .py.")
            return
        self.btn_compile.config(state="disabled")
        threading.Thread(target=self._compile_task, daemon=True).start()

    def _compile_task(self):
        success = False
        total = self.build_32.get() + self.build_64.get()
        done = 0

        if self.build_32.get():
            if self.build_single(PYTHON_32, MINGW32, "32"):
                success = True
            done += 1
            self.progress["value"] = (done / total) * 100 if total else 100

        if self.build_64.get():
            if self.build_single(PYTHON_64, MINGW64, "64"):
                success = True
            done += 1
            self.progress["value"] = (done / total) * 100 if total else 100

        if success:
            self.progress_label.config(text="✅ Compilation terminée.")
            self.btn_open.config(state="normal")
        else:
            self.progress_label.config(text="❌ Échec complet.")
        self.btn_compile.config(state="normal")


if __name__ == "__main__":
    root = tk.Tk()
    app = KerberosNuitkaBuilder(root)
    root.mainloop()