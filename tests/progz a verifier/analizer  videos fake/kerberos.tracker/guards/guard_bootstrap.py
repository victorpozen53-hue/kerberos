#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
🌱 GUARD BOOTSTRAP — Initialisation de l'architecture modulaire
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
Version: 1.0.1 (Corrigé)
Author: Victor Pozen
License: GPLv3
"""
import logging
from pathlib import Path
from typing import Dict, Any, Optional
from datetime import datetime

try:
    from guards.guard_interface import GuardInterface
except ImportError:
    class GuardInterface:
        def __init__(self, name):
            self.name = name
            self.is_running = False
            self.stats = {}
        def start(self): pass
        def stop(self): pass
        def get_stats(self): return self.stats

logger = logging.getLogger(__name__)


class BootstrapGuard(GuardInterface):
    """Guard qui initialise l'architecture modulaire de Kerberos"""
    
    def __init__(self, kerberos_app=None):
        super().__init__("bootstrap")
        self.kerberos = kerberos_app
        self.is_running = False
        self.guards_dir = Path(__file__).parent
        
        self.stats = {
            "dirs_created": 0,
            "inits_created": 0,
            "last_bootstrap": None
        }
        
        logger.info("🌱 BootstrapGuard initialisé")
    
    def _create_directory_structure(self) -> None:
        """Crée l'architecture de dossiers modulaires"""
        required_dirs = [
            self.guards_dir / "boutons",
            self.guards_dir / "onglets",
        ]
        
        for dir_path in required_dirs:
            if not dir_path.exists():
                try:
                    dir_path.mkdir(parents=True, exist_ok=True)
                    logger.info(f"📁 Dossier créé : {dir_path.name}")
                    self.stats["dirs_created"] += 1
                except Exception as e:
                    logger.error(f"❌ Erreur création dossier {dir_path}: {e}")
    
    def _create_init_files(self) -> None:
        """Crée les fichiers __init__.py"""
        init_content = '''#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Package {package_name} — Architecture modulaire Kerberos
"""
__version__ = "1.0.0"
__author__ = "Victor Pozen"
__license__ = "GPLv3"
'''
        
        required_inits = [
            self.guards_dir / "boutons" / "__init__.py",
            self.guards_dir / "onglets" / "__init__.py",
        ]
        
        for init_path in required_inits:
            if not init_path.exists():
                try:
                    package_name = init_path.parent.name
                    content = init_content.format(package_name=package_name)
                    init_path.write_text(content, encoding='utf-8')
                    logger.info(f"📄 Fichier créé : {init_path.name}")
                    self.stats["inits_created"] += 1
                except Exception as e:
                    logger.error(f"❌ Erreur création {init_path}: {e}")
    
    def bootstrap(self) -> None:
        """Exécute le bootstrap complet"""
        logger.info(" Démarrage du bootstrap...")
        
        # 1. Création des dossiers
        self._create_directory_structure()
        
        # 2. Création des __init__.py
        self._create_init_files()
        
        self.stats["last_bootstrap"] = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        
        logger.info(f"✅ Bootstrap terminé ({self.stats['dirs_created']} dossiers, {self.stats['inits_created']} fichiers)")
    
    # Interface GuardInterface
    def start(self):
        self.is_running = True
        self.bootstrap()
    
    def stop(self):
        self.is_running = False
    
    def get_stats(self) -> Dict[str, Any]:
        return self.stats.copy()


# ============================================================================
# FONCTIONS GLOBALES
# ============================================================================
_guard_instance: Optional[BootstrapGuard] = None

def start_guard(kerberos_app=None) -> Optional[BootstrapGuard]:
    global _guard_instance
    _guard_instance = BootstrapGuard(kerberos_app)
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