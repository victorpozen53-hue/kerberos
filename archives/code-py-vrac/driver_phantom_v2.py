#!/usr/bin/env python3
"""
╔══════════════════════════════════════════════════════════════╗
║           DRIVER PHANTOM  —  v2.0 PRO                       ║
║     Détection & Mise à jour automatique des drivers         ║
║     Windows 10/11  •  Dell OptiPlex  •  Fix registry       ║
╚══════════════════════════════════════════════════════════════╝
"""

import os, sys, re, json, time, queue, hashlib, shutil
import threading, subprocess, ctypes, platform
import urllib.request, urllib.parse
from pathlib import Path
from datetime import datetime
from tkinter import *
from tkinter import ttk, filedialog, messagebox
import tkinter as tk

if platform.system() != 'Windows':
    print("Driver Phantom est conçu pour Windows 10/11.")
    sys.exit(0)

import winreg

# ═══════════════════════════════════════════════════════════════
# PALETTE
# ═══════════════════════════════════════════════════════════════
C = {
    'bg':        '#0C0E14', 'bg2':    '#12151F', 'bg3':  '#1A1E2E',
    'bg4':       '#222638', 'bg5':    '#2A2F45', 'panel':'#080A0F',
    'accent':    '#4FC3F7', 'accent2':'#0288D1',
    'green':     '#00E676', 'green_dim':'#00600F',
    'yellow':    '#FFD54F', 'yellow_dim':'#6D4C00',
    'red':       '#FF5252', 'red_dim':'#7F0000',
    'orange':    '#FF8A65', 'purple': '#CE93D8', 'teal': '#4DB6AC',
    'text':      '#E8EAF6', 'text2':  '#78909C', 'text3':'#37474F',
    'border':    '#263238', 'selected':'#0D2137',
}

FN  = ('Segoe UI', 10)
FNS = ('Segoe UI', 9)
FNB = ('Segoe UI', 11, 'bold')
FNM = ('Consolas', 9)

CATEGORIES = {
    'Display':   ('🖥️',  C['purple']),
    'Network':   ('🌐',  C['accent']),
    'Audio':     ('🔊',  C['teal']),
    'USB':       ('🔌',  C['orange']),
    'Storage':   ('💾',  C['yellow']),
    'Input':     ('⌨️',  C['green']),
    'Chipset':   ('⚙️',  C['text2']),
    'Bluetooth': ('📡',  C['purple']),
    'Camera':    ('📷',  C['teal']),
    'Other':     ('❓',  C['text3']),
}

CLASS_MAP = {
    'display':'Display', 'monitor':'Display',
    'net':'Network', 'nettrans':'Network',
    'media':'Audio', 'audioendpoint':'Audio', 'sound':'Audio',
    'usb':'USB', 'usbdevice':'USB', 'usbhub':'USB',
    'diskdrive':'Storage', 'cdrom':'Storage', 'hdc':'Storage',
    'scsi':'Storage', 'scsiadapter':'Storage', 'volume':'Storage',
    'keyboard':'Input', 'mouse':'Input', 'hidclass':'Input',
    'bluetooth':'Bluetooth',
    'camera':'Camera', 'image':'Camera',
    'system':'Chipset', 'processor':'Chipset', 'computer':'Chipset',
    'battery':'Other', 'firmware':'Other', 'softwaredevice':'Other',
    'printqueue':'Other', 'printer':'Other',
}

