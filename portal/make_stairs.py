#!/usr/bin/env python3
"""Tangga batu penghubung jalan -> platform bangunan. Paste dengan //paste -a."""
import nbtlib
from nbtlib import Compound, Int, Short, ByteArray, IntArray, List

AIR = "minecraft:air"
blocks = {}
def put(x, y, z, b):
    blocks[(x, y, z)] = b

def staircase(x0, y0, z0, dx, dz, steps, facing):
    """tangga 3 lebar, turun 1 per langkah ke arah (dx,dz)"""
    # vektor tegak lurus untuk lebar
    px, pz = -dz, dx
    for i in range(steps):
        x = x0 + dx * i
        z = z0 + dz * i
        y = y0 - i
        for w in (-1, 0, 1):
            bx, bz = x + px * w, z + pz * w
            # anak tangga
            put(bx, y, bz, f"minecraft:stone_brick_stairs[facing={facing},half=bottom,shape=straight]")
            # fondasi di bawah (2 blok)
            put(bx, y - 1, bz, "minecraft:stone_bricks")
            put(bx, y - 2, bz, "minecraft:stone_bricks")
            # bersihkan atas
            put(bx, y + 1, bz, AIR)
            put(bx, y + 2, bz, AIR)
        # railing + lentera tiap 5 langkah
        if i % 5 == 0:
            for w in (-2, 2):
                bx, bz = x + px * w, z + pz * w
                put(bx, y + 1, bz, "minecraft:cobblestone_wall")
                put(bx, y + 2, bz, "minecraft:lantern[hanging=false]")
                put(bx, y, bz, "minecraft:stone_bricks")

# DOJO: dari jalan (0,103,68) turun ke selatan -> platform 75
# 28 langkah: (0,103,68) -> (0,75,96), facing=north (tangga menghadap utara/atas)
staircase(0, 103, 68, 0, 1, 28, "north")

# ZEN: dari timur (-12,116,-20) turun ke barat -> platform 95
# 21 langkah: (-12,116,-20) -> (-33,95,-20), facing=east
staircase(-12, 116, -20, -1, 0, 21, "east")

# BRIDGE: dari barat (23,66,75) naik ke timur -> platform 70
# 5 langkah naik: pakai staircase terbalik (naik)
# buat manual: naik 1 per langkah ke timur
px, pz = 0, 1  # tegak lurus arah timur
for i in range(6):
    x = 23 + i
    y = 65 + i
    z = 75
    for w in (-1, 0, 1):
        bx, bz = x, z + w
        put(bx, y, bz, "minecraft:stone_brick_stairs[facing=west,half=bottom,shape=straight]")
        put(bx, y - 1, bz, "minecraft:stone_bricks")
        put(bx, y + 1, bz, AIR)
        put(bx, y + 2, bz, AIR)
    if i % 3 == 0:
        for w in (-2, 2):
            put(x, y + 1, z + w, "minecraft:cobblestone_wall")
            put(x, y + 2, z + w, "minecraft:lantern[hanging=false]")

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
dest = "/home/hatch/workspace/minecraft/server/plugins/WorldEdit/schematics/stairs.schem"
nbtlib.File({"Schematic": schem}).save(dest, gzipped=True)
print(f"paste di //pos1 {x0},{y0},{z0} dengan //paste -a")
