#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Guard Object Detector — Détection objets"""
import cv2, numpy as np, logging
from pathlib import Path
from guards.guard_interface import GuardInterface
logger = logging.getLogger(__name__)

class ObjectDetectorGuard(GuardInterface):
    def __init__(self, kerberos_app=None):
        super().__init__("object_detector")
        self.kerberos = kerberos_app; self.net = None
        self.CLASSES = ["background", "aeroplane", "bicycle", "bird", "boat", "bottle", "bus", "car", "cat", "chair", "cow", "diningtable", "dog", "horse", "motorbike", "person", "pottedplant", "sheep", "sofa", "train", "tvmonitor"]
        self.stats = {"total_frames": 0, "vehicles": 0, "objects": {}}
        self._load_model()
    
    def _load_model(self):
        prototxt = Path("guards/models/MobileNetSSD_deploy.prototxt"); model = Path("guards/models/MobileNetSSD_deploy.caffemodel")
        if prototxt.exists() and model.exists(): self.net = cv2.dnn.readNetFromCaffe(str(prototxt), str(model))
    
    def detect(self, frame):
        if self.net is None or frame is None: return []
        h, w = frame.shape[:2]; blob = cv2.dnn.blobFromImage(cv2.resize(frame, (300, 300)), 0.007843, (300, 300), 127.5)
        self.net.setInput(blob); detections = self.net.forward(); objects = []
        for i in range(detections.shape[2]):
            confidence = detections[0, 0, i, 2]
            if confidence > 0.5:
                idx = int(detections[0, 0, i, 1]); label = self.CLASSES[idx]
                objects.append({"class": label, "confidence": float(confidence)})
                self.stats["objects"][label] = self.stats["objects"].get(label, 0) + 1
                if label in ["car", "bus", "motorbike", "bicycle", "train"]: self.stats["vehicles"] += 1
        self.stats["total_frames"] += 1
        return objects
    
    def start(self): self.is_running = True
    def stop(self): self.is_running = False
    def get_stats(self): return self.stats.copy()

_guard_instance = None
def start_guard(kerberos_app=None):
    global _guard_instance; _guard_instance = ObjectDetectorGuard(kerberos_app); return _guard_instance
def stop_guard():
    global _guard_instance
    if _guard_instance: _guard_instance.stop()