# ═══════════════════════════════════════════════════════════════
# HARDWARE DETECTOR — VERSION CORRIGÉE WINDOWS 10
# ═══════════════════════════════════════════════════════════════
class HardwareDetector:
    """
    Structure réelle du registry Windows 10:
    HKLM\SYSTEM\CurrentControlSet\Enum\PCI
        └── VEN_8086&DEV_1234&SUBSYS_...&REV_XX   ← niveau 1
                └── 0&1A2B3C4D&0&...              ← niveau 2 = instance
                        └── valeurs (FriendlyName, HardwareID, etc.)
    """

    BUS_PATHS = [
        ('PCI',     r'SYSTEM\CurrentControlSet\Enum\PCI'),
        ('USB',     r'SYSTEM\CurrentControlSet\Enum\USB'),
        ('HID',     r'SYSTEM\CurrentControlSet\Enum\HID'),
        ('ACPI',    r'SYSTEM\CurrentControlSet\Enum\ACPI'),
        ('IDE',     r'SYSTEM\CurrentControlSet\Enum\IDE'),
        ('SCSI',    r'SYSTEM\CurrentControlSet\Enum\SCSI'),
        ('STORAGE', r'SYSTEM\CurrentControlSet\Enum\STORAGE'),
        ('DISPLAY', r'SYSTEM\CurrentControlSet\Enum\DISPLAY'),
        ('BTH',     r'SYSTEM\CurrentControlSet\Enum\BTH'),
        ('SWD',     r'SYSTEM\CurrentControlSet\Enum\SWD'),
        ('ROOT',    r'SYSTEM\CurrentControlSet\Enum\ROOT'),
    ]

    def detect_all(self, progress_cb=None, log_cb=None) -> list:
        devices = []
        seen    = set()
        log     = log_cb or (lambda t, tag='info': None)

        total = len(self.BUS_PATHS)
        for i, (bus_name, reg_path) in enumerate(self.BUS_PATHS):
            if progress_cb:
                progress_cb(i / total * 50, f"Scan {bus_name}...")
            try:
                devs = self._scan_bus(reg_path, bus_name)
                for d in devs:
                    uid = d['hardware_id'] or d['device_id']
                    if uid and uid not in seen:
                        seen.add(uid)
                        devices.append(d)
                log(f"  {bus_name}: {len(devs)} entrées trouvées", 'info')
            except Exception as e:
                log(f"  {bus_name}: erreur ({e})", 'warn')

        if progress_cb: progress_cb(55, "Enrichissement WMI...")
        log(f"\n  Total brut: {len(devices)} périphériques", 'info')

        # Enrichissement WMI
        wmi = self._wmi_pnp()
        log(f"  WMI PnP: {len(wmi)} entrées", 'info')
        devices = self._merge(devices, wmi)

        # Fallback: si registry vide, utiliser WMI seul
        if len(devices) == 0 and wmi:
            log("  Fallback: utilisation WMI seul", 'warn')
            devices = self._wmi_to_devices(wmi)

        if progress_cb: progress_cb(80, "Lecture drivers installés...")

        # Driver info depuis pnputil
        pnp_drivers = self._pnputil_list()
        log(f"  pnputil: {len(pnp_drivers)} drivers dans le store", 'info')
        self._enrich_drivers(devices, pnp_drivers)

        if progress_cb: progress_cb(100, f"✓ {len(devices)} périphériques")
        return [d for d in devices if d['name'] and len(d['name']) > 2]

    def _scan_bus(self, reg_path: str, bus: str) -> list:
        """Scan un bus — structure 2 niveaux Windows 10"""
        devices = []
        try:
            root = winreg.OpenKey(winreg.HKEY_LOCAL_MACHINE, reg_path,
                                  access=winreg.KEY_READ | winreg.KEY_ENUMERATE_SUB_KEYS)
        except OSError:
            return devices

        # Niveau 1 : VEN_XXXX&DEV_XXXX ou VID_XXXX&PID_XXXX etc.
        i = 0
        while True:
            try:
                key1_name = winreg.EnumKey(root, i)
            except OSError:
                break
            i += 1
            try:
                key1 = winreg.OpenKey(root, key1_name,
                                      access=winreg.KEY_READ | winreg.KEY_ENUMERATE_SUB_KEYS)
                # Niveau 2 : instances
                j = 0
                while True:
                    try:
                        key2_name = winreg.EnumKey(key1, j)
                    except OSError:
                        break
                    j += 1
                    try:
                        key2 = winreg.OpenKey(key1, key2_name, access=winreg.KEY_READ)
                        dev  = self._read_device_key(key2, bus, key1_name, key2_name)
                        if dev:
                            devices.append(dev)
                        winreg.CloseKey(key2)
                    except OSError:
                        pass
                winreg.CloseKey(key1)
            except OSError:
                pass

        winreg.CloseKey(root)
        return devices

    def _read_device_key(self, key, bus: str, level1: str, level2: str) -> dict | None:
        def rv(name):
            try:
                val, _ = winreg.QueryValueEx(key, name)
                return val
            except:
                return None

        # Nom du périphérique
        friendly = rv('FriendlyName') or rv('DeviceDesc') or ''
        # Nettoyer la chaîne indirecte "@oem12.inf,..."
        if isinstance(friendly, str) and ';' in friendly:
            friendly = friendly.split(';')[-1].strip()
        if isinstance(friendly, str) and friendly.startswith('@'):
            friendly = ''

        # HardwareID
        hw_ids = rv('HardwareID') or []
        if isinstance(hw_ids, str):
            hw_ids = [hw_ids]

        compat = rv('CompatibleIDs') or []
        if isinstance(compat, str):
            compat = [compat]

        # Class
        class_name = (rv('Class') or 'other').lower().strip()
        class_guid = rv('ClassGUID') or ''
        mfg = rv('Mfg') or ''
        if isinstance(mfg, str) and ';' in mfg:
            mfg = mfg.split(';')[-1].strip()

        # Status (ConfigFlags)
        config_flags = rv('ConfigFlags') or 0
        problem = rv('Problem') or 0

        # VID/PID extraction
        vid = did = ''
        all_ids = list(hw_ids) + list(compat) + [level1]
        for hid in all_ids:
            if not isinstance(hid, str): continue
            m = re.search(r'VEN_([0-9A-Fa-f]{4})', hid)
            if m: vid = m.group(1).upper()
            m = re.search(r'DEV_([0-9A-Fa-f]{4})', hid)
            if m: did = m.group(1).upper()
            m = re.search(r'VID_([0-9A-Fa-f]{4})', hid)
            if m: vid = m.group(1).upper()
            m = re.search(r'PID_([0-9A-Fa-f]{4})', hid)
            if m: did = m.group(1).upper()
            if vid and did: break

        if not friendly and not hw_ids:
            return None

        # Nom de fallback si vide
        if not friendly:
            if hw_ids:
                friendly = hw_ids[0].split('\\')[-1]
            else:
                friendly = f"{bus}\\{level1}"

        cat = CLASS_MAP.get(class_name, 'Other')

        return {
            'device_id':      f"{bus}\\{level1}\\{level2}",
            'hardware_id':    hw_ids[0] if hw_ids else level1,
            'hw_ids':         list(hw_ids),
            'compat_ids':     list(compat),
            'name':           friendly[:120],
            'manufacturer':   mfg[:80],
            'class':          class_name,
            'class_guid':     class_guid,
            'category':       cat,
            'vendor_id':      vid,
            'device_id_hex':  did,
            'bus':            bus,
            'config_flags':   config_flags,
            'problem_code':   problem,
            'driver_version': '',
            'driver_date':    '',
            'driver_provider':'',
            'inf_path':       '',
            'status':         'unknown',
            'update_available': False,
            'new_version':    '',
            'catalog_data':   [],
        }

    def _wmi_pnp(self) -> list:
        """WMI Win32_PnPSignedDriver — source principale d'info driver"""
        try:
            ps = (
                'Get-WmiObject Win32_PnPSignedDriver | '
                'Select-Object DeviceName,DeviceID,DriverVersion,DriverDate,'
                'Manufacturer,DeviceClass,InfName,IsSigned | '
                'ConvertTo-Json -Compress -Depth 2'
            )
            out = subprocess.check_output(
                ['powershell', '-NoProfile', '-NonInteractive', '-Command', ps],
                timeout=45, stderr=subprocess.DEVNULL,
                creationflags=subprocess.CREATE_NO_WINDOW
            )
            data = json.loads(out.decode('utf-8', errors='replace'))
            if isinstance(data, dict): data = [data]
            return [d for d in (data or []) if isinstance(d, dict)]
        except Exception:
            return []

    def _wmi_to_devices(self, wmi_data: list) -> list:
        """Convertir données WMI directement en devices (fallback)"""
        devices = []
        seen    = set()
        for w in wmi_data:
            name = (w.get('DeviceName') or '').strip()
            if not name or name in seen: continue
            seen.add(name)
            cls  = (w.get('DeviceClass') or 'other').lower()
            cat  = CLASS_MAP.get(cls, 'Other')
            dev_id = w.get('DeviceID', '')
            vid = did = ''
            m = re.search(r'VEN_([0-9A-Fa-f]{4})', dev_id or '')
            if m: vid = m.group(1).upper()
            m = re.search(r'DEV_([0-9A-Fa-f]{4})', dev_id or '')
            if m: did = m.group(1).upper()
            devices.append({
                'device_id':       dev_id,
                'hardware_id':     dev_id,
                'hw_ids':          [dev_id] if dev_id else [],
                'compat_ids':      [],
                'name':            name,
                'manufacturer':    w.get('Manufacturer',''),
                'class':           cls,
                'class_guid':      '',
                'category':        cat,
                'vendor_id':       vid,
                'device_id_hex':   did,
                'bus':             dev_id.split('\\')[0] if dev_id else '',
                'config_flags':    0,
                'problem_code':    0,
                'driver_version':  w.get('DriverVersion',''),
                'driver_date':     self._parse_date(w.get('DriverDate','')),
                'driver_provider': w.get('Manufacturer',''),
                'inf_path':        w.get('InfName',''),
                'status':          'installed' if w.get('DriverVersion') else 'unknown',
                'update_available': False,
                'new_version':     '',
                'catalog_data':    [],
            })
        return devices

    def _merge(self, devices: list, wmi_data: list) -> list:
        """Enrichir les devices registry avec les infos WMI"""
        # Index WMI par nom (normalisé)
        wmi_by_name = {}
        wmi_by_devid = {}
        for w in wmi_data:
            n = (w.get('DeviceName') or '').strip().lower()
            d = (w.get('DeviceID') or '').strip().lower()
            if n: wmi_by_name[n] = w
            if d: wmi_by_devid[d] = w

        for dev in devices:
            w = (wmi_by_name.get(dev['name'].lower()) or
                 wmi_by_devid.get(dev['hardware_id'].lower()))
            if w:
                dev['driver_version']  = w.get('DriverVersion') or dev['driver_version']
                dev['driver_date']     = self._parse_date(w.get('DriverDate',''))
                dev['driver_provider'] = w.get('Manufacturer') or dev['manufacturer']
                dev['inf_path']        = w.get('InfName') or ''
                dev['status']          = 'installed' if dev['driver_version'] else 'unknown'

        return devices

    def _pnputil_list(self) -> dict:
        """Liste les drivers installés via pnputil"""
        drivers = {}
        try:
            out = subprocess.check_output(
                ['pnputil', '/enum-drivers'],
                timeout=20, stderr=subprocess.DEVNULL,
                creationflags=subprocess.CREATE_NO_WINDOW
            )
            text = out.decode('utf-8', errors='replace')
            # Parser les blocs
            current = {}
            for line in text.splitlines():
                line = line.strip()
                if ':' in line:
                    k, _, v = line.partition(':')
                    k = k.strip(); v = v.strip()
                    if 'Published Name' in k or 'Nom publié' in k:
                        current = {'inf': v}
                    elif 'Original Name' in k or 'Nom d\'origine' in k:
                        current['orig'] = v
                    elif 'Provider Name' in k or 'Nom du fournisseur' in k:
                        current['provider'] = v
                    elif 'Class Name' in k or 'Nom de la classe' in k:
                        current['class'] = v
                    elif 'Driver Version' in k or 'Version du pilote' in k:
                        current['version'] = v
                        if current.get('orig'):
                            drivers[current['orig'].lower()] = dict(current)
        except Exception:
            pass
        return drivers

    def _enrich_drivers(self, devices: list, pnp: dict):
        """Ajouter infos depuis pnputil si manquantes"""
        for dev in devices:
            if dev.get('driver_version'): continue
            inf = Path(dev.get('inf_path', '')).name.lower()
            if inf and inf in pnp:
                d = pnp[inf]
                dev['driver_version']  = d.get('version','')
                dev['driver_provider'] = d.get('provider','')
                if dev['driver_version']:
                    dev['status'] = 'installed'

    @staticmethod
    def _parse_date(s: str) -> str:
        if not s: return ''
        m = re.search(r'(\d{8})', str(s))
        if m:
            d = m.group(1)
            return f"{d[:4]}-{d[4:6]}-{d[6:8]}"
        return str(s)[:10]


