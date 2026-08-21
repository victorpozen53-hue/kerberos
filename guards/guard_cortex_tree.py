#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
🧠 Guard Cortex Tree — Mémoire de l'arborescence Kerberos
Licence : GPLv3 | Auteur : Victor Pozen
"""
import os
import json
from pathlib import Path
from collections import Counter

STATE_FILE = Path(__file__).parent / ".kerberos_tree_state.json"

def analyze_tree(target_dir: str) -> dict:
    """Analyse l'arbre et retourne un résumé statistique"""
    stats = {"total_files": 0, "extensions": Counter(), "total_size_mb": 0.0}
    target = Path(target_dir)
    
    for root, _, files in os.walk(target):
        if ".git" in root or "__pycache__" in root:
            continue
        for f in files:
            stats["total_files"] += 1
            ext = Path(f).suffix.lower() or "sans_extension"
            stats["extensions"][ext] += 1
            try:
                stats["total_size_mb"] += os.path.getsize(os.path.join(root, f)) / (1024 * 1024)
            except OSError:
                pass
                
    return {
        "total_files": stats["total_files"],
        "total_size_mb": round(stats["total_size_mb"], 2),
        "extensions": dict(stats["extensions"])
    }

def check_anomaly(target_dir: str) -> tuple:
    """Vérifie s'il y a une anomalie majeure par rapport à la dernière fois"""
    current = analyze_tree(target_dir)
    
    if STATE_FILE.exists():
        try:
            with open(STATE_FILE, 'r', encoding='utf-8') as f:
                previous = json.load(f)
            
            diff_files = current["total_files"] - previous.get("total_files", 0)
            if abs(diff_files) > 50:
                return False, f"⚠️ ALERTE CORTEX : Variation de {diff_files} fichiers détectée !"
        except Exception:
            pass

    with open(STATE_FILE, 'w', encoding='utf-8') as f:
        json.dump(current, f, indent=2)
        
    return True, f"✅ Cortex : Arborescence stable ({current['total_files']} fichiers, {current['total_size_mb']} Mo)"
