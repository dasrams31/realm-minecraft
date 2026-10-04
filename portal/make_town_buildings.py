#!/usr/bin/env python3
"""Generate jokamachi building schematics: samurai house, machiya, temple, gate."""
import nbtlib
from nbtlib import Compound, Int, Short, ByteArray, IntArray, List

AIR="minecraft:air"; WALL="minecraft:white_concrete"; WOOD="minecraft:dark_oak_planks"
BEAM="minecraft:stripped_dark_oak_log[axis=y]"; BEAMX="minecraft:stripped_dark_oak_log[axis=x]"
BEAMZ="minecraft:stripped_dark_oak_log[axis=z]"; ROOF="minecraft:deepslate_tiles"
GLASS="minecraft:white_stained_glass"; FLOOR="minecraft:oak_planks"
STONE="minecraft:cobblestone"; PAPER="minecraft:paper"  # placeholder unused
LANTERN="minecraft:lantern[hanging=false]"; FENCE="minecraft:dark_oak_fence"
TATAMI="minecraft:green_wool"

def new_canvas(w,h,l):
    return {},w,h,l

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
    for z in range(z0+1,z1):
        stairs(B,x0,y,z,"west"); stairs(B,x1,y,z,"east")
    fill(B,x0+1,y,z0+1,x1-1,y,z1-1,ROOF)
    s,yy=size-2,y+1
    while s>=3:
        hh=s//2; fill(B,cx-hh,yy,cz-hh,cx+hh,yy,cz+hh,ROOF); s-=2; yy+=1

# ============ 1. RUMAH SAMURAI (17x10x15) ============
B=new_canvas(17,10,15); blocks,_,_,_=B; CX,CZ=8,7
fill(B,0,0,0,16,0,14,STONE)  # fondasi
fill(B,1,1,1,15,1,13,FLOOR)
# dinding: putih + pilar kayu
for y in range(2,5):
    for x in range(1,16):
        for z in (1,13): put(B,x,y,z,WALL)
    for z in range(2,13):
        for x in (1,15): put(B,x,y,z,WALL)
for y in range(2,5):
    for x in (1,5,8,11,15):
        for z in (1,13): put(B,x,y,z,BEAM)
    for z in (1,13):
        for x in (1,15): put(B,x,y,z,BEAM)
for x in range(1,16): put(B,x,5,1,BEAMX); put(B,x,5,13,BEAMX)
# jendela kertas
for x in (3,6,10,13):
    put(B,x,3,1,GLASS); put(B,x,3,13,GLASS)
# pintu masuk selatan (genkan)
for y in (2,3): put(B,8,y,13,AIR); put(B,7,y,13,AIR)
fill(B,6,1,13,10,1,15,WOOD)  # teras
# sekat dalam + tatami
fill(B,2,1,2,14,1,12,TATAMI)
fill(B,8,2,2,8,4,12,WALL)  # dinding dalam
put(B,8,3,6,"minecraft:dark_oak_door[half=lower,hinge=left,facing=south]")
# atap
roof(B,CX,CZ,19,6)
# tembok keliling + gerbang kecil
fill(B,0,1,0,16,2,0,WALL); fill(B,0,1,14,16,2,14,WALL)
fill(B,0,1,1,0,2,13,WALL); fill(B,16,1,1,16,2,13,WALL)
for y in (1,2): put(B,8,y,14,AIR)
put(B,7,3,14,BEAM); put(B,9,3,14,BEAM); fill(B,7,4,14,9,4,14,WOOD)
save(*B,"samurai_house")

# ============ 2. MACHIYA (ruko pedagang 13x9x11) ============
B=new_canvas(13,9,11); CX,CZ=6,5
fill(B,0,0,0,12,0,10,STONE)
fill(B,0,1,0,12,1,10,WOOD)
# lantai 1: dinding kayu gelap + etalase
for y in range(2,4):
    for x in range(0,13):
        for z in (0,10): put(B,x,y,z,"minecraft:dark_oak_log[axis=y]")
    for z in range(1,10):
        for x in (0,12): put(B,x,y,z,"minecraft:dark_oak_log[axis=y]")
# etalase depan (kaca)
for x in (2,3,5,6,8,9): put(B,x,2,0,GLASS); put(B,x,3,0,GLASS)
for y in (2,3): put(B,4,y,0,AIR)  # pintu
# lantai 2: dinding putih + jendela kecil (mushiko)
for y in range(5,7):
    for x in range(0,13):
        for z in (0,10): put(B,x,y,z,WALL)
    for z in range(1,10):
        for x in (0,12): put(B,x,y,z,WALL)
for x in (2,4,6,8,10): put(B,x,6,0,"minecraft:dark_oak_trapdoor[half=top]")
fill(B,0,4,0,12,4,10,WOOD)  # lantai 2
# atap
roof(B,CX,CZ,15,7)
# noren (kain depan)
for x in (3,4,5): put(B,x,4,0,"minecraft:blue_wool")
save(*B,"machiya")

# ============ 3. KUIL (19x12x19) ============
B=new_canvas(19,12,19); CX,CZ=9,9
fill(B,2,0,2,16,1,16,STONE)  # panggung batu
fill(B,3,2,3,15,2,15,WOOD)
# pilar merah
RED="minecraft:stripped_crimson_stem[axis=y]"
for y in range(3,7):
    for x in (3,6,9,12,15):
        for z in (3,15): put(B,x,y,z,RED)
    for z in (3,15):
        for x in (3,15): put(B,x,y,z,RED)
for x in range(3,16): put(B,x,7,3,"minecraft:stripped_crimson_stem[axis=x]"); put(B,x,7,15,"minecraft:stripped_crimson_stem[axis=x]")
# dinding dalam sebagian
for y in range(3,6):
    for x in range(5,14): put(B,x,y,10,WALL)
# altar
fill(B,7,3,11,11,3,13,"minecraft:gold_block")
put(B,9,4,12,LANTERN)
# atap besar melengkung
roof(B,CX,CZ,21,8)
# tangga
for i in range(3):
    fill(B,8,1-i if 1-i>=0 else 0,16+i,10,1-i if 1-i>=0 else 0,16+i,STONE)
# lentera batu
for (x,z) in [(4,4),(14,4),(4,14),(14,14)]:
    put(B,x,2,z,"minecraft:cobblestone_wall"); put(B,x,3,z,LANTERN)
save(*B,"temple")

# ============ 4. GERBANG KOTA OTEMON (15x12x7) ============
B=new_canvas(15,12,7); CX=7
# dua pilar utama
for y in range(0,8):
    put(B,4,y,3,BEAM); put(B,10,y,3,BEAM)
# balok atas
fill(B,2,8,3,12,9,3,WOOD)
fill(B,1,9,2,13,9,4,WOOD)
# atap
roof(B,CX,3,17,10)
# dinding samping + pintu kecil
fill(B,0,0,0,2,5,6,WALL); fill(B,12,0,0,14,5,6,WALL)
for y in range(0,6):
    for x in (2,12): put(B,x,y,3,BEAM)
# lentera gantung
put(B,6,7,3,"minecraft:lantern[hanging=true]"); put(B,8,7,3,"minecraft:lantern[hanging=true]")
save(*B,"city_gate")
print("semua schematic kota jadi!")
