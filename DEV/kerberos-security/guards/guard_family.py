# === DANS LE PC MÈRE (guard_family_network.py) ===

class KerberosMotherTree:
    """
    PC Mère — Détecte et nourrit les graines
    """
    
    def __init__(self):
        self.seeds = {}  # Graines détectées
        self.kerberos_package = self._prepare_package()
    
    def _prepare_package(self):
        """Prépare le package Kerberos complet"""
        package = {
            "main_file": (KERBEROS_ROOT / "kerberos.ultimate.py").read_bytes(),
            "guards": [],
            "libs": [],
            "config": [],
            "total_size": 0
        }
        
        # Ajoute guards
        for guard_file in GUARDS_DIR.glob("*.py"):
            package["guards"].append({
                "name": f"guards/{guard_file.name}",
                "content": guard_file.read_bytes()
            })
        
        # Calcule taille totale
        package["total_size"] = len(package["main_file"])
        for guard in package["guards"]:
            package["total_size"] += len(guard["content"])
        
        return package
    
    def listen_for_seeds(self):
        """Écoute les graines sur le réseau"""
        sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        sock.bind(('', DISCOVERY_PORT))
        
        print("🌳 [Mère] Écoute des graines...")
        
        while True:
            data, addr = sock.recvfrom(4096)
            message = json.loads(data.decode())
            
            if message["type"] == "seed_hello":
                self._handle_seed_hello(message, addr)
    
    def _handle_seed_hello(self, message, addr):
        """Répond à une graine"""
        seed_ip = addr[0]
        graine_id = message["graine_id"]
        
        print(f"\n🌱 [Mère] Graine détectée : {graine_id}")
        print(f"   └─ IP: {seed_ip}")
        print(f"   └─ Hôte: {message['hostname']}")
        
        # Ajoute aux graines connues
        self.seeds[graine_id] = {
            "ip": seed_ip,
            "hostname": message["hostname"],
            "discovered_at": time.time(),
            "stage": "seed",
            "last_contact": time.time()
        }
        
        # Répond
        response = json.dumps({
            "type": "mother_response",
            "hostname": socket.gethostname(),
            "maturity": self.calculate_maturity_level(),
            "guards_count": len(self.kerberos_package["guards"]),
            "ready": True
        })
        
        sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        sock.sendto(response.encode(), addr)
        sock.close()
        
        # Lance installation
        threading.Thread(
            target=self._install_to_seed,
            args=(seed_ip, graine_id),
            daemon=True
        ).start()
    
    def _install_to_seed(self, seed_ip, graine_id):
        """Installe Kerberos sur la graine"""
        print(f"\n📦 [Mère] Installation vers {seed_ip}...")
        
        try:
            sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            sock.settimeout(60)
            sock.connect((seed_ip, SYNC_PORT))
            
            # Envoie fichier principal
            self._send_file(sock, "kerberos.ultimate.py", 
                          self.kerberos_package["main_file"])
            
            # Envoie guards
            for guard in self.kerberos_package["guards"]:
                self._send_file(sock, guard["name"], guard["content"])
            
            # Envoie completion
            completion = json.dumps({
                "type": "installation_complete",
                "total_files": len(self.kerberos_package["guards"]) + 1,
                "total_size": self.kerberos_package["total_size"]
            })
            sock.sendall(completion.encode())
            
            sock.close()
            
            print(f"✅ [Mère] Installation terminée vers {seed_ip}")
            
            # Met à jour statut
            if graine_id in self.seeds:
                self.seeds[graine_id]["stage"] = "sprout"
                self.seeds[graine_id]["installed_at"] = time.time()
            
        except Exception as e:
            print(f"❌ [Mère] Erreur installation : {e}")
    
    def _send_file(self, sock, name, content):
        """Envoie un fichier"""
        # Header
        header = json.dumps({
            "type": "package_start",
            "name": name,
            "size": len(content)
        })
        sock.sendall(header.encode())
        
        # Contenu
        sock.sendall(content)
        
        print(f"   └─ {name} ({len(content)} bytes)")
    
    def monitor_seeds(self):
        """Surveille la croissance des graines"""
        while True:
            for graine_id, seed in list(self.seeds.items()):
                # Si pas de nouvelles depuis 5 min
                if time.time() - seed["last_contact"] > 300:
                    print(f"💀 [Mère] Graine perdue : {graine_id}")
                    del self.seeds[graine_id]
                    continue
                
                # Affiche progression
                print(f"📊 [Mère] {seed['hostname']} — Stage: {seed['stage']}")
            
            time.sleep(60)
    
    def get_seed_status(self):
        """Retourne statut des graines"""
        return {
            "total_seeds": len(self.seeds),
            "seeds": [
                {
                    "id": gid,
                    "hostname": s["hostname"],
                    "stage": s["stage"],
                    "uptime": time.time() - s["discovered_at"]
                }
                for gid, s in self.seeds.items()
            ]
        }

