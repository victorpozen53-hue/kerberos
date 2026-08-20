#!/usr/bin/env python3
# guards/guard_browser_shield.py — ublock YARA (GPLv3)
# Bloque pubs/trackers/malwares dans TOUS les navigateurs
# White hat only • Local pur • Sans extension • Éthique hybride
#
# Copyright (C) 2025–2026 Victor Pozen
# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.

import os
import sys
import time
import threading
import json
import re
from pathlib import Path
import psutil

try:
    import yara
    _HAS_YARA = True
except ImportError:
    _HAS_YARA = False
    print("[⚠️ BROWSER] Module yara-python manquant — guard désactivé")

# === CONFIGURATION ===
BROWSERS = {
    "firefox": {
        "exe": ["firefox.exe"],
        "profiles": Path.home() / "AppData/Roaming/Mozilla/Firefox/Profiles",
        "extensions": "extensions.json",
        "cache": "cache2"
    },
    "chrome": {
        "exe": ["chrome.exe", "msedge.exe", "brave.exe", "vivaldi.exe"],
        "profiles": Path.home() / "AppData/Local/Google/Chrome/User Data",
        "extensions": "Default/Extensions",
        "cache": "Default/Cache"
    }
}

RULES_DIR = Path(__file__).parent.parent / "rules" / "web"
RULES_DIR.mkdir(parents=True, exist_ok=True)

HOSTS_FILE = Path("C:/Windows/System32/drivers/etc/hosts")
HOSTS_BACKUP = Path(__file__).parent.parent / "lymph" / "hosts_backup.txt"

LOG_PATH = Path(__file__).parent.parent / "logs" / "browser_shield.log"
LOG_PATH.parent.mkdir(parents=True, exist_ok=True)

QUARANTINE_DIR = Path(__file__).parent.parent / "soins_vibratoires" / "quarantine_browser"
QUARANTINE_DIR.mkdir(parents=True, exist_ok=True)

# === ÉTAT GLOBAL (thread-safe) ===
_ACTIVE = False
_AUTO_BLOCK = True  # Mode hybride : True = blocage auto trackers, False = manuel uniquement
_RECENT_EVENTS = []
_EVENTS_LOCK = threading.Lock()
_SCAN_LOCK = threading.Lock()
_LAST_SCAN = 0

