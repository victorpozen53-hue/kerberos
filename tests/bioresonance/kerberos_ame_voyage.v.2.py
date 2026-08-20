# -*- coding: utf-8 -*-
# ╔══════════════════════════════════════════════════════════════════════╗
# ║  KERBEROS v2.0 VOYAGE DE L'ÂME – Géolocalisation Ultra-Puissante   ║
# ║  GPLv3 modifiée – Victor Pozen 🐺                                   ║
# ║  ✅ Copier/coller + exports TXT/HTML dans le journal                ║
# ╚══════════════════════════════════════════════════════════════════════╝

import os
import sys
import json
import hashlib
import tkinter as tk
from tkinter import ttk, scrolledtext, messagebox
from datetime import datetime
from pathlib import Path
import threading
import webbrowser
import urllib.request
import urllib.parse
import socket

# === CONFIG FFmpeg ===
FFMPEG_DIR = Path(__file__).parent / "ffmpeg-8.0.1-essentials_build" / "bin"
if FFMPEG_DIR.exists():
    os.environ["PATH"] = str(FFMPEG_DIR) + os.pathsep + os.environ.get("PATH", "")

# Import conditionnel
HAS_AUDIO = False
try:
    from pydub import AudioSegment
    HAS_AUDIO = True
except ImportError:
    pass

HAS_PIL = False
try:
    from PIL import Image, ImageTk
    HAS_PIL = True
except ImportError:
    pass

try:
    import tkintermapview
    HAS_MAPVIEW = True
except ImportError:
    HAS_MAPVIEW = False

# === BRANCHEMENT DU CERVEAU ===
from brain.cortex import Cortex


# ═══════════════════════════════════════════════════════════════════════
# 🌍 GÉOCODAGE ULTRA-PUISSANT AVEC CACHE
# ═══════════════════════════════════════════════════════════════════════

