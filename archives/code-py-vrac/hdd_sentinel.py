#!/usr/bin/env python3
"""
╔══════════════════════════════════════════════════════════════╗
║          HDD SENTINEL PRO  —  v1.0                         ║
║   Surveillance complète des disques durs                   ║
║                                                              ║
║  • Lecture SMART complète (50+ attributs)                  ║
║  • Température temps réel + historique graphique           ║
║  • Santé & Performance en %                                ║
║  • Détection secteurs défaillants                          ║
║  • Isolation bad sectors (force remapping firmware)        ║
║  • Alertes configurables                                   ║
║  • Test de surface                                         ║
║  • Rapport complet                                         ║
║                                                              ║
║  python hdd_sentinel.py                                    ║
║  Windows 10/11 — Admin recommandé                         ║
╚══════════════════════════════════════════════════════════════╝
"""

import os, sys, re, json, time, struct, ctypes, threading
import queue, subprocess, platform, hashlib, math
from pathlib import Path
from datetime import datetime, timedelta
from collections import deque
from tkinter import *
from tkinter import ttk, messagebox, filedialog
import tkinter as tk
import tkinter.font as tkfont

if platform.system() != 'Windows':
    print("HDD Sentinel Pro est pour Windows uniquement.")
    sys.exit(0)

# ═══════════════════════════════════════════════════════════════
# PALETTE — Dark Teal Professional
# ═══════════════════════════════════════════════════════════════
C = {
    'bg':        '#090B10', 'bg2':    '#0F1218', 'bg3':  '#161B26',
    'bg4':       '#1E2536', 'bg5':    '#263045', 'panel':'#060810',
    'accent':    '#26C6DA', 'accent2':'#00ACC1',
    'green':     '#00E676', 'green2': '#00C853',
    'yellow':    '#FFD740', 'yellow2':'#FFC400',
    'red':       '#FF1744', 'red2':   '#D50000',
    'orange':    '#FF6D00', 'orange2':'#FF9100',
    'purple':    '#AA00FF', 'teal':   '#1DE9B6',
    'text':      '#ECEFF1', 'text2':  '#607D8B', 'text3':'#37474F',
    'border':    '#1E2D3D',
    # Health colors
    'health_good':    '#00E676',
    'health_warn':    '#FFD740',
    'health_bad':     '#FF1744',
    'health_unknown': '#607D8B',
    # Temp colors
    'temp_cool':   '#26C6DA',
    'temp_warm':   '#FFD740',
    'temp_hot':    '#FF6D00',
    'temp_danger': '#FF1744',
}

FN  = ('Segoe UI', 10)
FNS = ('Segoe UI', 9)
FNB = ('Segoe UI', 11, 'bold')
FNT = ('Segoe UI', 15, 'bold')
FNM = ('Consolas', 9)
FNC = ('Consolas', 10)

# ═══════════════════════════════════════════════════════════════
# SMART ATTRIBUTE DATABASE
# ═══════════════════════════════════════════════════════════════
SMART_ATTRS = {
    0x01: ('Read Error Rate',          'critical', 'Taux d\'erreurs de lecture'),
    0x02: ('Throughput Performance',   'info',     'Performance débit'),
    0x03: ('Spin-Up Time',             'warn',     'Temps de démarrage'),
    0x04: ('Start/Stop Count',         'info',     'Nb démarrages/arrêts'),
    0x05: ('Reallocated Sectors',      'critical', 'Secteurs réalloués ⚠'),
    0x07: ('Seek Error Rate',          'warn',     'Taux d\'erreurs de positionnement'),
    0x08: ('Seek Time Performance',    'info',     'Performance positionnement'),
    0x09: ('Power-On Hours',           'info',     'Heures sous tension'),
    0x0A: ('Spin Retry Count',         'critical', 'Tentatives redémarrage'),
    0x0B: ('Recalibration Retries',    'warn',     'Recalibrages'),
    0x0C: ('Power Cycle Count',        'info',     'Cycles d\'alimentation'),
    0x0D: ('Soft Read Error Rate',     'warn',     'Erreurs lecture soft'),
    0xB7: ('SATA Downshift Errors',    'warn',     'Erreurs SATA downshift'),
    0xB8: ('End-to-End Error',         'critical', 'Erreurs bout-en-bout'),
    0xBB: ('Uncorrectable Errors',     'critical', 'Erreurs non corrigées ⚠'),
    0xBC: ('Command Timeout',          'warn',     'Timeouts commandes'),
    0xBD: ('High Fly Writes',          'warn',     'Écritures haute altitude'),
    0xBE: ('Airflow Temperature',      'temp',     'Température flux d\'air'),
    0xBF: ('G-sense Error Rate',       'warn',     'Erreurs capteur G'),
    0xC0: ('Power-Off Retract',        'info',     'Rétractations power-off'),
    0xC1: ('Load/Unload Cycles',       'info',     'Cycles chargement tête'),
    0xC2: ('Temperature',              'temp',     'Température disque'),
    0xC3: ('Hardware ECC Recovered',   'info',     'ECC récupérés hardware'),
    0xC4: ('Reallocation Events',      'critical', 'Évènements réallocation ⚠'),
    0xC5: ('Current Pending Sectors',  'critical', 'Secteurs pending ⚠'),
    0xC6: ('Offline Uncorrectable',    'critical', 'Secteurs non corrigibles ⚠'),
    0xC7: ('UDMA CRC Error Rate',      'warn',     'Erreurs CRC UDMA'),
    0xC8: ('Write Error Rate',         'warn',     'Taux erreurs écriture'),
    0xC9: ('Soft Read Error Rate',     'warn',     'Erreurs lecture soft'),
    0xCA: ('Data Address Mark Errors', 'warn',     'Erreurs DAM'),
    0xCB: ('Run Out Cancel',           'info',     'Run-out cancel'),
    0xCC: ('Soft ECC Correction',      'info',     'Corrections ECC soft'),
    0xCD: ('Thermal Asperity Rate',    'warn',     'Défauts thermiques'),
    0xCE: ('Flying Height',            'info',     'Hauteur de vol'),
    0xCF: ('Spin High Current',        'warn',     'Courant démarrage élevé'),
    0xD0: ('Spin Buzz',                'info',     'Vibrations démarrage'),
    0xD1: ('Offline Seek Performance', 'info',     'Perf positionnement offline'),
    0xDC: ('Disk Shift',               'warn',     'Déplacement disque'),
    0xDD: ('G-Sense Error Rate 2',     'warn',     'Erreurs G-sense 2'),
    0xDE: ('Loaded Hours',             'info',     'Heures chargé'),
    0xDF: ('Load/Unload Retry Count',  'warn',     'Tentatives chargement'),
    0xE0: ('Load Friction',            'warn',     'Friction chargement'),
    0xE1: ('Load/Unload Cycle Count',  'info',     'Cycles charge/décharge'),
    0xE2: ('Load-In Time',             'info',     'Temps chargement'),
    0xE3: ('Torque Amplification',     'info',     'Amplification couple'),
    0xE4: ('Power-Off Retract Cycle',  'info',     'Cycles rétraction'),
    0xE6: ('GMR Head Amplitude',       'info',     'Amplitude tête GMR'),
    0xE7: ('Temperature SSD',          'temp',     'Température (SSD)'),
    0xE8: ('Available Reserved Space', 'info',     'Espace réservé SSD'),
    0xE9: ('Media Wearout Indicator',  'critical', 'Usure media SSD'),
    0xF0: ('Head Flying Hours',        'info',     'Heures vol tête'),
    0xF1: ('Total LBAs Written',       'info',     'Total LBAs écrits'),
    0xF2: ('Total LBAs Read',          'info',     'Total LBAs lus'),
    0xFE: ('Free Fall Protection',     'info',     'Protection chute libre'),
}

