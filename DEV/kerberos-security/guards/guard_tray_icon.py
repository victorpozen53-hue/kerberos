#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
🐕 Guard Tray Icon — Cerbère dans la barre des tâches Windows
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
- Icône Cerbère (3 têtes) dans la barre des tâches Windows
- Couleur dynamique : Blanc (calme) → Orange (tentative) → Rouge (attaque)
- Notifications Windows natives avec détail de l'attaque
- Menu clic droit : état, historique alertes, ouvrir Kerberos
- Écoute le GuardRegistry en temps réel (guard_ui_manager.py)
- Intégration Kerberos complète : start_guard / get_stats / _GUARD_METRICS
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
Copyright (C) 2025 Victor Pozen — GPLv3
"""
# ============================================================================
#  KERBEROS ULTIMATE v4.2 — Guard Tray Icon
#  Copyright (C) 2025 Victor Pozen
# ============================================================================
#  LICENCE  : GPLv3
#  AUTEUR   : Victor Pozen
#  VERSION  : 4.2 Ultimate
#  🔗 https://github.com/victorpozen
#  💰 https://liberapay.com/EthicalKerberos/
# ============================================================================
#
#  DÉPENDANCES :
#    pip install pystray pillow plyer
#
# ============================================================================

import threading
import time
import sys
from datetime import datetime
from pathlib import Path
from typing import Optional, List, Dict

try:
    import pystray
    from pystray import MenuItem as item, Menu
except ImportError:
    pystray = None

try:
    from PIL import Image, ImageDraw, ImageFont
except ImportError:
    Image = None

try:
    from plyer import notification as plyer_notify
except ImportError:
    plyer_notify = None

# ============================================================================
# === CONSTANTES =============================================================
# ============================================================================

GUARD_NAME = "guard_tray_icon"

# Palettes couleurs par niveau d'alerte
COLORS = {
    "calm":    {"cerb": (200, 220, 255), "bg": (20,  20,  40),  "eye": (100, 180, 255), "label": "⚪ CALME"},
    "warning": {"cerb": (255, 160,  40), "bg": (40,  25,   5),  "eye": (255, 220,  80), "label": "🟠 TENTATIVE"},
    "attack":  {"cerb": (255,  50,  50), "bg": (40,   5,   5),  "eye": (255, 220,  50), "label": "🔴 ATTAQUE"},
}

# Messages contextualisés par guard source
GUARD_MESSAGES = {
    "guard_antikeylogger":    ("🔴 KEYLOGGER DÉTECTÉ",        "Frappe clavier interceptée — processus suspect bloqué"),
    "guard_netshield":        ("🔴 INTRUSION RÉSEAU",          "Connexion suspecte bloquée sur le pare-feu"),
    "guard_plasma_shield":    ("🟠 PROCESSUS SUSPECT",         "Activité anormale détectée — surveillance renforcée"),
    "guard_browser":          ("🟠 MENACE NAVIGATEUR",         "Extension ou script malveillant détecté"),
    "guard_antitoolbar":      ("🟠 TOOLBAR SUSPECTE",          "Tentative d'injection de toolbar bloquée"),
    "guard_auto_discover":    ("⚪ SCAN RÉSEAU",               "Nouveau périphérique détecté sur le réseau"),
    "guard_bubble_shield":    ("🔴 INJECTION MÉMOIRE",         "Tentative d'injection dans un processus système"),
    "guard_hdd_sentinel":     ("🟠 ACTIVITÉ DISQUE SUSPECTE",  "Accès inhabituel au disque détecté"),
    "guard_explainer":        ("⚪ ANALYSE GUARD",             "Analyse de guard déclenchée"),
}

DEFAULT_ATTACK_MSG  = ("🔴 MENACE DÉTECTÉE",    "Un guard a détecté une activité malveillante")
DEFAULT_WARNING_MSG = ("🟠 TENTATIVE DÉTECTÉE", "Activité suspecte signalée par un guard")

# ============================================================================
# === DESSIN DE L'ICÔNE CERBÈRE ==============================================
# ============================================================================

def _draw_cerberus(size: int = 64, state: str = "calm") -> "Image":
    """
    Dessine une icône Cerbère à 3 têtes en PIL.
    State : 'calm' | 'warning' | 'attack'
    """
    palette = COLORS.get(state, COLORS["calm"])
    c  = palette["cerb"]   # couleur corps/têtes
    bg = palette["bg"]     # couleur fond
    ey = palette["eye"]    # couleur yeux

    img  = Image.new("RGBA", (size, size), (0, 0, 0, 0))
    draw = ImageDraw.Draw(img)

    s = size / 64  # facteur d'échelle

    def sc(x): return int(x * s)

    # ── Fond circulaire ───────────────────────────────────────────
    draw.ellipse([0, 0, size-1, size-1], fill=(*bg, 220))

    # ── Corps central ─────────────────────────────────────────────
    draw.ellipse([sc(20), sc(36), sc(44), sc(58)], fill=(*c, 255))

    # ── Cou central ───────────────────────────────────────────────
    draw.rectangle([sc(27), sc(26), sc(37), sc(38)], fill=(*c, 255))

    # ── Cou gauche ────────────────────────────────────────────────
    draw.rectangle([sc(12), sc(28), sc(22), sc(38)], fill=(*c, 255))

    # ── Cou droit ─────────────────────────────────────────────────
    draw.rectangle([sc(42), sc(28), sc(52), sc(38)], fill=(*c, 255))

    # ── Tête centrale (plus grande) ───────────────────────────────
    draw.ellipse([sc(22), sc(12), sc(42), sc(30)], fill=(*c, 255))

    # ── Tête gauche ───────────────────────────────────────────────
    draw.ellipse([sc(6),  sc(16), sc(24), sc(32)], fill=(*c, 255))

    # ── Tête droite ───────────────────────────────────────────────
    draw.ellipse([sc(40), sc(16), sc(58), sc(32)], fill=(*c, 255))

    # ── Oreilles tête centrale ────────────────────────────────────
    draw.polygon([sc(22),sc(14), sc(18),sc(8),  sc(25),sc(14)], fill=(*c, 255))
    draw.polygon([sc(42),sc(14), sc(46),sc(8),  sc(39),sc(14)], fill=(*c, 255))

    # ── Oreilles tête gauche ──────────────────────────────────────
    draw.polygon([sc(6), sc(18), sc(3), sc(12), sc(10),sc(18)], fill=(*c, 255))
    draw.polygon([sc(22),sc(17), sc(20),sc(11), sc(25),sc(17)], fill=(*c, 255))

    # ── Oreilles tête droite ──────────────────────────────────────
    draw.polygon([sc(40),sc(17), sc(38),sc(11), sc(43),sc(17)], fill=(*c, 255))
    draw.polygon([sc(58),sc(18), sc(61),sc(12), sc(54),sc(18)], fill=(*c, 255))

    # ── Yeux tête centrale ────────────────────────────────────────
    draw.ellipse([sc(26), sc(18), sc(30), sc(22)], fill=(*ey, 255))
    draw.ellipse([sc(34), sc(18), sc(38), sc(22)], fill=(*ey, 255))
    draw.ellipse([sc(27), sc(19), sc(29), sc(21)], fill=(0, 0, 0, 255))
    draw.ellipse([sc(35), sc(19), sc(37), sc(21)], fill=(0, 0, 0, 255))

    # ── Yeux tête gauche ─────────────────────────────────────────
    draw.ellipse([sc(10), sc(21), sc(14), sc(25)], fill=(*ey, 255))
    draw.ellipse([sc(16), sc(21), sc(20), sc(25)], fill=(*ey, 255))
    draw.ellipse([sc(11), sc(22), sc(13), sc(24)], fill=(0, 0, 0, 255))
    draw.ellipse([sc(17), sc(22), sc(19), sc(24)], fill=(0, 0, 0, 255))

    # ── Yeux tête droite ─────────────────────────────────────────
    draw.ellipse([sc(44), sc(21), sc(48), sc(25)], fill=(*ey, 255))
    draw.ellipse([sc(50), sc(21), sc(54), sc(25)], fill=(*ey, 255))
    draw.ellipse([sc(45), sc(22), sc(47), sc(24)], fill=(0, 0, 0, 255))
    draw.ellipse([sc(51), sc(22), sc(53), sc(24)], fill=(0, 0, 0, 255))

    # ── Museaux ───────────────────────────────────────────────────
    muzzle_color = tuple(max(0, x - 40) for x in c)
    draw.ellipse([sc(26), sc(24), sc(38), sc(30)], fill=(*muzzle_color, 200))
    draw.ellipse([sc(9),  sc(26), sc(21), sc(32)], fill=(*muzzle_color, 200))
    draw.ellipse([sc(43), sc(26), sc(55), sc(32)], fill=(*muzzle_color, 200))

    # ── Narines ───────────────────────────────────────────────────
    nose = (20, 20, 20)
    draw.ellipse([sc(29), sc(25), sc(31), sc(27)], fill=(*nose, 255))
    draw.ellipse([sc(33), sc(25), sc(35), sc(27)], fill=(*nose, 255))
    draw.ellipse([sc(12), sc(27), sc(14), sc(29)], fill=(*nose, 255))
    draw.ellipse([sc(16), sc(27), sc(18), sc(29)], fill=(*nose, 255))
    draw.ellipse([sc(46), sc(27), sc(48), sc(29)], fill=(*nose, 255))
    draw.ellipse([sc(50), sc(27), sc(52), sc(29)], fill=(*nose, 255))

    # ── Halo de couleur (anneau externe selon état) ───────────────
    if state != "calm":
        ring_color = (255, 120, 0) if state == "warning" else (255, 30, 30)
        draw.ellipse([1, 1, size-2, size-2],
                     outline=(*ring_color, 200), width=sc(3))

    return img


def _make_icon_image(state: str = "calm") -> "Image":
    """Génère l'image icône 64x64 pour pystray"""
    return _draw_cerberus(64, state)

