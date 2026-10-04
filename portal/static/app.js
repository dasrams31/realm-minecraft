const $ = id => document.getElementById(id);

async function api(path, method = "GET", data) {
  const r = await fetch(path, {
    method,
    headers: { "Content-Type": "application/json" },
    body: data ? JSON.stringify(data) : undefined,
  });
  if (r.status === 401) { showLogin(); throw new Error("unauthorized"); }
  const j = await r.json().catch(() => ({}));
  if (!r.ok) throw new Error(j.error || ("HTTP " + r.status));
  return j;
}

function showLogin() {
  $("login-screen").classList.remove("hidden");
  $("app").classList.add("hidden");
}
function showApp() {
  $("login-screen").classList.add("hidden");
  $("app").classList.remove("hidden");
}

// ---------- login ----------
$("login-btn").onclick = doLogin;
$("pw").onkeydown = e => { if (e.key === "Enter") doLogin(); };
async function doLogin() {
  $("login-err").textContent = "";
  try {
    await api("/api/login", "POST", { password: $("pw").value });
    $("pw").value = "";
    showApp();
    refreshAll();
  } catch (e) {
    $("login-err").textContent = e.message === "unauthorized" ? "" : "Password salah.";
  }
}
$("logout-btn").onclick = async () => {
  await api("/api/logout", "POST").catch(() => {});
  showLogin();
};

// ---------- tabs ----------
document.querySelectorAll(".tab").forEach(t => {
  t.onclick = () => {
    document.querySelectorAll(".tab").forEach(x => x.classList.remove("active"));
    document.querySelectorAll(".tabpanel").forEach(x => x.classList.remove("active"));
    t.classList.add("active");
    $("tab-" + t.dataset.tab).classList.add("active");
    if (t.dataset.tab === "log") loadActivity();
  };
});

// ---------- activity log ----------
function esc(s) {
  return String(s).replace(/&/g, "&amp;").replace(/</g, "&lt;").replace(/>/g, "&gt;");
}
async function loadActivity() {
  const box = $("act-list");
  try {
    const j = await api("/api/activity");
    const items = j.activity || [];
    if (!items.length) { box.innerHTML = '<p class="hint">Belum ada aktivitas tercatat.</p>'; return; }
    box.innerHTML = items.map(e => {
      const d = new Date(e.t * 1000);
      const ts = d.toLocaleDateString("id-ID", { day: "2-digit", month: "short" }) + " " +
                 d.toLocaleTimeString("id-ID", { hour: "2-digit", minute: "2-digit" });
      return `<div class="act-row"><span class="t">${ts}</span><span class="a">${esc(e.action)}</span><span class="d">${esc(e.detail || "")}</span></div>`;
    }).join("");
  } catch (e) { box.innerHTML = '<p class="hint">Gagal memuat.</p>'; }
}
$("act-reload").onclick = loadActivity;

// ---------- status ----------
async function loadStatus() {
  try {
    const s = await api("/api/status");
    const up = s.server_up;
    $("svc-dot").className = "dot " + (up ? "on" : "off");
    $("svc-text").textContent = up ? "Online" : "Offline";
    $("st-cond").textContent = up ? "● Online" : "● Offline";
    $("st-cond").style.color = up ? "var(--green)" : "var(--red)";
    $("st-ver").textContent = s.version || "—";
    $("st-motd").textContent = s.motd || "—";
    $("st-players").textContent = up ? `${s.online} / ${s.max}` : "—";
    $("st-diff").textContent = s.difficulty || "—";
    $("st-cheat").textContent = s.cheats ? "NYALA (OP semua)" : "MATI";
    $("st-cheat").style.color = s.cheats ? "var(--green)" : "var(--dim)";
  } catch (e) { /* stay silent, will retry */ }
}

$("say-btn").onclick = async () => {
  const t = $("say-text").value.trim();
  if (!t) return;
  try { await api("/api/cmd", "POST", { command: "say " + t }); $("say-text").value = ""; }
  catch (e) { alert("Gagal: " + e.message); }
};

// ---------- power ----------
for (const [id, act] of [["pwr-start", "start"], ["pwr-restart", "restart"], ["pwr-stop", "stop"]]) {
  $(id).onclick = async () => {
    if (act === "stop" && !confirm("Matikan server? Pemain akan terputus.")) return;
    $("pwr-msg").textContent = "Menjalankan " + act + "…";
    try {
      const r = await api("/api/power", "POST", { action: act });
      $("pwr-msg").textContent = "Service: " + (r.service_active ? "aktif" : "mati");
      setTimeout(loadStatus, 4000);
    } catch (e) { $("pwr-msg").textContent = "Gagal: " + e.message; }
  };
}

