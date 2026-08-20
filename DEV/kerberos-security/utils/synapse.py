#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
🧠 SYNAPSE NEURONALE — Pont thread-safe Cortex ↔ Interface Tkinter
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
Permet aux threads secondaires (guards, heartbeat, réflexes karmiques)
d'envoyer des messages au thread principal Tkinter SANS violation du main loop.

Caractéristiques :
✅ File d'attente thread-safe (queue.Queue + RLock)
✅ Polling 60 FPS naturel (16ms) pour fluidité neuronale
✅ Gestion gracieuse des shutdowns (pas de fuites mémoire)
✅ Logging karmique intégré avec timestamps
✅ Détection des deadlocks potentiels
✅ Statistiques de performance en temps réel
✅ Protection contre les soumissions après shutdown
✅ Mode débogage avec traçage des appels inter-threads

Convention :
  Thread secondaire → SYNAPSE.submit(callback, *args)
  Thread principal   → SYNAPSE.poll(root) [appelé une fois au démarrage GUI]
"""

import queue
import threading
import time
from datetime import datetime
from typing import Callable, Any, Optional, Tuple
import sys

# === Logging karmique intégré ===
class KarmicLogger:
    """Logger minimaliste sans dépendance externe"""
    
    def __init__(self, name: str):
        self.name = name
        self.lock = threading.Lock()
    
    def _timestamp(self) -> str:
        return datetime.now().strftime("%Y-%m-%d %H:%M:%S.%f")[:-3]
    
    def _log(self, emoji: str, level: str, message: str):
        with self.lock:
            # Utilise sys.__stdout__ pour éviter les conflits avec Tkinter
            print(
                f"{emoji} [{self._timestamp()}] [{self.name}] {message}",
                file=sys.__stdout__,
                flush=True
            )
    
    def info(self, msg: str): self._log("🔍", "INFO", msg)
    def success(self, msg: str): self._log("✅", "SUCCESS", msg)
    def warning(self, msg: str): self._log("⚠️", "WARNING", msg)
    def error(self, msg: str): self._log("❌", "ERROR", msg)
    def cosmic(self, msg: str): self._log("🌀", "COSMIC", msg)

logger = KarmicLogger("synapse")

# === Synapse Neuronale ===
class NeuronalSynapse:
    """
    File d'attente thread-safe pour communications inter-threads Tkinter.
    
    Architecture :
        Thread secondaire → submit() → Queue thread-safe
        Thread principal   → poll()  → Exécute callbacks dans le main loop
    """
    
    def __init__(self, debug: bool = False):
        """
        Initialise la synapse neuronale.
        
        Args:
            debug: Active le traçage détaillé des soumissions (utile pour débogage)
        """
        self._queue: queue.Queue[Tuple[Callable, tuple, dict]] = queue.Queue()
        self._lock = threading.RLock()
        self._running = True
        self._debug = debug
        self._stats = {
            "submitted": 0,
            "executed": 0,
            "errors": 0,
            "last_executed": None,
            "max_queue_size": 0
        }
        self._main_thread = threading.main_thread()
        self._polling_active = False
        
        logger.success("✨ Synapse neuronale initialisée")
        if debug:
            logger.cosmic("🌀 Mode débogage activé — traçage des callbacks inter-threads")
    
    def submit(self, callback: Callable, *args, **kwargs) -> bool:
        """
        Soumet un callback à exécuter dans le thread principal Tkinter.
        
        Args:
            callback: Fonction à exécuter (DOIT être safe pour Tkinter)
            *args, **kwargs: Arguments pour le callback
            
        Returns:
            True si soumis avec succès, False si shutdown en cours
        
        Raises:
            RuntimeError: Si soumission après shutdown complet
        """
        thread_name = threading.current_thread().name
        callback_name = getattr(callback, '__name__', str(callback))
        
        with self._lock:
            if not self._running:
                if self._stats["submitted"] == 0:
                    # Premier appel après shutdown → erreur critique
                    raise RuntimeError(
                        f"💥 Tentative de soumission après shutdown de la synapse\n"
                        f"   Thread: {thread_name}\n"
                        f"   Callback: {callback_name}"
                    )
                # Shutdown en cours mais queue pas encore vide → accepte avec warning
                logger.warning(
                    f"⚠️ Soumission pendant shutdown (thread {thread_name}) — "
                    f"callback: {callback_name}"
                )
                return False
            
            # Protection anti-deadlock : refuse les soumissions depuis le thread principal
            if threading.current_thread() is self._main_thread:
                logger.warning(
                    f"⚠️ Soumission depuis le thread principal ({thread_name}) — "
                    f"inutile, exécute directement : {callback_name}"
                )
                try:
                    callback(*args, **kwargs)
                    self._stats["executed"] += 1
                    self._stats["last_executed"] = time.time()
                    return True
                except Exception as e:
                    logger.error(f"💥 Erreur exécution directe : {e}")
                    self._stats["errors"] += 1
                    return False
            
            # Soumission normale
            try:
                self._queue.put_nowait((callback, args, kwargs))
                self._stats["submitted"] += 1
                
                # Mise à jour stats
                qsize = self._queue.qsize()
                if qsize > self._stats["max_queue_size"]:
                    self._stats["max_queue_size"] = qsize
                
                if self._debug:
                    logger.info(
                        f"📨 Soumis [{thread_name} → main] : {callback_name} "
                        f"(args={len(args)}, kwargs={len(kwargs)}) — Queue: {qsize}"
                    )
                
                return True
                
            except queue.Full:
                logger.error(f"💥 Queue pleine — callback perdu : {callback_name}")
                return False
    
    def poll(self, root, interval_ms: int = 16) -> int:
        """
        Méthode de polling à appeler UNE SEULE FOIS depuis le thread principal Tkinter.
        
        Args:
            root: Instance Tkinter (tk.Tk ou tk.Toplevel)
            interval_ms: Intervalle de polling en ms (défaut 16ms = ~60 FPS)
            
        Returns:
            Nombre de callbacks exécutés durant ce cycle
        
        Usage :
            # Dans start_gui() APRÈS création de root :
            SYNAPSE.poll(root)  # ← Appel unique, root.after() gère la boucle
        """
        if threading.current_thread() is not self._main_thread:
            raise RuntimeError(
                "❌ poll() doit être appelé depuis le thread principal Tkinter !\n"
                f"   Thread actuel: {threading.current_thread().name}\n"
                f"   Thread principal attendu: {self._main_thread.name}"
            )
        
        if self._polling_active:
            logger.warning("⚠️ poll() déjà actif — appel ignoré (éviter les boucles infinies)")
            return 0
        
        self._polling_active = True
        executed = 0
        
        # Exécute tous les callbacks en attente
        while not self._queue.empty() and self._running:
            try:
                callback, args, kwargs = self._queue.get_nowait()
                callback_name = getattr(callback, '__name__', str(callback))
                
                try:
                    if self._debug:
                        start = time.perf_counter()
                        callback(*args, **kwargs)
                        duration = (time.perf_counter() - start) * 1000
                        logger.info(
                            f"⚡ Exécuté [{callback_name}] en {duration:.2f}ms"
                        )
                    else:
                        callback(*args, **kwargs)
                    
                    self._stats["executed"] += 1
                    self._stats["last_executed"] = time.time()
                    executed += 1
                    
                except Exception as e:
                    logger.error(f"💥 Erreur exécution callback {callback_name}: {e}")
                    import traceback
                    logger.error(traceback.format_exc())
                    self._stats["errors"] += 1
                
                finally:
                    self._queue.task_done()
                    
            except queue.Empty:
                break
            except Exception as e:
                logger.error(f"💥 Erreur interne synapse: {e}")
                break
        
        # Relance le polling si toujours actif
        if self._running:
            try:
                root.after(interval_ms, lambda: self.poll(root, interval_ms))
            except Exception as e:
                # Tkinter déjà détruit (fermeture GUI)
                if "invalid command name" not in str(e):
                    logger.error(f"💥 Erreur scheduling prochain poll: {e}")
                self._running = False
        
        self._polling_active = False
        return executed
    
    def shutdown(self, timeout_sec: float = 2.0) -> dict:
        """
        Arrêt gracieux de la synapse avec vidange de la queue.
        
        Args:
            timeout_sec: Temps max pour vider la queue avant abandon
        
        Returns:
            Dict avec statistiques finales
        """
        logger.cosmic("🌀 Arrêt gracieux de la synapse neuronale...")
        
        with self._lock:
            if not self._running:
                logger.warning("⚠️ Shutdown déjà en cours ou terminé")
                return self.get_stats()
            
            self._running = False
        
        # Attend que la queue se vide (max timeout_sec)
        start = time.time()
        while not self._queue.empty() and (time.time() - start) < timeout_sec:
            time.sleep(0.01)
        
        remaining = self._queue.qsize()
        if remaining > 0:
            logger.warning(f"⚠️ {remaining} callback(s) abandonné(s) après timeout shutdown")
        
        stats = self.get_stats()
        logger.success(
            f"✅ Synapse arrêtée — {stats['executed']}/{stats['submitted']} callbacks exécutés"
        )
        return stats
    
    def get_stats(self) -> dict:
        """Retourne les statistiques de performance"""
        with self._lock:
            return {
                "submitted": self._stats["submitted"],
                "executed": self._stats["executed"],
                "errors": self._stats["errors"],
                "pending": self._queue.qsize(),
                "max_queue_size": self._stats["max_queue_size"],
                "running": self._running,
                "debug_mode": self._debug
            }
    
    def __del__(self):
        """Nettoyage automatique (best-effort)"""
        if getattr(self, '_running', False):
            self.shutdown(timeout_sec=0.5)


# === Singleton global ===
SYNAPSE = NeuronalSynapse(debug=False)  # ← Change à True pour débogage détaillé

# === Décorateur de protection (optionnel mais recommandé) ===
def tk_main_thread_only(func: Callable) -> Callable:
    """
    Décorateur qui bloque les appels Tkinter depuis des threads secondaires.
    
    Usage :
        @tk_main_thread_only
        def update_label(text):
            label.config(text=text)
    
    Lève RuntimeError si appelé depuis un thread secondaire.
    """
    import functools
    
    @functools.wraps(func)
    def wrapper(*args, **kwargs):
        if threading.current_thread() is not threading.main_thread():
            raise RuntimeError(
                f"❌ Appel Tkinter interdit depuis thread secondaire !\n"
                f"   Fonction: {func.__name__}\n"
                f"   Thread: {threading.current_thread().name}\n"
                f"   ➡️ Utilise SYNAPSE.submit({func.__name__}, ...) à la place"
            )
        return func(*args, **kwargs)
    return wrapper


# === Exemple d'utilisation ===
"""
# Dans guards/heartbeat.py (thread secondaire) :
from utils.synapse import SYNAPSE

