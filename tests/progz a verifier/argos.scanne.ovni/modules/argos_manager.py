#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
🧩 argos_manager.py — registre central + stats par la lymphe
(adapté de guard_manager.py)
- OrganeManager : register/start/stop/get_all_stats/stop_all
- publish_stats() : un organe publie ses compteurs dans lymph_argos/stats/
- read_all_stats() : le dashboard lit tout, sans imports fragiles
"""
import json
import time
from pathlib import Path

_p = Path(__file__).resolve().parent
ARGOS_ROOT = _p.parent if (_p.parent / "lymph_argos").exists() or _p.name == "modules" else _p
STATS_DIR = ARGOS_ROOT / "lymph_argos" / "stats"
STATS_DIR.mkdir(parents=True, exist_ok=True)


class OrganeManager:
    def __init__(self):
        self._o = {}

    def register(self, name, organe):
        if not name or not organe:
            return False
        self._o[name] = organe
        return True

    def start(self, name):
        o = self._o.get(name)
        if not o:
            return False
        try:
            if hasattr(o, "start"):
                o.start()
            return True
        except Exception:
            return False

    def stop(self, name):
        o = self._o.get(name)
        if not o:
            return False
        try:
            if hasattr(o, "stop"):
                o.stop()
            return True
        except Exception:
            return False

    def get(self, name):
        return self._o.get(name)

    def list(self):
        return list(self._o.keys())

    def get_all_stats(self):
        out = {}
        for n, o in self._o.items():
            try:
                if hasattr(o, "get_stats"):
                    out[n] = o.get_stats()
            except Exception:
                pass
        return out

    def stop_all(self):
        for n, o in list(self._o.items()):
            try:
                if hasattr(o, "stop"):
                    o.stop()
            except Exception:
                pass


def publish_stats(name, stats, running=False):
    try:
        (STATS_DIR / f"{name}.json").write_text(json.dumps(
            {"name": name, "running": running, "updated": time.time(), "stats": stats},
            indent=2, ensure_ascii=False), encoding="utf-8")
    except Exception:
        pass


def read_all_stats():
    out = {}
    for f in sorted(STATS_DIR.glob("*.json")):
        try:
            d = json.loads(f.read_text(encoding="utf-8"))
            out[d.get("name", f.stem)] = d
        except Exception:
            pass
    return out


def reset_stats():
    for f in STATS_DIR.glob("*.json"):
        try:
            f.unlink()
        except Exception:
            pass