// ---------- players ----------
function prow(name, isOp, isOnline) {
  const d = document.createElement("div");
  d.className = "prow";
  const left = document.createElement("span");
  left.innerHTML = `<span class="nm"></span>` + (isOp ? `<span class="badge-op">OP</span>` : "");
  left.querySelector(".nm").textContent = name;
  const acts = document.createElement("div");
  acts.className = "acts";
  const btn = (label, cls, fn) => {
    const b = document.createElement("button");
    b.className = "mc-btn small " + cls; b.textContent = label;
    b.onclick = fn; acts.appendChild(b);
  };
  if (isOnline) {
    btn(isOp ? "Cabut OP" : "Jadikan OP", "", async () => {
      await api("/api/player/" + (isOp ? "deop" : "op"), "POST", { name }); loadPlayers();
    });
    btn("Kick", "red", async () => {
      if (confirm("Kick " + name + "?")) { await api("/api/player/kick", "POST", { name }); loadPlayers(); }
    });
  } else if (isOp) {
    btn("Cabut OP", "", async () => { await api("/api/player/deop", "POST", { name }); loadPlayers(); });
  }
  d.appendChild(left); d.appendChild(acts);
  return d;
}

async function loadPlayers() {
  try {
    const p = await api("/api/players");
    const ops = new Set(p.ops.map(n => n.toLowerCase()));
    const box = $("online-list"); box.innerHTML = "";
    if (!p.server_up) box.innerHTML = '<p class="hint">Server offline.</p>';
    else if (!p.online.length) box.innerHTML = '<p class="hint">Tidak ada pemain online.</p>';
    p.online.forEach(n => box.appendChild(prow(n, ops.has(n.toLowerCase()), true)));

    const ob = $("ops-list"); ob.innerHTML = "";
    if (!p.ops.length) ob.innerHTML = '<p class="hint">Belum ada OP.</p>';
    p.ops.forEach(n => ob.appendChild(prow(n, true, p.online.map(x => x.toLowerCase()).includes(n.toLowerCase()))));

    const wb = $("wl-list"); wb.innerHTML = "";
    if (!p.whitelisted.length) wb.innerHTML = '<p class="hint">Whitelist kosong.</p>';
    p.whitelisted.forEach(n => {
      const d = document.createElement("div"); d.className = "prow";
      const s = document.createElement("span"); s.textContent = n;
      const b = document.createElement("button"); b.className = "mc-btn small red"; b.textContent = "Hapus";
      b.onclick = async () => { await api("/api/whitelist", "POST", { action: "remove", name: n }); loadPlayers(); };
      d.appendChild(s); d.appendChild(b); wb.appendChild(d);
    });
    $("wl-toggle").checked = p.whitelist_enabled;
  } catch (e) { /* silent */ }
}

$("op-add").onclick = async () => {
  const n = $("op-name").value.trim(); if (!n) return;
  try { await api("/api/player/op", "POST", { name: n }); $("op-name").value = ""; loadPlayers(); }
  catch (e) { alert("Gagal: " + e.message); }
};
$("wl-add").onclick = async () => {
  const n = $("wl-name").value.trim(); if (!n) return;
  try { await api("/api/whitelist", "POST", { action: "add", name: n }); $("wl-name").value = ""; loadPlayers(); }
  catch (e) { alert("Gagal: " + e.message); }
};
$("wl-toggle").onchange = async e => {
  try { await api("/api/whitelist", "POST", { action: e.target.checked ? "enable" : "disable" }); loadPlayers(); loadRules(); }
  catch (err) { alert("Gagal: " + err.message); e.target.checked = !e.target.checked; }
};
$("ban-btn").onclick = async () => {
  const n = $("ban-name").value.trim(); if (!n) return;
  if (!confirm("Ban " + n + "?")) return;
  try { await api("/api/player/ban", "POST", { name: n, reason: $("ban-reason").value.trim() }); $("ban-name").value = ""; }
  catch (e) { alert("Gagal: " + e.message); }
};
$("pardon-btn").onclick = async () => {
  const n = $("ban-name").value.trim(); if (!n) return;
  try { await api("/api/player/pardon", "POST", { name: n }); $("ban-name").value = ""; alert(n + " di-unban."); }
  catch (e) { alert("Gagal: " + e.message); }
};

