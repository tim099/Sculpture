# 憲法號 階段四十一 bumpkins＋main brace（Tim 2026-10-13「1~3 GO」⇒ todo「braces＋bumpkins 一起規劃」）
# 出處（查資料 agent 下載、裁切圖我自己看過標字）：USS Constitution Museum 模型資源
#   - Navy plan No. 24422「Spar Deck General Arrangement」1931（平面圖）：
#       船尾 quarter 兩舷各一根「MAIN BRACE BUMPKIN」往舷外伸，端頭一個滑車；「MAIN BRACE」從 bumpkin 端往前、往外拉；
#       「MAIN BRACE CHESSTREE」在 bumpkin 的船頭側、舷牆上（虛線圓）。船頭 head 兩舷各一根「FORETACK BUMPKIN」，從 head rails 底下斜著往前、往外伸，
#       端頭一條 guy 拉回中線（bowsprit／cutwater）。
#   - No. 24474「Outboard Profile, Fittings」1931（側面圖）：BUMPKIN、MAIN BRACE CHESSTREE 都在 spar deck 第 1 號砲門的船尾側、砲門上緣那一帶。
# 換算（我量）：
#   - 平面圖：用桅當尺 —— 圖上 mizzen→main 506 px（縮圖）＝ 作品 149 格（main 350.5、mizzen 201.5，對得上 24422 的 62.3 px/ft）。
#       main brace bumpkin X ≈ 108、chesstree X ≈ 115；圖上第 1 號砲門 X ≈ 132（作品 128–137，中 132.5）、船尾 X ≈ 99（作品欄杆頂 97）。
#   - 側面圖：用作品第 1 號砲門（10 格寬 ＝ 170 px）當尺 ⇒ chesstree X ≈ 114.8、bumpkin X ≈ 108.2、兩個都在 z ≈ 123（砲門上緣 124 下面一點）。
#     兩張圖各自量，差 < 1 格 ⇒ 取 bumpkin X 107–108、chesstree X 113–117（中 115）、z 123。
#     ⚠ 階段三十五的 main brace chesstree 放在 X 143（砲門的船頭側）—— 放錯邊，這一階段從 -chesstrees-side 刻掉、搬來這裡。
#   - fore tack bumpkin（平面圖，前桅 X 590.5 當尺）：根（穿過 head rail 那一點）(683.6, 180.4)、尖 (698.6, 199.9) ⇒ 往前 15、往外 19.5、長 24.6 格。
#     作品的 head rail 比 1931 窄（x 684 的外緣 y 174、圖上 180）⇒ 方向與長度照圖，穿過點對齊作品自己的 rail（x 684、y 174）；
#     圖上虛線那段（在 rail 裡面）約 5 格 ⇒ 往裡多 5 格。高度：作品上 rail 在 x 683–684 的底面 z 115 ⇒ bumpkin z 113–114（頂貼著 rail 底，
#     平面圖也是從 rail 底下穿過去）；側面圖量的是 z 109 —— 差 4.5 格，因為作品的 head 不是照 1931 那張做的。
# 設計：bumpkin 2×2 黑 36（圖上端頭八角，2 格做不出來 ⇒ 不做）；chesstree 同階段三十五的形狀（5 長 × 3 高、四角去掉、中間 3 格黑槽、橡木 136）。
#   一舷（S）子作品＋鏡像關聯；固定點：quarter —— brace-eye（bumpkin 尖那一格）、brace-block（尖的下面、往前 2、往裡 1 —— 圖上滑車掛在尖的前面裡面；v1 往裡 2 ⇒ S 舷回來那段擦到 quarter davit 的橫桁）、
#   chesstree（槽中間那一格）；bow —— tack（尖的上層）、guy（尖的下層）。
# 用法：python -I draft_bumpkins.py <design 資料夾> <組裝件 list 匯出檔（藏掉 bumpkin 四條關聯）>
import sys, os, json, hashlib, math
import numpy as np
from scipy import ndimage

sys.stdout.reconfigure(encoding='utf-8')
D = os.path.abspath(sys.argv[1])
BLACK, OAK = 36, 136
a = np.loadtxt(sys.argv[2], delimiter=',', comments='#', dtype=np.int32, ndmin=2, encoding='utf-8')
occ = {(int(x), int(y), int(z)): int(c) for x, y, z, c in a}
S = set(occ)


def outer_y(x, z, side):
    ys = [y for y in (range(175, 260) if side == 'S' else range(60, 146)) if (x, y, z) in S]
    return (max(ys) if side == 'S' else min(ys)) if ys else None


def connected(cells, margin=2):
    xs = [k[0] for k in cells]; ys = [k[1] for k in cells]; zs = [k[2] for k in cells]
    lo = (min(xs) - margin, min(ys) - margin, min(zs) - margin)
    hi = (max(xs) + margin + 1, max(ys) + margin + 1, max(zs) + margin + 1)
    shape = tuple(h - l for h, l in zip(hi, lo))
    old = np.zeros(shape, bool); new = np.zeros(shape, bool)
    for (x, y, z) in S:
        if lo[0] <= x < hi[0] and lo[1] <= y < hi[1] and lo[2] <= z < hi[2]:
            old[x - lo[0], y - lo[1], z - lo[2]] = True
    for (x, y, z) in cells:
        new[x - lo[0], y - lo[1], z - lo[2]] = True
    lab, _ = ndimage.label(old | new)
    anch = set(np.unique(lab[old])) - {0}
    nl, nn = ndimage.label(new)
    return all(L in anch for L in np.unique(lab[new])), int(nn)


