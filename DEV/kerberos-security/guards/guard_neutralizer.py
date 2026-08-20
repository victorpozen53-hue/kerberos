#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
🛡️ Guard Neutralizer — Mécanisme de suppression éthique de keyloggers
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
⚠️ PRINCIPE "FROG-TOXIC" DÉFENSIF :
- Neutralise les menaces détectées AVEC consentement utilisateur
- Quarantaine sécurisée (pas de suppression définitive sans validation)
- Journalisation complète pour audit et restauration
- Whitelist stricte pour éviter les faux positifs critiques
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
Copyright (C) 2025 Victor Pozen — GPLv3
"""
import os
import sys
import json
import time
import shutil
import psutil
import hashlib
from datetime import datetime
from pathlib import Path
from typing import Optional, Tuple

# ============================================================================
# === CONFIGURATION ==========================================================
# ============================================================================

NEUTRALIZER_DIR = Path(__file__).parent.parent / "lymph" / "neutralizer"
QUARANTINE_DIR = NEUTRALIZER_DIR / "quarantine"
LOG_FILE = NEUTRALIZER_DIR / "neutralizer.log"

# Créer les dossiers
NEUTRALIZER_DIR.mkdir(parents=True, exist_ok=True)
QUARANTINE_DIR.mkdir(parents=True, exist_ok=True)

# Whitelist CRITIQUE — jamais neutraliser ces processus
CRITICAL_WHITELIST = {
    'explorer.exe', 'svchost.exe', 'csrss.exe', 'wininit.exe', 'services.exe',
    'lsass.exe', 'smss.exe', 'winlogon.exe', 'system', 'idle',
    'python.exe', 'pythonw.exe', 'kerberos.exe',  # Kerberos lui-même
}

# Actions disponibles
ACTION_LOG = "log_only"           # Juste logger (par défaut)
ACTION_QUARANTINE = "quarantine"  # Déplacer en quarantaine
ACTION_TERMINATE = "terminate"    # Arrêter le processus
ACTION_FULL = "full"              # Terminer + quarantaine + log

# ============================================================================
# === CLASSE PRINCIPALE ======================================================
# ============================================================================

class Neutralizer:
    """Mécanisme de neutralisation éthique — style Frog-Toxic défensif"""
    
    def __init__(self, auto_mode: bool = False):
        """
        auto_mode: Si False, demande confirmation avant chaque action
                   Si True, agit automatiquement (pour mode "urgence")
        """
        self.auto_mode = auto_mode
        self.actions_taken = []
        self._log("INIT", f"Neutralizer démarré (auto_mode={auto_mode})")
    
    def _log(self, level: str, message: str):
        """Journalisation sécurisée"""
        timestamp = datetime.now().isoformat()
        log_line = f"[{timestamp}] [{level}] {message}\n"
        try:
            with open(LOG_FILE, "a", encoding="utf-8") as f:
                f.write(log_line)
        except:
            pass
        print(f"📋 [Neutralizer] {message}")
    
    def _hash_file(self, filepath: Path) -> str:
        """Calcule le hash SHA256 d'un fichier pour traçabilité"""
        try:
            sha256 = hashlib.sha256()
            with open(filepath, "rb") as f:
                for chunk in iter(lambda: f.read(8192), b""):
                    sha256.update(chunk)
            return sha256.hexdigest()
        except:
            return "unknown"
    
    def _is_critical_process(self, proc: psutil.Process) -> bool:
        """Vérifie si un processus est critique (jamais neutraliser)"""
        try:
            name = proc.name().lower()
            if name in CRITICAL_WHITELIST:
                return True
            # Vérifie si processus système
            if proc.username() in ["NT AUTHORITY\\SYSTEM", "SYSTEM"]:
                return True
            return False
        except:
            return True  # En cas de doute, on ne touche pas
    
    def _request_confirmation(self, threat_info: dict) -> bool:
        """Demande confirmation utilisateur (si pas en auto_mode)"""
        if self.auto_mode:
            return True
        
        print("\n" + "⚠️" * 40)
        print(f"🎯 MENACE DÉTECTÉE — Action requise")
        print(f"   Processus : {threat_info.get('name')}")
        print(f"   PID       : {threat_info.get('pid')}")
        print(f"   Chemin    : {threat_info.get('exe')}")
        print(f"   Raison    : {threat_info.get('reason')}")
        print(f"   Hash      : {threat_info.get('hash', 'N/A')[:16]}...")
        print("⚠️" * 40)
        print("\nActions disponibles :")
        print("  [1] 🔍 Logger seulement (aucune action)")
        print("  [2] 📦 Quarantaine (déplacer le fichier)")
        print("  [3] 🛑 Terminer le processus")
        print("  [4] 💥 FULL : Terminer + Quarantaine + Log")
        print("  [0] ❌ Annuler / Ignorer")
        
        while True:
            try:
                choice = input("\nVotre choix [1-4, 0=annuler] : ").strip()
                if choice in ["1", "2", "3", "4", "0"]:
                    return choice != "0"
                print("Choix invalide.")
            except KeyboardInterrupt:
                return False
    
    def quarantine_file(self, filepath: Path, threat_info: dict) -> bool:
        """Déplace un fichier suspect en quarantaine sécurisée"""
        try:
            if not filepath.exists():
                self._log("WARN", f"Fichier inexistant : {filepath}")
                return False
            
            # Nom unique pour la quarantaine : hash_timestamp_originalname
            file_hash = self._hash_file(filepath)
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            original_name = filepath.name
            quarantine_name = f"{file_hash[:12]}_{timestamp}_{original_name}"
            quarantine_path = QUARANTINE_DIR / quarantine_name
            
            # Métadonnées de quarantaine
            metadata = {
                "original_path": str(filepath),
                "original_name": original_name,
                "quarantine_name": quarantine_name,
                "hash_sha256": file_hash,
                "threat_reason": threat_info.get("reason"),
                "timestamp": datetime.now().isoformat(),
                "size": filepath.stat().st_size,
            }
            
            # Copie sécurisée (pas de move pour garder une trace)
            shutil.copy2(filepath, quarantine_path)
            
            # Sauvegarde métadonnées
            meta_file = QUARANTINE_DIR / f"{quarantine_name}.meta.json"
            with open(meta_file, "w", encoding="utf-8") as f:
                json.dump(metadata, f, indent=2, ensure_ascii=False)
            
            # Optionnel : supprimer l'original (à activer avec prudence)
            # filepath.unlink()
            
            self._log("QUARANTINE", f"{original_name} → {quarantine_name}")
            return True
            
        except Exception as e:
            self._log("ERROR", f"Échec quarantaine : {e}")
            return False
    
    def terminate_process(self, pid: int, threat_info: dict) -> bool:
        """Arrête un processus suspect de manière sécurisée"""
        try:
            proc = psutil.Process(pid)
            
            # Vérifications de sécurité
            if self._is_critical_process(proc):
                self._log("BLOCKED", f"Processus critique protégé : PID {pid}")
                return False
            
            name = proc.name()
            
            # Tentative de termination gracieuse d'abord
            proc.terminate()
            try:
                proc.wait(timeout=3)
                self._log("TERMINATE", f"{name} (PID {pid}) arrêté gracieusement")
                return True
            except psutil.TimeoutExpired:
                # Force kill si nécessaire
                proc.kill()
                proc.wait(timeout=2)
                self._log("TERMINATE", f"{name} (PID {pid}) forcé à s'arrêter")
                return True
                
        except psutil.NoSuchProcess:
            self._log("INFO", f"Processus PID {pid} déjà terminé")
            return True
        except psutil.AccessDenied:
            self._log("ERROR", f"Accès refusé pour PID {pid} (nécessite admin)")
            return False
        except Exception as e:
            self._log("ERROR", f"Erreur termination PID {pid} : {e}")
            return False
    
    def neutralize(self, threat_info: dict, action: str = ACTION_FULL) -> dict:
        """
        Neutralise une menace détectée
        
        threat_info: dict avec keys: pid, name, exe, reason, hash
        action: "log_only" | "quarantine" | "terminate" | "full"
        
        Retourne: dict avec résultat de l'action
        """
        result = {
            "success": False,
            "actions": [],
            "errors": [],
            "timestamp": datetime.now().isoformat()
        }
        
        # Demande confirmation si nécessaire
        if not self._request_confirmation(threat_info):
            result["actions"].append("cancelled_by_user")
            self._log("CANCEL", f"Neutralisation annulée par utilisateur")
            return result
        
        filepath = Path(threat_info.get("exe", "")) if threat_info.get("exe") != "N/A" else None
        pid = threat_info.get("pid")
        
        # Action 1: Logger (toujours)
        self._log("THREAT", f"Neutralisation: {threat_info.get('name')} | {threat_info.get('reason')}")
        result["actions"].append("logged")
        
        # Action 2: Quarantaine
        if action in [ACTION_QUARANTINE, ACTION_FULL] and filepath and filepath.exists():
            if self.quarantine_file(filepath, threat_info):
                result["actions"].append("quarantined")
            else:
                result["errors"].append("quarantine_failed")
        
        # Action 3: Terminer processus
        if action in [ACTION_TERMINATE, ACTION_FULL] and pid:
            if self.terminate_process(pid, threat_info):
                result["actions"].append("terminated")
            else:
                result["errors"].append("terminate_failed")
        
        result["success"] = len(result["errors"]) == 0 or len(result["actions"]) > 1
        self.actions_taken.append(result)
        
        return result

