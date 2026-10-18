# 新圖紙 W：三件武器元件（0.05 m／格；模型 scale 0.5 明寫）—— 全部照大炮規格的座標（造船規格 §4.1）：
#   x 沿船長（砲軸在 x 中線）、y ＝ 砲口方向、z 0 ＝ 甲板面那一層（底座最下面一層格）。
#   固定點：muzzle（砲口內膛／噴口那一格，空格）、breech（砲尾那一格）；另外 pivot（轉的中心，底座正中）。
# 1. siphon   希臘火噴筒：青銅藥槽（下面是炭盆）＋壓力泵（槓桿把手）＋青銅長管＋鍍金獅頭噴口（Anna Komnene 描述的獅頭；設計）。
# 2. ballista 弩砲（toxoballistra）：三腳架＋回轉座＋滑槽＋兩個扭力繩束＋弓臂＋絞盤。
# 3. mangonel 投石機（manganikon，牽引式）：A 字雙架＋軸（mangonel）＋投臂與投袋（mangonel-arm，子模型、會甩）；拉繩、投袋繩是繩。
# 用法：python -I -X utf8 -B draft_weapons.py ⇒ lists/w_<名>.txt、verify_weapons.json、sheetW_weapons.png
import os, sys, json, math
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import dro
from PIL import Image, ImageDraw, ImageFont

D = dro.D
C = dro.C
WOOD, WOOD_D, ROPE, BRONZE, GOLD, IRON, CHAR, EMBER = 136, 100, 177, 172, 212, 73, 36, 224   # 224 ＝ 炭火紅（r7 g0 b0）


class Part:
    def __init__(self, name, size):
        self.name, self.size, self.cells, self.anchors = name, size, {}, {}

    def put(self, x, y, z, c, over=True):
        x, y, z = int(round(x)), int(round(y)), int(round(z))
        sx, sy, sz = self.size
        if not (0 <= x < sx and 0 <= y < sy and 0 <= z < sz):
            raise ValueError('%s 出框 %s' % (self.name, (x, y, z)))
        if over or (x, y, z) not in self.cells:
            self.cells[(x, y, z)] = c

    def box(self, x0, x1, y0, y1, z0, z1, c):
        for x in range(x0, x1 + 1):
            for y in range(y0, y1 + 1):
                for z in range(z0, z1 + 1):
                    self.put(x, y, z, c)

    def cyl_y(self, cx, cz, r, y0, y1, c, hollow_r=None):      # 沿 y 的圓柱（格心判斷）
        for y in range(y0, y1 + 1):
            for x in range(int(cx - r - 1), int(cx + r + 2)):
                for z in range(int(cz - r - 1), int(cz + r + 2)):
                    d = math.hypot(x + 0.5 - cx, z + 0.5 - cz)
                    if d <= r and (hollow_r is None or d > hollow_r):
                        self.put(x, y, z, c)

    def cyl_z(self, cx, cy, r, z0, z1, c, hollow_r=None):
        for z in range(z0, z1 + 1):
            for x in range(int(cx - r - 1), int(cx + r + 2)):
                for y in range(int(cy - r - 1), int(cy + r + 2)):
                    d = math.hypot(x + 0.5 - cx, y + 0.5 - cy)
                    if d <= r and (hollow_r is None or d > hollow_r):
                        self.put(x, y, z, c)

    def line(self, a, b, r, c):                                   # 粗線段（木桿、繩）
        n = int(max(abs(b[i] - a[i]) for i in range(3)) * 2) + 1
        for k in range(n + 1):
            t = k / n
            p = [a[i] + (b[i] - a[i]) * t for i in range(3)]
            for dx in range(-2, 3):
                for dy in range(-2, 3):
                    for dz in range(-2, 3):
                        q = (math.floor(p[0]) + dx, math.floor(p[1]) + dy, math.floor(p[2]) + dz)
                        if math.dist((q[0] + 0.5, q[1] + 0.5, q[2] + 0.5), p) <= r:
                            self.put(*q, c)

    def carve(self, x, y, z):
        self.cells.pop((x, y, z), None)


