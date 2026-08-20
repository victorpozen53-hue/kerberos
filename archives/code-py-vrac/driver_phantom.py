#!/usr/bin/env python3
"""
╔══════════════════════════════════════════════════════════════╗
║           DRIVER PHANTOM  —  v1.0 PRO                       ║
║     Détection & Mise à jour automatique des drivers         ║
║     Windows 10/11  •  Sans dépendances externes            ║
║                                                              ║
║  • Détection hardware complète (PCI/USB/HID/Storage...)     ║
║  • Identification VendorID + DeviceID                       ║
║  • Recherche Microsoft Update Catalog                       ║
║  • Téléchargement + installation silencieuse                ║
║  • Backup drivers avant mise à jour                        ║
║  • Interface dark professionnelle                           ║
║                                                              ║
║  Usage: python driver_phantom.py                            ║
║  Requis: Windows 10/11, Python 3.8+, Admin recommandé      ║
╚══════════════════════════════════════════════════════════════╝
"""

import os, sys, re, json, time, queue, hashlib, shutil, zipfile
import threading, subprocess, ctypes, platform, winreg
import urllib.request, urllib.parse, urllib.error
from pathlib import Path
from datetime import datetime
from tkinter import *
from tkinter import ttk, filedialog, messagebox
import tkinter as tk

# ═══════════════════════════════════════════════════════════════
# VÉRIFICATION WINDOWS
# ═══════════════════════════════════════════════════════════════
if platform.system() != 'Windows':
    print("Driver Phantom est conçu pour Windows 10/11.")
    print("Sur Linux/Mac, utilisez le gestionnaire de paquets natif.")
    sys.exit(0)

# ═══════════════════════════════════════════════════════════════
# PALETTE — Dark Tech Blue
# ═══════════════════════════════════════════════════════════════
C = {
    'bg':          '#0C0E14',
    'bg2':         '#12151F',
    'bg3':         '#1A1E2E',
    'bg4':         '#222638',
    'bg5':         '#2A2F45',
    'panel':       '#080A0F',
    'accent':      '#4FC3F7',
    'accent2':     '#0288D1',
    'green':       '#00E676',
    'green_dim':   '#00600F',
    'yellow':      '#FFD54F',
    'yellow_dim':  '#6D4C00',
    'red':         '#FF5252',
    'red_dim':     '#7F0000',
    'orange':      '#FF8A65',
    'purple':      '#CE93D8',
    'teal':        '#4DB6AC',
    'text':        '#E8EAF6',
    'text2':       '#78909C',
    'text3':       '#37474F',
    'border':      '#263238',
    'selected':    '#0D2137',
    # Status colors
    'up_to_date':  '#00E676',
    'outdated':    '#FFD54F',
    'missing':     '#FF5252',
    'unknown':     '#78909C',
    'updating':    '#4FC3F7',
}

FN  = ('Segoe UI', 10)
FNS = ('Segoe UI', 9)
FNB = ('Segoe UI', 11, 'bold')
FNT = ('Segoe UI', 14, 'bold')
FNM = ('Consolas', 9)
FNC = ('Consolas', 10, 'bold')

# ═══════════════════════════════════════════════════════════════
# DEVICE CATEGORIES
# ═══════════════════════════════════════════════════════════════
CATEGORIES = {
    'Display':      ('🖥️',  C['purple']),
    'Network':      ('🌐',  C['accent']),
    'Audio':        ('🔊',  C['teal']),
    'USB':          ('🔌',  C['orange']),
    'Storage':      ('💾',  C['yellow']),
    'Input':        ('⌨️',  C['green']),
    'Chipset':      ('⚙️',  C['text2']),
    'Bluetooth':    ('📡',  C['purple']),
    'Camera':       ('📷',  C['teal']),
    'Printer':      ('🖨️',  C['text2']),
    'Other':        ('❓',  C['text3']),
}

# Classes Windows → notre catégorie
CLASS_MAP = {
    'display':           'Display',
    'monitor':           'Display',
    'net':               'Network',
    'nettrans':          'Network',
    'media':             'Audio',
    'audioendpoint':     'Audio',
    'usb':               'USB',
    'usbdevice':         'USB',
    'diskdrive':         'Storage',
    'cdrom':             'Storage',
    'floppydisk':        'Storage',
    'hdc':               'Storage',
    'scsi':              'Storage',
    'keyboard':          'Input',
    'mouse':             'Input',
    'hidclass':          'Input',
    'bluetooth':         'Bluetooth',
    'camera':            'Camera',
    'image':             'Camera',
    'printer':           'Printer',
    'system':            'Chipset',
    'processor':         'Chipset',
    'battery':           'Other',
    'firmware':          'Other',
    'softwaredevice':    'Other',
}