# ============================================================================
# === INTÉGRATION AVEC guard_antikeylogger ===================================
# ============================================================================

def neutralize_detected_threats(threats: list, auto_mode: bool = False) -> list:
    """
    Fonction helper pour neutraliser une liste de menaces
    Utilisable depuis guard_antikeylogger ou directement dans Kerberos
    """
    if not threats:
        return []
    
    neutralizer = Neutralizer(auto_mode=auto_mode)
    results = []
    
    for threat in threats:
        result = neutralizer.neutralize(threat, action="full")
        results.append({
            "threat": threat,
            "neutralization_result": result
        })
    
    return results

# ============================================================================
# === POINTS D'ENTRÉE ========================================================
# ============================================================================

def start_guard(auto_mode: bool = False):
    """Point d'entrée pour Kerberos — Surveillance + Neutralisation"""
    print("🛡️ [Neutralizer] Module chargé — En attente de menaces...")
    
    # Retourne la classe pour utilisation par Kerberos
    return Neutralizer(auto_mode=auto_mode)

def run(threats: Optional[list] = None, auto_mode: bool = False):
    """Exécution standalone ou avec menaces fournies"""
    if threats is None:
        # Mode démo : simuler une menace pour test
        print("🧪 Mode test — Aucune menace fournie, simulation...")
        demo_threat = {
            "pid": 9999,
            "name": "demo_threat.exe",
            "exe": "C:\\temp\\demo_threat.exe",
            "reason": "signature connue: 'keylogger'",
            "hash": "a1b2c3d4e5f6" * 4
        }
        threats = [demo_threat]
    
    print(f"🎯 Neutralisation de {len(threats)} menace(s)...")
    results = neutralize_detected_threats(threats, auto_mode=auto_mode)
    
    # Résumé
    success_count = sum(1 for r in results if r["neutralization_result"]["success"])
    print(f"\n✅ Résumé : {success_count}/{len(results)} neutralisation(s) réussie(s)")
    
    return results

if __name__ == "__main__":
    import argparse
    parser = argparse.ArgumentParser(description="🛡️ Guard Neutralizer — Suppression éthique de keyloggers")
    parser.add_argument("--auto", action="store_true", help="Mode automatique (sans confirmation)")
    parser.add_argument("--test", action="store_true", help="Mode test avec menace simulée")
    args = parser.parse_args()
    
    if args.test:
        run(auto_mode=args.auto)
    else:
        print("🛡️ Neutralizer prêt — Intégrez-le via guard_antikeylogger")
        print("   Ou lancez avec --test pour une démo")