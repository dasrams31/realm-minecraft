#!/usr/bin/env python3
"""Muse SMP admin portal — stdlib only.
Controls the local Paper server via RCON + server.properties + systemd.
Listens on 127.0.0.1:8082, exposed publicly through reverse SSH tunnel + Caddy.
"""
import hashlib
import hmac
import json
import os
import re
import secrets
import socket
import sqlite3
import struct
import subprocess
import threading
import time
import urllib.request
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from urllib.parse import urlparse, parse_qs, quote

BASE = os.path.dirname(os.path.abspath(__file__))
CONFIG = os.path.join(BASE, "config")
STATIC = os.path.join(BASE, "static")
MC_DIR = "/home/hatch/workspace/minecraft/server"
PROPS = os.path.join(MC_DIR, "server.properties")
OPS_JSON = os.path.join(MC_DIR, "ops.json")
WL_JSON = os.path.join(MC_DIR, "whitelist.json")
LOG_FILE = os.path.join(MC_DIR, "logs", "latest.log")
CHEATS_FILE = os.path.join(CONFIG, "cheats.json")

SESSION_TTL = 12 * 3600
sessions = {}  # token -> expiry
sessions_lock = threading.Lock()


# ---------------- RCON ----------------
class Rcon:
    def __init__(self):
        self.lock = threading.Lock()
        self.sock = None

    def _password(self):
        with open(os.path.join(CONFIG, "rcon_password")) as f:
            return f.read().strip()

    def _packet(self, rid, typ, body):
        b = body.encode("utf-8") + b"\x00\x00"
        return struct.pack("<iii", 4 + 4 + len(b), rid, typ) + b

    def _read(self, s):
        ln = struct.unpack("<i", self._recvn(s, 4))[0]
        if ln < 10 or ln > 10 * 1024 * 1024:
            raise ConnectionError("bad rcon length")
        d = self._recvn(s, ln)
        (rid, typ) = struct.unpack("<ii", d[:8])
        return rid, typ, d[8:-2].decode("utf-8", "replace")

    @staticmethod
    def _recvn(s, n):
        d = b""
        while len(d) < n:
            chunk = s.recv(n - len(d))
            if not chunk:
                raise ConnectionError("rcon closed")
            d += chunk
        return d

    def _connect(self):
        if self.sock:
            try:
                self.sock.sendall(b"")
                return
            except OSError:
                pass
            try:
                self.sock.close()
            except OSError:
                pass
            self.sock = None
        s = socket.create_connection(("127.0.0.1", 25575), timeout=8)
        s.sendall(self._packet(1, 3, self._password()))
        rid, _, _ = self._read(s)
        if rid != 1:
            s.close()
            raise PermissionError("rcon auth failed")
        self.sock = s

    def cmd(self, command):
        with self.lock:
            try:
                self._connect()
                self.sock.sendall(self._packet(2, 2, command))
                out = []
                # read until we get our response id (server may interleave junk)
                deadline = time.time() + 10
                while time.time() < deadline:
                    rid, typ, body = self._read(self.sock)
                    if rid == 2 and typ == 0:
                        out.append(body)
                        self.sock.settimeout(0.4)
                        try:
                            while True:
                                rid2, typ2, body2 = self._read(self.sock)
                                if rid2 == 2:
                                    out.append(body2)
                                else:
                                    break
                        except (socket.timeout, ConnectionError):
                            pass
                        finally:
                            self.sock.settimeout(8)
                        break
                return "".join(out).strip()
            except (OSError, ConnectionError, PermissionError):
                try:
                    if self.sock:
                        self.sock.close()
                except OSError:
                    pass
                self.sock = None
                raise


rcon = Rcon()


# ---------------- helpers ----------------
def read_props():
    vals, order = {}, []
    with open(PROPS, encoding="utf-8") as f:
        for line in f:
            s = line.strip()
            if not s or s.startswith("#") or "=" not in s:
                continue
            k, v = s.split("=", 1)
            vals[k] = v
            order.append(k)
    return vals, order


def write_props(vals):
    lines = []
    with open(PROPS, encoding="utf-8") as f:
        for line in f:
            s = line.strip()
            if s and not s.startswith("#") and "=" in s:
                k = s.split("=", 1)[0]
                if k in vals:
                    lines.append(f"{k}={vals[k]}\n")
                    continue
            lines.append(line)
    with open(PROPS, "w", encoding="utf-8") as f:
        f.writelines(lines)


def json_file(path):
    try:
        with open(path, encoding="utf-8") as f:
            return json.load(f)
    except (OSError, ValueError):
        return []


def get_cheats():
    try:
        with open(CHEATS_FILE, encoding="utf-8") as f:
            return bool(json.load(f).get("enabled", False))
    except (OSError, ValueError):
        return False


# ---------------- plugins ----------------
PLUGINS_DIR = os.path.join(MC_DIR, "plugins")
MR_API = "https://api.modrinth.com"
MR_UA = {"User-Agent": "MuseSMP-Portal/1.0 (admin)"}
JAR_RE = re.compile(r"^[A-Za-z0-9._\- ]+\.jar$")


def list_plugins():
    out = []
    if not os.path.isdir(PLUGINS_DIR):
        return out
    for fn in sorted(os.listdir(PLUGINS_DIR)):
        if fn.endswith(".jar"):
            enabled, disp = True, fn[:-4]
        elif fn.endswith(".jar.disabled"):
            enabled, disp = False, fn[:-13]
        else:
            continue
        try:
            size = os.path.getsize(os.path.join(PLUGINS_DIR, fn))
        except OSError:
            size = 0
        out.append({"file": fn, "name": disp, "enabled": enabled, "size": size})
    return out


def safe_jar_name(name):
    base = os.path.basename(str(name or "")).strip()
    if not JAR_RE.match(base):
        return None
    return base


def mr_get(path):
    req = urllib.request.Request(MR_API + path, headers=MR_UA)
    with urllib.request.urlopen(req, timeout=25) as r:
        return json.load(r)


def mr_download(url, dest, limit=128 * 1024 * 1024):
    if not url.startswith("https://cdn.modrinth.com/"):
        raise ValueError("URL download tidak valid")
    req = urllib.request.Request(url, headers=MR_UA)
    total = 0
    with urllib.request.urlopen(req, timeout=180) as r, open(dest, "wb") as f:
        while True:
            chunk = r.read(65536)
            if not chunk:
                break
            total += len(chunk)
            if total > limit:
                raise ValueError("file terlalu besar")
            f.write(chunk)
    return total


