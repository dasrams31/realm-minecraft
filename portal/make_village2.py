#!/usr/bin/env python3
"""Village expansion (east side): more houses, market, shrine, big farm."""
import nbtlib
from nbtlib import Compound, Int, Short, ByteArray, IntArray, List

W, H, L = 61, 35, 61
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

def stairs(b, facing):
    return f"minecraft:{b}_stairs[facing={facing},half=bottom,shape=straight]"

fill(0, 0, 0, W - 1, 5, L - 1, "minecraft:dirt")
fill(0, 6, 0, W - 1, 6, L - 1, "minecraft:dirt")
fill(0, 7, 0, W - 1, 7, L - 1, "minecraft:grass_block")
GY = 8

def path(x1, z1, x2, z2, w=2):
    hw = w // 2
    for x in range(min(x1, x2), max(x1, x2) + 1):
        for dx in range(-hw, hw + 1):
            put(x + dx, GY, z1, "minecraft:gravel")
    for z in range(min(z1, z2), max(z1, z2) + 1):
        for dx in range(-hw, hw + 1):
            put(x2 + dx, GY, z, "minecraft:gravel")

def lantern(x, z):
    put(x, GY, z, "minecraft:cobblestone")
    put(x, GY + 1, z, "minecraft:cobblestone_wall")
    put(x, GY + 2, z, "minecraft:lantern[hanging=false]")

def gable_roof(cx, cz, w, d, y):
    hw, hd = w // 2, d // 2
    for x in range(cx - hw - 1, cx + hw + 2):
        put(x, y, cz - hd - 1, stairs("dark_prismarine", "north"))
        put(x, y, cz + hd + 1, stairs("dark_prismarine", "south"))
    yy = y
    for i in range(hd + 1):
        z0, z1 = cz - hd + i, cz + hd - i
        if z0 > z1:
            break
        fill(cx - hw - 1, yy, z0, cx + hw + 1, yy, z1, "minecraft:dark_prismarine")
        yy += 1
    fill(cx - hw - 1, yy - 1, cz, cx + hw + 1, yy - 1, cz, "minecraft:dark_prismarine")

def house(cx, cz, w=9, d=7, facing="south"):
    hw, hd = w // 2, d // 2
    x0, x1 = cx - hw, cx + hw
    z0, z1 = cz - hd, cz + hd
    LOG = "minecraft:stripped_oak_log[axis=y]"
    fill(x0, GY, z0, x1, GY, z1, "minecraft:cobblestone")
    fill(x0, GY + 1, z0, x1, GY + 1, z1, "minecraft:oak_planks")
    for y in range(GY + 2, GY + 5):
        for x in (x0, x1):
            for z in (z0, z1):
                put(x, y, z, LOG)
        put(cx, y, z0, LOG)
        put(cx, y, z1, LOG)
    for y in range(GY + 2, GY + 5):
        for x in range(x0 + 1, x1):
            for z in (z0, z1):
                put(x, y, z, "minecraft:glass_pane" if x in (cx - 1, cx + 1) else "minecraft:white_concrete")
        for z in range(z0 + 1, z1):
            for x in (x0, x1):
                put(x, y, z, "minecraft:white_concrete")
    for x in range(x0, x1 + 1):
        put(x, GY + 5, z0, "minecraft:stripped_oak_log[axis=x]")
        put(x, GY + 5, z1, "minecraft:stripped_oak_log[axis=x]")
    dz = z1 if facing == "south" else z0
    df = 'north' if facing == 'south' else 'south'
    put(cx, GY + 2, dz, f"minecraft:oak_door[facing={df},half=lower,hinge=left,open=false,powered=false]")
    put(cx, GY + 3, dz, f"minecraft:oak_door[facing={df},half=upper,hinge=left,open=false,powered=false]")
    put(x0 + 1, GY + 2, z0 + 1, "minecraft:red_bed[facing=east,part=foot]")
    put(x0 + 2, GY + 2, z0 + 1, "minecraft:red_bed[facing=east,part=head]")
    put(x1 - 1, GY + 2, z0 + 1, "minecraft:crafting_table")
    put(x1 - 1, GY + 2, z1 - 1, "minecraft:furnace[facing=west]")
    put(cx, GY + 4, cz, "minecraft:lantern[hanging=false]")
    gable_roof(cx, cz, w, d, GY + 6)

