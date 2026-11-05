# 產生全部（TASK-0748 加拉塔塔 1453）：python -I -X utf8 -B build.py <design 資料夾>
#   ⇒ masks/<作品 id>.vox.txt、manifest.json（apply.py 照它下 CLI）、verify.json（讀數）、sheets/voxel_*.png（格子的立面、剖面、俯視）。
#   圖紙（照 plan.json 的參數畫、標尺寸）在 draft.py；這裡畫的是「格子長怎樣」，拿來跟圖紙對。
# 決定論：同一份 plan.json ⇒ 逐位元組相同。
import sys, os, json, hashlib
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import numpy as np
from scipy import ndimage
from PIL import Image, ImageDraw
import tower

ROOT = 'kaguya-galata-tower-1453'


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


def view(G, axis, rev=False, shade=True):
    """沿某軸看過去最先碰到的格（axis：'y' ＝ 從 y 小往大看＝正面；'x'；'z' ＝ 從上往下）⇒ RGB 圖（上 ＝ 高）。"""
    Zn, Yn, Xn = G.shape
    nz = G > 0
    if axis == 'z':
        idx = np.where(nz.any(0), Zn - 1 - nz[::-1].argmax(0), -1)          # [y, x]
        img = np.zeros((Yn, Xn, 3), np.uint8); img[:] = (238, 232, 216)
        yy, xx = np.nonzero(idx >= 0)
        for y, x in zip(yy, xx):
            z = idx[y, x]; s = 0.55 + 0.45 * z / Zn
            img[y, x] = [int(v * s) for v in rgbc(G[z, y, x])]
        return img
    if axis == 'y':
        A = nz[:, ::-1, :] if rev else nz
        first = np.where(A.any(1), A.argmax(1), -1)                           # [z, x]
        img = np.zeros((Zn, Xn, 3), np.uint8); img[:] = (238, 232, 216)
        zz, xx = np.nonzero(first >= 0)
        for z, x in zip(zz, xx):
            y = first[z, x]; y = Yn - 1 - y if rev else y
            s = 1.0 - (0.45 * (abs(y - Yn / 2) / (Yn / 2)) if shade else 0)
            img[Zn - 1 - z, x] = [int(v * (0.6 + 0.4 * (1 - abs(y - Yn / 2) / (Yn / 2)))) for v in rgbc(G[z, y, x])]
        return img
    A = nz
    first = np.where(A.any(2), A.argmax(2), -1)                               # [z, y]
    img = np.zeros((Zn, Yn, 3), np.uint8); img[:] = (238, 232, 216)
    zz, yy = np.nonzero(first >= 0)
    for z, y in zip(zz, yy):
        x = first[z, y]
        img[Zn - 1 - z, y] = [int(v * (0.6 + 0.4 * (1 - abs(x - Xn / 2) / (Xn / 2)))) for v in rgbc(G[z, y, x])]
    return img


def section(G, x):
    """x ＝ 那一欄的剖面（y 往右、z 往上）。"""
    Zn, Yn, Xn = G.shape
    img = np.zeros((Zn, Yn, 3), np.uint8); img[:] = (238, 232, 216)
    sl = G[:, :, x]
    zz, yy = np.nonzero(sl)
    for z, y in zip(zz, yy):
        img[Zn - 1 - z, y] = rgbc(sl[z, y])
    return img


