# 產生全部（TASK-0741）：python -I -X utf8 -B build.py <design 資料夾> [key …]
#   ⇒ masks/<作品 id>.vox.txt（x,y,z,color，排好序）、sheets/<key>.png（新圖紙：俯視＋正立面＋側立面）、
#      manifest.json（每件作品：框、標籤、固定點、關聯、外部模型 —— apply.py 照它下 CLI）、verify.json（讀數）。
# 決定論：同一份程式 ⇒ 逐位元組相同（⛔ random、⛔ 時間）。
import sys, os, json, hashlib
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import numpy as np
from scipy import ndimage
from kit import *
import parts as PT
import houses
import public
import walls

ROOT = 'summit-bourg-fr-01m'
STYLE = 'fr'


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


def boxes(links):
    """每條關聯的框（轉過之後）放到 at ⇒ 組裝件至少要多大。"""
    mx = [0, 0, 0]
    for L in links:
        W, H, Dz = MAN['works'][L['source']]['size']
        if L['turn'] in (90, 270):
            W, H = H, W
        assert min(L['at']) >= 0, L
        mx = [max(mx[0], L['at'][0] + W), max(mx[1], L['at'][1] + H), max(mx[2], L['at'][2] + Dz)]
    return mx


def bbox(cells):
    xs = [k[0] for k in cells]; ys = [k[1] for k in cells]; zs = [k[2] for k in cells]
    return [min(xs), min(ys), min(zs), max(xs) + 1, max(ys) + 1, max(zs) + 1]


