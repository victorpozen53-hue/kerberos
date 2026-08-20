# ============================================================
#  guard_matchid.py — ✅ v2 CORRIGÉ
#  - Vraie API JSON officielle : /deces/api/v1/search
#  - Requête intelligente (nom + prénom rare) + filtre côté client
#  - Respecte la limite officielle (1 req/s) via la Garde Cadence
#  - Aucune donnée perso en dur
# ============================================================
from urllib.parse import quote

NAME = "matchid"
TYPE = "auto"
UI = False
FRONTS = None
DESCRIPTION = "✅ Décès en France depuis 1970 (INSEE) — API officielle JSON"

API = "https://deces.matchid.io/deces/api/v1/search"

def _fmt_date(d):
    d = str(d or "")
    return f"{d[6:8]}/{d[4:6]}/{d[0:4]}" if len(d) == 8 else (d or "?")

def _requete(portier, q, size=50):
    r = portier.get(API, params={"q": q, "size": size})
    if not r:
        return None
    try:
        return r.json().get("response", {}).get("persons", [])
    except Exception:
        return None

def run(cible, ctx, emit):
    nom = (cible.get("nom") or "").strip()
    prenom = (cible.get("prenom") or "").strip()
    annee = str(cible.get("naissance") or "")
    if not nom:
        return
    tokens = [t for t in prenom.replace("-", " ").split() if t]

    # Requête 1 : nom + dernier prénom (souvent le plus rare, ex : PALMYRE)
    persons = _requete(ctx["portier"], f"{nom} {tokens[-1]}") if tokens else None
    # Requête 2 (repli) : nom seul, on filtre côté client
    if not persons:
        persons = _requete(ctx["portier"], nom, size=100) or []

    # Filtre côté client : prénoms + année de naissance
    found = []
    for p in persons:
        name = p.get("name", {})
        last = (name.get("last") or "").upper()
        firsts = " ".join(name.get("first", [])).upper()
        if nom.upper() not in last:
            continue
        ok_p = all(t.upper() in firsts for t in tokens) if tokens else True
        bd = str((p.get("birth") or {}).get("date") or "")
        ok_a = bd.startswith(annee) if annee and len(bd) >= 4 else True
        if ok_p and ok_a:
            found.append(p)

    if found:
        for p in found[:5]:
            name = p.get("name", {})
            b = p.get("birth") or {}
            d = p.get("death") or {}
            emit("   ✅ [matchid] %s %s — né %s %s — † %s %s (%s ans)" % (
                name.get("last", "?"), " ".join(name.get("first", [])),
                _fmt_date(b.get("date")), (b.get("location") or {}).get("city", ""),
                _fmt_date(d.get("date")), (d.get("location") or {}).get("city", ""),
                d.get("age", "?")))
    else:
        for p in persons[:3]:
            name = p.get("name", {})
            b = p.get("birth") or {}
            d = p.get("death") or {}
            emit("   🔎 [matchid] piste proche : %s %s — %s → %s" % (
                name.get("last", "?"), " ".join(name.get("first", [])),
                (b.get("location") or {}).get("city", "?"), _fmt_date(d.get("date"))))
        if not persons:
            emit("   [matchid] 0 décès FR post-1970")
    # Lien navigateur pré-rempli pour vérification à l'œil
    emit(f"   🔗 [matchid] vérifier : https://deces.matchid.io/search?q="
         f"{quote(nom + ' ' + (tokens[-1] if tokens else ''))}")