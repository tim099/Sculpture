# 階段十三 a：彈藥庫（船尾貨艙裡一間）＋火藥桶（引用憲法號 -powder-barrel 當外部模型）
# 設計 plan.json magazine（出處 provenance magazine.*）；從夜隼號 draft_magazine.py（階段十八 v2）改：
#   · 現況 ＝ 引擎匯出的組裝件格子（exports/stage12/ship_list.txt）；「船殼碗裡面」用設計那一側的船殼標籤（sk_world 'hull'）——
#     先對一次：框裡兩邊的實心格逐格相同（assert），不同就停。
#   · 房間 ＝ x0+1..x1−1 每個橫切面裡、z floor+1..ceil 從中線連到的艙內空氣
#   · 地板：floor 那一層（松木 177、每 6 格橡木壓條 136）；地板以下到船殼的空氣全部填實（橡木 136）—— 不留封閉空腔
#   · 頂板（夜隼號沒有：那間頂著艙房地板）：ceil+1 那一層，x0..x1 那段的艙內空氣全鋪（松木、壓條同地板）
#   · 兩道橫艙壁（x0、x1）：那個切面從船殼到頂板的艙內空氣 —— 銅 168、外圈一格橡木框 136；門洞在 x1（往後桅那邊）
#   · 側壁：房間裡貼著船殼的那一格鋪銅 168（到 lining_top）
#   · 桶：格點排（步距 keg_step）、每個桶的模型取樣點都在房間空氣裡、正下方是地板；最多 max_kegs 個
#   · 固定點（子作品座標 ＝ 世界 − frame_at）：blast ＝ 房間空氣重心最近那一格、door ＝ 門洞地板中線
#   · 最後：組裝件現況＋房間 ⇒ 6 連通 1 塊、封閉空腔 0（框外一圈算外面）才寫檔
# 輸出：masks/magazine/room.vox.txt（子作品座標）、verify_magazine.json。重跑逐位元組相同。
# 用法：python -I -X utf8 -B draft_magazine.py <design 資料夾> <匯出資料夾（ship_list.txt、powder_barrel_list.txt）>
import sys, os, json, hashlib
import numpy as np
from scipy import ndimage

sys.stdout.reconfigure(encoding='utf-8')
D, EX = os.path.abspath(sys.argv[1]), os.path.abspath(sys.argv[2])
sys.path.insert(0, D)
from sk_world import World

plan = json.load(open(os.path.join(D, 'plan.json'), encoding='utf-8'))
MG = plan['magazine']; YC = plan['frame']['YC']
w = World(D, with_yards=False)
NX, NY, NZ = w.lab.shape
a = np.loadtxt(os.path.join(EX, 'ship_list.txt'), delimiter=',', dtype=int, comments='#', ndmin=2)
occ = np.zeros((NX, NY, NZ), bool); occ[tuple(a[:, :3].T)] = True
H = w.lab == w.code('hull')
fa = np.array(MG['frame_at']); fs = np.array(MG['frame_size'])
win = tuple(slice(fa[i], fa[i] + fs[i]) for i in range(3))
assert (occ[win] == (w.lab[win] > 0)).all(), ('框裡引擎與設計的實心格不同', int((occ[win] != (w.lab[win] > 0)).sum()))
x0, x1 = MG['x']; zf, zc = MG['floor_z'], MG['ceil_z']; zr = zc + 1
COL = MG['colors']
st6 = ndimage.generate_binary_structure(2, 1)
cells = {}


def put(k, c):
    if occ[k]:
        raise ValueError(('撞到現況', k))
    cells[k] = c


def plank(x, c_default):
    return COL['oak'] if (x - x0) % MG['batten_step'] == 0 else c_default


# 艙內：同一個 (x, z) 那一列左右兩邊都有船殼、而且正下方有船殼 ＝ 船殼碗裡面（夜隼號 v2）
inside = np.zeros((NX, NY, NZ), bool)
for x in range(x0, x1 + 1):
    hs = H[x]
    for z in range(zr + 2):
        ys = np.nonzero(hs[:, z])[0]
        if len(ys):
            inside[x, ys.min() + 1:ys.max(), z] = True
    inside[x] &= np.cumsum(hs, axis=1) > 0
