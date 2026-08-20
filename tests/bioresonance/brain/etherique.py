# -*- coding: utf-8 -*-
from datetime import datetime, timedelta

class Etherique:
    def __init__(self, cortex):
        self.cortex = cortex

    def analyser_champ(self, contexte, incarnations):
        """Analyse le champ éthérique avec parsing robuste de la date"""
        # 🔑 CORRECTION : conversion str → datetime SANS échec
        date_naissance = contexte.get("date_naissance", "1990-01-01")
        
        if hasattr(date_naissance, 'strftime'):
            dt_naissance = date_naissance
        else:
            try:
                dt_naissance = datetime.strptime(str(date_naissance), "%Y-%m-%d")
            except:
                try:
                    dt_naissance = datetime.strptime(str(date_naissance), "%d/%m/%Y")
                except:
                    dt_naissance = datetime(1990, 1, 1)
        
        # ✅ Opérations timedelta sécurisées
        date_entree_ame = dt_naissance - timedelta(days=133)
        
        intensite = 0.7 + (len(incarnations) * 0.02)
        harmonie = "équilibré" if intensite < 0.9 else "déséquilibré"
        
        return {
            "date_entree_ame": date_entree_ame.strftime("%Y-%m-%d"),  # ✅ strftime() sur datetime
            "intensite_champ": min(1.0, intensite),
            "harmonie": harmonie,
            "proximite_lieux_sacres": "moyenne"
        }