def finish(name, cells, anchors, frame_at, frame_size, extra):
    hit = [k for k in cells if k in S]
    assert not hit, (name, '撞到現況', hit[:5])
    mhit = [k for k in cells if (k[0], 320 - k[1], k[2]) in S]
    assert not mhit, (name, '鏡像撞到現況', mhit[:5])
    ok, nparts = connected(cells)
    assert ok, (name, '浮空')
    fx, fy, fz = frame_at
    for p in list(cells) + list(anchors.values()):
        assert 0 <= p[0] - fx < frame_size[0] and 0 <= p[1] - fy < frame_size[1] and 0 <= p[2] - fz < frame_size[2], (name, '出框', p)
    out = os.path.join(D, 'masks', 'bumpkins')
    os.makedirs(out, exist_ok=True)
    txt = ''.join('%d,%d,%d,%d\n' % (x - fx, y - fy, z - fz, c) for (x, y, z), c in sorted(cells.items()))
    open(os.path.join(out, name + '.vox.txt'), 'w', encoding='utf-8', newline='\n').write(txt)
    v = dict(frame_at=list(frame_at), frame_size=list(frame_size), mirror_at=[fx, 321 - fy - frame_size[1], fz], cells=len(cells),
             parts=nparts, sha256=hashlib.sha256(txt.encode()).hexdigest(),
             anchors={k: [p[0] - fx, p[1] - fy, p[2] - fz] for k, p in anchors.items()}, anchors_world={k: list(p) for k, p in anchors.items()})
    v.update(extra)
    return v


V = dict(assembly_voxels=len(S))
# ───────── 船尾 quarter：main brace bumpkin＋chesstree ─────────
cells, log = {}, {}
x0, zc = 113, 123                                             # chesstree X 113–117（中 115）
for dx in range(5):
    for dz in (-1, 0, 1):
        if dz != 0 and dx in (0, 4):
            continue
        x, z = x0 + dx, zc + dz
        yo, yp = outer_y(x, z, 'S'), outer_y(x, z, 'P')
        assert yo is not None and 320 - yp == yo, ('chesstree 那一點船殼不對稱', x, z, yo, yp)
        cells[(x, yo + 1, z)] = BLACK if dz == 0 and 1 <= dx <= 3 else OAK
log['chesstree'] = dict(x=[x0, x0 + 4], z=[zc - 1, zc + 1], y=sorted({k[1] for k in cells}))
BX, BZ, TIP = (107, 108), (123, 124), 215
roots = []
for x in BX:
    for z in BZ:
        yo, yp = outer_y(x, z, 'S'), outer_y(x, z, 'P')
        assert yo is not None and 320 - yp == yo, ('bumpkin 根那一點船殼不對稱', x, z, yo, yp)
        roots.append(yo)
        for y in range(yo + 1, TIP + 1):
            cells[(x, y, z)] = BLACK
log['bumpkin'] = dict(x=list(BX), z=list(BZ), y=[min(roots) + 1, TIP], length=TIP - min(roots))
anchors = {'brace-eye': (108, TIP, 124), 'brace-block': (110, TIP - 1, 122), 'chesstree': (115, log['chesstree']['y'][0], 123)}
assert anchors['brace-block'] not in S and anchors['brace-block'] not in cells
V['quarter'] = finish('main_brace_bumpkin_side', cells, anchors, (100, 200, 115), (25, 20, 15), dict(items=log))

# ───────── 船頭：fore tack bumpkin ─────────
dx_, dy_ = 15.0, 19.5
L = math.hypot(dx_, dy_)
ux, uy = dx_ / L, dy_ / L
C = (684.0, 174.0)                                            # 穿過作品 head rail 那一點（外緣）
IN, OUTL = 5.0, L                                             # 往裡 5、往外 24.6
ZS = (113, 114)
cells = {}
skipped = 0
t = -IN
while t <= OUTL + 1e-9:
    for w in (-0.75, -0.25, 0.25, 0.75):                       # 寬 ≈ 1.5 ⇒ 斜著也面接面
        px = C[0] + ux * t - uy * w
        py = C[1] + uy * t + ux * w
        for z in ZS:
            k = (int(math.floor(px)), int(math.floor(py)), z)
            if k in S:
                skipped += 1
                continue
            cells[k] = BLACK
    t += 0.1
tip = (int(math.floor(C[0] + ux * OUTL)), int(math.floor(C[1] + uy * OUTL)))
anchors = {'tack': (tip[0], tip[1], 114), 'guy': (tip[0], tip[1], 113)}
assert all(p in cells for p in anchors.values()), ('固定點不在 bumpkin 上', anchors)
V['bow'] = finish('foretack_bumpkin_side', cells, anchors, (670, 161, 105), (45, 50, 15),
                  dict(items=dict(cross=C, dir=[dx_, dy_], inboard=IN, length=round(L, 2), z=list(ZS), overlap_cells_skipped=skipped)))
json.dump(V, open(os.path.join(D, 'verify_bumpkins.json'), 'w', encoding='utf-8', newline='\n'), ensure_ascii=False, indent=1)
print(json.dumps({k: (dict(cells=v['cells'], parts=v['parts'], sha=v['sha256'][:12], anchors_world=v['anchors_world'], items=v['items']) if isinstance(v, dict) else v) for k, v in V.items()}, ensure_ascii=False))
