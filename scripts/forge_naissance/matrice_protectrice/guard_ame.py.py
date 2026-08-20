# guards/guard_ame.py
# -*- coding: utf-8 -*-
# GPLv3 – Victor Pozen / Kerberos
# Guérison de l'âme via fréquences temporelles (animation ~19 semaines)

import os
import json
import hashlib
from datetime import datetime, timedelta
from pathlib import Path
from tkinter import Tk, Toplevel, Label, Entry, Button, messagebox

try:
    from pydub import AudioSegment
    from pydub.generators import Sine
    _has_pydub = True
except ImportError:
    _has_pydub = False

# === GÉOCODAGE LOCAL (zéro dépendance) ===
VILLE_PAR_DEFAUT = {"lat": 48.8566, "lon": 2.3522}
VILLES_GEO = {
    "paris": VILLE_PAR_DEFAUT,
    "marseille": {"lat": 43.2965, "lon": 5.3698},
    "lyon": {"lat": 45.7640, "lon": 4.8357},
    "toulouse": {"lat": 43.6047, "lon": 1.4442},
    "nice": {"lat": 43.7102, "lon": 7.2620},
    "nantes": {"lat": 47.2184, "lon": -1.5536},
    "strasbourg": {"lat": 48.5734, "lon": 7.7521},
    "montpellier": {"lat": 43.6108, "lon": 3.8767},
    "bordeaux": {"lat": 44.8378, "lon": -0.5792},
    "lille": {"lat": 50.6292, "lon": 3.0573}
}

def geocoder_local(ville: str):
    if not ville.strip():
        return VILLE_PAR_DEFAUT
    return VILLES_GEO.get(ville.strip().lower(), VILLE_PAR_DEFAUT)

# === GÉNÉRATION DU SOIN ===
def generer_soin_ame(date_naiss: str, lieu: str = "Paris", dossier_sortie: str = "ame_soin"):
    if not _has_pydub:
        raise RuntimeError("pydub manquant — installez-le et placez ffmpeg.exe dans le dossier racine.")
    
    # Calcul du moment d'animation (~19 semaines après fécondation)
    naiss = datetime.strptime(date_naiss, "%Y-%m-%d")
    animation = naiss - timedelta(days=266 - 19*7)  # 266 jours gestation + 19 semaines
    
    # Création du dossier
    sortie = Path(dossier_sortie)
    sortie.mkdir(exist_ok=True)
    
    # Génération audio (19 min, 7.83 Hz binaural)
    base, schumann = 200, 7.83
    duree_ms = 19 * 60 * 1000
    gauche = Sine(base).to_audio_segment(duration=duree_ms)
    droite = Sine(base + schumann).to_audio_segment(duration=duree_ms)
    binaural = AudioSegment.from_mono_audiosegments(gauche, droite)
    
    nom_fichier = f"soin_ame_{animation.strftime('%Y%m%d')}.wav"
    chemin = sortie / nom_fichier
    binaural.export(chemin, format="wav")
    
    # Hash forensic
    sha256 = hashlib.sha256()
    with open(chemin, "rb") as f:
        for chunk in iter(lambda: f.read(4096), b""):
            sha256.update(chunk)
    
    # Rapport TXT
    rapport = f"""[GUARD AME - RAPPORT FORENSIC]
Date de naissance : {date_naiss}
Lieu             : {lieu}
Moment d'animation : {animation.strftime('%Y-%m-%d')}
Fichier audio    : {nom_fichier}
SHA256           : {sha256.hexdigest()}
Statut           : SOIN GENERE - A ECOUTER EN CASQUE
"""
    rapport_path = sortie / f"rapport_ame_{animation.strftime('%Y%m%d')}.txt"
    rapport_path.write_text(rapport, encoding="utf-8")
    
    return str(chemin), str(rapport_path)

# === INTERFACE GRAPHIQUE (mode standalone) ===
def lancer_interface():
    root = Toplevel()
    root.title("👁️‍🗨️ Guard AME — Guérison de l’Âme")
    root.geometry("450x220")
    root.configure(bg='#1e1e1e')
    
    Label(root, text="Date naiss. (AAAA-MM-JJ):", bg='#1e1e1e', fg='white').pack(pady=5)
    ent_date = Entry(root, bg='#333', fg='white')
    ent_date.pack(); ent_date.insert(0, "1967-04-20")
    
    Label(root, text="Lieu (ex: Paris):", bg='#1e1e1e', fg='white').pack(pady=5)
    ent_lieu = Entry(root, bg='#333', fg='white')
    ent_lieu.pack(); ent_lieu.insert(0, "Paris")
    
    def on_genere():
        try:
            fichier, _ = generer_soin_ame(ent_date.get(), ent_lieu.get())
            messagebox.showinfo("✅ Succès", f"Soin généré !\n{fichier}")
        except Exception as e:
            messagebox.showerror("❌ Erreur", str(e))
    
    Button(root, text="🌀 Activer le Garde Âme", command=on_genere, bg="#2d5a2d", fg="white").pack(pady=15)
    root.transient()  # reste au premier plan

# === POINT D'ENTRÉE POUR KERBEROS ===
def start_guard():
    """Appelé automatiquement par Kerberos si présent dans guards_manifest.json"""
    print("[👁️‍🗨️] Guard AME chargé — prêt pour la guérison vibratoire.")
    return None  # pas de thread continu → activation manuelle via GUI

# === FONCTION D'EXÉCUTION DIRECTE (via bouton dans le panneau) ===
def run():
    """Appelé quand on clique sur le bouton 'Guard Ame' dans le panneau"""
    try:
        lancer_interface()
        return "✅ Interface Guard AME ouverte."
    except Exception as e:
        return f"❌ Erreur : {e}"