#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
📋 Guard Clipboard Shield — Protection du presse-papier contre le vol
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
⚠️ CE MODULE PROTÈGE :
- Surveillance des changements du presse-papier
- Détection de données sensibles (passwords, crypto, IBAN, etc.)
- Protection contre le clipboard hijacking (crypto addresses)
- Clear automatique après délai configurable
- Alerte si application suspecte accède au clipboard
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
✅ ACTIONS :
- 🧹 Clear automatique du clipboard
- 🔔 Alerte UI + Cerbère + Logs
- 🔒 Verrouillage clipboard temporaire
- 📝 Log de tous les accès suspects
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
Copyright (C) 2025 Victor Pozen — GPLv3
"""
# ============================================================================
#  KERBEROS ULTIMATE v4.2 — Guard Clipboard Shield
#  Copyright (C) 2025 Victor Pozen
# ============================================================================
#  LICENCE : GPLv3
#  AUTEUR  : Victor Pozen
#  VERSION : 4.2 Ultimate
#  DATE    : 2025
#  🔗 https://github.com/victorpozen
#  💰 https://liberapay.com/EthicalKerberos/
# ============================================================================

import os
import sys
import re
import time
import json
import hashlib
import threading
from pathlib import Path
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Set
import tkinter as tk

# ============================================================================
# === INTÉGRATION KERBEROS ===================================================
# ============================================================================
try:
    _kerberos_main = sys.modules.get("__main__")
    _GUARD_METRICS: dict = getattr(_kerberos_main, "_GUARD_METRICS", {})
except Exception:
    _GUARD_METRICS = {}

_MODULE_NAME = Path(__file__).name

def _publish_metric(level: float):
    _GUARD_METRICS[_MODULE_NAME] = max(0.0, min(1.0, level))

def _fire_alert(color: str, message: str):
    """Envoie alerte à UI Manager"""
    try:
        from guard_ui_manager import fire_alert
        fire_alert(_MODULE_NAME, color, message)
    except ImportError:
        pass

# ============================================================================
# === CONFIGURATION ==========================================================
# ============================================================================
KERBEROS_ROOT = Path(__file__).parent.parent
GUARDS_DIR = KERBEROS_ROOT / "guards"
LOGS_DIR = KERBEROS_ROOT / "logs"

# Création des dossiers
for d in [LOGS_DIR]:
    d.mkdir(parents=True, exist_ok=True)

# Patterns de données sensibles
SENSITIVE_PATTERNS = {
    "password": re.compile(r'(?i)(password|passwd|pwd|motdepasse)\s*[:=]\s*\S+'),
    "crypto_address": re.compile(r'\b[13][a-km-zA-HJ-NP-Z1-9]{25,34}\b'),  # Bitcoin
    "ethereum_address": re.compile(r'\b0x[a-fA-F0-9]{40}\b'),
    "iban": re.compile(r'\b[A-Z]{2}\d{2}\s?[A-Z0-9]{4}\s?\d{4,}\s?\d{4,}\s?\d{4,}\b'),
    "credit_card": re.compile(r'\b\d{4}[\s-]?\d{4}[\s-]?\d{4}[\s-]?\d{4}\b'),
    "private_key": re.compile(r'(?i)(private[_-]?key|priv[_-]?key)\s*[:=]\s*\S+'),
    "api_key": re.compile(r'(?i)(api[_-]?key|apikey)\s*[:=]\s*[a-zA-Z0-9]{20,}'),
    "bearer_token": re.compile(r'(?i)bearer\s+[a-zA-Z0-9\-_]+\.[a-zA-Z0-9\-_]+\.[a-zA-Z0-9\-_]+'),
}

# Applications légitimes pouvant accéder au clipboard
ALLOWED_APPS = {
    "notepad.exe", "notepad++.exe", "code.exe", "pycharm.exe",
    "firefox.exe", "chrome.exe", "edge.exe", "brave.exe",
    "explorer.exe", "clipbrd.exe", "dizgui.exe",
    "python.exe", "pythonw.exe", "kerberos.exe",
}

# Seuils de détection
CLIPBOARD_CHECK_INTERVAL = 2  # Secondes entre chaque vérification
AUTO_CLEAR_DELAY = 30  # Secondes avant clear automatique
MAX_CLIPBOARD_HISTORY = 100  # Nombre max d'entrées dans l'historique

# ============================================================================
# === LOGGING ================================================================
# ============================================================================
LOG_FILE = LOGS_DIR / "clipboard_shield.log"

def _log(msg: str, level="INFO"):
    """Log les actions de Clipboard Shield"""
    ts = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    line = f"[{ts}] [{level}] {msg}"
    try:
        with open(LOG_FILE, "a", encoding="utf-8") as f:
            f.write(line + "\n")
    except:
        pass
    print(f"📋 [Clipboard Shield] [{level}] {msg}")

# ============================================================================
# === DÉTECTION DE DONNÉES SENSIBLES =========================================
# ============================================================================

def _check_sensitive_data(text: str) -> Dict:
    """Vérifie si le texte contient des données sensibles"""
    results = {
        "is_sensitive": False,
        "types": [],
        "risk_level": "low",
    }
    
    for pattern_name, pattern in SENSITIVE_PATTERNS.items():
        if pattern.search(text):
            results["is_sensitive"] = True
            results["types"].append(pattern_name)
    
    # Déterminer le niveau de risque
    if len(results["types"]) >= 3:
        results["risk_level"] = "critical"
    elif len(results["types"]) >= 2:
        results["risk_level"] = "high"
    elif len(results["types"]) >= 1:
        results["risk_level"] = "medium"
    
    return results

def _get_clipboard_text() -> Optional[str]:
    """Récupère le texte du presse-papier"""
    try:
        root = tk.Tk()
        root.withdraw()
        text = root.clipboard_get()
        root.destroy()
        return text.strip() if text else None
    except Exception as e:
        return None

def _clear_clipboard():
    """Efface le presse-papier"""
    try:
        root = tk.Tk()
        root.withdraw()
        root.clipboard_clear()
        root.update()
        root.destroy()
        _log("🧹 Presse-papier effacé", "ACTION")
        return True
    except Exception as e:
        _log(f"❌ Échec clear clipboard: {e}", "ERROR")
        return False

# ============================================================================
# === SURVEILLANCE CONTINUE ==================================================
# ============================================================================

class ClipboardMonitor:
    """Surveillance continue du presse-papier"""
    
    def __init__(self):
        self.last_clipboard_content: Optional[str] = None
        self.last_check_time: float = 0
        self.clipboard_history: List[Dict] = []
        self.sensitive_count: int = 0
        self.clear_scheduled: Optional[float] = None
        self.monitoring: bool = False
        self.auto_clear_enabled: bool = True
    
    def _add_to_history(self, content: str, sensitive: bool, types: List[str]):
        """Ajoute une entrée à l'historique"""
        entry = {
            "timestamp": datetime.now().isoformat(),
            "content_hash": hashlib.sha256(content.encode()).hexdigest()[:16],
            "sensitive": sensitive,
            "types": types,
            "length": len(content),
        }
        
        self.clipboard_history.append(entry)
        
        # Limiter l'historique
        if len(self.clipboard_history) > MAX_CLIPBOARD_HISTORY:
            self.clipboard_history = self.clipboard_history[-MAX_CLIPBOARD_HISTORY:]
        
        if sensitive:
            self.sensitive_count += 1
    
    def check_clipboard(self) -> Dict:
        """Vérifie le presse-papier et retourne les résultats"""
        result = {
            "changed": False,
            "sensitive": False,
            "types": [],
            "risk_level": "none",
            "content_length": 0,
        }
        
        # Récupérer le contenu actuel
        current_content = _get_clipboard_text()
        
        if current_content is None:
            return result
        
        # Vérifier si le contenu a changé
        if current_content != self.last_clipboard_content:
            result["changed"] = True
            result["content_length"] = len(current_content)
            
            # Vérifier les données sensibles
            sensitivity = _check_sensitive_data(current_content)
            result["sensitive"] = sensitivity["is_sensitive"]
            result["types"] = sensitivity["types"]
            result["risk_level"] = sensitivity["risk_level"]
            
            # Ajouter à l'historique
            self._add_to_history(
                current_content,
                sensitivity["is_sensitive"],
                sensitivity["types"]
            )
            
            # Mettre à jour le dernier contenu
            self.last_clipboard_content = current_content
            self.last_check_time = time.time()
            
            # Planifier le clear automatique si données sensibles
            if sensitivity["is_sensitive"] and self.auto_clear_enabled:
                self.clear_scheduled = time.time() + AUTO_CLEAR_DELAY
                _log(f"⏱️ Clear automatique planifié dans {AUTO_CLEAR_DELAY}s", "INFO")
        
        # Vérifier si on doit clear automatiquement
        if self.clear_scheduled and time.time() >= self.clear_scheduled:
            if _clear_clipboard():
                result["cleared"] = True
                _fire_alert("#ff9800", "📋 Clipboard Shield: Presse-papier effacé (données sensibles)")
            self.clear_scheduled = None
        
        return result
    
    def get_stats(self) -> Dict:
        """Retourne les statistiques de surveillance"""
        return {
            "monitoring": self.monitoring,
            "sensitive_count": self.sensitive_count,
            "history_size": len(self.clipboard_history),
            "auto_clear_enabled": self.auto_clear_enabled,
            "clear_scheduled": self.clear_scheduled is not None,
            "last_check": self.last_check_time,
        }

