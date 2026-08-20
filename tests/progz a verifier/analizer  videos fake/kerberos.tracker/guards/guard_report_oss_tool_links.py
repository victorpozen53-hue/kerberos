#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Guard Report OSS Tool Links — Liens OSINT"""
import logging
from typing import Dict, Any
from guards.guard_interface import GuardInterface
logger = logging.getLogger(__name__)

class OSSToolLinksReportGuard(GuardInterface):
    def __init__(self, kerberos_app=None):
        super().__init__("report_oss_tool_links")
        self.kerberos = kerberos_app; self.is_running = False
        self.stats = {"sections_generated": 0}
    
    def generate_section(self, stats: Dict[str, Any]) -> str:
        self.stats["sections_generated"] += 1
        return """<div class="section"><h2>🔗 Outils OSINT Recommandés</h2><div class="grid"><div class="card"><h3>Yandex Images</h3><div class="val"><a href="https://yandex.com/images/" target="_blank">Recherche inversée</a></div></div><div class="card"><h3>TinEye</h3><div class="val"><a href="https://tineye.com/" target="_blank">Reverse Image Search</a></div></div><div class="card"><h3>InVID Verification</h3><div class="val"><a href="https://www.invid-project.eu/" target="_blank">Plugin fact-checking</a></div></div><div class="card"><h3>Whois.com</h3><div class="val"><a href="https://www.whois.com/" target="_blank">Informations domaine</a></div></div></div></div>"""
    
    def start(self): self.is_running = True
    def stop(self): self.is_running = False
    def get_stats(self): return self.stats.copy()

_guard_instance = None
def start_guard(kerberos_app=None):
    global _guard_instance; _guard_instance = OSSToolLinksReportGuard(kerberos_app); return _guard_instance
def stop_guard():
    global _guard_instance
    if _guard_instance: _guard_instance.stop()