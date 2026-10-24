# 產生全部（抄自 kaguya-cpl-housing-1453/design/build.py）：python -I -X utf8 -B build.py <design 資料夾> [key …]
#   ⇒ masks/<作品 id>.vox.txt、sheets/<key>.png（圖紙）、manifest.json（apply.py 照它下 CLI）、verify.json（讀數）。
# 決定論：同一份程式 ⇒ 逐位元組相同。部件全部借（summit-carib-01m 的木板門窗、summit-bourg-fr-01m 的玻璃窗、氣窗、煙囪）⇒ 關聯指回原作品，不建部件作品。
# 作品 id：<ROOT>-<key>（例 kaguya-smallhouse-01m-cabin-4x4-a）；牆身、屋頂、外廊 ＝ 再加 -body／-roof／-gallery。
import sys, os, json, hashlib
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import numpy as np
from scipy import ndimage
import small
from small import *

ROOT = 'kaguya-smallhouse-01m'
SUMMIT_ROOT = 'summit-carib-01m'
STAGE = {'body': (0.0, 0.6), 'gallery': (0.45, 0.8), 'roof': (0.6, 0.9)}   # 施工階段（同 crest、kaguya-cpl-housing-1453）
PART_STAGE0, MODEL_STAGE = 0.85, 1.0


def wid(*a):
    return '-'.join([ROOT] + list(a))


def part_src(pid):
    return pid if pid.startswith('summit-') else SUMMIT_ROOT + '-part-' + pid


def dump(path, cells):
    with open(path, 'w', encoding='utf-8', newline='\n') as f:
        for k in sorted(cells):
            f.write('%d,%d,%d,%d\n' % (k[0], k[1], k[2], cells[k]))
    return hashlib.md5(open(path, 'rb').read()).hexdigest()


def structure(cells, dims, floating=False):
    if not cells:
        return (0, 0, []) if floating else (0, 0)
    a = np.zeros(dims, bool)
    for k in cells:
        a[k] = True
    lab, n = ndimage.label(a)
    cav = int((ndimage.binary_fill_holes(a) & ~a).sum())
    if not floating:
        return int(n), cav
    ground = set(np.unique(lab[:, :, 0])) - {0}
    fl = [int((lab == i).sum()) for i in range(1, n + 1) if i not in ground]
    return int(n), cav, fl


def bbox(cells):
    xs = [k[0] for k in cells]; ys = [k[1] for k in cells]; zs = [k[2] for k in cells]
    return [min(xs), min(ys), min(zs), max(xs) + 1, max(ys) + 1, max(zs) + 1]


def rd_comp(path):
    out = {}
    for l in open(path, encoding='utf-8'):
        a = l.split(',')
        out[(int(a[0]), int(a[1]), int(a[2]))] = int(a[3])
    return out


