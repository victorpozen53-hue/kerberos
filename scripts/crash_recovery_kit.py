#!/usr/bin/env python3
"""
╔══════════════════════════════════════════════════════════════╗
║         CRASH RECOVERY KIT  —  v1.0                        ║
║   Kit clé USB pour récupération HDD head crash             ║
║                                                              ║
║  UTILISATION SUR PC SACRIFICIEL :                          ║
║  1. Brancher le HDD 1TB de destination                     ║
║  2. Booter le PC normalement                               ║
║  3. Lancer ce script EN ADMIN                              ║
║  4. Brancher le HDD crashé À CHAUD                         ║
║  5. Suivre les instructions à l'écran                      ║
║                                                              ║
║  python crash_recovery_kit.py                              ║
╚══════════════════════════════════════════════════════════════╝
"""

import os, sys, time, struct, threading, ctypes, json, queue
import subprocess, platform, hashlib
from pathlib import Path
from datetime import datetime
from tkinter import *
from tkinter import ttk, messagebox
import tkinter as tk

if platform.system() != 'Windows':
    print("Ce kit est pour Windows uniquement.")
    sys.exit(0)

import winreg

# ═══════════════════════════════════════════════════════════════
# COULEURS
# ═══════════════════════════════════════════════════════════════
C = {
    'bg':     '#0A0C10', 'bg2':   '#12151F', 'bg3':   '#1A1E2E',
    'bg4':    '#222638', 'panel': '#060810',
    'accent': '#00E5FF', 'green': '#00FF9D', 'yellow':'#FFD23F',
    'red':    '#FF3860', 'orange':'#FF6B35', 'purple':'#B794F4',
    'text':   '#CDD6F4', 'text2': '#6C7086', 'text3': '#45475A',
    'border': '#2A2D3E',
}
FN  = ('Consolas', 10)
FNS = ('Consolas', 9)
FNB = ('Consolas', 12, 'bold')
FNT = ('Consolas', 15, 'bold')
FNM = ('Courier New', 9)

# ═══════════════════════════════════════════════════════════════
# DISK MANAGER
# ═══════════════════════════════════════════════════════════════
class DiskManager:
    """Gestion des disques physiques Windows"""

    def list_disks(self) -> list:
        """Liste tous les disques via PowerShell"""
        try:
            ps = ('Get-Disk | Select-Object Number,FriendlyName,Size,'
                  'HealthStatus,OperationalStatus,BusType,PartitionStyle | '
                  'ConvertTo-Json -Compress')
            out = subprocess.check_output(
                ['powershell','-NoProfile','-Command', ps],
                timeout=15, stderr=subprocess.DEVNULL,
                creationflags=subprocess.CREATE_NO_WINDOW)
            data = json.loads(out.decode('utf-8','replace'))
            if isinstance(data, dict): data = [data]
            disks = []
            for d in (data or []):
                if not isinstance(d, dict): continue
                disks.append({
                    'number':    d.get('Number', 0),
                    'name':      d.get('FriendlyName','?'),
                    'size':      d.get('Size', 0),
                    'size_str':  self._fmt(d.get('Size',0)),
                    'health':    d.get('HealthStatus','?'),
                    'status':    d.get('OperationalStatus','?'),
                    'bus':       d.get('BusType','?'),
                    'partition': d.get('PartitionStyle','?'),
                    'path':      f"\\\\.\\PhysicalDrive{d.get('Number',0)}",
                })
            return disks
        except Exception as e:
            return []

    def get_disk_size(self, disk_num: int) -> int:
        try:
            h = ctypes.windll.kernel32.CreateFileW(
                f"\\\\.\\PhysicalDrive{disk_num}",
                0x80000000, 0x3, None, 3, 0, None)
            if h == ctypes.c_void_p(-1).value: return 0
            size = ctypes.c_ulonglong(0)
            ctypes.windll.kernel32.DeviceIoControl(
                h, 0x70000,  # IOCTL_DISK_GET_DRIVE_GEOMETRY_EX approx
                None, 0, ctypes.byref(size), 8, None, None)
            ctypes.windll.kernel32.CloseHandle(h)
            return size.value
        except: return 0

    @staticmethod
    def _fmt(s: int) -> str:
        if not s: return '?'
        for u in ['B','KB','MB','GB','TB']:
            if s < 1024: return f"{s:.1f} {u}"
            s /= 1024
        return f"{s:.1f} PB"

    def is_admin(self) -> bool:
        try: return bool(ctypes.windll.shell32.IsUserAnAdmin())
        except: return False


