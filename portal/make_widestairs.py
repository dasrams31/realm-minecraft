#!/usr/bin/env python3
"""Tangga BATU LEBAR (7 blok) yang tersambung. Paste dengan //paste -a."""
import nbtlib
from nbtlib import Compound, Int, Short, ByteArray, IntArray, List

AIR = "minecraft:air"
blocks = {}
def put(x, y, z, b):
    blocks[(x, y, z)] = b

def wide_stairs(x0, y0, z0, dx, dz, steps, facing, width=7):
    """tangga lebar, turun 1 per langkah"""
    px, pz = -dz, dx
    hw = width // 2
    for i in range(steps):
        x = x0 + dx * i
        z = z0 + dz * i
        y = y0 - i
        for w in range(-hw, hw + 1):
            bx, bz = x + px * w, z + pz * w
            put(bx, y, bz, f"minecraft:stone_brick_stairs[facing={facing},half=bottom,shape=straight]")
            # fondasi tebal 3 blok
            for d in range(1, 4):
                put(bx, y - d, bz, "minecraft:stone_bricks")
            put(bx, y + 1, bz, AIR)
            put(bx, y + 2, bz, AIR)
        # pilar lentera tiap 4 langkah
        if i % 4 == 0:
            for w in (-hw - 1, hw + 1):
                bx, bz = x + px * w, z + pz * w
                put(bx, y, bz, "minecraft:stone_bricks")
                put(bx, y + 1, bz, "minecraft:stone_brick_wall")
                put(bx, y + 2, bz, "minecraft:lantern[hanging=false]")
    # plaza di atas (awal tangga)
    for w in range(-hw - 1, hw + 2):
        for d in range(-2, 1):
            bx, bz = x0 + px * w + dx * d, z0 + pz * w + dz * d
            put(bx, y0, bz, "minecraft:stone_bricks")
            put(bx, y0 + 1, bz, AIR)
            put(bx, y0 + 2, bz, AIR)

# === DOJO: dari (0,102,62) turun ke selatan, 27 langkah -> (0,75,89) ===
wide_stairs(0, 102, 62, 0, 1, 27, "north")

# === ZEN: dari (-8,108,-14) turun ke barat-laut, 13 langkah -> (-21,95,-27) ===
# arah diagonal: dx=-1, dz=-1
wide_stairs(-8, 108, -14, -1, -1, 13, "east")

# === BRIDGE: dari (48,92,52) turun ke tenggara, 22 langkah -> (26,70,74) ===
wide_stairs(48, 92, 52, -1, 1, 22, "east")

# === sambung jalan yang putus: ZEN road repair (0,20)->(-8,-14) ===
# jalan kerikil mengikuti terrain kasar y~100
for i in range(30):
    t = i / 29
    x = int(0 + (-8) * t)
    z = int(20 + (-34) * t)
    y = 100
    for w in (-1, 0, 1):
        put(x + w, y, z, "minecraft:gravel" if w == 0 else "minecraft:cobblestone")
        put(x + w, y + 1, z, AIR)

# === BRIDGE road repair (54,40)->(48,52) ===
for i in range(15):
    t = i / 14
    x = int(54 + (-6) * t)
    z = int(40 + 12 * t)
    y = 100 - i // 3
    for w in (-1, 0, 1):
        put(x + w, y, z, "minecraft:gravel" if w == 0 else "minecraft:cobblestone")
        put(x + w, y + 1, z, AIR)

# bounding box
xs = [k[0] for k in blocks]; ys = [k[1] for k in blocks]; zs = [k[2] for k in blocks]
x0, y0, z0 = min(xs), min(ys) - 1, min(zs)
W, H, L = max(xs) - x0 + 1, max(ys) - y0 + 1, max(zs) - z0 + 1
print(f"bbox {W}x{H}x{L}, blok: {len(blocks)}")

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
w = nbtlib.load("/home/hatch/workspace/minecraft/server/world/level.dat")
dv = int(w["Data"]["DataVersion"])
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
dest = "/home/hatch/workspace/minecraft/server/plugins/WorldEdit/schematics/widestairs.schem"
nbtlib.File({"Schematic": schem}).save(dest, gzipped=True)
print(f"paste di //pos1 {x0},{y0},{z0} dengan //paste -a")
