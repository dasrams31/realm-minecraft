#!/usr/bin/env python3
"""Generate a Japanese pagoda as a Sponge schematic (.schem) for WorldEdit."""
import gzip
import struct
import sys

import nbtlib
from nbtlib import Compound, Int, Short, ByteArray, IntArray, List, String

W, H, L = 21, 36, 25  # x, y, z (extra room south for torii gate)

# blockstate palette
AIR = "minecraft:air"
FOUND = "minecraft:polished_andesite"
FLOOR = "minecraft:dark_oak_planks"
PILLAR = "minecraft:stripped_dark_oak_log[axis=y]"
WALL = "minecraft:white_concrete"
GLASS = "minecraft:white_stained_glass"
ROOF = "minecraft:deepslate_tiles"
ROOF_SLAB = "minecraft:deepslate_tile_slab[type=bottom]"
WALL_TOP = "minecraft:cobblestone_wall"
GOLD = "minecraft:gold_block"
ROD = "minecraft:lightning_rod[facing=up]"
LANTERN = "minecraft:lantern[hanging=false]"
TORII_BEAM = "minecraft:dark_oak_planks"
STONE = "minecraft:stone_bricks"

blocks = {}


def put(x, y, z, b):
    if 0 <= x < W and 0 <= y < H and 0 <= z < L:
        blocks[(x, y, z)] = b


def fill(x1, y1, z1, x2, y2, z2, b):
    for x in range(min(x1, x2), max(x1, x2) + 1):
        for y in range(min(y1, y2), max(y1, y2) + 1):
            for z in range(min(z1, z2), max(z1, z2) + 1):
                put(x, y, z, b)


def hollow_box(cx, cz, size, y1, y2, wall_block, pillar_block):
    """Story: floor handled separately; pillars at corners, walls with windows."""
    h = size // 2
    x0, x1 = cx - h, cx + h
    z0, z1 = cz - h, cz + h
    for y in range(y1, y2 + 1):
        for x in range(x0, x1 + 1):
            for z in (z0, z1):
                put(x, y, z, wall_block)
        for z in range(z0, z1 + 1):
            for x in (x0, x1):
                put(x, y, z, wall_block)
    # corner pillars (overwrite)
    for y in range(y1, y2 + 1):
        for x in (x0, x1):
            for z in (z0, z1):
                put(x, y, z, pillar_block)
    # windows: 2-wide glass on each side, middle height
    mid = (y1 + y2) // 2
    for dx in (-1, 0):
        put(cx + dx, mid, z0, GLASS); put(cx + dx, mid, z1, GLASS)
        put(x0, mid, cz + dx, GLASS); put(x1, mid, cz + dx, GLASS)


def roof(cx, cz, size, y):
    """Stepped pyramid roof with stairs eave (upturned look)."""
    h = size // 2
    x0, x1 = cx - h, cx + h
    z0, z1 = cz - h, cz + h
    # eave: stairs facing outward around perimeter
    for x in range(x0, x1 + 1):
        put(x, y, z0, f"minecraft:deepslate_tile_stairs[facing=north,half=bottom,shape=straight]")
        put(x, y, z1, f"minecraft:deepslate_tile_stairs[facing=south,half=bottom,shape=straight]")
    for z in range(z0 + 1, z1):
        put(x0, y, z, f"minecraft:deepslate_tile_stairs[facing=west,half=bottom,shape=straight]")
        put(x1, y, z, f"minecraft:deepslate_tile_stairs[facing=east,half=bottom,shape=straight]")
    # fill inside of eave layer
    fill(x0 + 1, y, z0 + 1, x1 - 1, y, z1 - 1, ROOF)
    # step in
    s = size - 2
    yy = y + 1
    while s >= 3:
        hh = s // 2
        fill(cx - hh, yy, cz - hh, cx + hh, yy, cz + hh, ROOF)
        s -= 2
        yy += 1


CX, CZ = 10, 9  # pagoda center (room for torii at south z~20)

