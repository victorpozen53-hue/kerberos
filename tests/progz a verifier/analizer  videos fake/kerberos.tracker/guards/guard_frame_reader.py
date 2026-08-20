#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""📂 GUARD FRAME READER v1.0.1 — FIX IMPORT NUMPY"""
import os, cv2, numpy as np, base64, logging, threading
from pathlib import Path
from datetime import datetime
from typing import Dict, Any, List, Optional
from guards.guard_interface import GuardInterface
logger = logging.getLogger(__name__)

class FrameReaderGuard(GuardInterface):
    def __init__(self, kerberos_app=None):
        super().__init__("frame_reader")
        self.kerberos, self.is_running = kerberos_app, False
        self._lock = threading.Lock()
        self.frames_dir = Path(__file__).parent.parent / "reports" / "frames"
        self.stats = {"total_frames_found": 0, "frames_analyzed": 0, "suspicious_frames": 0, "real_frames": 0, "uncertain_frames": 0, "errors": 0}
        self.analysis_results: List[Dict[str, Any]] = []
        logger.info(f"📂 FrameReaderGuard initialisé")
        if self.frames_dir.exists():
            frame_count = len(list(self.frames_dir.glob("*.png")) + list(self.frames_dir.glob("*.jpg")))
            logger.info(f"✅ {frame_count} frame(s) trouvée(s)")

    def list_frames(self) -> List[Path]:
        if not self.frames_dir.exists(): return []
        frames = []
        for pattern in ["*.png", "*.jpg", "*.jpeg"]: frames.extend(self.frames_dir.glob(pattern))
        frames.sort(key=lambda x: x.stat().st_mtime, reverse=True)
        return frames

    def load_frame(self, frame_path: Path) -> Optional[np.ndarray]:
        try: return cv2.imread(str(frame_path))
        except Exception as e: logger.error(f"❌ Erreur chargement {frame_path}: {e}"); return None

    def frame_to_base64(self, frame: np.ndarray) -> str:
        try:
            _, buffer = cv2.imencode('.jpg', frame)
            return "data:image/jpeg;base64," + base64.b64encode(buffer).decode('utf-8')
        except: return ""

    def analyze_single_frame(self, frame_path: Path) -> Optional[Dict[str, Any]]:
        try:
            frame = self.load_frame(frame_path)
            if frame is None: return None
            frame_b64 = self.frame_to_base64(frame)
            video_info = {"frame": frame_b64, "pageUrl": f"file://{frame_path}", "videoSrc": str(frame_path)}
            video_analyzer = self.kerberos.guard_manager.get_guard("video_analyzer") if self.kerberos and hasattr(self.kerberos, 'guard_manager') else None
            if video_analyzer and hasattr(video_analyzer, 'analyze_frame'):
                score, classification = video_analyzer.analyze_frame(video_info)
            else: score, classification = 50, "UNCERTAIN"
            return {"frame_path": str(frame_path), "frame_name": frame_path.name, "score": score, "classification": classification}
        except Exception as e: logger.error(f"❌ Erreur analyse {frame_path}: {e}"); return None

    def analyze_batch(self, max_frames: Optional[int] = None) -> Dict[str, Any]:
        self.is_running = True
        frames = self.list_frames()
        if not frames: return {"error": "Aucune frame"}
        if max_frames: frames = frames[:max_frames]
        results, stats = [], {"total": len(frames), "suspicious": 0, "real": 0, "uncertain": 0, "errors": 0}
        for idx, frame_path in enumerate(frames, 1):
            if not self.is_running: break
            result = self.analyze_single_frame(frame_path)
            if result:
                results.append(result)
                stats[result["classification"].lower()] += 1
            else: stats["errors"] += 1
            threading.Event().wait(0.1)
        self.analysis_results = results
        with self._lock:
            self.stats.update({"total_frames_found": len(self.list_frames()), "frames_analyzed": len(results), "suspicious_frames": stats["suspicious"], "real_frames": stats["real"], "uncertain_frames": stats["uncertain"], "errors": stats["errors"]})
        return {"results": results, "stats": stats}

    def start(self): self.is_running = True
    def stop(self): self.is_running = False
    def get_stats(self) -> Dict[str, Any]:
        with self._lock: return self.stats.copy()

_guard_instance: Optional[FrameReaderGuard] = None
def start_guard(kerberos_app=None) -> Optional[FrameReaderGuard]:
    global _guard_instance; _guard_instance = FrameReaderGuard(kerberos_app); return _guard_instance
def stop_guard() -> None:
    global _guard_instance
    if _guard_instance: _guard_instance.stop(); _guard_instance = None
def get_stats() -> Dict[str, Any]:
    global _guard_instance; return _guard_instance.get_stats() if _guard_instance else {}