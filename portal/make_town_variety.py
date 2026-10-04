#!/usr/bin/env python3
"""Bangunan variasi untuk perluasan jokamachi: sakagura, kajiya, chaya, yagura, dojo, kura, sento, barak."""
import nbtlib
from nbtlib import Compound, Int, Short, ByteArray, IntArray, List

AIR="minecraft:air"; WALL="minecraft:white_concrete"; WOOD="minecraft:dark_oak_planks"
OAK="minecraft:oak_planks"; BEAM="minecraft:stripped_dark_oak_log[axis=y]"
BEAMX="minecraft:stripped_dark_oak_log[axis=x]"; ROOF="minecraft:deepslate_tiles"
GLASS="minecraft:white_stained_glass"; STONE="minecraft:cobblestone"
SBRICK="minecraft:stone_bricks"; LANTERN="minecraft:lantern[hanging=false]"
RED="minecraft:stripped_crimson_stem[axis=y]"; PLASTER="minecraft:white_concrete"

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
def stairs(B,x,y,z,f):
    put(B,x,y,z,f"minecraft:deepslate_tile_stairs[facing={f},half=bottom,shape=straight]")
def roof(B,cx,cz,size,y):
    h=size//2; x0,x1=cx-h,cx+h; z0,z1=cz-h,cz+h
    for x in range(x0,x1+1): stairs(B,x,y,z0,"north"); stairs(B,x,y,z1,"south")
    for z in range(z0+1,z1): stairs(B,x0,y,z,"west"); stairs(B,x1,y,z,"east")
    fill(B,x0+1,y,z0+1,x1-1,y,z1-1,ROOF)
    s,yy=size-2,y+1
    while s>=3:
        hh=s//2; fill(B,cx-hh,yy,cz-hh,cx+hh,yy,cz+hh,ROOF); s-=2; yy+=1
def walls(B,x0,x1,z0,z1,y1,y2,mat,corner=None):
    for y in range(y1,y2+1):
        for x in range(x0,x1+1):
            for z in (z0,z1): put(B,x,y,z,mat)
        for z in range(z0+1,z1):
            for x in (x0,x1): put(B,x,y,z,mat)
    if corner:
        for y in range(y1,y2+1):
            for x in (x0,x1):
                for z in (z0,z1): put(B,x,y,z,corner)

# ===== 1. SAKAGURA (pabrik sake, 19x12x15, cerobong) =====
B=new(19,12,15); CX,CZ=9,7
fill(B,0,0,0,18,0,14,STONE); fill(B,1,1,1,17,1,13,OAK)
walls(B,1,17,1,13,2,5,WALL,BEAM)
for x in range(1,18): put(B,x,6,1,BEAMX); put(B,x,6,13,BEAMX)
for x in (4,8,12,16): put(B,x,3,1,GLASS); put(B,x,3,13,GLASS)
for y in (2,3,4): put(B,9,y,13,AIR); put(B,10,y,13,AIR)  # pintu ganda
# cerobong asap
fill(B,14,2,10,16,9,12,SBRICK); put(B,15,10,11,"minecraft:campfire[lit=true]")
roof(B,CX,CZ,21,7)
# tong sake di dalam
for (x,z) in [(4,4),(6,4),(4,6)]: put(B,x,2,z,"minecraft:barrel[facing=up]")
save(*B,"sakagura")

# ===== 2. KAJIYA (pandai besi, 15x10x13, perapian) =====
B=new(15,10,13); CX,CZ=7,6
fill(B,0,0,0,14,0,12,STONE); fill(B,1,1,1,13,1,11,"minecraft:blackstone")
walls(B,1,13,1,11,2,4,"minecraft:cobbled_deepslate",BEAM)
for x in range(1,14): put(B,x,5,1,BEAMX); put(B,x,5,11,BEAMX)
# perapian + cerobong
fill(B,5,2,4,9,4,6,"minecraft:furnace[facing=south]")
fill(B,6,5,4,8,8,6,SBRICK)
put(B,7,2,8,"minecraft:lava")  # bara api (hiasan aman di dalam)
put(B,7,3,8,"minecraft:iron_bars")
for y in (2,3): put(B,7,y,11,AIR)
roof(B,CX,CZ,17,6)
# landasan
put(B,3,2,8,"minecraft:anvil[facing=east]")
save(*B,"kajiya")

# ===== 3. CHAYA (kedai teh elegan, 15x9x13, taman) =====
B=new(15,9,13); CX,CZ=7,6
fill(B,0,0,0,14,0,12,STONE); fill(B,1,1,1,13,1,11,"minecraft:bamboo_planks")
walls(B,1,13,1,11,2,4,WALL,BEAM)
# jendela besar + pintu geser
for x in (3,5,9,11): put(B,x,3,1,"minecraft:bamboo_trapdoor[half=top]")
for y in (2,3): 
    for x in (6,7,8): put(B,x,y,11,AIR)