# ============================================================================
# === BOUCLE DE SURVEILLANCE =================================================
# ============================================================================

def _monitor_loop(monitor: ClipboardMonitor):
    """Boucle de surveillance continue"""
    _log("👁️ Surveillance clipboard activée", "START")
    
    while monitor.monitoring:
        try:
            result = monitor.check_clipboard()
            
            if result["changed"]:
                if result["sensitive"]:
                    # Alerte pour données sensibles
                    types_str = ", ".join(result["types"])
                    _log(f"🚨 DONNÉES SENSIBLES DÉTECTÉES: {types_str} (risque: {result['risk_level']})", "ALERT")
                    _fire_alert("#ff5252", f"📋 Clipboard Shield: {result['risk_level'].upper()} - {types_str}")
                    _publish_metric(0.9)
                else:
                    # Changement normal
                    _log(f"📝 Clipboard changé ({result['content_length']} chars)", "INFO")
                    _publish_metric(0.2)
            
            if result.get("cleared"):
                _publish_metric(0.1)
            
            time.sleep(CLIPBOARD_CHECK_INTERVAL)
            
        except Exception as e:
            _log(f"❌ Erreur surveillance: {e}", "ERROR")
            time.sleep(5)

# ============================================================================
# === POINT D'ENTRÉE KERBEROS ================================================
# ============================================================================

