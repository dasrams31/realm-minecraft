#!/usr/bin/env python3
"""Generate Edo-period castle tenshu (donjon) as Sponge schematic."""
import nbtlib
from nbtlib import Compound, Int, Short, ByteArray, IntArray, List

W, H, L = 41, 55, 41

AIR = "minecraft:air"
STONE = "minecraft:stone_bricks"
STONE_CRACK = "minecraft:cracked_stone_bricks"
WALL = "minecraft:white_concrete"
BEAM = "minecraft:stripped_dark_oak_log[axis=y]"
BEAM_X = "minecraft:stripped_dark_oak_log[axis=x]"
BEAM_Z = "minecraft:stripped_dark_oak_log[axis=z]"
FLOOR = "minecraft:dark_oak_planks"
ROOF = "minecraft:deepslate_tiles"
GOLD = "minecraft:gold_block"
GLASS = "minecraft:black_stained_glass"
LANTERN = "minecraft:lantern[hanging=false]"
DOOR = "minecraft:dark_oak_door[half=lower,hinge=left,facing=south]"

blocks = {}

def put(x, y, z, b):
    if 0 <= x < W and 0 <= y < H and 0 <= z < L:
        blocks[(x, y, z)] = b

def fill(x1, y1, z1, x2, y2, z2, b):
    for x in range(min(x1,x2), max(x1,x2)+1):
        for y in range(min(y1,y2), max(y1,y2)+1):
            for z in range(min(z1,z2), max(z1,z2)+1):
                put(x, y, z, b)

def stairs(x, y, z, facing):
    put(x, y, z, f"minecraft:deepslate_tile_stairs[facing={facing},half=bottom,shape=straight]")

def roof_layer(cx, cz, size, y):
    """Atap khas Jepang: eave menukik dengan sudut terangkat."""
    h = size // 2
    x0, x1 = cx-h, cx+h
    z0, z1 = cz-h, cz+h
    # eave stairs
    for x in range(x0, x1+1):
        stairs(x, y, z0, "north"); stairs(x, y, z1, "south")
    for z in range(z0+1, z1):
        stairs(x0, y, z, "west"); stairs(x1, y, z, "east")
    # sudut terangkat (upturned corners)
    for (sx, sz, fx, fz) in [(-1,-1,"north","west"),(1,-1,"north","east"),
                              (-1,1,"south","west"),(1,1,"south","east")]:
        put(cx+sx*(h+1), y+1, cz+sz*(h+1), f"minecraft:deepslate_tile_stairs[facing={fx},half=top,shape=straight]")
    fill(x0+1, y, z0+1, x1-1, y, z1-1, ROOF)
    # susut ke atas
    s, yy = size-2, y+1
    while s >= 5:
        hh = s//2
        fill(cx-hh, yy, cz-hh, cx+hh, yy, cz+hh, ROOF)
        s -= 2; yy += 1

def story(cx, cz, size, y1, y2, door_side=None):
    """Satu lantai: dinding putih, pilar sudut, jendela hitam."""
    h = size//2
    x0, x1 = cx-h, cx+h
    z0, z1 = cz-h, cz+h
    fill(x0, y1, z0, x1, y1, z1, FLOOR)
    for y in range(y1+1, y2+1):
        for x in range(x0, x1+1):
            for z in (z0, z1): put(x, y, z, WALL)
        for z in range(z0+1, z1):
            for x in (x0, x1): put(x, y, z, WALL)
    # pilar sudut
    for y in range(y1+1, y2+1):
        for x in (x0, x1):
            for z in (z0, z1): put(x, y, z, BEAM)
    # balok horizontal atas
    for x in range(x0, x1+1):
        put(x, y2, z0, BEAM_X); put(x, y2, z1, BEAM_X)
    for z in range(z0, z1+1):
        put(x0, y2, z, BEAM_Z); put(x1, y2, z, BEAM_Z)
    # jendela
    mid = (y1+y2)//2 + 1
    for dx in (-2, 0, 2):
        put(cx+dx, mid, z0, GLASS); put(cx+dx, mid, z1, GLASS)
        put(x0, mid, cz+dx, GLASS); put(x1, mid, cz+dx, GLASS)
    # pintu
    if door_side == "south":
        for dx in (-1, 0, 1):
            for y in (y1+1, y1+2): put(cx+dx, y, z1, AIR)
    fill(x0, y2+1 if False else y2, z0, x1, y2, z1, FLOOR)  # langit-langit = lantai atas
    return y2+1

