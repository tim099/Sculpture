# 階段十八：彈藥庫（艙房地板底下一間）＋火藥桶（引用憲法號 -powder-barrel 當外部模型）
# 設計 plan.json magazine（出處 provenance magazine.*）；做法照 basecamp 憲法號階段三十二（Shipbuilding §8）；現況 nf_state stage16。
#   · 房間 ＝ x0+1..x1−1 每個橫切面裡、z floor+1..ceil 從中線連到的艙內空氣
#   · 地板：floor 那一層（松木 177、每 6 格橡木壓條 136）；地板底下到船殼的空氣全部填實（橡木 136）—— 不留封閉空腔
#   · 兩道橫艙壁（x0、x1）：房間那個切面的空氣（含地板以下到船殼的那段一起填）—— 銅 168、外圈一格橡木框 136；門洞在 x1（往船頭）
#   · 側壁：房間裡貼著船殼的那一格鋪銅 168（到 lining_top）
#   · 桶：格點排（步距 keg_step）、每個桶的模型取樣點都在房間空氣裡、正下方是地板；最多 max_kegs 個
#   · 固定點（組裝件座標，跟子作品同框 ⇒ at ＝ frame_at）：blast ＝ 房間空氣重心最近那一格、door ＝ 門洞地板中線
#   · 最後：組裝件現況＋房間 ⇒ 6 連通 1 塊、封閉空腔 0（框外一圈算外面）才寫檔
# 輸出：masks/magazine/room.vox.txt（子作品座標）、verify_magazine.json
# 用法：python -I -X utf8 -B draft_magazine.py <design 資料夾> <火藥桶清單（-powder-barrel 的 export list）>
import sys, os, json, math, hashlib
import numpy as np
from scipy import ndimage

sys.stdout.reconfigure(encoding='utf-8')
D = os.path.abspath(sys.argv[1])
sys.path.insert(0, D)
from nf_state import state_after, occupancy, NX, NY, NZ

plan = json.load(open(os.path.join(D, 'plan.json'), encoding='utf-8'))
MG = plan['magazine']
W = state_after(D, 'stage16')
occ = occupancy(W)
H = W['hull']
x0, x1 = MG['x']; zf, zc = MG['floor_z'], MG['ceil_z']
COL = MG['colors']
st6 = ndimage.generate_binary_structure(2, 1)

cells = {}


def put(k, c):
    if occ[k]:
        raise ValueError(('撞到現況', k))
    cells[k] = c


# 艙內（v2）：同一個 (x, z) 那一列左右兩邊都有船殼、而且正下方 (x, y, <z) 有船殼 ＝ 船殼碗裡面。
# 🩸 v1 只在 2D 橫切面從中線連空氣：外板在切面上是階梯、只靠斜角相接 ⇒ 艙內空氣從斜角縫漏到船外，
#     地板與地板下的填實跟著長到船殼外（5,587 格裡 3,582 格在船底外，x 98–121、z 0–8）。1 塊／空腔 0／左右對稱 三把尺都量不到。
inside = np.zeros((NX, NY, NZ), bool)
for x in range(x0, x1 + 1):
    hs = H[x] > 0
    for z in range(NZ):
        ys = np.nonzero(hs[:, z])[0]
        if len(ys):
            inside[x, ys.min() + 1:ys.max(), z] = True
    inside[x] &= np.cumsum(hs, axis=1) > 0                 # 正下方有船殼
inside &= ~occ
room = np.zeros((NX, NY, NZ), bool)
below = {}
for x in range(x0, x1 + 1):
    sl = inside[x].copy()                               # y × z 的艙內空氣（v2）
    lab, n = ndimage.label(sl, st6)
    seed = lab[80, zf + 1]
    assert seed > 0, ('中線那格不是空氣', x)
    reg = (lab == seed)
    reg[:, :zf + 1] |= False
    part = np.zeros_like(reg); part[:, zf + 1:zc + 1] = reg[:, zf + 1:zc + 1]
    # 再從中線連一次（只看 floor+1..ceil）
    lab2, _ = ndimage.label(part, st6); part = lab2 == lab2[80, zf + 1]
    if x0 < x < x1:
        room[x] = part
    ys = sorted(set(np.nonzero(part.any(axis=1))[0].tolist()))
    # 地板以下：這些 y 從 floor 往下到船殼的空氣全部填
    for y in ys:
        for z in range(zf, -1, -1):
            if occ[x, y, z] or not inside[x, y, z]:
                break
            below[(x, y, z)] = True
for (x, y, z) in below:
    if x in (x0, x1):
        continue
    put((x, y, z), COL['oak'] if (z < zf or (x - x0) % MG['batten_step'] == 0) else COL['pine'])
