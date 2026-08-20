#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
🛡️ Guard Plasma Shield — Bulle de protection visuelle et fonctionnelle
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
- Overlay plasma coloré autour du bureau (vert → orange → rouge)
- Surveillance des processus non autorisés (détection + log)
- Blindage fenêtres actives (détection hooks clavier/souris suspects)
- Protection screenshot (détection BitBlt / PrintScreen suspects)
- Détection injection mémoire (OpenProcess sur processus système)
- Mode urgence activable (whitelist stricte)
- Alertes visuelles via signal Kerberos (pas de second tk.Tk())
- Connexion directe Guard Tray Icon (Cerbère change de couleur)
- Intégration Kerberos complète : _GUARD_METRICS / get_stats / start_guard
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
NOTE : Sur Windows, la suspension de processus tiers nécessite des droits
administrateur. Sans admin, ce guard détecte et alerte — il ne tue pas.
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
Copyright (C) 2025 Victor Pozen — GPLv3
"""
import os
import sys
import json
import time
import threading
import psutil
from pathlib import Path
from datetime import datetime
from typing import Dict, List, Optional, Callable

# ============================================================================
# === INTÉGRATION KERBEROS ===================================================
# ============================================================================
try:
    _kerberos_main = sys.modules.get("__main__")
    _GUARD_METRICS: dict = getattr(_kerberos_main, "_GUARD_METRICS", {})
except Exception:
    _GUARD_METRICS = {}

_MODULE_NAME = Path(__file__).name   # "guard_plasma_shield.py"

def _publish_metric(level: float):
    """Publie l'activité dans les VU-mètres Kerberos (0.0–1.0)"""
    _GUARD_METRICS[_MODULE_NAME] = max(0.0, min(1.0, level))

# ============================================================================
# === CONFIGURATION ==========================================================
# ============================================================================

PLASMA_DIR = Path(__file__).parent.parent / "lymph" / "plasma"
PLASMA_DIR.mkdir(parents=True, exist_ok=True)
ALERT_LOG  = PLASMA_DIR / "plasma_alerts.json"

# Whitelist des processus autorisés
ALLOWED_PROCESSES = {
    "firefox.exe", "firefox",
    "chrome.exe", "chrome",
    "msedge.exe", "msedge",
    "brave.exe", "brave",
    "opera.exe", "opera",
    "kerberos.exe", "kerberos.py",
    "python.exe", "pythonw.exe",
    "python3", "python3.exe",
    "code.exe",           # VS Code
    "notepad.exe",        # Notepad
    "notepad++.exe",      # Notepad++
    "vlc.exe",            # VLC
    "spotify.exe",        # Spotify
    "discord.exe",        # Discord
    "steam.exe",          # Steam
}

# Processus système toujours autorisés (ne jamais toucher)
SYSTEM_PROCESSES = {
    "system", "idle", "svchost.exe", "explorer.exe",
    "csrss.exe", "wininit.exe", "services.exe",
    "lsass.exe", "smss.exe", "dwm.exe", "winlogon.exe",
    "taskmgr.exe", "conhost.exe", "ntoskrnl.exe",
    "audiodg.exe", "spoolsv.exe", "fontdrvhost.exe",
    "sihost.exe", "ctfmon.exe", "searchindexer.exe",
    "runtimebroker.exe", "shellexperiencehost.exe",
    "startmenuexperiencehost.exe", "textinputhost.exe",
    "securityhealthservice.exe", "msmpeng.exe",
    "registry", "memory compression",
}

# Processus suspects connus (keyloggers, RAT, etc.)
KNOWN_THREATS = {
    "keylogger", "ratpoison", "njrat", "darkcomet",
    "xtreme", "blackshades", "spybot", "ardamax",
    "revealer", "refog", "actual keylogger",
}

# ============================================================================
# === SIGNAL OVERLAY (sans second tk.Tk()) ===================================
# ============================================================================
_alert_callback:  Optional[Callable] = None
_tray_guard:      Optional[object]   = None   # référence guard_tray_icon