# === RÈGLES YARA WEB PAR DÉFAUT (création auto si absentes) ===
_DEFAULT_RULES = {
    "trackers.yar": """/*
 * Trackers : Google Analytics, Facebook Pixel, Hotjar...
 */
rule Google_Analytics_Universal {
    meta: k_score = 70
    strings:
        $ga1 = "google-analytics.com/analytics.js" nocase
        $ga2 = "www.google-analytics.com/analytics.js" nocase
        $ga3 = "ga('create'" nocase
    condition: 2 of ($ga*)
}
rule Facebook_Pixel {
    meta: k_score = 75
    strings:
        $fb1 = "connect.facebook.net/en_US/fbevents.js" nocase
        $fb2 = "fbq('init'" nocase
    condition: any of ($fb*)
}
rule Hotjar_Tracking {
    meta: k_score = 65
    strings:
        $hj1 = "static.hotjar.com/c/hotjar-" nocase
        $hj2 = "hj('trigger'" nocase
    condition: any of ($hj*)
}""",
    
    "ads.yar": """/*
 * Publicités : AdSense, Taboola, Outbrain...
 */
rule Google_AdSense {
    meta: k_score = 80
    strings:
        $ads1 = "pagead2.googlesyndication.com/pagead/js/adsbygoogle.js" nocase
        $ads2 = "adsbygoogle.push" nocase
    condition: 2 of ($ads*)
}
rule Taboola_Ads {
    meta: k_score = 75
    strings:
        $tab1 = "cdn.taboola.com/libtrc/" nocase
        $tab2 = "taboola.push" nocase
    condition: any of ($tab*)
}
rule Outbrain_Ads {
    meta: k_score = 75
    strings:
        $out1 = "widgets.outbrain.com/outbrain.js" nocase
        $out2 = "OB_ADV_ID" nocase
    condition: any of ($out*)
}""",
    
    "crypto_miners.yar": """/*
 * Miners cryptos malveillants
 */
rule Coinhive_CryptoMiner {
    meta: k_score = 95
    strings:
        $ch1 = "coinhive.com/lib/coinhive.min.js" nocase
        $ch2 = "CoinHive.Anonymous" nocase
    condition: any of ($ch*)
}
rule CryptoLoot_CryptoMiner {
    meta: k_score = 95
    strings:
        $cl1 = "cryptoloot.pro/lib/miner.min.js" nocase
        $cl2 = "CryptoLoot.Anonymous" nocase
    condition: any of ($cl*)
}""",
    
    "malicious_extensions.yar": """/*
 * Extensions malveillantes : hijackers, adware, keyloggers
 */
rule Browser_Hijacker_Extension {
    meta: k_score = 90
    strings:
        $hijack1 = "chrome_settings_overrides" nocase
        $hijack2 = "homepage_url" nocase
    condition: 2 of ($hijack*)
}
rule Adware_Extension {
    meta: k_score = 85
    strings:
        $adware1 = "content_scripts" nocase
        $adware2 = "matches" nocase
        $adware3 = "*://*/*" nocase
    condition: 3 of ($adware*)
}""",
    
    "malicious_scripts.yar": """/*
 * Scripts malveillants inline
 */
rule Obfuscated_JavaScript {
    meta: k_score = 82
    strings:
        $obf1 = "eval(" nocase
        $obf2 = "Function(" nocase
        $obf3 = "String.fromCharCode" nocase
    condition: 2 of ($obf*)
}
rule DriveBy_Download_Script {
    meta: k_score = 92
    strings:
        $drive1 = "iframe" nocase
        $drive2 = "src=" nocase
        $drive3 = ".exe" nocase
    condition: 3 of ($drive*)
}"""
}

def _init_rules():
    """Crée les règles YARA par défaut si absentes"""
    created = 0
    for name, content in _DEFAULT_RULES.items():
        rule_file = RULES_DIR / name
        if not rule_file.exists():
            rule_file.write_text(content, encoding="utf-8")
            created += 1
    if created:
        _log(f"✅ {created} règle(s) YARA web créée(s) dans {RULES_DIR}")

def _log(msg: str):
    """Log thread-safe avec timestamp"""
    timestamp = time.strftime("%Y-%m-%d %H:%M:%S")
    with open(LOG_PATH, "a", encoding="utf-8") as f:
        f.write(f"[BROWSER] {timestamp} | {msg}\n")
    
    # Stocker les événements récents pour l'UI
    with _EVENTS_LOCK:
        _RECENT_EVENTS.append({"time": timestamp, "msg": msg})
        if len(_RECENT_EVENTS) > 50:  # Garder max 50 événements
            _RECENT_EVENTS.pop(0)

def _is_browser_running() -> bool:
    """Vérifie si un navigateur est actif"""
    for proc in psutil.process_iter(['name']):
        try:
            name = proc.info['name'].lower()
            for config in BROWSERS.values():
                if any(exe.lower() in name for exe in config['exe']):
                    return True
        except (psutil.NoSuchProcess, psutil.AccessDenied):
            continue
    return False

def _scan_extensions() -> list:
    """Scan les extensions installées dans tous les navigateurs"""
    threats = []
    
    for browser_name, config in BROWSERS.items():
        profiles_dir = config['profiles']
        if not profiles_dir.exists():
            continue
        
        # Firefox : plusieurs profils possibles
        if browser_name == "firefox":
            for profile_dir in profiles_dir.glob("*"):
                if profile_dir.is_dir():
                    ext_file = profile_dir / config['extensions']
                    if ext_file.exists():
                        threats.extend(_scan_extension_file(ext_file, browser_name))
        
        # Chrome/Edge/Brave : un seul profil principal
        else:
            ext_path = profiles_dir / config['extensions']
            if ext_path.exists():
                for ext_dir in ext_path.glob("*"):
                    if ext_dir.is_dir():
                        manifest = ext_dir / "manifest.json"
                        if manifest.exists():
                            threats.extend(_scan_extension_manifest(manifest, browser_name))
    
    return threats

