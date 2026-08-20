#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Gestionnaire centralisé des guards"""
from typing import Dict, Any, Optional
import logging
logger = logging.getLogger(__name__)

class GuardManager:
    def __init__(self) -> None:
        self._guards: Dict[str, Any] = {}
        logger.info("GuardManager initialisé")
    
    def register_guard(self, name: str, guard_instance: Any) -> bool:
        if not name or not guard_instance: return False
        self._guards[name] = guard_instance
        return True
    
    def start_guard(self, name: str) -> bool:
        guard = self._guards.get(name)
        if not guard: return False
        try:
            if hasattr(guard, 'start'): guard.start()
            elif hasattr(guard, 'start_analysis'): guard.start_analysis()
            return True
        except Exception as e:
            logger.error(f"Erreur démarrage {name}: {e}")
            return False
    
    def stop_guard(self, name: str) -> bool:
        guard = self._guards.get(name)
        if not guard: return False
        try:
            if hasattr(guard, 'stop'): guard.stop()
            elif hasattr(guard, 'stop_analysis'): guard.stop_analysis()
            return True
        except Exception as e:
            logger.error(f"Erreur arrêt {name}: {e}")
            return False
    
    def pause_guard(self, name: str) -> bool:
        guard = self._guards.get(name)
        if guard and hasattr(guard, 'pause'):
            guard.pause()
            return True
        return False
    
    def resume_guard(self, name: str) -> bool:
        guard = self._guards.get(name)
        if guard and hasattr(guard, 'resume'):
            guard.resume()
            return True
        return False
    
    def get_guard(self, name: str) -> Optional[Any]:
        return self._guards.get(name)
    
    def get_all_stats(self) -> Dict[str, Any]:
        stats = {}
        for name, guard in self._guards.items():
            try:
                if hasattr(guard, 'get_stats'): stats[name] = guard.get_stats()
            except: pass
        return stats
    
    def list_guards(self) -> list:
        return list(self._guards.keys())
    
    def stop_all_guards(self) -> None:
        for name, guard in list(self._guards.items()):
            try:
                if hasattr(guard, 'stop'): guard.stop()
                elif hasattr(guard, 'stop_analysis'): guard.stop_analysis()
            except: pass