# ───────────── 1. 希臘火噴筒 ─────────────
def siphon():
    p = Part('siphon', (21, 64, 30))
    cx = 10.5                                     # 砲軸（x 中線 ＝ 第 10 格的格心）
    # 底座：木台車（兩條縱樑＋橫木）＋中間一根立軸（pivot）
    p.box(2, 5, 4, 34, 0, 2, WOOD_D); p.box(15, 18, 4, 34, 0, 2, WOOD_D)
    for y0 in (4, 18, 31):
        p.box(2, 18, y0, y0 + 3, 3, 4, WOOD)
    # 炭盆（鐵）＋炭火
    p.box(6, 14, 8, 16, 3, 4, IRON); p.box(7, 13, 9, 15, 5, 5, EMBER)
    # 青銅藥槽（立著的圓桶，直徑 0.55 m）
    p.cyl_z(cx, 12.5, 5.5, 6, 17, BRONZE)
    p.cyl_z(cx, 12.5, 6.2, 9, 10, GOLD)              # 箍
    p.cyl_z(cx, 12.5, 3.0, 18, 19, BRONZE)           # 蓋與注口
    # 壓力泵：槽前的泵筒＋槓桿（往船尾的把手）
    p.cyl_z(cx, 21.5, 2.5, 5, 18, BRONZE)
    p.line((cx, 21.5, 20), (cx, 2.0, 25), 1.0, WOOD)      # 槓桿
    p.box(5, 16, 1, 2, 24, 26, WOOD)                  # 把手橫桿（兩人壓）
    p.box(9, 11, 21, 22, 19, 21, IRON)                # 槓桿支點
    # 青銅長管：從泵筒頂往前（+y）到獅頭，管軸 z 14.5
    zc = 14.5
    p.cyl_y(cx, zc, 2.0, 22, 52, BRONZE, hollow_r=0.8)
    for y0 in (30, 40, 49):
        p.cyl_y(cx, zc, 2.6, y0, y0 + 1, GOLD, hollow_r=0.8)
    # 管架：兩個木叉托
    for y0 in (33, 45):
        p.box(8, 13, y0, y0 + 1, 3, 11, WOOD); p.box(7, 14, y0, y0 + 1, 12, 12, WOOD)
    # 鍍金獅頭（y 53–61）：頭（近似圓）＋鬃毛環＋張開的嘴（噴口）＋耳朵與眼
    for y in range(53, 62):
        t = (y - 53) / 8
        R = 5.0 - 2.4 * t ** 1.4                       # 前面收成口鼻
        for x in range(0, 21):
            for z in range(4, 26):
                d = math.hypot(x + 0.5 - cx, (z + 0.5 - zc) * 1.05)
                if d <= R:
                    p.put(x, y, z, GOLD)
    p.cyl_y(cx, zc, 6.4, 53, 54, BRONZE, hollow_r=4.4)          # 鬃毛
    for ex in (cx - 3, cx + 2):
        p.put(ex, 56, zc + 3, CHAR)                             # 眼
        p.put(ex, 54, zc + 5, GOLD); p.put(ex, 53, zc + 6, GOLD)   # 耳
    # 嘴：上下顎張開，內膛空；舌（紅）
    for y in range(57, 62):
        for x in range(8, 14):
            for z in range(12, 18):
                p.carve(x, y, z)
    for y in range(57, 61):
        p.put(cx - 0.5, y, 12, EMBER); p.put(cx + 0.5, y, 12, EMBER)
    for x in range(8, 14):
        p.put(x, 61, 17, GOLD); p.put(x, 61, 11, GOLD)          # 牙列
    # 管的內膛一路通到嘴裡
    for y in range(22, 62):
        p.carve(10, y, 14)
    p.anchors = {'muzzle': (10, 60, 14), 'breech': (10, 22, 14), 'pivot': (10, 18, 0), 'tank': (10, 12, 12), 'pump': (10, 2, 25)}
    return p


