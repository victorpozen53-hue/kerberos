#!/usr/bin/env python3
# -*- coding: utf-8 -*-
# organic_yara.py — Système immunitaire adaptatif de Kerberos
# GPLv3 — Victor.Pozen @2026
# (-; White hat • Local only • No cloud

"""
🧬 organic_yara.py

Ce module transforme YARA en un organe vivant :
- Les règles sont des gènes stockés dans lymph/memory_cells/
- Elles naissent après exposition à une menace
- Elles mutent pour échapper à la détection
- Elles dorment si inutiles, s’activent si nécessaire

Pas de règles statiques. Pas de signatures fixes.
Juste de la mémoire immunitaire numérique.

Kerberos ne scanne pas — il se souvient.
"""

import yara
import json
import hashlib
from pathlib import Path
from datetime import datetime, timezone

# === RACINE KERBEROS ===
KERBEROS_ROOT = Path(__file__).resolve().parent.parent
_MEMORY_CELLS = KERBEROS_ROOT / "lymph" / "memory_cells"
_MEMORY_CELLS.mkdir(parents=True, exist_ok=True)

# === ÉTAT INTERNE ===
_compiled_immune_system = None
_last_compilation = 0
_gene_count = 0

def _log(msg: str):
    print(f"[🧬 YARA ORGANIQUE] {msg}")

def _dna_of_gene(content: str) -> str:
    """Calcule l'ADN unique d'un gène (règle YARA)."""
    return hashlib.sha256(content.encode("utf-8")).hexdigest()[:12]

def create_memory_gene(
    threat_name: str,
    pattern: str,
    context: str = "comportement anormal",
    k_score: int = 80,
    auto_mutate: bool = True
) -> bool:
    """
    🩸 Crée un nouveau gène de mémoire après exposition à une menace.
    Simule la production d'un anticorps spécifique.
    """
    if not _MEMORY_CELLS.exists():
        _MEMORY_CELLS.mkdir(parents=True)

    # Mutation légère pour éviter la détection par les attaquants
    if auto_mutate:
        # Ex: échapper les espaces, ajouter des variantes
        mutated_pattern = pattern.replace(" ", "[\\s]*")
    else:
        mutated_pattern = pattern

    gene_content = f"""rule KRB_{threat_name.upper()} {{
    meta:
        k_score = {k_score}
        first_seen = "{datetime.now(timezone.utc).isoformat()}"
        context = "{context}"
        creator = "Kerberos Genèse"
        mutation_level = {"1" if auto_mutate else "0"}
    strings:
        $pattern = "{mutated_pattern}" fullword wide
    condition:
        $pattern
}}"""

    gene_path = _MEMORY_CELLS / f"{threat_name}.gene"
    gene_path.write_text(gene_content, encoding="utf-8")

    _log(f"Nouveau gène mémorisé : {threat_name} (ADN: {_dna_of_gene(gene_content)[:8]}...)")
    return True

def compile_organic_defenses() -> yara.Rules | None:
    """
    🧠 Compile toutes les règles depuis lymph/memory_cells/ —
    comme un thymus qui active les lymphocytes matures.
    """
    global _compiled_immune_system, _last_compilation, _gene_count

    gene_files = list(_MEMORY_CELLS.glob("*.gene"))
    if not gene_files:
        _log("Aucun gène de mémoire trouvé — système immunitaire naïf.")
        return None

    sources = {}
    valid_genes = 0

    for gene in gene_files:
        try:
            content = gene.read_text(encoding="utf-8")
            # Vérification ADN optionnelle ici
            sources[gene.stem] = content
            valid_genes += 1
        except Exception as e:
            _log(f"Gène corrompu ignoré : {gene.name} → {e}")

    if not sources:
        return None

    try:
        compiled = yara.compile(sources=sources)
        _compiled_immune_system = compiled
        _gene_count = valid_genes
        _last_compilation = datetime.now().timestamp()
        _log(f"Système immunitaire compilé : {_gene_count} gènes actifs.")
        return compiled
    except Exception as e:
        _log(f"Échec compilation organique : {e}")
        return None

def scan_with_organic_memory(target_path: str | Path) -> list:
    """
    🔍 Scan une cible (registre, fichier, processus) avec la mémoire immunitaire.
    Retourne les menaces détectées — comme une réponse inflammatoire.
    """
    if not _compiled_immune_system:
        rules = compile_organic_defenses()
        if not rules:
            return []

    try:
        matches = _compiled_immune_system.match(str(target_path))
        threats = [m.rule for m in matches]
        if threats:
            _log(f"ALERTE IMMUNITAIRE : {len(threats)} menace(s) reconnue(s) → {threats}")
        return threats
    except Exception as e:
        _log(f"Erreur scan organique : {e}")
        return []

def get_immune_status() -> dict:
    """📊 État de santé du système immunitaire."""
    return {
        "genes_active": _gene_count,
        "last_compilation": _last_compilation,
        "memory_dir": str(_MEMORY_CELLS),
        "status": "actif" if _compiled_immune_system else "inactif"
    }

# === INTERFACE POUR GUARDS ===
def run(dry_run: bool = False):
    """Exécute un cycle immunitaire complet."""
    if dry_run:
        return {"status": "simulation", "genes_found": len(list(_MEMORY_CELLS.glob("*.gene")))}

    status = get_immune_status()
    if status["status"] == "inactif":
        compile_organic_defenses()

    return status

# === EXEMPLE D'APPRENTISSAGE AUTOMATIQUE ===
if __name__ == "__main__":
    print("🧪 Test du système immunitaire organique de Kerberos")
    
    # Simule une menace détectée
    create_memory_gene(
        threat_name="fake_rdp_enable",
        pattern="fDenyTSConnections = 0x0",
        context="Registre Windows modifié"
    )

    # Compile et scanne un faux registre
    fake_reg = _MEMORY_CELLS / "test.reg"
    fake_reg.write_text("Windows Registry Editor Version 5.00\n[HKEY_LOCAL_MACHINE\\...]\nfDenyTSConnections=0x0\n")

    threats = scan_with_organic_memory(fake_reg)
    print(f"\nRésultat : {threats}")

    fake_reg.unlink(missing_ok=True)