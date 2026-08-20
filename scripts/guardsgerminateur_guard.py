#!/usr/bin/env python3
# -*- coding: utf-8 -*-
# Copyright (C) 2025 Victor Pozen
# Ce programme est sous licence GPLv3 – voir LICENSE à la racine du projet.
# Projet Kerberos : système de défense numérique éthique, local, open source.

"""
Germinateur Guard – Interface Tkinter
• IPs publiques en masse
• Attaques variées (y compris rares)
• Debug maison intégré
• Sortie : logs.full.option/logs.simulation/
"""

import os
import sys
import random
import threading
import time
from datetime import datetime, timedelta
import tkinter as tk
from tkinter import ttk, scrolledtext, messagebox

# -------------------------
# Chemins
# -------------------------
BASE_DIR = r"I:\IA.KERBEROS"
LOGS_OUTPUT_DIR = os.path.join(BASE_DIR, "logs.full.option", "logs.simulation")
DEBUG_LOG_FILE = os.path.join(BASE_DIR, "logs", "germinateur_debug.log")

os.makedirs(LOGS_OUTPUT_DIR, exist_ok=True)
os.makedirs(os.path.dirname(DEBUG_LOG_FILE), exist_ok=True)

# -------------------------
# Debug maison (UI + fichier)
# -------------------------
def debug_log(msg, level="INFO", ui_callback=None):
    timestamp = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
    full_msg = f"[{timestamp}] [{level}] {msg}"
    print(full_msg)
    try:
        with open(DEBUG_LOG_FILE, "a", encoding="utf-8") as f:
            f.write(full_msg + "\n")
    except Exception:
        pass
    if ui_callback:
        ui_callback(full_msg)

# -------------------------
# Générateur d'IP publique
# -------------------------
def generate_public_ip():
    while True:
        a = random.randint(1, 223)
        if a in (10, 127):
            continue
        b = random.randint(0, 255)
        if a == 192 and b == 168:
            continue
        if a == 172 and 16 <= b <= 31:
            continue
        c = random.randint(0, 255)
        d = random.randint(1, 254)
        ip = f"{a}.{b}.{c}.{d}"
        if ip.startswith(("0.", "255.", "169.254.", "224.", "239.", "240.")):
            continue
        return ip

# -------------------------
# Attaques
# -------------------------
ATTACKS = [
    "SSH brute-force (user: root)",
    "Scan Nmap ports 22,80,443",
    "Tentative RDP (Hydra)",
    "GET /wp-login.php",
    "SQLi: ' OR '1'='1",
    "XSS: <script>alert(1)</script>",
    "wpscan WordPress",
    "EternalBlue simulé",
    "CVE-2023-1234 (Apache)",
    "UPnP exploitation",
    "Accès /phpmyadmin",
    "Téléchargement /backup.zip",
    "Scan SNMP (community: public)",
    "Attaque Mirai (Telnet IoT)",
    "Requête CoAP malveillante",
    "Zero-day simulé : KerberosAuthBypass",
    "Injection LDAP",
    "Cache poisoning DNS",
    "HTTP/2 headers malveillants",
    "Scan caméras IP (Hikvision)",
    "Accès /debug.php",
    "Fragmentation IPv6 théorique",
    "GraphQL introspection"
]

