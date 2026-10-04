#!/usr/bin/env python3
"""Konektor lurus lebar dari ujung jalan ke bangunan. Paste //paste -a."""
import nbtlib
from nbtlib import Compound, Int, Short, ByteArray, IntArray, List

AIR = "minecraft:air"
blocks = {}
def put(x, y, z, b):
    blocks[(x, y, z)] = b

def connector(x1, y1, z1, x2, y2, z2, width=9):
    """ramp lurus lebar dari (x1,y1,z1) ke (x2,y2,z2)"""
    dx, dz = x2 - x1, z2 - z1
    steps = max(abs(dx), abs(dz))
    px, pz = -dz / max(1, steps), dx / max(1, steps)
    # normalisasi tegak lurus
    import math
    l = math.hypot(px, pz) or 1
    px, pz = px / l, pz / l
    hw = width // 2
    for i in range(steps + 1):
        t = i / steps
        cx = int(x1 + dx * t)
        cz = int(z1 + dz * t)
        cy = int(y1 + (y2 - y1) * t)
        for w in range(-hw, hw + 1):
            bx = int(cx + px * w)
            bz = int(cz + pz * w)
            # slab untuk ramp halus (naik/turun gradual)
            put(bx, cy, bz, "minecraft:stone_brick_slab[type=bottom]")
            put(bx, cy - 1, bz, "minecraft:stone_bricks")
            put(bx, cy + 1, bz, AIR)
        # lentera tiap 6 langkah
        if i % 6 == 0:
            for w in (-hw - 1, hw + 1):
                bx = int(cx + px * w)
                bz = int(cz + pz * w)
                put(bx, cy, bz, "minecraft:stone_bricks")
                put(bx, cy + 1, bz, "minecraft:cobblestone_wall")
                put(bx, cy + 2, bz, "minecraft:lantern[hanging=false]")

# ZEN: dari ujung jalan (-5,100,5) ke platform (-20,95,-15)
connector(-5, 100, 5, -20, 95, -15)

# BRIDGE: dari ujung jalan (35,100,60) ke platform (35,70,68)
connector(35, 100, 60, 35, 70, 68)

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
dest = "/home/hatch/workspace/minecraft/server/plugins/WorldEdit/schematics/connectors.schem"
nbtlib.File({"Schematic": schem}).save(dest, gzipped=True)
print(f"paste di //pos1 {x0},{y0},{z0} dengan //paste -a")
