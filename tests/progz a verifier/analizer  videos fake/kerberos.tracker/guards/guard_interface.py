#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Interface standard pour tous les guards"""
from abc import ABC, abstractmethod
from typing import Dict, Any
import logging
logger = logging.getLogger(__name__)

class GuardInterface(ABC):
    def __init__(self, name: str) -> None:
        if not name: raise ValueError(f"Nom invalide: {name}")
        self.name: str = name
        self.is_running: bool = False
        self.stats: Dict[str, Any] = {}
        logger.info(f"Guard '{name}' initialisé")
    
    @abstractmethod
    def start(self) -> None: pass
    
    @abstractmethod
    def stop(self) -> None: pass
    
    @abstractmethod
    def get_stats(self) -> Dict[str, Any]: return self.stats
    
    def get_status(self) -> Dict[str, Any]:
        return {"name": self.name, "running": self.is_running, "stats": self.get_stats()}
    
    def __repr__(self) -> str:
        return f"<Guard '{self.name}' running={self.is_running}>"