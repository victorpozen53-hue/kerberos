#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
🧬 Guard YARA — Détection malware par signatures
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
- Règles : frogs-toxic.yar, bubble-shield.yar
- Scan fichiers et processus
- Intégration Kerberos complète
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
Copyright (C) 2025 Victor Pozen — GPLv3
"""
# ============================================================================
#  KERBEROS ULTIMATE v4.2 — Guard YARA
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
import json
import time
import threading
from pathlib import Path
from datetime import datetime
from typing import Dict, List, Optional

try:
    import yara
    YARA_AVAILABLE = True
except ImportError:
    YARA_AVAILABLE = False

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

# ============================================================================
# === CONFIGURATION ==========================================================
# ============================================================================
YARA_DIR = Path(__file__).parent.parent / "lymph" / "yara"
RULES_DIR = YARA_DIR / "rules"
LOG_FILE = Path(__file__).parent.parent / "logs" / "yara_guard.log"

for d in [YARA_DIR, RULES_DIR, LOG_FILE.parent]:
    d.mkdir(parents=True, exist_ok=True)

ACTIVE_RULES = ["frogs-toxic.yar", "bubble-shield.yar"]

SCAN_EXTENSIONS = {".exe", ".dll", ".sys", ".bat", ".cmd", ".ps1", ".vbs", ".js", ".msi", ".scr"}

# ============================================================================
# === LOGGING ================================================================
# ============================================================================
def _log(msg: str, level: str = "INFO"):
    ts = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    line = f"[{ts}] [{level}] {msg}\n"
    try:
        with open(LOG_FILE, "a", encoding="utf-8") as f:
            f.write(line)
    except:
        pass
    if __name__ == "__main__":
        print(line.strip())

# ============================================================================
# === RÈGLES EMBARQUÉES (fallback) ===========================================
# ============================================================================
FROGS_TOXIC_RULES = r'''
rule Frogs_Toxic_PE_Signature {
    meta:
        description = "Détection exécutable type Frogs-Toxic"
        author = "Victor Pozen — Kerberos Ultimate"
        license = "GPLv3"
        severity = "high"
    strings:
        $mz_header = { 4D 5A }
        $frog_str1 = "frogs_payload" ascii wide
        $frog_str2 = "toxic_inject" ascii wide
        $inject_api1 = "VirtualAllocEx" ascii
        $inject_api2 = "WriteProcessMemory" ascii
    condition:
        $mz_header at 0 and
        (2 of ($frog_str*) or 2 of ($inject_api*)) and
        filesize < 10MB
}
'''

BUBBLE_SHIELD_RULES = r'''
rule Bubble_Shield_Memory_Injection {
    meta:
        description = "Détection injection mémoire"
        author = "Victor Pozen — Kerberos Ultimate"
        license = "GPLv3"
        severity = "critical"
    strings:
        $inject1 = "VirtualAllocEx" ascii
        $inject2 = "WriteProcessMemory" ascii
        $inject3 = "CreateRemoteThread" ascii
        $target_proc1 = "lsass.exe" ascii wide
        $shellcode_pattern = { 60 68 ?? ?? ?? ?? E8 ?? ?? ?? ?? 61 }
    condition:
        (2 of ($inject*) and 1 of ($target_proc*)) or
        $shellcode_pattern
}
'''

# ============================================================================
# === YARA ENGINE ============================================================
# ============================================================================
class YaraEngine:
    def __init__(self):
        self.compiled_rules = None
        self.scanned_files = 0
        self.matches_found = 0
        self.last_scan = None
        self._lock = threading.Lock()
    
    def load_rules(self) -> bool:
        if not YARA_AVAILABLE:
            _log("❌ YARA non disponible", "ERROR")
            return False
        
        rules_source = {}
        for rule_file in ACTIVE_RULES:
            rule_path = RULES_DIR / rule_file
            if rule_path.exists():
                try:
                    rules_source[rule_file] = rule_path.read_text(encoding="utf-8")
                    _log(f"✅ Règle chargée : {rule_file}", "OK")
                except Exception as e:
                    _log(f"⚠️ Erreur lecture {rule_file}: {e}", "WARN")
            else:
                if rule_file == "frogs-toxic.yar":
                    rules_source[rule_file] = FROGS_TOXIC_RULES
                elif rule_file == "bubble-shield.yar":
                    rules_source[rule_file] = BUBBLE_SHIELD_RULES
                _log(f"⚠️ {rule_file} absent — règles embarquées", "WARN")
        
        if not rules_source:
            _log("❌ Aucune règle YARA disponible", "ERROR")
            return False
        
        try:
            self.compiled_rules = yara.compile(sources=rules_source)
            _log(f"✅ {len(rules_source)} règle(s) compilée(s)", "OK")
            return True
        except Exception as e:
            _log(f"❌ Erreur compilation YARA : {e}", "ERROR")
            return False
    
    def scan_file(self, filepath: Path) -> List[Dict]:
        if not self.compiled_rules or not YARA_AVAILABLE or not filepath.exists():
            return []
        
        try:
            matches = self.compiled_rules.match(str(filepath))
            if matches:
                results = []
                for match in matches:
                    result = {
                        "file": str(filepath),
                        "rule": match.rule,
                        "tags": match.tags,
                        "strings": [{"name": s.identifier, "value": s.plaintext or s.hex_data} for s in match.strings],
                        "timestamp": datetime.now().isoformat(),
                    }
                    results.append(result)
                with self._lock:
                    self.matches_found += len(results)
                return results
        except Exception as e:
            _log(f"⚠️ Erreur scan {filepath}: {e}", "WARN")
        
        with self._lock:
            self.scanned_files += 1
        return []
    
    def get_stats(self) -> Dict:
        with self._lock:
            return {
                "scanned_files": self.scanned_files,
                "matches_found": self.matches_found,
                "last_scan": self.last_scan,
                "yara_available": YARA_AVAILABLE,
            }

# ============================================================================
# === GUARD PRINCIPAL ========================================================
# ============================================================================
_engine: Optional[YaraEngine] = None
_running = False

def start_guard():
    global _engine, _running
    _log("🧬 [YARA] Démarrage du guard...", "INFO")
    
    if not YARA_AVAILABLE:
        _log("⚠️ [YARA] Module yara-python non installé", "WARN")
        _publish_metric(0.1)
        return None
    
    _engine = YaraEngine()
    if _engine.load_rules():
        _log("✅ [YARA] Rules chargées — guard actif", "OK")
        _publish_metric(0.2)
    else:
        _log("❌ [YARA] Échec chargement règles", "ERROR")
        _publish_metric(0.0)
    
    _running = True
    return _engine

def get_stats() -> Dict:
    stats = {
        "guard_name": "YARA Scanner",
        "status": "active" if _running else "inactive",
        "yara_available": YARA_AVAILABLE,
        "rules_count": len(ACTIVE_RULES),
    }
    if _engine:
        stats.update(_engine.get_stats())
    return stats

def run(scan_path_arg: str = None) -> Dict:
    print("""
