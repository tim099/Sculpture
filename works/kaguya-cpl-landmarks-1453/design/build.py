# 產生全部地標（TASK-0748 君士坦丁堡地標 1453）：python -I -X utf8 -B build.py <design 資料夾> [地標名 …]（不給 ⇒ 全部）
#   每一座地標一支 lm_<名>.py（用 byz.py 的形狀拼），各自匯出：
#   ⇒ masks/<作品 id>.vox.txt（每件子作品）、<成品>.composite.txt、manifest.json（apply.py 照它下 CLI；多座地標合在同一份）、
#     verify.json（讀數）、sheets/<名>_views.png（格子的立面、俯視）。
#   抄大競技場 kaguya-hippodrome-1453/design/build.py；改：一份設計資料夾產好幾件成品（成品的 parent ＝ 委託作品 ROOT）。
# 決定論：同一份參數 ⇒ 逐位元組相同。
import sys, os, json, hashlib, importlib
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import numpy as np
from scipy import ndimage
from PIL import Image, ImageDraw, ImageFont

ROOT = 'kaguya-cpl-landmarks-1453'
GLASS_PART = ('glass', 200, '窗玻璃', {'part': 'window', 'material': 'glass'})   # byz.GLASS_LAY；關聯 meta 照造船規格 §9.5 的玻璃＋窗部件 ⇒ Blocksail 匯入：近處畫成半透明、夜裡亮窗（BUILDING_SPEC §5.1）
ORDER = ['column_constantine', 'column_arcadius', 'column_justinian', 'hagia_irene', 'chora', 'pammakaristos', 'pantokrator', 'little_hagia_sophia',
         'lips', 'myrelaion', 'kalenderhane', 'tekfur', 'cistern_aetius', 'cistern_aspar', 'cistern_mocius', 'holy_apostles', 'stoudios']


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
    """沿某軸看過去最先碰到的格 ⇒ RGB（axis 0 ＝ 從上往下、1 ＝ 從正面（y 0）看、2 ＝ 從左側（x 0）看）；遠的暗一點。"""
    nz = G > 0
    A = np.flip(nz, axis) if rev else nz
    if axis == 0:
        A = A[::-1]; Gs = G[::-1]
    else:
        Gs = np.flip(G, axis) if rev else G
    hit = A.any(axis); idx = A.argmax(axis)
    n = A.shape[axis]
    col = np.take_along_axis(Gs, np.expand_dims(idx, axis), axis).squeeze(axis)
    rgb = np.array([rgbc(c) for c in range(256)], np.float32)[col]
    k = (0.55 + 0.45 * (1 - idx / n))[..., None]
    img = np.where(hit[..., None], rgb * k, np.array([238, 232, 216], np.float32)).astype(np.uint8)
    if axis != 0:
        img = img[::-1]
    return img


def sheet(path, G, title, px):
    Zn, Yn, Xn = G.shape
    ims = [('正面（y 0）', proj(G, 1)), ('背面', proj(G, 1, True)[:, ::-1]), ('左側（x 0）', proj(G, 2)), ('右側', proj(G, 2, True)[:, ::-1])]
    top = proj(G, 0)
    W = sum(i.shape[1] for _, i in ims) * px + 15 * len(ims) + 10
    H = Zn * px + 50
    im = Image.new('RGB', (max(W, Xn * px + 20), H + Yn * px + 40), (250, 247, 240)); dr = ImageDraw.Draw(im)
    ft = ImageFont.truetype('C:/Windows/Fonts/msjh.ttc', 14)
    x0 = 10
    for t, a_ in ims:
        im.paste(Image.fromarray(a_).resize((a_.shape[1] * px, a_.shape[0] * px), Image.NEAREST), (x0, 30)); dr.text((x0, 8), t, fill=(60, 50, 40), font=ft); x0 += a_.shape[1] * px + 15
    dr.text((10, H + 12), title + ' —— 俯視（上 ＝ 正面 y 0、左 ＝ x 0）', fill=(60, 50, 40), font=ft)
    im.paste(Image.fromarray(top).resize((Xn * px, Yn * px), Image.NEAREST), (10, H + 30))
    im.save(path)


