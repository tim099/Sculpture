# 哨兵號的主砲塔改成自己的一座（TASK-0659／0661；Tim 2026-10-17：「哨兵號真的去用新功能造砲塔」「因為我想用真實用在遊戲內的船確認功能ok」）：
#   原船（莫尼特號）的砲塔藏起來（link_hide 加「砲塔」），換一座 -turret（砲塔層 kind=turret，造船規格 §4.8）：
#     圓筒、頂（沿用莫尼特號的 -turret-armor、-turret-roof）＋吊籃地板 -turret-basket（半徑 8–28，中間留洞給住艙甲板上來的艙口梯；會轉的甲板）
#     ＋砲塔裡的備便彈藥箱 -turret-locker（8×7×7、一桶，kind=magazine；Tim 2026-10-17「減成一桶」—— 原本 8×12 兩桶；放在砲尾後面靠圓筒內側，跟砲尾之間留走道 ——
#       ⛔ 先用甲板上那件 14×14 的 -locker ⇒ 剛好擋在兩門砲放藥箱的位置中間，砲-b 那邊走不到取用點）＋兩門 XI 吋（照原本的擺法，固定在砲塔上）
#     ＋頂上正中央疊一座開放的砲房 -turret-top（kind=turret、arc ±180、30°／秒；平台＋前盾＋兩片側翼，跟速射砲的砲房同一型）＋一門三叉戟速射砲。
#   站在吊籃、砲塔頂上的人跟著主砲塔轉；站在頂上砲房平台的人再跟著那一座轉（Tim：「就只有砲塔頂部會是一塊跟著轉的甲板」）。
#   ⛔ 不做通到砲塔頂的梯子：梯子是不轉的船殼，放在會轉的砲塔裡對不上 ⇒ 頂上的砲班開場就站在上面（補人上不去）。
# 用法：python -I -X utf8 apply_turret.py [--dry]
import sys, os, json, math, subprocess, shutil, tempfile
S = shutil.which('senate'); PER = 'meadow'; W = 'meadow-sentinel-01m'
TUR, BASKET, TOP, LOCK = W + '-turret', W + '-turret-basket', W + '-turret-top', W + '-turret-locker'
WORKS = os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', '..')
DRY = '--dry' in sys.argv
IRON_BLACK, IRON, LEAD = 36, 73, 146
AT = (269, 33, 35); SIZE = (65, 65, 43)                                  # 主砲塔的框（跟原船的圓筒同一個原點；z 35–77，頂上砲房到 z 77）
C = (301.5, 65.5)                                                        # 轉軸（原船砲塔的 pivot）
GW = 'gura-tridente-01m-gun-trident'; PIV, SC, TRUN = (16.5, 34, 0), 0.5, (16.5, 30.5, 16.5)


def run(*a, ok_codes=(0,)):
    args = [S, 'cmd', 'sculpture']
    for k, v in a: args += ['--arg', '%s=%s' % (k, v)]
    p = subprocess.run(args, capture_output=True, text=True, encoding='utf-8', errors='replace')
    if p.returncode not in ok_codes: print((p.stdout + p.stderr)[-1500:]); sys.exit(1)
    return p.stdout


def rz(p, deg):
    c, s = math.cos(math.radians(deg)), math.sin(math.radians(deg))
    return (p[0] * c - p[1] * s, p[0] * s + p[1] * c)


def names(wid, fn, key):
    f = os.path.join(WORKS, wid, fn)
    return [x['name'] for x in json.load(open(f, encoding='utf-8'))[key]] if os.path.exists(f) else []


tmp = tempfile.mkdtemp(prefix='sturret_')


def load_list(fn):
    d = {}
    if os.path.exists(fn):
        for l in open(fn, encoding='utf-8'):
            if l[:1].isdigit(): a = l.split(','); d[(int(a[0]), int(a[1]), int(a[2]))] = int(a[3])
    return d


def export(wid, links='all'):
    fn = os.path.join(tmp, wid + '_' + links + '.txt').replace(os.sep, '/')
    a = [('op', 'export'), ('format', 'list'), ('work', wid), ('out', fn)]
    if links != 'all': a.append(('links', links))
    run(*a)
    return load_list(fn)