def _scan_extension_file(ext_file: Path, browser_name: str) -> list:
    """Scan le fichier extensions.json de Firefox"""
    try:
        data = json.loads(ext_file.read_text(encoding="utf-8"))
        threats = []
        for ext_id, ext_info in data.get("addons", {}).items():
            name = ext_info.get("defaultLocale", {}).get("name", "unknown").lower()
            if any(kw in name for kw in ("adware", "toolbar", "coupon", "deal", "savings")):
                threats.append({
                    "type": "extension",
                    "browser": browser_name,
                    "name": ext_info.get("defaultLocale", {}).get("name", "unknown"),
                    "id": ext_id,
                    "k_score": 80,
                    "action": "detection_only"  # Jamais de quarantaine auto
                })
                _log(f"Extension suspecte détectée [{browser_name}] : {ext_info.get('defaultLocale', {}).get('name', 'unknown')}")
        return threats
    except Exception as e:
        _log(f"Erreur scan extension {ext_file}: {e}")
        return []

def _scan_extension_manifest(manifest: Path, browser_name: str) -> list:
    """Scan le manifest.json d'une extension Chrome/Edge"""
    try:
        data = json.loads(manifest.read_text(encoding="utf-8"))
        name = data.get("name", "unknown")
        threats = []
        
        # Détection via YARA
        manifest_text = json.dumps(data)
        for rule_file in RULES_DIR.glob("malicious_extensions.yar"):
            try:
                rules = yara.compile(filepath=str(rule_file))
                matches = rules.match(data=manifest_text.encode('utf-8'))
                for match in matches:
                    threats.append({
                        "type": "extension",
                        "browser": browser_name,
                        "name": name,
                        "manifest": str(manifest),
                        "rule": match.rule,
                        "k_score": match.meta.get('k_score', 85),
                        "action": "detection_only"
                    })
                    _log(f"Extension malveillante détectée [{browser_name}] : {name} (règle: {match.rule})")
            except Exception as e:
                _log(f"Erreur YARA sur {manifest}: {e}")
        
        return threats
    except Exception as e:
        _log(f"Erreur scan manifest {manifest}: {e}")
        return []

def _block_domains(domains: list) -> bool:
    """Bloque des domaines via le fichier hosts (méthode la plus légère)"""
    if not _AUTO_BLOCK:
        _log(f"Blocage auto désactivé — {len(domains)} domaine(s) ignorés")
        return False
    
    try:
        # Backup du hosts original (une seule fois)
        if not HOSTS_BACKUP.exists():
            HOSTS_BACKUP.parent.mkdir(parents=True, exist_ok=True)
            if HOSTS_FILE.exists():
                HOSTS_BACKUP.write_text(HOSTS_FILE.read_text(encoding="utf-8"), encoding="utf-8")
                _log(f"Backup hosts créé : {HOSTS_BACKUP}")
        
        # Lire le hosts actuel
        hosts_content = HOSTS_FILE.read_text(encoding="utf-8") if HOSTS_FILE.exists() else ""
        
        # Ajouter les domaines bloqués (si absents)
        added = []
        for domain in domains:
            entry = f"\n127.0.0.1 {domain}  # Bloqué par Kerberos Browser Shield"
            if entry not in hosts_content:
                hosts_content += entry
                added.append(domain)
        
        if added:
            # Écrire le nouveau hosts (nécessite droits admin)
            try:
                HOSTS_FILE.write_text(hosts_content, encoding="utf-8")
                _log(f"✅ {len(added)} domaine(s) bloqué(s) : {', '.join(added[:3])}{'...' if len(added) > 3 else ''}")
                return True
            except PermissionError:
                _log("❌ Erreur : droits admin requis pour modifier hosts (blocage auto désactivé)")
                return False
        
        return False
    except Exception as e:
        _log(f"❌ Erreur blocage domains : {e}")
        return False

