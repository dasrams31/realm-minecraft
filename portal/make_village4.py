#!/usr/bin/env python3
"""Ekspansi desa barat: sakagura, terakoya, klinik, pasar malam, makam, kebun teh."""
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
        for x in range(min(x1,x2), max(x1,x2)+1):
            for y in range(min(y1,y2), max(y1,y2)+1):
                for z in range(min(z1,z2), max(z1,z2)+1):
                    self.put(x, y, z, b)
    def flatten(self, gy_local):
        self.fill(0, 0, 0, self.W-1, gy_local-1, self.L-1, "minecraft:dirt")
        self.fill(0, gy_local, 0, self.W-1, gy_local, self.L-1, "minecraft:grass_block")
        self.gy = gy_local + 1
    def save(self, name):
        pal = sorted(set(self.blocks.values()))
        if AIR not in pal: pal = [AIR] + pal
        pi = {b: i for i, b in enumerate(pal)}
        order = [self.blocks.get((x,y,z), AIR) for y in range(self.H) for z in range(self.L) for x in range(self.W)]
        out = bytearray()
        for b in order:
            v = pi[b]
            while True:
                bits = v & 0x7F; v >>= 7
                out.append(bits | 0x80) if v else out.append(bits)
                if not v: break
        w = nbtlib.load("/home/hatch/workspace/minecraft/server/world/level.dat")
        dv = int(w["Data"]["DataVersion"])
        s = Compound({"Version": Int(3), "DataVersion": Int(dv), "Width": Short(self.W),
            "Height": Short(self.H), "Length": Short(self.L), "Offset": IntArray([0,0,0]),
            "Blocks": Compound({"Palette": Compound({k: Int(v) for k,v in pi.items()}),
            "Data": ByteArray(out), "BlockEntities": List([])}), "Entities": List([])})
        nbtlib.File({"Schematic": s}).save(
            f"/home/hatch/workspace/minecraft/server/plugins/WorldEdit/schematics/{name}.schem", gzipped=True)
        print(f"{name}: {self.W}x{self.H}x{self.L}")

LOG = "minecraft:stripped_oak_log[axis=y]"
ROOF = "minecraft:dark_prismarine"
s = Schem(55, 26, 61)
s.flatten(8)
gy = s.gy

