# 產生全部（Blocksail TASK-0899 港口建築的水上版；抄自 crest-berth-01m/design/build.py）：python -I -X utf8 -B build.py <design 資料夾> [key …]
#   ⇒ masks/<作品 id>.vox.txt（x,y,z,color，排好序）、sheets/<key>.png（圖紙：俯視＋正立面＋側立面）、
#      manifest.json（每件作品：框、標籤、固定點、關聯、外部模型 —— apply.py 照它下 CLI）、verify.json（讀數）。
# 決定論：同一份程式 ⇒ 逐位元組相同（⛔ random、⛔ 時間）。
# 部件全部借 summit-carib-01m（自己做的木板門、窗）與 summit-bourg-fr-01m（貨門、氣窗）的作品 ⇒ 這裡不建部件作品。
# 每一棟的風格（meta style）照它自己：加勒比海那一套 carib；不分地區的港口配套 common（TOWN_BUILD §2.1 的退路）。
import sys, os, json, hashlib
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import numpy as np
from scipy import ndimage
import waterside, cranes
from waterside import *

ROOT = 'crest-waterside-01m'
SUMMIT_ROOT = 'summit-carib-01m'
MODULES = [waterside, cranes]


def wid(*a):
    return '-'.join([ROOT] + list(a))


def dump(path, cells):
    with open(path, 'w', encoding='utf-8', newline='\n') as f:
        for k in sorted(cells):
            f.write('%d,%d,%d,%d\n' % (k[0], k[1], k[2], cells[k]))
    return hashlib.md5(open(path, 'rb').read()).hexdigest()


def structure(cells, dims, floating=False, ground=(0,), ropes=()):
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
    ground = set(np.concatenate([np.unique(lab[:, :, g]) for g in ground])) - {0}   # 泊位：棧橋面（z SINK × 10）也算地面（berth.py）
    ground = rope_ground(lab, ground, ropes)                         # 掛在繩上的那一團（吊鉤、貨網）算接到（berth.py rope_ground）
    fl = [int((lab == i).sum()) for i in range(1, n + 1) if i not in ground]
    return int(n), cav, fl


def rope_list(M):
    """M.ropes（berth.py rope）⇒ manifest 的 ropes：apply.py ropes 照它下 work sub=rope（端點 x,y,z 格座標、色 #RRGGBB、粗細 ＝ 直徑格、鬆緊）。"""
    f = lambda v: ','.join('%g' % round(c, 3) for c in v)
    return [{'name': R['name'], 'from': f(R['a']), 'to': f(R['b']), 'color': '#%02x%02x%02x' % rgb(R['color']), 'thickness': R['thick'], 'slack': R['slack']}
            for R in getattr(M, 'ropes', [])]


def bbox(cells):
    xs = [k[0] for k in cells]; ys = [k[1] for k in cells]; zs = [k[2] for k in cells]
    return [min(xs), min(ys), min(zs), max(xs) + 1, max(ys) + 1, max(zs) + 1]


def part_src(pid):
    return pid if pid.startswith('summit-') else SUMMIT_ROOT + '-part-' + pid


