#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""📱 GUARD DEVICE DETECTOR — Détection d'Appareils par Sondes"""
import cv2, numpy as np, logging, threading
from typing import Dict, Any, List, Optional  # ✅ FIX: Optional ajouté
from abc import ABC, abstractmethod
from guards.guard_interface import GuardInterface
logger = logging.getLogger(__name__)

class DeviceSonde(ABC):
    def __init__(self, name: str, weight: float = 1.0):
        self.name, self.weight, self.is_active = name, weight, True
    @abstractmethod
    def probe(self, frame: np.ndarray, metadata: Dict[str, Any] = None) -> Dict[str, Any]: pass

class ResolutionSonde(DeviceSonde):
    def __init__(self): super().__init__("resolution", 0.8)
    def probe(self, frame: np.ndarray, metadata: Dict[str, Any] = None) -> Dict[str, Any]:
        if frame is None: return {"label": "Unknown", "confidence": 0.0, "details": "Invalide"}
        h, w = frame.shape[:2]
        if h > w and w < 1080: return {"label": "Smartphone", "confidence": 0.85, "details": f"{w}x{h} Portrait"}
        elif w >= 1920: return {"label": "Professional", "confidence": 0.8, "details": f"{w}x{h} HD"}
        return {"label": "Webcam", "confidence": 0.7, "details": f"{w}x{h}"}

class NoiseSonde(DeviceSonde):
    def __init__(self): super().__init__("noise", 1.0)
    def probe(self, frame: np.ndarray, metadata: Dict[str, Any] = None) -> Dict[str, Any]:
        if frame is None: return {"label": "Unknown", "confidence": 0.0, "details": "Invalide"}
        try:
            noise = cv2.Laplacian(cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY), cv2.CV_64F).var()
            if noise > 500: return {"label": "Professional", "confidence": 0.75, "details": f"Bruit élevé ({noise:.0f})"}
            elif noise > 150: return {"label": "Smartphone", "confidence": 0.6, "details": f"Bruit moyen ({noise:.0f})"}
            return {"label": "Webcam", "confidence": 0.55, "details": f"Bruit faible ({noise:.0f})"}
        except: return {"label": "Unknown", "confidence": 0.0, "details": "Erreur"}

class DeviceDetectorGuard(GuardInterface):
    def __init__(self, kerberos_app=None):
        super().__init__("device_detector")
        self.kerberos, self.is_running, self._lock = kerberos_app, False, threading.Lock()
        self.sondes: List[DeviceSonde] = [ResolutionSonde(), NoiseSonde()]
        self.stats = {"frames_analyzed": 0, "device_predictions": {"Smartphone": 0, "Webcam": 0, "Professional": 0, "Unknown": 0}}
        logger.info(f"📱 DeviceDetectorGuard initialisé ({len(self.sondes)} sondes)")

    def analyze_frame(self, frame: np.ndarray, metadata: Dict[str, Any] = None) -> Dict[str, Any]:
        if frame is None: return {"device": "Unknown", "confidence": 0.0, "details": []}
        with self._lock: self.stats["frames_analyzed"] += 1
        
        results, total_weight, details_parts = [], 0.0, []
        for sonde in self.sondes:
            if not sonde.is_active: continue
            try:
                r = sonde.probe(frame, metadata)
                r["sonde"], r["weight"] = sonde.name, sonde.weight
                results.append(r)
            except Exception as e: logger.debug(f"Erreur sonde {sonde.name}: {e}")
        
        device_votes = {"Smartphone": 0.0, "Webcam": 0.0, "Professional": 0.0, "Unknown": 0.0}
        for r in results:
            if r["label"] in device_votes:
                device_votes[r["label"]] += r["confidence"] * r["weight"]
                total_weight += r["weight"]
                details_parts.append(f"{r['sonde']}:{r['label']}({r['confidence']:.2f})")
        
        if total_weight > 0:
            for d in device_votes: device_votes[d] /= total_weight
        
        winner = max(device_votes, key=device_votes.get)
        with self._lock:
            if winner in self.stats["device_predictions"]: self.stats["device_predictions"][winner] += 1
        
        return {"device": winner, "confidence": round(device_votes[winner], 3), "details": " | ".join(details_parts)}

    def start(self): self.is_running = True
    def stop(self): self.is_running = False
    def get_stats(self) -> Dict[str, Any]:
        with self._lock: return self.stats.copy()

_guard_instance: Optional[DeviceDetectorGuard] = None
def start_guard(kerberos_app=None) -> Optional[DeviceDetectorGuard]:
    global _guard_instance; _guard_instance = DeviceDetectorGuard(kerberos_app); return _guard_instance
def stop_guard() -> None:
    global _guard_instance
    if _guard_instance: _guard_instance.stop(); _guard_instance = None
def get_stats() -> Dict[str, Any]:
    global _guard_instance; return _guard_instance.get_stats() if _guard_instance else {}