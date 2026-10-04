#!/usr/bin/env python3
"""SATU tangga dojo yang bersih. Verifikasi manual."""
import nbtlib
from nbtlib import Compound, Int, Short, ByteArray, IntArray, List

AIR = "minecraft:air"
blocks = {}
def put(x, y, z, b):
    blocks[(x, y, z)] = b

# DOJO: dari (0,100,60) ke selatan, 25 langkah -> (0,75,85)
# Lebar 5 (x -2..2). Tiap langkah: stairs di y, fondasi di y-1 (1 blok saja, tidak overlap)
for i in range(26):
    z = 60 + i
    y = 100 - i
    for x in range(-2, 3):
        # anak tangga menghadap utara (ke arah atas)
        put(x, y, z, "minecraft:stone_brick_stairs[facing=north,half=bottom,shape=straight]")
        # fondasi 1 blok di bawah
        put(x, y - 1, z, "minecraft:stone_bricks")
        put(x, y + 1, z, AIR)
    # tembok sisi
    for x in (-3, 3):
        put(x, y, z, "minecraft:stone_bricks")
        put(x, y + 1, z, AIR)

# bounding box
xs = [k[0] for k in blocks]; ys = [k[1] for k in blocks]; zs = [k[2] for k in blocks]
x0, y0, z0 = min(xs), min(ys), min(zs)
W, H, L = max(xs) - x0 + 1, max(ys) - y0 + 1, max(zs) - z0 + 1

pal_list = sorted(set(blocks.values()))
if AIR not in pal_list: pal_list = [AIR] + pal_list
palette = {b: i for i, b in enumerate(pal_list)}
shifted = {(x - x0, y - y0, z - z0): b for (x, y, z), b in blocks.items()}
order = [shifted.get((x, y, z), AIR) for y in range(H) for z in range(L) for x in range(W)]
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
dest = "/home/hatch/workspace/minecraft/server/plugins/WorldEdit/schematics/dojo_stairs_clean.schem"
nbtlib.File({"Schematic": schem}).save(dest, gzipped=True)
print(f"bbox {W}x{H}x{L}")
print(f"mulai: world ({x0},{y0+1},{z0}) -> akhir: world ({x0},{y0+1-25},{z0+25})")
print(f"paste di //pos1 {x0},{y0},{z0}")
