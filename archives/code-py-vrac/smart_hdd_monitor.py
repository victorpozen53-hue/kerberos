#!/usr/bin/env python3
"""
╔══════════════════════════════════════════════════════════════╗
║         SMART HDD MONITOR  —  v1.0                         ║
║   Scan disques sains → reboot → détecte HDD abîmé         ║
║                                                              ║
║  MODE 1 — Premier boot (sans HDD abîmé) :                  ║
║    python smart_hdd_monitor.py --scan                      ║
║    → Mémorise les disques sains                            ║
║    → Installe la tâche planifiée                           ║
║    → Tu éteinds, tu branches le HDD abîmé                 ║
║                                                              ║
║  MODE 2 — Deuxième boot (automatique) :                    ║
║    → Tâche planifiée se déclenche                          ║
║    → Détecte le nouveau disque                             ║
║    → Lance l'image DD automatiquement                      ║
║                                                              ║
║  MODE GUI :                                                 ║
║    python smart_hdd_monitor.py                             ║
╚══════════════════════════════════════════════════════════════╝
"""

import os, sys, re, json, time, ctypes, subprocess, platform
import threading, queue, hashlib, struct, argparse
from pathlib import Path
from datetime import datetime
from tkinter import *
from tkinter import ttk, messagebox
import tkinter as tk

if platform.system() != 'Windows':
    print("Smart HDD Monitor est pour Windows uniquement.")
    sys.exit(0)

# ═══════════════════════════════════════════════════════════════
# CONFIG
# ═══════════════════════════════════════════════════════════════
APP_NAME    = "SmartHDDMonitor"
STATE_FILE  = Path(os.environ.get('PROGRAMDATA','C:\\ProgramData')) / APP_NAME / 'known_disks.json'
LOG_FILE    = Path(os.environ.get('PROGRAMDATA','C:\\ProgramData')) / APP_NAME / 'monitor.log'
OUTPUT_DIR  = Path(os.environ.get('USERPROFILE','C:\\')) / 'HDD_Recovery'
TASK_NAME   = "SmartHDDMonitor_AutoDetect"
SCRIPT_PATH = Path(sys.argv[0]).resolve()

# ═══════════════════════════════════════════════════════════════
# COULEURS
# ═══════════════════════════════════════════════════════════════
C = {
    'bg':     '#0A0C10', 'bg2':  '#12151F', 'bg3':  '#1A1E2E',
    'bg4':    '#222638', 'panel':'#060810',
    'accent': '#00E5FF', 'green':'#00FF9D', 'yellow':'#FFD23F',
    'red':    '#FF3860', 'orange':'#FF6B35','purple':'#B794F4',
    'text':   '#CDD6F4', 'text2':'#6C7086', 'text3': '#45475A',
}
FN  = ('Consolas', 10)
FNS = ('Consolas', 9)
FNB = ('Consolas', 12, 'bold')
FNT = ('Consolas', 15, 'bold')
FNM = ('Courier New', 9)

# ═══════════════════════════════════════════════════════════════
# DISK SCANNER
# ═══════════════════════════════════════════════════════════════
class DiskScanner:

    def get_all_disks(self) -> list:
        """Récupère tous les disques via PowerShell"""
        try:
            ps = ('Get-Disk | Select-Object Number,FriendlyName,SerialNumber,'
                  'Size,HealthStatus,OperationalStatus,BusType,FirmwareVersion,'
                  'Manufacturer,Model,PartitionStyle | ConvertTo-Json -Compress')
            out = subprocess.check_output(
                ['powershell','-NoProfile','-Command', ps],
                timeout=20, stderr=subprocess.DEVNULL,
                creationflags=subprocess.CREATE_NO_WINDOW)
            data = json.loads(out.decode('utf-8','replace'))
            if isinstance(data, dict): data = [data]
            disks = []
            for d in (data or []):
                if not isinstance(d, dict): continue
                serial = (d.get('SerialNumber') or '').strip()
                size   = d.get('Size', 0) or 0
                name   = (d.get('FriendlyName') or d.get('Model') or '?').strip()
                disks.append({
                    'number':   d.get('Number', 0),
                    'name':     name,
                    'serial':   serial,
                    'size':     size,
                    'size_str': self._fmt(size),
                    'health':   d.get('HealthStatus','?'),
                    'status':   d.get('OperationalStatus','?'),
                    'bus':      d.get('BusType','?'),
                    'firmware': d.get('FirmwareVersion',''),
                    'model':    d.get('Model',''),
                    'path':     f"\\\\.\\PhysicalDrive{d.get('Number',0)}",
                    # Empreinte unique = serial + taille + nom
                    'fingerprint': self._fingerprint(serial, size, name),
                    'scanned_at': datetime.now().isoformat(),
                })
            return disks
        except Exception as e:
            self._log_file(f"get_all_disks error: {e}")
            return []

    def _fingerprint(self, serial: str, size: int, name: str) -> str:
        """Empreinte unique d'un disque"""
        raw = f"{serial}|{size}|{name}".encode()
        return hashlib.md5(raw).hexdigest()[:12]

    def find_new_disks(self, known: list, current: list) -> list:
        """Retourne les disques présents dans current mais pas dans known"""
        known_fps = {d['fingerprint'] for d in known}
        new = []
        for d in current:
            if d['fingerprint'] not in known_fps:
                new.append(d)
        return new

    def save_state(self, disks: list):
        """Sauvegarde l'état des disques sains"""
        STATE_FILE.parent.mkdir(parents=True, exist_ok=True)
        data = {
            'saved_at':    datetime.now().isoformat(),
            'hostname':    os.environ.get('COMPUTERNAME','?'),
            'disk_count':  len(disks),
            'disks':       disks,
            'script_path': str(SCRIPT_PATH),
        }
        STATE_FILE.write_text(json.dumps(data, indent=2), encoding='utf-8')

    def load_state(self) -> dict | None:
        """Charge l'état sauvegardé"""
        try:
            if STATE_FILE.exists():
                return json.loads(STATE_FILE.read_text(encoding='utf-8'))
        except: pass
        return None

    def has_state(self) -> bool:
        return STATE_FILE.exists()

    @staticmethod
    def _fmt(s: int) -> str:
        if not s: return '?'
        for u in ['B','KB','MB','GB','TB']:
            if s < 1024: return f"{s:.1f} {u}"
            s /= 1024
        return f"{s:.1f} PB"

    @staticmethod
    def _log_file(msg: str):
        try:
            LOG_FILE.parent.mkdir(parents=True, exist_ok=True)
            with open(LOG_FILE,'a',encoding='utf-8') as f:
                f.write(f"[{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}] {msg}\n")
        except: pass