inside &= ~occ
room = np.zeros((NX, NY, NZ), bool)
below, roof = {}, {}
for x in range(x0, x1 + 1):
    lab, _ = ndimage.label(inside[x], st6)
    seed = lab[YC, zf + 1]
    assert seed > 0, ('中線那格不是空氣', x)
    part = np.zeros((NY, NZ), bool); part[:, zf + 1:zc + 1] = (lab == seed)[:, zf + 1:zc + 1]
    lab2, _ = ndimage.label(part, st6); part = lab2 == lab2[YC, zf + 1]
    if x0 < x < x1:
        room[x] = part
    for y in sorted(set(np.nonzero(part.any(axis=1))[0].tolist())):
        for z in range(zf, -1, -1):
            if occ[x, y, z] or not inside[x, y, z]:
                break
            below[(x, y, z)] = True
    for y in np.nonzero(inside[x, :, zr])[0]:                                # 頂板那一層的艙內空氣（從中線連到的）
        roof[(x, int(y), zr)] = True
for (x, y, z) in below:
    if x in (x0, x1):
        continue
    put((x, y, z), COL['oak'] if z < zf else plank(x, COL['pine']))
for (x, y, z) in roof:
    if x in (x0, x1):
        continue
    put((x, y, z), plank(x, COL['pine']))
# 橫艙壁：船殼到頂板
door = MG['door']
for x in (x0, x1):
    sl = np.zeros((NY, NZ), bool)
    for (xx, y, z) in below:
        if xx == x: sl[y, z] = True
    lab, _ = ndimage.label(inside[x], st6)
    reg = lab == lab[YC, zf + 1]
    sl[:, zf + 1:zr + 1] |= reg[:, zf + 1:zr + 1]
    for (xx, y, z) in roof:
        if xx == x: sl[y, z] = True
    edge = sl & ~ndimage.binary_erosion(sl, st6)
    for y, z in zip(*np.nonzero(sl)):
        if x == x1 and abs(y - YC) <= door['half'] and zf + 1 <= z <= zf + door['height']:
            continue
        put((x, int(y), int(z)), COL['oak'] if (edge[y, z] or z <= zf or z == zr) else COL['copper'])
# 側壁銅皮
for x in range(x0 + 1, x1):
    for y in range(NY):
        for z in range(zf + 1, MG['lining_top'] + 1):
            if room[x, y, z] and (occ[x, y - 1, z] or occ[x, y + 1, z]) and (x, y, z) not in cells:
                put((x, y, z), COL['copper'])
                room[x, y, z] = False
# 現況＋房間：1 塊、空腔 0
after = occ.copy()
for k in cells: after[k] = True
lab3, n = ndimage.label(after, ndimage.generate_binary_structure(3, 1))
pad = np.pad(~after, 1, constant_values=True)
alab, na = ndimage.label(pad, ndimage.generate_binary_structure(3, 1))
assert n == 1, ('彈藥庫讓組裝件變成', n, '塊')
assert na == 1, ('彈藥庫封出空腔', na - 1, sorted([int((alab == i).sum()) for i in range(2, na + 1)])[:5])
# ── 桶 ──
keg = np.loadtxt(os.path.join(EX, 'powder_barrel_list.txt'), delimiter=',', dtype=int, comments='#', ndmin=2)[:, :3].astype(float)
kc = (keg[:, None, :] + np.array([[0.5, 0.5, 0.5], [0.1, 0.1, 0.1], [0.9, 0.9, 0.1], [0.1, 0.9, 0.9], [0.9, 0.1, 0.9]])[None]).reshape(-1, 3)
KS = MG['keg_scale']; kp = np.array(MG['keg_pivot'])
bot = keg[keg[:, 2] == keg[:, 2].min()] + [0.5, 0.5, 0.0]
kegs = []
xs = np.arange(x0 + 1 + MG['keg_clear'], x1 - MG['keg_clear'], MG['keg_step'])[::-1]       # 從門那頭（寬的那頭）排起
ys = sorted({YC + 0.5 + s * k * MG['keg_step'] for k in range(0, 8) for s in (1, -1)}, key=lambda v: abs(v - YC - 0.5))
taken = np.zeros_like(room)
for xc in xs:
    for yc in ys:
        if len(kegs) >= MG['max_kegs']:
            break
        at = np.array([xc + MG['keg_step'] / 2.0, yc, zf + 1.0])
        if x1 - door['height'] < at[0] and abs(yc - YC - 0.5) <= door['half'] + 3:            # 門口那一條留給走道
            continue
        P = (kc - kp) * KS + at
        i = np.floor(P).astype(int)
        if not (room[i[:, 0], i[:, 1], i[:, 2]].all() and not taken[i[:, 0], i[:, 1], i[:, 2]].any()):
            continue
        b = np.floor((bot - kp) * KS + at).astype(int); b[:, 2] -= 1
        if not np.array([after[tuple(q)] for q in b]).all():
            continue
        taken[i[:, 0], i[:, 1], i[:, 2]] = True
        kegs.append([round(float(v), 3) for v in at])