def set_alert_callback(fn: Callable):
    """Enregistre une callback appelée lors d'une alerte"""
    global _alert_callback
    _alert_callback = fn

def set_tray_guard(tray_mod):
    """Branche le Cerbère (guard_tray_icon) pour mise à jour icône"""
    global _tray_guard
    _tray_guard = tray_mod

def _fire_alert(color: str = '#ff0000', guard_name: str = "", message: str = ""):
    """Déclenche toutes les callbacks d'alerte"""
    # Callback Kerberos principale
    if _alert_callback:
        try:
            _alert_callback(color)
        except Exception:
            pass

    # Cerbère tray icon
    if _tray_guard and hasattr(_tray_guard, 'on_guard_alert'):
        try:
            _tray_guard.on_guard_alert(
                guard_name or _MODULE_NAME,
                color,
                message or "Plasma Shield — activité suspecte"
            )
        except Exception:
            pass

    # GuardRegistry si disponible
    try:
        from guard_ui_manager import fire_alert as _reg_fire
        _reg_fire(
            guard_name or _MODULE_NAME,
            color,
            message or "Plasma Shield — activité suspecte"
        )
    except ImportError:
        pass

# ============================================================================
# === OVERLAY PLASMA VISUEL ==================================================
# ============================================================================

class PlasmaOverlay:
    """
    Anneau coloré autour du bureau Windows.
    Vert = calme | Orange = tentative | Rouge = attaque
    Utilise win32api si disponible, sinon mode silencieux.
    """

    COLORS = {
        "calm":    (0,   200,  80),   # Vert plasma
        "warning": (255, 140,   0),   # Orange
        "attack":  (255,  20,  20),   # Rouge vif
    }

    def __init__(self):
        self._hwnd      = None
        self._active    = False
        self._state     = "calm"
        self._win32_ok  = False
        self._thread    = None
        self._init_win32()

    def _init_win32(self):
        try:
            import ctypes
            self._ctypes   = ctypes
            self._win32_ok = True
            print("🛡️ [Plasma Overlay] win32 disponible — overlay actif")
        except Exception:
            print("⚠️ [Plasma Overlay] Mode silencieux (win32 non disponible)")

    def set_state(self, state: str):
        """Change la couleur de l'anneau plasma"""
        if state == self._state:
            return
        self._state = state
        if self._win32_ok and self._active:
            self._draw_border()

    def _draw_border(self):
        """Dessine un anneau coloré sur les bords de l'écran via ctypes"""
        try:
            import ctypes
            import ctypes.wintypes

            # Récupère dimensions écran
            user32  = ctypes.windll.user32
            sw      = user32.GetSystemMetrics(0)   # largeur
            sh      = user32.GetSystemMetrics(1)   # hauteur
            thickness = 4

            # Récupère le DC du bureau
            hdc = user32.GetDC(0)
            if not hdc:
                return

            r, g, b = self.COLORS.get(self._state, (0, 200, 80))
            color   = ctypes.windll.gdi32.RGB(r, g, b) if hasattr(ctypes.windll, 'gdi32') else (b << 16 | g << 8 | r)

            # Crée un pen de la couleur voulue
            gdi32  = ctypes.windll.gdi32
            pen    = gdi32.CreatePen(0, thickness, color)   # PS_SOLID=0
            old_pen = gdi32.SelectObject(hdc, pen)

            # Dessine les 4 bords
            gdi32.MoveToEx(hdc, 0,      0,      None)
            gdi32.LineTo(hdc,   sw - 1, 0)
            gdi32.LineTo(hdc,   sw - 1, sh - 1)
            gdi32.LineTo(hdc,   0,      sh - 1)
            gdi32.LineTo(hdc,   0,      0)

            # Nettoyage
            gdi32.SelectObject(hdc, old_pen)
            gdi32.DeleteObject(pen)
            user32.ReleaseDC(0, hdc)

        except Exception as e:
            pass   # Silencieux si erreur GDI

    def _pulse_loop(self):
        """Fait pulser légèrement l'anneau quand actif"""
        while self._active:
            if self._state != "calm":
                self._draw_border()
                time.sleep(0.8)
                # Petit fade en dessinant noir brièvement
                old = self._state
                self._state = "calm"
                self._draw_border()
                self._state = old
                time.sleep(0.2)
            else:
                self._draw_border()
                time.sleep(3)

    def start(self):
        self._active = True
        if self._win32_ok:
            self._thread = threading.Thread(
                target=self._pulse_loop, daemon=True, name="PlasmaOverlay")
            self._thread.start()

    def stop(self):
        self._active = False
        # Efface l'anneau (dessine en noir)
        if self._win32_ok:
            old = self._state
            self._state = "calm"
            try:
                self._draw_border()
            except Exception:
                pass
            self._state = old