# ═══════════════════════════════════════════════════════════════
# IMAGE ENGINE  — Lecture raw avec retry + majority voting
# ═══════════════════════════════════════════════════════════════
class ImageEngine:
    BLOCK = 65536  # 64 KB par bloc

    def __init__(self, src_num: int, dst_path: str,
                 log_cb=None, progress_cb=None, done_cb=None):
        self.src_num    = src_num
        self.dst_path   = dst_path
        self.log        = log_cb or print
        self.prog       = progress_cb or (lambda *a: None)
        self.done_cb    = done_cb or (lambda *a: None)
        self.running    = True
        self.stats      = {
            'bytes_total': 0, 'bytes_done': 0,
            'blocks_ok': 0, 'blocks_bad': 0,
            'bad_sectors': [], 'start_time': 0,
            'speed': 0, 'eta': 0,
        }

    def stop(self): self.running = False

    def run(self):
        src_path = f"\\\\.\\PhysicalDrive{self.src_num}"
        self.stats['start_time'] = time.time()
        self.log(f"Source  : {src_path}", 'info')
        self.log(f"Dest    : {self.dst_path}", 'info')

        # Ouvrir source
        src = ctypes.windll.kernel32.CreateFileW(
            src_path, 0x80000000, 0x3, None, 3, 0x20000000, None)
        if src == ctypes.c_void_p(-1).value:
            self.log("✗ Impossible d'ouvrir le disque source", 'err')
            self.log("  → Vérifiez que le HDD est bien branché", 'warn')
            self.done_cb(False, self.stats); return

        # Taille du disque
        size_buf = ctypes.create_string_buffer(24)
        ret_bytes = ctypes.c_ulong(0)
        ctypes.windll.kernel32.DeviceIoControl(
            src, 0x00070000, None, 0,
            size_buf, 24, ctypes.byref(ret_bytes), None)
        try:
            # DISK_GEOMETRY: cylinders(8), media(4), trk/cyl(4), sec/trk(4), bytes/sec(4)
            geom = struct.unpack_from('<qIIII', size_buf)
            disk_size = geom[0] * geom[2] * geom[3] * geom[4]
        except:
            disk_size = 0

        # Fallback taille via SetFilePointer
        if not disk_size:
            hi = ctypes.c_long(0)
            lo = ctypes.windll.kernel32.SetFilePointer(src, 0, ctypes.byref(hi), 2)
            disk_size = (hi.value << 32) | (lo & 0xFFFFFFFF)
            ctypes.windll.kernel32.SetFilePointer(src, 0, None, 0)

        if not disk_size:
            self.log("✗ Impossible de lire la taille du disque", 'err')
            self.log("  → Le disque est peut-être trop endommagé", 'warn')
            ctypes.windll.kernel32.CloseHandle(src)
            self.done_cb(False, self.stats); return

        self.stats['bytes_total'] = disk_size
        self.log(f"Taille  : {disk_size/1e9:.1f} GB ({disk_size:,} bytes)", 'ok')
        self.log(f"Début de l'image — patience...", 'title')

        Path(self.dst_path).parent.mkdir(parents=True, exist_ok=True)

        try:
            with open(self.dst_path, 'wb') as dst:
                offset    = 0
                last_prog = time.time()
                last_bytes= 0

                while offset < disk_size and self.running:
                    to_read = min(self.BLOCK, disk_size - offset)
                    data    = self._read_block(src, offset, to_read)

                    if data:
                        dst.write(data)
                        self.stats['blocks_ok'] += 1
                    else:
                        # Bloc bad → zéros + log
                        dst.write(b'\x00' * to_read)
                        self.stats['blocks_bad'] += 1
                        sector = offset // 512
                        self.stats['bad_sectors'].append(sector)
                        if len(self.stats['bad_sectors']) % 10 == 1:
                            self.log(f"  ⚠ Bad sector ~{sector:,} (offset 0x{offset:X})", 'warn')

                    offset += to_read
                    self.stats['bytes_done'] = offset

                    # Progression toutes les 2 secondes
                    now = time.time()
                    if now - last_prog >= 2:
                        elapsed  = now - self.stats['start_time']
                        speed    = (offset - last_bytes) / (now - last_prog)
                        remaining= (disk_size - offset) / max(speed, 1)
                        self.stats['speed'] = speed
                        self.stats['eta']   = remaining
                        pct = offset / disk_size * 100
                        self.prog(pct, offset, disk_size, speed, remaining,
                                  self.stats['blocks_bad'])
                        last_prog  = now
                        last_bytes = offset

        except Exception as e:
            self.log(f"✗ Erreur écriture: {e}", 'err')
            ctypes.windll.kernel32.CloseHandle(src)
            self.done_cb(False, self.stats); return

        ctypes.windll.kernel32.CloseHandle(src)

        if self.running:
            elapsed = time.time() - self.stats['start_time']
            self.log(f"\n✓ Image terminée !", 'ok')
            self.log(f"  Durée    : {elapsed/60:.1f} minutes", 'ok')
            self.log(f"  OK       : {self.stats['blocks_ok']:,} blocs", 'ok')
            self.log(f"  Bad      : {self.stats['blocks_bad']:,} blocs", 'warn' if self.stats['blocks_bad'] else 'ok')
            self.log(f"  Fichier  : {self.dst_path}", 'ok')
            # Sauvegarder rapport bad sectors
            self._save_bad_sectors_report()
            self.done_cb(True, self.stats)
        else:
            self.log("⏹ Arrêté par l'utilisateur", 'warn')
            self.done_cb(False, self.stats)

    def _read_block(self, handle, offset: int, size: int,
                    retries: int = 8) -> bytes | None:
        """Lecture avec retry + majority voting"""
        reads = []
        for attempt in range(retries):
            if not self.running: return None
            try:
                # Positionner
                hi = ctypes.c_long(offset >> 32)
                lo_result = ctypes.windll.kernel32.SetFilePointer(
                    handle, offset & 0xFFFFFFFF, ctypes.byref(hi), 0)
                if lo_result == 0xFFFFFFFF: raise IOError("SetFilePointer failed")

                buf  = ctypes.create_string_buffer(size)
                read = ctypes.c_ulong(0)
                ok   = ctypes.windll.kernel32.ReadFile(
                    handle, buf, size, ctypes.byref(read), None)

                if ok and read.value > 0:
                    data = bytes(buf[:read.value])
                    # Padding si lecture partielle
                    if read.value < size:
                        data += b'\x00' * (size - read.value)
                    reads.append(data)
                    if attempt == 0: return data  # Premier essai OK → rapide
                    break
            except:
                pass
            # Attente progressive
            time.sleep(0.02 * (2 ** min(attempt, 4)))

        if len(reads) == 1: return reads[0]
        if len(reads) > 1:  return self._vote(reads, size)
        return None

    def _vote(self, reads: list, size: int) -> bytes:
        """Majority voting sur plusieurs lectures"""
        result = bytearray(size)
        for i in range(size):
            votes = [r[i] for r in reads if i < len(r)]
            result[i] = max(set(votes), key=votes.count) if votes else 0
        return bytes(result)

    def _save_bad_sectors_report(self):
        if not self.stats['bad_sectors']: return
        rp = Path(self.dst_path).with_suffix('.bad_sectors.txt')
        with open(rp, 'w') as f:
            f.write(f"Bad sectors rapport — {datetime.now()}\n")
            f.write(f"Source: PhysicalDrive{self.src_num}\n")
            f.write(f"Total bad: {len(self.stats['bad_sectors'])}\n\n")
            for s in self.stats['bad_sectors']:
                f.write(f"Secteur {s} (LBA 0x{s:X})\n")
        self.log(f"  Rapport bad sectors: {rp.name}", 'info')


