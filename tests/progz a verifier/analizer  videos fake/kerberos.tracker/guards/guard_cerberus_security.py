#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
‍🦺 GUARD CERBERUS SECURITY — Système Immunitaire de Kerberos
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
Version: 1.0.0
Author: Victor Pozen
License: GPLv3

Fonctionnalités :
- File Integrity Monitoring (FIM) via SHA256
- Analyse AST (Abstract Syntax Tree) pour détecter le code malveillant
- Auto-Quarantaine des fichiers suspects
- Surveillance temps réel du dossier guards/
"""
import ast
import hashlib
import logging
import re
import threading
import time
from pathlib import Path
from typing import Dict, Any, List, Set, Optional
from datetime import datetime

try:
    from guards.guard_interface import GuardInterface
except ImportError:
    class GuardInterface:
        def __init__(self, name): self.name = name; self.is_running = False; self.stats = {}
        def start(self): pass
        def stop(self): pass
        def get_stats(self): return self.stats
        def analyze_frame(self, frame, metadata=None): return {"suspicion_score": 0.0, "details": []}

logger = logging.getLogger(__name__)

#  MOTIFS DANGEREUX (AST & Regex)
DANGEROUS_CALLS = {
    'eval': "Fonction eval() détectée (Exécution de code dynamique)",
    'exec': "Fonction exec() détectée (Exécution de code dynamique)",
    '__import__': "Import dynamique suspect",
    'compile': "Compilation de code dynamique",
}

DANGEROUS_MODULES = {
    'subprocess': "Appel à subprocess (Exécution de commandes système)",
    'os': "Appel à os (Manipulation système avancée)",
    'ctypes': "Appel à ctypes (Accès bas niveau / DLL)",
    'socket': "Connexion réseau brute",
    'urllib': "Téléchargement réseau",
    'requests': "Requêtes HTTP externes",
}

# 🛡️ FICHIERS PROTÉGÉS (Ne jamais quarantainer)
PROTECTED_FILES = {
    "guard_interface.py", "guard_manager.py", "__init__.py", 
    "guard_manifest_injector.py", "guard_cerberus_security.py"
}

class DangerousNodeVisitor(ast.NodeVisitor):
    """Visiteur AST pour trouver les appels dangereux"""
    def __init__(self):
        self.findings = []
        
    def visit_Call(self, node):
        if isinstance(node.func, ast.Name) and node.func.id in DANGEROUS_CALLS:
            self.findings.append(f"Ligne {node.lineno}: {DANGEROUS_CALLS[node.func.id]}")
        elif isinstance(node.func, ast.Attribute) and node.func.attr in DANGEROUS_CALLS:
            self.findings.append(f"Ligne {node.lineno}: Appel suspect à {node.func.attr}")
        self.generic_visit(node)

    def visit_Import(self, node):
        for alias in node.names:
            if alias.name in DANGEROUS_MODULES:
                self.findings.append(f"Ligne {node.lineno}: Import de module système '{alias.name}'")
        self.generic_visit(node)

    def visit_ImportFrom(self, node):
        if node.module and node.module in DANGEROUS_MODULES:
            self.findings.append(f"Ligne {node.lineno}: Import depuis '{node.module}'")
        self.generic_visit(node)


class CerberusSecurityGuard(GuardInterface):
    """Le gardien à 3 têtes intégré à Kerberos"""
    
    def __init__(self, kerberos_app=None):
        super().__init__("cerberus_security")
        self.kerberos = kerberos_app
        self.is_running = False
        self._lock = threading.Lock()
        
        # Chemins
        self.guards_dir = Path(__file__).parent
        self.baseline_hashes: Dict[str, str] = {}
        
        # Stats
        self.stats = {
            "files_monitored": 0,
            "integrity_violations": 0,
            "ast_threats_found": 0,
            "files_quarantined": 0,
            "last_scan": None,
            "system_status": "SECURE"
        }
        
        self._monitor_thread: Optional[threading.Thread] = None
        logger.info("‍🦺 CerberusSecurityGuard initialisé (Système Immunitaire)")

    def _compute_sha256(self, file_path: Path) -> str:
        """Calcule le hash SHA256 d'un fichier"""
        sha256 = hashlib.sha256()
        try:
            with open(file_path, 'rb') as f:
                for block in iter(lambda: f.read(4096), b''):
                    sha256.update(block)
            return sha256.hexdigest()
        except Exception as e:
            logger.error(f"Erreur hash {file_path}: {e}")
            return ""

    def _compute_baseline(self) -> None:
        """Calcule les hashes de référence de tous les guards"""
        self.baseline_hashes.clear()
        for py_file in self.guards_dir.glob("*.py"):
            if py_file.name.endswith((".bak", ".quarantined")):
                continue
            self.baseline_hashes[py_file.name] = self._compute_sha256(py_file)
        self.stats["files_monitored"] = len(self.baseline_hashes)
        logger.info(f" Baseline de sécurité établie ({len(self.baseline_hashes)} guards)")

    def _ast_scan_file(self, file_path: Path) -> List[str]:
        """Scanne un fichier avec l'AST pour trouver du code malveillant"""
        try:
            code = file_path.read_text(encoding='utf-8', errors='ignore')
            tree = ast.parse(code, filename=str(file_path))
            visitor = DangerousNodeVisitor()
            visitor.visit(tree)
            return visitor.findings
        except SyntaxError:
            return ["️ Erreur de syntaxe Python (fichier corrompu ?)"]
        except Exception as e:
            return [f"Erreur scan: {e}"]

    def _quarantine_file(self, file_name: str, reason: str) -> None:
        """Met un fichier en quarantaine"""
        if file_name in PROTECTED_FILES:
            logger.warning(f"🛡️ Tentative de quarantaine ignorée sur fichier protégé: {file_name}")
            return
            
        src = self.guards_dir / file_name
        dst = src.with_suffix(src.suffix + ".quarantined")
        
        try:
            src.rename(dst)
            self.stats["files_quarantined"] += 1
            logger.critical(f"🚨 Fichier mis en quarantaine: {file_name} -> {dst.name} | Raison: {reason}")
        except Exception as e:
            logger.error(f"Erreur quarantaine {file_name}: {e}")

    def _integrity_check(self) -> None:
        """Vérifie l'intégrité des fichiers par rapport à la baseline"""
        current_files = {f.name: f for f in self.guards_dir.glob("*.py") if not f.name.endswith((".bak", ".quarantined"))}
        
        # 1. Fichiers modifiés ou supprimés
        for name, original_hash in self.baseline_hashes.items():
            if name not in current_files:
                logger.warning(f"⚠️ Fichier supprimé: {name}")
                continue
                
            current_hash = self._compute_sha256(current_files[name])
            if current_hash != original_hash:
                self.stats["integrity_violations"] += 1
                self.stats["system_status"] = "COMPROMISED"
                logger.critical(f"🚨 INTEGRITY VIOLATION: {name} a été modifié !")
                # On ne quarantaine pas tout de suite pour éviter les faux positifs sur les logs, 
                # mais on alerte massivement.

        # 2. Nouveaux fichiers (Injections)
        for name, file_path in current_files.items():
            if name not in self.baseline_hashes:
                logger.warning(f"️ Nouveau fichier détecté: {name}. Analyse AST...")
                threats = self._ast_scan_file(file_path)
                if threats:
                    self.stats["ast_threats_found"] += len(threats)
                    self.stats["system_status"] = "CRITICAL"
                    for t in threats:
                        logger.critical(f" MENACE AST dans {name}: {t}")
                    self._quarantine_file(name, "Nouveau fichier avec code suspect")

    def _monitor_loop(self) -> None:
        """Boucle de surveillance en arrière-plan"""
        logger.info("🕵️ Surveillance Cerberus démarrée (Intervalle: 30s)")
        while self.is_running:
            try:
                self._integrity_check()
                self.stats["last_scan"] = datetime.now().strftime('%H:%M:%S')
            except Exception as e:
                logger.error(f"Erreur boucle Cerberus: {e}")
            
            # Attendre 30 secondes (interruptible)
            for _ in range(30):
                if not self.is_running:
                    break
                time.sleep(1)

    # =========================================================================
    # INTERFACE PUBLIQUE
    # =========================================================================
    def analyze_frame(self, frame, metadata=None):
        """Ne fait rien sur les frames, retourne l'état du système"""
        return {
            "suspicion_score": 0.0, 
            "details": [f"Système: {self.stats['system_status']}"]
        }

    def start(self):
        if self.is_running:
            return
        self._compute_baseline()
        self.is_running = True
        self._monitor_thread = threading.Thread(target=self._monitor_loop, daemon=True, name="CerberusMonitor")
        self._monitor_thread.start()
        logger.info("🐕‍🦺 CerberusSecurityGuard démarré")

    def stop(self):
        self.is_running = False
        if self._monitor_thread:
            self._monitor_thread.join(timeout=2)
        logger.info("🐕‍🦺 CerberusSecurityGuard arrêté")

    def get_stats(self) -> Dict[str, Any]:
        with self._lock:
            return self.stats.copy()

# ============================================================================
# FONCTIONS GLOBALES
# ============================================================================
_guard_instance: Optional[CerberusSecurityGuard] = None

def start_guard(kerberos_app=None) -> Optional[CerberusSecurityGuard]:
    global _guard_instance
    _guard_instance = CerberusSecurityGuard(kerberos_app)
    _guard_instance.start()
    return _guard_instance

def stop_guard() -> None:
    global _guard_instance
    if _guard_instance:
        _guard_instance.stop()
        _guard_instance = None

def get_stats() -> Dict[str, Any]:
    global _guard_instance
    return _guard_instance.get_stats() if _guard_instance else {}