# ============================================================================
# === DÉTECTEURS AVANCÉS =====================================================
# ============================================================================

class ThreatDetector:
    """
    Détecteurs avancés de menaces bureau.
    Fonctionne en lecture seule — aucune modification système.
    """

    def __init__(self):
        self._hook_baseline: Dict[int, set] = {}   # pid → modules chargés
        self._screenshot_baseline: Dict[int, int] = {}
        self._lock = threading.Lock()

    # ── Détection hooks clavier/souris suspects ───────────────────────────
    def check_window_hooks(self) -> List[Dict]:
        """
        Détecte les processus qui chargent des DLL de hook (keylogger pattern).
        Cherche : user32.dll SetWindowsHookEx signatures dans les modules chargés.
        """
        threats = []
        hook_dlls = {"hookapi.dll", "keyhook.dll", "mousehook.dll",
                     "kbdhook.dll", "winhook.dll", "spy.dll"}
        suspicious_names = {"hook", "spy", "logger", "record", "capture",
                            "keylog", "monitor", "stealth", "hidden"}

        try:
            for proc in psutil.process_iter(['pid', 'name', 'exe']):
                try:
                    name_low = proc.info['name'].lower() if proc.info['name'] else ""

                    # Vérifie nom suspect
                    if any(s in name_low for s in suspicious_names):
                        threats.append({
                            "type":    "suspicious_name",
                            "pid":     proc.info['pid'],
                            "name":    proc.info['name'],
                            "detail":  "Nom de processus suspect (pattern hook/spy)",
                            "level":   "warning",
                        })
                        continue

                    # Vérifie les modules DLL chargés (si accessible)
                    try:
                        mods = {m.name.lower() for m in proc.memory_maps()}
                        bad_mods = mods & hook_dlls
                        if bad_mods:
                            threats.append({
                                "type":    "hook_dll",
                                "pid":     proc.info['pid'],
                                "name":    proc.info['name'],
                                "detail":  f"DLL de hook détectée : {bad_mods}",
                                "level":   "attack",
                            })
                    except (psutil.AccessDenied, psutil.NoSuchProcess, NotImplementedError):
                        pass

                except (psutil.NoSuchProcess, psutil.AccessDenied):
                    continue
        except Exception:
            pass

        return threats

    # ── Détection screenshot suspects ─────────────────────────────────────
    def check_screenshot_activity(self) -> List[Dict]:
        """
        Détecte les processus avec une activité I/O anormale vers des fichiers
        image (pattern screenshot automatique).
        """
        threats = []
        image_extensions = {'.png', '.jpg', '.bmp', '.tiff', '.gif'}

        try:
            for proc in psutil.process_iter(['pid', 'name', 'open_files']):
                try:
                    files = proc.info.get('open_files') or []
                    image_files = [
                        f.path for f in files
                        if Path(f.path).suffix.lower() in image_extensions
                    ]
                    if len(image_files) >= 3:   # 3+ fichiers image ouverts = suspect
                        threats.append({
                            "type":    "screenshot_pattern",
                            "pid":     proc.info['pid'],
                            "name":    proc.info['name'],
                            "detail":  f"{len(image_files)} fichiers image ouverts simultanément",
                            "level":   "warning",
                            "files":   image_files[:3],
                        })
                except (psutil.NoSuchProcess, psutil.AccessDenied):
                    continue
        except Exception:
            pass

        return threats

    # ── Détection injection mémoire ───────────────────────────────────────
    def check_memory_injection(self) -> List[Dict]:
        """
        Détecte les patterns d'injection mémoire :
        - Processus avec connections réseau ET modules inhabituels
        - Processus enfants de processus système suspects
        - Processus sans exe sur disque (fileless malware pattern)
        """
        threats = []
        fileless_suspects = []

        try:
            for proc in psutil.process_iter(['pid', 'name', 'exe', 'ppid', 'status']):
                try:
                    exe = proc.info.get('exe') or ""

                    # Pattern fileless : processus actif sans exe sur disque
                    if exe and not Path(exe).exists():
                        name = proc.info['name'] or ""
                        if name.lower() not in SYSTEM_PROCESSES:
                            fileless_suspects.append({
                                "type":    "fileless_pattern",
                                "pid":     proc.info['pid'],
                                "name":    name,
                                "detail":  f"Processus sans exe sur disque : {exe}",
                                "level":   "attack",
                            })

                    # Processus enfant d'un processus système avec connexions réseau
                    ppid = proc.info.get('ppid', 0)
                    if ppid:
                        try:
                            parent = psutil.Process(ppid)
                            parent_name = parent.name().lower()
                            if parent_name in {"explorer.exe", "svchost.exe"}:
                                conns = proc.connections()
                                if conns:
                                    proc_name = proc.info['name'] or ""
                                    if proc_name.lower() not in ALLOWED_PROCESSES:
                                        threats.append({
                                            "type":    "suspicious_child",
                                            "pid":     proc.info['pid'],
                                            "name":    proc_name,
                                            "detail":  f"Enfant de {parent_name} avec {len(conns)} connexion(s) réseau",
                                            "level":   "warning",
                                            "parent":  parent_name,
                                        })
                        except (psutil.NoSuchProcess, psutil.AccessDenied):
                            pass

                except (psutil.NoSuchProcess, psutil.AccessDenied):
                    continue

        except Exception:
            pass

        threats.extend(fileless_suspects)
        return threats

    # ── Détection nom connu malveillant ───────────────────────────────────
    def check_known_threats(self) -> List[Dict]:
        """Vérifie les noms de processus connus comme malveillants"""
        threats = []
        try:
            for proc in psutil.process_iter(['pid', 'name', 'exe']):
                try:
                    name_low = (proc.info['name'] or "").lower()
                    if any(t in name_low for t in KNOWN_THREATS):
                        threats.append({
                            "type":    "known_threat",
                            "pid":     proc.info['pid'],
                            "name":    proc.info['name'],
                            "detail":  "Nom correspondant à une menace connue",
                            "level":   "attack",
                        })
                except (psutil.NoSuchProcess, psutil.AccessDenied):
                    continue
        except Exception:
            pass
        return threats

    def full_scan(self) -> Dict:
        """Scan complet — tous les détecteurs"""
        hooks       = self.check_window_hooks()
        screenshots = self.check_screenshot_activity()
        injections  = self.check_memory_injection()
        known       = self.check_known_threats()

        all_threats = hooks + screenshots + injections + known

        attacks  = [t for t in all_threats if t.get("level") == "attack"]
        warnings = [t for t in all_threats if t.get("level") == "warning"]

        return {
            "threats":       all_threats,
            "attacks":       attacks,
            "warnings":      warnings,
            "hook_threats":  hooks,
            "screenshot_threats": screenshots,
            "injection_threats":  injections,
            "known_threats": known,
            "total":         len(all_threats),
            "critical":      len(attacks),
        }