╔════════════════════════════════════════════════════════════╗
║  🧬 KERBEROS YARA GUARD — Détection malware              ║
║  Règles : frogs-toxic.yar, bubble-shield.yar              ║
║  Licence : GPLv3 — Victor Pozen                           ║
╚════════════════════════════════════════════════════════════╝
    """)
    
    global _engine
    if not YARA_AVAILABLE:
        print("❌ Module yara-python non installé")
        return {"status": "error", "message": "YARA non disponible"}
    
    _engine = YaraEngine()
    if not _engine.load_rules():
        print("❌ Échec chargement des règles")
        return {"status": "error", "message": "Rules non chargées"}
    
    target = scan_path_arg or "."
    print(f"\n🔍 Scan de : {target}")
    
    p = Path(target)
    if p.is_file():
        matches = _engine.scan_file(p)
    else:
        matches = []
        for f in p.rglob("*"):
            if f.is_file() and f.suffix.lower() in SCAN_EXTENSIONS:
                matches.extend(_engine.scan_file(f))
    
    print(f"\n📊 RÉSULTATS : {len(matches)} matches")
    for m in matches[:5]:
        print(f"   • {m['rule']} → {m['file']}")
    
    return {"status": "success", "matches": matches, "stats": _engine.get_stats()}

def stop_guard():
    global _running
    _running = False
    _publish_metric(0.0)
    _log("🛑 [YARA] Guard arrêté", "INFO")

if __name__ == "__main__":
    result = run()
    sys.exit(0 if result.get("status") == "success" else 1)