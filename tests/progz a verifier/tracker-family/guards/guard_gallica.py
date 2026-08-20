# ============================================================
#  guard_gallica.py — 📄 v3 : multi-stratégie + téléchargement
#  - API SRU officielle (la SEULE interface Gallica qui marche)
#  - 3 stratégies de requête (phrase exacte / prénom rare / termes)
#  - Liens DIRECTS ark:/ des documents trouvés
#  - Télécharge la 1ère page (IIIF) dans captures/gallica/
# ============================================================
import re, time
from pathlib import Path

NAME = "gallica"
TYPE = "auto"
UI = False
FRONTS = None
DESCRIPTION = "📄 Gallica BnF — multi-stratégie + liens + téléchargement"

API = "https://gallica.bnf.fr/services/engine/search/sru"
DEST = Path(__file__).parent.parent / "captures" / "gallica"
DEST.mkdir(parents=True, exist_ok=True)
UA = "KerberosFamilyTrace/1.1 (recherche familiale personnelle)"

def _nettoie(t):
    return re.sub(r"<.*?>", "", t).strip()

def _requete(portier, q, maxr=10):
    r = portier.get(API, params={"version": "1.2", "operation": "searchRetrieve",
                                 "query": q, "startRecord": 1, "maximumRecords": maxr})
    if not r:
        return []
    blocs = re.findall(r"<(?:\w+:)?record\b.*?>(.*?)</(?:\w+:)?record>", r.text, re.S)
    out = []
    for b in blocs:
        tm = re.search(r"<dc:title>(.*?)</dc:title>", b, re.S)
        im = re.search(r"<dc:identifier>(.*?)</dc:identifier>", b, re.S)
        titre = _nettoie(tm.group(1)) if tm else ""
        lien = im.group(1).strip() if im else ""
        if titre and lien.startswith("http"):
            out.append((titre, lien))
    return out

def _telecharge_page(lien, emit):
    """Télécharge la 1ère page du document via IIIF (meilleur effort)."""
    import requests
    ark_id = lien.split("ark:/")[-1]
    for qual in ("native", "default"):
        url = f"https://gallica.bnf.fr/iiif/ark:/{ark_id}/f1/full/full/0/{qual}.jpg"
        try:
            time.sleep(0.5)
            ir = requests.get(url, headers={"User-Agent": UA}, timeout=60)
            if ir.ok and len(ir.content) > 2000:
                p = DEST / f"{ark_id.split('/')[-1]}_p1.jpg"
                p.write_bytes(ir.content)
                emit(f"   📥 [gallica] 1ère page sauvée : {p.name}")
                return
        except Exception:
            continue

def run(cible, ctx, emit):
    nom = (cible.get("nom") or "").strip().lower()
    prenom = (cible.get("prenom") or "").strip().lower()
    tokens = [t for t in prenom.replace("-", " ").split() if t]
    termes = [t.lower() for t in ctx["config"].get("termes_extra", []) if t]
    if not nom:
        return
    strategies = [f'"{nom} {prenom}"']
    if tokens:
        strategies.append(f'"{nom}" AND {tokens[-1]}')
    if termes:
        strategies.append(f'"{nom}" AND ({" OR ".join(termes)})')
    found = []
    for q in strategies:
        found = _requete(ctx["portier"], q)
        if found:
            break
    if not found:
        emit("   [gallica] 0 résultat (normal si pas dans presse/livres)")
        return
    for titre, lien in found[:6]:
        emit(f"   📄 [gallica] {titre} -> {lien}")
        _telecharge_page(lien, emit)