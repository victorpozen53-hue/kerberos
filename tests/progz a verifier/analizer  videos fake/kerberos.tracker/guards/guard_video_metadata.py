#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Guard Video Metadata — Extracteur métadonnées"""
import os, json, logging
from pathlib import Path
from datetime import datetime
from guards.guard_interface import GuardInterface
logger = logging.getLogger(__name__)

class VideoMetadataGuard(GuardInterface):
    def __init__(self, kerberos_app=None):
        super().__init__("video_metadata")
        self.kerberos = kerberos_app; self.is_running = False
        self.stats = {"videos_analyzed": 0, "metadata_extracted": 0}
        self.metadata_cache = {}
    
    def extract_metadata(self, video_path: str):
        if not Path(video_path).exists(): return {"error": "Fichier introuvable"}
        self.stats["videos_analyzed"] += 1
        metadata = {"file": {}, "technical": {}, "encoding": {}}
        try:
            stat = os.stat(video_path)
            metadata["file"] = {"path": video_path, "size_bytes": stat.st_size, "size_mb": round(stat.st_size / (1024**2), 2), "created": datetime.fromtimestamp(stat.st_ctime).isoformat(), "modified": datetime.fromtimestamp(stat.st_mtime).isoformat()}
            self.stats["metadata_extracted"] += 1; self.metadata_cache[video_path] = metadata
            return metadata
        except Exception as e: return {"error": str(e)}
    
    def start(self): self.is_running = True
    def stop(self): self.is_running = False
    def get_stats(self): return self.stats.copy()

_guard_instance = None
def start_guard(kerberos_app=None):
    global _guard_instance; _guard_instance = VideoMetadataGuard(kerberos_app); return _guard_instance
def stop_guard():
    global _guard_instance
    if _guard_instance: _guard_instance.stop()