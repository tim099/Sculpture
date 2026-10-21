# 定遠號 中甲板（Zwischendeck，裝甲甲板／下甲板 z 60 與主甲板 z 84 之間）的艙房 —— 照 Fig. 14（Die Kriegsschiffbauten 1881–1882，56 個艙室的圖例）簡化。
#   兩件子作品（整船的框、at 0,0,0）：
#     rooms-lower-side：右舷一排（y > 110），關聯兩次（照原樣＋mirror=y）⇒ 兩舷都有（固定點跟著翻）
#     rooms-lower-mid ：中線的艙房與兩舷不對稱的那幾間（艦長套房、餐廳、病房…），關聯一次
#   牆 1 格厚、從甲板面（z 61）到主甲板板底（z 82），只填還空著的艙內空氣（碰到主甲板的橫樑 z 80–82 就讓開）；門 0.8 m 寬、到 z 79。
#   每間一個空艙房（造船規格 §9.2）：固定點 <房名>.min／.max ＝ 只框空氣（z 61..79：橫樑底下）。
# 用法：python -I -X utf8 -B gen_rooms.py <gen_dingyuan 輸出>（讀 own.npy；寫 part_rooms-lower-*.txt、rooms_meta.json）
import sys, os, json
import numpy as np

out = sys.argv[1]
HERE = os.path.dirname(os.path.abspath(__file__))
PLAN = json.load(open(os.path.join(HERE, 'plan.json'), encoding='utf-8'))
C = PLAN['params']['colors']; RP = PLAN['params']['rooms']
own = np.load(os.path.join(out, 'own.npy'))
names = json.load(open(os.path.join(out, 'own_names.json'), encoding='utf-8'))['names']
NX, NY, NZ = own.shape; YC = (NY - 1) // 2
Z0, Z1, ZW = RP['z_floor'], RP['z_top'], RP['z_wall_top']         # 房間 z 61..79、牆到 82
hull = own == names.index('hull') + 1
occ = own > 0
# 艙內：每一 (x, z) 兩舷船殼內面之間
inside = np.zeros(own.shape, bool)
for x in range(NX):
    for z in range(Z0, ZW + 1):
        ys = np.nonzero(hull[x, :, z])[0]
        if len(ys) < 2: continue
        lo, hi = ys[ys <= YC], ys[ys >= YC]
        if len(lo) and len(hi): inside[x, lo.max() + 1:hi.min(), z] = True
free = inside & ~occ
side = np.zeros(own.shape, bool); mid = np.zeros(own.shape, bool)
DOOR_W, DOOR_Z = RP['door_w'], Z1