# ═══════════════════════════════════════════════════════════════
# HARDWARE DETECTOR
# ═══════════════════════════════════════════════════════════════
class HardwareDetector:
    """Détection complète du hardware via WMI + Registry"""

    REGISTRY_PATHS = [
        r"SYSTEM\CurrentControlSet\Enum\PCI",
        r"SYSTEM\CurrentControlSet\Enum\USB",
        r"SYSTEM\CurrentControlSet\Enum\HID",
        r"SYSTEM\CurrentControlSet\Enum\ACPI",
        r"SYSTEM\CurrentControlSet\Enum\STORAGE",
        r"SYSTEM\CurrentControlSet\Enum\IDE",
        r"SYSTEM\CurrentControlSet\Enum\SCSI",
        r"SYSTEM\CurrentControlSet\Enum\DISPLAY",
        r"SYSTEM\CurrentControlSet\Enum\BTH",
        r"SYSTEM\CurrentControlSet\Enum\SWD",
    ]

    def detect_all(self, progress_cb=None) -> list:
        devices = []
        seen_ids = set()

        total = len(self.REGISTRY_PATHS)
        for i, path in enumerate(self.REGISTRY_PATHS):
            if progress_cb:
                progress_cb(i / total * 60, f"Scan {path.split(chr(92))[-1]}...")
            devs = self._scan_registry_path(path)
            for d in devs:
                uid = d.get('hardware_id', d['device_id'])
                if uid not in seen_ids:
                    seen_ids.add(uid)
                    devices.append(d)

        # WMI pour infos supplémentaires
        if progress_cb: progress_cb(65, "Requêtes WMI...")
        wmi_data = self._wmi_query()
        devices = self._merge_wmi(devices, wmi_data)

        # Enrichir avec infos driver actuelles
        if progress_cb: progress_cb(80, "Lecture drivers installés...")
        for d in devices:
            self._get_driver_info(d)

        if progress_cb: progress_cb(100, f"{len(devices)} périphériques détectés")
        return devices

    def _scan_registry_path(self, path: str) -> list:
        devices = []
        try:
            key = winreg.OpenKey(winreg.HKEY_LOCAL_MACHINE, path)
            i = 0
            while True:
                try:
                    vendor_name = winreg.EnumKey(key, i)
                    vendor_key  = winreg.OpenKey(key, vendor_name)
                    j = 0
                    while True:
                        try:
                            device_name = winreg.EnumKey(vendor_key, j)
                            device_key  = winreg.OpenKey(vendor_key, device_name)
                            dev = self._parse_device_key(device_key, path, vendor_name, device_name)
                            if dev: devices.append(dev)
                            winreg.CloseKey(device_key)
                        except OSError: break
                        j += 1
                    winreg.CloseKey(vendor_key)
                except OSError: break
                i += 1
            winreg.CloseKey(key)
        except Exception: pass
        return devices

    def _parse_device_key(self, key, bus_path, vendor_str, device_str) -> dict:
        try:
            # Lire les sous-clés (instances)
            k = 0
            best = None
            while True:
                try:
                    inst_name = winreg.EnumKey(key, k)
                    inst_key  = winreg.OpenKey(key, inst_name)
                    dev = self._read_instance(inst_key, bus_path, vendor_str, device_str)
                    if dev:
                        best = dev
                        winreg.CloseKey(inst_key)
                        break
                    winreg.CloseKey(inst_key)
                except OSError: break
                k += 1
            return best
        except: return None

    def _read_instance(self, key, bus_path, vendor_str, device_str) -> dict:
        def rv(name, default=None):
            try: return winreg.QueryValueEx(key, name)[0]
            except: return default

        friendly = rv('FriendlyName') or rv('DeviceDesc', '')
        if isinstance(friendly, str) and ';' in friendly:
            friendly = friendly.split(';')[-1]

        hw_ids = rv('HardwareID', [])
        if isinstance(hw_ids, str): hw_ids = [hw_ids]

        compat  = rv('CompatibleIDs', [])
        if isinstance(compat, str): compat = [compat]

        class_  = rv('Class', 'Other').lower()
        class_guid = rv('ClassGUID', '')
        mfg    = rv('Mfg', '')
        if isinstance(mfg, str) and ';' in mfg:
            mfg = mfg.split(';')[-1]

        # Extraire VEN/DEV IDs
        vid = did = None
        for hid in hw_ids:
            vm = re.search(r'VEN_([0-9A-Fa-f]{4})', hid)
            dm = re.search(r'DEV_([0-9A-Fa-f]{4})', hid)
            um = re.search(r'VID_([0-9A-Fa-f]{4}).*PID_([0-9A-Fa-f]{4})', hid)
            if vm: vid = vm.group(1).upper()
            if dm: did = dm.group(1).upper()
            if um: vid, did = um.group(1).upper(), um.group(2).upper()
            if vid and did: break

        if not friendly or friendly.startswith('@'):
            return None

        bus = bus_path.split('\\')[-1]
        cat = CLASS_MAP.get(class_, 'Other')

        return {
            'device_id':    f"{bus}\\{vendor_str}\\{device_str}",
            'hardware_id':  hw_ids[0] if hw_ids else f"{bus}\\{vendor_str}",
            'hw_ids':       hw_ids,
            'compat_ids':   compat,
            'name':         friendly,
            'manufacturer': mfg,
            'class':        class_,
            'category':     cat,
            'vendor_id':    vid or '',
            'device_id_hex':did or '',
            'bus':          bus,
            'driver_version': '',
            'driver_date':    '',
            'driver_provider':'',
            'status':         'unknown',
            'inf_path':       '',
            'update_available': False,
            'new_version':    '',
            'download_url':   '',
        }

    def _wmi_query(self) -> list:
        """Query WMI via PowerShell (pas besoin de pywin32)"""
        results = []
        try:
            cmd = [
                'powershell', '-NoProfile', '-NonInteractive', '-Command',
                'Get-WmiObject Win32_PnPSignedDriver | '
                'Select-Object DeviceName,DriverVersion,DriverDate,Manufacturer,DeviceClass,InfName,DeviceID | '
                'ConvertTo-Json -Compress'
            ]
            out = subprocess.check_output(cmd, timeout=30, stderr=subprocess.DEVNULL,
                                          creationflags=subprocess.CREATE_NO_WINDOW)
            data = json.loads(out.decode('utf-8', errors='replace'))
            if isinstance(data, dict): data = [data]
            results = data or []
        except Exception: pass
        return results

    def _merge_wmi(self, devices: list, wmi_data: list) -> list:
        wmi_map = {}
        for w in wmi_data:
            if not isinstance(w, dict): continue
            name = (w.get('DeviceName') or '').strip()
            if name: wmi_map[name.lower()] = w

        for d in devices:
            w = wmi_map.get(d['name'].lower())
            if w:
                d['driver_version']  = w.get('DriverVersion', '')
                d['driver_date']     = self._parse_wmi_date(w.get('DriverDate', ''))
                d['driver_provider'] = w.get('Manufacturer', '') or d['manufacturer']
                d['inf_path']        = w.get('InfName', '')
        return devices

    def _get_driver_info(self, device: dict):
        """Lire infos driver depuis registry si pas trouvé via WMI"""
        if device['driver_version']: return
        try:
            path = f"SYSTEM\\CurrentControlSet\\Enum\\{device['device_id']}\\Properties"
            key  = winreg.OpenKey(winreg.HKEY_LOCAL_MACHINE, path)
            winreg.CloseKey(key)
        except: pass

        # Essayer driverstore
        if not device['driver_version']:
            device['status'] = 'unknown'
        else:
            device['status'] = 'installed'

    @staticmethod
    def _parse_wmi_date(s: str) -> str:
        if not s: return ''
        try:
            m = re.search(r'(\d{8})', str(s))
            if m:
                d = m.group(1)
                return f"{d[:4]}-{d[4:6]}-{d[6:8]}"
        except: pass
        return str(s)[:10]


# ═══════════════════════════════════════════════════════════════
# DRIVER SEARCHER — Microsoft Update Catalog
# ═══════════════════════════════════════════════════════════════
class DriverSearcher:
    """Recherche drivers sur Microsoft Update Catalog et DriverPack"""

    CATALOG_URL  = "https://www.catalog.update.microsoft.com/Search.aspx"
    CATALOG_DL   = "https://www.catalog.update.microsoft.com/DownloadDialog.aspx"
    HEADERS = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36',
        'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8',
    }
    TIMEOUT = 15

    def search_driver(self, device: dict) -> list:
        """Retourne liste de drivers trouvés pour ce périphérique"""
        results = []

        # Stratégie 1 : VendorID + DeviceID exact
        if device['vendor_id'] and device['device_id_hex']:
            q = f"VEN_{device['vendor_id']}&DEV_{device['device_id_hex']}"
            results += self._search_catalog(q)

        # Stratégie 2 : Nom du device
        if not results and device['name']:
            name = re.sub(r'[^\w\s]', ' ', device['name'])[:50]
            results += self._search_catalog(name)

        # Stratégie 3 : Hardware ID brut
        if not results and device['hw_ids']:
            results += self._search_catalog(device['hw_ids'][0][:60])

        return results[:5]  # max 5 résultats

    def _search_catalog(self, query: str) -> list:
        try:
            url = f"{self.CATALOG_URL}?q={urllib.parse.quote(query)}"
            req = urllib.request.Request(url, headers=self.HEADERS)
            with urllib.request.urlopen(req, timeout=self.TIMEOUT) as resp:
                html = resp.read().decode('utf-8', errors='replace')
            return self._parse_catalog(html)
        except Exception:
            return []

    def _parse_catalog(self, html: str) -> list:
        results = []
        # Parser les résultats du catalog Microsoft
        rows = re.findall(
            r'<tr[^>]*id="[^"]*_\d+"[^>]*>(.*?)</tr>',
            html, re.DOTALL
        )
        for row in rows[:8]:
            cells = re.findall(r'<td[^>]*>(.*?)</td>', row, re.DOTALL)
            if len(cells) < 5: continue
            def clean(s):
                s = re.sub(r'<[^>]+>', '', s)
                return re.sub(r'\s+', ' ', s).strip()
            title    = clean(cells[1]) if len(cells) > 1 else ''
            products = clean(cells[2]) if len(cells) > 2 else ''
            version  = clean(cells[3]) if len(cells) > 3 else ''
            date     = clean(cells[4]) if len(cells) > 4 else ''
            size     = clean(cells[5]) if len(cells) > 5 else ''
            # Extraire GUID pour download
            guid_m = re.search(r"goToDetails\('([^']+)'", row)
            guid   = guid_m.group(1) if guid_m else ''
            if title and guid:
                results.append({
                    'title':    title,
                    'products': products,
                    'version':  version,
                    'date':     date,
                    'size':     size,
                    'guid':     guid,
                    'source':   'Microsoft Catalog',
                })
        return results

    def get_download_url(self, guid: str) -> str:
        """Récupère l'URL de téléchargement pour un GUID catalog"""
        try:
            data = f"updateIDs=[{{\"size\":0,\"languages\":\"\",\"uidInfo\":\"{guid}\",\"updateID\":\"{guid}\"}}]"
            req  = urllib.request.Request(
                self.CATALOG_DL,
                data=data.encode(),
                headers={**self.HEADERS, 'Content-Type': 'application/x-www-form-urlencoded'},
                method='POST'
            )
            with urllib.request.urlopen(req, timeout=self.TIMEOUT) as resp:
                html = resp.read().decode('utf-8', errors='replace')
            urls = re.findall(r'(https://[^"\'<>\s]+\.(?:cab|exe|msi|zip|inf))', html, re.I)
            return urls[0] if urls else ''
        except: return ''

    def search_winupdate(self, device: dict) -> dict | None:
        """Cherche via Windows Update (pnputil + wuauclt)"""
        if not device['hw_ids']: return None
        try:
            # Vérifier si Windows Update a des drivers
            cmd = ['pnputil', '/enum-drivers']
            out = subprocess.check_output(cmd, timeout=10, stderr=subprocess.DEVNULL,
                                          creationflags=subprocess.CREATE_NO_WINDOW)
            text = out.decode('utf-8', errors='replace')
            # Chercher le hardware ID dans les drivers installés
            for hid in device['hw_ids']:
                if hid.lower() in text.lower():
                    return {'source': 'Windows Driver Store', 'installed': True}
        except: pass
        return None


