# 餘燼號 補漆（Tim 2026-10-12：「船頭可以補噴漆（有發現縫）」＋兩張截圖：船頭的暗紅帶被黑色直條切開）
#   原因：階段三的塗法只塗「每個 (x, z) 往外最遠那一格」—— 船頭的面朝前（+x），看得到的是每個 (y, z) 最前面那一格，沒被塗到
#   改法：x ≥ x_from 的黑外板（36）只要有一面貼著船外的空氣（從外框外面 flood 進來的空氣）就算表面；
#         帶子的上下緣照那一欄已經塗紅的高度（兩條帶各自；那一欄沒有紅 ⇒ 借最近一欄）⇒ 帶內 → 暗紅、上下各一格 → 金
#   ⇒ masks/paint/paint_fix.vox.txt（stampvox overwrite=1）、verify_paint_fix.json
# 用法：python -I draft_paint_fix.py <design 資料夾>
import sys, os, json, hashlib
import numpy as np
from scipy import ndimage

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from draft_ports import export_mark   # noqa: E402

W = 'basecamp-ember-01m'
YC = 160


def main():
    sys.stdout.reconfigure(encoding='utf-8')
    design = os.path.abspath(sys.argv[1])
    plan = json.load(open(os.path.join(design, 'plan.json'), encoding='utf-8'))
    F = plan['paint_fix']
    a = export_mark(W, F['world_mark'])
    assert len(a) == F['world_voxels'], len(a)
    H = {(int(x), int(y), int(z)): int(c) for x, y, z, c in a}
    red, gold, black, cut = F['band'], F['line'], F['black'], plan['band']['cut_z']
    # 船外的空氣：外框外擴 1 格、從角落 flood（船艙經過砲門也通到外面 —— 只塗黑外板，內板是 177，不受影響）
    arr = np.array(sorted(H))
    lo = arr.min(0) - 1
    shape = tuple(arr.max(0) - lo + 2)
    S = np.zeros(shape, bool)
    S[tuple((arr - lo).T)] = True
    lab, n = ndimage.label(~S)
    ext = lab == lab[0, 0, 0]
    # 每一欄兩條帶的上下緣（照現在已經塗紅的格）
    bands = {}
    for (x, y, z), c in H.items():
        if c == red:
            i = 0 if z < cut else 1
            b = bands.setdefault((x, i), [z, z])
            b[0], b[1] = min(b[0], z), max(b[1], z)
    xs = sorted({x for (x, i) in bands})

    def band(x, i):
        if (x, i) in bands:
            return bands[(x, i)], False
        best = min((abs(xx - x), xx) for xx in xs if (xx, i) in bands)[1]
        return bands[(best, i)], True
    pt = {}
    borrowed = set()
    for (x, y, z), c in H.items():
        if c != black or x < F['x_from']:
            continue
        p = np.array((x, y, z)) - lo
        if not any(ext[tuple(p + d)] for d in ((1, 0, 0), (-1, 0, 0), (0, 1, 0), (0, -1, 0), (0, 0, 1), (0, 0, -1))):
            continue
        for i in (0, 1):
            (zl, zh), b = band(x, i)
            if zl <= z <= zh:
                pt[(x, y, z)] = red
            elif z in (zl - 1, zh + 1):
                pt[(x, y, z)] = gold
            else:
                continue
            if b:
                borrowed.add(x)
    v = {'world': len(H), 'paint': len(pt), 'to': {str(k): sum(1 for c in pt.values() if c == k) for k in (red, gold)},
         'x_borrowed_band': sorted(borrowed)[:20], 'x_borrowed_count': len(borrowed),
         'by_x_bucket': {str(k): vv for k, vv in sorted(__import__('collections').Counter(x // 50 * 50 for (x, y, z) in pt).items())},
         'mirror_mismatch': sum(1 for (x, y, z), c in pt.items() if pt.get((x, 320 - y, z)) != c)}
    out = os.path.join(design, 'masks', 'paint')
    p = os.path.join(out, 'paint_fix.vox.txt')
    rows = sorted((k[0], k[1], k[2], c) for k, c in pt.items())
    open(p, 'w', encoding='utf-8', newline='\n').write('# 補漆（stampvox overwrite=1；世界座標 at 0,0,0）（%d 格）\n' % len(rows) + '\n'.join('%d,%d,%d,%d' % r for r in rows) + '\n')
    v['file'] = {'cells': len(rows), 'sha256': hashlib.sha256(open(p, 'rb').read()).hexdigest()}
    json.dump(v, open(os.path.join(design, 'verify_paint_fix.json'), 'w', encoding='utf-8', newline='\n'), ensure_ascii=False, indent=1)
    print(json.dumps(v, ensure_ascii=False, indent=1))


if __name__ == '__main__':
    main()
