#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
🔍 GUARD VISUAL ANOMALY — Détecteur d'Anomalies Visuelles (Temps Réel)
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
Version: 1.0.0
Author: Victor Pozen
License: GPLv3

Détecte en temps réel :
- Flou artistique / Motion blur
- Images trop nettes (over-sharpness)
- Images trop lisses (over-smoothing / IA)
- Bruit de capteur anormal
- Artefacts de compression
- Incohérences de lumière
- Objets flottants (ombres manquantes)
"""
import cv2
import numpy as np
import logging
from typing import Dict, Any
from guards.guard_interface import GuardInterface

logger = logging.getLogger(__name__)

class VisualAnomalyGuard(GuardInterface):
    def __init__(self, kerberos_app=None):
        super().__init__("visual_anomaly")
        self.kerberos = kerberos_app
        self.is_running = False
        
        # Seuils de détection (ajustables)
        self.thresholds = {
            "blur_max": 500,       # Au-dessus = trop net
            "smoothness_max": 30,  # En dessous = trop lisse (IA)
            "noise_min": 10,       # En dessous = bruit absent (IA)
            "compression_max": 0.3 # Au-dessus = artefacts compression
        }
        
        self.stats = {
            "frames_analyzed": 0,
            "blurry_frames": 0,
            "oversharp_frames": 0,
            "oversmooth_frames": 0,
            "noisy_frames": 0,
            "compressed_frames": 0,
            "anomalous_frames": 0
        }
        logger.info("🔍 VisualAnomalyGuard initialisé (7 moteurs d'analyse)")

    def _calculate_blur_score(self, frame: np.ndarray) -> float:
        """Détecte le flou artistique (motion blur, gaussian blur). Retourne 0-100."""
        gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
        laplacian_var = cv2.Laplacian(gray, cv2.CV_64F).var()
        gaussian_blur_score = max(0, 100 - (laplacian_var / 10))
        return gaussian_blur_score

    def _calculate_noise_level(self, frame: np.ndarray) -> float:
        """Mesure le bruit de capteur. Faible = image trop lisse (IA)."""
        gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
        flat_mask = cv2.inRange(gray, 100, 150)
        if np.sum(flat_mask > 0) > 1000:
            return np.std(gray[flat_mask > 0])
        return np.std(gray)

    def _calculate_smoothness(self, frame: np.ndarray) -> float:
        """Détecte si l'image est trop lisse (over-smoothing IA)."""
        gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY).astype(np.float32)
        kernel = np.ones((5, 5), np.float32) / 25
        mean_img = cv2.filter2D(gray, -1, kernel)
        variance_map = cv2.filter2D((gray - mean_img)**2, -1, kernel)
        return np.mean(variance_map)

    def _detect_compression_artifacts(self, frame: np.ndarray) -> float:
        """Détecte les artefacts de compression (blocs 8x8, ringing)."""
        gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
        h, w = gray.shape
        small = cv2.resize(gray, (w // 8, h // 8), interpolation=cv2.INTER_AREA)
        reconstructed = cv2.resize(small, (w, h), interpolation=cv2.INTER_CUBIC)
        diff = cv2.absdiff(gray, reconstructed)
        return np.mean(diff) / 255.0

    def _analyze_lighting_consistency(self, frame: np.ndarray) -> float:
        """Vérifie la cohérence de l'éclairage (IA = lumières incohérentes)."""
        gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
        h, w = gray.shape
        zone_h, zone_w = h // 3, w // 3
        zone_brightness = []
        for i in range(3):
            for j in range(3):
                zone = gray[i*zone_h:(i+1)*zone_h, j*zone_w:(j+1)*zone_w]
                zone_brightness.append(np.mean(zone))
        mean_brightness = np.mean(zone_brightness)
        if mean_brightness > 0:
            return np.std(zone_brightness) / mean_brightness
        return 0

    def _detect_floating_objects(self, frame: np.ndarray) -> bool:
        """Détecte les objets flottants (pas d'ombre de contact)."""
        gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
        h, w = gray.shape
        edges = cv2.Canny(gray, 50, 150)
        contours, _ = cv2.findContours(edges, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
        if not contours: return False
        
        main_contour = max(contours, key=cv2.contourArea)
        x, y, w_obj, h_obj = cv2.boundingRect(main_contour)
        check_y_start = y + h_obj
        check_y_end = min(h, check_y_start + 20)
        
        if check_y_end < h and w_obj > 50 and h_obj > 50:
            region_below = gray[check_y_start:check_y_end, x:x+w_obj]
            object_region = gray[y:y+h_obj, x:x+w_obj]
            avg_below = np.mean(region_below)
            avg_object = np.mean(object_region)
            if avg_below > avg_object - 15:
                return True
        return False

    def analyze_frame(self, frame: np.ndarray, metadata: Dict[str, Any] = None) -> Dict[str, Any]:
        """Analyse complète d'une frame pour le système de vote Kerberos."""
        if frame is None:
            return {"suspicion_score": 0.0, "details": []}
        
        self.stats["frames_analyzed"] += 1
        details = []
        anomaly_score = 0.0
        
        # 1. Flou artistique
        blur_score = self._calculate_blur_score(frame)
        if blur_score > 70:
            details.append(f"Flou artistique détecté ({blur_score:.0f})")
            anomaly_score += 0.3
            self.stats["blurry_frames"] += 1
            
        # 2. Image trop nette
        sharpness = cv2.Laplacian(cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY), cv2.CV_64F).var()
        if sharpness > self.thresholds["blur_max"]:
            details.append(f"Image trop nette (over-sharpness: {sharpness:.0f})")
            anomaly_score += 0.2
            self.stats["oversharp_frames"] += 1
            
        # 3. Image trop lisse (IA)
        smoothness = self._calculate_smoothness(frame)
        if smoothness < self.thresholds["smoothness_max"]:
            details.append(f"Image trop lisse (over-smoothing IA)")
            anomaly_score += 0.3
            self.stats["oversmooth_frames"] += 1
            
        # 4. Bruit insuffisant
        noise_level = self._calculate_noise_level(frame)
        if noise_level < self.thresholds["noise_min"]:
            details.append(f"Bruit de capteur absent (suspect IA: {noise_level:.1f})")
            anomaly_score += 0.4
            self.stats["noisy_frames"] += 1
            
        # 5. Artefacts de compression
        compression = self._detect_compression_artifacts(frame)
        if compression > self.thresholds["compression_max"]:
            details.append(f"Artefacts de compression excessifs")
            anomaly_score += 0.2
            self.stats["compressed_frames"] += 1
            
        # 6. Lumière incohérente
        lighting = self._analyze_lighting_consistency(frame)
        if lighting > 0.5:
            details.append(f"Éclairage incohérent (dispersion: {lighting:.2f})")
            anomaly_score += 0.3
            
        # 7. Objet flottant
        if self._detect_floating_objects(frame):
            details.append("Objet flottant (ombre manquante)")
            anomaly_score += 0.5
            
        # Normalisation et stats
        anomaly_score = min(1.0, anomaly_score)
        if anomaly_score > 0.5:
            self.stats["anomalous_frames"] += 1
            
        return {
            "suspicion_score": float(anomaly_score),
            "details": details,
            "metrics": {
                "blur": blur_score,
                "sharpness": sharpness,
                "noise": noise_level,
                "smoothness": smoothness
            }
        }

    def start(self):
        self.is_running = True
        logger.info("🔍 VisualAnomalyGuard démarré")
        
    def stop(self):
        self.is_running = False
        logger.info("🔍 VisualAnomalyGuard arrêté")
        
    def get_stats(self) -> Dict[str, Any]:
        return self.stats.copy()

# Fonctions globales pour le GuardManager
_guard_instance = None

def start_guard(kerberos_app=None):
    global _guard_instance
    _guard_instance = VisualAnomalyGuard(kerberos_app)
    return _guard_instance

def stop_guard():
    global _guard_instance
    if _guard_instance:
        _guard_instance.stop()

def get_stats():
    global _guard_instance
    return _guard_instance.get_stats() if _guard_instance else {}