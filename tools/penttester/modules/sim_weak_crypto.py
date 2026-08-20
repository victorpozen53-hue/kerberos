#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
🔑 sim_weak_crypto — Génère clés et certs cryptographiquement faibles
GPLv3 — Victor Pozen — Kerberos Pentest Suite v1.0
"""
import time
from pathlib import Path
from datetime import datetime, timezone, timedelta

MODULE_NAME  = "sim_weak_crypto"
MODULE_LABEL = "Weak Crypto"
_running     = False
_OUT_DIR     = Path(__file__).parent.parent / "payloads_fake" / "crypto"


def _try_gen_rsa(bits: int) -> bytes:
    """Génère une vraie clé RSA faible"""
    try:
        from cryptography.hazmat.primitives.asymmetric import rsa
        from cryptography.hazmat.primitives import serialization
        key = rsa.generate_private_key(public_exponent=65537, key_size=bits)
        return key.private_bytes(
            serialization.Encoding.PEM,
            serialization.PrivateFormat.TraditionalOpenSSL,
            serialization.NoEncryption())
    except Exception:
        # Fallback : PEM fake avec header correct
        return (f"-----BEGIN RSA PRIVATE KEY-----\n"
                f"KERBEROS_PENTEST_FAKE_RSA_{bits}_KEY\n"
                f"-----END RSA PRIVATE KEY-----\n").encode()


def _try_gen_weak_cert(bits: int) -> bytes:
    """Génère un certificat auto-signé avec clé RSA faible"""
    try:
        from cryptography import x509
        from cryptography.hazmat.primitives.asymmetric import rsa
        from cryptography.hazmat.primitives import hashes, serialization
        from cryptography.x509.oid import NameOID

        key = rsa.generate_private_key(public_exponent=65537, key_size=bits)
        subject = x509.Name([
            x509.NameAttribute(NameOID.COMMON_NAME, "KERBEROS_PENTEST_WEAK_CERT"),
            x509.NameAttribute(NameOID.ORGANIZATION_NAME, "Pentest Suite Test"),
        ])
        cert = (x509.CertificateBuilder()
                .subject_name(subject)
                .issuer_name(subject)
                .public_key(key.public_key())
                .serial_number(x509.random_serial_number())
                .not_valid_before(datetime.now(timezone.utc))
                .not_valid_after(datetime.now(timezone.utc) + timedelta(days=365))
                .sign(key, hashes.SHA256()))
        return cert.public_bytes(serialization.Encoding.PEM)
    except Exception:
        return (f"-----BEGIN CERTIFICATE-----\n"
                f"KERBEROS_PENTEST_FAKE_CERT_RSA_{bits}\n"
                f"-----END CERTIFICATE-----\n").encode()


def run(target: str = "127.0.0.1", callback=None) -> dict:
    global _running
    _running = True
    _OUT_DIR.mkdir(parents=True, exist_ok=True)

    results = {"module": MODULE_NAME, "target": target,
               "started": datetime.now().isoformat(),
               "events": [], "files": [], "status": "running"}

    def log(msg):
        results["events"].append(msg)
        if callback: callback(msg)

    log("🔑 Démarrage simulation Weak Crypto...")

    weak_cases = [
        (512,  "RSA-512 — cassable en minutes classiquement"),
        (1024, "RSA-1024 — cassable par Shor + classiquement"),
        (2048, "RSA-2048 — vulnérable à Shor"),
    ]

    for bits, desc in weak_cases:
        if not _running:
            break
        time.sleep(0.3)
        # Clé privée
        fk = _OUT_DIR / f"fake_rsa_{bits}_key.pem"
        fk.write_bytes(_try_gen_rsa(bits))
        results["files"].append(str(fk))
        log(f"✅ Clé {desc} → {fk.name}")

        # Certificat
        time.sleep(0.3)
        fc = _OUT_DIR / f"fake_rsa_{bits}_cert.pem"
        fc.write_bytes(_try_gen_weak_cert(bits))
        results["files"].append(str(fc))
        log(f"✅ Cert RSA-{bits} auto-signé → {fc.name}")

    # Clé DSA (totalement cassable)
    time.sleep(0.2)
    f_dsa = _OUT_DIR / "fake_dsa_key.pem"
    f_dsa.write_text(
        "-----BEGIN DSA PRIVATE KEY-----\n"
        "KERBEROS_PENTEST_FAKE_DSA_KEY_TOTALLY_BROKEN\n"
        "-----END DSA PRIVATE KEY-----\n",
        encoding="utf-8")
    results["files"].append(str(f_dsa))
    log("✅ Clé DSA fake (cassable classiquement + Shor)")

    log("   → guard_post_quantum.py scan_ssh_keys() doit détecter")
    log("   → guard_post_quantum.py scan_local_certificates() doit détecter")
    log(f"📊 {len(results['files'])} fichier(s) crypto faibles créés")

    results["status"] = "completed"
    results["finished"] = datetime.now().isoformat()
    _running = False
    return results


def stop():
    global _running
    _running = False


def get_info() -> dict:
    return {"name": MODULE_NAME, "label": MODULE_LABEL,
            "description": "Génère vraies clés RSA faibles + certs vulnérables",
            "version": "1.0", "targets": ["guard_post_quantum.py"]}