assert all(inside[k] for k in cells), ('有格在船殼碗外面', sum(1 for k in cells if not inside[k]))
for k in cells:
    assert (fa <= np.array(k)).all() and (np.array(k) < fa + fs).all(), ('框外', k)
rc = np.argwhere(room)
cen = rc.mean(0)
blast = tuple(int(v) for v in rc[np.argmin(((rc - cen) ** 2).sum(1))])
door_pt = (x1, YC, zf + 1)
path = os.path.join(D, 'masks', 'magazine', 'room.vox.txt'); os.makedirs(os.path.dirname(path), exist_ok=True)
NL = chr(10)
txt = '# 風暴角號彈藥庫（draft_magazine.py）子作品座標 x,y,z,color；世界 ＝ ＋frame_at' + NL + ''.join(
    '%d,%d,%d,%d' % (k[0] - fa[0], k[1] - fa[1], k[2] - fa[2], c) + NL for k, c in sorted(cells.items()))
open(path, 'w', encoding='utf-8', newline=NL).write(txt)
cnt = {}
for c in cells.values(): cnt[c] = cnt.get(c, 0) + 1
out = {'note': 'draft_magazine.py（階段十三 a）—— 現況 ＝ 引擎匯出 exports/stage12（%d 格）' % len(a),
       'work': MG['work'], 'title': MG['title'], 'frame_at': MG['frame_at'], 'frame_size': MG['frame_size'],
       'stamp_order': {'magazine': [{'name': 'room', 'op': 'stampvox', 'file': 'masks/magazine/room.vox.txt', 'at': [0, 0, 0], 'origin_world': MG['frame_at'],
                                     'voxels': len(cells), 'sha256': hashlib.sha256(txt.encode('utf-8')).hexdigest()}]},
       'link': {'name': '彈藥庫', 'at': MG['frame_at'], 'meta': {'kind': 'magazine', 'pos': 'aft', 'powder_lb': 100 * len(kegs)}},
       'anchors': [{'name': 'blast', 'world': list(blast)}, {'name': 'door', 'world': list(door_pt)}],
       'kegs': {'source_work': MG['keg_work'], 'scale': KS, 'pivot': MG['keg_pivot'], 'at_world': kegs, 'meta': {'kind': 'powder', 'powder_lb': 100}},
       'counts': {'cells': len(cells), 'below_floor': sum(1 for k in below if k[0] not in (x0, x1)), 'roof': sum(1 for k in roof if k[0] not in (x0, x1)),
                  'colors': {str(k): v for k, v in sorted(cnt.items())}, 'room_air': int(room.sum()), 'kegs': len(kegs),
                  'components_after': int(n), 'cavities_after': int(na - 1), 'assembly_expect': len(a) + len(cells)}}
for an in out['anchors']:
    an['at'] = [int(v) for v in np.array(an['world']) - fa]
with open(os.path.join(D, 'verify_magazine.json'), 'w', encoding='utf-8', newline='\n') as f:
    json.dump(out, f, ensure_ascii=False, indent=1, sort_keys=True); f.write('\n')
print(json.dumps(out['counts'], ensure_ascii=False), 'blast', blast, 'door', door_pt)