# ═══════════════════════════════════════════════════════════════
# TASK SCHEDULER
# ═══════════════════════════════════════════════════════════════
class TaskScheduler:

    def install_task(self, delay_seconds: int = 45) -> bool:
        """
        Installe une tâche planifiée qui se déclenche :
        - Au démarrage de Windows
        - Après login utilisateur
        - Avec un délai pour laisser Windows finir de booter
        """
        try:
            # Commande à exécuter
            python_exe = sys.executable
            cmd = f'"{python_exe}" "{SCRIPT_PATH}" --autodetect'

            ps = f"""
$Action  = New-ScheduledTaskAction -Execute '{python_exe}' `
           -Argument '"{SCRIPT_PATH}" --autodetect'

$Trigger = New-ScheduledTaskTrigger -AtLogOn

$Settings = New-ScheduledTaskSettingsSet `
    -ExecutionTimeLimit (New-TimeSpan -Minutes 120) `
    -MultipleInstances IgnoreNew `
    -RunOnlyIfNetworkAvailable $false `
    -StartWhenAvailable

$Principal = New-ScheduledTaskPrincipal `
    -UserId "$env:USERNAME" `
    -RunLevel Highest `
    -LogonType Interactive

Register-ScheduledTask `
    -TaskName '{TASK_NAME}' `
    -Action   $Action `
    -Trigger  $Trigger `
    -Settings $Settings `
    -Principal $Principal `
    -Force | Out-Null

Write-Output "OK"
"""
            out = subprocess.check_output(
                ['powershell','-NoProfile','-Command', ps],
                timeout=30, stderr=subprocess.DEVNULL,
                creationflags=subprocess.CREATE_NO_WINDOW)
            return b'OK' in out
        except Exception as e:
            DiskScanner._log_file(f"install_task error: {e}")
            return False

    def remove_task(self) -> bool:
        """Supprime la tâche planifiée"""
        try:
            subprocess.run(
                ['powershell','-NoProfile','-Command',
                 f"Unregister-ScheduledTask -TaskName '{TASK_NAME}' -Confirm:$false"],
                timeout=15, stderr=subprocess.DEVNULL,
                creationflags=subprocess.CREATE_NO_WINDOW)
            return True
        except: return False

    def task_exists(self) -> bool:
        try:
            out = subprocess.check_output(
                ['powershell','-NoProfile','-Command',
                 f"Get-ScheduledTask -TaskName '{TASK_NAME}' -ErrorAction SilentlyContinue | Select-Object -ExpandProperty TaskName"],
                timeout=10, stderr=subprocess.DEVNULL,
                creationflags=subprocess.CREATE_NO_WINDOW)
            return TASK_NAME.encode() in out
        except: return False

    def is_admin(self) -> bool:
        try: return bool(ctypes.windll.shell32.IsUserAnAdmin())
        except: return False


