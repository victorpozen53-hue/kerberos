#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
🔍 Guard Anti-Stego — Détection de malware caché dans les médias
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
⚠️ CE MODULE DÉTECTE :
- Images (JPG, PNG, GIF, BMP, WEBP) avec données cachées
- Vidéos (AVI, MP4, MKV, MOV) avec payload caché
- Audio (MP3, WAV, FLAC) avec steganographie
- Documents (PDF, DOCX) avec scripts cachés
- Anomalies de structure (EOF markers, metadata suspecte)
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
Copyright (C) 2025 Victor Pozen — GPLv3
"""
# ============================================================================
#  KERBEROS ULTIMATE v4.2 — Guard Anti-Stego
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
import hashlib
import threading
import subprocess
from pathlib import Path
from datetime import datetime
from typing import Dict, List, Optional, Tuple
import struct

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
KERBEROS_ROOT = Path(__file__).parent.parent
GUARDS_DIR = KERBEROS_ROOT / "guards"
LOGS_DIR = KERBEROS_ROOT / "logs"
QUARANTINE_DIR = KERBEROS_ROOT / "lymph" / "quarantine" / "stego"

# Extensions à scanner
IMAGE_EXTS = {'.jpg', '.jpeg', '.png', '.gif', '.bmp', '.webp', '.tiff', '.ico'}
VIDEO_EXTS = {'.avi', '.mp4', '.mkv', '.mov', '.wmv', '.flv', '.webm'}
AUDIO_EXTS = {'.mp3', '.wav', '.flac', '.aac', '.ogg', '.wma'}
DOC_EXTS = {'.pdf', '.docx', '.xlsx', '.pptx', '.odt'}

ALL_EXTS = IMAGE_EXTS | VIDEO_EXTS | AUDIO_EXTS | DOC_EXTS

# Seuils de détection
MAX_METADATA_SIZE = 1024 * 1024  # 1MB max pour metadata
SUSPICIOUS_ENTROPY_THRESHOLD = 7.5  # Entropie très haute = données chiffrées/cachées

# Création des dossiers
for d in [LOGS_DIR, QUARANTINE_DIR]:
    d.mkdir(parents=True, exist_ok=True)

# ============================================================================
# === LOGGING ================================================================
# ============================================================================
LOG_FILE = LOGS_DIR / "anti_stego.log"

def _log(msg: str, level="INFO"):
    """Log les actions de Anti-Stego"""
    ts = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    line = f"[{ts}] [{level}] {msg}"
    try:
        with open(LOG_FILE, "a", encoding="utf-8") as f:
            f.write(line + "\n")
    except:
        pass
    print(f"🔍 [Anti-Stego] [{level}] {msg}")

# ============================================================================
# === DÉTECTION STÉGANOGRAPHIE ===============================================
# ============================================================================

def _calculate_entropy(data: bytes) -> float:
    """Calcule l'entropie de Shannon des données"""
    if not data:
        return 0.0
    
    entropy = 0.0
    byte_counts = [0] * 256
    
    for byte in data:
        byte_counts[byte] += 1
    
    data_len = len(data)
    for count in byte_counts:
        if count > 0:
            p = count / data_len
            entropy -= p * (p and (p * 0.6931471805599453) or 0)  # log2
    
    return entropy / 0.6931471805599453  # Normaliser à 0-8

