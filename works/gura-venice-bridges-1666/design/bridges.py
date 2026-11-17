# 威尼斯 1666 的三座橋（Blocksail TASK-1291；Tim 2026-11-17：「新增橋洞高度更高的橋(參考現實資料) 讓大船可以穿過」「大橋可以只有一兩座」「船體至少能過」
#   「跨大運河的橋是否也可以改用高橋」「橋的部件可以支援voxel建造(參考城牆做法)」「吊橋一些部件可以用繩索?(參考目前起重機建築)」「船靠近打開」）。
#
# 一座橋 ＝ 一件城牆式的模組（BUILDING_SPEC §6、§6.9 引水渠的 line 擺法）：kind=wall、part=section、set=<套件>、len、deck、rise；接口 wall-a、wall-b 在中線、最底那一層。
#   座標：x ＝ 沿橋（規劃那一座的 path 從頭到尾；遊戲照弦長把整件沿 x 伸縮）、y ＝ 橫過橋（中線 y = Y/2）、z ＝ 往上；0.2 m／格。
#   z 0 ＝ 水面下 BOT 公尺（遊戲把最底那一層往下延到地面 ⇒ 只有橋台、樁會延下去；拱底那一段最底那一層是空的）。
#   deck ＝ 兩頭的路面在模型裡多高（遊戲擺在 規劃的 z − deck）；rise ＝ 拱背：橋面 ＝ deck ＋ rise · 4u(1 − u)（u ＝ x ÷ 長）——
#     同 Blockside 63_towns.js townBridgeForm 的拋物線 ⇒ 鎮民走的面跟雕的面是同一條（遊戲有模型時照模型的 rise）。
# 史料（研究：本 session 子代理，出處都在 Blocksail docs/evidence/venice1291/README 第 30 步）：
#   里亞托橋 1588–1591 Antonio da Ponte：伊斯特拉石單拱，跨約 28.8 m、拱頂離水 6～7.3 m；拱頂中間一座門廊（兩面山牆），兩坡是台階。
#   San Biasio（o de le Cadene）在兵工廠運河口的斯拉夫人堤岸上；今天是磚石弧拱，1666 年的形制查不到 ⇒ 照威尼斯常見的磚拱＋伊斯特拉石鑲邊。
#   兵工廠橋（水門前）：Carlevarijs 1703、Canaletto 約 1740–45（RCIN 907477）、Guardi 約 1755–60 畫的都是木造吊橋（1938 換固定橋）；1666 年沒有直接證據。
#   遊戲裡的尺寸照遊戲的河寬（拓寬過的兵工廠運河、大運河 43 m）與能過的船（船身頂離水：風暴角號約 8.9 m），不是史實的尺寸。
import os, sys, math

HERE = os.path.dirname(os.path.abspath(__file__))
WORKS = os.path.dirname(os.path.dirname(HERE))
for d in (os.path.join(WORKS, 'gura-venice-housing-1666', 'design'), os.path.join(WORKS, 'summit-bourg-fr-01m', 'design')):
    if d not in sys.path:
        sys.path.insert(0, d)
from common import *                                   # noqa: E402,F401,F403  Model、調色盤（ISTRIA、MATTONE、PAVE、WOOD…）

MPV = 0.2
K = 5                                                  # 一公尺幾格
BOT = 1.5                                              # z 0 ＝ 水面下幾公尺


def m2v(v):
    return int(round(v * K))


def rope(M, name, a, b, color=IRON, thick=0.5, slack=1.0):
    """真的繩（work sub=rope；同 crest-berth-01m/design/berth.py rope）：a、b ＝ 兩端的格座標（可帶小數）、thick ＝ 直徑（格）、slack ＝ 繩長 ÷ 直線距離。"""
    if not hasattr(M, 'ropes'):
        M.ropes = []
    M.ropes.append({'name': name, 'a': [float(v) for v in a], 'b': [float(v) for v in b], 'color': color, 'thick': thick, 'slack': slack})


def arc_z(xm, w0, w1, spring, crown):
    """拱的內弧（弓形，過兩個拱腳 (w0, spring)、(w1, spring) 與拱頂 ((w0 + w1) / 2, crown)）在 xm 的高；拱外 ⇒ None。"""
    if not (w0 < xm < w1):
        return None
    c, s = (w1 - w0) / 2, crown - spring
    R = (c * c + s * s) / (2 * s)
    dx = xm - (w0 + w1) / 2
    return crown - R + math.sqrt(max(0.0, R * R - dx * dx))


