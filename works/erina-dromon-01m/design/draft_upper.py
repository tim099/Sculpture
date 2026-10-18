# 新圖紙 04：甲板上與艙裡的結構（每一件一份清單；子作品都用整船的框、關聯 at 0,0,0 ⇒ 子作品座標 ＝ 組裝件座標）。
#   forecastle  pseudopation：艏部高起的木板平台（四根柱撐、三面木板胸牆帶垛口），siphon 在它底下（Leo VI《Taktika》§6；ref §6）
#   castles     xylokastra：中桅前、中線兩側各一座木塔（柱＋斜撐＋平台＋垛口胸牆），中間留走道給桅與帆桁放倒（Pryor pp.234–236；尺寸 design）
#   fittings    艉部舵橫樑（through-beam）與兩舷舵箱、艏部兩舷錨架（periboloi）、甲板上的帆腳繫柱
#   magazine    希臘火藥庫（艙底，中段偏後）：前後兩道隔艙壁、後壁開門
#   ladders     五座梯子：艙口兩座（艙底 ↔ 主甲板）、pseudopation 一座、木塔兩座
# 用法：python -I -X utf8 -B draft_upper.py ⇒ lists/<件>.txt、verify_upper.json
import os, sys, json, math
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import numpy as np
import dro

D = dro.D
P = dro.PLAN
C = dro.C
YC = dro.YC
VH = json.load(open(os.path.join(D, 'verify_hull.json'), encoding='utf-8'))
ZAIR = VH['zair']


def load(path):
    a = np.loadtxt(os.path.join(D, path), delimiter=',', comments='#', dtype=int, ndmin=2)
    return {(int(r[0]), int(r[1]), int(r[2])): int(r[3]) for r in a}


HULL = load('lists/hull.txt')
DECK = load('lists/deck_main.txt')
HOLD = load('lists/deck_hold.txt')
TAKEN = set(HULL) | set(DECK) | set(HOLD)


def inner(x, z):
    """舷牆內面的半寬（格心可以放東西的最外那一格離中線的距離）。"""
    w = dro.hb(x + 0.5, z + 0.5)
    return int(math.floor(w - 2.5)) if w >= 0 else -1


class Piece:
    def __init__(self, name):
        self.name, self.cells, self.anchors, self.ladders = name, {}, {}, []

    def put(self, x, y, z, c):
        k = (int(x), int(y), int(z))
        if k in TAKEN:
            return False
        self.cells[k] = c
        return True

    def box(self, x0, x1, y0, y1, z0, z1, c):
        for x in range(x0, x1 + 1):
            for y in range(y0, y1 + 1):
                for z in range(z0, z1 + 1):
                    self.put(x, y, z, c)

    def sym(self, x0, x1, o0, o1, z0, z1, c):   # 兩舷對稱：離中線 o0..o1 格
        self.box(x0, x1, YC + o0, YC + o1, z0, z1, c); self.box(x0, x1, YC - o1, YC - o0, z0, z1, c)


PIECES = {}

# ───────────── forecastle（pseudopation）─────────────
F = Piece('forecastle')
FX0, FX1, FZ = 316, 348, 40            # 平台板在 z 40（上面第一層空氣 z 41）—— 艏甲板（z 25）以上 1.5 m、底下站得下 siphon 的砲班
def fw(x):                                          # 平台半寬：舷牆內面，往前收窄的地方往外挑出（最少 8 格）—— 戰鬥平台比船殼寬一點
    w = inner(x, ZAIR[x] + 8)
    return max(w, 10 - max(0, x - (FX1 - 5)) * 2) if w >= 0 else -1
for x in range(FX0, FX1 + 1):
    w = fw(x)
    if w < 2:
        continue
    for y in range(YC - w, YC + w + 1):
        F.put(x, y, FZ, C['deck'])
        if (x - FX0) % 6 == 0:
            F.put(x, y, FZ - 1, C['beam'])        # 平台底下的橫木
    # 兩側胸牆（板）＋垛口：每 5 格留一格缺口在頂上兩層
    for side in (-1, 1):
        y = YC + side * w
        for z in range(FZ + 1, FZ + 10):
            if z >= FZ + 8 and (x - FX0) % 5 == 2:
                continue
            F.put(x, y, z, C['castle'])
