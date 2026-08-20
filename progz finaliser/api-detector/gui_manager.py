#!/usr/bin/env python3
# -*- coding: utf-8 -*-
# Copyright (C) 2026 Victor Pozen — GPLv3
"""
GUI Manager v1.0 — Interface Cerberus
======================================
Interface graphique modulaire
"""
import tkinter as tk
from tkinter import ttk, filedialog, messagebox, scrolledtext
from pathlib import Path
import threading
from datetime import datetime

from api_detector_v5 import CerberusEngine, logger

# ============================================================
# 🎨 GUI MANAGER
# ============================================================
class GUIManager:
    def __init__(self):
        self.engine = CerberusEngine()
        self.root = tk.Tk()
        self.root.title("🐕‍🦺 Cerberus v5.3 — Interface de Gestion")
        self.root.geometry("1200x750")
        self.root.configure(bg='#1e1e1e')
        
        self.target_path = tk.StringVar()
        self._setup_style()
        self._build_ui()
        
        logger.info("️ GUI Manager prêt")
        self.root.mainloop()
    
    def _setup_style(self):
        style = ttk.Style()
        try:
            style.theme_use('clam')
        except:
            pass
        
        style.configure('TFrame', background='#1e1e1e')
        style.configure('TLabel', background='#1e1e1e', foreground='#00ffcc', font=('Consolas', 10))
        style.configure('TButton', background='#2d5a7b', foreground='#ffffff', font=('Consolas', 10))
        style.configure('TLabelframe', background='#1e1e1e', foreground='#00ffcc')
        style.configure('TLabelframe.Label', background='#1e1e1e', foreground='#00ffcc')
        style.configure('Treeview', background='#2d2d2d', foreground='#ffffff')
        style.configure('Treeview.Heading', background='#3a3a3a', foreground='#00ffcc')
    
    def _build_ui(self):
        # Zone supérieure — Sélection dossier
        top_frame = ttk.LabelFrame(self.root, text=" Dossier à analyser", padding=10)
        top_frame.pack(fill=tk.X, padx=10, pady=10)
        
        ttk.Label(top_frame, text="Dossier:").pack(side=tk.LEFT, padx=5)
        ttk.Entry(top_frame, textvariable=self.target_path, width=80).pack(side=tk.LEFT, padx=5)
        ttk.Button(top_frame, text="📂 Parcourir", command=self._select_folder).pack(side=tk.LEFT, padx=5)
        ttk.Button(top_frame, text="🔍 Scanner", command=self._start_scan).pack(side=tk.LEFT, padx=10)
        
        # Zone centrale — Résultats
        results_frame = ttk.Frame(self.root)
        results_frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)
        
        # Onglets
        notebook = ttk.Notebook(results_frame)
        notebook.pack(fill=tk.BOTH, expand=True)
        
        # Onglet Stdlib
        stdlib_tab = ttk.Frame(notebook)
        notebook.add(stdlib_tab, text="📚 Stdlib")
        self.text_stdlib = scrolledtext.ScrolledText(stdlib_tab, bg='#2d2d2d', fg='#00ffcc', font=('Consolas', 10))
        self.text_stdlib.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)
        
        # Onglet Locaux
        local_tab = ttk.Frame(notebook)
        notebook.add(local_tab, text="🏠 Locaux")
        self.text_local = scrolledtext.ScrolledText(local_tab, bg='#2d2d2d', fg='#b388ff', font=('Consolas', 10))
        self.text_local.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)
        
        # Onglet Installés
        installed_tab = ttk.Frame(notebook)
        notebook.add(installed_tab, text="✅ Installés")
        self.tree_installed = ttk.Treeview(installed_tab, columns=('module', 'pip', 'version'), show='headings')
        self.tree_installed.heading('module', text='Module')
        self.tree_installed.heading('pip', text='Package')
        self.tree_installed.heading('version', text='Version')
        self.tree_installed.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)
        
        # Onglet Manquants
        missing_tab = ttk.Frame(notebook)
        notebook.add(missing_tab, text="❌ Manquants")
        self.tree_missing = ttk.Treeview(missing_tab, columns=('module', 'pip'), show='headings')
        self.tree_missing.heading('module', text='Module')
        self.tree_missing.heading('pip', text='Package')
        self.tree_missing.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)
        
        # Zone inférieure — Actions
        bottom_frame = ttk.Frame(self.root)
        bottom_frame.pack(fill=tk.X, padx=10, pady=10)
        
        ttk.Button(bottom_frame, text="📦 Installer (sélection)", command=self._install_selected).pack(side=tk.LEFT, padx=5)
        ttk.Button(bottom_frame, text="💾 Rapport TXT", command=self._export_report).pack(side=tk.LEFT, padx=5)
        ttk.Button(bottom_frame, text="🔄 Reload Guards", command=self._reload_guards).pack(side=tk.LEFT, padx=10)
        
        # Progress bar
        self.progress = ttk.Progressbar(bottom_frame, mode='determinate', length=300)
        self.progress.pack(side=tk.RIGHT, padx=10)
        self.progress_label = ttk.Label(bottom_frame, text="Prêt")
        self.progress_label.pack(side=tk.RIGHT, padx=5)
        
        # Console logs
        console_frame = ttk.LabelFrame(self.root, text=" Console", padding=5)
        console_frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=(0, 10))
        
        self.console = scrolledtext.ScrolledText(console_frame, height=8, bg='#1a1a1a', fg='#00ff00', font=('Consolas', 9))
        self.console.pack(fill=tk.BOTH, expand=True)
        self._log("‍🦺 Cerberus GUI v5.3 prêt")
    
    def _log(self, msg: str):
        timestamp = datetime.now().strftime('%H:%M:%S')
        self.console.configure(state='normal')
        self.console.insert(tk.END, f"[{timestamp}] {msg}\n")
        self.console.see(tk.END)
        self.console.configure(state='disabled')
    
    def _select_folder(self):
        path = filedialog.askdirectory(title="Sélectionner un dossier")
        if path:
            self.target_path.set(path)
            self._log(f"📂 Dossier sélectionné: {path}")
    
    def _start_scan(self):
        target = self.target_path.get().strip()
        if not target:
            messagebox.showwarning("⚠️", "Sélectionne un dossier")
            return
        
        target_path = Path(target)
        if not target_path.is_dir():
            messagebox.showerror("❌", f"Dossier introuvable: {target}")
            return
        
        self._log(f"🔍 Scan démarré: {target}")
        self.progress.config(value=0)
        self.progress_label.config(text="Scan en cours...")
        
        def scan_worker():
            try:
                results = self.engine.scan_directory(target_path)
                self.root.after(0, lambda: self._display_results(results))
                self.root.after(0, lambda: self._update_progress(100, "✅ Scan terminé"))
            except Exception as e:
                self.root.after(0, lambda: self._log(f" Erreur: {e}"))
                self.root.after(0, lambda: self._update_progress(0, "❌ Erreur"))
        
        threading.Thread(target=scan_worker, daemon=True).start()
    
    def _display_results(self, results):
        # Stdlib
        self.text_stdlib.delete('1.0', tk.END)
        for m in results['stdlib']:
            self.text_stdlib.insert(tk.END, f"📚 {m}\n")
        
        # Locaux
        self.text_local.delete('1.0', tk.END)
        for m in results['local']:
            self.text_local.insert(tk.END, f"🏠 {m}\n")
        
        # Installés
        self.tree_installed.delete(*self.tree_installed.get_children())
        for pkg in results['installed']:
            self.tree_installed.insert('', tk.END, values=(pkg['module'], pkg['pip_name'], pkg['version']))
        
        # Manquants
        self.tree_missing.delete(*self.tree_missing.get_children())
        for pkg in results['missing']:
            self.tree_missing.insert('', tk.END, values=(pkg['module'], pkg['pip_name']))
        
        self._log(f"✅ Scan terminé: {len(results['installed'])} installés, {len(results['missing'])} manquants")
    
    def _install_selected(self):
        selected = self.tree_missing.selection()
        if not selected:
            messagebox.showinfo("ℹ️", "Sélectionne des packages dans l'onglet 'Manquants'")
            return
        
        packages = [self.tree_missing.item(i, 'values')[1] for i in selected]
        
        if not messagebox.askyesno("📦 Installation", f"Installer {len(packages)} package(s) ?"):
            return
        
        self._log(f"📦 Installation de {len(packages)} package(s)...")
        self.progress.config(value=0)
        
        def install_worker():
            def progress_cb(i, total, pkg):
                self.root.after(0, lambda: self._update_progress(int((i/total)*100), f"Installation: {pkg}"))
            
            result = self.engine.install_packages(packages, progress_cb)
            self.root.after(0, lambda: self._log(f"✅ Succès: {len(result['success'])}, ❌ Échecs: {len(result['failed'])}"))
            self.root.after(0, lambda: self._update_progress(100, "✅ Installation terminée"))
        
        threading.Thread(target=install_worker, daemon=True).start()
    
    def _export_report(self):
        if not self.engine.analysis_results:
            messagebox.showwarning("⚠️", "Aucune analyse disponible")
            return
        
        path = filedialog.asksaveasfilename(defaultextension=".txt", filetypes=[("Text files", "*.txt")])
        if path:
            if self.engine.generate_report(Path(path)):
                self._log(f"💾 Rapport exporté: {path}")
                messagebox.showinfo("✅", "Rapport généré avec succès")
    
    def _reload_guards(self):
        self._log("🔄 Rechargement des guards...")
        results = self.engine.reload_guards()
        if results:
            self._log(f"✅ {len(results)} guard(s) rechargé(s)")
        else:
            self._log("⚠️ Aucun guard rechargé")
    
    def _update_progress(self, value: int, text: str):
        self.progress.config(value=value)
        self.progress_label.config(text=text)

# Point d'entrée
if __name__ == '__main__':
    GUIManager()