def wall_x(piece, x, y0, y1, doors=()):
    """橫向牆（x 固定、y0..y1 含兩端）；doors ＝ 門的中心 y（寬 DOOR_W，z 到 DOOR_Z）。"""
    m = np.zeros(own.shape, bool); m[x, y0:y1 + 1, Z0:ZW + 1] = True
    for yc in doors: m[x, yc - DOOR_W // 2:yc - DOOR_W // 2 + DOOR_W, Z0:DOOR_Z + 1] = False
    piece |= m & free


def wall_y(piece, y, x0, x1, doors=()):
    """縱向牆（y 固定、x0..x1 含兩端）；doors ＝ 門的中心 x。"""
    m = np.zeros(own.shape, bool); m[x0:x1 + 1, y, Z0:ZW + 1] = True
    for xc in doors: m[xc - DOOR_W // 2:xc - DOOR_W // 2 + DOOR_W, y, Z0:DOOR_Z + 1] = False
    piece |= m & free


ROOMS = {'side': [], 'mid': []}


def room(which, nm, x0, x1, y0, y1, legend):
    """空艙房：x0..x1、y0..y1 是牆內；y 那一邊碰到船殼的收到「整段都是艙內空氣」為止（框只框空氣）。"""
    blk = lambda a, b, c, d: (free[a:b + 1, c:d + 1, Z0:Z1 + 1] & ~side[a:b + 1, c:d + 1, Z0:Z1 + 1] & ~mid[a:b + 1, c:d + 1, Z0:Z1 + 1]).all()
    if y1 is None:                                                  # 往右舷外收：最大的 y1
        y1 = y0
        while blk(x0, x1, y0, y1 + 1): y1 += 1
    if y0 is None:                                                  # 往左舷外收：最小的 y0
        y0 = y1
        while blk(x0, x1, y0 - 1, y1): y0 -= 1
    assert blk(x0, x1, y0, y1), (nm, x0, x1, y0, y1)
    ROOMS[which].append({'name': nm, 'min': [x0, y0, Z0], 'max': [x1, y1, Z1], 'legend': legend,
                         'size_m': [round((x1 - x0 + 1) * 0.1, 1), round((y1 - y0 + 1) * 0.1, 1), round((Z1 - Z0 + 1) * 0.1, 1)]})


A, F = RP['aft'], RP['fwd']
# ── 艉段：艦長套房（x 39..99）、門廳（x 100..108，橫貫）、兩舷走道外的軍官艙、中線的餐廳與梯子走道 ──
cp, cs = A['corr_p'], A['corr_s']                                  # 走道 y 範圍（左舷、右舷）
yi = cs[1] + 1                                                      # 右舷軍官艙的內牆
xs = A['cabin_walls']                                               # 軍官艙之間的橫牆（含頭尾）
wall_y(side, yi, xs[0], xs[-1], doors=[(xs[k] + xs[k + 1]) // 2 for k in range(len(xs) - 1)])
for k, x in enumerate(xs): wall_x(side, x, yi, NY - 1)
# 中線那一塊（兩舷走道之間 y cp[1]+1 .. cs[0]-1）：牆在 y ＝ cp[1]+1、cs[0]-1
ym0, ym1 = cp[1] + 1, cs[0] - 1
lad0, lad1 = A['ladder_pass']                                       # 橫走道（艉樓梯子落在這裡）
mx = A['mid_walls']                                                 # 中線那一塊的橫牆：[門廳後, 餐廳｜走道, 走道｜配膳室, 配膳室｜士官餐廳, 城堡端]
wall_y(mid, ym0, mx[0], lad0 - 1); wall_y(mid, ym0, lad1 + 1, mx[4], doors=[(mx[3] + mx[4]) // 2])
wall_y(mid, ym1, mx[0], lad0 - 1); wall_y(mid, ym1, lad1 + 1, mx[4], doors=[(lad1 + 2 + mx[3]) // 2])   # 配膳室另開一扇往右舷走道（梯子那條橫走道的門外被艉樓梯子擋住）
wall_x(mid, mx[0], ym0, ym1); wall_x(mid, lad0 - 1, ym0, ym1, doors=[YC]); wall_x(mid, lad1 + 1, ym0, ym1, doors=[YC])
wall_x(mid, mx[3], ym0, ym1); wall_x(mid, mx[4], ym0, ym1)
# 艦長套房
s0, s1 = A['suite_x']                                               # 套房外牆 x（艉端、門廳端）
wall_x(mid, s0, ym0, ym1); wall_x(mid, s1, ym0, ym1, doors=[YC])    # 會客室
wall_y(mid, ym0, s0, s1); wall_y(mid, ym1, s0, s1)
bx = A['suite_split']                                               # 臥室｜浴室、辦公室｜儲藏室 之間的橫牆
for sg in (1, -1):
    y_in = ym1 if sg > 0 else ym0
    ya, yb = (y_in, NY - 1) if sg > 0 else (0, y_in)
    wall_x(mid, s0, ya, yb); wall_x(mid, bx, ya, yb, doors=[y_in + sg * 6]); wall_x(mid, s1, ya, yb, doors=[y_in + sg * 6])
# ── 艏段：兩舷各兩間（右舷一排鏡像）、船頭中線的病房＋藥房 ──
fi = F['inner_y']; fx = F['side_walls']
wall_y(side, fi, fx[0], fx[-1], doors=[(fx[k] + fx[k + 1]) // 2 for k in range(len(fx) - 1)])
for x in fx: wall_x(side, x, fi, NY - 1)
sb = F['sick']; ph = F['pharm']
wall_x(mid, sb['x'][0] - 1, sb['y'][0] - 1, sb['y'][1] + 1, doors=[YC]); wall_x(mid, sb['x'][1] + 1, sb['y'][0] - 1, sb['y'][1] + 1, doors=[YC])
wall_y(mid, sb['y'][0] - 1, sb['x'][0] - 1, sb['x'][1] + 1); wall_y(mid, sb['y'][1] + 1, sb['x'][0] - 1, sb['x'][1] + 1)
wall_x(mid, ph['x'][1] + 1, ph['y'][0] - 1, ph['y'][1] + 1)
wall_y(mid, ph['y'][0] - 1, ph['x'][0] - 1, ph['x'][1] + 1); wall_y(mid, ph['y'][1] + 1, ph['x'][0] - 1, ph['x'][1] + 1)
# 牆只在右舷那一件的 y > 110（鏡像那一份翻過去）
side &= (np.arange(NY) > YC)[None, :, None]
# ── 空艙房 ──
for k in range(len(xs) - 1):
    room('side', '軍官艙-%d' % (k + 1), xs[k] + 1, xs[k + 1] - 1, yi + 1, None, A['cabin_legend'][k])
room('mid', '艦長會客室', s0 + 1, s1 - 1, ym0 + 1, ym1 - 1, '51 Salon des Kommandanten')
room('mid', '艦長臥室', bx + 1, s1 - 1, ym1 + 1, None, '54 Schlafzimmer des Kommandanten')
room('mid', '艦長浴室', s0 + 1, bx - 1, ym1 + 1, None, '53 Badezimmer des Kommandanten')
room('mid', '艦長辦公室', bx + 1, s1 - 1, None, ym0 - 1, '50 Arbeitszimmer des Kommandanten')
room('mid', '儲藏室', s0 + 1, bx - 1, None, ym0 - 1, '55 Spind／56 Instrumentenkammer')
room('mid', '軍官餐廳', mx[0] + 1, lad0 - 2, ym0 + 1, ym1 - 1, '44 Offiziersmesse')
room('mid', '配膳室', lad1 + 2, mx[3] - 1, ym0 + 1, ym1 - 1, '39 Pantry')
room('mid', '士官餐廳', mx[3] + 1, mx[4] - 1, ym0 + 1, ym1 - 1, '43 Deckoffiziersmesse')
for k in range(len(fx) - 1):
    room('side', '艏艙-%d' % (k + 1), fx[k] + 1, fx[k + 1] - 1, fi + 1, None, F['side_legend'][k])
room('mid', '病房', sb['x'][0], sb['x'][1], sb['y'][0], sb['y'][1], '6 Lazareth')
room('mid', '藥房', ph['x'][0], ph['x'][1], ph['y'][0], ph['y'][1], '7 Apotheke')
# ── 輸出 ──
for nm, m in (('rooms-lower-side', side), ('rooms-lower-mid', mid)):
    idx = np.argwhere(m)
    with open(os.path.join(out, 'part_%s.txt' % nm), 'w', newline='\n') as f:
        f.write('# %s —— x,y,z,color（框 %d×%d×%d）\n' % ((nm,) + own.shape))
        f.write('\n'.join('%d,%d,%d,%d' % (a, b, c, C['wall']) for a, b, c in idx.tolist()) + '\n')
json.dump({'rooms': ROOMS, 'cells': {'side': int(side.sum()), 'mid': int(mid.sum())}}, open(os.path.join(out, 'rooms_meta.json'), 'w', encoding='utf-8'), ensure_ascii=False, indent=1)
print(json.dumps({'cells': {'side': int(side.sum()), 'mid': int(mid.sum())}, 'rooms': {k: [(r['name'], r['size_m']) for r in v] for k, v in ROOMS.items()}}, ensure_ascii=False))