def main():
    D = os.path.abspath(sys.argv[1])
    want = set(sys.argv[2:])
    os.makedirs(os.path.join(D, 'masks'), exist_ok=True)
    os.makedirs(os.path.join(D, 'sheets'), exist_ok=True)
    man_p, ver_p = os.path.join(D, 'manifest.json'), os.path.join(D, 'verify.json')
    man = json.load(open(man_p, encoding='utf-8')) if os.path.exists(man_p) else {'root': ROOT, 'works': {}}
    ver = json.load(open(ver_p, encoding='utf-8')) if os.path.exists(ver_p) else {}
    keys = []
    for fn in small.ALL:
        B = fn()
        key = B['key']
        keys.append(key)
        if want and key not in want:
            continue
        M = B['M']
        pw = wid(key)
        links, layer_ver = [], {}
        meta_b = {'kind': 'building', 'use': B['use'], 'style': B['style'], 'lot': '%d,%d' % B['lot'], 'base': 4, 'variant': B['variant']}
        for ln, lname in B['layers'].items():
            cells = M.layer(ln)
            if not cells:
                continue
            w = wid(key, ln)
            md5 = dump(os.path.join(D, 'masks', w + '.vox.txt'), cells)
            n, cav = structure(cells, (M.X, M.Y, M.Z))
            man['works'][w] = {'title': '%s｜%s' % (B['title'].split('（')[0], lname), 'size': [M.X, M.Y, M.Z], 'tags': 'sub', 'mask': w + '.vox.txt',
                               'anchors': {}, 'links': [], 'models': [], 'order': 1}
            layer_ver[w] = {'voxels': len(cells), 'components': n, 'cavity': cav, 'bbox': bbox(cells), 'md5': md5}
            b0, b1 = STAGE[ln]
            stg = {'build0': b0, 'build1': b1, 'sweep': 'z'}
            links.append({'name': lname, 'source': w, 'at': [0, 0, 0], 'turn': 0, 'mirror': '', 'recolor': {},
                          'meta': dict(meta_b, **stg) if ln == 'body' else dict({'part': ln}, **stg)})
        for L in M.links:
            src = part_src(L['part'])
            links.append({'name': L['name'], 'source': src, 'at': L['at'], 'turn': L['turn'], 'mirror': L['mirror'],
                          'recolor': {str(a): b for a, b in L.get('recolor', {}).items()}, 'meta': {'part': src.rsplit('-part-', 1)[1], 'build0': PART_STAGE0, 'build1': PART_STAGE0}})
        for m in M.models:
            m['meta'] = dict(m['meta'], build0=MODEL_STAGE, build1=MODEL_STAGE)
        comp, clash = composite(M)
        dump(os.path.join(D, 'masks', pw + '.composite.txt'), comp)
        man['works'][pw] = {'title': B['title'], 'size': [M.X, M.Y, M.Z], 'tags': 'building,' + B['style'], 'mask': None, 'expect': pw + '.composite.txt',
                            'anchors': {k: list(v) for k, v in M.anchors.items()}, 'links': links, 'models': M.models, 'order': 2}
        dx, dy, dz = M.anchors['door']
        door_ok = (dx, dy, dz) not in comp and (dz == 0 or (dx, dy, dz - 1) in comp) and (dx, dy, dz + 1) not in comp
        n, cav, fl = structure(comp, (M.X, M.Y, M.Z), floating=True)
        ver[pw] = {'lot': list(B['lot']), 'style': B['style'], 'use': B['use'], 'size': [M.X, M.Y, M.Z], 'oob': M.oob, 'part_clash': clash,
                   'composite_voxels': len(comp), 'composite_components': n, 'composite_floating': fl, 'composite_cavity': cav, 'bbox': bbox(comp),
                   'door': list(M.anchors['door']), 'door_ok': door_ok, 'links': len(links), 'models': len(M.models), 'layers': layer_ver}
        sheet(comp, (M.X, M.Y, M.Z), os.path.join(D, 'sheets', key + '.png'),
              '%s｜%s｜地塊 %d × %d m｜%d 格（組好）｜框 %s' % (B['style'], B['title'], B['lot'][0], B['lot'][1], len(comp), 'x'.join(str(v) for v in (M.X, M.Y, M.Z))), px=4)
        print(pw, json.dumps({k: v for k, v in ver[pw].items() if k != 'layers'}, ensure_ascii=False))

    # ── 任務作品（樣板街）：一排 a 型小木屋（4 m 深）、一排 b 型、一排 5 m 深的兩型、最後一排其他小建築 ──
    if not want or 'street' in want:
        links, comp = [], {}

        def put(w, cells, at, name):
            links.append({'name': name, 'source': w, 'at': list(at), 'turn': 0, 'mirror': '', 'recolor': {}, 'meta': {}})
            for k, c in cells.items():
                comp.setdefault((k[0] + at[0], k[1] + at[1], k[2] + at[2]), c)
        rows = [[k for k in keys if k.startswith('cabin-') and k.endswith('x4-a')], [k for k in keys if k.startswith('cabin-') and k.endswith('x4-b')],
                [k for k in keys if k.startswith('cabin-') and k.endswith('x5-a')], [k for k in keys if k.startswith('cabin-') and k.endswith('x5-b')],
                [k for k in keys if not k.startswith('cabin-')]]
        y = 20
        for row in rows:
            x, dmax = 20, 0
            for key in row:
                w = wid(key)
                S = man['works'][w]['size']
                put(w, rd_comp(os.path.join(D, 'masks', w + '.composite.txt')), (x, y, 0), key)
                x += S[0] + 20
                dmax = max(dmax, S[1])
            y += dmax + 30
        X = max(l['at'][0] + man['works'][l['source']]['size'][0] for l in links) + 20
        Zb = max(max(k[2] for k in comp) + 1, max(man['works'][l['source']]['size'][2] for l in links))
        dump(os.path.join(D, 'masks', ROOT + '.composite.txt'), comp)
        man['works'][ROOT] = {'title': '小地塊的建築（0.1 m）—— 樣板街：小木屋 4 m 深 a／b、5 m 深 a／b（寬 4～12 m），最後一排小倉庫、小砲台、小酒館、小教堂、英國酒館',
                              'size': [X, y, Zb], 'tags': 'town', 'mask': None, 'expect': ROOT + '.composite.txt', 'anchors': {}, 'links': links,
                              'models': [], 'order': 4, 'root': True}
        ver[ROOT] = {'size': [X, y, Zb], 'composite_voxels': len(comp), 'links': len(links)}
        sheet(comp, (X, y, Zb), os.path.join(D, 'sheets', 'street.png'), '樣板街：小木屋 a／b、4／5 m 深；小倉庫、小砲台、小酒館、小教堂、英國酒館｜%d 格' % len(comp), px=1)
        print(ROOT, json.dumps(ver[ROOT], ensure_ascii=False))

    json.dump(man, open(man_p, 'w', encoding='utf-8', newline='\n'), ensure_ascii=False, indent=1, sort_keys=True)
    json.dump(ver, open(ver_p, 'w', encoding='utf-8', newline='\n'), ensure_ascii=False, indent=1, sort_keys=True)


if __name__ == '__main__':
    main()