def main():
    D = os.path.abspath(sys.argv[1])
    want = set(sys.argv[2:])
    os.makedirs(os.path.join(D, 'masks'), exist_ok=True)
    os.makedirs(os.path.join(D, 'sheets'), exist_ok=True)
    man_p = os.path.join(D, 'manifest.json')
    ver_p = os.path.join(D, 'verify.json')
    global MAN
    man = json.load(open(man_p, encoding='utf-8')) if os.path.exists(man_p) else {'root': ROOT, 'works': {}}
    MAN = man
    ver = json.load(open(ver_p, encoding='utf-8')) if os.path.exists(ver_p) else {}

    # ── 通用部件 ──
    for pid, P in PT.all_parts().items():
        w = wid('part', pid)
        md5 = dump(os.path.join(D, 'masks', w + '.vox.txt'), P['cells'])
        n, cav = structure(P['cells'], P['dims'])
        man['works'][w] = {'title': P['title'], 'size': list(P['dims']), 'tags': 'sub,part', 'mask': w + '.vox.txt',
                           'anchors': {k: list(v) for k, v in P['anchors'].items()}, 'links': [], 'models': [], 'order': 0}
        ver[w] = {'voxels': len(P['cells']), 'components': n, 'cavity': cav, 'md5': md5}

    # ── 建築 ──
    builders = houses.ALL + public.ALL
    for i, fn in enumerate(builders):
        if want and fn.__name__.replace('_', '-') not in want:
            continue
        B = fn()
        key = B['key']
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
            links.append({'name': L['name'], 'source': wid('part', L['part']), 'at': L['at'], 'turn': L['turn'], 'mirror': L['mirror'],
                          'recolor': {str(a): b for a, b in L.get('recolor', {}).items()}, 'meta': {'part': L['part']}})
        comp, clash = composite(M)
        dump(os.path.join(D, 'masks', pw + '.composite.txt'), comp)
        man['works'][pw] = {'title': B['title'], 'size': [M.X, M.Y, M.Z], 'tags': 'building,' + STYLE, 'mask': None, 'expect': pw + '.composite.txt',
                            'anchors': {k: list(v) for k, v in M.anchors.items()}, 'links': links, 'models': M.models, 'order': 2}
        # 讀數：門口固定點要是空氣、腳下有東西；框外 0；部件撞格 0
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

    # ── 城牆模組＋每一級一段樣板牆 ──
    for tier, fns in walls.TIERS.items():
        if want and ('wall%d' % tier) not in want:
            continue
        mods = {}
        for fn in fns:
            B = fn()
            M = B['M']
            w = wid(B['key'])
            cells = M.layer('body')
            md5 = dump(os.path.join(D, 'masks', w + '.vox.txt'), cells)
            n, cav, fl = structure(cells, (M.X, M.Y, M.Z), floating=True)
            man['works'][w] = {'title': B['title'], 'size': [M.X, M.Y, M.Z], 'tags': 'wall,' + STYLE, 'mask': w + '.vox.txt',
                               'anchors': {k: list(v) for k, v in M.anchors.items()}, 'links': [], 'models': [], 'order': 1}
            ver[w] = {'voxels': len(cells), 'oob': M.oob, 'components': n, 'floating': fl, 'cavity': cav, 'bbox': bbox(cells), 'md5': md5,
                      'anchors': {k: list(v) for k, v in M.anchors.items()}}
            mods[B['part']] = (B, w, cells)
            print(w, json.dumps(ver[w], ensure_ascii=False))
        # 樣板段：收尾（翻面）—斷面×4—塔—斷面×4—城門—斷面×4—接頭—轉 90°：斷面×4—收尾
        Yk = 40
        seq = [('end', 'x')] + [('section', '')] * 4 + [('tower', '')] + [('section', '')] * 4 + [('gate', '')] + [('section', '')] * 4 + [('joint', '')]
        links, comp, cur, cnt = [], {}, 0, {}
        def add(part, at, turn, mirror, name):
            B, w, cells = mods[part]
            M = B['M']
            meta = {'kind': 'wall', 'part': part, 'tier': tier, 'style': STYLE}
            if part == 'section':
                meta['len'] = B['len']
            links.append({'name': name, 'source': w, 'at': list(at), 'turn': turn, 'mirror': mirror, 'recolor': {}, 'meta': meta})
            for (x, y, z), c in cells.items():
                k = xform(x, y, z, (M.X, M.Y, M.Z), turn, mirror, at)
                if k not in comp:
                    comp[k] = c
        for part, mir in seq:
            B, w, cells = mods[part]
            M = B['M']
            a = M.anchors['wall-a'][0]
            yc = M.anchors['wall-a'][1]
            if mir == 'x':                                            # 起點的收尾：翻面 ⇒ 接口在 +x 那一面
                at = (cur, Yk - yc, 0)
                cur = cur + M.X
            else:
                at = (cur - a, Yk - yc, 0)
                b = M.anchors.get('wall-b', [M.X - 1])[0]
                cur = at[0] + b + 1
            cnt[part] = cnt.get(part, 0) + 1
            add(part, at, 0, mir, '%s-%02d' % (part, cnt[part]))
        Bj = mods['joint'][0]['M']
        cx = cur - (Bj.anchors['wall-b'][0] + 1 - Bj.anchors['wall-a'][0]) // 2   # 轉角的中線
        cy = Yk + (Bj.anchors['wall-b'][0] + 1 - Bj.anchors['wall-a'][0]) // 2
        for i, part in enumerate(['section'] * 4 + ['end']):
            B, w, cells = mods[part]
            M = B['M']
            yc = M.anchors['wall-a'][1]
            a = M.anchors['wall-a'][0]
            at = (cx - (M.Y - yc), cy - a, 0)                         # turn 90：模組 y ⇒ 組裝件 −x；中線 y ＝ yc ⇒ x ＝ cx
            cy = at[1] + (M.anchors.get('wall-b', [M.X - 1])[0] + 1)
            cnt[part] = cnt.get(part, 0) + 1
            add(part, at, 90, '', '%s-%02d' % (part, cnt[part]))
        X, Yb, Zb = boxes(links)                                    # 引擎要被關聯的作品整個框都放得進來（⛔ 不是只看有格的地方）
        pw = wid('wall%d' % tier)
        dump(os.path.join(D, 'masks', pw + '.composite.txt'), comp)
        man['works'][pw] = {'title': '城牆 %d 級（%s）樣板段：收尾—斷面—塔—斷面—城門—斷面—接頭—轉 90°—斷面—收尾' % (tier, walls.TIER_NAME[tier]),
                            'size': [X, Yb, Zb], 'tags': 'wall,' + STYLE, 'mask': None, 'expect': pw + '.composite.txt',
                            'anchors': {}, 'links': links, 'models': [], 'order': 2}
        n, cav, fl = structure(comp, (X, Yb, Zb), floating=True)
        ver[pw] = {'size': [X, Yb, Zb], 'composite_voxels': len(comp), 'components': n, 'floating': fl, 'links': len(links)}
        sheet(comp, (X, Yb, Zb), os.path.join(D, 'sheets', 'wall%d.png' % tier), man['works'][pw]['title'] + '｜%d 格' % len(comp), px=2)
        print(pw, json.dumps(ver[pw], ensure_ascii=False))

    # ── 配色變化：一件組裝件、一條關聯指到原型＋替換色（TASK-0584）⇒ 不另存格子 ──
    def rd_comp(w):
        p = os.path.join(D, 'masks', w + '.composite.txt')
        out = {}
        for l in open(p, encoding='utf-8'):
            a = l.split(',')
            out[(int(a[0]), int(a[1]), int(a[2]))] = int(a[3])
        return out
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
                                'models': [], 'order': 3}
            ver[pw] = {'base': bw, 'recolor': {str(a): b for a, b in rc.items()}, 'composite_voxels': len(comp),
                       'changed': sum(1 for c in rd_comp(bw).values() if c in rc)}
            sheet(comp, tuple(B0['size']), os.path.join(D, 'sheets', key + '.png'), title, px=3)
            print(pw, json.dumps(ver[pw], ensure_ascii=False))

    # ── 任務作品（樣板街）：北排面向街（turn 0）、南排背向（turn 180）、最後一排三級城牆樣板段 ──
    if not want or 'street' in want:
        links, comp = [], {}
        def put(w, at, turn, name):
            W0 = man['works'][w]
            links.append({'name': name, 'source': w, 'at': list(at), 'turn': turn, 'mirror': '', 'recolor': {}, 'meta': {}})
            for k, c in rd_comp(w).items():
                comp.setdefault(xform(k[0], k[1], k[2], tuple(W0['size']), turn, '', at), c)
        x = 40
        for key in ('house-a', 'house-b', 'house-c', 'house-a2', 'house-b2', 'house-c2', 'tavern', 'warehouse'):
            put(wid(key), (x, STREET_Y1, 0), 0, key)
            x += man['works'][wid(key)]['size'][0]
        x = 40
        for key in ('church', 'townhall', 'market', 'governor'):
            S = man['works'][wid(key)]['size']
            put(wid(key), (x, STREET_Y0 - S[1], 0), 180, key)
            x += S[0] + 20
        x = 40
        for t in (1, 2, 3):
            S = man['works'][wid('wall%d' % t)]['size']
            put(wid('wall%d' % t), (x, WALL_Y, 0), 0, 'wall%d' % t)
            x += S[0] + 20
        X, Yb, Zb = boxes(links)
        X, Yb = X + 40, Yb + 40
        dump(os.path.join(D, 'masks', ROOT + '.composite.txt'), comp)
        man['works'][ROOT] = {'title': '法式殖民城鎮建築套件（風格 fr；0.1 m）—— 樣板街：住宅三型＋配色變化、酒館、倉庫｜教堂、市政廳、市場、總督府｜城牆 1～3 級樣板段',
                              'size': [X, Yb, Zb], 'tags': 'town', 'mask': None, 'expect': ROOT + '.composite.txt', 'anchors': {}, 'links': links,
                              'models': [], 'order': 4, 'root': True}
        ver[ROOT] = {'size': [X, Yb, Zb], 'composite_voxels': len(comp), 'links': len(links)}
        sheet(comp, (X, Yb, Zb), os.path.join(D, 'sheets', 'street.png'), '樣板街（北排面向街、南排背向；最下一排城牆 1～3 級）｜%d 格' % len(comp), px=1)
        print(ROOT, json.dumps(ver[ROOT], ensure_ascii=False))

    json.dump(man, open(man_p, 'w', encoding='utf-8', newline='\n'), ensure_ascii=False, indent=1, sort_keys=True)
    json.dump(ver, open(ver_p, 'w', encoding='utf-8', newline='\n'), ensure_ascii=False, indent=1, sort_keys=True)


