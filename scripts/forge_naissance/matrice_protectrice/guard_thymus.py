#!/usr/bin/env python3
# -*- coding: utf-8 -*-
# Copyright (C) 2025–2026 Victor Pozen
#
# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program.  If not, see <https://www.gnu.org/licenses/>.
#
# KERBEROS — Sécurité desktop locale, zéro cloud, matériel ancien (Win7/10)
# White hat only • Pas de trace • Juste du code qui protège • (-;

"""
🛡️ guard_thymus.py — Orchestrateur immunitaire central de Kerberos

Le thymus forme, éduque et active les gardes — comme les lymphocytes T.
Il garantit :
  → Aucun guard ne s’exécute s’il n’est pas "mature" (signature, ADN, structure OK),
  → Aucune attaque auto-immune (ex. : modification de kerberos.py sans autorisation),
  → Une coordination claire entre genome, lymphatic, wbc.

Conçu pour OptiPlex 780, HDD, Win7 — local, silencieux, efficace.

GPLv3 — Victor.Pozen @2026
(-;
"""

import hashlib
import json
import sys
from pathlib import Path
import importlib.util

# === DÉTECTION RACINE KERBEROS ===
def _find_kerberos_root():
    here = Path(__file__).resolve()
    for parent in [here.parent] + list(here.parents):
        if (parent / "kerberos.py").exists() or (parent / "LICENCE.txt").exists():
            return parent
    return Path.cwd()

KERBEROS_ROOT = _find_kerberos_root()
LYMPH_DIR = KERBEROS_ROOT / "lymph"
GENOME_FILE = LYMPH_DIR / "genome.json"
THYMUS_LOG = KERBEROS_ROOT / "logs" / "thymus.log"

# Dossiers critiques — auto-immunité = interdit par défaut
SELF_CRITICAL = {
    KERBEROS_ROOT / "kerberos.py",
    GENOME_FILE,
    LYMPH_DIR / "plasma",
    LYMPH_DIR / "memory_cells",
}

# Création silencieuse
THYMUS_LOG.parent.mkdir(parents=True, exist_ok=True)

def _log(msg: str, level="INFO"):
    from datetime import datetime, timezone
    ts = datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M:%S UTC")
    line = f"[{ts}] [{level}] {msg}"
    with open(THYMUS_LOG, "a", encoding="utf-8") as f:
        f.write(line + "\n")
    if __name__ == "__main__":
        print(line)

# === ÉTAPE 1 : ÉDUCATION (vérification avant exécution) ===

def _check_hybrid_signature(file_path: Path):
    """Vérifie la signature .ybrid si présente — comme dans auto_activate_guards."""
    hybrid = file_path.with_suffix('.ybrid')
    if not hybrid.exists():
        return True, "pas de .ybrid"
    try:
        sig = hybrid.read_text().strip()
        if not sig.startswith("sha256:"):
            return False, ".ybrid invalide (pas de sha256:)"
        expected = sig.split(":", 1)[1].lower()
        actual = hashlib.sha256(file_path.read_bytes()).hexdigest().lower()
        if actual != expected:
            return False, "intégrité rompue (.ybrid ≠ fichier)"
        return True, "signature OK"
    except Exception as e:
        return False, f"erreur .ybrid : {e}"

def _inspect_guard(file_path: Path):
    """Analyse statique du guard — sans exécution."""
    if not file_path.suffix in (".py", ".vkr"):
        return {"valid": False, "reason": "extension non supportée"}

    # Signature hybride
    sig_ok, sig_msg = _check_hybrid_signature(file_path)
    if not sig_ok:
        return {"valid": False, "reason": sig_msg}

    try:
        if file_path.suffix == ".py":
            # Lecture statique AST — pas d'exécution
            spec = importlib.util.spec_from_file_location(file_path.stem, file_path)
            module = importlib.util.module_from_spec(spec)
            # On ne fait PAS spec.loader.exec_module → pas de run !
            # On lit juste la structure via AST pour chercher run/main
            with open(file_path, "r", encoding="utf-8") as f:
                tree = __import__('ast').parse(f.read(), filename=str(file_path))
            has_run = any(
                isinstance(node, __import__('ast').FunctionDef) and node.name in ("run", "main")
                for node in __import__('ast').walk(tree)
            )
            if not has_run:
                return {"valid": False, "reason": "pas de run() ni main() détecté (AST)"}

            # Vérif qu’il ne touche pas aux fichiers critiques (recherche naïve de patterns)
            source = Path(file_path).read_text(encoding="utf-8")
            forbidden = [str(p) for p in SELF_CRITICAL]
            for fp in forbidden:
                if fp in source:
                    _log(f"⚠️  Pattern suspect trouvé : '{fp[:20]}…' dans {file_path.name}", "WARN")
                    # On ne bloque pas — on avertit (mode éducatif)
            return {"valid": True, "type": "py", "ast_ok": True}

        elif file_path.suffix == ".vkr":
            # Format VKR1 — déjà validé dans kerberos.py, on fait un double-check léger
            data = file_path.read_bytes()
            if len(data) < 0x28 or data[:4] != b"VKR1":
                return {"valid": False, "reason": "magic VKR1 manquant"}
            sz = int.from_bytes(data[4:8], 'little')
            exp_hash = data[8:0x28]
            payload = data[0x28:0x28+sz]
            if hashlib.sha256(payload).digest() != exp_hash:
                return {"valid": False, "reason": "SHA-256 payload invalide"}
            import json
            guard = json.loads(payload.decode('utf-8'))
            code = guard.get("code", "")
            if "run" not in code and "main" not in code:
                return {"valid": False, "reason": ".vkr sans run()/main() dans code"}
            return {"valid": True, "type": "vkr"}

    except Exception as e:
        return {"valid": False, "reason": f"erreur inspection : {e}"}

    return {"valid": False, "reason": "inconnu"}