def _scan_running_browsers() -> list:
    """Scan les processus navigateurs actifs pour scripts malveillants"""
    threats = []
    
    for proc in psutil.process_iter(['pid', 'name', 'cmdline']):
        try:
            name = proc.info['name'].lower()
            cmdline = " ".join(proc.info['cmdline']).lower() if proc.info['cmdline'] else ""
            
            # Vérifier si c'est un navigateur
            is_browser = False
            browser_name = "unknown"
            for bname, config in BROWSERS.items():
                if any(exe.lower() in name for exe in config['exe']):
                    is_browser = True
                    browser_name = bname
                    break
            
            if is_browser and cmdline:
                # Scan du cmdline avec YARA
                for rule_file in RULES_DIR.glob("*.yar"):
                    try:
                        rules = yara.compile(filepath=str(rule_file))
                        matches = rules.match(data=cmdline.encode('utf-8'))
                        for match in matches:
                            k_score = match.meta.get('k_score', 70)
                            if k_score >= 70:  # Seuil significatif
                                threats.append({
                                    "type": "process",
                                    "pid": proc.info['pid'],
                                    "browser": browser_name,
                                    "rule": match.rule,
                                    "k_score": k_score
                                })
                                _log(f" menace détectée [{browser_name} PID {proc.info['pid']}] : {match.rule} (score={k_score})")
                    except Exception as e:
                        _log(f"Erreur YARA sur processus {proc.info['pid']}: {e}")
        except (psutil.NoSuchProcess, psutil.AccessDenied):
            continue
        except Exception as e:
            _log(f"Erreur scan processus : {e}")
    
    return threats

def _background_watcher():
    """Thread silencieux — scan toutes les 2 minutes"""
    global _LAST_SCAN, _ACTIVE
    
    while _ACTIVE:
        now = time.time()
        if now - _LAST_SCAN >= 120:  # 2 minutes
            with _SCAN_LOCK:
                _LAST_SCAN = now
                
                # 🔒 BLOCAGE AUTO DES TRACKERS CONNU (mode hybride)
                if _AUTO_BLOCK:
                    common_trackers = [
                        "google-analytics.com", "googletagmanager.com",
                        "connect.facebook.net", "static.hotjar.com",
                        "pagead2.googlesyndication.com", "cdn.taboola.com",
                        "widgets.outbrain.com", "adservice.google.com"
                    ]
                    _block_domains(common_trackers)
                
                # Scan extensions (détection uniquement — pas de quarantaine auto)
                ext_threats = _scan_extensions()
                if ext_threats:
                    _log(f"⚠️ {len(ext_threats)} extension(s) suspecte(s) détectée(s) — Quarantaine manuelle requise")
                
                # Scan processus (détection miners/cryptojacking)
                proc_threats = _scan_running_browsers()
                if proc_threats:
                    high_risk = [t for t in proc_threats if t['k_score'] >= 90]
                    if high_risk:
                        _log(f"🚨 {len(high_risk)} menace(s) CRITIQUE(S) détectée(s) (score ≥ 90)")
        
        time.sleep(30)  # Vérifie toutes les 30s si besoin de scanner

# === FONCTIONS PUBLIQUES POUR L'UI ===
def set_auto_block(enabled: bool):
    """Active/désactive le blocage automatique (appelé par l'UI)"""
    global _AUTO_BLOCK
    _AUTO_BLOCK = enabled
    mode = "activé" if enabled else "désactivé"
    _log(f"🔄 Mode blocage auto {mode} par l'utilisateur")
    return {"status": "success", "auto_block": enabled}

def get_recent_events(limit: int = 20) -> list:
    """Retourne les événements récents pour l'UI (thread-safe)"""
    with _EVENTS_LOCK:
        return _RECENT_EVENTS[-limit:]

def get_stats() -> dict:
    """Statistiques pour l'UI"""
    with _EVENTS_LOCK:
        total_events = len(_RECENT_EVENTS)
        last_24h = [e for e in _RECENT_EVENTS if "bloqué" in e['msg'].lower() or "détection" in e['msg'].lower()]
    
    return {
        "auto_block_enabled": _AUTO_BLOCK,
        "total_events": total_events,
        "events_last_24h": len(last_24h),
        "last_scan": time.strftime("%H:%M:%S", time.localtime(_LAST_SCAN)) if _LAST_SCAN else "jamais"
    }

