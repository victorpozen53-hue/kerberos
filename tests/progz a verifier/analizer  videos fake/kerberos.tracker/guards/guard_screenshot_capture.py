#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
📸 GUARD SCREENSHOT CAPTURE — Capture d'Écran (Auto & Manuel)
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
Version: 1.0.0
Author: Victor Pozen
License: GPLv3

Fonctionnalités :
- Mode Auto : Capture la page navigateur si score SUSPICIOUS
- Mode Manuel : Capture à la demande via l'UI
- Sauvegarde dans reports/screenshots/
"""
import logging
import threading
from datetime import datetime
from pathlib import Path
from typing import Optional, Any
from guards.guard_interface import GuardInterface

logger = logging.getLogger(__name__)

class ScreenshotCaptureGuard(GuardInterface):
    def __init__(self, kerberos_app=None):
        super().__init__("screenshot_capture")
        self.kerberos = kerberos_app
        self.is_running = False
        self._lock = threading.Lock()
        
        # Dossier de sauvegarde
        self.screenshots_dir = Path(__file__).parent.parent / "reports" / "screenshots"
        self.screenshots_dir.mkdir(parents=True, exist_ok=True)
        
        # Stats
        self.stats = {
            "auto_captures": 0,
            "manual_captures": 0,
            "errors": 0,
            "last_capture_path": ""
        }
        logger.info(f"📸 ScreenshotCaptureGuard initialisé ({self.screenshots_dir})")

    def _generate_filename(self, mode: str, score: int = 0, classification: str = "") -> str:
        """Génère un nom de fichier unique et propre"""
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        safe_class = "".join(c for c in classification if c.isalnum() or c in (' ', '_')).rstrip()
        return f"screen_{mode}_{timestamp}_{safe_class}_{score}.png"

    def capture_browser(self, page: Any, mode: str = "manual", score: int = 0, classification: str = "") -> Optional[str]:
        """
        Capture la page Playwright complète.
        :param page: L'objet Playwright Page
        :param mode: "auto" ou "manual"
        :param score: Score de détection (pour le nom de fichier)
        :param classification: REAL, SUSPICIOUS, etc.
        """
        if not page:
            logger.warning("⚠️ Aucune page Playwright disponible pour le screenshot")
            return None

        with self._lock:
            try:
                filename = self._generate_filename(mode, score, classification)
                filepath = self.screenshots_dir / filename
                
                # Capture Playwright (full_page=True pour tout avoir)
                page.screenshot(path=str(filepath), full_page=False)
                
                # Mise à jour des stats
                if mode == "auto":
                    self.stats["auto_captures"] += 1
                else:
                    self.stats["manual_captures"] += 1
                self.stats["last_capture_path"] = str(filepath)
                
                logger.info(f" Screenshot {mode.upper()} sauvegardé : {filepath.name}")
                return str(filepath)
                
            except Exception as e:
                self.stats["errors"] += 1
                logger.error(f"❌ Erreur capture screenshot: {e}")
                return None

    def trigger_auto_capture(self, page: Any, score: int, classification: str) -> Optional[str]:
        """
        Déclencheur automatique : à appeler quand une vidéo est classée SUSPICIOUS.
        """
        # On ne capture que si c'est suspect (pour ne pas saturer le disque)
        if classification == "SUSPICIOUS" and score > 65:
            return self.capture_browser(page, mode="auto", score=score, classification=classification)
        return None

    def trigger_manual_capture(self, page: Any) -> Optional[str]:
        """
        Déclencheur manuel : à appeler depuis le bouton UI.
        """
        return self.capture_browser(page, mode="manual", score=0, classification="MANUAL")

    def start(self):
        self.is_running = True
        logger.info("📸 ScreenshotCaptureGuard démarré")
        
    def stop(self):
        self.is_running = False
        logger.info("📸 ScreenshotCaptureGuard arrêté")
        
    def get_stats(self) -> dict:
        return self.stats.copy()

# Fonctions globales pour le GuardManager
_guard_instance = None

def start_guard(kerberos_app=None):
    global _guard_instance
    _guard_instance = ScreenshotCaptureGuard(kerberos_app)
    return _guard_instance

def stop_guard():
    global _guard_instance
    if _guard_instance:
        _guard_instance.stop()

def get_stats():
    global _guard_instance
    return _guard_instance.get_stats() if _guard_instance else {}