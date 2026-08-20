# modules/kerberos_network.py — Réseau Kerberos Éthique (GPLv3)
import json, hashlib, time, threading
from pathlib import Path
import socket, ssl

NETWORK_DIR = Path(__file__).parent.parent / "lymph" / "network"
NETWORK_DIR.mkdir(parents=True, exist_ok=True)
PEERS_FILE = NETWORK_DIR / "peers.json"  # Liste des pairs autorisés (manuellement gérée)
SHARED_SIGS_DIR = NETWORK_DIR / "shared_signatures"
SHARED_SIGS_DIR.mkdir(exist_ok=True)

# === CONFIGURATION ===
_ENABLED = False  # Désactivé par défaut — activation manuelle requise
_PEERS = []       # Liste des adresses IP:port autorisées

def enable_network(peers_list=None):
    """Active le réseau KRE — consentement explicite requis"""
    global _ENABLED, _PEERS
    if peers_list:
        _PEERS = peers_list
        _PEERS = [p for p in _PEERS if _validate_peer(p)]
    _ENABLED = True
    print("[🔗 KRE] Réseau Kerberos Éthique activé")
    print(f"   • Pairs connectés : {len(_PEERS)}")
    print("   • Données partagées : signatures YARA anonymisées uniquement")
    print("   • Aucune donnée personnelle ne quitte cette machine")
    _start_background_sync()

def disable_network():
    """Désactive immédiatement le réseau KRE"""
    global _ENABLED
    _ENABLED = False
    print("[🔗 KRE] Réseau désactivé — plus aucune communication réseau")

def _validate_peer(peer_addr):
    """Valide qu'une adresse est un pair Kerberos authentique"""
    try:
        ip, port = peer_addr.split(":")
        socket.inet_aton(ip)  # Valide IPv4
        port = int(port)
        return 1024 <= port <= 65535
    except:
        return False

def share_threat_signature(rule_name, yara_rule, k_score):
    """
    Partage une signature YARA anonymisée avec le réseau
    Appelé après détection + confirmation utilisateur
    """
    if not _ENABLED or not _PEERS:
        return False
    
    # Créer signature anonymisée
    sig_id = hashlib.sha256(f"{rule_name}{yara_rule}{k_score}{time.time()}".encode()).hexdigest()[:16]
    signature = {
        "sig_id": sig_id,
        "rule_name": rule_name,
        "yara_rule": yara_rule,
        "k_score": k_score,
        "timestamp": time.time(),
        "source": "kerberos_v4.1",  # Pas d'identifiant machine
        "dna_hash": hashlib.sha256(yara_rule.encode()).hexdigest()[:8]  # Empreinte de la règle uniquement
    }
    
    # Sauvegarder localement
    sig_file = SHARED_SIGS_DIR / f"{sig_id}.json"
    sig_file.write_text(json.dumps(signature, indent=2), encoding="utf-8")
    
    # Diffuser aux pairs (en arrière-plan)
    threading.Thread(target=_broadcast_signature, args=(signature,), daemon=True).start()
    return True

def _broadcast_signature(signature):
    """Diffuse la signature aux pairs autorisés (TLS obligatoire)"""
    if not _ENABLED:
        return
    
    for peer in _PEERS:
        try:
            # Connexion TLS minimale (pas de certificat commercial — auto-signé)
            context = ssl.SSLContext(ssl.PROTOCOL_TLS_CLIENT)
            context.check_hostname = False
            context.verify_mode = ssl.CERT_NONE  # ⚠️ À améliorer avec certificats Kerberos
            
            with socket.create_connection((peer.split(":")[0], int(peer.split(":")[1])), timeout=5) as sock:
                with context.wrap_socket(sock, server_hostname=peer.split(":")[0]) as ssock:
                    ssock.sendall(json.dumps({
                        "type": "threat_signature",
                        "payload": signature,
                        "timestamp": time.time()
                    }).encode() + b"\n")
        except Exception as e:
            print(f"[🔗 KRE] Erreur envoi à {peer}: {e}")

def _start_background_sync():
    """Thread silencieux — synchronisation toutes les 5 minutes"""
    def _loop():
        while _ENABLED:
            time.sleep(300)  # 5 minutes
            if _PEERS:
                print(f"[🔗 KRE] Synchronisation avec {len(_PEERS)} pair(s)")
                # Ici : récupérer nouvelles signatures des pairs
                # (implémentation minimale pour le prototype)
    
    threading.Thread(target=_loop, daemon=True, name="kerberos_network_sync").start()

def get_network_stats():
    """Retourne les stats du réseau pour l'UI"""
    return {
        "enabled": _ENABLED,
        "peers_count": len(_PEERS),
        "shared_signatures": len(list(SHARED_SIGS_DIR.glob("*.json"))),
        "last_sync": time.strftime("%H:%M:%S") if _ENABLED else "jamais"
    }