def main():
    D = os.path.abspath(sys.argv[1])
    only = sys.argv[2:]
    os.makedirs(os.path.join(D, 'masks'), exist_ok=True); os.makedirs(os.path.join(D, 'sheets'), exist_ok=True)
    mp, vp = os.path.join(D, 'manifest.json'), os.path.join(D, 'verify.json')
    man = json.load(open(mp, encoding='utf-8')) if os.path.exists(mp) else {'root': ROOT, 'works': {}}
    ver = json.load(open(vp, encoding='utf-8')) if os.path.exists(vp) else {}
    for name in ORDER:
        if only and name not in only:
            continue
        if not os.path.exists(os.path.join(D, 'lm_%s.py' % name)):
            continue
        lm = importlib.import_module('lm_' + name)
        G, L, anchors, info = lm.build()
        Zn, Yn, Xn = G.shape
        prod = ROOT.replace('-landmarks-1453', '') + '-' + lm.KEY + '-1453'        # 例 kaguya-cpl-chora-1453
        for w in [k for k in man['works'] if k == prod or man['works'][k].get('product') == prod]:
            del man['works'][w]
        allc = {}
        links = []
        for i, pt in enumerate(tuple(lm.PARTS) + (GLASS_PART,)):        # 窗玻璃一律排最後（byz.finish 放進件號 GLASS_LAY；沒有窗 ⇒ 空的、不建）
            part, code, title = pt[:3]
            cells = cells_of(G, L == code); allc.update(cells)
            if not cells: continue                                   # 空的子作品不建（例：這一座的園子剛好沒有橄欖）
            w = prod + '-' + part
            md5 = dump(os.path.join(D, 'masks', w + '.vox.txt'), cells)
            man['works'][w] = {'order': 10 * (i + 1), 'title': lm.TITLE_SHORT + '｜' + title, 'size': [Xn, Yn, Zn], 'tags': 'sub', 'mask': w + '.vox.txt',
                               'anchors': {}, 'links': [], 'parent': prod, 'product': prod, 'mpv': lm.MPV}
            ver[w] = {'cells': len(cells), 'md5': md5}
            meta = dict(lm.META) if i == 0 else dict({'part': part}, **(pt[3] if len(pt) > 3 else {}))   # 第四格 ＝ 關聯多帶的 meta（樹：kind=tree、tree=樹種）
            links.append({'name': title.split('（')[0], 'source': w, 'at': [0, 0, 0], 'turn': 0, 'mirror': '', 'recolor': {}, 'meta': meta})
        dump(os.path.join(D, 'masks', prod + '.composite.txt'), allc)
        man['works'][prod] = {'order': 5, 'title': lm.TITLE, 'size': [Xn, Yn, Zn], 'tags': 'building,roman', 'mask': None, 'expect': prod + '.composite.txt',
                              'anchors': {k: list(v) for k, v in anchors.items()}, 'links': links, 'parent': ROOT, 'product': prod, 'mpv': lm.MPV, 'key': lm.KEY}
        a = G > 0
        lab, n = ndimage.label(a)
        sizes = ndimage.sum(a, lab, range(1, n + 1))
        ground = set(np.unique(lab[0])) - {0}
        floating = sorted([int(sizes[i - 1]) for i in range(1, n + 1) if i not in ground], reverse=True)
        zs = np.nonzero(a.any((1, 2)))[0]
        meas = {'最高（m）': round((zs.max() + 1) * lm.MPV, 2)}
        meas.update(info)
        ver[prod] = {'cells': len(allc), 'components': int(n), 'floating': floating[:10], 'measured': meas, 'anchors': {k: list(v) for k, v in anchors.items()}}
        print('%s：格數 %d（%s）元件 %d 浮空 %s' % (prod, len(allc), '、'.join('%s %d' % (pt[0], ver[prod + '-' + pt[0]]['cells']) for pt in lm.PARTS if prod + '-' + pt[0] in man['works']), n, floating[:10]))
        print('  量回來', json.dumps(meas, ensure_ascii=False))
        px = max(1, int(round(500 / max(Xn, Yn, Zn))))
        sheet(os.path.join(D, 'sheets', lm.KEY + '_views.png'), G, lm.TITLE_SHORT, px)
    json.dump(man, open(mp, 'w', encoding='utf-8', newline='\n'), ensure_ascii=False, indent=1, sort_keys=True)
    json.dump(ver, open(vp, 'w', encoding='utf-8', newline='\n'), ensure_ascii=False, indent=1, sort_keys=True)


if __name__ == '__main__':
    main()
