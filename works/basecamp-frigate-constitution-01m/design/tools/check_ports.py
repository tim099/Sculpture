# 階段八（TASK-0490）雕完的檢查：砲門 vs 作品（events 重播；⛔ 不讀產圖程式的中間結果，只讀它寫出的盒子／清單與原圖讀數）
#   python -I check_ports.py [位移格數]   位移 ≠ 0 ⇒ 反向對照：把讀數往 +X 推那麼多格，開口對讀數那一格要報得出來
import sys, os, glob, json
sys.stdout.reconfigure(encoding='utf-8')
import numpy as np
from scipy import ndimage
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from replay import replay              # noqa: E402

W = 'D:/Unity/Valhalla/Sculpture/works/basecamp-frigate-constitution-01m'
DES = W + '/design'
NOLINE = '--no-lining' in sys.argv          # 反向對照：把砲門框那幾格當成沒貼 ⇒ 砲門框那一格要報得出縫
ARGS = [a for a in sys.argv[1:] if not a.startswith('--')]
SHIFT = float(ARGS[0]) if ARGS else 0.0
YC = 160
plan = json.load(open(DES + '/plan.json', encoding='utf-8'))['gunports']
FIRST = plan['world_upto']
boxes = json.load(open(DES + '/masks/ports/carve_boxes.json', encoding='utf-8'))['boxes']
src = json.load(open(DES + '/source_ports.json', encoding='utf-8'))
ok = True


def check(name, cond, detail=''):
    global ok
    ok &= bool(cond)
    print(('✓ ' if cond else '✗ ') + name + ('  ' + str(detail) if detail != '' else ''))


def load_list(f):
    out = {}
    for line in open(f, encoding='utf-8'):
        if line.strip() and not line.startswith('#'):
            x, y, z, c = (int(v) for v in line.split(','))
            out[(x, y, z)] = c
    return out


pre = {k: v[0] for k, v in replay(W, upto=FIRST).items()}
post = {k: v[0] for k, v in replay(W).items()}
lining = load_list(DES + '/masks/ports/lining.vox.txt')
if NOLINE:
    post = {k: v for k, v in post.items() if k not in lining}

# ── 結果帳 ──
paint = load_list(DES + '/masks/ports/touchup_paint.vox.txt')     # v1.1 細修：白帶補漆（overwrite）
fill = load_list(DES + '/masks/ports/touchup_fill.vox.txt')       # v1.1 細修：船頭砲門後壁的縫＋兩個單格空腔
cut = set()
for b in boxes:
    for x in range(b['x1'], b['x2'] + 1):
        for y in range(b['y1'], b['y2'] + 1):
            for z in range(b['z1'], b['z2'] + 1):
                if (x, y, z) in pre:
                    cut.add((x, y, z))
expect = {k: v for k, v in pre.items() if k not in cut}
expect.update(lining)
expect.update(fill)
check('白帶補漆只蓋在黑外板上（細修前是 36）', all(expect.get(k) == 36 for k in paint), sum(1 for k in paint if expect.get(k) != 36))
expect.update(paint)
miss = sum(1 for k in expect if k not in post)
extra = sum(1 for k in post if k not in expect)
diffc = sum(1 for k in expect if k in post and post[k] != expect[k])
check('結果帳：應有 %d ／ 實有 %d' % (len(expect), len(post)), miss == extra == diffc == 0, {'缺': miss, '多': extra, '顏色不同': diffc})
evs = sorted(glob.glob(W + '/events/*/*.json'))
later = [f for f in evs if os.path.basename(os.path.dirname(f)) + '/' + os.path.basename(f) >= FIRST]
ops = [json.load(open(f, encoding='utf-8')).get('op') for f in later]
check('階段八的事件 ＝ %d 刀 carve ＋ 1 刀 stampvox（lining）＋ 2 刀細修' % len(boxes), ops == ['carve'] * len(boxes) + ['stampvox'] * 3, '%d 個事件' % len(later))
check('lining 只落在空格（階段八前也是空的）', all(k not in pre for k in lining) and all(k not in cut for k in lining))