# 橫艙壁
door = MG['door']
for x in (x0, x1):
    sl = np.zeros((NY, NZ), bool)
    for (xx, y, z) in below:
        if xx == x:
            sl[y, z] = True
    lab, _ = ndimage.label(inside[x], st6)
    reg = lab == lab[80, zf + 1]
    sl[:, zf + 1:zc + 1] |= reg[:, zf + 1:zc + 1]
    edge = sl & ~ndimage.binary_erosion(sl, st6)
    for y, z in zip(*np.nonzero(sl)):
        if x == x1 and abs(y - 80) <= door['half'] and zf + 1 <= z <= zf + door['height']:
            continue
        put((x, y, z), COL['oak'] if (edge[y, z] or z <= zf) else COL['copper'])
# 側壁銅皮
for x in range(x0 + 1, x1):
    for y in range(NY):
        for z in range(zf + 1, MG['lining_top'] + 1):
            if room[x, y, z] and (occ[x, y - 1, z] or occ[x, y + 1, z]) and (x, y, z) not in cells:
                put((x, y, z), COL['copper'])
                room[x, y, z] = False

# 艙房地板開一個艙口（v1：彈藥庫的後艙壁把船尾那段貨艙 x 66–97 封成 5,604 格的空腔 ⇒ 從艙房下去的 lazarette 艙口）
SC = MG['aft_scuttle']; Mw = W['main']
scuttle = {}
for x in range(SC['x'][0], SC['x'][1] + 1):
    for y in range(SC['y'][0], SC['y'][1] + 1):
        zs = np.nonzero(Mw[x, y, :40])[0]
        for z in zs:
            scuttle[(int(x), int(y), int(z))] = int(Mw[x, y, z])
# 現況＋房間：1 塊、空腔 0
after = occ.copy()
for k in cells:
    after[k] = True
for k in scuttle:
    after[k] = False
lab, n = ndimage.label(after, ndimage.generate_binary_structure(3, 1))
pad = np.pad(~after, 1, constant_values=True)
alab, na = ndimage.label(pad, ndimage.generate_binary_structure(3, 1))
assert n == 1, ('彈藥庫讓組裝件變成', n, '塊')
assert na == 1, ('彈藥庫封出空腔', na - 1, [int((alab == i).sum()) for i in range(2, na + 1)][:5])

# ── 桶 ──
keg = np.loadtxt(sys.argv[2], delimiter=',', dtype=int, comments='#', ndmin=2)[:, :3].astype(float)
kc = (keg[:, None, :] + np.array([[0.5, 0.5, 0.5], [0.1, 0.1, 0.1], [0.9, 0.9, 0.1], [0.1, 0.9, 0.9], [0.9, 0.1, 0.9]])[None]).reshape(-1, 3)
KS = MG['keg_scale']
kp = np.array(MG['keg_pivot'])
bot = keg[keg[:, 2] == keg[:, 2].min()] + [0.5, 0.5, 0.0]
air = room.copy()
kegs = []
xs = np.arange(x0 + 1 + MG['keg_clear'], x1 - MG['keg_clear'], MG['keg_step'])
ys = sorted({80.5 + s * k * MG['keg_step'] for k in range(0, 8) for s in (1, -1)}, key=lambda v: abs(v - 80.5))
taken = np.zeros_like(air)
for xc in xs:
    for yc in ys:
        if len(kegs) >= MG['max_kegs']:
            break
        at = np.array([xc + MG['keg_step'] / 2.0, yc, zf + 1.0])
        P = (kc - kp) * KS + at
        i = np.floor(P).astype(int)
        if not (air[i[:, 0], i[:, 1], i[:, 2]].all() and not taken[i[:, 0], i[:, 1], i[:, 2]].any()):
            continue
        b = np.floor((bot - kp) * KS + at).astype(int)
        b[:, 2] -= 1
        if not np.array([after[tuple(q)] for q in b]).all():
            continue
        taken[i[:, 0], i[:, 1], i[:, 2]] = True
        kegs.append([round(float(v), 3) for v in at])
fa = np.array(MG['frame_at']); fs = np.array(MG['frame_size'])
assert all(inside[k] for k in cells), ('有格在船殼碗外面', sum(1 for k in cells if not inside[k]))
for k in cells:
    assert (fa <= np.array(k)).all() and (np.array(k) < fa + fs).all(), ('框外', k)
rc = np.argwhere(room)
cen = rc.mean(0)
blast = tuple(int(v) for v in rc[np.argmin(((rc - cen) ** 2).sum(1))])
door_pt = (x1, 80, zf + 1)
path = os.path.join(D, 'masks', 'magazine', 'room.vox.txt')
os.makedirs(os.path.dirname(path), exist_ok=True)
txt = '# 夜隼號彈藥庫（draft_magazine.py）子作品座標 x,y,z,color；世界 ＝ ＋frame_at\n' + ''.join(
    '%d,%d,%d,%d\n' % (k[0] - fa[0], k[1] - fa[1], k[2] - fa[2], c) for k, c in sorted(cells.items()))
