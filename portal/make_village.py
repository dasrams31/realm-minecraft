#!/usr/bin/env python3
"""Generate a Japanese village as a Sponge schematic (.schem) for WorldEdit."""
import nbtlib
from nbtlib import Compound, Int, Short, ByteArray, IntArray, List

W, H, L = 61, 35, 61  # x, y, z; center (30,*,30)

AIR = "minecraft:air"
GRASS = "minecraft:grass_block"
DIRT = "minecraft:dirt"
COBBLE = "minecraft:cobblestone"
STONE_BRICK = "minecraft:stone_bricks"
GRAVEL = "minecraft:gravel"
PLANKS = "minecraft:oak_planks"
LOG = "minecraft:stripped_oak_log[axis=y]"
LOGX = "minecraft:stripped_oak_log[axis=x]"
LOGZ = "minecraft:stripped_oak_log[axis=z]"
WALL = "minecraft:white_concrete"
GLASS = "minecraft:glass_pane"
ROOF = "minecraft:dark_prismarine"
WATER = "minecraft:water"
FARMLAND = "minecraft:farmland[moisture=7]"
WHEAT = "minecraft:wheat[age=7]"
CARROT = "minecraft:carrots[age=7]"
LANTERN = "minecraft:lantern[hanging=false]"
FENCE = "minecraft:oak_fence"
LEAF = "minecraft:oak_leaves[persistent=true]"
CHERRY_LEAF = "minecraft:pink_petals[flower_amount=4]"
BED = "minecraft:red_bed[facing=east,part=head]"
BED_F = "minecraft:red_bed[facing=east,part=foot]"
CRAFT = "minecraft:crafting_table"
FURNACE = "minecraft:furnace[facing=west]"
TORCH = "minecraft:torch"

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

# ---- flatten ground: y0-1 dirt, y2 grass ----
fill(0, 0, 0, W - 1, 5, L - 1, DIRT)
fill(0, 6, 0, W - 1, 6, L - 1, DIRT)
fill(0, 7, 0, W - 1, 7, L - 1, GRASS)

GY = 8  # ground build level

def path(x1, z1, x2, z2, w=2):
    """Gravel path (axis-aligned, L-shaped)."""
    hw = w // 2
    if x1 == x2 or True:
        # x segment then z segment
        for x in range(min(x1, x2), max(x1, x2) + 1):
            for dx in range(-hw, hw + 1):
                put(x + dx, GY, z1, GRAVEL)
        for z in range(min(z1, z2), max(z1, z2) + 1):
            for dx in range(-hw, hw + 1):
                put(x2 + dx, GY, z, GRAVEL)

def lantern(x, z):
    put(x, GY, z, COBBLE)
    put(x, GY + 1, z, "minecraft:cobblestone_wall")
    put(x, GY + 2, z, LANTERN)

def gable_roof(cx, cz, w, d, y):
    """Gable roof, ridge along x. w,d = footprint."""
    hw, hd = w // 2, d // 2
    # eaves: overhang 1
    for x in range(cx - hw - 1, cx + hw + 2):
        put(x, y, cz - hd - 1, stairs("dark_prismarine", "north"))
        put(x, y, cz + hd + 1, stairs("dark_prismarine", "south"))
    yy = y
    for i in range(hd + 1):
        z0, z1 = cz - hd + i, cz + hd - i
        if z0 > z1:
            break
        fill(cx - hw - 1, yy, z0, cx + hw + 1, yy, z1, ROOF)
        # gable ends: fill triangle with wall
        yy += 1
    # ridge cap
    fill(cx - hw - 1, yy - 1, cz, cx + hw + 1, yy - 1, cz, ROOF)

def house(cx, cz, facing="south"):
    """Japanese minka ~9x7. facing = door side."""
    w, d = 9, 7
    hw, hd = w // 2, d // 2
    x0, x1 = cx - hw, cx + hw
    z0, z1 = cz - hd, cz + hd
    # foundation + floor
    fill(x0, GY, z0, x1, GY, z1, COBBLE)
    fill(x0, GY + 1, z0, x1, GY + 1, z1, PLANKS)
    # pillars at corners + mid
    for y in range(GY + 2, GY + 5):
        for x in (x0, x1):
            for z in (z0, z1):
                put(x, y, z, LOG)
        put(cx, y, z0, LOG)
        put(cx, y, z1, LOG)
    # walls with windows
    for y in range(GY + 2, GY + 5):
        for x in range(x0 + 1, x1):
            for z in (z0, z1):
                if x in (cx - 1, cx + 1):
                    put(x, y, z, GLASS)
                else:
                    put(x, y, z, WALL)
        for z in range(z0 + 1, z1):
            for x in (x0, x1):
                put(x, y, z, WALL)
    # top beam
    for x in range(x0, x1 + 1):
        put(x, GY + 5, z0, LOGX)
        put(x, GY + 5, z1, LOGX)
    for z in range(z0, z1 + 1):
        put(x0, GY + 5, z, LOGZ)
        put(x1, GY + 5, z, LOGZ)
    # door (south default)
    dz = z1 if facing == "south" else z0
    put(cx, GY + 2, dz, f"minecraft:oak_door[facing={'north' if facing=='south' else 'south'},half=lower,hinge=left,open=false,powered=false]")
    put(cx, GY + 3, dz, f"minecraft:oak_door[facing={'north' if facing=='south' else 'south'},half=upper,hinge=left,open=false,powered=false]")
    # interior: bed, craft, furnace, lantern
    put(x0 + 1, GY + 2, z0 + 1, BED_F)
    put(x0 + 2, GY + 2, z0 + 1, BED)
    put(x1 - 1, GY + 2, z0 + 1, CRAFT)
    put(x1 - 1, GY + 2, z1 - 1, FURNACE)
    put(cx, GY + 4, cz, LANTERN)
    # roof
    gable_roof(cx, cz, w, d, GY + 6)

