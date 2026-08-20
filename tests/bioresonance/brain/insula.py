# -*- coding: utf-8 -*-
from datetime import datetime, timedelta

class Insula:
    def __init__(self, cortex):
        self.cortex = cortex

    def evaluer_etat_ame(self, contexte, incarnations):
        """Évalue l'état émotionnel de l'âme avec parsing robuste de la date"""
        # 🔑 CORRECTION : conversion str → datetime SANS échec
        date_naissance = contexte.get("date_naissance", "1990-01-01")
        
        # Si c'est déjà un datetime, utiliser directement
        if hasattr(date_naissance, 'strftime'):
            dt_naissance = date_naissance
        else:
            # Sinon parser la chaîne
            try:
                dt_naissance = datetime.strptime(str(date_naissance), "%Y-%m-%d")
            except:
                try:
                    dt_naissance = datetime.strptime(str(date_naissance), "%d/%m/%Y")
                except:
                    dt_naissance = datetime(1990, 1, 1)  # valeur par défaut
        
        # ✅ Opérations timedelta sécurisées
        date_debut_cycle = dt_naissance - timedelta(days=365*7)
        
        besoin_guerison = len([inc for inc in incarnations if "guerre" in inc.get("lecon_karmique", "").lower()]) > 3
        
        return {
            "besoin_guerison": besoin_guerison,
            "date_debut_cycle": date_debut_cycle.strftime("%Y-%m-%d"),  # ✅ strftime() sur datetime
            "intensite_karmique": min(1.0, len(incarnations) / 12.0)
        }