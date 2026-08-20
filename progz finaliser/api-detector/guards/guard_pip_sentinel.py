#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
🚑 Guard Pip Sentinel — Protocole Sandow & Arsenal
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
- Sandow (Sandbox) : Téléchargement et analyse isolée
- Arsenal : Installation locale dans l'écosystème Kerberos
- Injection dynamique : Ajout au sys.path (zéro dépendance globale)
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
Copyright (C) 2026 Victor Pozen — GPLv3
"""
import os, sys, subprocess, re, shutil
from pathlib import Path
from datetime import datetime
from typing import Dict, List, Tuple, Optional, Callable

# === CONFIGURATION BIOLOGIQUE ===
KERBEROS_ROOT = Path(__file__).parent.parent
LYMPH_DIR = KERBEROS_ROOT / "lymph"
SANDOW_DIR = LYMPH_DIR / "sandow"
QUARANTINE_DIR = SANDOW_DIR / "quarantine"  # Zone de test
ARSENAL_DIR = SANDOW_DIR / "arsenal"        # Zone de déploiement final
LOG_FILE = KERBEROS_ROOT / "logs" / "pip_sentinel.log"

for d in [SANDOW_DIR, QUARANTINE_DIR, ARSENAL_DIR, LOG_FILE.parent]:
    d.mkdir(parents=True, exist_ok=True)

# === SIGNATURES MENACES (Regex Commando) ===
MALWARE_SIGNATURES = [
    (r'os\.system\s*\(', "Exec système directe"),
    (r'subprocess\.(call|run|Popen)\s*\(', "Subprocess suspect"),
    (r'\beval\s*\(', "Eval dangereux"),
    (r'\bexec\s*\(', "Exec dynamique"),
    (r'__import__\s*\(', "Import dynamique"),
    (r'base64\.b64decode', "Décodage base64 suspect"),
    (r'socket\.(connect|bind)\s*\(', "Connexion réseau brute"),
    (r'ctypes\.windll', "Appel DLL bas niveau"),
    (r'pickle\.loads', "Désérialisation dangereuse"),
]

def _log(msg: str, level: str = "INFO"):
    ts = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    line = f"[{ts}] [{level}] {msg}\n"
    try:
        with open(LOG_FILE, "a", encoding="utf-8") as f: f.write(line)
    except: pass

class PipSentinelEngine:
    def __init__(self):
        self.python_exe = sys.executable
        self._activate_arsenal()

    def _activate_arsenal(self) -> None:
        """Injecte l'Arsenal dans le sys.path pour que Python trouve les libs locales"""
        arsenal_str = str(ARSENAL_DIR)
        if arsenal_str not in sys.path:
            sys.path.insert(0, arsenal_str)
            _log(f"🔗 Arsenal injecté dans sys.path", "OK")

    def check_local_dna(self, module_name: str) -> bool:
        """Vérifie si le module est déjà dans l'Arsenal ou le Python global"""
        try:
            import importlib.util
            spec = importlib.util.find_spec(module_name)
            if spec and spec.origin:
                # Si le module vient de notre Arsenal, c'est bon
                if "sandow/arsenal" in spec.origin:
                    return True
                return Path(spec.origin).exists()
        except: pass
        return False

    def fetch_to_sandow(self, package_name: str) -> Tuple[bool, Path]:
        """Télécharge dans la zone Sandow (Quarantaine)"""
        quarantine_pkg = QUARANTINE_DIR / package_name
        if quarantine_pkg.exists(): shutil.rmtree(quarantine_pkg)
        quarantine_pkg.mkdir(parents=True, exist_ok=True)
        
        _log(f"🪂 Extraction {package_name} → Sandow", "FETCH")
        try:
            result = subprocess.run(
                [self.python_exe, "-m", "pip", "download", 
                 "--dest", str(quarantine_pkg), "--no-deps", "--quiet", package_name],
                capture_output=True, text=True, timeout=180
            )
            if result.returncode == 0: return True, quarantine_pkg
            else: return False, quarantine_pkg
        except: return False, quarantine_pkg

    def scan_sandow(self, package_path: Path) -> Tuple[bool, List[str]]:
        """Contrôle les fichiers dans le Sandow"""
        threats = []
        for py_file in package_path.rglob("*.py"):
            try:
                content = py_file.read_text(encoding='utf-8', errors='ignore')
                for pattern, description in MALWARE_SIGNATURES:
                    if re.search(pattern, content, re.IGNORECASE):
                        threats.append(f"⚠️ {description} dans {py_file.name}")
            except: continue
        return len(threats) == 0, threats

    def deploy_to_arsenal(self, package_name: str) -> bool:
        """Installe le paquet proprement dans l'Arsenal local (pas de pip global)"""
        _log(f"📦 Déploiement {package_name} → Arsenal", "DEPLOY")
        try:
            # --target force l'installation dans notre dossier local
            result = subprocess.run(
                [self.python_exe, "-m", "pip", "install", 
                 "--target", str(ARSENAL_DIR), 
                 "--quiet", "--no-cache-dir", package_name],
                capture_output=True, text=True, timeout=180
            )
            if result.returncode == 0:
                _log(f"✅ {package_name} déployé dans l'Arsenal", "OK")
                return True
            else: return False
        except: return False

    def commando_heal(self, package_name: str) -> Dict:
        """Protocole complet : Sandow → Contrôle → Arsenal"""
        report = {"package": package_name, "status": "unknown", "threats": [], "phase": ""}
        
        # 1. Check
        report["phase"] = "detect"
        if self.check_local_dna(package_name):
            report["status"] = "already_present"; return report
        
        # 2. Sandow
        report["phase"] = "sandow"
        success, path = self.fetch_to_sandow(package_name)
        if not success: report["status"] = "fetch_failed"; return report
        
        # 3. Contrôle
        report["phase"] = "control"
        is_clean, threats = self.scan_sandow(path)
        report["threats"] = threats
        if not is_clean: 
            report["status"] = "quarantined_malware"; return report
        
        # 4. Arsenal
        report["phase"] = "arsenal"
        if self.deploy_to_arsenal(package_name):
            report["status"] = "deployed"
            shutil.rmtree(path, ignore_errors=True) # Nettoyage du sandow
        else: 
            report["status"] = "deploy_failed"
            
        return report

    def commando_batch(self, packages: List[str], progress_cb: Optional[Callable] = None) -> List[Dict]:
        results = []
        total = len(packages)
        for i, pkg in enumerate(packages):
            if progress_cb: progress_cb(i, total, pkg)
            results.append(self.commando_heal(pkg))
        if progress_cb: progress_cb(total, total, "DONE")
        return results

_sentinel_engine: Optional[PipSentinelEngine] = None

def start_guard():
    global _sentinel_engine
    _log("🚑 [PipSentinel] Démarrage du protocole Sandow", "INFO")
    _sentinel_engine = PipSentinelEngine()
    return _sentinel_engine

def get_engine() -> PipSentinelEngine:
    global _sentinel_engine
    if _sentinel_engine is None: start_guard()
    return _sentinel_engine

if __name__ == "__main__":
    print("🚑 KERBEROS PIP SENTINEL — Protocole Sandow & Arsenal prêt.")
    start_guard()