# ============================================================================
# === GUARD TRAY ICON ========================================================
# ============================================================================

class CerberusTrayIcon:
    """
    Guard Tray Icon — Cerbère dans la barre des tâches Windows.
    Écoute le GuardRegistry et change de couleur selon les alertes.
    """

    def __init__(self, open_kerberos_callback=None):
        self._state             = "calm"
        self._last_alert        = None
        self._alert_history: List[Dict] = []
        self._max_history       = 20
        self._icon              = None
        self._running           = False
        self._lock              = threading.Lock()
        self._open_kerberos_cb  = open_kerberos_callback
        self._reset_timer       = None

        # Métriques Kerberos
        self._GUARD_METRICS     = {"tray_icon": 0.0}

    # ── État ─────────────────────────────────────────────────────
    def set_state(self, state: str, guard_name: str = "", message: str = "", color_hint: str = ""):
        """Change l'état de l'icône et déclenche notification si besoin"""
        with self._lock:
            old_state   = self._state
            self._state = state

            alert_entry = {
                "state":      state,
                "guard":      guard_name,
                "message":    message,
                "timestamp":  datetime.now().strftime("%H:%M:%S"),
            }
            self._alert_history.append(alert_entry)
            if len(self._alert_history) > self._max_history:
                self._alert_history = self._alert_history[-self._max_history:]
            self._last_alert = alert_entry

        # Mise à jour icône
        self._update_icon()

        # Notification Windows si nouvel état plus grave
        if state == "attack" or (state == "warning" and old_state == "calm"):
            self._notify(guard_name, message, state)

        # Reset automatique vers calm après 30s (si pas de nouvelle alerte)
        self._schedule_reset(30 if state == "warning" else 60)

        # Métrique
        val = 1.0 if state == "attack" else 0.5 if state == "warning" else 0.0
        self._GUARD_METRICS["tray_icon"] = val
        _publish_metric(GUARD_NAME, val)

    def _schedule_reset(self, delay: int):
        """Remet l'icône en 'calm' après un délai si aucune nouvelle alerte"""
        if self._reset_timer:
            self._reset_timer.cancel()
        self._reset_timer = threading.Timer(delay, self._auto_reset)
        self._reset_timer.daemon = True
        self._reset_timer.start()

    def _auto_reset(self):
        with self._lock:
            self._state = "calm"
        self._update_icon()

    # ── Icône ─────────────────────────────────────────────────────
    def _update_icon(self):
        if self._icon is None:
            return
        try:
            with self._lock:
                state = self._state
            new_img   = _make_icon_image(state)
            tooltip   = self._build_tooltip()
            self._icon.icon  = new_img
            self._icon.title = tooltip
        except Exception:
            pass

    def _build_tooltip(self) -> str:
        with self._lock:
            state = self._state
            last  = self._last_alert
        label = COLORS.get(state, COLORS["calm"])["label"]
        if last and state != "calm":
            return f"Kerberos — {label}\n{last['guard']} | {last['timestamp']}\n{last['message'][:60]}"
        return f"Kerberos — {label}\nAucune menace détectée"

    # ── Notification Windows ──────────────────────────────────────
    def _notify(self, guard_name: str, message: str, state: str):
        """Affiche une notification Windows native via plyer"""

        # Titre et corps contextualisés
        key = guard_name.replace(".py", "")
        if state == "attack":
            title, body = GUARD_MESSAGES.get(key, DEFAULT_ATTACK_MSG)
        else:
            title, body = GUARD_MESSAGES.get(key, DEFAULT_WARNING_MSG)

        # Corps enrichi avec le message du guard
        if message and message not in body:
            body = f"{body}\n📋 {message}"

        body += f"\n🕐 {datetime.now().strftime('%H:%M:%S')}"
        if guard_name:
            body += f"\n🛡️ Source : {guard_name}"

        # Notification via plyer
        if plyer_notify:
            try:
                plyer_notify.notify(
                    title       = title,
                    message     = body,
                    app_name    = "Kerberos v4.2",
                    timeout     = 8,
                )
                return
            except Exception:
                pass

        # Fallback : notification via win10toast si plyer échoue
        try:
            from win10toast import ToastNotifier
            toaster = ToastNotifier()
            toaster.show_toast(title, body, duration=8, threaded=True)
        except Exception:
            pass

    # ── Menu clic droit ───────────────────────────────────────────
    def _build_menu(self):
        """Construit le menu contextuel dynamique"""

        def make_alert_items():
            with self._lock:
                history = list(reversed(self._alert_history[-5:]))
            if not history:
                return [item("Aucune alerte récente", lambda: None, enabled=False)]
            items = []
            for h in history:
                icon_s = "🔴" if h["state"] == "attack" else "🟠" if h["state"] == "warning" else "⚪"
                label  = f"{icon_s} {h['timestamp']} — {h['guard'] or 'système'}"
                items.append(item(label, lambda: None, enabled=False))
            return items

        def open_kerberos(icon, _item):
            if self._open_kerberos_cb:
                try:
                    self._open_kerberos_cb()
                except Exception:
                    pass

        def force_calm(icon, _item):
            self.set_state("calm", "manual", "Remise à zéro manuelle")

        def quit_guard(icon, _item):
            self.stop()

        with self._lock:
            state = self._state
        label_state = COLORS.get(state, COLORS["calm"])["label"]

        return Menu(
            item(f"🐕 KERBEROS — {label_state}", lambda: None, enabled=False),
            Menu.SEPARATOR,
            item("📋 Dernières alertes", Menu(*make_alert_items())),
            Menu.SEPARATOR,
            item("🖥️  Ouvrir Kerberos",    open_kerberos),
            item("⚪ Remettre à zéro",      force_calm),
            Menu.SEPARATOR,
            item("❌ Fermer le guard",      quit_guard),
        )

    # ── Démarrage / Arrêt ─────────────────────────────────────────
    def start(self):
        """Démarre l'icône tray dans un thread dédié"""
        if pystray is None or Image is None:
            print("⚠️ [Tray Icon] pystray ou PIL manquant — pip install pystray pillow")
            return

        self._running = True

        def _run():
            img = _make_icon_image("calm")
            self._icon = pystray.Icon(
                name    = "kerberos_cerberus",
                icon    = img,
                title   = "Kerberos — ⚪ CALME",
                menu    = self._build_menu(),
            )
            # Refresh du menu toutes les 5s pour mettre à jour l'historique
            threading.Thread(target=self._menu_refresh_loop, daemon=False).start()
            self._icon.run()

        t = threading.Thread(target=_run, daemon=False, name="CerberusTray")
        t.start()
        print("🐕 [Tray Icon] Cerbère démarré dans la barre des tâches")

    def _menu_refresh_loop(self):
        """Recrée le menu toutes les 5s pour afficher les nouvelles alertes"""
        while self._running and self._icon:
            time.sleep(5)
            try:
                if self._icon:
                    self._icon.menu = self._build_menu()
                    self._update_icon()
            except Exception:
                pass

    def stop(self):
        """Arrête l'icône tray"""
        self._running = False
        if self._reset_timer:
            self._reset_timer.cancel()
        if self._icon:
            try:
                self._icon.stop()
            except Exception:
                pass
        print("🐕 [Tray Icon] Cerbère arrêté")

    # ── Callback pour GuardRegistry ───────────────────────────────
    def on_alert(self, color: str, message: str):
        """
        Callback branché sur GuardRegistry.set_global_ui_alert().
        color : '#ff0000' (attaque) | '#ff9800' (warning) | autre (calm)
        """
        color_low = color.lower()
        if any(x in color_low for x in ["ff0000", "ff3333", "cc0000", "red"]):
            state = "attack"
        elif any(x in color_low for x in ["ff9800", "ff6600", "ffa500", "orange"]):
            state = "warning"
        else:
            state = "calm"
        self.set_state(state, message=message, color_hint=color)

    def on_guard_alert(self, guard_name: str, color: str, message: str):
        """Callback avec nom du guard (pour messages contextualisés)"""
        color_low = color.lower()
        if any(x in color_low for x in ["ff0000", "ff3333", "cc0000", "red"]):
            state = "attack"
        elif any(x in color_low for x in ["ff9800", "ff6600", "ffa500", "orange"]):
            state = "warning"
        else:
            state = "calm"
        self.set_state(state, guard_name=guard_name, message=message)