# ============================================================================
# === UI : ONGLET GRAINES ====================================================
# ============================================================================

def _create_seeds_tab(self, nb):
    """Onglet montrant les graines en croissance"""
    tab = ttk.Frame(nb)
    nb.add(tab, text=' 🌱 Graines ')
    
    frame = tk.LabelFrame(tab, text=" 🌳 Graines en Croissance ",
        bg='#1e1e2e', fg='#00ffcc', font=("Consolas", 11, "bold"))
    frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)
    
    # Canvas pour dessiner les graines
    canvas = tk.Canvas(frame, bg='#0a0f1a', height=400)
    canvas.pack(fill=tk.BOTH, expand=True)
    
    # Dessine le PC Mère au centre
    cx, cy = 400, 80
    canvas.create_oval(cx-60, cy-60, cx+60, cy+60,
                      fill='#4CAF50', outline='#00ffcc', width=3)
    canvas.create_text(cx, cy-20, text="🌳", font=("Consolas", 40))
    canvas.create_text(cx, cy+20, text="PC MÈRE",
                      font=("Consolas", 12, "bold"), fill='white')
    canvas.create_text(cx, cy+40, text=f"{mother_tree.calculate_maturity_level()}%",
                      font=("Consolas", 10), fill='white')
    
    # Dessine les graines en dessous
    seed_y = 250
    seed_x_start = 100
    seed_spacing = 150
    
    def update_seeds_display():
        canvas.delete("seeds")
        
        seeds = mother_tree.get_seed_status()["seeds"]
        for i, seed in enumerate(seeds):
            seed_x = seed_x_start + (i * seed_spacing)
            
            # Ligne mycélienne
            canvas.create_line(cx, cy+60, seed_x, seed_y-40,
                              fill='#8B4513', width=3, dash=(5, 5), tags="seeds")
            
            # Emoji selon stage
            stage_emoji = {"seed": "🌰", "sprout": "🌱", "sapling": "🌿", "mature": "🌳"}
            emoji = stage_emoji.get(seed["stage"], "🌱")
            
            # Cercle graine
            canvas.create_oval(seed_x-40, seed_y-40, seed_x+40, seed_y+40,
                              fill='#ffeb3b', outline='#00ffcc', width=2, tags="seeds")
            canvas.create_text(seed_x, seed_y-15, text=emoji,
                              font=("Consolas", 24), tags="seeds")
            canvas.create_text(seed_x, seed_y+10, text=seed["hostname"][:10],
                              font=("Consolas", 9), fill='white', tags="seeds")
            canvas.create_text(seed_x, seed_y+25, text=seed["stage"],
                              font=("Consolas", 8), fill='white', tags="seeds")
        
        # Mise à jour
        if not _is_app_closing():
            self.root.after(5000, update_seeds_display)
    
    update_seeds_display()
    
    # Stats
    stats_frame = tk.Frame(frame, bg='#1e1e2e')
    stats_frame.pack(fill=tk.X, pady=10)
    tk.Label(stats_frame, text="📊 Total graines: 0 | En croissance: 0 | Matures: 0",
            bg='#1e1e2e', fg='#00ffcc', font=("Consolas", 10)).pack()