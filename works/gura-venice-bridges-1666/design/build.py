# 產生全部（gura-venice-bridges-1666；Blocksail TASK-1291 的三座橋；骨架抄 crest-waterside-01m/design/build.py）：python -I -X utf8 -B build.py <design 資料夾> [key …]
#   ⇒ masks/<作品 id>.vox.txt（x,y,z,color，排好序）、sheets/<key>.png（圖紙）、manifest.json（apply.py 照它下 CLI：框、標籤、固定點、關聯、繩）、verify.json（讀數）。
# 一座橋 ＝ 一件組裝件 <ROOT>-<key>：每一層一件子作品（body、roof、會動的 leaf-a／leaf-b），用關聯擺在 0,0,0；橋身那一條關聯帶城牆模組的 meta（bridges.py），
#   會動的橋板那一條帶旋轉件的 meta（spin=bridge）。決定論：同一份程式 ⇒ 逐位元組相同。
import sys, os, json, hashlib
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import numpy as np
from scipy import ndimage
import bridges
from bridges import *                                                  # noqa: F401,F403

ROOT = 'gura-venice-bridges-1666'


def wid(*a):
    return '-'.join([ROOT] + list(a))


def dump(path, cells):
    with open(path, 'w', encoding='utf-8', newline='\n') as f:
        for k in sorted(cells):
            f.write('%d,%d,%d,%d\n' % (k[0], k[1], k[2], cells[k]))
    return hashlib.md5(open(path, 'rb').read()).hexdigest()


def structure(cells, dims):
    """元件數（6 連通）、封閉空腔格數、沒碰到 z 0 的元件格數（會動的橋板另算：它們本來就懸著）。"""
    if not cells:
        return 0, 0, []
    a = np.zeros(dims, bool)
    for k in cells:
        a[k] = True
    lab, n = ndimage.label(a)
    cav = int((ndimage.binary_fill_holes(a) & ~a).sum())
    ground = set(np.unique(lab[:, :, 0])) - {0}
    fl = [int((lab == i).sum()) for i in range(1, n + 1) if i not in ground]
    return int(n), cav, fl


def bbox(cells):
    xs = [k[0] for k in cells]; ys = [k[1] for k in cells]; zs = [k[2] for k in cells]
    return [min(xs), min(ys), min(zs), max(xs) + 1, max(ys) + 1, max(zs) + 1]


def rope_list(M):
    f = lambda v: ','.join('%g' % round(c, 3) for c in v)
    return [{'name': R['name'], 'from': f(R['a']), 'to': f(R['b']), 'color': '#%02x%02x%02x' % rgb(R['color']), 'thickness': R['thick'], 'slack': R['slack']}
            for R in getattr(M, 'ropes', [])]


def main():
    D = os.path.abspath(sys.argv[1])
    want = set(sys.argv[2:])
    man_p, ver_p = os.path.join(D, 'manifest.json'), os.path.join(D, 'verify.json')
    man = json.load(open(man_p, encoding='utf-8')) if os.path.exists(man_p) else {'root': ROOT, 'mpv': MPV, 'works': {}}
    ver = json.load(open(ver_p, encoding='utf-8')) if os.path.exists(ver_p) else {}
    for fn in bridges.ALL:
        if want and fn.__name__ not in want:
            continue
        B = fn()
        key, M = B['key'], B['M']
        pw = wid(key)
        links, lv = [], {}
        for ln, lname in B['layers'].items():
            cells = M.layer(ln)
            if not cells:
                continue
            w = wid(key, ln)
            md5 = dump(os.path.join(D, 'masks', w + '.vox.txt'), cells)
            n, cav, fl = structure(cells, (M.X, M.Y, M.Z))
            man['works'][w] = {'title': '%s｜%s' % (B['title'].split('（')[0], lname), 'size': [M.X, M.Y, M.Z], 'tags': 'sub', 'mask': w + '.vox.txt',
                               'anchors': {}, 'links': [], 'models': [], 'order': 1, 'mpv': MPV}
            lv[w] = {'voxels': len(cells), 'components': n, 'cavity': cav, 'floating': sum(fl), 'bbox': bbox(cells), 'md5': md5}
            meta = B['meta'] if ln == 'body' else B.get('layer_meta', {}).get(ln, {'part': ln})
            links.append({'name': lname, 'source': w, 'at': [0, 0, 0], 'turn': 0, 'mirror': '', 'recolor': {}, 'meta': meta})
        comp = {k: v[1] for k, v in M.cells.items()}
        dump(os.path.join(D, 'masks', pw + '.composite.txt'), comp)
        man['works'][pw] = {'title': B['title'], 'size': [M.X, M.Y, M.Z], 'tags': 'bridge,venice', 'mask': None, 'expect': pw + '.composite.txt',
                            'anchors': {k: list(v) for k, v in M.anchors.items()}, 'links': links, 'models': [], 'order': 2, 'ropes': rope_list(M), 'flags': [], 'mpv': MPV}
        n, cav, fl = structure(comp, (M.X, M.Y, M.Z))
        ver[pw] = {'size': [M.X, M.Y, M.Z], 'oob': M.oob, 'voxels': len(comp), 'components': n, 'floating': fl, 'cavity': cav, 'meta': B['meta'],
                   'ropes': len(getattr(M, 'ropes', [])), 'layers': lv}
        sheet(comp, (M.X, M.Y, M.Z), os.path.join(D, 'sheets', key + '.png'), '%s｜%d 格｜框 %s' % (B['title'].split('（')[0], len(comp), 'x'.join(str(v) for v in (M.X, M.Y, M.Z))), px=2)
        print(key, json.dumps({k: v for k, v in ver[pw].items() if k != 'layers'}, ensure_ascii=False))
        for w, v in lv.items():
            print('   ', w, v)
    json.dump(man, open(man_p, 'w', encoding='utf-8', newline='\n'), ensure_ascii=False, indent=1, sort_keys=True)
    json.dump(ver, open(ver_p, 'w', encoding='utf-8', newline='\n'), ensure_ascii=False, indent=1, sort_keys=True)


if __name__ == '__main__':
    main()
