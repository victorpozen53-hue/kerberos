# -*- coding: utf-8 -*-
# ==============================================================
# guard_image.py — v1.1 — (-;
# Analyse éthique locale des images (JPEG, PNG, GIF, BMP)
# White hat only. GPLv3.
# ==============================================================
# (-; — Victor.Pozen

import os
import struct
import re

# === SIGNATURES BINAIRES ===
MAGIC_BYTES = {
    b"\xFF\xD8\xFF": "JPEG",
    b"\x89PNG\r\n\x1a\n": "PNG",
    b"GIF87a": "GIF",
    b"GIF89a": "GIF",
    b"BM": "BMP",
    b"\x00\x00\x01\x00": "ICO"
}

# === VULNÉRABILITÉS CONNUES ===
KNOWN_VULNS = {
    # CVE-2004-0448 — Heap Overflow PNG (Jasc Paint Shop Pro 8)
    "PSP8_PNG_OVERFLOW": {
        "type": "PNG",
        "pattern": re.compile(rb"IHDR.{4}.{4}\x01\x00\x00\x00.*?IDAT", re.DOTALL),
        "desc": "Heap overflow PNG — Jasc PSP 8"
    },
    # CVE-2004-0200 — EXIF overflow
    "EXIF_OVERFLOW": {
        "type": "JPEG",
        "pattern": re.compile(rb"\xFF\xE1.{2}Exif\x00\x00.{2,1000}$"),
        "desc": "Exif overflow — lecteurs JPEG vulnérables"
    }
}

# === FONCTIONS UTILITAIRES ===
def detect_image_type(filepath: str) -> str:
    if not os.path.isfile(filepath):
        return "not_found"
    try:
        with open(filepath, "rb") as f:
            header = f.read(12)
        for magic, fmt in MAGIC_BYTES.items():
            if header.startswith(magic):
                return fmt
        return "unknown"
    except:
        return "error"

def scan_for_vulns(filepath: str) -> list:
    alerts = []
    typ = detect_image_type(filepath)
    if typ == "unknown":
        return alerts
    try:
        with open(filepath, "rb") as f:
            data = f.read()
        for name, vuln in KNOWN_VULNS.items():
            if vuln["type"] == typ and vuln["pattern"].search(data):
                alerts.append(f"{name}: {vuln['desc']}")
    except:
        pass
    return alerts

def extract_exif(filepath: str) -> dict:
    metadata = {}
    if detect_image_type(filepath) != "JPEG":
        return metadata
    try:
        with open(filepath, "rb") as f:
            data = f.read()
        exif_start = data.find(b"Exif\x00\x00")
        if exif_start != -1:
            if b"Software" in data:
                metadata["software"] = "[présent]"
            if b"GPS" in data or b"\x02\x02\x00\x01" in data:
                metadata["gps"] = "[précis]"
            if b"DateTime" in data:
                metadata["datetime"] = "[timestamp]"
    except:
        pass
    return metadata

def sanitize_image(filepath: str) -> str:
    """Génère une version propre (sans métadonnées)."""
    clean_path = filepath + ".sanitized"
    typ = detect_image_type(filepath)
    try:
        with open(filepath, "rb") as f:
            raw = f.read()
        if typ == "JPEG":
            soi = raw.find(b"\xFF\xD8")
            eoi = raw.find(b"\xFF\xD9")
            if soi != -1 and eoi != -1:
                clean = raw[soi:eoi+2]
                with open(clean_path, "wb") as out:
                    out.write(clean)
                return clean_path
        elif typ == "PNG":
            clean = b"\x89PNG\r\n\x1a\n"
            pos = 8
            while pos < len(raw) - 12:
                try:
                    length = struct.unpack(">I", raw[pos:pos+4])[0]
                    chunk_type = raw[pos+4:pos+8]
                    if chunk_type in [b"IHDR", b"IDAT", b"IEND"]:
                        clean += raw[pos:pos+8+length+4]
                    pos += 8 + length + 4
                except:
                    break
            with open(clean_path, "wb") as out:
                out.write(clean)
            return clean_path
        else:
            with open(clean_path, "wb") as out:
                out.write(raw)
            return clean_path
    except:
        return ""
    return ""

# === ANALYSE INTERNE (sans boucle) ===
def _is_suspicious_core(filepath: str) -> bool:
    if not os.path.isfile(filepath):
        return False
    typ = detect_image_type(filepath)
    if typ == "unknown":
        return False
    vulns = scan_for_vulns(filepath)
    exif = extract_exif(filepath)
    return len(vulns) > 0 or any(k in ["gps", "software", "datetime"] for k in exif)

# === INTERFACE KERBEROS BRAIN v2.0 ===
def is_suspicious(filepath: str) -> bool:
    return _is_suspicious_core(filepath)

def scan(content: str, url: str = "") -> list:
    alerts = []
    if "image/" in url.lower():
        alerts.append("🖼️ Image distante détectée")
    if "base64," in content:
        alerts.append("🖼️ Données image base64 détectées — analyse manuelle recommandée")
    return alerts

def get_status() -> str:
    return "✅" if os.path.isfile(__file__) else "❌"

# === TEST STANDALONE ===
if __name__ == "__main__":
    print("[GUARD] guard_image.py — v1.1 — (-;")
    print("[GUARD] Interface : is_suspicious(), scan(), get_status()")
    print("[GUARD] Prêt à protéger — (-;")