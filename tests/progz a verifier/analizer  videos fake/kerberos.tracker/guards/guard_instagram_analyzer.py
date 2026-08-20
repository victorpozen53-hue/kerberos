#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""📸 GUARD INSTAGRAM ANALYZER — Détection Spécialisée Instagram"""
import cv2, numpy as np, logging
from typing import Dict, Any
from guards.guard_interface import GuardInterface
logger = logging.getLogger(__name__)

class InstagramAnalyzerGuard(GuardInterface):
    def __init__(self, kerberos_app=None):
        super().__init__("instagram_analyzer")
        self.kerberos, self.is_running = kerberos_app, False
        self.stats = {"frames_analyzed": 0, "beauty_filters": 0, "color_grading": 0}
        logger.info("📸 InstagramAnalyzerGuard initialisé")

    def analyze_frame(self, frame: np.ndarray, metadata: Dict[str, Any] = None) -> Dict[str, Any]:
        if frame is None: return {"suspicion_score": 0.0, "details": []}
        self.stats["frames_analyzed"] += 1
        results = {"suspicion_score": 0.0, "details": [], "filters_applied": []}
        
        h, w = frame.shape[:2]
        if 0.9 <= (h / w) <= 1.1: results["details"].append("Format carré Instagram")
        elif 1.5 <= (h / w) <= 2.0: results["details"].append("Format vertical Reels")
        
        try:
            hsv = cv2.cvtColor(frame, cv2.COLOR_BGR2HSV)
            avg_sat, avg_val = np.mean(hsv[:,:,1]), np.mean(hsv[:,:,2])
            if avg_sat > 150 and avg_val > 180:
                results["filters_applied"].append("color_grading")
                results["suspicion_score"] += 0.3
                self.stats["color_grading"] += 1
        except: pass
        
        results["suspicion_score"] = min(1.0, results["suspicion_score"])
        return results

    def start(self): self.is_running = True
    def stop(self): self.is_running = False
    def get_stats(self) -> Dict[str, Any]: return self.stats.copy()

_guard_instance = None
def start_guard(kerberos_app=None):
    global _guard_instance; _guard_instance = InstagramAnalyzerGuard(kerberos_app); return _guard_instance
def stop_guard():
    global _guard_instance
    if _guard_instance: _guard_instance.stop()
def get_stats():
    global _guard_instance; return _guard_instance.get_stats() if _guard_instance else {}