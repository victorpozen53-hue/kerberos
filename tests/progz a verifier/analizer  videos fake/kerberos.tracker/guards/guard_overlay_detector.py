#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Guard Overlay Detector — Détection incrustations"""
import cv2, numpy as np, logging
from guards.guard_interface import GuardInterface
logger = logging.getLogger(__name__)

class OverlayDetectorGuard(GuardInterface):
    def __init__(self, kerberos_app=None):
        super().__init__("overlay_detector")
        self.kerberos = kerberos_app; self.is_running = False
        self.stats = {"frames_analyzed": 0, "overlays_detected": 0, "logos_found": 0, "text_found": 0}
    
    def analyze_frame(self, frame: np.ndarray, frame_number: int = 0):
        if frame is None: return {"overlays": [], "count": 0}
        self.stats["frames_analyzed"] += 1; results = {"overlays": [], "logos": [], "text_regions": [], "count": 0}
        gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY); h, w = gray.shape
        corner_regions = {"top_left": (0, 0, int(w * 0.2), int(h * 0.15)), "top_right": (int(w * 0.8), 0, w, int(h * 0.15)), "bottom_left": (0, int(h * 0.85), int(w * 0.2), h), "bottom_right": (int(w * 0.8), int(h * 0.85), w, h)}
        for corner_name, (x1, y1, x2, y2) in corner_regions.items():
            roi = gray[y1:y2, x1:x2]; edges = cv2.Canny(roi, 50, 150)
            edge_density = np.sum(edges > 0) / (roi.shape[0] * roi.shape[1])
            if edge_density > 0.08: results["logos"].append({"type": "logo", "position": corner_name, "confidence": min(1.0, edge_density * 5)}); self.stats["logos_found"] += 1
        results["overlays"].extend(results["logos"]); results["count"] = len(results["overlays"])
        if results["count"] > 0: self.stats["overlays_detected"] += 1
        return results
    
    def start(self): self.is_running = True
    def stop(self): self.is_running = False
    def get_stats(self): return self.stats.copy()

_guard_instance = None
def start_guard(kerberos_app=None):
    global _guard_instance; _guard_instance = OverlayDetectorGuard(kerberos_app); return _guard_instance
def stop_guard():
    global _guard_instance
    if _guard_instance: _guard_instance.stop()