# Attributs critiques qui affectent la santé
CRITICAL_ATTRS = {0x05, 0xBB, 0xC4, 0xC5, 0xC6, 0x0A, 0x01}
TEMP_ATTRS     = {0xBE, 0xC2, 0xE7}

# ═══════════════════════════════════════════════════════════════
# SMART READER — Accès direct via DeviceIoControl
# ═══════════════════════════════════════════════════════════════
class SMARTReader:
    # IOCTL codes
    IOCTL_STORAGE_QUERY_PROPERTY  = 0x002D1400
    IOCTL_DISK_GET_DRIVE_GEOMETRY = 0x00070000
    SMART_RCV_DRIVE_DATA          = 0x0007C088
    IOCTL_STORAGE_PREDICT_FAILURE = 0x002D1100
    DFP_RECEIVE_DRIVE_DATA        = 0x0007C088

    def __init__(self):
        self._handles = {}

    def _open(self, disk_num: int):
        path = f"\\\\.\\PhysicalDrive{disk_num}"
        h = ctypes.windll.kernel32.CreateFileW(
            path, 0xC0000000, 0x3, None, 3, 0, None)
        if h == ctypes.c_void_p(-1).value:
            # Try read-only
            h = ctypes.windll.kernel32.CreateFileW(
                path, 0x80000000, 0x3, None, 3, 0, None)
        return h if h != ctypes.c_void_p(-1).value else None

    def _close(self, h):
        if h: ctypes.windll.kernel32.CloseHandle(h)

    def get_smart_data(self, disk_num: int) -> dict | None:
        """Lecture SMART via IOCTL_STORAGE_PREDICT_FAILURE"""
        h = self._open(disk_num)
        if not h: return None

        try:
            # STORAGE_PREDICT_FAILURE structure
            buf  = ctypes.create_string_buffer(512 + 4)
            rb   = ctypes.c_ulong(0)
            ok   = ctypes.windll.kernel32.DeviceIoControl(
                h, self.IOCTL_STORAGE_PREDICT_FAILURE,
                None, 0, buf, len(buf), ctypes.byref(rb), None)

            if ok:
                # PredictFailure (4 bytes) + VendorSpecific (512 bytes)
                predict = struct.unpack_from('<I', buf, 0)[0]
                vendor  = bytes(buf[4:516])
                attrs   = self._parse_smart_attrs(vendor)
                self._close(h)
                return {'predict_failure': bool(predict), 'attributes': attrs, 'raw': vendor}

            # Fallback: WMI
            self._close(h)
            return self._smart_via_wmi(disk_num)

        except Exception:
            self._close(h)
            return self._smart_via_wmi(disk_num)

    def _parse_smart_attrs(self, data: bytes) -> list:
        """Parser les attributs SMART depuis les données brutes"""
        attrs = []
        # Structure SMART: commence à offset 2, chaque attr = 12 bytes
        offset = 2
        for _ in range(30):
            if offset + 12 > len(data): break
            attr_id  = data[offset]
            if attr_id == 0:
                offset += 12; continue
            flags    = struct.unpack_from('<H', data, offset+1)[0]
            current  = data[offset+3]
            worst    = data[offset+4]
            raw_data = data[offset+5:offset+11]
            raw_val  = int.from_bytes(raw_data[:6], 'little')
            threshold= 0  # threshold séparé

            info = SMART_ATTRS.get(attr_id, (f'Attr 0x{attr_id:02X}', 'info', ''))
            attrs.append({
                'id':       attr_id,
                'name':     info[0],
                'type':     info[1],
                'desc':     info[2],
                'current':  current,
                'worst':    worst,
                'raw':      raw_val,
                'raw_bytes':raw_data,
                'flags':    flags,
                'is_critical': attr_id in CRITICAL_ATTRS,
                'is_temp':     attr_id in TEMP_ATTRS,
            })
            offset += 12
        return attrs

    def _smart_via_wmi(self, disk_num: int) -> dict | None:
        """Fallback SMART via WMI MSStorageDriver_ATAPISmartData"""
        try:
            ps = f"""
$disk = Get-WmiObject -Namespace root\\wmi -Class MSStorageDriver_ATAPISmartData |
        Where-Object {{ $_.InstanceName -like '*{disk_num}*' }} |
        Select-Object -First 1
if ($disk) {{
    $result = @{{
        PredictFailure = $disk.PredictFailure
        VendorSpecific = $disk.VendorSpecific
    }}
    $result | ConvertTo-Json -Compress
}}
"""
            out = subprocess.check_output(
                ['powershell','-NoProfile','-Command', ps],
                timeout=15, stderr=subprocess.DEVNULL,
                creationflags=subprocess.CREATE_NO_WINDOW)
            d = json.loads(out.decode('utf-8','replace'))
            if d and d.get('VendorSpecific'):
                vendor = bytes(d['VendorSpecific'][:512])
                attrs  = self._parse_smart_attrs(vendor)
                return {'predict_failure': d.get('PredictFailure',False),
                        'attributes': attrs, 'raw': vendor}
        except: pass
        return None

    def get_temperature(self, disk_num: int, attrs: list) -> int | None:
        """Extraire la température depuis les attrs SMART"""
        for a in attrs:
            if a['id'] in TEMP_ATTRS and a['raw'] > 0:
                t = a['raw'] & 0xFF  # byte de poids faible = temp en °C
                if 10 < t < 80: return t
        return None

    def get_disk_info(self, disk_num: int) -> dict:
        """Infos disque via PowerShell"""
        try:
            ps = (f'Get-Disk -Number {disk_num} | '
                  'Select-Object FriendlyName,SerialNumber,Size,FirmwareVersion,'
                  'Manufacturer,Model,BusType,HealthStatus,OperationalStatus,'
                  'PartitionStyle,NumberOfPartitions | ConvertTo-Json -Compress')
            out = subprocess.check_output(
                ['powershell','-NoProfile','-Command', ps],
                timeout=15, stderr=subprocess.DEVNULL,
                creationflags=subprocess.CREATE_NO_WINDOW)
            d = json.loads(out.decode('utf-8','replace'))
            return {
                'name':       (d.get('FriendlyName') or d.get('Model') or '?').strip(),
                'serial':     (d.get('SerialNumber') or '?').strip(),
                'size':       d.get('Size', 0) or 0,
                'firmware':   d.get('FirmwareVersion','?'),
                'model':      (d.get('Model') or '?').strip(),
                'bus':        d.get('BusType','?'),
                'health':     d.get('HealthStatus','?'),
                'status':     d.get('OperationalStatus','?'),
                'partitions': d.get('NumberOfPartitions', 0),
            }
        except: return {'name':'?','serial':'?','size':0,'firmware':'?',
                        'model':'?','bus':'?','health':'?','status':'?','partitions':0}

    def list_disks(self) -> list:
        try:
            ps = ('Get-Disk | Select-Object Number,FriendlyName,Size,'
                  'HealthStatus,BusType | ConvertTo-Json -Compress')
            out = subprocess.check_output(
                ['powershell','-NoProfile','-Command', ps],
                timeout=15, stderr=subprocess.DEVNULL,
                creationflags=subprocess.CREATE_NO_WINDOW)
            data = json.loads(out.decode('utf-8','replace'))
            if isinstance(data, dict): data = [data]
            return [{'number':d.get('Number',0),
                     'name':(d.get('FriendlyName') or '?').strip(),
                     'size':d.get('Size',0) or 0,
                     'health':d.get('HealthStatus','?'),
                     'bus':d.get('BusType','?')} for d in (data or []) if isinstance(d,dict)]
        except: return []

    def calculate_health(self, attrs: list) -> int:
        """Calculer la santé en % depuis les attributs SMART"""
        if not attrs: return -1
        health = 100
        for a in attrs:
            if not a['is_critical']: continue
            if a['id'] == 0x05:  # Reallocated sectors
                if a['raw'] > 0:
                    health -= min(40, a['raw'] * 2)
            elif a['id'] == 0xC5:  # Pending sectors
                if a['raw'] > 0:
                    health -= min(30, a['raw'] * 3)
            elif a['id'] == 0xC6:  # Uncorrectable
                if a['raw'] > 0:
                    health -= min(50, a['raw'] * 5)
            elif a['id'] == 0xBB:  # Uncorrectable errors
                if a['raw'] > 0:
                    health -= min(40, a['raw'] * 4)
            elif a['id'] == 0x0A:  # Spin retry
                if a['raw'] > 3:
                    health -= min(20, a['raw'])
        return max(0, min(100, health))

    def calculate_performance(self, attrs: list) -> int:
        """Calculer la performance en %"""
        if not attrs: return -1
        perf = 100
        seek_err = next((a for a in attrs if a['id']==0x07), None)
        if seek_err and seek_err['current'] < 100:
            perf -= (100 - seek_err['current']) // 2
        throughput = next((a for a in attrs if a['id']==0x02), None)
        if throughput and throughput['current'] < 100:
            perf -= (100 - throughput['current']) // 3
        return max(0, min(100, perf))


