#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""️ GUARD ENSEMBLE VOTER v2.1 — FIX DÉCODAGE & BOUCLE"""
import cv2, numpy as np, base64, logging
from typing import Dict, Any, List, Tuple
from guards.guard_interface import GuardInterface
logger = logging.getLogger(__name__)

class EnsembleVoterGuard(GuardInterface):
    def __init__(self, kerberos_app=None):
        super().__init__("ensemble_voter")
        self.kerberos, self.is_running = kerberos_app, False
        
        # ✅ video_analyzer RETIRÉ pour éviter la boucle infinie
        self.guard_weights = {
            "pixel_density": 1.3, "shadow_analyzer": 1.2,
            "tiktok_analyzer": 1.0, "resolution_analyzer": 1.1
        }
        self.disabled_guards = ["context_filter", "artistic_effects"]
        self.stats = {"frames_voted": 0, "final_decisions": {"SUSPICIOUS": 0, "REAL": 0}}
        logger.info("🗳️ EnsembleVoterGuard v2.1 initialisé")
        self._disable_interfering_guards()

    def _disable_interfering_guards(self):
        for guard_name in self.disabled_guards:
            guard = self.kerberos.guard_manager.get_guard(guard_name) if self.kerberos else None
            if guard:
                guard.is_running = False
                logger.info(f"🚫 Guard '{guard_name}' désactivé")

    def _decode_frame(self, frame_data) -> np.ndarray:
        """✅ Décode le Base64 en image Numpy pour que les guards ne soient pas aveugles"""
        if isinstance(frame_data, np.ndarray): return frame_data
        if not frame_data or frame_data == "TAINTED": return None
        try:
            if isinstance(frame_data, str) and ',' in frame_data:
                frame_data = frame_data.split(',')[1]
            img_bytes = base64.b64decode(frame_data)
            return cv2.imdecode(np.frombuffer(img_bytes, dtype=np.uint8), cv2.IMREAD_COLOR)
        except Exception as e:
            logger.debug(f"Erreur décodage frame: {e}")
            return None

    def vote(self, frame_data: Dict[str, Any]) -> Tuple[int, str, List[str]]:
        self.stats["frames_voted"] += 1
        decoded_frame = self._decode_frame(frame_data.get('frame'))
        if decoded_frame is None: return 50, "UNCERTAIN", ["Erreur décodage image"]

        weighted_scores, total_weight, all_details = [], 0.0, []
        for guard_name, weight in self.guard_weights.items():
            guard = self.kerberos.guard_manager.get_guard(guard_name) if self.kerberos else None
            if guard and hasattr(guard, 'analyze_frame'):
                try:
                    result = guard.analyze_frame(decoded_frame, frame_data)
                    if result:
                        suspicion = result.get('suspicion_score', 0.0)
                        weighted_scores.append(suspicion * 100 * weight)
                        total_weight += weight
                        all_details.extend(result.get('details', []))
                except Exception as e: logger.debug(f"Erreur guard {guard_name}: {e}")
        
        final_score = sum(weighted_scores) / total_weight if total_weight > 0 else 50
        classification = "SUSPICIOUS" if final_score > 65 else ("UNCERTAIN" if final_score > 40 else "REAL")
        self.stats["final_decisions"][classification] = self.stats["final_decisions"].get(classification, 0) + 1
        return int(final_score), classification, all_details

    def start(self): self.is_running = True
    def stop(self): self.is_running = False
    def get_stats(self) -> Dict[str, Any]: return self.stats.copy()

_guard_instance = None
def start_guard(kerberos_app=None):
    global _guard_instance; _guard_instance = EnsembleVoterGuard(kerberos_app); return _guard_instance
def stop_guard():
    global _guard_instance
    if _guard_instance: _guard_instance.stop()
def get_stats():
    global _guard_instance; return _guard_instance.get_stats() if _guard_instance else {}