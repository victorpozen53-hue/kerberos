#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
🔗 Guard UI Manager — Registre central pour intégration guards ↔ Kerberos
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
- Registre partagé _GUARD_METRICS (0.0–1.0 pour VU-mètres)
- API d'enregistrement : register_guard(name, callbacks, ui_hooks)
- Système d'alertes : fire_alert(guard_name, color, message)
- Thread-safe avec RLock
- Aucune dépendance Tkinter ici (reste dans kerberos.py)
- Callback UI globale : capturée à l'init, active pour TOUS les guards
  y compris ceux chargés après integrate_with_kerberos()

✅ CORRECTIONS APPLIQUÉES :
1. Boucle publish_metric() fixée (super().__setitem__ pour éviter récursion)
2. RuntimeError gérés dans les callbacks UI (widget détruit entre-temps)
3. Log des guards enregistrés (debugging facilité)
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
Copyright (C) 2025 Victor Pozen — GPLv3
"""
import threading
import sys
from typing import Dict, Callable, Optional, List
from datetime import datetime
from pathlib import Path

# ============================================================================
# === REGISTRE PARTAGÉ — THREAD-SAFE =========================================
# ============================================================================

class GuardRegistry:
    """Registre central pour les guards — thread-safe"""

    def __init__(self):
        self._lock          = threading.RLock()
        self._metrics:      Dict[str, float]    = {}
        self._callbacks:    Dict[str, Dict]     = {}
        self._ui_hooks:     Dict[str, Callable] = {}
        self._alerts_log:   List[Dict]          = []
        self._max_alerts    = 100
        self._global_ui_alert: Optional[Callable[[str, str], None]] = None
        self._global_stats_refresh: Optional[Callable] = None

    # ── Enregistrement ────────────────────────────────────────────────────
    def register_guard(self,
                       name:      str,
                       on_alert:  Optional[Callable[[str, str], None]] = None,
                       on_stats:  Optional[Callable[[], Dict]]         = None,
                       ui_hook:   Optional[Callable]                   = None):
        """Enregistre un guard avec ses callbacks optionnelles"""
        with self._lock:
            self._callbacks[name] = {
                "on_alert":       on_alert,
                "on_stats":       on_stats,
                "registered_at":  datetime.now().isoformat(),
            }
            if ui_hook:
                self._ui_hooks[name] = ui_hook
            self._metrics.setdefault(name, 0.0)
        
        # ✅ CORRECTION 3 : Log des guards enregistrés (debugging)
        print(f"🔗 [UI Manager] Guard enregistré : {name}")

    # ── Métriques VU-mètres ───────────────────────────────────────────────
    def publish_metric(self, guard_name: str, value: float):
        """Publie une métrique d'activité (0.0–1.0) pour les VU-mètres"""
        with self._lock:
            self._metrics[guard_name] = max(0.0, min(1.0, value))

    def get_metric(self, guard_name: str) -> float:
        with self._lock:
            return self._metrics.get(guard_name, 0.0)

    def get_all_metrics(self) -> Dict[str, float]:
        with self._lock:
            return dict(self._metrics)

    # ── Alertes ───────────────────────────────────────────────────────────
    def fire_alert(self, guard_name: str, color: str, message: str):
        """Déclenche une alerte : log + callback UI + callback spécifique"""
        alert = {
            "guard":     guard_name,
            "color":     color,
            "message":   message,
            "timestamp": datetime.now().isoformat(),
        }
        with self._lock:
            self._alerts_log.append(alert)
            if len(self._alerts_log) > self._max_alerts:
                self._alerts_log = self._alerts_log[-self._max_alerts:]
            # Snapshot des callbacks pour appel hors verrou (évite deadlock)
            global_cb  = self._global_ui_alert
            specific_cb = self._callbacks.get(guard_name, {}).get("on_alert")

        # Appels hors du verrou pour éviter deadlock
        if global_cb:
            try:
                global_cb(color, message)
            # ✅ CORRECTION 2 : RuntimeError gérés (widget détruit entre-temps)
            except RuntimeError:
                pass  # Widget Tkinter détruit pendant l'appel
            except Exception:
                pass
        if specific_cb:
            try:
                specific_cb(color, message)
            except RuntimeError:
                pass
            except Exception:
                pass

    def get_alerts(self, limit: int = 10) -> List[Dict]:
        with self._lock:
            return list(self._alerts_log[-limit:])

    # ── Stats ─────────────────────────────────────────────────────────────
    def get_guard_stats(self, guard_name: str) -> Optional[Dict]:
        """Appelle le callback on_stats du guard si disponible"""
        with self._lock:
            cb = self._callbacks.get(guard_name, {}).get("on_stats")
        if cb:
            try:
                return cb()
            except Exception:
                pass
        return None

    def get_all_guard_stats(self) -> Dict[str, Optional[Dict]]:
        """Retourne les stats de tous les guards enregistrés"""
        with self._lock:
            names = list(self._callbacks.keys())
        return {name: self.get_guard_stats(name) for name in names}

    # ── Hooks UI ──────────────────────────────────────────────────────────
    def get_ui_hooks(self) -> Dict[str, Callable]:
        with self._lock:
            return dict(self._ui_hooks)

    def list_guards(self) -> List[str]:
        """Liste les guards enregistrés"""
        with self._lock:
            return list(self._callbacks.keys())

    # ── Intégration Kerberos ──────────────────────────────────────────────
    def set_global_ui_alert(self, fn: Callable[[str, str], None]):
        """Définit la callback UI globale"""
        with self._lock:
            self._global_ui_alert = fn

    def set_global_stats_refresh(self, fn: Callable):
        """Définit la callback de rafraîchissement des stats UI"""
        with self._lock:
            self._global_stats_refresh = fn

    def trigger_stats_refresh(self):
        """Déclenche le rafraîchissement de l'onglet Guards dans Kerberos"""
        with self._lock:
            fn = self._global_stats_refresh
        if fn:
            try:
                fn()
            except RuntimeError:
                pass
            except Exception:
                pass


