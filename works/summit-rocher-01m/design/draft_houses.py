# 岩堡港 新圖紙 02 房屋（TASK-0580）：plan.json 的 houses ⇒ 每個配色一份逐格清單、立面／平面圖紙、verify_houses.json。
# 用法：python -I -X utf8 -B draft_houses.py <design 資料夾> [型 ...]（不給 ⇒ 全部）
#   · 格子由 houses.py 產；圖紙是格子的正投影（正面從 −y 看、側面從 −x 看、背面從 +y 看、平面 ＝ 一樓窗台高的水平切面、屋頂 ＝ 從上看）。
#   · 讀數：格數、各色格數、外框、6 連通元件數、3D 封閉空腔（scipy binary_fill_holes）、固定點。
#   · 清單每行 `x,y,z,color`（相對作品原點；stampvox at=0,0,0 原樣貼）、照 (z, y, x) 排序 ⇒ 重跑逐位元組相同。
import sys, os, json
import numpy as np
from PIL import Image, ImageDraw, ImageFont
from scipy import ndimage

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import houses

FONT = r"C:\Windows\Fonts\msjh.ttc"
BG = (250, 248, 242)
INK = (30, 30, 30)


def rgb332(k):
    return (round((k >> 5) * 255 / 7), round(((k >> 2) & 7) * 255 / 7), (k & 3) * 85)


def font(sz):
    return ImageFont.truetype(FONT, sz)


def to_array(V):
    xs = [k[0] for k in V]; ys = [k[1] for k in V]; zs = [k[2] for k in V]
    if min(xs) < 0 or min(ys) < 0 or min(zs) < 0:  # ⛔ 負座標：numpy 會從尾巴繞回去、悄悄畫到另一頭（B1 的招牌踩過）
        raise SystemExit('負座標：min x %d y %d z %d' % (min(xs), min(ys), min(zs)))
    S = (max(xs) + 1, max(ys) + 1, max(zs) + 1)
    a = np.zeros(S, dtype=np.int16)
    for (x, y, z), c in V.items():
        a[x, y, z] = c
    return a


def structure(a):
    occ = a > 0
    lab, n = ndimage.label(occ, structure=ndimage.generate_binary_structure(3, 1))
    cav = ndimage.binary_fill_holes(occ) & ~occ
    return int(n), int(cav.sum())


def project(a, axis, rev, px, flip=False):
    """正投影：沿 axis 找第一格（rev ＝ 從大的那一端看）；越深越暗一點（好分前後）。回 PIL 圖（上 ＝ z 大）。"""
    occ = a > 0
    n = a.shape[axis]
    idx = np.arange(n)
    if rev:
        idx = idx[::-1]
    b = np.moveaxis(a, axis, 0)[idx]
    o = np.moveaxis(occ, axis, 0)[idx]
    first = np.argmax(o, axis=0)
    has = o.any(axis=0)
    c = np.take_along_axis(b, first[None], axis=0)[0]
    h, w = c.shape[1], c.shape[0]          # (u, z)
    img = np.zeros((c.shape[1], c.shape[0], 3), dtype=np.uint8)
    img[:] = BG
    for u in range(c.shape[0]):
        for z in range(c.shape[1]):
            if has[u, z]:
                r, g, bb = rgb332(int(c[u, z]))
                k = max(0.55, 1.0 - first[u, z] / max(1, n) * 0.9)
                img[c.shape[1] - 1 - z, u] = (int(r * k), int(g * k), int(bb * k))
    im = Image.fromarray(img)
    if flip:                               # 從 −x 看：右手邊是 −y；從 +y 看：右手邊是 −x ⇒ 左右翻（不翻 ＝ 鏡像）
        im = im.transpose(Image.FLIP_LEFT_RIGHT)
    return im.resize((im.width * px, im.height * px), Image.NEAREST)


def plan_cut(a, z, px):
    s = a[:, :, z]
    img = np.zeros((s.shape[1], s.shape[0], 3), dtype=np.uint8)
    img[:] = BG
    for x in range(s.shape[0]):
        for y in range(s.shape[1]):
            if s[x, y]:
                img[y, x] = rgb332(int(s[x, y]))
    im = Image.fromarray(img)
    return im.resize((im.width * px, im.height * px), Image.NEAREST)


def roof_view(a, px):
    occ = a > 0
    top = np.where(occ.any(axis=2), occ.shape[2] - 1 - np.argmax(occ[:, :, ::-1], axis=2), -1)
    img = np.zeros((a.shape[1], a.shape[0], 3), dtype=np.uint8)
    img[:] = BG
    for x in range(a.shape[0]):
        for y in range(a.shape[1]):
            if top[x, y] >= 0:
                r, g, b = rgb332(int(a[x, y, top[x, y]]))
                k = 0.6 + 0.4 * top[x, y] / a.shape[2]
                img[y, x] = (int(r * k), int(g * k), int(b * k))
    im = Image.fromarray(img)
    return im.resize((im.width * px, im.height * px), Image.NEAREST)


def scale_bar(g, x0, y0, px_per_m, meters, f):
    for i in range(meters):
        a = x0 + i * px_per_m
        g.rectangle([a, y0, a + px_per_m, y0 + 6], outline=INK, fill=INK if i % 2 == 0 else BG)
    for i in range(meters + 1):
        g.text((x0 + i * px_per_m - 4, y0 + 9), str(i), fill=INK, font=f)
    g.text((x0 + meters * px_per_m + 10, y0 - 3), "m", fill=INK, font=f)


