#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
🛡️ Guard Anti-Toolbar — Détection et suppression de toolbars navigateur
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
- Scan extensions Chrome/Edge/Firefox/Opera
- Vérifie registres Windows (IE toolbars)
- Détecte toolbars connues (Yahoo, Ask, Conduit, etc.)
- Quarantaine sécurisée + RESTAURATION possible
- Rapport détaillé JSON + texte
- Intégration Kerberos (_GUARD_METRICS + get_stats)
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
Copyright (C) 2025 Victor Pozen — GPLv3
"""
import os
import sys
import json
import shutil
import time
import psutil
from datetime import datetime
from pathlib import Path
from typing import List, Dict, Optional

# ============================================================================
# === INTÉGRATION KERBEROS — _GUARD_METRICS ==================================
# ============================================================================

def _get_guard_metrics_ref():
    """Récupère la référence _GUARD_METRICS depuis kerberos.py (safe)"""
    try:
        import sys as _sys
        main_module = _sys.modules.get("__main__")
        if main_module and hasattr(main_module, "_GUARD_METRICS"):
            return main_module._GUARD_METRICS
    except Exception:
        pass
    # Fallback : dict local si Kerberos non chargé (mode standalone)
    if not hasattr(_get_guard_metrics_ref, "_local_metrics"):
        _get_guard_metrics_ref._local_metrics = {}
    return _get_guard_metrics_ref._local_metrics

_MODULE_NAME = Path(__file__).name  # "guard_anti_toolbar.py"
_SCAN_ACTIVE = False

def _publish_metric(level: float):
    """Publie l'activité du guard dans les VU-mètres Kerberos (0.0–1.0)"""
    try:
        metrics = _get_guard_metrics_ref()
        metrics[_MODULE_NAME] = max(0.0, min(1.0, level))
    except Exception:
        pass  # Silencieux en mode standalone

# ============================================================================
# === CONFIGURATION — CHEMINS CONSISTANTS ====================================
# ============================================================================

# Chemin racine Kerberos (parent du dossier guards)
KERBEROS_ROOT = Path(__file__).parent.parent.resolve()

ANTI_TOOLBAR_DIR = KERBEROS_ROOT / "lymph" / "anti_toolbar"
QUARANTINE_DIR   = ANTI_TOOLBAR_DIR / "quarantine"
REPORTS_DIR      = KERBEROS_ROOT / "reports"

for d in [ANTI_TOOLBAR_DIR, QUARANTINE_DIR, REPORTS_DIR]:
    d.mkdir(parents=True, exist_ok=True)

# Profondeur max pour rglob filesystem (évite scan infini)
MAX_SCAN_DEPTH = 4

KNOWN_TOOLBARS = {
    "yahoo_toolbar": {
        "names": ["Yahoo Toolbar", "Yahoo Companion"],
        "ids": ["{635ADC61-0C3E-4E5F-B0C0-1F0C0E0C0E0C}"],
        "files": ["ytoolbar.dll", "ycomp.dll"],
        "risk": "high"
    },
    "ask_toolbar": {
        "names": ["Ask Toolbar", "Ask Partner Network"],
        "ids": ["{D4027C7F-154A-4066-A1AD-4243D8127440}"],
        "files": ["askbar.dll", "asktp.dll"],
        "risk": "high"
    },
    "conduit_toolbar": {
        "names": ["Conduit Toolbar", "Community Toolbar"],
        "ids": ["{3CA2F312-6F6E-4B53-A66E-4E65E497C8C0}"],
        "files": ["conduit.dll", "engine.dll"],
        "risk": "critical"
    },
    "babylon_toolbar": {
        "names": ["Babylon Toolbar", "Babylon Translator"],
        "ids": ["{98889811-442D-49dd-99D7-DC866BE87DBC}"],
        "files": ["babylon.dll", "bttoolbar.dll"],
        "risk": "high"
    },
    "sweetim_toolbar": {
        "names": ["SweetIM Toolbar", "Sweet Packs"],
        "ids": ["{EEE6C35B-6118-11DC-9C72-001320C79847}"],
        "files": ["sweetim.dll", "simtoolbar.dll"],
        "risk": "critical"
    },
    "searchqu_toolbar": {
        "names": ["SearchQu Toolbar", "4shared Toolbar"],
        "ids": ["{995C996E-D918-4A8C-A302-45719A6F4EA7}"],
        "files": ["searchqu.dll", "sqtoolbar.dll"],
        "risk": "high"
    },
    "delta_homes": {
        "names": ["Delta Homes", "Delta Search"],
        "ids": ["{82E1477C-B154-48A3-98D4-831787D55E11}"],
        "files": ["delta.dll", "deltasearch.dll"],
        "risk": "critical"
    },
    "mypc_backup": {
        "names": ["MyPC Backup", "Backup MyPC"],
        "ids": [],
        "files": ["mypcbackup.exe", "backupmypc.exe"],
        "risk": "high"
    }
}

