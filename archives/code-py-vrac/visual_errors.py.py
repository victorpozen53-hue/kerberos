#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Module Graphique Visual Errors - Kerberos Debugger v4.1
═════════════════════════════════════════════════════════

Visualisation graphique des erreurs Python sous forme d'arbre interactif
→ Aucune IA embarquée
→ Aucune connexion réseau silencieuse
→ Ouverture navigateur UNIQUEMENT sur action EXPLICITE de l'utilisateur
→ Boîte de dialogue de consentement avant tout partage de données

Philosophie Éthique :
─────────────────────
• 100% local par défaut — zéro appel réseau sans ton accord
• Transparence totale — tu vois EXACTEMENT quand tes données quittent ton PC
• Consentement explicite — confirmation requise avant chaque ouverture
• Aucune clé API requise — pas de configuration complexe

Licence : GPLv3
Développé par Victor Pozen © 2026
"""

import tkinter as tk
from tkinter import ttk, scrolledtext, messagebox
import re
import webbrowser
import urllib.parse
import os
import sys


class VisualErrorsPanel:
    """
    Panneau graphique optionnel pour visualiser les erreurs Python
    
    Fonctionnalités :
    ─────────────────
    • Arbre interactif du traceback (fichiers, lignes, fonctions)
    • Boutons d'ouverture vers Qwen / ChatGPT / Gemini (avec consentement)
    • Toggle ON/OFF pour activer/désactiver le panneau
    • Zéro connexion réseau sans action consciente de l'utilisateur
    
    Intégration :
    ─────────────
    1. Importe ce module dans kerberos_debugger_v4.py
    2. Crée une instance : panel = VisualErrorsPanel(parent_frame, debugger)
    3. Appelle panel.display_error(error_type, message, traceback_lines) lors d'une erreur
    """
    
    def __init__(self, parent_frame: tk.Frame, debugger_instance):
        """
        Initialise le panneau graphique
        
        Args:
            parent_frame (tk.Frame): Frame parent dans lequel insérer le panneau
            debugger_instance: Instance du debugger principal (pour logs/messages)
        """
        self.parent = parent_frame
        self.debugger = debugger_instance
        self.enabled = False
        self.last_error = None
        
        # Couleurs Kerberos (thème sombre)
        self.colors = {
            "bg_dark": "#0a0e17",
            "bg_mid": "#121826",
            "bg_light": "#1e273a",
            "accent": "#6c5ce7",
            "accent_hover": "#a29bfe",
            "text": "#f7f9fc",
            "text_dim": "#636e72",
            "error": "#ff7675",
            "success": "#00b894",
            "warning": "#fdcb6e",
            "info": "#00cec9"
        }
        
        # Création du panneau (initialement caché)
        self.panel = tk.Frame(
            self.parent,
            bg=self.colors["bg_dark"],
            relief=tk.RAISED,
            borderwidth=1
        )
        self.panel.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)
        self.panel.pack_forget()  # Caché par défaut
        
        # Création des widgets internes
        self._create_widgets()
        
        # État initial
        self.debugger.log_message(
            "🎨 Module graphique Visual Errors chargé (optionnel)",
            "ai"
        )
    
    def _create_widgets(self):
        """Crée l'interface graphique du panneau"""
        
        # ════════════════════════════════════════════════════════════════
        # HEADER : Titre + Toggle
        # ════════════════════════════════════════════════════════════════
        header = tk.Frame(self.panel, bg=self.colors["bg_dark"])
        header.pack(fill=tk.X, padx=10, pady=8)
        
        # Toggle pour activer/désactiver le panneau
        self.toggle_var = tk.BooleanVar(value=False)
        toggle = tk.Checkbutton(
            header,
            text="🎨 Visualisation Graphique des Erreurs",
            variable=self.toggle_var,
            command=self._toggle_panel,
            bg=self.colors["bg_dark"],
            fg=self.colors["accent"],
            selectcolor=self.colors["bg_mid"],
            font=("Consolas", 10, "bold"),
            activebackground=self.colors["bg_dark"],
            activeforeground=self.colors["accent_hover"]
        )
        toggle.pack(side=tk.LEFT)
        
        # Info tooltip (optionnel)
        info_label = tk.Label(
            header,
            text="ℹ️ Clique pour activer/désactiver",
            bg=self.colors["bg_dark"],
            fg=self.colors["text_dim"],
            font=("Consolas", 8)
        )
        info_label.pack(side=tk.LEFT, padx=(10, 0))
        
        # ════════════════════════════════════════════════════════════════
        # TREEVIEW : Arbre des erreurs
        # ════════════════════════════════════════════════════════════════
        tree_frame = tk.Frame(self.panel, bg=self.colors["bg_mid"])
        tree_frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=5)
        
        # Style pour le Treeview
        style = ttk.Style()
        
        # Configurer le style du Treeview
        style.configure(
            "ErrorTree.Treeview",
            background=self.colors["bg_light"],
            foreground=self.colors["text"],
            fieldbackground=self.colors["bg_light"],
            font=("Consolas", 10),
            rowheight=25
        )
        
        # Style pour les éléments sélectionnés
        style.map(
            "ErrorTree.Treeview",
            background=[("selected", self.colors["accent"])],
            foreground=[("selected", "white")]
        )
        
        # Treeview pour l'arbre des erreurs
        self.tree = ttk.Treeview(
            tree_frame,
            columns=("type", "location", "message"),
            show="headings",
            style="ErrorTree.Treeview"
        )
        
        # Configuration des colonnes
        self.tree.heading("type", text="Type")
        self.tree.heading("location", text="Fichier:Ligne")
        self.tree.heading("message", text="Message")
        
        self.tree.column("type", width=120, anchor=tk.W, stretch=False)
        self.tree.column("location", width=180, anchor=tk.W, stretch=False)
        self.tree.column("message", width=400, anchor=tk.W, stretch=True)
        
        # Scrollbars
        vsb = ttk.Scrollbar(tree_frame, orient="vertical", command=self.tree.yview)
        hsb = ttk.Scrollbar(tree_frame, orient="horizontal", command=self.tree.xview)
        self.tree.configure(yscrollcommand=vsb.set, xscrollcommand=hsb.set)
        
        # Disposition
        self.tree.grid(row=0, column=0, sticky="nsew")
        vsb.grid(row=0, column=1, sticky="ns")
        hsb.grid(row=1, column=0, sticky="ew")
        
        tree_frame.grid_rowconfigure(0, weight=1)
        tree_frame.grid_columnconfigure(0, weight=1)
        
        # ════════════════════════════════════════════════════════════════
        # BOUTONS D'ACTION : Ouvrir dans Qwen / ChatGPT / Gemini
        # ════════════════════════════════════════════════════════════════
        btn_frame = tk.Frame(self.panel, bg=self.colors["bg_dark"])
        btn_frame.pack(fill=tk.X, padx=10, pady=8)
        
        # Bouton Qwen
        self.btn_qwen = tk.Button(
            btn_frame,
            text="🐉 Ouvrir dans Qwen",
            command=lambda: self._open_in_provider("qwen"),
            bg="#ffaa00",  # Orange
            fg="#1a1a1a",  # Noir
            font=("Consolas", 9, "bold"),
            relief=tk.FLAT,
            padx=12,
            pady=6,
            cursor="hand2",
            state=tk.DISABLED  # Désactivé tant qu'aucune erreur
        )
        self.btn_qwen.pack(side=tk.LEFT, padx=5)
        
        # Bouton ChatGPT
        self.btn_chatgpt = tk.Button(
            btn_frame,
            text="🤖 Ouvrir dans ChatGPT",
            command=lambda: self._open_in_provider("chatgpt"),
            bg="#ff5252",  # Rouge
            fg="white",
            font=("Consolas", 9, "bold"),
            relief=tk.FLAT,
            padx=12,
            pady=6,
            cursor="hand2",
            state=tk.DISABLED
        )
        self.btn_chatgpt.pack(side=tk.LEFT, padx=5)
        
        # Bouton Gemini
        self.btn_gemini = tk.Button(
            btn_frame,
            text="✨ Ouvrir dans Gemini",
            command=lambda: self._open_in_provider("gemini"),
            bg="#64dd17",  # Vert
            fg="#1a237e",  # Bleu foncé
            font=("Consolas", 9, "bold"),
            relief=tk.FLAT,
            padx=12,
            pady=6,
            cursor="hand2",
            state=tk.DISABLED
        )
        self.btn_gemini.pack(side=tk.LEFT, padx=5)
        
        # ════════════════════════════════════════════════════════════════
        # NOTE ÉTHIQUE : Explication transparente
        # ════════════════════════════════════════════════════════════════
        ethical_frame = tk.Frame(self.panel, bg=self.colors["bg_dark"])
        ethical_frame.pack(fill=tk.X, padx=10, pady=(0, 10))
        
        ethical_icon = tk.Label(
            ethical_frame,
            text="🔒",
            bg=self.colors["bg_dark"],
            fg=self.colors["warning"],
            font=("Consolas", 12)
        )
        ethical_icon.pack(side=tk.LEFT, padx=(0, 5))
        
        ethical_text = tk.Label(
            ethical_frame,
            text=(
                "Ces boutons ouvrent ton navigateur — AUCUNE donnée n'est envoyée "
                "sans ton consentement explicite. Confirmation requise avant chaque ouverture."
            ),
            bg=self.colors["bg_dark"],
            fg=self.colors["text_dim"],
            font=("Consolas", 8),
            wraplength=800,
            justify=tk.LEFT
        )
        ethical_text.pack(side=tk.LEFT)
        
        # ════════════════════════════════════════════════════════════════
        # STATUS BAR : État du module
        # ════════════════════════════════════════════════════════════════
        status_frame = tk.Frame(self.panel, bg=self.colors["bg_mid"], height=30)
        status_frame.pack(fill=tk.X, padx=10, pady=(5, 0))
        status_frame.pack_propagate(False)
        
        self.status_label = tk.Label(
            status_frame,
            text="⚪ Panneau désactivé — active le toggle pour visualiser les erreurs",
            bg=self.colors["bg_mid"],
            fg=self.colors["text_dim"],
            font=("Consolas", 9)
        )
        self.status_label.pack(side=tk.LEFT, padx=10)
    
    def _toggle_panel(self):
        """Active/désactive le panneau graphique"""
        if self.toggle_var.get():
            self.panel.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)
            self._update_status("🟢 Panneau activé — en attente d'erreur...")
            self.debugger.log_message(
                "🎨 Visualisation graphique → ACTIVÉE",
                "ai"
            )
        else:
            self.panel.pack_forget()
            self._update_status("⚪ Panneau désactivé")
            self.debugger.log_message(
                "🎨 Visualisation graphique → DÉSACTIVÉE",
                "ai"
            )
    
    def display_error(self, error_type: str, message: str, traceback_lines: list):
        """
        Affiche l'erreur sous forme d'arbre graphique
        
        Args:
            error_type (str): Type de l'erreur (ex: "NameError", "FileNotFoundError")
            message (str): Message d'erreur complet
            traceback_lines (list): Liste des lignes du traceback
        """
        # Sauvegarder l'erreur pour les boutons d'action
        self.last_error = {
            "type": error_type,
            "message": message,
            "traceback": traceback_lines
        }
        
        # Nettoyer l'arbre précédent
        for item in self.tree.get_children():
            self.tree.delete(item)
        
        # Parser le traceback pour extraire fichiers/lignes/fonctions
        nodes = self._parse_traceback(traceback_lines)
        
        # Ajouter le nœud racine (erreur principale)
        root_id = self.tree.insert(
            "", "end",
            text="Erreur",
            values=(
                error_type,
                "—",
                message[:80] + "..." if len(message) > 80 else message
            ),
            tags=("error_root",)
        )
        
        # Style pour le nœud racine
        self.tree.tag_configure(
            "error_root",
            foreground=self.colors["error"],
            font=("Consolas", 10, "bold")
        )
        
        # Ajouter les nœuds de traceback (max 5 pour la lisibilité)
        for i, node in enumerate(nodes[:5]):
            frame_id = self.tree.insert(
                root_id, "end",
                text=f"Frame {i+1}",
                values=(
                    "CallCheck",
                    f"{node['file']}:{node['line']}",
                    node["function"]
                ),
                tags=("traceback",)
            )
            
            # Style pour les nœuds de traceback
            self.tree.tag_configure(
                "traceback",
                foreground=self.colors["info"],
                font=("Consolas", 9)
            )
            
            # Ajouter les détails du frame comme sous-nœud
            if node.get("code"):
                self.tree.insert(
                    frame_id, "end",
                    text="Code",
                    values=("", "", node["code"].strip()),
                    tags=("code",)
                )
                self.tree.tag_configure(
                    "code",
                    foreground=self.colors["warning"],
                    font=("Consolas", 9, "italic")
                )
        
        # Activer les boutons d'action
        self.btn_qwen.config(state=tk.NORMAL)
        self.btn_chatgpt.config(state=tk.NORMAL)
        self.btn_gemini.config(state=tk.NORMAL)
        
        # Développer automatiquement le nœud racine
        self.tree.item(root_id, open=True)
        
        # Mettre à jour le statut
        self._update_status(
            f"✅ Erreur affichée : {error_type} ({len(nodes)} frames)"
        )
        
        self.debugger.log_message(
            f"🎨 Erreur visualisée : {error_type} — {len(nodes)} frames",
            "ai"
        )
    
    def _parse_traceback(self, lines: list) -> list:
        """
        Extrait fichiers/lignes/fonctions du traceback
        
        Args:
            lines (list): Lignes du traceback
        
        Returns:
            list: Liste de dictionnaires avec clés 'file', 'line', 'function', 'code'
        """
        nodes = []
        file_pattern = r'File "(.*?)", line (\d+), in (\w+)'
        code_pattern = r'^\s+(.+)$'  # Ligne de code après le traceback
        
        current_node = None
        capture_code = False
        
        for i, line in enumerate(lines):
            # Rechercher un frame de traceback
            file_match = re.search(file_pattern, line)
            if file_match:
                # Sauvegarder le node précédent s'il existe
                if current_node:
                    nodes.append(current_node)
                
                # Créer un nouveau node
                current_node = {
                    "file": os.path.basename(file_match.group(1)),
                    "line": file_match.group(2),
                    "function": file_match.group(3),
                    "code": None
                }
                capture_code = True
                continue
            
            # Capturer la ligne de code (si disponible)
            if capture_code and current_node and not current_node["code"]:
                code_match = re.match(code_pattern, line)
                if code_match:
                    current_node["code"] = code_match.group(1)[:60]  # Tronquer
                    capture_code = False
        
        # Ajouter le dernier node
        if current_node:
            nodes.append(current_node)
        
        return nodes
    
    def _open_in_provider(self, provider: str):
        """
        Ouvre l'erreur dans le navigateur — 100% transparent
        
        Args:
            provider (str): "qwen", "chatgpt" ou "gemini"
        """
        if not self.last_error:
            return
        
        # 🔒 BOÎTE DE DIALOGUE DE CONSENTEMENT AVANT OUVERTURE
        provider_names = {
            "qwen": "Qwen (Alibaba Cloud)",
            "chatgpt": "ChatGPT (OpenAI)",
            "gemini": "Gemini (Google)"
        }
        
        provider_name = provider_names.get(provider, provider.upper())
        
        confirm = messagebox.askyesno(
            "🔒 Confirmation de Privacy — Kerberos Debugger",
            f"ALERTE DE CONFIDENTIALITÉ :\n\n"
            f"Tu es sur le point d'ouvrir cette erreur dans {provider_name} :\n\n"
            f"• Tes données Python quitteront TON ordinateur\n"
            f"• Elles seront traitées par les serveurs de {provider.upper()}\n"
            f"• L'erreur inclut potentiellement du code source SENSIBLE\n\n"
            f"⚠️ NE CONFIRME PAS si ton code est :\n"
            f"  - Propriétaire / confidentiel\n"
            f"  - Lié à des projets personnels/métaphysiques\n"
            f"  - Contient des données privées\n\n"
            f"Confirmer l'ouverture dans ton navigateur ?",
            icon="warning",
            parent=self.panel
        )
        
        if not confirm:
            self.debugger.log_message(
                f"🔒 Ouverture vers {provider.upper()} annulée par l'utilisateur",
                "success"
            )
            return
        
        # Construire le message à envoyer
        error_text = (
            f"Type: {self.last_error['type']}\n"
            f"Message: {self.last_error['message']}\n\n"
            f"Traceback:\n" + "\n".join(self.last_error['traceback'])
        )
        
        # Encoder pour URL
        query = urllib.parse.quote(
            f"Debug this Python error:\n\n{error_text}\n\n"
            f"Provide a concise fix in French."
        )
        
        # URL selon le provider
        urls = {
            "qwen": f"https://chat.qwen.ai/?q={query}",
            "chatgpt": f"https://chatgpt.com/?q={query}",
            "gemini": f"https://gemini.google.com/app?q={query}"
        }
        
        target_url = urls.get(provider, "https://chat.qwen.ai")
        
        try:
            # Ouvrir dans le navigateur par défaut
            webbrowser.open(target_url)
            
            self.debugger.log_message(
                f"🌐 Navigateur ouvert vers {provider.upper()} — données partagées AVEC consentement",
                "warning"
            )
            
            self._update_status(
                f"🌐 Ouvert dans {provider.upper()} — consentement donné"
            )
            
            # Optionnel : désactiver temporairement les boutons
            self.btn_qwen.config(state=tk.DISABLED)
            self.btn_chatgpt.config(state=tk.DISABLED)
            self.btn_gemini.config(state=tk.DISABLED)
            
        except Exception as e:
            self.debugger.log_message(
                f"❌ Erreur ouverture navigateur : {e}",
                "error"
            )
            messagebox.showerror(
                "Erreur",
                f"Impossible d'ouvrir le navigateur :\n{e}",
                parent=self.panel
            )
    
    def _update_status(self, message: str):
        """Met à jour le label de statut"""
        self.status_label.config(text=message)
    
    def clear(self):
        """Nettoie le panneau (à appeler entre deux exécutions)"""
        # Nettoyer l'arbre
        for item in self.tree.get_children():
            self.tree.delete(item)
        
        # Désactiver les boutons
        self.btn_qwen.config(state=tk.DISABLED)
        self.btn_chatgpt.config(state=tk.DISABLED)
        self.btn_gemini.config(state=tk.DISABLED)
        
        # Réinitialiser l'erreur sauvegardée
        self.last_error = None
        
        # Mettre à jour le statut
        if self.toggle_var.get():
            self._update_status("⚪ En attente d'erreur...")
        
        self.debugger.log_message(
            "🎨 Panneau graphique réinitialisé",
            "ai"
        )
    
    def is_enabled(self) -> bool:
        """Retourne True si le panneau est activé"""
        return self.toggle_var.get()
    
    def destroy(self):
        """Détruit le panneau proprement"""
        self.clear()
        self.panel.destroy()
        self.debugger.log_message(
            "🎨 Module graphique détruit",
            "ai"
        )


