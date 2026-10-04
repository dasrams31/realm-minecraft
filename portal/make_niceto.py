#!/usr/bin/env python3
"""Nice to have: akademi samurai, pasar malam."""
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

def new(w,h,l): return {},w,h,l
def put(B,x,y,z,b):
    _,W,H,L=B
    if 0<=x<W and 0<=y<H and 0<=z<L: B[0][(x,y,z)]=b
def fill(B,x1,y1,z1,x2,y2,z2,b):
    for x in range(min(x1,x2),max(x1,x2)+1):
        for y in range(min(y1,y2),max(y1,y2)+1):
            for z in range(min(z1,z2),max(z1,z2)+1): put(B,x,y,z,b)

# AKADEMI SAMURAI (35x14x29): dojo besar + asrama
B=new(35,14,29)
# Dojo utama (tengah)
fill(B,10,0,8,24,0,20,"minecraft:stone_bricks")
fill(B,10,1,8,24,1,20,"minecraft:spruce_planks")
for y in range(2,8):
    for x in range(10,25):
        for z in (8,20): put(B,x,y,z,"minecraft:white_concrete")
for y in range(2,8):
    for z in range(9,20):
        for x in (10,24): put(B,x,y,z,"minecraft:white_concrete")
# Tatami
fill(B,12,2,10,22,2,18,"minecraft:green_wool")
# Rak senjata
for x in (12,22):
    put(B,x,2,9,"minecraft:armor_stand" if False else "minecraft:oak_fence")
    put(B,x,3,9,"minecraft:iron_sword" if False else "minecraft:lantern[hanging=false]")
# Atap dojo
fill(B,8,8,6,26,8,22,"minecraft:deepslate_tiles")
fill(B,10,9,8,24,9,20,"minecraft:deepslate_tiles")
# Asrama kiri
fill(B,0,0,0,8,0,12,"minecraft:cobblestone")
for y in range(1,5):
    for x in range(0,9):
        for z in (0,12): put(B,x,y,z,"minecraft:dark_oak_planks")
# Asrama kanan
fill(B,26,0,0,34,0,12,"minecraft:cobblestone")
for y in range(1,5):
    for x in range(26,35):
        for z in (0,12): put(B,x,y,z,"minecraft:dark_oak_planks")
# Tempat tidur asrama
for x in (2,4,6):
    put(B,x,1,2,"minecraft:blue_bed[part=head,facing=south]")
    put(B,28+x-2,1,2,"minecraft:blue_bed[part=head,facing=south]")
# Gerbang akademi
for y in range(1,6):
    for x in (16,18): put(B,x,y,0,"minecraft:stripped_dark_oak_log[axis=y]")
put(B,17,5,0,"minecraft:deepslate_tiles")
save(*B,"akademi_samurai")

# PASAR MALAM (29x10x21): kios + lentera warna-warni
B=new(29,10,21)
fill(B,0,0,0,28,0,20,"minecraft:gravel")
# 8 kios (4 kiri, 4 kanan)
colors = ["red","blue","yellow","green","orange","purple","cyan","pink"]
for i in range(4):
    for side,z in [(0,3),(1,15)]:
        x = 3+i*7
        # Meja kios
        fill(B,x,1,z,x+3,1,z+2,"minecraft:oak_planks")
        # Tiang
        for (px,pz) in [(x,z),(x+3,z),(x,z+2),(x+3,z+2)]:
            for y in range(1,5): put(B,px,y,pz,"minecraft:stripped_oak_log[axis=y]")
        # Atap warna-warni
        c = colors[i*2+side]
        fill(B,x-1,5,z-1,x+4,5,z+3,f"minecraft:{c}_wool")
        # Barang dagangan
        put(B,x+1,2,z+1,"minecraft:barrel[facing=up]")
# Lentera gantung di tengah jalan
for x in range(4,26,4):
    for y in range(4,6): put(B,x,y,10,"minecraft:dark_oak_fence")
    put(B,x,6,10,"minecraft:lantern[hanging=false]")
# Gapura masuk
for y in range(1,7):
    put(B,0,y,10,"minecraft:stripped_dark_oak_log[axis=y]")
    put(B,28,y,10,"minecraft:stripped_dark_oak_log[axis=y]")
fill(B,-1,7,9,29,7,11,"minecraft:deepslate_tiles")
save(*B,"pasar_malam")
print("2 nice-to-have jadi!")