# 配色變化（設計決定）：A 換米白牆藍百葉、B 換土黃牆紅百葉、C 換藍牆綠百葉（C 原本的紅百葉是部件關聯換的 49:160 ⇒ 外層看到的是 160）
VARIANTS = [('house-a2', 'house-a', {OCHRE: CREAM, SH_GREEN: SH_BLUE}, '住宅 A2（A 的配色變化：米白牆、藍百葉；替換色，不另存格子）'),
            ('house-b2', 'house-b', {BLUE: OCHRE, SH_GREEN: SH_RED}, '住宅 B2（B 的配色變化：土黃牆、紅百葉；替換色，不另存格子）'),
            ('house-c2', 'house-c', {CREAM: BLUE, SH_RED: SH_GREEN}, '住宅 C2（C 的配色變化：藍牆、綠百葉；替換色，不另存格子）'),
            ('house-a2-s', 'house-a-s', {OCHRE: CREAM, SH_GREEN: SH_BLUE}, '住宅 A2 淺版（A 淺版的配色變化：米白牆、藍百葉；替換色，不另存格子）'),   # 淺版（8 × 10，TASK-0742 轉角）照同一套替換色
            ('house-b2-s', 'house-b-s', {BLUE: OCHRE, SH_GREEN: SH_RED}, '住宅 B2 淺版（B 淺版的配色變化：土黃牆、紅百葉；替換色，不另存格子）'),
            ('house-c2-s', 'house-c-s', {CREAM: BLUE, SH_RED: SH_GREEN}, '住宅 C2 淺版（C 淺版的配色變化：藍牆、綠百葉；替換色，不另存格子）'),
            ('house-a2-xs', 'house-a-xs', {OCHRE: CREAM, SH_GREEN: SH_BLUE}, '住宅 A2 小版（A 小版的配色變化：米白牆、藍百葉；替換色，不另存格子）'),   # 小版（8 × 8，TASK-0840 轉角）照同一套替換色
            ('house-b2-xs', 'house-b-xs', {BLUE: OCHRE, SH_GREEN: SH_RED}, '住宅 B2 小版（B 小版的配色變化：土黃牆、紅百葉；替換色，不另存格子）'),
            ('house-c2-xs', 'house-c-xs', {CREAM: BLUE, SH_RED: SH_GREEN}, '住宅 C2 小版（C 小版的配色變化：藍牆、綠百葉；替換色，不另存格子）')]
STREET_Y0, STREET_Y1, WALL_Y = 320, 380, 580          # 街的南緣、北緣（6 m 寬）、城牆那一排


if __name__ == '__main__':
    main()