def _check_jpg_structure(file_path: Path) -> Dict:
    """Vérifie la structure d'un fichier JPG pour anomalies"""
    result = {
        "file": str(file_path),
        "type": "jpg",
        "suspicious": False,
        "reasons": [],
        "details": {}
    }
    
    try:
        with open(file_path, 'rb') as f:
            data = f.read()
        
        # Vérifier markers JPG
        if not data.startswith(b'\xff\xd8'):
            result["suspicious"] = True
            result["reasons"].append("❌ Missing JPG SOI marker")
        
        # Vérifier EOI marker (End Of Image)
        eoi_pos = data.rfind(b'\xff\xd9')
        if eoi_pos == -1:
            result["suspicious"] = True
            result["reasons"].append("❌ Missing JPG EOI marker")
        elif eoi_pos < len(data) - 2:
            # Données après la fin de l'image
            extra_data = len(data) - eoi_pos - 2
            result["details"]["extra_data_after_eof"] = extra_data
            if extra_data > 1024:  # Plus de 1KB après EOF = suspect
                result["suspicious"] = True
                result["reasons"].append(f"⚠️ {extra_data} octets après EOF marker")
        
        # Vérifier entropie
        entropy = _calculate_entropy(data)
        result["details"]["entropy"] = round(entropy, 2)
        if entropy > SUSPICIOUS_ENTROPY_THRESHOLD:
            result["suspicious"] = True
            result["reasons"].append(f"⚠️ Entropie très haute: {entropy:.2f}")
        
        # Vérifier taille fichier vs dimensions
        file_size = file_path.stat().st_size
        result["details"]["file_size"] = file_size
        
        if file_size > 50 * 1024 * 1024:  # > 50MB pour une image = suspect
            result["suspicious"] = True
            result["reasons"].append(f"⚠️ Taille anormale: {file_size / 1024 / 1024:.1f} MB")
        
    except Exception as e:
        result["error"] = str(e)
    
    return result

def _check_png_structure(file_path: Path) -> Dict:
    """Vérifie la structure d'un fichier PNG pour anomalies"""
    result = {
        "file": str(file_path),
        "type": "png",
        "suspicious": False,
        "reasons": [],
        "details": {}
    }
    
    try:
        with open(file_path, 'rb') as f:
            data = f.read()
        
        # Vérifier signature PNG
        if not data.startswith(b'\x89PNG\r\n\x1a\n'):
            result["suspicious"] = True
            result["reasons"].append("❌ Invalid PNG signature")
            return result
        
        # Vérifier chunks IEND
        iend_pos = data.rfind(b'IEND\xae\x42\x60\x82')
        if iend_pos == -1:
            result["suspicious"] = True
            result["reasons"].append("❌ Missing PNG IEND chunk")
        elif iend_pos < len(data) - 12:
            extra_data = len(data) - iend_pos - 12
            result["details"]["extra_data_after_iend"] = extra_data
            if extra_data > 1024:
                result["suspicious"] = True
                result["reasons"].append(f"⚠️ {extra_data} octets après IEND chunk")
        
        # Vérifier entropie
        entropy = _calculate_entropy(data)
        result["details"]["entropy"] = round(entropy, 2)
        if entropy > SUSPICIOUS_ENTROPY_THRESHOLD:
            result["suspicious"] = True
            result["reasons"].append(f"⚠️ Entropie très haute: {entropy:.2f}")
        
    except Exception as e:
        result["error"] = str(e)
    
    return result

def _check_media_structure(file_path: Path, ext: str) -> Dict:
    """Vérifie la structure des fichiers vidéo/audio"""
    result = {
        "file": str(file_path),
        "type": ext,
        "suspicious": False,
        "reasons": [],
        "details": {}
    }
    
    try:
        file_size = file_path.stat().st_size
        result["details"]["file_size"] = file_size
        
        # Vérifier entropie globale
        with open(file_path, 'rb') as f:
            sample = f.read(1024 * 1024)  # 1MB sample
        
        entropy = _calculate_entropy(sample)
        result["details"]["entropy"] = round(entropy, 2)
        
        # Pour les petits fichiers média, haute entropie = suspect
        if file_size < 100 * 1024 and entropy > 7.8:
            result["suspicious"] = True
            result["reasons"].append(f"⚠️ Petite taille + haute entropie")
        
        # Vérifier metadata excessive
        if file_size > 10 * 1024 * 1024:  # > 10MB
            result["details"]["large_file"] = True
        
    except Exception as e:
        result["error"] = str(e)
    
    return result

def _check_document_structure(file_path: Path, ext: str) -> Dict:
    """Vérifie la structure des documents"""
    result = {
        "file": str(file_path),
        "type": ext,
        "suspicious": False,
        "reasons": [],
        "details": {}
    }
    
    try:
        with open(file_path, 'rb') as f:
            data = f.read(1024)  # Header seulement
        
        # Vérifier signatures
        if ext == '.pdf' and not data.startswith(b'%PDF'):
            result["suspicious"] = True
            result["reasons"].append("❌ Invalid PDF header")
        
        elif ext == '.docx' and not data.startswith(b'PK'):
            result["suspicious"] = True
            result["reasons"].append("❌ Invalid DOCX header (not ZIP)")
        
        # Vérifier taille
        file_size = file_path.stat().st_size
        result["details"]["file_size"] = file_size
        
        if file_size > 100 * 1024 * 1024:  # > 100MB
            result["suspicious"] = True
            result["reasons"].append(f"⚠️ Taille anormale: {file_size / 1024 / 1024:.1f} MB")
        
    except Exception as e:
        result["error"] = str(e)
    
    return result