# ═══════════════════════════════════════════════════════════════
# APPLICATION
# ═══════════════════════════════════════════════════════════════
class CrashRecoveryKit(Tk):
    def __init__(self):
        super().__init__()
        self.title("CRASH RECOVERY KIT  —  HDD Head Crash Recovery")
        self.geometry("900x700")
        self.minsize(800, 600)
        self.configure(bg=C['bg'])

        self.dm      = DiskManager()
        self.engine  = None
        self.q       = queue.Queue()
        self.running = False
        self.disks   = []
        self.src_var = StringVar()
        self.dst_var = StringVar()
        self.step    = 0  # 0=select, 1=imaging, 2=done

        self._style()
        self._ui()
        self._poll()

        # Check admin
        if not self.dm.is_admin():
            messagebox.showwarning("Admin requis",
                "⚠ Lancez ce script EN ADMINISTRATEUR\n\n"
                "Clic droit → Exécuter en tant qu'administrateur\n\n"
                "Sans admin, la lecture du disque sera bloquée.")

        # Charger les disques
        threading.Thread(target=self._load_disks, daemon=True).start()

    def _style(self):
        s = ttk.Style(self); s.theme_use('clam')
        s.configure('.', background=C['bg'], foreground=C['text'], font=FN)
        s.configure('TFrame', background=C['bg'])
        s.configure('TLabel', background=C['bg'], foreground=C['text'])
        s.configure('TLabelframe', background=C['bg2'], foreground=C['accent'], relief='flat')
        s.configure('TLabelframe.Label', background=C['bg2'], foreground=C['accent'], font=('Consolas',9,'bold'))
        s.configure('TProgressbar', troughcolor=C['bg3'], background=C['green'], thickness=8)
        s.configure('Treeview', background=C['bg2'], foreground=C['text'],
                    fieldbackground=C['bg2'], rowheight=26, borderwidth=0, font=FN)
        s.configure('Treeview.Heading', background=C['bg4'], foreground=C['accent'],
                    font=('Consolas',9,'bold'), relief='flat')
        s.map('Treeview', background=[('selected',C['bg4'])], foreground=[('selected',C['accent'])])

    def _ui(self):
        # Header
        hdr = Frame(self, bg=C['panel'], height=56); hdr.pack(fill=X); hdr.pack_propagate(False)
        Frame(hdr, bg=C['red'], width=4).pack(side=LEFT, fill=Y)
        lg = Frame(hdr, bg=C['panel']); lg.pack(side=LEFT, padx=14, pady=8)
        Label(lg, text="💀 CRASH RECOVERY KIT", font=FNT, bg=C['panel'], fg=C['red']).pack(anchor=W)
        Label(lg, text="Récupération HDD Head Crash  •  Image DD  •  Majority Voting",
              font=FNS, bg=C['panel'], fg=C['text2']).pack(anchor=W)

        # Steps indicator
        steps = Frame(self, bg=C['bg3'], height=36); steps.pack(fill=X); steps.pack_propagate(False)
        self.step_labels = []
        for i, txt in enumerate(['1. Sélectionner les disques', '2. Créer l\'image DD', '3. Terminé — Phantom Recover !']):
            f = Frame(steps, bg=C['bg3']); f.pack(side=LEFT, padx=20, pady=8)
            lbl = Label(f, text=txt, font=FNS, bg=C['bg3'],
                       fg=C['accent'] if i==0 else C['text3'])
            lbl.pack()
            self.step_labels.append(lbl)

        # Main
        main = Frame(self, bg=C['bg']); main.pack(fill=BOTH, expand=True, padx=12, pady=8)

        # LEFT — config
        left = Frame(main, bg=C['bg'], width=310); left.pack(side=LEFT, fill=Y, padx=(0,8)); left.pack_propagate(False)
        self._left(left)

        # RIGHT — log + progress
        right = Frame(main, bg=C['bg']); right.pack(side=LEFT, fill=BOTH, expand=True)
        self._right(right)

        # Statusbar
        sb = Frame(self, bg=C['bg4'], height=26); sb.pack(fill=X, side=BOTTOM); sb.pack_propagate(False)
        Frame(sb, bg=C['red'], width=3).pack(side=LEFT, fill=Y)
        self.sv = StringVar(value="En attente — Chargement des disques...")
        Label(sb, textvariable=self.sv, font=FNS, bg=C['bg4'], fg=C['text2']).pack(side=LEFT, padx=8, pady=4)

    def _left(self, p):
        # ÉTAPE 1 — Disques
        f1 = ttk.LabelFrame(p, text=" ÉTAPE 1 — DISQUES ", padding=10); f1.pack(fill=X, pady=(0,8))

        Label(f1, text="💀 Source (HDD crashé) :", font=FNS, bg=C['bg2'], fg=C['red']).pack(anchor=W)
        self.src_cb = ttk.Combobox(f1, textvariable=self.src_var, state='readonly', font=FNS)
        self.src_cb.pack(fill=X, pady=(2,8))

        Label(f1, text="💾 Destination (HDD 1TB sain) :", font=FNS, bg=C['bg2'], fg=C['green']).pack(anchor=W)
        self.dst_cb = ttk.Combobox(f1, textvariable=self.dst_var, state='readonly', font=FNS)
        self.dst_cb.pack(fill=X, pady=(2,6))

        self.btn_refresh = self._btn(f1, "🔄 Actualiser les disques", self._load_disks, C['text2'], small=True)
        self.btn_refresh.pack(fill=X, pady=(4,0))

        # ÉTAPE 2 — Fichier image
        f2 = ttk.LabelFrame(p, text=" ÉTAPE 2 — IMAGE DD ", padding=10); f2.pack(fill=X, pady=(0,8))

        Label(f2, text="Nom du fichier image :", font=FNS, bg=C['bg2'], fg=C['text2']).pack(anchor=W)
        self.img_name = StringVar(value=f"hdd_crash_{datetime.now().strftime('%Y%m%d_%H%M')}.dd")
        Entry(f2, textvariable=self.img_name, bg=C['bg3'], fg=C['text'],
              insertbackground=C['accent'], relief='flat', font=FNM,
              bd=0, highlightthickness=1, highlightcolor=C['accent'],
              highlightbackground=C['border']).pack(fill=X, pady=2)

        Label(f2, text="Dossier destination :", font=FNS, bg=C['bg2'], fg=C['text2']).pack(anchor=W, pady=(6,0))
        self.img_dir = StringVar(value="D:\\RecupHDD")
        Entry(f2, textvariable=self.img_dir, bg=C['bg3'], fg=C['text'],
              insertbackground=C['accent'], relief='flat', font=FNM,
              bd=0, highlightthickness=1, highlightcolor=C['accent'],
              highlightbackground=C['border']).pack(fill=X, pady=2)

        # OPTIONS
        f3 = ttk.LabelFrame(p, text=" OPTIONS ", padding=10); f3.pack(fill=X, pady=(0,8))
        self.opt_retry  = BooleanVar(value=True)
        self.opt_voting = BooleanVar(value=True)
        self.opt_skip   = BooleanVar(value=True)
        for var, lbl, col in [
            (self.opt_retry,  "🔄  Retry sur bad sectors (x8)", C['yellow']),
            (self.opt_voting, "🗳️  Majority voting",            C['accent']),
            (self.opt_skip,   "⏩  Skip si trop long (>30s)",   C['orange']),
        ]:
            tk.Checkbutton(f3, text=lbl, variable=var,
                           bg=C['bg2'], fg=col, selectcolor=C['bg3'],
                           activebackground=C['bg2'], font=FNS,
                           cursor='hand2').pack(anchor=W, pady=2)

        # ACTIONS
        f4 = Frame(p, bg=C['bg']); f4.pack(fill=X, pady=(0,8))
        self.btn_start = self._btn(f4, "▶  LANCER L'IMAGE DD", self._start, C['green'])
        self.btn_start.pack(fill=X, pady=(0,4)); self.btn_start.config(state=DISABLED)
        self.btn_stop = self._btn(f4, "⏹  ARRÊTER", self._stop, C['red'])
        self.btn_stop.pack(fill=X); self.btn_stop.config(state=DISABLED)

        # PROGRESSION
        f5 = ttk.LabelFrame(p, text=" PROGRESSION ", padding=10); f5.pack(fill=X)
        self.pv = tk.DoubleVar()
        self.pb = ttk.Progressbar(f5, variable=self.pv, maximum=100)
        self.pb.pack(fill=X, pady=(0,6))
        self.plbl = Label(f5, text="En attente...", font=FNS, bg=C['bg2'], fg=C['text2'])
        self.plbl.pack(anchor=W)

        # Stats mini
        sf = Frame(f5, bg=C['bg2']); sf.pack(fill=X, pady=(6,0))
        self.sv_stats = {}
        for k, lbl, col in [
            ('done',  'Copié',       C['green']),
            ('bad',   'Bad sectors', C['red']),
            ('speed', 'Vitesse',     C['accent']),
            ('eta',   'Temps restant',C['yellow']),
        ]:
            r = Frame(sf, bg=C['bg2']); r.pack(fill=X, pady=1)
            Label(r, text=f"{lbl}:", font=FNS, bg=C['bg2'], fg=C['text2'], width=14, anchor=W).pack(side=LEFT)
            v = StringVar(value='—'); self.sv_stats[k] = v
            Label(r, textvariable=v, font=FNS, bg=C['bg2'], fg=col).pack(side=LEFT)

    def _right(self, p):
        # Instructions
        inst = Frame(p, bg=C['bg3']); inst.pack(fill=X, pady=(0,8))
        Label(inst, text="⚡ PROCÉDURE — Lis bien avant de commencer",
              font=('Consolas',10,'bold'), bg=C['bg3'], fg=C['yellow']).pack(anchor=W, padx=10, pady=(8,4))

        steps_txt = [
            ("1.", "Branche le HDD 1TB SAIN en destination (SATA ou USB)",   C['green']),
            ("2.", "Clique 'Actualiser' pour voir les disques",              C['accent']),
            ("3.", "Sélectionne la source (HDD crashé) et la destination",  C['accent']),
            ("4.", "Démarre l'image DD",                                     C['accent']),
            ("5.", "SEULEMENT APRÈS le démarrage → branche le HDD crashé À CHAUD", C['red']),
            ("6.", "Windows va le détecter → l'image commence automatiquement", C['green']),
            ("7.", "Ne touche RIEN pendant l'image — laisse tourner",        C['yellow']),
            ("8.", "Une fois terminé → copier l'image sur KERBEROS-IA",     C['green']),
            ("9.", "Lancer Phantom Recover sur l'image .dd ✓",              C['purple']),
        ]
        for num, txt, col in steps_txt:
            r = Frame(inst, bg=C['bg3']); r.pack(fill=X, padx=10, pady=1)
            Label(r, text=num, font=('Consolas',9,'bold'), bg=C['bg3'], fg=col, width=3).pack(side=LEFT)
            Label(r, text=txt, font=FNS, bg=C['bg3'], fg=C['text'], anchor=W).pack(side=LEFT)
        Frame(inst, bg=C['bg3'], height=6).pack()

        # Log
        lf = ttk.LabelFrame(p, text=" LOG EN TEMPS RÉEL ", padding=4); lf.pack(fill=BOTH, expand=True)
        self.log_w = Text(lf, bg=C['bg2'], fg=C['text'], font=FNM,
                          insertbackground=C['accent'], relief='flat',
                          wrap=WORD, state=DISABLED)
        lsb = ttk.Scrollbar(lf, command=self.log_w.yview)
        self.log_w.configure(yscrollcommand=lsb.set)
        lsb.pack(side=RIGHT, fill=Y); self.log_w.pack(fill=BOTH, expand=True)
        for tag, col, bold in [
            ('title', C['accent'],  True), ('ok',   C['green'],  False),
            ('warn',  C['yellow'],  False), ('err',  C['red'],    False),
            ('info',  C['text2'],   False), ('sep',  C['text3'],  False),
        ]:
            self.log_w.tag_configure(tag, foreground=col,
                font=('Courier New',9,'bold' if bold else 'normal'))

    # ── BOUTONS ─────────────────────────────────────────────
    def _btn(self, p, text, cmd, color=None, small=False):
        c = color or C['accent']
        f = FNS if small else ('Consolas', 10, 'bold')
        py = 3 if small else 8
        b = tk.Button(p, text=text, command=cmd,
                      bg=C['bg3'], fg=c, activebackground=C['bg4'],
                      activeforeground=c, relief='flat', bd=0,
                      font=f, cursor='hand2', padx=8, pady=py)
        b.bind('<Enter>', lambda e: b.config(bg=C['bg4']))
        b.bind('<Leave>', lambda e: b.config(bg=C['bg3']))
        return b

    # ── DISQUES ─────────────────────────────────────────────
    def _load_disks(self):
        self._log("Chargement des disques...", 'info')
        self.disks = self.dm.list_disks()
        self.q.put(('disks', self.disks))

    def _on_disks(self, disks):
        if not disks:
            self._log("⚠ Aucun disque détecté — vérifiez les connexions", 'warn')
            self._log("  Si le HDD crashé n'est pas encore branché → c'est normal", 'info')
            self._log("  Branchez-le à chaud puis cliquez 'Actualiser'", 'info')
            return

        opts = [f"Drive {d['number']} — {d['name']} — {d['size_str']} — {d['bus']}" for d in disks]
        self.src_cb['values'] = opts
        self.dst_cb['values'] = opts

        self._log(f"✓ {len(disks)} disque(s) détecté(s) :", 'ok')
        for d in disks:
            health_col = 'ok' if d['health'] == 'Healthy' else 'warn'
            self._log(f"  Drive {d['number']}: {d['name']} — {d['size_str']} — {d['health']} — {d['bus']}", health_col)

        self.btn_start.config(state=NORMAL)
        self.sv.set(f"✓ {len(disks)} disques détectés — Sélectionnez source et destination")

        # Auto-sélection si 2 disques
        if len(disks) >= 2:
            self._log("\n💡 Conseil: sélectionnez le plus petit comme source (HDD crashé)", 'info')

    # ── IMAGE ────────────────────────────────────────────────
    def _start(self):
        src_sel = self.src_var.get()
        dst_sel = self.dst_var.get()

        if not src_sel or not dst_sel:
            messagebox.showerror("Erreur", "Sélectionnez source ET destination !"); return
        if src_sel == dst_sel:
            messagebox.showerror("Erreur", "Source et destination identiques !"); return

        # Extraire numéro de drive
        try:
            src_num = int(re.search(r'Drive (\d+)', src_sel).group(1))
            dst_num = int(re.search(r'Drive (\d+)', dst_sel).group(1))
        except:
            messagebox.showerror("Erreur", "Impossible de lire le numéro de drive"); return

        # Trouver infos destination
        dst_disk = next((d for d in self.disks if d['number'] == dst_num), None)
        src_disk = next((d for d in self.disks if d['number'] == src_num), None)

        # Vérif taille
        if dst_disk and src_disk:
            if dst_disk['size'] < src_disk['size']:
                messagebox.showerror("Erreur",
                    f"Destination trop petite !\n"
                    f"Source : {src_disk['size_str']}\n"
                    f"Dest   : {dst_disk['size_str']}"); return

        # Confirmation
        msg = (f"CONFIRMER L'IMAGE DD\n\n"
               f"Source  : Drive {src_num} — {src_disk['name'] if src_disk else '?'}\n"
               f"Dest    : {self.img_dir.get()}\\{self.img_name.get()}\n\n"
               f"⚠ L'image peut prendre 30-90 minutes pour 500 GB\n"
               f"⚠ Ne pas toucher les câbles pendant l'opération\n\n"
               f"Continuer ?")
        if not messagebox.askyesno("Confirmation", msg): return

        # Construire chemin
        img_path = str(Path(self.img_dir.get()) / self.img_name.get())

        self.running = True
        self.btn_start.config(state=DISABLED)
        self.btn_stop.config(state=NORMAL)
        self._set_step(1)
        self.pv.set(0)

        self._log("="*50, 'sep')
        self._log(" IMAGE DD — DÉMARRAGE", 'title')
        self._log("="*50, 'sep')
        self._log(f"Source   : PhysicalDrive{src_num}", 'info')
        self._log(f"Dest     : {img_path}", 'info')
        self._log(f"Retry    : {'Oui' if self.opt_retry.get() else 'Non'}", 'info')
        self._log(f"Voting   : {'Oui' if self.opt_voting.get() else 'Non'}", 'info')
        self._log("\n⚡ MAINTENANT — branchez le HDD crashé à chaud si pas déjà fait !", 'warn')
        self._log("   Attendez 15 secondes que le disque soit reconnu...", 'warn')

        self.engine = ImageEngine(
            src_num, img_path,
            log_cb      = self._log,
            progress_cb = lambda p, done, total, spd, eta, bad:
                          self.q.put(('prog', (p, done, total, spd, eta, bad))),
            done_cb     = lambda ok, stats: self.q.put(('done', (ok, stats, img_path)))
        )

        threading.Thread(target=self.engine.run, daemon=True).start()

    def _stop(self):
        if self.engine: self.engine.stop()
        self.running = False
        self._log("⏹ Arrêt demandé...", 'warn')

    # ── POLL ────────────────────────────────────────────────
    def _poll(self):
        try:
            while True:
                msg, data = self.q.get_nowait()
                if msg == 'log':
                    self._append_log(data[1], data[0])
                elif msg == 'disks':
                    self._on_disks(data)
                elif msg == 'prog':
                    p, done, total, spd, eta, bad = data
                    self.pv.set(p)
                    done_str  = f"{done/1e9:.1f}/{total/1e9:.1f} GB"
                    spd_str   = f"{spd/1e6:.1f} MB/s"
                    eta_str   = f"{int(eta//60)}m {int(eta%60)}s"
                    self.plbl.config(text=f"{p:.1f}%  —  {done_str}")
                    self.sv_stats['done'].set(done_str)
                    self.sv_stats['bad'].set(str(bad))
                    self.sv_stats['speed'].set(spd_str)
                    self.sv_stats['eta'].set(eta_str)
                    self.sv.set(f"Image en cours: {p:.1f}% — {spd_str} — {bad} bad sectors")
                elif msg == 'done':
                    self._on_done(*data)
        except queue.Empty: pass
        self.after(100, self._poll)

    def _on_done(self, ok: bool, stats: dict, img_path: str):
        self.running = False
        self.btn_stop.config(state=DISABLED)
        self.btn_start.config(state=NORMAL)

        if ok:
            self._set_step(2)
            self.pv.set(100)
            bad = stats['blocks_bad']
            self._log("="*50, 'sep')
            self._log("✓ IMAGE TERMINÉE AVEC SUCCÈS !", 'ok')
            self._log("="*50, 'sep')
            self._log(f"\n📋 PROCHAINES ÉTAPES :", 'title')
            self._log(f"  1. Copier ce fichier sur KERBEROS-IA :", 'info')
            self._log(f"     {img_path}", 'ok')
            self._log(f"  2. Lancer Phantom Recover", 'info')
            self._log(f"  3. Sélectionner l'image .dd comme source", 'info')
            self._log(f"  4. Lancer analyse MFT + Carving", 'info')
            if bad > 0:
                self._log(f"\n  ⚠ {bad} bad sectors — fichiers partiels possibles", 'warn')
                self._log(f"     Phantom Recover gère les fichiers partiels ✓", 'info')

            messagebox.showinfo("✓ Image terminée !",
                f"Image créée avec succès !\n\n"
                f"Fichier : {img_path}\n"
                f"Bad sectors : {bad}\n\n"
                f"→ Copier ce fichier sur KERBEROS-IA\n"
                f"→ Lancer Phantom Recover dessus")
        else:
            self._log("✗ Image échouée ou arrêtée", 'err')
            self._log("  Vérifiez que le disque est bien branché", 'warn')

    # ── HELPERS ─────────────────────────────────────────────
    def _log(self, text, tag='info'):
        self.q.put(('log', (tag, text)))

    def _append_log(self, text, tag):
        self.log_w.config(state=NORMAL)
        ts = datetime.now().strftime('%H:%M:%S')
        self.log_w.insert(END, f"[{ts}] {text}\n", tag)
        self.log_w.config(state=DISABLED)
        self.log_w.see(END)

    def _set_step(self, step: int):
        for i, lbl in enumerate(self.step_labels):
            if i < step:  lbl.config(fg=C['green'])
            elif i == step: lbl.config(fg=C['accent'])
            else:           lbl.config(fg=C['text3'])

    def _fmt_size(self, s):
        if not s: return '?'
        for u in ['B','KB','MB','GB','TB']:
            if s < 1024: return f"{s:.1f} {u}"
            s /= 1024
        return f"{s:.1f} PB"

import re

if __name__ == '__main__':
    app = CrashRecoveryKit()
    app.mainloop()