BROWSER_PATHS = {
    "chrome": {
        "extensions":  Path.home() / "AppData" / "Local" / "Google" / "Chrome" / "User Data" / "Default" / "Extensions",
        "preferences": Path.home() / "AppData" / "Local" / "Google" / "Chrome" / "User Data" / "Default" / "Preferences",
    },
    "edge": {
        "extensions":  Path.home() / "AppData" / "Local" / "Microsoft" / "Edge" / "User Data" / "Default" / "Extensions",
        "preferences": Path.home() / "AppData" / "Local" / "Microsoft" / "Edge" / "User Data" / "Default" / "Preferences",
    },
    "opera": {
        "extensions":  Path.home() / "AppData" / "Roaming" / "Opera Software" / "Opera Stable" / "Extensions",
        "preferences": None,
    },
}

# ============================================================================
# === UTILITAIRES ============================================================
# ============================================================================

def _rglob_limited(base: Path, pattern: str, max_depth: int) -> List[Path]:
    """rglob avec limite de profondeur — évite les scans infinis"""
    results = []
    try:
        base_depth = len(base.parts)
        for p in base.rglob(pattern):
            if len(p.parts) - base_depth <= max_depth:
                results.append(p)
                if len(results) >= 20:  # Limite absolue par pattern
                    break
    except Exception:
        pass
    return results

def _read_json_safe(path: Path) -> Optional[dict]:
    """Lecture JSON sécurisée — retourne None si erreur"""
    try:
        return json.loads(path.read_text(encoding="utf-8", errors="ignore"))
    except Exception:
        return None

# ============================================================================
# === CLASSE PRINCIPALE ======================================================
# ============================================================================