def main():
    D = os.path.abspath(sys.argv[1])
    os.makedirs(os.path.join(D, 'masks'), exist_ok=True); os.makedirs(os.path.join(D, 'sheets'), exist_ok=True)
    G, LAY, anchors, sail, arm = tower.build()
    Zn, Yn, Xn = G.shape
    man = {'root': ROOT, 'mpv': tower.MPV, 'works': {}}
    ver = {}
    # 部件（LAY 值 ⇒ 子作品）：武裝那幾件是 TASK-1025 加的（甲板、梯子、火藥間各自一件 ⇒ 關聯的 meta 才分得出層）
    PARTS = (('body', 1, 10, '塔身（石砌、磚層、射口、盲拱、托石、雉堞、樓板、門、1452 年外堡）', {}, []),
             ('roof', 2, 20, '屋頂（鉛皮圓錐）與頂飾（旗杆、熱那亞旗、帶十字的金球）', {}, []),
             ('deck-gun', 3, 30, '3 層砲甲板（樓板）與三門砲', {}, arm['gundeck']['models']),
             ('deck-top', 4, 40, '頂層砲台（塔頂樓板與牆頂）與重弩、砲', {}, arm['top']['models']),
             ('ladder', 5, 50, '3 層 ⇒ 頂層的直梯', {k: list(v) for k, v in arm['ladder'].items()}, []),
             ('magazine', 6, 60, '火藥間（3 層、木板圍起來）', {k: list(v) for k, v in arm['magazine']['anchors'].items()}, arm['magazine']['models']))
    allc, npart = {}, {}
    for part, lay, order, title, anc, models in PARTS:
        w = ROOT + '-' + part
        cells = cells_of(G, LAY == lay)
        md5 = dump(os.path.join(D, 'masks', w + '.vox.txt'), cells)
        man['works'][w] = {'order': order, 'title': '加拉塔塔 1453｜' + title, 'size': [Xn, Yn, Zn], 'tags': 'sub', 'mask': w + '.vox.txt', 'anchors': anc, 'links': [], 'models': models}
        ver[w] = {'cells': len(cells), 'md5': md5}
        allc.update(cells); npart[part] = len(cells)
    dump(os.path.join(D, 'masks', ROOT + '.composite.txt'), allc)
    meta_body = {'kind': 'building', 'use': 'galata-tower', 'style': 'genoa', 'lot': '32,32', 'base': 0, 'variant': 'a'}   # 特殊建築（Blocksail world/town.js SPECIAL）⇒ use ＝ 那一種（上一版的 model 鍵已刪，9a8d6e42）
    man['works'][ROOT] = {'order': 90, 'title': tower.P['title'], 'size': [Xn, Yn, Zn], 'tags': 'building,genoa', 'mask': None, 'expect': ROOT + '.composite.txt',
                          'anchors': {k: list(v) for k, v in anchors.items()},
                          'sails': [{'name': sail['name'], 'corners': '%s|%s|%s|%s' % (sail['hoist'][0], sail['hoist'][1], '%d,%d,%d' % sail['fly'][0], '%d,%d,%d' % sail['fly'][1]),
                                     'bind': '0', 'free': '2,3', 'color': 255, 'meta': {'kind': 'flag', 'flag': 'ensign', 'pattern': 'genoa'}}],
                          'links': [{'name': '塔身', 'source': ROOT + '-body', 'at': [0, 0, 0], 'turn': 0, 'mirror': '', 'recolor': {}, 'meta': meta_body},
                                    {'name': '屋頂', 'source': ROOT + '-roof', 'at': [0, 0, 0], 'turn': 0, 'mirror': '', 'recolor': {}, 'meta': {'part': 'roof'}},
                                    {'name': '3 層砲甲板', 'source': ROOT + '-deck-gun', 'at': [0, 0, 0], 'turn': 0, 'mirror': '', 'recolor': {},
                                     'meta': {'kind': 'deck', 'deck': 'gun', 'level': 0, 'name': '3 層砲台', 'floor': arm['gundeck']['floor'], 'material': 'stone', 'thick': tower.K}},
                                    {'name': '頂層砲台', 'source': ROOT + '-deck-top', 'at': [0, 0, 0], 'turn': 0, 'mirror': '', 'recolor': {},
                                     'meta': {'kind': 'deck', 'deck': 'top', 'level': 1, 'name': '頂層砲台', 'floor': arm['top']['floor'], 'material': 'stone', 'thick': tower.K}},
                                    {'name': '直梯', 'source': ROOT + '-ladder', 'at': [0, 0, 0], 'turn': 0, 'mirror': '', 'recolor': {}, 'meta': {'kind': 'ladders'}},
                                    {'name': '火藥間', 'source': ROOT + '-magazine', 'at': [0, 0, 0], 'turn': 0, 'mirror': '', 'recolor': {},
                                     'meta': {'kind': 'magazine', 'material': 'wood', 'pos': 'mid', 'powder_lb': arm['magazine']['powder_lb']}}]}
    # 讀數：框外、元件、空腔、浮空；幾個關鍵尺寸從格子量回來（跟 plan.json 比）
    a = G > 0
    lab, n = ndimage.label(a)
    cav = int((ndimage.binary_fill_holes(a) & ~a).sum())
    ground = set(np.unique(lab[0])) - {0}
    floating = [int((lab == i).sum()) for i in range(1, n + 1) if i not in ground]
    mpv = tower.MPV
    yy, xx = np.mgrid[0:Yn, 0:Xn]; R = np.hypot(xx + 0.5 - tower.CX, yy + 0.5 - tower.CY) * mpv
    def r_at(zm):
        z = int(zm / mpv); m = (G[z] > 0) & (R < 12); return round(float(R[m].max()) + mpv / 2, 2) if m.any() else None
    meas = {'外半徑 @10 m': r_at(10.0), '外半徑 @1 m（牆腳）': r_at(1.0), '雉堞外半徑 @30.5 m': r_at(30.5), '簷半徑 @32.1 m': r_at(32.1),
            '石砌頂（m）': round(max(z for z in range(Zn) if ((G[z] > 0) & (R < 7.5) & (R > 5.2)).any() and z < tower.zc(32.0)) * mpv + mpv, 2),   # 5.2：鼓座（4.475～5.075）不算石砌頂
            '錐頂（m）': None, '最高（m）': round((np.nonzero(a.any((1, 2)))[0].max() + 1) * mpv, 2)}
    cone = [z for z in range(Zn) if ((G[z] == 146) | (G[z] == 110)).any() and z >= tower.zc(32.0)]
    meas['錐頂（m）'] = round((max(cone) + 1) * mpv, 2) if cone else None
    ver[ROOT] = {'cells': len(allc), 'components': int(n), 'cavity': cav, 'floating': floating, 'oob': 0, 'measured': meas, 'anchors': {k: list(v) for k, v in anchors.items()}}
    print('格數 %d（%s）元件 %d 空腔 %d 浮空 %s' % (len(allc), '、'.join('%s %d' % kv for kv in npart.items()), n, cav, floating))
    print('量回來', json.dumps(meas, ensure_ascii=False))
    # 格子圖：正面（北，城外）、背面（南）、側面、剖面、俯視
    px = 3 if tower.K == 1 else 2
    ims = [('正面（北・城外）', view(G, 'y')), ('背面（南・城裡）', view(G, 'y', rev=True)), ('側面（從東）', view(G, 'x')), ('剖面 x=%d' % int(tower.CX), section(G, int(tower.CX)))]
    W = sum(i.shape[1] for _, i in ims) * px + 40; H = Zn * px + 40
    im = Image.new('RGB', (W, H + Yn * px + 30), (250, 247, 240)); d = ImageDraw.Draw(im)
    x0 = 10
    for t, a_ in ims:
        im.paste(Image.fromarray(a_).resize((a_.shape[1] * px, a_.shape[0] * px), Image.NEAREST), (x0, 30)); d.text((x0, 8), t, fill=(60, 50, 40)); x0 += a_.shape[1] * px + 10
    top = view(G, 'z'); im.paste(Image.fromarray(top).resize((Xn * px, Yn * px), Image.NEAREST), (10, H + 20))
    im.save(os.path.join(D, 'sheets', 'voxel_views.png'))
    json.dump(man, open(os.path.join(D, 'manifest.json'), 'w', encoding='utf-8', newline='\n'), ensure_ascii=False, indent=1, sort_keys=True)
    json.dump(ver, open(os.path.join(D, 'verify.json'), 'w', encoding='utf-8', newline='\n'), ensure_ascii=False, indent=1, sort_keys=True)


if __name__ == '__main__':
    main()