# ── Singleton ────────────────────────────────────────────────────────────────
_tray = CerberusTrayIcon()

# ============================================================================
# === INTÉGRATION KERBEROS ===================================================
# ============================================================================

_GUARD_METRICS = _tray._GUARD_METRICS

def start_guard(open_kerberos_callback=None):
    """Point d'entrée Kerberos — démarre le Cerbère dans la barre des tâches"""
    if open_kerberos_callback:
        _tray._open_kerberos_cb = open_kerberos_callback
    _tray.start()

    # Branchement sur GuardRegistry si disponible
    try:
        from guard_ui_manager import _registry, fire_alert as _fire_alert

        # On surcharge fire_alert pour intercepter TOUTES les alertes
        original_fire = _registry.fire_alert.__func__ if hasattr(_registry.fire_alert, '__func__') else None

        def _patched_fire(self_reg, guard_name: str, color: str, message: str):
            # Appel original
            from guard_ui_manager import GuardRegistry
            GuardRegistry.fire_alert(self_reg, guard_name, color, message)
            # Mise à jour icône Cerbère
            _tray.on_guard_alert(guard_name, color, message)

        import types
        from guard_ui_manager import GuardRegistry
        _registry.fire_alert = types.MethodType(_patched_fire, _registry)

        print("🐕 [Tray Icon] Branché sur GuardRegistry — toutes les alertes interceptées")

    except ImportError:
        print("🐕 [Tray Icon] guard_ui_manager non disponible — mode autonome")

    return _tray

