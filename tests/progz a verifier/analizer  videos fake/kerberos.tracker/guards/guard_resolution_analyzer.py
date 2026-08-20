#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
📐 GUARD RESOLUTION ANALYZER — Détection Anomalies de Résolution
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
Version: 1.0.0
Author: Victor Pozen
License: GPLv3

Détecte :
- Upscaling IA (ESRGAN, Real-ESRGAN, etc.)
- Downscaling excessif (compression)
- Résolutions incohérentes (mix de qualités)
- Artefacts de super-résolution
"""
import cv2
import numpy as np
import logging
from typing import Dict, Any
from guards.guard_interface import GuardInterface
logger = logging.getLogger(__name__)

class ResolutionAnalyzerGuard(GuardInterface):
    """Guard d'analyse de résolution et détection upscaling/downscaling"""
    
    def __init__(self, kerberos_app=None):
        super().__init__("resolution_analyzer")
        self.kerberos = kerberos_app
        self.is_running = False
        
        self.stats = {
            "frames_analyzed": 0,
            "upscaling_detected": 0,
            "downscaling_detected": 0,
            "resolution_anomalies": 0
        }
        
        # Seuils de détection
        self.thresholds = {
            "edge_blur_ratio": 0.3,      # Ratio flou bords/centre
            "texture_consistency": 0.7,  # Cohérence texture
            "sharpness_variance": 100,   # Variance de netteté
            "pixelation_score": 0.5      # Score de pixellisation
        }
        
        logger.info("📐 ResolutionAnalyzerGuard initialisé")
    
    def analyze_frame(self, frame: np.ndarray, metadata: Dict[str, Any] = None) -> Dict[str, Any]:
        """Analyse la résolution et détecte les anomalies"""
        if frame is None:
            return {"suspicion_score": 0.0, "details": [], "resolution_issues": []}
        
        self.stats["frames_analyzed"] += 1
        
        results = {
            "suspicion_score": 0.0,
            "details": [],
            "resolution_issues": [],
            "upscaling_probability": 0.0,
            "downscaling_probability": 0.0
        }
        
        h, w = frame.shape[:2]
        gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
        
        # 1. Détection upscaling IA (ESRGAN, etc.)
        upscale_score = self._detect_upscaling(gray, frame)
        if upscale_score > 0.6:
            results["resolution_issues"].append("upscaling_ia")
            results["upscaling_probability"] = upscale_score
            results["suspicion_score"] += upscale_score * 0.5
            self.stats["upscaling_detected"] += 1
            results["details"].append(f"Upscaling IA détecté ({upscale_score:.2f})")
        
        # 2. Détection downscaling excessif
        downscale_score = self._detect_downscaling(gray)
        if downscale_score > 0.6:
            results["resolution_issues"].append("downscaling_excessif")
            results["downscaling_probability"] = downscale_score
            results["suspicion_score"] += downscale_score * 0.3
            self.stats["downscaling_detected"] += 1
            results["details"].append(f"Downscaling excessif ({downscale_score:.2f})")
        
        # 3. Incohérence de résolution (zones de qualités différentes)
        inconsistency_score = self._detect_resolution_inconsistency(gray)
        if inconsistency_score > 0.7:
            results["resolution_issues"].append("incoherence_resolution")
            results["suspicion_score"] += inconsistency_score * 0.4
            self.stats["resolution_anomalies"] += 1
            results["details"].append(f"Incohérence résolution ({inconsistency_score:.2f})")
        
        # 4. Artefacts de super-résolution
        sr_artifacts = self._detect_super_resolution_artifacts(gray)
        if sr_artifacts > 0.5:
            results["resolution_issues"].append("artefacts_super_resolution")
            results["suspicion_score"] += sr_artifacts * 0.4
            results["details"].append(f"Artefacts super-résolution ({sr_artifacts:.2f})")
        
        results["suspicion_score"] = min(1.0, results["suspicion_score"])
        
        return results
    
    def _detect_upscaling(self, gray: np.ndarray, frame: np.ndarray) -> float:
        """
        Détecte l'upscaling IA (ESRGAN, Real-ESRGAN)
        Signes : bords flous mais centre net, textures trop régulières
        """
        try:
            h, w = gray.shape
            
            # 1. Comparer netteté centre vs bords
            center_y, center_x = h // 2, w // 2
            center_region = gray[center_y-50:center_y+50, center_x-50:center_x+50]
            
            # Bords (4 coins)
            corners = [
                gray[0:100, 0:100],
                gray[0:100, w-100:w],
                gray[h-100:h, 0:100],
                gray[h-100:h, w-100:w]
            ]
            
            # Calculer la netteté (variance du Laplacian)
            center_sharpness = cv2.Laplacian(center_region, cv2.CV_64F).var()
            corner_sharpness = np.mean([cv2.Laplacian(c, cv2.CV_64F).var() for c in corners])
            
            # Ratio centre/bords (si > 2 = centre beaucoup plus net = upscaling)
            sharpness_ratio = center_sharpness / (corner_sharpness + 1)
            
            # 2. Détecter les textures trop régulières (artefacts ESRGAN)
            # ESRGAN crée des motifs répétitifs
            edges = cv2.Canny(gray, 50, 150)
            edge_density = np.sum(edges > 0) / edges.size
            
            # 3. Score composite
            upscaling_score = 0.0
            if sharpness_ratio > 2.0:
                upscaling_score += 0.4
            if edge_density < 0.05:  # Trop peu de détails fins
                upscaling_score += 0.3
            if center_sharpness > 1000 and corner_sharpness < 200:
                upscaling_score += 0.3
            
            return min(1.0, upscaling_score)
        except:
            return 0.0
    
    def _detect_downscaling(self, gray: np.ndarray) -> float:
        """
        Détecte le downscaling excessif (compression)
        Signes : pixellisation, perte de détails, blocs visibles
        """
        try:
            h, w = gray.shape
            
            # 1. Détecter la pixellisation (blocs de 8x8 visibles)
            # Réduire l'image et la comparer à l'originale
            small = cv2.resize(gray, (w // 4, h // 4), interpolation=cv2.INTER_AREA)
            reconstructed = cv2.resize(small, (w, h), interpolation=cv2.INTER_CUBIC)
            
            # Différence entre originale et reconstruite
            diff = cv2.absdiff(gray, reconstructed)
            pixelation_score = np.mean(diff) / 255.0
            
            # 2. Perte de détails (faible variance du Laplacian)
            detail_loss = cv2.Laplacian(gray, cv2.CV_64F).var()
            
            # 3. Score composite
            downscaling_score = 0.0
            if pixelation_score > 15:  # Pixellisation visible
                downscaling_score += 0.5
            if detail_loss < 50:  # Très peu de détails
                downscaling_score += 0.3
            if pixelation_score > 25:
                downscaling_score += 0.2
            
            return min(1.0, downscaling_score)
        except:
            return 0.0
    
    def _detect_resolution_inconsistency(self, gray: np.ndarray) -> float:
        """
        Détecte les incohérences de résolution (zones de qualités différentes)
        Signes : certaines zones très nettes, d'autres floues
        """
        try:
            h, w = gray.shape
            
            # Diviser l'image en 9 zones
            zone_h, zone_w = h // 3, w // 3
            zones = []
            
            for i in range(3):
                for j in range(3):
                    zone = gray[i*zone_h:(i+1)*zone_h, j*zone_w:(j+1)*zone_w]
                    sharpness = cv2.Laplacian(zone, cv2.CV_64F).var()
                    zones.append(sharpness)
            
            # Calculer la variance entre les zones
            variance = np.std(zones)
            mean_sharpness = np.mean(zones)
            
            # Coefficient de variation (si > 0.5 = très incohérent)
            cv_score = variance / (mean_sharpness + 1)
            
            return min(1.0, cv_score)
        except:
            return 0.0
    
    def _detect_super_resolution_artifacts(self, gray: np.ndarray) -> float:
        """
        Détecte les artefacts spécifiques à la super-résolution IA
        Signes : halos autour des bords, textures "plastiques"
        """
        try:
            # 1. Détecter les halos (overshooting)
            edges = cv2.Canny(gray, 50, 150)
            dilated_edges = cv2.dilate(edges, np.ones((3,3), np.uint8), iterations=2)
            halo_region = cv2.subtract(dilated_edges, edges)
            halo_score = np.sum(halo_region > 0) / halo_region.size
            
            # 2. Détecter les textures "plastiques" (trop lisses)
            # Calculer la variance locale
            kernel = np.ones((5,5), np.float32) / 25
            mean_img = cv2.filter2D(gray.astype(np.float32), -1, kernel)
            variance_local = cv2.filter2D((gray.astype(np.float32) - mean_img)**2, -1, kernel)
            
            # Si variance locale très faible = texture trop uniforme
            uniform_score = 1.0 - (np.mean(variance_local) / 1000.0)
            
            # 3. Score composite
            sr_score = (halo_score * 0.5) + (max(0, uniform_score) * 0.5)
            
            return min(1.0, sr_score)
        except:
            return 0.0
    
    def start(self):
        self.is_running = True
        logger.info("📐 ResolutionAnalyzerGuard démarré")
    
    def stop(self):
        self.is_running = False
        logger.info(" ResolutionAnalyzerGuard arrêté")
    
    def get_stats(self) -> Dict[str, Any]:
        return self.stats.copy()

# Fonctions globales
_guard_instance = None

def start_guard(kerberos_app=None):
    global _guard_instance
    _guard_instance = ResolutionAnalyzerGuard(kerberos_app)
    return _guard_instance

def stop_guard():
    global _guard_instance
    if _guard_instance:
        _guard_instance.stop()

def get_stats():
    global _guard_instance
    return _guard_instance.get_stats() if _guard_instance else {}