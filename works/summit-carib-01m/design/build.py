# 產生全部（TASK-0757；照 summit-bourg-fr-01m/design/build.py 的做法）：python -I -X utf8 -B build.py <design 資料夾> [key …]
#   ⇒ masks/<作品 id>.vox.txt（x,y,z,color，排好序）、sheets/<key>.png（新圖紙：俯視＋正立面＋側立面）、
#      manifest.json（每件作品：框、標籤、固定點、關聯、外部模型 —— apply.py 照它下 CLI）、verify.json（讀數）。
# 決定論：同一份程式 ⇒ 逐位元組相同（⛔ random、⛔ 時間）。
# 借來的部件（法式套件的貨門、氣窗）不在這裡建作品：關聯直接指到 summit-bourg-fr-01m-part-*。
import sys, os, json, hashlib
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import numpy as np
from scipy import ndimage
from carib import *
import parts as PT
import houses
import public

ROOT = 'summit-carib-01m'
STYLE = 'carib'


def wid(*a):
    return '-'.join([ROOT] + list(a))


def dump(path, cells):
    with open(path, 'w', encoding='utf-8', newline='\n') as f:
        for k in sorted(cells):
            f.write('%d,%d,%d,%d\n' % (k[0], k[1], k[2], cells[k]))
    return hashlib.md5(open(path, 'rb').read()).hexdigest()


def structure(cells, dims, floating=False):
    """元件數（6 連通）、封閉空腔格數；floating ⇒ 另回「沒碰到地面（z 0）的元件」的格數清單。"""
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


def boxes(links, sizes):
    mx = [0, 0, 0]
    for L in links:
        W, H, Dz = sizes[L['source']]
        if L['turn'] in (90, 270):
            W, H = H, W
        assert min(L['at']) >= 0, L
        mx = [max(mx[0], L['at'][0] + W), max(mx[1], L['at'][1] + H), max(mx[2], L['at'][2] + Dz)]
    return mx