def get_stats() -> dict:
    with _tray._lock:
        state   = _tray._state
        history = list(_tray._alert_history)
    attacks  = sum(1 for h in history if h["state"] == "attack")
    warnings = sum(1 for h in history if h["state"] == "warning")
    return {
        "guard_name":      GUARD_NAME,
        "current_state":   state,
        "state_label":     COLORS.get(state, COLORS["calm"])["label"],
        "total_alerts":    len(history),
        "attacks":         attacks,
        "warnings":        warnings,
        "last_alert":      _tray._last_alert,
        "pystray_ok":      pystray is not None,
        "pillow_ok":       Image is not None,
        "plyer_ok":        plyer_notify is not None,
    }

def simulate_attack(guard_name: str = "guard_netshield",
                    color: str = "#ff0000",
                    message: str = "Test attaque simulée"):
    """Simule une attaque pour tester l'icône (debug)"""
    _tray.on_guard_alert(guard_name, color, message)

def _publish_metric(guard_name: str, value: float):
    """Alias détecté par Guard Explainer — VU-mètre actif"""
    try:
        from guard_ui_manager import publish_metric
        publish_metric(guard_name, value)
    except ImportError:
        pass

def simulate_warning(guard_name: str = "guard_plasma_shield",
                     color: str = "#ff9800",
                     message: str = "Test tentative simulée"):
    """Simule une tentative pour tester l'icône (debug)"""
    _tray.on_guard_alert(guard_name, color, message)

