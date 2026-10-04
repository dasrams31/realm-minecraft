#!/usr/bin/env python3
"""3 landmark prioritas: arena sumo, teater kabuki, istana shogun."""
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

# 1. ARENA SUMO (31x12x31)
B=new(31,12,31)
cx=cz=15
# Lantai
fill(B,0,0,0,30,0,30,"minecraft:dark_oak_planks")
fill(B,0,1,0,30,1,30,"minecraft:oak_planks")
# Dohyo (ring tanah)
for x in range(12,19):
    for z in range(12,19):
        dx,dz = x-15,z-15
        if dx*dx+dz*dz <= 12: put(B,x,2,z,"minecraft:coarse_dirt")
# Atap di atas dohyo (4 pilar)
for (px,pz) in [(12,12),(12,18),(18,12),(18,18)]:
    for y in range(2,8): put(B,px,y,pz,"minecraft:stripped_dark_oak_log[axis=y]")
fill(B,11,8,11,19,8,19,"minecraft:deepslate_tiles")
fill(B,12,9,12,18,9,18,"minecraft:deepslate_tiles")
# Tribun bertingkat
for tier in range(3):
    y0 = 2+tier*2
    r0 = 11-tier
    for x in range(cx-r0,cx+r0+1):
        for z in [cz-r0,cz+r0]:
            put(B,x,y0,z,f"minecraft:oak_stairs[facing={'north' if z<cz else 'south'},half=bottom,shape=straight]")
        for z in range(cz-r0+1,cz+r0):
            for xx in [cx-r0,cx+r0]:
                put(B,xx,y0,z,"minecraft:oak_planks")
# Dinding luar + atap
for y in range(2,6):
    for x in range(0,31):
        for z in (0,30): put(B,x,y,z,"minecraft:white_concrete")
    for z in range(1,30):
        for x in (0,30): put(B,x,y,z,"minecraft:white_concrete")
fill(B,-1,6,-1,31,6,31,"minecraft:deepslate_tiles")
# Pintu masuk
for y in (2,3,4):
    for x in (14,15,16): put(B,x,y,0,AIR); put(B,x,y,30,AIR)
# Lentera
for (lx,lz) in [(7,7),(23,7),(7,23),(23,23)]:
    put(B,lx,2,lz,"minecraft:cobblestone_wall")
    put(B,lx,3,lz,"minecraft:lantern[hanging=false]")
save(*B,"arena_sumo")

# 2. TEATER KABUKI (25x14x19)
B=new(25,14,19)
# Lantai panggung
fill(B,0,0,0,24,0,18,"minecraft:dark_oak_planks")
fill(B,0,1,0,24,1,18,"minecraft:oak_planks")
# Panggung tinggi di belakang
fill(B,2,2,2,22,3,8,"minecraft:spruce_planks")
# Tirai merah
for x in range(4,21):
    put(B,x,4,3,"minecraft:red_wool")
# Dinding
for y in range(2,8):
    for x in range(0,25):
        for z in (0,18): put(B,x,y,z,"minecraft:dark_oak_planks")
    for z in range(1,18):
        for x in (0,24): put(B,x,y,z,"minecraft:dark_oak_planks")
# Kursi penonton bertingkat
for row in range(3):
    z = 12+row*2
    for x in range(3,22):
        put(B,x,2+row,z,f"minecraft:oak_stairs[facing=north,half=bottom,shape=straight]")
# Atap
fill(B,-1,8,-1,25,8,19,"minecraft:deepslate_tiles")
fill(B,0,9,0,24,9,18,"minecraft:deepslate_tiles")
# Pintu + jendela
for y in (2,3):
    for x in (11,12,13): put(B,x,y,18,AIR)
# Lentera warna-warni
for i,lx in enumerate([5,10,15,20]):
    put(B,lx,2,17,"minecraft:cobblestone_wall")
    color = ["red","blue","yellow","green"][i%4]
    put(B,lx,3,17,f"minecraft:{color}_lantern" if False else "minecraft:lantern[hanging=false]")
save(*B,"teater_kabuki")

# 3. ISTANA SHOGUN (41x20x31) - lebih megah dari kastil
B=new(41,20,31)
# Fondasi batu bertingkat
fill(B,0,0,0,40,2,30,"minecraft:stone_bricks")
fill(B,2,3,2,38,3,28,"minecraft:polished_diorite")
# Lantai utama
fill(B,4,4,4,36,4,26,"minecraft:dark_oak_planks")
# Aula utama (tengah)
for y in range(5,11):
    for x in range(14,27):
        for z in (8,22): put(B,x,y,z,"minecraft:white_concrete")
    for z in range(9,22):
        for x in (14,26): put(B,x,y,z,"minecraft:white_concrete")
# Pilar emas
for (px,pz) in [(14,8),(26,8),(14,22),(26,22)]:
    for y in range(5,11): put(B,px,y,pz,"minecraft:gold_block")
# Sayap kiri-kanan
for y in range(5,9):
    for x in range(4,14):
        for z in (10,20): put(B,x,y,z,"minecraft:white_concrete")
    for x in range(27,37):
        for z in (10,20): put(B,x,y,z,"minecraft:white_concrete")
# Atap bertingkat megah
fill(B,2,11,2,38,11,28,"minecraft:deepslate_tiles")
fill(B,6,12,6,34,12,24,"minecraft:deepslate_tiles")
fill(B,10,13,10,30,13,20,"minecraft:deepslate_tiles")
fill(B,14,14,14,26,14,16,"minecraft:deepslate_tiles")
put(B,20,15,15,"minecraft:gold_block")  # puncak emas
# Taman dalam
fill(B,16,4,24,24,4,26,"minecraft:grass_block")
put(B,20,5,25,"minecraft:water")
# Pintu gerbang emas
for y in (5,6,7):
    for x in (19,20,21): put(B,x,y,8,AIR)
# Lentera
for (lx,lz) in [(10,15),(30,15),(20,10),(20,20)]:
    put(B,lx,4,lz,"minecraft:cobblestone_wall")
    put(B,lx,5,lz,"minecraft:lantern[hanging=false]")
save(*B,"istana_shogun")
print("3 landmark jadi!")
