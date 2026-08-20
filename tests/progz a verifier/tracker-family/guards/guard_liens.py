# ============================================================
#  guard_liens.py — 🔗 v3 : placeholders complets
#  {nom} {prenom} {q} {naissance} {lieu}
#  - liens.json peut contenir des liens DIRECTS pré-remplis
#  - FamilySearch / Maitron / FindAGrave arrivent déjà remplis
#  - Aucune donnée perso en dur (tout vient de la cible au runtime)
# ============================================================
import json
from pathlib import Path
from urllib.parse import quote

NAME = "liens"
TYPE = "lien"
UI = False
FRONTS = None
DESCRIPTION = "🔗 Liens humains + liens directs pré-remplis (liens.json)"

def run(cible, ctx, emit):
    f = Path(__file__).parent.parent / "liens.json"
    if not f.exists():
        emit("   [liens] liens.json absent"); return
    try:
        data = json.loads(f.read_text(encoding="utf-8"))
    except Exception as e:
        emit(f"   [liens] erreur JSON : {e}"); return

    front = cible.get("front")
    nom = quote(cible.get("nom", "") or "")
    prenom = quote(cible.get("prenom", "") or "")
    q = quote(f"{cible.get('nom','')} {cible.get('prenom','')}".strip())
    naissance = quote(str(cible.get("naissance") or ""))
    lieu = quote(cible.get("lieu", "") or "")

    for l in data.get("liens", []):
        fronts = l.get("fronts")
        if fronts and front not in fronts:
            continue
        url = l.get("url") or "COURRIER"
        if url != "COURRIER":
            url = (url.replace("{nom}", nom).replace("{prenom}", prenom)
                   .replace("{q}", q).replace("{naissance}", naissance)
                   .replace("{lieu}", lieu))
        consigne = (l.get("consigne", "")
                    .replace("{nom}", cible.get("nom", "") or "")
                    .replace("{prenom}", cible.get("prenom", "") or ""))
        emit(f"   🔗 [{l.get('nom')}] {consigne} -> {url}")