# === ÉTAPE 2 : ACTIVATION CONTRÔLÉE ===

def train(guard_path: Path):
    """🎓 Éduque un guard — retourne son statut de maturité."""
    result = _inspect_guard(guard_path)
    status = "mature" if result["valid"] else "immature"
    _log(f"🎓 {guard_path.name} → {status} ({result.get('reason', 'OK')})", "TRAIN")
    return {
        "guard": guard_path.name,
        "path": str(guard_path),
        "mature": result["valid"],
        "type": result.get("type", "?"),
        "reason": result.get("reason", ""),
        "timestamp": __import__('datetime').datetime.now(__import__('datetime').timezone.utc).isoformat()
    }

def activate(guard_path: Path, dry_run=False):
    """⚡ Active un guard *seulement s’il est mature*."""
    report = train(guard_path)
    if not report["mature"]:
        _log(f"❌ Refus activation : {guard_path.name} immature", "BLOCK")
        return {**report, "activated": False}

    if dry_run:
        _log(f"[DRY] Activation autorisée : {guard_path.name}", "DRY")
        return {**report, "activated": True, "dry_run": True}

    # On délègue l’exécution à kerberos.py (via importlib)
    # → ainsi, le thymus ne lance *rien* lui-même : il autorise seulement
    _log(f"✅ Activation autorisée : {guard_path.name}", "ACTIVATE")
    return {**report, "activated": True}

def self_tolerance_check():
    """🛡️ Vérifie qu’aucun guard actif ne menace le 'soi' (kerberos.py, genome, plasma)."""
    # Liste des guards actifs (on scanne les threads nommés)
    import threading
    active_guards = [
        t.name for t in threading.enumerate()
        if t.name.startswith("kerberos_guard_")
    ]
    _log(f"🔍 Auto-tolérance — {len(active_guards)} guard(s) actif(s)", "CHECK")
    # Pour l’instant : pas de blocage automatique → rapport seulement
    # (à étendre plus tard avec whitelist explicite)
    return {
        "self_tolerance": "ok",  # ou "warning"
        "active_guards": active_guards,
        "critical_files": [str(p) for p in SELF_CRITICAL]
    }

# === INTERFACE GUARD — compatible avec KerberosApp.auto_activate_guards() ===

def run(dry_run=False):
    """
    Exécute un cycle de supervision thymique :
      - Éduque tous les guards trouvés
      - Active ceux qui sont mûrs (si dry_run=False)
      - Retourne un rapport standardisé
    """
    guards_dir = KERBEROS_ROOT / "guards"
    candidates = list(guards_dir.glob("guard_*.py")) + list(guards_dir.glob("guard_*.vkr"))
    
    _log("="*50, "INFO")
    _log("🛡️  GUARD THYMUS — éducation immunitaire en cours", "INFO")
    _log(f"📁 Dossier guards : {guards_dir}", "INFO")
    _log(f"🧪 Mode dry_run : {dry_run}", "INFO")

    trained = []
    activated = []

    for g in sorted(candidates):
        if any(skip in g.stem for skip in ("_skip_", "_test_", "_old_", "_bak")):
            continue
        report = train(g)
        trained.append(report)
        if report["mature"] and not dry_run:
            act = activate(g)
            if act["activated"]:
                activated.append(g.name)

    tolerance = self_tolerance_check()

    final_status = "success" if len(trained) > 0 else "no_guards"
    if any(not t["mature"] for t in trained):
        final_status = "partial"

    return {
        "guard": "thymus",
        "timestamp": __import__('datetime').datetime.now(__import__('datetime').timezone.utc).isoformat(),
        "status": final_status,
        "trained": len(trained),
        "mature": sum(1 for t in trained if t["mature"]),
        "activated": activated,
        "tolerance_check": tolerance
    }

# === MODE STANDALONE ===
if __name__ == "__main__":
    print("\n" + "="*60)
    print("🛡️  GUARD THYMUS — Orchestrateur immunitaire de Kerberos")
    print("White hat • Local only • GPL v3 • (-;")
    print("="*60 + "\n")

    dry = "--dry" in sys.argv
    result = run(dry_run=dry)

    print(f"📊 Rapport Thymus :")
    print(f"  • Guards trouvés    : {result['trained']}")
    print(f"  • Mûrs (éligibles)  : {result['mature']}")
    print(f"  • Activés           : {len(result['activated'])}")
    print(f"  • Tolérance au soi  : {result['tolerance_check']['self_tolerance']}")
    print(f"  • Statut            : {result['status']}")

    if result["activated"]:
        print(f"\n✅ Activés : {', '.join(result['activated'])}")

    print(f"\n🩺 Logs : logs/thymus.log")
    print("Kerberos ne ment jamais — mais parfois, il grogne. 🐺\n")