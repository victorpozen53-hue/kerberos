# -*- coding: utf-8 -*-
# ╔══════════════════════════════════════════════════════════════════════╗
# ║  Lobe Occipital – Générateur de Vision Karmique                     ║
# ║  Projet Kerberos – BioResonance                                     ║
# ╚══════════════════════════════════════════════════════════════════════╝
#
# Copyright (C) 2026  Victor.Pozen
#
# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program.  If not, see <https://www.gnu.org/licenses/>.

"""
👁️‍🗨️ Lobe Occipital – Transforme les données en vision.
Génère un rapport HTML/TXT structuré en 4 piliers :
- Corps physique
- Corps éthérique
- Âme
- Esprit
"""

from datetime import datetime


class LobeOccipital:
    def __init__(self, cortex):
        self.cortex = cortex

    def generer_rapport(self, incarnations, contexte):
        """Retourne un dictionnaire avec les versions HTML et TXT du rapport."""
        html = self._generer_html(incarnations, contexte)
        txt = self._generer_txt(incarnations, contexte)
        return {"html": html, "txt": txt}

    def _generer_html(self, incarnations, contexte):
        # Récupérer les composants du rapport
        etat_ame = contexte.get("etat_ame", {})
        esprit = contexte.get("esprit", {})
        corps_etherique = contexte.get("corps_etherique", {})

        html = '''<!DOCTYPE html>
<html lang="fr">
<head>
<meta charset="UTF-8">
<title>Voyage de l'Âme – Kerberos v2.4</title>
<style>
body { background: linear-gradient(135deg, #0a0a1a 0%, #1a0033 100%); color: #e0e0ff; font-family: Consolas, monospace; padding: 30px; }
.container { max-width: 1000px; margin: 0 auto; background: rgba(30, 10, 60, 0.4); padding: 40px; border-radius: 20px; }
h1 { text-align: center; color: #4fc3f7; font-size: 32px; margin-bottom: 30px; }
.pilier { margin: 30px 0; padding: 20px; border-radius: 12px; }
.physique { background: rgba(50, 100, 50, 0.2); border-left: 4px solid #4caf50; }
.etherique { background: rgba(100, 50, 150, 0.2); border-left: 4px solid #9c27b0; }
.ame { background: rgba(150, 50, 50, 0.2); border-left: 4px solid #f44336; }
.esprit { background: rgba(30, 30, 60, 0.3); border-left: 4px solid #2196f3; }
.incarnation { background: rgba(80, 40, 120, 0.2); margin: 15px 0; padding: 15px; border-radius: 10px; }
</style>
</head>
<body>
<div class="container">
<h1>🌀 VOYAGE DE TON ÂME À TRAVERS LES SIÈCLES</h1>

<!-- PILIER 1 : CORPS PHYSIQUE -->
<div class="pilier physique">
<h2>🪨 CORPS PHYSIQUE</h2>
<p><b>Date de naissance :</b> {date_naissance}</p>
<p><b>Lieu :</b> {latitude:.2f}°, {longitude:.2f}°</p>
</div>

<!-- PILIER 2 : CORPS ÉTHÉRIQUE -->
<div class="pilier etherique">
<h2>🌿 CORPS ÉTHÉRIQUE</h2>
'''.format(
    date_naissance=contexte["date_naissance"].strftime("%Y-%m-%d"),
    latitude=contexte["latitude"],
    longitude=contexte["longitude"]
        )

        if corps_etherique:
            html += f'''
<p><b>État :</b> {corps_etherique.get("etat", "inconnu")}</p>
<p><b>Fréquence actuelle :</b> {corps_etherique.get("frequence_actuelle_hz", 0)} Hz</p>
<p><b>Description :</b> {corps_etherique.get("description", "")}</p>
<p><b>Soins recommandés :</b></p>
<ul>
'''
            for soin in corps_etherique.get("soins_recommandes", []):
                html += f"<li>{soin}</li>"
            html += "</ul>"
        else:
            html += "<p>Aucune analyse éthérique disponible.</p>"

        html += '''
</div>

<!-- PILIER 3 : ÂME -->
<div class="pilier ame">
<h2>🌀 ÂME</h2>
'''

        if etat_ame:
            besoin = "⚠️ Guérison nécessaire" if etat_ame.get("besoin_guerison") else "💚 En harmonie"
            html += f"<p><b>État global :</b> {besoin}</p>"

        html += "<h3>Incarnations significatives :</h3>"
        for inc in incarnations:
            html += f'''
<div class="incarnation">
<b>Vie #{inc['numero']} — {inc['type_ame']}</b><br>
Époque : {inc['epoque']} (vers {inc['annee']})<br>
Lieu : {inc['latitude']:.2f}°, {inc['longitude']:.2f}°<br>
Leçon : {inc['lecon_karmique']}
</div>
'''

        html += '''
</div>

<!-- PILIER 4 : ESPRIT -->
<div class="pilier esprit">
<h2>👁️‍🗨️ ESPRIT</h2>
'''

        if esprit:
            html += f'''
<p><i>« {esprit.get("message", "Je suis celui qui observe.")} »</i></p>
<p>L’âme voyage. L’Esprit demeure.</p>
'''
        else:
            html += "<p>Présence éternelle, hors du temps.</p>"

        html += '''
</div>
</div>
</body>
</html>'''
        return html

    def _generer_txt(self, incarnations, contexte):
        etat_ame = contexte.get("etat_ame", {})
        esprit = contexte.get("esprit", {})
        corps_etherique = contexte.get("corps_etherique", {})

        txt = "═" * 70 + "\n"
        txt += "        🌀 VOYAGE DE TON ÂME À TRAVERS LES SIÈCLES\n"
        txt += "═" * 70 + "\n\n"

        # Corps physique
        txt += "🪨 CORPS PHYSIQUE\n"
        txt += f"   Date : {contexte['date_naissance'].strftime('%Y-%m-%d')}\n"
        txt += f"   Lieu : {contexte['latitude']:.2f}°, {contexte['longitude']:.2f}°\n\n"

        # Corps éthérique
        txt += "🌿 CORPS ÉTHÉRIQUE\n"
        if corps_etherique:
            txt += f"   État : {corps_etherique.get('etat', 'inconnu')}\n"
            txt += f"   Fréquence : {corps_etherique.get('frequence_actuelle_hz', 0)} Hz\n"
            txt += f"   {corps_etherique.get('description', '')}\n"
            txt += "   Soins recommandés :\n"
            for soin in corps_etherique.get("soins_recommandes", []):
                txt += f"     • {soin}\n"
        else:
            txt += "   Aucune analyse éthérique disponible.\n"
        txt += "\n"

        # Âme
        txt += "🌀 ÂME\n"
        if etat_ame:
            besoin = "⚠️ Guérison nécessaire" if etat_ame.get("besoin_guerison") else "💚 En harmonie"
            txt += f"   État global : {besoin}\n"
        txt += "\n   Incarnations significatives :\n"
        for inc in incarnations:
            txt += f"\n   Vie #{inc['numero']} — {inc['type_ame']}\n"
            txt += f"     Époque : {inc['epoque']} (vers {inc['annee']})\n"
            txt += f"     Lieu : {inc['latitude']:.2 f}°, {inc['longitude']:.2f}°\n"
            txt += f"     Leçon : {inc['lecon_karmique']}\n"
        txt += "\n"

        # Esprit
        txt += "👁️‍🗨️ ESPRIT\n"
        if esprit:
            txt += f"   « {esprit.get('message', 'Je suis celui qui observe.')} »\n"
            txt += "   L’âme voyage. L’Esprit demeure.\n"
        else:
            txt += "   Présence éternelle, hors du temps.\n"

        txt += "\n" + "═" * 70
        return txt