# ═══════════════════════════════════════════════════════════════
# IMAGE ENGINE  (version légère pour mode auto)
# ═══════════════════════════════════════════════════════════════
class QuickImager:
    BLOCK = 65536

    def __init__(self, src_num: int, dst_path: str, log_cb=None, prog_cb=None):
        self.src_num  = src_num
        self.dst_path = dst_path
        self.log      = log_cb or print
        self.prog     = prog_cb or (lambda *a: None)
        self.running  = True
        self.bad      = 0
        self.done_bytes = 0

    def stop(self): self.running = False

    def run(self) -> bool:
        src_path = f"\\\\.\\PhysicalDrive{self.src_num}"
        DiskScanner._log_file(f"Starting image: {src_path} → {self.dst_path}")
        self.log(f"Source  : {src_path}", 'info')
        self.log(f"Dest    : {self.dst_path}", 'info')

        # Ouvrir disque
        h = ctypes.windll.kernel32.CreateFileW(
            src_path, 0x80000000, 0x3, None, 3, 0x20000000, None)
        if h == ctypes.c_void_p(-1).value:
            self.log(f"✗ Impossible d'ouvrir PhysicalDrive{self.src_num}", 'err')
            return False

        # Taille
        disk_size = self._get_size(h)
        if not disk_size:
            self.log("✗ Taille illisible — disque trop endommagé ?", 'err')
            ctypes.windll.kernel32.CloseHandle(h)
            return False

        self.log(f"Taille  : {disk_size/1e9:.1f} GB", 'ok')
        Path(self.dst_path).parent.mkdir(parents=True, exist_ok=True)

        start = time.time()
        offset = 0
        last_t = start; last_b = 0

        try:
            with open(self.dst_path, 'wb') as f:
                while offset < disk_size and self.running:
                    to_read = min(self.BLOCK, disk_size - offset)
                    data    = self._read(h, offset, to_read)
                    if data:
                        f.write(data)
                    else:
                        f.write(b'\x00' * to_read)
                        self.bad += 1

                    offset += to_read
                    self.done_bytes = offset

                    now = time.time()
                    if now - last_t >= 3:
                        spd = (offset - last_b) / (now - last_t)
                        eta = (disk_size - offset) / max(spd, 1)
                        pct = offset / disk_size * 100
                        self.prog(pct, offset, disk_size, spd, eta, self.bad)
                        last_t = now; last_b = offset

        except Exception as e:
            self.log(f"✗ Erreur: {e}", 'err')
            ctypes.windll.kernel32.CloseHandle(h)
            return False

        ctypes.windll.kernel32.CloseHandle(h)
        elapsed = time.time() - start

        if self.running:
            self.log(f"✓ Image terminée en {elapsed/60:.1f} min — {self.bad} bad sectors", 'ok')
            DiskScanner._log_file(f"Image done: {self.dst_path} bad={self.bad}")
            return True
        return False

    def _get_size(self, h) -> int:
        try:
            buf = ctypes.create_string_buffer(24)
            rb  = ctypes.c_ulong(0)
            ctypes.windll.kernel32.DeviceIoControl(h,0x00070000,None,0,buf,24,ctypes.byref(rb),None)
            g = struct.unpack_from('<qIIII', buf)
            sz = g[0]*g[2]*g[3]*g[4]
            if sz: return sz
        except: pass
        try:
            hi = ctypes.c_long(0)
            lo = ctypes.windll.kernel32.SetFilePointer(h,0,ctypes.byref(hi),2)
            sz = (hi.value<<32)|(lo&0xFFFFFFFF)
            ctypes.windll.kernel32.SetFilePointer(h,0,None,0)
            return sz
        except: return 0

    def _read(self, h, offset: int, size: int, retries: int=6) -> bytes|None:
        reads = []
        for attempt in range(retries):
            try:
                hi = ctypes.c_long(offset>>32)
                ctypes.windll.kernel32.SetFilePointer(h,offset&0xFFFFFFFF,ctypes.byref(hi),0)
                buf = ctypes.create_string_buffer(size)
                rb  = ctypes.c_ulong(0)
                ok  = ctypes.windll.kernel32.ReadFile(h,buf,size,ctypes.byref(rb),None)
                if ok and rb.value > 0:
                    d = bytes(buf[:rb.value])
                    if rb.value < size: d += b'\x00'*(size-rb.value)
                    reads.append(d)
                    if attempt==0: return d
                    break
            except: pass
            time.sleep(0.02*(2**min(attempt,4)))
        if reads:
            result = bytearray(size)
            for i in range(size):
                votes = [r[i] for r in reads if i<len(r)]
                result[i] = max(set(votes),key=votes.count) if votes else 0
            return bytes(result)
        return None


# ═══════════════════════════════════════════════════════════════
# MODE AUTO-DETECT (lancé par la tâche planifiée)
# ═══════════════════════════════════════════════════════════════
def run_autodetect():
    """Mode silencieux — lancé automatiquement au boot"""
    scanner = DiskScanner()
    sched   = TaskScheduler()
    scanner._log_file("=== AUTO-DETECT démarré ===")

    # Charger état connu
    state = scanner.load_state()
    if not state:
        scanner._log_file("Aucun état connu — abort")
        return

    known_disks = state.get('disks', [])
    scanner._log_file(f"Disques connus: {len(known_disks)}")

    # Attendre que Windows soit complètement prêt
    time.sleep(30)

    # Scanner les disques actuels
    current = scanner.get_all_disks()
    scanner._log_file(f"Disques actuels: {len(current)}")

    # Trouver nouveaux disques
    new_disks = scanner.find_new_disks(known_disks, current)
    scanner._log_file(f"Nouveaux disques: {len(new_disks)}")

    if not new_disks:
        scanner._log_file("Aucun nouveau disque — fin normale")
        # Supprimer la tâche — plus besoin
        # sched.remove_task()  # optionnel
        return

    # Nouveau(x) disque(s) détecté(s) !
    for new in new_disks:
        scanner._log_file(f"NOUVEAU: {new['name']} {new['size_str']} Drive{new['number']}")

    # Lancer la GUI avec le disque détecté
    _launch_gui_automode(new_disks, known_disks, scanner, sched)


def _launch_gui_automode(new_disks, known_disks, scanner, sched):
    """Lance la GUI en mode automatique avec le disque pré-sélectionné"""
    app = SmartMonitorApp(
        automode=True,
        detected_disks=new_disks,
        known_disks=known_disks,
        scanner=scanner,
        sched=sched
    )
    app.mainloop()