// ---------- cheats ----------
async function loadCheats() {
  try {
    const c = await api("/api/cheats");
    const on = c.enabled;
    $("cheat-state").textContent = on ? "● NYALA" : "● MATI";
    $("cheat-state").className = "bigstate " + (on ? "on" : "off");
    $("cheat-toggle").textContent = on ? "Matikan Cheat" : "Nyalakan Cheat";
    $("cheat-toggle").className = "mc-btn big " + (on ? "red" : "green");
  } catch (e) {}
}
$("cheat-toggle").onclick = async () => {
  const wantOn = $("cheat-state").classList.contains("off");
  if (!confirm((wantOn ? "Nyalakan" : "Matikan") + " mode cheat untuk semua pemain online?")) return;
  $("cheat-msg").textContent = "Memproses…";
  try {
    const r = await api("/api/cheats", "POST", { enabled: wantOn });
    $("cheat-msg").textContent = "Berhasil — " + (r.affected.length ? r.affected.length + " pemain diproses." : "tidak ada pemain online.");
    loadCheats(); loadPlayers(); loadStatus();
  } catch (e) { $("cheat-msg").textContent = "Gagal: " + e.message; }
};

async function loadRules() {
  try {
    const s = await api("/api/settings");
    const v = s.values;
    $("rule-pvp").textContent = v["pvp"] === "true" ? "Aktif" : "Mati";
    $("rule-cb").textContent = v["enable-command-block"] === "true" ? "Aktif" : "Mati";
    $("rule-wl").textContent = v["white-list"] === "true" ? "Aktif" : "Mati";
  } catch (e) {}
}

// ---------- settings ----------
let settingsMeta = {}, settingsBools = [];
async function loadSettings() {
  try {
    const s = await api("/api/settings");
    settingsMeta = s.meta; settingsBools = s.bools;
    const f = $("settings-form"); f.innerHTML = "";
    for (const k of Object.keys(settingsMeta)) {
      const v = s.values[k] || "";
      const row = document.createElement("div"); row.className = "srow";
      const lab = document.createElement("label");
      lab.innerHTML = `<b></b><span class="meta"></span>`;
      lab.querySelector("b").textContent = k;
      lab.querySelector(".meta").textContent = settingsMeta[k];
      let inp;
      if (settingsBools.includes(k)) {
        inp = document.createElement("input"); inp.type = "checkbox"; inp.checked = v === "true";
      } else if (k === "difficulty") {
        inp = document.createElement("select");
        ["peaceful", "easy", "normal", "hard"].forEach(o => {
          const op = document.createElement("option"); op.value = o; op.textContent = o;
          if (o === v) op.selected = true; inp.appendChild(op);
        });
      } else if (k === "gamemode") {
        inp = document.createElement("select");
        ["survival", "creative", "adventure", "spectator"].forEach(o => {
          const op = document.createElement("option"); op.value = o; op.textContent = o;
          if (o === v) op.selected = true; inp.appendChild(op);
        });
      } else {
        inp = document.createElement("input"); inp.type = "text"; inp.value = v;
      }
      inp.dataset.key = k;
      row.appendChild(lab); row.appendChild(inp); f.appendChild(row);
    }
  } catch (e) {}
}
$("save-settings").onclick = async () => {
  const vals = {};
  $("settings-form").querySelectorAll("[data-key]").forEach(el => {
    vals[el.dataset.key] = el.type === "checkbox" ? (el.checked ? "true" : "false") : el.value;
  });
  $("settings-msg").textContent = "Menyimpan…";
  try {
    await api("/api/settings", "POST", { values: vals });
    $("settings-msg").textContent = "Tersimpan. Restart server agar berlaku.";
    loadRules();
  } catch (e) { $("settings-msg").textContent = "Gagal: " + e.message; }
};