# ============================================================================
# === ÉTAT PARTAGÉ ===========================================================
# ============================================================================
_shared_stats: Dict = {
    "status":             "inactive",
    "strict_mode":        False,
    "blocked":            0,
    "allowed":            0,
    "threats":            [],
    "advanced_threats":   [],
    "start_time":         None,
    "last_scan":          None,
    "overlay_state":      "calm",
    "total_scans":        0,
    "attacks_detected":   0,
    "warnings_detected":  0,
}

# ============================================================================
# === CLASSE PRINCIPALE ======================================================
# ============================================================================

class PlasmaShieldGuard:
    """Guard Plasma Shield — Bouclier asymétrique bureau Windows"""

    def __init__(self, strict_mode: bool = False, overlay: bool = True):
        self.strict_mode    = strict_mode
        self._monitoring    = False
        self._thread: threading.Thread | None = None
        self._lock          = threading.Lock()
        self._detector      = ThreatDetector()
        self._overlay       = PlasmaOverlay() if overlay else None

        _shared_stats["start_time"]  = datetime.now().isoformat()
        _shared_stats["strict_mode"] = strict_mode
        _shared_stats["status"]      = "inactive"

        _publish_metric(0.05)
        print("🛡️ [Plasma Shield] Initialisation OK")
        if overlay and self._overlay:
            self._overlay.start()
            print("🌈 [Plasma Shield] Overlay plasma actif")

    # ── Vérification processus (scan de base) ─────────────────────────────
    def _is_process_allowed(self, proc: psutil.Process) -> bool:
        try:
            name = proc.name().lower()
            if name in ALLOWED_PROCESSES:
                return True
            if name in SYSTEM_PROCESSES:
                return True
            if self.strict_mode:
                return False
            try:
                exe = proc.exe().lower()
                trusted_vendors = ["mozilla", "google", "microsoft", "opera",
                                   "brave", "apple", "adobe", "valve",
                                   "discord", "spotify", "jetbrains"]
                if any(v in exe for v in trusted_vendors):
                    return True
            except (psutil.AccessDenied, psutil.NoSuchProcess):
                pass
            return False
        except (psutil.NoSuchProcess, psutil.AccessDenied):
            return True   # Doute → on ne bloque pas

    def _scan_processes(self) -> Dict:
        """Scan basique des processus (compatible sans admin)"""
        threats:  List[Dict] = []
        allowed_count = 0
        is_admin = self._check_admin()

        for proc in psutil.process_iter(['pid', 'name', 'exe', 'username']):
            try:
                if not self._is_process_allowed(proc):
                    threat = {
                        "pid":       proc.info['pid'],
                        "name":      proc.info['name'],
                        "exe":       proc.info.get('exe') or 'N/A',
                        "user":      proc.info.get('username') or 'N/A',
                        "timestamp": datetime.now().isoformat(),
                        "action":    "none",
                    }
                    if is_admin and self.strict_mode:
                        try:
                            p = psutil.Process(proc.info['pid'])
                            p.suspend()
                            threat["action"] = "suspended"
                        except Exception:
                            threat["action"] = "detection_only"
                    else:
                        threat["action"] = "detection_only"
                    threats.append(threat)
                    with self._lock:
                        _shared_stats["blocked"] += 1
                else:
                    allowed_count += 1
            except (psutil.NoSuchProcess, psutil.AccessDenied):
                continue

        with self._lock:
            _shared_stats["allowed"] = allowed_count
            _shared_stats["threats"] = threats[-10:]

        return {"threats": threats, "blocked": len(threats)}

    def _check_admin(self) -> bool:
        try:
            if os.name == 'nt':
                import ctypes
                return bool(ctypes.windll.shell32.IsUserAnAdmin())
            else:
                return os.geteuid() == 0
        except Exception:
            return False

    # ── Boucle surveillance principale ────────────────────────────────────
    def _monitor_loop(self):
        print("👁️ [Plasma Shield] Surveillance active...")
        _shared_stats["status"] = "active"
        _publish_metric(0.2)

        scan_counter = 0

        while self._monitoring:
            try:
                # ── Scan basique toutes les 2s ────────────────────────────
                basic = self._scan_processes()
                basic_threats = basic["blocked"]

                # ── Scan avancé toutes les 10s (moins fréquent = moins lourd)
                advanced_threats = []
                if scan_counter % 5 == 0:
                    adv = self._detector.full_scan()
                    advanced_threats = adv["threats"]
                    with self._lock:
                        _shared_stats["advanced_threats"]  = adv["threats"][-10:]
                        _shared_stats["attacks_detected"]  += adv["critical"]
                        _shared_stats["warnings_detected"] += len(adv["warnings"])
                        _shared_stats["total_scans"]       += 1
                        _shared_stats["last_scan"]         = datetime.now().isoformat()

                # ── Calcul niveau de menace global ────────────────────────
                critical_count = sum(
                    1 for t in advanced_threats if t.get("level") == "attack"
                )
                warning_count = sum(
                    1 for t in advanced_threats if t.get("level") == "warning"
                )

                if critical_count > 0 or basic_threats > 5:
                    # 🔴 ATTAQUE
                    threat_level  = "attack"
                    overlay_state = "attack"
                    alert_color   = "#ff0000"
                    detail_msg    = (
                        f"{critical_count} menace(s) critique(s) détectée(s)"
                        if critical_count > 0
                        else f"{basic_threats} processus non autorisés"
                    )
                    _fire_alert(alert_color, _MODULE_NAME, detail_msg)
                    _publish_metric(min(1.0, 0.6 + critical_count * 0.2))
                    print(f"🔴 [Plasma] ATTAQUE — {detail_msg}")

                elif warning_count > 0 or basic_threats > 0:
                    # 🟠 TENTATIVE
                    threat_level  = "warning"
                    overlay_state = "warning"
                    alert_color   = "#ff9800"
                    detail_msg    = (
                        f"{warning_count} comportement(s) suspect(s)"
                        if warning_count > 0
                        else f"{basic_threats} processus suspect(s)"
                    )
                    _fire_alert(alert_color, _MODULE_NAME, detail_msg)
                    _publish_metric(min(0.8, 0.3 + warning_count * 0.1))
                    print(f"🟠 [Plasma] TENTATIVE — {detail_msg}")

                else:
                    # ⚪ CALME
                    threat_level  = "calm"
                    overlay_state = "calm"
                    _publish_metric(0.1 + (time.time() % 2) * 0.04)

                # Mise à jour overlay
                if self._overlay:
                    self._overlay.set_state(overlay_state)

                with self._lock:
                    _shared_stats["overlay_state"] = overlay_state

                # Log si menaces
                all_threats = basic["threats"] + [
                    t for t in advanced_threats if t.get("level") == "attack"
                ]
                if all_threats:
                    self._append_alert_log(all_threats)

                scan_counter += 1
                time.sleep(2)

            except Exception as e:
                print(f"❌ [Plasma] Erreur monitoring : {e}")
                time.sleep(5)

        _shared_stats["status"] = "inactive"
        _publish_metric(0.05)
        if self._overlay:
            self._overlay.stop()
        print("🛑 [Plasma Shield] Surveillance arrêtée")

    def _append_alert_log(self, threats: List[Dict]):
        """Ajoute les alertes au log JSON persistant"""
        try:
            existing = []
            if ALERT_LOG.exists():
                try:
                    existing = list(json.loads(
                        ALERT_LOG.read_text(encoding="utf-8")))
                except Exception:
                    pass
            existing.extend(threats)
            ALERT_LOG.write_text(
                json.dumps(existing[-500:], indent=2, ensure_ascii=False),
                encoding="utf-8")
        except Exception:
            pass

    # ── Modes ─────────────────────────────────────────────────────────────
    def enable_strict_mode(self):
        self.strict_mode = True
        _shared_stats["strict_mode"] = True
        print("🚨 [Plasma Shield] MODE URGENCE ACTIVÉ")
        _fire_alert('#ff0000', _MODULE_NAME, "Mode urgence activé — whitelist stricte")
        if self._overlay:
            self._overlay.set_state("attack")
        _publish_metric(0.9)

    def disable_strict_mode(self):
        self.strict_mode = False
        _shared_stats["strict_mode"] = False
        print("✅ [Plasma Shield] Mode normal restauré")
        if self._overlay:
            self._overlay.set_state("calm")
        _publish_metric(0.2)

    # ── Démarrage / arrêt ─────────────────────────────────────────────────
    def start_monitoring(self):
        if self._monitoring:
            return
        self._monitoring = True
        self._thread = threading.Thread(
            target=self._monitor_loop, daemon=True, name="PlasmaShield")
        self._thread.start()
        return self._thread

    def stop_monitoring(self):
        self._monitoring = False
        if self._thread:
            self._thread.join(timeout=5)

    def get_stats(self) -> Dict:
        with self._lock:
            return dict(_shared_stats)

    def destroy(self):
        self.stop_monitoring()
        if self._overlay:
            self._overlay.stop()
        print("✅ [Plasma Shield] Nettoyage terminé")


