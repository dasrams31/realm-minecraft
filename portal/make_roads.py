#!/usr/bin/env python3
"""Jalan setapak antar bangunan, mengikuti kontur tanah. Paste dengan //paste -a."""
import nbtlib, math, struct, zlib, tempfile, os, re
from nbtlib import Compound, Int, Short, ByteArray, IntArray, List

REG = '/home/hatch/workspace/minecraft/server/world/dimensions/minecraft/overworld/region/'
_regcache = {}

def load_reg(rf):
    if rf not in _regcache:
        _regcache[rf] = open(REG + rf, 'rb').read()
    return _regcache[rf]

def get_chunk(data, cx, cz):
    lx, lz = cx & 31, cz & 31
    loc = struct.unpack('>I', data[(lx + lz*32)*4:(lx + lz*32)*4+4])[0]
    if loc == 0:
        return None
    off = (loc >> 8) * 4096
    ln = struct.unpack('>I', data[off:off+4])[0]
    raw = zlib.decompress(data[off+5:off+5+ln-1])
    fd, tp = tempfile.mkstemp(); os.write(fd, raw); os.close(fd)
    ch = nbtlib.load(tp, gzipped=False); os.unlink(tp)
    return ch

def block_at(chunk, x, y, z):
    sy = y // 16
    sec = next((s for s in chunk['sections'] if int(s['Y']) == sy), None)
    if sec is None: return 'air'
    bs = sec.get('block_states')
    if bs is None: return 'air'
    pal = list(bs['palette'])
    if len(pal) == 1:
        b = str(pal[0])
    else:
        bpb = max(4, math.ceil(math.log2(len(pal))))
        arr = list(bs['data'])
        li = ((y % 16) * 256) + ((z % 16) * 16) + (x % 16)
        vp = 64 // bpb; wi = li // vp; bi = (li % vp) * bpb
        word = int(arr[wi])
        if bi + bpb > 64 and wi + 1 < len(arr): word |= int(arr[wi+1]) << 64
        b = str(pal[(word >> bi) & ((1 << bpb) - 1)])
    m = re.search(r'minecraft:([a-z_]+)', b)
    return m.group(1) if m else 'air'

def terrain_h(x, z):
    cx, cz = x // 16, z // 16
    try:
        ch = get_chunk(load_reg(f"r.{cx//32}.{cz//32}.mca"), cx, cz)
    except Exception:
        return 90
    if not ch: return 90
    for y in range(160, 55, -1):
        b = block_at(ch, x % 16, y, z % 16)
        # abaikan dedaunan & salju saat cari tanah
        if b not in ('air', 'oak_leaves', 'snow', 'snow_layer', 'grass', 'tall_grass',
                     'pink_petals', 'torch', 'lantern', 'oak_fence', 'cobblestone_wall'):
            return y
    return 90

# rute: (x1,z1) -> (x2,z2)
routes = [
    (0, 20, 18, 25),        # spawn -> loket
    (0, 20, -25, -8),       # spawn -> zen
    (-10, 25, -63, 25),     # spawn -> gerbang barat desa
    (-20, 2, 0, -25),       # desa utara -> onsen
    (10, 58, 0, 72),        # desa selatan -> dojo
    (-63, 20, -75, -10),    # desa barat -> jinja
    (54, 40, 32, 75),       # desa timur -> jembatan
]

blocks = {}
def put(x, y, z, b):
    blocks[(x, y, z)] = b

for x1, z1, x2, z2 in routes:
    dx, dz = x2 - x1, z2 - z1
    steps = max(abs(dx), abs(dz)) * 2
    prev_y = None
    for i in range(steps + 1):
        t = i / steps
        # sedikit lengkungan alami
        curve = math.sin(t * math.pi) * 3
        px = int(x1 + dx * t + (-dz / max(1, abs(dx)+abs(dz))) * curve)
        pz = int(z1 + dz * t + (dx / max(1, abs(dx)+abs(dz))) * curve)
        y = terrain_h(px, pz)
        # arah tegak lurus untuk lebar 3
        length = math.hypot(dx, dz) or 1
        nx, nz = -dz / length, dx / length
        for w in (-1, 0, 1):
            bx, bz = int(px + nx * w), int(pz + nz * w)
            by = terrain_h(bx, bz)
            # tangga jika menanjak
            if prev_y is not None and by > prev_y + 1:
                put(bx, by, bz, "minecraft:cobblestone_stairs[facing=north,half=bottom,shape=straight]")
            else:
                # pola: tengah gravel, tepi cobble
                put(bx, by, bz, "minecraft:gravel" if w == 0 else "minecraft:cobblestone")
            # bersihkan 2 blok di atas jalan (daun dkk)
            put(bx, by + 1, bz, "minecraft:air")
            put(bx, by + 2, bz, "minecraft:air")
        # lentera tiap ~15 blok
        if i % 30 == 0:
            lx, lz = int(px + nx * 2), int(pz + nz * 2)
            ly = terrain_h(lx, lz)
            put(lx, ly + 1, lz, "minecraft:cobblestone_wall")
            put(lx, ly + 2, lz, "minecraft:lantern[hanging=false]")
        prev_y = y

# bounding box
xs = [k[0] for k in blocks]; ys = [k[1] for k in blocks]; zs = [k[2] for k in blocks]
x0, y0, z0 = min(xs), min(ys) - 2, min(zs)
W, H, L = max(xs) - x0 + 1, max(ys) - y0 + 1, max(zs) - z0 + 1
print(f"bbox {W}x{H}x{L}, blok jalan: {len(blocks)}")

AIR = "minecraft:air"
pal_list = sorted(set(blocks.values()))
if AIR not in pal_list: pal_list = [AIR] + pal_list
palette = {b: i for i, b in enumerate(pal_list)}
shifted = {(x - x0, y - y0, z - z0): b for (x, y, z), b in blocks.items()}
order = []
for y in range(H):
    for z in range(L):
        for x in range(W):
            order.append(shifted.get((x, y, z), AIR))
out = bytearray()
for b in order:
    v = palette[b]
    while True:
        bits = v & 0x7F; v >>= 7
        if v: out.append(bits | 0x80)
        else: out.append(bits); break
try:
    w = nbtlib.load("/home/hatch/workspace/minecraft/server/world/level.dat")
    dv = int(w["Data"]["DataVersion"])
except Exception:
    dv = 4435
schem = Compound({
    "Version": Int(3), "DataVersion": Int(dv),
    "Width": Short(W), "Height": Short(H), "Length": Short(L),
    "Offset": IntArray([0, 0, 0]),
    "Blocks": Compound({
        "Palette": Compound({k: Int(v) for k, v in palette.items()}),
        "Data": ByteArray(out), "BlockEntities": List([]),
    }),
    "Entities": List([]),
})
dest = "/home/hatch/workspace/minecraft/server/plugins/WorldEdit/schematics/roads.schem"
nbtlib.File({"Schematic": schem}).save(dest, gzipped=True)
print(f"wrote {dest}; paste di //pos1 {x0},{y0},{z0} dengan //paste -a")