# 前胸牆（最前那一排）：留 siphon 噴口上面那段實心
xf = FX1
wf = fw(xf)
for y in range(YC - wf, YC + wf + 1):
    for z in range(FZ + 1, FZ + 5):                   # 前胸牆低（0.4 m）：平台上的弩砲往前打要越過它
        F.put(xf, y, z, C['castle'])
# 後緣：低欄杆（中間留梯口 y ±3）
for y in range(YC - fw(FX0), YC + fw(FX0) + 1):
    if abs(y - YC) <= 3:
        continue
    for z in range(FZ + 1, FZ + 4):
        F.put(FX0, y, z, C['castle'])
# 柱：四根 2×2，從艏甲板到平台底
for (px, off) in ((FX0 + 1, None), (FX1 - 6, None)):
    w = inner(px, ZAIR[px] + 8)
    for side in (-1, 1):
        yy = YC + side * (w - 1)
        for z in range(ZAIR[px], FZ):
            F.box(px, px + 1, min(yy, yy + side), max(yy, yy + side), z, z, C['beam'])
PIECES['forecastle'] = F

# ───────────── castles（xylokastra）─────────────
K = Piece('castles')
KX0, KX1, KO0, KO1, KZ = 206, 237, 4, 20, 38      # x 3.2 m、離中線 4..20（寬 1.7 m）、平台板 z 38（甲板 z 21 以上 1.7 m）
for x in range(KX0, KX1 + 1):
    for o in range(KO0, KO1 + 1):
        for s in (-1, 1):
            K.put(x, YC + s * o, KZ, C['deck'])
    if (x - KX0) % 6 == 0:
        K.sym(x, x, KO0, KO1, KZ - 1, KZ - 1, C['beam'])
