#!/usr/bin/env python3
"""Tower variasi: pagoda mini, menara batu, menara kayu."""
import nbtlib
from nbtlib import Compound, Int, Short, ByteArray, IntArray, List

AIR="minecraft:air"; STONE="minecraft:stone_bricks"; WOOD="minecraft:dark_oak_planks"
BEAM="minecraft:stripped_dark_oak_log[axis=y]"; ROOF="minecraft:deepslate_tiles"
WALL="minecraft:white_concrete"; GLASS="minecraft:white_stained_glass"

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
    print(f"{name}: non-air {sum(1 for b in order if b!=AIR)}")

def new(w,h,l): return {},w,h,l
def put(B,x,y,z,b):
    _,W,H,L=B
    if 0<=x<W and 0<=y<H and 0<=z<L: B[0][(x,y,z)]=b
def fill(B,x1,y1,z1,x2,y2,z2,b):
    for x in range(min(x1,x2),max(x1,x2)+1):
        for y in range(min(y1,y2),max(y1,y2)+1):
            for z in range(min(z1,z2),max(z1,z2)+1): put(B,x,y,z,b)

# Tower 1: Pagoda mini 3 tingkat (7x18x7)
B=new(7,18,7)
fill(B,0,0,0,6,2,6,STONE)
fill(B,1,3,1,5,3,5,WOOD)
for y in range(4,6):
    for x in range(1,6):
        for z in (1,5): put(B,x,y,z,WALL)
    for z in range(2,5):
        for x in (1,5): put(B,x,y,z,WALL)
fill(B,0,6,0,6,6,6,ROOF); fill(B,1,7,1,5,7,5,ROOF)
fill(B,2,8,2,4,8,4,WOOD)
for y in range(9,11):
    for x in range(2,5):
        for z in (2,4): put(B,x,y,z,WALL)
fill(B,1,11,1,5,11,5,ROOF); fill(B,2,12,2,4,12,4,ROOF)
put(B,3,13,3,WOOD); fill(B,2,14,2,4,14,4,ROOF)
put(B,3,15,3,"minecraft:gold_block")
save(*B,"tower_pagoda")

# Tower 2: Menara batu kokoh (9x16x9)
B=new(9,16,9)
fill(B,0,0,0,8,10,8,STONE)
fill(B,1,1,1,7,9,7,AIR)
fill(B,3,1,3,5,1,5,"minecraft:oak_planks")
for y in (4,7):
    for x in (2,4,6):
        put(B,x,y,0,"minecraft:iron_bars"); put(B,x,y,8,"minecraft:iron_bars")
# Puncak + api
fill(B,0,11,0,8,11,8,STONE)
fill(B,0,12,0,0,12,8,STONE); fill(B,8,12,0,8,12,8,STONE)
fill(B,0,12,0,8,12,0,STONE); fill(B,0,12,8,8,12,8,STONE)
put(B,4,11,4,"minecraft:campfire[lit=true]")
save(*B,"tower_stone")

# Tower 3: Menara kayu tinggi (7x20x7)
B=new(7,20,7)
for (x,z) in [(1,1),(1,5),(5,1),(5,5)]:
    for y in range(0,16): put(B,x,y,z,BEAM)
for y in range(0,16,4):
    fill(B,1,y,1,5,y,5,WOOD)
    fill(B,2,y+1,2,4,y+1,4,AIR)
# Gardu atas
fill(B,0,16,0,6,16,6,WOOD)
for y in range(17,19):
    for x in range(0,7):
        for z in (0,6): put(B,x,y,z,WALL)
    for z in range(1,6):
        for x in (0,6): put(B,x,y,z,WALL)
fill(B,0,19,0,6,19,6,ROOF)
put(B,3,17,3,"minecraft:lantern[hanging=false]")
save(*B,"tower_wood")
print("3 tower variasi jadi!")