// ---------- console ----------
$("cmd-send").onclick = async () => {
  const c = $("cmd-input").value.trim(); if (!c) return;
  $("cmd-out").textContent = "…";
  try {
    const r = await api("/api/cmd", "POST", { command: c });
    $("cmd-out").textContent = "> " + c + "\n" + (r.output || "(tidak ada output)");
  } catch (e) { $("cmd-out").textContent = "Gagal: " + e.message; }
  $("cmd-input").value = "";
};
$("cmd-input").onkeydown = e => { if (e.key === "Enter") $("cmd-send").click(); };
$("logs-reload").onclick = async () => {
  try {
    const r = await api("/api/logs");
    $("logs-out").textContent = r.lines.join("\n") || "(log kosong)";
    $("logs-out").scrollTop = $("logs-out").scrollHeight;
  } catch (e) { $("logs-out").textContent = "Gagal: " + e.message; }
};

// ---------- plugins ----------
function fmtSize(b) {
  if (b > 1048576) return (b / 1048576).toFixed(1) + " MB";
  return Math.max(1, Math.round(b / 1024)) + " KB";
}
async function loadPlugins() {
  const box = $("plugin-list");
  try {
    const r = await api("/api/plugins");
    box.innerHTML = "";
    if (!r.plugins.length) box.innerHTML = '<p class="hint">Belum ada plugin. Cari di Modrinth atau upload manual.</p>';
    r.plugins.forEach(p => {
      const d = document.createElement("div"); d.className = "prow";
      const left = document.createElement("span");
      left.innerHTML = `<span class="nm"></span> <span class="hint">${fmtSize(p.size)}</span>` +
        (p.enabled ? "" : `<span class="badge-op" style="background:#4a4a4a">NONAKTIF</span>`);
      left.querySelector(".nm").textContent = p.name;
      const acts = document.createElement("div"); acts.className = "acts";
      const t = document.createElement("button");
      t.className = "mc-btn small"; t.textContent = p.enabled ? "Nonaktifkan" : "Aktifkan";
      t.onclick = async () => {
        await api("/api/plugins/toggle", "POST", { file: p.file, enabled: !p.enabled });
        loadPlugins();
      };
      const del = document.createElement("button");
      del.className = "mc-btn small red"; del.textContent = "Hapus";
      del.onclick = async () => {
        if (confirm("Hapus plugin " + p.name + "?")) {
          await api("/api/plugins/delete", "POST", { file: p.file });
          loadPlugins();
        }
      };
      acts.appendChild(t); acts.appendChild(del);
      d.appendChild(left); d.appendChild(acts); box.appendChild(d);
    });
  } catch (e) { box.innerHTML = '<p class="hint">Gagal memuat.</p>'; }
}
$("plugin-upload").onclick = async () => {
  const f = $("plugin-file").files[0];
  if (!f) { $("plugin-up-msg").textContent = "Pilih file .jar dulu."; return; }
  if (!/\.jar$/i.test(f.name)) { $("plugin-up-msg").textContent = "Hanya file .jar."; return; }
  $("plugin-up-msg").textContent = "Mengupload…";
  const fd = new FormData(); fd.append("file", f);
  try {
    const r = await fetch("/api/plugins/upload", { method: "POST", body: fd });
    const j = await r.json();
    if (!r.ok) throw new Error(j.error || r.status);
    $("plugin-up-msg").textContent = "Terupload: " + j.file + ". Restart server agar aktif.";
    $("plugin-file").value = ""; loadPlugins();
  } catch (e) { $("plugin-up-msg").textContent = "Gagal: " + e.message; }
};
$("plugin-restart").onclick = async () => {
  if (!confirm("Restart server sekarang? Pemain akan terputus sebentar.")) return;
  await api("/api/power", "POST", { action: "restart" });
  setTimeout(() => { loadStatus(); loadPlayers(); }, 5000);
};
$("mr-search").onclick = async () => {
  const q = $("mr-q").value.trim(); if (!q) return;
  $("mr-msg").textContent = "Mencari…"; $("mr-hits").innerHTML = ""; $("mr-vers").innerHTML = "";
  try {
    const r = await api("/api/plugins/search?q=" + encodeURIComponent(q));
    $("mr-msg").textContent = r.hits.length ? "" : "Tidak ketemu.";
    r.hits.forEach(h => {
      const d = document.createElement("div"); d.className = "prow";
      const left = document.createElement("span");
      left.innerHTML = `<span class="nm"></span><br><span class="hint"></span>`;
      left.querySelector(".nm").textContent = h.title;
      left.querySelector(".hint").textContent = h.description;
      const b = document.createElement("button");
      b.className = "mc-btn small"; b.textContent = "Pilih versi";
      b.onclick = () => showVersions(h.id, h.title);
      d.appendChild(left); d.appendChild(b); $("mr-hits").appendChild(d);
    });
  } catch (e) { $("mr-msg").textContent = "Gagal: " + e.message; }
};
$("mr-q").onkeydown = e => { if (e.key === "Enter") $("mr-search").click(); };
async function showVersions(pid, title) {
  $("mr-vers").innerHTML = '<p class="hint">Memuat versi…</p>';
  try {
    const r = await api("/api/plugins/versions?id=" + encodeURIComponent(pid));
    const box = $("mr-vers"); box.innerHTML = "";
    const h = document.createElement("p"); h.className = "hint";
    h.textContent = "Versi " + title + " (Paper):"; box.appendChild(h);
    if (!r.versions.length) box.innerHTML += '<p class="hint">Tidak ada versi Paper.</p>';
    r.versions.forEach(v => {
      const d = document.createElement("div"); d.className = "prow";
      const left = document.createElement("span");
      left.innerHTML = `<span class="nm"></span> <span class="hint"></span>`;
      left.querySelector(".nm").textContent = v.version_number;
      left.querySelector(".hint").textContent = (v.game_versions || []).join(", ") + " · " + v.date;
      const b = document.createElement("button");
      b.className = "mc-btn small green"; b.textContent = "Install";
      b.onclick = async () => {
        if (!confirm("Install " + title + " " + v.version_number + "?")) return;
        b.textContent = "…"; b.disabled = true;
        try {
          const j = await api("/api/plugins/install", "POST", { version_id: v.version_id });
          $("mr-msg").textContent = "Terinstall: " + j.file + ". Restart server agar aktif.";
          loadPlugins();
        } catch (e) { $("mr-msg").textContent = "Gagal: " + e.message; }
        b.textContent = "Install"; b.disabled = false;
      };
      d.appendChild(left); d.appendChild(b); box.appendChild(d);
    });
    box.scrollIntoView({ behavior: "smooth", block: "nearest" });
  } catch (e) { $("mr-msg").textContent = "Gagal: " + e.message; }
}

