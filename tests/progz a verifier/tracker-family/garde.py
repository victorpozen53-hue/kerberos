import time
try: import requests
except ImportError: requests = None
from urllib.parse import urlparse
from urllib.robotparser import RobotFileParser

class Decision:
    def __init__(self, ok, raison=""): self.ok, self.raison = ok, raison

class GardeJournal:
    def controle(self, req, ctx):
        ctx["logger"].info(f"[garde] passage {req['url']}"); return Decision(True)

class GardeIdentite:
    def controle(self, req, ctx):
        req.setdefault("headers", {})["User-Agent"] = ctx["ua"]; return Decision(True)

class GardeRobots:
    def __init__(self): self._cache = {}
    def controle(self, req, ctx):
        host = urlparse(req["url"]).netloc
        if host not in self._cache:
            rp = RobotFileParser(); rp.set_url(f"https://{host}/robots.txt")
            try: rp.read()
            except Exception: rp.parse([])
            self._cache[host] = rp
        if self._cache[host].can_fetch(ctx["ua"], req["url"]): return Decision(True)
        return Decision(False, f"robots.txt interdit {req['url']}")

class GardeCadence:
    def controle(self, req, ctx):
        time.sleep(ctx.get("pause", 1.5)); return Decision(True)

class Portier:
    def __init__(self, gardes, ctx, timeout=20):
        self.gardes, self.ctx, self.timeout = gardes, ctx, timeout
    def get(self, url, params=None):
        if requests is None:
            self.ctx["logger"].info("requests absent"); return None
        req = {"url": url, "params": params, "headers": {}}
        for g in self.gardes:
            d = g.controle(req, self.ctx)
            if not d.ok:
                self.ctx["logger"].info(f"[garde] BLOQUE {g.__class__.__name__}: {d.raison}")
                return None
        try:
            r = requests.get(url, params=params, headers=req["headers"], timeout=self.timeout)
            self.ctx["logger"].info(f"[requete] {r.status_code} {url}")
            return r if r.ok else None
        except Exception as e:
            self.ctx["logger"].info(f"[requete] ERREUR {url} -> {e}"); return None