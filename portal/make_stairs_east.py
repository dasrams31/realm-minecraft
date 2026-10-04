#!/usr/bin/env python3
"""Tangga desa2->desa3 yang RAPI. Paste //paste -a."""
import nbtlib
from nbtlib import Compound, Int, Short, ByteArray, IntArray, List

AIR = "minecraft:air"
blocks = {}
def put(x, y, z, b):
    blocks[(x, y, z)] = b

# tangga dari (56,100,30) ke timur, 25 langkah -> (80,76,30)
# desain: tiap langkah = slab di atas + fondasi solid di bawah (tidak overlap)
for i in range(26):
    x = 56 + i
    y = 100 - i
    for z in range(27, 34):  # lebar 7
        # permukaan: stairs menghadap barat (naik ke barat)
        put(x, y, z, "minecraft:stone_brick_stairs[facing=west,half=bottom,shape=straight]")
        # fondasi: 2 blok di bawah stairs (y-1, y-2) — TIDAK sampai y-3 agar tidak nimpa langkah berikut
        put(x, y - 1, z, "minecraft:stone_bricks")
        put(x, y - 2, z, "minecraft:stone_bricks")
        # udara di atas
        put(x, y + 1, z, AIR)
        put(x, y + 2, z, AIR)
    # dinding penahan di sisi (biar rapi, tidak ada blok ngambang terlihat)
    for z in (26, 34):
        # dinding mengikuti profil tangga
        for dy in range(-2, 1):
            put(x, y + dy, z, "minecraft:stone_bricks")
        put(x, y + 1, z, AIR)
    # lentera tiap 5 langkah
    if i % 5 == 2:
        for z in (26, 34):
            put(x, y + 1, z, "minecraft:cobblestone_wall")
            put(x, y + 2, z, "minecraft:lantern[hanging=false]")

# bounding box
xs = [k[0] for k in blocks]; ys = [k[1] for k in blocks]; zs = [k[2] for k in blocks]
x0, y0, z0 = min(xs), min(ys), min(zs)
W, H, L = max(xs) - x0 + 1, max(ys) - y0 + 1, max(zs) - z0 + 1

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
dest = "/home/hatch/workspace/minecraft/server/plugins/WorldEdit/schematics/stairs_east.schem"
nbtlib.File({"Schematic": schem}).save(dest, gzipped=True)
print(f"bbox {W}x{H}x{L}, paste di //pos1 {x0},{y0},{z0} dengan //paste -a")