def base(cx, cz, w, d, f):
    s.fill(cx-w//2, gy, cz-d//2, cx+w//2, gy, cz+d//2, f)
def walls(cx, cz, w, d, h, wb):
    for y in range(gy+1, gy+1+h):
        for x in (cx-w//2, cx+w//2):
            for z in range(cz-d//2, cz+d//2+1): s.put(x, y, z, LOG)
        for z in (cz-d//2, cz+d//2):
            for x in range(cx-w//2+1, cx+w//2): s.put(x, y, z, wb)
def roof(cx, cz, w, d, by):
    for i in range(d//2+2):
        z0, z1 = cz-d//2-1+i, cz+d//2+1-i
        if z0 > z1: break
        s.fill(cx-w//2-1, by+i, z0, cx+w//2+1, by+i, z1, ROOF)

# 1. SAKAGURA (pabrik sake) di (14,15), 13x9
cx, cz = 14, 15
base(cx, cz, 13, 9, "minecraft:dark_oak_planks")
walls(cx, cz, 13, 9, 3, "minecraft:oak_planks")
# tong sake besar
for dx, dz in [(-4,-2), (-4,2), (4,-2), (4,2), (0,0)]:
    s.put(cx+dx, gy+1, cz+dz, "minecraft:barrel[facing=up]")
    s.put(cx+dx, gy+2, cz+dz, "minecraft:barrel[facing=up]")
# cerobong
s.fill(cx+5, gy+1, cz-3, cx+5, gy+5, cz-3, "minecraft:bricks")
s.put(cx+5, gy+6, cz-3, "minecraft:campfire[lit=true]")
roof(cx, cz, 13, 9, gy+4)

# 2. TERAKOYA (sekolah) di (40,15), 11x8
cx, cz = 40, 15
base(cx, cz, 11, 8, "minecraft:oak_planks")
walls(cx, cz, 11, 8, 2, "minecraft:white_concrete")
# meja murid
for dx in (-3, -1, 1, 3):
    s.put(cx+dx, gy+1, cz, "minecraft:oak_slab[type=bottom]")
    s.put(cx+dx, gy+1, cz+1, "minecraft:oak_stairs[facing=north,half=bottom,shape=straight]")
# papan tulis
s.fill(cx-2, gy+2, cz-3, cx+2, gy+3, cz-3, "minecraft:black_concrete")
roof(cx, cz, 11, 8, gy+3)
s.put(cx, gy+1, cz+2, "minecraft:lantern[hanging=false]")

# 3. KLINIK di (14,45), 9x7
cx, cz = 14, 45
base(cx, cz, 9, 7, "minecraft:white_concrete")
walls(cx, cz, 9, 7, 2, "minecraft:white_concrete")
# palang merah (red concrete cross di depan)
s.fill(cx-1, gy+3, cz+4, cx+1, gy+3, cz+4, "minecraft:red_concrete")
s.put(cx, gy+2, cz+4, "minecraft:red_concrete")
s.put(cx, gy+4, cz+4, "minecraft:red_concrete")
# tempat tidur
s.put(cx-2, gy+1, cz-1, "minecraft:white_bed[facing=east,part=head]")
s.put(cx-3, gy+1, cz-1, "minecraft:white_bed[facing=east,part=foot]")
s.put(cx+2, gy+1, cz-1, "minecraft:white_bed[facing=west,part=head]")
s.put(cx+3, gy+1, cz-1, "minecraft:white_bed[facing=west,part=foot]")
roof(cx, cz, 9, 7, gy+3)

# 4. PASAR MALAM (4 kios) di (40,45)
for i, (kx, kz, warna) in enumerate([(36,42,"red"), (44,42,"blue"), (36,48,"yellow"), (44,48,"green")]):
    s.fill(kx-1, gy, kz-1, kx+1, gy, kz+1, "minecraft:oak_planks")
    for dx, dz in [(-1,-1), (1,-1), (-1,1), (1,1)]:
        s.put(kx+dx, gy+1, kz+dz, LOG)
        s.put(kx+dx, gy+2, kz+dz, LOG)
    s.fill(kx-2, gy+3, kz-2, kx+2, gy+3, kz+2, f"minecraft:{warna}_concrete")
    s.put(kx, gy+1, kz, "minecraft:campfire[lit=true]")
    s.put(kx, gy+2, kz, "minecraft:lantern[hanging=true]")

# 5. MAKAM di (27,8), area 15x10
cx, cz = 27, 8
s.fill(cx-7, gy, cz-4, cx+7, gy, cz+4, "minecraft:mossy_cobblestone")
for i, (mx, mz) in enumerate([(cx-5,cz-2), (cx-2,cz), (cx+1,cz-2), (cx+4,cz), (cx-3,cz+2), (cx+3,cz+2)]):
    s.put(mx, gy+1, mz, "minecraft:stone_bricks")
    s.put(mx, gy+2, mz, "minecraft:stone_brick_wall")
    s.put(mx, gy+3, mz, "minecraft:stone_brick_slab[type=top]")
# gapura kecil
for dx in (-8, 8):
    s.put(cx+dx, gy+1, cz, "minecraft:cobblestone_wall")
    s.put(cx+dx, gy+2, cz, "minecraft:cobblestone_wall")
s.fill(cx-8, gy+3, cz, cx+8, gy+3, cz, "minecraft:stone_bricks")

# 6. KEBUN TEH terasering di (27,55)
cx, cz = 27, 55
for t in range(4):
    z = cz - 6 + t * 4
    y = gy + t
    s.fill(cx-10, y, z, cx+10, y, z+3, "minecraft:grass_block")
    s.fill(cx-10, y, z+3, cx+10, y, z+3, "minecraft:dirt")
    # tanaman teh (bush)
    for x in range(cx-9, cx+10, 3):
        s.put(x, y+1, z+1, "minecraft:oak_leaves[persistent=true]")

# jalan utama
for x in range(2, 53):
    for w in (-1, 0, 1):
        s.put(x, gy, 30+w, "minecraft:gravel" if w == 0 else "minecraft:cobblestone")
for lx in (10, 27, 44):
    s.put(lx, gy+1, 28, "minecraft:cobblestone_wall")
    s.put(lx, gy+2, 28, "minecraft:lantern[hanging=false]")

s.save("village4")
print("selesai!")