# ═══════════════════════════════════════════════════════════════
# DRIVER SEARCHER
# ═══════════════════════════════════════════════════════════════
class DriverSearcher:
    HEADERS = {'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'}
    TIMEOUT = 15

    def search(self, device: dict) -> list:
        results = []
        # Stratégie 1: VEN+DEV exact
        if device['vendor_id'] and device['device_id_hex']:
            q = f"VEN_{device['vendor_id']}&DEV_{device['device_id_hex']}"
            results += self._catalog(q)
        # Stratégie 2: nom
        if not results and device['name']:
            q = re.sub(r'[^\w\s]', ' ', device['name'])[:50]
            results += self._catalog(q)
        # Stratégie 3: HW ID brut
        if not results and device['hw_ids']:
            results += self._catalog(device['hw_ids'][0][:60])
        return results[:5]

    def _catalog(self, query: str) -> list:
        try:
            url = f"https://www.catalog.update.microsoft.com/Search.aspx?q={urllib.parse.quote(query)}"
            req = urllib.request.Request(url, headers=self.HEADERS)
            with urllib.request.urlopen(req, timeout=self.TIMEOUT) as r:
                html = r.read().decode('utf-8', errors='replace')
            return self._parse(html)
        except:
            return []

    def _parse(self, html: str) -> list:
        results = []
        rows = re.findall(r'<tr[^>]*id="[^"]*_\d+"[^>]*>(.*?)</tr>', html, re.DOTALL)
        for row in rows[:6]:
            cells = re.findall(r'<td[^>]*>(.*?)</td>', row, re.DOTALL)
            if len(cells) < 5: continue
            def cl(s): return re.sub(r'\s+',' ', re.sub(r'<[^>]+>','',s)).strip()
            title = cl(cells[1]) if len(cells)>1 else ''
            ver   = cl(cells[3]) if len(cells)>3 else ''
            date  = cl(cells[4]) if len(cells)>4 else ''
            size  = cl(cells[5]) if len(cells)>5 else ''
            gm    = re.search(r"goToDetails\('([^']+)'", row)
            guid  = gm.group(1) if gm else ''
            if title and guid:
                results.append({'title':title,'version':ver,'date':date,'size':size,'guid':guid})
        return results

    def get_dl_url(self, guid: str) -> str:
        try:
            data = f'updateIDs=[{{"size":0,"languages":"","uidInfo":"{guid}","updateID":"{guid}"}}]'
            req  = urllib.request.Request(
                'https://www.catalog.update.microsoft.com/DownloadDialog.aspx',
                data=data.encode(),
                headers={**self.HEADERS,'Content-Type':'application/x-www-form-urlencoded'},
                method='POST')
            with urllib.request.urlopen(req, timeout=self.TIMEOUT) as r:
                html = r.read().decode('utf-8','replace')
            urls = re.findall(r'(https://[^"\'<>\s]+\.(?:cab|exe|msi|zip))', html, re.I)
            return urls[0] if urls else ''
        except: return ''

    def check_windows_update(self) -> list:
        """Lister les mises à jour de drivers disponibles via Windows Update"""
        try:
            ps = """
$Session = New-Object -ComObject Microsoft.Update.Session
$Searcher = $Session.CreateUpdateSearcher()
$Results = $Searcher.Search("IsInstalled=0 and Type='Driver'")
$out = @()
foreach ($u in $Results.Updates) {
    $out += [PSCustomObject]@{Title=$u.Title;Description=$u.Description}
}
$out | ConvertTo-Json -Compress
"""
            out = subprocess.check_output(
                ['powershell','-NoProfile','-Command', ps],
                timeout=30, stderr=subprocess.DEVNULL,
                creationflags=subprocess.CREATE_NO_WINDOW)
            data = json.loads(out.decode('utf-8','replace'))
            if isinstance(data, dict): data=[data]
            return data or []
        except: return []

    def install_windows_update(self) -> int:
        """Installer tous les drivers via Windows Update"""
        try:
            ps = """
$Session = New-Object -ComObject Microsoft.Update.Session
$Searcher = $Session.CreateUpdateSearcher()
$Results = $Searcher.Search("IsInstalled=0 and Type='Driver'")
if ($Results.Updates.Count -gt 0) {
    $DL = $Session.CreateUpdateDownloader(); $DL.Updates=$Results.Updates; $DL.Download()
    $IN = $Session.CreateUpdateInstaller(); $IN.Updates=$Results.Updates
    $R  = $IN.Install()
    Write-Output $Results.Updates.Count
} else { Write-Output 0 }
"""
            out = subprocess.check_output(
                ['powershell','-NoProfile','-Command', ps],
                timeout=300, stderr=subprocess.DEVNULL,
                creationflags=subprocess.CREATE_NO_WINDOW)
            return int(out.decode().strip() or '0')
        except: return 0


