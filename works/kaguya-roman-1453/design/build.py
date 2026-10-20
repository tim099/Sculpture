# 產生全部（TASK-0748 東羅馬城牆 1453）：python -I -X utf8 -B build.py <design 資料夾>
#   ⇒ masks/<作品 id>.vox.txt（x,y,z,color，排好序）、sheets/<key>.png（圖紙：牆外看的正立面＋俯視＋側立面）、
#      manifest.json（每件作品：框、標籤、固定點、關聯 —— apply.py 照它下 CLI）、verify.json（讀數）。
# 決定論：同一份程式 ⇒ 逐位元組相同（⛔ random、⛔ 時間）。
import sys, os, json, hashlib
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import numpy as np
from scipy import ndimage
from PIL import Image, ImageDraw
from rkit import *
import walls

ROOT = 'kaguya-roman-1453'
STYLE = 'roman'


def wid(key):
    return ROOT + '-' + key[len('wall-'):]                 # wall-land-inner-section ⇒ kaguya-roman-1453-land-inner-section


def dump(path, cells):
    with open(path, 'w', encoding='utf-8', newline='\n') as f:
        for k in sorted(cells):
            f.write('%d,%d,%d,%d\n' % (k[0], k[1], k[2], cells[k]))
    return hashlib.md5(open(path, 'rb').read()).hexdigest()


def structure(cells, dims):
    """元件數（6 連通）、封閉空腔格數、沒碰到地面（z 0）的元件格數。"""
    a = np.zeros(dims, bool)
    for k in cells:
        a[k] = True
    lab, n = ndimage.label(a)
    cav = int((ndimage.binary_fill_holes(a) & ~a).sum())
    ground = set(np.unique(lab[:, :, 0])) - {0}
    fl = [int((lab == i).sum()) for i in range(1, n + 1) if i not in ground]
    return int(n), cav, fl


def rgbc(c):
    c = int(c)
    return ((c >> 5) & 7) * 255 // 7, ((c >> 2) & 7) * 255 // 7, (c & 3) * 255 // 3


def sheet(cells, dims, path, title, px=3):
    """圖紙：上 ＝ 從牆外（−y）看的正立面、下左 ＝ 俯視（+y 在下）、下右 ＝ 從 −x 看的側立面；每一格照最先碰到的那一格上色、越深越暗。"""
    X, Y, Z = dims
    g = np.zeros((X, Y, Z), np.uint8)
    for (x, y, z), c in cells.items():
        g[x, y, z] = c

    def proj(axis_dir):
        if axis_dir == 'front':                            # 沿 +y 看：(x, z)
            arr, depth = g, Y
            img = np.zeros((Z, X, 3), np.uint8); img[:] = (24, 30, 40)
            for x in range(X):
                col = g[x]                                 # [y, z]
                nz = col != 0
                first = np.where(nz.any(0), nz.argmax(0), -1)
                for z in range(Z):
                    y = first[z]
                    if y >= 0:
                        sh = 1.0 - 0.45 * y / max(1, Y)
                        img[Z - 1 - z, x] = [int(v * sh) for v in rgbc(col[y, z])]
            return img
        if axis_dir == 'top':                              # 從上往下：(x, y)
            img = np.zeros((Y, X, 3), np.uint8); img[:] = (24, 30, 40)
            nz = g != 0
            top = np.where(nz.any(2), Z - 1 - nz[:, :, ::-1].argmax(2), -1)
            for x in range(X):
                for y in range(Y):
                    z = top[x, y]
                    if z >= 0:
                        sh = 0.55 + 0.45 * z / max(1, Z)
                        img[y, x] = [int(v * sh) for v in rgbc(g[x, y, z])]
            return img
        img = np.zeros((Z, Y, 3), np.uint8); img[:] = (24, 30, 40)    # 側：沿 +x 看 (y, z)
        nz = g != 0
        first = np.where(nz.any(0), nz.argmax(0), -1)      # [y, z]
        for y in range(Y):
            for z in range(Z):
                x = first[y, z]
                if x >= 0:
                    sh = 1.0 - 0.45 * x / max(1, X)
                    img[Z - 1 - z, y] = [int(v * sh) for v in rgbc(g[x, y, z])]
        return img

    f, t, s = proj('front'), proj('top'), proj('side')
    Wd = max(X, X + Y + 8) * px
    H = (Z + 8 + max(Y, Z)) * px + 22
    im = Image.new('RGB', (Wd, H), (16, 20, 28))
    im.paste(Image.fromarray(f).resize((X * px, Z * px), Image.NEAREST), (0, 22))
    im.paste(Image.fromarray(t).resize((X * px, Y * px), Image.NEAREST), (0, 22 + (Z + 8) * px))
    im.paste(Image.fromarray(s).resize((Y * px, Z * px), Image.NEAREST), ((X + 8) * px, 22 + (Z + 8) * px))
    ImageDraw.Draw(im).text((4, 4), title, fill=(230, 220, 190))
    im.save(path)


