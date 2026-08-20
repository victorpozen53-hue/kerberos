#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
🛡️ GUARD MULTILAYER ANALYZER — Analyse en 3 Couches
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
Version: 1.0.0
Author: Victor Pozen
License: GPLv3

Architecture en entonnoir :
- Couche 1 : Triage rapide (Metadata/Stats)
- Couche 2 : Analyse spatiale (Physique/Bruit/Ombres)
- Couche 3 : Analyse temporelle (Cohérence inter-frames)
"""
import cv2
import numpy as np
import logging
from collections import deque
from typing import Dict, Any, List
from guards.guard_interface import GuardInterface

logger = logging.getLogger(__name__)

class MultiLayerAnalyzerGuard(GuardInterface):
    def __init__(self, kerberos_app=None):
        super().__init__("multilayer_analyzer")
        self.kerberos = kerberos_app
        self.is_running = False
        
        # Mémoire tampon pour l'analyse temporelle (Couche 3)
        # On garde les 10 dernières frames en niveaux de gris
        self.frame_buffer = deque(maxlen=10)
        
        # Seuils par couche
        self.thresholds = {
            "layer1_brightness_min": 10,
            "layer1_brightness_max": 240,
            "layer2_noise_min": 10,
            "layer2_shadow_threshold": -40,
            "layer3_temporal_variance_max": 5.0  # Si le bruit change trop entre les frames = IA
        }
        
        self.stats = {
            "frames_analyzed": 0,
            "layer1_passed": 0,
            "layer2_passed": 0,
            "layer3_passed": 0,
            "ia_detected": 0
        }
        logger.info("🛡️ MultiLayerAnalyzerGuard initialisé (3 Couches)")

    def _layer1_fast_triage(self, frame: np.ndarray) -> Dict[str, Any]:
        """Couche 1 : Triage rapide (Metadata & Stats de base)"""
        h, w = frame.shape[:2]
        gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
        mean_brightness = np.mean(gray)
        
        details = []
        score = 0.0
        
        # 1. Résolution suspecte (trop parfaite ou bizarre)
        if (h * w) > 4_000_000:  # > 4K
            score += 0.2
            details.append("Résolution 4K+ suspecte")
            
        # 2. Luminosité anormale (IA a parfois du mal avec les extrêmes)
        if mean_brightness < self.thresholds["layer1_brightness_min"] or mean_brightness > self.thresholds["layer1_brightness_max"]:
            score += 0.3
            details.append(f"Luminosité anormale ({mean_brightness:.1f})")
            
        # 3. Ratio d'aspect bizarre
        ratio = h / w
        if ratio > 2.5 or ratio < 0.3:
            score += 0.2
            details.append(f"Ratio d'aspect extrême ({ratio:.2f})")
            
        return {"score": min(1.0, score), "details": details, "passed": score < 0.5}

    def _layer2_spatial_analysis(self, frame: np.ndarray) -> Dict[str, Any]:
        """Couche 2 : Analyse spatiale (Bruit, Ombres, Netteté)"""
        gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
        h, w = gray.shape
        details = []
        score = 0.0
        
        # 1. Bruit de capteur (Noise Floor)
        flat_mask = cv2.inRange(gray, 100, 150)
        if np.sum(flat_mask > 0) > 1000:
            noise_floor = np.std(gray[flat_mask > 0])
        else:
            noise_floor = np.std(gray)
            
        if noise_floor < self.thresholds["layer2_noise_min"]:
            score += 0.5
            details.append(f"Bruit capteur absent (IA) : {noise_floor:.2f}")
            
        # 2. Netteté excessive (Over-sharpness)
        sharpness = cv2.Laplacian(gray, cv2.CV_64F).var()
        if sharpness > 800:
            score += 0.3
            details.append(f"Netteté excessive (IA) : {sharpness:.0f}")
            
        # 3. Ombres flottantes (Simplifié pour la vitesse)
        edges = cv2.Canny(gray, 50, 150)
        contours, _ = cv2.findContours(edges, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
        if contours:
            main_contour = max(contours, key=cv2.contourArea)
            x, y, w_obj, h_obj = cv2.boundingRect(main_contour)
            check_y = min(h, y + h_obj + 10)
            if check_y < h and w_obj > 50:
                avg_obj = np.mean(gray[y:y+h_obj, x:x+w_obj])
                avg_below = np.mean(gray[y+h_obj:check_y, x:x+w_obj])
                if avg_below > avg_obj + self.thresholds["layer2_shadow_threshold"]:
                    score += 0.4
                    details.append("Objet flottant (Ombre manquante)")
                    
        return {"score": min(1.0, score), "details": details, "passed": score < 0.6}

    def _layer3_temporal_analysis(self, frame: np.ndarray) -> Dict[str, Any]:
        """Couche 3 : Analyse temporelle (Cohérence entre les frames)"""
        gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
        details = []
        score = 0.0
        
        # Ajouter la frame au buffer
        self.frame_buffer.append(gray)
        
        # Il faut au moins 3 frames pour faire une analyse temporelle
        if len(self.frame_buffer) < 3:
            return {"score": 0.0, "details": ["Pas assez de frames pour l'analyse temporelle"], "passed": True}
            
        # Calculer la variance du bruit entre les frames récentes
        # Les vraies caméras ont un bruit de capteur STABLE dans le temps
        # Les IA ont un bruit qui "scintille" (change aléatoirement)
        recent_frames = list(self.frame_buffer)[-5:]
        noise_variances = [np.std(f) for f in recent_frames]
        
        # Si la variance du bruit fluctue trop d'une frame à l'autre = IA
        noise_stability = np.std(noise_variances)
        
        if noise_stability > self.thresholds["layer3_temporal_variance_max"]:
            score += 0.7
            details.append(f"Scintillement temporel détecté (Stabilité: {noise_stability:.2f})")
            
        # Détection de "Morphing" (changement brutal de pixels entre frames)
        if len(recent_frames) >= 2:
            diff = cv2.absdiff(recent_frames[-1], recent_frames[-2])
            mean_diff = np.mean(diff)
            # Si trop de pixels changent brutalement sans mouvement de caméra = Artefact IA
            if mean_diff > 15: 
                score += 0.4
                details.append(f"Artefacts de morphing (Diff: {mean_diff:.2f})")
                
        return {"score": min(1.0, score), "details": details, "passed": score < 0.5}

    def analyze_frame(self, frame: np.ndarray, metadata: Dict[str, Any] = None) -> Dict[str, Any]:
        """Pipeline d'analyse multi-couches"""
        if frame is None:
            return {"suspicion_score": 0.0, "details": []}
            
        self.stats["frames_analyzed"] += 1
        final_details = []
        layer_scores = {}
        
        # --- COUCHE 1 : TRIAGE RAPIDE ---
        l1 = self._layer1_fast_triage(frame)
        layer_scores["layer1_triage"] = l1["score"]
        final_details.extend(l1["details"])
        
        if not l1["passed"]:
            self.stats["ia_detected"] += 1
            return {
                "suspicion_score": l1["score"],
                "details": final_details,
                "stopped_at": "Layer 1"
            }
        self.stats["layer1_passed"] += 1
        
        # --- COUCHE 2 : ANALYSE SPATIALE ---
        l2 = self._layer2_spatial_analysis(frame)
        layer_scores["layer2_spatial"] = l2["score"]
        final_details.extend(l2["details"])
        
        if not l2["passed"]:
            self.stats["ia_detected"] += 1
            return {
                "suspicion_score": max(l1["score"], l2["score"]),
                "details": final_details,
                "stopped_at": "Layer 2"
            }
        self.stats["layer2_passed"] += 1
        
        # --- COUCHE 3 : ANALYSE TEMPORELLE ---
        l3 = self._layer3_temporal_analysis(frame)
        layer_scores["layer3_temporal"] = l3["score"]
        final_details.extend(l3["details"])
        
        if not l3["passed"]:
            self.stats["ia_detected"] += 1
            
        self.stats["layer3_passed"] += 1
        
        # Score final combiné (Moyenne pondérée)
        final_score = (l1["score"] * 0.2) + (l2["score"] * 0.4) + (l3["score"] * 0.4)
        
        return {
            "suspicion_score": min(1.0, final_score),
            "details": final_details,
            "layer_scores": layer_scores,
            "stopped_at": "Completed"
        }

    def start(self):
        self.is_running = True
        logger.info("️ MultiLayerAnalyzerGuard démarré")
        
    def stop(self):
        self.is_running = False
        self.frame_buffer.clear()
        logger.info("🛡️ MultiLayerAnalyzerGuard arrêté")
        
    def get_stats(self) -> Dict[str, Any]:
        return self.stats.copy()

# Fonctions globales pour le GuardManager
_guard_instance = None

def start_guard(kerberos_app=None):
    global _guard_instance
    _guard_instance = MultiLayerAnalyzerGuard(kerberos_app)
    return _guard_instance

def stop_guard():
    global _guard_instance
    if _guard_instance:
        _guard_instance.stop()

def get_stats():
    global _guard_instance
    return _guard_instance.get_stats() if _guard_instance else {}