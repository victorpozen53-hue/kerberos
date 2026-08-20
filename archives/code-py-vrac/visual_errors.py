# X:\debug-plus\IA\graphique\visual_errors.py
"""
Module graphique léger pour visualiser les erreurs Python
→ Aucune IA embarquée
→ Aucune connexion réseau silencieuse
→ Ouverture navigateur uniquement sur action EXPLICITE de l'utilisateur
GPLv3 - Victor Pozen © 2026
"""

import tkinter as tk
from tkinter import ttk, scrolledtext
import re
import webbrowser
import urllib.parse
import os

class VisualErrorsPanel:
    """
    Panneau graphique optionnel pour visualiser les erreurs sous forme d'arbre
    → S'active via toggle dans l'UI principale
    → Zéro connexion réseau sans action consciente de l'utilisateur
    """
    
    def __init__(self, parent_frame: tk.Frame, debugger_instance):
        self.parent = parent_frame
        self.debugger = debugger_instance
        self.enabled = False
        self.last_error = None
        
        # Création du panneau (initialement caché)
        self.panel = tk.Frame(self.parent, bg="#0a0e17", relief=tk.RAISED, borderwidth=1)
        self.panel.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)
        self.panel.pack_forget()  # Caché par défaut
        
        # Widgets internes
        self._create_widgets()
    
    def _create_widgets(self):
        """Crée l'interface graphique du panneau"""
        # Titre avec toggle
        header = tk.Frame(self.panel, bg="#0a0e17")
        header.pack(fill=tk.X, padx=10, pady=8)
        
        self.toggle_var = tk.BooleanVar(value=False)
        toggle = tk.Checkbutton(
            header,
            text="🎨 Visualisation Graphique des Erreurs",
            variable=self.toggle_var,
            command=self._toggle_panel,
            bg="#0a0e17",
            fg="#6c5ce7",
            selectcolor="#121826",
            font=("Consolas", 10, "bold")
        )
        toggle.pack(side=tk.LEFT)
        
        # Zone d'arbre des erreurs
        tree_frame = tk.Frame(self.panel, bg="#0f172a")
        tree_frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=5)
        
        # Style pour le Treeview
        style = ttk.Style()
        style.configure("ErrorTree.Treeview",
            background="#1e273a",
            foreground="#55efc4",
            fieldbackground="#1e273a",
            font=("Consolas", 10)
        )
        style.map("ErrorTree.Treeview",
            background=[("selected", "#6c5ce7")],
            foreground=[("selected", "white")]
        )
        
        # Treeview pour l'arbre des erreurs
        self.tree = ttk.Treeview(
            tree_frame,
            columns=("type", "location", "message"),
            show="headings",
            style="ErrorTree.Treeview"
        )
        self.tree.heading("type", text="Type")
        self.tree.heading("location", text="Fichier:Ligne")
        self.tree.heading("message", text="Message")
        
        self.tree.column("type", width=120, anchor=tk.W)
        self.tree.column("location", width=180, anchor=tk.W)
        self.tree.column("message", width=400, anchor=tk.W)
        
        # Scrollbars
        vsb = ttk.Scrollbar(tree_frame, orient="vertical", command=self.tree.yview)
        hsb = ttk.Scrollbar(tree_frame, orient="horizontal", command=self.tree.xview)
        self.tree.configure(yscrollcommand=vsb.set, xscrollcommand=hsb.set)
        
        self.tree.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        vsb.pack(side=tk.RIGHT, fill=tk.Y)
        hsb.pack(side=tk.BOTTOM, fill=tk.X)
        
        # Boutons d'action (100% transparents)
        btn_frame = tk.Frame(self.panel, bg="#0a0e17")
        btn_frame.pack(fill=tk.X, padx=10, pady=8)
        
        self.btn_qwen = tk.Button(
            btn_frame,
            text="🐉 Ouvrir dans Qwen",
            command=lambda: self._open_in_provider("qwen"),
            bg="#ffaa00", fg="#1a1a1a",
            font=("Consolas", 9, "bold"),
            relief=tk.FLAT,
            padx=10, pady=5
        )
        self.btn_qwen.pack(side=tk.LEFT, padx=5)
        self.btn_qwen.config(state=tk.DISABLED)  # Désactivé tant qu'aucune erreur
        
        self.btn_chatgpt = tk.Button(
            btn_frame,
            text="🤖 Ouvrir dans ChatGPT",
            command=lambda: self._open_in_provider("chatgpt"),
            bg="#ff5252", fg="white",
            font=("Consolas", 9, "bold"),
            relief=tk.FLAT,
            padx=10, pady=5
        )
        self.btn_chatgpt.pack(side=tk.LEFT, padx=5)
        self.btn_chatgpt.config(state=tk.DISABLED)
        
        self.btn_gemini = tk.Button(
            btn_frame,
            text="✨ Ouvrir dans Gemini",
            command=lambda: self._open_in_provider("gemini"),
            bg="#64dd17", fg="#1a237e",
            font=("Consolas", 9, "bold"),
            relief=tk.FLAT,
            padx=10, pady=5
        )
        self.btn_gemini.pack(side=tk.LEFT, padx=5)
        self.btn_gemini.config(state=tk.DISABLED)
        
        # Zone d'explication éthique
        ethical_note = tk.Label(
            btn_frame,
            text="ℹ️ Ces boutons ouvrent ton navigateur — AUCUNE donnée n'est envoyée sans ton consentement explicite",
            bg="#0a0e17",
            fg="#636e72",
            font=("Consolas", 8),
            anchor=tk.W
        )
        ethical_note.pack(side=tk.LEFT, padx=20)
    
    def _toggle_panel(self):
        """Active/désactive le panneau graphique"""
        if self.toggle_var.get():
            self.panel.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)
            self.debugger.log_message("🎨 Visualisation graphique → ACTIVÉE", "ai")
        else:
            self.panel.pack_forget()
            self.debugger.log_message("🎨 Visualisation graphique → DÉSACTIVÉE", "ai")
    
    def display_error(self, error_type: str, message: str, traceback_lines: list):
        """Affiche l'erreur sous forme d'arbre graphique"""
        self.last_error = {
            "type": error_type,
            "message": message,
            "traceback": traceback_lines
        }
        
        # Nettoyer l'arbre précédent
        for item in self.tree.get_children():
            self.tree.delete(item)
        
        # Parser le traceback pour extraire fichiers/lignes
        nodes = self._parse_traceback(traceback_lines)
        
        # Ajouter le nœud racine (erreur principale)
        root_id = self.tree.insert(
            "", "end",
            text="Erreur",
            values=(error_type, "—", message[:80] + "..." if len(message) > 80 else message),
            tags=("error_root",)
        )
        self.tree.tag_configure("error_root", foreground="#ff5252", font=("Consolas", 10, "bold"))
        
        # Ajouter les nœuds de traceback
        for i, node in enumerate(nodes):
            self.tree.insert(
                root_id, "end",
                text=f"Frame {i+1}",
                values=("CallCheck", f"{node['file']}:{node['line']}", node["function"]),
                tags=("traceback",)
            )
        
        # Activer les boutons
        self.btn_qwen.config(state=tk.NORMAL)
        self.btn_chatgpt.config(state=tk.NORMAL)
        self.btn_gemini.config(state=tk.NORMAL)
        
        # Développer automatiquement le nœud racine
        self.tree.item(root_id, open=True)
    
    def _parse_traceback(self, lines: list) -> list:
        """Extrait fichiers/lignes/fonctions du traceback"""
        nodes = []
        pattern = r'File "(.*?)", line (\d+), in (\w+)'
        
        for line in lines:
            match = re.search(pattern, line)
            if match:
                nodes.append({
                    "file": os.path.basename(match.group(1)),
                    "line": match.group(2),
                    "function": match.group(3)
                })
        return nodes[-5:]  # Limiter à 5 frames max pour la lisibilité
    
    def _open_in_provider(self, provider: str):
        """Ouvre l'erreur dans le navigateur — 100% transparent"""
        if not self.last_error:
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
        
        # 🔒 AVERTISSEMENT ÉTHIQUE AVANT OUVERTURE
        confirm = tk.messagebox.askyesno(
            "🔒 Confirmation de Privacy",
            f"Tu es sur le point d'ouvrir cette erreur dans {provider.upper()} :\n\n"
            f"• Tes données quitteront ton ordinateur\n"
            f"• Elles seront traitées par les serveurs de {provider.upper()}\n"
            f"• Ne JAMAIS faire cela avec du code sensible\n\n"
            f"Confirmer l'ouverture dans ton navigateur ?",
            icon="warning"
        )
        
        if confirm:
            webbrowser.open(target_url)
            self.debugger.log_message(
                f"🌐 Navigateur ouvert vers {provider.upper()} — données partagées avec ton consentement",
                "warning"
            )
        else:
            self.debugger.log_message(
                f"🔒 Ouverture annulée par l'utilisateur — privacy préservée",
                "success"
            )
    
    def clear(self):
        """Nettoie le panneau"""
        for item in self.tree.get_children():
            self.tree.delete(item)
        self.btn_qwen.config(state=tk.DISABLED)
        self.btn_chatgpt.config(state=tk.DISABLED)
        self.btn_gemini.config(state=tk.DISABLED)
        self.last_error = None