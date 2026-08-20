# immune_core.py
# Licence : GNU GPL v3
# Projet Kerberos – Système immunitaire contre l'auto-destruction
# Fonctionne sur n'importe quel chemin, n'importe quel utilisateur

import os

# Détection automatique de la racine de Kerberos (là où ce fichier se trouve)
KERBEROS_ROOT = os.path.abspath(os.path.dirname(__file__))

def is_self(filepath):
    """
    Retourne True si le fichier donné fait partie de l'installation courante de Kerberos.
    Utilisé par tous les guards pour s'auto-exclure des analyses.
    """
    if not os.path.exists(filepath):
        return False
    try:
        abs_path = os.path.abspath(filepath)
        # Normalisation pour compatibilité Windows (évite les problèmes de \ vs /)
        return os.path.normpath(abs_path).startswith(os.path.normpath(KERBEROS_ROOT))
    except Exception:
        return False

# Auto-test (optionnel)
if __name__ == "__main__":
    print(f"[IMMUNITÉ] Racine détectée : {KERBEROS_ROOT}")
    if is_self(__file__):
        print("[✅] Ce fichier est reconnu comme faisant partie de Kerberos.")
    else:
        print("[❌] Problème : Kerberos ne se reconnaît pas lui-même.")
    input("Appuyez sur Entrée pour quitter...")