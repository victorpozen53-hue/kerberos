# guard_no_tracker.py — v0.1 — (-;
# Liste noire locale de trackers — mis à jour manuellement

TRACKERS = {
    # Google
    "google-analytics.com", "analytics.google.com", "googletagmanager.com",
    # Meta
    "facebook.com", "connect.facebook.net", "fbcdn.net",
    # Ads
    "doubleclick.net", "adservice.google.", "amazon-adsystem.com",
    # Autres
    "scorecardresearch.com", "quantcast.com", "newrelic.com"
}

def is_tracker_domain(domain: str) -> bool:
    domain = domain.lower()
    return any(tracker in domain for tracker in TRACKERS)

def block_trackers_in_html(html_content: str) -> str:
    """Nettoie les trackers dans du HTML (ex: navigateur)"""
    # Supprimer les scripts de tracking
    for tracker in TRACKERS:
        html_content = html_content.replace(f'"{tracker}', '"#')
        html_content = html_content.replace(f"'{tracker}", "'#")
    # Bloquer les iframes
    html_content = html_content.replace("<iframe", "<!-- iframe bloqué -->")
    return html_content

if __name__ == "__main__":
    print("KERBEROS — guard_no_tracker.py — (-;")
    print("Trackers connus :", len(TRACKERS))
    for t in sorted(TRACKERS):
        print(f"  • {t}")