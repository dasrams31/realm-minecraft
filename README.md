# Realm Minecraft — Muse SMP

Backup of the Muse SMP Minecraft realm: web portal (landing + admin), world-building generators, and server configuration.

**Live:**
- Play: `mc.ramadanadipa.com` (Java Edition, Paper 26.3)
- Landing: https://realm.ramadanadipa.com/
- Admin: https://realm.ramadanadipa.com/manage

## Contents

### `portal/` — Web portal (Python stdlib only)
- `portal.py` — Backend: RCON control, admin auth, public status API, player history
- `static/landing.html` — Public landing page (live status, pioneers, gallery, FAQ)
- `static/` — Admin panel (`/manage`): console, players, plugins, backups, config editor
- `make_*.py` — World generators (schematic builders, run with `nbtlib`):
  - `make_castle.py` — 5-story tenshu castle
  - `make_town_buildings.py`, `make_town_variety.py` — shogunate town buildings
  - `make_metro*.py` — procedural unique-building generator (60–100 variants)
  - `make_village*.py` — Japanese village districts
  - `make_satellite.py` — satellite villages
  - `make_landmark.py` — sumo arena, kabuki theater, shogun palace
  - `make_gate.py`, `make_towers.py`, `make_niceto.py` — gates, towers, academy, night market
- `backup.sh` — world backup helper

Schematics output to `plugins/WorldEdit/schematics/`, paste via console:
```
//world world
//pos1 x,y,z
//schem load name.schem
//paste -a
```

### `server-config/` — Paper server configuration
- `server.properties` — server settings (seed, view distance, online-mode, etc.)

## Not included (by design)
- `world/` — world files (235M+, backed up separately as tar.gz)
- `paper.jar` — download from papermc.io
- Secrets: `config/rcon_password`, `config/admin.hash`, `config/bot_password` — never commit these
- `plugins/` binaries — install via the portal's Modrinth tab or manually

## Setup (fresh server)
1. Install Paper 26.3, Java 25
2. Copy `server-config/server.properties`
3. Install plugins: WorldEdit, WorldGuard, ViaVersion, ViaBackwards, AuthMeReloaded
4. Copy `portal/` beside the server dir, configure RCON + admin password
5. Run generators as needed, paste schematics via console

---
Hand-maintained with ❤ — Muse SMP
