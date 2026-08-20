#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
🛡️ Guard Anti-Keylogger — Détection précise sans faux positifs
"""

import os
import sys
import json
import psutil
import time
from datetime import datetime
from pathlib import Path

# ✅ WHITELIST : processus légitimes
WHITELISTED_PROCESSES = {
    'firefox.exe', 'chrome.exe', 'msedge.exe', 'opera.exe', 'brave.exe', 'vivaldi.exe',
    'outlook.exe', 'thunderbird.exe', 'discord.exe', 'slack.exe', 'teams.exe',
    'explorer.exe', 'svchost.exe', 'dllhost.exe', 'runtimebroker.exe',
}

# 🔍 Signatures comportementales de keyloggers
SUSPICIOUS_NAMES = [
    "keylogger", "keylog", "logger", "spy", "stealer", "trojan",
    "refog", "kidlogger", "activitymonitor", "keystroke", "formgrabber"
]

def is_legitimate_process(proc) -> bool:
    try:
        name = proc.name().lower()
        if name in WHITELISTED_PROCESSES:
            return True
        if proc.username().lower().startswith("nt authority"):
            return True
        exe = proc.exe() if proc.exe() else ""
        if any(path in exe.lower() for path in ["c:\\program files\\", "c:\\windows\\"]):
            return True
        return False
    except (psutil.NoSuchProcess, psutil.AccessDenied):
        return False

def is_suspicious_process(proc) -> tuple:
    try:
        name = proc.name().lower()
        cmdline = " ".join(proc.cmdline()).lower() if proc.cmdline() else ""
        
        if is_legitimate_process(proc):
            return False, ""
        
        for keyword in SUSPICIOUS_NAMES:
            if keyword in name or keyword in cmdline:
                return True, f"signature connue: '{keyword}'"
        
        try:
            connections = proc.connections()
            has_network = any(c.status == 'ESTABLISHED' for c in connections)
            if has_network and proc.create_time() < time.time() - 300:
                return True, f"comportement caché + réseau: '{name}'"
        except (psutil.AccessDenied, psutil.NoSuchProcess):
            pass
        
        return False, ""
    except (psutil.NoSuchProcess, psutil.AccessDenied, AttributeError):
        return False, ""

def scan_processes() -> dict:
    threats = []
    scanned = 0
    start_time = time.time()
    
    for proc in psutil.process_iter(['pid', 'name', 'username', 'exe', 'create_time']):
        scanned += 1
        try:
            suspicious, reason = is_suspicious_process(proc)
            if suspicious:
                threats.append({
                    'pid': proc.info['pid'],
                    'name': proc.info['name'],
                    'username': proc.info['username'],
                    'exe': proc.info['exe'] or "N/A",
                    'reason': reason,
                    'uptime_sec': int(time.time() - proc.info['create_time']),
                    'timestamp': datetime.now().isoformat()
                })
        except (psutil.NoSuchProcess, psutil.AccessDenied):
            continue
    
    elapsed = time.time() - start_time
    
    return {
        'guard': 'antikeylogger',
        'status': 'warning' if threats else 'ok',
        'timestamp': datetime.now().isoformat(),
        'scanned_processes': scanned,
        'threats_detected': len(threats),
        'threats': threats,
        'scan_duration_sec': round(elapsed, 2),
        'quarantine_required': bool(threats),
        'report': generate_report(threats, scanned, elapsed)
    }

def generate_report(threats: list, scanned: int, elapsed: float) -> str:
    lines = [
        "🛡️ RAPPORT ANTI-KEYLOGGER — Scan de sécurité",
        "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━",
        f"Processus analysés : {scanned}",
        f"Durée du scan     : {elapsed:.2f} secondes",
        f"Menaces détectées : {len(threats)}",
        "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
    ]
    
    if threats:
        lines.append("⚠️  MENACES DÉTECTÉES :")
        for t in threats:
            lines.append(f"   • PID {t['pid']:5d} | {t['name']} | {t['username']} | {t['reason']}")
        lines.append("")
        lines.append("✋ ACTION REQUISE :")
        lines.append("   → Aucun blocage automatique effectué")
        lines.append("   → Vérifiez manuellement les processus suspects")
    else:
        lines.append("✅ Aucun keylogger détecté")
        lines.append("ℹ️  Whitelist active : navigateurs et apps légitimes exclus du scan")
    
    lines.append("━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━")
    return "\n".join(lines)

def run(gui: bool = False) -> dict:
    print("🔍 [antikeylogger] Démarrage du scan anti-keylogger...")
    
    try:
        result = scan_processes()
        print(f"✅ [antikeylogger] Scan terminé — {result['threats_detected']} menace(s) détectée(s)")
        print("\n" + result['report'])
        return result
    except Exception as e:
        error_msg = f"❌ Erreur dans guard_antikeylogger : {str(e)}"
        print(error_msg)
        return {
            'guard': 'antikeylogger',
            'status': 'error',
            'error': str(e),
            'timestamp': datetime.now().isoformat(),
            'report': error_msg
        }

# ============================================================================
# === ⚠️ AJOUT CRITIQUE : start_guard() POUR CORTEX ==========================
# ============================================================================

def start_guard():
    """Point d'entrée pour Kerberos — Surveillance keylogger"""
    print("🔑 [Anti-Keylogger] Surveillance active")
    result = run()
    if result['threats_detected'] > 0:
        print(f"   └─ ⚠️ {result['threats_detected']} menace(s) détectée(s)")
    else:
        print("   └─ ✅ Aucun keylogger détecté")
    return None  # Scan unique, pas de thread

if __name__ == "__main__":
    result = run()
    
    report_path = Path("soins_vibratoires") / f"antikeylogger_{int(time.time())}.json"
    report_path.parent.mkdir(exist_ok=True)
    
    with open(report_path, 'w', encoding='utf-8') as f:
        json.dump(result, f, indent=2, ensure_ascii=False)
    
    print(f"\n📄 Rapport sauvegardé : {report_path}")
    sys.exit(0 if result['status'] == 'ok' else 1)