CX, CZ = 20, 20

# --- Ishigaki: base batu miring (khas kastil Jepang) ---
# lapis 1: 33x33 y0-2, lapis 2: 29x29 y3-5, lapis 3: 25x25 y6-8 (menyusut = efek miring)
fill(CX-16, 0, CZ-16, CX+16, 2, CZ+16, STONE)
fill(CX-14, 3, CZ-14, CX+14, 5, CZ+14, STONE)
fill(CX-12, 6, CZ-12, CX+12, 8, CZ+12, STONE)
# aksen retak acak di permukaan
import random
random.seed(42)
for _ in range(40):
    x = random.randint(CX-16, CX+16); z = random.randint(CZ-16, CZ+16)
    y = 2 if abs(x-CX)<=16 and abs(z-CZ)<=16 else 5
    if abs(x-CX) in (15,16) or abs(z-CZ) in (15,16):
        put(x, y, z, STONE_CRACK)
# tangga batu sisi selatan
for i in range(9):
    fill(CX-1, 8-i, CZ+13+i, CX+1, 8-i, CZ+13+i, "minecraft:stone_brick_stairs[facing=south,half=bottom,shape=straight]")

y = 9
# --- Lantai 1: 21x21 ---
y = story(CX, CZ, 21, y, y+3, door_side="south")
roof_layer(CX, CZ, 25, y); y += 5
# --- Lantai 2: 17x17 ---
y = story(CX, CZ, 17, y, y+3)
roof_layer(CX, CZ, 21, y); y += 5
# --- Lantai 3: 13x13 ---
y = story(CX, CZ, 13, y, y+3)
roof_layer(CX, CZ, 17, y); y += 5
# --- Lantai 4: 9x9 ---
y = story(CX, CZ, 9, y, y+2)
roof_layer(CX, CZ, 13, y); y += 4
# --- Lantai 5: 5x5 + atap emas ---
y = story(CX, CZ, 5, y, y+2)
roof_layer(CX, CZ, 9, y); y += 4
# puncak emas (shachi)
put(CX, y, CZ, GOLD)
put(CX, y+1, CZ, "minecraft:lightning_rod[facing=up]")
for dx in (-2, 2):
    put(CX+dx, y-1, CZ, GOLD)

# lentera di base
for (sx, sz) in [(-1,-1),(1,-1),(-1,1),(1,1)]:
    put(CX+sx*14, 9, CZ+sz*14, "minecraft:cobblestone_wall")
    put(CX+sx*14, 10, CZ+sz*14, LANTERN)

# ---- encode ----
order = []
for yy in range(H):
    for z in range(L):
        for x in range(W):
            order.append(blocks.get((x, yy, z), AIR))
palette, pal_list = {}, []
for b in order:
    if b not in palette:
        palette[b] = len(pal_list); pal_list.append(b)
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
    "Offset": IntArray([0,0,0]),
    "Blocks": Compound({
        "Palette": Compound({k: Int(v) for k,v in palette.items()}),
        "Data": ByteArray(out), "BlockEntities": List([]),
    }),
    "Entities": List([]),
})
dest = "/home/hatch/workspace/minecraft/server/plugins/WorldEdit/schematics/castle_tenshu.schem"
nbtlib.File({"Schematic": schem}).save(dest, gzipped=True)
print(f"kastil: {W}x{H}x{L}, {len(pal_list)} tipe, non-air {sum(1 for b in order if b!=AIR)}")
