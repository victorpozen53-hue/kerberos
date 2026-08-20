#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Guard Watermark Detector — Détection filigranes"""
import cv2, numpy as np, logging
from guards.guard_interface import GuardInterface
logger = logging.getLogger(__name__)

class WatermarkDetectorGuard(GuardInterface):
    def __init__(self, kerberos_app=None):
        super().__init__("watermark_detector")
        self.kerberos = kerberos_app
        self.stats = {"total": 0, "watermarks_detected": 0}
    
    def detect(self, frame):
        if frame is None: return False
        gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
        h, w = gray.shape
        zones = [gray[0:h//10, 0:w//10], gray[0:h//10, 9*w//10:w], gray[9*h//10:h, 0:w//10], gray[9*h//10:h, 9*w//10:w]]
        score = sum(1 for z in zones if np.sum(cv2.Canny(z, 50, 150) > 0) / (z.shape[0] * z.shape[1]) > 0.05)
        has_watermark = score >= 2
        self.stats["total"] += 1
        if has_watermark: self.stats["watermarks_detected"] += 1
        return has_watermark
    
    def start(self): self.is_running = True
    def stop(self): self.is_running = False
    def get_stats(self): return self.stats.copy()

_guard_instance = None
def start_guard(kerberos_app=None):
    global _guard_instance; _guard_instance = WatermarkDetectorGuard(kerberos_app); return _guard_instance
def stop_guard():
    global _guard_instance
    if _guard_instance: _guard_instance.stop()