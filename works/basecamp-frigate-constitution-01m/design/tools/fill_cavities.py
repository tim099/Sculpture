# 封閉空腔補實（Tim 2026-10-11：「封閉小空腔是否可以用鄰近 voxel 顏色填滿（確保模型輸出時會合併）」）
#   封閉空腔 ＝ 6 連通、跟外面不通的空氣（同 check_ports.cavities）—— 從外面看不到，但 export 每一個都多一圈朝內的面
#   每格顏色 ＝ 6 鄰居裡實心格最多的那個顏色（同票先取 141 木色，再取色號小的）；
#   鄰居全是空氣的（大空腔的內部）從外圈往內一層一層傳（每一層只看已經有顏色的鄰居）
#   ⇒ design/masks/cavities/<名稱>.vox.txt（stampvox 清單，at=0,0,0）＋ <名稱>.json（格數、空腔數、大小分布、顏色、sha256、自我驗算）
# 用法：python -I fill_cavities.py <名稱> [--draft]    （--draft ＝ 量「作品＋草稿」）
#   每鋪一層封得住空氣的東西（外板、內板、甲板…）之後都可以再跑一次；名稱帶階段，例 after_stage8
import sys, os, json, hashlib, collections
sys.stdout.reconfigure(encoding='utf-8')
import numpy as np
from scipy import ndimage
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from replay import replay              # noqa: E402

W = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
DES = os.path.join(W, 'design')
WOOD = 141
N6 = ((1, 0, 0), (-1, 0, 0), (0, 1, 0), (0, -1, 0), (0, 0, 1), (0, 0, -1))


def cavities(vox):
    k = np.array(list(vox.keys()))
    lo = k.min(0) - 1
    A = np.zeros(k.max(0) - lo + 2, bool)
    A[tuple((k - lo).T)] = True
    lab, _ = ndimage.label(~A)
    outside = lab[0, 0, 0]
    inner = (lab != outside) & ~A
    ids, sizes = np.unique(lab[inner], return_counts=True)
    cells = [tuple(int(v) for v in c + lo) for c in np.argwhere(inner)]
    return len(ids), sizes, cells


def pick(colors):
    cnt = collections.Counter(colors)
    best = max(cnt.values())
    top = [c for c, n in cnt.items() if n == best]
    return WOOD if WOOD in top else min(top)


def main():
    name = [a for a in sys.argv[1:] if not a.startswith('--')][0]
    draft = '--draft' in sys.argv
    vox = {k: v[0] for k, v in replay(W, draft=draft).items()}
    n, sizes, cells = cavities(vox)
    todo = set(cells)
    fill = {}
    layers = 0
    while todo:
        layer = {}
        for c in todo:
            cols = [vox.get(t) or fill.get(t) for t in ((c[0] + d[0], c[1] + d[1], c[2] + d[2]) for d in N6)]
            cols = [v for v in cols if v]
            if cols:
                layer[c] = pick(cols)
        if not layer:
            raise SystemExit('有空腔格一個實心鄰居都傳不到（不該發生）')
        fill.update(layer)
        todo -= set(layer)
        layers += 1
    # 自我驗算：補完之後封閉空腔 ＝ 0、補的格都原本是空的、不碰到外面的空氣
    after = dict(vox)
    assert all(c not in vox for c in fill)
    after.update(fill)
    n2, _, _ = cavities(after)
    mirror = sum(1 for (x, y, z), v in fill.items() if fill.get((x, 320 - y, z)) != v)
    out = os.path.join(DES, 'masks', 'cavities')
    os.makedirs(out, exist_ok=True)
    p = os.path.join(out, name + '.vox.txt')
    body = '\n'.join('%d,%d,%d,%d' % (c[0], c[1], c[2], v) for c, v in sorted(fill.items()))
    open(p, 'w', encoding='utf-8', newline='\n').write(
        '# %s —— 封閉空腔補實（%d 個空腔、%d 格；顏色 ＝ 6 鄰居實心格最多的顏色，同票取 141；at=0,0,0）\n' % (name, n, len(fill)) + body + '\n')
    a = np.array(list(fill.keys()))
    res = {'name': name, 'measured': '作品＋草稿' if draft else '作品現在', 'world_voxels': len(vox),
           'cavities': n, 'cells': len(fill), 'layers': layers,
           'size_hist': {str(k): v for k, v in sorted(collections.Counter(sizes.tolist()).items())},
           'colors': {str(k): v for k, v in sorted(collections.Counter(fill.values()).items())},
           'x': [int(a[:, 0].min()), int(a[:, 0].max())], 'z': [int(a[:, 2].min()), int(a[:, 2].max())],
           'mirror_mismatch': mirror, 'cavities_after': n2, 'expect_after': len(vox) + len(fill),
           'sha256': hashlib.sha256(open(p, 'rb').read()).hexdigest()}
    json.dump(res, open(os.path.join(out, name + '.json'), 'w', encoding='utf-8', newline='\n'), ensure_ascii=False, indent=1)
    print(json.dumps(res, ensure_ascii=False))
    if n2 != 0 or mirror:
        sys.exit(1)


if __name__ == '__main__':
    main()
