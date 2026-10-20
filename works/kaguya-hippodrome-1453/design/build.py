# 產生全部（TASK-0748 大競技場 1453）：python -I -X utf8 -B build.py <design 資料夾>
#   ⇒ masks/<作品 id>.vox.txt、manifest.json（apply.py 照它下 CLI）、verify.json（讀數）、sheets/voxel_views.png（格子的立面、俯視）。
#   抄聖索菲亞 kaguya-hagia-sophia-1453/design/build.py；改：三件子作品（看台／半圓端柱廊／中線與碑柱）、量回來的讀數。
# 決定論：同一份 plan.json ⇒ 逐位元組相同。
import sys, os, json, hashlib
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import numpy as np
from scipy import ndimage
from PIL import Image, ImageDraw
import hippo

ROOT = 'kaguya-hippodrome-1453'
PARTS = (('stands', 1, 10, '看台（兩條長邊的看台與外牆拱、北端起跑門、皇帝包廂殘塊）'),
         ('sphendone', 2, 20, '半圓端柱廊（37 個柱位留 30 根、柱頂迴廊與女兒牆）'),
         ('spina', 3, 30, '中線（矮牆、狄奧多西方尖碑、蛇柱、砌石方尖碑、兩根散柱）'))


def rgbc(c):
    c = int(c)
    return ((c >> 5) & 7) * 255 // 7, ((c >> 2) & 7) * 255 // 7, (c & 3) * 255 // 3


def dump(path, cells):
    with open(path, 'w', encoding='utf-8', newline='\n') as f:
        for k in sorted(cells):
            f.write('%d,%d,%d,%d\n' % (k[0], k[1], k[2], cells[k]))
    return hashlib.md5(open(path, 'rb').read()).hexdigest()


def cells_of(G, sel):
    z, y, x = np.nonzero(sel)
    return {(int(a), int(b), int(c)): int(G[c, b, a]) for a, b, c in zip(x, y, z)}


def proj(G, axis, rev=False):
    """沿某軸看過去最先碰到的格 ⇒ RGB（axis 0 ＝ 從上往下、1 ＝ 沿模型 y（從正面 ＝ 西看）、2 ＝ 沿模型 x（從北看））；遠的暗一點。"""
    nz = G > 0
    A = np.flip(nz, axis) if rev else nz
    if axis == 0: A = A[::-1]; Gs = G[::-1]
    else: Gs = np.flip(G, axis) if rev else G
    hit = A.any(axis); idx = A.argmax(axis)
    n = A.shape[axis]
    col = np.take_along_axis(Gs, np.expand_dims(idx, axis), axis).squeeze(axis)
    rgb = np.array([rgbc(c) for c in range(256)], np.float32)[col]
    k = (0.55 + 0.45 * (1 - idx / n))[..., None]
    img = np.where(hit[..., None], rgb * k, np.array([238, 232, 216], np.float32))
    img = img.astype(np.uint8)
    if axis != 0: img = img[::-1]                                  # z 往上
    return img