def main():
    D = os.path.abspath(sys.argv[1])
    want = set(sys.argv[2:])
    os.makedirs(os.path.join(D, 'masks'), exist_ok=True)
    os.makedirs(os.path.join(D, 'sheets'), exist_ok=True)
    man_p = os.path.join(D, 'manifest.json')
    ver_p = os.path.join(D, 'verify.json')
    man = json.load(open(man_p, encoding='utf-8')) if os.path.exists(man_p) else {'root': ROOT, 'works': {}}
    ver = json.load(open(ver_p, encoding='utf-8')) if os.path.exists(ver_p) else {}

    for fn in sum([m.ALL for m in MODULES], []):
        key = fn.__name__.replace('_', '-')                            # 函式名 ＝ key（底線換成 -）⇒ 只產點名的那幾棟不用先跑一遍
        if want and key not in want:
            continue
        B = fn()
        key = B['key']
        M = B['M']
        style = B.get('style', 'carib')
        pw = wid(key)
        links, layer_ver = [], {}
        meta_b = {'kind': 'building', 'use': B['use'], 'style': style, 'lot': '%g,%g' % B['lot'], 'base': 4, 'variant': B.get('variant', 'a')}
        meta_b.update(B.get('meta', {}))                               # 水上版：water、deckz、slip、base 0（waterside.py）
        for ln, lname in B['layers'].items():
            cells = M.layer(ln)
            if not cells:
                continue
            w = wid(key, ln)
            md5 = dump(os.path.join(D, 'masks', w + '.vox.txt'), cells)
            n, cav = structure(cells, (M.X, M.Y, M.Z))
            man['works'][w] = {'title': '%s｜%s' % (B['title'].split('（')[0], lname), 'size': [M.X, M.Y, M.Z], 'tags': 'sub', 'mask': w + '.vox.txt',
                               'anchors': {k: list(v) for k, v in B.get('layer_anchors', {}).get(ln, {}).items()},
                               'links': [], 'models': B.get('layer_models', {}).get(ln, []), 'order': 1, 'mpv': B.get('mpv', 0.1)}
            layer_ver[w] = {'voxels': len(cells), 'components': n, 'cavity': cav, 'bbox': bbox(cells), 'md5': md5}
            links.append({'name': lname, 'source': w, 'at': [0, 0, 0], 'turn': 0, 'mirror': '', 'recolor': {},
                          'meta': meta_b if ln == 'body' else B.get('layer_meta', {}).get(ln, {'part': ln})})   # 每一層可以帶自己的 meta（堡壘的甲板、彈藥庫，TASK-0853／0861）
        for L in M.links:
            src = part_src(L['part'])
            links.append({'name': L['name'], 'source': src, 'at': L['at'], 'turn': L['turn'], 'mirror': L['mirror'],
                          'recolor': {str(a): b for a, b in L.get('recolor', {}).items()}, 'meta': {'part': src.rsplit('-part-', 1)[1]}})
        comp, clash = composite(M)
        dump(os.path.join(D, 'masks', pw + '.composite.txt'), comp)
        man['works'][pw] = {'title': B['title'], 'size': [M.X, M.Y, M.Z], 'tags': 'building,' + style, 'mask': None, 'expect': pw + '.composite.txt',
                            'anchors': {k: list(v) for k, v in M.anchors.items()}, 'links': links, 'models': M.models, 'order': 2, 'ropes': rope_list(M),
                            'flags': B.get('flags', []), 'mpv': B.get('mpv', 0.1)}
        dx, dy, dz = M.anchors['door']
        door_ok = (dx, dy, dz) not in comp and (dz == 0 or B.get('door_deck') or (dx, dy, dz - 1) in comp) and (dx, dy, dz + 1) not in comp   # 泊位：腳下是遊戲畫的棧橋面
        n, cav, fl = structure(comp, (M.X, M.Y, M.Z), floating=True, ground=B.get('ground', (0,)), ropes=getattr(M, 'ropes', []))
        ver[pw] = {'lot': list(B['lot']), 'size': [M.X, M.Y, M.Z], 'style': style, 'use': B['use'], 'oob': M.oob, 'part_clash': clash, 'composite_voxels': len(comp),
                   'composite_components': n, 'composite_floating': fl, 'composite_cavity': cav, 'bbox': bbox(comp), 'door': list(M.anchors['door']), 'door_ok': door_ok,
                   'links': len(links), 'models': len(M.models), 'ropes': len(getattr(M, 'ropes', [])), 'layers': layer_ver}
        sheet(comp, (M.X, M.Y, M.Z), os.path.join(D, 'sheets', key + '.png'),
              '%s｜地塊 %g × %g m｜%d 格（組好）｜框 %s' % (B['title'].split('（')[0], B['lot'][0], B['lot'][1], len(comp), 'x'.join(str(v) for v in (M.X, M.Y, M.Z))), px=B.get('px', 3))
        print(key, json.dumps({k: v for k, v in ver[pw].items() if k != 'layers'}, ensure_ascii=False))
        for w, lv in layer_ver.items():
            print('   ', w, lv)

    json.dump(man, open(man_p, 'w', encoding='utf-8', newline='\n'), ensure_ascii=False, indent=1, sort_keys=True)
    json.dump(ver, open(ver_p, 'w', encoding='utf-8', newline='\n'), ensure_ascii=False, indent=1, sort_keys=True)


if __name__ == '__main__':
    main()
