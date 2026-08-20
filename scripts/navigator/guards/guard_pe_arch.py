# guard_pe_arch.py — v0.1 — (-;
# Analyse statique basique de fichiers PE (exe/dll)

def is_suspicious_pe(filepath: str) -> bool:
    if not os.path.isfile(filepath):
        return False
    try:
        with open(filepath, "rb") as f:
            header = f.read(2)
            if header != b"MZ":
                return False  # pas un PE
            
            f.seek(0x3C)
            pe_offset = int.from_bytes(f.read(4), "little")
            f.seek(pe_offset)
            if f.read(4) != b"PE\0\0":
                return False

            # Sections suspectes
            f.seek(pe_offset + 0x18)
            num_sections = int.from_bytes(f.read(2), "little")
            suspicious = 0
            for _ in range(num_sections):
                name = f.read(8).rstrip(b"\0").decode("ascii", errors="ignore")
                if name in [".upx", "UPX0", "UPX1", "rsrc", ".adata"]:
                    suspicious += 1
                f.seek(32, 1)  # skip rest of section header
            
            # Imports suspects
            # (ici, version simplifiée — à étendre)
            return suspicious >= 2
    except Exception as e:
        print(f"[PE] ❌ Erreur analyse {filepath} : {e} — (-;")
        return False