"""Fit the shallow hold and the aft shelter on the galea's 0.1 m grid."""
import json
from pathlib import Path

from apply_rig import entries, ensure_anchor, mask
from apply_upper import ASM, HULL, cli, component, coords, link
from verify_assembly import read

D = Path(__file__).resolve().parent
OUT = D / 'masks' / 'interior'
FULL = (560, 321, 90)
WOOD, PLANK, IRON = 104, 141, 32


def add(parent, suffix, title, cells, size=FULL, meta=None):
    path = OUT / (suffix + '.txt')
    mask(path, cells)
    work = component(suffix, title, path, size)
    if suffix not in entries(parent, 'links'):
        link(parent, suffix, work, meta=meta)
    return work


def box(cells, xs, ys, z, depth, palette=(WOOD, PLANK, IRON)):
    for x in xs:
        for y in ys:
            for h in range(depth):
                frame = x in (xs.start, xs.stop-1) or y in (ys.start, ys.stop-1)
                if frame or h == depth-1:
                    cells[x,y,z+h] = palette[2] if h in (1, depth-2) and frame else palette[int(h==depth-1)]


def apply():
    deck = HULL + '-deck'
    source = read(D/'masks/upper/deck.txt')
    cut = {p:c for p,c in source.items() if 211<=p[0]<=223 and 156<=p[1]<=164 and 17<=p[2]<=20}
    cutfile = OUT/'access-opening.txt'
    mask(cutfile, cut)
    expected = read(D/'masks/hull/hull_01.vox.txt')
    assert not expected.keys() & cut.keys()
    marker = OUT/'access-applied.json'
    if not marker.exists():
        print(cli('carvevox', work=deck, at='0,0,0', voxels=cutfile, expect_pixels=len(cut)), flush=True)
        marker.write_text(json.dumps({'cut':len(cut)},indent=2)+'\n',encoding='utf-8')

    recess = {p:c for p,c in source.items() if 193<=p[0]<=210 and 157<=p[1]<=163 and 17<=p[2]<=18}
    assert not expected.keys() & recess.keys()
    ceiling_file = OUT/'hold-headroom.txt'
    mask(ceiling_file,recess)
    ceiling_done = OUT/'headroom-applied.json'
    if not ceiling_done.exists():
        print(cli('carvevox', work=deck, at='0,0,0', voxels=ceiling_file, expect_pixels=len(recess)), flush=True)
        ceiling_done.write_text(json.dumps({'cut':len(recess)},indent=2)+'\n',encoding='utf-8')

    floor = {(x,y,4):PLANK for x in range(191,247) for y in range(151,170) if (x,y,4) not in expected}
    hold = add(ASM, 'hold-floor', '威尼斯 galea 底艙踏板', floor,
               meta=dict(kind='deck',deck='hold',level=-1,floor='191:5,246:5',thick=1))
    ladder = {}
    for x in range(211,224):
        top = 5 + round((x-211)*15/12)
        for y in range(156,165):
            ladder[x,y,top] = PLANK
            if y in (156,164):
                for z in range(max(5,top-2),top):
                    ladder[x,y,z]=WOOD
    seats = read(D/'masks/upper/benches.txt') | read(D/'masks/upper/rails.txt')
    ladder = {p:c for p,c in ladder.items() if p not in seats}
    ladder_work = add(ASM, 'hold-ladder', '威尼斯 galea 底艙梯', ladder,
                      meta={'kind':'ladders','hold-access.decks':'hold,main'})
    for name, xyz in dict(foot=(210,160,5),lo=(211,160,6),hi=(223,160,21),head=(224,160,21)).items():
        ensure_anchor(ladder_work, 'hold-access.' + name, xyz)

    hold_space = {(x,y,z) for x in range(193,203) for y in range(157,164) for z in range(5,19)}
    assert not hold_space & (expected.keys() | (source.keys()-recess.keys()) | ladder.keys())
    partition = {(192,y,z):WOOD for y in range(151,170) for z in range(5,17)
                 if (192,y,z) not in expected}
    shape = add(hold, 'hold-stores', '威尼斯 galea 底艙物料間', partition, (560,321,30), {'kind':'rooms'})
    for key, p in (('stores.min',(193,157,5)),('stores.max',(202,163,18))):
        actual = entries(shape,'anchors').get(key)
        if actual is not None and tuple(actual['at']) != p:
            cli('work',sub='unanchor',work=shape,name=key)
        ensure_anchor(shape,key,p)

    cover = {(x,y,0):(IRON if x in (0,14) or y==0 else PLANK) for x in range(15) for y in range(11)}
    for x in range(6,9):
        cover[x,8,1]=IRON
    path = OUT/'hold-hatch.txt'
    mask(path,cover)
    hatch = component('hold-hatch','威尼斯 galea 底艙艙蓋',path,(15,11,3))
    ensure_anchor(hatch,'hinge-a',(0,0,0))
    ensure_anchor(hatch,'hinge-b',(14,0,0))
    if 'hold-hatch' not in entries(deck,'models'):
        cli('work',sub='model',work=deck,name='hold-hatch',source_work=hatch,at='210,155,21',
            pivot='0,0,0',meta={'kind':'door','open':'up','open_deg':100})

    aft_deck = read(D/'masks/ends/stern.txt')
    props = {}
    # The table follows the stepped shelter floor; a clear centre route stays aft.
    for x in range(68,80):
        for y in range(151,157):
            support = max(z for z in range(30) if (x,y,z) in aft_deck or (x,y,z) in source)
            if x in (68,79) and y in (151,156):
                for z in range(support+1,30):
                    if (x,y,z) not in aft_deck:
                        props[x,y,z]=WOOD
            for z in (30,31):
                props[x,y,z]=PLANK
    box(props,range(65,73),range(165,170),25,5)
    box(props,range(228,235),range(152,157),5,5)
    box(props,range(236,243),range(165,169),5,5)
    for x,y in ((84,150),(84,170)):
        for dx in range(-2,3):
            for z in range(23,27):
                if abs(dx)<=1 or z==26:
                    props[x+dx,y,z]=WOOD if z<26 else PLANK
    props = {p:c for p,c in props.items() if p not in (expected.keys() | source.keys() | aft_deck.keys())}
    path = OUT/'stores-and-aft-fittings.txt'
    mask(path,props)
    dress = component('interior-fittings','威尼斯 galea 艙內箱具、艉篷桌與繫纜木',path,FULL)
    if 'interior-fittings' not in entries(ASM,'models'):
        cli('work',sub='model',work=ASM,name='interior-fittings',source_work=dress,at='0,0,0',
            pivot='0,0,0',meta={'deco':1})
    print(cli('work',sub='ropecheck',work=ASM),flush=True)

if __name__ == '__main__':
    apply()