# foundation
fill(CX - 8, 0, CZ - 8, CX + 8, 1, CZ + 8, FOUND)
# steps (south side)
fill(CX - 1, 0, CZ + 9, CX + 1, 0, CZ + 10, STONE)

# lantern posts at foundation corners
for sx in (-1, 1):
    for sz in (-1, 1):
        lx, lz = CX + sx * 7, CZ + sz * 7
        put(lx, 2, lz, WALL_TOP)
        put(lx, 3, lz, LANTERN)

# --- story 1: 13x13, y2..6 ---
fill(CX - 6, 2, CZ - 6, CX + 6, 2, CZ + 6, FLOOR)
hollow_box(CX, CZ, 13, 3, 5, WALL, PILLAR)
# door opening (south, 3 wide x 3 tall)
for dx in (-1, 0, 1):
    for y in (3, 4, 5):
        put(CX + dx, y, CZ + 6, AIR)
fill(CX - 6, 6, CZ - 6, CX + 6, 6, CZ + 6, FLOOR)  # ceiling
roof(CX, CZ, 17, 7)  # roof 1: y7..10

# --- story 2: 9x9, y11..14 ---
fill(CX - 4, 11, CZ - 4, CX + 4, 11, CZ + 4, FLOOR)
hollow_box(CX, CZ, 9, 12, 13, WALL, PILLAR)
for dx in (-1, 0, 1):
    for y in (12, 13):
        put(CX + dx, y, CZ + 4, AIR)
fill(CX - 4, 14, CZ - 4, CX + 4, 14, CZ + 4, FLOOR)
roof(CX, CZ, 13, 15)  # roof 2: y15..17

# --- story 3: 7x7, y18..21 ---
fill(CX - 3, 18, CZ - 3, CX + 3, 18, CZ + 3, FLOOR)
hollow_box(CX, CZ, 7, 19, 20, WALL, PILLAR)
fill(CX - 3, 21, CZ - 3, CX + 3, 21, CZ + 3, FLOOR)
roof(CX, CZ, 11, 22)  # roof 3: y22..24

# spire
for y in range(25, 29):
    put(CX, y, CZ, WALL_TOP)
put(CX, 29, CZ, GOLD)
put(CX, 30, CZ, ROD)

# torii gate (south of pagoda)
tz = CZ + 13
for dx in (-3, 3):
    for y in range(2, 7):
        put(CX + dx, y, tz, PILLAR)
fill(CX - 4, 7, tz, CX + 4, 7, tz, TORII_BEAM)
fill(CX - 3, 6, tz, CX + 3, 6, tz, TORII_BEAM)
put(CX, 8, tz, TORII_BEAM)

# ---- encode sponge schematic v3 ----
order = []
for y in range(H):
    for z in range(L):
        for x in range(W):
            order.append(blocks.get((x, y, z), AIR))

palette = {}
pal_list = []
for b in order:
    if b not in palette:
        palette[b] = len(pal_list)
        pal_list.append(b)

# varint encode
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

# DataVersion: read from world for best compat
try:
    w = nbtlib.load("/home/hatch/workspace/minecraft/server/world/level.dat")
    dv = int(w["Data"]["DataVersion"])
except Exception:
    dv = 4435

schem = Compound({
    "Version": Int(3),
    "DataVersion": Int(dv),
    "Width": Short(W),
    "Height": Short(H),
    "Length": Short(L),
    "Offset": IntArray([0, 0, 0]),
    "Blocks": Compound({
        "Palette": Compound({k: Int(v) for k, v in palette.items()}),
        "Data": ByteArray(out),
        "BlockEntities": List([]),
    }),
    "Entities": List([]),
})
dest = "/home/hatch/workspace/minecraft/server/plugins/WorldEdit/schematics/pagoda.schem"
nbtlib.File({"Schematic": schem}).save(dest, gzipped=True)
print(f"wrote {dest} ({W}x{H}x{L}, {len(pal_list)} block types, DataVersion {dv})")
non_air = sum(1 for b in order if b != AIR)
print(f"non-air blocks: {non_air}")
