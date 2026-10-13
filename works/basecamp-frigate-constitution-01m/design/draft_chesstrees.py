# 憲法號 階段三十五 chesstrees（Tim 2026-10-13「繼續GO」⇒ todo「fenders／chesstree」）
# 出處：Navy plan No. 24474「Restoration 1927–1931, U.S. Frigate Constitution, Outboard Profile, Fittings, Taken From Work」（Boston Navy Yard，1931-09-30 核准），
#   USS Constitution Museum 的模型資源（https://ussconstitutionmuseum.org/download/outboard-profile-fittings/）。查資料 agent 找到、我自己看過裁切圖確認標字。
#   ⇒ 右舷三個，都在 spar deck 舷牆那一帶：FORE SHEET CHESSTREE（船腰）、CHESSTREE FOR LOWER STUDDINGSAIL BOOM（船腰、更前）、MAIN BRACE CHESSTREE（船尾 quarter，bumpkin 旁）。
#   形狀：橫的圓頭小滑輪板（不是英式的直木）。fenders：1931 舷側沒有（現代只在吃水線）⇒ 不做。
# 位置換算（用砲門當尺，因為 1931 圖跟作品依據的 1927 11 號圖不是同一張）：
#   · 船腰兩個：圖上 entry port 往前第 1 個 gun deck 砲門 ＝ 作品第 7 號（X 390.6）；fore sheet 在第 8、9 號（422.3／455.35）中間、比例 0.493 ⇒ X 438.6；
#     studdingsail 在第 9、10 號（455.35／488.52）之間、比例 0.78 ⇒ X 481.2。高度：圖上在 rail 與 planksheer 之間 48% ⇒ 作品 waist 舷頂 123 與 spar deck 107 之間 ⇒ z 115。
#   · main brace：用 gun deck 第 1 號換 X 145.6、用最近的 spar deck 砲門換 X 139.7（兩張圖差 6 格）⇒ 取中 143；高度在砲門上緣一帶 ⇒ z 123（舷頂 126 下面）。
#   ⚠ 尺寸圖上沒標：滑輪板量起來約 14"（≈ 3.6 格）長、不到 1 ft 高 ⇒ 設計：5 長 × 3 高、四角去掉、中間一排 3 格黑（槽）、凸出船殼 1 格。
# 一舷（S）子作品＋鏡像關聯；每一格貼在那一點 (x, z) 的船殼最外面 ＋1（跟著船殼弧度）。
# 用法：python -I draft_chesstrees.py <design 資料夾> <組裝件 list 匯出檔（藏掉 chesstrees／chesstrees-鏡像）>
import sys, os, json, hashlib
import numpy as np
from scipy import ndimage

sys.stdout.reconfigure(encoding='utf-8')
D = os.path.abspath(sys.argv[1])
OAK, BLACK = 136, 36
ITEMS = [dict(name='fore-sheet', label='FORE SHEET CHESSTREE（船腰）', x=438.6, z=115),
         dict(name='studdingsail', label='CHESSTREE FOR LOWER STUDDINGSAIL BOOM（船腰）', x=481.2, z=115),
         dict(name='main-brace', label='MAIN BRACE CHESSTREE（船尾 quarter）', x=143.0, z=123)]
FRAME_AT = (130, 200, 108)
FRAME_SIZE = (370, 40, 24)

a = np.loadtxt(sys.argv[2], delimiter=',', comments='#', dtype=np.int32, ndmin=2, encoding='utf-8')
occ = {(int(x), int(y), int(z)): int(c) for x, y, z, c in a}
S = set(occ)


def outer_y(x, z, side):
    ys = [y for y in (range(175, 260) if side == 'S' else range(60, 146)) if (x, y, z) in S]
    return (max(ys) if side == 'S' else min(ys)) if ys else None


cells, log = {}, []
for it in ITEMS:
    x0 = int(round(it['x'])) - 2
    shape = []
    for dx in range(5):
        for dz in (-1, 0, 1):
            if dz != 0 and dx in (0, 4):
                continue                                  # 四角去掉 ⇒ 圓頭
            col = BLACK if dz == 0 and 1 <= dx <= 3 else OAK
            shape.append((x0 + dx, it['z'] + dz, col))
    ys, under = [], []
    for x, z, c in shape:
        yo = outer_y(x, z, 'S')
        yp = outer_y(x, z, 'P')
        assert yo is not None and yp is not None, ('那一點沒有船殼', it['name'], x, z)
        assert 320 - yp == yo, ('兩舷船殼外緣不對稱', it['name'], x, z, yo, yp)
        under.append(occ[(x, yo, z)])
        cells[(x, yo + 1, z)] = c
        ys.append(yo + 1)
    log.append(dict(name=it['name'], label=it['label'], x=[x0, x0 + 4], z=[it['z'] - 1, it['z'] + 1], y=[min(ys), max(ys)],
                    hull_colors_under=sorted(set(under))))
hit = [k for k in cells if k in S]
assert not hit, ('撞到現況', hit[:5])
mhit = [k for k in cells if (k[0], 320 - k[1], k[2]) in S]
assert not mhit, ('鏡像撞到現況', mhit[:5])
# 每一塊都要面接面連到現況
xs = [k[0] for k in cells]
lo = min(xs) - 1
sub = np.zeros((max(xs) - lo + 2, 320, 160), bool)
new = np.zeros_like(sub)
for (x, y, z) in S:
    if lo <= x <= max(xs) + 1 and z < 160:
        sub[x - lo, y, z] = True
for (x, y, z) in cells:
    new[x - lo, y, z] = True
lab, n = ndimage.label(sub | new)
anch = set(np.unique(lab[sub]))
assert all(L in anch for L in np.unique(lab[new])), '浮空'
fx, fy, fz = FRAME_AT
for (x, y, z) in cells:
    assert 0 <= x - fx < FRAME_SIZE[0] and 0 <= y - fy < FRAME_SIZE[1] and 0 <= z - fz < FRAME_SIZE[2], ('出框', (x, y, z))
out = os.path.join(D, 'masks', 'chesstrees')
os.makedirs(out, exist_ok=True)
txt = ''.join('%d,%d,%d,%d\n' % (x - fx, y - fy, z - fz, c) for (x, y, z), c in sorted(cells.items()))
open(os.path.join(out, 'chesstrees_side.vox.txt'), 'w', encoding='utf-8', newline='\n').write(txt)
v = dict(source='Navy plan No. 24474 (1931), USS Constitution Museum', frame_at=list(FRAME_AT), frame_size=list(FRAME_SIZE),
         mirror_at=[fx, 321 - fy - FRAME_SIZE[1], fz], cells=len(cells), sha256=hashlib.sha256(txt.encode()).hexdigest(),
         assembly_voxels=len(S), items=log)
json.dump(v, open(os.path.join(D, 'verify_chesstrees.json'), 'w', encoding='utf-8', newline='\n'), ensure_ascii=False, indent=1)
print(json.dumps(v, ensure_ascii=False))
