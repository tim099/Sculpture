# 階段九（TASK-0496）船殼內部的檢查：作品 vs 清單＋原圖約束（⛔ 不 import draft_interior.py；艙內空氣、外板漆的定義在這裡另外寫一次）
#   python -I check_interior.py [--draft] [--no-ceiling]
#     --draft       量「作品＋草稿」（apply 之前）；不給 ⇒ 量標記 船殼內部:end 那一刻
#     --no-ceiling  反向對照：把內板那幾格當成沒鋪 ⇒「看得到外板漆」那一格要報得出來
import sys, os, glob, json
sys.stdout.reconfigure(encoding='utf-8')
import numpy as np
from scipy import ndimage
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from replay import replay              # noqa: E402

W = 'D:/Unity/Valhalla/Sculpture/works/basecamp-frigate-constitution-01m'
DES = W + '/design'
DRAFT = '--draft' in sys.argv
NOCEIL = '--no-ceiling' in sys.argv
YC = 160
X0, X1, Y0, Y1, NZ = 90, 690, 88, 233, 145
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


plan = json.load(open(DES + '/plan.json', encoding='utf-8'))['interior']
pre = {k: v[0] for k, v in replay(W, mark=plan['world_mark']).items()}
post = {k: v[0] for k, v in (replay(W, draft=True) if DRAFT else replay(W, mark='船殼內部:end')).items()}
print('量的是：%s（%d 格）；階段九之前 %d 格' % ('作品＋草稿' if DRAFT else '標記 船殼內部:end 那一刻', len(post), len(pre)))
check('讀到的「階段九之前」＝ plan 記的格數', len(pre) == plan['world_voxels'], len(pre))

# ── 結果帳 ──
names = ['ceiling', 'limber', 'bands', 'riders', 'hooks', 'cap'] + (['riders_t'] if os.path.exists(DES + '/masks/interior/riders_t.vox.txt') else [])
lists = {n: load_list(DES + '/masks/interior/%s.vox.txt' % n) for n in names}
recolor = load_list(DES + '/masks/interior/recolor.vox.txt')
fill = load_list(DES + '/masks/cavities/after_stage9.vox.txt')
seen = set()
overlap = 0
for n in names:
    overlap += len(seen & set(lists[n]))
    seen |= set(lists[n])
check('%d 份清單互不重疊、都落在階段九之前的空格' % len(names), overlap == 0 and not (seen & set(pre)), {'overlap': overlap, 'on_solid': len(seen & set(pre))})
check('換色只換階段九之前就有的格（keelson 209、apron 173）', all(pre.get(k) in (209, 173) for k in recolor), len(recolor))
check('補空腔只落在空格（不碰清單、不碰原本的格）', not (set(fill) & seen) and not (set(fill) & set(pre)), len(fill))
expect = dict(pre)
for n in names:
    expect.update(lists[n])
expect.update(recolor)
expect.update(fill)
miss = sum(1 for k in expect if k not in post)
extra = sum(1 for k in post if k not in expect)
diffc = sum(1 for k in expect if k in post and post[k] != expect[k])
check('結果帳：應有 %d ／ 實有 %d' % (len(expect), len(post)), miss == extra == diffc == 0, {'缺': miss, '多': extra, '顏色不同': diffc})
if not DRAFT:
    evs = sorted(glob.glob(W + '/events/*/*.json'))
    marks = json.load(open(W + '/marks.json', encoding='utf-8'))['marks']
    b = next(m['event'] for m in marks if m['name'] == '船殼內部' and m['phase'] == 'begin')
    e = next(m['event'] for m in marks if m['name'] == '船殼內部' and m['phase'] == 'end')
    later = [f for f in evs if b < os.path.basename(os.path.dirname(f)) + '/' + os.path.basename(f) <= e]
    ops = [json.load(open(f, encoding='utf-8')).get('op') for f in later]
    check('階段九的事件 ＝ 草稿 apply（v1 一筆＋v1.1 橫向 rider 一筆）', ops in (['workedit'], ['workedit', 'workedit']), ops)

if NOCEIL:
    for k in lists['ceiling']:
        post.pop(k, None)
    print('⚠ 反向對照：內板 %d 格當成沒鋪' % len(lists['ceiling']))

# ── 網格 ──
G = np.zeros((X1 - X0, Y1 - Y0, NZ), np.uint8)
for (x, y, z), c in post.items():
    G[x - X0, y - Y0, z] = c
plank = np.zeros(G.shape, bool)
for f in glob.glob(DES + '/masks/planking/plank_*.vox.txt') + [DES + '/masks/planking/dub.vox.txt']:
    for (x, y, z) in load_list(f):
        if X0 <= x < X1 and Y0 <= y < Y1:
            plank[x - X0, y - Y0, z] = True
