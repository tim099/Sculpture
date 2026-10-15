# 階段四（TASK-0593）讀數：每件子作品匯出 vs 清單（結果帳）、子作品之間與船殼的重疊、梯子點（從組裝件 export format=parts 讀 ＝ 遊戲讀的那一份）
#   用法：python -I -X utf8 tools/check_decks.py <design>
#   · 作品那一側一律從 CLI 匯出讀；梯子點的「空氣、腳下實心、頭頂 14 格」拿組裝件整個組起來的格子量
import json, os, subprocess, sys, tempfile
import numpy as np

sys.stdout.reconfigure(encoding='utf-8')
design = sys.argv[1]
sys.path.insert(0, os.path.join(design, 'tools'))
from wio import export_list, key

HULL = 'calli-cosecha-01m'
plan = json.load(open(os.path.join(design, 'plan.json'), encoding='utf-8'))
pts = json.load(open(os.path.join(design, 'ladder_points.json'), encoding='utf-8'))
parts = {'deck-' + r['key']: os.path.join(design, 'masks', 'decks', r['key'] + '.vox.txt') for r in plan['decks']['rows']}
for up in sorted({v['up'] for v in pts.values()}):
    parts['ladders-' + up] = os.path.join(design, 'masks', 'ladders', up + '.vox.txt')

seen = {}
hull = set(key(export_list(HULL, None)).tolist())
bad = 0
for nm, path in parts.items():
    W = export_list('%s-%s' % (HULL, nm), None)
    D = np.loadtxt(path, delimiter=',', comments='#', dtype=np.int32, ndmin=2, encoding='utf-8')
    cw = dict(zip(key(W).tolist(), W[:, 3].tolist()))
    cd = dict(zip(key(D).tolist(), D[:, 3].tolist()))
    miss, extra = len(set(cd) - set(cw)), len(set(cw) - set(cd))
    cdiff = sum(1 for k in set(cd) & set(cw) if cd[k] != cw[k])
    ov_h = len(set(cw) & hull)
    ov_p = sum(len(set(cw) & s) for s in seen.values())
    seen[nm] = set(cw)
    bad += miss + extra + cdiff + ov_h + ov_p
    print('%-18s 作品 %6d、設計 %6d、缺 %d、多 %d、色差 %d；跟船殼重疊 %d、跟前面幾件重疊 %d' % (nm, len(cw), len(cd), miss, extra, cdiff, ov_h, ov_p))
print('子作品 %d 件、%d 格；問題合計 %d' % (len(parts), sum(len(s) for s in seen.values()), bad))

# 梯子點：組裝件 export format=parts（遊戲讀的那一份）⇒ 每座 4 點；跟設計（ladder_points.json）比
with tempfile.TemporaryDirectory() as d:
    out = os.path.join(d, 'p.json').replace('\\', '/')
    r = subprocess.run(['senate', 'cmd', 'sculpture', '--arg', 'op=export', '--arg', 'format=parts', '--arg', 'work=%s-assembly' % HULL, '--arg', 'out=' + out],
                       capture_output=True, text=True, encoding='utf-8', errors='replace')
    if r.returncode != 0:
        raise SystemExit(r.stdout[-800:] + r.stderr[-800:])
    P = json.load(open(out, encoding='utf-8'))


def walk(node, acc, path=''):
    """parts 匯出的格式不確定時：走一遍整棵樹，收所有「名字像 <梯名>.<點>」的固定點（座標取最後一層換算好的世界座標）。"""
    if isinstance(node, dict):
        for k, v in node.items():
            if isinstance(v, (list, tuple)) and len(v) == 3 and all(isinstance(a, (int, float)) for a in v) and '.' in k:
                acc.setdefault(k, []).append((path, v))
            else:
                walk(v, acc, path + '/' + str(k))
    elif isinstance(node, list):
        for i, v in enumerate(node):
            walk(v, acc, path + '[%d]' % i)


acc = {}
walk(P, acc)
asm = set()
with tempfile.TemporaryDirectory() as d:
    out = os.path.join(d, 'a.txt').replace('\\', '/')
    r = subprocess.run(['senate', 'cmd', 'sculpture', '--arg', 'op=export', '--arg', 'format=list', '--arg', 'work=%s-assembly' % HULL, '--arg', 'out=' + out],
                       capture_output=True, text=True, encoding='utf-8', errors='replace')
    A = np.loadtxt(out, delimiter=',', comments='#', dtype=np.int32, ndmin=2, encoding='utf-8')
    asm = set(key(A).tolist())
k3 = lambda x, y, z: (x * 1000 + y) * 1000 + z
diffs, probs, found = 0, [], 0
for nm, v in sorted(pts.items()):
    for pk, (x, y, z) in v['points'].items():
        name = '%s.%s' % (nm, pk)
        hits = [c for (pth, c) in acc.get(name, [])]
        if not hits:
            probs.append((name, 'parts 裡找不到'))
            continue
        found += 1
        gx, gy, gz = [float(a) for a in hits[-1]]
        if (abs(gx - (x + 0.5)) > 0.01 and abs(gx - x) > 0.01) or (abs(gy - (y + 0.5)) > 0.01 and abs(gy - y) > 0.01) or (abs(gz - (z + 0.5)) > 0.01 and abs(gz - z) > 0.01):
            diffs += 1
        air = k3(x, y, z) not in asm
        floor = k3(x, y, z - 1) in asm
        head = sum(1 for dz in range(14) if k3(x, y, z + dz) in asm)
        if not (air and floor) or head:
            probs.append((name, 'air=%s floor=%s head=%d' % (air, floor, head)))
print('梯子點（組裝件 parts）：%d 座、找到 %d／%d 點、跟設計差 %d；空氣／腳下／頭頂 14 格的問題 %s' % (len(pts), found, len(pts) * 4, diffs, probs or 0))
