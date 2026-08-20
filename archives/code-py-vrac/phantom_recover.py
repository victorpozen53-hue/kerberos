#!/usr/bin/env python3
"""
╔══════════════════════════════════════════════════════════════╗
║           PHANTOM RECOVER  —  v3.0 PRO                      ║
║     NTFS Deep Recovery Tool  •  Windows 10/11               ║
║                                                              ║
║  • Lecture directe PhysicalDrive (bypass filesystem)        ║
║  • Majority Voting sur secteurs instables                   ║
║  • Carte visuelle des clusters                              ║
║  • MFT scanner (deleted only — ignore fichiers existants)   ║
║  • File Carving 20+ formats                                 ║
║  • Reconstruction partielle fichiers fragmentés             ║
║                                                              ║
║  Lancement : python phantom_recover.py                      ║
║  Aucune dépendance externe requise (tkinter natif)          ║
╚══════════════════════════════════════════════════════════════╝
"""

import os, sys, struct, threading, hashlib, json, queue, time, ctypes, platform
from pathlib import Path
from datetime import datetime, timezone
from tkinter import *
from tkinter import ttk, filedialog, messagebox
import tkinter as tk
import tkinter.font as tkfont

IS_WINDOWS = platform.system() == 'Windows'

# ═══════════════════════════════════════════════════════════════
# PALETTE  —  Dark Industrial Forensic
# ═══════════════════════════════════════════════════════════════
C = {
    'bg':         '#0D0F14',
    'bg2':        '#141720',
    'bg3':        '#1C2030',
    'bg4':        '#242838',
    'panel':      '#0A0C10',
    'accent':     '#00E5FF',
    'accent_dim': '#007A99',
    'green':      '#00FF9D',
    'green_dim':  '#007A4A',
    'yellow':     '#FFD23F',
    'yellow_dim': '#7A5E00',
    'red':        '#FF3860',
    'red_dim':    '#7A0020',
    'orange':     '#FF6B35',
    'purple':     '#B794F4',
    'text':       '#CDD6F4',
    'text2':      '#6C7086',
    'text3':      '#45475A',
    'border':     '#2A2D3E',
    'selected':   '#1E3A5F',
    # Cluster map colors
    'cl_free':    '#1C2030',
    'cl_used':    '#2A3550',
    'cl_deleted': '#FFD23F',
    'cl_bad':     '#FF3860',
    'cl_recovered':'#00FF9D',
    'cl_pending': '#FF6B35',
    'cl_carved':  '#B794F4',
}

FN  = ('Consolas', 10)
FNS = ('Consolas', 9)
FNB = ('Consolas', 11, 'bold')
FNT = ('Consolas', 14, 'bold')
FNM = ('Courier New', 9)

# ═══════════════════════════════════════════════════════════════
# FILE SIGNATURES  — 22 formats
# ═══════════════════════════════════════════════════════════════
SIGS = {
    'jpg':   (b'\xFF\xD8\xFF',           b'\xFF\xD9',          15_000_000),
    'png':   (b'\x89PNG\r\n\x1a\n',      b'IEND\xAEB`\x82',   20_000_000),
    'gif':   (b'GIF8',                   b'\x00\x3B',          10_000_000),
    'bmp':   (b'BM',                     None,                  5_000_000),
    'tiff':  (b'II*\x00',                None,                 30_000_000),
    'pdf':   (b'%PDF',                   b'%%EOF',             50_000_000),
    'docx':  (b'PK\x03\x04',             b'PK\x05\x06',       30_000_000),
    'xlsx':  (b'PK\x03\x04',             b'PK\x05\x06',       20_000_000),
    'pptx':  (b'PK\x03\x04',             b'PK\x05\x06',       50_000_000),
    'zip':   (b'PK\x03\x04',             b'PK\x05\x06',      100_000_000),
    'rar':   (b'Rar!\x1a\x07',           None,                500_000_000),
    '7z':    (b"7z\xBC\xAF'\x1C",        None,                500_000_000),
    'gz':    (b'\x1f\x8b',              None,                200_000_000),
    'mp4':   (b'\x00\x00\x00\x18ftyp',  None,              2_000_000_000),
    'avi':   (b'RIFF',                  None,              2_000_000_000),
    'mp3':   (b'\xFF\xFB',              None,               20_000_000),
    'wav':   (b'RIFF',                  None,              200_000_000),
    'evtx':  (b'ElfFile\x00',           None,               50_000_000),
    'sqlite':(b'SQLite format 3',       None,              100_000_000),
    'reg':   (b'regf',                  None,               10_000_000),
    'psd':   (b'8BPS',                  None,              500_000_000),
    'wmv':   (b'\x30\x26\xB2\x75',      None,            2_000_000_000),
}

# ═══════════════════════════════════════════════════════════════
# NTFS STRUCTURES
# ═══════════════════════════════════════════════════════════════
class NTFSBoot:
    def __init__(self, data: bytes):
        if data[3:11] != b'NTFS    ':
            raise ValueError(f"OEM: {data[3:11]}")
        self.bps  = struct.unpack_from('<H', data, 0x0B)[0]
        self.spc  = struct.unpack_from('<B', data, 0x0D)[0]
        self.tots = struct.unpack_from('<Q', data, 0x28)[0]
        self.mftc = struct.unpack_from('<Q', data, 0x30)[0]
        self.mfmc = struct.unpack_from('<Q', data, 0x38)[0]
        raw = struct.unpack_from('<b', data, 0x40)[0]
        self.mft_rec_sz = 2**(-raw) if raw < 0 else raw * self.spc * self.bps
        self.cls  = self.bps * self.spc
        self.mft_off = self.mftc * self.cls
        self.mfm_off = self.mfmc * self.cls
        self.total_clusters = self.tots // self.spc