class AntiToolbarGuard:
    """Détection, quarantaine et restauration de toolbars de navigateur"""

    def __init__(self):
        self.detected_toolbars: List[Dict] = []
        self.scan_results: Dict = {
            "browsers_scanned": [],
            "toolbars_found":   [],
            "registry_entries": [],
            "files_found":      [],
            "timestamp":        datetime.now().isoformat(),
            "total_detected":   0,
        }
        self._alive = True  # Pour cleanup propre

    def destroy(self):
        """Cleanup propre (comme VUMeter)"""
        self._alive = False

    # ── Scan Chrome / Edge / Opera ────────────────────────────────────────
    def _scan_browser_extensions(self, browser: str) -> List[Dict]:
        found = []
        info = BROWSER_PATHS.get(browser)
        if not info:
            return found

        ext_dir = info.get("extensions")
        if not (ext_dir and ext_dir.exists()):
            return found

        self.scan_results["browsers_scanned"].append(browser)
        _publish_metric(0.4)

        for ext_folder in ext_dir.iterdir():
            if not ext_folder.is_dir():
                continue
            ext_id = ext_folder.name

            manifests = list(ext_folder.rglob("manifest.json"))
            for manifest_file in manifests[:3]:
                manifest = _read_json_safe(manifest_file)
                if not manifest:
                    continue
                ext_name = manifest.get("name", "Unknown")

                for toolbar_id, toolbar_info in KNOWN_TOOLBARS.items():
                    if ext_name in toolbar_info["names"] or ext_id in toolbar_info["ids"]:
                        item = {
                            "type":         "extension",
                            "browser":      browser,
                            "toolbar_id":   toolbar_id,
                            "extension_id": ext_id,
                            "name":         ext_name,
                            "path":         str(ext_folder),
                            "risk":         toolbar_info["risk"],
                            "manifest":     manifest,
                        }
                        found.append(item)
                        if toolbar_id not in self.scan_results["toolbars_found"]:
                            self.scan_results["toolbars_found"].append(toolbar_id)
        return found

    # ── Scan Firefox (via extensions.json) ────────────────────────────────
    def _scan_firefox(self) -> List[Dict]:
        found = []
        ff_profiles_root = Path.home() / "AppData" / "Roaming" / "Mozilla" / "Firefox" / "Profiles"

        if not ff_profiles_root.exists():
            return found

        self.scan_results["browsers_scanned"].append("firefox")
        _publish_metric(0.5)

        for profile_dir in ff_profiles_root.iterdir():
            if not profile_dir.is_dir():
                continue

            ext_json = profile_dir / "extensions.json"
            if ext_json.exists():
                data = _read_json_safe(ext_json)
                if data:
                    for addon in data.get("addons", []):
                        addon_id   = addon.get("id", "")
                        addon_name = addon.get("defaultLocale", {}).get("name", "")
                        for toolbar_id, toolbar_info in KNOWN_TOOLBARS.items():
                            if (addon_name in toolbar_info["names"]
                                    or addon_id in toolbar_info["ids"]):
                                found.append({
                                    "type":       "extension",
                                    "browser":    "firefox",
                                    "toolbar_id": toolbar_id,
                                    "extension_id": addon_id,
                                    "name":       addon_name,
                                    "path":       str(profile_dir / "extensions"),
                                    "risk":       toolbar_info["risk"],
                                    "manifest":   addon,
                                })
                                if toolbar_id not in self.scan_results["toolbars_found"]:
                                    self.scan_results["toolbars_found"].append(toolbar_id)
        return found

    # ── Scan Registre Windows ─────────────────────────────────────────────
    def _scan_registry(self) -> List[Dict]:
        found = []
        if os.name != 'nt':
            return found
        try:
            import winreg
            registry_keys = [
                (winreg.HKEY_CURRENT_USER,
                 r"Software\Microsoft\Internet Explorer\Toolbar"),
                (winreg.HKEY_CURRENT_USER,
                 r"Software\Microsoft\Windows\CurrentVersion\Explorer\Browser Helper Objects"),
                (winreg.HKEY_LOCAL_MACHINE,
                 r"SOFTWARE\Microsoft\Windows\CurrentVersion\Explorer\Browser Helper Objects"),
            ]
            _publish_metric(0.6)
            for hkey, path in registry_keys:
                try:
                    key = winreg.OpenKey(hkey, path, 0, winreg.KEY_READ)
                    i = 0
                    while True:
                        try:
                            subkey_name = winreg.EnumKey(key, i)
                            for toolbar_id, toolbar_info in KNOWN_TOOLBARS.items():
                                if subkey_name in toolbar_info["ids"]:
                                    found.append({
                                        "type":         "registry",
                                        "toolbar_id":   toolbar_id,
                                        "registry_key": f"{path}\\{subkey_name}",
                                        "name":         toolbar_info["names"][0],
                                        "risk":         toolbar_info["risk"],
                                    })
                                    self.scan_results["registry_entries"].append(subkey_name)
                            i += 1
                        except OSError:
                            break
                    winreg.CloseKey(key)
                except Exception:
                    pass
        except ImportError:
            pass
        return found

    # ── Scan Filesystem (profondeur limitée) ──────────────────────────────
    def _scan_filesystem(self) -> List[Dict]:
        found = []
        search_paths = [
            Path("C:\\Program Files"),
            Path("C:\\Program Files (x86)"),
            Path.home() / "AppData" / "Local",
            Path.home() / "AppData" / "Roaming",
        ]
        _publish_metric(0.7)
        for toolbar_id, toolbar_info in KNOWN_TOOLBARS.items():
            for file_pattern in toolbar_info.get("files", []):
                for base_path in search_paths:
                    if not base_path.exists():
                        continue
                    for filepath in _rglob_limited(base_path, file_pattern, MAX_SCAN_DEPTH):
                        found.append({
                            "type":       "file",
                            "toolbar_id": toolbar_id,
                            "filepath":   str(filepath),
                            "name":       toolbar_info["names"][0],
                            "risk":       toolbar_info["risk"],
                        })
                        self.scan_results["files_found"].append(str(filepath))
        return found

    # ── Quarantaine ───────────────────────────────────────────────────────
    def _quarantine_item(self, item: Dict) -> bool:
        if not self._alive:
            return False
        try:
            ts = datetime.now().strftime("%Y%m%d_%H%M%S")

            if item["type"] == "extension":
                src  = Path(item["path"])
                name = f"{item['toolbar_id']}_{ts}_{src.name}"
                dst  = QUARANTINE_DIR / name
                shutil.copytree(src, dst)
                meta = {
                    "original_path":   str(src),
                    "quarantine_path": str(dst),
                    "toolbar_id":      item["toolbar_id"],
                    "browser":         item.get("browser", "unknown"),
                    "timestamp":       ts,
                    "type":            "extension",
                }
                (QUARANTINE_DIR / f"{name}.meta.json").write_text(
                    json.dumps(meta, indent=2), encoding="utf-8")
                return True

            elif item["type"] == "file":
                src  = Path(item["filepath"])
                name = f"{item['toolbar_id']}_{ts}_{src.name}"
                dst  = QUARANTINE_DIR / name
                shutil.copy2(src, dst)
                meta = {
                    "original_path":   str(src),
                    "quarantine_path": str(dst),
                    "toolbar_id":      item["toolbar_id"],
                    "timestamp":       ts,
                    "type":            "file",
                }
                (QUARANTINE_DIR / f"{name}.meta.json").write_text(
                    json.dumps(meta, indent=2), encoding="utf-8")
                return True

            elif item["type"] == "registry":
                meta = {
                    "registry_key": item["registry_key"],
                    "toolbar_id":   item["toolbar_id"],
                    "timestamp":    ts,
                    "type":         "registry",
                    "action":       "logged_only",
                }
                (QUARANTINE_DIR / f"registry_{item['toolbar_id']}_{ts}.meta.json").write_text(
                    json.dumps(meta, indent=2), encoding="utf-8")
                return True

        except Exception as e:
            print(f"❌ [Anti-Toolbar] Erreur quarantaine : {e}")
        return False

    # ── RESTAURATION ──────────────────────────────────────────────────────
    def list_quarantine(self) -> List[Dict]:
        """Liste tous les éléments en quarantaine"""
        items = []
        for meta_file in QUARANTINE_DIR.glob("*.meta.json"):
            data = _read_json_safe(meta_file)
            if data:
                data["meta_file"] = str(meta_file)
                items.append(data)
        return items

    def restore_item(self, meta_file_path: str) -> bool:
        """Restaure un élément depuis la quarantaine"""
        meta_path = Path(meta_file_path)
        meta = _read_json_safe(meta_path)
        if not meta:
            return False

        original = Path(meta["original_path"])
        quarantine = Path(meta["quarantine_path"])

        if not quarantine.exists():
            return False

        try:
            if meta["type"] == "extension":
                if original.exists():
                    shutil.rmtree(original)
                shutil.copytree(quarantine, original)
            elif meta["type"] == "file":
                original.parent.mkdir(parents=True, exist_ok=True)
                shutil.copy2(quarantine, original)

            # Supprime de la quarantaine après restauration
            if quarantine.is_dir():
                shutil.rmtree(quarantine)
            else:
                quarantine.unlink(missing_ok=True)
            meta_path.unlink(missing_ok=True)
            return True
        except Exception:
            return False

    def restore_all(self) -> Dict:
        """Restaure tous les éléments en quarantaine"""
        results = {"restored": 0, "failed": 0}
        for item in self.list_quarantine():
            if self.restore_item(item["meta_file"]):
                results["restored"] += 1
            else:
                results["failed"] += 1
        return results

    # ── Scan complet ──────────────────────────────────────────────────────
    def scan(self) -> Dict:
        global _SCAN_ACTIVE
        _SCAN_ACTIVE = True
        _publish_metric(0.2)

        for browser in BROWSER_PATHS.keys():
            self.detected_toolbars.extend(self._scan_browser_extensions(browser))

        self.detected_toolbars.extend(self._scan_firefox())
        self.detected_toolbars.extend(self._scan_registry())
        self.detected_toolbars.extend(self._scan_filesystem())

        self.scan_results["total_detected"] = len(self.detected_toolbars)
        self.scan_results["detected_items"] = self.detected_toolbars

        # VU-mètre : activité proportionnelle aux menaces
        threat_level = min(1.0, len(self.detected_toolbars) / 5.0)
        _publish_metric(max(0.1, threat_level))
        _SCAN_ACTIVE = False

        return self.scan_results

    def quarantine_all(self) -> Dict:
        results = {"quarantined": 0, "failed": 0, "items": []}
        for item in self.detected_toolbars:
            if self._quarantine_item(item):
                results["quarantined"] += 1
                results["items"].append({"item": item, "status": "quarantined"})
            else:
                results["failed"] += 1
                results["items"].append({"item": item, "status": "failed"})
        return results

    def generate_report(self) -> str:
        lines = [
            "🛡️ RAPPORT ANTI-TOOLBAR — Scan de sécurité",
            "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━",
            f"Date     : {self.scan_results['timestamp']}",
            f"Browsers : {', '.join(self.scan_results['browsers_scanned']) or 'aucun'}",
            f"Toolbars : {self.scan_results.get('total_detected', 0)} détectée(s)",
            f"Registre : {len(self.scan_results['registry_entries'])} entrée(s)",
            f"Fichiers : {len(self.scan_results['files_found'])} fichier(s)",
            "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━",
        ]
        if self.detected_toolbars:
            lines.append("⚠️  TOOLBAR(S) DÉTECTÉE(S) :")
            for i, item in enumerate(self.detected_toolbars, 1):
                risk = item.get("risk", "unknown").upper()
                lines.append(f"   {i}. {item.get('name', 'Unknown')} [{risk}]")
                lines.append(f"      Type    : {item['type']}")
                if item["type"] == "extension":
                    lines.append(f"      Browser : {item.get('browser', '?')}")
                lines.append("")
        else:
            lines.append("✅ Aucune toolbar suspecte détectée")
        lines.append("━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━")
        return "\n".join(lines)

