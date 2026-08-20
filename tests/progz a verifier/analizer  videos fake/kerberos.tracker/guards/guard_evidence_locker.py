#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""🔒 GUARD EVIDENCE LOCKER v1.1 — SÉCURISÉ (Anti-Path Traversal)"""
import hashlib, json, logging, base64, io, re
from datetime import datetime
from pathlib import Path
from typing import Dict, Any, Optional
from guards.guard_interface import GuardInterface
try:
    from PIL import Image; HAS_PIL = True
except ImportError: HAS_PIL = False
logger = logging.getLogger(__name__)

def sanitize_filename(name: str) -> str:
    return re.sub(r'[^a-zA-Z0-9_-]', '', name)[:100] or "unknown"

class EvidenceLockerGuard(GuardInterface):
    def __init__(self, kerberos_app=None):
        super().__init__("evidence_locker")
        self.kerberos = kerberos_app
        self.is_running = False
        self.evidence_dir = (Path(__file__).parent.parent / "evidence" / "deepfakes").resolve()
        self.evidence_dir.mkdir(parents=True, exist_ok=True)
        self.stats = {"evidence_saved": 0, "total_size_mb": 0.0, "path_traversal_blocked": 0}

    def _validate_path(self, path: Path) -> bool:
        try: return str(path.resolve()).startswith(str(self.evidence_dir))
        except: return False

    def save_evidence(self, video_info: Dict[str, Any], frame_data: str = None) -> Optional[Path]:
        if not HAS_PIL: return None
        try:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            safe_hash = hashlib.sha256(str(video_info).encode()).hexdigest()[:16]
            evidence_id = sanitize_filename(f"evidence_{timestamp}_{safe_hash}")
            evidence_path = self.evidence_dir / evidence_id
            
            # ✅ VALIDATION ANTI-PATH TRAVERSAL
            if not self._validate_path(evidence_path):
                self.stats["path_traversal_blocked"] += 1
                logger.error(f"🚫 Path traversal bloqué: {evidence_path}")
                return None
            
            evidence_path.mkdir(parents=True, exist_ok=True)
            img_path = None
            if frame_data and frame_data != "TAINTED":
                img_path = evidence_path / "frame.png"
                if ',' in frame_data: frame_data = frame_data.split(',')[1]
                img_bytes = base64.b64decode(frame_data)
                img = Image.open(io.BytesIO(img_bytes))
                img.save(img_path, "PNG")
                self.stats["total_size_mb"] += img_path.stat().st_size / (1024**2)
            
            metadata = {
                "evidence_id": evidence_id, "timestamp_captured": datetime.now().isoformat(),
                "video_info": {k: str(v)[:500] for k, v in video_info.items() if isinstance(v, str)},
                "classification": sanitize_filename(str(video_info.get("classification", "UNKNOWN"))),
                "score": int(video_info.get("score", 0)), "page_url": str(video_info.get("page_url", ""))[:1000], "hash_sha256": None
            }
            if img_path and img_path.exists():
                with open(img_path, "rb") as f: metadata["hash_sha256"] = hashlib.sha256(f.read()).hexdigest()
            
            with open(evidence_path / "metadata.json", "w", encoding="utf-8") as f:
                json.dump(metadata, f, indent=2, ensure_ascii=False)
            
            self.stats["evidence_saved"] += 1
            logger.info(f"🔒 Preuve sauvegardée: {evidence_id}")
            return evidence_path
        except Exception as e:
            logger.error(f"❌ Erreur sauvegarde preuve: {e}")
            return None

    def start(self): self.is_running = True
    def stop(self): self.is_running = False
    def get_stats(self) -> Dict[str, Any]: return self.stats.copy()

_guard_instance = None
def start_guard(kerberos_app=None):
    global _guard_instance; _guard_instance = EvidenceLockerGuard(kerberos_app); return _guard_instance
def stop_guard():
    global _guard_instance
    if _guard_instance: _guard_instance.stop()
def get_stats():
    global _guard_instance; return _guard_instance.get_stats() if _guard_instance else {}