# ════════════════════════════════════════════════════════════════════════════
# TEST UNITAIRE (optionnel — exécute ce fichier seul pour tester)
# ════════════════════════════════════════════════════════════════════════════

if __name__ == "__main__":
    print("🧪 Test unitaire : VisualErrorsPanel")
    print("=" * 60)
    
    # Créer une fenêtre Tkinter de test
    root = tk.Tk()
    root.title("Test VisualErrorsPanel")
    root.geometry("900x600")
    root.configure(bg="#0a0e17")
    
    # Frame parent
    parent_frame = tk.Frame(root, bg="#0a0e17")
    parent_frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)
    
    # Stub debugger pour les logs
    class StubDebugger:
        def log_message(self, msg, tag=""):
            print(f"[LOG] {msg}")
    
    debugger = StubDebugger()
    
    # Créer le panneau
    panel = VisualErrorsPanel(parent_frame, debugger)
    
    # Simuler une erreur
    def simulate_error():
        error_type = "NameError"
        message = "name 'x' is not defined"
        traceback_lines = [
            '  File "test_script.py", line 10, in <module>',
            '    print(x)',
            '  File "test_script.py", line 5, in calculate',
            '    result = x + y',
            '  File "utils.py", line 15, in helper',
            '    return process(data)'
        ]
        
        panel.display_error(error_type, message, traceback_lines)
    
    # Bouton de test
    test_btn = tk.Button(
        root,
        text="🧪 Simuler une Erreur",
        command=simulate_error,
        bg="#6c5ce7",
        fg="white",
        font=("Consolas", 10, "bold"),
        relief=tk.FLAT,
        padx=20,
        pady=10
    )
    test_btn.pack(pady=10)
    
    # Lancer la boucle Tkinter
    print("✅ Panneau créé — fenêtre Tkinter ouverte")
    print("👉 Clique sur le toggle pour activer le panneau")
    print("👉 Clique sur 'Simuler une Erreur' pour tester")
    print("=" * 60)
    
    root.mainloop()