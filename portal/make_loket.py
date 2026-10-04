#!/usr/bin/env python3
"""Loket informasi kecil untuk bot Muse (gaya Jepang)."""
import nbtlib
from nbtlib import Compound, Int, Short, ByteArray, IntArray, List

W, H, L = 9, 12, 9
AIR = "minecraft:air"
blocks = {}

def put(x, y, z, b):
    if 0 <= x < W and 0 <= y < H and 0 <= z < L:
        blocks[(x, y, z)] = b

def fill(x1, y1, z1, x2, y2, z2, b):
    for x in range(min(x1, x2), max(x1, x2) + 1):
        for y in range(min(y1, y2), max(y1, y2) + 1):
            for z in range(min(z1, z2), max(z1, z2) + 1):
                put(x, y, z, b)

# fondasi
fill(0, 0, 0, 8, 2, 8, "minecraft:dirt")
fill(0, 3, 0, 8, 3, 8, "minecraft:grass_block")
# lantai loket 5x4
fill(2, 3, 2, 6, 3, 5, "minecraft:stone_bricks")
# dinding belakang + samping (terbuka depan/barat)
for y in (4, 5):
    for x in range(2, 7):
        put(x, y, 5, "minecraft:white_concrete")  # belakang
    for z in range(2, 6):
        put(2, y, z, "minecraft:white_concrete")   # kiri
        put(6, y, z, "minecraft:white_concrete")   # kanan
# tiang kayu sudut
for y in (4, 5, 6):
    for x, z in [(2, 2), (6, 2), (2, 5), (6, 5)]:
        put(x, y, z, "minecraft:stripped_oak_log[axis=y]")
# konter depan
for x in range(2, 7):
    put(x, 4, 2, "minecraft:dark_oak_planks")
    put(x, 5, 2, "minecraft:oak_fence")
# atap
fill(1, 7, 1, 7, 7, 6, "minecraft:dark_prismarine")
fill(1, 8, 2, 7, 8, 5, "minecraft:dark_prismarine")
# lentera gantung
put(4, 6, 4, "minecraft:lantern[hanging=true]")
# papan (counter depan)
put(4, 4, 1, "minecraft:oak_sign")

pal_list = sorted(set(blocks.values()))
if AIR not in pal_list:
    pal_list = [AIR] + pal_list
palette = {b: i for i, b in enumerate(pal_list)}
order = []
for y in range(H):
    for z in range(L):
        for x in range(W):
            order.append(blocks.get((x, y, z), AIR))
out = bytearray()
for b in order:
    v = palette[b]
    while True:
        bits = v & 0x7F
        v >>= 7
        if v:
            out.append(bits | 0x80)
        else:
            out.append(bits)
            break
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
dest = "/home/hatch/workspace/minecraft/server/plugins/WorldEdit/schematics/loket.schem"
nbtlib.File({"Schematic": schem}).save(dest, gzipped=True)
print(f"wrote {dest}")
