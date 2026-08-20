#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""🎵 GUARD TIKTOK ANALYZER — Détection Spécialisée TikTok"""
import cv2, numpy as np, logging
from typing import Dict, Any
from guards.guard_interface import GuardInterface
logger = logging.getLogger(__name__)

class TikTokAnalyzerGuard(GuardInterface):
    def __init__(self, kerberos_app=None):
        super().__init__("tiktok_analyzer")
        self.kerberos, self.is_running = kerberos_app, False
        self.stats = {"frames_analyzed": 0, "tiktok_filters_detected": 0, "beauty_filters": 0}
        logger.info("🎵 TikTokAnalyzerGuard initialisé")

    def analyze_frame(self, frame: np.ndarray, metadata: Dict[str, Any] = None) -> Dict[str, Any]:
        if frame is None: return {"suspicion_score": 0.0, "details": []}
        self.stats["frames_analyzed"] += 1
        results = {"suspicion_score": 0.0, "details": [], "filters_detected": []}
        
        h, w = frame.shape[:2]
        if 1.5 <= (h / w) <= 2.0: results["details"].append("Format vertical TikTok")
        
        try:
            hsv = cv2.cvtColor(frame, cv2.COLOR_BGR2HSV)
            skin_mask = cv2.inRange(hsv, np.array([0, 48, 0]), np.array([20, 255, 255]))
            if np.sum(skin_mask > 0) > 1000:
                variance = np.var(frame[skin_mask > 0])
                if variance < 1500:
                    results["filters_detected"].append("beauty_filter")
                    results["suspicion_score"] += 0.4
                    self.stats["beauty_filters"] += 1
        except: pass
        
        if results["filters_detected"]: self.stats["tiktok_filters_detected"] += 1
        results["suspicion_score"] = min(1.0, results["suspicion_score"])
        return results

    def start(self): self.is_running = True
    def stop(self): self.is_running = False
    def get_stats(self) -> Dict[str, Any]: return self.stats.copy()

_guard_instance = None
def start_guard(kerberos_app=None):
    global _guard_instance; _guard_instance = TikTokAnalyzerGuard(kerberos_app); return _guard_instance
def stop_guard():
    global _guard_instance
    if _guard_instance: _guard_instance.stop()
def get_stats():
    global _guard_instance; return _guard_instance.get_stats() if _guard_instance else {}