class GeoCodageAvance:
    """Système de géocodage multi-sources avec cache intelligent"""
    
    def __init__(self, cache_dir="resources/geo_cache", mapquest_key=None):
        self.cache_dir = Path(cache_dir)
        self.cache_dir.mkdir(parents=True, exist_ok=True)
        self.cache_file = self.cache_dir / "geocache.json"
        self.cache = self._charger_cache()
        self.mapquest_key = mapquest_key
        
    def _charger_cache(self):
        if self.cache_file.exists():
            try:
                return json.loads(self.cache_file.read_text(encoding="utf-8"))
            except:
                return {}
        return {}
    
    def _sauver_cache(self):
        self.cache_file.write_text(json.dumps(self.cache, indent=2, ensure_ascii=False), encoding="utf-8")
    
    def _cache_key(self, adresse):
        return hashlib.md5(adresse.lower().encode()).hexdigest()
    
    def geocoder(self, adresse, log_callback=None):
        key = self._cache_key(adresse)
        if key in self.cache:
            if log_callback:
                log_callback(f"📦 Cache hit : {adresse}")
            return self.cache[key]
        
        resultats = []
        
        # 1. Nominatim (OpenStreetMap)
        try:
            r = self._geocode_nominatim(adresse)
            if r:
                resultats.append(r)
        except Exception as e:
            if log_callback:
                log_callback(f"⚠️ Nominatim : {e}")
        
        # 2. Photon (Komoot)
        try:
            r = self._geocode_photon(adresse)
            if r:
                resultats.append(r)
        except Exception as e:
            if log_callback:
                log_callback(f"⚠️ Photon : {e}")
        
        # 3. GeoNames
        try:
            r = self._geocode_geonames(adresse)
            if r:
                resultats.append(r)
        except Exception as e:
            if log_callback:
                log_callback(f"⚠️ GeoNames : {e}")
        
        # 4. MapQuest (uniquement si clé fournie)
        if self.mapquest_key:
            try:
                r = self._geocode_mapquest(adresse)
                if r:
                    resultats.append(r)
            except Exception as e:
                if log_callback:
                    log_callback(f"⚠️ MapQuest : {e}")
        
        if not resultats:
            raise Exception("Aucune API n'a pu géocoder cette adresse")
        
        if len(resultats) >= 2:
            resultat = self._trianguler(resultats, log_callback)
        else:
            resultat = resultats[0]
        
        self.cache[key] = resultat
        self._sauver_cache()
        return resultat
    
    def _geocode_nominatim(self, adresse):
        query = urllib.parse.quote(adresse)
        # ✅ URL CORRIGÉE : 0 espace après q=
        url = f"https://nominatim.openstreetmap.org/search?q={query}&format=json&limit=1&addressdetails=1"
        req = urllib.request.Request(url, headers={'User-Agent': 'Kerberos-v2.0'})
        with urllib.request.urlopen(req, timeout=5) as response:
            data = json.loads(response.read().decode('utf-8'))
            if data:  # ✅ Correction : condition complète
                return {
                    "source": "Nominatim",
                    "lat": float(data[0]['lat']),
                    "lon": float(data[0]['lon']),
                    "nom": data[0]['display_name'],
                    "score": 5 + int(float(data[0].get('importance', 0)) * 10)
                }
        return None
    
    def _geocode_photon(self, adresse):
        query = urllib.parse.quote(adresse)
        # ✅ URL CORRIGÉE : 0 espace après q=
        url = f"https://photon.komoot.io/api?q={query}&limit=1"
        with urllib.request.urlopen(url, timeout=5) as response:
            data = json.loads(response.read().decode('utf-8'))
            if data.get('features'):
                feature = data['features'][0]
                props = feature['properties']
                coords = feature['geometry']['coordinates']
                return {
                    "source": "Photon",
                    "lat": float(coords[1]),
                    "lon": float(coords[0]),
                    "nom": f"{props.get('name', '')}, {props.get('city', '')}",
                    "score": 4
                }
        return None
    
    def _geocode_geonames(self, adresse):
        query = urllib.parse.quote(adresse.split(',')[0])
        url = f"http://api.geonames.org/searchJSON?q={query}&maxRows=1&username=demo"  # ✅ username=demo (public)
        try:
            with urllib.request.urlopen(url, timeout=5) as response:
                data = json.loads(response.read().decode('utf-8'))
                if data.get('geonames'):
                    item = data['geonames'][0]
                    return {
                        "source": "GeoNames",
                        "lat": float(item['lat']),
                        "lon": float(item['lng']),
                        "nom": f"{item['name']}, {item.get('countryName', '')}",
                        "score": 3
                    }
        except:
            pass
        return None
    
    def _geocode_mapquest(self, adresse):
        if not self.mapquest_key:
            return None
        query = urllib.parse.quote(adresse)
        # ✅ URL CORRIGÉE : 0 espace après key=
        url = f"https://www.mapquestapi.com/geocoding/v1/address?key={self.mapquest_key}&location={query}&maxResults=1"
        with urllib.request.urlopen(url, timeout=5) as response:
            data = json.loads(response.read().decode('utf-8'))
            if data.get('results') and data['results'][0].get('locations'):
                loc = data['results'][0]['locations'][0]
                lat = loc['latLng']['lat']
                lon = loc['latLng']['lng']
                nom = f"{loc.get('street', '')}, {loc.get('adminArea5', '')}, {loc.get('adminArea1', '')}".strip(", ")
                return {
                    "source": "MapQuest",
                    "lat": float(lat),
                    "lon": float(lon),
                    "nom": nom,
                    "score": 2
                }
        return None
    
    def _trianguler(self, resultats, log_callback):
        total_score = sum(r['score'] for r in resultats)
        lat = sum(r['lat'] * r['score'] for r in resultats) / total_score
        lon = sum(r['lon'] * r['score'] for r in resultats) / total_score
        sources = " + ".join(r['source'] for r in resultats)
        if log_callback:
            log_callback(f"🎯 TRIANGULATION ({sources})")
            for r in resultats:
                log_callback(f"   • {r['source']}: {r['lat']:.5f}, {r['lon']:.5f} (score: {r['score']})")
            log_callback(f"   ➜ Résultat final: {lat:.5f}, {lon:.5f}")
        return {
            "source": f"Triangulation ({sources})",
            "lat": lat,
            "lon": lon,
            "nom": f"Triangulé depuis {len(resultats)} sources",
            "score": sum(r['score'] for r in resultats)
        }


# ═══════════════════════════════════════════════════════════════════════
# 🎨 INTERFACE PRINCIPALE
# ═══════════════════════════════════════════════════════════════════════