def well(cx, cz):
    fill(cx - 1, GY, cz - 1, cx + 1, GY, cz + 1, STONE_BRICK)
    for dx in (-1, 1):
        for dz in (-1, 1):
            put(cx + dx, GY + 1, cz + dz, "minecraft:cobblestone_wall")
    put(cx, GY + 1, cz, WATER)
    for y in range(GY + 1, GY + 4):
        put(cx - 2, y, cz, LOG)
        put(cx + 2, y, cz, LOG)
    fill(cx - 2, GY + 4, cz - 1, cx + 2, GY + 4, cz + 1, ROOF)

def farm(cx, cz, w=7, d=5, crop=WHEAT):
    x0, x1 = cx - w // 2, cx + w // 2
    z0, z1 = cz - d // 2, cz + d // 2
    # fence border
    for x in range(x0 - 1, x1 + 2):
        put(x, GY + 1, z0 - 1, FENCE)
        put(x, GY + 1, z1 + 1, FENCE)
    for z in range(z0, z1 + 1):
        put(x0 - 1, GY + 1, z, FENCE)
        put(x1 + 1, GY + 1, z, FENCE)
    # water channel middle
    for x in range(x0, x1 + 1):
        put(x, GY, cz, WATER)
    for x in range(x0, x1 + 1):
        for z in range(z0, z1 + 1):
            if z == cz:
                continue
            put(x, GY, z, FARMLAND)
            put(x, GY + 1, z, crop)

def torii(cx, cz):
    for dx in (-2, 2):
        for y in range(GY, GY + 5):
            put(cx + dx, y, cz, "minecraft:stripped_dark_oak_log[axis=y]")
    fill(cx - 3, GY + 5, cz, cx + 3, GY + 5, cz, "minecraft:dark_oak_planks")
    fill(cx - 2, GY + 6, cz, cx + 2, GY + 6, cz, "minecraft:dark_oak_planks")

def tree(cx, cz):
    for y in range(GY + 1, GY + 4):
        put(cx, y, cz, "minecraft:oak_log[axis=y]")
    for dx in range(-2, 3):
        for dz in range(-2, 3):
            for dy in range(0, 2):
                if abs(dx) == 2 and abs(dz) == 2:
                    continue
                put(cx + dx, GY + 4 + dy, cz + dz, LEAF)
    put(cx, GY + 6, cz, LEAF)

# ================= layout =================
CX, CZ = 30, 30
# plaza
fill(CX - 6, GY, CZ - 6, CX + 6, GY, CZ + 6, STONE_BRICK)
well(CX, CZ)
# houses
house(14, 14, "east")
house(46, 14, "west")
house(14, 46, "east")
house(46, 46, "west")
house(30, 12, "south")
house(30, 48, "north")
# paths: plaza to houses
path(CX, CZ + 7, CX, 52)
path(CX, CZ - 7, CX, 8)
path(CX - 7, CZ, 10, CZ)
path(CX + 7, CZ, 50, CZ)
path(30, 8, 30, 12)
path(30, 52, 30, 48)
# farms
farm(8, 30, crop=WHEAT)
farm(52, 30, crop=CARROT)
# lanterns along paths
for lx, lz in [(24, 40), (36, 40), (24, 20), (36, 20), (20, 24), (20, 36), (40, 24), (40, 36),
               (30, 16), (30, 44), (12, 30), (48, 30)]:
    lantern(lx, lz)
# torii south entrance
torii(30, 58)
path(30, 52, 30, 58)
# trees
for tx, tz in [(8, 8), (52, 8), (8, 52), (52, 52), (22, 8), (38, 52)]:
    tree(tx, tz)

# ================= write schematic =================
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
dest = "/home/hatch/workspace/minecraft/server/plugins/WorldEdit/schematics/village.schem"
nbtlib.File({"Schematic": schem}).save(dest, gzipped=True)
non_air = sum(1 for b in order if b != AIR)
print(f"wrote {dest} ({W}x{H}x{L}, {len(pal_list)} types, DV {dv}, non-air {non_air})")
