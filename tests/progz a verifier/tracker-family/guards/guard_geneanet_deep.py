# ============================================================
#  guard_geneanet_deep.py — 🌳 v2 : cookie AUTO intégré
#  - Pas de cookie ? → l'extrait LUI-MÊME de Brave et le sauvegarde
#  - Teste le mur de login directement sur la page de recherche
#  - Aucun mot de passe en dur — tout reste local
# ============================================================
import re, sys
from pathlib import Path
from urllib.parse import quote

_HERE = Path(__file__).parent
if str(_HERE) not in sys.path:
    sys.path.insert(0, str(_HERE))
try:
    import guard_comptes as GC
except Exception:
    GC = None

NAME = "geneanet_deep"
TYPE = "auto"
UI = False
FRONTS = None
DESCRIPTION = "🌳 Geneanet profond — cookie auto, actif si session vivante"

UA = "KerberosFamilyTrace/1.1 (recherche familiale personnelle)"

def _cookie_auto():
    """Cookie : sessions.json d'abord, sinon extraction directe Brave."""
    if GC is None:
        return ""
    c = GC.get_cookie("geneanet")
    if c:
        return c
    c, err = GC.auto_cookie("geneanet")
    if c:
        data = GC._load()
        data["geneanet"] = c
        GC._save(data)
    return c or ""

def run(cible, ctx, emit):
    nom = (cible.get("nom") or "").strip()
    prenom = (cible.get("prenom") or "").strip()
    if not nom:
        return
    cookie = _cookie_auto()
    if not cookie:
        emit("   🔒 [geneanet] aucun cookie — ouvre Brave connecté à Geneanet puis relance")
        return
    import requests
    url = (f"https://www.geneanet.org/fonds/individus/"
           f"?nom={quote(nom)}&prenom={quote(prenom)}")
    try:
        r = requests.get(url, headers={"User-Agent": UA, "Cookie": cookie}, timeout=30)
    except Exception:
        emit("   ⚠️ [geneanet] requête impossible")
        return
    low = r.text.lower()
    if ("mot de passe" in low or "password" in low) and ("connexion" in low or "login" in low):
        emit("   🔒 [geneanet] session expirée — reconnecte-toi dans Brave puis relance le scan")
        return
    texte = re.sub(r"<[^>]+>", " ", r.text)
    texte = re.sub(r"\s+", " ", texte)
    parts = re.split(f"(?i)({re.escape(nom)})", texte)
    seen, n = set(), 0
    for i in range(1, len(parts) - 1, 2):
        frag = (parts[i] + parts[i + 1][:90]).strip()
        if any(c.isdigit() for c in frag) and frag not in seen:
            seen.add(frag)
            n += 1
            emit(f"   🌳 [geneanet] {frag}")
        if n >= 6:
            break
    if not n:
        emit("   🌳 [geneanet] 0 résultat (même connecté)")
    emit(f"   🔗 [geneanet] vérifier : {url}")