def ensure(wid, title, size, parent):
    if not os.path.exists(os.path.join(WORKS, wid, 'work.json')):
        run(('op', 'work'), ('sub', 'create'), ('persona', PER), ('id', wid), ('title', title), ('parent_work', parent), ('size', size), ('tags', 'sub'))
    run(('op', 'work'), ('sub', 'update'), ('persona', PER), ('work', wid), ('title', title), ('meters_per_voxel', '0.1'))


def sync(wid, new, size):
    old = export(wid, 'none')
    rm = [k for k, c in old.items() if new.get(k) != c]; add = [k for k, c in new.items() if old.get(k) != c]
    for nm, lst, op, src in (('rm', rm, 'carvevox', old), ('add', add, 'stampvox', new)):
        if op == 'stampvox' and size: run(('op', 'work'), ('sub', 'update'), ('persona', PER), ('work', wid), ('size', size))
        if not lst: continue
        fn = os.path.join(tmp, '%s_%s.txt' % (wid, nm)).replace(os.sep, '/')
        open(fn, 'w').write('\n'.join('%d,%d,%d,%d' % (k[0], k[1], k[2], src[k]) for k in lst) + '\n')
        run(('op', op), ('persona', PER), ('work', wid), ('at', '0,0,0'), ('voxels', fn), ('expect_pixels', str(len(lst))), ('share', '0'))
    print('  %s：刻 %d、補 %d（現在 %d 格）' % (wid, len(rm), len(add), len(new)))


def anchor(wid, nm, at, note):
    f = os.path.join(WORKS, wid, 'anchors.json')
    if os.path.exists(f) and nm in [x['name'] for x in json.load(open(f, encoding='utf-8'))['anchors']]:
        run(('op', 'work'), ('sub', 'unanchor'), ('persona', PER), ('work', wid), ('name', nm))
    run(('op', 'work'), ('sub', 'anchor'), ('persona', PER), ('work', wid), ('name', nm), ('at', '%d,%d,%d' % at), ('note', note))


def link(wid, nm, src, at, meta, extra=()):
    a = [('op', 'work'), ('sub', 'link'), ('persona', PER), ('work', wid), ('name', nm), ('source_work', src), ('at', '%s,%s,%s' % tuple(at)), ('meta', json.dumps(meta, ensure_ascii=False))] + list(extra)
    if nm in names(wid, 'links.json', 'links'): a.append(('overwrite', '1'))
    run(*a); print('  關聯 %s/%s' % (wid, nm))


def model(wid, nm, src, at, pivot, rotate, scale, meta, mirror=''):
    a = [('op', 'work'), ('sub', 'model'), ('persona', PER), ('work', wid), ('name', nm), ('source_work', src), ('at', '%s,%s,%s' % tuple(at)),
         ('pivot', '%s,%s,%s' % tuple(pivot)), ('rotate', '%s,%s,%s' % tuple(rotate)), ('scale', '%s,%s,%s' % tuple(scale)), ('meta', json.dumps(meta, ensure_ascii=False))]
    if mirror: a.append(('mirror', mirror))
    if nm in names(wid, 'models.json', 'models'): a.append(('overwrite', '1'))
    run(*a); print('  模型 %s/%s' % (wid, nm))


# ── 吊籃地板（主砲塔座標，z 0 ＝ 船的 z 35）──
basket = {(x, y, 0): IRON for x in range(65) for y in range(65) if 8 <= math.hypot(x + 0.5 - 32.5, y + 0.5 - 32.5) <= 28}

# ── 砲塔裡的彈藥箱（作品座標，框 8×7×7、箱底 z 0）：鐵殼、鉛灰的蓋、兩個黃銅提把；一桶憲法號火藥桶（Tim 2026-10-17：「減成一桶」）──
BRASS = 180
LX, LY, LZ = 8, 7, 7
lock = {}
for x in range(LX):
    for y in range(LY):
        for z in range(LZ):
            if z == LZ - 1: lock[(x, y, z)] = BRASS if (x in (3, 4) and y in (1, LY - 2)) else LEAD
            elif x in (0, LX - 1) or y in (0, LY - 1) or z == 0: lock[(x, y, z)] = IRON_BLACK
