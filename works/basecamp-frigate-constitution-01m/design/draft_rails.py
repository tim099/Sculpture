# 憲法號 階段三十四 quarterdeck／forecastle 舷頂上的欄杆（Tim 2026-10-13「繼續GO」⇒ todo「quarterdeck 那段欄杆比 waist 高（11 號有畫）」）
# 讀圖（11 號 1927 sheer plan；Z 換算用 52 個砲門上下緣擬 Z = a·py + b·px + c，rms 0.09）：
#   quarterdeck X 208–364：三道線 —— 欄杆 129.2→126.4、舷頂 126.4→124.1、下面一道 121.7→119.5（＝ waist 那道往後延伸的線）
#   entry port X ≈ 372–384：兩根柱、沒有線；waist X 393–510：只有一道 119.3–120.8
#   forecastle X 520–618：欄杆 128.2→132.8、舷頂 125.3→129.0（跟著舷弧升）
# 作品現況（組裝件 list 匯出，S 舷舷側最高格 ＝ cap rail 104）：quarterdeck 126→124、waist 123、forecastle 124→129
#   ⇒ quarterdeck／forecastle 的舷頂跟圖一致；缺的是上面那道欄杆（圖上比舷頂高約 2.8–3.8 格）。
# 設計決定：只加、不刻 —— 舷頂上加一道 2 格寬的欄杆（z ＝ 那一欄舷頂 ＋3），每 8 格一根 1 格支柱（z ＋1..＋2），兩頭的柱高出欄杆 1 格（圖上的圓頭柱）。
#   waist 不往下刻（作品 waist 比圖高 3.5 格，照實記）；欄杆的格不比圖精細，高低差照每一欄的舷頂走。
#   一舷做（S）、另一舷鏡像關聯（mirror=y）；產生程式驗：新格（與鏡像）都在空氣裡、P 舷的舷頂跟 S 舷逐欄同高同寬。
# 用法：python -I draft_rails.py <design 資料夾> <組裝件 list 匯出檔（藏掉 欄杆／欄杆-鏡像）>
#   ⇒ masks/rails/rail_side.vox.txt（子作品座標）、verify_rails.json
import sys, os, json, hashlib
import numpy as np
from scipy import ndimage

sys.stdout.reconfigure(encoding='utf-8')
D = os.path.abspath(sys.argv[1])
CAP = 104
SEGS = [dict(name='quarterdeck', x0=206, x1=None, stop_at_gap=True), dict(name='forecastle', x0=515, x1=626, stop_at_gap=False)]
FRAME_AT = (200, 190, 118)        # 子作品固定框（S 舷）：x 200..639、y 190..229、z 118..141
FRAME_SIZE = (440, 40, 24)
POST_EVERY = 8
RAIL_UP = 3

a = np.loadtxt(sys.argv[2], delimiter=',', comments='#', dtype=np.int32, ndmin=2, encoding='utf-8')
S = {}
for x, y, z, c in a:
    S[(int(x), int(y), int(z))] = int(c)
occ = set(S)


# 先把每一欄的 S／P 舷頂讀出來（只讀 x 200..640 那一段，省時間）
byx = {}
for (x, y, z), c in S.items():
    if 200 <= x <= 640 and 100 <= z < 160 and (y >= 175 or y <= 145):
        byx.setdefault(x, []).append((y, z, c))


def top_of(X, side):
    rows = [(y, z, c) for y, z, c in byx.get(X, []) if (y >= 175 if side == 'S' else y <= 145)]
    if not rows:
        return None
    t = max(z for y, z, c in rows)
    ys = [y for y, z, c in rows if z == t]
    cols = {c for y, z, c in rows if z == t}
    return t, min(ys), max(ys), cols


