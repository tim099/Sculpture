# 產生全部（TASK-0893；抄自 crest-housing-density-01m/design/build.py ⇐ summit-bourg-fr-01m）：python -I -X utf8 -B build.py <design 資料夾> [key …]
#   ⇒ masks/<作品 id>.vox.txt（x,y,z,color，排好序）、sheets/<key>.png（圖紙：俯視＋正立面＋側立面）、<key>-build.png（施工階段）、
#      manifest.json（每件作品：框、標籤、固定點、關聯、外部模型 —— apply.py 照它下 CLI）、verify.json（讀數）。
# 決定論：同一份程式 ⇒ 逐位元組相同（⛔ random、⛔ 時間）。
# 部件是這一套自己的（bzparts.py）⇒ 建成 <ROOT>-part-<id>；房子用關聯擺。
# 作品 id：<ROOT>-roman-<key>（例 kaguya-cpl-housing-1453-roman-house-m-a）；牆身、屋頂、陽台 ＝ 再加 -body／-roof／-gallery。
import sys, os, json, hashlib
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import numpy as np
from scipy import ndimage
from common import *
import bzparts
import roman_dense
import roman_low

ROOT = roman_dense.ROOT
STYLE = 'roman'
# 施工階段（同 crest 那兩套，TASK-0895）：每一條關聯的 meta 帶 build0／build1（工程進度 0～1）＋ sweep（'z' ＝ 照高度由下往上長）。
STAGE = {'body': (0.0, 0.6), 'gallery': (0.45, 0.8), 'roof': (0.6, 0.9)}
PART_STAGE0 = 0.85
MODEL_STAGE = 1.0
STAGE_SHOTS = (0.1, 0.25, 0.5, 0.75, 1.0)


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


def rd_comp(path):
    out = {}
    for l in open(path, encoding='utf-8'):
        a = l.split(',')
        out[(int(a[0]), int(a[1]), int(a[2]))] = int(a[3])
    return out


def stage_t(M):
    T = {}
    for ln, (b0, b1) in STAGE.items():
        cells = M.layer(ln)
        if not cells:
            continue
        zs = [k[2] for k in cells]
        z0, h = min(zs), max(1, max(zs) - min(zs))
        for k in cells:
            T[k] = b0 + (b1 - b0) * (k[2] - z0) / h
    for L in M.links:
        for k in L['cells']:
            T.setdefault(k, PART_STAGE0)
    return T


def stage_sheet(M, B, path):
    """施工分格圖：正立面＋俯視照 STAGE_SHOTS 一格一格排；外部模型不畫。"""
    from PIL import Image, ImageDraw, ImageFont
    comp, _ = composite(M)
    T = stage_t(M)
    X, Y, Z = M.X, M.Y, M.Z
    px = 2
    try:
        font = ImageFont.truetype('C:/Windows/Fonts/msjh.ttc', 16)
    except Exception:
        font = None
    panels = []
    for p in STAGE_SHOTS:
        im = Image.new('RGB', (X, Z + 8 + Y), (232, 228, 214))
        pf = im.load()
        fr, tp = {}, {}
        for k, c in comp.items():
            if T.get(k, 1.0) > p + 1e-9:
                continue
            x, y, z = k
            if (x, z) not in fr or y < fr[(x, z)][0]:
                fr[(x, z)] = (y, c)
            if (x, y) not in tp or z > tp[(x, y)][0]:
                tp[(x, y)] = (z, c)
        for (x, z), (y, c) in fr.items():
            f = 1.0 - 0.45 * y / max(1, Y)
            r, g, b = rgb(c)
            pf[x, Z - 1 - z] = (int(r * f), int(g * f), int(b * f))
        for (x, y), (z, c) in tp.items():
            f = 0.55 + 0.45 * z / max(1, Z)
            r, g, b = rgb(c)
            pf[x, Z + 8 + y] = (int(r * f), int(g * f), int(b * f))
        panels.append((p, im))
    W = len(panels) * (X * px + 30) + 30
    H = (Z + 8 + Y) * px + 80
    out = Image.new('RGB', (W, H), (250, 248, 240))
    d = ImageDraw.Draw(out)
    d.text((20, 10), '%s｜%s｜施工階段（上：正立面、下：俯視；meta build0／build1／sweep）' % (STYLE, B['title'].split('（')[0]), fill=(30, 30, 30), font=font)
    xo = 30
    for p, im in panels:
        out.paste(im.resize((X * px, (Z + 8 + Y) * px), Image.NEAREST), (xo, 60))
        d.text((xo, 38), '%d%%' % round(p * 100), fill=(60, 60, 60), font=font)
        xo += X * px + 30
    out.save(path)


