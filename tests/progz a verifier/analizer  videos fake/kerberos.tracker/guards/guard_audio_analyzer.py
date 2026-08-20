#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Guard Audio Analyzer — Détection voix synthétique"""
import numpy as np, logging
from pathlib import Path
from guards.guard_interface import GuardInterface
logger = logging.getLogger(__name__)
try:
    import librosa; HAS_LIBROSA = True
except: HAS_LIBROSA = False

class AudioAnalyzerGuard(GuardInterface):
    def __init__(self, kerberos_app=None):
        super().__init__("audio_analyzer")
        self.kerberos = kerberos_app; self.is_running = False
        self.stats = {"samples_analyzed": 0, "synthetic_voice_detected": 0, "real_voice_detected": 0}
    
    def analyze_audio_file(self, audio_path: str):
        if not Path(audio_path).exists(): return {"synthetic": False, "confidence": 0.0, "error": "Fichier introuvable"}
        self.stats["samples_analyzed"] += 1
        if HAS_LIBROSA:
            try:
                audio_data, sample_rate = librosa.load(audio_path, sr=16000)
                spectral_flatness = librosa.feature.spectral_flatness(y=audio_data)
                avg_flatness = np.mean(spectral_flatness)
                synthetic = avg_flatness > 0.3
                if synthetic: self.stats["synthetic_voice_detected"] += 1
                else: self.stats["real_voice_detected"] += 1
                return {"synthetic": synthetic, "confidence": float(avg_flatness)}
            except Exception as e: return {"synthetic": False, "confidence": 0.0, "error": str(e)}
        return {"synthetic": False, "confidence": 0.0, "error": "librosa non installé"}
    
    def start(self): self.is_running = True
    def stop(self): self.is_running = False
    def get_stats(self): return self.stats.copy()

_guard_instance = None
def start_guard(kerberos_app=None):
    global _guard_instance; _guard_instance = AudioAnalyzerGuard(kerberos_app); return _guard_instance
def stop_guard():
    global _guard_instance
    if _guard_instance: _guard_instance.stop()