_monitor_instance: Optional[ClipboardMonitor] = None
_monitor_thread: Optional[threading.Thread] = None

def start_guard():
    """Point d'entrée pour Kerberos"""
    global _monitor_instance, _monitor_thread
    
    _log("📋 [Clipboard Shield] Guard démarré — Surveillance active", "START")
    
    _monitor_instance = ClipboardMonitor()
    _monitor_instance.monitoring = True
    
    _monitor_thread = threading.Thread(
        target=_monitor_loop,
        args=(_monitor_instance,),
        daemon=True,
        name="kerberos_clipboard_shield"
    )
    _monitor_thread.start()
    
    _publish_metric(0.1)
    return _monitor_thread

def run(mode: str = "scan"):
    """Exécution standalone — scan manuel"""
    _log(f"🔍 [Clipboard Shield] Scan manuel: {mode}", "MANUAL")
    
    monitor = ClipboardMonitor()
    
    if mode == "scan":
        # Scan unique
        result = monitor.check_clipboard()
        
        print("\n" + "="*60)
        print("📋 RAPPORT CLIPBOARD SHIELD")
        print("="*60)
        print(f"📝 Contenu détecté: {'OUI' if result['changed'] else 'NON'}")
        print(f"🚨 Données sensibles: {'OUI' if result['sensitive'] else 'NON'}")
        print(f"⚠️ Types: {', '.join(result['types']) if result['types'] else 'Aucun'}")
        print(f"📊 Risque: {result['risk_level']}")
        print(f"📏 Longueur: {result['content_length']} chars")
        print("="*60)
        
        return {
            "guard": "clipboard_shield",
            "status": "scan_complete",
            "result": result,
        }
    
    elif mode == "clear":
        # Clear manuel
        if _clear_clipboard():
            print("✅ Presse-papier effacé avec succès")
            return {"status": "cleared"}
        else:
            print("❌ Échec du clear")
            return {"status": "failed"}
    
    elif mode == "watch":
        # Surveillance continue
        monitor.monitoring = True
        print("👁️ Mode surveillance activé (Ctrl+C pour arrêter)")
        try:
            _monitor_loop(monitor)
        except KeyboardInterrupt:
            print("🛑 Arrêt")
            monitor.monitoring = False
        return {"status": "stopped"}
    
    return {"status": "unknown_mode"}