def parse_multipart(handler):
    """Minimal single-file multipart parser. Returns (filename, bytes)."""
    ctype = handler.headers.get("Content-Type", "")
    m = re.search(r"boundary=([^\s;]+)", ctype)
    if not m:
        return None, None
    boundary = m.group(1).strip('"').encode()
    try:
        length = int(handler.headers.get("Content-Length", 0))
    except ValueError:
        return None, None
    if length <= 0 or length > 64 * 1024 * 1024:
        return None, None
    data = handler.rfile.read(length)
    fm = re.search(rb'filename="([^"]+)"', data)
    if not fm:
        return None, None
    hstart = data.find(b"\r\n\r\n", fm.start())
    if hstart == -1:
        return None, None
    start = hstart + 4
    end = data.find(b"\r\n--" + boundary, start)
    if end == -1:
        return None, None
    return fm.group(1).decode("utf-8", "replace"), data[start:end]


def set_cheats(v):
    with open(CHEATS_FILE, "w", encoding="utf-8") as f:
        json.dump({"enabled": bool(v)}, f)


# ---------------- public stats ----------------
AUTHME_DB = os.path.join(MC_DIR, "plugins", "AuthMe", "authme.db")
HIST_FILE = os.path.join(CONFIG, "player_history.jsonl")
ACTIVITY_FILE = os.path.join(CONFIG, "activity.jsonl")
_pub_cache = {"ts": 0, "size": 0}


def log_activity(action, detail=""):
    """Catat aksi admin ke activity.jsonl (maks 500 entri)."""
    try:
        os.makedirs(CONFIG, exist_ok=True)
        entry = json.dumps({"t": int(time.time()), "action": str(action)[:60],
                            "detail": str(detail)[:300]}, ensure_ascii=False)
        lines = []
        try:
            with open(ACTIVITY_FILE, encoding="utf-8") as f:
                lines = f.readlines()
        except OSError:
            pass
        lines.append(entry + "\n")
        with open(ACTIVITY_FILE, "w", encoding="utf-8") as f:
            f.writelines(lines[-500:])
    except Exception:
        pass


def registered_count():
    try:
        con = sqlite3.connect(f"file:{AUTHME_DB}?mode=ro", uri=True, timeout=5)
        n = con.execute("SELECT COUNT(*) FROM authme").fetchone()[0]
        con.close()
        return int(n)
    except Exception:
        return None


def cached_world_size():
    now = time.time()
    if now - _pub_cache["ts"] > 300:
        total = 0
        for d in ("world", "world_nether", "world_the_end"):
            p = os.path.join(MC_DIR, d)
            if os.path.isdir(p):
                r = subprocess.run(["du", "-sb", p], capture_output=True, text=True)
                try:
                    total += int(r.stdout.split()[0])
                except (ValueError, IndexError):
                    pass
        _pub_cache.update(ts=now, size=total)
    return _pub_cache["size"]


def history_tracker():
    """Catat jumlah pemain online tiap 5 menit (maks 7 hari)."""
    while True:
        try:
            out = rcon.cmd("list")
            online, _, _ = parse_list_output(out)
            entry = json.dumps({"t": int(time.time()), "n": online})
            os.makedirs(CONFIG, exist_ok=True)
            cutoff = time.time() - 7 * 24 * 3600
            kept = []
            try:
                with open(HIST_FILE, encoding="utf-8") as f:
                    for line in f:
                        try:
                            e = json.loads(line)
                            if e.get("t", 0) >= cutoff:
                                kept.append(line if line.endswith("\n") else line + "\n")
                        except (ValueError, KeyError):
                            pass
            except OSError:
                pass
            kept.append(entry + "\n")
            with open(HIST_FILE, "w", encoding="utf-8") as f:
                f.writelines(kept[-2016:])
        except Exception:
            pass
        time.sleep(300)


def parse_list_output(out):
    # "There are 2 of a max of 10 players online: Steve, Alex"
    m = re.search(r"There are (\d+) of a max of (\d+) players online:(.*)", out, re.S)
    if not m:
        return 0, 10, []
    names = [n.strip() for n in m.group(3).split(",") if n.strip()]
    # kecualikan bot dari hitungan/tampilan
    names = [n for n in names if n.lower() not in ("muse", "museafk")]
    return len(names), int(m.group(2)), names


def check_password(pw):
    try:
        with open(os.path.join(CONFIG, "admin.hash"), encoding="utf-8") as f:
            salt_hex, hash_hex = f.read().strip().split(":")
    except (OSError, ValueError):
        return False
    calc = hashlib.pbkdf2_hmac("sha256", pw.encode(), bytes.fromhex(salt_hex), 200_000).hex()
    return hmac.compare_digest(calc, hash_hex)


def new_session():
    tok = secrets.token_urlsafe(32)
    with sessions_lock:
        sessions[tok] = time.time() + SESSION_TTL
    return tok


def valid_session(handler):
    cookie = handler.headers.get("Cookie", "")
    m = re.search(r"mcportal_session=([A-Za-z0-9_\-]+)", cookie)
    if not m:
        return False
    with sessions_lock:
        exp = sessions.get(m.group(1))
        if not exp:
            return False
        if exp < time.time():
            del sessions[m.group(1)]
            return False
        sessions[m.group(1)] = time.time() + SESSION_TTL
        return True


def kill_session(handler):
    cookie = handler.headers.get("Cookie", "")
    m = re.search(r"mcportal_session=([A-Za-z0-9_\-]+)", cookie)
    if m:
        with sessions_lock:
            sessions.pop(m.group(1), None)


