#!/usr/bin/env python3
"""Generate 5 Japanese buildings: onsen, dojo, jinja, zen garden, bridge+pond."""
import nbtlib
from nbtlib import Compound, Int, Short, ByteArray, IntArray, List

AIR = "minecraft:air"

class Schem:
    def __init__(self, w, h, l):
        self.W, self.H, self.L = w, h, l
        self.blocks = {}
    def put(self, x, y, z, b):
        if 0 <= x < self.W and 0 <= y < self.H and 0 <= z < self.L:
            self.blocks[(x, y, z)] = b
    def fill(self, x1, y1, z1, x2, y2, z2, b):
        for x in range(min(x1, x2), max(x1, x2) + 1):
            for y in range(min(y1, y2), max(y1, y2) + 1):
                for z in range(min(z1, z2), max(z1, z2) + 1):
                    self.put(x, y, z, b)
    def flatten(self, ground_y, dirt_depth=5):
        self.fill(0, 0, 0, self.W - 1, dirt_depth - 1, self.L - 1, "minecraft:dirt")
        self.fill(0, dirt_depth, 0, self.W - 1, ground_y - 1, self.L - 1, "minecraft:dirt")
        self.fill(0, ground_y, 0, self.W - 1, ground_y, self.L - 1, "minecraft:grass_block")
        self.gy = ground_y + 1
    def stairs(self, b, facing):
        return f"minecraft:{b}_stairs[facing={facing},half=bottom,shape=straight]"
    def save(self, name):
        pal_list = sorted(set(self.blocks.values()))
        if AIR not in pal_list:
            pal_list = [AIR] + pal_list
        palette = {b: i for i, b in enumerate(pal_list)}
        order = []
        for y in range(self.H):
            for z in range(self.L):
                for x in range(self.W):
                    order.append(self.blocks.get((x, y, z), AIR))
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
            "Width": Short(self.W), "Height": Short(self.H), "Length": Short(self.L),
            "Offset": IntArray([0, 0, 0]),
            "Blocks": Compound({
                "Palette": Compound({k: Int(v) for k, v in palette.items()}),
                "Data": ByteArray(out), "BlockEntities": List([]),
            }),
            "Entities": List([]),
        })
        dest = f"/home/hatch/workspace/minecraft/server/plugins/WorldEdit/schematics/{name}.schem"
        nbtlib.File({"Schematic": schem}).save(dest, gzipped=True)
        print(f"{name}: {self.W}x{self.H}x{self.L}, non-air {sum(1 for b in order if b != AIR)}")

LOG = "minecraft:stripped_oak_log[axis=y]"
DLOG = "minecraft:stripped_dark_oak_log[axis=y]"

# ================= 1. ONSEN =================
s = Schem(31, 22, 31)
s.flatten(6)
gy = s.gy
CX, CZ = 15, 15
# deck
s.fill(CX - 10, gy, CZ - 10, CX + 10, gy, CZ + 10, "minecraft:stone_bricks")
# pool 9x7, 2 deep
for x in range(CX - 4, CX + 5):
    for z in range(CZ - 3, CZ + 4):
        s.put(x, gy, z, AIR)
        s.put(x, gy - 1, z, "minecraft:water")
        s.put(x, gy - 2, z, "minecraft:stone_bricks")
# pool border rocks
for x in range(CX - 5, CX + 6):
    for z in (CZ - 4, CZ + 4):
        s.put(x, gy + 1, z, "minecraft:cobblestone")
for z in range(CZ - 3, CZ + 4):
    for x in (CX - 5, CX + 5):
        s.put(x, gy + 1, z, "minecraft:cobblestone")
# campfires for steam (corners, under deck edge)
for dx, dz in [(-6, -5), (6, -5), (-6, 5), (6, 5)]:
    s.put(CX + dx, gy + 1, CZ + dz, "minecraft:campfire[lit=true]")
# bamboo fence around deck
for x in range(CX - 10, CX + 11):
    for z in (CZ - 10, CZ + 10):
        s.put(x, gy + 1, z, "minecraft:bamboo_block")
        if x % 3 == 0:
            s.put(x, gy + 2, z, "minecraft:bamboo_block")
for z in range(CZ - 9, CZ + 10):
    for x in (CX - 10, CX + 10):
        s.put(x, gy + 1, z, "minecraft:bamboo_block")
# changing hut 5x4 at north
hx, hz = CX, CZ - 7
s.fill(hx - 2, gy, hz - 2, hx + 2, gy, hz + 2, "minecraft:oak_planks")
for y in (gy + 1, gy + 2):
    for x in (hx - 2, hx + 2):
        for z in (hz - 2, hz + 2):
            s.put(x, y, z, LOG)
for x in range(hx - 2, hx + 3):
    s.put(x, gy + 3, hz - 2, "minecraft:dark_prismarine")
    s.put(x, gy + 3, hz + 2, "minecraft:dark_prismarine")