# ═══════════════════════════════════════════════════════════════
# APPLICATION GUI
# ═══════════════════════════════════════════════════════════════
class SmartMonitorApp(Tk):
    def __init__(self, automode=False, detected_disks=None,
                 known_disks=None, scanner=None, sched=None):
        super().__init__()

        self.automode       = automode
        self.detected_disks = detected_disks or []
        self.known_disks    = known_disks or []
        self.scanner        = scanner or DiskScanner()
        self.sched          = sched   or TaskScheduler()
        self.q              = queue.Queue()
        self.running        = False
        self.engine         = None
        self.all_disks      = []

        self.title("SMART HDD MONITOR  —  Détection automatique HDD abîmé")
        self.geometry("980x720")
        self.minsize(850, 600)
        self.configure(bg=C['bg'])

        self._style()
        self._ui()
        self._poll()

        # Charger les disques
        threading.Thread(target=self._load, daemon=True).start()

        # Mode auto : démarrer directement
        if automode and self.detected_disks:
            self.after(2000, self._auto_start)

    # ── STYLE ─────────────────────────────────────────────
    def _style(self):
        s = ttk.Style(self); s.theme_use('clam')
        s.configure('.', background=C['bg'], foreground=C['text'], font=FN)
        s.configure('TFrame', background=C['bg'])
        s.configure('TLabel', background=C['bg'], foreground=C['text'])
        s.configure('TLabelframe', background=C['bg2'], foreground=C['accent'], relief='flat')
        s.configure('TLabelframe.Label', background=C['bg2'], foreground=C['accent'], font=('Consolas',9,'bold'))
        s.configure('TProgressbar', troughcolor=C['bg3'], background=C['green'], thickness=8)
        s.configure('Treeview', background=C['bg2'], foreground=C['text'],
                    fieldbackground=C['bg2'], rowheight=24, borderwidth=0, font=FN)
        s.configure('Treeview.Heading', background=C['bg4'], foreground=C['accent'],
                    font=('Consolas',9,'bold'), relief='flat')
        s.map('Treeview', background=[('selected',C['selected'] if 'selected' in C else C['bg4'])],
              foreground=[('selected',C['accent'])])

    # ── UI ────────────────────────────────────────────────
    def _ui(self):
        # Header
        hdr = Frame(self, bg=C['panel'], height=58); hdr.pack(fill=X); hdr.pack_propagate(False)
        Frame(hdr, bg=C['accent'], width=4).pack(side=LEFT, fill=Y)
        lg = Frame(hdr, bg=C['panel']); lg.pack(side=LEFT, padx=14, pady=8)
        Label(lg, text="🧠 SMART HDD MONITOR", font=FNT, bg=C['panel'], fg=C['accent']).pack(anchor=W)
        Label(lg, text="Scan disques sains → Reboot → Détecte HDD abîmé automatiquement",
              font=FNS, bg=C['panel'], fg=C['text2']).pack(anchor=W)

        # Mode badge
        mode_txt = "⚡ MODE AUTO — HDD détecté !" if self.automode else "● MODE MANUEL"
        mode_col = C['green'] if self.automode else C['text2']
        mode_bg  = C['bg4']
        Label(hdr, text=mode_txt, font=('Consolas',9,'bold'),
              bg=mode_bg, fg=mode_col, padx=10, pady=4).pack(side=RIGHT, padx=14, pady=18)

        # Tabs
        nb = ttk.Notebook(self)
        # Utiliser un style custom pour le notebook
        nb.pack(fill=BOTH, expand=True, padx=8, pady=6)

        # Tab 1 — Workflow principal
        t1 = Frame(nb, bg=C['bg']); nb.add(t1, text="  🔧 WORKFLOW PRINCIPAL  ")
        self._tab_workflow(t1)

        # Tab 2 — Disques connus
        t2 = Frame(nb, bg=C['bg']); nb.add(t2, text="  💾 DISQUES CONNUS  ")
        self._tab_known(t2)

        # Tab 3 — Log
        t3 = Frame(nb, bg=C['bg']); nb.add(t3, text="  📋 LOG  ")
        self.log_w = Text(t3, bg=C['bg2'], fg=C['text'], font=FNM,
                          insertbackground=C['accent'], relief='flat', wrap=WORD, state=DISABLED)
        lsb = ttk.Scrollbar(t3, command=self.log_w.yview)
        self.log_w.configure(yscrollcommand=lsb.set)
        lsb.pack(side=RIGHT, fill=Y); self.log_w.pack(fill=BOTH, expand=True)
        for tag, col, bold in [
            ('title',C['accent'],True),('ok',C['green'],False),
            ('warn',C['yellow'],False),('err',C['red'],False),
            ('info',C['text2'],False),('sep',C['text3'],False),
            ('big', C['green'], True),
        ]:
            self.log_w.tag_configure(tag, foreground=col,
                font=('Courier New', 11 if bold else 9, 'bold' if bold else 'normal'))

        # Statusbar
        sb = Frame(self, bg=C['bg4'], height=26); sb.pack(fill=X, side=BOTTOM); sb.pack_propagate(False)
        Frame(sb, bg=C['accent'], width=3).pack(side=LEFT, fill=Y)
        self.sv = StringVar(value="Prêt")
        Label(sb, textvariable=self.sv, font=FNS, bg=C['bg4'], fg=C['text2']).pack(side=LEFT, padx=8, pady=4)
        self.sv2 = StringVar(value="")
        Label(sb, textvariable=self.sv2, font=FNS, bg=C['bg4'], fg=C['green']).pack(side=RIGHT, padx=12)

    def _tab_workflow(self, p):
        # Split gauche/droite
        left = Frame(p, bg=C['bg'], width=320); left.pack(side=LEFT, fill=Y, padx=(8,6), pady=8); left.pack_propagate(False)
        right = Frame(p, bg=C['bg']); right.pack(side=LEFT, fill=BOTH, expand=True, padx=(0,8), pady=8)

        # ── ÉTAPE 1 ──
        f1 = ttk.LabelFrame(left, text=" ÉTAPE 1 — SCAN DISQUES SAINS ", padding=10)
        f1.pack(fill=X, pady=(0,8))

        self.lbl_state = Label(f1, text="⚪ Aucun état sauvegardé",
                               font=FNS, bg=C['bg2'], fg=C['text2'])
        self.lbl_state.pack(anchor=W, pady=(0,6))

        self.btn_scan = self._btn(f1, "🔍  SCANNER LES DISQUES SAINS", self._scan_healthy)
        self.btn_scan.pack(fill=X, pady=(0,4))

        # ── ÉTAPE 2 ──
        f2 = ttk.LabelFrame(left, text=" ÉTAPE 2 — INSTALLER LA TÂCHE ", padding=10)
        f2.pack(fill=X, pady=(0,8))

        self.lbl_task = Label(f2, text="⚪ Tâche non installée",
                              font=FNS, bg=C['bg2'], fg=C['text2'])
        self.lbl_task.pack(anchor=W, pady=(0,6))

        self.btn_task = self._btn(f2, "⚙️  INSTALLER TÂCHE PLANIFIÉE", self._install_task, C['yellow'])
        self.btn_task.pack(fill=X, pady=(0,4))
        self.btn_task.config(state=DISABLED)

        self.btn_remove_task = self._btn(f2, "🗑️  SUPPRIMER LA TÂCHE", self._remove_task, C['text2'], small=True)
        self.btn_remove_task.pack(fill=X)

        # Délai
        Label(f2, text="Délai après boot (secondes):", font=FNS, bg=C['bg2'], fg=C['text2']).pack(anchor=W, pady=(8,0))
        self.delay_var = StringVar(value='30')
        Entry(f2, textvariable=self.delay_var, bg=C['bg3'], fg=C['text'],
              insertbackground=C['accent'], relief='flat', font=FNM,
              bd=0, highlightthickness=1, highlightcolor=C['accent'],
              highlightbackground=C['bg4'], width=8).pack(anchor=W, pady=2)

        # ── ÉTAPE 3 ──
        f3 = ttk.LabelFrame(left, text=" ÉTAPE 3 — ÉTEINDRE & BRANCHER ", padding=10)
        f3.pack(fill=X, pady=(0,8))

        for txt, col in [
            ("1. Sauvegarde l'état ✓",           C['text2']),
            ("2. Installe la tâche ✓",           C['text2']),
            ("3. Éteins le PC",                  C['yellow']),
            ("4. Branche le HDD abîmé (SATA)",   C['yellow']),
            ("5. Rallume le PC",                 C['yellow']),
            ("6. Script se lance auto ✓",        C['green']),
            ("7. Image DD démarre seul ✓",       C['green']),
        ]:
            Label(f3, text=f"  {txt}", font=FNS, bg=C['bg2'], fg=col).pack(anchor=W, pady=1)

        # Bouton extinction
        self.btn_shutdown = self._btn(f3, "⏻  ÉTEINDRE LE PC MAINTENANT",
                                      self._shutdown, C['red'])
        self.btn_shutdown.pack(fill=X, pady=(8,0))
        self.btn_shutdown.config(state=DISABLED)

        # ── ÉTAPE 4 — IMAGE (mode auto) ──
        f4 = ttk.LabelFrame(left, text=" ÉTAPE 4 — IMAGE DD ", padding=10)
        f4.pack(fill=X, pady=(0,8))

        Label(f4, text="Destination image:", font=FNS, bg=C['bg2'], fg=C['text2']).pack(anchor=W)
        self.out_var = StringVar(value=str(OUTPUT_DIR / f"crash_{datetime.now().strftime('%Y%m%d')}.dd"))
        Entry(f4, textvariable=self.out_var, bg=C['bg3'], fg=C['text'],
              insertbackground=C['accent'], relief='flat', font=FNM,
              bd=0, highlightthickness=1, highlightcolor=C['accent'],
              highlightbackground=C['bg4']).pack(fill=X, pady=2)

        self.btn_img = self._btn(f4, "▶  LANCER L'IMAGE MANUELLEMENT", self._manual_image, C['green'])
        self.btn_img.pack(fill=X, pady=(6,4))
        self.btn_img.config(state=DISABLED)

        self.btn_stop_img = self._btn(f4, "⏹  ARRÊTER", self._stop_image, C['red'])
        self.btn_stop_img.pack(fill=X)
        self.btn_stop_img.config(state=DISABLED)

        # ── PROGRESS ──
        f5 = ttk.LabelFrame(left, text=" PROGRESSION IMAGE ", padding=10)
        f5.pack(fill=X)
        self.pv = tk.DoubleVar()
        ttk.Progressbar(f5, variable=self.pv, maximum=100).pack(fill=X, pady=(0,4))
        self.plbl = Label(f5, text="En attente...", font=FNS, bg=C['bg2'], fg=C['text2'])
        self.plbl.pack(anchor=W)
        sf = Frame(f5, bg=C['bg2']); sf.pack(fill=X, pady=(4,0))
        self.sv_img = {}
        for k,lbl,col in [('pct','%',C['green']),('spd','Vitesse',C['accent']),
                           ('eta','ETA',C['yellow']),('bad','Bad sectors',C['red'])]:
            r=Frame(sf,bg=C['bg2']); r.pack(fill=X, pady=1)
            Label(r,text=f"{lbl}:",font=FNS,bg=C['bg2'],fg=C['text2'],width=12,anchor=W).pack(side=LEFT)
            v=StringVar(value='—'); self.sv_img[k]=v
            Label(r,textvariable=v,font=FNS,bg=C['bg2'],fg=col).pack(side=LEFT)

        # ── RIGHT — Disk list ──
        df = ttk.LabelFrame(right, text=" DISQUES DÉTECTÉS ", padding=6)
        df.pack(fill=BOTH, expand=True, pady=(0,8))

        cols = ('num','name','size','health','bus','status','note')
        self.dtree = ttk.Treeview(df, columns=cols, show='headings', selectmode='browse')
        for col,hdr,w in [('num','#',40),('name','Disque',220),('size','Taille',80),
                           ('health','Santé',80),('bus','Bus',60),
                           ('status','État',80),('note','Note',100)]:
            self.dtree.heading(col,text=hdr); self.dtree.column(col,width=w,anchor='center' if col!='name' else 'w')
        self.dtree.tag_configure('known',   foreground=C['green'])
        self.dtree.tag_configure('new',     foreground=C['red'])
        self.dtree.tag_configure('healthy', foreground=C['green'])
        dsb=ttk.Scrollbar(df,orient=VERTICAL,command=self.dtree.yview)
        self.dtree.configure(yscrollcommand=dsb.set)
        dsb.pack(side=RIGHT,fill=Y); self.dtree.pack(fill=BOTH,expand=True)

        self._btn(right, "🔄 Actualiser les disques", self._load,
                  C['text2'], small=True).pack(fill=X)

    def _tab_known(self, p):
        """Onglet affichant les disques mémorisés"""
        state = self.scanner.load_state()
        txt = Text(p, bg=C['bg2'], fg=C['text'], font=FNM, relief='flat', state=DISABLED)
        txt.pack(fill=BOTH, expand=True, padx=8, pady=8)
        txt.tag_configure('h', foreground=C['accent'], font=('Consolas',10,'bold'))
        txt.tag_configure('v', foreground=C['text'])
        txt.tag_configure('k', foreground=C['yellow'])
        txt.config(state=NORMAL)
        if state:
            txt.insert(END, f"État sauvegardé le : {state.get('saved_at','?')}\n", 'h')
            txt.insert(END, f"Machine            : {state.get('hostname','?')}\n\n", 'v')
            for d in state.get('disks',[]):
                txt.insert(END, f"  Drive {d['number']}", 'k')
                txt.insert(END, f"  {d['name']:<35}  {d['size_str']:>10}  {d['health']}  {d['bus']}\n", 'v')
                txt.insert(END, f"         Serial: {d['serial']}  Fingerprint: {d['fingerprint']}\n", 'v')
        else:
            txt.insert(END, "Aucun état sauvegardé.\nLancez d'abord le scan des disques sains.", 'h')
        txt.config(state=DISABLED)
        self.known_txt = txt

    # ── LOAD DISKS ────────────────────────────────────────
    def _load(self):
        self._log("Scan des disques...", 'info')
        def run():
            disks = self.scanner.get_all_disks()
            self.q.put(('disks', disks))
        threading.Thread(target=run, daemon=True).start()

    def _on_disks(self, disks):
        self.all_disks = disks
        for i in self.dtree.get_children(): self.dtree.delete(i)

        state = self.scanner.load_state()
        known_fps = {d['fingerprint'] for d in state.get('disks',[])} if state else set()

        for d in disks:
            is_new   = d['fingerprint'] not in known_fps and bool(known_fps)
            is_known = d['fingerprint'] in known_fps
            note = "🔴 NOUVEAU !" if is_new else ("✓ Connu" if is_known else "?")
            tag  = 'new' if is_new else ('known' if is_known else '')
            self.dtree.insert('', END,
                values=(d['number'], d['name'], d['size_str'],
                        d['health'], d['bus'], d['status'], note),
                tags=(tag,))

        # Mettre à jour état
        if state:
            self.lbl_state.config(
                text=f"✓ État: {len(state.get('disks',[]))} disques mémorisés",
                fg=C['green'])
            self.btn_shutdown.config(state=NORMAL)
            self.btn_img.config(state=NORMAL)
        else:
            self.lbl_state.config(text="⚪ Aucun état sauvegardé", fg=C['text2'])

        # Tâche planifiée
        if self.sched.task_exists():
            self.lbl_task.config(text=f"✓ Tâche installée: {TASK_NAME}", fg=C['green'])
        else:
            self.lbl_task.config(text="⚪ Tâche non installée", fg=C['text2'])

        self._log(f"✓ {len(disks)} disque(s) détecté(s)", 'ok')
        for d in disks:
            flag = "🔴 NOUVEAU" if d['fingerprint'] not in known_fps and known_fps else ""
            self._log(f"  Drive {d['number']}: {d['name']} — {d['size_str']} — {d['bus']} {flag}",
                      'warn' if flag else 'info')

        self.sv.set(f"✓ {len(disks)} disques détectés")

        # Mode auto : si nouveaux disques → image auto
        if self.automode and self.detected_disks:
            new = self.detected_disks[0]
            self._log(f"\n⚡ MODE AUTO — Nouveau disque: {new['name']}", 'big')
            self._log(f"   Drive {new['number']} — {new['size_str']}", 'ok')
            self.btn_img.config(state=NORMAL)

    # ── SCAN SAINS ────────────────────────────────────────
    def _scan_healthy(self):
        if not self.all_disks:
            messagebox.showwarning("Attendre", "Chargement des disques en cours...")
            return
        n = len(self.all_disks)
        if not messagebox.askyesno("Confirmer",
            f"Mémoriser {n} disque(s) comme 'disques sains' ?\n\n"
            f"Ces disques seront la référence.\n"
            f"Au prochain boot, tout nouveau disque sera détecté."):
            return

        self.scanner.save_state(self.all_disks)
        self._log(f"✓ {n} disque(s) mémorisé(s) comme sains", 'ok')
        for d in self.all_disks:
            self._log(f"  Drive {d['number']}: {d['name']} — {d['size_str']} [{d['fingerprint']}]", 'info')
        self.lbl_state.config(text=f"✓ {n} disques mémorisés ✓", fg=C['green'])
        self.btn_task.config(state=NORMAL)
        self.btn_shutdown.config(state=NORMAL)
        messagebox.showinfo("✓ Sauvegardé",
            f"{n} disques mémorisés !\n\n"
            f"Fichier: {STATE_FILE}\n\n"
            f"Prochaine étape:\n"
            f"→ Installer la tâche planifiée\n"
            f"→ Éteindre le PC\n"
            f"→ Brancher le HDD abîmé\n"
            f"→ Rallumer !")

    # ── TÂCHE PLANIFIÉE ───────────────────────────────────
    def _install_task(self):
        if not self.sched.is_admin():
            messagebox.showerror("Admin requis",
                "La tâche planifiée nécessite des droits admin.\n"
                "Relancez en tant qu'administrateur.")
            return
        delay = int(self.delay_var.get() or 30)
        self._log(f"Installation tâche planifiée (délai: {delay}s)...", 'info')

        def run():
            ok = self.sched.install_task(delay)
            self.q.put(('task_installed', ok))
        threading.Thread(target=run, daemon=True).start()

    def _remove_task(self):
        if self.sched.remove_task():
            self._log("✓ Tâche supprimée", 'ok')
            self.lbl_task.config(text="⚪ Tâche supprimée", fg=C['text2'])
        else:
            self._log("✗ Impossible de supprimer la tâche", 'err')

    # ── EXTINCTION ────────────────────────────────────────
    def _shutdown(self):
        state = self.scanner.load_state()
        if not state:
            messagebox.showerror("Erreur", "Scannez d'abord les disques sains !")
            return
        if not self.sched.task_exists():
            if not messagebox.askyesno("Attention",
                "La tâche planifiée n'est pas installée !\n"
                "La détection auto ne fonctionnera pas.\n\n"
                "Éteindre quand même ?"):
                return

        if messagebox.askyesno("Éteindre le PC",
            "Le PC va s'éteindre dans 30 secondes.\n\n"
            "Après l'extinction :\n"
            "1. Branche le HDD abîmé (SATA + alim)\n"
            "2. Rallume le PC\n"
            "3. Le script se lance automatiquement\n\n"
            "Confirmer l'extinction ?"):
            self._log("⏻ Extinction dans 30 secondes...", 'warn')
            subprocess.Popen(['shutdown','/s','/t','30','/c',
                             'Smart HDD Monitor — Branchez le HDD abîmé avant de rallumer !'])
            messagebox.showinfo("Extinction",
                "Extinction dans 30 secondes.\n\n"
                "IMPORTANT : Branchez le HDD abîmé AVANT de rallumer !")

    # ── IMAGE ─────────────────────────────────────────────
    def _manual_image(self):
        """Lancer l'image manuellement"""
        # Trouver le disque source
        if self.automode and self.detected_disks:
            src_num = self.detected_disks[0]['number']
        else:
            # Demander à l'utilisateur de sélectionner dans le tree
            sel = self.dtree.selection()
            if not sel:
                messagebox.showinfo("Sélection", "Sélectionnez le disque abîmé dans la liste")
                return
            vals = self.dtree.item(sel[0], 'values')
            try: src_num = int(vals[0])
            except: return

        dst = self.out_var.get().strip()
        if not dst:
            messagebox.showerror("Erreur", "Spécifiez le chemin de l'image"); return

        src_disk = next((d for d in self.all_disks if d['number']==src_num), None)
        name = src_disk['name'] if src_disk else f"Drive{src_num}"

        if not messagebox.askyesno("Confirmer",
            f"Créer une image DD de :\n"
            f"Drive {src_num} — {name}\n\n"
            f"Vers : {dst}\n\n"
            f"Continuer ?"):
            return

        self.running = True
        self.btn_img.config(state=DISABLED)
        self.btn_stop_img.config(state=NORMAL)
        self.pv.set(0)
        self._log(f"▶ Image DD — Drive {src_num} → {dst}", 'title')

        # Supprimer la tâche maintenant qu'on l'utilise
        self.sched.remove_task()
        self._log("  Tâche planifiée supprimée (plus nécessaire)", 'info')

        self.engine = QuickImager(
            src_num, dst,
            log_cb  = self._log,
            prog_cb = lambda p,done,total,spd,eta,bad:
                      self.q.put(('prog',(p,done,total,spd,eta,bad)))
        )

        def run():
            ok = self.engine.run()
            self.q.put(('img_done', (ok, dst)))
        threading.Thread(target=run, daemon=True).start()

    def _stop_image(self):
        if self.engine: self.engine.stop()
        self.running = False
        self._log("⏹ Arrêt image demandé...", 'warn')

    def _auto_start(self):
        """Démarrage automatique en mode auto"""
        new = self.detected_disks[0]
        self._log("="*50, 'sep')
        self._log("⚡ DÉMARRAGE AUTOMATIQUE", 'big')
        self._log("="*50, 'sep')
        self._log(f"Nouveau disque détecté :", 'title')
        self._log(f"  {new['name']} — {new['size_str']} — Drive {new['number']}", 'ok')
        self._log(f"\nLancement de l'image dans 10 secondes...", 'warn')
        self._log(f"(Fermez cette fenêtre pour annuler)", 'info')

        # Countdown
        for i in range(10, 0, -1):
            self.after((10-i)*1000, lambda n=i: self.sv.set(f"⚡ Auto-start dans {n}s..."))

        self.after(10000, self._manual_image)

    # ── POLL ──────────────────────────────────────────────
    def _poll(self):
        try:
            while True:
                msg, data = self.q.get_nowait()
                if msg == 'log':
                    self._append_log(data[1], data[0])
                elif msg == 'disks':
                    self._on_disks(data)
                elif msg == 'task_installed':
                    if data:
                        self.lbl_task.config(text=f"✓ Tâche installée !", fg=C['green'])
                        self.btn_shutdown.config(state=NORMAL)
                        self._log(f"✓ Tâche planifiée installée : {TASK_NAME}", 'ok')
                        messagebox.showinfo("✓ Tâche installée",
                            f"Tâche planifiée installée !\n\n"
                            f"Au prochain boot, le script se lancera\n"
                            f"automatiquement après le login.\n\n"
                            f"Prochaine étape → Éteindre le PC")
                    else:
                        self._log("✗ Erreur installation tâche", 'err')
                        messagebox.showerror("Erreur",
                            "Impossible d'installer la tâche.\n"
                            "Vérifiez les droits admin.")
                elif msg == 'prog':
                    p,done,total,spd,eta,bad = data
                    self.pv.set(p)
                    self.plbl.config(text=f"{p:.1f}%  {done/1e9:.1f}/{total/1e9:.1f} GB")
                    self.sv_img['pct'].set(f"{p:.1f}%")
                    self.sv_img['spd'].set(f"{spd/1e6:.1f} MB/s")
                    self.sv_img['eta'].set(f"{int(eta//60)}m{int(eta%60)}s")
                    self.sv_img['bad'].set(str(bad))
                    self.sv.set(f"Image: {p:.1f}% — {spd/1e6:.1f} MB/s — {bad} bad sectors")
                elif msg == 'img_done':
                    ok, dst = data
                    self.running = False
                    self.btn_img.config(state=NORMAL)
                    self.btn_stop_img.config(state=DISABLED)
                    self.pv.set(100 if ok else self.pv.get())
                    if ok:
                        self._log("="*50, 'sep')
                        self._log("✓ IMAGE TERMINÉE !", 'big')
                        self._log(f"  Fichier : {dst}", 'ok')
                        self._log("  → Lancer Phantom Recover sur ce fichier", 'info')
                        messagebox.showinfo("✓ Image terminée !",
                            f"Image créée avec succès !\n\n"
                            f"Fichier :\n{dst}\n\n"
                            f"→ Copier sur KERBEROS-IA\n"
                            f"→ Lancer Phantom Recover !")
                    else:
                        self._log("✗ Image échouée", 'err')
        except queue.Empty: pass
        self.after(100, self._poll)

    def _log(self, text, tag='info'):
        self.q.put(('log', (tag, text)))

    def _append_log(self, text, tag):
        self.log_w.config(state=NORMAL)
        ts = datetime.now().strftime('%H:%M:%S')
        self.log_w.insert(END, f"[{ts}] {text}\n", tag)
        self.log_w.config(state=DISABLED)
        self.log_w.see(END)

    def _btn(self, p, text, cmd, color=None, small=False):
        c=color or C['accent']; f=FNS if small else ('Consolas',10,'bold'); py=3 if small else 7
        b=tk.Button(p,text=text,command=cmd,bg=C['bg3'],fg=c,activebackground=C['bg4'],
                    activeforeground=c,relief='flat',bd=0,font=f,cursor='hand2',padx=8,pady=py)
        b.bind('<Enter>',lambda e:b.config(bg=C['bg4']))
        b.bind('<Leave>',lambda e:b.config(bg=C['bg3']))
        return b