# ---------------- HTTP ----------------
class Handler(BaseHTTPRequestHandler):
    server_version = "MuseSMP-Portal/1.0"

    def log_message(self, *a):
        pass

    def _send(self, code, body, ctype="application/json", headers=None):
        if isinstance(body, str):
            body = body.encode("utf-8")
        self.send_response(code)
        self.send_header("Content-Type", ctype)
        self.send_header("Content-Length", str(len(body)))
        for k, v in (headers or {}).items():
            self.send_header(k, v)
        self.end_headers()
        self.wfile.write(body)

    def _json(self, obj, code=200, headers=None):
        self._send(code, json.dumps(obj), headers=headers)

    def _body(self):
        try:
            ln = int(self.headers.get("Content-Length", 0))
        except ValueError:
            ln = 0
        return self.rfile.read(ln) if ln else b""

    def _require_auth(self):
        if not valid_session(self):
            self._json({"error": "unauthorized"}, 401)
            return False
        return True

    # ----- routes -----
    def do_GET(self):
        path = urlparse(self.path).path
        if path == "/":
            return self._static("landing.html", "text/html; charset=utf-8")
        if path == "/sitemap.xml":
            xml = """<?xml version="1.0" encoding="UTF-8"?>
<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">
  <url><loc>https://realm.ramadanadipa.com/</loc><changefreq>daily</changefreq><priority>1.0</priority></url>
</urlset>"""
            return self._send(200, xml, "application/xml")
        if path == "/manage":
            return self._static("index.html", "text/html; charset=utf-8")
        if path.startswith("/static/"):
            name = path[len("/static/"):]
            if ".." in name or "/" in name:
                return self._json({"error": "not found"}, 404)
            ctype = {"css": "text/css", "js": "application/javascript"}.get(name.rsplit(".", 1)[-1], "application/octet-stream")
            return self._static(name, ctype)
        if path == "/api/me":
            return self._json({"logged_in": valid_session(self)})
        if path == "/api/public-status":
            return self._api_public_status()
        if path == "/api/public-history":
            return self._api_public_history()
        if path == "/api/public-pioneers":
            return self._api_public_pioneers()
        if path == "/api/activity":
            if not self._require_auth():
                return
            return self._api_activity()
        if not self._require_auth():
            return
        try:
            if path == "/api/status":
                return self._api_status()
            if path == "/api/players":
                return self._api_players()
            if path == "/api/cheats":
                return self._json({"enabled": get_cheats()})
            if path == "/api/settings":
                return self._api_get_settings()
            if path == "/api/logs":
                return self._api_logs()
            if path == "/api/plugins":
                return self._json({"plugins": list_plugins()})
            if path == "/api/plugins/search":
                q = parse_qs(urlparse(self.path).query).get("q", [""])[0].strip()
                if not q:
                    return self._json({"hits": []})
                facets = quote('[["project_type:plugin"],["loaders:paper"]]')
                data = mr_get(f"/v2/search?query={quote(q)}&limit=12&facets={facets}")
                hits = [{"id": h.get("project_id"), "slug": h.get("slug"),
                         "title": h.get("title"), "description": (h.get("description") or "")[:160],
                         "downloads": h.get("downloads", 0),
                         "icon": h.get("icon_url") or ""}
                        for h in data.get("hits", [])]
                return self._json({"hits": hits})
            if path == "/api/plugins/versions":
                pid = parse_qs(urlparse(self.path).query).get("id", [""])[0].strip()
                if not pid or not re.match(r"^[A-Za-z0-9]+$", pid):
                    return self._json({"error": "id tidak valid"}, 400)
                vers = mr_get(f"/v2/project/{pid}/version?loaders=%5B%22paper%22%5D&limit=15")
                out = []
                for v in vers:
                    files = [{"name": f.get("filename"), "size": f.get("size", 0),
                              "primary": bool(f.get("primary"))} for f in v.get("files", [])
                             if (f.get("filename") or "").endswith(".jar")]
                    if not files:
                        continue
                    out.append({"version_id": v.get("id"),
                                "version_number": v.get("version_number"),
                                "game_versions": v.get("game_versions", []),
                                "date": (v.get("date_published") or "")[:10],
                                "files": files})
                return self._json({"versions": out})
            if path == "/api/perf":
                return self._api_perf()
            if path == "/api/gamerules":
                return self._api_gamerules()
            if path == "/api/world":
                return self._api_world()
            if path == "/api/world/download":
                fn = parse_qs(urlparse(self.path).query).get("file", [""])[0]
                if not re.match(r"^world-[a-z\-]+-\d{8}-\d{6}\.tar\.gz$", fn or ""):
                    return self._json({"error": "file tidak valid"}, 400)
                fp = os.path.join(MC_DIR, "backups", fn)
                if not os.path.isfile(fp):
                    return self._json({"error": "file tidak ada"}, 404)
                with open(fp, "rb") as f:
                    data = f.read()
                return self._send(200, data, "application/gzip",
                                  {"Content-Disposition": f"attachment; filename={fn}"})
            if path == "/api/files":
                return self._api_files(parse_qs(urlparse(self.path).query).get("dir", ["."])[0])
            if path == "/api/file":
                return self._api_file_get(parse_qs(urlparse(self.path).query).get("path", [""])[0])
            if path == "/api/schedule":
                return self._api_schedule_get()
            if path == "/api/paper":
                return self._api_paper()
        except (OSError, ConnectionError, PermissionError) as e:
            return self._json({"error": str(e)}, 502)
        except Exception as e:
            return self._json({"error": f"Modrinth: {e}"}, 502)
        return self._json({"error": "not found"}, 404)

    def do_POST(self):
        path = urlparse(self.path).path
        if path == "/api/plugins/upload":
            if not self._require_auth():
                return
            return self._api_plugin_upload()
        try:
            data = json.loads(self._body() or b"{}")
        except ValueError:
            data = {}
        if path == "/api/login":
            if check_password(str(data.get("password", ""))):
                tok = new_session()
                log_activity("login", "admin login berhasil")
                return self._json({"ok": True}, headers={
                    "Set-Cookie": f"mcportal_session={tok}; Path=/; HttpOnly; SameSite=Lax; Max-Age={SESSION_TTL}"})
            time.sleep(1)
            return self._json({"error": "password salah"}, 401)
        if path == "/api/logout":
            kill_session(self)
            return self._json({"ok": True}, headers={
                "Set-Cookie": "mcportal_session=; Path=/; HttpOnly; SameSite=Lax; Max-Age=0"})
        if not self._require_auth():
            return
        try:
            if path == "/api/cmd":
                out = rcon.cmd(str(data.get("command", ""))[:500])
                log_activity("konsol", str(data.get("command", ""))[:120])
                return self._json({"output": out})
            if path == "/api/player/op":
                rcon.cmd(f"op {data.get('name','')}")
                log_activity("op", str(data.get("name", ""))[:40])
                return self._json({"ok": True})
            if path == "/api/player/deop":
                rcon.cmd(f"deop {data.get('name','')}")
                log_activity("deop", str(data.get("name", ""))[:40])
                return self._json({"ok": True})
            if path == "/api/player/kick":
                rcon.cmd(f"kick {data.get('name','')} {data.get('reason','') or 'Dikeluarkan oleh admin'}")
                log_activity("kick", f"{data.get('name','')} — {data.get('reason','')}"[:120])
                return self._json({"ok": True})
            if path == "/api/player/ban":
                rcon.cmd(f"ban {data.get('name','')} {data.get('reason','') or 'Banned oleh admin'}")
                log_activity("ban", f"{data.get('name','')} — {data.get('reason','')}"[:120])
                return self._json({"ok": True})
            if path == "/api/player/pardon":
                rcon.cmd(f"pardon {data.get('name','')}")
                log_activity("unban", str(data.get("name", ""))[:40])
                return self._json({"ok": True})
            if path == "/api/whitelist":
                return self._api_whitelist(data)
            if path == "/api/cheats":
                return self._api_cheats(bool(data.get("enabled")))
            if path == "/api/settings":
                return self._api_set_settings(data.get("values", {}))
            if path == "/api/power":
                return self._api_power(str(data.get("action", "")))
            if path == "/api/plugins/toggle":
                return self._api_plugin_toggle(str(data.get("file", "")), bool(data.get("enabled")))
            if path == "/api/plugins/delete":
                return self._api_plugin_delete(str(data.get("file", "")))
            if path == "/api/plugins/install":
                return self._api_plugin_install(str(data.get("version_id", "")))
            if path == "/api/gamerule":
                return self._api_gamerule_set(str(data.get("name", "")), data.get("value"))
            if path == "/api/difficulty":
                return self._api_difficulty(str(data.get("value", "")))
            if path == "/api/world/backup":
                return self._api_world_backup()
            if path == "/api/world/seed":
                return self._api_world_seed(data.get("seed", ""))
            if path == "/api/file":
                return self._api_file_put(str(data.get("path", "")), str(data.get("content", "")))
            if path == "/api/schedule":
                d = data
                return self._api_schedule_set(str(d.get("kind", "")), d.get("hour"), d.get("minute"), bool(d.get("enabled")))
            if path == "/api/paper/update":
                return self._api_paper_update()
        except (OSError, ConnectionError, PermissionError) as e:
            return self._json({"error": str(e)}, 502)
        except Exception as e:
            return self._json({"error": str(e)}, 502)
        return self._json({"error": "not found"}, 404)

    def _static(self, name, ctype):
        p = os.path.join(STATIC if name != "index.html" else STATIC, name)
        try:
            with open(p, "rb") as f:
                data = f.read()
        except OSError:
            return self._json({"error": "not found"}, 404)
        self._send(200, data, ctype)

    # ----- api impl -----
    def _api_public_status(self):
        # public: same info a server-list ping would show, no auth needed
        vals, _ = read_props()
        try:
            out = rcon.cmd("list")
            online, mx, names = parse_list_output(out)
            server_up = True
        except (OSError, ConnectionError, PermissionError):
            server_up, online, mx = False, 0, int(vals.get("max-players", 10) or 10)
            names = []
        self._json({
            "server_up": server_up,
            "online": online, "max": mx, "names": names,
            "motd": vals.get("motd", ""),
            "difficulty": vals.get("difficulty", "normal"),
            "cheats": get_cheats(),
            "registered": registered_count(),
            "world_size": cached_world_size(),
        })

    def _api_public_history(self):
        pts = []
        cutoff = time.time() - 24 * 3600
        try:
            with open(HIST_FILE, encoding="utf-8") as f:
                for line in f:
                    try:
                        e = json.loads(line)
                        if e.get("t", 0) >= cutoff:
                            pts.append({"t": e["t"], "n": e["n"]})
                    except (ValueError, KeyError, TypeError):
                        pass
        except OSError:
            pass
        self._json({"points": pts[-96:]})

    def _api_public_pioneers(self):
        rows = []
        try:
            con = sqlite3.connect(f"file:{AUTHME_DB}?mode=ro", uri=True, timeout=5)
            for i, r in enumerate(
                    con.execute("SELECT username, lastlogin FROM authme ORDER BY rowid"), 1):
                rows.append({"name": r[0], "rank": i, "last": r[1]})
            con.close()
        except Exception:
            pass
        self._json({"pioneers": rows[:8]})

    def _api_activity(self):
        items = []
        try:
            with open(ACTIVITY_FILE, encoding="utf-8") as f:
                for line in f:
                    try:
                        items.append(json.loads(line))
                    except ValueError:
                        pass
        except OSError:
            pass
        self._json({"activity": items[-100:][::-1]})

    def _api_status(self):
        vals, _ = read_props()
        try:
            out = rcon.cmd("list")
            online, mx, names = parse_list_output(out)
            server_up = True
        except (OSError, ConnectionError, PermissionError):
            server_up, online, mx, names = False, 0, int(vals.get("max-players", 10)), []
        version = ""
        if server_up:
            try:
                version = rcon.cmd("version").split("\n")[0][:120]
                if "Checking version" in version:
                    time.sleep(2)
                    version = rcon.cmd("version").split("\n")[0][:120]
                version = re.sub(r"§.", "", version).strip()
            except (OSError, ConnectionError, PermissionError):
                pass
        active = subprocess.run(["systemctl", "is-active", "minecraft.service"],
                                capture_output=True, text=True).stdout.strip()
        self._json({
            "server_up": server_up,
            "service_active": active == "active",
            "version": version,
            "motd": vals.get("motd", ""),
            "online": online, "max": mx, "names": names,
            "difficulty": vals.get("difficulty", "normal"),
            "cheats": get_cheats(),
        })

    def _api_players(self):
        try:
            _, _, names = parse_list_output(rcon.cmd("list"))
            server_up = True
        except (OSError, ConnectionError, PermissionError):
            names, server_up = [], False
        ops = [e.get("name", "") for e in json_file(OPS_JSON) if e.get("name")]
        wl = [e.get("name", "") for e in json_file(WL_JSON) if e.get("name")]
        vals, _ = read_props()
        self._json({"server_up": server_up, "online": names, "ops": ops,
                    "whitelisted": wl, "whitelist_enabled": vals.get("white-list", "false") == "true"})

    def _api_whitelist(self, data):
        action = data.get("action")
        name = str(data.get("name", "")).strip()
        if action == "enable":
            rcon.cmd("whitelist on")
        elif action == "disable":
            rcon.cmd("whitelist off")
        elif action == "add" and name:
            rcon.cmd(f"whitelist add {name}")
        elif action == "remove" and name:
            rcon.cmd(f"whitelist remove {name}")
        else:
            return self._json({"error": "aksi tidak valid"}, 400)
        vals, _ = read_props()
        vals["white-list"] = "true" if action in ("enable",) or (
            action in ("add", "remove") and vals.get("white-list") == "true") else (
            "false" if action == "disable" else vals.get("white-list", "false"))
        write_props({"white-list": vals["white-list"]})
        log_activity("whitelist", f"{action} {name}".strip())
        return self._json({"ok": True})

    def _api_cheats(self, enabled):
        try:
            _, _, names = parse_list_output(rcon.cmd("list"))
        except (OSError, ConnectionError, PermissionError):
            return self._json({"error": "server tidak merespons (RCON)"}, 502)
        for n in names:
            try:
                rcon.cmd(f"{'op' if enabled else 'deop'} {n}")
            except (OSError, ConnectionError, PermissionError):
                pass
        set_cheats(enabled)
        log_activity("cheat", f"{'ON' if enabled else 'OFF'} ({len(names)} pemain online)")
        return self._json({"ok": True, "enabled": enabled, "affected": names})

    EDITABLE = {
        "motd": "MOTD (nama tampil server)",
        "max-players": "Maks pemain",
        "difficulty": "Difficulty",
        "gamemode": "Default gamemode",
        "pvp": "PvP",
        "enable-command-block": "Command block",
        "white-list": "Whitelist",
        "spawn-protection": "Radius spawn protection",
        "view-distance": "View distance",
        "simulation-distance": "Simulation distance",
    }
    BOOLS = {"pvp", "enable-command-block", "white-list"}

    def _api_get_settings(self):
        vals, _ = read_props()
        return self._json({"values": {k: vals.get(k, "") for k in self.EDITABLE},
                           "bools": sorted(self.BOOLS),
                           "meta": self.EDITABLE})

    def _api_set_settings(self, values):
        vals, _ = read_props()
        new = {}
        for k in self.EDITABLE:
            if k in values:
                v = str(values[k]).strip()
                if k in self.BOOLS:
                    v = "true" if v.lower() in ("true", "1", "on", "yes") else "false"
                new[k] = v
        write_props(new)
        log_activity("pengaturan", ", ".join(f"{k}={v}" for k, v in new.items())[:200])
        return self._json({"ok": True, "restart_required": True})

    def _api_power(self, action):
        if action not in ("start", "stop", "restart"):
            return self._json({"error": "aksi tidak valid"}, 400)
        subprocess.run(["systemctl", action, "minecraft.service"], capture_output=True)
        time.sleep(2)
        active = subprocess.run(["systemctl", "is-active", "minecraft.service"],
                                capture_output=True, text=True).stdout.strip()
        log_activity("power", action)
        return self._json({"ok": True, "service_active": active == "active"})

    def _known_plugin_file(self, file):
        base = os.path.basename(file)
        if base != file:
            return None
        if base not in [p["file"] for p in list_plugins()]:
            return None
        return base

    def _api_plugin_upload(self):
        filename, data = parse_multipart(self)
        name = safe_jar_name(filename)
        if not name or not data:
            return self._json({"error": "upload gagal — pastikan file .jar (maks 64MB)"}, 400)
        os.makedirs(PLUGINS_DIR, exist_ok=True)
        dest = os.path.join(PLUGINS_DIR, name)
        if os.path.exists(dest):
            return self._json({"error": f"{name} sudah ada"}, 409)
        with open(dest, "wb") as f:
            f.write(data)
        log_activity("plugin", f"upload {name}")
        return self._json({"ok": True, "file": name, "restart_required": True})

    def _api_plugin_toggle(self, file, enabled):
        base = self._known_plugin_file(file)
        if not base:
            return self._json({"error": "file tidak dikenal"}, 400)
        src = os.path.join(PLUGINS_DIR, base)
        if enabled and base.endswith(".jar.disabled"):
            dst = os.path.join(PLUGINS_DIR, base[:-9])
        elif not enabled and base.endswith(".jar") and not base.endswith(".jar.disabled"):
            dst = src + ".disabled"
        else:
            return self._json({"ok": True, "restart_required": True})
        os.rename(src, dst)
        log_activity("plugin", f"{'aktifkan' if enabled else 'nonaktifkan'} {base}")
        return self._json({"ok": True, "restart_required": True})

    def _api_plugin_delete(self, file):
        base = self._known_plugin_file(file)
        if not base:
            return self._json({"error": "file tidak dikenal"}, 400)
        os.remove(os.path.join(PLUGINS_DIR, base))
        log_activity("plugin", f"hapus {base}")
        return self._json({"ok": True, "restart_required": True})

    def _api_plugin_install(self, version_id):
        if not version_id or not re.match(r"^[A-Za-z0-9]+$", version_id):
            return self._json({"error": "version_id tidak valid"}, 400)
        v = mr_get(f"/v2/version/{version_id}")
        files = [f for f in v.get("files", []) if (f.get("filename") or "").endswith(".jar")]
        if not files:
            return self._json({"error": "tidak ada file .jar pada versi ini"}, 400)
        files.sort(key=lambda f: (not f.get("primary"), f.get("size", 0)))
        target = files[0]
        name = safe_jar_name(target.get("filename"))
        if not name:
            return self._json({"error": "nama file tidak valid"}, 400)
        os.makedirs(PLUGINS_DIR, exist_ok=True)
        dest = os.path.join(PLUGINS_DIR, name)
        if os.path.exists(dest):
            return self._json({"error": f"{name} sudah terinstall"}, 409)
        mr_download(target["url"], dest)
        log_activity("plugin", f"install dari Modrinth: {name}")
        return self._json({"ok": True, "file": name, "restart_required": True})

    # ---------- performa ----------
    @staticmethod
    def _strip(s):
        return re.sub(r"§.", "", s or "")

    def _java_pid(self):
        r = subprocess.run(["pgrep", "-f", "paper.jar"], capture_output=True, text=True)
        for line in r.stdout.split():
            if line.strip().isdigit():
                return int(line.strip())
        return None

    def _api_perf(self):
        tps, mspt = {"m1": None, "m5": None, "m15": None}, None
        try:
            out = self._strip(rcon.cmd("tps"))
            first = out.split("\n")[0]
            after = first.split(":", 1)[1] if ":" in first else first
            fl = re.findall(r"(\d+(?:\.\d+)?)", after)
            if len(fl) >= 3:
                tps = {"m1": float(fl[0]), "m5": float(fl[1]), "m15": float(fl[2])}
            m2 = re.search(r"(?i)mspt[^\d]*(\d+(?:\.\d+)?)", out)
            if m2:
                mspt = float(m2.group(1))
        except (OSError, ConnectionError, PermissionError):
            pass
        mem_mb = uptime_s = pid = None
        pid = self._java_pid()
        if pid:
            try:
                mem_mb = int(subprocess.run(["ps", "-o", "rss=", "-p", str(pid)],
                                            capture_output=True, text=True).stdout.strip()) // 1024
                uptime_s = int(subprocess.run(["ps", "-o", "etimes=", "-p", str(pid)],
                                              capture_output=True, text=True).stdout.strip())
            except (ValueError, OSError):
                pass
        self._json({"tps": tps, "mspt": mspt, "mem_mb": mem_mb, "mem_max_mb": 1024,
                    "uptime_s": uptime_s, "pid": pid})

    # ---------- gamerules ----------
    GAMERULES = {
        "announce_advancements": "bool", "block_explosion_drop_decay": "bool",
        "command_block_output": "bool", "do_daylight_cycle": "bool",
        "do_fire_tick": "bool", "do_immediate_respawn": "bool",
        "do_insomnia": "bool", "do_limited_crafting": "bool",
        "do_mob_loot": "bool", "do_mob_spawning": "bool",
        "do_patrol_spawning": "bool", "do_tile_drops": "bool",
        "do_trader_spawning": "bool", "do_warden_spawning": "bool",
        "do_weather_cycle": "bool", "drowning_damage": "bool",
        "fall_damage": "bool", "fire_damage": "bool",
        "forgive_dead_players": "bool", "freeze_damage": "bool",
        "global_sound_events": "bool", "keep_inventory": "bool",
        "lava_source_conversion": "bool", "log_admin_commands": "bool",
        "max_command_forks": "int", "max_entity_cramming": "int",
        "mob_explosion_drop_decay": "bool", "mob_griefing": "bool",
        "natural_regeneration": "bool", "players_sleeping_percentage": "int",
        "random_tick_speed": "int", "reduced_debug_info": "bool",
        "send_command_feedback": "bool", "show_death_messages": "bool",
        "spawn_radius": "int", "tnt_explosion_drop_decay": "bool",
        "water_source_conversion": "bool",
    }
    GAMERULE_DESC = {
        "keep_inventory": "Item tidak hilang saat mati",
        "do_fire_tick": "Api menyebar/mematikan",
        "mob_griefing": "Mob bisa merusak blok (Creeper, Enderman)",
        "do_mob_spawning": "Mob muncul natural",
        "do_daylight_cycle": "Siklus siang/malam berjalan",
        "do_weather_cycle": "Cuaca berubah-ubah",
        "do_immediate_respawn": "Respawn langsung tanpa layar kematian",
        "do_insomnia": "Phantom muncul kalau belum tidur",
        "do_patrol_spawning": "Patroli pillager muncul",
        "do_trader_spawning": "Wandering trader muncul",
        "do_warden_spawning": "Warden muncul",
        "natural_regeneration": "Darah regen natural",
        "announce_advancements": "Pengumuman advancement di chat",
        "command_block_output": "Output command block di chat",
        "log_admin_commands": "Log command admin",
        "send_command_feedback": "Feedback command ke pelaksana",
        "show_death_messages": "Pesan kematian di chat",
        "random_tick_speed": "Kecepatan tick acak (default 3)",
        "spawn_radius": "Radius proteksi spawn (blok)",
        "max_entity_cramming": "Batas entity bertumpuk",
        "players_sleeping_percentage": "% pemain harus tidur untuk skip malam",
        "reduced_debug_info": "Kurangi info debug (F3)",
        "drowning_damage": "Damage tenggelam",
        "fall_damage": "Damage jatuh",
        "fire_damage": "Damage api",
        "freeze_damage": "Damage beku",
        "do_mob_loot": "Mob drop loot",
        "do_tile_drops": "Blok drop item saat hancur",
        "do_limited_crafting": "Crafting terbatas resep terbuka",
        "forgive_dead_players": "Piglin netral lupa marah saat pemain mati",
        "global_sound_events": "Suara global (wither, naga)",
        "lava_source_conversion": "Lava bisa buat obsidian infinite",
        "water_source_conversion": "Air infinite 2x2",
        "block_explosion_drop_decay": "Blok drop utuh saat ledakan blok",
        "mob_explosion_drop_decay": "Blok drop utuh saat ledakan mob",
        "tnt_explosion_drop_decay": "Blok drop utuh saat ledakan TNT",
        "max_command_forks": "Batas percabangan command",
    }

    def _api_gamerules(self):
        out = {}
        for name, typ in self.GAMERULES.items():
            try:
                r = self._strip(rcon.cmd(f"gamerule {name}"))
                m = re.search(r"currently set to\s+(.+)", r)
                out[name] = {"type": typ, "value": m.group(1).strip() if m else "?"}
            except (OSError, ConnectionError, PermissionError):
                out[name] = {"type": typ, "value": "?"}
        self._json({"rules": out, "desc": self.GAMERULE_DESC})

    def _api_gamerule_set(self, name, value):
        if name not in self.GAMERULES:
            return self._json({"error": "gamerule tidak dikenal"}, 400)
        typ = self.GAMERULES[name]
        if typ == "bool":
            v = str(value).lower()
            if v not in ("true", "false"):
                return self._json({"error": "nilai harus true/false"}, 400)
            value = v
        else:
            try:
                value = str(int(value))
            except (ValueError, TypeError):
                return self._json({"error": "nilai harus angka"}, 400)
        rcon.cmd(f"gamerule {name} {value}")
        log_activity("gamerule", f"{name} = {value}")
        return self._json({"ok": True})

    def _api_difficulty(self, value):
        if value not in ("peaceful", "easy", "normal", "hard"):
            return self._json({"error": "difficulty tidak valid"}, 400)
        rcon.cmd(f"difficulty {value}")
        write_props({"difficulty": value})
        log_activity("difficulty", value)
        return self._json({"ok": True})

    # ---------- dunia ----------
    WORLD_DIRS = ["world", "world_nether", "world_the_end"]

    def _world_size(self):
        total = 0
        for d in self.WORLD_DIRS:
            p = os.path.join(MC_DIR, d)
            if os.path.isdir(p):
                r = subprocess.run(["du", "-sb", p], capture_output=True, text=True)
                try:
                    total += int(r.stdout.split()[0])
                except (ValueError, IndexError):
                    pass
        return total

    def _api_world(self):
        seed = "?"
        try:
            r = self._strip(rcon.cmd("seed"))
            m = re.search(r"\[(-?\d+)\]", r)
            seed = m.group(1) if m else r[:40]
        except (OSError, ConnectionError, PermissionError):
            pass
        vals, _ = read_props()
        backups = sorted([f for f in os.listdir(os.path.join(MC_DIR, "backups"))
                          if f.endswith(".tar.gz")], reverse=True)[:20] \
            if os.path.isdir(os.path.join(MC_DIR, "backups")) else []
        self._json({"seed": seed, "level_name": vals.get("level-name", "world"),
                    "size_bytes": self._world_size(), "backups": backups})

    def _backup_world(self, tag):
        os.makedirs(os.path.join(MC_DIR, "backups"), exist_ok=True)
        ts = time.strftime("%Y%m%d-%H%M%S")
        fn = f"world-{tag}-{ts}.tar.gz"
        dest = os.path.join(MC_DIR, "backups", fn)
        dirs = [d for d in self.WORLD_DIRS if os.path.isdir(os.path.join(MC_DIR, d))]
        try:
            rcon.cmd("save-all flush")
        except (OSError, ConnectionError, PermissionError):
            pass
        time.sleep(2)
        r = subprocess.run(["tar", "-czf", dest] + dirs, cwd=MC_DIR,
                           capture_output=True, timeout=600)
        if r.returncode != 0 or not os.path.exists(dest):
            raise OSError("backup gagal")
        return fn

    def _api_world_backup(self):
        fn = self._backup_world("manual")
        log_activity("dunia", f"backup manual: {fn}")
        return self._json({"ok": True, "file": fn})

    def _api_world_seed(self, seed):
        seed = str(seed).strip()
        if not re.match(r"^-?\d{1,19}$", seed):
            return self._json({"error": "seed harus angka (maks 19 digit)"}, 400)
        fn = self._backup_world("sebelum-ganti-seed")
        subprocess.run(["systemctl", "stop", "minecraft.service"], capture_output=True)
        time.sleep(4)
        write_props({"level-seed": seed})
        for d in self.WORLD_DIRS:
            p = os.path.join(MC_DIR, d)
            if os.path.isdir(p):
                subprocess.run(["rm", "-rf", p], capture_output=True, timeout=120)
        subprocess.run(["systemctl", "start", "minecraft.service"], capture_output=True)
        log_activity("dunia", f"ganti seed → {seed} (backup: {fn})")
        return self._json({"ok": True, "backup": fn,
                           "message": "Dunia baru sedang di-generate (~1 menit)"})

    # ---------- file manager ----------
    FILE_EXTS = {".yml", ".yaml", ".properties", ".txt", ".json", ".log"}

    def _safe_mc_path(self, rel):
        rel = (rel or "").strip().lstrip("/")
        if not rel or ".." in rel.split("/"):
            raise ValueError("path tidak valid")
        p = os.path.realpath(os.path.join(MC_DIR, rel))
        if p != MC_DIR and not p.startswith(MC_DIR + os.sep):
            raise ValueError("path tidak valid")
        return p

    def _api_files(self, subdir):
        base = self._safe_mc_path(subdir or ".")
        if not os.path.isdir(base):
            return self._json({"error": "bukan direktori"}, 400)
        dirs, files = [], []
        for name in sorted(os.listdir(base)):
            if name.startswith("."):
                continue
            fp = os.path.join(base, name)
            rel = os.path.relpath(fp, MC_DIR)
            if os.path.isdir(fp):
                dirs.append(rel)
            elif os.path.splitext(name)[1].lower() in self.FILE_EXTS:
                try:
                    files.append({"path": rel, "size": os.path.getsize(fp)})
                except OSError:
                    pass
        parent = os.path.relpath(os.path.dirname(base), MC_DIR)
        self._json({"cwd": os.path.relpath(base, MC_DIR), "parent": None if parent == "." and base == MC_DIR else parent,
                    "dirs": dirs, "files": files})

    def _api_file_get(self, path):
        p = self._safe_mc_path(path)
        if not os.path.isfile(p) or os.path.getsize(p) > 300 * 1024:
            return self._json({"error": "file tidak valid / terlalu besar"}, 400)
        with open(p, encoding="utf-8", errors="replace") as f:
            return self._json({"path": path, "content": f.read()})

    def _api_file_put(self, path, content):
        p = self._safe_mc_path(path)
        if not os.path.isfile(p):
            return self._json({"error": "file tidak ada"}, 400)
        if len(content) > 300 * 1024:
            return self._json({"error": "konten terlalu besar"}, 400)
        bak = p + ".bak"
        try:
            with open(p, "rb") as f:
                old = f.read()
            with open(bak, "wb") as f:
                f.write(old)
            with open(p, "w", encoding="utf-8") as f:
                f.write(content)
        except OSError as e:
            return self._json({"error": str(e)}, 500)
        log_activity("file", f"edit {path}")
        return self._json({"ok": True, "backup": os.path.basename(bak),
                           "note": "Restart server jika mengubah konfigurasi"})

    # ---------- jadwal (systemd timer) ----------
    SCHED_FILE = os.path.join(CONFIG, "schedule.json")

    def _sched_load(self):
        try:
            with open(self.SCHED_FILE, encoding="utf-8") as f:
                return json.load(f)
        except (OSError, ValueError):
            return {}

    def _sched_save(self, data):
        os.makedirs(CONFIG, exist_ok=True)
        with open(self.SCHED_FILE, "w", encoding="utf-8") as f:
            json.dump(data, f)

    def _sched_apply(self, kind, hour, minute, enabled):
        timer, svc = f"mc-sched-{kind}.timer", f"mc-sched-{kind}.service"
        desc = "Restart otomatis" if kind == "restart" else "Backup dunia otomatis"
        if kind == "restart":
            exec_cmd = "/usr/bin/systemctl restart minecraft.service"
        else:
            exec_cmd = "/home/hatch/workspace/mc-portal/backup.sh"
        with open(f"/etc/systemd/system/{svc}", "w") as f:
            f.write(f"[Unit]\nDescription=Muse SMP {desc}\n\n"
                    f"[Service]\nType=oneshot\nExecStart={exec_cmd}\n")
        with open(f"/etc/systemd/system/{timer}", "w") as f:
            f.write(f"[Unit]\nDescription=Muse SMP {desc} (timer)\n\n"
                    f"[Timer]\nOnCalendar=*-*-* {hour:02d}:{minute:02d}:00\nPersistent=true\n\n"
                    f"[Install]\nWantedBy=timers.target\n")
        subprocess.run(["systemctl", "daemon-reload"], capture_output=True)
        if enabled:
            subprocess.run(["systemctl", "enable", "--now", timer], capture_output=True)
        else:
            subprocess.run(["systemctl", "disable", "--now", timer], capture_output=True)

    def _api_schedule_get(self):
        return self._json(self._sched_load())

    def _api_schedule_set(self, kind, hour, minute, enabled):
        if kind not in ("restart", "backup"):
            return self._json({"error": "jenis tidak valid"}, 400)
        try:
            hour, minute = int(hour), int(minute)
            assert 0 <= hour <= 23 and 0 <= minute <= 59
        except (ValueError, TypeError, AssertionError):
            return self._json({"error": "jam/menit tidak valid"}, 400)
        data = self._sched_load()
        if enabled:
            data[kind] = {"hour": hour, "minute": minute}
        else:
            data.pop(kind, None)
        self._sched_save(data)
        self._sched_apply(kind, hour, minute, enabled)
        log_activity("jadwal", f"{kind} {'ON' if enabled else 'OFF'}" +
                     (f" {hour:02d}:{minute:02d}" if enabled else ""))
        return self._json({"ok": True})


    # ---------- update paper ----------
    @staticmethod
    def _fetch_json(url, timeout=30):
        req = urllib.request.Request(url, headers=MR_UA)
        with urllib.request.urlopen(req, timeout=timeout) as r:
            return json.load(r)

    def _paper_builds(self):
        data = self._fetch_json("https://fill.papermc.io/v3/projects/paper/versions/26.3")
        builds = data.get("builds", [])
        return max(builds) if builds else None

    def _current_build(self):
        try:
            v = self._strip(rcon.cmd("version"))
            m = re.search(r"26\.3-(\d+)", v)
            return int(m.group(1)) if m else None
        except (OSError, ConnectionError, PermissionError):
            return None

    def _api_paper(self):
        cur, latest = self._current_build(), self._paper_builds()
        self._json({"current": cur, "latest": latest,
                    "update_available": bool(cur and latest and latest > cur)})

    def _api_paper_update(self):
        latest = self._paper_builds()
        if not latest:
            return self._json({"error": "tidak bisa cek versi terbaru"}, 502)
        cur = self._current_build()
        if cur and latest <= cur:
            return self._json({"error": "sudah versi terbaru"}, 400)
        info = self._fetch_json(
            f"https://fill.papermc.io/v3/projects/paper/versions/26.3/builds/{latest}")
        dl = (info.get("downloads") or {}).get("server:default") or {}
        url = dl.get("url")
        if not url or not url.startswith("https://fill-data.papermc.io/"):
            return self._json({"error": "URL download tidak valid"}, 502)
        tmp = os.path.join(MC_DIR, "paper.jar.new")
        req = urllib.request.Request(url, headers=MR_UA)
        with urllib.request.urlopen(req, timeout=900) as r, open(tmp, "wb") as f:
            while True:
                chunk = r.read(65536)
                if not chunk:
                    break
                f.write(chunk)
        if os.path.getsize(tmp) < 10 * 1024 * 1024:
            os.remove(tmp)
            return self._json({"error": "file download rusak/kecil"}, 502)
        subprocess.run(["systemctl", "stop", "minecraft.service"], capture_output=True)
        time.sleep(4)
        old = os.path.join(MC_DIR, "paper.jar")
        bak = os.path.join(MC_DIR, "paper.jar.bak")
        if os.path.exists(bak):
            os.remove(bak)
        os.rename(old, bak)
        os.rename(tmp, old)
        subprocess.run(["systemctl", "start", "minecraft.service"], capture_output=True)
        log_activity("paper", f"update ke build {latest}")
        return self._json({"ok": True, "build": latest,
                           "message": "Paper diupdate, server restart (~1 menit)"})

    def _api_logs(self):
        try:
            with open(LOG_FILE, encoding="utf-8", errors="replace") as f:
                lines = f.readlines()
        except OSError:
            lines = []
        return self._json({"lines": [l.rstrip("\n")[-300:] for l in lines[-200:]]})