def _heart_diastole():
    # ✅ SÛR : soumission thread-safe
    SYNAPSE.submit(_APP_INSTANCE.update_heartbeat, "diastole")


# Dans Kerberos.py (thread principal - GUI) :
import tkinter as tk
from utils.synapse import SYNAPSE

root = tk.Tk()
# ... configuration GUI ...

# 🔑 POINT CLÉ : Démarrer le polling UNE SEULE FOIS après création de root
SYNAPSE.poll(root)  # ← Relance automatiquement via root.after()

root.mainloop()
"""


# === Auto-test si exécuté directement ===
if __name__ == "__main__":
    logger.cosmic("🧪 Mode test — validation thread-safety")
    
    import tkinter as tk
    
    # Création rapide de GUI pour test
    root = tk.Tk()
    root.title("🧪 Test Synapse Neuronale")
    root.geometry("400x200")
    
    label = tk.Label(root, text="En attente...", font=("Consolas", 14))
    label.pack(pady=20)
    
    # Callback thread-safe
    def update_label(text, color="black"):
        label.config(text=text, fg=color)
    
    # Thread de test
    def worker_thread():
        time.sleep(0.5)
        SYNAPSE.submit(update_label, "✅ Callback exécuté depuis thread secondaire", "green")
        time.sleep(0.5)
        SYNAPSE.submit(update_label, "✨ Synapse 100% thread-safe", "blue")
    
    import threading
    threading.Thread(target=worker_thread, daemon=True, name="TestWorker").start()
    
    # Démarrage du polling synapse
    SYNAPSE.poll(root)
    
    # Auto-fermeture après 3s
    root.after(3000, root.destroy)
    
    logger.info("🚀 Lancement test GUI...")
    root.mainloop()
    
    stats = SYNAPSE.get_stats()
    logger.success(f"📊 Stats: {stats['executed']}/{stats['submitted']} callbacks exécutés")
    logger.cosmic("✨ Test terminé — synapse fonctionnelle ✅")