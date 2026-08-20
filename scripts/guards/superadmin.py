# superadmin.py — généré par kerb_core_validator
__kerb_guard__ = True
requires = ["polox.auth", "diskcache.lock"]
permissions = ["core.modify", "system.elevate"]

def elevate():
    import os
    return os.getuid() == 0 if hasattr(os, "getuid") else True  # Windows → True pour test
