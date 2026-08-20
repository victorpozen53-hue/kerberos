# KERBEROS — GUARDS — (-;

Sécurité desktop locale — Windows 7/10, matériel ancien, zéro cloud.  
White hat only. GPLv3.

## 🛡️ Liste des gardes

| Garde | Rôle |
|-------|------|
| `guard_bubble.py` | Exécute un programme dans une bulle isolée (pas de VM) |
| `guard_no_shodan.py` | Bloque Shodan/Censys via hosts + firewall |
| `guard_no_tracker.py` | Neutralise les trackers (Google Analytics, Meta, etc.) |
| `guard_no_spamm.py` | Filtre spams locaux (heuristique texte) |
| `guard_no_pub.py` | Supprime pubs dans HTML/JSON |
| `guard_pe_arch.py` | Détection heuristique de PE malveillants |

## ✅ Utilisation

- Copiez ce dossier dans `H:\navigator\guards\`  
- Importez dans vos scripts :
  ```python
  from guards.guard_bubble import run_in_bubble
  from guards.guard_no_tracker import is_tracker_domain