#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Guard Image Forensics — Analyse forensique images"""
import cv2, numpy as np, logging, base64, io
from guards.guard_interface import GuardInterface
logger = logging.getLogger(__name__)
try:
    from PIL import Image; HAS_PIL = True
except: HAS_PIL = False

class ImageForensicsGuard(GuardInterface):
    def __init__(self, kerberos_app=None):
        super().__init__("image_forensics")
        self.kerberos = kerberos_app; self.is_running = False
        self.ai_exif_signatures = ["midjourney", "dall-e", "stable diffusion", "leonardo.ai", "firefly"]
        self.stats = {"images_analyzed": 0, "ai_generated_detected": 0, "clean_images": 0}
    
    def analyze_image_from_base64(self, b64_data: str):
        if not HAS_PIL: return {"error": "PIL non disponible", "ai_probability": 0}
        self.stats["images_analyzed"] += 1
        try:
            if ',' in b64_data: b64_data = b64_data.split(',')[1]
            img_bytes = base64.b64decode(b64_data); img = Image.open(io.BytesIO(img_bytes))
            results = {"ai_probability": 0.0, "details": [], "exif_data": {}, "noise_level": 0.0}
            exif_analysis = self._check_exif_ai(img)
            results["exif_data"] = exif_analysis["data"]
            if exif_analysis["is_ai"]: results["ai_probability"] += 0.6; results["details"].append(f"Signature IA EXIF: {exif_analysis['software']}"); self.stats["ai_generated_detected"] += 1
            noise_score = self._analyze_noise(img); results["noise_level"] = noise_score
            if noise_score < 15.0: results["ai_probability"] += 0.3; results["details"].append("Bruit de capteur inexistant (IA)")
            if results["ai_probability"] == 0.0: self.stats["clean_images"] += 1
            return results
        except Exception as e: return {"error": str(e), "ai_probability": 0}
    
    def _check_exif_ai(self, img: Image.Image):
        result = {"is_ai": False, "software": "Unknown", "data": {}}
        try:
            exif_data = img._getexif()
            if exif_data:
                from PIL.ExifTags import TAGS
                for tag_id, value in exif_data.items():
                    tag = TAGS.get(tag_id, tag_id); result["data"][tag] = str(value)
                    if tag == "Software" and isinstance(value, str):
                        for signature in self.ai_exif_signatures:
                            if signature.lower() in value.lower(): result["is_ai"] = True; result["software"] = value; return result
        except: pass
        return result
    
    def _analyze_noise(self, img: Image.Image):
        try:
            gray = np.array(img.convert('L')); laplacian = cv2.Laplacian(gray, cv2.CV_64F); return float(laplacian.var())
        except: return 0.0
    
    def start(self): self.is_running = True
    def stop(self): self.is_running = False
    def get_stats(self): return self.stats.copy()

_guard_instance = None
def start_guard(kerberos_app=None):
    global _guard_instance; _guard_instance = ImageForensicsGuard(kerberos_app); return _guard_instance
def stop_guard():
    global _guard_instance
    if _guard_instance: _guard_instance.stop()