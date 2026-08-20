# -*- coding: utf-8 -*-
# kerberos_nuitka_cross.py
# 🛡️ Compilateur Nuitka 32/64 bits – Kerberos v1.0 (PORTABLE)
# Sécurité éthique locale pour vieux PCs (Win 7/10)
# Licence : GNU GPLv3 – https://liberapay.com/EthicalKerberos/

import os
import sys
import json
import shutil
import subprocess
import threading
import tkinter as tk
from tkinter import ttk, filedialog, scrolledtext, messagebox
import time

SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
CONFIG_DIR  = os.path.join(SCRIPT_DIR, "config")
BUILD_DIR   = os.path.join(SCRIPT_DIR, "build")
CONFIG_FILE = os.path.join(CONFIG_DIR, "compiler.json")

os.makedirs(CONFIG_DIR, exist_ok=True)
os.makedirs(BUILD_DIR,  exist_ok=True)

DEFAULT_CONFIG = {
    "python_32": "",
    "python_64": "",
    "mingw32":   "",
    "mingw64":   ""
}

# ============================================================
# DÉTECTION AUTOMATIQUE DU BON python.exe
# ============================================================

def find_python_exe(folder: str, target_bits: int) -> str:
    """
    Cherche le bon python.exe dans un dossier Python.
    Vérifie l'architecture réelle (32 ou 64 bits) avec struct.calcsize.
    Retourne le chemin si trouvé et correct, sinon "".
    """
    if not folder or not os.path.isdir(folder):
        return ""

    # Candidats dans l'ordre de priorité
    candidates = ["python.exe", "python3.exe", "pythonw.exe"]

    # Cherche aussi dans les sous-dossiers courants (ex: H:\python.32\python.exe)
    search_dirs = [folder]
    for sub in os.listdir(folder):
        full = os.path.join(folder, sub)
        if os.path.isdir(full):
            search_dirs.append(full)

    for directory in search_dirs:
        for name in candidates:
            exe = os.path.join(directory, name)
            if not os.path.isfile(exe):
                continue
            # Vérifie l'architecture réelle via struct.calcsize
            bits = _get_python_bits(exe)
            if bits == target_bits:
                return exe
            # Si on ne peut pas détecter, on accepte quand même pythonw en dernier recours
    
    # 2ème passe : retourner n'importe quel python.exe trouvé (sans vérif archi)
    for directory in search_dirs:
        for name in candidates:
            exe = os.path.join(directory, name)
            if os.path.isfile(exe):
                return exe

    return ""

def _get_python_bits(python_exe: str) -> int:
    """
    Lance python_exe -c "import struct; print(struct.calcsize('P')*8)"
    et retourne 32 ou 64. Retourne 0 si erreur.
    """
    try:
        result = subprocess.run(
            [python_exe, "-c", "import struct; print(struct.calcsize('P')*8)"],
            capture_output=True, text=True, timeout=5
        )
        val = result.stdout.strip()
        if val in ("32", "64"):
            return int(val)
    except Exception:
        pass
    return 0

def _get_python_version(python_exe: str) -> str:
    """Retourne la version Python ex: '3.11.4' ou '?' si erreur."""
    try:
        result = subprocess.run(
            [python_exe, "--version"],
            capture_output=True, text=True, timeout=5
        )
        out = (result.stdout + result.stderr).strip()
        # "Python 3.11.4" → "3.11.4"
        if out.lower().startswith("python"):
            return out.split()[-1]
    except Exception:
        pass
    return "?"

def _check_nuitka(python_exe: str) -> bool:
    """Vérifie si nuitka est installé pour ce Python."""
    try:
        result = subprocess.run(
            [python_exe, "-m", "nuitka", "--version"],
            capture_output=True, text=True, timeout=8
        )
        return result.returncode == 0
    except Exception:
        return False

# ============================================================
# CONFIG
# ============================================================

def load_config():
    if os.path.isfile(CONFIG_FILE):
        try:
            with open(CONFIG_FILE, "r", encoding="utf-8") as f:
                cfg = json.load(f)
                for k, v in DEFAULT_CONFIG.items():
                    if k not in cfg:
                        cfg[k] = v
                return cfg
        except Exception:
            pass
    return DEFAULT_CONFIG.copy()

