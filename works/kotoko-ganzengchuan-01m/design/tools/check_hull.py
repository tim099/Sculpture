# 步驟 4 讀數：作品匯出 vs 設計應有（結果帳）、結構（元件數／封閉空腔／鏡像差）、線形對照與反向對照
#   出處：calli-cosecha-01m/design/tools/check_hull.py（改寫為福建趕繒船含砲門刻除與花屁股塗裝之完整船殼驗證）
#   用法：python -I -X utf8 tools/check_hull.py <design> [probe_x=<站>]
import os, sys, math, json
import numpy as np
from scipy import ndimage

sys.stdout.reconfigure(encoding='utf-8')
design = sys.argv[1]
probe_x = int(next((a.split('=', 1)[1] for a in sys.argv[2:] if a.startswith('probe_x=')), '-1'))
sys.path.insert(0, design)
sys.path.insert(0, os.path.join(design, 'tools'))
import lines as HL
from wio import export_list

WORK = 'kotoko-ganzengchuan-01m'


def load_vox(path):
    return np.loadtxt(path, delimiter=',', comments='#', dtype=np.int32, ndmin=2, encoding='utf-8')


# 1. 從清單重算應有船殼（hull_01 - carve + paint）
D_hull = load_vox(os.path.join(design, 'masks', 'hull', 'hull_01.vox.txt'))
expected = {(int(x), int(y), int(z)): int(c) for x, y, z, c in D_hull.tolist()}
carve_path = os.path.join(design, 'masks', 'ports', 'carve.vox.txt')
paint_path = os.path.join(design, 'masks', 'ports', 'paint.vox.txt')
if os.path.exists(carve_path):
    for x, y, z, _ in load_vox(carve_path).tolist():
        expected.pop((int(x), int(y), int(z)), None)
if os.path.exists(paint_path):
    for x, y, z, c in load_vox(paint_path).tolist():
        k = (int(x), int(y), int(z))
        if k in expected:
            expected[k] = int(c)

# 2. 從 CLI 匯出實際作品
W = export_list(WORK)
actual = {(int(x), int(y), int(z)): int(c) for x, y, z, c in W.tolist()}

miss = len(expected.keys() - actual.keys())
extra = len(actual.keys() - expected.keys())
cdiff = sum(1 for k in expected.keys() & actual.keys() if expected[k] != actual[k])
print(f'結果帳：作品 {len(actual)}、應有 {len(expected)}、缺 {miss}、多 {extra}、色差 {cdiff}')

# 3. 3D 結構檢查（元件數、封閉空腔、鏡像差）
pts = np.array(list(actual.keys()), dtype=np.int32)
x0, y0, z0 = pts.min(axis=0)
x1, y1, z1 = pts.max(axis=0)
grid = np.zeros((x1 - x0 + 1, y1 - y0 + 1, z1 - z0 + 1), dtype=bool)
grid[pts[:, 0] - x0, pts[:, 1] - y0, pts[:, 2] - z0] = True
_, n_comp = ndimage.label(grid)
cavities = int((ndimage.binary_fill_holes(grid) & ~grid).sum())

plan = HL.load_plan(design)
L = HL.Lines(plan)
YC = L.YC
mirror_diff = sum(1 for (x, y, z), c in actual.items() if actual.get((x, 2 * YC - y, z)) != c)
print(f'結構檢查：連通元件 {n_comp}、封閉空腔 {cavities}、鏡像色差 {mirror_diff}')

# 4. 線形對照與反向對照（避開砲門開口段）
carved_set = set()
if os.path.exists(carve_path):
    carved_set = {(int(x), int(y), int(z)) for x, y, z, _ in load_vox(carve_path).tolist()}

outer = {}
for (x, y, z) in actual:
    if y >= YC:
        k = (x, z)
        if y - YC > outer.get(k, -1):
            outer[k] = y - YC

diffs, worst, probe_hits = [], (0, None), 0
for x in range(84, 316, 12):
    for z in range(4, 56, 4):
        if z > L.top_z(x + 0.5) - 1 or z < L.zb(x + 0.5) + 1:
            continue
        # 若該站 (x, z) 落在砲門開口範圍內則略過
        if any(abs(x - gx) <= 5 and z >= 38 for gx in plan['ports']['gun']['x']):
            continue
        h = float(L.hb(np.array([x + 0.5]), np.array([z + 0.5]))[0])
        if h < 0:
            continue
        want = math.floor(h) + (3 if x == probe_x else 0)
        got = outer.get((x, z))
        if got is None:
            continue
        dlt = got - want
        diffs.append(abs(dlt))
        if x == probe_x and dlt != 0:
            probe_hits += 1
        if abs(dlt) > abs(worst[0]):
            worst = (dlt, (x, z, got, want))

print(f'線形對照：{len(diffs)} 點、|差| 最大 {max(diffs)}（{worst[1]}）、差≠0 的 {sum(1 for v in diffs if v)} 點'
      + (f'（probe_x={probe_x}：設計那一站 +3 ⇒ 報 {probe_hits} 點）' if probe_x >= 0 else ''))

out = {
    'actual': len(actual), 'expected': len(expected), 'missing': miss, 'extra': extra, 'color_diff': cdiff,
    'components': n_comp, 'cavities': cavities, 'mirror_diff': mirror_diff,
    'lines_points': len(diffs), 'lines_max_abs_diff': max(diffs),
}
if probe_x >= 0:
    out['probe_x'] = probe_x
    out['probe_hits'] = probe_hits
print(json.dumps(out, ensure_ascii=False))