s.fill(hx - 3, gy + 4, hz - 3, hx + 3, gy + 4, hz + 3, "minecraft:dark_prismarine")
# lanterns
for dx, dz in [(-8, -8), (8, -8), (-8, 8), (8, 8)]:
    s.put(CX + dx, gy + 1, CZ + dz, "minecraft:cobblestone_wall")
    s.put(CX + dx, gy + 2, CZ + dz, "minecraft:lantern[hanging=false]")
s.save("onsen")

# ================= 2. DOJO =================
s = Schem(33, 22, 33)
s.flatten(6)
gy = s.gy
CX, CZ = 16, 16
# floor 17x13
s.fill(CX - 8, gy, CZ - 6, CX + 8, gy, CZ + 6, "minecraft:oak_planks")
# tatami center (bamboo planks look)
s.fill(CX - 4, gy, CZ - 3, CX + 4, gy, CZ + 3, "minecraft:bamboo_planks")
# pillars
for y in range(gy + 1, gy + 5):
    for x in (-8, -4, 0, 4, 8):
        for z in (-6, 6):
            s.put(CX + x, y, CZ + z, LOG)
    for z in (-3, 0, 3):
        for x in (-8, 8):
            s.put(CX + x, y, CZ + z, LOG)
# beams
for x in range(CX - 8, CX + 9):
    s.put(x, gy + 5, CZ - 6, "minecraft:stripped_oak_log[axis=x]")
    s.put(x, gy + 5, CZ + 6, "minecraft:stripped_oak_log[axis=x]")
# gable roof
for i in range(8):
    z0, z1 = CZ - 7 + i, CZ + 7 - i
    if z0 > z1:
        break
    s.fill(CX - 9, gy + 6 + i, z0, CX + 9, gy + 6 + i, z1, "minecraft:dark_prismarine")
# weapon racks (fences with lanterns)
for dx in (-6, 6):
    s.put(CX + dx, gy + 1, CZ - 4, "minecraft:oak_fence")
    s.put(CX + dx, gy + 1, CZ + 4, "minecraft:oak_fence")
# hanging lanterns
for x in (-4, 0, 4):
    s.put(CX + x, gy + 4, CZ, "minecraft:lantern[hanging=true]")
# entrance steps south
s.fill(CX - 1, gy, CZ + 7, CX + 1, gy, CZ + 8, "minecraft:stone_bricks")
s.save("dojo")

# ================= 3. JINJA (grand shrine) =================
s = Schem(33, 28, 33)
s.flatten(6)
gy = s.gy
CX, CZ = 16, 16
# elevated stone platform 15x15, 3 high
s.fill(CX - 7, gy, CZ - 7, CX + 7, gy + 2, CZ + 7, "minecraft:stone_bricks")
py = gy + 3
# big torii at south entrance of platform
for dx in (-3, 3):
    for y in range(py, py + 6):
        s.put(CX + dx, y, CZ + 7, DLOG)
s.fill(CX - 4, py + 6, CZ + 7, CX + 4, py + 6, CZ + 7, "minecraft:dark_oak_planks")
s.fill(CX - 3, py + 7, CZ + 7, CX + 3, py + 7, CZ + 7, "minecraft:dark_oak_planks")
# main hall 7x7
hx, hz = CX, CZ - 2
s.fill(hx - 3, py, hz - 3, hx + 3, py, hz + 3, "minecraft:dark_oak_planks")
for y in (py + 1, py + 2):
    for x in (hx - 3, hx + 3):
        for z in (hz - 3, hz + 3):
            s.put(x, y, z, DLOG)
for x in range(hx - 3, hx + 4):
    s.put(x, py + 1, hz - 3, "minecraft:white_concrete")
    s.put(x, py + 1, hz + 3, "minecraft:white_concrete")
    s.put(x, py + 2, hz - 3, "minecraft:white_concrete")
    s.put(x, py + 2, hz + 3, "minecraft:white_concrete")
# offering box
s.put(hx, py + 1, hz + 2, "minecraft:chest[facing=south,type=single]")
s.put(hx, py + 2, hz, "minecraft:lantern[hanging=false]")
s.put(hx, py + 3, hz, "minecraft:gold_block")
# roof
for i in range(6):
    x0, x1 = hx - 5 + i, hx + 5 - i
    z0, z1 = hz - 5 + i, hz + 5 - i
    if x0 > x1:
        break
    s.fill(x0, py + 4 + i, z0, x1, py + 4 + i, z1, "minecraft:dark_prismarine")
# stone lantern path from torii to hall
for dz in (4, 1, -2):
    for dx in (-5, 5):
        s.put(CX + dx, py, CZ + dz, "minecraft:cobblestone")
        s.put(CX + dx, py + 1, CZ + dz, "minecraft:cobblestone_wall")
        s.put(CX + dx, py + 2, CZ + dz, "minecraft:lantern[hanging=false]")
# sacred tree
tx, tz = CX + 9, CZ - 6
for y in range(py, py + 4):
    s.put(tx, y, tz, "minecraft:oak_log[axis=y]")
for dx in range(-2, 3):
    for dz in range(-2, 3):
        s.put(tx + dx, py + 4, tz + dz, "minecraft:oak_leaves[persistent=true]")
        s.put(tx + dx, py + 5, tz + dz, "minecraft:oak_leaves[persistent=true]")