// ---------- perf ----------
const tpsHist = [];
function fmtDur(s) {
  if (s == null) return "…";
  s = Math.floor(s);
  const h = Math.floor(s / 3600), m = Math.floor(s % 3600 / 60);
  return h > 0 ? `${h}j ${m}m` : `${m}m ${s % 60}d`;
}
async function loadPerf() {
  try {
    const p = await api("/api/perf");
    const t = p.tps.m1;
    $("pf-tps").textContent = t == null ? "…" : t.toFixed(1);
    $("pf-tps").style.color = t == null ? "" : (t >= 18 ? "var(--green)" : (t >= 14 ? "var(--yellow)" : "var(--red)"));
    $("pf-mspt").textContent = p.mspt == null ? "…" : p.mspt.toFixed(1) + " ms";
    $("pf-ram").textContent = p.mem_mb == null ? "…" : `${p.mem_mb} / ${p.mem_max_mb} MB`;
    $("pf-up").textContent = fmtDur(p.uptime_s);
    if (t != null) {
      tpsHist.push(t); if (tpsHist.length > 60) tpsHist.shift();
      drawTps();
    }
  } catch (e) {}
}
function drawTps() {
  const c = $("tps-chart"); if (!c) return;
  const x = c.getContext("2d"), W = c.width, H = c.height;
  x.clearRect(0, 0, W, H);
  x.strokeStyle = "#3a3a3a"; x.beginPath();
  const y20 = H - (20 / 22) * H;
  x.moveTo(0, y20); x.lineTo(W, y20); x.stroke();
  if (tpsHist.length < 2) return;
  x.strokeStyle = "#5fca35"; x.lineWidth = 2; x.beginPath();
  tpsHist.forEach((t, i) => {
    const px = (i / (tpsHist.length - 1)) * W, py = H - (Math.min(t, 22) / 22) * H;
    i ? x.lineTo(px, py) : x.moveTo(px, py);
  });
  x.stroke(); x.lineWidth = 1;
}

