# -*- coding: utf-8 -*-
# ==============================================================
# kerberos_brain.py — v2.0 — (-;
# Cerveau symbolique central — chargement dynamique des guards.
# Sécurité éthique locale — Windows 7/10, matériel ancien, zéro cloud.
# White hat only. GPLv3.
# ==============================================================
# (-; — Victor.Pozen

import os
import sys
from pathlib import Path
import importlib.util
from datetime import datetime

# Chemin par défaut des guards
DEFAULT_GUARD_DIR = r"H:\navigator\guards"

class KerberosBrain:
    """Cerveau central — orchestre les guards sans les connaître à l’avance."""
    
    def __init__(self, guard_dir=DEFAULT_GUARD_DIR):
        self.guard_dir = Path(guard_dir)
        self.guards = {}
        self.load_all_guards()
    
    def load_all_guards(self):
        """Charge tous les modules guard_*.py du dossier."""
        self.guards.clear()
        if not self.guard_dir.exists():
            print(f"[BRAIN] ⚠️ Dossier guards absent : {self.guard_dir} — (-;")
            return
        
        for f in self.guard_dir.glob("guard_*.py"):
            name = f.stem  # ex: guard_image
            try:
                spec = importlib.util.spec_from_file_location(name, f)
                mod = importlib.util.module_from_spec(spec)
                spec.loader.exec_module(mod)
                # Vérifier interface minimale
                if hasattr(mod, 'is_suspicious') or hasattr(mod, 'scan') or hasattr(mod, 'run'):
                    self.guards[name] = mod
                    print(f"[BRAIN] ✅ {name} chargé — (-;")
                else:
                    print(f"[BRAIN] ⚠️ {name} ignoré (pas d’interface standard) — (-;")
            except Exception as e:
                print(f"[BRAIN] ❌ {name} échec : {e} — (-;")
    
    def is_suspicious(self, filepath: str) -> bool:
        """Analyse un fichier avec tous les guards capables."""
        for name, guard in self.guards.items():
            if hasattr(guard, 'is_suspicious'):
                try:
                    if guard.is_suspicious(filepath):
                        print(f"[BRAIN] 🚨 {name} : fichier suspect — {filepath} — (-;")
                        return True
                except Exception as e:
                    print(f"[BRAIN] ⚠️ {name}.is_suspicious() échoué : {e} — (-;")
        return False
    
    def scan_content(self, content: str, url: str = "") -> list:
        """Analyse du contenu (HTML, JSON, texte) pour trackers, pubs, etc."""
        alerts = []
        for name, guard in self.guards.items():
            if hasattr(guard, 'scan'):
                try:
                    result = guard.scan(content, url)
                    if result:
                        alerts.extend(result)
                except Exception as e:
                    print(f"[BRAIN] ⚠️ {name}.scan() échoué : {e} — (-;")
        return alerts
    
    def run_guard(self, guard_name: str):
        """Exécute guard.run() si présent."""
        guard = self.guards.get(guard_name)
        if guard and hasattr(guard, 'run'):
            try:
                guard.run()
                print(f"[BRAIN] 🛡️ {guard_name}.run() → OK — (-;")
                return True
            except Exception as e:
                print(f"[BRAIN] ❌ {guard_name}.run() échoué : {e} — (-;")
        return False
    
    def get_guard_status(self) -> dict:
        """Retourne un dict {nom: état} pour l’UI (✅/❌/⚠️)."""
        status = {}
        for name in self.guards:
            mod = self.guards[name]
            if hasattr(mod, 'get_status'):
                try:
                    s = mod.get_status()
                    status[name] = s
                except:
                    status[name] = "✅"
            else:
                status[name] = "✅"  # présent = actif par défaut
        # Compléter avec les guards manquants
        expected = {"guard_bubble", "guard_no_shodan", "guard_no_tracker",
                    "guard_no_pub", "guard_no_spamm", "guard_pe_arch", "guard_image"}
        for name in expected:
            if name not in status:
                status[name] = "❌"
        return status

    def log_decision(self, message: str):
        """Sauvegarde une décision dans apprentissage/derniere_decision.txt."""
        try:
            app_dir = Path("H:/navigator/apprentissage")
            app_dir.mkdir(exist_ok=True)
            log_path = app_dir / "derniere_decision.txt"
            now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            with open(log_path, "a", encoding="utf-8") as f:
                f.write(f"[{now}] {message}\n")
        except:
            pass

# === API SIMPLE POUR LES OUTILS ===
_brain_instance = None

def get_brain():
    """Singleton — retourne le même cerveau partout."""
    global _brain_instance
    if _brain_instance is None:
        _brain_instance = KerberosBrain()
    return _brain_instance

def is_suspicious(filepath: str) -> bool:
    return get_brain().is_suspicious(filepath)

def scan_content(content: str, url: str = "") -> list:
    return get_brain().scan_content(content, url)

def run_guard(name: str):
    return get_brain().run_guard(name)

def get_guard_status() -> dict:
    return get_brain().get_guard_status()

# === TEST STANDALONE ===
if __name__ == "__main__":
    brain = KerberosBrain()
    print("\n" + "="*50)
    print("KERBEROS — CERVEAU v2.0 — (-;")
    print("="*50)
    print(f"🔄 Guards chargés : {len(brain.guards)}")
    for name in sorted(brain.guards):
        print(f"  ✅ {name}")
    print("\n📊 État des guards attendus :")
    for name, state in brain.get_guard_status().items():
        print(f"  {state} {name}")
    print("\n🧠 Prêt à protéger — (-;")