# ============================================================================
# === INTÉGRATION KERBEROS — get_stats() =====================================
# ============================================================================

def get_stats() -> Dict:
    """
    Retourne les statistiques pour l'onglet Guards de Kerberos.
    Compatible avec le format de guard_netshield.py
    """
    stats = {
        "total_blocked":  0,
        "government":     0,
        "trackers":       0,
        "malware":        0,
        "quarantined":    0,
        "last_scan":      "jamais",
        "guard_name":     "Anti-Toolbar",
    }
    try:
        meta_files = list(QUARANTINE_DIR.glob("*.meta.json"))
        stats["quarantined"] = len(meta_files)
        stats["total_blocked"] = len(meta_files)

        reports = sorted(REPORTS_DIR.glob("anti_toolbar_*.json"))
        if reports:
            latest = _read_json_safe(reports[-1])
            if latest:
                stats["total_blocked"] = latest.get("total_detected", 0)
                stats["last_scan"]     = latest.get("timestamp", "?")
    except Exception:
        pass
    return stats

# ============================================================================
# === POINTS D'ENTRÉE ========================================================
# ============================================================================

def start_guard():
    """Point d'entrée pour Kerberos (chargement passif)"""
    print("🛡️ [Anti-Toolbar] Module chargé — En attente de scans...")
    _publish_metric(0.05)
    return AntiToolbarGuard()