# ── Singleton ────────────────────────────────────────────────────────────────
_registry = GuardRegistry()

# ============================================================================
# === _GUARD_METRICS UNIFIÉ ==================================================
# ============================================================================

class _MetricsProxy(dict):
    """
    Dict spécialisé : toute écriture publie aussi dans le registry.
    Compatible avec le code existant (get/set/in).
    
    ✅ CORRECTION 1 : Utilise super().__setitem__ pour éviter la boucle infinie
    """
    def __setitem__(self, key: str, value):
        # Écrit directement dans le dict SANS déclencher __setitem__ récursif
        super(_MetricsProxy, self).__setitem__(key, value)
        # Puis publie dans le registry (une seule fois)
        _registry.publish_metric(key, float(value))

GUARD_METRICS = _MetricsProxy()

# ============================================================================
# === API PUBLIQUE ============================================================
# ============================================================================

def register_guard(name:     str,
                   on_alert: Optional[Callable[[str, str], None]] = None,
                   on_stats: Optional[Callable[[], Dict]]         = None,
                   ui_hook:  Optional[Callable]                   = None):
    """Enregistre un guard avec ses callbacks"""
    _registry.register_guard(name, on_alert, on_stats, ui_hook)

def publish_metric(guard_name: str, value: float):
    """Publie une métrique d'activité (0.0–1.0) pour les VU-mètres"""
    _registry.publish_metric(guard_name, value)
    # ✅ CORRECTION 1 : Utilise super() pour éviter la boucle
    super(_MetricsProxy, GUARD_METRICS).__setitem__(guard_name, float(value))

def get_metric(guard_name: str) -> float:
    return _registry.get_metric(guard_name)

def get_all_metrics() -> Dict[str, float]:
    return _registry.get_all_metrics()

def fire_alert(guard_name: str, color: str, message: str):
    _registry.fire_alert(guard_name, color, message)

