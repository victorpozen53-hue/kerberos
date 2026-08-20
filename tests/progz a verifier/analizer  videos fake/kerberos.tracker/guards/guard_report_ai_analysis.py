#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Guard Report AI Analysis — Détails IA"""
import logging
from typing import Dict, Any
from guards.guard_interface import GuardInterface
logger = logging.getLogger(__name__)

class AIAnalysisReportGuard(GuardInterface):
    def __init__(self, kerberos_app=None):
        super().__init__("report_ai_analysis")
        self.kerberos = kerberos_app; self.is_running = False
        self.stats = {"sections_generated": 0}
    
    def generate_section(self, stats: Dict[str, Any]) -> str:
        ai_types = stats.get("detailed_stats", {}).get("ai_types", {})
        self.stats["sections_generated"] += 1
        total_ai = sum(ai_types.values()) if ai_types else 0
        section = '<div class="section"><h2>🤖 Analyse Détaillée de l\'IA</h2><div class="grid">'
        if ai_types and total_ai > 0:
            for ai_type, count in ai_types.items():
                if count > 0: percentage = (count / total_ai) * 100; section += f'<div class="card"><h3>{ai_type}</h3><div class="val" style="color:#ff5252;">{count} détections ({percentage:.1f}%)</div></div>'
        else: section += '<div class="card"><h3>Aucune IA détectée</h3><div class="val">0</div></div>'
        section += "</div></div>"; return section
    
    def start(self): self.is_running = True
    def stop(self): self.is_running = False
    def get_stats(self): return self.stats.copy()

_guard_instance = None
def start_guard(kerberos_app=None):
    global _guard_instance; _guard_instance = AIAnalysisReportGuard(kerberos_app); return _guard_instance
def stop_guard():
    global _guard_instance
    if _guard_instance: _guard_instance.stop()