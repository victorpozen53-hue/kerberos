#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""🔬 GUARD PIXEL DENSITY v1.1 — FIX SEUIL TIKTOK"""
import cv2, numpy as np, logging
from typing import Dict, Any
from guards.guard_interface import GuardInterface
logger = logging.getLogger(__name__)

class PixelDensityGuard(GuardInterface):
    def __init__(self, kerberos_app=None):
        super().__init__("pixel_density")
        self.kerberos, self.is_running, self.is_active = kerberos_app, False, True
        self.stats = {"frames_analyzed": 0, "fake_high_res_detected": 0, "natural_noise_detected": 0}
        self.noise_floor_threshold = 3.5
        logger.info("🔬 PixelDensityGuard v1.1 initialisé")

    def analyze_frame(self, frame: np.ndarray, metadata: Dict[str, Any] = None) -> Dict[str, Any]:
        if not self.is_active or frame is None: return {"suspicion_score": 0.0, "details": []}
        self.stats["frames_analyzed"] += 1
        results = {"suspicion_score": 0.0, "details": [], "is_fake_high_res": False}
        
        h, w = frame.shape[:2]
        total_pixels = h * w
        gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
        
        flat_mask = cv2.inRange(gray, 100, 150)
        noise_floor = np.std(gray[flat_mask > 0]) if np.sum(flat_mask > 0) > 1000 else np.std(gray)
        
        kernel = np.ones((3,3), np.float32) / 9
        mean_img = cv2.filter2D(gray.astype(np.float32), -1, kernel)
        variance_map = cv2.filter2D((gray.astype(np.float32) - mean_img)**2, -1, kernel)
        subpixel_variance = np.mean(variance_map)
        
        # ✅ FIX: Seuil abaissé à 500 000
        is_high_res = total_pixels > 500_000 
        
        if is_high_res:
            if noise_floor < self.noise_floor_threshold:
                results["is_fake_high_res"] = True
                results["suspicion_score"] += 0.8
                results["details"].append(f"Fausse HD : Bruit trop faible ({noise_floor:.2f})")
                self.stats["fake_high_res_detected"] += 1
            elif subpixel_variance < 50:
                results["suspicion_score"] += 0.6
                results["details"].append(f"Sub-pixel trop lisse ({subpixel_variance:.2f})")
            else:
                results["suspicion_score"] -= 0.2
                results["details"].append(f"Signature capteur OK (Bruit: {noise_floor:.2f})")
                self.stats["natural_noise_detected"] += 1
        
        results["suspicion_score"] = min(1.0, results["suspicion_score"])
        return results

    def start(self): self.is_running = True
    def stop(self): self.is_running = False
    def get_stats(self) -> Dict[str, Any]: return self.stats.copy()

_guard_instance = None
def start_guard(kerberos_app=None):
    global _guard_instance; _guard_instance = PixelDensityGuard(kerberos_app); return _guard_instance
def stop_guard():
    global _guard_instance
    if _guard_instance: _guard_instance.stop()
def get_stats():
    global _guard_instance; return _guard_instance.get_stats() if _guard_instance else {}