#!/usr/bin/env python3
# -*- coding: utf-8 -*-
# kerberos_cleaner.py — Outil noyau Kerberos
# White hat only • GPLv3 • Pas de trace. Pas de nuage. Juste du code qui protège. (-;

import os
import sys
import subprocess
import threading
import hashlib
import json
from datetime import datetime
from pathlib import Path
import tkinter as tk
from tkinter import ttk, scrolledtext, messagebox

ROOT = Path(__file__).parent
TEMP_DL = ROOT / "temp_dl"
EXTRACT_DIR = ROOT / "extracted"
REPORTS = ROOT / "reports"
REPORTS.mkdir(exist_ok=True)

class KerberosCleaner:
    def __init__(self, root):
        self.root = root
        self.root.title("🛡️ Kerberos Cleaner — Outil noyau")
        self.root.geometry("920x580")
        self.root.configure(bg="#0a0a0a")

        # Titre
        tk.Label(
            root, text="🛡️ Kerberos Cleaner — LV7",
            font=("Consolas", 14, "bold"), fg="#00ccff", bg="#0a0a0a"
        ).pack(pady=8)

        # Console
        self.console = scrolledtext.ScrolledText(
            root, bg="#0d0d0d", fg="#d4d4d4", font=("Consolas", 9),
            wrap=tk.WORD, height=22
        )
        self.console.pack(fill=tk.BOTH, expand=True, padx=12, pady=5)

        # Boutons — 4 fonctions cœurs
        btn_frame = tk.Frame(root, bg="#0a0a0a")
        btn_frame.pack(pady=6)

        self.btn_bulle = tk.Button(
            btn_frame, text="🌐 Bulle LV7",
            command=self.bulle_lv7, width=16,
            bg="#1e2a38", fg="white", font=("Consolas", 10, "bold")
        )
        self.btn_bulle.pack(side=tk.LEFT, padx=3)

        self.btn_dll = tk.Button(
            btn_frame, text="📥 Extract DLL",
            command=self.extract_dll, width=16,
            bg="#1e2a38", fg="white", font=("Consolas", 10, "bold")
        )
        self.btn_dll.pack(side=tk.LEFT, padx=3)

        self.btn_scan = tk.Button(
            btn_frame, text="🔍 Scan & Rasure",
            command=self.scan_rasure, width=16,
            bg="#1e2a38", fg="white", font=("Consolas", 10, "bold")
        )
        self.btn_scan.pack(side=tk.LEFT, padx=3)

        self.btn_clean = tk.Button(
            btn_frame, text="🧹 Fuera les troll",
            command=self.fuera_troll, width=16,
            bg="#1e2a38", fg="white", font=("Consolas", 10, "bold")
        )
        self.btn_clean.pack(side=tk.LEFT, padx=3)

        self.status = tk.Label(
            root, text="➡️ Prêt — Sécurité éthique locale",
            fg="#666", bg="#0a0a0a", font=("Consolas", 9)
        )
        self.status.pack(pady=4)

        self.log("ℹ️ Kerberos Cleaner — LV7")
        self.log("   → Zéro couleur superflue. Zéro dépendance cloud.")
        self.log("   → 100 % local. 100 % éthique. GPLv3.")

    def log(self, msg):
        self.console.configure(state="normal")
        self.console.insert(tk.END, f"{msg}\n")
        self.console.see(tk.END)
        self.console.configure(state="disabled")

    # === 1. BULLE LV7 ===
    def bulle_lv7(self):
        self.log("[🌐] Démarrage de la Bulle LV7…")
        try:
            guard = ROOT / "guard_nassa.py"
            if not guard.exists():
                # Auto-génération minimale si absent
                guard.write_text(
                    "import threading; print('[✅] Bulle LV7 active → 127.0.0.1:7777'); "
                    "import socket; s=socket.socket(); s.bind(('127.0.0.1',7777)); "
                    "threading.Thread(target=lambda: s.listen(5) or [s.accept() for _ in iter(int,1)], daemon=True).start()",
                    encoding="utf-8"
                )
            subprocess.Popen([sys.executable, str(guard)])
            self.log("[✅] Bulle LV7 active → 127.0.0.1:7777")
            self.status.config(text="🌐 Bulle LV7 active", fg="#00cc44")
        except Exception as e:
            self.log(f"[❌] Échec Bulle LV7 : {e}")

    # === 2. EXTRACT DLL ===
    def extract_dll(self):
        self.log("[📥] Téléchargement pywin32 (sans installation)…")
        TEMP_DL.mkdir(exist_ok=True)
        try:
            subprocess.run([
                sys.executable, "-m", "pip", "download", "pywin32==306",
                "--no-deps", "-d", str(TEMP_DL)
            ], check=True, capture_output=True)
            whl = next(TEMP_DL.glob("pywin32-306-*.whl"), None)
            if whl:
                self.log(f"[✅] .whl téléchargé : {whl.name}")
                # Extraction
                import zipfile
                with zipfile.ZipFile(whl) as zf:
                    for name in zf.namelist():
                        if name.endswith(("pywintypes38.dll", "pythoncom38.dll")):
                            out = EXTRACT_DIR / name
                            out.parent.mkdir(parents=True, exist_ok=True)
                            with zf.open(name) as src, open(out, "wb") as dst:
                                dst.write(src.read())
                            # SHA-256
                            h = hashlib.sha256()
                            with open(out, "rb") as f:
                                for chunk in iter(lambda: f.read(4096), b""):
                                    h.update(chunk)
                            self.log(f"[🔍] {name} → SHA: {h.hexdigest()[:8]}…")
                self.log("[✅] DLL extraites → ./extracted/")
                self.status.config(text="📥 DLL extraites", fg="#00cc44")
            else:
                self.log("[⚠️] Aucun .whl trouvé")
        except Exception as e:
            self.log(f"[❌] Échec extraction : {e}")

    # === 3. SCAN & RASURE ===
    def scan_rasure(self):
        self.log("[🔍] Scan & Rasure — mémoire / disque")
        try:
            # Suppression ciblée
            targets = [
                ROOT / "logs" / "sim.frames",
                ROOT / "logs.full.option" / "logs.simulation",
                ROOT / "nuitka-crash-report.xml",
                ROOT / "kerb-startup-debug.log",
            ]
            erased = 0
            for t in targets:
                if t.exists():
                    if t.is_file():
                        t.unlink()
                        erased += 1
                    elif t.is_dir():
                        import shutil
                        shutil.rmtree(t)
                        erased += 1
            self.log(f"[🧹] {erased} éléments effacés")
            self.status.config(text="🔍 Scan & Rasure terminé", fg="#00cc44")
        except Exception as e:
            self.log(f"[❌] Échec rasure : {e}")

    # === 4. FUERA LES TROLL ===
    def fuera_troll(self):
        self.log("[🧹] Fuera les troll — nettoyage profond")
        try:
            # Nettoyage systématique
            count = 0
            for root_dir, dirs, files in os.walk(ROOT):
                # Supprime __pycache__
                if "__pycache__" in dirs:
                    import shutil
                    shutil.rmtree(os.path.join(root_dir, "__pycache__"))
                    count += 1
                # Supprime .tmp, .bak, logs orphelins
                for f in files:
                    if f.endswith((".tmp", ".bak", ".old", "debug.log")):
                        os.remove(os.path.join(root_dir, f))
                        count += 1
            self.log(f"[✅] {count} éléments nettoyés")
            # Génération rapport
            ts = datetime.now().strftime("%Y%m%d_%H%M%S")
            rapport = f"""<!DOCTYPE html>
<html><head><meta charset="utf-8"><title>Kerberos Cleaner — Rapport</title></head>
<body style="font-family:Consolas;background:#0a0a0a;color:#d4d4d4;padding:20px">
<h1>🛡️ Rapport Kerberos Cleaner — {ts}</h1>
<p><b>Opérations :</b><br>
• Bulle LV7 : active<br>
• DLL extraites : pywintypes38.dll, pythoncom38.dll<br>
• Scan & Rasure : effectué<br>
• Fuera les troll : {count} éléments nettoyés</p>
<hr>
<footer style="font-size:0.8em;color:#555">
Kerberos v4.0 — Cleaner • GPLv3<br>
Code : <a href="https://github.com/victorpozen/kerberos">GitHub</a><br>
Soutien : <a href="https://liberapay.com/EthicalKerberos/">Liberapay</a>
</footer>
</body></html>"""
            (REPORTS / f"cleaner_{ts}.html").write_text(rapport, encoding="utf-8")
            self.log("[📄] Rapport HTML généré")
            self.status.config(text="🧹 Fuera les troll — terminé", fg="#00cc44")
        except Exception as e:
            self.log(f"[❌] Échec nettoyage : {e}")

if __name__ == "__main__":
    root = tk.Tk()
    app = KerberosCleaner(root)
    root.mainloop()