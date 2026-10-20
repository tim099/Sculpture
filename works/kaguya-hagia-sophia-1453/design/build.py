# 產生全部（TASK-0748 聖索菲亞 1453）：python -I -X utf8 -B build.py <design 資料夾>
#   ⇒ masks/<作品 id>.vox.txt、manifest.json（apply.py 照它下 CLI）、verify.json（讀數）、sheets/voxel_views.png（格子的立面、剖面、俯視）。
#   圖紙（照 plan.json 的參數畫、標尺寸）在 draft.py；這裡畫的是「格子長怎樣」，拿來跟圖紙對。
# 決定論：同一份 plan.json ⇒ 逐位元組相同。
import sys, os, json, hashlib
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import numpy as np
from scipy import ndimage
from PIL import Image, ImageDraw
import sophia

ROOT = 'kaguya-hagia-sophia-1453'
PARTS = (('body', 1, 10, '主體（磚牆、扶壁墩、前廊、鐘樓、飛扶壁、穹頂基座、後殿；窗與門）'),
         ('roof', 2, 20, '屋頂（中央穹頂與 40 個窗間墩、半穹頂、壁龕、筒拱、後殿半穹頂、鉛皮屋面、鐘樓尖頂、十字）'),
         ('annex', 3, 30, '附屬（中庭三面迴廊與噴泉、宗主教府、聖器室、洗禮堂）'))


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
    G, L, anchors = sophia.build()
    Zn, Yn, Xn = G.shape
    man = {'root': ROOT, 'mpv': sophia.MPV, 'works': {}}
    ver = {}
    allc = {}
    for part, code, order, title in PARTS:
        cells = cells_of(G, L == code); allc.update(cells)
        w = ROOT + '-' + part
        md5 = dump(os.path.join(D, 'masks', w + '.vox.txt'), cells)
        man['works'][w] = {'order': order, 'title': '聖索菲亞 1453｜' + title, 'size': [Xn, Yn, Zn], 'tags': 'sub', 'mask': w + '.vox.txt', 'anchors': {}, 'links': []}
        ver[w] = {'cells': len(cells), 'md5': md5}
    dump(os.path.join(D, 'masks', ROOT + '.composite.txt'), allc)
    meta_body = {'kind': 'building', 'use': 'hagia-sophia', 'style': 'roman', 'lot': '122,145', 'base': 0, 'variant': 'a'}   # 特殊建築（Blocksail world/town.js SPECIAL）
    man['works'][ROOT] = {'order': 90, 'title': sophia.P['title'], 'size': [Xn, Yn, Zn], 'tags': 'building,roman', 'mask': None, 'expect': ROOT + '.composite.txt',
                          'anchors': {k: list(v) for k, v in anchors.items()},
                          'links': [{'name': '主體', 'source': ROOT + '-body', 'at': [0, 0, 0], 'turn': 0, 'mirror': '', 'recolor': {}, 'meta': meta_body},
                                    {'name': '屋頂', 'source': ROOT + '-roof', 'at': [0, 0, 0], 'turn': 0, 'mirror': '', 'recolor': {}, 'meta': {'part': 'roof'}},
                                    {'name': '附屬', 'source': ROOT + '-annex', 'at': [0, 0, 0], 'turn': 0, 'mirror': '', 'recolor': {}, 'meta': {'part': 'annex'}}]}
    a = G > 0
    lab, n = ndimage.label(a)
    sizes = ndimage.sum(a, lab, range(1, n + 1))
    ground = set(np.unique(lab[0])) - {0}
    floating = sorted([int(sizes[i - 1]) for i in range(1, n + 1) if i not in ground], reverse=True)
    mpv = sophia.MPV
    zs = np.nonzero(a.any((1, 2)))[0]
    # 從格子量回來：穹頂頂、十字頂、主體外框（研究座標）、穹頂在窗間墩上面那一圈的直徑
    ys, xs = np.nonzero(a.any(0))
    Xr = sophia.FX[0] + (ys + 0.5) * mpv; Yr = sophia.FY[1] - (xs + 0.5) * mpv
    lead = (G == sophia.C['lead']) | (G == sophia.C['lead_seam'])
    zc = int(50.0 / mpv); sl = lead[zc]; yy, xx = np.nonzero(sl)
    def ext(v): return round(float(v.max() - v.min()) + mpv, 2) if len(v) else None
    meas = {'最高（m，含十字）': round((zs.max() + 1) * mpv, 2),
            '鉛皮最高（m）': round((np.nonzero(lead.any((1, 2)))[0].max() + 1) * mpv, 2),
            '穹頂 @50 m 東西寬（m）': ext(sophia.FX[0] + (yy + 0.5) * mpv), '穹頂 @50 m 南北寬（m）': ext(sophia.FY[1] - (xx + 0.5) * mpv),
            '框內佔到的 X 範圍（m）': [round(float(Xr.min() - mpv / 2), 1), round(float(Xr.max() + mpv / 2), 1)],
            '框內佔到的 Y 範圍（m）': [round(float(Yr.min() - mpv / 2), 1), round(float(Yr.max() + mpv / 2), 1)]}
    ver[ROOT] = {'cells': len(allc), 'components': int(n), 'floating': floating[:10], 'measured': meas, 'anchors': {k: list(v) for k, v in anchors.items()}}
    print('格數 %d（%s）元件 %d 浮空 %s' % (len(allc), '、'.join('%s %d' % (p, ver[ROOT + '-' + p]['cells']) for p, _, _, _ in PARTS), n, floating[:10]))
    print('量回來', json.dumps(meas, ensure_ascii=False))
    px = 2
    ims = [('西立面（正面）', proj(G, 1)), ('北立面', proj(G, 2)), ('東立面（後殿）', proj(G, 1, rev=True))]
    W = sum(i.shape[1] for _, i in ims) * px + 50; H = Zn * px + 50
    top = proj(G, 0)
    im = Image.new('RGB', (max(W, Xn * px + 20), H + Yn * px + 40), (250, 247, 240)); dr = ImageDraw.Draw(im)
    x0 = 10
    for t, a_ in ims:
        im.paste(Image.fromarray(a_).resize((a_.shape[1] * px, a_.shape[0] * px), Image.NEAREST), (x0, 30)); dr.text((x0, 8), t, fill=(60, 50, 40)); x0 += a_.shape[1] * px + 15
    dr.text((10, H + 12), '俯視（上 ＝ 模型 y 0 ＝ 西、左 ＝ 北）', fill=(60, 50, 40))
    im.paste(Image.fromarray(top).resize((Xn * px, Yn * px), Image.NEAREST), (10, H + 30))
    im.save(os.path.join(D, 'sheets', 'voxel_views.png'))
    json.dump(man, open(os.path.join(D, 'manifest.json'), 'w', encoding='utf-8', newline='\n'), ensure_ascii=False, indent=1, sort_keys=True)
    json.dump(ver, open(os.path.join(D, 'verify.json'), 'w', encoding='utf-8', newline='\n'), ensure_ascii=False, indent=1, sort_keys=True)


if __name__ == '__main__':
    main()
