# 組裝件的封閉空腔補實（Tim 2026-10-11：封閉小空腔用鄰近 voxel 顏色填滿，模型輸出才會合併）
#   憲法號 design/tools/fill_cavities.py 只量一件作品；餘燼號這種空腔常是好幾件一起圍出來的（船殼牆＋clamp＋甲板子作品的橫樑頭）
#   ⇒ 量組裝件（links=all）；顏色規則照那支：6 鄰居裡實心格最多的顏色（同票先取 141 木色，再取色號小的），大空腔從外圈往內一層層傳
#   ⇒ design/masks/cavities/<名稱>.vox.txt（落進 <目標作品>，at 0,0,0；格在目標作品裡一定是空的 —— 組裝件都空了）
# 用法：python -I fill_cavities_asm.py <design 資料夾> <組裝件> <名稱>
import sys, os, json, hashlib, collections
import numpy as np
from scipy import ndimage
sys.stdout.reconfigure(encoding='utf-8')
D = os.path.abspath(sys.argv[1])
sys.path.insert(0, D)
import draft_profile as DP   # noqa: E402

WOOD = 141
N6 = ((1, 0, 0), (-1, 0, 0), (0, 1, 0), (0, -1, 0), (0, 0, 1), (0, 0, -1))
vox = {(int(x), int(y), int(z)): int(c) for x, y, z, c in DP.export_list(sys.argv[2], 'all')}
k = np.array(list(vox.keys()))
lo = k.min(0) - 1
A = np.zeros(k.max(0) - lo + 2, bool)
A[tuple((k - lo).T)] = True
lab, _ = ndimage.label(~A)
inner = (lab != lab[0, 0, 0]) & ~A
ids, sizes = np.unique(lab[inner], return_counts=True)
todo = {tuple(int(v) for v in c + lo) for c in np.argwhere(inner)}
fill = {}
while todo:
    layer = {}
    for p in todo:
        cols = [vox.get((p[0] + a, p[1] + b, p[2] + c)) or fill.get((p[0] + a, p[1] + b, p[2] + c)) for a, b, c in N6]
        cols = [c for c in cols if c]
        if cols:
            cnt = collections.Counter(cols)
            best = max(cnt.values())
            top = [c for c, n in cnt.items() if n == best]
            layer[p] = WOOD if WOOD in top else min(top)
    if not layer:
        raise SystemExit('有空腔傳不到顏色')
    fill.update(layer)
    todo -= set(layer)
out = os.path.join(D, 'masks', 'cavities')
os.makedirs(out, exist_ok=True)
p = os.path.join(out, sys.argv[3] + '.vox.txt')
rows = sorted((a[0], a[1], a[2], c) for a, c in fill.items())
open(p, 'w', encoding='utf-8', newline='\n').write('# 封閉空腔補實 %s（世界座標）（%d 格）\n' % (sys.argv[3], len(rows)) + '\n'.join('%d,%d,%d,%d' % r for r in rows) + '\n')
v = {'cavities': int(len(ids)), 'cells': len(rows), 'sizes': sorted(int(s) for s in sizes), 'colors': dict(collections.Counter(fill.values())),
     'mirror_mismatch': sum(1 for (x, y, z) in fill if (x, 320 - y, z) not in fill), 'sha256': hashlib.sha256(open(p, 'rb').read()).hexdigest()}
json.dump(v, open(os.path.join(out, sys.argv[3] + '.json'), 'w', encoding='utf-8', newline='\n'), ensure_ascii=False, indent=1)
print(json.dumps(v, ensure_ascii=False))
