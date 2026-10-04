#!/usr/bin/env python3
"""Generator 60 bangunan unik kota shogun - arsitek prosedural.
Setiap bangunan beda: ukuran, atap, warna, fungsi, detail."""
import nbtlib, random
from nbtlib import Compound, Int, Short, ByteArray, IntArray, List

AIR="minecraft:air"
random.seed(20261004)

# Palet material
WALLS = ["minecraft:white_concrete", "minecraft:white_concrete", "minecraft:oak_planks",
         "minecraft:dark_oak_planks", "minecraft:mud_bricks", "minecraft:white_concrete"]
ROOFS = ["minecraft:deepslate_tiles", "minecraft:deepslate_tiles", "minecraft:dark_prismarine",
         "minecraft:cyan_terracotta"]
WOODS = ["minecraft:stripped_dark_oak_log[axis=y]", "minecraft:stripped_oak_log[axis=y]",
         "minecraft:stripped_spruce_log[axis=y]"]
FLOORS = ["minecraft:dark_oak_planks", "minecraft:oak_planks", "minecraft:spruce_planks",
          "minecraft:bamboo_planks"]
GLASS = "minecraft:white_stained_glass"
STONE = "minecraft:cobblestone"

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

def make_building(idx):
    """Bangun satu gedung unik berdasarkan index."""
    # Variasi ukuran
    w = random.choice([9, 11, 13, 15])
    d = random.choice([9, 11, 13])
    h_wall = random.choice([3, 4, 5])
    H = h_wall + 6
    W, L = w+4, d+4  # + ruang atap
    
    wall = random.choice(WALLS)
    roof = random.choice(ROOFS)
    wood = random.choice(WOODS)
    floor = random.choice(FLOORS)
    beamx = wood.replace("[axis=y]","[axis=x]")
    
    B = {}
    def put(x,y,z,b):
        if 0<=x<W and 0<=y<H and 0<=z<L: B[(x,y,z)]=b
    def fill(x1,y1,z1,x2,y2,z2,b):
        for x in range(min(x1,x2),max(x1,x2)+1):
            for y in range(min(y1,y2),max(y1,y2)+1):
                for z in range(min(z1,z2),max(z1,z2)+1): put(x,y,z,b)
    
    cx, cz = W//2, L//2
    hw, hd = w//2, d//2
    x0,x1 = cx-hw, cx+hw
    z0,z1 = cz-hd, cz+hd
    
    # Fondasi + lantai
    fill(x0-1,0,z0-1,x1+1,0,z1+1,STONE)
    fill(x0,1,z0,x1,1,z1,floor)
    
    # Dinding
    for y in range(2,2+h_wall):
        for x in range(x0,x1+1):
            for z in (z0,z1): put(x,y,z,wall)
        for z in range(z0+1,z1):
            for x in (x0,x1): put(x,y,z,wall)
    
    # Pilar sudut
    for y in range(2,2+h_wall):
        for x in (x0,x1):
            for z in (z0,z1): put(x,y,z,wood)
    
    # Balok atas
    for x in range(x0,x1+1): put(x,2+h_wall,z0,beamx); put(x,2+h_wall,z1,beamx)
    
    # Jendela (variasi posisi)
    mid = 2+h_wall//2
    n_win = random.randint(2,4)
    for i in range(n_win):
        wx = x0+2+i*((x1-x0-3)//max(1,n_win-1)) if n_win>1 else cx
        if wx<=x1-1: put(wx,mid,z0,GLASS); put(wx,mid,z1,GLASS)
    
    # Pintu (variasi sisi)
    door_side = random.choice(['south','north','east','west'])
    dw = random.randint(1,2)  # lebar pintu
    if door_side=='south':
        for dx in range(dw):
            for y in (2,3): put(cx+dx,y,z1,AIR)
    elif door_side=='north':
        for dx in range(dw):
            for y in (2,3): put(cx+dx,y,z0,AIR)
    
    # Atap (variasi model)
    roof_y = 2+h_wall+1
    roof_style = random.choice(['hip','gable','flat'])
    if roof_style=='hip':
        # Atap limasan
        for y in range(roof_y, roof_y+4):
            inset = y-roof_y
            fill(x0-1-inset//2,y,z0-1-inset//2,x1+1+inset//2,y,z1+1+inset//2,roof) if inset<2 else None
            if inset>=2: break
        # Sederhanakan: atap bertingkat
        fill(x0-2,roof_y,z0-2,x1+2,roof_y,z1+2,roof)
        fill(x0-1,roof_y+1,z0-1,x1+1,roof_y+1,z1+1,roof)
        fill(x0,roof_y+2,z0,x1,roof_y+2,z1,roof)
    elif roof_style=='gable':
        # Atap pelana
        fill(x0-2,roof_y,z0-2,x1+2,roof_y,z1+2,roof)
        for i in range(1,4):
            fill(x0-2+i,roof_y+i,z0-2,x1+2-i,roof_y+i,z1+2,roof)
    else:
        # Atap datar + pagar
        fill(x0-1,roof_y,z0-1,x1+1,roof_y,z1+1,roof)
        for x in range(x0-1,x1+2):
            put(x,roof_y+1,z0-1,STONE); put(x,roof_y+1,z1+1,STONE)
    
    # Detail interior (variasi fungsi)
    func = idx % 6
    if func==0:  # rumah: tempat tidur + meja
        put(x0+1,2,z0+1,"minecraft:red_bed[part=head,facing=east]")
        put(x0+2,2,z0+1,"minecraft:crafting_table")
    elif func==1:  # toko: rak + counter
        fill(x0+1,2,z0+1,x0+3,3,z0+1,"minecraft:barrel[facing=up]")
        put(cx,2,cz,"minecraft:oak_planks")
    elif func==2:  # workshop: furnace + anvil
        put(x0+1,2,z0+1,"minecraft:furnace[facing=east]")
        put(x1-1,2,z1-1,"minecraft:anvil[facing=north]")
    elif func==3:  # gudang: peti
        for dx in range(3):
            put(x0+1+dx,2,z0+1,"minecraft:chest[facing=south,type=single]")
    elif func==4:  # kuil kecil: altar
        put(cx,2,cz,"minecraft:gold_block")
        put(cx,3,cz,"minecraft:lantern[hanging=false]")
    else:  # kedai: meja + kursi
        put(cx,2,cz,"minecraft:oak_planks")
        for (dx,dz) in [(-1,0),(1,0),(0,-1),(0,1)]:
            put(cx+dx,2,cz+dz,"minecraft:oak_stairs[facing=north,half=bottom,shape=straight]")
    
    # Lentera depan (variasi)
    if random.random()<0.7:
        put(x0-1,2,z1+1,"minecraft:cobblestone_wall")
        put(x0-1,3,z1+1,"minecraft:lantern[hanging=false]")
    
    name = f"metro2_{idx:02d}"
    save(B,W,H,L,name)
    return name, W, L

print("Generate 60 bangunan unik...", flush=True)
names = []
for i in range(100):
    name,W,L = make_building(i)
    names.append((name,W,L))
    if (i+1)%15==0: print(f"{i+1}/100", flush=True)
print("100 schematic unik jadi!", flush=True)
# Simpan daftar untuk paste
with open("/tmp/metro2_list.txt","w") as f:
    for n,w,l in names: f.write(f"{n} {w} {l}\n")