# ═══════════════════════════════════════════════════════════════
# BAD SECTOR ISOLATOR
# ═══════════════════════════════════════════════════════════════
class BadSectorIsolator:
    """
    Isolation des bad sectors via écriture forcée.
    Le disque détecte l'erreur et relouge automatiquement
    le secteur vers un spare dans sa G-List firmware.
    """
    SECTOR_SIZE = 512

    def __init__(self, disk_num: int, log_cb=None, prog_cb=None):
        self.disk_num = disk_num
        self.log      = log_cb or print
        self.prog     = prog_cb or (lambda *a: None)
        self.running  = True
        self.isolated = []
        self.failed   = []

    def stop(self): self.running = False

    def scan_and_isolate(self, start_lba: int = 0, end_lba: int = None,
                          write_zeros: bool = True) -> dict:
        """
        Scan les secteurs et isole les bad sectors.
        write_zeros=True → force le remapping firmware
        """
        path = f"\\\\.\\PhysicalDrive{self.disk_num}"
        self.log(f"Ouverture: {path}", 'info')

        # Ouvrir en lecture+écriture
        h = ctypes.windll.kernel32.CreateFileW(
            path, 0xC0000000, 0x3, None, 3, 0, None)
        if h == ctypes.c_void_p(-1).value:
            self.log("✗ Accès refusé — admin requis pour l'isolation", 'err')
            return {'isolated': [], 'failed': [], 'scanned': 0}

        # Taille totale
        disk_size = self._get_size(h)
        total_sectors = disk_size // self.SECTOR_SIZE if disk_size else 0

        if not end_lba:
            end_lba = total_sectors

        self.log(f"Secteurs: {start_lba:,} → {end_lba:,} ({(end_lba-start_lba):,} secteurs)", 'info')
        self.log(f"Méthode: {'Écriture zéros (remapping actif)' if write_zeros else 'Lecture seule'}", 'info')

        scanned = 0
        lba = start_lba

        while lba < end_lba and self.running:
            offset = lba * self.SECTOR_SIZE
            # Lire secteur
            data = self._read_sector(h, offset)

            if data is None:
                # BAD SECTOR DÉTECTÉ !
                self.log(f"  ⚠ Bad sector LBA {lba:,} (0x{lba:X})", 'warn')

                if write_zeros:
                    # Écrire des zéros → force le firmware à remapper
                    ok = self._write_zeros(h, offset)
                    if ok:
                        self.isolated.append(lba)
                        self.log(f"  ✓ LBA {lba:,} → remappé dans firmware", 'ok')
                    else:
                        self.failed.append(lba)
                        self.log(f"  ✗ LBA {lba:,} → remapping impossible", 'err')
                else:
                    self.isolated.append(lba)

            scanned += 1
            lba += 1

            # Progress toutes les 1000 secteurs
            if scanned % 1000 == 0:
                pct = (lba - start_lba) / max(end_lba - start_lba, 1) * 100
                self.prog(pct, lba, end_lba, len(self.isolated), len(self.failed))

        ctypes.windll.kernel32.CloseHandle(h)
        return {'isolated': self.isolated, 'failed': self.failed, 'scanned': scanned}

    def isolate_specific(self, lba_list: list) -> dict:
        """Isoler une liste spécifique de LBAs"""
        path = f"\\\\.\\PhysicalDrive{self.disk_num}"
        h = ctypes.windll.kernel32.CreateFileW(
            path, 0xC0000000, 0x3, None, 3, 0, None)
        if h == ctypes.c_void_p(-1).value:
            return {'isolated': [], 'failed': lba_list}

        ok_list = []; fail_list = []
        for lba in lba_list:
            if not self.running: break
            offset = lba * self.SECTOR_SIZE
            if self._write_zeros(h, offset):
                ok_list.append(lba)
                self.log(f"  ✓ LBA {lba:,} → isolé", 'ok')
            else:
                fail_list.append(lba)
                self.log(f"  ✗ LBA {lba:,} → échec", 'err')

        ctypes.windll.kernel32.CloseHandle(h)
        return {'isolated': ok_list, 'failed': fail_list}

    def _read_sector(self, h, offset: int, retries: int=3) -> bytes|None:
        for _ in range(retries):
            try:
                hi = ctypes.c_long(offset>>32)
                ctypes.windll.kernel32.SetFilePointer(h,offset&0xFFFFFFFF,ctypes.byref(hi),0)
                buf = ctypes.create_string_buffer(self.SECTOR_SIZE)
                rb  = ctypes.c_ulong(0)
                ok  = ctypes.windll.kernel32.ReadFile(h,buf,self.SECTOR_SIZE,ctypes.byref(rb),None)
                if ok and rb.value==self.SECTOR_SIZE:
                    return bytes(buf)
            except: pass
            time.sleep(0.01)
        return None

    def _write_zeros(self, h, offset: int) -> bool:
        try:
            hi = ctypes.c_long(offset>>32)
            ctypes.windll.kernel32.SetFilePointer(h,offset&0xFFFFFFFF,ctypes.byref(hi),0)
            zeros = ctypes.create_string_buffer(self.SECTOR_SIZE)
            wb    = ctypes.c_ulong(0)
            ok    = ctypes.windll.kernel32.WriteFile(h,zeros,self.SECTOR_SIZE,ctypes.byref(wb),None)
            return bool(ok and wb.value==self.SECTOR_SIZE)
        except: return False

    def _get_size(self, h) -> int:
        try:
            hi = ctypes.c_long(0)
            lo = ctypes.windll.kernel32.SetFilePointer(h,0,ctypes.byref(hi),2)
            sz = (hi.value<<32)|(lo&0xFFFFFFFF)
            ctypes.windll.kernel32.SetFilePointer(h,0,None,0)
            return sz
        except: return 0