def get_alerts(limit: int = 10) -> List[Dict]:
    return _registry.get_alerts(limit)

def get_guard_stats(guard_name: str) -> Optional[Dict]:
    return _registry.get_guard_stats(guard_name)

def get_all_guard_stats() -> Dict[str, Optional[Dict]]:
    return _registry.get_all_guard_stats()

def get_ui_hooks() -> Dict[str, Callable]:
    return _registry.get_ui_hooks()

def list_guards() -> List[str]:
    return _registry.list_guards()

# ============================================================================
# === INTÉGRATION KERBEROS ===================================================
# ============================================================================

def integrate_with_kerberos(app_instance, root_widget):
    """
    Connecte le registry à l'instance Kerberos.
    À appeler UNE FOIS dans KerberosApp.__init__(), après _setup_ui().
    """

    def _ui_alert(color: str, message: str):
        """Flash + log dans le chat Kerberos"""
        try:
            # ✅ CORRECTION 2 : Vérifie winfo_exists() avant toute opération
            if not root_widget.winfo_exists():
                return
            original = root_widget.cget('bg')
            root_widget.configure(bg=color)
            
            def restore():
                try:
                    if root_widget.winfo_exists():
                        root_widget.configure(bg=original)
                except RuntimeError:
                    pass  # Widget détruit entre-temps
            
            root_widget.after(300, restore)
            
            # Log dans le chat
            if hasattr(app_instance, 'append_to_chat'):
                app_instance.append_to_chat(f"🚨 [Alerte] {message}\n")
            
            # Flash heartbeat label si disponible
            if hasattr(app_instance, 'heartbeat_label'):
                try:
                    if root_widget.winfo_exists():
                        app_instance.heartbeat_label.config(bg=color)
                        root_widget.after(
                            500,
                            lambda: app_instance.heartbeat_label.config(bg='#16213e')
                            if root_widget.winfo_exists() else None
                        )
                except RuntimeError:
                    pass
        # ✅ CORRECTION 2 : RuntimeError capturés (widget en destruction)
        except RuntimeError:
            pass
        except Exception:
            pass

    def _stats_refresh():
        """Rafraîchit l'onglet Guards si la fenêtre gestion est ouverte"""
        try:
            if hasattr(app_instance, '_refresh_guards_vu'):
                app_instance._refresh_guards_vu()
        except RuntimeError:
            pass
        except Exception:
            pass

    # Injection globale — couvre tous les guards présents ET futurs
    _registry.set_global_ui_alert(_ui_alert)
    _registry.set_global_stats_refresh(_stats_refresh)

    # Connecte aussi set_alert_callback() de Plasma Shield si déjà chargé
    _connect_plasma_shield()

    print("🔗 [UI Manager] Intégré à Kerberos — callback globale active")


def _connect_plasma_shield():
    """
    Si guard_plasma_shield est déjà chargé, branche sa set_alert_callback
    sur fire_alert() du registry pour unifier les deux systèmes.
    """
    plasma = sys.modules.get("guard_plasma_shield")
    if plasma and hasattr(plasma, 'set_alert_callback'):
        plasma.set_alert_callback(
            lambda color: fire_alert("guard_plasma_shield.py", color,
                                     "Processus suspect détecté"))
        print("🔗 [UI Manager] Plasma Shield connecté au registry")


# ============================================================================
# === AUTO-CONNEXION AU CHARGEMENT ===========================================
# ============================================================================

def sync_main_metrics():
    """
    Remplace _GUARD_METRICS de __main__ par le proxy si présent.
    Appeler dans kerberos.py juste après l'import de ce module.
    """
    main = sys.modules.get("__main__")
    if main and hasattr(main, "_GUARD_METRICS"):
        existing = getattr(main, "_GUARD_METRICS")
        if not isinstance(existing, _MetricsProxy):
            GUARD_METRICS.update(existing)
            setattr(main, "_GUARD_METRICS", GUARD_METRICS)
            print("🔗 [UI Manager] _GUARD_METRICS synchronisé avec le registry")