# 柱（四角＋中間各一）、斜撐
for px in (KX0, (KX0 + KX1) // 2, KX1 - 1):
    for po in (KO0, KO1 - 1):
        K.sym(px, px + 1, po, po + 1, ZAIR[px], KZ - 1, C['beam'])
for z in range(ZAIR[KX0] + 1, KZ - 1):
    t = (z - ZAIR[KX0]) / (KZ - 1 - ZAIR[KX0])
    xa = int(KX0 + 2 + t * (KX1 - KX0 - 4) / 2)       # X 形斜撐（外側那一面）
    xb = int(KX1 - 2 - t * (KX1 - KX0 - 4) / 2)
    K.sym(xa, xa, KO1, KO1, z, z, C['beam']); K.sym(xb, xb, KO1, KO1, z, z, C['beam'])
# 胸牆：四面，頂上兩層垛口（每 5 格缺一格）；後面（x KX0）中間留梯口
for x in range(KX0, KX1 + 1):
    for z in range(KZ + 1, KZ + 10):
        cren = z >= KZ + 8
        for o, edge in ((KO1, True), (KO0, True)):
            if cren and (x - KX0) % 5 == 2:
                continue
            if o == KO1 and 219 <= x <= 234 and z >= KZ + 2:
                continue                              # 弩砲的射口（外胸牆中段開低）
            K.sym(x, x, o, o, z, z, C['castle'])
for o in range(KO0, KO1 + 1):
    for z in range(KZ + 1, KZ + 10):
        cren = z >= KZ + 8
        if not (cren and (o - KO0) % 5 == 2):
            K.sym(KX1, KX1, o, o, z, z, C['castle'])
        if 10 <= o <= 14:
            continue                                   # 梯口
        if not (cren and (o - KO0) % 5 == 2):
            K.sym(KX0, KX0, o, o, z, z, C['castle'])
# 木橋：兩座塔在弩砲那一段（x 222..230）用平台高度的木板接起來 —— 送藥手站在中線、兩舷的砲手互相支援；
#   橋的前後照樣是走道（中桅的帆桁照舊放得倒）；橋那一段的內胸牆拿掉
BX0, BX1 = 222, 230
for x in range(BX0, BX1 + 1):
    for o in range(-KO0 + 1, KO0):
        K.put(x, YC + o, KZ, C['deck'])
for k in [k for k in K.cells if BX0 <= k[0] <= BX1 and abs(k[1] - YC) == KO0 and k[2] > KZ]:
    del K.cells[k]
for x in (BX1 + 1,):                                  # 橋前緣的低欄杆（0.3 m；後緣是梯口）
    for o in range(-KO0 + 1, KO0):
        for z in range(KZ + 1, KZ + 4):
            K.put(x, YC + o, z, C['castle'])
# 掛盾：胸牆外側每 4 格一面圓盾（紅／藍交替，0.5 m）—— 盾是格子（不當裝飾模型：它是牆的一部分）
PIECES['castles'] = K

# ───────────── fittings ─────────────
G = Piece('fittings')
# 舵橫樑：x 70..73，穿過船殼兩舷、伸出 0.9 m；在甲板上 z ZAIR..+2
RB_X0, RB_X1 = 70, 73
zb = ZAIR[RB_X0] + 3
wout = int(dro.hb(RB_X0 + 0.5, zb + 0.5)) + 9
for x in range(RB_X0, RB_X1 + 1):
    for y in range(YC - wout, YC + wout + 1):
        for z in range(zb, zb + 3):
            G.put(x, y, z, C['beam'])
# 舵箱：橫樑兩頭各一個框（舵桿穿過的地方），x 66..77、離中線 wout-4..wout、z zb-6..zb+5
RUD_O = wout - 2                                     # 舵桿的離中線距離
for s in (-1, 1):
    for x in range(RB_X0 - 4, RB_X1 + 5):
        for o in (RUD_O - 2, RUD_O + 2):
            for z in range(zb - 5, zb + 6):
                if x in (RB_X0 - 4, RB_X1 + 4) or z in (zb - 5, zb + 5):
                    G.put(x, YC + s * o, z, C['beam'])
    for x in (RB_X0 - 4, RB_X1 + 4):
        for o in range(RUD_O - 2, RUD_O + 3):
            for z in (zb - 5, zb + 5):
                G.put(x, YC + s * o, z, C['beam'])
# 錨架（periboloi）：艏部兩舷 x 328..330 伸出 0.7 m，z 舷牆頂下 2 格
CX = 328
zc = ZAIR[CX] + 5
wc = int(dro.hb(CX + 0.5, zc + 0.5))
for x in range(CX, CX + 3):
    for s in (-1, 1):
        for o in range(wc - 6, wc + 8):
            for z in range(zc, zc + 2):
                G.put(x, YC + s * o, z, C['beam'])
# 帆腳繫柱（每舷兩根，中段舷牆內側）
for bx in (150, 240):
    w = inner(bx, ZAIR[bx] + 2)
    G.sym(bx, bx + 1, w - 1, w, ZAIR[bx], ZAIR[bx] + 5, C['beam'])
G.anchors = {'rudder-axis-S': (RB_X0 + 1, YC + RUD_O, zb + 1), 'rudder-axis-P': (RB_X0 + 1, YC - RUD_O, zb + 1),
             'cathead-S': (CX + 1, YC + wc + 7, zc + 1), 'cathead-P': (CX + 1, YC - wc - 7, zc + 1),
             'bitt-150-S': (150, YC + inner(150, ZAIR[150] + 2), ZAIR[150] + 5), 'bitt-150-P': (150, YC - inner(150, ZAIR[150] + 2), ZAIR[150] + 5),
             'bitt-240-S': (240, YC + inner(240, ZAIR[240] + 2), ZAIR[240] + 5), 'bitt-240-P': (240, YC - inner(240, ZAIR[240] + 2), ZAIR[240] + 5)}
for z in range(51, 62):                              # 艉旗桿：艉柱頭上面（旗 ensign 掛在 x 40.5、z 54–61）
    G.put(40, YC, z, C['beam'])
G.put(40, YC, 62, C['gold'])
for s_ in (-1, 1):                                   # 舵桿孔：舵軸周圍 r 1.8 的格拿掉（舵桿從橫樑頭的孔穿過）
    ay = YC + s_ * RUD_O
    for k in [k for k in G.cells if math.hypot(k[0] + 0.5 - (RB_X0 + 1.5), k[1] + 0.5 - (ay + 0.5)) <= 1.8]:
        del G.cells[k]
PIECES['fittings'] = G

# ───────────── magazine（希臘火藥庫）─────────────
M = Piece('magazine')
MX0, MX1 = 130, 147                                 # 隔艙壁讓開下層第 6、8 位的槳口與槳手（plan provenance；原本 128／146）
hz = P['deck_hold']['z']
for x in (MX0, MX1):
    for y in range(0, dro.NY):
        for z in range(hz + 1, ZAIR[x] - 2):
            if dro.hb(x + 0.5, z + 0.5) < abs(y + 0.5 - dro.YM):
                continue
            if x == MX0 and abs(y - YC) <= 2 and z <= hz + 12:
                continue                             # 門洞 5 格寬、1.2 m 高
            M.put(x, y, z, C['beam'])
M.anchors = {'blast': ((MX0 + MX1) // 2, YC, hz + 6), 'door': (MX0, YC, hz + 1)}
PIECES['magazine'] = M

# ───────────── ladders ─────────────
L = Piece('ladders')


def ladder(name, x_foot, x_head_edge, z_foot_air, z_head_air, y0, y1, step=3):
    """斜梯：沿 x 走（x_foot → x_head_edge），每 step 格高一階。踏板 ＝ (x, y0..y1, z)；兩側梯幫。回傳四個固定點。"""
    dirx = 1 if x_head_edge > x_foot else -1
    n = (z_head_air - z_foot_air) // step
    run = abs(x_head_edge - x_foot)
    treads = []
    for k in range(1, n + 1):
        z = z_foot_air + k * step - 1
        x = x_foot + dirx * int(round(run * k / (n + 1)))
        for y in range(y0, y1 + 1):
            L.put(x, y, z, C['beam'])
        treads.append((x, z))
    # 梯幫：兩條斜木
    for k in range(0, 4 * (n + 1) + 1):
        t = k / (4 * (n + 1))
        x = int(round(x_foot + dirx * run * t))
        z = int(round(z_foot_air - 1 + (z_head_air - z_foot_air) * t))
        for y in (y0 - 1, y1 + 1):
            L.put(x, y, z, C['beam'])
    ym = (y0 + y1) // 2
    lo, hi = treads[0], treads[-1]
    an = {name + '.foot': (x_foot - dirx * 2, ym, z_foot_air), name + '.lo': (lo[0], ym, lo[1] + 1),
          name + '.hi': (hi[0], ym, hi[1] + 1), name + '.head': (x_head_edge + dirx * 2, ym, z_head_air)}
    L.anchors.update(an)
    L.ladders.append(name)


# 艙口梯（艙口 x 112..120、296..304，hw 4）：梯腳在艙底走道（z hz+1 是空氣），梯頭在艙口外的甲板面
ladder('hold-aft', 123, 112, hz + 1, ZAIR[110], YC - 2, YC + 2)
ladder('hold-fore', 293, 304, hz + 1, ZAIR[306], YC - 2, YC + 2)
ladder('forecastle', 307, FX0 - 1, ZAIR[308], FZ + 1, YC - 2, YC + 2)
ladder('castle', 210, BX0 - 1, ZAIR[210], KZ + 1, YC - 2, YC + 2)   # 中線梯：主甲板 → 兩座塔之間的木橋（塔的後門留著當出入口）
PIECES['ladders'] = L

# ───────────── 讀數與輸出 ─────────────
OUT = {}
seen = set(TAKEN)
for nm, pc in PIECES.items():
    ov = sum(1 for k in pc.cells if k in seen)
    seen |= set(pc.cells)
    n = dro.write_list(os.path.join(D, 'lists', nm + '.txt'), pc.cells, '持火號 %s（draft_upper.py）' % nm)
    mir = sum(1 for (x, y, z) in pc.cells if (x, dro.mirror_y(y), z) not in pc.cells)
    OUT[nm] = {'file': 'lists/%s.txt' % nm, 'cells': n, 'overlap_prev': ov, 'mirror_diff': mir, 'anchors': pc.anchors, 'ladders': pc.ladders}
OUT['_geo'] = {'forecastle': [FX0, FX1, FZ], 'castles': [KX0, KX1, KO0, KO1, KZ], 'rudder': {'x': RB_X0 + 1, 'o': RUD_O, 'zb': zb},
               'magazine': [MX0, MX1], 'cathead': [CX, wc, zc]}
json.dump(OUT, open(os.path.join(D, 'verify_upper.json'), 'w', encoding='utf-8'), ensure_ascii=False, indent=1, sort_keys=True)
print(json.dumps({k: (v['cells'], v['overlap_prev'], v['mirror_diff']) for k, v in OUT.items() if k[0] != '_'}, ensure_ascii=False), OUT['_geo'])
