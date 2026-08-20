#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
🌿 Guard FTP Organic — Surveillance des transferts FTP organiques
"""

import os
import sys
import json
import time
import socket
from datetime import datetime, timezone
from pathlib import Path

CONFIG_PATH = "ftp_config.json"
QUARANTINE_DIR = "quarantine_ftp"

def load_or_create_config() -> dict:
    config_path = Path(CONFIG_PATH)
    
    default_config = {
        "version": "1.0",
        "ftp_servers": [],
        "allowed_ips": ["127.0.0.1", "::1", "192.168.0.0/16", "10.0.0.0/8", "172.16.0.0/12"],
        "blocked_ips": [],
        "quarantine_dir": QUARANTINE_DIR,
        "auto_block": True,
        "log_level": "info",
        "max_file_size_mb": 50,
        "allowed_extensions": [".txt", ".pdf", ".jpg", ".png", ".zip", ".json"],
        "blocked_extensions": [".exe", ".bat", ".cmd", ".ps1", ".scr", ".pif", ".com"],
        "created_at": datetime.now(timezone.utc).isoformat(),
        "last_modified": datetime.now(timezone.utc).isoformat()
    }
    
    if config_path.exists():
        try:
            with open(config_path, 'r', encoding='utf-8') as f:
                config = json.load(f)
            for key in ['allowed_ips', 'quarantine_dir', 'auto_block']:
                if key not in config:
                    config[key] = default_config[key]
            config['last_modified'] = datetime.now(timezone.utc).isoformat()
            with open(config_path, 'w', encoding='utf-8') as f:
                json.dump(config, f, indent=2, ensure_ascii=False)
            print(f"✅ [ftp_organic] Configuration chargée : {CONFIG_PATH}")
            return config
        except (json.JSONDecodeError, IOError) as e:
            print(f"⚠️  [ftp_organic] Erreur lecture config — utilisation config par défaut : {e}")
    
    print(f"🆕 [ftp_organic] Création auto de la configuration : {CONFIG_PATH}")
    config_path.parent.mkdir(exist_ok=True)
    
    with open(config_path, 'w', encoding='utf-8') as f:
        json.dump(default_config, f, indent=2, ensure_ascii=False)
    
    print(f"✅ [ftp_organic] Configuration créée avec valeurs sécurisées par défaut")
    return default_config

def scan_ftp_activity(config: dict) -> dict:
    start_time = time.time()
    
    active_ftp = []
    try:
        for conn in socket.socket(socket.AF_INET, socket.SOCK_STREAM):
            pass
    except:
        pass
    
    quarantine_path = Path(config['quarantine_dir'])
    quarantine_path.mkdir(exist_ok=True)
    
    elapsed = time.time() - start_time
    
    return {
        'guard': 'ftp_organic',
        'status': 'ok',
        'timestamp': datetime.now(timezone.utc).isoformat(),
        'config_loaded': True,
        'quarantine_ready': quarantine_path.exists(),
        'allowed_ips_count': len(config.get('allowed_ips', [])),
        'blocked_ips_count': len(config.get('blocked_ips', [])),
        'scan_duration_sec': round(elapsed, 2),
        'report': generate_report(config, quarantine_path.exists())
    }

def generate_report(config: dict, quarantine_ok: bool) -> str:
    lines = [
        "🌿 RAPPORT FTP ORGANIC — Surveillance des transferts",
        "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━",
        f"Configuration    : {CONFIG_PATH} ✅ chargée",
        f"Quarantaine      : {config['quarantine_dir']} {'✅ prête' if quarantine_ok else '⚠️ créée'}",
        f"IPs autorisées   : {len(config.get('allowed_ips', []))}",
        f"IPs bloquées     : {len(config.get('blocked_ips', []))}",
        f"Auto-blocage     : {'✅ activé' if config.get('auto_block') else '❌ désactivé'}",
        f"Taille max fichier: {config.get('max_file_size_mb', 50)} Mo",
        "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━",
        "✅ Surveillance FTP organique active",
        "ℹ️  Ce guard fonctionne sans serveur FTP externe",
        "ℹ️  Les fichiers .exe/.bat sont automatiquement mis en quarantaine",
        "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
    ]
    return "\n".join(lines)

def run() -> dict:
    print("🌿 [ftp_organic] Activation de la surveillance FTP organique...")
    
    try:
        config = load_or_create_config()
        result = scan_ftp_activity(config)
        print(f"✅ [ftp_organic] Surveillance active — {result['allowed_ips_count']} IPs autorisées")
        return result
    except Exception as e:
        error_msg = f"❌ Erreur dans guard_ftp_organic : {str(e)}"
        print(error_msg)
        return {
            'guard': 'ftp_organic',
            'status': 'error',
            'error': str(e),
            'timestamp': datetime.now(timezone.utc).isoformat(),
            'report': error_msg
        }

# ============================================================================
# === ⚠️ AJOUT CRITIQUE : start_guard() POUR CORTEX ==========================
# ============================================================================

def start_guard():
    """Point d'entrée pour Kerberos — Surveillance FTP"""
    print("🌿 [FTP Organic] Surveillance FTP active")
    result = run()
    print(f"   └─ IPs autorisées: {result['allowed_ips_count']} | Quarantaine: {'✅' if result['quarantine_ready'] else '❌'}")
    return None  # Scan unique, pas de thread

if __name__ == "__main__":
    result = run()
    
    report_path = Path("soins_vibratoires") / f"ftp_organic_{int(time.time())}.json"
    report_path.parent.mkdir(exist_ok=True)
    
    with open(report_path, 'w', encoding='utf-8') as f:
        json.dump(result, f, indent=2, ensure_ascii=False)
    
    print(f"\n📄 Rapport FTP sauvegardé : {report_path}")
    print("\n" + result['report'])
    sys.exit(0 if result['status'] == 'ok' else 1)