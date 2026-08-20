#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
🎮 Test CyberMap Inject — Interface GUI pour tester la CyberMap
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
- Interface Tkinter pour injecter de fausses attaques
- Teste guard_cybermap.py sans vrai trafic réseau
- Boutons pour différents types d'attaques
- Visualisation des injections en temps réel
- Compatible avec mode test de guard_cybermap.py
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
Copyright (C) 2025 Victor Pozen — GPLv3
"""
# ============================================================================
#  KERBEROS ULTIMATE v4.2 — Test CyberMap Inject GUI
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
import sys
import time
import threading
import random
from pathlib import Path
from datetime import datetime

# ============================================================================
# === IMPORT GUARD_CYBERMAP ==================================================
# ============================================================================
GUARDS_DIR = Path(__file__).parent / "guards"
sys.path.insert(0, str(Path(__file__).parent))

try:
    from guards.guard_cybermap import (
        enable_test_mode,
        inject_test_connection,
        clear_test_connections,
        _TEST_CONNECTIONS,
        _TEST_MODE
    )
    CYBERMAP_AVAILABLE = True
except ImportError:
    CYBERMAP_AVAILABLE = False
    print("⚠️ guard_cybermap.py non trouvé — mode simulation uniquement")

# ============================================================================
# === DONNÉES GÉOGRAPHIQUES ==================================================
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

PORTS = [22, 23, 80, 443, 4444, 5900, 8080, 3389, 8443, 9001]

# ============================================================================
# === CLASSE PRINCIPALE ======================================================
# ============================================================================
class CyberMapTestInjector:
    def __init__(self):
        self.root = tk.Tk()
        self.root.title("🎮 Kerberos CyberMap — Test Injector")
        self.root.geometry("1000x700")
        self.root.configure(bg='#0a0f1a')
        
        self.test_mode_active = False
        self.injection_count = 0
        self.injection_history = []
        
        self._setup_ui()
        self._start_monitoring()
        
    def _setup_ui(self):
        # ── Header ───────────────────────────────────────────────────────
        header = tk.Frame(self.root, bg='#16213e', height=80)
        header.pack(fill=tk.X)
        header.pack_propagate(False)
        
        tk.Label(header, text="🎮 CYBERMAP TEST INJECTOR",
                bg='#16213e', fg='#00ffcc',
                font=("Consolas", 18, "bold")).pack(pady=20)
        
        # ── Status Panel ─────────────────────────────────────────────────
        status_frame = tk.Frame(self.root, bg='#0a0f1a')
        status_frame.pack(fill=tk.X, padx=20, pady=10)
        
        self.status_label = tk.Label(status_frame, 
                                     text="⚪ MODE TEST: DÉSACTIVÉ",
                                     bg='#1a1a2e', fg='#ff5252',
                                     font=("Consolas", 12, "bold"),
                                     padx=20, pady=10)
        self.status_label.pack(fill=tk.X)
        
        # ── Controls ─────────────────────────────────────────────────────
        controls = tk.Frame(self.root, bg='#1e1e2e', height=180)
        controls.pack(fill=tk.X, padx=20, pady=10)
        controls.pack_propagate(False)
        
        # Ligne 1: Activation
        tk.Label(controls, text="🎛️ CONTRÔLES",
                bg='#1e1e2e', fg='#00ffcc',
                font=("Consolas", 11, "bold")).grid(row=0, column=0, 
                                                     columnspan=4, pady=(10, 5), sticky="w")
        
        tk.Button(controls, text="▶️ ACTIVER MODE TEST",
                 bg='#4CAF50', fg='white',
                 font=("Consolas", 10, "bold"),
                 command=self._enable_test_mode).grid(row=1, column=0, 
                                                       padx=5, pady=5, sticky="nsew")
        
        tk.Button(controls, text="⏹️ DÉSACTIVER",
                 bg='#f44336', fg='white',
                 font=("Consolas", 10, "bold"),
                 command=self._disable_test_mode).grid(row=1, column=1, 
                                                        padx=5, pady=5, sticky="nsew")
        
        tk.Button(controls, text="🧹 EFFACER TOUT",
                 bg='#FF9800', fg='white',
                 font=("Consolas", 10, "bold"),
                 command=self._clear_all).grid(row=1, column=2, 
                                                padx=5, pady=5, sticky="nsew")
        
        # Ligne 2: Injections
        tk.Button(controls, text="⚡ 1 ATTAQUE",
                 bg='#2196F3', fg='white',
                 font=("Consolas", 10, "bold"),
                 command=self._inject_one).grid(row=2, column=0, 
                                                 padx=5, pady=5, sticky="nsew")
        
        tk.Button(controls, text="⚡⚡ 5 ATTAQUES",
                 bg='#2196F3', fg='white',
                 font=("Consolas", 10, "bold"),
                 command=self._inject_five).grid(row=2, column=1, 
                                                  padx=5, pady=5, sticky="nsew")
        
        tk.Button(controls, text="⚡⚡⚡ 10 ATTAQUES",
                 bg='#2196F3', fg='white',
                 font=("Consolas", 10, "bold"),
                 command=self._inject_ten).grid(row=2, column=2, 
                                                 padx=5, pady=5, sticky="nsew")
        
        # Ligne 3: Types spécifiques
        tk.Button(controls, text="🇷🇺 RUSSIE",
                 bg='#9C27B0', fg='white',
                 font=("Consolas", 9),
                 command=lambda: self._inject_country("Russie")).grid(row=3, column=0, 
                                                                       padx=5, pady=5, sticky="nsew")
        
        tk.Button(controls, text="🇨🇳 CHINE",
                 bg='#9C27B0', fg='white',
                 font=("Consolas", 9),
                 command=lambda: self._inject_country("Chine")).grid(row=3, column=1, 
                                                                      padx=5, pady=5, sticky="nsew")
        
        tk.Button(controls, text="🇺🇸 USA",
                 bg='#9C27B0', fg='white',
                 font=("Consolas", 9),
                 command=lambda: self._inject_country("États-Unis")).grid(row=3, column=2, 
                                                                           padx=5, pady=5, sticky="nsew")
        
        controls.columnconfigure(0, weight=1)
        controls.columnconfigure(1, weight=1)
        controls.columnconfigure(2, weight=1)
        
        # ── Stats ────────────────────────────────────────────────────────
        stats_frame = tk.Frame(self.root, bg='#0a0f1a')
        stats_frame.pack(fill=tk.X, padx=20, pady=10)
        
        self.stats_labels = {}
        for i, (key, label, color) in enumerate([
            ("total", "📊 Total", "#00ffcc"),
            ("active", "🔴 Actives", "#ff5252"),
            ("critical", "☢️ Critiques", "#9c27b0"),
        ]):
            box = tk.Frame(stats_frame, bg='#1a1a2e', relief=tk.RIDGE, bd=1)
            box.grid(row=0, column=i, padx=10, sticky="nsew")
            
            tk.Label(box, text=label, bg='#1a1a2e', fg='#a0a0c0',
                    font=("Consolas", 9)).pack(pady=3)
            
            val = tk.Label(box, text="0", bg='#1a1a2e', fg=color,
                          font=("Consolas", 14, "bold"))
            val.pack(pady=3)
            self.stats_labels[key] = val
        
        stats_frame.columnconfigure(0, weight=1)
        stats_frame.columnconfigure(1, weight=1)
        stats_frame.columnconfigure(2, weight=1)
        
        # ── Logs ─────────────────────────────────────────────────────────
        log_frame = tk.Frame(self.root, bg='#0a0f1a')
        log_frame.pack(fill=tk.BOTH, expand=True, padx=20, pady=(0, 20))
        
        tk.Label(log_frame, text="📜 JOURNAL D'INJECTIONS",
                bg='#0a0f1a', fg='#00ffcc',
                font=("Consolas", 11, "bold")).pack(anchor=tk.W)
        
        self.log_text = scrolledtext.ScrolledText(log_frame,
                                                  bg='#0a0a0a', fg='#00ff00',
                                                  font=("Consolas", 9),
                                                  height=12)
        self.log_text.pack(fill=tk.BOTH, expand=True)
        
        # ── Footer ───────────────────────────────────────────────────────
        footer = tk.Frame(self.root, bg='#16213e', height=40)
        footer.pack(fill=tk.X, side=tk.BOTTOM)
        footer.pack_propagate(False)
        
        tk.Label(footer, text="GPLv3 • Victor Pozen • Test uniquement — ne modifie pas le système",
                bg='#16213e', fg='#607d8b',
                font=("Consolas", 8)).pack(pady=10)
        
    def _setup_ui(self):
        # ── Header ───────────────────────────────────────────────────────
        header = tk.Frame(self.root, bg='#16213e', height=80)
        header.pack(fill=tk.X)
        header.pack_propagate(False)
        
        tk.Label(header, text="🎮 CYBERMAP TEST INJECTOR",
                bg='#16213e', fg='#00ffcc',
                font=("Consolas", 18, "bold")).pack(pady=20)
        
        # ── Status Panel ─────────────────────────────────────────────────
        status_frame = tk.Frame(self.root, bg='#0a0f1a')
        status_frame.pack(fill=tk.X, padx=20, pady=10)
        
        self.status_label = tk.Label(status_frame, 
                                     text="⚪ MODE TEST: DÉSACTIVÉ",
                                     bg='#1a1a2e', fg='#ff5252',
                                     font=("Consolas", 12, "bold"),
                                     padx=20, pady=10)
        self.status_label.pack(fill=tk.X)
        
        # ── Controls ─────────────────────────────────────────────────────
        controls = tk.Frame(self.root, bg='#1e1e2e', height=180)
        controls.pack(fill=tk.X, padx=20, pady=10)
        controls.pack_propagate(False)
        
        tk.Label(controls, text="🎛️ CONTRÔLES",
                bg='#1e1e2e', fg='#00ffcc',
                font=("Consolas", 11, "bold")).grid(row=0, column=0, 
                                                     columnspan=3, pady=(10, 5), sticky="w")
        
        tk.Button(controls, text="▶️ ACTIVER MODE TEST",
                 bg='#4CAF50', fg='white',
                 font=("Consolas", 10, "bold"),
                 command=self._enable_test_mode).grid(row=1, column=0, 
                                                       padx=5, pady=5, sticky="nsew")
        
        tk.Button(controls, text="⏹️ DÉSACTIVER",
                 bg='#f44336', fg='white',
                 font=("Consolas", 10, "bold"),
                 command=self._disable_test_mode).grid(row=1, column=1, 
                                                        padx=5, pady=5, sticky="nsew")
        
        tk.Button(controls, text="🧹 EFFACER TOUT",
                 bg='#FF9800', fg='white',
                 font=("Consolas", 10, "bold"),
                 command=self._clear_all).grid(row=1, column=2, 
                                                padx=5, pady=5, sticky="nsew")
        
        tk.Button(controls, text="⚡ 1 ATTAQUE",
                 bg='#2196F3', fg='white',
                 font=("Consolas", 10, "bold"),
                 command=self._inject_one).grid(row=2, column=0, 
                                                 padx=5, pady=5, sticky="nsew")
        
        tk.Button(controls, text="⚡⚡ 5 ATTAQUES",
                 bg='#2196F3', fg='white',
                 font=("Consolas", 10, "bold"),
                 command=self._inject_five).grid(row=2, column=1, 
                                                  padx=5, pady=5, sticky="nsew")
        
        tk.Button(controls, text="⚡⚡⚡ 10 ATTAQUES",
                 bg='#2196F3', fg='white',
                 font=("Consolas", 10, "bold"),
                 command=self._inject_ten).grid(row=2, column=2, 
                                                 padx=5, pady=5, sticky="nsew")
        
        tk.Button(controls, text="🇷🇺 RUSSIE",
                 bg='#9C27B0', fg='white',
                 font=("Consolas", 9),
                 command=lambda: self._inject_country("Russie")).grid(row=3, column=0, 
                                                                       padx=5, pady=5, sticky="nsew")
        
        tk.Button(controls, text="🇨🇳 CHINE",
                 bg='#9C27B0', fg='white',
                 font=("Consolas", 9),
                 command=lambda: self._inject_country("Chine")).grid(row=3, column=1, 
                                                                      padx=5, pady=5, sticky="nsew")
        
        tk.Button(controls, text="🇺🇸 USA",
                 bg='#9C27B0', fg='white',
                 font=("Consolas", 9),
                 command=lambda: self._inject_country("États-Unis")).grid(row=3, column=2, 
                                                                           padx=5, pady=5, sticky="nsew")
        
        controls.columnconfigure(0, weight=1)
        controls.columnconfigure(1, weight=1)
        controls.columnconfigure(2, weight=1)
        
        # ── Stats ────────────────────────────────────────────────────────
        stats_frame = tk.Frame(self.root, bg='#0a0f1a')
        stats_frame.pack(fill=tk.X, padx=20, pady=10)
        
        self.stats_labels = {}
        for i, (key, label, color) in enumerate([
            ("total", "📊 Total", "#00ffcc"),
            ("active", "🔴 Actives", "#ff5252"),
            ("critical", "☢️ Critiques", "#9c27b0"),
        ]):
            box = tk.Frame(stats_frame, bg='#1a1a2e', relief=tk.RIDGE, bd=1)
            box.grid(row=0, column=i, padx=10, sticky="nsew")
            
            tk.Label(box, text=label, bg='#1a1a2e', fg='#a0a0c0',
                    font=("Consolas", 9)).pack(pady=3)
            
            val = tk.Label(box, text="0", bg='#1a1a2e', fg=color,
                          font=("Consolas", 14, "bold"))
            val.pack(pady=3)
            self.stats_labels[key] = val
        
        stats_frame.columnconfigure(0, weight=1)
        stats_frame.columnconfigure(1, weight=1)
        stats_frame.columnconfigure(2, weight=1)
        
        # ── Logs ─────────────────────────────────────────────────────────
        log_frame = tk.Frame(self.root, bg='#0a0f1a')
        log_frame.pack(fill=tk.BOTH, expand=True, padx=20, pady=(0, 20))
        
        tk.Label(log_frame, text="📜 JOURNAL D'INJECTIONS",
                bg='#0a0f1a', fg='#00ffcc',
                font=("Consolas", 11, "bold")).pack(anchor=tk.W)
        
        self.log_text = scrolledtext.ScrolledText(log_frame,
                                                  bg='#0a0a0a', fg='#00ff00',
                                                  font=("Consolas", 9),
                                                  height=12)
        self.log_text.pack(fill=tk.BOTH, expand=True)
        
        # ── Footer ───────────────────────────────────────────────────────
        footer = tk.Frame(self.root, bg='#16213e', height=40)
        footer.pack(fill=tk.X, side=tk.BOTTOM)
        footer.pack_propagate(False)
        
        tk.Label(footer, text="GPLv3 • Victor Pozen • Test uniquement — ne modifie pas le système",
                bg='#16213e', fg='#607d8b',
                font=("Consolas", 8)).pack(pady=10)
    
    def _log(self, message: str, level: str = "INFO"):
        """Ajoute un message au journal"""
        timestamp = datetime.now().strftime("%H:%M:%S")
        icon = "📊" if level == "INFO" else "🚨" if level == "ATTACK" else "✅"
        log_line = f"[{timestamp}] {icon} {message}\n"
        
        self.log_text.insert(tk.END, log_line)
        self.log_text.see(tk.END)
        
        # Garde seulement 100 lignes
        lines = self.log_text.get("1.0", tk.END).splitlines()
        if len(lines) > 100:
            self.log_text.delete("1.0", "2.0")
    
    def _update_stats(self):
        """Met à jour les statistiques"""
        if CYBERMAP_AVAILABLE:
            total = len(_TEST_CONNECTIONS)
            critical = sum(1 for c in _TEST_CONNECTIONS 
                          if c.get("country") in ["Russie", "Chine", "Corée du Nord"])
        else:
            total = self.injection_count
            critical = 0
        
        self.stats_labels["total"].config(text=str(total))
        self.stats_labels["active"].config(text=str(total))
        self.stats_labels["critical"].config(text=str(critical))
    
    def _enable_test_mode(self):
        """Active le mode test"""
        if CYBERMAP_AVAILABLE:
            enable_test_mode(True)
            self.test_mode_active = True
            self.status_label.config(
                text="🟢 MODE TEST: ACTIVÉ",
                bg='#1a2e1a', fg='#4CAF50'
            )
            self._log("Mode test ACTIVÉ — Les attaques apparaîtront sur CyberMap", "INFO")
        else:
            self.test_mode_active = True
            self.status_label.config(
                text="🟠 MODE TEST: SIMULATION",
                bg='#2e1a1a', fg='#FF9800'
            )
            self._log("Mode simulation ACTIVÉ (guard_cybermap.py non disponible)", "INFO")
    
    def _disable_test_mode(self):
        """Désactive le mode test"""
        if CYBERMAP_AVAILABLE:
            enable_test_mode(False)
            clear_test_connections()
        self.test_mode_active = False
        self.injection_count = 0
        self.status_label.config(
            text="⚪ MODE TEST: DÉSACTIVÉ",
            bg='#1a1a2e', fg='#ff5252'
        )
        self._log("Mode test DÉSACTIVÉ", "INFO")
        self._update_stats()
    
    def _clear_all(self):
        """Efface toutes les injections"""
        if CYBERMAP_AVAILABLE:
            clear_test_connections()
        self.injection_count = 0
        self._log("Toutes les injections effacées", "INFO")
        self._update_stats()
    
    def _inject_connection(self, source=None):
        """Injecte une connexion test"""
        if source is None:
            source = random.choice(ATTACK_SOURCES)
        
        malware = random.choice(MALWARE_TYPES)
        process = random.choice(PROCESSES)
        port = random.choice(PORTS)
        
        if CYBERMAP_AVAILABLE and self.test_mode_active:
            inject_test_connection(source)
            self._log(f"ATTAQUE: {source['country']} ({source['city']}) → {malware} | Port {port} | {process}", "ATTACK")
        else:
            self.injection_count += 1
            self._log(f"SIMULATION: {source['country']} → {malware} (mode test inactif)", "ATTACK")
        
        self.injection_history.append({
            "timestamp": datetime.now().isoformat(),
            "country": source["country"],
            "city": source["city"],
            "malware": malware,
            "port": port,
            "process": process,
            "threat": source["threat"],
        })
        
        self._update_stats()
    
    def _inject_one(self):
        """Injecte 1 attaque"""
        self._inject_connection()
    
    def _inject_five(self):
        """Injecte 5 attaques"""
        for i in range(5):
            self._inject_connection()
        self._log("5 attaques injectées en lot", "INFO")
    
    def _inject_ten(self):
        """Injecte 10 attaques"""
        for i in range(10):
            self._inject_connection()
        self._log("10 attaques injectées en lot", "INFO")
    
    def _inject_country(self, country: str):
        """Injecte une attaque depuis un pays spécifique"""
        sources = [s for s in ATTACK_SOURCES if s["country"] == country]
        if sources:
            self._inject_connection(random.choice(sources))
            self._log(f"Attaque ciblée depuis {country}", "INFO")
        else:
            self._log(f"Pays {country} non trouvé dans la liste", "INFO")
    
    def _start_monitoring(self):
        """Démarre le monitoring des stats"""
        def monitor():
            self._update_stats()
            self.root.after(2000, monitor)
        monitor()
    
    def run(self):
        self.root.protocol("WM_DELETE_WINDOW", self._on_close)
        self._log("🎮 Test Injector démarré — Prêt à injecter des attaques", "INFO")
        self._log("💡 Astuce: Active le mode test puis clique sur les boutons d'injection", "INFO")
        self.root.mainloop()
    
    def _on_close(self):
        if CYBERMAP_AVAILABLE:
            enable_test_mode(False)
            clear_test_connections()
        self.root.destroy()

# ============================================================================
# === POINT D'ENTRÉE =========================================================
# ============================================================================
if __name__ == "__main__":
    print("""
╔════════════════════════════════════════════════════════════╗
║  🎮 KERBEROS CYBERMAP TEST INJECTOR — GUI                ║
║                                                            ║
║  • Interface Tkinter pour tester la CyberMap             ║
║  • Injecte de fausses attaques en temps réel             ║
║  • Compatible avec guard_cybermap.py (mode test)         ║
║  • Usage : TEST UNIQUEMENT — ne modifie pas le système   ║
║                                                            ║
║  Licence : GPLv3 — Victor Pozen                           ║
║  🔗 github.com/victorpozen                                ║
╚════════════════════════════════════════════════════════════╝
    """)
    
    app = CyberMapTestInjector()
    app.run()