# 艙內空氣（這裡的定義）：外板格與塗裝色以內 —— 每個 (x, z) 每一舷，從中線往外走到第一格外板之前的空格；跟 (440,160,60) 6 連通
inner = np.zeros(G.shape, bool)
paint = (plank & (G > 0)) | np.isin(G, (36, 168, 255))
yc = YC - Y0
for side in (1, -1):
    rng = range(yc, Y1 - Y0) if side == 1 else range(yc, -1, -1)
    hit = np.zeros((G.shape[0], NZ), bool)
    this = np.zeros(G.shape, bool)
    for j in rng:
        hit |= paint[:, j, :]
        this[:, j, :] = ~hit
    this &= hit[:, None, :]                 # 那一列這一舷整列都沒碰到外板（船外、舷頂以上）⇒ 不算艙內
    inner |= this
ztop = np.where(paint.any(1), np.arange(NZ)[None, :], -1).max(1)      # 每一欄外板／塗裝的最高格
inner &= np.arange(NZ)[None, None, :] <= ztop[:, None, None]
air = (G == 0) & inner
lab, _ = ndimage.label(air)
ia = lab == lab[440 - X0, 160 - Y0, 60]
vp = json.load(open(DES + '/verify_ports.json', encoding='utf-8'))
portxz = np.zeros((G.shape[0], NZ), bool)
for p in vp['ports']:
    for zz, (xa, xb) in p['x_rows'].items():
        portxz[xa - X0:xb - X0 + 1, int(zz)] = True
faces = 0
where = []
for ax in range(3):
    for k in (1, -1):
        nb = np.roll(paint, k, axis=ax)
        f = ia & nb & ~portxz[:, None, :]
        faces += int(f.sum())
        where += [tuple(int(v) for v in c) for c in np.argwhere(f)[:3]]
check('從艙內看不到外板的漆（不算砲門開口那幾列）', faces == 0 if not NOCEIL else faces > 0,
      '%d 面%s' % (faces, '（反向對照：要 > 0）' if NOCEIL else '') + (' 例 %s' % [(x + X0, y + Y0, z) for x, y, z in where[:3]] if faces else ''))

# ── 砲門透光、結構、鏡像 ──
left = 0
for p in vp['ports']:
    for zz, (xa, xb) in p['x_rows'].items():
        left += int((G[xa - X0:xb - X0 + 1, :, int(zz)] > 0).sum())
check('砲門開口那幾列（兩舷、所有 dy）一格實心都沒有（透光）', left == 0, left)
lab2, n = ndimage.label(G > 0)
check('全船 face-connected 元件 ＝ 1', n == 1, n)
pad = np.pad(G > 0, 1)
lab3, _ = ndimage.label(~pad)
cav = int(((lab3 != lab3[0, 0, 0]) & ~pad).sum())
check('封閉空腔 0 格（內板封出來的縫已補實）', cav == 0, cav)
mir = sum(1 for (x, y, z), c in post.items() if post.get((x, 2 * YC - y, z)) != c)
check('兩舷鏡像（含顏色）', mir == 0, mir)
# ── 原圖約束 ──
dk = plan['decks']


def seg_z(segs, x):
    for a, b, z in segs:
        if (a is None or x >= a) and (b is None or x < b):
            return z
gun = dk['gun']
bad = []
for p in vp['ports']:
    zs = sorted(int(z) for z in p['x_rows'])
    xr = [p['x_rows'][str(z)] for z in zs]
    xc = (min(a for a, b in xr) + max(b for a, b in xr)) // 2
    h = zs[0] - seg_z(gun['segments'], xc)
    sp = seg_z(dk['spar']['segments'], xc)
    clamp_bottom = sp - dk['spar']['plank'] - dk['spar']['beam'] - dk['spar']['clamp']
    if not (6 <= h <= 9) or clamp_bottom <= zs[-1]:
        bad.append((p['n'], h, clamp_bottom, zs[-1]))
check('每個砲門下緣離 gun deck 6–9 格、spar clamp 在砲門上緣之上', not bad, bad)
rid = set(lists['riders'])
D = dk['berth']
inclamp = sum(1 for (x, y, z) in rid if seg_z(D['segments'], x) is not None and
              z >= seg_z(D['segments'], x) - D['plank'] - D['beam'] - D['clamp'])
check('斜肋的頭停在 berth clamp 底下（clamp、橫樑、甲板板那幾列 0 格）', inclamp == 0, inclamp)
print('ALL OK' if ok else 'FAIL')