def stone_bridge(key, title, L, wet, deck, rise, clr, body_w, walk_w, face, ring, portico=False):
    """石造單拱高橋（里亞托、San Biasio）。L 長、wet ＝ 落水那一段 [起, 迄]（拱腳）、deck ＝ 兩頭路面在模型裡的高、rise ＝ 拱背、clr ＝ 拱頂離水的淨空、
    body_w ＝ 橋身寬、walk_w ＝ 欄杆之間的走道寬、face ＝ 拱肩的牆面色、ring ＝ 拱圈（鑲邊）色；portico ⇒ 拱頂的門廊（里亞托）。"""
    X, Y = m2v(L), m2v(body_w) + 2                     # ＋2：兩側各一格的腰線
    Z = m2v(deck + rise + (8.5 if portico else 2.5))
    M = Model((X, Y, Z))
    yc = Y / 2.0
    y0b, y1b = 1, Y - 1                                # 橋身 [y0b, y1b)
    hw = m2v(walk_w) // 2
    yw0, yw1 = int(yc) - hw, int(yc) + hw              # 走道 [yw0, yw1)
    spring, crown = BOT, BOT + clr
    w0, w1 = wet
    RING = 0.9                                         # 拱圈厚（公尺）
    tops = []
    for x in range(X):
        xm = (x + 0.5) / K
        u = xm / L
        top = deck + rise * 4 * u * (1 - u)
        zt = m2v(top)                                  # 橋面：z < zt 是實心，zt 是第一層空氣
        tops.append(zt)
        ai = arc_z(xm, w0, w1, spring, crown)
        z0 = 0 if ai is None else m2v(ai)
        for z in range(z0, zt):
            zm = (z + 0.5) / K
            in_ring = ai is not None and zm - ai < RING
            for y in range(y0b, y1b):
                side = y in (y0b, y1b - 1)
                if z == z0 and ai is not None:
                    c = ISTRIA_G                       # 拱腹（底下看上去）
                elif side:
                    if in_ring:
                        seg = int(((xm - (w0 + w1) / 2) * 1.25))   # 拱石：每 0.8 m 一塊、兩色交錯
                        c = ring if seg % 2 == 0 else ISTRIA_G
                    else:
                        c = face
                else:
                    c = ISTRIA_G if ai is not None and in_ring else face
                if z == zt - 1 and yw0 <= y < yw1:
                    c = PAVE                           # 走道的石板（trachite）
                M.put('body', x, y, z, c)
        # 腰線（橋面下兩格往外各伸一格）、欄杆
        for z in (zt - 3, zt - 2):
            if z >= z0 + 1:
                M.put('body', x, 0, z, ISTRIA)
                M.put('body', x, Y - 1, z, ISTRIA)
        for (ya, yb) in ((y0b, yw0), (yw1, y1b)):      # 欄杆：底座一層、立柱每 3 格一根（0.6 m）、扶手 2 層
            for y in range(ya, yb):
                M.put('body', x, y, zt, ISTRIA)
                for z in (zt + 4, zt + 5):
                    M.put('body', x, y, z, ISTRIA)
                if x % 3 == 0:
                    for z in range(zt + 1, zt + 4):
                        M.put('body', x, y, z, ISTRIA_G if (ya == y0b and y == ya) or (ya != y0b and y == yb - 1) else ISTRIA)
    if portico:
        # 拱頂的門廊（里亞托：中間一座兩面山牆的拱廊，走道從它底下穿過）：四角的方墩、兩面（朝運河）各一個大拱、頂上山牆、坡頂
        cx = X // 2
        zt = max(tops[cx - 16:cx + 16])
        x0, x1 = cx - 15, cx + 15                      # 6 m
        H1 = m2v(5.0)                                  # 墩高（走道上 5 m）
        for (xa, xb) in ((x0, x0 + 5), (x1 - 5, x1)):
            for (ya, yb) in ((y0b, yw0), (yw1, y1b)):
                for x in range(xa, xb):
                    for y in range(ya, yb):
                        for z in range(tops[x], zt + H1):
                            M.put('body', x, y, z, ISTRIA, force=True)
        for x in range(x0, x1):                        # 頂上的楣（整塊）＋兩面朝運河的拱（照 x 的半圓：拱頂在 zt + H1）
            for y in range(y0b, y1b):
                for z in range(zt + H1 - 3, zt + H1 + 3):
                    M.put('body', x, y, z, ISTRIA, force=True)
            r = (x1 - x0) / 2.0 - 5
            dx = x + 0.5 - cx
            if abs(dx) < (x1 - x0) / 2.0 - 5:
                za = zt + H1 - 3 - int(round(r - math.sqrt(max(0, r * r - dx * dx))))
                for y in (y0b, y1b - 1):
                    for z in range(za, zt + H1 - 3):
                        M.put('body', x, y, z, ISTRIA, force=True)
        for y in range(y0b - 1, y1b + 1):              # 坡頂（屋脊沿 y、兩面朝運河是山牆）：鉛皮
            pass
        for x in range(x0 - 1, x1 + 1):
            h = int(round((((x1 - x0) / 2.0 + 1) - abs(x + 0.5 - cx)) * 0.55))
            for y in range(y0b - 1, y1b + 1):
                for z in range(zt + H1 + 3, zt + H1 + 3 + max(1, h)):
                    M.put('roof', x, y, z, SLATE if y not in (y0b - 1, y1b) else ISTRIA)
    M.anchor('wall-a', 0, int(yc), 0)
    M.anchor('wall-b', X - 1, int(yc), 0)
    meta = {'kind': 'wall', 'part': 'section', 'set': key, 'style': 'venice', 'variant': 'section', 'len': round(X / K, 2), 'deck': deck, 'rise': rise}
    return {'key': key, 'title': title, 'M': M, 'meta': meta, 'layers': {'body': '橋身'} if not portico else {'body': '橋身', 'roof': '門廊的頂'}}


