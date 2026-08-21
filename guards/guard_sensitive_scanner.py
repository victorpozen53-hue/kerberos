#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
🔍 Guard Sensitive Scanner — Détection de fuites de données
Licence : GPLv3 | Auteur : Victor Pozen
"""
import os
import re
from pathlib import Path

WATCHED_EXTENSIONS = {".json", ".csv", ".txt", ".env", ".ini", ".html"}
SENSITIVE_PATTERNS = [
    re.compile(r"(?i)(password|passwd|pwd|api_key|secret|token)\s*[:=]\s*['"][^'"]+['"]"),
    re.compile(r"(?i)(lieux_sacres|private|confidential)"),
]

def scan_for_sensitive_files(target_dir: str) -> list:
    """Retourne une liste de fichiers suspects avec la raison"""
    flagged_files = []
    target = Path(target_dir)
    
    for root, _, files in os.walk(target):
        if ".git" in root or "__pycache__" in root:
            continue
            
        for f in files:
            ext = Path(f).suffix.lower()
            if ext in WATCHED_EXTENSIONS:
                filepath = Path(root) / f
                reasons = []
                
                if any(word in f.lower() for word in ["password", "secret", "private", "sacres"]):
                    reasons.append("Nom de fichier sensible")
                    
                if ext in {".json", ".env", ".txt"}:
                    try:
                        content = filepath.read_text(encoding='utf-8', errors='ignore')[:5000]
                        for pattern in SENSITIVE_PATTERNS:
                            if pattern.search(content):
                                reasons.append("Motif sensible détecté dans le contenu")
                                break
                    except Exception:
                        pass
                
                if reasons:
                    flagged_files.append({
                        "path": str(filepath.relative_to(target)),
                        "reasons": ", ".join(reasons),
                        "approved": False
                    })
                    
    return flagged_files