open(path, 'w', encoding='utf-8', newline='\n').write(txt)
with open(os.path.join(D, 'masks', 'magazine', 'main_scuttle.vox.txt'), 'w', encoding='utf-8', newline='\n') as f:
    f.write('# 艙房地板的 lazarette 艙口（從主甲板子作品刻掉，draft_magazine.py）x,y,z,color —— 世界座標\n')
    for k, c in sorted(scuttle.items()):
        f.write('%d,%d,%d,%d\n' % (k[0], k[1], k[2], c))
v1 = {}
for l in open(os.path.join(D, 'masks', 'magazine', 'room_v1.vox.txt'), encoding='utf-8'):
    if l.startswith('#'):
        continue
    x_, y_, z_, c_ = map(int, l.split(','))
    v1[(x_ + fa[0], y_ + fa[1], z_ + fa[2])] = c_
v1_out = {k: c for k, c in v1.items() if cells.get(k) != c}
v2_in = {k: c for k, c in cells.items() if v1.get(k) != c}
for name, dd in (('room_v1_out', v1_out), ('room_v2_in', v2_in)):
    with open(os.path.join(D, 'masks', 'magazine', name + '.vox.txt'), 'w', encoding='utf-8', newline='\n') as f:
        f.write('# 彈藥庫 %s（draft_magazine.py）子作品座標 x,y,z,color\n' % name)
        for k, c in sorted(dd.items()):
            f.write('%d,%d,%d,%d\n' % (k[0] - fa[0], k[1] - fa[1], k[2] - fa[2], c))
cnt = {}
for c in cells.values():
    cnt[c] = cnt.get(c, 0) + 1
out = {'note': 'draft_magazine.py（階段十八）—— 現況 nf_state stage16',
       'work': MG['work'], 'frame_at': MG['frame_at'], 'frame_size': MG['frame_size'],
       'stamp_order': {'main': [{'name': 'aft_scuttle', 'op': 'carvevox', 'file': 'masks/magazine/main_scuttle.vox.txt', 'at': [0, 0, 0], 'origin_world': [0, 0, 0], 'voxels': len(scuttle)}],
                       'magazine': [{'name': 'room_v1', 'op': 'stampvox', 'file': 'masks/magazine/room_v1.vox.txt', 'at': [0, 0, 0], 'origin_world': MG['frame_at'],
                                     'voxels': len(v1), 'note': 'v1 已落格（凍結，不重產）：2D 切面漏到船外'},
                                    {'name': 'v1_out', 'op': 'carvevox', 'file': 'masks/magazine/room_v1_out.vox.txt', 'at': [0, 0, 0], 'origin_world': MG['frame_at'], 'voxels': len(v1_out)},
                                    ] + ([{'name': 'v2_in', 'op': 'stampvox', 'file': 'masks/magazine/room_v2_in.vox.txt', 'at': [0, 0, 0], 'origin_world': MG['frame_at'], 'voxels': len(v2_in)}] if v2_in else [])},
       'room_v2': {'file': 'masks/magazine/room.vox.txt', 'voxels': len(cells), 'sha256': hashlib.sha256(txt.encode('utf-8')).hexdigest()},
       'link': {'name': '彈藥庫', 'at': MG['frame_at'], 'meta': {'kind': 'magazine', 'powder_lb': 100 * len(kegs)}},
       'anchors': [{'name': 'blast', 'world': list(blast)}, {'name': 'door', 'world': list(door_pt)}],
       'kegs': {'source_work': MG['keg_work'], 'scale': KS, 'pivot': MG['keg_pivot'], 'at_world': kegs, 'meta': {'kind': 'powder', 'powder_lb': 100}},
       'counts': {'scuttle': len(scuttle), 'v1': len(v1), 'v1_out': len(v1_out), 'v2_in': len(v2_in), 'cells': len(cells), 'colors': {str(k): v for k, v in sorted(cnt.items())}, 'room_air': int(room.sum()), 'kegs': len(kegs),
                  'components_after': int(n), 'cavities_after': int(na - 1)}}
for a in out['anchors']:
    a['at'] = [int(v) for v in np.array(a['world']) - fa]
with open(os.path.join(D, 'verify_magazine.json'), 'w', encoding='utf-8', newline='\n') as f:
    json.dump(out, f, ensure_ascii=False, indent=1)
print(json.dumps(out['counts'], ensure_ascii=False), 'blast', blast, 'door', door_pt, 'kegs', kegs)
