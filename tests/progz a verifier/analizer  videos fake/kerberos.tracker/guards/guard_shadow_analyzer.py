#!/usr/bin/env python3
# -*- coding: utf-8 -*-
""" GUARD SHADOW ANALYZER v2.1 — FIX SEUIL TOLÉRANT"""
import cv2, numpy as np, logging
from typing import Dict, Any
from guards.guard_interface import GuardInterface
logger = logging.getLogger(__name__)

class ShadowAnalyzerGuard(GuardInterface):
    def __init__(self, kerberos_app=None):
        super().__init__("shadow_analyzer")
        self.kerberos, self.is_running = kerberos_app, False
        self.shadow_threshold = -40  # ✅ FIX: Plus tolérant
        self.stats = {"frames_analyzed": 0, "floating_objects": 0, "shadow_inconsistencies": 0}
        logger.info(f"🌑 ShadowAnalyzerGuard v2.1 initialisé (seuil: {self.shadow_threshold})")

    def analyze_frame(self, frame: np.ndarray, metadata: Dict[str, Any] = None) -> Dict[str, Any]:
        if frame is None: return {"suspicion_score": 0.0, "details": []}
        self.stats["frames_analyzed"] += 1
        results = {"suspicion_score": 0.0, "details": [], "issues": []}
        gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
        h, w = gray.shape
        
        edges = cv2.Canny(gray, 50, 150)
        contours, _ = cv2.findContours(edges, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
        
        if contours:
            main_contour = max(contours, key=cv2.contourArea)
            x, y, w_obj, h_obj = cv2.boundingRect(main_contour)
            check_y_start = y + h_obj
            check_y_end = min(h, check_y_start + 20)
            
            if check_y_end < h and w_obj > 50 and h_obj > 50:
                region_below = gray[check_y_start:check_y_end, x:x+w_obj]
                object_region = gray[y:y+h_obj, x:x+w_obj]
                avg_brightness_below = np.mean(region_below)
                avg_brightness_object = np.mean(object_region)
                
                if avg_brightness_below > avg_brightness_object + self.shadow_threshold:
                    results["suspicion_score"] += 0.6
                    results["details"].append(f"Objet flottant détecté (Pas d'ombre de contact)")
                    results["issues"].append("floating_object")
                    self.stats["floating_objects"] += 1
        
        dark_regions = cv2.inRange(gray, 0, 50)
        if np.sum(dark_regions > 0) > 1000:
            shadow_variance = np.std(gray[dark_regions > 0])
            if shadow_variance < 8.0:
                results["suspicion_score"] += 0.4
                results["details"].append(f"Ombres trop uniformes (Variance: {shadow_variance:.1f})")
                results["issues"].append("uniform_shadows")
                self.stats["shadow_inconsistencies"] += 1
                
        results["suspicion_score"] = min(1.0, results["suspicion_score"])
        return results

    def start(self): self.is_running = True
    def stop(self): self.is_running = False
    def get_stats(self) -> Dict[str, Any]: return self.stats.copy()

_guard_instance = None
def start_guard(kerberos_app=None):
    global _guard_instance; _guard_instance = ShadowAnalyzerGuard(kerberos_app); return _guard_instance
def stop_guard():
    global _guard_instance
    if _guard_instance: _guard_instance.stop()
def get_stats():
    global _guard_instance; return _guard_instance.get_stats() if _guard_instance else {}