# ═══════════════════════════════════════════════════════════════
# ENTRY POINT
# ═══════════════════════════════════════════════════════════════
if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('--scan',       action='store_true', help='Scan et sauvegarde les disques sains (CLI)')
    parser.add_argument('--autodetect', action='store_true', help='Mode auto-détection (lancé par tâche planifiée)')
    parser.add_argument('--status',     action='store_true', help='Affiche l\'état sauvegardé')
    args = parser.parse_args()

    if args.scan:
        # Mode CLI — scan rapide sans GUI
        print("Smart HDD Monitor — Scan disques sains")
        scanner = DiskScanner()
        disks   = scanner.get_all_disks()
        print(f"✓ {len(disks)} disque(s) détecté(s):")
        for d in disks:
            print(f"  Drive {d['number']}: {d['name']} — {d['size_str']} — {d['health']}")
        scanner.save_state(disks)
        print(f"✓ Sauvegardé dans: {STATE_FILE}")

    elif args.status:
        scanner = DiskScanner()
        state   = scanner.load_state()
        if state:
            print(f"État sauvegardé le: {state['saved_at']}")
            for d in state['disks']:
                print(f"  Drive {d['number']}: {d['name']} — {d['size_str']}")
        else:
            print("Aucun état sauvegardé.")

    elif args.autodetect:
        # Mode automatique — lancé par la tâche planifiée
        run_autodetect()

    else:
        # GUI normale
        app = SmartMonitorApp()
        app.mainloop()