def main():
    D = os.path.abspath(sys.argv[1])
    want = set(sys.argv[2:])
    os.makedirs(os.path.join(D, 'masks'), exist_ok=True)
    os.makedirs(os.path.join(D, 'sheets'), exist_ok=True)
    man_p = os.path.join(D, 'manifest.json')
    ver_p = os.path.join(D, 'verify.json')
    man = json.load(open(man_p, encoding='utf-8')) if os.path.exists(man_p) else {'root': ROOT, 'works': {}}
    ver = json.load(open(ver_p, encoding='utf-8')) if os.path.exists(ver_p) else {}
    sizes = {}

    # ── 通用部件（自己做的才建作品；借來的只記框）──
    for pid, P in PT.all_parts().items():
        if P.get('src'):
            sizes[P['src']] = list(P['dims'])
            continue
        w = wid('part', pid)
        sizes[w] = list(P['dims'])
        md5 = dump(os.path.join(D, 'masks', w + '.vox.txt'), P['cells'])
        n, cav = structure(P['cells'], P['dims'])
        man['works'][w] = {'title': P['title'], 'size': list(P['dims']), 'tags': 'sub,part', 'mask': w + '.vox.txt',
                           'anchors': {k: list(v) for k, v in P['anchors'].items()}, 'links': [], 'models': [], 'order': 0}
        ver[w] = {'voxels': len(P['cells']), 'components': n, 'cavity': cav, 'md5': md5}

    # ── 建築 ──
    for fn in houses.ALL + public.ALL:
        B = fn()
        key = B['key']
        if want and key not in want:
            continue
        M = B['M']
        pw = wid(key)
        links, layer_ver = [], {}
        meta_b = {'kind': 'building', 'use': B['use'], 'style': STYLE, 'lot': '%d,%d' % B['lot'], 'base': 4, 'variant': key.split('-', 1)[1] if '-' in key else 'a'}
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
            links.append({'name': lname, 'source': w, 'at': [0, 0, 0], 'turn': 0, 'mirror': '', 'recolor': {},
                          'meta': meta_b if ln == 'body' else {'part': ln}})
        for L in M.links:
            src = L['part'] if L['part'].startswith('summit-') else wid('part', L['part'])
            links.append({'name': L['name'], 'source': src, 'at': L['at'], 'turn': L['turn'], 'mirror': L['mirror'],
                          'recolor': {str(a): b for a, b in L.get('recolor', {}).items()}, 'meta': {'part': src.rsplit('-part-', 1)[1]}})
        comp, clash = composite(M)
        dump(os.path.join(D, 'masks', pw + '.composite.txt'), comp)
        man['works'][pw] = {'title': B['title'], 'size': [M.X, M.Y, M.Z], 'tags': 'building,' + STYLE, 'mask': None, 'expect': pw + '.composite.txt',
                            'anchors': {k: list(v) for k, v in M.anchors.items()}, 'links': links, 'models': M.models, 'order': 2,
                            'flags': B.get('flags', [])}
        sizes[pw] = [M.X, M.Y, M.Z]
        dx, dy, dz = M.anchors['door']
        door_ok = (dx, dy, dz) not in comp and (dz == 0 or (dx, dy, dz - 1) in comp) and (dx, dy, dz + 1) not in comp
        n, cav, fl = structure(comp, (M.X, M.Y, M.Z), floating=True)
        ver[pw] = {'lot': list(B['lot']), 'size': [M.X, M.Y, M.Z], 'oob': M.oob, 'part_clash': clash, 'composite_voxels': len(comp),
                   'composite_components': n, 'composite_floating': fl, 'composite_cavity': cav, 'bbox': bbox(comp), 'door': list(M.anchors['door']), 'door_ok': door_ok,
                   'links': len(links), 'models': len(M.models), 'layers': layer_ver}
        sheet(comp, (M.X, M.Y, M.Z), os.path.join(D, 'sheets', key + '.png'),
              '%s｜地塊 %d × %d m｜%d 格（組好）｜框 %s' % (B['title'], B['lot'][0], B['lot'][1], len(comp), 'x'.join(str(v) for v in (M.X, M.Y, M.Z))), px=3)
        print(key, json.dumps({k: v for k, v in ver[pw].items() if k != 'layers'}, ensure_ascii=False))
        for w, lv in layer_ver.items():
            print('   ', w, lv)

    def rd_comp(w):
        out = {}
        for l in open(os.path.join(D, 'masks', w + '.composite.txt'), encoding='utf-8'):
            a = l.split(',')
            out[(int(a[0]), int(a[1]), int(a[2]))] = int(a[3])
        return out

    # ── 配色變化：一件組裝件、一條關聯指到原型＋替換色（TASK-0584）⇒ 不另存格子 ──
    if not want or 'variants' in want:
        for key, base, rc, title in VARIANTS:
            bw, pw = wid(base), wid(key)
            B0 = man['works'][bw]
            body = [L for L in B0['links'] if L['meta'].get('kind') == 'building'][0]
            meta = dict(body['meta'], variant=key.split('-', 1)[1])
            comp = {k: rc.get(c, c) for k, c in rd_comp(bw).items()}
            dump(os.path.join(D, 'masks', pw + '.composite.txt'), comp)
            man['works'][pw] = {'title': title, 'size': B0['size'], 'tags': 'building,' + STYLE, 'mask': None, 'expect': pw + '.composite.txt',
                                'anchors': dict(B0['anchors']), 'links': [{'name': '本體', 'source': bw, 'at': [0, 0, 0], 'turn': 0, 'mirror': '',
                                                                          'recolor': {str(a): b for a, b in rc.items()}, 'meta': meta}],
                                'models': [], 'order': 3, 'flags': B0.get('flags', [])}
            ver[pw] = {'base': bw, 'recolor': {str(a): b for a, b in rc.items()}, 'composite_voxels': len(comp),
                       'changed': sum(1 for c in rd_comp(bw).values() if c in rc)}
            sheet(comp, tuple(B0['size']), os.path.join(D, 'sheets', key + '.png'), title, px=3)
            print(pw, json.dumps(ver[pw], ensure_ascii=False))

    # ── 任務作品（樣板街）：北排面向街（turn 0）、南排背向（turn 180）──
    if not want or 'street' in want:
        links, comp = [], {}
        for w0, W0 in man['works'].items():
            sizes.setdefault(w0, W0['size'])

        def put(w, at, turn, name):
            W0 = man['works'][w]
            links.append({'name': name, 'source': w, 'at': list(at), 'turn': turn, 'mirror': '', 'recolor': {}, 'meta': {}})
            for k, c in rd_comp(w).items():
                comp.setdefault(xform(k[0], k[1], k[2], tuple(W0['size']), turn, '', at), c)
        x = 40
        for key in NORTH:
            put(wid(key), (x, STREET_Y1, 0), 0, key)
            x += man['works'][wid(key)]['size'][0]
        x = 40
        for key in SOUTH:
            S = man['works'][wid(key)]['size']
            put(wid(key), (x, STREET_Y0 - S[1], 0), 180, key)
            x += S[0] + 20
        X, Yb, Zb = boxes(links, sizes)
        X, Yb = X + 40, Yb + 40
        dump(os.path.join(D, 'masks', ROOT + '.composite.txt'), comp)
        man['works'][ROOT] = {'title': '加勒比海風格城鎮建築套件（風格 carib；0.1 m）—— 樣板街：住宅三型＋配色變化、酒館、倉庫｜小教堂、長官的屋子、砲台',
                              'size': [X, Yb, Zb], 'tags': 'town', 'mask': None, 'expect': ROOT + '.composite.txt', 'anchors': {}, 'links': links,
                              'models': [], 'order': 4, 'root': True}
        ver[ROOT] = {'size': [X, Yb, Zb], 'composite_voxels': len(comp), 'links': len(links)}
        sheet(comp, (X, Yb, Zb), os.path.join(D, 'sheets', 'street.png'), '樣板街（北排面向街、南排背向）｜%d 格' % len(comp), px=1)
        print(ROOT, json.dumps(ver[ROOT], ensure_ascii=False))

    json.dump(man, open(man_p, 'w', encoding='utf-8', newline='\n'), ensure_ascii=False, indent=1, sort_keys=True)
    json.dump(ver, open(ver_p, 'w', encoding='utf-8', newline='\n'), ensure_ascii=False, indent=1, sort_keys=True)