// ---------- paper update ----------
async function loadPaper() {
  try {
    const r = await api("/api/paper");
    $("pu-cur").textContent = r.current == null ? "?" : "26.3 build " + r.current;
    $("pu-latest").textContent = r.latest == null ? "?" : "26.3 build " + r.latest;
    const btn = $("pu-btn");
    if (r.update_available) { btn.classList.remove("hidden"); $("pu-msg").textContent = "Update tersedia!"; }
    else { btn.classList.add("hidden"); $("pu-msg").textContent = r.latest ? "Sudah versi terbaru." : ""; }
  } catch (e) {}
}
$("pu-btn").onclick = async () => {
  if (!confirm("Update Paper ke build terbaru? Server akan restart.")) return;
  $("pu-msg").textContent = "Mengunduh & mengupdate… (bisa 1-3 menit)";
  try {
    const r = await api("/api/paper/update", "POST");
    $("pu-msg").textContent = r.message;
    setTimeout(() => { loadPaper(); loadStatus(); }, 15000);
  } catch (e) { $("pu-msg").textContent = "Gagal: " + e.message; }
};

// ---------- dunia ----------
function fmtBytes(b) {
  if (b > 1073741824) return (b / 1073741824).toFixed(2) + " GB";
  if (b > 1048576) return (b / 1048576).toFixed(1) + " MB";
  return Math.round(b / 1024) + " KB";
}
async function loadWorld() {
  try {
    const w = await api("/api/world");
    $("w-seed").textContent = w.seed;
    $("w-size").textContent = fmtBytes(w.size_bytes);
    const box = $("w-backups"); box.innerHTML = "";
    if (!w.backups.length) box.innerHTML = '<p class="hint">Belum ada backup.</p>';
    w.backups.forEach(fn => {
      const d = document.createElement("div"); d.className = "prow";
      const s = document.createElement("span"); s.textContent = fn;
      const a = document.createElement("a");
      a.href = "/api/world/download?file=" + encodeURIComponent(fn);
      a.className = "mc-btn small"; a.textContent = "Unduh"; a.style.textDecoration = "none";
      d.appendChild(s); d.appendChild(a); box.appendChild(d);
    });
  } catch (e) {}
}
$("w-backup").onclick = async () => {
  $("w-msg").textContent = "Membackup…";
  try {
    const r = await api("/api/world/backup", "POST");
    $("w-msg").textContent = "Backup tersimpan: " + r.file;
    loadWorld();
  } catch (e) { $("w-msg").textContent = "Gagal: " + e.message; }
};
$("w-seed-btn").onclick = async () => {
  const s = $("w-seed-in").value.trim();
  if (!/^-?\d{1,19}$/.test(s)) { alert("Seed harus angka."); return; }
  if (!confirm("Ganti seed ke " + s + "? Dunia lama di-backup, dunia baru di-generate (~1 menit). Pemain akan terputus.")) return;
  $("w-msg").textContent = "Mengganti seed…";
  try {
    const r = await api("/api/world/seed", "POST", { seed: s });
    $("w-msg").textContent = r.message + " Backup: " + r.backup;
    $("w-seed-in").value = "";
    setTimeout(() => { loadWorld(); loadStatus(); }, 20000);
  } catch (e) { $("w-msg").textContent = "Gagal: " + e.message; }
};

// ---------- gamerules ----------
async function loadGamerules() {
  const box = $("gr-list");
  try {
    const r = await api("/api/gamerules");
    box.innerHTML = "";
    Object.keys(r.rules).sort().forEach(name => {
      const g = r.rules[name], desc = (r.desc && r.desc[name]) || "";
      const row = document.createElement("div"); row.className = "grow";
      const left = document.createElement("div"); left.className = "gl";
      left.innerHTML = `<b></b><span></span>`;
      left.querySelector("b").textContent = name;
      left.querySelector("span").textContent = desc;
      const gv = document.createElement("div"); gv.className = "gv";
      let inp;
      if (g.type === "bool") {
        inp = document.createElement("input"); inp.type = "checkbox";
        inp.checked = g.value === "true";
        inp.onchange = () => setGamerule(name, inp.checked ? "true" : "false", inp);
      } else {
        inp = document.createElement("input"); inp.type = "text"; inp.value = g.value;
        const b = document.createElement("button");
        b.className = "mc-btn small"; b.textContent = "OK";
        b.onclick = () => setGamerule(name, inp.value.trim(), inp);
        gv.appendChild(inp); gv.appendChild(b);
      }
      if (g.type === "bool") gv.appendChild(inp);
      row.appendChild(left); row.appendChild(gv); box.appendChild(row);
    });
  } catch (e) { box.innerHTML = '<p class="hint">Gagal memuat (server offline?).</p>'; }
}
async function setGamerule(name, value, el) {
  try {
    await api("/api/gamerule", "POST", { name, value });
    el.style.outline = "2px solid var(--green)";
    setTimeout(() => el.style.outline = "", 800);
  } catch (e) { alert("Gagal: " + e.message); loadGamerules(); }
}
$("diff-btn").onclick = async () => {
  try {
    await api("/api/difficulty", "POST", { value: $("diff-sel").value });
    alert("Difficulty diganti ke " + $("diff-sel").value);
    loadStatus();
  } catch (e) { alert("Gagal: " + e.message); }
};

