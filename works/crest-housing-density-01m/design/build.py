# 產生全部（TASK-0893；抄自 summit-bourg-fr-01m/design/build.py）：python -I -X utf8 -B build.py <design 資料夾> [key …]
#   ⇒ masks/<作品 id>.vox.txt（x,y,z,color，排好序）、sheets/<key>.png（圖紙：俯視＋正立面＋側立面）、
#      manifest.json（每件作品：框、標籤、固定點、關聯、外部模型 —— apply.py 照它下 CLI）、verify.json（讀數）。
# 決定論：同一份程式 ⇒ 逐位元組相同（⛔ random、⛔ 時間）。
# 部件全部借 summit 兩套（common.py）⇒ 這裡不建部件作品；關聯的 source 一律是原作品的 id。
# 作品 id：<ROOT>-<風格>-<key>（例 crest-housing-density-01m-fr-house-m-a）；牆身、屋頂、廊 ＝ 再加 -body／-roof／-gallery。
import sys, os, json, hashlib
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import numpy as np
from scipy import ndimage
from common import *
import fr_dense
import carib_dense

ROOT = 'crest-housing-density-01m'
STYLES = [('fr', fr_dense, FR_ROOT), ('carib', carib_dense, CARIB_ROOT)]


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


def part_src(p):
    """關聯的 source：common.put_part 已經換成原作品 id；summit fr houses.py 的工具（廚房、院門）擺的是短名 ⇒ 補上 fr 的前綴。"""
    return p if '-part-' in p else FR_ROOT + '-part-' + p


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
    man_p = os.path.join(D, 'manifest.json')
    ver_p = os.path.join(D, 'verify.json')
    man = json.load(open(man_p, encoding='utf-8')) if os.path.exists(man_p) else {'root': ROOT, 'works': {}}
    ver = json.load(open(ver_p, encoding='utf-8')) if os.path.exists(ver_p) else {}
    sizes = {}

    for style, mod, _ in STYLES:
        for fn in mod.ALL:
            B = fn()
            key = B['key']
            if want and (style + '-' + key) not in want:
                continue
            M = B['M']
            pw = wid(style, key)
            links, layer_ver = [], {}
            meta_b = {'kind': 'building', 'use': B['use'], 'style': style, 'lot': '%d,%d' % B['lot'], 'base': 4, 'variant': B['variant'],
                      'level': B['level'], 'live': B['live']}
            for ln, lname in B['layers'].items():
                cells = M.layer(ln)
                if not cells:
                    continue
                w = wid(style, key, ln)
                md5 = dump(os.path.join(D, 'masks', w + '.vox.txt'), cells)
                n, cav = structure(cells, (M.X, M.Y, M.Z))
                man['works'][w] = {'title': '%s｜%s' % (B['title'].split('（')[0], lname), 'size': [M.X, M.Y, M.Z], 'tags': 'sub', 'mask': w + '.vox.txt',
                                   'anchors': {}, 'links': [], 'models': [], 'order': 1}
                layer_ver[w] = {'voxels': len(cells), 'components': n, 'cavity': cav, 'bbox': bbox(cells), 'md5': md5}
                links.append({'name': lname, 'source': w, 'at': [0, 0, 0], 'turn': 0, 'mirror': '', 'recolor': {},
                              'meta': meta_b if ln == 'body' else {'part': ln}})
            for L in M.links:
                src = part_src(L['part'])
                links.append({'name': L['name'], 'source': src, 'at': L['at'], 'turn': L['turn'], 'mirror': L['mirror'],
                              'recolor': {str(a): b for a, b in L.get('recolor', {}).items()}, 'meta': {'part': src.rsplit('-part-', 1)[1]}})
            comp, clash = composite(M)
            dump(os.path.join(D, 'masks', pw + '.composite.txt'), comp)
            man['works'][pw] = {'title': B['title'], 'size': [M.X, M.Y, M.Z], 'tags': 'building,' + style, 'mask': None, 'expect': pw + '.composite.txt',
                                'anchors': {k: list(v) for k, v in M.anchors.items()}, 'links': links, 'models': M.models, 'order': 2}
            # 讀數：門口固定點要是空氣、腳下有東西；框外 0；部件撞格 0
            dx, dy, dz = M.anchors['door']
            door_ok = (dx, dy, dz) not in comp and (dz == 0 or (dx, dy, dz - 1) in comp) and (dx, dy, dz + 1) not in comp
            n, cav, fl = structure(comp, (M.X, M.Y, M.Z), floating=True)
            ver[pw] = {'lot': list(B['lot']), 'level': B['level'], 'live': B['live'], 'size': [M.X, M.Y, M.Z], 'oob': M.oob, 'part_clash': clash,
                       'composite_voxels': len(comp), 'composite_components': n, 'composite_floating': fl, 'composite_cavity': cav, 'bbox': bbox(comp),
                       'door': list(M.anchors['door']), 'door_ok': door_ok, 'links': len(links), 'models': len(M.models), 'layers': layer_ver}
            sheet(comp, (M.X, M.Y, M.Z), os.path.join(D, 'sheets', style + '-' + key + '.png'),
                  '%s｜%s｜地塊 %d × %d m｜住 %d 人｜%d 格（組好）｜框 %s' % (style, B['title'], B['lot'][0], B['lot'][1], B['live'], len(comp),
                                                               'x'.join(str(v) for v in (M.X, M.Y, M.Z))), px=3)
            print(pw, json.dumps({k: v for k, v in ver[pw].items() if k != 'layers'}, ensure_ascii=False))
            for w, lv in layer_ver.items():
                print('   ', w, lv)

        # ── 配色變化：一件組裝件、一條關聯指到原型＋替換色（TASK-0584）⇒ 不另存格子 ──
        for key, base, rc, title in mod.VARIANTS:
            if want and (style + '-' + key) not in want and (style + '-variants') not in want:
                continue
            bw, pw = wid(style, base), wid(style, key)
            B0 = man['works'][bw]
            body = [L for L in B0['links'] if L['meta'].get('kind') == 'building'][0]
            meta = dict(body['meta'], variant=key.split('-', 1)[1])
            base_comp = rd_comp(os.path.join(D, 'masks', bw + '.composite.txt'))
            comp = {k: rc.get(c, c) for k, c in base_comp.items()}
            dump(os.path.join(D, 'masks', pw + '.composite.txt'), comp)
            man['works'][pw] = {'title': title, 'size': B0['size'], 'tags': 'building,' + style, 'mask': None, 'expect': pw + '.composite.txt',
                                'anchors': dict(B0['anchors']), 'links': [{'name': '本體', 'source': bw, 'at': [0, 0, 0], 'turn': 0, 'mirror': '',
                                                                          'recolor': {str(a): b for a, b in rc.items()}, 'meta': meta}],
                                'models': [], 'order': 3}
            ver[pw] = {'base': bw, 'recolor': {str(a): b for a, b in rc.items()}, 'composite_voxels': len(comp),
                       'changed': sum(1 for c in base_comp.values() if c in rc)}
            sheet(comp, tuple(B0['size']), os.path.join(D, 'sheets', style + '-' + key + '.png'), style + '｜' + title, px=3)
            print(pw, json.dumps(ver[pw], ensure_ascii=False))

    # ── 任務作品（樣板街）：每一排從左到右 ＝ 現有的低密度住宅（summit 的作品，只關聯不複製）、中密度、中密度配色、高密度、高密度配色；fr 一排、carib 一排 ──
    if not want or 'street' in want:
        links, comp = [], {}
        def put(w, size, cells, at, name):
            links.append({'name': name, 'source': w, 'at': list(at), 'turn': 0, 'mirror': '', 'recolor': {}, 'meta': {}})
            for k, c in cells.items():
                comp.setdefault((k[0] + at[0], k[1] + at[1], k[2] + at[2]), c)
            return size
        y = 40
        for style, mod, sroot in STYLES:
            x = 40
            sman = json.load(open(os.path.join(WORKS, sroot, 'design', 'manifest.json'), encoding='utf-8'))
            low = sroot + ('-house-a' if style == 'fr' else '-house-c')
            S = put(low, sman['works'][low]['size'], rd_comp(os.path.join(WORKS, sroot, 'design', 'masks', low + '.composite.txt')), (x, y, 0), style + '-低密度')
            x += S[0] + 40
            for key in ('house-m-a', 'house-m-a2', 'house-h-a', 'house-h-a2'):
                w = wid(style, key)
                S = put(w, man['works'][w]['size'], rd_comp(os.path.join(D, 'masks', w + '.composite.txt')), (x, y, 0), style + '-' + key)
                x += S[0] + 40
            y += 160 + 60
        X = max(l['at'][0] for l in links) + 200
        Yb = y
        Zb = max(max(k[2] for k in comp) + 1, max(man['works'][l['source']]['size'][2] if l['source'] in man['works'] else 0 for l in links))
        dump(os.path.join(D, 'masks', ROOT + '.composite.txt'), comp)
        man['works'][ROOT] = {'title': '住宅三級密度（TASK-0893；0.1 m）—— 樣板街：每一排 低密度（現有）｜中密度＋配色｜高密度＋配色；上排 fr、下排 carib',
                              'size': [X, Yb, Zb], 'tags': 'town', 'mask': None, 'expect': ROOT + '.composite.txt', 'anchors': {}, 'links': links,
                              'models': [], 'order': 4, 'root': True}
        ver[ROOT] = {'size': [X, Yb, Zb], 'composite_voxels': len(comp), 'links': len(links)}
        sheet(comp, (X, Yb, Zb), os.path.join(D, 'sheets', 'street.png'), '樣板街：低密度（現有）｜中密度＋配色｜高密度＋配色（上 fr、下 carib）｜%d 格' % len(comp), px=1)
        print(ROOT, json.dumps(ver[ROOT], ensure_ascii=False))

    json.dump(man, open(man_p, 'w', encoding='utf-8', newline='\n'), ensure_ascii=False, indent=1, sort_keys=True)
    json.dump(ver, open(ver_p, 'w', encoding='utf-8', newline='\n'), ensure_ascii=False, indent=1, sort_keys=True)


if __name__ == '__main__':
    main()
