#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
🫀 Guard Lymphatic Heart — MONITEUR SEULEMENT (PAS DE DOUBLE CŒUR)
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
- ⚠️ CORRECTION : Ne crée PAS son propre cœur (conflit avec kerberos.py)
- Surveille l'état du cœur principal dans kerberos.py
- Affiche les stats de phase (systole/diastole/pause)
- Thread-safe avec l'UI Tkinter
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
Copyright (C) 2025 Victor Pozen — GPLv3
"""
import time
import threading
import json
from pathlib import Path
from datetime import datetime

# === CONFIGURATION ===
_BIO_ROOT = Path(__file__).parent.parent / "lymph"
_GENOME_FILE = _BIO_ROOT / "genome.json"
_LOG_FILE = Path(__file__).parent.parent / "logs" / "lymphatic_heart.log"
_LOG_FILE.parent.mkdir(parents=True, exist_ok=True)

# === ÉTAT GLOBAL (EN LECTURE SEULE — PAS DE CRÉATION DE CŒUR) ===
_monitoring = False
_app_instance = None

def _log(msg: str, level="INFO"):
    """Log interne"""
    ts = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    line = f"[{ts}] [{level}] {msg}"
    try:
        with open(_LOG_FILE, "a", encoding="utf-8") as f:
            f.write(line + "\n")
    except:
        pass
    if __name__ == "__main__":
        print(line)

def _monitor_heart():
    """Surveille le cœur principal (kerberos.py) — NE CRÉE PAS DE NOUVEAU CŒUR"""
    global _monitoring
    
    _log("🫀 [Lymphatic Heart] Mode MONITEUR — Surveille le cœur de kerberos.py")
    
    while _monitoring:
        try:
            # Vérifie le genome.json pour l'état du cœur
            if _GENOME_FILE.exists():
                try:
                    genome = json.loads(_GENOME_FILE.read_text(encoding="utf-8"))
                    last_pulse = genome.get("last_pulse", 0)
                    
                    # Si pas de pulse depuis 120s → alerte
                    if time.time() - last_pulse > 120:
                        _log("⚠️ [Heart] Cœur principal semble arrêté — dernier pulse: " + 
                             datetime.fromtimestamp(last_pulse).strftime("%H:%M:%S"), "WARN")
                    else:
                        _log("✅ [Heart] Cœur principal actif", "INFO")
                except:
                    pass
            
            time.sleep(30)  # Check toutes les 30s
        except Exception as e:
            _log(f"Erreur monitoring : {e}", "ERROR")
            time.sleep(10)

def set_app_instance(app):
    """Définit l'instance de l'application (pour référence)"""
    global _app_instance
    _app_instance = app

def start_guard(app_instance=None):
    """
    Point d'entrée pour Kerberos — MODE MONITEUR SEULEMENT
    ⚠️ NE CRÉE PAS DE NOUVEAU CŒUR (kerberos.py s'en occupe)
    """
    global _monitoring
    
    if app_instance:
        set_app_instance(app_instance)
    
    _monitoring = True
    
    # Démarre le monitoring en thread (léger, pas de conflit)
    thread = threading.Thread(target=_monitor_heart, daemon=True, name="LymphaticHeart-Monitor")
    thread.start()
    
    print("🫀 [Lymphatic Heart] Guard actif — Mode MONITEUR (pas de double cœur)")
    return thread

def stop_guard():
    """Arrête le monitoring"""
    global _monitoring
    _monitoring = False
    print("🫀 [Lymphatic Heart] Arrêt du monitoring")

def get_status():
    """Retourne le statut du guard"""
    return {
        "guard": "lymphatic_heart",
        "status": "monitoring" if _monitoring else "stopped",
        "mode": "monitor_only",  # ← IMPORTANT : pas de création de cœur
        "genome_file": str(_GENOME_FILE),
        "genome_exists": _GENOME_FILE.exists()
    }

def run():
    """Exécution standalone (test)"""
    print("""
╔════════════════════════════════════════════════════════╗
║  🫀 KERBEROS LYMPHATIC HEART — Mode Moniteur          ║
║                                                        ║
║  ⚠️  NE CRÉE PAS DE DOUBLE CŒUR                       ║
║  • Surveille le cœur de kerberos.py                   ║
║  • Alerte si cœur principal arrêté                    ║
║  • Thread-safe avec UI                                ║
╚════════════════════════════════════════════════════════╝
    """)
    
    start_guard()
    
    try:
        while True:
            time.sleep(1)
    except KeyboardInterrupt:
        stop_guard()
        print("\n🫀 [Lymphatic Heart] Arrêt test")

if __name__ == "__main__":
    run()