# === POINT D'ENTRÉE KERBEROS ===
def start_guard(auto_block: bool = True):
    """
    Lancé automatiquement par le Cortex.
    Mode hybride : blocage auto des trackers + détection silencieuse des extensions.
    """
    global _ACTIVE, _AUTO_BLOCK
    
    if not _HAS_YARA:
        print("[🛡️ BROWSER] Désactivé — module yara-python manquant")
        return None
    
    _init_rules()
    _ACTIVE = True
    _AUTO_BLOCK = auto_block
    
    mode_str = "✅ AUTO (trackers)" if auto_block else "⚠️ MANUEL (détection uniquement)"
    print(f"[🛡️ BROWSER SHIELD] Activé — ublock YARA hybride {mode_str}")
    print("   • Navigateurs : Firefox, Chrome, Edge, Brave, Vivaldi")
    print("   • Blocage auto : trackers/publicités (hosts file)")
    print("   • Détection : extensions malveillantes, miners, scripts")
    print("   • Quarantaine : MANUELLE uniquement (respect utilisateur)")
    
    watcher = threading.Thread(
        target=_background_watcher,
        daemon=True,
        name="kerberos_browser_shield"
    )
    watcher.start()
    return watcher

def run():
    """
    Appelé via le bouton 'Scanner les navigateurs' dans l'UI.
    Retourne un rapport détaillé SANS action destructive.
    """
    _init_rules()
    
    _log("🔍 Scan manuel des navigateurs déclenché par l'utilisateur")
    
    # Scan extensions
    ext_threats = _scan_extensions()
    
    # Scan processus
    proc_threats = _scan_running_browsers()
    
    # Compter les blocages récents
    blocked_count = sum(1 for e in _RECENT_EVENTS if "bloqué" in e['msg'].lower())
    
    # Générer le rapport
    report_lines = [
        "🛡️ RAPPORT ublock YARA — Scan manuel",
        "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━",
        f"Extensions analysées : {len(ext_threats)} menace(s) détectée(s)",
        f"Processus scannés    : {len(proc_threats)} menace(s) détectée(s)",
        f"Trackers bloqués     : {blocked_count} (depuis le dernier démarrage)",
        "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━",
        "✅ Aucune suppression automatique effectuée.",
        "✅ Les trackers sont bloqués via le fichier hosts (réversible).",
        "✋ Les extensions suspectes nécessitent VOTRE confirmation pour quarantaine.",
        "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
    ]
    
    # Ajouter détails menaces
    if ext_threats:
        report_lines.append("\n⚠️  Extensions suspectes :")
        for t in ext_threats[:5]:  # Max 5 dans le rapport
            report_lines.append(f"  • [{t['browser']}] {t['name']} (score={t['k_score']})")
        if len(ext_threats) > 5:
            report_lines.append(f"  ... et {len(ext_threats)-5} autre(s)")
    
    if proc_threats:
        report_lines.append("\n🚨 Processus malveillants :")
        for t in proc_threats[:5]:
            report_lines.append(f"  • PID {t['pid']} ({t['browser']}) — {t['rule']} (score={t['k_score']})")
        if len(proc_threats) > 5:
            report_lines.append(f"  ... et {len(proc_threats)-5} autre(s)")
    
    full_report = "\n".join(report_lines)
    _log(f"Scan manuel terminé — {len(ext_threats)} extensions + {len(proc_threats)} processus")
    
    return {
        "guard": "browser_shield",
        "status": "scan_complete",
        "extensions_threats": ext_threats,
        "process_threats": proc_threats,
        "blocked_count": blocked_count,
        "report": full_report,
        "auto_block_enabled": _AUTO_BLOCK
    }

if __name__ == "__main__":
    print("[🛡️ BROWSER SHIELD] Mode standalone : scan unique des navigateurs")
    result = run()
    print(result["report"])
    print(f"\n💡 Conseil : Activez le guard via Cortex pour une protection continue.")