def run(quiet: bool = False) -> Dict:
    """Exécution complète (scan + rapport + sauvegarde)"""
    if not quiet:
        print("""
╔════════════════════════════════════════════════════════════╗
║  🛡️ KERBEROS ANTI-TOOLBAR — Détection de toolbars         ║
║                                                            ║
║  • Yahoo  • Ask  • Conduit  • Babylon                     ║
║  • SweetIM  • SearchQu  • Delta Homes                     ║
╚════════════════════════════════════════════════════════════╝
""")
    guard   = AntiToolbarGuard()
    results = guard.scan()

    if not quiet:
        print("\n" + guard.generate_report())
        report_file = REPORTS_DIR / f"anti_toolbar_{int(datetime.now().timestamp())}.json"
        report_file.write_text(
            json.dumps(results, indent=2, ensure_ascii=False), encoding="utf-8")
        print(f"\n📄 Rapport sauvegardé : {report_file}")

    return results

if __name__ == "__main__":
    import argparse
    parser = argparse.ArgumentParser(description="🛡️ Kerberos Anti-Toolbar Guard")
    parser.add_argument("--quarantine",  action="store_true",
                        help="Met en quarantaine les toolbars détectées")
    parser.add_argument("--restore-all", action="store_true",
                        help="Restaure tous les éléments en quarantaine")
    parser.add_argument("--list-quarantine", action="store_true",
                        help="Liste les éléments en quarantaine")
    parser.add_argument("--quiet", action="store_true",
                        help="Mode silencieux")
    args = parser.parse_args()

    if args.restore_all:
        g = AntiToolbarGuard()
        r = g.restore_all()
        print(f"♻️  Restauration : {r['restored']} réussie(s), {r['failed']} échec(s)")
        sys.exit(0)

    if args.list_quarantine:
        g = AntiToolbarGuard()
        items = g.list_quarantine()
        if items:
            print(f"📦 {len(items)} élément(s) en quarantaine :")
            for item in items:
                print(f"  • [{item['type']}] {item['toolbar_id']} — {item['timestamp']}")
        else:
            print("✅ Quarantaine vide")
        sys.exit(0)

    results = run(quiet=args.quiet)

    if args.quarantine and results.get("total_detected", 0) > 0:
        guard = AntiToolbarGuard()
        guard.detected_toolbars = results.get("detected_items", [])
        qr = guard.quarantine_all()
        print(f"\n📦 Quarantaine : {qr['quarantined']} réussie(s), {qr['failed']} échec(s)")

    sys.exit(0 if results.get("total_detected", 0) == 0 else 1)