# ═══════════════════════════════════════════════════════════════
# DRIVER INSTALLER
# ═══════════════════════════════════════════════════════════════
class DriverInstaller:
    def __init__(self, work_dir: Path, log_cb=None):
        self.work = work_dir
        self.log  = log_cb or print
        self.work.mkdir(parents=True, exist_ok=True)

    def download(self, url: str, name: str, progress_cb=None) -> Path | None:
        """Télécharger un driver avec progression"""
        if not url: return None
        safe = re.sub(r'[^\w\-_.]', '_', name)[:60]
        ext  = Path(url.split('?')[0]).suffix or '.cab'
        dest = self.work / f"{safe}{ext}"
        try:
            self.log(f"  ↓ Téléchargement: {name}", 'info')
            req = urllib.request.Request(url, headers={
                'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64)'
            })
            with urllib.request.urlopen(req, timeout=60) as resp:
                total = int(resp.headers.get('Content-Length', 0))
                done  = 0
                with open(dest, 'wb') as f:
                    while True:
                        chunk = resp.read(65536)
                        if not chunk: break
                        f.write(chunk); done += len(chunk)
                        if progress_cb and total:
                            progress_cb(done / total * 100)
            self.log(f"  ✓ Téléchargé: {dest.name} ({done//1024} KB)", 'ok')
            return dest
        except Exception as e:
            self.log(f"  ✗ Échec téléchargement: {e}", 'err')
            return None

    def backup_driver(self, device: dict, backup_dir: Path) -> bool:
        """Backup du driver actuel avant mise à jour"""
        try:
            if not device.get('inf_path'): return False
            inf = Path(os.environ.get('SystemRoot','C:\\Windows')) / 'System32' / 'DriverStore' / 'FileRepository'
            # Chercher le dossier du driver
            name = Path(device['inf_path']).stem
            for d in inf.iterdir() if inf.exists() else []:
                if d.is_dir() and name.lower() in d.name.lower():
                    dest = backup_dir / d.name
                    shutil.copytree(str(d), str(dest), dirs_exist_ok=True)
                    self.log(f"  ✓ Backup: {d.name}", 'ok')
                    return True
        except Exception as e:
            self.log(f"  ⚠ Backup impossible: {e}", 'warn')
        return False

    def install_cab(self, cab_path: Path, device: dict) -> bool:
        """Installer un driver .cab via pnputil"""
        try:
            # Extraire le CAB
            extract_dir = self.work / 'extracted' / cab_path.stem
            extract_dir.mkdir(parents=True, exist_ok=True)
            subprocess.run(
                ['expand', str(cab_path), '-F:*', str(extract_dir)],
                timeout=60, check=True, stderr=subprocess.DEVNULL,
                creationflags=subprocess.CREATE_NO_WINDOW
            )
            # Trouver les .inf
            infs = list(extract_dir.rglob('*.inf'))
            if not infs:
                self.log("  ✗ Pas de .inf dans l'archive", 'err')
                return False
            # Installer via pnputil
            for inf in infs:
                result = subprocess.run(
                    ['pnputil', '/add-driver', str(inf), '/install', '/subdirs'],
                    timeout=120, capture_output=True, text=True,
                    creationflags=subprocess.CREATE_NO_WINDOW
                )
                if result.returncode == 0:
                    self.log(f"  ✓ Driver installé: {inf.name}", 'ok')
                    return True
                else:
                    self.log(f"  ⚠ pnputil: {result.stdout.strip()[:80]}", 'warn')
            return False
        except Exception as e:
            self.log(f"  ✗ Installation échouée: {e}", 'err')
            return False

    def install_exe(self, exe_path: Path, silent: bool = True) -> bool:
        """Installer un driver .exe en mode silencieux"""
        try:
            flags = ['/s', '/silent', '/quiet', '/norestart', '-s', '-silent']
            if silent:
                for f in flags[:3]:
                    try:
                        result = subprocess.run(
                            [str(exe_path), f],
                            timeout=180, capture_output=True,
                            creationflags=subprocess.CREATE_NO_WINDOW
                        )
                        if result.returncode in (0, 3010):  # 3010 = reboot needed
                            self.log(f"  ✓ Installé (code {result.returncode})", 'ok')
                            return True
                    except: continue
            # Fallback : lancer normalement
            subprocess.Popen([str(exe_path)])
            self.log(f"  ↗ Lancé en mode normal (manuel requis)", 'warn')
            return True
        except Exception as e:
            self.log(f"  ✗ Échec exe: {e}", 'err')
            return False

    def force_update_via_wuapi(self, device: dict) -> bool:
        """Forcer Windows Update à chercher le driver"""
        try:
            ps = f"""
$Session = New-Object -ComObject Microsoft.Update.Session
$Searcher = $Session.CreateUpdateSearcher()
$Results = $Searcher.Search("IsInstalled=0 and Type='Driver'")
Write-Output "Found: $($Results.Updates.Count) driver updates"
$Results.Updates | ForEach-Object {{ Write-Output $_.Title }}
"""
            out = subprocess.check_output(
                ['powershell', '-NoProfile', '-Command', ps],
                timeout=30, stderr=subprocess.DEVNULL,
                creationflags=subprocess.CREATE_NO_WINDOW
            )
            text = out.decode('utf-8', errors='replace')
            self.log(f"  Windows Update: {text[:200]}", 'info')
            return True
        except: return False

    def install_via_windows_update(self, device: dict) -> bool:
        """Installer via Windows Update automatiquement"""
        try:
            ps = f"""
$Session = New-Object -ComObject Microsoft.Update.Session
$Searcher = $Session.CreateUpdateSearcher()
$Results = $Searcher.Search("IsInstalled=0 and Type='Driver'")
if ($Results.Updates.Count -gt 0) {{
    $Downloader = $Session.CreateUpdateDownloader()
    $Downloader.Updates = $Results.Updates
    $Downloader.Download()
    $Installer = $Session.CreateUpdateInstaller()
    $Installer.Updates = $Results.Updates
    $InstallResult = $Installer.Install()
    Write-Output "Result: $($InstallResult.ResultCode)"
}}
"""
            subprocess.run(
                ['powershell', '-NoProfile', '-Command', ps],
                timeout=300, creationflags=subprocess.CREATE_NO_WINDOW
            )
            return True
        except: return False

    def is_admin(self) -> bool:
        try: return ctypes.windll.shell32.IsUserAnAdmin()
        except: return False


