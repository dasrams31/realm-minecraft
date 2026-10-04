#!/usr/bin/env python3
"""Benteng gerbang masif: istana tembok raksasa di atas tembok utama."""
import nbtlib
from nbtlib import Compound, Int, Short, ByteArray, IntArray, List
AIR="minecraft:air"

def save(blocks,W,H,L,name):
    order=[]
    for y in range(H):
        for z in range(L):
            for x in range(W):
                order.append(blocks.get((x,y,z),AIR))
    palette,pal_list={},[]
    for b in order:
        if b not in palette: palette[b]=len(pal_list); pal_list.append(b)
    out=bytearray()
    for b in order:
        v=palette[b]
        while True:
            bits=v&0x7F; v>>=7
            if v: out.append(bits|0x80)
            else: out.append(bits); break
    try:
        w=nbtlib.load("/home/hatch/workspace/minecraft/server/world/level.dat"); dv=int(w["Data"]["DataVersion"])
    except: dv=4435
    schem=Compound({"Version":Int(3),"DataVersion":Int(dv),"Width":Short(W),"Height":Short(H),
        "Length":Short(L),"Offset":IntArray([0,0,0]),
        "Blocks":Compound({"Palette":Compound({k:Int(v) for k,v in palette.items()}),
            "Data":ByteArray(out),"BlockEntities":List([])}),"Entities":List([])})
    dest=f"/home/hatch/workspace/minecraft/server/plugins/WorldEdit/schematics/{name}.schem"
    nbtlib.File({"Schematic":schem}).save(dest,gzipped=True)
    print(f"{name}: {sum(1 for b in order if b!=AIR)} blok")

W,H,L = 51, 30, 21
B = {}
def put(x,y,z,b):
    if 0<=x<W and 0<=y<H and 0<=z<L: B[(x,y,z)]=b
def fill(x1,y1,z1,x2,y2,z2,b):
    for x in range(min(x1,x2),max(x1,x2)+1):
        for y in range(min(y1,y2),max(y1,y2)+1):
            for z in range(min(z1,z2),max(z1,z2)+1): put(x,y,z,b)

STONE="minecraft:stone_bricks"
DARK="minecraft:deepslate_bricks"
ROOF="minecraft:deepslate_tiles"
GOLD="minecraft:gold_block"
WOOD="minecraft:dark_oak_planks"

cx = W//2
# Dua menara raksasa (kiri-kanan)
for sx in [8, 42]:
    # Badan menara
    fill(sx-6,0,2,sx+6,22,18,STONE)
    fill(sx-5,1,3,sx+5,21,17,AIR)
    # Jendela
    for y in [6,12,18]:
        for x in range(sx-6,sx+7):
            put(x,y,2,"minecraft:iron_bars"); put(x,y,18,"minecraft:iron_bars")
    # Atap menara
    fill(sx-8,23,0,sx+8,23,20,ROOF)
    fill(sx-6,24,2,sx+6,24,18,ROOF)
    fill(sx-4,25,4,sx+4,25,16,ROOF)
    put(sx,26,10,GOLD)
    # Tangga dalam
    for y in range(1,22):
        put(sx,y,10,"minecraft:stone_brick_stairs[facing=north,half=bottom,shape=straight]")

# Jembatan penghubung di atas (lantai 2)
fill(2,14,7,48,16,13,STONE)
fill(3,15,8,47,15,12,AIR)
# Jendela jembatan
for x in range(4,48,4):
    put(x,15,7,"minecraft:iron_bars"); put(x,15,13,"minecraft:iron_bars")
# Atap jembatan
fill(0,17,5,50,17,15,ROOF)
fill(4,18,7,46,18,13,ROOF)

# Gerbang utama di bawah (lorong)
for y in range(0,10):
    for x in range(cx-4,cx+5):
        for z in range(2,19): put(x,y,z,AIR)
# Pilar gerbang
for x in [cx-5,cx+5]:
    fill(x,0,2,x,12,18,DARK)
# Lengkung atas gerbang
fill(cx-6,10,2,cx+6,12,18,DARK)
fill(cx-4,10,2,cx+4,12,18,AIR)

# Dek observasi atas
fill(10,27,4,40,27,16,WOOD)
for x in range(10,41):
    put(x,28,4,"minecraft:cobblestone_wall"); put(x,28,16,"minecraft:cobblestone_wall")
# Lentera
for x in [14,25,36]:
    put(x,27,10,"minecraft:lantern[hanging=false]")

# Spanduk
for x in [20,30]:
    put(x,16,7,"minecraft:red_banner"); put(x,16,13,"minecraft:red_banner")

save(B,W,H,L,"gerbang_masif")
print("Gerbang masif jadi!")