class MFTRecord:
    def __init__(self, data: bytes, num: int):
        self.num=num; self.valid=False; self.deleted=False
        self.is_dir=False; self.names=[]; self.size=0
        self.created=self.modified=None
        self.data_runs=[]; self.resident=None
        self.lcns=set()  # clusters utilisés par ce fichier
        if data[:4] not in (b'FILE', b'BAAD'): return
        d = bytearray(data)
        try:
            uso=struct.unpack_from('<H',d,4)[0]; uss=struct.unpack_from('<H',d,6)[0]
            for i in range(1,uss):
                se=i*512-2
                if se+1<len(d): d[se]=d[uso+i*2]; d[se+1]=d[uso+i*2+1]
        except: pass
        flags=struct.unpack_from('<H',d,22)[0]
        self.deleted=not(flags&1); self.is_dir=bool(flags&2); self.valid=True
        ao=struct.unpack_from('<H',d,20)[0]
        self._attrs(d,ao)

    def _attrs(self,d,off):
        while off<len(d)-4:
            t=struct.unpack_from('<I',d,off)[0]
            if t in(0xFFFFFFFF,0): break
            l=struct.unpack_from('<I',d,off+4)[0]
            if l==0 or off+l>len(d): break
            try:
                if t==0x30: self._fn(d,off)
                elif t==0x10: self._si(d,off)
                elif t==0x80: self._da(d,off)
            except: pass
            off+=l

    def _fn(self,d,off):
        if d[off+8]: return
        co=struct.unpack_from('<H',d,off+20)[0]; ao=off+co
        if ao+66>len(d): return
        nl=d[ao+64]; ns=d[ao+65]
        ns2=ao+66; ne=ns2+nl*2
        if ne>len(d): return
        try: self.names.append((d[ns2:ne].decode('utf-16-le','replace'),ns))
        except: pass

    def _si(self,d,off):
        if d[off+8]: return
        co=struct.unpack_from('<H',d,off+20)[0]; ao=off+co
        if ao+32>len(d): return
        self.created=self._ft(struct.unpack_from('<Q',d,ao)[0])
        self.modified=self._ft(struct.unpack_from('<Q',d,ao+8)[0])

    def _da(self,d,off):
        if not d[off+8]:
            co=struct.unpack_from('<H',d,off+20)[0]
            cs=struct.unpack_from('<I',d,off+16)[0]
            self.size=cs; self.resident=bytes(d[off+co:off+co+cs]); return
        self.size=struct.unpack_from('<Q',d,off+48)[0]
        ro=struct.unpack_from('<H',d,off+32)[0]
        self.data_runs=self._runs(d,off+ro)
        for _,lcn,rlen in self.data_runs:
            if lcn>0:
                for c in range(lcn,lcn+rlen): self.lcns.add(c)

    def _runs(self,d,off):
        runs=[]; vcn=0; lcn=0
        while off<len(d):
            h=d[off]
            if h==0: break
            ls=h&0xF; os2=(h>>4)&0xF; off+=1
            if off+ls+os2>len(d): break
            rl=int.from_bytes(d[off:off+ls],'little'); off+=ls
            if os2>0:
                rb=d[off:off+os2]; delta=int.from_bytes(rb,'little')
                if rb[-1]&0x80: delta-=(1<<(os2*8))
                lcn+=delta
            off+=os2; runs.append((vcn,lcn,rl)); vcn+=rl
        return runs

    @staticmethod
    def _ft(v):
        if not v: return None
        try: return datetime.fromtimestamp((v-116444736000000000)/1e7,tz=timezone.utc)
        except: return None

    @property
    def name(self):
        for n,ns in self.names:
            if ns==1: return n
        return self.names[0][0] if self.names else f'[#{self.num}]'

# ═══════════════════════════════════════════════════════════════
# PHYSICAL DRIVE ACCESS + MAJORITY VOTING
# ═══════════════════════════════════════════════════════════════
class PhysicalReader:
    """Lecture directe bypass filesystem — Windows + Linux"""

    def __init__(self, path: str, sector_size=512):
        self.path = path
        self.ss   = sector_size
        self.bad_sectors = set()
        self.recovered_sectors = set()
        self._handle = None

    def _open_win(self, path):
        if not IS_WINDOWS: return None
        try:
            h = ctypes.windll.kernel32.CreateFileW(
                path, 0x80000000, 0x3, None, 3, 0x20000000, None)
            return h if h != ctypes.c_void_p(-1).value else None
        except: return None

    def read_sector(self, lba: int, retries: int = 8) -> bytes | None:
        """Lecture avec retry intelligent"""
        if IS_WINDOWS:
            return self._read_win(lba, retries)
        else:
            return self._read_file(lba, retries)

    def _read_file(self, lba: int, retries: int) -> bytes | None:
        for attempt in range(retries):
            try:
                with open(self.path, 'rb') as f:
                    f.seek(lba * self.ss)
                    data = f.read(self.ss)
                    if len(data) == self.ss:
                        self.recovered_sectors.add(lba)
                        return data
            except OSError:
                time.sleep(0.02 * (attempt + 1))
        self.bad_sectors.add(lba)
        return None

    def _read_win(self, lba: int, retries: int) -> bytes | None:
        reads = []
        for attempt in range(retries):
            try:
                h = self._open_win(self.path)
                if h is None: return self._read_file(lba, 1)
                offset = lba * self.ss
                hi = ctypes.c_long(offset >> 32)
                ctypes.windll.kernel32.SetFilePointer(h, offset & 0xFFFFFFFF, ctypes.byref(hi), 0)
                buf  = ctypes.create_string_buffer(self.ss)
                read = ctypes.c_ulong(0)
                ok   = ctypes.windll.kernel32.ReadFile(h, buf, self.ss, ctypes.byref(read), None)
                ctypes.windll.kernel32.CloseHandle(h)
                if ok and read.value == self.ss:
                    reads.append(bytes(buf))
                    if attempt == 0:  # Premier essai réussi
                        self.recovered_sectors.add(lba)
                        return reads[0]
            except:
                pass
            time.sleep(0.03 * (attempt + 1))

        if reads:
            result = self._majority_vote(reads)
            self.recovered_sectors.add(lba)
            return result
        self.bad_sectors.add(lba)
        return None

    def _majority_vote(self, reads: list) -> bytes:
        """Vote majoritaire bit à bit — technique forensique pro"""
        if len(reads) == 1: return reads[0]
        result = bytearray(self.ss)
        for i in range(self.ss):
            votes = [r[i] for r in reads if i < len(r)]
            result[i] = max(set(votes), key=votes.count) if votes else 0
        return bytes(result)

    def read_sectors_range(self, start: int, count: int, progress_cb=None) -> dict:
        """Lire une plage de secteurs, retourne {lba: data|None}"""
        results = {}
        for i, lba in enumerate(range(start, start + count)):
            results[lba] = self.read_sector(lba)
            if progress_cb and i % 100 == 0:
                progress_cb(i, count, len(self.bad_sectors))
        return results

