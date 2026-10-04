#!/usr/bin/env python3
"""Desa satelit: rumah minka, torii besar, hokora, sumur, sawah."""
import nbtlib
from nbtlib import Compound, Int, Short, ByteArray, IntArray, List

AIR="minecraft:air"; WOOD="minecraft:dark_oak_planks"; OAK="minecraft:oak_planks"
BEAM="minecraft:stripped_dark_oak_log[axis=y]"; BEAMX="minecraft:stripped_dark_oak_log[axis=x]"
WALL="minecraft:white_concrete"; ROOF="minecraft:deepslate_tiles"
GLASS="minecraft:white_stained_glass"; STONE="minecraft:cobblestone"
THATCH="minecraft:hay_block"; LANTERN="minecraft:lantern[hanging=false]"
RED="minecraft:stripped_crimson_stem[axis=y]"

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
    print(f"{name}: {W}x{H}x{L} non-air {sum(1 for b in order if b!=AIR)}")

def new(w,h,l): return {},w,h,l
def put(B,x,y,z,b):
    _,W,H,L=B
    if 0<=x<W and 0<=y<H and 0<=z<L: B[0][(x,y,z)]=b
def fill(B,x1,y1,z1,x2,y2,z2,b):
    for x in range(min(x1,x2),max(x1,x2)+1):
        for y in range(min(y1,y2),max(y1,y2)+1):
            for z in range(min(z1,z2),max(z1,z2)+1): put(B,x,y,z,b)
def stairs(B,x,y,z,f,mat="minecraft:deepslate_tile_stairs"):
    put(B,x,y,z,f"{mat}[facing={f},half=bottom,shape=straight]")

# ===== MINKA (rumah petani atap jerami 13x9x11) =====
B=new(13,9,11); CX,CZ=6,5
fill(B,0,0,0,12,0,10,STONE); fill(B,1,1,1,11,1,9,"minecraft:dark_oak_planks")
for y in range(2,5):
    for x in range(1,12):
        for z in (1,9): put(B,x,y,z,WALL)
    for z in range(2,9):
        for x in (1,11): put(B,x,y,z,WALL)
for y in range(2,5):
    for x in (1,6,11):
        for z in (1,9): put(B,x,y,z,BEAM)
for x in range(1,12): put(B,x,5,1,BEAMX); put(B,x,5,9,BEAMX)
# atap jerami curam khas minka
for y in range(6,9):
    wdt = 7-(y-6)*2
    if wdt < 1: break
    h=wdt//2
    fill(B,CX-h,y,CZ-5,CX+h,y,CZ+5,THATCH)
# pintu + jendela
for y in (2,3): put(B,6,y,9,AIR); put(B,5,y,9,AIR)
put(B,3,3,1,GLASS); put(B,9,3,1,GLASS)
# irori (perapian dalam)
put(B,6,2,5,"minecraft:campfire[lit=false]")
save(*B,"minka")

# ===== TORII BESAR (11x10x3) =====
B=new(11,10,3)
for y in range(0,8):
    put(B,2,y,1,RED); put(B,8,y,1,RED)
fill(B,0,8,1,10,9,1,"minecraft:stripped_crimson_stem[axis=x]")
fill(B,1,7,1,9,7,1,"minecraft:stripped_crimson_stem[axis=x]")
put(B,5,10,1,"minecraft:stripped_crimson_stem[axis=x]")
# papan nama
put(B,5,8,0,"minecraft:dark_oak_sign")
save(*B,"torii_big")

# ===== HOKORA (kuil kecil 5x6x5) =====
B=new(5,6,5)
fill(B,0,0,0,4,0,4,STONE)
fill(B,1,1,1,3,3,3,WALL)
put(B,2,2,3,AIR); put(B,2,3,3,AIR)
put(B,2,2,2,"minecraft:gold_block")
for x in range(0,5):
    stairs(B,x,4,0,"north"); stairs(B,x,4,4,"south")
for z in range(1,4):
    stairs(B,0,4,z,"west"); stairs(B,4,4,z,"east")
fill(B,1,4,1,3,4,3,ROOF)
put(B,2,5,2,ROOF)
save(*B,"hokora")

# ===== SUMUR (5x5x5) =====
B=new(5,5,5)
for (x,z) in [(1,1),(1,3),(3,1),(3,3)]:
    put(B,x,1,z,STONE); put(B,x,2,z,STONE)
fill(B,1,1,1,3,1,3,"minecraft:water")
for y in range(1,4):
    put(B,1,y,2,BEAM); put(B,3,y,2,BEAM)
fill(B,0,4,2,4,4,2,WOOD)
put(B,2,3,2,"minecraft:lantern[hanging=true]")
save(*B,"sumur")

print("5 schematic desa satelit jadi!")