def drawbridge(key, title, L, deck, rise, hinge_a, hinge_b, deck_w, open_deg, gal_h=9.0):
    """木造雙葉吊橋（兵工廠橋）：兩頭固定的木棧（樁＋橫樑＋板）、中間兩片橋板各掛在一座墩上（旋轉件 spin=bridge：船靠近打開）、
    墩上的吊架（兩根柱＋頂樑）拉鐵鍊到橋板的尖端（繩；會動的那一頭在橋板上）。"""
    X, Y = m2v(L), m2v(deck_w) + 8                     # ＋8：兩側吊架的柱子（各 0.8 m）
    Z = m2v(deck + rise + gal_h + 1.5)
    M = Model((X, Y, Z))
    yc = Y / 2.0
    y0d, y1d = 4, Y - 4                                # 橋面 [y0d, y1d)
    T = 2                                              # 板＋樑厚 0.4 m（2 格）
    xa, xb = m2v(hinge_a), m2v(hinge_b)                # 兩片橋板 [xa, xm)、[xm, xb)
    xm = (xa + xb) // 2

    def top(x):
        u = (x + 0.5) / K / L
        return m2v(deck + rise * 4 * u * (1 - u))

    for x in range(X):
        zt = top(x)
        layer = 'body' if x < xa or x >= xb else ('leaf-a' if x < xm else 'leaf-b')
        if x == xm or x == xm - 1:
            pass
        for y in range(y0d, y1d):
            for z in range(zt - T, zt):
                c = WOOD if z == zt - 1 else WOOD_D
                if z == zt - 1 and (x % 4 == 0):
                    c = WOOD_G                         # 板縫
                M.put(layer, x, y, z, c)
        for y in (y0d, y1d - 1):                       # 欄杆：柱每 6 格（1.2 m）＋扶手
            M.put(layer, x, y, zt + 4, WOOD_D)
            if x % 6 == 0:
                for z in range(zt, zt + 4):
                    M.put(layer, x, y, z, WOOD_D)
        if layer == 'body':                            # 固定段的樁：每 2.4 m 一排、三根（兩邊＋中間）、從橋面下到最底
            if x % 12 in (0, 1):
                for y in (y0d, int(yc) - 1, int(yc), y1d - 1):
                    for z in range(0, zt - T):
                        M.put('body', x, y, z, WOOD_G)
                for y in range(y0d, y1d):              # 樁頂的橫樑
                    M.put('body', x, y, zt - T - 1, WOOD_D)
    # 鉸鏈的墩（橋板的根）：一整排粗樁＋石帽，跟吊架
    for (hx, sgn) in ((xa, -1), (xb, 1)):
        xs = range(hx - 5, hx) if sgn < 0 else range(hx, hx + 5)
        for x in xs:
            zt = top(x)
            for y in range(y0d - 1, y1d + 1):
                for z in range(0, zt - T):
                    M.put('body', x, y, z, ISTRIA if z >= zt - T - 3 else WOOD_G, force=True)
        # 吊架：兩根柱（橋面外側）到橋面上 gal_h、頂上一根橫樑（橋板全開時尖端在鉸鏈上 板長 · sin 75° ⇒ 吊架要比它高）
        px = hx - 3 if sgn < 0 else hx + 2
        zt = top(px)
        ztop = zt + m2v(gal_h)
        for y in (1, 2, Y - 3, Y - 2):
            for x in (px, px + 1):
                for z in range(0, ztop):
                    M.put('body', x, y, z, WOOD_D, force=True)
        for y in range(0, Y):
            for x in (px, px + 1):
                for z in (ztop, ztop + 1):
                    M.put('body', x, y, z, WOOD_D, force=True)
        for y in range(3, Y - 3):                      # 斜撐（柱頂兩側往裡）
            pass
    # 鐵鍊：吊架頂樑 ⇒ 橋板尖端（兩邊各一條）；會動的那一頭在橋板上（Blocksail tools/townmodels.py ropes_of 量端點落在哪一件）
    for (hx, tipx, sgn, nm) in ((xa, xm - 1, -1, 'a'), (xb, xm, 1, 'b')):
        px = hx - 3 if sgn < 0 else hx + 2
        ztop = top(px) + m2v(gal_h)
        for (y, side) in ((y0d + 0.5, '左'), (y1d - 0.5, '右')):
            rope(M, '吊鍊-%s-%s' % (nm, side), (px + 1.0, y, ztop - 0.5), (tipx + 0.5, y, top(tipx) + 4.5), color=IRON, thick=0.4, slack=1.0)
    # 旋轉件的軸：橋板根部的下緣、沿 y；左片（往 +x 伸）照右手定則繞 +y 轉負角尖端往上、右片轉正角
    za, zb = top(xa) - T, top(xb - 1) - T
    leaf_meta = {
        'leaf-a': {'part': 'leaf', 'spin': 'bridge', 'spin_mode': 'angle', 'spin_k': -open_deg, 'spin_zero': 0,
                   'spin_pivot_x': float(xa), 'spin_pivot_y': yc, 'spin_pivot_z': float(za), 'spin_axis_x': 0, 'spin_axis_y': 1, 'spin_axis_z': 0},
        'leaf-b': {'part': 'leaf', 'spin': 'bridge', 'spin_mode': 'angle', 'spin_k': open_deg, 'spin_zero': 0,
                   'spin_pivot_x': float(xb), 'spin_pivot_y': yc, 'spin_pivot_z': float(zb), 'spin_axis_x': 0, 'spin_axis_y': 1, 'spin_axis_z': 0}}
    M.anchor('wall-a', 0, int(yc), 0)
    M.anchor('wall-b', X - 1, int(yc), 0)
    meta = {'kind': 'wall', 'part': 'section', 'set': key, 'style': 'venice', 'variant': 'section', 'len': round(X / K, 2), 'deck': deck, 'rise': rise, 'draw': 1}
    return {'key': key, 'title': title, 'M': M, 'meta': meta, 'layers': {'body': '固定段、墩與吊架', 'leaf-a': '左橋板（會動）', 'leaf-b': '右橋板（會動）'},
            'layer_meta': leaf_meta}