# ── 刻掉的是誰 ──
lab = {}
for f in glob.glob(DES + '/masks/ends/*.vox.txt'):
    n = os.path.basename(f)[:-8]
    for k in load_list(f):
        lab[k] = n
for f in glob.glob(DES + '/masks/planking/*.vox.txt'):
    n = 'paint_struct' if 'paint_struct' in f else 'plank'
    for k in load_list(f):
        lab[k] = n
kinds = {}
for k in cut:
    n = lab.get(k) or ('frame' if pre[k] == 141 else 'structure')
    if n.startswith('B-cant') or n.startswith('S-cant'):
        n = 'cant'
    kinds[n] = kinds.get(n, 0) + 1
check('刻掉的只有外板／方肋／cant', set(kinds) <= {'plank', 'frame', 'cant'}, kinds)

# ── 開口 vs 原圖讀數（右舷外板層：階段八前是外板、現在空了的格）──
holes = {}
for k in cut:
    if lab.get(k) == 'plank' and k[1] > YC:
        holes.setdefault(k[0] // 1, set()).add(k)
ports = []
for p in src['ports_gun_deck']:
    cells = [k for k in cut if lab.get(k) == 'plank' and k[1] > YC and p['X_aft'] - 3 <= k[0] + 0.5 <= p['X_fwd'] + 3]
    xs = [k[0] for k in cells]
    zs = [k[2] for k in cells]
    if not cells:
        ports.append((p['n'], None))
        continue
    xa, xb = min(xs), max(xs)
    za, zb = min(zs), max(zs)
    dev = max(abs(xa - (p['X_aft'] + SHIFT)), abs(xb + 1 - (p['X_fwd'] + SHIFT)), abs(za - p['sill']), abs(zb + 1 - p['lintel']))
    ports.append((p['n'], round(dev, 2)))
worst = max(d for _, d in ports if d is not None)
check('14 個方砲門的開口邊 vs 讀數框（最大偏差 %.2f 格%s）' % (worst, '，讀數故意 +X 偏 %g' % SHIFT if SHIFT else ''),
      (worst <= 1.0) if SHIFT == 0 else (abs(worst - SHIFT) <= 1.0), ports)

# ── 透光、砲門框、結構 ──
mk = np.array(list(post.keys()))
mn = mk.min(0)
A = np.zeros(mk.max(0) - mn + 1, bool)
A[tuple((mk - mn).T)] = True
lab3, n = ndimage.label(A)
check('全船 face-connected 元件 ＝ 1', n == 1, n)
# 透光：每個開口的 (x, z) 從中線一路到外面（兩舷、所有 dy）都沒有實心的格 ——
# ⚠ 不能只看「刻掉的格現在是空的」（那是結果帳的套套邏輯，永遠綠）；要看開口範圍裡**還剩下**什麼
vp = json.load(open(DES + '/verify_ports.json', encoding='utf-8'))
left = []
for p in vp['ports']:
    for zs, (xa, xb) in p['x_rows'].items():
        z = int(zs)
        for x in range(xa, xb + 1):
            for y in range(0, 320):
                if (x, y, z) in post:
                    left.append((p['n'], x, y, z, post[(x, y, z)]))
check('開口範圍裡（兩舷、所有 dy）沒有剩下任何實心的格（透光）', not left, left[:6])
# 反向對照：同一把尺掃開口上緣再往上一列（lintel＋白帶）⇒ 一定要掃到實心的格
p8 = vp['ports'][7]
ztop = max(int(z) for z in p8['x_rows'])
xa, xb = p8['x_rows'][str(ztop)]
above = sum(1 for x in range(xa, xb + 1) for y in range(0, 320) if (x, y, ztop + 1) in post)
check('反向對照：第 8 個砲門上緣再往上一列 ⇒ 掃得到實心的格（lintel＋外板）', above > 0, above)
# 砲門框：開口四面（左右 x−1／x+1、上下 z−1／z+1）在肋骨那一層（hb − m(z) ≤ dy < hb）還有沒有空格（從砲門往裡看得到的縫）
sys.path.insert(0, DES)
import draft_frames as DF               # noqa: E402
import draft_planking as DP             # noqa: E402
M = DP.Model(DES)
M.lines()
M.hull()
m_of = DF.moulded_fn(json.load(open(DES + '/plan.json', encoding='utf-8'))['framing'])
gaps, faces = [], 0
for p in vp['ports']:
    rows = {int(z): v for z, v in p['x_rows'].items()}
    zs = sorted(rows)
    ring = set()
    for z in zs:
        ring.add((rows[z][0] - 1, z))
        ring.add((rows[z][1] + 1, z))
    for z, zz in ((zs[0] - 1, zs[0]), (zs[-1] + 1, zs[-1])):
        for x in range(rows[zz][0] - 1, rows[zz][1] + 2):
            ring.add((x, z))
    for (x, z) in ring:
        h = float(M.H[x - DP.X0, z])
        m = float(m_of(z + 0.5))
        for d in range(int(np.floor(h - m)), int(np.ceil(h))):
            if not (h - m <= d < h):
                continue
            for side in (1, -1):
                faces += 1
                if (x, YC + side * d, z) not in post:
                    gaps.append((p['n'], x, YC + side * d, z))
check('砲門框：開口四面在肋骨那一層沒有空格（%d 格面）' % faces, not gaps, gaps[:6])
# 白帶：每個砲門上緣上一列、下緣下一列，開口範圍裡最外面那格外板是白（verifier 量到第 4 個上面整排是黑）
plank_cells = set()
for f in glob.glob(DES + '/masks/planking/plank_*.vox.txt') + [DES + '/masks/planking/dub.vox.txt']:
    plank_cells |= set(load_list(f))
nowhite = []
for p in vp['ports']:
    rows = {int(z): v for z, v in p['x_rows'].items()}
    zs = sorted(rows)
    for z, zr in ((zs[-1] + 1, zs[-1]), (zs[0] - 1, zs[0])):
        for x in range(rows[zr][0], rows[zr][1] + 1):
            for side in (1, -1):
                outer = next(((x, YC + side * d, z) for d in range(80, -1, -1) if (x, YC + side * d, z) in plank_cells and (x, YC + side * d, z) in post), None)
                if outer is None or post[outer] != 255:
                    nowhite.append((p['n'], x, z, side, post.get(outer) if outer else None))
check('白帶：每個砲門上下各一列白（開口範圍裡最外面那格外板）', not nowhite, nowhite[:6])
# 封閉空腔：階段八前後各數一次（6 連通、跟外面不通的空氣）—— 階段八不應新增
def cavities(vox):
    k = np.array(list(vox.keys()))
    lo = k.min(0) - 1
    A = np.zeros(k.max(0) - lo + 2, bool)
    A[tuple((k - lo).T)] = True
    lab, n = ndimage.label(~A)
    outside = lab[0, 0, 0]
    inner = (lab != outside) & ~A
    ids = set(np.unique(lab[inner]).tolist())
    cells = {tuple(int(v) for v in c + lo) for c in np.argwhere(inner)}
    return len(ids), cells
npre, cpre = cavities(pre)
npost, cpost = cavities(post)
newc = sorted(cpost - cpre)
check('階段八沒有新增封閉空腔（前 %d 個／%d 格 → 後 %d 個／%d 格）' % (npre, len(cpre), npost, len(cpost)), not newc, newc[:6])
asym = sum(1 for (x, y, z) in cut if (x, 2 * YC - y, z) not in cut) + sum(1 for (x, y, z) in lining if (x, 2 * YC - y, z) not in lining)     + sum(1 for (x, y, z) in paint if (x, 2 * YC - y, z) not in paint) + sum(1 for (x, y, z) in fill if (x, 2 * YC - y, z) not in fill)
check('兩舷鏡像（刻掉的格＋砲門框）', asym == 0, asym)
print('ALL OK' if ok else 'FAIL')