def stall(cx, cz):
    """Market stall."""
    for dx, dz in [(-1, -1), (1, -1), (-1, 1), (1, 1)]:
        for y in range(GY + 1, GY + 4):
            put(cx + dx, y, cz + dz, "minecraft:oak_fence")
    fill(cx - 1, GY + 1, cz - 1, cx + 1, GY + 1, cz + 1, "minecraft:oak_planks")
    put(cx, GY + 2, cz, "minecraft:chest[facing=south,type=single]")
    fill(cx - 2, GY + 4, cz - 2, cx + 2, GY + 4, cz + 2, "minecraft:red_wool")
    fill(cx - 1, GY + 5, cz - 1, cx + 1, GY + 5, cz + 1, "minecraft:white_wool")

def shrine(cx, cz):
    """Small shrine."""
    fill(cx - 2, GY, cz - 2, cx + 2, GY, cz + 2, "minecraft:stone_bricks")
    fill(cx - 1, GY + 1, cz - 1, cx + 1, GY + 1, cz + 1, "minecraft:oak_planks")
    for dx, dz in [(-1, -1), (1, -1), (-1, 1), (1, 1)]:
        for y in range(GY + 2, GY + 4):
            put(cx + dx, y, cz + dz, "minecraft:stripped_dark_oak_log[axis=y]")
    fill(cx - 2, GY + 4, cz - 2, cx + 2, GY + 4, cz + 2, "minecraft:dark_prismarine")
    put(cx, GY + 2, cz, "minecraft:lantern[hanging=false]")
    put(cx, GY + 3, cz, "minecraft:gold_block")

def farm(cx, cz, w=9, d=6, crop="minecraft:wheat[age=7]"):
    x0, x1 = cx - w // 2, cx + w // 2
    z0, z1 = cz - d // 2, cz + d // 2
    for x in range(x0 - 1, x1 + 2):
        put(x, GY + 1, z0 - 1, "minecraft:oak_fence")
        put(x, GY + 1, z1 + 1, "minecraft:oak_fence")
    for z in range(z0, z1 + 1):
        put(x0 - 1, GY + 1, z, "minecraft:oak_fence")
        put(x1 + 1, GY + 1, z, "minecraft:oak_fence")
    for x in range(x0, x1 + 1):
        put(x, GY, cz, "minecraft:water")
    for x in range(x0, x1 + 1):
        for z in range(z0, z1 + 1):
            if z != cz:
                put(x, GY, z, "minecraft:farmland[moisture=7]")
                put(x, GY + 1, z, crop)

def tree(cx, cz):
    for y in range(GY + 1, GY + 4):
        put(cx, y, cz, "minecraft:oak_log[axis=y]")
    for dx in range(-2, 3):
        for dz in range(-2, 3):
            for dy in range(0, 2):
                if abs(dx) == 2 and abs(dz) == 2:
                    continue
                put(cx + dx, GY + 4 + dy, cz + dz, "minecraft:oak_leaves[persistent=true]")
    put(cx, GY + 6, cz, "minecraft:oak_leaves[persistent=true]")

# ================= layout (local, center 30,30) =================
CX, CZ = 30, 30
# market plaza (north)
fill(CX - 8, GY, CZ - 24, CX + 8, GY, CZ - 12, "minecraft:stone_bricks")
for sx, sz in [(-5, -18), (5, -18), (-5, -14), (5, -14)]:
    stall(CX + sx, CZ + sz)
# shrine (northeast)
shrine(48, 12)
# houses
house(14, 14, 11, 8, "east")
house(48, 40, 9, 7, "west")
house(14, 44, 9, 7, "east")
house(30, 48, 11, 8, "north")
# big farm (southeast)
farm(44, 30, 11, 7, "minecraft:potatoes[age=7]")
# paths
path(30, 18, 30, 6)      # to market
path(6, 30, 0, 30)       # west to old village
path(30, 34, 30, 44)
path(14, 30, 30, 30)
path(44, 30, 54, 30)
path(48, 30, 48, 14)
# lanterns
for lx, lz in [(24, 12), (36, 12), (12, 24), (12, 36), (48, 24), (36, 36), (24, 44), (30, 24)]:
    lantern(lx, lz)
# trees
for tx, tz in [(8, 8), (54, 8), (8, 54), (54, 54), (22, 54)]:
    tree(tx, tz)

# ================= write =================
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
dest = "/home/hatch/workspace/minecraft/server/plugins/WorldEdit/schematics/village2.schem"
nbtlib.File({"Schematic": schem}).save(dest, gzipped=True)
print(f"wrote {dest} non-air {sum(1 for b in order if b != AIR)}")
