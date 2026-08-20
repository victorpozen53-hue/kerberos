#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
🧬 Guard YARA — Détection malware par signatures
Copyright (C) 2026 Victor Pozen — GPLv3
"""
import os, sys, json, time, threading
from pathlib import Path
from datetime import datetime
from typing import Dict, List, Optional

try:
    import yara
    YARA_AVAILABLE = True
except ImportError:
    YARA_AVAILABLE = False

YARA_DIR = Path(__file__).parent.parent / "lymph" / "yara"
RULES_DIR = YARA_DIR / "rules"
LOG_FILE = Path(__file__).parent.parent / "logs" / "yara_guard.log"
for d in [YARA_DIR, RULES_DIR, LOG_FILE.parent]:
    d.mkdir(parents=True, exist_ok=True)

ACTIVE_RULES = ["frogs-toxic.yar", "bubble-shield.yar"]

def _log(msg: str, level: str = "INFO"):
    ts = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    line = f"[{ts}] [{level}] {msg}\n"
    try:
        with open(LOG_FILE, "a", encoding="utf-8") as f: f.write(line)
    except: pass

class YaraEngine:
    def __init__(self):
        self.compiled_rules = None
        self.scanned_files = 0
        self.matches_found = 0
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
                except: pass
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
                results = [{"file": str(filepath), "rule": m.rule, "tags": m.tags} for m in matches]
                with self._lock: self.matches_found += len(results)
                return results
        except Exception as e:
            _log(f"️ Erreur scan {filepath}: {e}", "WARN")
        return []

_engine: Optional[YaraEngine] = None
_running = False

def start_guard():
    global _engine, _running
    _log("🧬 [YARA] Démarrage du guard...", "INFO")
    if not YARA_AVAILABLE:
        _log("️ [YARA] Module yara-python non installé", "WARN")
        return None
    _engine = YaraEngine()
    if _engine.load_rules():
        _log("✅ [YARA] Rules chargées — guard actif", "OK")
    _running = True
    return _engine

def stop_guard():
    global _running
    _running = False
    _log("🛑 [YARA] Guard arrêté", "INFO")

if __name__ == "__main__":
    start_guard()
    print("🧬 Guard YARA prêt.")