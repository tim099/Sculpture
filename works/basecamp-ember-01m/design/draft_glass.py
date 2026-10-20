# 窗的玻璃（TASK-0753；Tim 2026-10-20「新增一種透明材質標記(玻璃) … 用來做憲法號跟餘燼號的窗戶」）
#   遊戲材質表 glass：半透明＋反光 ⇒ 開著的窗補回一層玻璃，看得到裡面。兩件子作品：
#   ① basecamp-ember-01m-stern-glass（組裝件座標 at=0,0,0）：三層船尾窗（plan.json stern.tiers，船尾砲門不算）——
#      每一欄窗在船尾面往裡 1 格放 1 格玻璃（照憲法號窗格那一層）；船尾面 xf：刻過的層照 masks/stern/openings_carve（那一欄刻掉的最前一格），
#      下層窗（carve=false，本來就開著）照同一列窗框兩邊最近的實心格；上下兩排差 1 格的地方往下一排補 1 格（斜看不露縫）。
#   ② basecamp-ember-01m-gallery-glass（quarter gallery 座標 at=0,0,0）：gallery_open 拿掉的琥珀玻璃（masks/gallery/gallery_carve 裡色 245 的格）照原位放回 ——
#      掛在 quarter gallery 作品自己的關聯底下 ⇒ 左右兩舷（後廊-S、後廊-P mirror y）一起有。
#   兩件的關聯 meta material=glass。玻璃色 245（琥珀；原本 gallery 亮著的窗色，餘燼的主題色）。
# 讀：plan.json、masks/stern/openings_carve.vox.txt、masks/gallery/gallery_carve.vox.txt、組裝件現在的格（export format=list region=85..140,95..225,85..165 ⇒ 第一個參數）
# 寫：masks/glass/stern_glass.vox.txt、masks/glass/gallery_glass.vox.txt（stampvox at=0,0,0）
import json, os, sys

HERE = os.path.dirname(os.path.abspath(__file__))
GLASS, GAL_GLASS, YC = 245, 245, 160
PL = json.load(open(os.path.join(HERE, 'plan.json'), encoding='utf-8'))


def cells(path):
    out = {}
    for ln in open(path, encoding='utf-8'):
        if ln.startswith('#') or not ln.strip():
            continue
        v = [int(t) for t in ln.split(',')]
        out[(v[0], v[1], v[2])] = v[3] if len(v) > 3 else 1
    return out


now = cells(sys.argv[1])
carve = cells(os.path.join(HERE, 'masks', 'stern', 'openings_carve.vox.txt'))
xf = {}
for (x, y, z) in carve:
    xf[(y, z)] = min(xf.get((y, z), 10 ** 9), x)
face = {}                                   # 現況每欄最前（x 最小）的實心格
for (x, y, z) in now:
    if x < PL['stern']['face_x_max']:
        face[(y, z)] = min(face.get((y, z), 10 ** 9), x)
glass, skipped, read = {}, [], []


def put(x, y, z):
    if (x, y, z) in now:
        skipped.append((x, y, z, now[(x, y, z)]))
        return
    glass[(x, y, z)] = GLASS


for tier in PL['stern']['tiers']:
    for w in tier['openings']:
        if '砲門' in w['name']:
            continue
        (d0, d1), (z0, z1) = w['dy'], w['z']
        for sg in ((1, -1) if d0 > 0 else (1,)):
            ys = sorted(YC + sg * dy for dy in range(d0, d1 + 1))
            col = {}
            for z in range(z0, z1 + 1):
                for y in ys:
                    if (y, z) in xf:
                        col[(y, z)] = xf[(y, z)]
                    else:                    # 本來就開著的窗：同一列兩邊窗框最近的實心格
                        fr = [face[(yy, z)] for yy in (ys[0] - 1, ys[0] - 2, ys[-1] + 1, ys[-1] + 2) if (yy, z) in face]
                        if fr:
                            col[(y, z)] = min(fr)
            n0 = len(glass)
            for (y, z), x in sorted(col.items()):
                put(x + 1, y, z)
                if (y, z - 1) in col:
                    for xx in range(x + 2, col[(y, z - 1)] + 2):
                        put(xx, y, z)
            read.append((tier['name'], w['name'], sg, len(glass) - n0))
os.makedirs(os.path.join(HERE, 'masks', 'glass'), exist_ok=True)


def write(name, D, note):
    rows = sorted((k[0], k[1], k[2], c) for k, c in D.items())
    with open(os.path.join(HERE, 'masks', 'glass', name), 'w', encoding='utf-8', newline='') as f:
        f.write('# %s（%d 格，at=0,0,0；TASK-0753）\n' % (note, len(rows)))
        for r in rows:
            f.write('%d,%d,%d,%d\n' % r)
    return len(rows)


n1 = write('stern_glass.vox.txt', glass, '船尾窗的玻璃（組裝件座標）')
gal = {k: GAL_GLASS for k, c in cells(os.path.join(HERE, 'masks', 'gallery', 'gallery_carve.vox.txt')).items() if c == PL['gallery_open']['glass']}
n2 = write('gallery_glass.vox.txt', gal, 'quarter gallery 窗的玻璃（gallery 座標，原本的琥珀玻璃放回）')
for r in read:
    print(r)
print('船尾玻璃 %d 格；跳過（已經有格）%d：%s' % (n1, len(skipped), skipped[:8]))
print('gallery 玻璃 %d 格' % n2)