def ensure_schedules():
    """Terapkan ulang jadwal tersimpan saat portal start (tahan VM replacement)."""
    try:
        with open(os.path.join(CONFIG, "schedule.json"), encoding="utf-8") as f:
            data = json.load(f)
    except (OSError, ValueError):
        return
    h = object.__new__(Handler)
    for kind, v in data.items():
        if kind in ("restart", "backup") and isinstance(v, dict):
            try:
                h._sched_apply(kind, int(v["hour"]), int(v["minute"]), True)
            except (ValueError, TypeError, OSError):
                pass

def main():
    os.makedirs(CONFIG, exist_ok=True)
    if not os.path.exists(os.path.join(CONFIG, "admin.hash")):
        print("FATAL: config/admin.hash belum ada. Buat dulu:")
        print("  python3 -c \"import hashlib,secrets; s=secrets.token_bytes(16);")
        print("    print(s.hex()+':'+hashlib.pbkdf2_hmac('sha256',b'PASSWORD',s,200000).hex())\" > config/admin.hash")
        raise SystemExit(1)
    srv = ThreadingHTTPServer(("127.0.0.1", 8082), Handler)
    print("mc-portal listening on 127.0.0.1:8082", flush=True)
    ensure_schedules()
    threading.Thread(target=history_tracker, daemon=True).start()
    srv.serve_forever()


if __name__ == "__main__":
    main()