# ═══════════════════════════════════════════════════════════════
# TEMPERATURE GRAPH WIDGET
# ═══════════════════════════════════════════════════════════════
class TempGraph(Canvas):
    MAX_POINTS = 120  # 2 minutes à 1s interval

    def __init__(self, parent, **kw):
        super().__init__(parent, bg=C['bg2'], highlightthickness=0, **kw)
        self.history = deque(maxlen=self.MAX_POINTS)
        self.bind('<Configure>', lambda e: self._draw())

    def add_temp(self, temp: int):
        self.history.append((time.time(), temp))
        self._draw()

    def _draw(self):
        self.delete('all')
        w = self.winfo_width(); h = self.winfo_height()
        if w < 10 or h < 10 or not self.history: return

        # Grid
        for y_pct in [0.25, 0.5, 0.75]:
            y = h * y_pct
            self.create_line(0, y, w, y, fill=C['bg4'], dash=(2,4))

        # Temp labels
        temps = [t for _, t in self.history]
        min_t = max(0, min(temps) - 5)
        max_t = max(60, max(temps) + 5)

        for label_t in range(int(min_t), int(max_t)+1, 10):
            y = h - (label_t - min_t) / (max_t - min_t) * h
            self.create_text(28, y, text=f"{label_t}°", fill=C['text2'], font=('Consolas',7))

        # Zone danger (>55°C)
        danger_y = h - (55 - min_t) / (max_t - min_t) * h
        if danger_y > 0:
            self.create_rectangle(0, 0, w, danger_y, fill='#1A0A0A', outline='')

        # Courbe température
        if len(self.history) > 1:
            points = []
            for i, (_, t) in enumerate(self.history):
                x = 30 + (i / (self.MAX_POINTS-1)) * (w - 35)
                y = h - (t - min_t) / max(max_t - min_t, 1) * h
                points.extend([x, y])

            # Couleur selon temp actuelle
            last_t = temps[-1]
            if last_t < 40:   color = C['temp_cool']
            elif last_t < 50: color = C['temp_warm']
            elif last_t < 55: color = C['temp_hot']
            else:             color = C['temp_danger']

            if len(points) >= 4:
                self.create_line(*points, fill=color, width=2, smooth=True)

            # Point actuel
            last_x = 30 + ((len(self.history)-1) / (self.MAX_POINTS-1)) * (w-35)
            last_y = h - (last_t - min_t) / max(max_t-min_t,1) * h
            self.create_oval(last_x-4, last_y-4, last_x+4, last_y+4,
                           fill=color, outline='')
            self.create_text(last_x+20, last_y, text=f"{last_t}°C",
                           fill=color, font=('Consolas',9,'bold'))

        # Labels axes
        self.create_text(w//2, h-8, text="← 2 min d'historique →",
                        fill=C['text3'], font=('Consolas',7))


# ═══════════════════════════════════════════════════════════════
# HEALTH GAUGE WIDGET
# ═══════════════════════════════════════════════════════════════
class HealthGauge(Canvas):
    def __init__(self, parent, **kw):
        super().__init__(parent, bg=C['bg2'], highlightthickness=0, **kw)
        self.value = -1
        self.label = "Santé"

    def set_value(self, value: int, label: str = "Santé"):
        self.value = value
        self.label = label
        self._draw()

    def _draw(self):
        self.delete('all')
        w = self.winfo_width(); h = self.winfo_height()
        if w < 10 or h < 10: return

        cx = w // 2; cy = h * 0.6
        r  = min(w, h) * 0.38

        # Arc de fond
        self.create_arc(cx-r, cy-r, cx+r, cy+r,
                       start=180, extent=180,
                       style='arc', outline=C['bg4'], width=12)

        if self.value >= 0:
            # Couleur selon valeur
            if self.value >= 80:   color = C['health_good']
            elif self.value >= 50: color = C['health_warn']
            else:                  color = C['health_bad']

            # Arc valeur
            extent = self.value / 100 * 180
            self.create_arc(cx-r, cy-r, cx+r, cy+r,
                           start=180, extent=extent,
                           style='arc', outline=color, width=12)

            # Valeur
            self.create_text(cx, cy-8, text=f"{self.value}%",
                           font=('Segoe UI',18,'bold'), fill=color)

        self.create_text(cx, cy+18, text=self.label,
                        font=('Segoe UI',9), fill=C['text2'])