class PanelAmeFull:
    def __init__(self, root):
        self.root = root
        self.tracker = TrackerGuerison(self)
        self.cerveau = Cortex()

        root.title("👁️‍🗨️ KERBEROS v2.0 – Voyage de l'Âme 🌍")
        root.geometry("1200x800")
        root.configure(bg="#1e1e1e")
        root.protocol("WM_DELETE_WINDOW", self.quitter)

        self.internet_ok = self.verifier_internet()
        if not self.internet_ok:
            self.root.after(1000, lambda: messagebox.showwarning(
                "🌐 Réseau", "Mode hors-ligne activé.\nLe géocodage et le voyage de l'âme sont désactivés."
            ))

        root.update_idletasks()
        x = (root.winfo_screenwidth() // 2) - (1200 // 2)
        y = (root.winfo_screenheight() // 2) - (800 // 2)
        root.geometry(f"+{x}+{y}")

        style = ttk.Style()
        try:
            style.theme_use('clam')
        except:
            pass
        style.configure("TLabel", background="#1e1e1e", foreground="#e0e0e0", font=("Consolas", 10))
        style.configure("TButton", background="#2d5a2d", foreground="white", font=("Consolas", 10, "bold"), padding=6)
        style.map("TButton", background=[("active", "#3a7a3a"), ("disabled", "#444444")])

        # === FIX CRITIQUE POUR NOTEBOOK SOUS WINDOWS ===
        style.configure("TNotebook", background="#1e1e1e")
        style.configure("TNotebook.Tab", background="#2a2a2a", foreground="#e0e0e0")
        style.map("TNotebook.Tab",
                  background=[("selected", "#1e1e1e"), ("active", "#3a3a3a")],
                  foreground=[("selected", "#4fc3f7"), ("active", "#ffffff")])

        self._create_ui()
        self.maternites_data = []
        self.schemas_karmiques = self.charger_schemas_karmiques()
        self.ent_schema['values'] = [s["schema"] for s in self.schemas_karmiques]

        self.log_msg("═" * 60)
        self.log_msg("🌿 KERBEROS v2.0 – VOYAGE DE L'ÂME ACTIVÉ")
        self.log_msg(f"🌐 Réseau : {'ACTIF (3–4 APIs + Cache)' if self.internet_ok else 'HORS-LIGNE'}")
        self.log_msg("🌀 Fonctionne SANS MapQuest – optionnel uniquement")
        self.log_msg("⌨️ Tapez /help pour les commandes")
        self.log_msg("═" * 60)

    def _create_ui(self):
        left_frame = tk.Frame(self.root, bg="#1e1e1e", padx=15, pady=15)
        left_frame.pack(side="left", fill="y")

        tk.Label(left_frame, text="🌀 CONFIGURATION", bg="#1e1e1e", fg="#4CAF50",
                 font=("Consolas", 12, "bold")).pack(anchor="w", pady=(0, 15))

        tk.Label(left_frame, text="📅 Date naissance (AAAA-MM-JJ)", bg="#1e1e1e", fg="#e0e0e0").pack(anchor="w")
        self.ent_date = ttk.Entry(left_frame, width=28, font=("Consolas", 11))
        self.ent_date.insert(0, "1990-01-01")
        self.ent_date.pack(pady=(2, 10))

        tk.Label(left_frame, text="🕒 Heure naissance (HH:MM)", bg="#1e1e1e", fg="#e0e0e0").pack(anchor="w")
        self.ent_heure = ttk.Entry(left_frame, width=28, font=("Consolas", 11))
        self.ent_heure.insert(0, "12:00")
        self.ent_heure.pack(pady=(2, 15))

        tk.Label(left_frame, text="📍 Coordonnées", bg="#1e1e1e", fg="#e0e0e0").pack(anchor="w", pady=(10, 5))
        coord_frame = tk.Frame(left_frame, bg="#1e1e1e")
        coord_frame.pack(anchor="w")
        tk.Label(coord_frame, text="Lat :", bg="#1e1e1e", fg="#bbb", font=("Consolas", 9)).pack(side="left")
        self.ent_lat = ttk.Entry(coord_frame, width=12, font=("Consolas", 10))
        self.ent_lat.pack(side="left", padx=(0, 10))
        tk.Label(coord_frame, text="Lon :", bg="#1e1e1e", fg="#bbb", font=("Consolas", 9)).pack(side="left")
        self.ent_lon = ttk.Entry(coord_frame, width=12, font=("Consolas", 10))
        self.ent_lon.pack(side="left")

        tk.Label(left_frame, text="🌍 Lieu de naissance", bg="#1e1e1e", fg="#e0e0e0").pack(anchor="w", pady=(10, 2))
        self.ent_lieu = ttk.Entry(left_frame, width=28, font=("Consolas", 11))
        self.ent_lieu.pack(pady=(2, 10))
        if self.internet_ok:
            self.ent_lieu.bind("<KeyRelease>", self.auto_geocode)

        tk.Label(left_frame, text="👤 Nom (optionnel)", bg="#1e1e1e", fg="#e0e0e0").pack(anchor="w")
        self.ent_nom = ttk.Entry(left_frame, width=28, font=("Consolas", 11))
        self.ent_nom.pack(pady=(2, 15))

        tk.Label(left_frame, text="🌀 Schéma karmique", bg="#1e1e1e", fg="#e0e0e0").pack(anchor="w")
        self.ent_schema = ttk.Combobox(left_frame, width=26, font=("Consolas", 10))
        self.ent_schema.pack(pady=(2, 15))

        # === CONTRÔLE SCHUMANN ===
        self.schumann_var = tk.BooleanVar(value=True)
        schumann_frame = tk.Frame(left_frame, bg="#1e1e1e")
        schumann_frame.pack(anchor="w", pady=(5, 15))
        tk.Label(schumann_frame, text="🔊 Fréquence de Schumann (7.83 Hz)", bg="#1e1e1e", fg="#e0e0e0", font=("Consolas", 9)).pack(side="left")
        self.chk_schumann = tk.Checkbutton(
            schumann_frame,
            variable=self.schumann_var,
            bg="#1e1e1e",
            fg="#4CAF50",
            selectcolor="#1e1e1e",
            activebackground="#1e1e1e",
            activeforeground="#4CAF50"
        )
        self.chk_schumann.pack(side="left", padx=(5, 0))
        tk.Label(schumann_frame, text="⚠️ Désactivez si antécédent neurologique", bg="#1e1e1e", fg="#ff9800", font=("Consolas", 7)).pack(anchor="w", padx=(0, 0), pady=(2, 0))

        # === OPTIONS AVANCÉES ===
        ttk.Separator(left_frame, orient='horizontal').pack(fill='x', pady=10)
        tk.Label(left_frame, text="⚙️ OPTIONS AVANCÉES", bg="#1e1e1e", fg="#2196F3",
                 font=("Consolas", 11, "bold")).pack(anchor="w", pady=(5, 10))

        # Origine cosmique
        self.origine_cosmique_var = tk.BooleanVar(value=True)
        origine_frame = tk.Frame(left_frame, bg="#1e1e1e")
        origine_frame.pack(anchor="w", pady=2)
        tk.Checkbutton(origine_frame, text="Inclure l’Origine Cosmique (Source Unitaire)",
                       variable=self.origine_cosmique_var,
                       bg="#1e1e1e", fg="#BB86FC", selectcolor="#1e1e1e").pack(anchor="w")

        # Humour sacré
        self.humour_sacre_var = tk.BooleanVar(value=True)
        humour_frame = tk.Frame(left_frame, bg="#1e1e1e")
        humour_frame.pack(anchor="w", pady=2)
        tk.Checkbutton(humour_frame, text="Mode Humour Sacré (alléger le karma)",
                       variable=self.humour_sacre_var,
                       bg="#1e1e1e", fg="#03DAC6", selectcolor="#1e1e1e").pack(anchor="w")

        # Mode lignée
        self.mode_lignee_var = tk.BooleanVar(value=False)
        lignee_frame = tk.Frame(left_frame, bg="#1e1e1e")
        lignee_frame.pack(anchor="w", pady=2)
        tk.Checkbutton(lignee_frame, text="Mode Lignée Historique (vs résonance actuelle)",
                       variable=self.mode_lignee_var,
                       bg="#1e1e1e", fg="#CF6679", selectcolor="#1e1e1e").pack(anchor="w")

        ttk.Separator(left_frame, orient='horizontal').pack(fill='x', pady=10)
        tk.Label(left_frame, text="🌀 VOYAGE DE L'ÂME", bg="#1e1e1e", fg="#9c27b0",
                 font=("Consolas", 11, "bold")).pack(anchor="w", pady=(5, 10))

        btn_voyage = ttk.Button(left_frame, text="🌍 CALCULER INCARNATIONS PASSÉES", command=self.calculer_voyage_ame)
        btn_voyage.pack(pady=5, ipadx=10, ipady=5)

        ttk.Separator(left_frame, orient='horizontal').pack(fill='x', pady=10)
        self.btn_gen = ttk.Button(left_frame, text="🌀 GÉNÉRER LE SOIN", command=self.lancer_generation)
        self.btn_gen.pack(pady=15, ipadx=15, ipady=5)

        # PANNEAU DROIT – ONGLETS
        right_frame = tk.Frame(self.root, bg="#1e1e1e", padx=10, pady=15)
        right_frame.pack(side="right", fill="both", expand=True)
        
        notebook = ttk.Notebook(right_frame)
        notebook.pack(fill="both", expand=True)
        
        tab_journal = tk.Frame(notebook, bg="#1e1e1e")
        tab_voyage = tk.Frame(notebook, bg="#1e1e1e")
        tab_carte = tk.Frame(notebook, bg="#1e1e1e")
        tab_mapquest = tk.Frame(notebook, bg="#1e1e1e")
        
        notebook.add(tab_journal, text="📜 Journal")
        notebook.add(tab_voyage, text="🌀 Voyage Âme")
        notebook.add(tab_carte, text="🌍 Carte")
        notebook.add(tab_mapquest, text="🔑 MapQuest (opt.)")

        # Onglet Journal - AVEC BARRE D'OUTILS
        tk.Label(tab_journal, text="📜 JOURNAL", bg="#1e1e1e", fg="#4CAF50", 
                 font=("Consolas", 12, "bold")).pack(anchor="w", pady=(0, 5))
        
        # Barre d'outils export
        btn_frame = tk.Frame(tab_journal, bg="#1e1e1e")
        btn_frame.pack(fill="x", pady=(0, 5))
        ttk.Button(btn_frame, text="📋 COPIER TOUT", command=self.copier_journal, width=12).pack(side="left", padx=2)
        ttk.Button(btn_frame, text="💾 TXT", command=self.exporter_journal_txt, width=8).pack(side="left", padx=2)
        ttk.Button(btn_frame, text="🌐 HTML", command=self.exporter_journal_html, width=8).pack(side="left", padx=2)
        ttk.Button(btn_frame, text="🗑️ VIDER", command=self.vider_journal, width=8).pack(side="right", padx=2)

        self.log = scrolledtext.ScrolledText(tab_journal, wrap=tk.WORD, font=("Consolas", 9), 
                                             bg="#0a0a0a", fg="#00ff00")
        self.log.pack(fill="both", expand=True)

        # Onglet Voyage Âme
        tk.Label(tab_voyage, text="🌀 INCARNATIONS PASSÉES", bg="#1e1e1e", fg="#9c27b0",
                 font=("Consolas", 12, "bold")).pack(anchor="w", pady=(0, 8))
        self.voyage_text = scrolledtext.ScrolledText(tab_voyage, wrap=tk.WORD, font=("Consolas", 9),
                                                     bg="#0a0a0a", fg="#ce93d8")
        self.voyage_text.pack(fill="both", expand=True, pady=(0, 10))
        ttk.Button(tab_voyage, text="💾 Exporter rapport HTML", command=self.exporter_rapport_voyage).pack(pady=5)

        # Onglet Carte
        ttk.Button(tab_carte, text="🗺️ Afficher Carte des Vies", command=self.afficher_carte_vies).pack(pady=10)
        self.canvas_carte = tk.Frame(tab_carte, bg="#0a0a0a", highlightthickness=1, highlightbackground="#4fc3f7")
        self.canvas_carte.pack(fill="both", expand=True, padx=10, pady=10)

        # Onglet MapQuest
        tk.Label(tab_mapquest, text="🌍 MAPQUEST – GÉOCODAGE OPTIONNEL", bg="#1e1e1e", fg="#ff9800",
                 font=("Consolas", 12, "bold")).pack(anchor="w", pady=(10, 15))
        info_text = (
            "MapQuest est une API de géocodage supplémentaire (max 15 000 requêtes/mois).\n"
            "⚠️ Elle nécessite une clé API gratuite, mais MapQuest exige une carte bancaire.\n\n"
            "✅ KERBEROS FONCTIONNE PARFAITEMENT SANS MAPQUEST !\n"
            "Les 3 autres sources (Nominatim, Photon, GeoNames) sont suffisantes.\n\n"
            "→ Si vous possédez une clé MapQuest, collez-la ci-dessous :"
        )
        tk.Label(tab_mapquest, text=info_text, bg="#1e1e1e", fg="#bbb",
                 font=("Consolas", 9), justify="left", wraplength=600).pack(anchor="w", padx=15)
        self.ent_mapquest_key = ttk.Entry(tab_mapquest, width=50, font=("Consolas", 10), show="•")
        self.ent_mapquest_key.pack(pady=10, padx=15)
        self.ent_mapquest_key.insert(0, "collez_votre_clé_ici_ou_laissez_vide")
        self.ent_mapquest_key.bind("<FocusIn>", self._effacer_placeholder_mapquest)
        ttk.Button(tab_mapquest, text="🧪 Tester la clé", command=self._tester_mapquest).pack(pady=5)

        self._gps_timer = None
        self.threads_actives = []

    def _effacer_placeholder_mapquest(self, event=None):
        if self.ent_mapquest_key.get() == "collez_votre_clé_ici_ou_laissez_vide":
            self.ent_mapquest_key.delete(0, tk.END)
            self.ent_mapquest_key.config(show="•")

    def _get_mapquest_key(self):
        key = self.ent_mapquest_key.get().strip()
        if key and key != "collez_votre_clé_ici_ou_laissez_vide":
            return key
        return None

    def _tester_mapquest(self):
        key = self._get_mapquest_key()
        if not key:
            messagebox.showwarning("⚠️ Clé manquante", "Veuillez entrer une clé MapQuest.")
            return
        try:
            # ✅ URL CORRIGÉE : 0 espace après key=
            url = f"https://www.mapquestapi.com/geocoding/v1/address?key={key}&location=Paris&maxResults=1"
            with urllib.request.urlopen(url, timeout=5) as response:
                data = json.loads(response.read().decode('utf-8'))
                if data.get('results'):
                    messagebox.showinfo("✅ Succès", "La clé MapQuest est valide !\nElle sera utilisée lors du géocodage.")
                else:
                    raise Exception("Réponse invalide")
        except Exception as e:
            messagebox.showerror("❌ Échec", f"Clé invalide ou erreur :\n{e}")

    def auto_geocode(self, event=None):
        if not self.ent_lieu.get().strip() or len(self.ent_lieu.get().strip()) < 3:
            return
        if hasattr(self, '_gps_timer') and self._gps_timer:
            self._gps_timer.cancel()
        self._gps_timer = threading.Timer(1.5, self._geocode_thread)
        self._gps_timer.start()
    
    def _geocode_thread(self):
        adresse = self.ent_lieu.get().strip()
        if not adresse:
            return
        mapquest_key = self._get_mapquest_key()
        geocodeur = GeoCodageAvance(mapquest_key=mapquest_key)
        try:
            resultat = geocodeur.geocoder(adresse, log_callback=self.log_msg)
            self.root.after(0, lambda: self.ent_lat.delete(0, tk.END))
            self.root.after(0, lambda: self.ent_lat.insert(0, f"{resultat['lat']:.5f}"))
            self.root.after(0, lambda: self.ent_lon.delete(0, tk.END))
            self.root.after(0, lambda: self.ent_lon.insert(0, f"{resultat['lon']:.5f}"))
        except Exception as e:
            self.root.after(0, lambda: self.log_msg(f"❌ Géocodage : {e}"))
    
    def calculer_voyage_ame(self):
        try:
            lat_str = self.ent_lat.get().strip()
            lon_str = self.ent_lon.get().strip()
            if not lat_str or not lon_str:
                messagebox.showerror("❌ Erreur", "Coordonnées manquantes. Patientez après géocodage.")
                return

            donnees = {
                "date_naissance": self.ent_date.get().strip(),
                "latitude": float(lat_str),
                "longitude": float(lon_str),
                "utiliser_schumann": self.schumann_var.get(),
                "inclure_origine": self.origine_cosmique_var.get(),
                "mode_lignee": self.mode_lignee_var.get(),
                "humour_sacre": self.humour_sacre_var.get()
            }
            rapport = self.cerveau.initier_voyage_de_l_ame(donnees)
            incarnations = rapport["incarnations"]
            patterns = rapport["etat_ame"]

            self.voyage_text.delete(1.0, tk.END)
            self.voyage_text.insert(tk.END, "═" * 70 + "\n")
            self.voyage_text.insert(tk.END, "        🌀 VOYAGE DE TON ÂME À TRAVERS LES SIÈCLES\n")
            self.voyage_text.insert(tk.END, "═" * 70 + "\n\n")
            for inc in incarnations:
                type_ame = inc["type_ame"]
                emoji = self._emoji_par_type_ame(type_ame)
                self.voyage_text.insert(tk.END, f"\n{emoji} VIE #{inc['numero']} — {type_ame.upper()}\n")
                self.voyage_text.insert(tk.END, f"{'─' * 70}\n")
                self.voyage_text.insert(tk.END, f"📅 Époque : {inc['epoque']} (vers {inc['annee']})\n")
                self.voyage_text.insert(tk.END, f"📍 Lieu : {inc['latitude']:.2f}°, {inc['longitude']:.2f}°\n")
                self.voyage_text.insert(tk.END, f"📏 Distance actuelle : {inc['distance_actuelle_km']:.0f} km\n")
                self.voyage_text.insert(tk.END, f"🎯 Leçon karmique : {inc['lecon_karmique']}\n")
            self.voyage_text.insert(tk.END, "\n\n" + "═" * 70 + "\n")
            self.voyage_text.insert(tk.END, "        📊 ANALYSE KARMIQUE GLOBALE\n")
            self.voyage_text.insert(tk.END, "═" * 70 + "\n")
            self.voyage_text.insert(tk.END, f"🧠 État de l’âme : {'⚠️ Guérison nécessaire' if patterns['besoin_guerison'] else '💚 En harmonie'}\n")

            # Option Humour Sacré
            if self.humour_sacre_var.get() and any("pouvoir absolu" in inc.get("lecon_karmique", "") for inc in incarnations):
                self.voyage_text.insert(tk.END, "\n🎭 PS : Si tu ressens une envie soudaine de nommer un cheval sénateur… respire. L’âme a évolué. 🐴\n")

            self.log_msg("✅ Voyage de l'âme calculé par le cerveau neuronal")
            messagebox.showinfo("🧠 Cerveau", "Voyage de l’âme activé par le cerveau Kerberos !")

        except Exception as e:
            messagebox.showerror("❌ Erreur Cerveau", str(e))
            self.log_msg(f"Erreur cerveau : {e}")
    
    def afficher_carte_vies(self):
        if not HAS_MAPVIEW:
            messagebox.showerror("❌ Carte", "tkintermapview requis :\npip install tkintermapview")
            return
        try:
            lat = float(self.ent_lat.get().strip())
            lon = float(self.ent_lon.get().strip())
            date_str = self.ent_date.get().strip()
            donnees = {
                "date_naissance": date_str,
                "latitude": lat,
                "longitude": lon,
                "utiliser_schumann": self.schumann_var.get(),
                "inclure_origine": self.origine_cosmique_var.get(),
                "mode_lignee": self.mode_lignee_var.get()
            }
            rapport = self.cerveau.initier_voyage_de_l_ame(donnees)
            incarnations = rapport["incarnations"]
        except Exception as e:
            messagebox.showerror("❌ Carte", f"Impossible de charger les incarnations :\n{e}")
            return

        for widget in self.canvas_carte.winfo_children():
            widget.destroy()
        map_widget = tkintermapview.TkinterMapView(self.canvas_carte, corner_radius=0)
        map_widget.pack(fill="both", expand=True)
        map_widget.set_position(lat, lon)
        map_widget.set_zoom(4)
        map_widget.set_marker(
            lat, lon,
            text="🌟 VIE ACTUELLE",
            marker_color_circle="gold",
            marker_color_outside="orange"
        )
        for inc in incarnations:
            type_ame = inc["type_ame"]
            emoji = self._emoji_par_type_ame(type_ame)
            couleur = self._couleur_par_type(type_ame)
            map_widget.set_marker(
                inc['latitude'],
                inc['longitude'],
                text=f"{emoji} Vie #{inc['numero']}\n{type_ame}\n{inc['epoque']}",
                marker_color_circle=couleur,
                marker_color_outside="black"
            )
        self.log_msg("🗺️ Carte des vies affichée")
    
    def exporter_rapport_voyage(self):
        try:
            lat = float(self.ent_lat.get().strip())
            lon = float(self.ent_lon.get().strip())
            date_str = self.ent_date.get().strip()
            donnees = {
                "date_naissance": date_str,
                "latitude": lat,
                "longitude": lon,
                "utiliser_schumann": self.schumann_var.get(),
                "inclure_origine": self.origine_cosmique_var.get(),
                "mode_lignee": self.mode_lignee_var.get()
            }
            rapport = self.cerveau.initier_voyage_de_l_ame(donnees)
            incarnations = rapport["incarnations"]
        except Exception as e:
            messagebox.showwarning("⚠️ Export", f"Impossible de générer le rapport :\n{e}")
            return

        html = f'''<!DOCTYPE html>
<html lang="fr">
<head>
<meta charset="UTF-8">
<title>Voyage de l'Âme</title>
<style>
body{{background:linear-gradient(135deg,#1a0033 0%,#2d004d 100%);color:#e1bee7;font-family:Consolas,monospace;padding:30px}}
.container{{max-width:1000px;margin:0 auto;background:rgba(74,20,140,0.3);padding:40px;border-radius:20px}}
h1{{text-align:center;color:#ce93d8;font-size:32px}}
.incarnation{{background:rgba(123,31,162,0.2);margin:20px 0;padding:20px;border-left:5px solid;border-radius:10px}}
.patterns{{background:rgba(233,30,99,0.2);padding:20px;margin-top:30px;border-radius:10px}}
</style>
</head>
<body>
<div class="container">
<h1>🌀 VOYAGE DE TON ÂME À TRAVERS LES SIÈCLES</h1>
'''
        for inc in incarnations:
            type_ame = inc["type_ame"]
            emoji = self._emoji_par_type_ame(type_ame)
            couleur = self._couleur_par_type(type_ame)
            html += f'''<div class="incarnation" style="border-color:{couleur}">
<h2>{emoji} Vie #{inc['numero']} — {type_ame}</h2>
<p><b>Époque :</b> {inc['epoque']} (vers {inc['annee']})</p>
<p><b>Localisation :</b> {inc['latitude']:.2f}°, {inc['longitude']:.2f}°</p>
<p><b>Distance actuelle :</b> {inc['distance_actuelle_km']:.0f} km</p>
<p><b>Leçon karmique :</b> {inc['lecon_karmique']}</p>
</div>'''
        html += f'''<div class="patterns">
<h2>📊 Analyse Karmique Globale</h2>
<p><b>État de l’âme :</b> {'⚠️ Guérison nécessaire' if rapport['etat_ame']['besoin_guerison'] else '💚 En harmonie'}</p>
'''
        # Humour sacré dans HTML
        if self.humour_sacre_var.get() and any("pouvoir absolu" in inc.get("lecon_karmique", "") for inc in incarnations):
            html += '<p style="font-style:italic; color:#03DAC6;">🎭 PS : Si tu ressens une envie soudaine de nommer un cheval sénateur… respire. L’âme a évolué. 🐴</p>'
        html += '</div></div></body></html>'

        chemin = Path("soins_vibratoires") / f"voyage_ame_{datetime.now().strftime('%Y%m%d_%H%M')}.html"
        chemin.parent.mkdir(exist_ok=True)
        chemin.write_text(html, encoding="utf-8")
        webbrowser.open(chemin.absolute().as_uri())
        self.log_msg(f"💾 Rapport exporté : {chemin.name}")

    def lancer_generation(self):
        messagebox.showinfo("Info", "Génération du soin non implémentée dans ce code minimal")
    
    def charger_schemas_karmiques(self):
        return []
    
    def log_msg(self, msg):
        try:
            timestamp = datetime.now().strftime('%H:%M:%S')
            self.log.insert(tk.END, f"[{timestamp}] {msg}\n")
            self.log.see(tk.END)
        except:
            pass
    
    def verifier_internet(self):
        try:
            socket.create_connection(("8.8.8.8", 53), timeout=2)
            return True
        except:
            return False
    
    def quitter(self):
        if hasattr(self, '_gps_timer') and self._gps_timer:
            self._gps_timer.cancel()
        self.root.destroy()

    # === MÉTHODES AJOUTÉES POUR LE JOURNAL ===
    def copier_journal(self):
        contenu = self.log.get("1.0", tk.END).strip()
        if contenu:
            self.root.clipboard_clear()
            self.root.clipboard_append(contenu)
            self.log_msg("📋 Journal copié")
            messagebox.showinfo("📋 Copié", "✓ Contenu copié dans le presse-papiers")
        else:
            messagebox.showwarning("⚠️ Vide", "Le journal est vide.")

    def exporter_journal_txt(self):
        contenu = self.log.get("1.0", tk.END).strip()
        if not contenu:
            messagebox.showwarning("⚠️ Vide", "Le journal est vide.")
            return
        chemin = Path("soins_vibratoires") / f"journal_{datetime.now().strftime('%Y%m%d_%H%M%S')}.txt"
        chemin.parent.mkdir(exist_ok=True)
        chemin.write_text(contenu, encoding="utf-8")
        self.log_msg(f"💾 Exporté : {chemin.name}")
        messagebox.showinfo("✅ TXT", f"Sauvegardé :\n{chemin.name}")

    def exporter_journal_html(self):
        contenu = self.log.get("1.0", tk.END).strip()
        if not contenu:
            messagebox.showwarning("⚠️ Vide", "Le journal est vide.")
            return
        
        html = f'''<!DOCTYPE html>
<html lang="fr">
<head>
<meta charset="UTF-8">
<title>Journal Kerberos</title>
<style>
body {{ background:#0a0a1a; color:#00ff9d; font-family:Consolas,monospace; padding:30px; }}
h1 {{ text-align:center; color:#bb86fc; }}
.entry {{ margin:8px 0; padding-left:10px; border-left:3px solid #4fc3f7; }}
.timestamp {{ color:#ff9800; }}
</style>
</head>
<body>
<h1>👁️‍🗨️ JOURNAL KERBEROS v2.0</h1>
'''
        for ligne in contenu.split('\n'):
            if ligne.strip():
                html += f'<div class="entry">{self._echapper_html(ligne)}</div>\n'
        html += '</body></html>'
        
        chemin = Path("soins_vibratoires") / f"journal_{datetime.now().strftime('%Y%m%d_%H%M%S')}.html"
        chemin.parent.mkdir(exist_ok=True)
        chemin.write_text(html, encoding="utf-8")
        webbrowser.open(chemin.absolute().as_uri())
        self.log_msg(f"🌐 HTML ouvert : {chemin.name}")

    def vider_journal(self):
        if messagebox.askyesno("🗑️ Vider", "Effacer tout le journal ?"):
            self.log.delete("1.0", tk.END)
            self.log_msg("🧹 Journal vidé")

    def _echapper_html(self, texte):
        return (texte.replace('&', '&amp;')
                    .replace('<', '&lt;')
                    .replace('>', '&gt;'))


class TrackerGuerison:
    def __init__(self, panel):
        self.panel = panel


def main():
    root = tk.Tk()
    app = PanelAmeFull(root)
    root.mainloop()


if __name__ == "__main__":
    main()