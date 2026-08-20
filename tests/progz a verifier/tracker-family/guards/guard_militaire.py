# ============================================================
#  guard_militaire.py — 🎖️ Archives militaires mondiales
#  - ITALIE : liste di leva (classe 1929 pour Mirco), caduti,
#    fogli matricolari, prisonniers Grande Guerre
#  - FRANCE : Grand Mémorial, Mémoire des Hommes (famille Boyer)
#  - MONDE : CWGC, Volksbund, War Heritage Belgique
#  - Bonus : calcule la CLASSE militaire (naissance + 20)
#  - Liens pré-remplis + consignes (zéro donnée en dur)
# ============================================================
from urllib.parse import quote

NAME = "militaire"
TYPE = "lien"
UI = False
FRONTS = None
DESCRIPTION = "🎖️ Archives militaires — leva, caduti, Mémoire des Hommes, CWGC"

SOURCES = [
    # ---------- ITALIE (Mirco : classe 1929) ----------
    {"nom": "🇮🇹 antenati-leva", "fronts": ["Italie"],
     "url": "https://antenati.cultura.gov.it/",
     "consigne": "Search registers → Archivio Stato Udine → série MILITAIRE (liste di leva, classe 1929)"},
    {"nom": "🇮 onorcaduti", "fronts": ["Italie"],
     "url": "http://www.onorcaduti.gov.it/",
     "consigne": "Ricerca caduti : {nom} {prenom} (1940-45)"},
    {"nom": "🇮🇹 cri-grandeguerra", "fronts": ["Italie"],
     "url": "https://grandeguerra.cri.it/",
     "consigne": "Prisonniers Grande Guerre (Croix-Rouge italienne)"},
    {"nom": "🇮🇹 archivio-udine", "fronts": ["Italie"],
     "url": None,
     "consigne": "COURRIER : Archivio di Stato di Udine — foglio matricolare classe 1929"},

    # ---------- FRANCE (famille Boyer : 14-18 / 39-45) ----------
    {"nom": "🇫🇷 grand-memorial", "fronts": ["France"],
     "url": "https://grandmemorial.culture.gouv.fr/",
     "consigne": "Registres matricules français (père/frères de {prenom} {nom})"},
    {"nom": "🇫🇷 memoire-hommes", "fronts": ["France"],
     "url": "https://www.memoiredeshommes.sga.defense.gouv.fr/",
     "consigne": "Morts pour la France 14-18 / 39-45 : {nom}"},

    # ---------- BELGIQUE (famille Keijnen) ----------
    {"nom": "🇧🇪 warheritage", "fronts": ["Belgique", "Mer"],
     "url": "https://warheritage.be/",
     "consigne": "Institut d'histoire militaire belge : {nom}"},

    # ---------- MONDE ----------
    {"nom": "🌍 cwgc", "fronts": None,
     "url": "https://www.cwgc.org/find-results/?surname={nom}",
     "consigne": "Commonwealth War Graves (recherche directe)"},
    {"nom": "🌍 volksbund", "fronts": None,
     "url": "https://www.volksbund.de/graebersuche/",
     "consigne": "Sépultures militaires allemandes : {nom}"},
]

def run(cible, ctx, emit):
    front = cible.get("front")
    nom = quote(cible.get("nom", ""))
    prenom = quote(cible.get("prenom", ""))
    # 🎖️ Bonus : classe militaire = naissance + 20
    classe = ""
    annee = cible.get("naissance")
    if annee:
        try:
            classe = f" [classe {int(annee) + 20}]"
        except Exception:
            classe = ""
    for s in SOURCES:
        fronts = s.get("fronts")
        if fronts and front not in fronts:
            continue
        url = s.get("url") or "COURRIER"
        if url != "COURRIER":
            url = url.replace("{nom}", nom).replace("{prenom}", prenom)
        consigne = (s["consigne"]
                    .replace("{nom}", cible.get("nom", ""))
                    .replace("{prenom}", cible.get("prenom", "")))
        emit(f"   🎖️ [{s['nom']}] {consigne}{classe} -> {url}")