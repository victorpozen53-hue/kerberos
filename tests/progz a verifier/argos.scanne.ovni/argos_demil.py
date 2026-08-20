#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
🕊️ ARGOS DEMIL v1.0 — dé-militarisation de la doctrine
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
Author: Victor Pozen | GPLv3
Réécrit war_doctrine.txt en version 100% CIVILE :
observation & inventaire, jamais de ciblage.
(carré = bâtiment, triangle = avion léger, rond = dôme/réservoir…)
Le Thymus sauvegardera ensuite la doctrine civile dans le plasma.
"""
from pathlib import Path

DOCTRINE = Path(__file__).resolve().parent / "war_doctrine.txt"

CIVILE = """# forme;label;couleur — DOCTRINE CIVILE (observation, jamais de ciblage)
# générée par argos_demil.py — GPLv3 Victor Pozen
triangle;AVION LEGER;orange
rectangle;CAMION;jaune
carre;BATIMENT;magenta
croix;AVION COMMERCIAL;blanc
x;HELICO;cyan
rond;DOME OU RESERVOIR;rouge
ligne;ROUTE;rouge_sombre
"""


def main():
    try:
        DOCTRINE.write_text(CIVILE, encoding="utf-8")
        print("🕊️ Doctrine dé-militarisée:", DOCTRINE)
        print("   L'engine Argos lira la version civile au prochain départ.")
        print("   Le Thymus la sauvegardera dans le plasma (immunité civile).")
    except Exception as e:
        print("❌", e)
    input("Appuyez sur Entrée...")


if __name__ == '__main__':
    main()