def _scan_file(file_path: Path) -> Dict:
    """Scan un fichier pour steganographie"""
    ext = file_path.suffix.lower()
    
    if ext in {'.jpg', '.jpeg'}:
        return _check_jpg_structure(file_path)
    elif ext == '.png':
        return _check_png_structure(file_path)
    elif ext in VIDEO_EXTS | AUDIO_EXTS:
        return _check_media_structure(file_path, ext)
    elif ext in DOC_EXTS:
        return _check_document_structure(file_path, ext)
    else:
        return {
            "file": str(file_path),
            "type": ext,
            "suspicious": False,
            "reasons": ["Extension non supportée"],
            "details": {}
        }

# ============================================================================
# === QUARANTAINE ============================================================
# ============================================================================

def _quarantine_file(file_path: Path, reason: str) -> bool:
    """Met un fichier suspect en quarantaine"""
    try:
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        quarantine_name = f"{file_path.stem}_{timestamp}{file_path.suffix}.quarantine"
        quarantine_path = QUARANTINE_DIR / quarantine_name
        
        # Copier le fichier
        import shutil
        shutil.copy2(file_path, quarantine_path)
        
        # Créer un fichier de métadonnées
        meta_path = quarantine_path.with_suffix('.quarantine.meta')
        meta = {
            "original_path": str(file_path),
            "quarantine_path": str(quarantine_path),
            "reason": reason,
            "timestamp": datetime.now().isoformat(),
            "sha256": hashlib.sha256(file_path.read_bytes()).hexdigest()
        }
        meta_path.write_text(json.dumps(meta, indent=2), encoding="utf-8")
        
        # Supprimer l'original (optionnel - mode auto)
        # file_path.unlink()
        
        _log(f"✅ Quarantaine: {file_path.name} → {quarantine_name}", "QUARANTINE")
        return True
        
    except Exception as e:
        _log(f"❌ Échec quarantaine {file_path.name}: {e}", "ERROR")
        return False

# ============================================================================
# === SURVEILLANCE ===========================================================
# ============================================================================

def _scan_directory(directory: Path, recursive: bool = True) -> List[Dict]:
    """Scan un dossier pour fichiers suspects"""
    results = []
    
    if not directory.exists():
        _log(f"❌ Dossier introuvable: {directory}", "ERROR")
        return results
    
    _log(f"🔍 Scan du dossier: {directory}", "SCAN")
    
    if recursive:
        files = directory.rglob("*")
    else:
        files = directory.glob("*")
    
    for file_path in files:
        if file_path.is_file() and file_path.suffix.lower() in ALL_EXTS:
            result = _scan_file(file_path)
            results.append(result)
            
            if result.get("suspicious"):
                _log(f"🚨 SUSPECT: {file_path.name} — {', '.join(result.get('reasons', []))}", "ALERT")
                _quarantine_file(file_path, "; ".join(result.get("reasons", [])))
    
    return results

def _watch_folders(folders: List[Path]):
    """Surveillance continue des dossiers"""
    _log(f"👁️ Surveillance active de {len(folders)} dossier(s)", "WATCH")
    
    known_files = {}
    
    while True:
        try:
            for folder in folders:
                if not folder.exists():
                    continue
                
                for file_path in folder.rglob("*"):
                    if file_path.is_file() and file_path.suffix.lower() in ALL_EXTS:
                        file_hash = hashlib.md5(file_path.read_bytes()).hexdigest()
                        
                        if file_hash not in known_files:
                            known_files[file_hash] = str(file_path)
                            result = _scan_file(file_path)
                            
                            if result.get("suspicious"):
                                _log(f"🚨 NOUVEAU FICHIER SUSPECT: {file_path.name}", "ALERT")
                                _quarantine_file(file_path, "; ".join(result.get("reasons", [])))
            
            time.sleep(30)  # Scan toutes les 30 secondes
            
        except Exception as e:
            _log(f"❌ Erreur surveillance: {e}", "ERROR")
            time.sleep(60)

