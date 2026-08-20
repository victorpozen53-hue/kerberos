# guard_no_spamm.py — v0.1 — (-;
# Filtre heuristique local — pas de cloud, pas d'IA

SPAM_KEYWORDS = {
    "urgent", "gagnant", "loterie", "bitcoin", "crypto", "gratuit", "clic ici",
    "offre exceptionnelle", "dernière chance", "confirmation requise"
}

def is_spam(text: str) -> bool:
    text = text.lower()
    hits = sum(1 for kw in SPAM_KEYWORDS if kw in text)
    return hits >= 2  # seuil bas pour éviter faux négatifs

def clean_text(text: str) -> str:
    if is_spam(text):
        return "[ALERTE SPAM — (-;]"
    return text