# 配色變化（有史料的只有刷石灰白與沒刷的泥牆 —— 17 世紀的遮板、門的漆色查不到，⛔ 不編；references/README.md §8）
VARIANTS = [('house-a2', 'house-a', {BOARD: LIME}, '住宅 A2（A 的配色變化：板牆刷石灰白 —— Saba「刷得很白」；替換色，不另存格子）'),
            ('house-b2', 'house-b', {LIME: EARTH_W}, '住宅 B2（B 的配色變化：沒刷石灰的泥牆（肥土＋牛糞的本色）；替換色，不另存格子）'),
            ('house-c2', 'house-c', {RUBBLE: LIME, RUBBLE_D: LIME, MORTAR: LIME}, '住宅 C2（C 的配色變化：一樓石牆刷白 —— St Thomas「照荷蘭方式刷白」；替換色，不另存格子）'),
            ('house-a2-s', 'house-a-s', {BOARD: LIME}, '住宅 A2 淺版（A 淺版的配色變化：板牆刷石灰白；替換色，不另存格子）'),   # 淺版（8 × 10，TASK-0742 轉角）照同一套替換色
            ('house-b2-s', 'house-b-s', {LIME: EARTH_W}, '住宅 B2 淺版（B 淺版的配色變化：沒刷石灰的泥牆；替換色，不另存格子）'),
            ('house-c2-s', 'house-c-s', {RUBBLE: LIME, RUBBLE_D: LIME, MORTAR: LIME}, '住宅 C2 淺版（C 淺版的配色變化：一樓石牆刷白；替換色，不另存格子）')]
NORTH = ['house-a', 'house-b', 'house-c', 'house-a2', 'house-b2', 'house-c2', 'tavern', 'warehouse', 'commandant']
SOUTH = ['church', 'battery']
STREET_Y0, STREET_Y1 = 300, 360


if __name__ == '__main__':
    main()
