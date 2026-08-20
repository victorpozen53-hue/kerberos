#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Guard Face Analyzer — Analyse visages"""
import cv2, numpy as np, logging
from guards.guard_interface import GuardInterface
logger = logging.getLogger(__name__)

class FaceAnalyzerGuard(GuardInterface):
    def __init__(self, kerberos_app=None):
        super().__init__("face_analyzer")
        self.kerberos = kerberos_app
        self.face_cascade = cv2.CascadeClassifier(cv2.data.haarcascades + 'haarcascade_frontalface_default.xml')
        self.stats = {"faces_detected": 0, "anomalies": 0}
    
    def analyze(self, frame):
        if frame is None: return []
        gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
        faces = self.face_cascade.detectMultiScale(gray, 1.1, 5, minSize=(30, 30))
        results = []
        for (x, y, w, h) in faces:
            face_roi = gray[y:y+h, x:x+w]
            blur = cv2.Laplacian(face_roi, cv2.CV_64F).var()
            is_coherent = blur > 80
            results.append({"bbox": (x, y, w, h), "blur_score": float(blur), "coherent": is_coherent})
            self.stats["faces_detected"] += 1
            if not is_coherent: self.stats["anomalies"] += 1
        return results
    
    def start(self): self.is_running = True
    def stop(self): self.is_running = False
    def get_stats(self): return self.stats.copy()

_guard_instance = None
def start_guard(kerberos_app=None):
    global _guard_instance; _guard_instance = FaceAnalyzerGuard(kerberos_app); return _guard_instance
def stop_guard():
    global _guard_instance
    if _guard_instance: _guard_instance.stop()