# ───────────── 2. 弩砲 ─────────────
def ballista():
    p = Part('ballista', (31, 48, 30))
    cx = 15.5
    # 三腳架＋回轉座
    for (fx, fy) in ((3, 6), (28, 6), (15, 30)):
        p.line((fx + 0.5, fy + 0.5, 1.3), (cx, 18.5, 12), 1.2, WOOD_D)
    p.cyl_z(cx, 18.5, 3.5, 12, 13, IRON)
    p.cyl_z(cx, 18.5, 2.0, 0, 13, WOOD_D)
    # 滑槽（沿 y）＋ 托架
    p.box(13, 18, 2, 46, 14, 15, WOOD); p.box(14, 17, 2, 44, 16, 16, WOOD_D)   # 槽溝
    # 前端的弓架（框）：兩根立柱＋上下橫樑；兩側扭力繩束（白麻）
    p.box(5, 26, 38, 41, 14, 15, WOOD); p.box(5, 26, 38, 41, 24, 25, WOOD)
    for x0 in (5, 12, 19, 26):
        p.box(x0, x0, 38, 41, 16, 23, WOOD_D)
    p.box(7, 10, 39, 40, 13, 26, ROPE); p.box(21, 24, 39, 40, 13, 26, ROPE)
    p.box(7, 10, 39, 40, 26, 26, IRON); p.box(21, 24, 39, 40, 26, 26, IRON)
    # 弓臂（往後掠）。弓弦不畫格子：改成兩條繩（meta kind=bowstring，string-a → nock → string-b；Tim 2026-10-18「弩炮的弦是否可以改用繩索 並在開火時有動態」）
    p.line((8.5, 39.5, 20), (1.5, 31.5, 20), 1.0, WOOD)
    p.line((22.5, 39.5, 20), (29.5, 31.5, 20), 1.0, WOOD)
    # 絞盤（後端）＋把手
    p.box(9, 22, 3, 5, 15, 18, WOOD_D)
    p.box(7, 8, 3, 5, 12, 20, IRON); p.box(23, 24, 3, 5, 12, 20, IRON)
    # 箭（鐵頭）
    p.box(15, 15, 20, 44, 17, 17, WOOD); p.box(15, 15, 45, 46, 17, 17, IRON)
    p.carve(15, 47, 17)
    p.anchors = {'muzzle': (15, 47, 17), 'breech': (15, 3, 17), 'pivot': (15, 18, 0),
                 'string-a': (1, 31, 20), 'string-b': (29, 31, 20), 'nock': (15, 20, 17), 'nock-fire': (15, 31, 20)}   # 弓臂尖兩端、扣弦點（拉滿）、放出去之後扣弦點的位置（兩弓臂尖的連線上）
    return p


# ───────────── 3. 投石機 ─────────────
# Tim 2026-10-18：「接著做投石機吧(同時把一些零件換成繩索)」「投石機是否可以給高拋物線彈道(可以砸到甲板)」⇒ 拆成兩件：
#   mangonel      架子（底框、兩座 A 字架、鐵軸）＝ 遊戲裡的「砲」（kind=gun gun=mangonel；Blockside 砲種表 mangonel：石彈、曲射）
#   mangonel-arm  投臂＋投袋（同一個框、同一個座標 ⇒ 放在同一點就對齊）＝ 子模型，meta spin=gun 照開火進度繞鐵軸甩出去、照裝填拉回來
#   拉繩（短臂前端 → 拉繩手手上）、投袋繩（長臂尾端 → 投袋）不畫格子：改成繩（apply_mangonel_ropes.py）；握環拿掉（拉繩下端各自在拉繩手手上）；
#   石彈不畫在投袋裡（開火之後會留在投袋裡；飛出去的那一顆遊戲自己畫）。
MG_SIZE = (41, 72, 64)
MG_CX, MG_YA, MG_ZT = 20.5, 32, 40            # 中線 x、鐵軸 y、鐵軸 z


def mangonel():
    p = Part('mangonel', MG_SIZE)
    cx, ya, zt = MG_CX, MG_YA, MG_ZT
    # 底框（井字）
    p.box(4, 7, 14, 50, 0, 2, WOOD_D); p.box(33, 36, 14, 50, 0, 2, WOOD_D)
    for y0 in (14, 30, 47):
        p.box(4, 36, y0, y0 + 3, 3, 4, WOOD)
    # 兩座 A 字架（左右各一，頂到軸 z 40）
    for xs in (6.0, 35.0):
        p.line((xs, 16.0, 5), (xs, ya + 0.5, zt), 1.3, WOOD)
        p.line((xs, 49.0, 5), (xs, ya + 0.5, zt), 1.3, WOOD)
        p.line((xs, 24.0, 22), (xs, 41.0, 22), 1.0, WOOD_D)
    # 軸（鐵）
    p.box(4, 37, ya - 1, ya + 1, zt - 1, zt + 1, IRON)
    # 砲軸：沿 y 的一條水平線（砲口 ＝ 框前方的空格）；拉繩下端：拉好（rest，拉繩手站著握住）／放出去之後（fire，往下拉到底）
    p.anchors = {'muzzle': (20, 70, 40), 'breech': (20, 6, 40), 'pivot': (20, 32, 0), 'axle': (20, 32, 40)}
    for i, x in enumerate((13, 20, 28)):
        p.anchors['grip-%d' % (i + 1)] = (x, ya + 26, 6)
        p.anchors['grip-%d-fire' % (i + 1)] = (x, ya + 20, 2)
    return p


