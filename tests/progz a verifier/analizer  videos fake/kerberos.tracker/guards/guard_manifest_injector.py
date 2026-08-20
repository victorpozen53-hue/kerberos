#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""📋 GUARD MANIFEST INJECTOR v2.0 — Auto-Nettoyage"""
import json, shutil, logging, threading
from datetime import datetime
from pathlib import Path
from typing import Dict, Any, List, Optional
from guards.guard_interface import GuardInterface
logger = logging.getLogger(__name__)

CATEGORY_PATTERNS = {
    "systeme": ["cortex", "thymus", "ui_manager", "interface", "injector", "buttons"],
    "plateformes": ["platform", "tiktok", "youtube", "instagram"],
    "orchestration": ["orchestrator", "sonde"],
    "analyse_cv": ["inspector", "device_detector"],
    "filtrage": ["filter", "artistic"],
    "detection_specialisee": ["detector", "analyzer", "face", "object", "human", "animal", "vehicle", "game", "overlay", "ai", "watermark"],
    "preuve_et_rapport": ["report", "saver", "locker", "evidence", "splitter"],
}
PROTECTED = ["guard_interface.py", "guard_manager.py", "__init__.py", "guard_manifest_injector.py"]

class ManifestInjectorGuard(GuardInterface):
    def __init__(self, kerberos_app=None):
        super().__init__("manifest_injector")
        self.kerberos, self.is_running, self._lock = kerberos_app, False, threading.Lock()
        self.guards_dir = Path(__file__).parent
        self.manifest_path = self.guards_dir / "guards_manifest.json"
        self.backup_dir = self.guards_dir / ".manifest_backups"
        self.backup_dir.mkdir(exist_ok=True)
        self.stats = {"scans": 0, "injected": 0, "cleaned": 0}
        logger.info("📋 ManifestInjectorGuard v2.0 initialisé")
        self._do_inject()

    def _clean_manifest(self, manifest: Dict[str, Any]) -> Dict[str, Any]:
        cleaned = {}
        for key, value in manifest.items():
            clean_key = key.strip()
            if isinstance(value, str): cleaned[clean_key] = value.strip()
            elif isinstance(value, list): cleaned[clean_key] = [item.strip() if isinstance(item, str) else item for item in value]
            elif isinstance(value, dict): cleaned[clean_key] = self._clean_manifest(value)
            else: cleaned[clean_key] = value
        return cleaned

    def _do_inject(self):
        try:
            result = self.inject_new_guards()
            if result.get("injected"): logger.info(f"🎉 {len(result['injected'])} guard(s) injecté(s)")
            else: logger.info("✅ Manifest à jour")
        except Exception as e: logger.error(f"❌ Erreur injection: {e}")

    def scan_guards_folder(self) -> List[str]:
        if not self.guards_dir.exists(): return []
        guards = []
        for f in sorted(self.guards_dir.glob("guard_*.py")):
            if f.name in PROTECTED or f.name.endswith(("_filtered.py", "_test.py")): continue
            try:
                if "def start_guard" in f.read_text(encoding='utf-8', errors='ignore'): guards.append(f.name)
            except: pass
        return guards

    def load_manifest(self) -> Optional[Dict[str, Any]]:
        if not self.manifest_path.exists():
            return {"version": "7.4", "auteur": "Victor Pozen", "licence": "GPLv3", "active_guards": [], "categories": {cat: [] for cat in CATEGORY_PATTERNS.keys()}}
        try:
            with open(self.manifest_path, 'r', encoding='utf-8') as f: raw_manifest = json.load(f)
            cleaned_manifest = self._clean_manifest(raw_manifest)
            if cleaned_manifest != raw_manifest:
                logger.info(" Manifest corrompu détecté — Nettoyage automatique...")
                self.stats["cleaned"] += 1
                self._save_manifest(cleaned_manifest)
            return cleaned_manifest
        except Exception as e: logger.error(f"❌ Erreur chargement manifest: {e}"); return None

    def _save_manifest(self, manifest: Dict[str, Any]) -> None:
        if self.manifest_path.exists(): shutil.copy2(self.manifest_path, self.backup_dir / f"manifest_backup_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json")
        manifest["derniere_mise_a_jour"] = datetime.now().strftime("%d/%m/%Y %H:%M")
        with open(self.manifest_path, 'w', encoding='utf-8') as f: json.dump(manifest, f, indent=2, ensure_ascii=False)

    def categorize_guard(self, guard_file: str) -> str:
        name = guard_file.lower().replace("guard_", "").replace(".py", "")
        scores = {cat: sum(1 for p in patterns if p in name) for cat, patterns in CATEGORY_PATTERNS.items()}
        best = max(scores, key=scores.get)
        return best if scores[best] > 0 else "detection_specialisee"

    def inject_new_guards(self) -> Dict[str, Any]:
        with self._lock:
            self.stats["scans"] += 1
            manifest = self.load_manifest()
            if not manifest: return {"error": "Manifest introuvable"}
            all_guards = self.scan_guards_folder()
            active = manifest.get("active_guards", [])
            categories = manifest.get("categories", {})
            injected = []
            for g in all_guards:
                if g in active: continue
                active.append(g)
                cat = self.categorize_guard(g)
                if cat not in categories: categories[cat] = []
                if g not in categories[cat]: categories[cat].append(g)
                injected.append(g)
                logger.info(f"✅ Injecté: {g} → [{cat}]")
            if injected:
                manifest["active_guards"] = active
                manifest["categories"] = categories
                self._save_manifest(manifest)
                self.stats["injected"] += len(injected)
                return {"injected": injected, "total": len(active)}
            return {"injected": [], "total": len(active)}

    def start(self): self.is_running = True
    def stop(self): self.is_running = False
    def get_stats(self) -> Dict[str, Any]:
        with self._lock: return self.stats.copy()

_guard_instance: Optional[ManifestInjectorGuard] = None
def start_guard(kerberos_app=None) -> Optional[ManifestInjectorGuard]:
    global _guard_instance; _guard_instance = ManifestInjectorGuard(kerberos_app); return _guard_instance
def stop_guard() -> None:
    global _guard_instance
    if _guard_instance: _guard_instance.stop(); _guard_instance = None
def get_stats() -> Dict[str, Any]:
    global _guard_instance; return _guard_instance.get_stats() if _guard_instance else {}