LKEGS = [{'name': '桶-1', 'at': (4, 3.5, 1)}]
LAT = (51, 29, 1)                                                        # 主砲塔座標 ⇒ 船的 x 320–327、y 62–68（兩桶時 y 26 起、59–70），照舊對著中線：離轉軸最遠 26.8 格內（吊籃 28 內）、砲尾後面留 3 格走道

# ── 頂上的砲房（船的座標；照 apply_shields.py 的砲房，轉軸 ＝ 主砲塔的轉軸、前方 −x ＝ 主砲塔的前方）──
ROT = 90                                                                 # 砲模型轉 90° ⇒ 砲口朝 −x
ax = rz((0, 1), ROT); pv = rz((1, 0), ROT)
Z0 = 65                                                                  # 砲塔頂（鐵軌 z 63–64）上面一格
top = {}
for x in range(int(C[0]) - 16, int(C[0]) + 17):
    for y in range(int(C[1]) - 16, int(C[1]) + 17):
        dx, dy = x + 0.5 - C[0], y + 0.5 - C[1]
        u, v = dx * ax[0] + dy * ax[1], dx * pv[0] + dy * pv[1]
        for z in range(Z0, Z0 + 13):
            plate = 8 <= u < 10 and abs(v) < 13.5 and not (abs(v) < 5.5 and Z0 + 7 <= z <= Z0 + 9)   # 砲門：三根砲管 z 73.25
            wing = 12 <= abs(v) < 13.5 and -13 <= u < 8 and Z0 + 1 <= z <= Z0 + 12
            deck = z == Z0 and -13 <= u < 10 and 8.5 <= abs(v) < 13.5
            if plate or wing or deck: top[(x, y, z)] = LEAD if z == Z0 + 12 else IRON_BLACK
tlo = (min(k[0] for k in top), min(k[1] for k in top), min(k[2] for k in top)); thi = (max(k[0] for k in top), max(k[1] for k in top), max(k[2] for k in top))
t = rz(((TRUN[0] - PIV[0]) * SC, (TRUN[1] - PIV[1]) * SC), ROT); gat = (C[0] - t[0], C[1] - t[1], Z0)   # 耳軸落在轉軸上
print('頂上砲房 %d 格、框 %s–%s、離轉軸最遠 %.1f 格；砲 at %s' % (len(top), tlo, thi, max(math.hypot(k[0] + 0.5 - C[0], k[1] + 0.5 - C[1]) for k in top), gat))

# ── 檢查：原船藏起砲塔之後，主砲塔的框裡沒有別的格 ──
LK = {l['name']: l for l in json.load(open(os.path.join(WORKS, W, 'links.json'), encoding='utf-8'))['links']}
hide = LK['原船'].get('hide') or []
if not DRY and '砲塔' not in hide:
    link(W, '原船', 'meadow-monitor-01m-assembly', (0, 0, 0), LK['原船'].get('meta') or {}, (('link_hide', ','.join(hide + ['砲塔'])), ('link_carve', LK['原船'].get('carve') or 'none')))
have = set(export(W))
own = set()
if '砲塔' in LK and LK['砲塔']['work'] == TUR: own = {k for k in have if AT[0] <= k[0] < AT[0] + SIZE[0] and AT[1] <= k[1] < AT[1] + SIZE[1] and AT[2] <= k[2] < AT[2] + SIZE[2]}   # 重跑：框裡的就是這座砲塔
inbox = [k for k in have - own if AT[0] <= k[0] < AT[0] + SIZE[0] and AT[1] <= k[1] < AT[1] + SIZE[1] and AT[2] <= k[2] < AT[2] + SIZE[2]]
print('哨兵號現在 %d 格；主砲塔的框 %s +%s 裡別的格 %d%s' % (len(have), AT, SIZE, len(inbox), '' if DRY or '砲塔' in hide else '（原船的砲塔已藏）'))
if inbox and not ('砲塔' not in hide and DRY): sys.exit('框裡有別的格（例 %s）⇒ 停' % sorted(inbox)[:5])
if DRY: sys.exit(0)

