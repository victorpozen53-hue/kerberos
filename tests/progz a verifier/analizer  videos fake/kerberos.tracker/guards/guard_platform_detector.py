#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""🌐 GUARD PLATFORM DETECTOR — FIX INCOHÉRENCE"""
import logging
from typing import Dict, Any
from guards.guard_interface import GuardInterface
logger = logging.getLogger(__name__)

PLATFORM_PATTERNS = {
    "tiktok": ["tiktok.com", "tiktokcdn.com"],
    "youtube": ["youtube.com", "youtu.be"],
    "instagram": ["instagram.com", "instagr.am"],
    "twitter": ["twitter.com", "x.com", "twimg.com"],
}
PLATFORM_CONFIG = {
    "tiktok": {"name": "TikTok", "threshold_adjustment": -10, "ai_filters_common": True},
    "youtube": {"name": "YouTube", "threshold_adjustment": 0, "ai_filters_common": False},
    "instagram": {"name": "Instagram", "threshold_adjustment": -5, "ai_filters_common": True},
    "twitter": {"name": "Twitter", "threshold_adjustment": 5, "ai_filters_common": False},
    "unknown": {"name": "Unknown", "threshold_adjustment": 0, "ai_filters_common": False}
}

class PlatformDetectorGuard(GuardInterface):
    def __init__(self, kerberos_app=None):
        super().__init__("platform_detector")
        self.kerberos, self.is_running, self.current_platform = kerberos_app, False, "unknown"
        self.stats = {"urls_analyzed": 0, "platforms_detected": {}}
        logger.info("🌐 PlatformDetectorGuard initialisé")

    def detect_platform(self, url: str) -> str:
        self.stats["urls_analyzed"] += 1
        url_lower = url.lower() if url else ""
        for platform, patterns in PLATFORM_PATTERNS.items():
            if any(p in url_lower for p in patterns):
                self.current_platform = platform
                self.stats["platforms_detected"][platform] = self.stats["platforms_detected"].get(platform, 0) + 1
                logger.info(f" Plateforme détectée: {platform.upper()}")
                return platform
        # ✅ FIX: Réinitialiser à "unknown"
        self.current_platform = "unknown"
        return "unknown"

    def get_platform_config(self) -> Dict[str, Any]:
        return PLATFORM_CONFIG.get(self.current_platform, PLATFORM_CONFIG["unknown"])

    def adjust_threshold_for_platform(self, base_threshold: int) -> int:
        adj = self.get_platform_config().get("threshold_adjustment", 0)
        return max(30, min(95, base_threshold + adj))

    def start(self): self.is_running = True
    def stop(self): self.is_running = False
    def get_stats(self) -> Dict[str, Any]: return {**self.stats, "current_platform": self.current_platform}

_guard_instance = None
def start_guard(kerberos_app=None):
    global _guard_instance; _guard_instance = PlatformDetectorGuard(kerberos_app); return _guard_instance
def stop_guard():
    global _guard_instance
    if _guard_instance: _guard_instance.stop()
def get_stats():
    global _guard_instance; return _guard_instance.get_stats() if _guard_instance else {}