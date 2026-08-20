#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Guard Frame Analyzer — Analyse forensique frames"""
import cv2, numpy as np, logging
from pathlib import Path
from guards.guard_interface import GuardInterface
logger = logging.getLogger(__name__)

class FrameAnalyzerGuard(GuardInterface):
    def __init__(self, kerberos_app=None):
        super().__init__("frame_analyzer")
        self.kerberos = kerberos_app; self.is_running = False
        self.frames_dir = Path("reports/frames"); self.analysis_dir = Path("reports/frame_analysis"); self.analysis_dir.mkdir(parents=True, exist_ok=True)
        self.stats = {"frames_scanned": 0, "frames_analyzed": 0, "deepfake_detected": 0, "real_detected": 0, "suspicious": 0}
    
    def scan_and_analyze(self):
        if not self.frames_dir.exists(): return {"error": "Dossier introuvable"}
        image_files = list(self.frames_dir.glob("*.png"))
        if not image_files: return {"message": "Aucune frame trouvée"}
        results = {"timestamp": __import__('datetime').datetime.now().isoformat(), "total_frames": len(image_files), "deepfakes": [], "real": [], "suspicious": []}
        for img_path in image_files:
            try:
                analysis = self.analyze_frame_forensics(img_path); results["deepfakes" if analysis["ai_probability"] > 0.7 else "suspicious" if analysis["ai_probability"] > 0.4 else "real"].append(analysis)
                self.stats["frames_analyzed"] += 1
            except Exception as e: logger.error(f"Erreur analyse {img_path}: {e}")
        self.stats["frames_scanned"] = len(image_files)
        return results
    
    def analyze_frame_forensics(self, img_path: Path):
        result = {"file": str(img_path.name), "ai_probability": 0.0, "scores": {}, "details": []}
        try:
            img_np = np.array(__import__('PIL.Image').Image.open(img_path))
            gray = cv2.cvtColor(img_np, cv2.COLOR_RGB2GRAY) if len(img_np.shape) == 3 else img_np
            noise_variance = cv2.Laplacian(gray, cv2.CV_64F).var()
            result["scores"]["noise_level"] = noise_variance
            if noise_variance < 15.0: result["ai_probability"] += 0.3; result["details"].append("Bruit insuffisant (IA)")
            result["ai_probability"] = min(1.0, result["ai_probability"])
            result["classification"] = "🤖 DEEPFAKE" if result["ai_probability"] > 0.7 else "⚠️ SUSPICIEUX" if result["ai_probability"] > 0.4 else "✅ RÉEL"
        except Exception as e: result["error"] = str(e)
        return result
    
    def start(self): self.is_running = True
    def stop(self): self.is_running = False
    def get_stats(self): return self.stats.copy()

_guard_instance = None
def start_guard(kerberos_app=None):
    global _guard_instance; _guard_instance = FrameAnalyzerGuard(kerberos_app); return _guard_instance
def stop_guard():
    global _guard_instance
    if _guard_instance: _guard_instance.stop()