def save_config(cfg):
    with open(CONFIG_FILE, "w", encoding="utf-8") as f:
        json.dump(cfg, f, indent=4, ensure_ascii=False)

# ============================================================
# UI
# ============================================================

class NuitkaCrossBuilder:
    def __init__(self, root):
        self.root = root
        self.root.title("Kerberos – Nuitka 32/64 bits (PORTABLE)")
        self.root.geometry("900x860")
        self.root.configure(bg="#1e1e1e")

        self.config = load_config()

        # ── Titre ──────────────────────────────────────────
        tk.Label(root,
            text="Nuitka → 32 & 64 bits – Mode Portable Kerberos",
            fg="#00ff00", bg="#1e1e1e", font=("Consolas", 14, "bold")
        ).pack(pady=5)

        # ── Chemins des outils ─────────────────────────────
        tools_frame = tk.LabelFrame(root,
            text="⚙️ Chemins des outils (dossiers Python ou fichier .exe direct)",
            bg="#1e1e1e", fg="#00ff00", font=("Consolas", 10))
        tools_frame.pack(pady=5, padx=10, fill=tk.X)

        self.py32_var   = tk.StringVar(value=self.config.get("python_32", ""))
        self.py64_var   = tk.StringVar(value=self.config.get("python_64", ""))
        self.mingw32_var = tk.StringVar(value=self.config.get("mingw32", ""))
        self.mingw64_var = tk.StringVar(value=self.config.get("mingw64", ""))

        # Labels de statut détection
        self.status_py32 = tk.StringVar(value="—")
        self.status_py64 = tk.StringVar(value="—")

        rows_tools = [
            ("Python 32 bits (dossier ou .exe) :", self.py32_var,
             self._select_py32_folder, self._select_py32_exe, self.status_py32),
            ("Python 64 bits (dossier ou .exe) :", self.py64_var,
             self._select_py64_folder, self._select_py64_exe, self.status_py64),
        ]
        for label, var, cmd_dir, cmd_exe, status_var in rows_tools:
            row = tk.Frame(tools_frame, bg="#1e1e1e")
            row.pack(fill=tk.X, padx=5, pady=3)
            tk.Label(row, text=label, fg="#00ff00", bg="#1e1e1e",
                     font=("Consolas", 9), width=35, anchor="w").pack(side=tk.LEFT)
            tk.Entry(row, textvariable=var, width=38,
                     font=("Consolas", 9), bg="#2d2d2d", fg="white",
                     insertbackground="white").pack(side=tk.LEFT, padx=4)
            tk.Button(row, text="📁 Dossier", command=cmd_dir,
                      bg="#2d2d2d", fg="#00ff00", font=("Consolas", 8)).pack(side=tk.LEFT, padx=2)
            tk.Button(row, text="📄 .exe", command=cmd_exe,
                      bg="#2d2d2d", fg="#00ff00", font=("Consolas", 8)).pack(side=tk.LEFT, padx=2)
            tk.Label(row, textvariable=status_var, fg="#888888", bg="#1e1e1e",
                     font=("Consolas", 8)).pack(side=tk.LEFT, padx=6)

        rows_mingw = [
            ("MinGW 32 bits (dossier bin/) :", self.mingw32_var, self._select_mingw32),
            ("MinGW 64 bits (dossier bin/) :", self.mingw64_var, self._select_mingw64),
        ]
        for label, var, cmd in rows_mingw:
            row = tk.Frame(tools_frame, bg="#1e1e1e")
            row.pack(fill=tk.X, padx=5, pady=3)
            tk.Label(row, text=label, fg="#00ff00", bg="#1e1e1e",
                     font=("Consolas", 9), width=35, anchor="w").pack(side=tk.LEFT)
            tk.Entry(row, textvariable=var, width=38,
                     font=("Consolas", 9), bg="#2d2d2d", fg="white",
                     insertbackground="white").pack(side=tk.LEFT, padx=4)
            tk.Button(row, text="📁 Dossier", command=cmd,
                      bg="#2d2d2d", fg="#00ff00", font=("Consolas", 8)).pack(side=tk.LEFT, padx=2)

        # Boutons actions chemins
        btn_row = tk.Frame(tools_frame, bg="#1e1e1e")
        btn_row.pack(pady=5)
        tk.Button(btn_row, text="🔍 Détecter python.exe automatiquement",
                  command=self._auto_detect,
                  bg="#004080", fg="white", font=("Consolas", 9)).pack(side=tk.LEFT, padx=5)
        tk.Button(btn_row, text="💾 Sauvegarder les chemins",
                  command=self.save_paths,
                  bg="#006400", fg="white", font=("Consolas", 9)).pack(side=tk.LEFT, padx=5)

        # ── Script + icône ─────────────────────────────────
        file_frame = tk.Frame(root, bg="#1e1e1e")
        file_frame.pack(pady=5)

        tk.Label(file_frame, text="Script Python :", fg="#00ff00", bg="#1e1e1e",
                 font=("Consolas", 10)).pack(anchor=tk.W)
        self.script_var = tk.StringVar()
        tk.Entry(file_frame, textvariable=self.script_var, width=72,
                 font=("Consolas", 10), bg="#2d2d2d", fg="white",
                 insertbackground="white").pack(pady=2)
        tk.Button(file_frame, text="📂 Choisir .py", command=self.select_script,
                  bg="#2d2d2d", fg="white", font=("Consolas", 10)).pack(pady=2)

        tk.Label(file_frame, text="Icône (optionnel) :", fg="#00ff00", bg="#1e1e1e",
                 font=("Consolas", 10)).pack(anchor=tk.W)
        self.icon_var = tk.StringVar()
        tk.Entry(file_frame, textvariable=self.icon_var, width=72,
                 font=("Consolas", 10), bg="#2d2d2d", fg="white",
                 insertbackground="white").pack(pady=2)
        tk.Button(file_frame, text="📂 Choisir .ico", command=self.select_icon,
                  bg="#2d2d2d", fg="white", font=("Consolas", 10)).pack(pady=2)

        # ── Options ────────────────────────────────────────
        opt_frame = tk.Frame(root, bg="#1e1e1e")
        opt_frame.pack(pady=8)
        self.build_32_var   = tk.BooleanVar(value=True)
        self.build_64_var   = tk.BooleanVar(value=True)
        self.no_console_var = tk.BooleanVar(value=True)
        self.clean_build_var = tk.BooleanVar(value=True)

        for text, var in [
            ("📦 Compiler en 32 bits (Windows 7/10 32)",  self.build_32_var),
            ("📦 Compiler en 64 bits (Windows 10/11 64)", self.build_64_var),
            ("🖥️ Désactiver la console (--windows-console-mode=disable)", self.no_console_var),
            ("🗑️ Nettoyer après compilation (garder uniquement .exe)", self.clean_build_var),
        ]:
            tk.Checkbutton(opt_frame, text=text, variable=var,
                           bg="#1e1e1e", fg="#00ff00",
                           selectcolor="#333", font=("Consolas", 9)).pack(anchor=tk.W)

        # ── Barre de progression ────────────────────────────
        prog_frame = tk.Frame(root, bg="#1e1e1e")
        prog_frame.pack(pady=6, padx=20, fill=tk.X)
        self.progress_label = tk.Label(prog_frame, text="En attente...",
                                       fg="#00ff00", bg="#1e1e1e", font=("Consolas", 10))
        self.progress_label.pack()
        self.progress_bar = ttk.Progressbar(prog_frame, orient="horizontal",
                                             length=860, mode="determinate")
        self.progress_bar.pack(pady=4)

        # ── Boutons compile ────────────────────────────────
        btn_frame = tk.Frame(root, bg="#1e1e1e")
        btn_frame.pack(pady=8)
        self.btn_compile = tk.Button(btn_frame, text="🚀 Compiler 32/64 bits",
                                     command=self.compile_both,
                                     bg="#8b0000", fg="white", font=("Consolas", 12))
        self.btn_compile.pack(side=tk.LEFT, padx=5)
        self.btn_open_build = tk.Button(btn_frame, text="📂 Ouvrir build/",
                                        command=self.open_build_dir,
                                        bg="#006400", fg="white",
                                        font=("Consolas", 10), state="disabled")
        self.btn_open_build.pack(side=tk.LEFT, padx=5)

        # ── Console ────────────────────────────────────────
        self.console = scrolledtext.ScrolledText(
            root, wrap=tk.WORD, font=("Consolas", 10),
            bg="#0a0a0a", fg="#00ff00", height=12, state="normal",
            insertbackground="#00ff00",
            selectbackground="#003300", selectforeground="#00ff00"
        )
        self.console.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)
        self.console.bind("<Key>", lambda e: "break")
        # Force fond noir sur Windows (évite le fond bleu système)
        self.console.configure(bg="#0a0a0a", fg="#00ff00")

        sys.stdout = self

        # Chargement des chemins prédéfinis connus
        self._apply_known_paths()

    # ── Chemins prédéfinis Kerberos ────────────────────────
    def _apply_known_paths(self):
        """
        Pré-remplit les chemins depuis la config sauvegardée.
        Si la config est vide, suggère les chemins connus du projet.
        """
        known = {
            "python_32": r"H:\python.32",
            "python_64": r"H:\python.64",
            "mingw32":   r"F:\compiller_nuitka\mingw32\bin",
            "mingw64":   r"F:\compiller_nuitka\mingw64\bin",
        }
        for key, default_path in known.items():
            var = {
                "python_32": self.py32_var,
                "python_64": self.py64_var,
                "mingw32":   self.mingw32_var,
                "mingw64":   self.mingw64_var,
            }[key]
            # Seulement si le champ est vide
            if not var.get():
                var.set(default_path)

    # ── Détection automatique ──────────────────────────────
    def _auto_detect(self):
        """Cherche automatiquement python.exe dans les dossiers configurés."""
        self._log("🔍 Détection automatique en cours...\n")
        threading.Thread(target=self._auto_detect_thread, daemon=True).start()

    def _auto_detect_thread(self):
        for bits, folder_var, status_var, config_key in [
            (32, self.py32_var, self.status_py32, "python_32"),
            (64, self.py64_var, self.status_py64, "python_64"),
        ]:
            folder = folder_var.get().strip()
            self._log(f"  → Recherche Python {bits} bits dans : {folder}\n")

            # Si le champ pointe déjà vers un .exe valide
            if os.path.isfile(folder) and folder.endswith(".exe"):
                detected_bits = _get_python_bits(folder)
                version       = _get_python_version(folder)
                has_nuitka    = _check_nuitka(folder)
                nuitka_str    = "✅ nuitka OK" if has_nuitka else "⚠️ nuitka absent"
                info = f"✅ {bits}bit | Python {version} | {nuitka_str}"
                status_var.set(info)
                self._log(f"  ✅ Python {bits} bits : {folder} ({version}) {nuitka_str}\n")
                self.config[config_key] = folder
                continue

            # Cherche dans le dossier
            exe = find_python_exe(folder, bits)
            if exe:
                version    = _get_python_version(exe)
                has_nuitka = _check_nuitka(exe)
                nuitka_str = "✅ nuitka" if has_nuitka else "⚠️ sans nuitka"
                info = f"✅ {exe} | v{version} | {nuitka_str}"
                status_var.set(info)
                folder_var.set(exe)  # Met à jour le champ avec le .exe trouvé
                self.config[config_key] = exe
                self._log(f"  ✅ Trouvé : {exe} | Python {version} | {nuitka_str}\n")
                if not has_nuitka:
                    self._log(f"  ⚠️  Nuitka absent pour Python {bits} bits.\n")
                    self._log(f"       Installe-le : {exe} -m pip install nuitka\n")
            else:
                status_var.set(f"❌ python.exe {bits}bit non trouvé")
                self._log(f"  ❌ Aucun python.exe {bits} bits trouvé dans : {folder}\n")

        self._log("🔍 Détection terminée.\n")

    # ── Sélection fichiers ─────────────────────────────────
    def _select_py32_folder(self):
        path = filedialog.askdirectory(title="Dossier Python 32 bits")
        if path:
            self.py32_var.set(path)

    def _select_py32_exe(self):
        path = filedialog.askopenfilename(title="python.exe 32 bits", filetypes=[("Exe", "*.exe")])
        if path:
            self.py32_var.set(path)

    def _select_py64_folder(self):
        path = filedialog.askdirectory(title="Dossier Python 64 bits")
        if path:
            self.py64_var.set(path)

    def _select_py64_exe(self):
        path = filedialog.askopenfilename(title="python.exe 64 bits", filetypes=[("Exe", "*.exe")])
        if path:
            self.py64_var.set(path)

    def _select_mingw32(self):
        path = filedialog.askdirectory(title="Dossier bin/ MinGW 32 bits")
        if path:
            self.mingw32_var.set(path)

    def _select_mingw64(self):
        path = filedialog.askdirectory(title="Dossier bin/ MinGW 64 bits")
        if path:
            self.mingw64_var.set(path)

    def save_paths(self):
        cfg = {
            "python_32": self.py32_var.get(),
            "python_64": self.py64_var.get(),
            "mingw32":   self.mingw32_var.get(),
            "mingw64":   self.mingw64_var.get(),
        }
        save_config(cfg)
        self.config = cfg
        messagebox.showinfo("✅ OK", "Chemins sauvegardés dans config/compiler.json")

    # ── Logging console ────────────────────────────────────
    def _log(self, msg: str):
        self.console.insert(tk.END, msg)
        self.console.see(tk.END)
        self.root.update_idletasks()

    def write(self, msg):
        if msg.strip():
            self._log(msg)

    def flush(self): pass

    # ── Fichiers script/icône ──────────────────────────────
    def select_script(self):
        path = filedialog.askopenfilename(title="Sélectionner un script Python",
                                          filetypes=[("Python", "*.py")])
        if path:
            self.script_var.set(path)

    def select_icon(self):
        path = filedialog.askopenfilename(title="Sélectionner une icône",
                                          filetypes=[("Icon", "*.ico")])
        if path:
            self.icon_var.set(path)

    def open_build_dir(self):
        if os.path.exists(BUILD_DIR):
            os.startfile(BUILD_DIR)
        else:
            messagebox.showwarning("⚠️", f"Dossier introuvable :\n{BUILD_DIR}")

    # ── Compilation ────────────────────────────────────────
    def compile_single(self, python_exe: str, mingw_path: str, arch: str) -> bool:
        script     = self.script_var.get()
        custom_ico = self.icon_var.get().strip()

        # Validations
        if not script or not script.endswith(".py"):
            self._log("❌ Script invalide.\n"); return False
        if not os.path.exists(script):
            self._log(f"❌ Script introuvable : {script}\n"); return False

        # Résolution automatique du python.exe si c'est un dossier
        if python_exe and os.path.isdir(python_exe):
            bits = 32 if arch == "32" else 64
            detected = find_python_exe(python_exe, bits)
            if detected:
                self._log(f"🔍 python.exe {arch}bit détecté : {detected}\n")
                python_exe = detected
            else:
                self._log(f"❌ Impossible de trouver python.exe {arch}bit dans : {python_exe}\n")
                return False

        if not python_exe or not os.path.isfile(python_exe):
            self._log(f"❌ Python {arch} bits introuvable : {python_exe}\n"); return False
        if not mingw_path or not os.path.isdir(mingw_path):
            self._log(f"❌ MinGW {arch} bits introuvable : {mingw_path}\n"); return False

        log_path = os.path.join(BUILD_DIR, f"compilation_{arch}.log")

        cmd = [
            python_exe, "-m", "nuitka",
            "--standalone",
            "--mingw64",
            "--assume-yes-for-downloads",
            f"--output-dir={BUILD_DIR}"
        ]
        if self.no_console_var.get():
            cmd.append("--windows-console-mode=disable")
        if custom_ico and os.path.exists(custom_ico):
            cmd.append(f"--windows-icon-from-ico={custom_ico}")
        cmd.append(script)

        env          = os.environ.copy()
        env["PATH"]  = mingw_path + os.pathsep + env.get("PATH", "")
        env["NO_COLOR"] = "1"

        self._log(f"\n📦 Compilation {arch} bits...\n")
        self._log(f"   Python : {python_exe}\n")
        self._log(f"   MinGW  : {mingw_path}\n")
        self._log(f"   Script : {script}\n\n")

        try:
            with open(log_path, "w", encoding="utf-8") as log_file:
                log_file.write(f"=== LOG KERBEROS NUITKA {arch}bit ===\n")
                log_file.write(f"Date    : {time.strftime('%Y-%m-%d %H:%M:%S')}\n")
                log_file.write(f"Python  : {python_exe}\n")
                log_file.write(f"Commande: {' '.join(cmd)}\n")
                log_file.write("-" * 60 + "\n\n")

                # encoding="utf-8" + errors="replace" évite les  sur Windows
                process = subprocess.Popen(
                    cmd, env=env, cwd=SCRIPT_DIR,
                    stdout=subprocess.PIPE, stderr=subprocess.STDOUT,
                    text=True, encoding="utf-8", errors="replace",
                    creationflags=subprocess.CREATE_NO_WINDOW if hasattr(subprocess, "CREATE_NO_WINDOW") else 0
                )
                for line in process.stdout:
                    log_file.write(line)
                    log_file.flush()
                    self._log(line)

                rc = process.wait()
                if rc == 0:
                    self._log(f"✅ Compilation {arch} bits réussie !\n")
                    if self.clean_build_var.get():
                        self.cleanup_dist(script, arch)
                    return True
                else:
                    self._log(f"❌ Échec {arch} bits (code {rc}) — voir build/compilation_{arch}.log\n")
                    return False

        except Exception as e:
            self._log(f"💥 Erreur {arch} bits : {e}\n")
            return False

    def cleanup_dist(self, script: str, arch: str):
        exe_name  = os.path.splitext(os.path.basename(script))[0] + ".exe"
        dist_dir  = os.path.join(BUILD_DIR, exe_name.replace(".exe", ".dist"))
        if not os.path.exists(dist_dir):
            # Cherche aussi le dossier .dist avec nom nettoyé (Nuitka remplace + par _)
            base_clean = os.path.splitext(os.path.basename(script))[0]
            base_clean = base_clean.replace("+", "_").replace(" ", "_")
            dist_dir   = os.path.join(BUILD_DIR, base_clean + ".dist")
        if not os.path.exists(dist_dir):
            self._log(f"⚠️ Dossier .dist introuvable pour nettoyage {arch}.\n")
            return
        try:
            for item in os.listdir(dist_dir):
                p = os.path.join(dist_dir, item)
                try:
                    if os.path.isdir(p):
                        shutil.rmtree(p)
                    elif item != exe_name:
                        os.unlink(p)
                except OSError as e:
                    self._log(f"  ⚠️ Impossible de supprimer {item} : {e}\n")
            self._log(f"🧹 Nettoyage {arch} bits terminé.\n")
        except Exception as e:
            self._log(f"⚠️ Nettoyage partiel : {e}\n")

    def compile_both(self):
        script = self.script_var.get()
        if not script or not script.endswith(".py"):
            messagebox.showerror("Erreur", "Choisissez un fichier .py valide."); return

        if self.build_32_var.get() and not self.py32_var.get():
            messagebox.showerror("Erreur", "Chemin Python 32 bits non configuré."); return
        if self.build_64_var.get() and not self.py64_var.get():
            messagebox.showerror("Erreur", "Chemin Python 64 bits non configuré."); return

        self.btn_compile.config(state="disabled")
        self.progress_bar["value"] = 0
        self.progress_label.config(text="⏳ Compilation en cours...")
        threading.Thread(target=self._compile_thread, daemon=True).start()

    def _compile_thread(self):
        total   = (1 if self.build_32_var.get() else 0) + (1 if self.build_64_var.get() else 0)
        done    = 0
        success = False

        if self.build_32_var.get():
            ok = self.compile_single(
                self.py32_var.get().strip(),
                self.mingw32_var.get().strip(), "32")
            if ok:
                success = True
            done += 1
            self.progress_bar["value"] = (done / total) * 100

        if self.build_64_var.get():
            ok = self.compile_single(
                self.py64_var.get().strip(),
                self.mingw64_var.get().strip(), "64")
            if ok:
                success = True
            done += 1
            self.progress_bar["value"] = (done / total) * 100

        self.btn_compile.config(state="normal")
        if success:
            self.progress_label.config(text="✅ Compilation terminée")
            self.btn_open_build.config(state="normal")
        else:
            self.progress_label.config(text="❌ Échec — voir console et logs build/")

# ============================================================
# MAIN
# ============================================================

if __name__ == "__main__":
    root = tk.Tk()
    app  = NuitkaCrossBuilder(root)
    root.mainloop()