def sheet(plan, typ, builds, path):
    H = plan['houses'][typ]
    px = 4
    first = builds[0]
    a, meta = first['a'], first['meta']
    f14, f18, f24 = font(14), font(18), font(24)
    front = project(a, 1, False, px)
    side = project(a, 0, False, px, flip=True)
    back = project(a, 1, True, px, flip=True)
    cut = plan_cut(a, meta['floors'][0][0] + 15, px)
    roof = roof_view(a, px)
    others = [project(b['a'], 1, False, px // 2) for b in builds[1:]]
    W = 60 + front.width + 40 + side.width + 40 + back.width + 60
    Hh = 120 + max(front.height, side.height) + 80 + max(cut.height, roof.height) + 140
    im = Image.new('RGB', (max(W, 1760), Hh), BG)
    g = ImageDraw.Draw(im)
    g.text((20, 12), "岩堡港 Port-du-Rocher　新圖紙 02　房屋 " + typ + "：" + H['label'] + "　0.1 m／格　summit 2026-10-14　（設計；沒有描圖）", fill=INK, font=f24)
    y1 = 80
    x = 60
    for title, img in (("正面（從街上看，-y）" + first['variant'], front), ("側面（從左看，-x；右 = 街）", side), ("背面（+y）", back)):
        g.text((x, y1 - 26), title, fill=INK, font=f18)
        im.paste(img, (x, y1 + max(front.height, side.height) - img.height))
        x += img.width + 40
    y2 = y1 + max(front.height, side.height) + 60
    g.text((60, y2 - 26), "一樓平面（z " + str(meta['floors'][0][0] + 15) + " 切面；上 = 街）", fill=INK, font=f18)
    im.paste(cut, (60, y2))
    xr = 60 + max(cut.width, 300) + 40                # 標題比圖寬 ⇒ 照標題留位置（不然兩個標題疊在一起）
    g.text((xr, y2 - 26), "屋頂（從上看）", fill=INK, font=f18)
    im.paste(roof, (xr, y2))
    xo = xr + roof.width + 60
    for b, img in zip(builds[1:], others):
        g.text((xo, y2 - 26), "配色 " + b['variant'] + "（正面，½）", fill=INK, font=f18)
        im.paste(img, (xo, y2))
        xo += max(img.width, 160) + 30
    y3 = y2 + max(cut.height, roof.height) + 30
    scale_bar(g, 60, y3, 10 * px, 8, f14)
    lines = ["讀數（verify_houses.json）"]
    for b in builds:
        R = b['R']
        lines.append(b['variant'] + "：" + str(R['voxels']) + " 格　外框 " + "×".join(str(v) for v in R['bbox']) + "　元件 " + str(R['components']) + "　封閉空腔 " + str(R['cavity']) + "　簷高 " + str(meta['z_eave'] / 10) + " m　屋脊 " + str(meta['z_ridge'] / 10) + " m")
    for i, s_ in enumerate(lines):
        g.text((60 + 8 * 10 * px + 80, y3 - 6 + i * 22), s_, fill=INK, font=f18 if i == 0 else f14)
    im.save(path, optimize=False)


def main():
    d = sys.argv[1]
    plan = json.load(open(os.path.join(d, 'plan.json'), encoding='utf-8'))
    want = sys.argv[2:] or sorted(plan['houses'].keys())
    out = os.path.join(d, 'masks', 'houses')
    os.makedirs(out, exist_ok=True)
    vpath = os.path.join(d, 'verify_houses.json')
    allR = json.load(open(vpath, encoding='utf-8')) if os.path.exists(vpath) else {}
    for typ in want:
        builds = []
        for var in sorted(plan['houses'][typ]['variants'].keys()):
            V, A, meta = houses.build(plan, typ, var)
            a = to_array(V)
            comp, cav = structure(a)
            cols = {}
            for c in V.values():
                cols[str(c)] = cols.get(str(c), 0) + 1
            R = {'voxels': len(V), 'bbox': list(a.shape), 'components': comp, 'cavity': cav, 'colors': cols, 'anchors': A, 'meta': meta}
            with open(os.path.join(out, var + '.vox.txt'), 'w', encoding='utf-8', newline='\n') as fo:
                fo.write("# 岩堡港 房屋 " + typ + " 配色 " + var + "（houses.py；" + str(len(V)) + " 格）\n")
                for (x, y, z) in sorted(V.keys(), key=lambda k: (k[2], k[1], k[0])):
                    fo.write(f"{x},{y},{z},{V[(x, y, z)]}\n")
            allR[var] = R
            builds.append({'variant': var, 'a': a, 'meta': meta, 'R': R})
            print(var, R['voxels'], R['bbox'], 'components', comp, 'cavity', cav)
        sheet(plan, typ, builds, os.path.join(d, 'sheet02_house_' + typ + '_v1.png'))
    with open(vpath, 'w', encoding='utf-8', newline='\n') as fo:
        json.dump(allR, fo, ensure_ascii=False, indent=1, sort_keys=True); fo.write('\n')


if __name__ == '__main__':
    main()