def main():
    D = os.path.abspath(sys.argv[1])
    os.makedirs(os.path.join(D, 'masks'), exist_ok=True)
    os.makedirs(os.path.join(D, 'sheets'), exist_ok=True)
    man = {'root': ROOT, 'mpv': MPV, 'works': {}}
    ver = {}
    mods = {}
    for i, fn in enumerate(walls.ALL):
        B = fn()
        M = B['M']
        w = wid(B['key'])
        md5 = dump(os.path.join(D, 'masks', w + '.vox.txt'), M.cells)
        n, cav, fl = structure(M.cells, (M.X, M.Y, M.Z))
        meta = {'kind': 'wall', 'part': B['part'], 'set': B['set'], 'style': STYLE, 'variant': B['variant']}
        if 'len' in B:
            meta['len'] = B['len']
        man['works'][w] = {'order': 10 + i, 'title': '東羅馬城牆 1453｜' + B['title'], 'size': [M.X, M.Y, M.Z], 'tags': 'sub,wall,' + STYLE,
                           'mask': w + '.vox.txt', 'anchors': {k: list(v) for k, v in sorted(M.anchors.items())}, 'links': [], 'meta': meta}
        ver[w] = {'cells': len(M.cells), 'oob': M.oob, 'components': n, 'cavity': cav, 'floating': fl, 'md5': md5, 'size': [M.X, M.Y, M.Z],
                  'anchors': {k: list(v) for k, v in sorted(M.anchors.items())}}
        mods[B['key']] = (w, M)
        sheet(M.cells, (M.X, M.Y, M.Z), os.path.join(D, 'sheets', B['key'] + '.png'), '%s  %d 格  %s' % (w, len(M.cells), 'x'.join(map(str, (M.X, M.Y, M.Z)))))
        print('%-44s %8d 格  框 %s  元件 %d  空腔 %d  浮空 %s  框外 %d' % (w, len(M.cells), (M.X, M.Y, M.Z), n, cav, fl, M.oob))

    # ── 樣板段（任務作品）：三排 —— 內牆（y 150）、外牆在它外面 20 m（y 50）、海牆（y 210）；每排 斷面—塔—斷面—城門—斷面—塔—斷面—收尾 ──
    rows = [(150, ['land-inner-section'] * 4 + ['land-inner-tower'] + ['land-inner-section'] * 4 + ['land-inner-gate'] + ['land-inner-section'] * 4 + ['land-inner-tower'] + ['land-inner-section'] * 2 + ['land-inner-end']),
            (50, ['land-outer-section'] * 5 + ['land-outer-tower'] + ['land-outer-section'] * 5 + ['land-outer-gate'] + ['land-outer-section'] * 5 + ['land-outer-tower-b'] + ['land-outer-section'] * 5 + ['land-outer-end']),
            (210, ['sea-section'] * 4 + ['sea-tower'] + ['sea-section'] * 4 + ['sea-gate'] + ['sea-section'] * 4 + ['sea-tower'] + ['sea-section'] * 3 + ['sea-end'])]
    links, comp, cnt = [], {}, {}
    X = Yb = Zb = 0
    for yc, seq in rows:
        x = 0
        for k in seq:
            w, M = mods['wall-' + k]
            at = [x, yc - M.anchors['wall-a'][1], 0]
            cnt[k] = cnt.get(k, 0) + 1
            meta = dict(man['works'][w]['meta'])
            links.append({'name': '%s-%d' % (k, cnt[k]), 'source': w, 'at': at, 'turn': 0, 'mirror': '', 'recolor': {}, 'meta': meta})
            for (cx, cy, cz), c in M.cells.items():
                comp[(cx + at[0], cy + at[1], cz + at[2])] = c
            x += M.X
            X, Yb, Zb = max(X, x), max(Yb, at[1] + M.Y), max(Zb, M.Z)
    dump(os.path.join(D, 'masks', ROOT + '.composite.txt'), comp)
    man['works'][ROOT] = {'order': 90, 'title': '東羅馬城牆 1453（君士坦丁堡：狄奧多西內牆、外牆、海牆）樣板段', 'size': [640, 240, 104], 'tags': 'wall,' + STYLE,
                          'mask': None, 'expect': ROOT + '.composite.txt', 'anchors': {}, 'links': links}
    assert X <= 640 and Yb <= 240 and Zb <= 104, (X, Yb, Zb)
    ver[ROOT] = {'cells': len(comp), 'links': len(links), 'bbox': [X, Yb, Zb]}
    sheet(comp, (640, 240, 104), os.path.join(D, 'sheets', 'sample.png'), '%s 樣板段  %d 格（組好）  %d 條關聯' % (ROOT, len(comp), len(links)), px=2)
    print('樣板段', len(comp), '格', len(links), '條關聯', 'bbox', (X, Yb, Zb))
    json.dump(man, open(os.path.join(D, 'manifest.json'), 'w', encoding='utf-8', newline='\n'), ensure_ascii=False, indent=1, sort_keys=True)
    json.dump(ver, open(os.path.join(D, 'verify.json'), 'w', encoding='utf-8', newline='\n'), ensure_ascii=False, indent=1, sort_keys=True)


if __name__ == '__main__':
    main()
