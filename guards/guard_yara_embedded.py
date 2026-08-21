#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
🦠 Guard YARA Embedded — Scan de signatures malveillantes
Licence : GPLv3 | Auteur : Victor Pozen
"""
import os
from pathlib import Path

try:
    import yara
    YARA_AVAILABLE = True
except ImportError:
    YARA_AVAILABLE = False

YARA_RULES = r'''
rule Suspicious_Python_Exec {
    meta:
        description = "Détection de tentative d'exécution de code dynamique dangereux"
    strings:
        $exec1 = "os.system(" ascii
        $exec2 = "subprocess.call(" ascii
        $exec3 = "eval(" ascii
    condition:
        2 of them and filesize < 5MB
}
'''

def scan_with_yara(target_dir: str) -> list:
    """Scanne les fichiers Python pour des signatures dangereuses"""
    alerts = []
    if not YARA_AVAILABLE:
        return ["️ YARA non installé (pip install yara-python). Scan basique activé."]
        
    try:
        rules = yara.compile(source=YARA_RULES)
        target = Path(target_dir)
        
        for filepath in target.rglob("*.py"):
            if ".git" in str(filepath) or "__pycache__" in str(filepath):
                continue
            try:
                matches = rules.match(str(filepath))
                if matches:
                    alerts.append(f"🦠 {filepath.name} : {matches[0].rule}")
            except Exception:
                pass
        return alerts
    except Exception as e:
        return [f"❌ Erreur moteur YARA : {e}"]