ensure(TUR, '哨兵號 主砲塔（砲塔層：圓筒、頂、吊籃、彈藥箱、兩門 XI 吋、頂上一座砲房）', '%d,%d,%d' % SIZE, W)
ensure(BASKET, '哨兵號 主砲塔的吊籃地板（半徑 8–28、中間留洞給艙口梯）', '65,65,1', W)
ensure(LOCK, '哨兵號 主砲塔裡的備便彈藥箱（一桶）', '%d,%d,%d' % (LX, LY, LZ), W)
sync(LOCK, lock, '%d,%d,%d' % (LX, LY, LZ))
for nm in set(names(LOCK, 'models.json', 'models')) - {k['name'] for k in LKEGS}:   # 減桶：多的那幾個拿掉
    run(('op', 'work'), ('sub', 'unmodel'), ('persona', PER), ('work', LOCK), ('name', nm)); print('  拿掉模型 %s/%s' % (LOCK, nm))
for k in LKEGS: model(LOCK, k['name'], 'basecamp-frigate-constitution-01m-powder-barrel', k['at'], (11, 11, 0), (0, 0, 0), (0.2, 0.2, 0.2), {'kind': 'powder', 'powder_lb': 100})
ensure(TOP, '哨兵號 主砲塔頂上的砲房（小砲塔：平台＋前盾＋兩片側翼）＋三叉戟速射砲', '%d,%d,%d' % (thi[0] - tlo[0] + 1, thi[1] - tlo[1] + 1, thi[2] - tlo[2] + 1), W)
run(('op', 'work'), ('sub', 'update'), ('persona', PER), ('work', TUR), ('size', '%d,%d,%d' % SIZE))
sync(BASKET, basket, '65,65,1')
sync(TOP, {(k[0] - tlo[0], k[1] - tlo[1], k[2] - tlo[2]): c for k, c in top.items()}, '%d,%d,%d' % (thi[0] - tlo[0] + 1, thi[1] - tlo[1] + 1, thi[2] - tlo[2] + 1))
anchor(TUR, 'pivot', (32, 32, 0), '轉軸（格心 32.5,32.5）＝ 原船砲塔的 pivot 301.5,65.5')
anchor(TUR, 'front', (0, 32, 0), '前方：砲口那一邊（開局朝 −x，船尾）')
anchor(TOP, 'pivot', (int(C[0]) - tlo[0], int(C[1]) - tlo[1], 0), '轉軸 ＝ 主砲塔的轉軸、砲的耳軸')
anchor(TOP, 'front', (int(C[0]) - 8 - tlo[0], int(C[1]) - tlo[1], 0), '前方 ＝ 砲口那一邊（開局朝 −x）')
link(TUR, '裝甲', 'meadow-monitor-01m-turret-armor', (0, 0, 0), {'material': 'iron', 'render': 'smooth'})
link(TUR, '頂', 'meadow-monitor-01m-turret-roof', (0, 0, 28), {'material': 'iron'})
link(TUR, '吊籃', BASKET, (0, 0, 0), {'material': 'iron'})
link(TUR, '彈藥箱', LOCK, LAT, {'kind': 'magazine', 'material': 'iron', 'pos': 'mid'})
link(TUR, '頂砲房', TOP, (tlo[0] - AT[0], tlo[1] - AT[1], tlo[2] - AT[2]), {'kind': 'turret', 'arc': '-180,180', 'rate': 30, 'material': 'iron'})
for nm, mir in (('砲-a', ''), ('砲-b', 'x')):
    model(TUR, nm, 'meadow-monitor-01m-turret-gun', (32.5, 32.5, 0), (66.5, 66.5, 0), (0, 0, 90), (0.5, 0.5, 0.5), {'kind': 'gun', 'gun': '11d'}, mir)
model(TOP, '速射砲-頂', GW, (gat[0] - tlo[0], gat[1] - tlo[1], gat[2] - tlo[2]), PIV, (0, 0, ROT), (SC, SC, SC), {'kind': 'gun', 'gun': 'trident', 'barrels': 3, 'deck': 'main', 'side': 'C'})
link(W, '砲塔', TUR, AT, {'kind': 'turret', 'arc': '-180,180', 'fire': '-174,174', 'rate': 16})
print('done')
