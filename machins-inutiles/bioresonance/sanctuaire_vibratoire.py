# sanctuaire_vibratoire.py
# -*- coding: utf-8 -*-
# GPLv3 – Sanctuaire Vibratoire / Projet Kerberos
# Auteur : Victor Pozen – White hat • Anonymous • Résistant numérique (-;

import os
import hashlib
import tkinter as tk
from tkinter import ttk, scrolledtext, messagebox
from datetime import datetime, timedelta
from pathlib import Path
import math
import threading
import webbrowser
from math import radians, sin, cos, sqrt, atan2

# === CONFIG FFmpeg ===
FFMPEG_DIR = Path(__file__).parent / "ffmpeg-8.0.1-essentials_build" / "bin"
FFMPEG_EXE = FFMPEG_DIR / "ffmpeg.exe"

if FFMPEG_DIR.exists():
    os.environ["PATH"] = str(FFMPEG_DIR) + os.pathsep + os.environ.get("PATH", "")

# Import conditionnel
HAS_AUDIO = False
try:
    from pydub import AudioSegment
    from pydub.generators import Sine
    HAS_AUDIO = True
except ImportError:
    print("⚠️ pydub non installé - mode simulation activé")

class SanctuaireVibratoire:
    def __init__(self, root):
        self.root = root
        root.title("👁️‍🗨️ SANCTUAIRE VIBRATOIRE – Projet Kerberos")
        root.geometry("880x660")
        root.configure(bg="#1e1e1e")
        
        # Centrer
        root.update_idletasks()
        x = (root.winfo_screenwidth() // 2) - (880 // 2)
        y = (root.winfo_screenheight() // 2) - (660 // 2)
        root.geometry(f"+{x}+{y}")

        style = ttk.Style()
        style.theme_use('clam')
        style.configure("TLabel", background="#1e1e1e", foreground="#e0e0e0", font=("Consolas", 10))
        style.configure("TButton", background="#2d5a2d", foreground="white", font=("Consolas", 10, "bold"), padding=6)

        # === PANNEAU GAUCHE ===
        left_frame = tk.Frame(root, bg="#1e1e1e", padx=15, pady=15)
        left_frame.pack(side="left", fill="y")

        tk.Label(left_frame, text="🌀 CONFIGURATION", bg="#1e1e1e", fg="#4CAF50", 
                font=("Consolas", 12, "bold")).pack(anchor="w", pady=(0,15))

        # Date + Heure
        tk.Label(left_frame, text="📅 Date naissance (AAAA-MM-JJ)", bg="#1e1e1e", fg="#e0e0e0").pack(anchor="w")
        self.ent_date = ttk.Entry(left_frame, width=28, font=("Consolas", 11))
        self.ent_date.pack(pady=(2,10))
        self.ent_date.insert(0, "1967-04-20")
        self._create_context_menu(self.ent_date)

        tk.Label(left_frame, text="🕒 Heure naissance (HH:MM)", bg="#1e1e1e", fg="#e0e0e0").pack(anchor="w")
        self.ent_heure = ttk.Entry(left_frame, width=28, font=("Consolas", 11))
        self.ent_heure.pack(pady=(2,15))
        self.ent_heure.insert(0, "14:30")
        self._create_context_menu(self.ent_heure)

        # Sélection par thème
        tk.Label(left_frame, text="🌍 Pays", bg="#1e1e1e", fg="#e0e0e0").pack(anchor="w")
        self.combo_pays = ttk.Combobox(left_frame, width=26, font=("Consolas", 10))
        self.combo_pays.pack(pady=(2,8))
        self.combo_pays.bind("<<ComboboxSelected>>", self.on_pays_select)

        tk.Label(left_frame, text="🌀 Thème", bg="#1e1e1e", fg="#e0e0e0").pack(anchor="w")
        self.combo_theme = ttk.Combobox(left_frame, width=26, font=("Consolas", 10))
        self.combo_theme.pack(pady=(2,8))
        self.combo_theme.bind("<<ComboboxSelected>>", self.on_theme_select)

        tk.Label(left_frame, text="⛩️ Lieu sacré", bg="#1e1e1e", fg="#e0e0e0").pack(anchor="w")
        self.combo_lieu = ttk.Combobox(left_frame, width=26, font=("Consolas", 10))
        self.combo_lieu.pack(pady=(2,15))
        self.combo_lieu.bind("<<ComboboxSelected>>", self.on_lieu_select)

        # Coordonnées manuelles (fallback)
        coord_frame = tk.Frame(left_frame, bg="#1e1e1e")
        coord_frame.pack(anchor="w")
        tk.Label(coord_frame, text="Lat :", bg="#1e1e1e", fg="#bbb", font=("Consolas", 9)).pack(side="left")
        self.ent_lat = ttk.Entry(coord_frame, width=12, font=("Consolas", 10))
        self.ent_lat.pack(side="left", padx=(0,10))
        self.ent_lat.insert(0, "48.8566")
        self._create_context_menu(self.ent_lat)
        tk.Label(coord_frame, text="Lon :", bg="#1e1e1e", fg="#bbb", font=("Consolas", 9)).pack(side="left")
        self.ent_lon = ttk.Entry(coord_frame, width=12, font=("Consolas", 10))
        self.ent_lon.pack(side="left")
        self.ent_lon.insert(0, "2.3522")
        self._create_context_menu(self.ent_lon)

        # Nom
        tk.Label(left_frame, text="👤 Nom/Prénom (optionnel)", bg="#1e1e1e", fg="#e0e0e0").pack(anchor="w")
        self.ent_nom = ttk.Entry(left_frame, width=28, font=("Consolas", 11))
        self.ent_nom.pack(pady=(2,15))
        self._create_context_menu(self.ent_nom)

        # Boutons
        btn_carte = ttk.Button(left_frame, text="🌍 Voir sur la carte", command=self.ouvrir_carte_lieu)
        btn_carte.pack(pady=(0,10))

        # Options
        ttk.Separator(left_frame, orient='horizontal').pack(fill='x', pady=10)
        tk.Label(left_frame, text="⚙️ OPTIONS", bg="#1e1e1e", fg="#4CAF50", font=("Consolas", 11, "bold")).pack(anchor="w", pady=(5,10))
        self.var_ultrason = tk.BooleanVar(value=True)
        tk.Checkbutton(left_frame, text="🔊 Ultrasons (25 kHz)", variable=self.var_ultrason, bg="#1e1e1e", fg="white", selectcolor="#333").pack(anchor="w")
        self.var_harmoniques = tk.BooleanVar(value=False)
        tk.Checkbutton(left_frame, text="🎵 Harmoniques renforcées", variable=self.var_harmoniques, bg="#1e1e1e", fg="white", selectcolor="#333").pack(anchor="w")
        self.var_ouvrir_auto = tk.BooleanVar(value=True)
        tk.Checkbutton(left_frame, text="📂 Ouvrir fichiers après génération", variable=self.var_ouvrir_auto, bg="#1e1e1e", fg="white", selectcolor="#333").pack(anchor="w")

        # Bouton principal
        self.btn_gen = ttk.Button(left_frame, text="🌀 GÉNÉRER LE SANCTUAIRE", command=self.lancer_generation)
        self.btn_gen.pack(pady=20, ipadx=15, ipady=5)

        # Statut
        ttk.Separator(left_frame, orient='horizontal').pack(fill='x', pady=10)
        tk.Label(left_frame, text="📊 STATUT", bg="#1e1e1e", fg="#4CAF50", font=("Consolas", 10, "bold")).pack(anchor="w", pady=(5,8))
        statut_ffmpeg = "✅ FFmpeg OK" if FFMPEG_EXE.exists() else "❌ FFmpeg manquant"
        fg_ffmpeg = "#0f0" if FFMPEG_EXE.exists() else "#f00"
        tk.Label(left_frame, text=statut_ffmpeg, bg="#1e1e1e", fg=fg_ffmpeg, font=("Consolas", 9)).pack(anchor="w")
        statut_pydub = "✅ Pydub OK" if HAS_AUDIO else "⚠️ Pydub manquant"
        fg_pydub = "#0f0" if HAS_AUDIO else "#ff9800"
        tk.Label(left_frame, text=statut_pydub, bg="#1e1e1e", fg=fg_pydub, font=("Consolas", 9)).pack(anchor="w")

        # === PANNEAU DROIT ===
        right_frame = tk.Frame(root, bg="#1e1e1e", padx=10, pady=15)
        right_frame.pack(side="right", fill="both", expand=True)
        tk.Label(right_frame, text="📜 JOURNAL DU SANCTUAIRE", bg="#1e1e1e", fg="#4CAF50", font=("Consolas", 12, "bold")).pack(anchor="w", pady=(0,8))
        self.log = scrolledtext.ScrolledText(right_frame, wrap=tk.WORD, font=("Consolas", 9), bg="#0a0a0a", fg="#00ff00", state="disabled")
        self.log.pack(fill="both", expand=True, pady=(0,12))
        self.progress_canvas = tk.Canvas(right_frame, height=20, bg="#0a0a0a", highlightthickness=0)
        self.progress_canvas.pack(fill="x", pady=(0,5))
        self.progress_rect = self.progress_canvas.create_rectangle(0, 0, 0, 20, fill="#4fc3f7", outline="")
        self.lbl_progress = tk.Label(right_frame, text="En attente...", bg="#1e1e1e", fg="#888", font=("Consolas", 9))
        self.lbl_progress.pack()

        self.log_msg("═" * 50)
        self.log_msg("🌿 SANCTUAIRE VIBRATOIRE – Projet Kerberos")
        self.log_msg("═" * 50)

        # Charger les lieux
        self.charger_lieux_par_theme()

    def _create_context_menu(self, widget):
        menu = tk.Menu(widget, tearoff=0, bg="#2d2d2d", fg="white", font=("Consolas", 9))
        menu.add_command(label="Couper", command=lambda: widget.event_generate("<<Cut>>"))
        menu.add_command(label="Copier", command=lambda: widget.event_generate("<<Copy>>"))
        menu.add_command(label="Coller", command=lambda: widget.event_generate("<<Paste>>"))
        menu.add_separator()
        menu.add_command(label="Tout sélectionner", command=lambda: widget.select_range(0, 'end'))
        def show_menu(e): menu.tk_popup(e.x_root, e.y_root)
        widget.bind("<Button-3>", show_menu)

    def charger_lieux_par_theme(self):
        chemin = Path("resources/lieux_sacres_themes.csv")
        if not chemin.exists():
            chemin.parent.mkdir(exist_ok=True)
            exemple = '''pays,theme,nom_païen,nom_chretien,latitude,longitude,energie,description
France,Fontaines sacrées,Fontaine de Barenton,Chapelle Saint-Éloi,48.0725,-2.9317,calmante,"Lieu druidique – Merlin y rencontra Viviane"
France,Montagnes sacrées,Mont Saint-Michel,,48.6361,-1.5115,puissante,"Ancien sanctuaire dédié à Belenos"
Belgique,Sources sacrées,Source de Bruxelles,Église Sainte-Gudule,50.8450,4.3500,calmante,"Source sacrée sous la cathédrale"
Turquie,Temples néolithiques,Göbekli Tepe,,37.2233,38.9111,neutre,"Premier lieu de pause du corps – 9600 av. J.-C."
USA,Vortex,Sedona,,34.8697,-111.7610,puissante,"Vortex d’élévation mentale – roches rouges"'''
            chemin.write_text(exemple, encoding="utf-8")

        self.lieux_data = []
        self.pays_themes = {}
        try:
            with open(chemin, encoding="utf-8") as f:
                lignes = f.readlines()
                for ligne in lignes[1:]:
                    p = ligne.strip().split(",", 7)
                    if len(p) >= 8:
                        pays, theme, nom_paien, nom_chretien, lat, lon, energie, desc = p
                        lieu = {
                            "pays": pays,
                            "theme": theme,
                            "nom_païen": nom_paien,
                            "nom_chretien": nom_chretien,
                            "lat": float(lat),
                            "lon": float(lon),
                            "energie": energie,
                            "description": desc
                        }
                        self.lieux_data.append(lieu)
                        if pays not in self.pays_themes:
                            self.pays_themes[pays] = set()
                        self.pays_themes[pays].add(theme)
        except Exception as e:
            self.log_msg(f"⚠️ Erreur chargement lieux : {e}")

        self.combo_pays['values'] = sorted(self.pays_themes.keys())

    def on_pays_select(self, event=None):
        pays = self.combo_pays.get()
        themes = sorted(self.pays_themes.get(pays, []))
        self.combo_theme['values'] = themes
        self.combo_theme.set("")
        self.combo_lieu['values'] = []
        self.combo_lieu.set("")

    def on_theme_select(self, event=None):
        pays = self.combo_pays.get()
        theme = self.combo_theme.get()
        lieux = [
            f"{l['nom_païen']} ({l['energie']})" 
            for l in self.lieux_data 
            if l["pays"] == pays and l["theme"] == theme
        ]
        self.combo_lieu['values'] = lieux
        self.combo_lieu.set("")

    def on_lieu_select(self, event=None):
        selection = self.combo_lieu.get()
        if not selection:
            return
        for l in self.lieux_data:  # ← CORRIGÉ ICI
            label = f"{l['nom_païen']} ({l['energie']})"
            if label == selection:
                self.ent_lat.delete(0, tk.END)
                self.ent_lat.insert(0, str(l["lat"]))
                self.ent_lon.delete(0, tk.END)
                self.ent_lon.insert(0, str(l["lon"]))
                self.ent_lieu_val = l["nom_païen"]
                self.lieu_selectionne = l
                break

    def ouvrir_carte_lieu(self):
        lat = self.ent_lat.get().strip()
        lon = self.ent_lon.get().strip()
        try:
            url = f"https://www.openstreetmap.org/#map=15/{float(lat)}/{float(lon)}"
            webbrowser.open(url)
        except:
            messagebox.showinfo("Info", "Entrez des coordonnées valides.")

    def log_msg(self, msg):
        self.log.configure(state="normal")
        timestamp = datetime.now().strftime('%H:%M:%S')
        self.log.insert(tk.END, f"[{timestamp}] {msg}\n")
        self.log.configure(state="disabled")
        self.log.see(tk.END)
        self.root.update_idletasks()

    def update_progress(self, value, message=""):
        if message:
            self.lbl_progress.config(text=message)
        width = self.progress_canvas.winfo_width()
        if width <= 1: width = 300
        self.progress_canvas.coords(self.progress_rect, 0, 0, width * (value / 100), 20)
        ratio = value / 100
        r = int(148 * (1 - ratio) + 76 * ratio)
        g = int(0 * (1 - ratio) + 198 * ratio)
        b = int(212 * (1 - ratio) + 247 * ratio)
        color = f"#{r:02x}{g:02x}{b:02x}"
        self.progress_canvas.itemconfig(self.progress_rect, fill=color)
        self.root.update_idletasks()

    def lancer_generation(self):
        self.btn_gen.config(state="disabled")
        self.progress_canvas.coords(self.progress_rect, 0, 0, 0, 20)
        self.lbl_progress.config(text="Démarrage...")
        thread = threading.Thread(target=self.generer_sanctuaire, daemon=True)
        thread.start()

    def generer_sanctuaire(self):
        try:
            date_str = self.ent_date.get().strip()
            heure_str = self.ent_heure.get().strip() or "12:00"
            lat_str = self.ent_lat.get().strip()
            lon_str = self.ent_lon.get().strip()
            nom = self.ent_nom.get().strip() or "Anonyme"
            lieu = getattr(self, 'ent_lieu_val', f"({lat_str}, {lon_str})")

            lat = float(lat_str)
            lon = float(lon_str)
            if not (-90 <= lat <= 90) or not (-180 <= lon <= 180):
                raise ValueError("Coordonnées hors limites")

            naiss = datetime.strptime(f"{date_str} {heure_str}", "%Y-%m-%d %H:%M")
            fecondation = naiss - timedelta(days=266)
            animation = fecondation + timedelta(weeks=19)
            jours_lune = (animation - datetime(2000, 1, 6)).days % 29.5
            freq_base = 7.83 + (math.sin(2 * math.pi * jours_lune / 29.5) * 0.3)

            # Générer audio
            if HAS_AUDIO and FFMPEG_EXE.exists():
                chemin_wav = self.generer_audio(animation, freq_base)
            else:
                chemin_wav = self.creer_fichier_simulation(animation)

            # Rapports
            lieu_sacre = getattr(self, 'lieu_selectionne', None)
            rapport_html = self.generer_rapport_html(naiss, nom, lieu, lat, lon, animation, freq_base, lieu_sacre, chemin_wav)
            rapport_txt = self.generer_rapport_txt(naiss, nom, lieu, lat, lon, animation, freq_base, lieu_sacre, chemin_wav)

            self.root.after(0, lambda: self.finaliser(chemin_wav, rapport_html, rapport_txt))

        except Exception as e:
            self.root.after(0, lambda err=str(e): self.gerer_erreur(err))

    def generer_audio(self, animation, freq_base):
        base = 200
        duree_ms = 19 * 60 * 1000
        gauche = Sine(base).to_audio_segment(duree_ms)
        droite_infrason = Sine(base + freq_base).to_audio_segment(duree_ms)

        if self.var_harmoniques.get():
            harm1 = Sine(base * 2).to_audio_segment(duree_ms).apply_gain(-15)
            harm2 = Sine(base * 3).to_audio_segment(duree_ms).apply_gain(-20)
            gauche = gauche.overlay(harm1).overlay(harm2)

        if self.var_ultrason.get():
            ultrason = Sine(25000).to_audio_segment(duree_ms).apply_gain(-30)
            droite = droite_infrason.overlay(ultrason)
        else:
            droite = droite_infrason

        audio = AudioSegment.from_mono_audiosegments(gauche, droite)
        sortie = Path("sanctuaires")
        sortie.mkdir(exist_ok=True)
        nom_fichier = f"sanctuaire_{animation.strftime('%Y%m%d_%H%M')}.wav"
        chemin = sortie / nom_fichier
        audio.export(chemin, format="wav")
        return chemin

    def creer_fichier_simulation(self, animation):
        sortie = Path("sanctuaires")
        sortie.mkdir(exist_ok=True)
        nom_fichier = f"sanctuaire_{animation.strftime('%Y%m%d_%H%M')}_SIMULATION.txt"
        chemin = sortie / nom_fichier
        contenu = f"[MODE SIMULATION]\nDate : {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}"
        chemin.write_text(contenu, encoding="utf-8")
        return chemin

    def generer_rapport_txt(self, naiss, nom, lieu, lat, lon, animation, freq_base, lieu_sacre, chemin_wav):
        sha256 = hashlib.sha256()
        if chemin_wav.exists():
            with open(chemin_wav, "rb") as f:
                for chunk in iter(lambda: f.read(4096), b""):
                    sha256.update(chunk)
            hash_value = sha256.hexdigest()
        else:
            hash_value = "N/A"

        rapport = f"""╔═══════════════════════════════════════════════════════════════╗
║     SANCTUAIRE VIBRATOIRE – RAPPORT FORENSIC KERBEROS v4.5   ║
╚═══════════════════════════════════════════════════════════════╝
  👤 Sujet            : {nom}
  📍 Lieu             : {lieu}
  🌍 Coordonnées      : {lat:.4f}, {lon:.4f}
  💾 SHA256           : {hash_value}
"""
        if lieu_sacre:
            rapport += f"\n⛩️ LIEU SACRÉ\n"
            rapport += f"• Ancien : {lieu_sacre['nom_païen']}\n"
            rapport += f"• Énergie : {lieu_sacre['energie']}\n"
            rapport += f"• Contexte : {lieu_sacre['description']}\n"

        rapport += "\n━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━\n"
        rapport += "  🌿 White hat • Anonymous • Résistant numérique • (-;\n"
        rapport += "  📜 GPLv3 – Victor Pozen / Projet Kerberos\n"
        rapport += "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━\n"

        sortie = Path("sanctuaires")
        rapport_path = sortie / f"rapport_{animation.strftime('%Y%m%d_%H%M')}.txt"
        rapport_path.write_text(rapport, encoding="utf-8")
        return rapport_path

    def generer_rapport_html(self, naiss, nom, lieu, lat, lon, animation, freq_base, lieu_sacre, chemin_wav):
        tomatis_svg = '<svg width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="#4fc3f7" stroke-width="1.5"><circle cx="12" cy="12" r="10"/><path d="M12 8v8M8 12h8"/></svg>'
        lieu_sacre_html = ""
        if lieu_sacre:
            lieu_sacre_html = f'''
            <div class="sacred-site">
              <div>⛩️ Lieu sacré : {lieu_sacre['nom_païen']}</div>
              <div><b>Énergie :</b> {lieu_sacre['energie']}</div>
              <div>{lieu_sacre['description']}</div>
            </div>
            '''

        html_content = f'''<!DOCTYPE html>
<html lang="fr">
<head><meta charset="UTF-8"><title>Sanctuaire – {nom}</title>
<style>
body{{background:linear-gradient(135deg,#0f0f1b 0%,#1a1a2e 100%);color:#e0f7fa;font-family:'Consolas',monospace;padding:20px;}}
.container{{max-width:900px;margin:0 auto;background:rgba(26,35,126,0.6);border-radius:15px;padding:30px;box-shadow:0 8px 32px rgba(0,0,0,0.4);}}
header{{text-align:center;border-bottom:2px solid #4fc3f7;padding-bottom:25px;margin-bottom:30px;}}
h1{{color:#4fc3f7;font-size:28px;}}
.card{{background:rgba(13,27,42,0.7);padding:18px;margin:15px 0;border-radius:10px;border-left:4px solid #4fc3f7;}}
.data-row{{margin:8px 0;padding-left:15px;}}
.data-label{{color:#81d4fa;display:inline-block;width:180px;}}
.data-value{{color:#fff;font-weight:bold;}}
.wave-container{{height:120px;background:rgba(13,27,42,0.9);border-radius:10px;margin:20px 0;position:relative;overflow:hidden;}}
canvas{{width:100%;height:100%;}}
.frequency-display{{text-align:center;font-size:32px;color:#4fc3f7;margin:20px 0;}}
.tomatis{{display:inline-block;margin-right:8px;vertical-align:middle;}}
footer{{text-align:center;margin-top:40px;padding-top:20px;border-top:1px solid rgba(79,195,247,0.3);color:#546e7a;font-size:11px;}}
</style>
</head>
<body>
<div class="container">
<header><h1>👁️‍🗨️ Sanctuaire Vibratoire</h1></header>
<div class="card">
<div class="data-row"><span class="data-label">👤 Sujet :</span> <span class="data-value">{nom}</span></div>
<div class="data-row"><span class="data-label">📍 Lieu :</span> <span class="data-value">{lieu}</span></div>
<div class="data-row"><span class="data-label">🌍 Coordonnées :</span> <span class="data-value">{lat:.4f}, {lon:.4f}</span></div>
</div>
<div class="frequency-display"><span class="tomatis">{tomatis_svg}</span>{freq_base:.3f} Hz</div>
{lieu_sacre_html}
<div class="wave-container"><canvas id="waveCanvas"></canvas></div>
<footer>
<div>🌿 White hat • Anonymous • Résistant numérique • (-;</div>
<div>📜 GPLv3 – Victor Pozen / Projet Kerberos</div>
</footer>
</div>
<script>
const canvas=document.getElementById('waveCanvas');
function resize(){{canvas.width=canvas.offsetWidth;canvas.height=canvas.offsetHeight;}}
resize();window.addEventListener('resize',resize);
function draw(){{
const w=canvas.width,h=canvas.height,t=Date.now()/800;
const ctx=canvas.getContext('2d');
ctx.fillStyle='rgba(13,27,42,0.1)';ctx.fillRect(0,0,w,h);
ctx.strokeStyle='#4fc3f7';ctx.lineWidth=2;ctx.beginPath();
for(let x=0;x<w;x+=2){{const y=h/2+Math.sin(x/40+t)*(h/3);x===0?ctx.moveTo(x,y):ctx.lineTo(x,y);}}ctx.stroke();
requestAnimationFrame(draw);}}draw();
</script>
</body>
</html>'''

        sortie = Path("sanctuaires")
        sortie.mkdir(exist_ok=True)
        rapport_path = sortie / f"rapport_{animation.strftime('%Y%m%d_%H%M')}.html"
        rapport_path.write_text(html_content, encoding="utf-8")
        return rapport_path

    def finaliser(self, chemin_wav, rapport_html, rapport_txt):
        self.update_progress(100, "✅ Terminé !")
        self.log_msg("✅ Sanctuaire généré avec succès")
        if self.var_ouvrir_auto.get():
            try:
                if chemin_wav.exists(): os.startfile(str(chemin_wav))
                webbrowser.open(rapport_html.absolute().as_uri())
            except: pass
        messagebox.showinfo("✅ Succès", f"Sanctuaire prêt !\n{chemin_wav.name}")
        self.btn_gen.config(state="normal")

    def gerer_erreur(self, msg):
        self.log_msg(f"❌ ERREUR : {msg}")
        messagebox.showerror("Erreur", msg)
        self.btn_gen.config(state="normal")
        self.lbl_progress.config(text="Erreur - Prêt")

def main():
    try:
        root = tk.Tk()
        app = SanctuaireVibratoire(root)
        root.mainloop()
    except Exception as e:
        messagebox.showerror("Erreur critique", f"Impossible de démarrer :\n{e}")

if __name__ == "__main__":
    main()