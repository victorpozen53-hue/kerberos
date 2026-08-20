#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Guard Animal Detector — Détection animaux"""
import cv2, numpy as np, logging
from pathlib import Path
from guards.guard_interface import GuardInterface
logger = logging.getLogger(__name__)

class AnimalDetectorGuard(GuardInterface):
    def __init__(self, kerberos_app=None):
        super().__init__("animal_detector")
        self.kerberos = kerberos_app; self.net = self._load_model()
        self.TARGET_CLASSES = {3: "bird", 8: "cat", 10: "cow", 12: "dog", 14: "horse", 17: "sheep"}
        self.stats = {"frames_analyzed": 0, "animals_detected": {}, "total_animals": 0}
    
    def _load_model(self):
        prototxt = Path("guards/models/MobileNetSSD_deploy.prototxt"); model = Path("guards/models/MobileNetSSD_deploy.caffemodel")
        if prototxt.exists() and model.exists(): return cv2.dnn.readNetFromCaffe(str(prototxt), str(model))
        return None
    
    def analyze_frame(self, frame):
        if self.net is None or frame is None: return 0
        h, w = frame.shape[:2]; blob = cv2.dnn.blobFromImage(cv2.resize(frame, (300, 300)), 0.007843, (300, 300), 127.5)
        self.net.setInput(blob); detections = self.net.forward(); count = 0
        for i in range(detections.shape[2]):
            if detections[0, 0, i, 2] > 0.5:
                idx = int(detections[0, 0, i, 1])
                if idx in self.TARGET_CLASSES:
                    label = self.TARGET_CLASSES[idx]; self.stats["animals_detected"][label] = self.stats["animals_detected"].get(label, 0) + 1; count += 1
        self.stats["frames_analyzed"] += 1; self.stats["total_animals"] += count
        return count
    
    def start(self): self.is_running = True
    def stop(self): self.is_running = False
    def get_stats(self): return self.stats.copy()

_guard_instance = None
def start_guard(kerberos_app=None):
    global _guard_instance; _guard_instance = AnimalDetectorGuard(kerberos_app); return _guard_instance
def stop_guard():
    global _guard_instance
    if _guard_instance: _guard_instance.stop()