def main():
    D = os.path.abspath(sys.argv[1])
    want = set(sys.argv[2:])
    os.makedirs(os.path.join(D, 'masks'), exist_ok=True)
    os.makedirs(os.path.join(D, 'sheets'), exist_ok=True)
    man_p = os.path.join(D, 'manifest.json')
    ver_p = os.path.join(D, 'verify.json')
    man = json.load(open(man_p, encoding='utf-8')) if os.path.exists(man_p) else {'root': ROOT, 'works': {}}
    ver = json.load(open(ver_p, encoding='utf-8')) if os.path.exists(ver_p) else {}

    # ── 部件 ──
    for pid, P in bzparts.all_parts().items():
        w = wid('part', pid)
        md5 = dump(os.path.join(D, 'masks', w + '.vox.txt'), P['cells'])
        n, cav = structure(P['cells'], P['dims'])
        man['works'][w] = {'title': P['title'], 'size': list(P['dims']), 'tags': 'sub,part', 'mask': w + '.vox.txt',
                           'anchors': {k: list(v) for k, v in P['anchors'].items()}, 'links': [], 'models': [], 'order': 0}
        ver[w] = {'voxels': len(P['cells']), 'components': n, 'cavity': cav, 'md5': md5}
        sheet(P['cells'], P['dims'], os.path.join(D, 'sheets', 'part-' + pid + '.png'), P['title'], px=8)

    # ── 房子 ──
    for fn in roman_low.ALL + roman_dense.ALL:
        B = fn()
        key = B['key']
        if want and key not in want:
            continue
        M = B['M']
        pw = wid(STYLE, key)
        links, layer_ver = [], {}
        meta_b = {'kind': 'building', 'use': B['use'], 'style': STYLE, 'lot': '%d,%d' % B['lot'], 'base': 4, 'variant': B['variant'],
                  'level': B['level'], 'live': B['live']}
        for ln, lname in B['layers'].items():
            cells = M.layer(ln)
            if not cells:
                continue
            w = wid(STYLE, key, ln)
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
            pn = L['part'].rsplit('-part-', 1)[1]
            links.append({'name': L['name'], 'source': L['part'], 'at': L['at'], 'turn': L['turn'], 'mirror': L['mirror'],
                          'recolor': {str(a): b for a, b in L.get('recolor', {}).items()}, 'meta': {'part': pn, 'build0': PART_STAGE0, 'build1': PART_STAGE0}})
        for m in M.models:
            m['meta'] = dict(m['meta'], build0=MODEL_STAGE, build1=MODEL_STAGE)
        comp, clash = composite(M)
        dump(os.path.join(D, 'masks', pw + '.composite.txt'), comp)
        man['works'][pw] = {'title': B['title'], 'size': [M.X, M.Y, M.Z], 'tags': 'building,' + STYLE, 'mask': None, 'expect': pw + '.composite.txt',
                            'anchors': {k: list(v) for k, v in M.anchors.items()}, 'links': links, 'models': M.models, 'order': 2}
        dx, dy, dz = M.anchors['door']
        door_ok = (dx, dy, dz) not in comp and (dz == 0 or (dx, dy, dz - 1) in comp) and (dx, dy, dz + 1) not in comp
        n, cav, fl = structure(comp, (M.X, M.Y, M.Z), floating=True)
        ver[pw] = {'lot': list(B['lot']), 'level': B['level'], 'live': B['live'], 'size': [M.X, M.Y, M.Z], 'oob': M.oob, 'part_clash': clash,
                   'composite_voxels': len(comp), 'composite_components': n, 'composite_floating': fl, 'composite_cavity': cav, 'bbox': bbox(comp),
                   'door': list(M.anchors['door']), 'door_ok': door_ok, 'links': len(links), 'models': len(M.models), 'layers': layer_ver}
        sheet(comp, (M.X, M.Y, M.Z), os.path.join(D, 'sheets', STYLE + '-' + key + '.png'),
              '%s｜%s｜地塊 %d × %d m｜住 %d 人｜%d 格（組好）｜框 %s' % (STYLE, B['title'], B['lot'][0], B['lot'][1], B['live'], len(comp),
                                                           'x'.join(str(v) for v in (M.X, M.Y, M.Z))), px=3)
        stage_sheet(M, B, os.path.join(D, 'sheets', STYLE + '-' + key + '-build.png'))
        print(pw, json.dumps({k: v for k, v in ver[pw].items() if k != 'layers'}, ensure_ascii=False))
        for w, lv in layer_ver.items():
            print('   ', w, lv)

    # ── 配色變化：一件組裝件、一條關聯指到原型＋替換色 ⇒ 不另存格子 ──
    for key, base, rc, title in roman_low.VARIANTS + roman_dense.VARIANTS:
        if want and key not in want and 'variants' not in want:
            continue
        bw, pw = wid(STYLE, base), wid(STYLE, key)
        B0 = man['works'][bw]
        body = [L for L in B0['links'] if L['meta'].get('kind') == 'building'][0]
        meta = dict(body['meta'], variant=key.split('-', 1)[1])
        base_comp = rd_comp(os.path.join(D, 'masks', bw + '.composite.txt'))
        comp = {k: rc.get(c, c) for k, c in base_comp.items()}
        dump(os.path.join(D, 'masks', pw + '.composite.txt'), comp)
        man['works'][pw] = {'title': title, 'size': B0['size'], 'tags': 'building,' + STYLE, 'mask': None, 'expect': pw + '.composite.txt',
                            'anchors': dict(B0['anchors']), 'links': [{'name': '本體', 'source': bw, 'at': [0, 0, 0], 'turn': 0, 'mirror': '',
                                                                      'recolor': {str(a): b for a, b in rc.items()}, 'meta': meta}],
                            'models': [], 'order': 3}
        ver[pw] = {'base': bw, 'recolor': {str(a): b for a, b in rc.items()}, 'composite_voxels': len(comp),
                   'changed': sum(1 for c in base_comp.values() if c in rc)}
        sheet(comp, tuple(B0['size']), os.path.join(D, 'sheets', STYLE + '-' + key + '.png'), STYLE + '｜' + title, px=3)
        print(pw, json.dumps(ver[pw], ensure_ascii=False))

    # ── 任務作品（樣板街）：第一排低密度、第二排照升級的路 中 2×3｜中 3×3｜高 3×3｜高 4×4，第三排配色變化 ──
    if not want or 'street' in want:
        links, comp = [], {}

        def put(w, size, cells, at, name):
            links.append({'name': name, 'source': w, 'at': list(at), 'turn': 0, 'mirror': '', 'recolor': {}, 'meta': {}})
            for k, c in cells.items():
                comp.setdefault((k[0] + at[0], k[1] + at[1], k[2] + at[2]), c)
            return size
        y = 40
        for row in (('house-a', 'house-a2', 'house-b', 'house-b2', 'house-c', 'house-c2', 'house-a-xs', 'house-b-xs', 'house-c-xs'),
                    ('house-m-b', 'house-m-a', 'house-h-b', 'house-h-a'), ('house-m-b2', 'house-m-a2', 'house-h-b2', 'house-h-a2')):
            x = 40
            for key in row:
                w = wid(STYLE, key)
                S = put(w, man['works'][w]['size'], rd_comp(os.path.join(D, 'masks', w + '.composite.txt')), (x, y, 0), key)
                x += S[0] + 40
            y += 160 + 60
        X = max(l['at'][0] + man['works'][l['source']]['size'][0] for l in links) + 40
        Yb = y
        Zb = max(max(k[2] for k in comp) + 1, max(man['works'][l['source']]['size'][2] for l in links))   # 關聯要整件放得進框（引擎擋）
        dump(os.path.join(D, 'masks', ROOT + '.composite.txt'), comp)
        man['works'][ROOT] = {'title': '君士坦丁堡 1453 的中、高密度住宅（TASK-0893；0.1 m）—— 樣板街：第一排低密度三型＋配色、小版；第二排照升級的路 中 2×3（原地升級）｜中 3×3｜高 3×3（原地升級）｜高 4×4；第三排是配色變化',
                              'size': [X, Yb, Zb], 'tags': 'town', 'mask': None, 'expect': ROOT + '.composite.txt', 'anchors': {}, 'links': links,
                              'models': [], 'order': 4, 'root': True}
        ver[ROOT] = {'size': [X, Yb, Zb], 'composite_voxels': len(comp), 'links': len(links)}
        sheet(comp, (X, Yb, Zb), os.path.join(D, 'sheets', 'street.png'), '樣板街（roman）：低密度三型＋配色、小版｜中 2×3｜中 3×3｜高 3×3｜高 4×4｜配色變化｜%d 格' % len(comp), px=1)
        print(ROOT, json.dumps(ver[ROOT], ensure_ascii=False))

    json.dump(man, open(man_p, 'w', encoding='utf-8', newline='\n'), ensure_ascii=False, indent=1, sort_keys=True)
    json.dump(ver, open(ver_p, 'w', encoding='utf-8', newline='\n'), ensure_ascii=False, indent=1, sort_keys=True)


if __name__ == '__main__':
    main()
