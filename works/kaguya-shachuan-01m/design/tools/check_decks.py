# 出處：kaguya-guineaman-01m/design/tools/check_decks.py（改寫供沙船步驟 5 驗證）
# 讀數：子作品匯出 vs 清單、彼此與船殼重疊、梯子點（parts）、第一人稱可達與走回有向圖（walkback）
import json, os, subprocess, sys, tempfile
from collections import deque
import numpy as np

sys.stdout.reconfigure(encoding='utf-8')
design = sys.argv[1]
sys.path.insert(0, os.path.join(design, 'tools'))
from wio import export_list, key

HULL = 'kaguya-shachuan-01m'
plan = json.load(open(os.path.join(design, 'plan.json'), encoding='utf-8'))
pts = json.load(open(os.path.join(design, 'ladder_points.json'), encoding='utf-8'))
parts = {'deck-' + k: os.path.join(design, 'masks', 'decks', k + '.vox.txt') for k in plan['decks_build']['spans']}
for up in sorted({v['up'] for v in pts.values()}):
    parts['ladders-' + up] = os.path.join(design, 'masks', 'ladders', up + '.vox.txt')

seen = {}
hull = set(key(export_list(HULL, None)).tolist())
bad = 0
for nm, path in parts.items():
    W = export_list(f'{HULL}-{nm}', None)
    D = np.loadtxt(path, delimiter=',', comments='#', dtype=np.int32, ndmin=2, encoding='utf-8')
    cw = dict(zip(key(W).tolist(), W[:, 3].tolist()))
    cd = dict(zip(key(D).tolist(), D[:, 3].tolist()))
    miss, extra = len(set(cd) - set(cw)), len(set(cw) - set(cd))
    cdiff = sum(1 for k in set(cd) & set(cw) if cd[k] != cw[k])
    ov_h = len(set(cw) & hull)
    ov_p = sum(len(set(cw) & s) for s in seen.values())
    seen[nm] = set(cw)
    bad += miss + extra + cdiff + ov_h + ov_p
    print('%-18s 作品 %6d、設計 %6d、缺 %d、多 %d、色差 %d；重疊殼 %d／前 %d' % (nm, len(cw), len(cd), miss, extra, cdiff, ov_h, ov_p))
print('子作品 %d 件、%d 格；問題合計 %d' % (len(parts), sum(len(s) for s in seen.values()), bad))

with tempfile.TemporaryDirectory() as d:
    out = os.path.join(d, 'p.json').replace('\\', '/')
    r = subprocess.run(['senate', 'cmd', 'sculpture', '--arg', 'op=export', '--arg', 'format=parts', '--arg', f'work={HULL}-assembly', '--arg', 'out=' + out],
                       capture_output=True, text=True, encoding='utf-8', errors='replace')
    if r.returncode != 0:
        raise SystemExit(r.stdout[-800:] + r.stderr[-800:])
    P = json.load(open(out, encoding='utf-8'))

def walk_pts(node, acc):
    if isinstance(node, dict):
        for k, v in node.items():
            if isinstance(v, (list, tuple)) and len(v) == 3 and all(isinstance(a, (int, float)) for a in v) and '.' in k:
                acc.setdefault(k, []).append(v)
            else:
                walk_pts(v, acc)
    elif isinstance(node, list):
        for v in node:
            walk_pts(v, acc)

acc = {}
walk_pts(P, acc)
A = export_list(f'{HULL}-assembly', None, links='all')
SX, SY, SZ = plan['space']['assembly']
grid = np.zeros((SX, SY, SZ), bool)
grid[A[:, 0], A[:, 1], A[:, 2]] = True

diffs, probs, found = 0, [], 0
for nm, v in sorted(pts.items()):
    for pk, (x, y, z) in v['points'].items():
        name = f'{nm}.{pk}'
        hits = acc.get(name, [])
        if not hits:
            probs.append((name, 'parts 裡找不到'))
            continue
        found += 1
        gx, gy, gz = [float(a) for a in hits[-1]]
        if (abs(gx - (x + 0.5)) > 0.01 and abs(gx - x) > 0.01) or (abs(gy - (y + 0.5)) > 0.01 and abs(gy - y) > 0.01) or (abs(gz - (z + 0.5)) > 0.01 and abs(gz - z) > 0.01):
            diffs += 1
        air = not grid[x, y, z]
        floor = bool(grid[x, y, z - 1])
        head = int(grid[x, y, z:z + 14].sum())
        if not (air and floor) or head:
            probs.append((name, f'air={air} floor={floor} head={head}'))
print('梯子點（parts）：%d 座、找到 %d／%d 點、差 %d；問題 %s' % (len(pts), found, len(pts) * 4, diffs, probs or 0))

# 第一人稱走得進去就走得出來（walkback）：以主甲板站點 (150, 96, 23) 為根
# 站立點：腳下實心 (z-1) 且頭上 14 格（z..z+13）全空；相鄰四柱上 ≤6、下 ≤8 且離腳最近
stand = {}
for x in range(36, 248):
    for y in range(60, 132):
        zs = []
        for z in range(1, 55):
            if grid[x, y, z - 1] and not grid[x, y, z:z + 14].any():
                zs.append(z)
        if zs:
            stand[(x, y)] = zs

def neighbors(x, y, z):
    for dx, dy in ((1,0),(-1,0),(0,1),(0,-1)):
        cands = [nz for nz in stand.get((x + dx, y + dy), ()) if -8 <= nz - z <= 6]
        if cands:
            best = min(cands, key=lambda nz: (abs(nz - z), -nz))
            yield (x + dx, y + dy, best)

root = (110, 96, 23)
assert root[:2] in stand and root[2] in stand[root[:2]], 'root not standable'
fwd = {root}
q = deque([root])
while q:
    u = q.popleft()
    for v in neighbors(*u):
        if v not in fwd:
            fwd.add(v)
            q.append(v)

# 反向圖：誰能走回 root
rev = {}
for x, y, zs in [(k[0], k[1], v) for k, v in stand.items()]:
    for z in zs:
        for v in neighbors(x, y, z):
            rev.setdefault(v, []).append((x, y, z))
back = {root}
q = deque([root])
while q:
    u = q.popleft()
    for v in rev.get(u, ()):
        if v not in back:
            back.add(v)
            q.append(v)
trapped = fwd - back
print('第一人稱走回檢查（框 x=36..247）：可達 %d 格、能走回 %d 格、困住 %d 格' % (len(fwd), len(back), len(trapped)))