# engawa (teras kayu keliling)
fill(B,0,1,12,14,1,12,"minecraft:bamboo_planks")
# taman mini: kolam + batu
fill(B,2,1,8,4,1,10,"minecraft:water")
put(B,3,2,9,"minecraft:lily_pad")
for (x,z) in [(11,3),(12,8)]: put(B,x,1,z,"minecraft:mossy_cobblestone")
put(B,11,2,3,"minecraft:lantern[hanging=false]")
roof(B,CX,CZ,17,5)
save(*B,"chaya")

# ===== 4. YAGURA (menara pengawas, 9x22x9) =====
B=new(9,22,9); CX,CZ=4,4
fill(B,0,0,0,8,3,8,SBRICK)  # base batu
fill(B,1,4,1,7,4,7,OAK)
walls(B,1,7,1,7,5,8,WALL,BEAM)
for y in (6,7):
    for x in (2,4,6): put(B,x,y,1,GLASS); put(B,x,y,7,GLASS)
walls(B,2,6,2,6,9,12,WALL,BEAM)
for y in (10,11):
    for x in (3,5): put(B,x,y,2,GLASS); put(B,x,y,6,GLASS)
fill(B,2,13,2,6,13,6,OAK)
roof(B,CX,CZ,11,14)
put(B,4,19,4,"minecraft:lightning_rod[facing=up]")
# tangga dalam
for y in range(4,13): put(B,3,y,3,"minecraft:oak_stairs[facing=east,half=bottom,shape=straight]")
save(*B,"yagura")

# ===== 5. DOJO (aula latihan, 21x10x15) =====
B=new(21,10,15); CX,CZ=10,7
fill(B,0,0,0,20,0,14,STONE); fill(B,1,1,1,19,1,13,"minecraft:spruce_planks")
walls(B,1,19,1,13,2,5,WALL,BEAM)
for x in range(1,20): put(B,x,6,1,BEAMX); put(B,x,6,13,BEAMX)
# pintu ganda besar
for y in (2,3,4):
    for x in (9,10,11): put(B,x,y,13,AIR)
# rak senjata dalam
for x in (3,5,17): put(B,x,2,2,"minecraft:armor_stand")
fill(B,14,2,2,16,2,2,"minecraft:barrel[facing=up]")
# kaligrafi dinding
put(B,10,4,1,"minecraft:oak_sign")
roof(B,CX,CZ,23,7)
save(*B,"dojo")

# ===== 6. KURA (gudang berdinding tebal, 13x11x11) =====
B=new(13,11,11); CX,CZ=6,5
fill(B,0,0,0,12,2,10,PLASTER)  # dinding tebal 3 lapis
fill(B,3,0,3,9,8,7,AIR)  # rongga dalam
fill(B,3,0,3,9,0,7,"minecraft:dark_oak_planks")
# jendela kecil tinggi
for x in (4,8): put(B,x,6,2,"minecraft:iron_bars"); put(B,x,6,8,"minecraft:iron_bars")
# pintu besi
for y in (1,2,3): put(B,6,y,10,"minecraft:iron_door[half=lower,hinge=left,facing=south]")
put(B,6,2,9,"minecraft:stone_button[face=wall,facing=south]")
roof(B,CX,CZ,15,9)
# atap tebal khas kura
fill(B,1,8,1,11,8,9,ROOF)
save(*B,"kura")

# ===== 7. SENTO (pemandian umum, 17x10x15) =====
B=new(17,10,15); CX,CZ=8,7
fill(B,0,0,0,16,0,14,STONE)
# kolam air panas dalam
fill(B,3,1,3,13,1,11,"minecraft:water")
fill(B,3,2,3,3,2,11,SBRICK); fill(B,13,2,3,13,2,11,SBRICK)
# uap (partikel via api unggun tersembunyi)
for (x,z) in [(5,5),(11,9)]: put(B,x,0,z,"minecraft:campfire[lit=true]")
walls(B,1,15,1,13,3,6,WALL,BEAM)
for x in range(1,16): put(B,x,7,1,BEAMX); put(B,x,7,13,BEAMX)
for y in (4,5):
    for x in (7,8,9): put(B,x,y,13,AIR)
# tirai noren
for x in (7,8,9): put(B,x,6,13,"minecraft:red_wool")
roof(B,CX,CZ,19,8)
save(*B,"sento")

# ===== 8. BARAK PENJAGA (15x8x11) =====
B=new(15,8,11); CX,CZ=7,5
fill(B,0,0,0,14,0,10,STONE); fill(B,1,1,1,13,1,9,OAK)
walls(B,1,13,1,9,2,4,"minecraft:mud_bricks",BEAM)
for x in range(1,14): put(B,x,5,1,BEAMX); put(B,x,5,9,BEAMX)
for x in (3,7,11): put(B,x,3,1,GLASS)
for y in (2,3): put(B,7,y,9,AIR)
# tempat tidur
for x in (2,3,11,12): put(B,x,2,3,"minecraft:red_bed[part=head,facing=east]")
roof(B,CX,CZ,17,6)
save(*B,"barak")

print("8 bangunan variasi jadi!")