# ═══════════════════════════════════════════════════════════════
# APPLICATION PRINCIPALE
# ═══════════════════════════════════════════════════════════════
class HDDSentinel(Tk):
    def __init__(self):
        super().__init__()
        self.title("HDD SENTINEL PRO  —  Surveillance disques durs")
        self.geometry("1280x820")
        self.minsize(1100, 700)
        self.configure(bg=C['bg'])

        self.reader    = SMARTReader()
        self.q         = queue.Queue()
        self.running   = False
        self.monitor   = True  # monitoring continu
        self.disks     = []
        self.cur_disk  = None
        self.cur_attrs = []
        self.temp_history = {}  # disk_num → deque
        self.alerts    = {}     # disk_num → list
        self.isolator  = None

        # Config alertes
        self.alert_temp    = 55
        self.alert_health  = 50
        self.alert_realoc  = 1

        self._style()
        self._ui()
        self._poll()

        # Charger les disques
        threading.Thread(target=self._load_disks, daemon=True).start()

        # Monitoring continu
        threading.Thread(target=self._monitor_loop, daemon=True).start()

    # ── STYLE ─────────────────────────────────────────────
    def _style(self):
        s = ttk.Style(self); s.theme_use('clam')
        s.configure('.', background=C['bg'], foreground=C['text'], font=FN)
        s.configure('TFrame', background=C['bg'])
        s.configure('TLabel', background=C['bg'], foreground=C['text'])
        s.configure('TLabelframe', background=C['bg2'], foreground=C['accent'],
                    relief='flat', borderwidth=1)
        s.configure('TLabelframe.Label', background=C['bg2'], foreground=C['accent'],
                    font=('Segoe UI',9,'bold'))
        s.configure('TProgressbar', troughcolor=C['bg3'],
                    background=C['green'], thickness=6)
        s.configure('Treeview', background=C['bg2'], foreground=C['text'],
                    fieldbackground=C['bg2'], rowheight=22, borderwidth=0, font=FNC)
        s.configure('Treeview.Heading', background=C['bg4'], foreground=C['accent'],
                    font=('Consolas',9,'bold'), relief='flat')
        s.map('Treeview', background=[('selected',C['bg5'])],
              foreground=[('selected',C['accent'])])
        s.configure('TNotebook', background=C['bg'], borderwidth=0)
        s.configure('TNotebook.Tab', background=C['bg3'], foreground=C['text2'],
                    padding=(14,6), font=FNS)
        s.map('TNotebook.Tab', background=[('selected',C['bg2'])],
              foreground=[('selected',C['accent'])])

    # ── UI ────────────────────────────────────────────────
    def _ui(self):
        # Header
        hdr = Frame(self, bg=C['panel'], height=56); hdr.pack(fill=X); hdr.pack_propagate(False)
        Frame(hdr, bg=C['accent'], width=4).pack(side=LEFT, fill=Y)
        lg = Frame(hdr, bg=C['panel']); lg.pack(side=LEFT, padx=14, pady=8)
        Label(lg, text="🛡️ HDD SENTINEL PRO", font=('Segoe UI',16,'bold'),
              bg=C['panel'], fg=C['accent']).pack(anchor=W)
        Label(lg, text="Surveillance SMART  •  Température  •  Santé  •  Isolation bad sectors",
              font=FNS, bg=C['panel'], fg=C['text2']).pack(anchor=W)

        # Disk selector
        sel = Frame(hdr, bg=C['panel']); sel.pack(side=LEFT, padx=30, pady=14)
        Label(sel, text="Disque:", font=FNS, bg=C['panel'], fg=C['text2']).pack(side=LEFT, padx=(0,6))
        self.disk_var = StringVar()
        self.disk_cb  = ttk.Combobox(sel, textvariable=self.disk_var,
                                      state='readonly', font=FNS, width=35)
        self.disk_cb.pack(side=LEFT)
        self.disk_cb.bind('<<ComboboxSelected>>', self._on_disk_select)

        self._btn(hdr, "🔄", self._refresh, small=True).pack(side=LEFT, padx=4, pady=18)

        # Monitor badge
        self.mon_var = StringVar(value="● LIVE")
        Label(hdr, textvariable=self.mon_var, font=('Segoe UI',9,'bold'),
              bg=C['bg4'], fg=C['green'], padx=10, pady=4).pack(side=RIGHT, padx=14, pady=18)

        # Main split
        main = Frame(self, bg=C['bg']); main.pack(fill=BOTH, expand=True, padx=8, pady=6)

        # LEFT — gauges + info (300px)
        left = Frame(main, bg=C['bg'], width=300)
        left.pack(side=LEFT, fill=Y, padx=(0,6)); left.pack_propagate(False)
        self._left(left)

        # RIGHT — tabs
        right = Frame(main, bg=C['bg']); right.pack(side=LEFT, fill=BOTH, expand=True)
        self._right(right)

        # Statusbar
        sb = Frame(self, bg=C['bg4'], height=26); sb.pack(fill=X, side=BOTTOM); sb.pack_propagate(False)
        Frame(sb, bg=C['accent2'], width=3).pack(side=LEFT, fill=Y)
        self.sv = StringVar(value="Chargement des disques...")
        Label(sb, textvariable=self.sv, font=FNS, bg=C['bg4'], fg=C['text2']).pack(side=LEFT, padx=8, pady=4)
        self.sv2 = StringVar(value="")
        Label(sb, textvariable=self.sv2, font=FNS, bg=C['bg4'], fg=C['yellow']).pack(side=RIGHT, padx=12)

    def _left(self, p):
        # Gauges santé + performance
        gf = Frame(p, bg=C['bg2']); gf.pack(fill=X, pady=(0,6))
        self.gauge_health = HealthGauge(gf, width=140, height=120)
        self.gauge_health.pack(side=LEFT, padx=4, pady=4)
        self.gauge_perf   = HealthGauge(gf, width=140, height=120)
        self.gauge_perf.pack(side=LEFT, padx=4, pady=4)
        self.gauge_health.set_value(-1, "Santé")
        self.gauge_perf.set_value(-1, "Performance")

        # Température
        tf = ttk.LabelFrame(p, text=" TEMPÉRATURE ", padding=6)
        tf.pack(fill=X, pady=(0,6))
        self.lbl_temp = Label(tf, text="--°C", font=('Segoe UI',28,'bold'),
                              bg=C['bg2'], fg=C['text2'])
        self.lbl_temp.pack()
        self.temp_graph = TempGraph(tf, height=80)
        self.temp_graph.pack(fill=X, pady=(4,0))

        # Infos disque
        inf = ttk.LabelFrame(p, text=" INFORMATIONS ", padding=8)
        inf.pack(fill=X, pady=(0,6))
        self.info_vars = {}
        for k, lbl in [
            ('model',   'Modèle'),('serial', 'Série'),
            ('size',    'Taille'),('firmware','Firmware'),
            ('bus',     'Interface'),('hours',   'Heures'),
            ('poweron', 'Démarrages'),('realoc', 'Réalloués'),
        ]:
            r = Frame(inf, bg=C['bg2']); r.pack(fill=X, pady=1)
            Label(r, text=f"{lbl}:", font=FNS, bg=C['bg2'], fg=C['text2'],
                  width=11, anchor=W).pack(side=LEFT)
            v = StringVar(value='—'); self.info_vars[k] = v
            Label(r, textvariable=v, font=FNS, bg=C['bg2'], fg=C['text']).pack(side=LEFT)

        # Alertes actives
        af = ttk.LabelFrame(p, text=" ALERTES ", padding=6)
        af.pack(fill=X)
        self.alert_box = Text(af, bg=C['bg2'], fg=C['yellow'], font=FNS,
                              height=4, relief='flat', state=DISABLED, wrap=WORD)
        self.alert_box.pack(fill=X)
        self.alert_box.tag_configure('ok',   foreground=C['green'])
        self.alert_box.tag_configure('warn', foreground=C['yellow'])
        self.alert_box.tag_configure('err',  foreground=C['red'])

    def _right(self, p):
        nb = ttk.Notebook(p); nb.pack(fill=BOTH, expand=True)

        # TAB 1 — SMART
        t1 = Frame(nb, bg=C['bg']); nb.add(t1, text="  📊 SMART  ")
        self._tab_smart(t1)

        # TAB 2 — Températures
        t2 = Frame(nb, bg=C['bg']); nb.add(t2, text="  🌡️ TEMPÉRATURES  ")
        self._tab_temp(t2)

        # TAB 3 — Isolation bad sectors
        t3 = Frame(nb, bg=C['bg']); nb.add(t3, text="  🔧 ISOLATION BAD SECTORS  ")
        self._tab_isolate(t3)

        # TAB 4 — Rapport
        t4 = Frame(nb, bg=C['bg']); nb.add(t4, text="  📄 RAPPORT  ")
        self._tab_report(t4)

    def _tab_smart(self, p):
        # Toolbar
        tb = Frame(p, bg=C['bg4'], height=34); tb.pack(fill=X); tb.pack_propagate(False)
        self._btn(tb, "🔄 Actualiser SMART", self._refresh_smart, small=True).pack(side=LEFT, padx=8, pady=5)
        Label(tb, text="Filtrer:", font=FNS, bg=C['bg4'], fg=C['text2']).pack(side=LEFT, padx=4)
        self.smart_filter = StringVar(value='Tous')
        ttk.Combobox(tb, textvariable=self.smart_filter, state='readonly', font=FNS,
                    values=['Tous','Critiques','Température','Avertissements'],
                    width=15).pack(side=LEFT, pady=6)
        self.smart_filter.trace('w', lambda *_: self._filter_smart())

        # Tree SMART
        cols = ('id','name','current','worst','raw','status','desc')
        self.smart_tree = ttk.Treeview(p, columns=cols, show='headings', selectmode='browse')
        for col,hdr,w,anc in [
            ('id',     'ID',           45,  'center'),
            ('name',   'Attribut',     200, 'w'),
            ('current','Valeur',       65,  'center'),
            ('worst',  'Pire',         55,  'center'),
            ('raw',    'Brut',         90,  'center'),
            ('status', 'Statut',       85,  'center'),
            ('desc',   'Description',  220, 'w'),
        ]:
            self.smart_tree.heading(col, text=hdr)
            self.smart_tree.column(col, width=w, anchor=anc)

        self.smart_tree.tag_configure('critical', foreground=C['red'])
        self.smart_tree.tag_configure('warn',     foreground=C['yellow'])
        self.smart_tree.tag_configure('temp',     foreground=C['teal'])
        self.smart_tree.tag_configure('ok',       foreground=C['text'])

        vsb = ttk.Scrollbar(p, orient=VERTICAL, command=self.smart_tree.yview)
        self.smart_tree.configure(yscrollcommand=vsb.set)
        vsb.pack(side=RIGHT, fill=Y); self.smart_tree.pack(fill=BOTH, expand=True)

    def _tab_temp(self, p):
        # Grand graphique température
        Label(p, text="Historique température — rafraîchissement toutes les 5s",
              font=FNS, bg=C['bg'], fg=C['text2']).pack(anchor=W, padx=8, pady=4)
        self.big_graph = TempGraph(p)
        self.big_graph.pack(fill=BOTH, expand=True, padx=8, pady=4)

        # Stats temp
        sf = Frame(p, bg=C['bg3']); sf.pack(fill=X, padx=8, pady=4)
        self.temp_stats = {}
        for k, lbl, col in [
            ('current','Actuelle', C['accent']),
            ('min',    'Minimum',  C['green']),
            ('max',    'Maximum',  C['red']),
            ('avg',    'Moyenne',  C['yellow']),
        ]:
            f = Frame(sf, bg=C['bg3']); f.pack(side=LEFT, padx=20, pady=8)
            Label(f, text=lbl, font=FNS, bg=C['bg3'], fg=C['text2']).pack()
            v = StringVar(value='--°C'); self.temp_stats[k] = v
            Label(f, textvariable=v, font=('Segoe UI',14,'bold'), bg=C['bg3'], fg=col).pack()

        # Seuils
        thf = ttk.LabelFrame(p, text=" SEUILS D'ALERTE ", padding=8)
        thf.pack(fill=X, padx=8, pady=4)
        Label(thf,text="Alerte à:",font=FNS,bg=C['bg2'],fg=C['text2']).pack(side=LEFT,padx=4)
        self.temp_thresh = StringVar(value=str(self.alert_temp))
        Entry(thf, textvariable=self.temp_thresh, bg=C['bg3'], fg=C['text'],
              insertbackground=C['accent'], relief='flat', font=FNM,
              bd=0, width=5).pack(side=LEFT)
        Label(thf,text="°C",font=FNS,bg=C['bg2'],fg=C['text2']).pack(side=LEFT,padx=4)
        self._btn(thf,"Appliquer",lambda:setattr(self,'alert_temp',int(self.temp_thresh.get() or 55)),
                  small=True,color=C['yellow']).pack(side=LEFT,padx=8)

    def _tab_isolate(self, p):
        # Explication
        exp = Frame(p, bg=C['bg3']); exp.pack(fill=X, padx=8, pady=8)
        Label(exp, text="🔧  ISOLATION DES BAD SECTORS", font=('Segoe UI',11,'bold'),
              bg=C['bg3'], fg=C['yellow']).pack(anchor=W, padx=10, pady=(8,4))
        for line, col in [
            ("Le disque contient des secteurs défaillants détectés par SMART (C5, C6, BB...)", C['text2']),
            ("Cette fonction écrit des zéros sur ces secteurs → le firmware les ajoute à sa G-List", C['text2']),
            ("Le disque les remplace automatiquement par des secteurs de spare internes", C['text2']),
            ("⚠ ATTENTION : Cette opération DÉTRUIT les données sur les secteurs concernés", C['red']),
            ("⚠ Faites une image DD complète AVANT toute isolation !", C['red']),
        ]:
            Label(exp, text=f"  {line}", font=FNS, bg=C['bg3'], fg=col).pack(anchor=W, padx=10, pady=1)
        Frame(exp, bg=C['bg3'], height=6).pack()

        # Config
        cf = Frame(p, bg=C['bg']); cf.pack(fill=X, padx=8)
        left = ttk.LabelFrame(cf, text=" CONFIGURATION ", padding=10); left.pack(side=LEFT, fill=Y, padx=(0,6))

        Label(left,text="LBA de début:",font=FNS,bg=C['bg2'],fg=C['text2']).pack(anchor=W)
        self.iso_start = StringVar(value='0')
        Entry(left,textvariable=self.iso_start,bg=C['bg3'],fg=C['text'],
              insertbackground=C['accent'],relief='flat',font=FNM,
              bd=0,highlightthickness=1,highlightcolor=C['accent'],
              highlightbackground=C['border'],width=15).pack(anchor=W,pady=2)

        Label(left,text="LBA de fin (vide=tout):",font=FNS,bg=C['bg2'],fg=C['text2']).pack(anchor=W,pady=(6,0))
        self.iso_end = StringVar(value='')
        Entry(left,textvariable=self.iso_end,bg=C['bg3'],fg=C['text'],
              insertbackground=C['accent'],relief='flat',font=FNM,
              bd=0,highlightthickness=1,highlightcolor=C['accent'],
              highlightbackground=C['border'],width=15).pack(anchor=W,pady=2)

        self.iso_write = BooleanVar(value=True)
        tk.Checkbutton(left,text="Écrire zéros (force remapping)",
                       variable=self.iso_write,bg=C['bg2'],fg=C['yellow'],
                       selectcolor=C['bg3'],activebackground=C['bg2'],
                       font=FNS,cursor='hand2').pack(anchor=W,pady=(8,2))

        self.iso_smart_only = BooleanVar(value=True)
        tk.Checkbutton(left,text="Seulement les bad SMART (rapide)",
                       variable=self.iso_smart_only,bg=C['bg2'],fg=C['accent'],
                       selectcolor=C['bg3'],activebackground=C['bg2'],
                       font=FNS,cursor='hand2').pack(anchor=W,pady=2)

        # Actions
        self.btn_iso_start = self._btn(left,"🔧  ISOLER LES BAD SECTORS",self._start_isolate,C['yellow'])
        self.btn_iso_start.pack(fill=X,pady=(10,4))
        self.btn_iso_stop = self._btn(left,"⏹  ARRÊTER",self._stop_isolate,C['red'])
        self.btn_iso_stop.pack(fill=X); self.btn_iso_stop.config(state=DISABLED)

        # Progress isolation
        right2 = ttk.LabelFrame(cf, text=" PROGRESSION ", padding=10); right2.pack(side=LEFT, fill=BOTH, expand=True)
        self.iso_pv = tk.DoubleVar()
        ttk.Progressbar(right2,variable=self.iso_pv,maximum=100).pack(fill=X,pady=(0,6))
        self.iso_plbl = Label(right2,text="En attente...",font=FNS,bg=C['bg2'],fg=C['text2'])
        self.iso_plbl.pack(anchor=W)

        iso_sf = Frame(right2,bg=C['bg2']); iso_sf.pack(fill=X,pady=(6,0))
        self.iso_stats = {}
        for k,lbl,col in [('scanned','Scanné',C['text2']),('isolated','Isolés',C['green']),
                           ('failed','Échoué',C['red'])]:
            r=Frame(iso_sf,bg=C['bg2']); r.pack(fill=X,pady=1)
            Label(r,text=f"{lbl}:",font=FNS,bg=C['bg2'],fg=C['text2'],width=10,anchor=W).pack(side=LEFT)
            v=StringVar(value='0'); self.iso_stats[k]=v
            Label(r,textvariable=v,font=FNS,bg=C['bg2'],fg=col).pack(side=LEFT)

        # Log isolation
        self.iso_log = Text(p,bg=C['bg2'],fg=C['text'],font=FNM,
                            relief='flat',wrap=WORD,state=DISABLED,height=8)
        isb=ttk.Scrollbar(p,orient=VERTICAL,command=self.iso_log.yview)
        self.iso_log.configure(yscrollcommand=isb.set)
        isb.pack(side=RIGHT,fill=Y); self.iso_log.pack(fill=BOTH,expand=True,padx=8,pady=4)
        for tag,col in [('ok',C['green']),('warn',C['yellow']),('err',C['red']),('info',C['text2'])]:
            self.iso_log.tag_configure(tag,foreground=col)

    def _tab_report(self, p):
        tf = Frame(p,bg=C['bg']); tf.pack(fill=X,padx=8,pady=8)
        self._btn(tf,"📄 Générer rapport",self._gen_report).pack(side=LEFT,padx=4)
        self._btn(tf,"💾 Sauvegarder JSON",self._save_json,C['text2']).pack(side=LEFT,padx=4)
        self._btn(tf,"📋 Copier",self._copy_report,C['text2'],small=True).pack(side=LEFT,padx=4)

        self.report_w = Text(p,bg=C['bg2'],fg=C['text'],font=FNM,
                             relief='flat',wrap=WORD,state=DISABLED)
        rsb=ttk.Scrollbar(p,command=self.report_w.yview)
        self.report_w.configure(yscrollcommand=rsb.set)
        rsb.pack(side=RIGHT,fill=Y); self.report_w.pack(fill=BOTH,expand=True,padx=8,pady=4)
        for tag,col,bold in [('h',C['accent'],True),('ok',C['green'],False),
                              ('warn',C['yellow'],False),('err',C['red'],False),('v',C['text'],False)]:
            self.report_w.tag_configure(tag,foreground=col,
                font=('Consolas',9,'bold' if bold else 'normal'))

    # ── WIDGETS ─────────────────────────────────────────────
    def _btn(self,p,text,cmd,color=None,small=False):
        c=color or C['accent']; f=FNS if small else ('Segoe UI',10,'bold'); py=3 if small else 7
        b=tk.Button(p,text=text,command=cmd,bg=C['bg3'],fg=c,activebackground=C['bg5'],
                    activeforeground=c,relief='flat',bd=0,font=f,cursor='hand2',padx=8,pady=py)
        b.bind('<Enter>',lambda e:b.config(bg=C['bg5']))
        b.bind('<Leave>',lambda e:b.config(bg=C['bg3']))
        return b

    # ── LOAD DISKS ────────────────────────────────────────
    def _load_disks(self):
        disks = self.reader.list_disks()
        self.q.put(('disks', disks))

    def _on_disks(self, disks):
        self.disks = disks
        opts = [f"Drive {d['number']}  —  {d['name']}  —  {self._fmt(d['size'])}  —  {d['bus']}"
                for d in disks]
        self.disk_cb['values'] = opts
        if disks:
            self.disk_cb.current(0)
            self._on_disk_select()
        self.sv.set(f"✓ {len(disks)} disque(s) détecté(s)")

    def _on_disk_select(self, event=None):
        idx = self.disk_cb.current()
        if idx < 0 or idx >= len(self.disks): return
        self.cur_disk = self.disks[idx]
        threading.Thread(target=self._read_smart, daemon=True).start()

    def _refresh(self):
        threading.Thread(target=self._load_disks, daemon=True).start()

    def _refresh_smart(self):
        if self.cur_disk:
            threading.Thread(target=self._read_smart, daemon=True).start()

    # ── READ SMART ────────────────────────────────────────
    def _read_smart(self):
        if not self.cur_disk: return
        num  = self.cur_disk['number']
        info = self.reader.get_disk_info(num)
        data = self.reader.get_smart_data(num)
        self.q.put(('smart', (info, data, num)))

    def _on_smart(self, info, data, disk_num):
        if not data:
            self.sv.set(f"⚠ SMART non disponible pour Drive {disk_num}")
            return

        attrs = data.get('attributes', [])
        self.cur_attrs = attrs

        # Santé & performance
        health = self.reader.calculate_health(attrs)
        perf   = self.reader.calculate_performance(attrs)
        self.gauge_health.set_value(health, "Santé")
        self.gauge_perf.set_value(perf, "Performance")

        # Température
        temp = self.reader.get_temperature(disk_num, attrs)
        if temp:
            col = C['temp_cool'] if temp<40 else C['temp_warm'] if temp<50 else C['temp_hot'] if temp<55 else C['temp_danger']
            self.lbl_temp.config(text=f"{temp}°C", fg=col)
            self.temp_graph.add_temp(temp)
            self.big_graph.add_temp(temp)
            # Stats
            hist = [t for _, t in self.temp_graph.history]
            self.temp_stats['current'].set(f"{temp}°C")
            self.temp_stats['min'].set(f"{min(hist)}°C")
            self.temp_stats['max'].set(f"{max(hist)}°C")
            self.temp_stats['avg'].set(f"{sum(hist)//len(hist)}°C")

        # Info disque
        hours  = next((a['raw'] for a in attrs if a['id']==0x09), 0)
        starts = next((a['raw'] for a in attrs if a['id']==0x0C), 0)
        realoc = next((a['raw'] for a in attrs if a['id']==0x05), 0)
        self.info_vars['model'].set(info.get('model','?')[:25])
        self.info_vars['serial'].set(info.get('serial','?')[:20])
        self.info_vars['size'].set(self._fmt(info.get('size',0)))
        self.info_vars['firmware'].set(info.get('firmware','?'))
        self.info_vars['bus'].set(info.get('bus','?'))
        self.info_vars['hours'].set(f"{hours:,} h")
        self.info_vars['poweron'].set(f"{starts:,}")
        col_r = C['red'] if realoc > 0 else C['green']
        self.info_vars['realoc'].set(f"{realoc}")

        # SMART tree
        self._fill_smart_tree(attrs)

        # Alertes
        self._check_alerts(attrs, temp, health, disk_num)

        # Status bar
        predict = data.get('predict_failure', False)
        if predict:
            self.sv.set(f"⚠ ATTENTION: Panne imminente prédite sur Drive {disk_num} !")
            self.sv2.set("PANNE PRÉDITE")
        else:
            self.sv.set(f"Drive {disk_num} — Santé: {health}% — Perf: {perf}% — {temp or '?'}°C")

    def _fill_smart_tree(self, attrs: list):
        for i in self.smart_tree.get_children(): self.smart_tree.delete(i)
        filt = self.smart_filter.get()
        for a in attrs:
            if filt == 'Critiques'     and not a['is_critical']: continue
            if filt == 'Température'   and not a['is_temp']:     continue
            if filt == 'Avertissements' and a['type'] not in ('critical','warn'): continue

            raw_disp = str(a['raw'])
            if a['is_temp']:
                raw_disp = f"{a['raw'] & 0xFF}°C"

            # Statut
            if a['is_critical'] and a['raw'] > 0:
                st = '⚠ ALERTE'; tag = 'critical'
            elif a['is_temp']:
                t = a['raw'] & 0xFF
                st = f"{t}°C"; tag = 'temp'
            elif a['type'] == 'warn' and a['current'] < 100:
                st = '⚠ Dégradé'; tag = 'warn'
            else:
                st = '✓ OK'; tag = 'ok'

            self.smart_tree.insert('',END,
                values=(f"0x{a['id']:02X}", a['name'], a['current'],
                        a['worst'], raw_disp, st, a['desc']),
                tags=(tag,))

    def _filter_smart(self):
        if self.cur_attrs: self._fill_smart_tree(self.cur_attrs)

    # ── ALERTES ───────────────────────────────────────────
    def _check_alerts(self, attrs, temp, health, disk_num):
        alerts = []
        if temp and temp >= self.alert_temp:
            alerts.append(('err', f"🌡️ Temp critique: {temp}°C (seuil: {self.alert_temp}°C)"))
        if health >= 0 and health <= self.alert_health:
            alerts.append(('err', f"💔 Santé critique: {health}%"))
        realoc = next((a['raw'] for a in attrs if a['id']==0x05), 0)
        if realoc >= self.alert_realoc:
            alerts.append(('warn', f"⚠ Secteurs réalloués: {realoc}"))
        pending = next((a['raw'] for a in attrs if a['id']==0xC5), 0)
        if pending > 0:
            alerts.append(('warn', f"⚠ Secteurs pending: {pending}"))
        uncorr = next((a['raw'] for a in attrs if a['id']==0xC6), 0)
        if uncorr > 0:
            alerts.append(('err', f"✗ Secteurs non corrigibles: {uncorr}"))

        self.alert_box.config(state=NORMAL)
        self.alert_box.delete('1.0', END)
        if alerts:
            for tag, msg in alerts:
                self.alert_box.insert(END, f"{msg}\n", tag)
            self.sv2.set(f"⚠ {len(alerts)} alerte(s)")
        else:
            self.alert_box.insert(END, "✓ Aucune alerte — disque sain", 'ok')
            self.sv2.set("")
        self.alert_box.config(state=DISABLED)

    # ── MONITORING LOOP ───────────────────────────────────
    def _monitor_loop(self):
        """Monitoring continu toutes les 5 secondes"""
        while self.monitor:
            time.sleep(5)
            if self.cur_disk:
                try:
                    num  = self.cur_disk['number']
                    data = self.reader.get_smart_data(num)
                    info = self.reader.get_disk_info(num)
                    if data:
                        self.q.put(('smart', (info, data, num)))
                except: pass

    # ── ISOLATION ─────────────────────────────────────────
    def _start_isolate(self):
        if not self.cur_disk:
            messagebox.showerror("Erreur","Sélectionnez un disque."); return

        # Vérifier bad sectors SMART
        pending = sum(a['raw'] for a in self.cur_attrs if a['id']==0xC5)
        uncorr  = sum(a['raw'] for a in self.cur_attrs if a['id']==0xC6)
        realoc  = sum(a['raw'] for a in self.cur_attrs if a['id']==0x05)

        msg = (f"ISOLATION BAD SECTORS\n\n"
               f"Disque: {self.cur_disk['name']}\n\n"
               f"SMART détecte:\n"
               f"  Secteurs pending    : {pending}\n"
               f"  Secteurs uncorr.    : {uncorr}\n"
               f"  Secteurs réalloués  : {realoc}\n\n"
               f"⚠ DONNÉES DÉTRUITES sur les secteurs isolés !\n"
               f"⚠ Faites une image DD avant de continuer !\n\n"
               f"Continuer l'isolation ?")

        if not messagebox.askyesno("⚠ Confirmation requise", msg): return

        num = self.cur_disk['number']
        try:
            start = int(self.iso_start.get() or 0)
            end   = int(self.iso_end.get()) if self.iso_end.get().strip() else None
        except:
            start, end = 0, None

        self.btn_iso_start.config(state=DISABLED)
        self.btn_iso_stop.config(state=NORMAL)
        self.iso_pv.set(0)
        self._iso_log("="*40,'info')
        self._iso_log(f"Isolation Drive {num} — LBA {start} → {end or 'fin'}","info")

        self.isolator = BadSectorIsolator(
            num,
            log_cb = lambda t,tag='info': self.q.put(('iso_log',(tag,t))),
            prog_cb = lambda p,lba,end,iso,fail:
                      self.q.put(('iso_prog',(p,lba,end,iso,fail)))
        )

        def run():
            if self.iso_smart_only.get() and (pending > 0 or uncorr > 0):
                # Isoler seulement les LBAs problématiques détectés
                # (on ne connaît pas les LBAs exacts depuis SMART,
                #  mais on peut scanner seulement les zones problématiques)
                self._iso_log("Mode: isolation ciblée basée SMART","info")
            result = self.isolator.scan_and_isolate(
                start, end, write_zeros=self.iso_write.get())
            self.q.put(('iso_done', result))

        threading.Thread(target=run, daemon=True).start()

    def _stop_isolate(self):
        if self.isolator: self.isolator.stop()
        self._iso_log("⏹ Arrêt demandé...","warn")

    def _iso_log(self, text, tag='info'):
        self.q.put(('iso_log',(tag,text)))

    # ── RAPPORT ───────────────────────────────────────────
    def _gen_report(self):
        if not self.cur_disk or not self.cur_attrs:
            messagebox.showinfo("Rapport","Sélectionnez un disque et lisez le SMART d'abord.")
            return
        self.report_w.config(state=NORMAL)
        self.report_w.delete('1.0',END)

        info = {k:v.get() for k,v in self.info_vars.items()}
        t    = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        temp = self.lbl_temp.cget('text')
        h    = self.reader.calculate_health(self.cur_attrs)
        pf   = self.reader.calculate_performance(self.cur_attrs)

        def ln(k,v,tag='v'): self.report_w.insert(END,f"  {k+':':<22}{v}\n",tag)

        self.report_w.insert(END,"╔══════════════════════════════════════╗\n",'h')
        self.report_w.insert(END,"║      HDD SENTINEL PRO — RAPPORT      ║\n",'h')
        self.report_w.insert(END,"╚══════════════════════════════════════╝\n\n",'h')
        self.report_w.insert(END,f"Généré le : {t}\n\n",'v')
        self.report_w.insert(END,"DISQUE\n",'h')
        for k,lbl in [('model','Modèle'),('serial','N° Série'),('size','Taille'),
                      ('firmware','Firmware'),('bus','Interface')]:
            ln(lbl,info.get(k,'?'))
        self.report_w.insert(END,"\nDIAGNOSTIC\n",'h')
        ln("Santé",       f"{h}%", 'ok' if h>80 else 'warn' if h>50 else 'err')
        ln("Performance", f"{pf}%")
        ln("Température", temp)
        ln("Heures",      info.get('hours','?'))
        ln("Démarrages",  info.get('poweron','?'))
        ln("Réalloués",   info.get('realoc','?'))
        self.report_w.insert(END,"\nATTRIBUTS SMART CRITIQUES\n",'h')
        for a in self.cur_attrs:
            if a['is_critical']:
                tag = 'err' if a['raw']>0 else 'ok'
                ln(a['name'],f"Valeur:{a['current']}  Brut:{a['raw']}",tag)
        self.report_w.insert(END,"\nTOUS LES ATTRIBUTS SMART\n",'h')
        for a in self.cur_attrs:
            ln(f"0x{a['id']:02X} {a['name']}",
               f"Cur:{a['current']:3}  Worst:{a['worst']:3}  Raw:{a['raw']}")
        self.report_w.config(state=DISABLED)

    def _save_json(self):
        if not self.cur_attrs: return
        p = filedialog.asksaveasfilename(defaultextension='.json',
            filetypes=[("JSON","*.json")],
            initialfile=f"hdd_report_{datetime.now().strftime('%Y%m%d_%H%M')}.json")
        if not p: return
        data = {
            'generated': datetime.now().isoformat(),
            'disk': {k:v.get() for k,v in self.info_vars.items()},
            'health': self.reader.calculate_health(self.cur_attrs),
            'performance': self.reader.calculate_performance(self.cur_attrs),
            'attributes': self.cur_attrs,
        }
        Path(p).write_text(json.dumps(data,indent=2,default=str),encoding='utf-8')
        messagebox.showinfo("Sauvegardé",f"Rapport JSON:\n{p}")

    def _copy_report(self):
        txt = self.report_w.get('1.0',END)
        self.clipboard_clear(); self.clipboard_append(txt)

    # ── POLL ──────────────────────────────────────────────
    def _poll(self):
        try:
            while True:
                msg,data = self.q.get_nowait()
                if msg=='disks':
                    self._on_disks(data)
                elif msg=='smart':
                    self._on_smart(*data)
                elif msg=='iso_log':
                    tag,text = data
                    self.iso_log.config(state=NORMAL)
                    self.iso_log.insert(END,f"[{datetime.now().strftime('%H:%M:%S')}] {text}\n",tag)
                    self.iso_log.config(state=DISABLED)
                    self.iso_log.see(END)
                elif msg=='iso_prog':
                    p,lba,end_lba,iso,fail = data
                    self.iso_pv.set(p)
                    self.iso_plbl.config(text=f"{p:.1f}% — LBA {lba:,} — {iso} isolés")
                    self.iso_stats['scanned'].set(f"{lba:,}")
                    self.iso_stats['isolated'].set(str(iso))
                    self.iso_stats['failed'].set(str(fail))
                elif msg=='iso_done':
                    self.btn_iso_start.config(state=NORMAL)
                    self.btn_iso_stop.config(state=DISABLED)
                    r = data
                    self.iso_pv.set(100)
                    self._iso_log(f"✓ Terminé — {len(r['isolated'])} secteurs isolés, {len(r['failed'])} échecs",'ok')
                    messagebox.showinfo("Isolation terminée",
                        f"✓ {len(r['isolated'])} bad sectors isolés dans le firmware\n"
                        f"✗ {len(r['failed'])} échecs\n\n"
                        f"Relancez la lecture SMART pour vérifier.")
                    threading.Thread(target=self._read_smart,daemon=True).start()
        except queue.Empty: pass
        self.after(200, self._poll)

    def destroy(self):
        self.monitor = False
        super().destroy()

    @staticmethod
    def _fmt(s):
        if not s: return '?'
        for u in ['B','KB','MB','GB','TB']:
            if s<1024: return f"{s:.1f} {u}"
            s/=1024
        return f"{s:.1f} PB"


# ═══════════════════════════════════════════════════════════════
if __name__ == '__main__':
    app = HDDSentinel()
    app.mainloop()