# ═══════════════════════════════════════════════════════════════
# INSTALLER
# ═══════════════════════════════════════════════════════════════
class DriverInstaller:
    def __init__(self, work: Path, log_cb=None):
        self.work = work; self.log = log_cb or print
        work.mkdir(parents=True, exist_ok=True)

    def is_admin(self):
        try: return bool(ctypes.windll.shell32.IsUserAnAdmin())
        except: return False

    def download(self, url, name, prog_cb=None) -> Path | None:
        safe = re.sub(r'[^\w\-_.]','_',name)[:50]
        ext  = Path(url.split('?')[0]).suffix or '.cab'
        dest = self.work / f"{safe}{ext}"
        try:
            req = urllib.request.Request(url, headers={'User-Agent':'Mozilla/5.0'})
            with urllib.request.urlopen(req, timeout=60) as r:
                total = int(r.headers.get('Content-Length',0))
                done  = 0
                with open(dest,'wb') as f:
                    while True:
                        chunk = r.read(65536)
                        if not chunk: break
                        f.write(chunk); done+=len(chunk)
                        if prog_cb and total: prog_cb(done/total*100)
            self.log(f"  ✓ Téléchargé: {dest.name} ({done//1024} KB)",'ok')
            return dest
        except Exception as e:
            self.log(f"  ✗ Download failed: {e}",'err'); return None

    def install_cab(self, cab: Path) -> bool:
        try:
            xd = self.work/'extracted'/cab.stem
            xd.mkdir(parents=True, exist_ok=True)
            subprocess.run(['expand',str(cab),'-F:*',str(xd)],
                timeout=60, check=True, stderr=subprocess.DEVNULL,
                creationflags=subprocess.CREATE_NO_WINDOW)
            for inf in xd.rglob('*.inf'):
                r = subprocess.run(
                    ['pnputil','/add-driver',str(inf),'/install','/subdirs'],
                    timeout=120, capture_output=True, text=True,
                    creationflags=subprocess.CREATE_NO_WINDOW)
                if r.returncode == 0:
                    self.log(f"  ✓ Installé via pnputil: {inf.name}",'ok'); return True
            return False
        except Exception as e:
            self.log(f"  ✗ CAB install: {e}",'err'); return False

    def install_exe(self, exe: Path) -> bool:
        try:
            for flag in ['/s','/silent','/quiet']:
                r = subprocess.run([str(exe),flag,'/norestart'],
                    timeout=180, capture_output=True,
                    creationflags=subprocess.CREATE_NO_WINDOW)
                if r.returncode in (0,3010):
                    self.log(f"  ✓ Installé (code {r.returncode})",'ok'); return True
            subprocess.Popen([str(exe)])
            self.log("  ↗ Lancé normalement (intervention manuelle)",'warn'); return True
        except Exception as e:
            self.log(f"  ✗ EXE: {e}",'err'); return False


# ═══════════════════════════════════════════════════════════════
# SYSTEM INFO
# ═══════════════════════════════════════════════════════════════
def get_sysinfo() -> dict:
    info = {'os':'','build':'','arch':'','cpu':'','ram':'','hostname':'','manufacturer':'','model':''}
    try:
        ps = ('Get-ComputerInfo | Select-Object OsName,OsBuildNumber,OsArchitecture,'
              'CsName,CsManufacturer,CsModel,CsProcessors,CsTotalPhysicalMemory | ConvertTo-Json -Compress')
        out = subprocess.check_output(['powershell','-NoProfile','-Command',ps],
            timeout=20, stderr=subprocess.DEVNULL, creationflags=subprocess.CREATE_NO_WINDOW)
        d = json.loads(out.decode('utf-8','replace'))
        info['os']  = d.get('OsName','').replace('Microsoft ','')
        info['build']= str(d.get('OsBuildNumber',''))
        info['arch'] = d.get('OsArchitecture','')
        info['hostname'] = d.get('CsName','')
        info['manufacturer'] = d.get('CsManufacturer','')
        info['model'] = d.get('CsModel','')
        ram = d.get('CsTotalPhysicalMemory',0)
        if ram: info['ram'] = f"{int(ram)//1073741824} GB"
        cpu = d.get('CsProcessors')
        if isinstance(cpu,list) and cpu: info['cpu'] = cpu[0].get('Name','')
        elif isinstance(cpu,dict): info['cpu'] = cpu.get('Name','')
    except: pass
    return info


