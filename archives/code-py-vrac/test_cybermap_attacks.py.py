#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
🎮 Test CyberMap Attacks — Simulateur d'attaques réseau
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
- Génère de fausses connexions depuis le monde entier
- Anime des lignes sur la carte (comme guard_cybermap.py)
- Teste la réactivité de l'UI Kerberos
- Usage : TEST UNIQUEMENT — ne modifie pas le système
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
Copyright (C) 2025 Victor Pozen — GPLv3
"""
# ============================================================================
#  KERBEROS ULTIMATE v4.2 — Test CyberMap Attacks
#  Copyright (C) 2025 Victor Pozen
# ============================================================================
#  LICENCE : GPLv3
#  AUTEUR  : Victor Pozen
#  VERSION : 4.2 Ultimate
#  DATE    : 2025
#  🔗 https://github.com/victorpozen
#  💰 https://liberapay.com/EthicalKerberos/
# ============================================================================

import tkinter as tk
from tkinter import ttk, scrolledtext
import threading
import time
import random
import json
from datetime import datetime
from pathlib import Path

# ============================================================================
# === DONNÉES GÉOGRAPHIQUES (fausses IP pour test) ==========================
# ============================================================================
ATTACK_SOURCES = [
    {"country": "Russie",        "city": "Moscou",      "lat": 55.7558, "lon": 37.6173, "threat": "critical"},
    {"country": "Chine",         "city": "Pékin",       "lat": 39.9042, "lon": 116.4074, "threat": "critical"},
    {"country": "Corée du Nord", "city": "Pyongyang",   "lat": 39.0392, "lon": 125.7625, "threat": "critical"},
    {"country": "Iran",          "city": "Téhéran",     "lat": 35.6892, "lon": 51.3890, "threat": "high"},
    {"country": "États-Unis",    "city": "New York",    "lat": 40.7128, "lon": -74.0060, "threat": "medium"},
    {"country": "États-Unis",    "city": "Los Angeles", "lat": 34.0522, "lon": -118.2437, "threat": "medium"},
    {"country": "Brésil",        "city": "São Paulo",   "lat": -23.5505, "lon": -46.6333, "threat": "medium"},
    {"country": "Allemagne",     "city": "Berlin",      "lat": 52.5200, "lon": 13.4050, "threat": "low"},
    {"country": "Royaume-Uni",   "city": "Londres",     "lat": 51.5074, "lon": -0.1278, "threat": "low"},
    {"country": "Inde",          "city": "Mumbai",      "lat": 19.0760, "lon": 72.8777, "threat": "medium"},
    {"country": "Nigeria",       "city": "Lagos",       "lat": 6.5244,  "lon": 3.3792,  "threat": "high"},
    {"country": "Ukraine",       "city": "Kiev",        "lat": 50.4501, "lon": 30.5234, "threat": "high"},
    {"country": "Pologne",       "city": "Varsovie",    "lat": 52.2297, "lon": 21.0122, "threat": "medium"},
    {"country": "Australie",     "city": "Sydney",      "lat": -33.8688, "lon": 151.2093, "threat": "low"},
    {"country": "Japon",         "city": "Tokyo",       "lat": 35.6762, "lon": 139.6503, "threat": "low"},
]

MALWARE_TYPES = [
    "Ransomware", "Trojan", "RAT", "Keylogger", "Spyware",
    "Botnet", "DDoS", "Phishing", "Rootkit", "Worm"
]

PROCESSES = [
    "svchost.exe", "explorer.exe", "chrome.exe", "firefox.exe",
    "malware.exe", "backdoor.dll", "injector.exe", "stealer.exe"
]

# Kerberos HQ (France)
KERBEROS_LAT, KERBEROS_LON = 48.8566, 2.3522

# ============================================================================
# === CLASSE PRINCIPALE ======================================================
# ============================================================================
class CyberMapAttackSimulator:
    def __init__(self):
        self.root = tk.Tk()
        self.root.title("🎮 Kerberos CyberMap — Test Attacks Simulator")
        self.root.geometry("1400x900")
        self.root.configure(bg='#0a0f1a')
        
        self.attacks = []
        self.running = False
        self.attack_count = 0
        self.blocked_count = 0
        
        self._setup_ui()
        self._start_attack_simulation()
        
    def _setup_ui(self):
        # ── Header ───────────────────────────────────────────────────────
        header = tk.Frame(self.root, bg='#16213e', height=80)
        header.pack(fill=tk.X)
        header.pack_propagate(False)
        
        tk.Label(header, text="🎮 CYBERMAP ATTACK SIMULATOR",
                bg='#16213e', fg='#00ffcc',
                font=("Consolas", 18, "bold")).pack(pady=20)
        
        # ── Stats Panel ──────────────────────────────────────────────────
        stats_frame = tk.Frame(self.root, bg='#0a0f1a')
        stats_frame.pack(fill=tk.X, padx=20, pady=10)
        
        self.stats_labels = {}
        for i, (key, label, color) in enumerate([
            ("total", "🔴 Attaques Totales", "#ff5252"),
            ("active", "⚡ Actives", "#ff9800"),
            ("blocked", "🛡️ Bloquées", "#4CAF50"),
            ("critical", "☢️ Critiques", "#9c27b0"),
        ]):
            box = tk.Frame(stats_frame, bg='#1a1a2e', relief=tk.RIDGE, bd=2)
            box.grid(row=0, column=i, padx=10, pady=5, sticky="nsew")
            
            tk.Label(box, text=label, bg='#1a1a2e', fg='#a0a0c0',
                    font=("Consolas", 9)).pack(pady=5)
            
            val = tk.Label(box, text="0", bg='#1a1a2e', fg=color,
                          font=("Consolas", 16, "bold"))
            val.pack()
            self.stats_labels[key] = val
        
        stats_frame.columnconfigure(0, weight=1)
        stats_frame.columnconfigure(1, weight=1)
        stats_frame.columnconfigure(2, weight=1)
        stats_frame.columnconfigure(3, weight=1)
        
        # ── Carte Canvas ─────────────────────────────────────────────────
        map_frame = tk.Frame(self.root, bg='#0a0f1a')
        map_frame.pack(fill=tk.BOTH, expand=True, padx=20, pady=10)
        
        self.canvas = tk.Canvas(map_frame, bg='#0a0f1a', highlightthickness=0)
        self.canvas.pack(fill=tk.BOTH, expand=True)
        
        # Dessine la carte de base
        self._draw_base_map()
        
        # ── Controls ─────────────────────────────────────────────────────
        controls = tk.Frame(self.root, bg='#16213e', height=60)
        controls.pack(fill=tk.X, padx=20, pady=(0, 20))
        controls.pack_propagate(False)
        
        tk.Button(controls, text="⚡ PLUS D'ATTAQUES", bg='#ff5252', fg='white',
                 font=("Consolas", 11, "bold"),
                 command=self._increase_attack_rate).pack(side=tk.LEFT, padx=10)
        
        tk.Button(controls, text="🛡️ BLOQUER TOUT", bg='#4CAF50', fg='white',
                 font=("Consolas", 11, "bold"),
                 command=self._block_all_attacks).pack(side=tk.LEFT, padx=10)
        
        tk.Button(controls, text="🔄 RESET", bg='#2196F3', fg='white',
                 font=("Consolas", 11, "bold"),
                 command=self._reset_stats).pack(side=tk.LEFT, padx=10)
        
        self.intensity_label = tk.Label(controls, text="Intensité: NORMALE",
                                       bg='#16213e', fg='#ff9800',
                                       font=("Consolas", 11, "bold"))
        self.intensity_label.pack(side=tk.RIGHT, padx=20)
        
        # ── Logs ─────────────────────────────────────────────────────────
        log_frame = tk.Frame(self.root, bg='#0a0f1a', height=150)
        log_frame.pack(fill=tk.X, padx=20, pady=(0, 20))
        log_frame.pack_propagate(False)
        
        tk.Label(log_frame, text="📜 Journal des Attaques",
                bg='#0a0f1a', fg='#00ffcc',
                font=("Consolas", 11, "bold")).pack(anchor=tk.W)
        
        self.log_text = scrolledtext.ScrolledText(log_frame,
                                                  bg='#0a0a0a', fg='#00ff00',
                                                  font=("Consolas", 9),
                                                  height=6)
        self.log_text.pack(fill=tk.BOTH, expand=True)
        
    def _draw_base_map(self):
        """Dessine une carte simplifiée du monde"""
        self.canvas.delete("all")
        
        # Continents simplifiés (rectangles approximatifs)
        continents = [
            # Amérique du Nord
            (-150, 100, -50, 250),
            # Amérique du Sud
            (-100, 280, -30, 450),
            # Europe
            (200, 80, 350, 180),
            # Afrique
            (180, 200, 350, 400),
            # Asie
            (350, 50, 600, 300),
            # Océanie
            (550, 350, 700, 450),
        ]
        
        for x1, y1, x2, y2 in continents:
            self.canvas.create_rectangle(x1, y1, x2, y2,
                                        outline='#1a2a3a', fill='#0d1117',
                                        width=1)
        
        # Kerberos HQ (France)
        hq_x, hq_y = self._lat_lon_to_xy(KERBEROS_LAT, KERBEROS_LON)
        self.canvas.create_oval(hq_x-10, hq_y-10, hq_x+10, hq_y+10,
                               fill='#00ccff', outline='#fff', width=2)
        self.canvas.create_text(hq_x, hq_y-20, text="🛡️ KERBEROS HQ",
                               fill='#00ffcc', font=("Consolas", 10, "bold"))
        
        # Grille
        for i in range(0, 800, 100):
            self.canvas.create_line(i, 0, i, 500, fill='#1a2a3a', dash=(2, 4))
            self.canvas.create_line(0, i, 800, i, fill='#1a2a3a', dash=(2, 4))
    
    def _lat_lon_to_xy(self, lat, lon):
        """Convertit lat/lon en coordonnées canvas"""
        x = (lon + 180) * (800 / 360)
        y = ((90 - lat) * (500 / 180))
        return x, y
    
    def _create_attack(self):
        """Crée une nouvelle attaque"""
        source = random.choice(ATTACK_SOURCES)
        malware = random.choice(MALWARE_TYPES)
        process = random.choice(PROCESSES)
        port = random.choice([22, 23, 80, 443, 4444, 5900, 8080, 3389])
        
        attack = {
            "id": self.attack_count,
            "source": source,
            "malware": malware,
            "process": process,
            "port": port,
            "timestamp": datetime.now().strftime("%H:%M:%S"),
            "status": "active",
            "color": "#ff0000" if source["threat"] == "critical" else
                    "#ff9800" if source["threat"] == "high" else
                    "#ffeb3b" if source["threat"] == "medium" else "#4CAF50",
        }
        
        self.attacks.append(attack)
        self.attack_count += 1
        
        # Animation
        self._animate_attack(attack)
        
        # Log
        self._log_attack(attack)
        
        # Update stats
        self._update_stats()
    
    def _animate_attack(self, attack):
        """Anime une ligne d'attaque depuis la source vers Kerberos HQ"""
        src_x, src_y = self._lat_lon_to_xy(attack["source"]["lat"],
                                           attack["source"]["lon"])
        hq_x, hq_y = self._lat_lon_to_xy(KERBEROS_LAT, KERBEROS_LON)
        
        # Dessine la ligne
        line_id = self.canvas.create_line(src_x, src_y, hq_x, hq_y,
                                         fill=attack["color"], width=2,
                                         dash=(5, 5))
        
        # Dessine le point source
        dot_id = self.canvas.create_oval(src_x-5, src_y-5, src_x+5, src_y+5,
                                        fill=attack["color"], outline='#fff')
        
        # Animation de progression
        steps = 50
        for i in range(steps):
            progress = i / steps
            x = src_x + (hq_x - src_x) * progress
            y = src_y + (hq_y - src_y) * progress
            
            self.canvas.coords(dot_id, x-5, y-5, x+5, y+5)
            self.canvas.update()
            time.sleep(0.02)
        
        # Supprime l'animation
        self.canvas.delete(line_id)
        self.canvas.delete(dot_id)
        
        # Marque l'attaque comme bloquée (simulé)
        attack["status"] = "blocked"
        self.blocked_count += 1
        self._update_stats()
    
    def _log_attack(self, attack):
        """Ajoute l'attaque au journal"""
        threat_icon = "☢️" if attack["source"]["threat"] == "critical" else \
                     "🔴" if attack["source"]["threat"] == "high" else \
                     "🟠" if attack["source"]["threat"] == "medium" else "🟢"
        
        log_line = (f"[{attack['timestamp']}] {threat_icon} "
                   f"{attack['source']['country']} ({attack['source']['city']}) → "
                   f"{attack['malware']} | Port {attack['port']} | "
                   f"{attack['process']}\n")
        
        self.log_text.insert(tk.END, log_line)
        self.log_text.see(tk.END)
        
        # Garde seulement 100 lignes
        lines = self.log_text.get("1.0", tk.END).splitlines()
        if len(lines) > 100:
            self.log_text.delete("1.0", "2.0")
    
    def _update_stats(self):
        """Met à jour les statistiques"""
        active = sum(1 for a in self.attacks if a["status"] == "active")
        critical = sum(1 for a in self.attacks if a["source"]["threat"] == "critical")
        
        self.stats_labels["total"].config(text=str(self.attack_count))
        self.stats_labels["active"].config(text=str(active))
        self.stats_labels["blocked"].config(text=str(self.blocked_count))
        self.stats_labels["critical"].config(text=str(critical))
    
    def _increase_attack_rate(self):
        """Augmente le taux d'attaques"""
        global ATTACK_INTERVAL
        ATTACK_INTERVAL = max(0.1, ATTACK_INTERVAL - 0.2)
        self.intensity_label.config(
            text=f"Intensité: {'MAXIMALE' if ATTACK_INTERVAL < 0.3 else 'ÉLEVÉE' if ATTACK_INTERVAL < 0.5 else 'NORMALE'}"
        )
    
    def _block_all_attacks(self):
        """Bloque toutes les attaques actives"""
        for attack in self.attacks:
            attack["status"] = "blocked"
        self.blocked_count = len(self.attacks)
        self._update_stats()
        self._log_attack({
            "timestamp": datetime.now().strftime("%H:%M:%S"),
            "source": {"country": "SYSTÈME", "city": ""},
            "malware": "TOUTES LES MENACES",
            "port": 0,
            "process": ""
        })
    
    def _reset_stats(self):
        """Reset les statistiques"""
        self.attacks = []
        self.attack_count = 0
        self.blocked_count = 0
        self.log_text.delete("1.0", tk.END)
        self._draw_base_map()
        self._update_stats()
        self._log_attack({
            "timestamp": datetime.now().strftime("%H:%M:%S"),
            "source": {"country": "SYSTÈME", "city": ""},
            "malware": "STATS RÉINITIALISÉES",
            "port": 0,
            "process": ""
        })
    
    def _attack_loop(self):
        """Boucle de génération d'attaques"""
        while self.running:
            self._create_attack()
            time.sleep(ATTACK_INTERVAL)
    
    def _start_attack_simulation(self):
        """Démarre la simulation"""
        self.running = True
        threading.Thread(target=self._attack_loop, daemon=True).start()
    
    def run(self):
        self.root.protocol("WM_DELETE_WINDOW", self._on_close)
        self.root.mainloop()
    
    def _on_close(self):
        self.running = False
        self.root.destroy()

# ============================================================================
# === POINT D'ENTRÉE =========================================================
# ============================================================================
ATTACK_INTERVAL = 0.5  # Secondes entre chaque attaque

if __name__ == "__main__":
    print("""
╔════════════════════════════════════════════════════════════╗
║  🎮 KERBEROS CYBERMAP ATTACK SIMULATOR                   ║
║                                                            ║
║  • Génère de fausses attaques depuis le monde entier     ║
║  • Teste la réactivité de l'UI CyberMap                  ║
║  • Usage : TEST UNIQUEMENT — ne modifie pas le système   ║
║                                                            ║
║  Licence : GPLv3 — Victor Pozen                           ║
║  🔗 github.com/victorpozen                                ║
╚════════════════════════════════════════════════════════════╝
    """)
    
    simulator = CyberMapAttackSimulator()
    simulator.run()