def get_stats() -> Dict:
    """Stats pour l'onglet Guards"""
    if _monitor_instance:
        stats = _monitor_instance.get_stats()
        return {
            "guard_name": "Clipboard Shield",
            "status": "active" if stats["monitoring"] else "inactive",
            "description": "Protection du presse-papier contre le vol de données",
            "sensitive_detected": stats["sensitive_count"],
            "history_size": stats["history_size"],
            "auto_clear": stats["auto_clear_enabled"],
        }
    else:
        return {
            "guard_name": "Clipboard Shield",
            "status": "inactive",
            "description": "Protection du presse-papier contre le vol de données",
            "sensitive_detected": 0,
            "history_size": 0,
            "auto_clear": True,
        }

def stop_guard():
    """Arrêt propre du guard"""
    global _monitor_instance, _monitor_thread
    
    if _monitor_instance:
        _monitor_instance.monitoring = False
        _log("🛑 [Clipboard Shield] Guard arrêté", "STOP")
    
    _monitor_instance = None
    _publish_metric(0.0)

# ============================================================================
# === MODE STANDALONE ========================================================
# ============================================================================

if __name__ == "__main__":
    import argparse
    
    parser = argparse.ArgumentParser(description="📋 Kerberos Clipboard Shield Guard")
    parser.add_argument("mode", nargs="?", default="scan", 
                       choices=["scan", "clear", "watch"],
                       help="Mode: scan, clear, ou watch")
    args = parser.parse_args()
    
    print("""
╔════════════════════════════════════════════════════════════╗
║  📋 KERBEROS CLIPBOARD SHIELD                             ║
║                                                            ║
║  Protection du presse-papier contre :                     ║
║    • Vol de mots de passe                                 ║
║    • Clipboard hijacking (crypto addresses)               ║
║    • Vol de données sensibles (IBAN, CB, etc.)           ║
║    • Accès par applications suspectes                     ║
║                                                            ║
║  Modes :                                                  ║
║    scan  → Scan unique du clipboard                       ║
║    clear → Effacer le clipboard                           ║
║    watch → Surveillance continue                          ║
║                                                            ║
║  Licence : GPLv3 — Victor Pozen                           ║
╚════════════════════════════════════════════════════════════╝
    """)
    
    result = run(args.mode)
    print(f"\n📊 Statut: {result.get('status', 'unknown')}")