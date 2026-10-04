#!/usr/bin/env python3
"""Ekspansi desa timur: chaya, izakaya, kura, kajiya, yagura, suisha, taman sakura, hokora."""
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
ROOF = "minecraft:dark_prismarine"

s = Schem(61, 30, 61)
s.flatten(8)
gy = s.gy

def house_base(cx, cz, w, d, floor_block):
    """fondasi + lantai"""
    s.fill(cx - w//2, gy, cz - d//2, cx + w//2, gy, cz + d//2, floor_block)

def walls(cx, cz, w, d, h, wall_block, corner_block=LOG):
    for y in range(gy + 1, gy + 1 + h):
        for x in (cx - w//2, cx + w//2):
            for z in range(cz - d//2, cz + d//2 + 1):
                s.put(x, y, z, corner_block if z in (cz - d//2, cz + d//2) else wall_block)
        for z in (cz - d//2, cz + d//2):
            for x in range(cx - w//2 + 1, cx + w//2):
                s.put(x, y, z, wall_block)

def gable_roof(cx, cz, w, d, base_y, over=1):
    for i in range(d//2 + over + 1):
        z0, z1 = cz - d//2 - over + i, cz + d//2 + over - i
        if z0 > z1: break
        s.fill(cx - w//2 - over, base_y + i, z0, cx + w//2 + over, base_y + i, z1, ROOF)

def door(cx, cz, facing):
    # pintu di sisi facing
    if facing == "south":
        s.put(cx, gy + 1, cz, AIR); s.put(cx, gy + 2, cz, AIR)
        s.put(cx, gy + 1, cz, "minecraft:dark_oak_door[facing=south,half=lower,hinge=left]")
        s.put(cx, gy + 2, cz, "minecraft:dark_oak_door[facing=south,half=upper,hinge=left]")
    elif facing == "north":
        s.put(cx, gy + 1, cz, "minecraft:dark_oak_door[facing=north,half=lower,hinge=left]")
        s.put(cx, gy + 2, cz, "minecraft:dark_oak_door[facing=north,half=upper,hinge=left]")

# ============ 1. CHAYA (kedai teh) di (12,15), 9x7 ============
cx, cz = 12, 15
house_base(cx, cz, 9, 7, "minecraft:bamboo_planks")
walls(cx, cz, 9, 7, 2, "minecraft:white_concrete")
# meja rendah (slab) + bantal (carpet)
for dx in (-2, 2):
    s.put(cx + dx, gy + 1, cz, "minecraft:oak_slab[type=bottom]")
    s.put(cx + dx - 1, gy + 1, cz + 1, "minecraft:red_carpet")
    s.put(cx + dx + 1, gy + 1, cz + 1, "minecraft:red_carpet")
# pintu selatan
for x in (cx - 1, cx + 1):
    s.put(x, gy + 1, cz + 3, AIR); s.put(x, gy + 2, cz + 3, AIR)
gable_roof(cx, cz, 9, 7, gy + 3)
s.put(cx, gy + 1, cz - 2, "minecraft:lantern[hanging=false]")

# ============ 2. IZAKAYA (kedai sake) di (48,15), 9x7 ============
cx, cz = 48, 15
house_base(cx, cz, 9, 7, "minecraft:dark_oak_planks")
walls(cx, cz, 9, 7, 2, "minecraft:oak_planks")
# noren (tirai) pakai banner merah di depan
for dx in (-2, 0, 2):
    s.put(cx + dx, gy + 2, cz + 4, "minecraft:red_banner")
# meja bar
s.fill(cx - 3, gy + 1, cz - 2, cx + 3, gy + 1, cz - 2, "minecraft:dark_oak_slab[type=top]")
# tong sake (barrel)
for dx in (-3, 3):
    s.put(cx + dx, gy + 1, cz + 2, "minecraft:barrel[facing=up]")
# pintu
for x in (cx - 1, cx + 1):
    s.put(x, gy + 1, cz + 3, AIR); s.put(x, gy + 2, cz + 3, AIR)
gable_roof(cx, cz, 9, 7, gy + 3)
# lentera merah (redstone lamp)
s.put(cx - 4, gy + 2, cz + 3, "minecraft:redstone_lantern" if False else "minecraft:lantern[hanging=false]")

# ============ 3. KURA (gudang) di (12,45), 7x7 ============
cx, cz = 12, 45
house_base(cx, cz, 7, 7, "minecraft:stone_bricks")
# dinding tebal putih
for y in range(gy + 1, gy + 4):
    for x in range(cx - 3, cx + 4):
        for z in (cz - 3, cz + 3):
            s.put(x, y, z, "minecraft:white_concrete")
    for z in range(cz - 2, cz + 3):
        for x in (cx - 3, cx + 3):
            s.put(x, y, z, "minecraft:white_concrete")
# jendela kecil
s.put(cx, gy + 2, cz - 3, "minecraft:iron_bars")
s.put(cx, gy + 2, cz + 3, "minecraft:iron_bars")
# pintu besi
s.put(cx, gy + 1, cz + 3, "minecraft:iron_door[facing=south,half=lower,hinge=left]")
s.put(cx, gy + 2, cz + 3, "minecraft:iron_door[facing=south,half=upper,hinge=left]")
s.put(cx, gy + 1, cz + 4, "minecraft:stone_button[face=floor,facing=south]")
# atap curam
for i in range(5):
    x0, x1 = cx - 4 + i, cx + 4 - i
    z0, z1 = cz - 4 + i, cz + 4 - i
    if x0 > x1: break
    s.fill(x0, gy + 4 + i, z0, x1, gy + 4 + i, z1, "minecraft:deepslate_tiles")

# ============ 4. KAJIYA (pandai besi) di (48,45), 9x7 ============
cx, cz = 48, 45
house_base(cx, cz, 9, 7, "minecraft:cobbled_deepslate")
# depan terbuka (tanpa dinding selatan)
for y in range(gy + 1, gy + 3):
    for x in (cx - 4, cx + 4):
        for z in range(cz - 3, cz + 4):
            s.put(x, y, z, DLOG)
    for z in (cz - 3,):
        for x in range(cx - 3, cx + 4):
            s.put(x, y, z, "minecraft:cobblestone")
# tungku (furnace + campfire)
s.put(cx - 2, gy + 1, cz - 2, "minecraft:blast_furnace[facing=south]")
s.put(cx + 2, gy + 1, cz - 2, "minecraft:campfire[lit=true]")
s.put(cx, gy + 1, cz - 2, "minecraft:anvil")
# tong air (cauldron)
s.put(cx + 3, gy + 1, cz + 1, "minecraft:water_cauldron[level=3]")
gable_roof(cx, cz, 9, 7, gy + 3)

# ============ 5. YAGURA (menara) di (30,30), 5x5, tinggi 14 ============
cx, cz = 30, 30
s.fill(cx - 2, gy, cz - 2, cx + 2, gy, cz + 2, "minecraft:stone_bricks")
for y in range(gy + 1, gy + 10):
    for x in (cx - 2, cx + 2):
        for z in (cx - 2, cx + 2):
            s.put(x, y, cz + (z - cx), DLOG)
# platform
s.fill(cx - 3, gy + 10, cz - 3, cx + 3, gy + 10, cz + 3, "minecraft:dark_oak_planks")
for x in range(cx - 3, cx + 4):
    for z in (cz - 3, cz + 3):
        s.put(x, gy + 11, z, "minecraft:dark_oak_fence")
for z in range(cz - 2, cz + 3):
    for x in (cx - 3, cx + 3):
        s.put(x, gy + 11, z, "minecraft:dark_oak_fence")
# atap
for i in range(5):
    x0, x1 = cx - 4 + i, cx + 4 - i
    z0, z1 = cz - 4 + i, cz + 4 - i
    if x0 > x1: break
    s.fill(x0, gy + 12 + i, z0, x1, gy + 12 + i, z1, ROOF)
# tangga naik (ladder)
for y in range(gy + 1, gy + 10):
    s.put(cx + 2, y, cz, "minecraft:ladder[facing=west]")

# ============ 6. SUISHA (kincir air) di (30,8) ============
cx, cz = 30, 8
# sungai kecil utara-selatan
for z in range(2, 14):
    for x in range(cx - 1, cx + 2):
        s.put(x, gy, z, AIR)
        s.put(x, gy - 1, z, "minecraft:water")
# gubuk kincir
house_base(cx + 5, cz, 7, 6, "minecraft:oak_planks")
walls(cx + 5, cz, 7, 6, 2, "minecraft:oak_planks")
gable_roof(cx + 5, cz, 7, 6, gy + 3)
# roda air (lingkaran vertikal, diameter 7)
wx = cx - 1
for dy in range(-3, 4):
    for dz in range(-3, 4):
        if abs(dy) + abs(dz) <= 4 and (dy*dy + dz*dz) >= 4:
            s.put(wx, gy + 3 + dy, cz + dz, "minecraft:dark_oak_planks")
# jari-jari
for d in range(-3, 4):
    s.put(wx, gy + 3 + d, cz, "minecraft:dark_oak_log[axis=y]")
    s.put(wx, gy + 3, cz + d, "minecraft:dark_oak_log[axis=z]")
s.put(wx, gy + 3, cz, "minecraft:stripped_dark_oak_log[axis=x]")

# ============ 7. TAMAN SAKURA di (30,52) ============
cx, cz = 30, 52
# 3 pohon sakura
for tx, tz in [(cx - 6, cz - 3), (cx + 6, cz - 3), (cx, cz + 4)]:
    for y in range(gy + 1, gy + 4):
        s.put(tx, y, tz, "minecraft:cherry_log[axis=y]")
    for dx in range(-2, 3):
        for dz in range(-2, 3):
            s.put(tx + dx, gy + 4, tz + dz, "minecraft:cherry_leaves[persistent=true]")
            if abs(dx) < 2 and abs(dz) < 2:
                s.put(tx + dx, gy + 5, tz + dz, "minecraft:cherry_leaves[persistent=true]")
    # kelopak jatuh
    s.put(tx + 2, gy + 1, tz + 1, "minecraft:pink_petals[flower_amount=3]")
# kolam kecil
for x in range(cx - 2, cx + 3):
    for z in range(cz - 1, cz + 2):
        s.put(x, gy, z, AIR)
        s.put(x, gy - 1, z, "minecraft:water")
# bangku
for dx in (-3, -2, 2, 3):
    s.put(cx + dx, gy + 1, cz + 6, "minecraft:cherry_planks")
s.put(cx - 3, gy, cz + 6, "minecraft:cherry_log[axis=y]")
s.put(cx + 3, gy, cz + 6, "minecraft:cherry_log[axis=y]")

# ============ 8. HOKORA (kuil kecil) di (20,30) & (40,30) ============
for hx, hz in [(20, 30), (40, 30)]:
    s.fill(hx - 1, gy, hz - 1, hx + 1, gy, hz + 1, "minecraft:stone_bricks")
    for dx in (-1, 1):
        s.put(hx + dx, gy + 1, hz, "minecraft:stone_brick_wall")
    s.put(hx, gy + 1, hz, "minecraft:lantern[hanging=false]")
    s.fill(hx - 1, gy + 2, hz - 1, hx + 1, gy + 2, hz + 1, "minecraft:stone_brick_slab[type=top]")

# ============ jalan utama timur-barat ============
for x in range(2, 59):
    for w in (-1, 0, 1):
        s.put(x, gy, 30 + w, "minecraft:gravel" if w == 0 else "minecraft:cobblestone")
# lentera jalan
for lx in (10, 25, 35, 50):
    s.put(lx, gy + 1, 28, "minecraft:cobblestone_wall")
    s.put(lx, gy + 2, 28, "minecraft:lantern[hanging=false]")
    s.put(lx, gy + 1, 32, "minecraft:cobblestone_wall")
    s.put(lx, gy + 2, 32, "minecraft:lantern[hanging=false]")

s.save("village3")
print("selesai!")
