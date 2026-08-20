# guard_no_pub.py — v0.1 — (-;
# Bloque pubs dans HTML/JSON — intégrable au navigateur

PUB_PATTERNS = [
    r"<div[^>]*class=[\"'][^\"']*ad[s\-_][^\"']*[\"'][^>]*>.*?</div>",
    r"<iframe[^>]*src=[\"'][^\"']*ads?[^\"']*[\"'][^>]*>",
    r'"ad_.*?"\s*:\s*".*?"',
    r'"banner.*?"\s*:\s*".*?"'
]

import re

def remove_ads(content: str) -> str:
    for pattern in PUB_PATTERNS:
        content = re.sub(pattern, "", content, flags=re.IGNORECASE | re.DOTALL)
    return content