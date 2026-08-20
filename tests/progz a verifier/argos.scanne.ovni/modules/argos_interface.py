#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""👁️ OrganeInterface — contrat standard des organes ARGOS (adapté de guard_interface.py)"""
from abc import ABC, abstractmethod


class OrganeInterface(ABC):
    def __init__(self, name):
        if not name:
            raise ValueError(f"Nom invalide: {name}")
        self.name = name
        self.is_running = False
        self.stats = {}

    @abstractmethod
    def start(self): pass

    @abstractmethod
    def stop(self): pass

    @abstractmethod
    def get_stats(self): return self.stats

    def get_status(self):
        return {"name": self.name, "running": self.is_running, "stats": self.get_stats()}

    def __repr__(self):
        return f"<Organe '{self.name}' running={self.is_running}>"