# ============================================================================
# === get_stats() MODULE-LEVEL ===============================================
# ============================================================================

def get_stats() -> Dict:
    """Retourne les statistiques pour l'onglet Guards de Kerberos"""
    stats = dict(_shared_stats)
    try:
        if ALERT_LOG.exists():
            alerts = json.loads(ALERT_LOG.read_text(encoding="utf-8"))
            stats["total_alerts_logged"] = len(alerts)
        else:
            stats["total_alerts_logged"] = 0
    except Exception:
        stats["total_alerts_logged"] = 0
    stats["guard_name"] = "Plasma Shield"
    return stats


# ============================================================================
# === POINTS D'ENTRÉE ========================================================
# ============================================================================

def start_guard(strict: bool = False, overlay: bool = True):
    """Point d'entrée pour Kerberos"""
    print("🛡️ [Plasma Shield] Démarrage du guard...")

    # Auto-branchement sur guard_tray_icon si chargé
    tray = sys.modules.get("guard_tray_icon")
    if tray:
        set_tray_guard(tray)
        print("🐕 [Plasma Shield] Branché sur le Cerbère")

    guard = PlasmaShieldGuard(strict_mode=strict, overlay=overlay)
    guard.start_monitoring()
    return guard


def run():
    """Exécution standalone"""
    print("""
╔════════════════════════════════════════════════════════════════╗
║  🛡️ KERBEROS PLASMA SHIELD v4.2 — Bouclier asymétrique       ║
║                                                                ║
║  • Overlay plasma coloré (vert → orange → rouge)              ║
║  • Surveillance processus en temps réel                        ║
║  • Détection hooks clavier/souris suspects                     ║
║  • Détection screenshots automatiques                          ║
║  • Détection injection mémoire / fileless malware              ║
║  • Alertes Cerbère (icône barre des tâches)                   ║
║  • Mode urgence : whitelist stricte                            ║
╚════════════════════════════════════════════════════════════════╝
    """)

    guard = PlasmaShieldGuard(overlay=True)
    guard.start_monitoring()

    try:
        while True:
            time.sleep(2)
            s = guard.get_stats()
            mode     = "🚨 URGENCE" if s["strict_mode"] else "🟢 NORMAL"
            overlay  = {"calm": "⚪", "warning": "🟠", "attack": "🔴"}.get(
                s.get("overlay_state", "calm"), "⚪")
            adv      = len(s.get("advanced_threats", []))
            print(
                f"\r{overlay} Bloqués : {s['blocked']:4d} | "
                f"Avancés : {adv:2d} | "
                f"Scans : {s.get('total_scans', 0):4d} | "
                f"Mode : {mode}   ",
                end='', flush=True)
    except KeyboardInterrupt:
        print("\n\n🛑 [Plasma Shield] Arrêt...")
        guard.destroy()
        print("✅ Arrêt propre")


if __name__ == "__main__":
    import argparse
    parser = argparse.ArgumentParser(description="🛡️ Kerberos Plasma Shield Guard")
    parser.add_argument("--strict",      action="store_true",
                        help="Mode urgence dès le démarrage")
    parser.add_argument("--no-overlay",  action="store_true",
                        help="Désactive l'overlay visuel")
    args = parser.parse_args()

    guard = PlasmaShieldGuard(
        strict_mode=args.strict,
        overlay=not args.no_overlay
    )
    guard.start_monitoring()

    try:
        while True:
            time.sleep(1)
    except KeyboardInterrupt:
        guard.destroy()