# -------------------------
# Génération massive (threadé)
# -------------------------
def generate_salve(count, ui_callback=None):
    debug_log(f"Démarrage de la salve : {count:,} logs", "INFO", ui_callback)
    
    timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
    output_file = os.path.join(LOGS_OUTPUT_DIR, f"guard_salve_{count}_{timestamp}.log")

    try:
        with open(output_file, "w", encoding="utf-8") as f:
            f.write(f"# Germinateur Guard – Salve autonome\n")
            f.write(f"# {count:,} logs générés le {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
            f.write("# IPs publiques uniques – attaques variées\n")
            f.write("# Projet Kerberos – Sécurité éthique locale pour vieux PCs (Win 7/10)\n\n")

            base_time = datetime.now() - timedelta(hours=24)
            for i in range(count):
                ip = generate_public_ip()
                attack = random.choice(ATTACKS)
                ts = (base_time + timedelta(seconds=random.randint(0, 86400))).strftime('%Y-%m-%d %H:%M:%S')
                f.write(f"[{ts}] {ip} → {attack}\n")

                if (i + 1) % 50000 == 0 and ui_callback:
                    debug_log(f"  → {i + 1:,}/{count:,} logs", "DEBUG", ui_callback)

        debug_log(f"✅ Salve terminée : {output_file}", "SUCCÈS", ui_callback)
        return output_file

    except Exception as e:
        debug_log(f"❌ Erreur critique : {e}", "ERREUR", ui_callback)
        return None

# ✅ Fonction requise par Kerberos
def run(count=100000):
    """
    Exécuté quand on clique sur le module dans le panneau latéral.
    Par défaut : 100 000 logs.
    """
    try:
        # Exécute en arrière-plan sans bloquer Kerberos
        def background_task():
            output = generate_salve(count)
            if output:
                print(f"📄 Germinateur : {os.path.basename(output)}")
            else:
                print("❌ Échec de la génération.")
        
        thread = threading.Thread(target=background_task, daemon=True)
        thread.start()
        return f"🌱 Génération de {count:,} logs lancée en arrière-plan."
    except Exception as e:
        return f"❌ Erreur Germinateur : {str(e)}"

# -------------------------
# Interface graphique – style Kerberos
# -------------------------
class GerminateurGuardUI:
    def __init__(self):
        self.root = tk.Tk()
        self.root.title("🌱 Germinateur Guard – Kerberos")
        self.root.geometry("900x600")
        self.root.configure(bg='#1e1e1e')

        style = ttk.Style()
        try:
            style.theme_use('clam')
        except:
            pass
        style.configure('TFrame', background='#1e1e1e')
        style.configure('TButton', background='#2d2d2d', foreground='white')
        style.configure('TLabel', background='#1e1e1e', foreground='white')

        # Contrôles
        ctrl = ttk.Frame(self.root)
        ctrl.pack(fill=tk.X, padx=10, pady=10)

        ttk.Label(ctrl, text="Nombre de logs (1k–1M) :").pack(side=tk.LEFT)
        self.count_var = tk.StringVar(value="100000")
        ttk.Entry(ctrl, textvariable=self.count_var, width=10).pack(side=tk.LEFT, padx=5)

        ttk.Button(ctrl, text="✅ Générer", command=self.start_generation).pack(side=tk.LEFT, padx=5)
        ttk.Button(ctrl, text="📂 Ouvrir logs.simulation", command=self.open_logs).pack(side=tk.LEFT, padx=5)
        ttk.Button(ctrl, text="📄 Voir debug.log", command=self.open_debug).pack(side=tk.LEFT, padx=5)
        ttk.Button(ctrl, text="❌ Quitter", command=self.root.destroy).pack(side=tk.RIGHT)

        # Zone de log (debug maison)
        self.log_area = scrolledtext.ScrolledText(
            self.root, wrap=tk.WORD, font=('Consolas', 10),
            bg='#2d2d2d', fg='#ffffff', insertbackground='white'
        )
        self.log_area.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)
        self.log_area.insert(tk.END, "Germinateur Guard prêt.\n")

        self.root.mainloop()

    def log_msg(self, msg):
        self.log_area.insert(tk.END, msg + "\n")
        self.log_area.see(tk.END)
        self.root.update_idletasks()

    def get_count(self):
        try:
            c = int(self.count_var.get().replace(',', ''))
            if 1000 <= c <= 1_000_000:
                return c
        except:
            pass
        messagebox.showerror("Erreur", "Entrez un nombre entre 1 000 et 1 000 000.")
        return None

    def start_generation(self):
        count = self.get_count()
        if count is None:
            return
        self.log_msg("\n" + "="*50)
        threading.Thread(target=generate_salve, args=(count, self.log_msg), daemon=True).start()

    def open_logs(self):
        if os.path.exists(LOGS_OUTPUT_DIR):
            os.startfile(LOGS_OUTPUT_DIR)
        else:
            messagebox.showwarning("⚠️", "Dossier introuvable.")

    def open_debug(self):
        if os.path.exists(DEBUG_LOG_FILE):
            os.startfile(DEBUG_LOG_FILE)
        else:
            messagebox.showwarning("⚠️", "Fichier de debug introuvable.")

# Permet de lancer l'UI séparément
if __name__ == "__main__":
    if len(sys.argv) > 1:
        try:
            count = int(sys.argv[1])
            debug_log("Mode CLI activé", "INFO")
            generate_salve(count, lambda msg: print(msg))
        except Exception as e:
            debug_log(f"Erreur CLI : {e}", "ERREUR")
    else:
        GerminateurGuardUI()