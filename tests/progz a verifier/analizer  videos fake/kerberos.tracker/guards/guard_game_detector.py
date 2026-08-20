#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Guard Game Detector — Détection gameplay"""
import cv2, numpy as np, logging
from guards.guard_interface import GuardInterface
logger = logging.getLogger(__name__)

class GameDetectorGuard(GuardInterface):
    def __init__(self, kerberos_app=None):
        super().__init__("game_detector")
        self.kerberos = kerberos_app; self.is_running = False
        self.stats = {"frames_analyzed": 0, "game_detected": 0, "real_world_detected": 0}
        self.thresholds = {"hud_edge_density": 0.15, "global_edge_density": 0.25, "saturation_std": 45}
    
    def analyze_frame(self, frame: np.ndarray):
        if frame is None: return {"is_game": False, "confidence": 0.0}
        self.stats["frames_analyzed"] += 1; scores = []
        gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY); hsv = cv2.cvtColor(frame, cv2.COLOR_BGR2HSV); h, w = gray.shape
        margin_h, margin_w = int(h * 0.15), int(w * 0.15)
        corners = [gray[0:margin_h, 0:margin_w], gray[0:margin_h, w-margin_w:w], gray[h-margin_h:h, 0:margin_w], gray[h-margin_h:h, w-margin_w:w]]
        hud_hits = sum(1 for corner in corners if np.sum(cv2.Canny(corner, 50, 150) > 0) / (corner.shape[0] * corner.shape[1]) > self.thresholds["hud_edge_density"])
        scores.append(min(1.0, hud_hits / 2.0))
        edges = cv2.Canny(gray, 50, 150); density = np.sum(edges > 0) / (gray.shape[0] * gray.shape[1])
        scores.append(0.8 if density > self.thresholds["global_edge_density"] else 0.2)
        sat_std = np.std(hsv[:,:,1]); scores.append(0.75 if sat_std > self.thresholds["saturation_std"] else 0.3)
        confidence = np.mean(scores); is_game = confidence > 0.55
        if is_game: self.stats["game_detected"] += 1
        else: self.stats["real_world_detected"] += 1
        return {"is_game": is_game, "confidence": float(confidence)}
    
    def start(self): self.is_running = True
    def stop(self): self.is_running = False
    def get_stats(self): return self.stats.copy()

_guard_instance = None
def start_guard(kerberos_app=None):
    global _guard_instance; _guard_instance = GameDetectorGuard(kerberos_app); return _guard_instance
def stop_guard():
    global _guard_instance
    if _guard_instance: _guard_instance.stop()