# ═══════════════════════════════════════════════════════════════
# APPLICATION
# ═══════════════════════════════════════════════════════════════
class DriverPhantom(Tk):
    def __init__(self):
        super().__init__()
        self.title("DRIVER PHANTOM v2  —  Dell OptiPlex 780  •  Win10")
        self.geometry("1300x820")
        self.minsize(1050,680)
        self.configure(bg=C['bg'])

        self.devices   = []
        self.q         = queue.Queue()
        self.running   = False
        self.work_dir  = Path(os.environ.get('TEMP','C:\\Temp'))/'DriverPhantom'
        self.backup_dir= Path(os.environ.get('USERPROFILE','C:\\'))/'DriverPhantom_Backup'
        self.detector  = HardwareDetector()
        self.searcher  = DriverSearcher()
        self.installer = DriverInstaller(self.work_dir, self._log)
        self.sysinfo   = {}
        self._sort_col = None
        self._sort_rev = False

        self._style()
        self._ui()
        self._poll()

        threading.Thread(target=lambda: self.q.put(('sysinfo', get_sysinfo())), daemon=True).start()

    # ── STYLE ──────────────────────────────────────────────
    def _style(self):
        s = ttk.Style(self); s.theme_use('clam')
        s.configure('.', background=C['bg'], foreground=C['text'], font=FN)
        s.configure('TFrame', background=C['bg'])
        s.configure('TLabel', background=C['bg'], foreground=C['text'])
        s.configure('TLabelframe', background=C['bg2'], foreground=C['accent'], relief='flat')
        s.configure('TLabelframe.Label', background=C['bg2'], foreground=C['accent'], font=('Segoe UI',9,'bold'))
        s.configure('TProgressbar', troughcolor=C['bg3'], background=C['accent'], thickness=5)
        s.configure('Treeview', background=C['bg2'], foreground=C['text'],
                    fieldbackground=C['bg2'], rowheight=24, borderwidth=0, font=FN)
        s.configure('Treeview.Heading', background=C['bg4'], foreground=C['accent'],
                    font=('Segoe UI',9,'bold'), relief='flat')
        s.map('Treeview', background=[('selected',C['selected'])], foreground=[('selected',C['accent'])])
        s.configure('TNotebook', background=C['bg'], borderwidth=0)
        s.configure('TNotebook.Tab', background=C['bg3'], foreground=C['text2'], padding=(14,6), font=FNS)
        s.map('TNotebook.Tab', background=[('selected',C['bg2'])], foreground=[('selected',C['accent'])])

    # ── UI ──────────────────────────────────────────────────
    def _ui(self):
        # Header
        hdr = Frame(self, bg=C['panel'], height=58); hdr.pack(fill=X); hdr.pack_propagate(False)
        Frame(hdr, bg=C['accent'], width=4).pack(side=LEFT, fill=Y)
        lg = Frame(hdr, bg=C['panel']); lg.pack(side=LEFT, padx=14, pady=8)
        Label(lg, text="◈ DRIVER PHANTOM  v2", font=('Segoe UI',16,'bold'), bg=C['panel'], fg=C['accent']).pack(anchor=W)
        Label(lg, text="Détection automatique des drivers  •  Windows 10  •  Dell OptiPlex", font=FNS, bg=C['panel'], fg=C['text2']).pack(anchor=W)
        self.lbl_sys = Label(hdr, text="Chargement...", font=FNS, bg=C['panel'], fg=C['text2'])
        self.lbl_sys.pack(side=LEFT, padx=20)
        is_adm = self.installer.is_admin()
        Label(hdr, text="⚡ ADMIN" if is_adm else "⚠ PAS ADMIN",
              font=('Segoe UI',9,'bold'), bg=C['green_dim'] if is_adm else C['red_dim'],
              fg=C['green'] if is_adm else C['red'], padx=10, pady=4).pack(side=RIGHT, padx=14, pady=16)

        # Main
        main = Frame(self, bg=C['bg']); main.pack(fill=BOTH, expand=True, padx=10, pady=8)
        left = Frame(main, bg=C['bg'], width=270); left.pack(side=LEFT, fill=Y, padx=(0,8)); left.pack_propagate(False)
        self._left(left)
        right = Frame(main, bg=C['bg']); right.pack(side=LEFT, fill=BOTH, expand=True)
        self._right(right)

        # Statusbar
        sb = Frame(self, bg=C['bg4'], height=26); sb.pack(fill=X, side=BOTTOM); sb.pack_propagate(False)
        Frame(sb, bg=C['accent2'], width=3).pack(side=LEFT, fill=Y)
        self.sv = StringVar(value="Prêt — Cliquez DÉTECTER pour analyser KERBEROS-IA")
        Label(sb, textvariable=self.sv, font=FNS, bg=C['bg4'], fg=C['text2']).pack(side=LEFT, padx=8, pady=4)
        self.sv2 = StringVar(value="")
        Label(sb, textvariable=self.sv2, font=FNS, bg=C['bg4'], fg=C['green']).pack(side=RIGHT, padx=12)

    def _left(self, p):
        # Actions
        f1 = ttk.LabelFrame(p, text=" ACTIONS ", padding=10); f1.pack(fill=X, pady=(0,7))
        self.b_scan   = self._btn(f1,"🔍  DÉTECTER LE HARDWARE",     self._scan)
        self.b_search = self._btn(f1,"🌐  CHERCHER MISES À JOUR",    self._search, C['yellow'])
        self.b_wu     = self._btn(f1,"🪟  WINDOWS UPDATE DRIVERS",   self._wu_check, C['teal'])
        self.b_upall  = self._btn(f1,"⚡  TOUT METTRE À JOUR",       self._upall, C['green'])
        self.b_upsel  = self._btn(f1,"▶  METTRE À JOUR SÉLECTION",  self._upsel, C['accent'])
        self.b_stop   = self._btn(f1,"⏹  ARRÊTER",                  self._stop, C['red'])
        for b in (self.b_scan,self.b_search,self.b_wu,self.b_upall,self.b_upsel,self.b_stop):
            b.pack(fill=X, pady=2)
        for b in (self.b_search,self.b_wu,self.b_upall,self.b_upsel,self.b_stop):
            b.config(state=DISABLED)

        # Filtres
        f2 = ttk.LabelFrame(p, text=" FILTRES ", padding=10); f2.pack(fill=X, pady=(0,7))
        Label(f2,text="Catégorie:",font=FNS,bg=C['bg2'],fg=C['text2']).pack(anchor=W)
        self.flt_cat = StringVar(value='Tous')
        ttk.Combobox(f2,textvariable=self.flt_cat,font=FNS,state='readonly',
            values=['Tous']+list(CATEGORIES.keys())).pack(fill=X,pady=(2,6))
        self.flt_cat.trace('w', lambda *_: self._filter())
        Label(f2,text="Statut:",font=FNS,bg=C['bg2'],fg=C['text2']).pack(anchor=W)
        self.flt_st = StringVar(value='Tous')
        ttk.Combobox(f2,textvariable=self.flt_st,font=FNS,state='readonly',
            values=['Tous','Installé','Manquant','Obsolète','Inconnu']).pack(fill=X,pady=(2,6))
        self.flt_st.trace('w', lambda *_: self._filter())
        Label(f2,text="Recherche:",font=FNS,bg=C['bg2'],fg=C['text2']).pack(anchor=W)
        self.flt_txt = StringVar(); self.flt_txt.trace('w', lambda *_: self._filter())
        Entry(f2,textvariable=self.flt_txt,bg=C['bg3'],fg=C['text'],insertbackground=C['accent'],
              relief='flat',font=FNM,bd=0,highlightthickness=1,
              highlightcolor=C['accent'],highlightbackground=C['border']).pack(fill=X,pady=2)

        # Options
        f3 = ttk.LabelFrame(p, text=" OPTIONS ", padding=10); f3.pack(fill=X, pady=(0,7))
        self.opt_backup = BooleanVar(value=True)
        self.opt_silent = BooleanVar(value=True)
        for var, lbl, col in [
            (self.opt_backup,"💾  Backup avant install", C['yellow']),
            (self.opt_silent,"🔇  Installation silencieuse", C['accent']),
        ]:
            tk.Checkbutton(f3,text=lbl,variable=var,bg=C['bg2'],fg=col,selectcolor=C['bg3'],
                activebackground=C['bg2'],font=FNS,cursor='hand2').pack(anchor=W,pady=2)

        # Progress
        f4 = ttk.LabelFrame(p, text=" PROGRESSION ", padding=10); f4.pack(fill=X, pady=(0,7))
        self.pv = tk.DoubleVar()
        ttk.Progressbar(f4,variable=self.pv,maximum=100).pack(fill=X,pady=(0,4))
        self.plbl = Label(f4,text="En attente...",font=FNS,bg=C['bg2'],fg=C['text2'])
        self.plbl.pack(anchor=W)

        # Stats
        f5 = ttk.LabelFrame(p, text=" RÉSUMÉ ", padding=8); f5.pack(fill=X)
        self.sv_stats = {}
        for k,lbl,col in [
            ('total','Périphériques',C['text2']),
            ('inst', 'Avec driver',  C['green']),
            ('miss', 'Sans driver',  C['red']),
            ('outd', 'Obsolètes',    C['yellow']),
            ('upd',  'Mis à jour',   C['accent']),
        ]:
            r=Frame(f5,bg=C['bg2']); r.pack(fill=X,pady=1)
            Label(r,text=f"{lbl}:",font=FNS,bg=C['bg2'],fg=C['text2'],width=14,anchor=W).pack(side=LEFT)
            v=StringVar(value='—'); self.sv_stats[k]=v
            Label(r,textvariable=v,font=FNS,bg=C['bg2'],fg=col).pack(side=LEFT)

    def _right(self, p):
        nb = ttk.Notebook(p); nb.pack(fill=BOTH, expand=True)

        # Tab drivers
        t1 = Frame(nb,bg=C['bg']); nb.add(t1,text="  🖥️ PÉRIPHÉRIQUES  ")
        tb = Frame(t1,bg=C['bg4'],height=36); tb.pack(fill=X); tb.pack_propagate(False)
        self._btn(tb,"☑ Tout",self._selall,small=True).pack(side=LEFT,padx=8,pady=5)
        for lbl,st,col in [('Manquants','missing',C['red']),('Obsolètes','outdated',C['yellow'])]:
            self._btn(tb,lbl,lambda s=st:self._sel_st(s),small=True,color=col).pack(side=LEFT,padx=2,pady=5)
        self._btn(tb,"📄 Rapport",self._report,small=True,color=C['text2']).pack(side=RIGHT,padx=8,pady=5)

        cols=('icon','name','mfg','ver','date','cat','status','action')
        self.tree=ttk.Treeview(t1,columns=cols,show='headings',selectmode='extended')
        for col,hdr,w,anc in [
            ('icon','',35,'center'),('name','Périphérique',300,'w'),
            ('mfg','Fabricant',130,'w'),('ver','Version',100,'center'),
            ('date','Date',95,'center'),('cat','Catégorie',90,'center'),
            ('status','Statut',95,'center'),('action','Action',85,'center'),
        ]:
            self.tree.heading(col,text=hdr,command=lambda c=col:self._sort(c))
            self.tree.column(col,width=w,anchor=anc,minwidth=25)

        self.tree.tag_configure('installed', foreground=C['green'])
        self.tree.tag_configure('outdated',  foreground=C['yellow'])
        self.tree.tag_configure('missing',   foreground=C['red'])
        self.tree.tag_configure('unknown',   foreground=C['text2'])
        self.tree.tag_configure('updating',  foreground=C['accent'])

        vsb=ttk.Scrollbar(t1,orient=VERTICAL,command=self.tree.yview)
        hsb=ttk.Scrollbar(t1,orient=HORIZONTAL,command=self.tree.xview)
        self.tree.configure(yscrollcommand=vsb.set,xscrollcommand=hsb.set)
        vsb.pack(side=RIGHT,fill=Y); self.tree.pack(side=TOP,fill=BOTH,expand=True); hsb.pack(side=BOTTOM,fill=X)
        self.tree.bind('<Double-1>', self._detail)
        self.tree.bind('<<TreeviewSelect>>', lambda e: self.b_upsel.config(state=NORMAL if self.tree.selection() else DISABLED))

        # Tab log
        t2=Frame(nb,bg=C['bg']); nb.add(t2,text="  📋 LOG  ")
        self.log_w=Text(t2,bg=C['bg2'],fg=C['text'],font=FNM,relief='flat',wrap=WORD,state=DISABLED)
        lsb=ttk.Scrollbar(t2,command=self.log_w.yview); self.log_w.configure(yscrollcommand=lsb.set)
        lsb.pack(side=RIGHT,fill=Y); self.log_w.pack(fill=BOTH,expand=True)
        for tag,col,bold in [('title',C['accent'],True),('ok',C['green'],False),
                              ('warn',C['yellow'],False),('err',C['red'],False),
                              ('info',C['text2'],False),('sep',C['text3'],False)]:
            self.log_w.tag_configure(tag,foreground=col,font=('Consolas',9,'bold' if bold else 'normal'))

        # Tab sysinfo
        t3=Frame(nb,bg=C['bg']); nb.add(t3,text="  💻 SYSTÈME  ")
        self.sys_w=Text(t3,bg=C['bg2'],fg=C['text'],font=FNM,relief='flat',state=DISABLED)
        self.sys_w.pack(fill=BOTH,expand=True)

    # ── BOUTONS ─────────────────────────────────────────────
    def _btn(self, p, text, cmd, color=None, small=False):
        c=color or C['accent']; f=FNS if small else ('Segoe UI',10,'bold'); py=3 if small else 7
        b=tk.Button(p,text=text,command=cmd,bg=C['bg3'],fg=c,activebackground=C['bg5'],
                    activeforeground=c,relief='flat',bd=0,font=f,cursor='hand2',padx=8,pady=py)
        b.bind('<Enter>',lambda e:b.config(bg=C['bg5']))
        b.bind('<Leave>',lambda e:b.config(bg=C['bg3']))
        return b

    # ── SCAN ────────────────────────────────────────────────
    def _scan(self):
        if self.running: return
        self.running=True; self.devices.clear()
        for i in self.tree.get_children(): self.tree.delete(i)
        self.b_scan.config(state=DISABLED); self.b_stop.config(state=NORMAL)
        self.b_search.config(state=DISABLED); self.pv.set(0)
        self._log("="*55,'sep'); self._log(" DRIVER PHANTOM v2 — Scan KERBEROS-IA",'title'); self._log("="*55,'sep')
        self._log(f"Dell OptiPlex 780 • Win10 Build 19045 • Core2Duo E7600",'info')

        def run():
            self.devices = self.detector.detect_all(
                progress_cb=lambda p,l: self.q.put(('prog',(p,l))),
                log_cb=lambda t,tag='info': self.q.put(('log',(tag,t)))
            )
            self.q.put(('scan_done', self.devices))
        threading.Thread(target=run, daemon=True).start()

    def _search(self):
        if self.running or not self.devices: return
        self.running=True; self.b_search.config(state=DISABLED); self.b_stop.config(state=NORMAL)
        self._log("\n🌐 Recherche Microsoft Catalog...",'title')

        def run():
            for i,dev in enumerate(self.devices):
                if not self.running: break
                self.q.put(('prog',(i/len(self.devices)*100,f"Recherche: {dev['name'][:38]}...")))
                results = self.searcher.search(dev)
                if results:
                    dev['catalog_data']    = results
                    dev['update_available']= True
                    dev['new_version']     = results[0].get('version','')
                    if dev['driver_version']:
                        dev['status'] = 'outdated'
                    else:
                        dev['status'] = 'missing'
                    self.q.put(('refresh', dev))
            self.q.put(('search_done', None))
        threading.Thread(target=run, daemon=True).start()

    def _wu_check(self):
        self.b_wu.config(state=DISABLED); self.b_stop.config(state=NORMAL)
        self._log("\n🪟 Vérification Windows Update...",'title')

        def run():
            updates = self.searcher.check_windows_update()
            self._log(f"  Windows Update: {len(updates)} driver(s) disponible(s)",'ok' if updates else 'info')
            for u in updates:
                self._log(f"  → {u.get('Title','')[:70]}",'info')
            if updates:
                msg = f"{len(updates)} driver(s) disponible(s) via Windows Update:\n\n"
                msg += '\n'.join(f"• {u.get('Title','')[:60]}" for u in updates[:10])
                msg += "\n\nCliquez 'TOUT METTRE À JOUR' pour installer."
                self.q.put(('msgbox', msg))
            else:
                self.q.put(('msgbox', "Aucune mise à jour de driver disponible via Windows Update."))
            self.q.put(('wu_done', len(updates)))
        threading.Thread(target=run, daemon=True).start()

    def _upall(self):
        todo = [d for d in self.devices if d.get('update_available') or d['status'] in ('missing','outdated')]
        if not todo:
            # Essayer Windows Update direct
            self._wu_install(); return
        self._do_update(todo)

    def _upsel(self):
        sel = self.tree.selection()
        if not sel: return
        names = {self.tree.item(i,'values')[1] for i in sel}
        self._do_update([d for d in self.devices if d['name'] in names])

    def _wu_install(self):
        self.running=True; self.b_upall.config(state=DISABLED); self.b_stop.config(state=NORMAL)
        self._log("\n⚡ Installation via Windows Update...",'title')

        def run():
            n = self.searcher.install_windows_update()
            self._log(f"✓ {n} driver(s) installé(s) via Windows Update",'ok')
            self.q.put(('update_done', n))
        threading.Thread(target=run, daemon=True).start()

    def _do_update(self, devs):
        if not devs: messagebox.showinfo("Info","Rien à mettre à jour."); return
        self.running=True; self.b_upall.config(state=DISABLED)
        self.b_upsel.config(state=DISABLED); self.b_stop.config(state=NORMAL)
        n_ok=[0]

        def run():
            for i,dev in enumerate(devs):
                if not self.running: break
                self._log(f"\n[{i+1}/{len(devs)}] {dev['name']}",'info')
                self.q.put(('prog',(i/len(devs)*100,f"Update: {dev['name'][:38]}...")))
                self.q.put(('set_st',(dev['name'],'updating')))
                ok=False
                # 1. Windows Update
                if not ok:
                    ok = self.searcher.install_windows_update() > 0
                # 2. Catalog
                if not ok:
                    for entry in dev.get('catalog_data',[])[:3]:
                        url = self.searcher.get_dl_url(entry.get('guid',''))
                        if not url: continue
                        if self.opt_backup.get():
                            (self.backup_dir/dev['name'][:40]).mkdir(parents=True,exist_ok=True)
                        path = self.installer.download(url, dev['name'][:40])
                        if not path: continue
                        if path.suffix.lower()=='.cab': ok=self.installer.install_cab(path)
                        else: ok=self.installer.install_exe(path)
                        if ok: break
                st='installed' if ok else 'unknown'
                if ok: n_ok[0]+=1
                self.q.put(('set_st',(dev['name'],st)))
                self._log(f"  {'✓ Succès' if ok else '✗ Échec'}",'ok' if ok else 'warn')
            self.q.put(('update_done',n_ok[0]))
        threading.Thread(target=run, daemon=True).start()

    def _stop(self):
        self.running=False; self._log("⏹ Arrêt...",'warn')

    # ── POLL ────────────────────────────────────────────────
    def _poll(self):
        try:
            while True:
                msg,data=self.q.get_nowait()
                if msg=='log':
                    self._append_log(data[1],data[0])
                elif msg=='prog':
                    p,l=data; self.pv.set(p); self.plbl.config(text=l); self.sv.set(l)
                elif msg=='scan_done':
                    self._on_scan(data)
                elif msg=='refresh':
                    self._add_row(data)
                elif msg=='set_st':
                    self._set_st(data[0],data[1])
                elif msg=='search_done':
                    self._on_search()
                elif msg=='update_done':
                    self._on_upd(data)
                elif msg=='wu_done':
                    self.b_wu.config(state=NORMAL); self.b_stop.config(state=DISABLED)
                    self.pv.set(100); self.plbl.config(text="✓ Windows Update vérifié")
                elif msg=='msgbox':
                    messagebox.showinfo("Windows Update",data)
                elif msg=='sysinfo':
                    self._show_sys(data)
        except queue.Empty: pass
        self.after(80, self._poll)

    def _log(self, text, tag='info'):
        self.q.put(('log',(tag,text)))

    def _append_log(self, text, tag):
        self.log_w.config(state=NORMAL)
        self.log_w.insert(END,f"[{datetime.now().strftime('%H:%M:%S')}] {text}\n",tag)
        self.log_w.config(state=DISABLED); self.log_w.see(END)

    # ── SCAN DONE ───────────────────────────────────────────
    def _on_scan(self, devs):
        self.running=False; self.b_scan.config(state=NORMAL)
        self.b_stop.config(state=DISABLED); self.b_search.config(state=NORMAL)
        self.b_wu.config(state=NORMAL); self.b_upall.config(state=NORMAL)
        self.pv.set(100)
        for d in devs: self._add_row(d)
        total=len(devs); inst=sum(1 for d in devs if d['driver_version']); miss=total-inst
        self.sv_stats['total'].set(str(total)); self.sv_stats['inst'].set(str(inst))
        self.sv_stats['miss'].set(str(miss)); self.sv_stats['upd'].set('0')
        self.sv2.set(f"{total} périphériques"); self.plbl.config(text=f"✓ {total} périphériques")
        self._log(f"\n✓ {total} périphériques | {inst} avec driver | {miss} sans driver",'ok')
        self._log("→ Cliquez 'CHERCHER MISES À JOUR' ou 'WINDOWS UPDATE DRIVERS'",'info')

    def _on_search(self):
        self.running=False; self.b_stop.config(state=DISABLED); self.b_search.config(state=NORMAL)
        self.pv.set(100)
        n=sum(1 for d in self.devices if d.get('update_available'))
        self.sv_stats['outd'].set(str(n))
        self._log(f"✓ {n} mise(s) à jour disponible(s)",'ok')
        self.plbl.config(text=f"✓ {n} mises à jour")

    def _on_upd(self, n):
        self.running=False; self.b_stop.config(state=DISABLED)
        self.b_upall.config(state=NORMAL); self.b_upsel.config(state=NORMAL)
        self.pv.set(100); self.sv_stats['upd'].set(str(n))
        self.plbl.config(text=f"✓ {n} drivers mis à jour")
        self._log(f"\n✓ {n} driver(s) mis à jour",'ok')
        if n: messagebox.showinfo("Terminé", f"{n} driver(s) mis à jour.\nRedémarrage recommandé.")

    # ── TREE ────────────────────────────────────────────────
    def _add_row(self, d):
        cat=d.get('category','Other')
        icon=CATEGORIES.get(cat,('❓',''))[0]
        ver=d.get('driver_version','') or '—'
        date=d.get('driver_date','') or '—'
        st=d.get('status','unknown')
        st_map={'installed':('✓ Installé','installed'),'outdated':('⚠ Obsolète','outdated'),
                'missing':('✗ Manquant','missing'),'updating':('↻ En cours','updating')}
        lbl,tag=st_map.get(st,('? Inconnu','unknown'))
        act='⬇ Update' if d.get('update_available') else ''
        for item in self.tree.get_children():
            if self.tree.item(item,'values')[1]==d['name']:
                self.tree.item(item,values=(icon,d['name'],d.get('manufacturer',''),ver,date,cat,lbl,act),tags=(tag,))
                return
        self.tree.insert('',END,values=(icon,d['name'],d.get('manufacturer',''),ver,date,cat,lbl,act),tags=(tag,))

    def _set_st(self, name, st):
        m={'installed':('✓ Installé','installed'),'outdated':('⚠ Obsolète','outdated'),
           'missing':('✗ Manquant','missing'),'updating':('↻ En cours','updating')}
        lbl,tag=m.get(st,('? Inconnu','unknown'))
        for item in self.tree.get_children():
            if self.tree.item(item,'values')[1]==name:
                v=list(self.tree.item(item,'values')); v[6]=lbl
                self.tree.item(item,values=tuple(v),tags=(tag,)); break

    def _filter(self):
        cat=self.flt_cat.get(); st=self.flt_st.get(); txt=self.flt_txt.get().lower()
        for i in self.tree.get_children(): self.tree.delete(i)
        sm={'Installé':'installed','Manquant':'missing','Obsolète':'outdated','Inconnu':'unknown'}
        for d in self.devices:
            if cat!='Tous' and d.get('category')!=cat: continue
            if st!='Tous' and d.get('status')!=sm.get(st,''): continue
            if txt and txt not in d['name'].lower() and txt not in d.get('manufacturer','').lower(): continue
            self._add_row(d)

    def _selall(self): self.tree.selection_set(self.tree.get_children())

    def _sel_st(self, st):
        self.tree.selection_remove(self.tree.get_children())
        for item in self.tree.get_children():
            if st in (self.tree.item(item,'tags') or []):
                self.tree.selection_add(item)

    def _sort(self, col):
        data=[(self.tree.set(k,col),k) for k in self.tree.get_children()]
        rev=self._sort_col==col and not self._sort_rev
        data.sort(reverse=rev, key=lambda x: x[0].lower() if x[0] else '')
        for i,(_,k) in enumerate(data): self.tree.move(k,'',i)
        self._sort_col=col; self._sort_rev=rev

    def _detail(self, event):
        sel=self.tree.selection()
        if not sel: return
        name=self.tree.item(sel[0],'values')[1]
        dev=next((d for d in self.devices if d['name']==name),None)
        if not dev: return
        w=Toplevel(self); w.title(f"Détail: {name[:40]}"); w.geometry("580x440")
        w.configure(bg=C['bg']); w.transient(self)
        Label(w,text=f"  {name}",font=FNB,bg=C['bg3'],fg=C['accent'],anchor=W).pack(fill=X)
        t=Text(w,bg=C['bg2'],fg=C['text'],font=FNM,relief='flat',wrap=WORD)
        sb=ttk.Scrollbar(w,command=t.yview); t.configure(yscrollcommand=sb.set)
        sb.pack(side=RIGHT,fill=Y); t.pack(fill=BOTH,expand=True,padx=4,pady=4)
        t.tag_configure('k',foreground=C['accent'],font=('Consolas',9,'bold'))
        t.tag_configure('v',foreground=C['text'])
        t.tag_configure('h',foreground=C['yellow'],font=('Consolas',10,'bold'))
        def ln(k,v): t.insert(END,f"  {k+':':<22}",'k'); t.insert(END,f"{v}\n",'v')
        t.insert(END,"PÉRIPHÉRIQUE\n",'h')
        ln("Nom",dev['name']); ln("Fabricant",dev.get('manufacturer','—'))
        ln("Catégorie",dev.get('category','—')); ln("Bus",dev.get('bus','—'))
        ln("Vendor ID",dev.get('vendor_id','—')); ln("Device ID",dev.get('device_id_hex','—'))
        t.insert(END,"\nDRIVER\n",'h')
        ln("Version",dev.get('driver_version','—')); ln("Date",dev.get('driver_date','—'))
        ln("Fournisseur",dev.get('driver_provider','—')); ln("INF",dev.get('inf_path','—'))
        t.insert(END,"\nHARDWARE IDs\n",'h')
        for hid in dev.get('hw_ids',[])[:6]: t.insert(END,f"  {hid}\n",'v')
        if dev.get('catalog_data'):
            t.insert(END,"\nMISES À JOUR TROUVÉES\n",'h')
            for r in dev['catalog_data']:
                ln("  Titre",r.get('title','')[:60]); ln("  Version",r.get('version',''))
        t.config(state=DISABLED)
        self._btn(w,"⬇ Mettre à jour",lambda:[w.destroy(),self._do_update([dev])],C['green']).pack(fill=X,padx=4,pady=4)

    def _show_sys(self, info):
        self.sysinfo=info
        self.lbl_sys.config(text=f"💻 {info.get('os','')} {info.get('build','')}  •  {info.get('cpu','')[:30]}  •  {info.get('ram','')}")
        self.sys_w.config(state=NORMAL); self.sys_w.delete('1.0',END)
        lines=["╔═══════════════════════════════════════════╗",
               "║        INFORMATIONS SYSTÈME               ║","╚═══════════════════════════════════════════╝","",
               f"  OS           : {info.get('os','')}",f"  Build        : {info.get('build','')}",
               f"  Architecture : {info.get('arch','')}",f"  Machine      : {info.get('hostname','')}",
               f"  Fabricant    : {info.get('manufacturer','')}",f"  Modèle       : {info.get('model','')}",
               f"  CPU          : {info.get('cpu','')}",f"  RAM          : {info.get('ram','')}","",
               f"  Work dir     : {self.work_dir}",f"  Backup dir   : {self.backup_dir}",
               f"  Admin        : {'Oui ✓' if self.installer.is_admin() else 'Non ✗  (certaines installations requièrent admin)'}"]
        self.sys_w.insert(END,'\n'.join(lines)); self.sys_w.config(state=DISABLED)

    def _report(self):
        if not self.devices: messagebox.showinfo("Rapport","Scannez d'abord."); return
        p=filedialog.asksaveasfilename(defaultextension='.txt',
            filetypes=[("Texte","*.txt"),("JSON","*.json")],
            initialfile=f"DriverReport_{datetime.now().strftime('%Y%m%d_%H%M')}")
        if not p: return
        if p.endswith('.json'):
            Path(p).write_text(json.dumps([{k:v for k,v in d.items() if k!='catalog_data'}
                for d in self.devices],indent=2,default=str),encoding='utf-8')
        else:
            lines=["DRIVER PHANTOM — RAPPORT\n","="*70+"\n",
                   f"Machine  : {self.sysinfo.get('manufacturer','')} {self.sysinfo.get('model','')}\n",
                   f"OS       : {self.sysinfo.get('os','')} Build {self.sysinfo.get('build','')}\n\n",
                   f"{'Statut':15}  {'Catégorie':12}  {'Version':20}  Périphérique\n","─"*90+"\n"]
            for d in sorted(self.devices, key=lambda x: x.get('status','')):
                lines.append(f"{d.get('status','?'):15}  {d.get('category',''):12}  {d.get('driver_version','—'):20}  {d['name']}\n")
            Path(p).write_text(''.join(lines),encoding='utf-8')
        messagebox.showinfo("Rapport",f"Sauvegardé:\n{p}")


# ═══════════════════════════════════════════════════════════════
if __name__ == '__main__':
    app = DriverPhantom()
    app.mainloop()