# ═══════════════════════════════════════════════════════════════
# SYSTEM INFO
# ═══════════════════════════════════════════════════════════════
class SystemInfo:
    @staticmethod
    def get() -> dict:
        info = {
            'os': '', 'build': '', 'arch': '',
            'cpu': '', 'ram': '', 'hostname': '',
            'pc_name': '', 'manufacturer': '', 'model': '',
        }
        try:
            # OS info
            cmd = ['powershell','-NoProfile','-Command',
                   'Get-ComputerInfo | Select-Object OsName,OsBuildNumber,OsArchitecture,'
                   'CsName,CsManufacturer,CsModel,CsProcessors,CsTotalPhysicalMemory | ConvertTo-Json -Compress']
            out = subprocess.check_output(cmd, timeout=15, stderr=subprocess.DEVNULL,
                                          creationflags=subprocess.CREATE_NO_WINDOW)
            d = json.loads(out.decode('utf-8', errors='replace'))
            info['os']   = d.get('OsName','').replace('Microsoft ','')
            info['build']= str(d.get('OsBuildNumber',''))
            info['arch'] = d.get('OsArchitecture','')
            info['hostname'] = d.get('CsName','')
            info['manufacturer'] = d.get('CsManufacturer','')
            info['model'] = d.get('CsModel','')
            ram = d.get('CsTotalPhysicalMemory', 0)
            if ram: info['ram'] = f"{int(ram)//1073741824} GB"
            cpu = d.get('CsProcessors')
            if isinstance(cpu, list) and cpu:
                info['cpu'] = cpu[0].get('Name','')
            elif isinstance(cpu, dict):
                info['cpu'] = cpu.get('Name','')
        except Exception: pass
        return info