cells, log, posts = {}, [], 0
for seg in SEGS:
    X = seg['x0']
    prev = None
    xs = []
    while True:
        if seg['x1'] is not None and X > seg['x1']:
            break
        t = top_of(X, 'S')
        if t is None or (prev and abs(t[0] - prev[0]) > 2) or CAP not in t[3]:
            if seg['stop_at_gap']:
                break
            raise SystemExit(('舷頂斷了', seg['name'], X, t, prev))
        tp = top_of(X, 'P')
        assert tp and tp[0] == t[0] and 320 - tp[2] == t[1] and 320 - tp[1] == t[2], ('P 舷舷頂跟 S 不對稱', X, t, tp)
        top, y0, y1 = t[0], t[1], t[2]
        yc = (y0 + y1) // 2
        rz = top + RAIL_UP
        ylo, yhi = yc, yc + 1
        zlo = rz
        if prev:
            ylo, yhi = min(ylo, prev[2]), max(yhi, prev[3])        # 船殼收窄時欄杆 y 換位：跟上一欄重疊，面接面
            zlo = min(rz, prev[1])                                    # 舷弧換高度：補到上一欄的高度，面接面
        for y in range(ylo, yhi + 1):
            for z in range(zlo, rz + 1):
                cells[(X, y, z)] = CAP
        xs.append(X)
        log.append(dict(seg=seg['name'], x=X, cap_top=top, cap_y=[y0, y1], rail_z=rz, rail_y=[ylo, yhi]))
        prev = (top, rz, yc, yc + 1)
        X += 1
    seg['x_end'] = xs[-1]
    # 支柱：每 8 格一根、兩頭各一根（站在舷頂上、外側那一格 y ＝ yc＋1）
    for X in xs:
        if (X - xs[0]) % POST_EVERY == 0 or X == xs[-1]:
            r = next(l for l in log if l['x'] == X and l['seg'] == seg['name'])
            yc = (r['cap_y'][0] + r['cap_y'][1]) // 2 + 1
            for z in range(r['cap_top'] + 1, r['rail_z']):
                cells[(X, yc, z)] = CAP
            if X in (xs[0], xs[-1]):
                cells[(X, yc, r['rail_z'] + 1)] = CAP                  # 兩頭的柱高出欄杆 1 格（圖上的圓頭柱）
            posts += 1

hit = [k for k in cells if k in occ]
assert not hit, ('撞到現況', hit[:5])
mhit = [k for k in cells if (k[0], 320 - k[1], k[2]) in occ]
assert not mhit, ('鏡像撞到現況', mhit[:5])
# 跟現況接得上：新格 ∪ 現況 裡，新格每一塊都要連到現況（局部框）
xs_all = [k[0] for k in cells]
box = (min(xs_all) - 1, max(xs_all) + 1)
sub = np.zeros((box[1] - box[0] + 1, 320, 160), bool)
new = np.zeros_like(sub)
for (x, y, z) in occ:
    if box[0] <= x <= box[1] and z < 160:
        sub[x - box[0], y, z] = True
for (x, y, z) in cells:
    new[x - box[0], y, z] = True
lab, n = ndimage.label(sub | new)
anch = set(np.unique(lab[sub]))
floating = [int(L) for L in np.unique(lab[new]) if L not in anch]
assert not floating, ('浮空', len(floating))
fx, fy, fz = FRAME_AT
for (x, y, z) in cells:
    assert 0 <= x - fx < FRAME_SIZE[0] and 0 <= y - fy < FRAME_SIZE[1] and 0 <= z - fz < FRAME_SIZE[2], ('出框', (x, y, z))
out = os.path.join(D, 'masks', 'rails')
os.makedirs(out, exist_ok=True)
txt = ''.join('%d,%d,%d,%d\n' % (x - fx, y - fy, z - fz, c) for (x, y, z), c in sorted(cells.items()))
open(os.path.join(out, 'rail_side.vox.txt'), 'w', encoding='utf-8', newline='\n').write(txt)
v = dict(frame_at=list(FRAME_AT), frame_size=list(FRAME_SIZE), mirror_at=[fx, 321 - fy - FRAME_SIZE[1], fz], cells=len(cells), posts=posts,
         segs=[dict(name=s['name'], x=[s['x0'], s['x_end']]) for s in SEGS], sha256=hashlib.sha256(txt.encode()).hexdigest(),
         assembly_voxels=len(occ), per_x=log)
json.dump(v, open(os.path.join(D, 'verify_rails.json'), 'w', encoding='utf-8', newline='\n'), ensure_ascii=False, indent=1)
print(json.dumps({k: v[k] for k in ('cells', 'posts', 'segs', 'mirror_at', 'assembly_voxels')}, ensure_ascii=False))
