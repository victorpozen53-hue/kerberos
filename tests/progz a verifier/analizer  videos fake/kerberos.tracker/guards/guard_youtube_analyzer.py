#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""▶️ GUARD YOUTUBE ANALYZER — Détection Spécialisée YouTube"""
import cv2, numpy as np, logging
from typing import Dict, Any
from guards.guard_interface import GuardInterface
logger = logging.getLogger(__name__)

class YouTubeAnalyzerGuard(GuardInterface):
    def __init__(self, kerberos_app=None):
        super().__init__("youtube_analyzer")
        self.kerberos, self.is_running = kerberos_app, False
        self.stats = {"frames_analyzed": 0, "compression_artifacts": 0, "deepfake_indicators": 0}
        logger.info("▶️ YouTubeAnalyzerGuard initialisé")

    def analyze_frame(self, frame: np.ndarray, metadata: Dict[str, Any] = None) -> Dict[str, Any]:
        if frame is None: return {"suspicion_score": 0.0, "details": []}
        self.stats["frames_analyzed"] += 1
        results = {"suspicion_score": 0.0, "details": [], "quality_score": 0.0}
        
        h, w = frame.shape[:2]
        if 1.6 <= (w / h) <= 1.8: results["details"].append("Format YouTube 16:9")
        
        try:
            gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
            dct = cv2.dct(gray.astype(np.float32))
            fh, fw = dct.shape
            block_artifacts = np.abs(dct[fh//8:fh//8+8, fw//8:fw//8+8])
            artifact_strength = np.mean(block_artifacts)
            
            if artifact_strength < 50:
                results["details"].append("Forte compression YouTube détectée")
                results["suspicion_score"] += 0.3
                self.stats["compression_artifacts"] += 1
        except: pass
        
        results["suspicion_score"] = min(1.0, results["suspicion_score"])
        return results

    def start(self): self.is_running = True
    def stop(self): self.is_running = False
    def get_stats(self) -> Dict[str, Any]: return self.stats.copy()

_guard_instance = None
def start_guard(kerberos_app=None):
    global _guard_instance; _guard_instance = YouTubeAnalyzerGuard(kerberos_app); return _guard_instance
def stop_guard():
    global _guard_instance
    if _guard_instance: _guard_instance.stop()
def get_stats():
    global _guard_instance; return _guard_instance.get_stats() if _guard_instance else {}