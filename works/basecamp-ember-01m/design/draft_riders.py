# 餘燼號 船艙底斜肋重畫（todo 可選項；notes 階段五：「船艙底的斜肋被複製成兩段斷開的斜線（鋸齒）」）
#   憲法號斜肋（masks/interior/riders.vox.txt，live oak 104、12 根 ＝ 6 對）。船身拉長時是「一欄一欄」搬格子：
#   x < 439 不動、x 439..471 複製成三份（＋0／＋33／＋66）、x ≥ 472 ＋66 ⇒ 跨過那一段的斜肋被剪開、重複三次。
#   ⇒ 整根斜肋照它的頭（berth clamp 底下那一端）搬：頭 < 439 的整根不動、頭 ≥ 472 的整根 ＋66（頭不准落在 439..471）。
#   ＋66 是 33 的倍數 ⇒ 憲法號 x 439..471 那幾欄在餘燼號 x＋66 是同一份船殼剖面；x < 439 的那截搬到 490..504，是拉長段的第二份（剖面相同的船中）。
#   現在船殼上的斜肋格 O ＝ 照「一欄一欄」搬出來的；新的 N ＝ 照「整根」搬。
#   O − N：拿掉 —— 照憲法號 limber 的規則（|dy| 6..12、正下方是內板）那一格該是 limber ⇒ 換回 limber，否則刻成空氣。
#   N − O：組裝件現況是空氣 ⇒ 落；是船殼的 limber ⇒ 換成斜肋（憲法號的 limber 本來就讓開斜肋）；其他 ⇒ 停。
#   ⇒ masks/riders/{carve,stamp,over_rider,refill_limber}.vox.txt（世界座標、at 0,0,0）、verify_riders.json
# 用法：python -I draft_riders.py <design 資料夾>
import sys, os, json, hashlib
import numpy as np
from scipy import ndimage

D = os.path.abspath(sys.argv[1])
sys.path.insert(0, D)
from draft_ladders import export_hidden  # noqa: E402

sys.stdout.reconfigure(encoding='utf-8')
P = json.load(open(os.path.join(D, 'plan.json'), encoding='utf-8'))['riders_fix']
src = np.loadtxt(P['source_mask'], delimiter=',', comments='#', dtype=np.int32, ndmin=2, encoding='utf-8')
assert len(src) == P['source_cells'], ('憲法號斜肋清單對不上', len(src))
C = int(src[0, 3])
assert (src[:, 3] == C).all()
A0, A1, SH = P['stretch']['copy_x']
SH = P['stretch']['shift']


def per_x(x):
    """拉長時那一欄搬到哪幾欄（一欄一欄搬）"""
    if x < A0:
        return [x]
    if x <= A1:
        n = A1 - A0 + 1
        return [x, x + n, x + 2 * n]
    return [x + SH]


mn = src[:, :3].min(0)
G = np.zeros(src[:, :3].max(0) - mn + 1, bool)
G[tuple((src[:, :3] - mn).T)] = True
lab, n = ndimage.label(G, np.ones((3, 3, 3)))
assert n == P['riders'], ('斜肋根數', n)
O, N, rows = set(), set(), []
for k in range(1, n + 1):
    c = np.argwhere(lab == k) + mn
    head = c[c[:, 2] == c[:, 2].max()]
    xh = float(head[:, 0].mean())
    assert not (A0 <= xh <= A1 + 0.5), ('斜肋頭落在複製段', xh)
    dx = 0 if xh < A0 else SH
    for x, y, z in c.tolist():
        for xx in per_x(x):
            O.add((xx, y, z))
        N.add((x + dx, y, z))
    rows.append({'rider': k, 'cells': int(len(c)), 'x': [int(c[:, 0].min()), int(c[:, 0].max())], 'head_x': round(xh, 1), 'dx': dx,
                 'crosses_copy': bool(c[:, 0].min() <= A1 and c[:, 0].max() >= A0)})

def export_mark(work, mark):
    import subprocess, tempfile
    with tempfile.TemporaryDirectory() as d:
        out = os.path.join(d, 'w.txt').replace('\\', '/')
        r = subprocess.run(['senate', 'cmd', 'sculpture', '--arg', 'op=export', '--arg', 'format=list', '--arg', 'work=' + work,
                            '--arg', 'mark=' + mark, '--arg', 'out=' + out], capture_output=True, text=True, encoding='utf-8', errors='replace')
        if r.returncode or not os.path.exists(out):
            return None
        return np.loadtxt(out, delimiter=',', comments='#', dtype=np.int32, ndmin=2, encoding='utf-8')


# 重跑要讀「這一階段之前」：船殼有 `斜肋:begin` 就讀那一刻；組裝件 ＝ 現況 − 船殼現況 ＋ 船殼那一刻（關聯兩兩不重疊、船殼 at 0,0,0）
asm = export_hidden(P['assembly'], [])
hull_now = export_hidden(P['hull'], [])
hull = export_mark(P['hull'], P['mark'] + ':begin')
if hull is None:
    hull = hull_now