# ── 三座（尺寸照 Blocksail main 7a335b32 ＋ 套件橋的規劃：world/townplans/town-venice.json 的那三座 bridges）──
def rialto():
    # p-ponte-di-rialto~br1：長 70.0 m（s 5～75）、落水 13.5～56.5、兩頭面高 1.90／1.83、淨空 9 ⇒ rise ＝ 9 ＋ 0.7 − 1.87 ≈ 7.8
    return stone_bridge('venice-rialto', '里亞托橋（Ponte di Rialto；1591 伊斯特拉石單拱，拱頂門廊；遊戲照大運河 43 m 的河寬、拱頂離水 9 m）',
                        L=70.0, wet=(13.5, 56.5), deck=3.4, rise=7.8, clr=9.0, body_w=10.0, walk_w=8.0, face=ISTRIA, ring=ISTRIA, portico=True)


def biasio():
    # p-ponte-san-biasio-delle-catene~br1：長 87.5 m（s 0～87.5）、落水 13～70（57 m）、兩頭面高 0.30／0.41、淨空 11 ⇒ rise ＝ 11 ＋ 0.7 − 0.36 ≈ 11.3
    return stone_bridge('venice-biasio', 'San Biasio 橋（Ponte San Biasio o de le Cadene；兵工廠運河口、斯拉夫人堤岸；磚拱＋伊斯特拉石鑲邊，拱頂離水 11 m）',
                        L=87.6, wet=(13.0, 70.0), deck=1.8, rise=11.3, clr=11.0, body_w=6.0, walk_w=4.0, face=MATTONE, ring=ISTRIA)


def arsenal():
    # p-ponte-de-l-arsenal~br1（第九輪：岸到岸一條，Tim「另外會需要處理這種沒跨岸的橋」）：長 61.96 m（s 0～61.96）、落水 6～55.5（49.5 m）、兩頭面高 0.57；
    #   開口在落水那一段的正中（30.75 m）：兩片橋板各 9 m ⇒ 船過的寬 18 m；兩頭固定的木棧打樁；吊橋關著的拱背 1.2 m
    return drawbridge('venice-arsenal-draw', '兵工廠吊橋（Ponte de l\'Arsenal；水門前，木造雙葉吊橋、吊架拉鐵鍊；船靠近打開）',
                      L=62.0, deck=2.0, rise=1.2, hinge_a=21.8, hinge_b=39.8, deck_w=4.0, open_deg=75, gal_h=10.5)


ALL = [rialto, biasio, arsenal]