// ---------- files ----------
let fileCur = ".", fileOpen = null;
async function loadFiles(dir) {
  fileCur = dir || ".";
  const box = $("file-list");
  try {
    const r = await api("/api/files?dir=" + encodeURIComponent(fileCur));
    $("file-cwd").textContent = "/" + (r.cwd === "." ? "" : r.cwd);
    box.innerHTML = "";
    r.dirs.forEach(d => {
      const row = document.createElement("div"); row.className = "prow";
      const s = document.createElement("span"); s.textContent = "📁 " + d.split("/").pop();
      row.appendChild(s);
      row.onclick = () => loadFiles(d);
      box.appendChild(row);
    });
    r.files.forEach(f => {
      const row = document.createElement("div"); row.className = "prow";
      const s = document.createElement("span");
      s.textContent = "📄 " + f.path.split("/").pop() + " ";
      const hz = document.createElement("span"); hz.className = "hint"; hz.textContent = fmtBytes(f.size);
      s.appendChild(hz); row.appendChild(s);
      row.onclick = () => openFile(f.path);
      box.appendChild(row);
    });
    if (!r.dirs.length && !r.files.length) box.innerHTML = '<p class="hint">Kosong.</p>';
    $("file-up").onclick = e => { e.preventDefault(); if (r.parent) loadFiles(r.parent); };
  } catch (e) { box.innerHTML = '<p class="hint">Gagal memuat.</p>'; }
}
async function openFile(path) {
  try {
    const r = await api("/api/file?path=" + encodeURIComponent(path));
    fileOpen = path;
    $("file-ed-title").textContent = "Edit: " + path;
    $("file-ed").value = r.content;
    $("file-editor-panel").classList.remove("hidden");
    $("file-msg").textContent = "";
    $("file-editor-panel").scrollIntoView({ behavior: "smooth", block: "nearest" });
  } catch (e) { alert("Gagal: " + e.message); }
}
$("file-save").onclick = async () => {
  if (!fileOpen) return;
  try {
    const r = await api("/api/file", "POST", { path: fileOpen, content: $("file-ed").value });
    $("file-msg").textContent = "Tersimpan (backup: " + r.backup + "). " + r.note;
  } catch (e) { $("file-msg").textContent = "Gagal: " + e.message; }
};
$("file-cancel").onclick = () => { $("file-editor-panel").classList.add("hidden"); fileOpen = null; };

// ---------- jadwal ----------
async function loadSchedule() {
  try {
    const s = await api("/api/schedule");
    for (const [p, k] of [["sch-r", "restart"], ["sch-b", "backup"]]) {
      const v = s[k];
      $(p + "-on").checked = !!v;
      if (v) { $(p + "-h").value = v.hour; $(p + "-m").value = v.minute; }
    }
  } catch (e) {}
}
async function saveSchedule(kind, p) {
  try {
    await api("/api/schedule", "POST", {
      kind, hour: $(p + "-h").value, minute: $(p + "-m").value,
      enabled: $(p + "-on").checked,
    });
    alert("Jadwal tersimpan.");
  } catch (e) { alert("Gagal: " + e.message); }
}
$("sch-r-save").onclick = () => saveSchedule("restart", "sch-r");
$("sch-b-save").onclick = () => saveSchedule("backup", "sch-b");

// ---------- boot ----------
function refreshAll() { loadStatus(); loadPlayers(); loadCheats(); loadRules(); loadSettings(); loadPlugins(); loadPerf(); loadPaper(); loadWorld(); loadGamerules(); loadFiles("."); loadSchedule(); }
(async () => {
  try {
    const me = await api("/api/me");
    if (me.logged_in) { showApp(); refreshAll(); } else showLogin();
  } catch (e) { showLogin(); }
})();
setInterval(() => { if (!$("app").classList.contains("hidden")) { loadStatus(); loadPerf(); } }, 15000);
