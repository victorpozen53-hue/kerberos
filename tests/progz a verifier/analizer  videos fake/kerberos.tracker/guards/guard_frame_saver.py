#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Guard Frame Saver — Sauvegarde frames"""
import base64, logging, threading
from datetime import datetime
from pathlib import Path
from typing import Dict, Any, Optional
from guards.guard_interface import GuardInterface
logger = logging.getLogger(__name__)

class FrameSaverGuard(GuardInterface):
    def __init__(self, kerberos_app=None):
        super().__init__("frame_saver")
        self.kerberos = kerberos_app; self.is_running = False; self._lock = threading.Lock()
        self.frames_dir = Path("reports/frames"); self.frames_dir.mkdir(parents=True, exist_ok=True)
        self.stats = {"frames_saved": 0, "suspicious_saved": 0, "real_saved": 0}
    
    def save_frame(self, frame_data: str, video_info: Dict[str, Any]) -> Optional[str]:
        if not frame_data or frame_data == "TAINTED": return None
        try:
            if ',' in frame_data: frame_data = frame_data.split(',')[1]
            img_bytes = base64.b64decode(frame_data)
            timestamp = datetime.now().strftime('%Y%m%d_%H%M%S_%f')
            classification = video_info.get('classification', 'UNKNOWN'); score = video_info.get('score', 0)
            filename = f"frame_{timestamp}_{classification}_{score}.png"
            filepath = self.frames_dir / filename
            with open(filepath, 'wb') as f: f.write(img_bytes)
            with self._lock:
                self.stats["frames_saved"] += 1
                if classification == "SUSPICIOUS": self.stats["suspicious_saved"] += 1
                else: self.stats["real_saved"] += 1
            return f"frames/{filename}"
        except Exception as e: logger.error(f"Erreur sauvegarde: {e}"); return None
    
    def start(self): self.is_running = True
    def stop(self): self.is_running = False
    def get_stats(self) -> Dict[str, Any]:
        with self._lock: return self.stats.copy()

_guard_instance = None
def start_guard(kerberos_app=None):
    global _guard_instance; _guard_instance = FrameSaverGuard(kerberos_app); return _guard_instance
def stop_guard():
    global _guard_instance
    if _guard_instance: _guard_instance.stop()
def get_stats():
    global _guard_instance; return _guard_instance.get_stats() if _guard_instance else {}