H = {(int(x), int(y), int(z)): int(c) for x, y, z, c in hull}
S = ({(int(x), int(y), int(z)) for x, y, z, c in asm} - {(int(x), int(y), int(z)) for x, y, z, c in hull_now}) | set(H)
assert len(S) == P['assembly_voxels'], ('組裝件（這一階段之前）對不上', len(S))
LB = P['limber']                                                   # 憲法號 limber：底肋頂上那層內板再往上一格、|dy| 在範圍內；斜肋蓋過它


def limber_slot(p):
    """這一格（斜肋拿掉之後）照憲法號的規則該不該是 limber：|dy| 在範圍內、正下方是內板色"""
    x, y, z = p
    return LB['dy'][0] <= abs(y - 160) <= LB['dy'][1] and H.get((x, y, z - 1)) == LB['below_color']


gone = sorted(O - N)
new = sorted(N - O)
# 拿掉的：船殼上那一格現在要是斜肋色（不是 ⇒ 它不是我們以為的那一格，停）；limber 的位置補回 limber，其他刻成空氣
bad_gone = [p for p in gone if H.get(p) != C]
refill = [p for p in gone if limber_slot(p)]
carve = [p for p in gone if not limber_slot(p)]
# 新的：組裝件現況那一格是空氣 ⇒ 落；是船殼的 limber ⇒ 換成斜肋（憲法號同：斜肋蓋過 limber）；其他 ⇒ 停
stamp = [p for p in new if p not in S]
over = [p for p in new if p in S and H.get(p) == LB['color'] and LB['dy'][0] <= abs(p[1] - 160) <= LB['dy'][1]]
bad_new = [p for p in new if p in S and p not in set(over)]
miss_O = [p for p in O & N if H.get(p) != C]                     # 本來就對的那些格，船殼上要真的是斜肋
assert not bad_gone, ('要拿掉的格不是斜肋色', len(bad_gone), bad_gone[:5])
assert not bad_new, ('要落的格不是空氣也不是 limber', len(bad_new), bad_new[:5])
assert not miss_O, ('該在的斜肋格不在', len(miss_O), miss_O[:5])
# 浮空：新的斜肋格每一格要 6 連通到「船殼現況 − 刻掉的 ＋ 落的」的主體
after = (set(H) - set(carve)) | set(stamp)
box_lo = np.array([min(p[i] for p in N) for i in range(3)]) - 2
box_hi = np.array([max(p[i] for p in N) for i in range(3)]) + 2
sub = np.zeros(box_hi - box_lo + 1, bool)
for p in after:
    q = np.array(p) - box_lo
    if (q >= 0).all() and (q <= box_hi - box_lo).all():
        sub[tuple(q)] = True
lab2, n2 = ndimage.label(sub)
big = np.bincount(lab2.ravel())[1:].argmax() + 1
float_cells = sum(1 for p in stamp if lab2[tuple(np.array(p) - box_lo)] != big)
# 鏡像（y ↔ 320 − y）
mirror = sum(1 for (x, y, z) in N if (x, 320 - y, z) not in N)

os.makedirs(os.path.join(D, 'masks', 'riders'), exist_ok=True)
out = {}
for name, cells, col in (('carve', carve, C), ('stamp', stamp, C), ('over_rider', over, C), ('refill_limber', refill, LB['color'])):
    p = os.path.join(D, 'masks', 'riders', name + '.vox.txt')
    txt = ''.join('%d,%d,%d,%d\n' % (x, y, z, col) for x, y, z in cells)
    open(p, 'w', encoding='utf-8', newline='\n').write(txt)
    out[name] = {'file': 'masks/riders/%s.vox.txt' % name, 'cells': len(cells), 'sha256': hashlib.sha256(txt.encode()).hexdigest()}
v = {'riders': rows, 'O_per_column': len(O), 'N_whole_rider': len(N), 'keep': len(O & N), 'carve': len(carve), 'refill_limber': len(refill),
     'stamp': len(stamp), 'over_rider': len(over),
     'stamp_floating': float_cells, 'mirror_miss': mirror, 'hull_voxels_after': len(H) - len(carve) + len(stamp),
     'assembly_voxels_after': len(S) - len(carve) + len(stamp), 'files': out}
json.dump(v, open(os.path.join(D, 'verify_riders.json'), 'w', encoding='utf-8', newline='\n'), ensure_ascii=False, indent=1)
for r in rows:
    print(r)
print({k: v[k] for k in ('O_per_column', 'N_whole_rider', 'keep', 'carve', 'refill_limber', 'stamp', 'over_rider', 'stamp_floating', 'mirror_miss', 'hull_voxels_after', 'assembly_voxels_after')})