# ═══════════════════════════════════════════════════════════════
# RECOVERY ENGINE
# ═══════════════════════════════════════════════════════════════
class RecoveryEngine:
    def __init__(self, source: str, output: str, offset_sectors: int = 0,
                 use_physical: bool = False, log_cb=None, progress_cb=None,
                 file_cb=None, cluster_cb=None):
        self.src     = source
        self.out     = Path(output)
        self.off     = offset_sectors
        self.phys    = use_physical
        self.log     = log_cb or print
        self.prog    = progress_cb or (lambda *a: None)
        self.file_cb = file_cb or (lambda *a: None)
        self.cl_cb   = cluster_cb or (lambda *a: None)
        self.running = True
        self.boot    = None
        self.reader  = PhysicalReader(source)
        self.cluster_map = {}  # lcn -> status string
        self.stats = dict(mft_total=0, mft_deleted=0, recovered=0,
                         carved=0, bad_sectors=0, recovered_sectors=0,
                         bytes_recovered=0, partial=0)
        for d in ('recovered','carved','partial','reports'):
            (self.out/d).mkdir(parents=True, exist_ok=True)

    def stop(self): self.running = False

    # ── BOOT ──────────────────────────────────────────────
    def detect_boot(self) -> bool:
        data = self._read_raw(self.off * 512, 512)
        if data:
            try:
                self.boot = NTFSBoot(data)
                self.log(f"✓ NTFS Boot sector OK", 'ok')
                self.log(f"  Cluster size     : {self.boot.cls} bytes", 'info')
                self.log(f"  Total clusters   : {self.boot.total_clusters:,}", 'info')
                self.log(f"  MFT offset       : 0x{self.boot.mft_off:X}", 'info')
                self.log(f"  Secteurs/cluster : {self.boot.spc}", 'info')
                return True
            except ValueError as e:
                self.log(f"⚠ Boot illisible: {e} — recherche en cours...", 'warn')
        return self._find_ntfs()

    def _find_ntfs(self) -> bool:
        self.log("  Scan des 4096 premiers secteurs...", 'info')
        for s in range(self.off, self.off + 4096):
            if not self.running: return False
            d = self._read_raw(s * 512, 512)
            if d and d[3:11] == b'NTFS    ' and d[510:512] == b'\x55\xAA':
                try:
                    self.boot = NTFSBoot(d)
                    self.off  = s
                    self.log(f"✓ NTFS trouvé au secteur {s}", 'ok')
                    return True
                except: pass
        self.log("✗ Aucune partition NTFS trouvée", 'err')
        return False

    # ── MFT SCAN ──────────────────────────────────────────
    def scan_mft(self, extract: bool = True):
        if not self.boot: return
        b    = self.boot
        base = self.off * 512 + b.mft_off
        rsz  = int(b.mft_rec_sz)
        if rsz <= 0: rsz = 1024
        img_sz = self._image_size()
        max_r  = min((img_sz - base) // rsz, 10_000_000)

        self.log(f"\n{'─'*50}", 'sep')
        self.log(f"📋  SCAN MFT — {int(max_r):,} records max", 'title')
        self.log(f"    Base: 0x{base:X}  RecSize: {rsz}B", 'info')

        for i in range(int(max_r)):
            if not self.running: break
            raw = self._read_raw(base + i * rsz, rsz)
            if not raw: continue
            r = MFTRecord(raw, i)
            if not r.valid: continue
            self.stats['mft_total'] += 1

            # ── SKIP fichiers existants (actifs) ──────────
            if not r.deleted:
                # Marquer clusters comme "used" sur la carte
                for lcn in r.lcns:
                    self.cluster_map[lcn] = 'used'
                continue   # ← ON IGNORE TOUT CE QUI EXISTE

            if r.is_dir: continue

            self.stats['mft_deleted'] += 1
            # Marquer clusters deleted sur la carte
            for lcn in r.lcns:
                if self.cluster_map.get(lcn) != 'bad':
                    self.cluster_map[lcn] = 'deleted'
            self.cl_cb(self.cluster_map)

            entry = {
                'num':    i,
                'name':   r.name,
                'size':   r.size,
                'date':   str(r.modified)[:19] if r.modified else '',
                'method': 'MFT',
                'status': 'detected',
                'path':   None,
                'partial': False,
            }

            if extract and r.size > 0:
                path, partial = self._extract(r, b)
                if path:
                    entry['path']    = str(path)
                    entry['status']  = 'partial' if partial else 'recovered'
                    entry['partial'] = partial
                    self.stats['recovered'] += 1
                    self.stats['bytes_recovered'] += r.size
                    if partial: self.stats['partial'] += 1
                    for lcn in r.lcns:
                        self.cluster_map[lcn] = 'recovered'
                    self.cl_cb(self.cluster_map)

            self.file_cb(entry)

            if i % 2000 == 0:
                pct = min(50, i / max(max_r, 1) * 50)
                self.prog(pct, f"MFT {i:,}/{int(max_r):,} — {self.stats['mft_deleted']} supprimés")
                self.stats['bad_sectors'] = len(self.reader.bad_sectors)

        self.log(f"✓ MFT: {self.stats['mft_total']:,} records, "
                 f"{self.stats['mft_deleted']:,} supprimés, "
                 f"{self.stats['recovered']:,} récupérés", 'ok')

    def _extract(self, r: MFTRecord, b: NTFSBoot):
        safe = ''.join(c if c.isalnum() or c in '._- ' else '_' for c in r.name)[:60]
        folder = self.out / ('partial' if False else 'recovered')
        path   = folder / f"{r.num}_{safe}"
        partial = False
        try:
            if r.resident is not None:
                path.write_bytes(r.resident); return path, False
            if not r.data_runs: return None, False
            with open(path, 'wb') as f:
                written = 0
                for vcn, lcn, rlen in r.data_runs:
                    if not self.running: break
                    if lcn == 0:
                        gap = min(rlen * b.cls, r.size - written)
                        f.write(b'\x00' * int(gap)); written += int(gap); continue
                    for cl in range(lcn, lcn + rlen):
                        if not self.running: break
                        if written >= r.size: break
                        cl_off = self.off * 512 + cl * b.cls
                        chunk  = self._read_raw_retry(cl_off, b.cls)
                        if chunk:
                            to_w = min(len(chunk), r.size - written)
                            f.write(chunk[:int(to_w)]); written += int(to_w)
                            self.cluster_map[cl] = 'recovered'
                        else:
                            # Cluster bad — écrire des zéros + marquer
                            gap = min(b.cls, r.size - written)
                            f.write(b'\x00' * int(gap)); written += int(gap)
                            self.cluster_map[cl] = 'bad'
                            partial = True
                            self.stats['bad_sectors'] += b.spc
            return path, partial
        except Exception as e:
            return None, False

    # ── FILE CARVING ──────────────────────────────────────
    def carve(self, extract: bool = True):
        img_sz  = self._image_size()
        chunk_s = 2 * 1024 * 1024
        self.log(f"\n{'─'*50}", 'sep')
        self.log(f"🔍  FILE CARVING — {img_sz/1e9:.2f} GB", 'title')

        counts = {ext: 0 for ext in SIGS}
        with open(self.src, 'rb') as f:
            offset = 0
            buf    = b''
            while offset < img_sz and self.running:
                chunk = f.read(chunk_s)
                if not chunk: break
                buf = buf[-128:] + chunk
                for ext, (hdr, ftr, maxsz) in SIGS.items():
                    pos = 0
                    while True:
                        idx = buf.find(hdr, pos)
                        if idx == -1: break
                        abs_pos = offset - len(buf) + 128 + idx
                        if abs_pos < 0: pos = idx+1; continue
                        if extract:
                            p = self._carve_one(f, abs_pos, hdr, ftr, maxsz, ext)
                            if p:
                                counts[ext] += 1
                                self.stats['carved'] += 1
                                entry = {
                                    'num': abs_pos, 'name': p.name,
                                    'size': p.stat().st_size,
                                    'date': '', 'method': 'CARVE',
                                    'status': 'carved', 'path': str(p), 'partial': False
                                }
                                self.file_cb(entry)
                                # Marquer clusters sur la carte
                                start_cl = abs_pos // self.boot.cls if self.boot else 0
                                end_cl   = (abs_pos + p.stat().st_size) // self.boot.cls if self.boot else 0
                                for c in range(start_cl, min(end_cl+1, start_cl+1000)):
                                    if self.cluster_map.get(c) == 'deleted':
                                        self.cluster_map[c] = 'carved'
                                self.cl_cb(self.cluster_map)
                        pos = idx + 1
                offset += len(chunk)
                pct = 50 + min(50, offset / img_sz * 50)
                self.prog(pct, f"Carving {offset/1e9:.2f}/{img_sz/1e9:.2f} GB — {self.stats['carved']} trouvés")

        for ext, n in counts.items():
            if n > 0:
                self.log(f"  {ext.upper():8}: {n:4} fichier(s)", 'ok')

    def _carve_one(self, f, offset: int, hdr, ftr, maxsz: int, ext: str):
        try:
            f.seek(offset)
            data = f.read(min(maxsz, 30*1024*1024))
            if not data.startswith(hdr): return None
            if ftr:
                e = data.find(ftr)
                if e != -1: data = data[:e+len(ftr)]
            if len(data) < len(hdr)+4: return None
            h = hashlib.md5(data[:512]).hexdigest()[:6]
            p = self.out / 'carved' / f"{offset:016X}_{h}.{ext}"
            p.write_bytes(data); return p
        except: return None

    # ── BAD SECTOR SCAN ───────────────────────────────────
    def scan_bad_sectors(self, sample_step: int = 64):
        """Scan rapide des secteurs défaillants par échantillonnage"""
        if not self.boot: return
        img_sz  = self._image_size()
        total_s = img_sz // 512
        self.log(f"\n{'─'*50}", 'sep')
        self.log(f"🩺  SCAN SECTEURS — 1 sur {sample_step} ({total_s//sample_step:,} tests)", 'title')

        bad = 0
        tested = 0
        for lba in range(0, total_s, sample_step):
            if not self.running: break
            d = self._read_raw(lba * 512, 512)
            tested += 1
            if d is None:
                bad += 1
                self.stats['bad_sectors'] += 1
                if self.boot:
                    cl = lba // self.boot.spc
                    self.cluster_map[cl] = 'bad'
            if tested % 500 == 0:
                pct = min(100, tested / (total_s // sample_step) * 100)
                self.prog(pct, f"Scan secteurs: {tested:,} testés — {bad} bad sectors")
                self.cl_cb(self.cluster_map)

        self.log(f"✓ {bad} bad sectors détectés sur {tested:,} testés", 'warn' if bad else 'ok')

    # ── RAPPORT ───────────────────────────────────────────
    def save_report(self, results: list):
        ts  = datetime.now().strftime('%Y%m%d_%H%M%S')
        jp  = self.out / 'reports' / f'report_{ts}.json'
        tp  = self.out / 'reports' / f'report_{ts}.txt'

        with open(jp,'w',encoding='utf-8') as f:
            json.dump({'stats':self.stats,'files':results}, f, indent=2, default=str)

        with open(tp,'w',encoding='utf-8') as f:
            f.write("PHANTOM RECOVER — RAPPORT D'ANALYSE\n")
            f.write("="*60+"\n")
            f.write(f"Date    : {datetime.now()}\n")
            f.write(f"Source  : {self.src}\n")
            f.write(f"Output  : {self.out}\n\n")
            f.write("STATISTIQUES:\n")
            for k,v in self.stats.items():
                f.write(f"  {k:25}: {v:,}\n")
            f.write(f"\n{'─'*60}\n")
            f.write(f"{'#':>8}  {'Statut':12}  {'Taille':>12}  {'Méthode':8}  Nom\n")
            f.write("─"*90+"\n")
            for r in results:
                st = '⚠ PARTIEL' if r.get('partial') else ('✓ OK' if r.get('path') else '◎ DÉTECTÉ')
                f.write(f"{r['num']:>8}  {st:12}  {self._fmtsz(r['size']):>12}  {r['method']:8}  {r['name']}\n")
        return jp, tp

    # ── HELPERS ───────────────────────────────────────────
    def _read_raw(self, offset: int, size: int) -> bytes | None:
        try:
            with open(self.src,'rb') as f:
                f.seek(offset); d=f.read(size)
                return d if len(d)==size else None
        except: return None

    def _read_raw_retry(self, offset: int, size: int, retries: int = 6) -> bytes | None:
        reads = []
        for attempt in range(retries):
            d = self._read_raw(offset, size)
            if d:
                reads.append(d)
                if attempt == 0: return d
            time.sleep(0.01 * (attempt+1))
        if reads:
            # Majority vote
            result = bytearray(size)
            for i in range(size):
                votes = [r[i] for r in reads if i < len(r)]
                result[i] = max(set(votes), key=votes.count) if votes else 0
            return bytes(result)
        self.reader.bad_sectors.add(offset // 512)
        return None

    def _image_size(self) -> int:
        try: return os.path.getsize(self.src)
        except: return 0

    @staticmethod
    def _fmtsz(s):
        if not s: return '0 B'
        for u in ['B','KB','MB','GB']:
            if s < 1024: return f"{s:.1f} {u}"
            s /= 1024
        return f"{s:.1f} TB"


# ═══════════════════════════════════════════════════════════════
# CLUSTER MAP WIDGET
# ═══════════════════════════════════════════════════════════════
class ClusterMap(Canvas):
    CELL = 6
    COLORS = {
        'free':      C['cl_free'],
        'used':      C['cl_used'],
        'deleted':   C['cl_deleted'],
        'bad':       C['cl_bad'],
        'recovered': C['cl_recovered'],
        'pending':   C['cl_pending'],
        'carved':    C['cl_carved'],
    }

    def __init__(self, parent, total_clusters=100000, **kw):
        super().__init__(parent, bg=C['bg2'], highlightthickness=0, **kw)
        self.total = total_clusters
        self.data  = {}
        self.bind('<Configure>', self._redraw)
        self._tooltip = None

    def update_map(self, cluster_map: dict):
        self.data = cluster_map
        self._redraw()

    def _redraw(self, event=None):
        self.delete('all')
        w = self.winfo_width()
        if w < 10: return
        cols   = max(1, w // (self.CELL + 1))
        rows   = max(1, self.total // cols + 1)
        new_h  = rows * (self.CELL + 1) + 4
        self.config(height=min(new_h, 200))

        for lcn in range(min(self.total, cols * rows)):
            status = self.data.get(lcn, 'free')
            color  = self.COLORS.get(status, C['cl_free'])
            col    = lcn % cols
            row    = lcn // cols
            x1 = 2 + col * (self.CELL+1)
            y1 = 2 + row * (self.CELL+1)
            self.create_rectangle(x1, y1, x1+self.CELL, y1+self.CELL,
                                  fill=color, outline='', tags=f'cl_{lcn}')


# ═══════════════════════════════════════════════════════════════
# MAIN APPLICATION
# ═══════════════════════════════════════════════════════════════
class PhantomRecover(Tk):
    def __init__(self):
        super().__init__()
        self.title("PHANTOM RECOVER  —  Deep NTFS Recovery")
        self.geometry("1280x800")
        self.minsize(1000, 650)
        self.configure(bg=C['bg'])

        # State
        self.src_var   = StringVar()
        self.out_var   = StringVar(value=str(Path.home()/'PhantomRecover'))
        self.off_var   = StringVar(value='0')
        self.do_mft    = BooleanVar(value=True)
        self.do_carve  = BooleanVar(value=True)
        self.do_bad    = BooleanVar(value=True)
        self.do_ext    = BooleanVar(value=True)
        self.q         = queue.Queue()
        self.running   = False
        self.engine    = None
        self.results   = []
        self._sort_col = None
        self._sort_rev = False

        self._mk_style()
        self._mk_ui()
        self._poll()

    # ── STYLE ─────────────────────────────────────────────
    def _mk_style(self):
        s = ttk.Style(self)
        s.theme_use('clam')
        s.configure('.',              background=C['bg'],   foreground=C['text'],  font=FN)
        s.configure('TFrame',         background=C['bg'])
        s.configure('TLabel',         background=C['bg'],   foreground=C['text'])
        s.configure('TLabelframe',    background=C['bg2'],  foreground=C['accent'],
                    relief='flat', borderwidth=1)
        s.configure('TLabelframe.Label', background=C['bg2'], foreground=C['accent'],
                    font=('Consolas',9,'bold'))
        s.configure('TProgressbar',   troughcolor=C['bg3'], background=C['accent'], thickness=5)
        s.configure('Treeview',       background=C['bg2'],  foreground=C['text'],
                    fieldbackground=C['bg2'], rowheight=21, borderwidth=0, font=FNM)
        s.configure('Treeview.Heading', background=C['bg4'], foreground=C['accent'],
                    font=('Consolas',9,'bold'), relief='flat')
        s.map('Treeview', background=[('selected',C['selected'])], foreground=[('selected',C['accent'])])
        s.configure('TNotebook',       background=C['bg'],  borderwidth=0)
        s.configure('TNotebook.Tab',   background=C['bg3'], foreground=C['text2'],
                    padding=(12,5), font=FNS)
        s.map('TNotebook.Tab', background=[('selected',C['bg2'])], foreground=[('selected',C['accent'])])

    # ── UI BUILD ──────────────────────────────────────────
    def _mk_ui(self):
        # HEADER
        hdr = Frame(self, bg=C['panel'], height=54)
        hdr.pack(fill=X); hdr.pack_propagate(False)
        Frame(hdr, bg=C['accent'], width=4).pack(side=LEFT, fill=Y)
        Label(hdr, text=" ◈ PHANTOM RECOVER", font=('Consolas',16,'bold'),
              bg=C['panel'], fg=C['accent']).pack(side=LEFT, padx=14, pady=12)
        Label(hdr, text="Deep NTFS Recovery  •  Majority Voting  •  Cluster Map  •  Windows 10/11",
              font=FNS, bg=C['panel'], fg=C['text2']).pack(side=LEFT, padx=4)
        Label(hdr, text="v3.0 PRO", font=FNS, bg=C['panel'], fg=C['text3']).pack(side=RIGHT, padx=16)

        # MAIN
        main = Frame(self, bg=C['bg'])
        main.pack(fill=BOTH, expand=True, padx=10, pady=8)

        # LEFT — config 280px
        left = Frame(main, bg=C['bg'], width=282)
        left.pack(side=LEFT, fill=Y, padx=(0,8))
        left.pack_propagate(False)
        self._mk_left(left)

        # RIGHT — results
        right = Frame(main, bg=C['bg'])
        right.pack(side=LEFT, fill=BOTH, expand=True)
        self._mk_right(right)

        # STATUSBAR
        sb = Frame(self, bg=C['bg4'], height=26)
        sb.pack(fill=X, side=BOTTOM); sb.pack_propagate(False)
        Frame(sb, bg=C['accent'], width=3).pack(side=LEFT, fill=Y)
        self.sv_status = StringVar(value="Prêt — Sélectionnez une image disque ou un disque physique")
        Label(sb, textvariable=self.sv_status, font=FNS,
              bg=C['bg4'], fg=C['text2']).pack(side=LEFT, padx=8, pady=4)
        self.sv_count = StringVar(value="0 fichiers")
        Label(sb, textvariable=self.sv_count, font=FNS,
              bg=C['bg4'], fg=C['green']).pack(side=RIGHT, padx=12, pady=4)

    def _mk_left(self, p):
        # SOURCE
        f1 = ttk.LabelFrame(p, text=" SOURCE ", padding=8)
        f1.pack(fill=X, pady=(0,6))

        Label(f1, text="Image / Disque physique:", font=FNS, bg=C['bg2'], fg=C['text2']).pack(anchor=W)
        r = Frame(f1, bg=C['bg2']); r.pack(fill=X, pady=3)
        Entry(r, textvariable=self.src_var, bg=C['bg3'], fg=C['text'],
              insertbackground=C['accent'], relief='flat', font=FNM,
              bd=0, highlightthickness=1, highlightcolor=C['accent'],
              highlightbackground=C['border']).pack(side=LEFT, fill=X, expand=True)
        self._btn(r, "📂", self._br_img, small=True).pack(side=RIGHT, padx=(3,0))

        if IS_WINDOWS:
            Label(f1, text="Ou disque physique:", font=FNS, bg=C['bg2'], fg=C['text2']).pack(anchor=W, pady=(5,0))
            r2 = Frame(f1, bg=C['bg2']); r2.pack(fill=X, pady=2)
            self.phys_var = StringVar()
            drives = self._list_drives()
            cb = ttk.Combobox(r2, textvariable=self.phys_var, values=drives,
                              font=FNS, state='readonly', width=22)
            cb.pack(side=LEFT, fill=X, expand=True)
            self._btn(r2, "→", self._use_drive, small=True).pack(side=RIGHT, padx=(3,0))

        Label(f1, text="Offset partition (secteurs):", font=FNS, bg=C['bg2'], fg=C['text2']).pack(anchor=W, pady=(5,0))
        Entry(f1, textvariable=self.off_var, bg=C['bg3'], fg=C['text'],
              insertbackground=C['accent'], relief='flat', font=FNM,
              bd=0, highlightthickness=1, highlightcolor=C['accent'],
              highlightbackground=C['border'], width=12).pack(anchor=W, pady=2)

        # DESTINATION
        f2 = ttk.LabelFrame(p, text=" DESTINATION ", padding=8)
        f2.pack(fill=X, pady=(0,6))
        r3 = Frame(f2, bg=C['bg2']); r3.pack(fill=X)
        Entry(r3, textvariable=self.out_var, bg=C['bg3'], fg=C['text'],
              insertbackground=C['accent'], relief='flat', font=FNM,
              bd=0, highlightthickness=1, highlightcolor=C['accent'],
              highlightbackground=C['border']).pack(side=LEFT, fill=X, expand=True)
        self._btn(r3, "📁", self._br_out, small=True).pack(side=RIGHT, padx=(3,0))

        # OPTIONS
        f3 = ttk.LabelFrame(p, text=" OPTIONS ", padding=8)
        f3.pack(fill=X, pady=(0,6))
        opts = [
            (self.do_bad,   "🩺  Scan bad sectors",        C['red']),
            (self.do_mft,   "📋  Analyse MFT (deleted only)",C['yellow']),
            (self.do_carve, "🔍  File Carving (22 formats)", C['accent']),
            (self.do_ext,   "💾  Extraire les fichiers",    C['green']),
        ]
        for var, lbl, col in opts:
            tk.Checkbutton(f3, text=lbl, variable=var,
                           bg=C['bg2'], fg=col, selectcolor=C['bg3'],
                           activebackground=C['bg2'], activeforeground=col,
                           font=FNS, cursor='hand2').pack(anchor=W, pady=1)

        # ACTIONS
        f4 = Frame(p, bg=C['bg']); f4.pack(fill=X, pady=(0,6))
        self.btn_go   = self._btn(f4, "▶  LANCER L'ANALYSE",   self._start)
        self.btn_go.pack(fill=X, pady=(0,3))
        self.btn_stop = self._btn(f4, "⏹  ARRÊTER",            self._stop, C['red'])
        self.btn_stop.pack(fill=X, pady=(0,3)); self.btn_stop.config(state=DISABLED)
        self._btn(f4, "💾  SAUVEGARDER RAPPORT", self._save_report, C['text2']).pack(fill=X)

        # PROGRESS
        f5 = ttk.LabelFrame(p, text=" PROGRESSION ", padding=8)
        f5.pack(fill=X, pady=(0,6))
        self.pv = tk.DoubleVar()
        ttk.Progressbar(f5, variable=self.pv, maximum=100).pack(fill=X, pady=(0,4))
        self.plbl = Label(f5, text="En attente...", font=FNS, bg=C['bg2'], fg=C['text2'])
        self.plbl.pack(anchor=W)

        # MINI STATS
        f6 = Frame(f5, bg=C['bg2']); f6.pack(fill=X, pady=(6,0))
        self.svars = {}
        for k, lbl, col in [
            ('mft_total',  'Records MFT',  C['text2']),
            ('mft_deleted','Supprimés',    C['yellow']),
            ('recovered',  'Récupérés',    C['green']),
            ('partial',    'Partiels',     C['orange']),
            ('carved',     'Carved',       C['purple']),
            ('bad_sectors','Bad sectors',  C['red']),
        ]:
            rr = Frame(f6, bg=C['bg2']); rr.pack(fill=X, pady=1)
            Label(rr, text=f"{lbl}:", font=FNS, bg=C['bg2'], fg=C['text2'],
                  width=14, anchor=W).pack(side=LEFT)
            v = StringVar(value='0'); self.svars[k] = v
            Label(rr, textvariable=v, font=FNS, bg=C['bg2'], fg=col).pack(side=LEFT)

    def _mk_right(self, p):
        nb = ttk.Notebook(p); nb.pack(fill=BOTH, expand=True)

        # TAB 1 — Fichiers
        t1 = Frame(nb, bg=C['bg']); nb.add(t1, text="  📁 FICHIERS RÉCUPÉRÉS  ")
        # toolbar
        tb = Frame(t1, bg=C['bg4'], height=34); tb.pack(fill=X); tb.pack_propagate(False)
        Label(tb, text="🔍", font=FNS, bg=C['bg4'], fg=C['text2']).pack(side=LEFT, padx=(8,2), pady=6)
        self.flt = StringVar(); self.flt.trace('w', self._filter)
        Entry(tb, textvariable=self.flt, bg=C['bg3'], fg=C['text'],
              insertbackground=C['accent'], relief='flat', font=FNM,
              bd=0, width=20).pack(side=LEFT, pady=6)
        # filter buttons
        for lbl, tag, col in [('Tous','all',C['text2']),('MFT','MFT',C['yellow']),
                               ('Carved','CARVE',C['purple']),('Partiels','partial',C['orange'])]:
            self._btn(tb, lbl, lambda t=tag: self._filter_by(t), small=True, color=col).pack(side=LEFT, padx=3, pady=5)
        self._btn(tb, "💾 Extraire sélection", self._extract_sel, small=True).pack(side=RIGHT, padx=8, pady=5)
        self._btn(tb, "☑ Tout", self._sel_all, small=True).pack(side=RIGHT, padx=2, pady=5)

        # treeview
        cols = ('num','nom','taille','type','statut','date','methode')
        self.tree = ttk.Treeview(t1, columns=cols, show='headings', selectmode='extended')
        for col, hdr, w, anchor in [
            ('num',    '#',          55,  'center'),
            ('nom',    'Nom fichier', 290, 'w'),
            ('taille', 'Taille',      90,  'center'),
            ('type',   'Type',        55,  'center'),
            ('statut', 'Statut',      95,  'center'),
            ('date',   'Date',        155, 'center'),
            ('methode','Méthode',     75,  'center'),
        ]:
            self.tree.heading(col, text=hdr, command=lambda c=col: self._sort(c))
            self.tree.column(col, width=w, anchor=anchor)

        self.tree.tag_configure('deleted',   foreground=C['yellow'])
        self.tree.tag_configure('carved',    foreground=C['purple'])
        self.tree.tag_configure('recovered', foreground=C['green'])
        self.tree.tag_configure('partial',   foreground=C['orange'])
        self.tree.tag_configure('detected',  foreground=C['text2'])

        vsb = ttk.Scrollbar(t1, orient=VERTICAL,   command=self.tree.yview)
        hsb = ttk.Scrollbar(t1, orient=HORIZONTAL, command=self.tree.xview)
        self.tree.configure(yscrollcommand=vsb.set, xscrollcommand=hsb.set)
        vsb.pack(side=RIGHT, fill=Y)
        self.tree.pack(side=TOP, fill=BOTH, expand=True)
        hsb.pack(side=BOTTOM, fill=X)

        # TAB 2 — Cluster Map
        t2 = Frame(nb, bg=C['bg']); nb.add(t2, text="  🗺️ CARTE CLUSTERS  ")
        self._mk_cluster_tab(t2)

        # TAB 3 — Log
        t3 = Frame(nb, bg=C['bg']); nb.add(t3, text="  📋 LOG  ")
        self.log_w = Text(t3, bg=C['bg2'], fg=C['text'], font=FNM,
                          insertbackground=C['accent'], relief='flat',
                          wrap=WORD, state=DISABLED)
        lsb = ttk.Scrollbar(t3, command=self.log_w.yview)
        self.log_w.configure(yscrollcommand=lsb.set)
        lsb.pack(side=RIGHT, fill=Y); self.log_w.pack(fill=BOTH, expand=True)
        for tag, col, bold in [
            ('title',  C['accent'],  True),
            ('ok',     C['green'],   False),
            ('warn',   C['yellow'],  False),
            ('err',    C['red'],     False),
            ('info',   C['text2'],   False),
            ('sep',    C['text3'],   False),
        ]:
            f = ('Consolas',9,'bold') if bold else FNS
            self.log_w.tag_configure(tag, foreground=col, font=f)

        # TAB 4 — Stats
        t4 = Frame(nb, bg=C['bg']); nb.add(t4, text="  📊 STATS  ")
        self.stats_w = Text(t4, bg=C['bg2'], fg=C['text'], font=FNM,
                            relief='flat', state=DISABLED)
        self.stats_w.pack(fill=BOTH, expand=True)

    def _mk_cluster_tab(self, parent):
        # Legend
        leg = Frame(parent, bg=C['bg3'], height=32)
        leg.pack(fill=X); leg.pack_propagate(False)
        Label(leg, text="CARTE DES CLUSTERS:", font=FNS, bg=C['bg3'], fg=C['text2']).pack(side=LEFT, padx=8, pady=6)
        for lbl, col in [('Libre',C['cl_free']),('Utilisé',C['cl_used']),
                          ('Supprimé',C['cl_deleted']),('Bad',C['cl_bad']),
                          ('Récupéré',C['cl_recovered']),('Partiel',C['cl_pending']),
                          ('Carved',C['cl_carved'])]:
            Frame(leg, bg=col, width=12, height=12).pack(side=LEFT, padx=(8,2), pady=10)
            Label(leg, text=lbl, font=FNS, bg=C['bg3'], fg=C['text2']).pack(side=LEFT, padx=(0,4), pady=6)

        # Scrollable cluster map
        frame = Frame(parent, bg=C['bg2'])
        frame.pack(fill=BOTH, expand=True, padx=4, pady=4)
        scr = ttk.Scrollbar(frame, orient=VERTICAL)
        scr.pack(side=RIGHT, fill=Y)
        self.cl_map = ClusterMap(frame, total_clusters=50000)
        self.cl_map.pack(fill=BOTH, expand=True)

        # Stats under map
        sf = Frame(parent, bg=C['bg3'], height=28)
        sf.pack(fill=X); sf.pack_propagate(False)
        self.cl_stats = StringVar(value="En attente...")
        Label(sf, textvariable=self.cl_stats, font=FNS,
              bg=C['bg3'], fg=C['text2']).pack(side=LEFT, padx=8, pady=5)

    # ── WIDGETS ───────────────────────────────────────────
    def _btn(self, parent, text, cmd, color=None, small=False):
        c = color or C['accent']
        f = FNS if small else FNB
        py = 3 if small else 7
        b = tk.Button(parent, text=text, command=cmd,
                      bg=C['bg3'], fg=c, activebackground=C['bg4'],
                      activeforeground=c, relief='flat', bd=0,
                      font=f, cursor='hand2', padx=8, pady=py)
        b.bind('<Enter>', lambda e: b.config(bg=C['bg4']))
        b.bind('<Leave>', lambda e: b.config(bg=C['bg3']))
        return b

    # ── BROWSE ────────────────────────────────────────────
    def _br_img(self):
        p = filedialog.askopenfilename(
            title="Image disque",
            filetypes=[("Images","*.dd *.img *.raw *.bin *.iso"),("Tous","*.*")])
        if p: self.src_var.set(p)

    def _br_out(self):
        p = filedialog.askdirectory(title="Dossier destination")
        if p: self.out_var.set(p)

    def _list_drives(self):
        drives = []
        if IS_WINDOWS:
            for i in range(8):
                drives.append(f"\\\\.\\PhysicalDrive{i}")
        return drives

    def _use_drive(self):
        d = self.phys_var.get() if hasattr(self,'phys_var') else ''
        if d: self.src_var.set(d)

    # ── SCAN CONTROL ──────────────────────────────────────
    def _start(self):
        src = self.src_var.get().strip()
        if not src:
            messagebox.showerror("Erreur", "Sélectionnez une image ou un disque."); return
        if not src.startswith('\\\\.\\') and not Path(src).exists():
            messagebox.showerror("Erreur", f"Source introuvable:\n{src}"); return

        self.running = True
        self.results.clear()
        for item in self.tree.get_children(): self.tree.delete(item)
        self.btn_go.config(state=DISABLED)
        self.btn_stop.config(state=NORMAL)
        self.pv.set(0)
        for v in self.svars.values(): v.set('0')

        threading.Thread(target=self._run, daemon=True).start()

    def _stop(self):
        self.running = False
        if self.engine: self.engine.stop()
        self._log("⏹ Arrêt demandé...", 'warn')

    def _run(self):
        src = self.src_var.get().strip()
        out = self.out_var.get().strip()
        off = int(self.off_var.get() or 0)
        ext = self.do_ext.get()

        self._log("="*55, 'sep')
        self._log(" PHANTOM RECOVER — Analyse démarrée", 'title')
        self._log("="*55, 'sep')
        self._log(f"Source : {src}", 'info')
        self._log(f"Output : {out}", 'info')
        self._log(f"Offset : {off} secteurs", 'info')
        self._log(f"OS     : {platform.system()} {platform.release()}", 'info')

        self.engine = RecoveryEngine(
            src, out, off,
            log_cb      = lambda t, tag='info': self._log(t, tag),
            progress_cb = lambda p, l: self.q.put(('prog', (p, l))),
            file_cb     = lambda e: self.q.put(('file', e)),
            cluster_cb  = lambda m: self.q.put(('clusters', m)),
        )

        # Boot
        if not self.engine.detect_boot():
            self._log("Impossible de trouver NTFS. Carving seul...", 'warn')

        # Bad sector scan
        if self.do_bad.get() and self.running:
            self.engine.scan_bad_sectors()

        # MFT
        if self.do_mft.get() and self.running:
            self.engine.scan_mft(extract=ext)

        # Carving
        if self.do_carve.get() and self.running:
            self.engine.carve(extract=ext)

        # Rapport
        jp, tp = self.engine.save_report(self.results)
        self._log(f"\n✓ Rapport sauvegardé:", 'ok')
        self._log(f"  {tp}", 'info')
        self._log("="*55, 'sep')

        # Update stats tab
        self.q.put(('stats_done', self.engine.stats))
        self.q.put(('done', len(self.results)))

    # ── QUEUE POLL ────────────────────────────────────────
    def _poll(self):
        try:
            while True:
                msg, data = self.q.get_nowait()
                if msg == 'log':
                    tag, text = data
                    self._append_log(text, tag)
                elif msg == 'file':
                    self._add_row(data)
                    self.results.append(data)
                    self.sv_count.set(f"{len(self.results)} fichier(s)")
                    for k in ('mft_total','mft_deleted','recovered','partial','carved','bad_sectors'):
                        if self.engine:
                            self.svars[k].set(f"{self.engine.stats.get(k,0):,}")
                elif msg == 'prog':
                    p, lbl = data
                    self.pv.set(p); self.plbl.config(text=lbl)
                    self.sv_status.set(lbl)
                elif msg == 'clusters':
                    self.cl_map.update_map(data)
                    # Update cluster stats
                    bad = sum(1 for v in data.values() if v=='bad')
                    rec = sum(1 for v in data.values() if v=='recovered')
                    del_ = sum(1 for v in data.values() if v=='deleted')
                    self.cl_stats.set(f"Clusters — Bad: {bad}  Récupérés: {rec}  Supprimés: {del_}  Total mappés: {len(data)}")
                elif msg == 'stats_done':
                    self._update_stats_tab(data)
                elif msg == 'done':
                    self.running = False
                    self.btn_go.config(state=NORMAL)
                    self.btn_stop.config(state=DISABLED)
                    self.pv.set(100)
                    self.sv_status.set(f"✓ Terminé — {data} fichiers trouvés")
                    self.plbl.config(text="✓ Terminé")
                    if self.engine:
                        for k in ('mft_total','mft_deleted','recovered','partial','carved','bad_sectors'):
                            self.svars[k].set(f"{self.engine.stats.get(k,0):,}")
        except queue.Empty:
            pass
        self.after(80, self._poll)

    def _log(self, text, tag='info'):
        self.q.put(('log', (tag, text)))

    def _append_log(self, text, tag):
        self.log_w.config(state=NORMAL)
        ts = datetime.now().strftime('%H:%M:%S')
        self.log_w.insert(END, f"[{ts}] {text}\n", tag)
        self.log_w.config(state=DISABLED)
        self.log_w.see(END)

    def _add_row(self, e):
        sz   = self._fmtsz(e['size'])
        ext  = Path(e['name']).suffix.lstrip('.').upper() or '?'
        if e['status'] == 'recovered': st = '✓ Récupéré'
        elif e['status'] == 'partial': st = '⚠ Partiel'
        elif e['status'] == 'carved':  st = '◈ Carved'
        else:                          st = '◎ Détecté'
        tag = e['status']
        self.tree.insert('', END,
            values=(e['num'], e['name'], sz, ext, st, e['date'], e['method']),
            tags=(tag,))

    # ── TREE ACTIONS ──────────────────────────────────────
    def _sel_all(self):
        self.tree.selection_set(self.tree.get_children())

    def _filter(self, *_):
        q = self.flt.get().lower()
        for item in self.tree.get_children(): self.tree.delete(item)
        for e in self.results:
            if q in e['name'].lower() or q in e['method'].lower():
                self._add_row(e)

    def _filter_by(self, tag):
        for item in self.tree.get_children(): self.tree.delete(item)
        for e in self.results:
            if tag == 'all': self._add_row(e)
            elif tag == 'partial' and e.get('partial'): self._add_row(e)
            elif tag != 'partial' and e['method'] == tag: self._add_row(e)

    def _sort(self, col):
        data = [(self.tree.set(k, col), k) for k in self.tree.get_children('')]
        rev  = self._sort_col == col and not self._sort_rev
        data.sort(reverse=rev, key=lambda x: x[0].lower() if isinstance(x[0],str) else x[0])
        for i, (_, k) in enumerate(data): self.tree.move(k,'',i)
        self._sort_col = col; self._sort_rev = rev

    def _extract_sel(self):
        sel = self.tree.selection()
        if not sel: messagebox.showinfo("Info","Sélectionnez des fichiers."); return
        out = filedialog.askdirectory(title="Extraire vers...")
        if not out: return
        import shutil; n=0
        for item in sel:
            vals = self.tree.item(item,'values')
            for r in self.results:
                if str(r['num']) == str(vals[0]) and r.get('path') and Path(r['path']).exists():
                    shutil.copy2(r['path'], out); n+=1; break
        messagebox.showinfo("Extraction", f"{n} fichier(s) copié(s) vers:\n{out}")

    def _save_report(self):
        if not self.results:
            messagebox.showinfo("Rapport","Aucun résultat."); return
        p = filedialog.asksaveasfilename(
            defaultextension='.txt',
            filetypes=[("Texte","*.txt"),("JSON","*.json")])
        if not p: return
        if p.endswith('.json'):
            Path(p).write_text(json.dumps(self.results,indent=2,default=str),encoding='utf-8')
        else:
            lines = ["PHANTOM RECOVER — RAPPORT\n","="*60+"\n",
                     f"Date  : {datetime.now()}\nSource: {self.src_var.get()}\n\n",
                     f"{'#':>8}  {'Statut':12}  {'Taille':>12}  {'Méthode':8}  Nom\n","─"*90+"\n"]
            for r in self.results:
                st = '⚠ PARTIEL' if r.get('partial') else ('✓ OK' if r.get('path') else '◎')
                lines.append(f"{r['num']:>8}  {st:12}  {self._fmtsz(r['size']):>12}  {r['method']:8}  {r['name']}\n")
            Path(p).write_text(''.join(lines),encoding='utf-8')
        messagebox.showinfo("Rapport",f"Sauvegardé:\n{p}")

    def _update_stats_tab(self, stats):
        self.stats_w.config(state=NORMAL)
        self.stats_w.delete('1.0',END)
        lines = [
            "╔══════════════════════════════════════════╗",
            "║         PHANTOM RECOVER — STATS          ║",
            "╚══════════════════════════════════════════╝","",
        ]
        for k,v in stats.items():
            lines.append(f"  {k:30}: {v:>12,}")
        lines += ["","  Source : "+self.src_var.get(),"  Output : "+self.out_var.get()]
        self.stats_w.insert(END,'\n'.join(lines))
        self.stats_w.config(state=DISABLED)

    @staticmethod
    def _fmtsz(s):
        if not s: return '0 B'
        for u in ['B','KB','MB','GB','TB']:
            if s < 1024: return f"{s:.1f} {u}"
            s /= 1024
        return f"{s:.1f} PB"


# ═══════════════════════════════════════════════════════════════
if __name__ == '__main__':
    app = PhantomRecover()
    app.mainloop()
