# -*- coding: utf-8 -*-
import os
import sys
import tkinter as tk
from tkinter import ttk, scrolledtext, filedialog, messagebox
from pathlib import Path
from datetime import datetime

class ErrorSearcher:
    def __init__(self, root):
        self.root = root
        self.root.title("🔍 Chercher erreur Python/CSV - Kerberos v2.0")
        self.root.geometry("980x700")
        self.root.configure(bg="#1a1a1a")
        self.self_filename = Path(__file__).name
        
        # Style
        style = ttk.Style()
        try:
            style.theme_use('clam')
        except:
            pass
        style.configure("TLabel", background="#1a1a1a", foreground="#e0e0e0", font=("Consolas", 10))
        style.configure("TButton", background="#2d5a2d", foreground="white", font=("Consolas", 10, "bold"))
        style.map("TButton", background=[("active", "#3a7a3a")])
        style.configure("TEntry", fieldbackground="#252525", foreground="#00ffcc")
        style.configure("TCheckbutton", background="#1a1a1a", foreground="#bb86fc", font=("Consolas", 9))
        
        self.create_ui()
        self.detecter_racine()
    
    def detecter_racine(self):
        """Détecte automatiquement le dossier bioresonance"""
        chemins_possibles = [
            r"F:\bioresonance",
            r"C:\bioresonance",
            str(Path.cwd()),
            str(Path.home() / "bioresonance")
        ]
        
        for chemin in chemins_possibles:
            if os.path.isdir(chemin) and (Path(chemin) / "brain").exists():
                self.path_entry.delete(0, tk.END)
                self.path_entry.insert(0, chemin)
                self.log(f"✅ Dossier projet détecté : {chemin}\n")
                return
        
        courant = str(Path.cwd())
        self.path_entry.delete(0, tk.END)
        self.path_entry.insert(0, courant)
        self.log(f"⚠️  Dossier bioresonance non trouvé. Utilisation du dossier courant :\n   {courant}\n")
        self.log("💡 Conseil : Clique sur 📁 pour sélectionner manuellement F:\\bioresonance\n")
    
    def create_ui(self):
        main = tk.Frame(self.root, bg="#1a1a1a", padx=20, pady=15)
        main.pack(fill="both", expand=True)
        
        # Titre
        tk.Label(main, text="🔍 RECHERCHE D'ERREUR MULTI-FORMAT", 
                bg="#1a1a1a", fg="#bb86fc", font=("Consolas", 16, "bold")).pack(pady=(0, 15))
        
        # Zone de saisie de l'erreur
        err_frame = tk.Frame(main, bg="#1a1a1a")
        err_frame.pack(fill="x", pady=(0, 12))
        tk.Label(err_frame, text="Erreur à chercher (ex: ' background') :", bg="#1a1a1a", fg="#4fc3f7", font=("Consolas", 11)).pack(anchor="w")
        self.err_entry = tk.Entry(err_frame, font=("Consolas", 11), width=70,
                                 bg="#252525", fg="#00ffcc", insertbackground="#00ffcc")
        self.err_entry.insert(0, "' background'")
        self.err_entry.pack(pady=(5, 0), fill="x")
        self.create_entry_context_menu(self.err_entry)
        
        # Dossier + Extensions
        path_ext_frame = tk.Frame(main, bg="#1a1a1a")
        path_ext_frame.pack(fill="x", pady=(0, 12))
        
        # Dossier
        path_frame = tk.Frame(path_ext_frame, bg="#1a1a1a")
        path_frame.pack(side="left", fill="x", expand=True)
        tk.Label(path_frame, text="Dossier à analyser :", bg="#1a1a1a", fg="#e0e0e0").pack(anchor="w")
        path_subframe = tk.Frame(path_frame, bg="#1a1a1a")
        path_subframe.pack(fill="x", pady=(5, 0))
        self.path_entry = tk.Entry(path_subframe, font=("Consolas", 10),
                                  bg="#252525", fg="#00ffcc", insertbackground="#00ffcc")
        self.path_entry.pack(side="left", fill="x", expand=True, padx=(0, 10))
        self.create_entry_context_menu(self.path_entry)
        ttk.Button(path_subframe, text="📁", width=4, command=self.browse_folder).pack(side="right")
        
        # Extensions (à droite)
        ext_frame = tk.Frame(path_ext_frame, bg="#1a1a1a", padx=20)
        ext_frame.pack(side="right", fill="y")
        tk.Label(ext_frame, text="Extensions :", bg="#1a1a1a", fg="#bb86fc", font=("Consolas", 10, "bold")).pack(anchor="w")
        self.ext_py = tk.BooleanVar(value=True)
        self.ext_csv = tk.BooleanVar(value=True)
        self.ext_json = tk.BooleanVar(value=False)
        self.ext_txt = tk.BooleanVar(value=False)
        ttk.Checkbutton(ext_frame, text=".py", variable=self.ext_py).pack(anchor="w")
        ttk.Checkbutton(ext_frame, text=".csv", variable=self.ext_csv).pack(anchor="w")
        ttk.Checkbutton(ext_frame, text=".json", variable=self.ext_json).pack(anchor="w")
        ttk.Checkbutton(ext_frame, text=".txt", variable=self.ext_txt).pack(anchor="w")
        
        # Boutons
        btn_frame = tk.Frame(main, bg="#1a1a1a")
        btn_frame.pack(fill="x", pady=(0, 15))
        ttk.Button(btn_frame, text="🚀 LANCER RECHERCHE", command=self.start_search, width=22).pack(side="left", padx=5)
        ttk.Button(btn_frame, text="💾 RAPPORT TXT", command=self.save_report, width=18).pack(side="left", padx=5)
        ttk.Button(btn_frame, text="🗑️ VIDER", command=self.clear, width=12).pack(side="right", padx=5)
        
        # Résultats
        tk.Label(main, text="Résultats :", bg="#1a1a1a", fg="#4CAF50", font=("Consolas", 11, "bold")).pack(anchor="w")
        self.results = scrolledtext.ScrolledText(main, wrap=tk.WORD, font=("Consolas", 9),
                                                bg="#0d0d0d", fg="#ffcc00", insertbackground="#ffcc00",
                                                height=28)
        self.results.pack(fill="both", expand=True, pady=(8, 0))
        self.create_results_context_menu()
        
        # Pied de page
        footer = tk.Frame(main, bg="#1a1a1a", pady=12)
        footer.pack(fill="x", side="bottom")
        tk.Label(footer, text="Kerberos v2.0 • GPLv3 modifiée – Victor Pozen 🐺", 
                bg="#1a1a1a", fg="#666", font=("Consolas", 8)).pack()
        
        # Config tags colorés
        self.results.tag_configure("sep", foreground="#555")
        self.results.tag_configure("fichier", foreground="#bb86fc", font=("Consolas", 10, "bold"))
        self.results.tag_configure("ligne", foreground="#4fc3f7")
        self.results.tag_configure("normal", foreground="#ffcc00")
        self.results.tag_configure("highlight", foreground="#000000", background="#ffff00", font=("Consolas", 9, "bold"))
        self.results.tag_configure("csv", foreground="#ff5252", font=("Consolas", 10, "bold"))
        self.results.tag_configure("py", foreground="#4CAF50", font=("Consolas", 10, "bold"))
        
        self.log("ℹ️  Saisis l'erreur EXACTE à chercher (ex: ' background' avec espace)\n")
        self.log("   → Ce script s'exclut lui-même pour éviter les faux positifs\n")
        self.log("   → Coche .csv pour trouver les erreurs dans lieux_sacres.csv !\n")
    
    # === MENUS CONTEXTUELS CORRIGÉS ===
    def create_entry_context_menu(self, entry_widget):
        """Menu contextuel fonctionnel pour tk.Entry"""
        menu = tk.Menu(self.root, tearoff=0, bg="#2d2d2d", fg="#e0e0e0",
                      activebackground="#3a3a3a", activeforeground="#00ffcc", font=("Consolas", 10))
        menu.add_command(label="✂️ Couper", command=lambda: entry_widget.event_generate("<<Cut>>"))
        menu.add_command(label="📋 Copier", command=lambda: entry_widget.event_generate("<<Copy>>"))
        menu.add_command(label="📥 Coller", command=lambda: entry_widget.event_generate("<<Paste>>"))
        menu.add_separator()
        menu.add_command(label="🗑️ Tout sélectionner", command=lambda: entry_widget.select_range(0, tk.END))
        
        entry_widget.bind("<Button-3>", lambda e: menu.tk_popup(e.x_root, e.y_root))
        entry_widget.bind("<FocusIn>", lambda e: entry_widget.selection_range(0, tk.END))
    
    def create_results_context_menu(self):
        """Menu contextuel pour ScrolledText"""
        self.context_menu = tk.Menu(self.root, tearoff=0, bg="#2d2d2d", fg="#e0e0e0",
                                   activebackground="#3a3a3a", activeforeground="#00ffcc", font=("Consolas", 10))
        self.context_menu.add_command(label="✂️ Couper", command=lambda: self.results.event_generate("<<Cut>>"))
        self.context_menu.add_command(label="📋 Copier", command=lambda: self.results.event_generate("<<Copy>>"))
        self.context_menu.add_command(label="📥 Coller", command=lambda: self.results.event_generate("<<Paste>>"))
        self.context_menu.add_separator()
        self.context_menu.add_command(label="🗑️ Tout sélectionner", command=self.select_all_results)
        
        self.results.bind("<Button-3>", self.show_results_menu)
        self.results.bind("<Control-a>", lambda e: self.select_all_results())
    
    def show_results_menu(self, event):
        try:
            self.results.selection_get()
            has_sel = True
        except:
            has_sel = False
        self.context_menu.entryconfig("✂️ Couper", state="normal" if has_sel else "disabled")
        self.context_menu.entryconfig("📋 Copier", state="normal" if has_sel else "disabled")
        self.context_menu.tk_popup(event.x_root, event.y_root)
    
    def select_all_results(self):
        self.results.tag_add("sel", "1.0", "end")
        self.results.mark_set("insert", "1.0")
        return "break"
    
    # === FIN MENUS CONTEXTUELS ===
    
    def browse_folder(self):
        initial = self.path_entry.get().strip() or str(Path.home())
        folder = filedialog.askdirectory(initialdir=initial, title="Sélectionner le dossier bioresonance")
        if folder:
            self.path_entry.delete(0, tk.END)
            self.path_entry.insert(0, folder)
    
    def log(self, msg, tag="normal"):
        try:
            self.results.insert(tk.END, msg, tag)
            self.results.see(tk.END)
            self.root.update_idletasks()
        except:
            pass
    
    def clear(self):
        self.results.delete("1.0", tk.END)
    
    def start_search(self):
        self.clear()
        dossier = self.path_entry.get().strip()
        motif = self.err_entry.get().strip()
        
        if not motif:
            messagebox.showwarning("⚠️ Attention", "Veuillez saisir le texte de l'erreur à chercher")
            return
        
        if not os.path.isdir(dossier):
            reponse = messagebox.askyesno("❌ Dossier introuvable", 
                f"Le dossier n'existe pas :\n{dossier}\n\nVoulez-vous le créer ?")
            if reponse:
                try:
                    Path(dossier).mkdir(parents=True, exist_ok=True)
                    self.log(f"✅ Dossier créé : {dossier}\n")
                except Exception as e:
                    messagebox.showerror("❌ Erreur", f"Impossible de créer le dossier :\n{e}")
                    return
            else:
                return
        
        # 🔧 CORRECTION CRITIQUE : extraction propre des extensions
        extensions = []
        if self.ext_py.get(): extensions.append((".py", "py"))
        if self.ext_csv.get(): extensions.append((".csv", "csv"))
        if self.ext_json.get(): extensions.append((".json", "json"))
        if self.ext_txt.get(): extensions.append((".txt", "txt"))
        
        if not extensions:
            messagebox.showwarning("⚠️ Attention", "Veuillez cocher au moins une extension à analyser")
            return
        
        self.log(f"🔍 Recherche EXACTE de : {repr(motif)}\n", "normal")
        self.log(f"📁 Dossier : {dossier}\n", "normal")
        self.log(f"🗃️ Extensions : {', '.join(ext[0] for ext in extensions)}\n\n", "normal")
        self.log("="*80 + "\n\n", "sep")
        
        # 🔧 CORRECTION : dictionnaire avec clés correctes
        resultats = {"py": [], "csv": [], "json": [], "txt": []}
        total_fichiers = 0
        
        for ext_pattern, ext_type in extensions:
            try:
                fichiers = list(Path(dossier).rglob(f"*{ext_pattern}"))
                total_fichiers += len(fichiers)
            except Exception as e:
                messagebox.showerror("❌ Erreur", f"Impossible de lire le dossier :\n{e}")
                return
            
            for chemin in fichiers:
                relatif = chemin.relative_to(dossier)
                
                # Exclure ce script lui-même
                if ext_type == "py" and relatif.name == self.self_filename:
                    continue
                
                try:
                    # 🔧 CORRECTION : lecture robuste avec gestion d'encodage
                    try:
                        contenu = chemin.read_text(encoding="utf-8")
                    except UnicodeDecodeError:
                        try:
                            contenu = chemin.read_text(encoding="latin-1")
                        except Exception as e2:
                            self.log(f"⚠️  Impossible de lire {relatif} (encodage)\n", "normal")
                            continue
                    
                    lignes = contenu.splitlines()
                    
                    for num, ligne in enumerate(lignes, 1):
                        if motif in ligne:
                            debut = max(0, num - 2)
                            fin = min(len(lignes), num + 2)
                            contexte = []
                            for i in range(debut, fin):
                                prefixe = " >> " if i+1 == num else "    "
                                contexte.append(f"{prefixe}{i+1:4d} | {lignes[i]}")
                            
                            resultats[ext_type].append({
                                "fichier": relatif,
                                "ligne": num,
                                "contexte": "\n".join(contexte)
                            })
                except Exception as e:
                    self.log(f"⚠️  Erreur lecture {relatif}: {str(e)[:60]}\n", "normal")
        
        # Afficher résultats groupés par type
        total_occurrences = sum(len(r) for r in resultats.values())
        if total_occurrences:
            # .py en vert
            if resultats["py"]:
                self.log(f"\n🐍 FICHIERS PYTHON (.py) — {len(resultats['py'])} occurrence(s)\n", "py")
                self.log("─"*80 + "\n", "sep")
                for r in resultats["py"]:
                    self.log_result(r["fichier"], r["ligne"], r["contexte"], motif)
            
            # .csv en rouge
            if resultats["csv"]:
                self.log(f"\n📊 FICHIERS CSV (.csv) — {len(resultats['csv'])} occurrence(s)\n", "csv")
                self.log("─"*80 + "\n", "sep")
                for r in resultats["csv"]:
                    self.log_result(r["fichier"], r["ligne"], r["contexte"], motif)
            
            # Autres formats
            for ext_type in ["json", "txt"]:
                if resultats[ext_type]:
                    self.log(f"\n📄 FICHIERS {ext_type.upper()} (.{ext_type}) — {len(resultats[ext_type])} occurrence(s)\n", "normal")
                    self.log("─"*80 + "\n", "sep")
                    for r in resultats[ext_type]:
                        self.log_result(r["fichier"], r["ligne"], r["contexte"], motif)
        else:
            self.log("✅ Aucune occurrence trouvée dans les fichiers analysés\n\n", "normal")
            self.log("💡 Conseils :\n", "normal")
            self.log("   • Vérifie la syntaxe EXACTE (espaces, apostrophes, guillemets)\n", "normal")
            self.log("   • Pour ' background' : l'espace AVANT 'background' est critique !\n", "normal")
            self.log("   • Vérifie resources/lieux_sacres.csv (colonnes avec espaces)\n", "normal")
        
        # Résumé final
        self.log("\n" + "="*80 + "\n", "sep")
        self.log(f"✅ TOTAL : {total_occurrences} occurrence(s) dans {total_fichiers} fichiers analysés\n", "normal")
        
        self.resultats_bruts = resultats
        self.motif = motif
        self.timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        self.save_report(auto=True)
    
    def log_result(self, fichier, ligne, contexte, motif):
        """Affiche un résultat avec surlignage du motif"""
        self.log(f"\n📍 {fichier}\n", "fichier")
        self.log(f"   Ligne {ligne}\n\n", "ligne")
        
        for line in contexte.split("\n"):
            if motif in line and motif.strip():
                parts = line.split(motif, 1)
                self.log(parts[0], "normal")
                self.log(motif, "highlight")
                self.log(parts[1] + "\n", "normal")
            else:
                self.log(line + "\n", "normal")
        self.log("\n", "normal")
    
    def save_report(self, auto=False):
        if not hasattr(self, 'resultats_bruts'):
            if not auto:
                messagebox.showwarning("⚠️ Attention", "Aucune recherche effectuée")
            return
        
        rapport = f"""============================================================
RAPPORT DE RECHERCHE D'ERREUR MULTI-FORMAT
Kerberos v2.0 – BioResonance
============================================================
Date      : {datetime.now().strftime('%d/%m/%Y %H:%M:%S')}
Dossier   : {self.path_entry.get().strip()}
Motif     : {repr(self.motif)}
Extensions: {', '.join([ext[0] for ext in [('.py','py'),('.csv','csv'),('.json','json'),('.txt','txt')] if getattr(self, f'ext_{ext[1]}').get()])}
============================================================

"""
        total = 0
        for ext_type, resultats in self.resultats_bruts.items():
            if resultats:
                rapport += f"\n{'='*60}\n"
                rapport += f"FICHIERS .{ext_type.upper()} ({len(resultats)} occurrence(s))\n"
                rapport += f"{'='*60}\n\n"
                for i, r in enumerate(resultats, 1):
                    rapport += f"{i}. [{r['fichier']}] Ligne {r['ligne']}\n"
                    rapport += r['contexte'] + "\n\n"
                total += len(resultats)
        
        if total == 0:
            rapport += "✅ AUCUNE OCCURRENCE TROUVÉE\n\n"
            rapport += "💡 L'erreur est probablement :\n"
            rapport += "   • Mal orthographiée dans le champ de recherche\n"
            rapport += "   • Générée dynamiquement (ex: concaténation avec espace)\n"
        
        rapport += "\n============================================================\n"
        rapport += "Kerberos v2.0 • GPLv3 modifiée – Victor Pozen 🐺\n"
        rapport += "============================================================"
        
        # Sauvegarder
        try:
            rapport_path = Path(self.path_entry.get().strip()) / f"rapport_erreur_{self.timestamp}.txt"
            rapport_path.write_text(rapport, encoding="utf-8")
            if not auto:
                messagebox.showinfo("✅ Succès", f"Rapport sauvegardé :\n{rapport_path}")
            self.log(f"\n📄 Rapport généré : rapport_erreur_{self.timestamp}.txt\n", "normal")
        except Exception as e:
            if not auto:
                messagebox.showerror("❌ Erreur", f"Impossible d'écrire le rapport :\n{e}")
            else:
                self.log(f"\n⚠️  Impossible de sauvegarder le rapport : {e}\n", "normal")

# === POINT D'ENTRÉE SÉCURISÉ ===
if __name__ == "__main__":
    try:
        root = tk.Tk()
        app = ErrorSearcher(root)
        root.mainloop()
    except Exception as e:
        print(f"ERREUR FATALE : {e}")
        print("\nAppuyez sur Entrée pour quitter...")
        input()