def main():
    D = os.path.abspath(sys.argv[1])
    os.makedirs(os.path.join(D, 'masks'), exist_ok=True); os.makedirs(os.path.join(D, 'sheets'), exist_ok=True)
    G, L, anchors, info = hippo.build()
    Zn, Yn, Xn = G.shape
    man = {'root': ROOT, 'mpv': hippo.MPV, 'works': {}}
    ver = {}
    allc = {}
    for part, code, order, title in PARTS:
        cells = cells_of(G, L == code); allc.update(cells)
        w = ROOT + '-' + part
        md5 = dump(os.path.join(D, 'masks', w + '.vox.txt'), cells)
        man['works'][w] = {'order': order, 'title': '大競技場 1453｜' + title, 'size': [Xn, Yn, Zn], 'tags': 'sub', 'mask': w + '.vox.txt', 'anchors': {}, 'links': []}
        ver[w] = {'cells': len(cells), 'md5': md5}
    dump(os.path.join(D, 'masks', ROOT + '.composite.txt'), allc)
    meta_body = {'kind': 'building', 'use': 'hippodrome', 'style': 'roman', 'lot': '130,450', 'base': 0, 'variant': 'a'}   # 特殊建築（Blocksail world/town.js SPECIAL）
    man['works'][ROOT] = {'order': 90, 'title': hippo.P['title'], 'size': [Xn, Yn, Zn], 'tags': 'building,roman', 'mask': None, 'expect': ROOT + '.composite.txt',
                          'anchors': {k: list(v) for k, v in anchors.items()},
                          'links': [{'name': '看台', 'source': ROOT + '-stands', 'at': [0, 0, 0], 'turn': 0, 'mirror': '', 'recolor': {}, 'meta': meta_body},
                                    {'name': '半圓端柱廊', 'source': ROOT + '-sphendone', 'at': [0, 0, 0], 'turn': 0, 'mirror': '', 'recolor': {}, 'meta': {'part': 'sphendone'}},
                                    {'name': '中線與碑柱', 'source': ROOT + '-spina', 'at': [0, 0, 0], 'turn': 0, 'mirror': '', 'recolor': {}, 'meta': {'part': 'spina'}}]}
    a = G > 0
    lab, n = ndimage.label(a)
    sizes = ndimage.sum(a, lab, range(1, n + 1))
    ground = set(np.unique(lab[0])) - {0}
    floating = sorted([int(sizes[i - 1]) for i in range(1, n + 1) if i not in ground], reverse=True)
    mpv = hippo.MPV
    zs = np.nonzero(a.any((1, 2)))[0]
    ys, xs = np.nonzero(a.any(0))
    def topz(color):
        m = (G == color); z = np.nonzero(m.any((1, 2)))[0]
        return round((z.max() + 1) * mpv, 2) if len(z) else None
    meas = {'最高（m）': round((zs.max() + 1) * mpv, 2), '外框 y（m）': round((ys.max() + 1 - ys.min()) * mpv, 2), '外框 x（m）': round((xs.max() + 1 - xs.min()) * mpv, 2),
            '狄奧多西方尖碑頂（m）': round(anchors['obelisk-theodosius-top'][2] * mpv, 2), '砌石方尖碑頂（m）': round(anchors['obelisk-walled-top'][2] * mpv, 2),
            '蛇柱頂（m）': round(anchors['serpent-top'][2] * mpv, 2), '柱廊頂（m）': round(anchors['colonnade-mid'][2] * mpv, 2),
            '挖空（格）': info['hollowed'], '倒掉的柱位': info['columns_gone']}
    ver[ROOT] = {'cells': len(allc), 'components': int(n), 'floating': floating[:10], 'measured': meas, 'anchors': {k: list(v) for k, v in anchors.items()}}
    print('格數 %d（%s）元件 %d 浮空 %s' % (len(allc), '、'.join('%s %d' % (p, ver[ROOT + '-' + p]['cells']) for p, _, _, _ in PARTS), n, floating[:10]))
    print('量回來', json.dumps(meas, ensure_ascii=False))
    px = 1
    ims = [('北立面（正面、起跑門）', proj(G, 1)), ('東南立面（皇帝包廂那一側）', proj(G, 2))]
    W = sum(i.shape[1] for _, i in ims) * px + 50; H = Zn * px + 50
    top = proj(G, 0)
    im = Image.new('RGB', (max(W, Xn * px + 20), H + Yn * px + 40), (250, 247, 240)); dr = ImageDraw.Draw(im)
    x0 = 10
    for t, a_ in ims:
        im.paste(Image.fromarray(a_).resize((a_.shape[1] * px, a_.shape[0] * px), Image.NEAREST), (x0, 30)); dr.text((x0, 8), t, fill=(60, 50, 40)); x0 += a_.shape[1] * px + 15
    dr.text((10, H + 12), '俯視（上 ＝ 模型 y 0 ＝ 北端起跑門、左 ＝ 東南）', fill=(60, 50, 40))
    im.paste(Image.fromarray(top).resize((Xn * px, Yn * px), Image.NEAREST), (10, H + 30))
    im.save(os.path.join(D, 'sheets', 'voxel_views.png'))
    json.dump(man, open(os.path.join(D, 'manifest.json'), 'w', encoding='utf-8', newline='\n'), ensure_ascii=False, indent=1, sort_keys=True)
    json.dump(ver, open(os.path.join(D, 'verify.json'), 'w', encoding='utf-8', newline='\n'), ensure_ascii=False, indent=1, sort_keys=True)


if __name__ == '__main__':
    main()