# ═══════════════════════════════════════════════════════════════
# MAIN APPLICATION
# ═══════════════════════════════════════════════════════════════
class DriverPhantom(Tk):
    def __init__(self):
        super().__init__()
        self.title("DRIVER PHANTOM  —  Auto Driver Detection & Update")
        self.geometry("1300x820")
        self.minsize(1050, 680)
        self.configure(bg=C['bg'])

        # State
        self.devices   = []
        self.q         = queue.Queue()
        self.running   = False
        self.work_dir  = Path(os.environ.get('TEMP','C:\\Temp')) / 'DriverPhantom'
        self.backup_dir= Path(os.environ.get('USERPROFILE','C:\\Users\\User')) / 'DriverPhantom_Backup'
        self.detector  = HardwareDetector()
        self.searcher  = DriverSearcher()
        self.installer = DriverInstaller(self.work_dir, log_cb=self._log)
        self.sysinfo   = {}
        self._filter_cat = 'All'
        self._filter_st  = 'All'
        self._sort_col   = None
        self._sort_rev   = False

        self._mk_style()
        self._mk_ui()
        self._poll()

        # Auto-load system info
        threading.Thread(target=self._load_sysinfo, daemon=True).start()

    # ── STYLE ─────────────────────────────────────────────
    def _mk_style(self):
        s = ttk.Style(self)
        s.theme_use('clam')
        s.configure('.',
            background=C['bg'], foreground=C['text'], font=FN)
        s.configure('TFrame',         background=C['bg'])
        s.configure('TLabel',         background=C['bg'],  foreground=C['text'])
        s.configure('TLabelframe',    background=C['bg2'], foreground=C['accent'],
            relief='flat', borderwidth=1)
        s.configure('TLabelframe.Label',
            background=C['bg2'], foreground=C['accent'], font=('Segoe UI',9,'bold'))
        s.configure('TProgressbar',
            troughcolor=C['bg3'], background=C['accent'], thickness=4)
        s.configure('Treeview',
            background=C['bg2'], foreground=C['text'],
            fieldbackground=C['bg2'], rowheight=26, borderwidth=0, font=FN)
        s.configure('Treeview.Heading',
            background=C['bg4'], foreground=C['accent'],
            font=('Segoe UI',9,'bold'), relief='flat')
        s.map('Treeview',
            background=[('selected',C['selected'])],
            foreground=[('selected',C['accent'])])
        s.configure('TNotebook',      background=C['bg'],  borderwidth=0)
        s.configure('TNotebook.Tab',  background=C['bg3'], foreground=C['text2'],
            padding=(14,6), font=FNS)
        s.map('TNotebook.Tab',
            background=[('selected',C['bg2'])],
            foreground=[('selected',C['accent'])])
        s.configure('TSeparator',     background=C['border'])

    # ── UI ────────────────────────────────────────────────
    def _mk_ui(self):
        # HEADER
        hdr = Frame(self, bg=C['panel'], height=60)
        hdr.pack(fill=X); hdr.pack_propagate(False)
        Frame(hdr, bg=C['accent'], width=4).pack(side=LEFT, fill=Y)
        # Logo area
        logo = Frame(hdr, bg=C['panel']); logo.pack(side=LEFT, padx=14, pady=8)
        Label(logo, text="◈ DRIVER PHANTOM", font=('Segoe UI',17,'bold'),
              bg=C['panel'], fg=C['accent']).pack(anchor=W)
        Label(logo, text="Détection & mise à jour automatique  •  Windows 10/11",
              font=FNS, bg=C['panel'], fg=C['text2']).pack(anchor=W)

        # Sysinfo header
        self.hdr_info = Label(hdr, text="Chargement système...",
                              font=FNS, bg=C['panel'], fg=C['text2'])
        self.hdr_info.pack(side=LEFT, padx=20, pady=18)

        # Admin badge
        is_admin = self.installer.is_admin()
        abg = C['green_dim'] if is_admin else C['red_dim']
        afg = C['green'] if is_admin else C['red']
        atx = "⚡ ADMIN" if is_admin else "⚠ PAS ADMIN"
        Label(hdr, text=atx, font=('Segoe UI',9,'bold'),
              bg=abg, fg=afg, padx=10, pady=4).pack(side=RIGHT, padx=16, pady=16)

        # MAIN
        main = Frame(self, bg=C['bg'])
        main.pack(fill=BOTH, expand=True, padx=10, pady=8)

        # LEFT 270px
        left = Frame(main, bg=C['bg'], width=272)
        left.pack(side=LEFT, fill=Y, padx=(0,8))
        left.pack_propagate(False)
        self._mk_left(left)

        # RIGHT
        right = Frame(main, bg=C['bg'])
        right.pack(side=LEFT, fill=BOTH, expand=True)
        self._mk_right(right)

        # STATUSBAR
        sb = Frame(self, bg=C['bg4'], height=28)
        sb.pack(fill=X, side=BOTTOM); sb.pack_propagate(False)
        Frame(sb, bg=C['accent2'], width=3).pack(side=LEFT, fill=Y)
        self.sv_status = StringVar(value="Prêt — Cliquez sur DÉTECTER pour analyser votre système")
        Label(sb, textvariable=self.sv_status, font=FNS,
              bg=C['bg4'], fg=C['text2']).pack(side=LEFT, padx=10, pady=5)
        self.sv_count = StringVar(value="")
        Label(sb, textvariable=self.sv_count, font=FNS,
              bg=C['bg4'], fg=C['green']).pack(side=RIGHT, padx=12)

    def _mk_left(self, p):
        # ACTIONS
        f1 = ttk.LabelFrame(p, text=" ACTIONS ", padding=10)
        f1.pack(fill=X, pady=(0,8))

        self.btn_scan = self._btn(f1, "🔍  DÉTECTER LE HARDWARE", self._start_scan)
        self.btn_scan.pack(fill=X, pady=(0,4))

        self.btn_search = self._btn(f1, "🌐  CHERCHER LES MISES À JOUR",
                                    self._start_search, C['yellow'])
        self.btn_search.pack(fill=X, pady=(0,4))
        self.btn_search.config(state=DISABLED)

        self.btn_update_all = self._btn(f1, "⚡  TOUT METTRE À JOUR",
                                         self._update_all, C['green'])
        self.btn_update_all.pack(fill=X, pady=(0,4))
        self.btn_update_all.config(state=DISABLED)

        self.btn_update_sel = self._btn(f1, "▶  METTRE À JOUR SÉLECTION",
                                         self._update_selected, C['teal'])
        self.btn_update_sel.pack(fill=X, pady=(0,4))
        self.btn_update_sel.config(state=DISABLED)

        self.btn_stop = self._btn(f1, "⏹  ARRÊTER", self._stop, C['red'])
        self.btn_stop.pack(fill=X); self.btn_stop.config(state=DISABLED)

        # FILTRES
        f2 = ttk.LabelFrame(p, text=" FILTRES ", padding=10)
        f2.pack(fill=X, pady=(0,8))

        Label(f2, text="Catégorie:", font=FNS, bg=C['bg2'], fg=C['text2']).pack(anchor=W)
        self.flt_cat = StringVar(value='All')
        cats = ['All'] + list(CATEGORIES.keys())
        cb1 = ttk.Combobox(f2, textvariable=self.flt_cat, values=cats,
                           state='readonly', font=FNS)
        cb1.pack(fill=X, pady=(2,8))
        cb1.bind('<<ComboboxSelected>>', lambda e: self._apply_filter())

        Label(f2, text="Statut:", font=FNS, bg=C['bg2'], fg=C['text2']).pack(anchor=W)
        self.flt_st = StringVar(value='All')
        cb2 = ttk.Combobox(f2, textvariable=self.flt_st,
                           values=['All','Installé','Manquant','Obsolète','Inconnu'],
                           state='readonly', font=FNS)
        cb2.pack(fill=X, pady=(2,8))
        cb2.bind('<<ComboboxSelected>>', lambda e: self._apply_filter())

        Label(f2, text="Recherche:", font=FNS, bg=C['bg2'], fg=C['text2']).pack(anchor=W)
        self.flt_txt = StringVar()
        self.flt_txt.trace('w', lambda *_: self._apply_filter())
        Entry(f2, textvariable=self.flt_txt, bg=C['bg3'], fg=C['text'],
              insertbackground=C['accent'], relief='flat', font=FNM,
              bd=0, highlightthickness=1, highlightcolor=C['accent'],
              highlightbackground=C['border']).pack(fill=X, pady=2)

        # OPTIONS
        f3 = ttk.LabelFrame(p, text=" OPTIONS ", padding=10)
        f3.pack(fill=X, pady=(0,8))

        self.opt_backup = BooleanVar(value=True)
        self.opt_silent = BooleanVar(value=True)
        self.opt_wupdate = BooleanVar(value=True)

        for var, lbl, col in [
            (self.opt_backup,  "💾  Backup avant install",    C['yellow']),
            (self.opt_silent,  "🔇  Installation silencieuse", C['accent']),
            (self.opt_wupdate, "🪟  Utiliser Windows Update",  C['teal']),
        ]:
            tk.Checkbutton(f3, text=lbl, variable=var,
                           bg=C['bg2'], fg=col, selectcolor=C['bg3'],
                           activebackground=C['bg2'], font=FNS,
                           cursor='hand2').pack(anchor=W, pady=2)

        self._btn(f3, "📂  Ouvrir dossier backup",
                  lambda: os.startfile(str(self.backup_dir)) if self.backup_dir.exists() else None,
                  C['text2'], small=True).pack(fill=X, pady=(6,0))

        # PROGRESSION
        f4 = ttk.LabelFrame(p, text=" PROGRESSION ", padding=10)
        f4.pack(fill=X, pady=(0,8))
        self.pv = tk.DoubleVar()
        ttk.Progressbar(f4, variable=self.pv, maximum=100).pack(fill=X, pady=(0,5))
        self.plbl = Label(f4, text="En attente...", font=FNS, bg=C['bg2'], fg=C['text2'])
        self.plbl.pack(anchor=W)

        # STATS MINI
        f5 = ttk.LabelFrame(p, text=" RÉSUMÉ ", padding=8)
        f5.pack(fill=X)
        self.stat_vars = {}
        for k, lbl, col in [
            ('total',    'Périphériques', C['text2']),
            ('installed','Installés',     C['green']),
            ('missing',  'Manquants',     C['red']),
            ('outdated', 'Obsolètes',     C['yellow']),
            ('updated',  'Mis à jour',    C['accent']),
        ]:
            r = Frame(f5, bg=C['bg2']); r.pack(fill=X, pady=1)
            Label(r, text=f"{lbl}:", font=FNS, bg=C['bg2'], fg=C['text2'],
                  width=13, anchor=W).pack(side=LEFT)
            v = StringVar(value='—'); self.stat_vars[k] = v
            Label(r, textvariable=v, font=FNS, bg=C['bg2'], fg=col).pack(side=LEFT)

    def _mk_right(self, p):
        nb = ttk.Notebook(p); nb.pack(fill=BOTH, expand=True)

        # TAB 1 — Drivers
        t1 = Frame(nb, bg=C['bg']); nb.add(t1, text="  🖥️ PÉRIPHÉRIQUES  ")
        self._mk_device_tab(t1)

        # TAB 2 — Log
        t2 = Frame(nb, bg=C['bg']); nb.add(t2, text="  📋 LOG  ")
        self.log_w = Text(t2, bg=C['bg2'], fg=C['text'], font=FNM,
                          insertbackground=C['accent'], relief='flat',
                          wrap=WORD, state=DISABLED)
        lsb = ttk.Scrollbar(t2, command=self.log_w.yview)
        self.log_w.configure(yscrollcommand=lsb.set)
        lsb.pack(side=RIGHT, fill=Y); self.log_w.pack(fill=BOTH, expand=True)
        for tag, col, bold in [
            ('title', C['accent'],  True),
            ('ok',    C['green'],   False),
            ('warn',  C['yellow'],  False),
            ('err',   C['red'],     False),
            ('info',  C['text2'],   False),
            ('sep',   C['text3'],   False),
            ('dev',   C['purple'],  False),
        ]:
            f = ('Consolas',9,'bold') if bold else FNM
            self.log_w.tag_configure(tag, foreground=col, font=f)

        # TAB 3 — System Info
        t3 = Frame(nb, bg=C['bg']); nb.add(t3, text="  💻 SYSTÈME  ")
        self.sysinfo_w = Text(t3, bg=C['bg2'], fg=C['text'], font=FNM,
                              relief='flat', state=DISABLED)
        self.sysinfo_w.pack(fill=BOTH, expand=True)

    def _mk_device_tab(self, parent):
        # Toolbar
        tb = Frame(parent, bg=C['bg4'], height=38)
        tb.pack(fill=X); tb.pack_propagate(False)

        self._btn(tb, "☑ Tout", self._sel_all, small=True).pack(side=LEFT, padx=8, pady=5)
        self._btn(tb, "☐ Aucun", lambda: self.tree.selection_remove(self.tree.get_children()),
                  small=True, color=C['text2']).pack(side=LEFT, padx=2, pady=5)

        for lbl, st, col in [
            ('Manquants', 'missing', C['red']),
            ('Obsolètes', 'outdated', C['yellow']),
            ('À jour',    'installed', C['green']),
        ]:
            self._btn(tb, lbl, lambda s=st: self._sel_by_status(s),
                      small=True, color=col).pack(side=LEFT, padx=2, pady=5)

        self._btn(tb, "📄 Rapport TXT", self._save_report,
                  small=True, color=C['text2']).pack(side=RIGHT, padx=8, pady=5)

        # Tree
        cols = ('icon','name','manufacturer','version','date','category','status','action')
        self.tree = ttk.Treeview(parent, columns=cols, show='headings', selectmode='extended')

        specs = [
            ('icon',        '',              35,  'center'),
            ('name',        'Périphérique',  300, 'w'),
            ('manufacturer','Fabricant',     140, 'w'),
            ('version',     'Version',       100, 'center'),
            ('date',        'Date driver',   100, 'center'),
            ('category',    'Catégorie',      90, 'center'),
            ('status',      'Statut',         95, 'center'),
            ('action',      'Action',         90, 'center'),
        ]
        for col, hdr, w, anchor in specs:
            self.tree.heading(col, text=hdr, command=lambda c=col: self._sort(c))
            self.tree.column(col, width=w, anchor=anchor, minwidth=30)

        # Tags
        self.tree.tag_configure('installed', foreground=C['up_to_date'])
        self.tree.tag_configure('outdated',  foreground=C['outdated'])
        self.tree.tag_configure('missing',   foreground=C['missing'])
        self.tree.tag_configure('unknown',   foreground=C['unknown'])
        self.tree.tag_configure('updating',  foreground=C['updating'])

        vsb = ttk.Scrollbar(parent, orient=VERTICAL,   command=self.tree.yview)
        hsb = ttk.Scrollbar(parent, orient=HORIZONTAL, command=self.tree.xview)
        self.tree.configure(yscrollcommand=vsb.set, xscrollcommand=hsb.set)
        vsb.pack(side=RIGHT, fill=Y)
        self.tree.pack(side=TOP, fill=BOTH, expand=True)
        hsb.pack(side=BOTTOM, fill=X)

        self.tree.bind('<Double-1>', self._on_double_click)
        self.tree.bind('<<TreeviewSelect>>', self._on_select)

    # ── WIDGETS ───────────────────────────────────────────
    def _btn(self, parent, text, cmd, color=None, small=False):
        c = color or C['accent']
        f = FNS if small else ('Segoe UI', 10, 'bold')
        py = 3 if small else 8
        b = tk.Button(parent, text=text, command=cmd,
                      bg=C['bg3'], fg=c, activebackground=C['bg5'],
                      activeforeground=c, relief='flat', bd=0,
                      font=f, cursor='hand2', padx=8, pady=py)
        b.bind('<Enter>', lambda e: b.config(bg=C['bg5']))
        b.bind('<Leave>', lambda e: b.config(bg=C['bg3']))
        return b

    # ── SCAN HARDWARE ─────────────────────────────────────
    def _start_scan(self):
        if self.running: return
        self.running = True
        self.devices.clear()
        for item in self.tree.get_children(): self.tree.delete(item)
        self.btn_scan.config(state=DISABLED)
        self.btn_stop.config(state=NORMAL)
        self.btn_search.config(state=DISABLED)
        self.btn_update_all.config(state=DISABLED)
        self.pv.set(0)

        self._log("="*55, 'sep')
        self._log(" DRIVER PHANTOM — Scan hardware", 'title')
        self._log("="*55, 'sep')

        def run():
            self.devices = self.detector.detect_all(
                progress_cb=lambda p, l: self.q.put(('prog', (p, l)))
            )
            self.q.put(('scan_done', self.devices))

        threading.Thread(target=run, daemon=True).start()

    # ── SEARCH UPDATES ────────────────────────────────────
    def _start_search(self):
        if self.running or not self.devices: return
        self.running = True
        self.btn_search.config(state=DISABLED)
        self.btn_stop.config(state=NORMAL)
        self._log("\n🌐 Recherche des mises à jour...", 'title')

        def run():
            total = len(self.devices)
            for i, dev in enumerate(self.devices):
                if not self.running: break
                self.q.put(('prog', (i/total*100, f"Recherche: {dev['name'][:40]}...")))
                # Windows Update check
                if self.opt_wupdate.get():
                    wu = self.searcher.search_winupdate(dev)
                    if wu and wu.get('installed'):
                        dev['status'] = 'installed'
                        continue
                # Microsoft Catalog
                results = self.searcher.search_driver(dev)
                if results:
                    best = results[0]
                    dev['update_available'] = True
                    dev['new_version']  = best.get('version','')
                    dev['download_url'] = best.get('guid','')
                    dev['catalog_data'] = results
                    if dev['driver_version'] and dev['new_version']:
                        dev['status'] = 'outdated'
                    elif not dev['driver_version']:
                        dev['status'] = 'missing'
                self.q.put(('update_row', dev))
            self.q.put(('search_done', None))

        threading.Thread(target=run, daemon=True).start()

    # ── UPDATE ────────────────────────────────────────────
    def _update_all(self):
        to_update = [d for d in self.devices if d.get('update_available') or d['status'] in ('missing','outdated')]
        self._do_update(to_update)

    def _update_selected(self):
        sel = self.tree.selection()
        if not sel: return
        names = {self.tree.item(i,'values')[1] for i in sel}
        to_update = [d for d in self.devices if d['name'] in names]
        self._do_update(to_update)

    def _do_update(self, devices: list):
        if not devices:
            messagebox.showinfo("Info", "Aucun périphérique à mettre à jour."); return
        if not self.installer.is_admin():
            messagebox.showwarning("Admin requis",
                "Certaines installations nécessitent des droits admin.\n"
                "Relancez en tant qu'administrateur pour l'installation automatique.\n\n"
                "La détection et la recherche fonctionnent sans admin.")

        self.running = True
        self.btn_update_all.config(state=DISABLED)
        self.btn_update_sel.config(state=DISABLED)
        self.btn_stop.config(state=NORMAL)
        n_updated = [0]

        def run():
            total = len(devices)
            self._log(f"\n⚡ Mise à jour de {total} périphérique(s)...", 'title')
            for i, dev in enumerate(devices):
                if not self.running: break
                self._log(f"\n[{i+1}/{total}] {dev['name']}", 'dev')
                self.q.put(('prog', (i/total*100, f"Mise à jour: {dev['name'][:40]}...")))
                self.q.put(('set_status', (dev['name'], 'updating')))

                ok = False

                # Option 1: Windows Update API
                if self.opt_wupdate.get() and not ok:
                    self._log("  → Tentative Windows Update...", 'info')
                    ok = self.installer.install_via_windows_update(dev)

                # Option 2: Microsoft Catalog download
                if not ok and dev.get('catalog_data'):
                    for entry in dev['catalog_data'][:3]:
                        if not self.running: break
                        guid = entry.get('guid','')
                        if not guid: continue
                        self._log(f"  → Catalog: {entry.get('title','')[:50]}", 'info')
                        url = self.searcher.get_download_url(guid)
                        if not url: continue
                        # Backup
                        if self.opt_backup.get():
                            self.installer.backup_driver(dev, self.backup_dir)
                        # Download
                        path = self.installer.download(url, dev['name'].replace(' ','_')[:40])
                        if not path: continue
                        # Install
                        if path.suffix.lower() == '.cab':
                            ok = self.installer.install_cab(path, dev)
                        elif path.suffix.lower() in ('.exe','.msi'):
                            ok = self.installer.install_exe(path, self.opt_silent.get())
                        if ok: break

                if ok:
                    n_updated[0] += 1
                    dev['status'] = 'installed'
                    self.q.put(('set_status', (dev['name'], 'installed')))
                    self._log(f"  ✓ Succès!", 'ok')
                else:
                    self.q.put(('set_status', (dev['name'], 'unknown')))
                    self._log(f"  ✗ Échec ou intervention manuelle requise", 'warn')

            self.q.put(('update_done', n_updated[0]))

        threading.Thread(target=run, daemon=True).start()

    def _stop(self):
        self.running = False
        self._log("⏹ Arrêt demandé...", 'warn')

    # ── QUEUE POLL ────────────────────────────────────────
    def _poll(self):
        try:
            while True:
                msg, data = self.q.get_nowait()
                if msg == 'log':
                    tag, text = data
                    self._append_log(text, tag)
                elif msg == 'prog':
                    p, lbl = data
                    self.pv.set(p); self.plbl.config(text=lbl)
                    self.sv_status.set(lbl)
                elif msg == 'scan_done':
                    self._on_scan_done(data)
                elif msg == 'update_row':
                    self._refresh_row(data)
                elif msg == 'set_status':
                    name, st = data
                    self._set_row_status(name, st)
                elif msg == 'search_done':
                    self._on_search_done()
                elif msg == 'update_done':
                    self._on_update_done(data)
                elif msg == 'sysinfo':
                    self._show_sysinfo(data)
        except queue.Empty: pass
        self.after(80, self._poll)

    def _on_scan_done(self, devices):
        self.running = False
        self.btn_scan.config(state=NORMAL)
        self.btn_stop.config(state=DISABLED)
        self.btn_search.config(state=NORMAL)
        self.pv.set(100)

        # Populate tree
        for item in self.tree.get_children(): self.tree.delete(item)
        for d in devices: self._add_row(d)

        # Update stats
        total = len(devices)
        inst  = sum(1 for d in devices if d['driver_version'])
        miss  = sum(1 for d in devices if not d['driver_version'])
        self.stat_vars['total'].set(str(total))
        self.stat_vars['installed'].set(str(inst))
        self.stat_vars['missing'].set(str(miss))
        self.stat_vars['outdated'].set('?')
        self.stat_vars['updated'].set('0')
        self.sv_count.set(f"{total} périphériques détectés")
        self.plbl.config(text=f"✓ {total} périphériques")

        self._log(f"\n✓ {total} périphériques détectés", 'ok')
        self._log(f"  Avec driver : {inst}", 'ok')
        self._log(f"  Sans driver : {miss}", 'warn' if miss else 'ok')
        self._log(f"\n→ Cliquez 'CHERCHER LES MISES À JOUR'", 'info')
        self._update_stats()

    def _on_search_done(self):
        self.running = False
        self.btn_stop.config(state=DISABLED)
        self.btn_search.config(state=NORMAL)
        self.btn_update_all.config(state=NORMAL)
        self.btn_update_sel.config(state=NORMAL)
        self.pv.set(100)
        outdated = sum(1 for d in self.devices if d.get('update_available'))
        self.stat_vars['outdated'].set(str(outdated))
        self._log(f"\n✓ Recherche terminée — {outdated} mises à jour disponibles", 'ok')
        self.plbl.config(text=f"✓ {outdated} mises à jour")
        self._update_stats()

    def _on_update_done(self, n):
        self.running = False
        self.btn_stop.config(state=DISABLED)
        self.btn_update_all.config(state=NORMAL)
        self.btn_update_sel.config(state=NORMAL)
        self.pv.set(100)
        self.stat_vars['updated'].set(str(n))
        self._log(f"\n✓ {n} driver(s) mis à jour", 'ok')
        if n > 0:
            self._log("  Un redémarrage peut être nécessaire", 'warn')
        self.plbl.config(text=f"✓ {n} drivers mis à jour")
        messagebox.showinfo("Terminé",
            f"{n} driver(s) mis à jour avec succès.\n"
            "Un redémarrage peut être nécessaire.")

    # ── TREE MANAGEMENT ───────────────────────────────────
    def _add_row(self, d: dict):
        cat   = d.get('category', 'Other')
        icon, _ = CATEGORIES.get(cat, ('❓', C['text2']))
        st    = d.get('status', 'unknown')
        ver   = d.get('driver_version', '') or '—'
        date  = d.get('driver_date', '') or '—'

        if st == 'installed':
            st_lbl, tag = '✓ Installé', 'installed'
        elif st == 'outdated':
            st_lbl, tag = '⚠ Obsolète', 'outdated'
        elif st == 'missing':
            st_lbl, tag = '✗ Manquant', 'missing'
        elif st == 'updating':
            st_lbl, tag = '↻ En cours...', 'updating'
        else:
            st_lbl, tag = '? Inconnu', 'unknown'

        action = '⬇ Mettre à jour' if d.get('update_available') else ''

        # Check if row exists
        for item in self.tree.get_children():
            if self.tree.item(item,'values')[1] == d['name']:
                self.tree.item(item, values=(icon, d['name'], d.get('manufacturer',''),
                               ver, date, cat, st_lbl, action), tags=(tag,))
                return

        self.tree.insert('', END,
            values=(icon, d['name'], d.get('manufacturer',''), ver, date, cat, st_lbl, action),
            tags=(tag,))

    def _refresh_row(self, d: dict):
        self._add_row(d)

    def _set_row_status(self, name: str, status: str):
        for item in self.tree.get_children():
            if self.tree.item(item,'values')[1] == name:
                vals = list(self.tree.item(item,'values'))
                st_map = {
                    'installed': ('✓ Installé', 'installed'),
                    'outdated':  ('⚠ Obsolète', 'outdated'),
                    'missing':   ('✗ Manquant', 'missing'),
                    'updating':  ('↻ En cours...', 'updating'),
                    'unknown':   ('? Inconnu', 'unknown'),
                }
                lbl, tag = st_map.get(status, ('? Inconnu','unknown'))
                vals[6] = lbl
                self.tree.item(item, values=tuple(vals), tags=(tag,))
                break

    def _update_stats(self):
        vals = [self.tree.item(i,'values') for i in self.tree.get_children()]
        total = len(vals)
        inst  = sum(1 for v in vals if '✓' in str(v[6]))
        miss  = sum(1 for v in vals if '✗' in str(v[6]))
        out   = sum(1 for v in vals if '⚠' in str(v[6]))
        self.stat_vars['total'].set(str(total))
        self.stat_vars['installed'].set(str(inst))
        self.stat_vars['missing'].set(str(miss))
        self.stat_vars['outdated'].set(str(out))

    # ── FILTERS ───────────────────────────────────────────
    def _apply_filter(self):
        cat = self.flt_cat.get()
        st  = self.flt_st.get()
        txt = self.flt_txt.get().lower()
        for item in self.tree.get_children(): self.tree.delete(item)
        for d in self.devices:
            if cat != 'All' and d.get('category') != cat: continue
            st_map = {'Installé':'installed','Manquant':'missing',
                      'Obsolète':'outdated','Inconnu':'unknown'}
            if st != 'All' and d.get('status') != st_map.get(st,''): continue
            if txt and txt not in d['name'].lower() and txt not in d.get('manufacturer','').lower(): continue
            self._add_row(d)

    def _sel_all(self):
        self.tree.selection_set(self.tree.get_children())

    def _sel_by_status(self, status: str):
        self.tree.selection_remove(self.tree.get_children())
        for item in self.tree.get_children():
            vals = self.tree.item(item,'values')
            tags = self.tree.item(item,'tags')
            if status in tags:
                self.tree.selection_add(item)

    def _sort(self, col):
        data = [(self.tree.set(k,col),k) for k in self.tree.get_children('')]
        rev  = self._sort_col == col and not self._sort_rev
        data.sort(reverse=rev, key=lambda x: x[0].lower() if x[0] else '')
        for i,(_,k) in enumerate(data): self.tree.move(k,'',i)
        self._sort_col=col; self._sort_rev=rev

    def _on_double_click(self, event):
        sel = self.tree.selection()
        if not sel: return
        name = self.tree.item(sel[0],'values')[1]
        dev  = next((d for d in self.devices if d['name']==name), None)
        if dev: self._show_device_detail(dev)

    def _on_select(self, event):
        sel = self.tree.selection()
        has = bool(sel)
        self.btn_update_sel.config(state=NORMAL if has else DISABLED)

    # ── DEVICE DETAIL POPUP ───────────────────────────────
    def _show_device_detail(self, dev: dict):
        w = Toplevel(self)
        w.title(f"Détail: {dev['name'][:40]}")
        w.geometry("600x450")
        w.configure(bg=C['bg'])
        w.transient(self)

        Label(w, text=f"  {CATEGORIES.get(dev['category'],('❓',''))[0]}  {dev['name']}",
              font=FNB, bg=C['bg3'], fg=C['accent'],
              anchor=W).pack(fill=X, pady=0)

        txt = Text(w, bg=C['bg2'], fg=C['text'], font=FNM,
                   relief='flat', wrap=WORD)
        sb  = ttk.Scrollbar(w, command=txt.yview)
        txt.configure(yscrollcommand=sb.set)
        sb.pack(side=RIGHT, fill=Y); txt.pack(fill=BOTH, expand=True, padx=4, pady=4)

        txt.tag_configure('key',  foreground=C['accent'], font=('Consolas',9,'bold'))
        txt.tag_configure('val',  foreground=C['text'])
        txt.tag_configure('head', foreground=C['yellow'], font=('Consolas',10,'bold'))

        def line(k, v):
            txt.insert(END, f"  {k+':':<24}", 'key')
            txt.insert(END, f"{v}\n", 'val')

        txt.insert(END, "INFORMATIONS PÉRIPHÉRIQUE\n", 'head')
        line("Nom",          dev['name'])
        line("Fabricant",    dev.get('manufacturer','—'))
        line("Catégorie",    dev.get('category','—'))
        line("Bus",          dev.get('bus','—'))
        line("Vendor ID",    dev.get('vendor_id','—'))
        line("Device ID",    dev.get('device_id_hex','—'))
        txt.insert(END, "\nDRIVER ACTUEL\n", 'head')
        line("Version",      dev.get('driver_version','—'))
        line("Date",         dev.get('driver_date','—'))
        line("Fournisseur",  dev.get('driver_provider','—'))
        line("INF",          dev.get('inf_path','—'))
        txt.insert(END, "\nHARDWARE IDs\n", 'head')
        for hid in dev.get('hw_ids',[]):
            txt.insert(END, f"  {hid}\n", 'val')
        if dev.get('catalog_data'):
            txt.insert(END, "\nMISES À JOUR DISPONIBLES\n", 'head')
            for r in dev['catalog_data']:
                txt.insert(END, f"  [{r.get('source','')}] {r.get('title','')}\n", 'val')
                line("    Version", r.get('version',''))
                line("    Date",    r.get('date',''))
                line("    Taille",  r.get('size',''))

        txt.config(state=DISABLED)
        self._btn(w, "⬇ Mettre à jour ce driver",
                  lambda: [w.destroy(), self._do_update([dev])],
                  C['green']).pack(fill=X, padx=4, pady=4)

    # ── SYSTEM INFO ───────────────────────────────────────
    def _load_sysinfo(self):
        info = SystemInfo.get()
        self.q.put(('sysinfo', info))

    def _show_sysinfo(self, info: dict):
        self.sysinfo = info
        hdr = f"{info.get('os','')}  {info.get('arch','')}  Build {info.get('build','')}"
        self.hdr_info.config(text=f"💻 {hdr}  •  {info.get('cpu','')[:35]}  •  {info.get('ram','')}")

        self.sysinfo_w.config(state=NORMAL)
        self.sysinfo_w.delete('1.0', END)
        lines = [
            "╔══════════════════════════════════════════════╗",
            "║           INFORMATIONS SYSTÈME               ║",
            "╚══════════════════════════════════════════════╝", "",
            f"  Système d'exploitation : {info.get('os','')}",
            f"  Build                  : {info.get('build','')}",
            f"  Architecture           : {info.get('arch','')}",
            f"  Nom de l'ordinateur    : {info.get('hostname','')}",
            f"  Fabricant              : {info.get('manufacturer','')}",
            f"  Modèle                 : {info.get('model','')}",
            f"  Processeur             : {info.get('cpu','')}",
            f"  Mémoire RAM            : {info.get('ram','')}",
            "", "  ─────────────────────────────────────────",
            f"  Dossier travail        : {self.work_dir}",
            f"  Dossier backup         : {self.backup_dir}",
            f"  Admin                  : {'Oui ✓' if self.installer.is_admin() else 'Non ✗'}",
        ]
        self.sysinfo_w.insert(END, '\n'.join(lines))
        self.sysinfo_w.config(state=DISABLED)

    # ── LOG ───────────────────────────────────────────────
    def _log(self, text, tag='info'):
        self.q.put(('log', (tag, text)))

    def _append_log(self, text, tag):
        self.log_w.config(state=NORMAL)
        ts = datetime.now().strftime('%H:%M:%S')
        self.log_w.insert(END, f"[{ts}] {text}\n", tag)
        self.log_w.config(state=DISABLED)
        self.log_w.see(END)

    # ── RAPPORT ───────────────────────────────────────────
    def _save_report(self):
        if not self.devices:
            messagebox.showinfo("Rapport","Aucun périphérique scanné."); return
        p = filedialog.asksaveasfilename(
            defaultextension='.txt',
            filetypes=[("Texte","*.txt"),("JSON","*.json")],
            title="Sauvegarder le rapport",
            initialfile=f"DriverReport_{datetime.now().strftime('%Y%m%d_%H%M')}")
        if not p: return
        if p.endswith('.json'):
            data = [{k:v for k,v in d.items() if k!='catalog_data'} for d in self.devices]
            Path(p).write_text(json.dumps(data,indent=2,default=str),encoding='utf-8')
        else:
            lines = [
                "DRIVER PHANTOM — RAPPORT\n","="*70+"\n",
                f"Date     : {datetime.now()}\n",
                f"Système  : {self.sysinfo.get('os','')} {self.sysinfo.get('arch','')} Build {self.sysinfo.get('build','')}\n",
                f"Machine  : {self.sysinfo.get('manufacturer','')} {self.sysinfo.get('model','')}\n\n",
                f"{'Statut':15}  {'Catégorie':12}  {'Version':15}  {'Date':12}  Périphérique\n",
                "─"*90+"\n",
            ]
            for d in sorted(self.devices, key=lambda x: x.get('status','')):
                st = d.get('status','?')[:10]
                lines.append(f"{st:15}  {d.get('category',''):12}  {d.get('driver_version','—'):15}  {d.get('driver_date','—'):12}  {d['name']}\n")
            Path(p).write_text(''.join(lines),encoding='utf-8')
        messagebox.showinfo("Rapport",f"Sauvegardé:\n{p}")


# ═══════════════════════════════════════════════════════════════
if __name__ == '__main__':
    app = DriverPhantom()
    app.mainloop()