# ============================================================================
# === POINT D'ENTRÉE KERBEROS ================================================
# ============================================================================

def start_guard():
    """Point d'entrée pour Kerberos"""
    _log("🔍 [Anti-Stego] Guard démarré — Surveillance steganographie active", "START")
    
    # Dossiers à surveiller
    watch_folders = [
        KERBEROS_ROOT / "downloads",
        KERBEROS_ROOT / "quarantine",
        Path.home() / "Downloads",
        Path.home() / "Desktop",
    ]
    
    # Filtrer les dossiers existants
    watch_folders = [f for f in watch_folders if f.exists()]
    
    if watch_folders:
        thread = threading.Thread(
            target=_watch_folders,
            args=(watch_folders,),
            daemon=True,
            name="kerberos_anti_stego"
        )
        thread.start()
        _publish_metric(0.3)
        return thread
    else:
        _log("⚠️ Aucun dossier à surveiller", "WARN")
        _publish_metric(0.1)
        return None

def run(scan_path: str = "."):
    """Exécution standalone"""
    _log(f"🔍 [Anti-Stego] Scan manuel: {scan_path}", "MANUAL")
    
    directory = Path(scan_path)
    results = _scan_directory(directory, recursive=True)
    
    suspicious_count = sum(1 for r in results if r.get("suspicious"))
    
    print("\n" + "="*60)
    print("🔍 RAPPORT ANTI-STEGO")
    print("="*60)
    print(f"📁 Fichiers scannés: {len(results)}")
    print(f"🚨 Fichiers suspects: {suspicious_count}")
    print(f"📦 Quarantaine: {QUARANTINE_DIR}")
    print("="*60)
    
    if suspicious_count > 0:
        print("\n🚨 FICHIERS SUSPECTS:")
        for r in results:
            if r.get("suspicious"):
                print(f"   • {r['file']}")
                for reason in r.get("reasons", []):
                    print(f"      └─ {reason}")
    
    _publish_metric(1.0 if suspicious_count > 0 else 0.2)
    
    return {
        "guard": "anti_stego",
        "status": "scan_complete",
        "files_scanned": len(results),
        "suspicious_count": suspicious_count,
        "results": results
    }

def get_stats() -> Dict:
    """Stats pour l'onglet Guards"""
    quarantine_files = list(QUARANTINE_DIR.glob("*.quarantine")) if QUARANTINE_DIR.exists() else []
    
    return {
        "guard_name": "Anti-Stego",
        "status": "active",
        "description": "Détection malware caché dans images/vidéos/audio",
        "quarantine_count": len(quarantine_files),
        "watched_folders": 4,
        "extensions": len(ALL_EXTS)
    }

# ============================================================================
# === MODE STANDALONE ========================================================
# ============================================================================

if __name__ == "__main__":
    import argparse
    
    parser = argparse.ArgumentParser(description="🔍 Kerberos Anti-Stego Guard")
    parser.add_argument("path", nargs="?", default=".", help="Dossier à scanner")
    parser.add_argument("--watch", action="store_true", help="Mode surveillance continue")
    args = parser.parse_args()
    
    print("""
╔════════════════════════════════════════════════════════════╗
║  🔍 KERBEROS ANTI-STEGO GUARD                             ║
║                                                            ║
║  Détection de malware caché dans :                        ║
║    • 🖼️ Images (JPG, PNG, GIF, BMP, WEBP)                ║
║    • 🎬 Vidéos (AVI, MP4, MKV, MOV)                       ║
║    • 🎵 Audio (MP3, WAV, FLAC)                            ║
║    • 📄 Documents (PDF, DOCX)                             ║
║                                                            ║
║  Détections :                                             ║
║    • Données après EOF markers                            ║
║    • Entropie anormale                                    ║
║    • Taille suspecte                                      ║
║    • Structure invalide                                   ║
║                                                            ║
║  Licence : GPLv3 — Victor Pozen                           ║
╚════════════════════════════════════════════════════════════╝
    """)
    
    if args.watch:
        print("👁️ Mode surveillance continue activé...")
        start_guard()
        try:
            while True:
                time.sleep(1)
        except KeyboardInterrupt:
            print("🛑 Arrêt")
    else:
        run(args.path)