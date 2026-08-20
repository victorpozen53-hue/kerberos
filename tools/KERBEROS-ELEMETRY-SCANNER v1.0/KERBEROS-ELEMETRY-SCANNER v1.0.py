#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
KERBEROS TELEMETRY SCANNER v1.1
--------------------------------------------------
White hat only • Local only • Zéro cloud
GPLv3 — https://liberapay.com/EthicalKerberos/
Code : https://github.com/victorpozen/kerberos
Rapport : H:\\kerb-scan-report.txt
"""

import os
import sys
import zipfile
import re
import tkinter as tk
from tkinter import scrolledtext, filedialog, messagebox
import hashlib
from datetime import datetime

DEBUG = 0

def log_debug(msg):
    if DEBUG:
        with open(r"H:\kerb-scan-debug.log", "a", encoding="utf-8") as f:
            f.write(f"[{datetime.now().strftime('%H:%M:%S')}] {msg}\n")

TELEMETRY_PATTERNS = [
    (r"\brequests\.", "réseau: requests"),
    (r"\bhttp[s]?://", "URL hardcodée"),
    (r"\bsocket\.create_connection", "socket réseau"),
    (r"\bsubprocess.*curl|wget|netsh|powershell.*http", "cmd réseau"),
    (r"\bos\.system.*http", "os.system + HTTP"),
    (r"\btelemetry|analytics|metrics|tracking", "mot-clé traçage"),
    (r"\blogger\.info.*token|key|id|uuid|user|host", "fuite info"),
    (r"\bgetpass\.getuser\(\)|platform\.node\(\)|socket\.gethostname\(\)", "identité machine"),
    (r"\bupdate\.check|autoupdate|phoning\.home", "auto-contact"),
    (r"https?://[a-zA-Z0-9\.\-_/]{10,}", "URL longue"),
    (r"\beval\(|exec\(|pickle\.loads\(", "exécution dynamique"),
]

class KerberosScannerGUI:
    def __init__(self, root):
        self.root = root
        self.root.title("🛡️ Kerberos — Telemetry Scanner (GPLv3)")
        self.root.geometry("940x580")
        self.root.configure(bg="#0d0d0d")
        self.results = {}  # {path: {'risky': [...], 'safe': True/False}}

        header = tk.Label(
            root, text="KERBEROS — Analyse anti-telemetry (local / offline)",
            bg="#1a1a1a", fg="#00cc44", font=("Consolas", 12, "bold"),
            anchor="w", padx=14, pady=6
        )
        header.pack(fill="x")

        btn_frame = tk.Frame(root, bg="#0d0d0d")
        btn_frame.pack(pady=8)
        tk.Button(btn_frame, text="📂 Ouvrir .whl", command=self.open_whl,
                  bg="#252525", fg="#88ffaa", font=("Consolas", 10), relief="flat",
                  padx=14, pady=5).pack(side="left", padx=4)
        tk.Button(btn_frame, text="🔍 Tout scanner", command=self.scan_all,
                  bg="#252525", fg="#88ccff", font=("Consolas", 10), relief="flat",
                  padx=14, pady=5).pack(side="left", padx=4)
        tk.Button(btn_frame, text="📄 Sauver rapport", command=self.save_report,
                  bg="#252525", fg="#ffdd88", font=("Consolas", 10), relief="flat",
                  padx=14, pady=5).pack(side="left", padx=4)
        tk.Button(btn_frame, text="📜 GPLv3", command=self.show_license,
                  bg="#252525", fg="#ffaa66", font=("Consolas", 10), relief="flat",
                  padx=14, pady=5).pack(side="left", padx=4)

        self.output = scrolledtext.ScrolledText(
            root, bg="#0a0a0a", fg="#00ff88", insertbackground="#00ff88",
            font=("Consolas", 9), relief="flat", padx=10, pady=8
        )
        self.output.pack(fill="both", expand=True, padx=14, pady=(0,14))
        self.output.insert("1.0", (
            "KERBEROS — Telemetry Scanner v1.1\n"
            "--------------------------------------------------\n"
            "White hat only • Local only • Zéro cloud\n"
            "GPLv3 — https://liberapay.com/EthicalKerberos/\n"
            "Code : https://github.com/victorpozen/kerberos\n\n"
            "➡️ Clique [Tout scanner] pour analyser H:\\tmp-deps\\*.whl\n"
        ))

    def open_whl(self):
        files = filedialog.askopenfilenames(
            title="Sélectionner des .whl",
            filetypes=[("Wheel files", "*.whl")],
            initialdir=r"H:\tmp-deps"
        )
        for f in files:
            self.scan_file(f)

    def scan_all(self):
        self.output.insert("end", "\n" + "="*60 + "\n")
        self.output.insert("end", "ᐅ Démarrage de l'analyse complète...\n")
        target = r"H:\tmp-deps"
        if not os.path.exists(target):
            target = os.getcwd()
        count = 0
        for f in os.listdir(target):
            if f.endswith('.whl'):
                self.scan_file(os.path.join(target, f))
                count += 1
        if count == 0:
            self.output.insert("end", "⚠️  Aucun .whl trouvé dans H:\\tmp-deps\n")
        else:
            self.output.insert("end", f"\n✅ Analyse terminée — {count} fichier(s) traité(s).\n")
            self.output.insert("end", "Utilise [📄 Sauver rapport] pour archiver.\n")
        self.output.see("end")

    def scan_file(self, path):
        name = os.path.basename(path)
        self.output.insert("end", f"\n🔍 {name}\n")
        self.root.update()

        risky = []
        try:
            with zipfile.ZipFile(path, 'r') as z:
                for arcname in z.namelist():
                    if arcname.endswith('.py'):
                        try:
                            data = z.read(arcname).decode('utf-8', errors='ignore')
                            for pattern, label in TELEMETRY_PATTERNS:
                                if re.search(pattern, data, re.IGNORECASE):
                                    risky.append((arcname, label))
                        except Exception as e:
                            log_debug(f"decode fail {arcname}: {e}")
        except Exception as e:
            self.output.insert("end", f"   ❌ Erreur : {e}\n")
            self.results[path] = {'risky': [], 'error': str(e), 'safe': False}
            return

        safe = len(risky) == 0
        self.results[path] = {'risky': risky, 'safe': safe}

        if risky:
            self.output.insert("end", "   ❗ Risques détectés :\n")
            for arcname, label in risky[:6]:
                self.output.insert("end", f"     • {arcname} → {label}\n")
            if len(risky) > 6:
                self.output.insert("end", f"     ... +{len(risky)-6} occurrences\n")
        else:
            self.output.insert("end", "   ✅ Aucun traceur détecté (analyse statique)\n")

        self.output.see("end")

    def save_report(self):
        if not self.results:
            messagebox.showinfo("ℹ️", "Aucun scan effectué.")
            return

        report_path = r"H:\kerb-scan-report.txt"
        now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        try:
            with open(report_path, "w", encoding="utf-8") as f:
                f.write("="*60 + "\n")
                f.write("RAPPORT KERBEROS — ANALYSE ANTI-TELEMETRY\n")
                f.write(f"Date : {now}\n")
                f.write("Système : Windows 10 (19045.6456)\n")
                f.write("Licence : GNU GPLv3\n")
                f.write("Projet : https://github.com/victorpozen/kerberos\n")
                f.write("Soutien : https://liberapay.com/EthicalKerberos/\n")
                f.write("="*60 + "\n\n")

                for path, data in self.results.items():
                    name = os.path.basename(path)
                    f.write(f"📦 {name}\n")
                    # SHA256
                    try:
                        with open(path, "rb") as whl:
                            sha256 = hashlib.sha256(whl.read()).hexdigest()[:16]
                        f.write(f"   SHA256: {sha256}...\n")
                    except:
                        f.write("   SHA256: [échec calcul]\n")

                    if 'error' in data:
                        f.write(f"   ❌ Erreur : {data['error']}\n")
                    elif data['safe']:
                        f.write("   ✅ Statut : SÉCURISÉ (aucun traceur détecté)\n")
                    else:
                        f.write("   ⚠️  Statut : RISQUE DÉTECTÉ\n")
                        for arcname, label in data['risky'][:10]:
                            f.write(f"      → {arcname} : {label}\n")
                        if len(data['risky']) > 10:
                            f.write(f"      ... +{len(data['risky'])-10} occurrences\n")
                    f.write("\n")

                f.write("--------------------------------------------------\n")
                f.write("White hat only. Zéro cloud. Pas de trace.\n")
                f.write("« Juste du code qui protège. » (-; — Victor.Pozen\n")

            self.output.insert("end", f"\n📄 Rapport sauvegardé :\n   {report_path}\n")
            messagebox.showinfo("✅ Succès", f"Rapport archivé dans :\n{report_path}")
        except Exception as e:
            messagebox.showerror("❌ Échec", f"Impossible d'écrire le rapport :\n{e}")

    def show_license(self):
        license_text = """                    GNU GENERAL PUBLIC LICENSE
                       Version 3, 29 June 2007

 Copyright (C) 2007 Free Software Foundation, Inc. <https://fsf.org/>
 Everyone is permitted to copy and distribute verbatim copies
 of this license document, but changing it is not allowed.

KERBEROS — Sécurité éthique locale
Copyright (C) 2025 Victor Pozen

This program is free software: you can redistribute it and/or modify
it under the terms of the GNU General Public License as published by
the Free Software Foundation, either version 3 of the License, or
(at your option) any later version.

This program is distributed in the hope that it will be useful,
but WITHOUT ANY WARRANTY; without even the implied warranty of
MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
GNU General Public License for more details.

You should have received a copy of the GNU General Public License
along with this program.  If not, see <https://www.gnu.org/licenses/>.
"""
        win = tk.Toplevel(self.root)
        win.title("📜 GPLv3 — Kerberos")
        win.geometry("780x520")
        win.configure(bg="#0d0d0d")
        txt = scrolledtext.ScrolledText(win, bg="#0a0a0a", fg="#88ccff", font=("Consolas", 9))
        txt.pack(fill="both", expand=True, padx=8, pady=8)
        txt.insert("1.0", license_text)
        txt.configure(state="disabled")

if __name__ == "__main__":
    root = tk.Tk()
    app = KerberosScannerGUI(root)
    root.mainloop()