def mangonel_arm():
    p = Part('mangonel-arm', MG_SIZE)
    cx, ya, zt = MG_CX, MG_YA, MG_ZT
    # 投臂：短臂往前（+y）、長臂往後下（-y，裝填姿勢：投袋在後面的甲板上方）；放出去 ＝ 繞鐵軸（+x）轉 −135°：長臂從後下甩過頭頂到正上方、短臂被拉到正下方
    piv = (cx, ya + 0.5, zt + 0.5)
    front = (cx, ya + 14.5, zt + 9.0)
    back = (cx, 6.0, 9.0)
    p.line(front, piv, 1.6, WOOD); p.line(piv, back, 1.3, WOOD)
    p.box(19, 21, ya + 13, ya + 15, zt + 8, zt + 9, IRON)             # 短臂前端的鐵箍（拉繩綁在這裡）
    # 投袋（皮）：掛在長臂尾端下面（繩是投袋繩）
    p.box(18, 22, 1, 4, 3, 5, 100)
    p.anchors = {'spin-a': (4, ya, zt), 'spin-b': (37, ya, zt),      # 轉軸 ＝ 鐵軸的中心線（+x）
                 'pull-1': (19, ya + 14, zt + 9), 'pull-2': (20, ya + 14, zt + 9), 'pull-3': (21, ya + 14, zt + 9),   # 拉繩上端（短臂前端的鐵箍）
                 'sling': (20, 6, 8), 'pouch-a': (18, 2, 5), 'pouch-b': (22, 2, 5)}                                 # 投袋繩：長臂尾端 → 投袋兩側
    return p


def render(parts):
    S = 6
    W = sum(max(pp.size[0], pp.size[1]) * S + 40 for pp in parts) + 40
    img = Image.new('RGB', (W * 1, 2 * 72 * S + 120), (250, 247, 238))
    g = ImageDraw.Draw(img)
    f = ImageFont.truetype('C:/Windows/Fonts/msjh.ttc', 22)
    g.text((20, 6), '新圖紙 W：武器（0.05 m／格；左：側面 y→右，右：正面）　erina 設計', font=f, fill=(30, 30, 40))
    ox = 20
    for pp in parts:
        sx, sy, sz = pp.size
        # 側面（看 -x 方向）：y 橫、z 縱，取最靠近觀者（x 最大）的格
        best = {}
        for (x, y, z), c in pp.cells.items():
            if (y, z) not in best or x > best[(y, z)][0]:
                best[(y, z)] = (x, c)
        for (y, z), (x, c) in best.items():
            sh = 0.75 + 0.25 * x / sx
            r, gg, b = dro.rgb332(c)
            g.rectangle([ox + y * S, 40 + (sz - z) * S, ox + y * S + S - 1, 40 + (sz - z) * S + S - 1], fill=(int(r * sh), int(gg * sh), int(b * sh)))
        best = {}
        for (x, y, z), c in pp.cells.items():
            if (x, z) not in best or y > best[(x, z)][0]:
                best[(x, z)] = (y, c)
        oy = 40 + sz * S + 30
        for (x, z), (y, c) in best.items():
            r, gg, b = dro.rgb332(c)
            g.rectangle([ox + x * S, oy + (sz - z) * S, ox + x * S + S - 1, oy + (sz - z) * S + S - 1], fill=(r, gg, b))
        for nm, (ax, ay, az) in pp.anchors.items():
            g.ellipse([ox + ay * S, 40 + (sz - az) * S, ox + ay * S + S, 40 + (sz - az) * S + S], outline=(200, 0, 0), width=2)
        g.text((ox, 40 + 2 * sz * S + 40), '%s %dx%dx%d　%d 格' % (pp.name, sx, sy, sz, len(pp.cells)), font=f, fill=(30, 30, 40))
        ox += max(sx, sy) * S + 40
    img.save(os.path.join(D, 'sheetW_weapons.png'))


if __name__ == '__main__':
    parts = [siphon(), ballista(), mangonel(), mangonel_arm()]
    V = {}
    for pp in parts:
        for nm, a in pp.anchors.items():
            if nm in ('muzzle',) and a in pp.cells:
                raise SystemExit('%s 的 muzzle 是實心格' % pp.name)
        n = dro.write_list(os.path.join(D, 'lists', 'w_%s.txt' % pp.name), pp.cells, '持火號 武器元件 %s（0.05 m／格；draft_weapons.py）' % pp.name)
        V[pp.name] = {'size': pp.size, 'cells': n, 'anchors': pp.anchors, 'file': 'lists/w_%s.txt' % pp.name}
    json.dump(V, open(os.path.join(D, 'verify_weapons.json'), 'w', encoding='utf-8'), ensure_ascii=False, indent=1, sort_keys=True)
    render(parts)
    print(json.dumps({k: (v['size'], v['cells']) for k, v in V.items()}, ensure_ascii=False))