# ============================================================================
# === RUN — TEST STANDALONE ==================================================
# ============================================================================

def run():
    print("""
╔════════════════════════════════════════════════════════════════╗
║  🐕 KERBEROS TRAY ICON — Cerbère dans la barre des tâches    ║
║                                                                ║
║  États :  ⚪ Blanc  = Calme — aucune menace                   ║
║           🟠 Orange = Tentative détectée                      ║
║           🔴 Rouge  = Attaque en cours !                      ║
║                                                                ║
║  Licence : GPLv3 — Victor Pozen                               ║
║  🔗 github.com/victorpozen                                    ║
║  💰 liberapay.com/EthicalKerberos                             ║
╚════════════════════════════════════════════════════════════════╝
    """)

    if pystray is None:
        print("❌ pystray manquant : pip install pystray")
        return
    if Image is None:
        print("❌ Pillow manquant : pip install pillow")
        return

    print("🐕 Démarrage du Cerbère...")
    start_guard()
    print("✅ Icône active dans la barre des tâches !")
    print()
    print("Commandes de test (entrée clavier) :")
    print("  a = simuler une ATTAQUE")
    print("  w = simuler une TENTATIVE")
    print("  c = remettre en CALME")
    print("  s = afficher les stats")
    print("  q = quitter")
    print()

    try:
        while True:
            cmd = input("> ").strip().lower()
            if cmd == "a":
                simulate_attack()
                print("🔴 Attaque simulée !")
            elif cmd == "w":
                simulate_warning()
                print("🟠 Tentative simulée !")
            elif cmd == "c":
                _tray.set_state("calm")
                print("⚪ Remis en calme")
            elif cmd == "s":
                import json
                print(json.dumps(get_stats(), indent=2, ensure_ascii=False, default=str))
            elif cmd == "q":
                _tray.stop()
                break
            else:
                print("? Commande inconnue (a/w/c/s/q)")
    except KeyboardInterrupt:
        _tray.stop()

if __name__ == "__main__":
    run()