# stairs up platform (south)
for i in range(3):
    s.fill(CX - 1, gy + i, CZ + 8 + i, CX + 1, gy + i, CZ + 8 + i, "minecraft:stone_brick_stairs[facing=south,half=bottom,shape=straight]")
s.save("jinja")

# ================= 4. ZEN GARDEN =================
s = Schem(27, 14, 27)
s.flatten(5)
gy = s.gy
CX, CZ = 13, 13
# sand base with raked stripes (alternating)
for x in range(CX - 10, CX + 11):
    for z in range(CZ - 10, CZ + 11):
        s.put(x, gy, z, "minecraft:sand" if (x + z) % 4 < 2 else "minecraft:smooth_sandstone")
# rock clusters
for rx, rz, rs in [(CX - 5, CZ - 4, 2), (CX + 6, CZ + 3, 3), (CX - 1, CZ + 6, 1)]:
    for dx in range(-rs, rs + 1):
        for dz in range(-rs, rs + 1):
            if dx * dx + dz * dz <= rs * rs:
                s.put(rx + dx, gy + 1, rz + dz, "minecraft:stone")
                if dx == 0 and dz == 0:
                    s.put(rx, gy + 2, rz, "minecraft:cobblestone")
# mossy rocks
s.put(CX + 3, gy + 1, CZ - 6, "minecraft:mossy_cobblestone")
s.put(CX - 7, gy + 1, CZ + 5, "minecraft:mossy_cobblestone")
# bamboo clusters
for bx, bz in [(CX - 8, CZ - 8), (CX + 8, CZ - 8), (CX - 8, CZ + 8)]:
    for dx in (-1, 0, 1):
        for dz in (-1, 0, 1):
            hgt = 3 + ((dx + dz) % 2)
            for y in range(gy + 1, gy + 1 + hgt):
                s.put(bx + dx, y, bz + dz, "minecraft:bamboo_block")
# stone lantern center-east
s.put(CX + 8, gy + 1, CZ + 2, "minecraft:cobblestone")
s.put(CX + 8, gy + 2, CZ + 2, "minecraft:cobblestone_wall")
s.put(CX + 8, gy + 3, CZ + 2, "minecraft:lantern[hanging=false]")
# wooden bench
for dx in (-1, 0, 1):
    s.put(CX + dx, gy + 1, CZ + 8, "minecraft:oak_planks")
s.put(CX - 1, gy, CZ + 8, "minecraft:oak_log[axis=y]")
s.put(CX + 1, gy, CZ + 8, "minecraft:oak_log[axis=y]")
# low fence border
for x in range(CX - 10, CX + 11):
    s.put(x, gy + 1, CZ - 11, "minecraft:oak_fence")
    s.put(x, gy + 1, CZ + 11, "minecraft:oak_fence")
s.save("zen")

# ================= 5. BRIDGE + KOI POND =================
s = Schem(33, 16, 25)
s.flatten(5)
gy = s.gy
CX, CZ = 16, 12
# pond 17x11, 2 deep
for x in range(CX - 8, CX + 9):
    for z in range(CZ - 5, CZ + 6):
        s.put(x, gy, z, AIR)
        s.put(x, gy - 1, z, "minecraft:water")
        s.put(x, gy - 2, z, "minecraft:clay")
# pond edge stones
for x in range(CX - 9, CX + 10):
    for z in (CZ - 6, CZ + 6):
        s.put(x, gy + 1, z, "minecraft:cobblestone")
# lily pads
for lx, lz in [(CX - 5, CZ - 2), (CX + 3, CZ + 1), (CX - 1, CZ + 3), (CX + 6, CZ - 3)]:
    s.put(lx, gy, lz, "minecraft:lily_pad")
# arched bridge along x (red/crimson)
for i, x in enumerate(range(CX - 7, CX + 8)):
    # arch height: peaks at center
    arch = 3 - abs(x - CX) // 3
    y = gy + 1 + max(0, arch)
    for dx in (-1, 0, 1):
        s.put(x, y, CZ + dx, "minecraft:crimson_planks")
    # rails
    if i % 2 == 0:
        for dz in (-2, 2):
            s.put(x, y + 1, CZ + dz, "minecraft:crimson_fence")
# bridge supports
for x in (CX - 7, CX + 7):
    for y in range(gy - 1, gy + 2):
        s.put(x, y, CZ - 1, "minecraft:dark_oak_log[axis=y]")
        s.put(x, y, CZ + 1, "minecraft:dark_oak_log[axis=y]")
# lanterns at bridge ends
for dx in (-8, 8):
    s.put(CX + dx, gy + 1, CZ - 3, "minecraft:cobblestone_wall")
    s.put(CX + dx, gy + 2, CZ - 3, "minecraft:lantern[hanging=false]")
    s.put(CX + dx, gy + 1, CZ + 3, "minecraft:cobblestone_wall")
    s.put(CX + dx, gy + 2, CZ + 3, "minecraft:lantern[hanging=false]")
s.save("bridge")
print("semua schematic jadi!")
