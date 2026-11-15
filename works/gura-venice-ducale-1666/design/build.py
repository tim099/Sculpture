# -*- coding: utf-8 -*-
"""威尼斯總督宮（Palazzo Ducale，1666）重做 —— gura 2026-11-14（TASK-1216）。

Tim 2026-11-14「總督府 希望重頭修改一下(每層檢查) 目前感覺很多細節需要優化 包含有一座樓梯被封死 以及內部構造不合理
可以參考現實圖紙 資料 以及由妳判斷 重新修改細節」

座標（作品格，0.2 m／格；框 360 × 370 × 160）：
  x：北（大教堂那一邊，0）→ 南（Molo 碼頭，359）　← 從小廣場面向宮看：左 → 右（地塊 rot 180，正面朝西）
  y：西（聖馬可小廣場 Piazzetta，0）→ 東（宮殿河 Rio di Palazzo，369）
  z：0 ＝ 地面那一層（實心），往上

照真的配置（it.wikipedia Palazzo Ducale；visitmuve 導覽）：
  · 三翼圍中庭，北邊接大教堂（中庭北邊是福斯卡里門廊 Porticato Foscari ＋ 福斯卡里拱門 Arco Foscari）。
  · 外立面（Molo、Piazzetta）：底層哥德柱廊（Molo 17 拱、Piazzetta 17 拱）＋ 二樓敞廊（雙倍的拱、四葉飾圓洞）＋ 上半粉白菱格牆（大尖窗、中央大陽台：Molo 1404、Piazzetta 1536）＋ 頂上鏤空雉堞。
  · 南翼二樓（主樓層）整翼是大議會廳 Sala del Maggior Consiglio（53 × 25 m，牆上天堂圖、東端總督席）；西翼主樓層是投票廳 Sala dello Scrutinio。
  · 東翼（Rizzo 文藝復興，沿河）：地面（南段是地牢 Pozzi）、敞廊層、主樓層（北段總督寓所）、二樓（元老院、十人會議…）、鉛頂下的閣樓（Piombi）。
  · 樓梯：巨人階梯 Scala dei Giganti（中庭 → 東翼敞廊；正對福斯卡里拱門與紙門 Porta della Carta 那一條軸）、
    黃金階梯 Scala d'Oro（東翼：敞廊 → 主樓層 → 二樓）、審查官階梯 Scala dei Censori（南翼：地面 → 敞廊 → 大議會廳）、西翼北端的樓梯（地面 → 敞廊 → 投票廳）。
  · 中庭兩口青銅井欄（16 世紀中）。

樓層（z）：地面 0（實心）｜底層 1–33｜樓板 34–36｜敞廊層 37–61｜樓板 62–64｜主樓層 65–121（兩廳一整層挑高；東翼 65–91、樓板 92–94、95–121）｜天花 122–123｜屋頂、雉堞 122 以上。

產出（scratchpad/ducale/out/）：body.txt（主作品）、glass.txt（窗玻璃子作品）、metal.txt（青銅子作品）、grid.npz（自檢用）。
"""
import math, os, sys
import numpy as np

OUT = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'out')   # 產出（不進版控）
SX, SY, SZ = 360, 370, 160

# ── 色（RGB332 ＝ r3 g3 b2）──
MARBLE = 254     # 伊斯特拉白石（柱、拱、窗框、雉堞）
STONE = 218      # 暖白石／室內灰泥
STONE_S = 182    # 陰面石、鋪地
PINK = 214       # 維羅納粉紅大理石（菱格）
PORPH = 137      # 深紅大理石
BRICK = 173      # 磚（中庭立面、北牆）
LEAD = 182       # 鉛皮屋頂（灰；146 畫出來太藍）
SEAM = 146       # 鉛皮接縫、屋脊
DARK = 36        # 深色（壁龕、畫裡的暗部）
LAPIS = 42       # 青金藍（紋章底）
GOLD = 248       # 金（獅子、星）
GOLD_S = 212     # 暗金（畫框、天花格）
WOOD = 104       # 木（梁、長椅、護牆板）
WOOD_D = 68      # 深木
GLASS = 46       # 窗玻璃（子作品；同其他地標）
BRONZE = 140     # 青銅（井欄；子作品 material=bronze）
BRONZE_D = 104

g = np.zeros((SX, SY, SZ), np.uint8)     # 主作品
gl = np.zeros((SX, SY, SZ), bool)       # 玻璃
mt = np.zeros((SX, SY, SZ), np.uint8)   # 青銅


def B(x0, x1, y0, y1, z0, z1, c, a=None):
    """填盒子（含兩端）；c 0 ＝ 挖空。a ＝ 填哪一份（預設主作品）。"""
    a = g if a is None else a
    x0, x1 = max(0, x0), min(SX - 1, x1)
    y0, y1 = max(0, y0), min(SY - 1, y1)
    z0, z1 = max(0, z0), min(SZ - 1, z1)
    if x0 <= x1 and y0 <= y1 and z0 <= z1:
        a[x0:x1 + 1, y0:y1 + 1, z0:z1 + 1] = c


def C(x0, x1, y0, y1, z0, z1):
    B(x0, x1, y0, y1, z0, z1, 0)
    B(x0, x1, y0, y1, z0, z1, False, gl)


# ── 平面（見檔頭）──
Z_G0, Z_G1 = 1, 33          # 底層的空氣
Z_L0, Z_L1 = 37, 61         # 敞廊層
Z_U0, Z_U1 = 65, 121        # 主樓層（兩廳）
Z_P1 = (65, 91)             # 東翼主樓層
Z_P2 = (95, 121)            # 東翼二樓
Z_TOP = 121                 # 牆頂
Z_CEIL = (122, 123)         # 天花

# 外立面柱列（底層 6 格厚；敞廊以上 4 格，貼外面）
PZ = (5, 10)      # 小廣場（西）柱列 y；外面 y 5
MO = (349, 354)   # Molo（南）柱列 x；外面 x 354
RIO = (365, 368)  # 河邊牆 y；外面 y 368
NW = (0, 3)       # 北牆 x（大教堂那邊）
# 中庭柱列（底層 6 格；樓上 4 格，貼中庭那一面）
CW = (90, 95)     # 西翼中庭柱列 y（面 y 95）
CS = (230, 235)   # 南翼中庭柱列 x（面 x 230）
CE = (280, 285)   # 東翼中庭柱列 y（面 y 280）
CN = (30, 35)     # 北邊福斯卡里門廊柱列 x（面 x 35），y 90–179
ARCO = (180, 195)  # 福斯卡里拱門 y


def massing():
    B(0, SX - 1, 0, SY - 1, 0, 0, STONE_S)                       # 地面一層（中庭、廣場邊、碼頭邊）
    B(32, 354, 5, 95, 0, 123, STONE)                             # 西翼
    B(230, 354, 5, 368, 0, 123, STONE)                           # 南翼（含東南角）
    B(0, 354, 280, 368, 0, 123, STONE)                           # 東翼
    B(0, 31, 5, 95, 0, 64, STONE)                                # 北端（紙門後面的通道上面兩層）
    B(0, 35, 96, 195, 0, 64, STONE)                              # 福斯卡里門廊那一條
    B(0, 3, 196, 279, 0, 72, BRICK)                              # 中庭北邊：大教堂南牆那一面


# ── 拱廊 ──
def arcade(axis, lo, hi, s0, s1, cols, z0, z1, spring, cap, ch, R, style, face_t, bal=False, qf=None, spc=STONE, colc=MARBLE, round_cols=True):
    """一排柱廊：axis 'x' ＝ 柱沿 x 排（柱列佔 y lo..hi）；'y' ＝ 沿 y（柱列佔 x lo..hi）。
    cols：柱心（沿排的方向，格座標；格 s 的中心 s＋0.5）；兩根之間開拱：z0..拱頂挖空，拱 R ＝ 半徑倍數（尖拱 >1、圓拱 1）。
    整條先填成拱肩色，再挖拱、修柱。cap：柱頭從哪一格起（到 spring 前一格）；ch：柱的半寬。
    bal：敞廊的欄杆；qf：(z 中心, 半徑) 四葉飾圓洞，開在每根柱子正上方。face_t：外面那一格（畫框線用）。"""
    def put(s, t, z, c):
        if axis == 'x': g[s, t, z] = c
        else: g[t, s, z] = c
    def get(s, t, z):
        return g[s, t, z] if axis == 'x' else g[t, s, z]
    T = range(lo, hi + 1)
    for s in range(s0, s1 + 1):
        for t in T:
            for z in range(z0, z1 + 1): put(s, t, z, spc)
    tc = (lo + hi + 1) / 2.0
    for a, b in zip(cols[:-1], cols[1:]):
        w = (b - a) / 2.0 - ch; m = (a + b) / 2.0; Rr = R * w
        for s in range(int(math.floor(a)), int(math.ceil(b)) + 1):
            if s < s0 or s > s1: continue
            u = w - abs(s + 0.5 - m)
            if u <= 0: continue
            top = spring + math.sqrt(max(0.0, Rr * Rr - (Rr - min(u, Rr)) ** 2)) if R > 0 else spring
            zt = min(z1 + 1, int(round(top)))
            for t in T:
                for z in range(z0, zt): put(s, t, z, 0)
                if bal:
                    for z in range(z0, min(z0 + 5, zt)):
                        if z in (z0, z0 + 4) or (s % 2 == 0 and abs(t + 0.5 - tc) < 1.6): put(s, t, z, MARBLE)
            # 拱圈：拱頂上一圈白石（外面那一格）
            if zt <= z1 and z0 < zt:
                put(s, face_t, zt, MARBLE)
                if zt + 1 <= z1: put(s, face_t, zt + 1, MARBLE)
    # 柱：柱身修圓（柱頭以下）、柱頭比柱寬一格
    for k, c in enumerate(cols):
        for s in range(int(math.floor(c - ch - 1)), int(math.ceil(c + ch + 1)) + 1):
            if s < s0 or s > s1: continue
            d = abs(s + 0.5 - c)
            for t in T:
                for z in range(z0, spring):
                    if z >= cap:
                        if d <= ch + 1.0: put(s, t, z, MARBLE)
                    elif d <= ch:
                        r = math.hypot(s + 0.5 - c, t + 0.5 - tc)
                        if round_cols and 0 < k < len(cols) - 1 and r > ch + 0.35 and not bal: put(s, t, z, 0)
                        else: put(s, t, z, colc)
    if qf:
        qz, qr = qf
        for c in cols[1:-1]:
            for s in range(int(c - qr - 2), int(c + qr + 3)):
                if s < s0 or s > s1: continue
                for z in range(int(qz - qr - 2), int(qz + qr + 3)):
                    ds, dz = s + 0.5 - c, z + 0.5 - qz
                    lobe = min(math.hypot(ds - ox, dz - oz) for ox, oz in ((qr * .45, 0), (-qr * .45, 0), (0, qr * .45), (0, -qr * .45)))
                    rr = math.hypot(ds, dz)
                    for t in T:
                        if lobe <= qr * .55: put(s, t, z, 0)
                        elif rr <= qr + 1.2 and t == face_t: put(s, t, z, MARBLE)


def cols_between(a, b, n):
    return [a + (b - a) * k / n for k in range(n + 1)]


def transverse(axis, lo, hi, s0, s1, z0, z1, spring, w_in):
    """柱廊裡橫跨的拱（撐上面的牆）：沿 axis 那一段 s0..s1（牆厚）填滿，再在 lo..hi（廊寬）開尖拱。"""
    for s in range(s0, s1 + 1):
        for t in range(lo, hi + 1):
            for z in range(z0, z1 + 1):
                if axis == 'x': g[s, t, z] = STONE
                else: g[t, s, z] = STONE
    m = (lo + hi + 1) / 2.0; w = (hi - lo + 1) / 2.0 - w_in; R = 1.3 * w
    for t in range(lo, hi + 1):
        u = w - abs(t + 0.5 - m)
        if u <= 0: continue
        top = spring + math.sqrt(max(0.0, R * R - (R - min(u, R)) ** 2))
        for s in range(s0, s1 + 1):
            for z in range(z0, min(z1 + 1, int(round(top)))):
                if axis == 'x': g[s, t, z] = 0
                else: g[t, s, z] = 0


# ── 窗、門 ──
def opening(face, pos, c, w, z0, spring, R, depth, glass=True, frame=MARBLE, mull=False, style='pointed'):
    """在牆上開窗：face ＝ 'x+'（牆面朝 +x，外面那一格 x＝pos）、'x-'、'y+'、'y-'；c 沿牆的中心（格座標，可小數）；w 半寬。
    depth：牆厚（往裡幾格）；玻璃在中間那一格；frame 外面一圈框；mull：中梃＋頂上小圓（哥德窗的花格）。"""
    ax = face[0]; sg = 1 if face[1] == '+' else -1
    lay = [pos - sg * i for i in range(depth)]       # 外 → 裡
    mid = lay[depth // 2]
    Rr = R * w
    apex = spring + (math.sqrt(max(0.0, Rr * Rr - (Rr - w) ** 2)) if R > 0 else 0)
    for s in range(int(math.floor(c - w - 2)), int(math.ceil(c + w + 2)) + 1):
        u = w - abs(s + 0.5 - c)
        for z in range(z0 - 1, int(apex) + 3):
            if u > 0:
                top = spring + (math.sqrt(max(0.0, Rr * Rr - (Rr - min(u, Rr)) ** 2)) if R > 0 else 0)
                inside = z0 <= z < top
            else:
                inside = False
            ring = False
            if not inside:
                uu = w + 1 - abs(s + 0.5 - c)
                if uu > 0 and z0 - 1 <= z:
                    R2 = R * (w + 1) if R > 0 else 0
                    top2 = spring + (math.sqrt(max(0.0, R2 * R2 - (R2 - min(uu, R2)) ** 2)) if R > 0 else 1)
                    ring = z < top2 + 1
            for L in lay:
                xx, yy = (L, s) if ax == 'x' else (s, L)
                if not (0 <= xx < SX and 0 <= yy < SY and 0 <= z < SZ): continue
                if inside:
                    g[xx, yy, z] = 0
                    if glass and L == mid: gl[xx, yy, z] = True
                    rc = spring + (apex - spring) * 0.45
                    if mull and L == lay[0] and ((abs(s + 0.5 - c) < 0.6 and z < rc - w * 0.42 + 1) or abs(math.hypot(s + 0.5 - c, z + 0.5 - rc) - w * 0.42) < 0.8):
                        g[xx, yy, z] = MARBLE; gl[xx, yy, z] = False
                elif ring and L == lay[0] and frame and g[xx, yy, z]:
                    g[xx, yy, z] = frame
    # 窗台
    for s in range(int(math.floor(c - w - 1)), int(math.ceil(c + w + 1)) + 1):
        xx, yy = (lay[0], s) if ax == 'x' else (s, lay[0])
        if 0 <= xx < SX and 0 <= yy < SY and g[xx, yy, z0 - 1]: g[xx, yy, z0 - 1] = MARBLE


def door(face, pos, c, w, z0, h, depth, frame=None):
    """門洞（方頭、上面一格過梁）：沿牆中心 c、半寬 w、從 z0 起高 h。"""
    ax = face[0]; sg = 1 if face[1] == '+' else -1
    for i in range(depth):
        L = pos - sg * i
        for s in range(int(math.floor(c - w)), int(math.ceil(c + w))):
            if abs(s + 0.5 - c) > w: continue
            for z in range(z0, z0 + h):
                if ax == 'x': g[L, s, z] = 0; gl[L, s, z] = False
                else: g[s, L, z] = 0; gl[s, L, z] = False
    if frame:
        L = pos
        for s in range(int(math.floor(c - w - 1)), int(math.ceil(c + w + 1))):
            for z in range(z0, z0 + h + 1):
                ok = abs(s + 0.5 - c) > w or z == z0 + h
                if not ok: continue
                if ax == 'x' and g[L, s, z]: g[L, s, z] = frame
                if ax == 'y' and g[s, L, z]: g[s, L, z] = frame


def cdoor(axis, s0, s1, c, w, z0, h):
    """隔間牆上的門（牆沿 axis 方向的厚度 s0..s1；門沿另一軸中心 c）。axis 'x' ＝ 牆的厚在 x（牆沿 y 延伸）。"""
    for s in range(s0, s1 + 1):
        for t in range(int(math.floor(c - w)), int(math.ceil(c + w))):
            if abs(t + 0.5 - c) > w: continue
            for z in range(z0, z0 + h):
                if axis == 'x': g[s, t, z] = 0
                else: g[t, s, z] = 0


# ── 樓梯 ──
def flight(lane, run_axis, start, d, z_base, n, tread, color=STONE, solid=False):
    """一跑：lane ＝ (t0, t1) 跑道寬（另一軸）；從 start 沿 run_axis 往 d（±1）走；第 i 階（1..n）頂 ＝ z_base＋i、深 tread 格。
    solid ⇒ 底下填到地；否則每階往下 3 格（斜的樓梯底）。"""
    t0, t1 = lane
    for i in range(1, n + 1):
        a = start + d * (i - 1) * tread
        ss = [a + d * k for k in range(tread)]
        top = z_base + i
        bot = 0 if solid else max(0, top - 3)
        for s in ss:
            for t in range(t0, t1 + 1):
                for z in range(bot, top + 1):
                    if run_axis == 'x': g[s, t, z] = color if z == top else STONE
                    else: g[t, s, z] = color if z == top else STONE
                for z in range(top + 1, top + 12):
                    if run_axis == 'x': g[s, t, z] = 0
                    else: g[t, s, z] = 0
    return start + d * n * tread     # 下一格


def doglegs(name, run_axis, lane1, lane2, s_land, s_start, d, segs, wall_out, ztop_shaft, center):
    """一座雙跑樓梯（每一段 ＝ 一層到下一層：兩跑、中間平台）。
    run_axis 跑的方向；lane1／lane2 兩條跑道（另一軸）；s_land..s_start−d ＝ 下端平台（各層的落腳處）；
    segs ＝ [(z_floor_top, rise_total, tread)…]；center ＝ (c0, c1) 中間的牆（另一軸）；
    回傳每一層落腳平台的 z（給自檢）。"""
    lands = []
    for zf, rise, tread in segs:
        h1 = rise // 2; h2 = rise - h1
        # 第一跑：lane1 往 d，從 zf 起 h1 階
        nxt = flight(lane1, run_axis, s_start, d, zf, h1, tread)
        zm = zf + h1
        # 中間平台：nxt 起 10 格（兩條跑道都鋪）
        lo_t = min(lane1[0], lane2[0]); hi_t = max(lane1[1], lane2[1])
        mid = [nxt + d * k for k in range(10)]
        for s in mid:
            for t in range(lo_t, hi_t + 1):
                for z in range(zm - 2, zm + 1):
                    if run_axis == 'x': g[s, t, z] = STONE
                    else: g[t, s, z] = STONE
                for z in range(zm + 1, zm + 12):
                    if run_axis == 'x': g[s, t, z] = 0
                    else: g[t, s, z] = 0
        # 第二跑：lane2 往 −d，從 nxt−d 起 h2 階（回到 s_start 那一頭）
        flight(lane2, run_axis, nxt - d, -d, zm, h2, tread)
        lands.append(zf + rise)
    return lands


# ════════════════════════ 蓋 ════════════════════════
massing()

# ── 底層（z 1–33）挖空 ──
G0, G1 = Z_G0, Z_G1
C(36, 348, 11, 28, G0, G1)            # 西外柱廊（小廣場）
C(329, 348, 11, 364, G0, G1)          # 南外柱廊（Molo）
C(36, 253, 33, 68, G0, G1)            # 西翼房間帶
C(36, 253, 73, 89, G0, G1)            # 西翼中庭柱廊
C(236, 253, 73, 303, G0, G1)          # 南翼中庭柱廊
C(4, 253, 286, 303, G0, G1)           # 東翼中庭柱廊
C(258, 324, 33, 303, G0, G1)          # 南翼房間帶
C(4, 324, 308, 364, G0, G1)           # 東翼房間帶
C(8, 27, 11, 95, G0, 28)              # 紙門後的通道（Andito Foscari）
C(4, 29, 96, 179, G0, G1)             # 福斯卡里門廊
# 天花：底層的天花（樓板底那一層）用木梁
# ── 敞廊層（z 37–61）──
L0, L1 = Z_L0, Z_L1
C(36, 350, 9, 28, L0, L1)             # 西外敞廊（柱列樓上 4 格厚 ⇒ 從 y 9 起）
C(329, 350, 9, 364, L0, L1)           # 南外敞廊
C(36, 253, 33, 68, L0, L1)
C(36, 253, 73, 91, L0, L1)            # 西翼中庭敞廊（柱列 y 92–95）
C(234, 253, 73, 303, L0, L1)          # 南翼中庭敞廊（柱列 x 230–233）
C(4, 253, 284, 303, L0, L1)           # 東翼中庭敞廊（柱列 y 280–283）
C(258, 324, 33, 303, L0, L1)
C(4, 324, 308, 364, L0, L1)
C(4, 29, 11, 91, L0, L1)              # 北端：紙門後面樓上一間（y 92–95 是牆，接中庭那一排）
C(4, 31, 96, 179, L0, L1)             # 福斯卡里門廊樓上的敞廊（柱列 x 32–35）
# ── 主樓層 ──
C(36, 229, 9, 91, Z_U0, Z_U1)         # 投票廳 Sala dello Scrutinio
C(234, 350, 9, 279, Z_U0, Z_U1)       # 大議會廳 Sala del Maggior Consiglio（23.4 × 54.2 m）
C(4, 350, 284, 364, Z_P1[0], Z_P1[1])  # 東翼主樓層
C(4, 350, 284, 364, Z_P2[0], Z_P2[1])  # 東翼二樓

# ── 外柱廊、敞廊 ──
# 小廣場（西）：17 拱，柱心 x 34.5 → 351.5；敞廊雙倍
colsW = cols_between(34.5, 351.5, 17)
arcade('x', 5, 10, 32, 354, colsW, G0, G1, spring=23, cap=19, ch=3, R=1.3, style='pointed', face_t=5)
arcade('x', 5, 8, 32, 354, cols_between(34.5, 351.5, 34), L0, L1, spring=49, cap=46, ch=2, R=1.5, style='pointed', face_t=5, bal=True, qf=(56.5, 3.6))
# Molo（南）：17 拱，柱心 y 7.5 → 365.5
colsS = cols_between(7.5, 365.5, 17)
arcade('y', 349, 354, 5, 368, colsS, G0, G1, spring=23, cap=19, ch=3, R=1.3, style='pointed', face_t=354)
arcade('y', 351, 354, 5, 368, cols_between(7.5, 365.5, 34), L0, L1, spring=49, cap=46, ch=2, R=1.5, style='pointed', face_t=354, bal=True, qf=(56.5, 3.6))
# 西南角的大柱（兩排共用）、西北端、東南端的墩
B(349, 354, 5, 10, G0, L1, MARBLE)
B(32, 37, 5, 10, G0, L1, MARBLE)
B(349, 354, 363, 368, G0, L1, MARBLE)
# 樓板外緣的白石帶（底層拱頂上那一條）
B(32, 354, 5, 5, 34, 36, MARBLE); B(354, 354, 5, 368, 34, 36, MARBLE)
B(32, 354, 5, 5, 62, 64, MARBLE); B(354, 354, 5, 368, 62, 64, MARBLE)

# ── 中庭柱廊（西、南、北：哥德磚；東：Rizzo 圓拱）──
arcade('x', 90, 95, 30, 235, cols_between(32.5, 232.5, 10), G0, G1, spring=22, cap=18, ch=3, R=1.25, style='pointed', face_t=95, spc=BRICK)
arcade('x', 92, 95, 30, 235, cols_between(32.5, 232.5, 20), L0, L1, spring=50, cap=47, ch=2, R=1.4, style='pointed', face_t=95, bal=True, spc=BRICK)
arcade('y', 230, 235, 90, 285, cols_between(92.5, 282.5, 10), G0, G1, spring=22, cap=18, ch=3, R=1.25, style='pointed', face_t=230, spc=BRICK)
arcade('y', 230, 233, 90, 285, cols_between(92.5, 282.5, 20), L0, L1, spring=50, cap=47, ch=2, R=1.4, style='pointed', face_t=230, bal=True, spc=BRICK)
arcade('x', 280, 285, 4, 235, cols_between(6.5, 232.5, 12), G0, G1, spring=21, cap=18, ch=3, R=1.0, style='round', face_t=280, spc=MARBLE, colc=STONE)
arcade('x', 280, 283, 4, 235, cols_between(6.5, 232.5, 24), L0, L1, spring=50, cap=47, ch=2, R=1.0, style='round', face_t=280, bal=True, spc=MARBLE, colc=STONE)
arcade('y', 30, 35, 90, 179, cols_between(92.5, 177.5, 4), G0, G1, spring=22, cap=18, ch=3, R=1.25, style='pointed', face_t=35, spc=BRICK)
arcade('y', 32, 35, 90, 179, cols_between(92.5, 177.5, 8), L0, L1, spring=50, cap=47, ch=2, R=1.4, style='pointed', face_t=35, bal=True, spc=BRICK)
# 中庭角柱
for (xa, xb, ya, yb) in ((230, 235, 90, 95), (230, 235, 280, 285), (30, 35, 90, 95)):
    B(xa, xb, ya, yb, G0, L1, MARBLE)

# ── 橫拱（撐上面的牆）──
transverse('x', 11, 28, 230, 233, G0, G1, 22, 1)       # 投票廳｜大議會廳的牆，跨西外柱廊
transverse('x', 9, 28, 230, 233, L0, L1, 50, 1)
transverse('x', 73, 89, 230, 233, G0, G1, 22, 1)       # 跨西翼中庭柱廊
transverse('x', 73, 91, 230, 233, L0, L1, 50, 1)
transverse('y', 236, 253, 280, 283, G0, G1, 22, 1)     # 大議會廳｜東翼的牆，跨南翼中庭柱廊
transverse('y', 234, 253, 280, 283, L0, L1, 50, 1)
transverse('y', 329, 348, 280, 283, G0, G1, 22, 1)     # 跨 Molo 柱廊
transverse('y', 329, 350, 280, 283, L0, L1, 50, 1)

# ── 隔間（底層、敞廊層）──
def wall_x(x0, x1, y0, y1, levels):
    for z0, z1 in levels: B(x0, x1, y0, y1, z0, z1, STONE)


LV = [(G0, G1), (L0, L1)]
# 西翼房間帶 x 36..253, y 33..68：隔牆
for xa in (116, 176):
    wall_x(xa, xa + 1, 33, 68, LV)
wall_x(230, 233, 33, 68, LV)                     # 上面兩廳之間那道牆
wall_x(254, 257, 33, 68, LV)                     # 接南翼
# 南翼房間帶 x 258..324, y 33..303：隔牆（沿 y 的厚度）
for ya in (98, 139, 156, 200, 250):
    wall_x(258, 324, ya, ya + 1, LV)
wall_x(258, 324, 280, 283, LV)                   # 大議會廳｜東翼那道牆底下
# 東翼房間帶 x 4..324, y 308..364
for xa in (60, 110, 206, 256):
    wall_x(xa, xa + 1, 308, 364, LV)
# 紙門通道兩邊的牆已在（massing）；北端樓上那一間 x 4..29
# 地牢（Pozzi）：東南 x 258..324, y 308..364 的底層
C(258, 324, 332, 339, G0, 14)
for xa in range(258, 325, 14):
    B(xa, xa + 1, 308, 331, G0, G1, STONE); B(xa, xa + 1, 340, 364, G0, G1, STONE)
B(258, 324, 330, 331, 15, G1, STONE); B(258, 324, 340, 341, 15, G1, STONE)
B(258, 324, 308, 331, 15, G1, STONE); B(258, 324, 340, 364, 15, G1, STONE)   # 地牢低矮：上面填實（牢房高 2.8 m）
for xa in range(258, 325, 14):
    cx = xa + 8
    if cx + 2 <= 324:
        cdoor('y', 330, 331, cx, 2, G0, 11); cdoor('y', 340, 341, cx, 2, G0, 11)
cdoor('x', 256, 257, 335.5, 3, G0, 13)          # 地牢走道接隔壁房間

# ── 主樓層、東翼的隔間 ──
for xa in (60, 110, 146, 206, 256, 300):
    B(xa, xa + 1, 284, 364, Z_P1[0], Z_P2[1], STONE)

# ════ 樓梯 ════
# A 巨人階梯（中庭 → 東翼敞廊；x 6..31，往東升；第 i 階頂 z i）
for i in range(1, 36):
    y0 = 200 + 2 * (i - 1)
    B(6, 31, y0, y0 + 1, 0, i, MARBLE if i % 2 else STONE)
B(6, 31, 270, 279, 0, 36, MARBLE)                # 頂上的平台（總督加冕的地方）
for i in range(0, 36):                           # 兩邊的白石欄（比階面高 5 格）
    y0 = 200 + 2 * i
    top = min(36, i + 1)
    for yy in (y0, y0 + 1):
        if yy > 279: continue
        B(4, 5, yy, yy, 0, top + 5, MARBLE); B(32, 33, yy, yy, 0, top + 5, MARBLE)
B(4, 5, 270, 279, 0, 41, MARBLE); B(32, 33, 270, 279, 0, 41, MARBLE)
# 戰神、海神（台座＋立像）
for xa in (6, 28):
    B(xa, xa + 3, 274, 278, 37, 41, MARBLE)
    B(xa + 1, xa + 2, 275, 277, 42, 56, STONE)          # 身
    B(xa, xa + 3, 275, 277, 50, 53, STONE)              # 肩、臂
    B(xa + 1, xa + 2, 275, 277, 57, 59, STONE)          # 頭
# 敞廊欄杆在階梯頂那一段打開
_bal = g[6:32, 280:284, L0:L0 + 5]
_bal[_bal == MARBLE] = 0
B(6, 31, 280, 283, 34, 36, MARBLE)

# B 審查官階梯（南翼：地面 → 敞廊 → 大議會廳；跑 x 方向）
#   井 x 258..313、y 101..118（跑道 y 101..108、111..118，中牆 y 109..110），下端平台 x 258..265
C(258, 313, 99, 120, G0, 64)
B(258, 313, 99, 100, G0, 64, STONE); B(258, 313, 119, 120, G0, 64, STONE); B(312, 313, 99, 120, G0, 64, STONE)
landsB = doglegs('B', 'x', (101, 108), (111, 118), 258, 266, 1, [(0, 36, 2), (36, 28, 2)], None, 64, (109, 110))
B(266, 301, 109, 110, G0, 47, STONE)              # 中牆
B(266, 293, 109, 110, 48, 69, STONE)
B(258, 265, 101, 118, 34, 36, STONE)              # 敞廊層的落腳平台
B(258, 265, 101, 118, 62, 64, STONE)              # 大議會廳的落腳平台（跟廳的地板同高）
cdoor('x', 254, 257, 104.5, 3.5, G0, 13)          # 從南翼中庭柱廊進樓梯
cdoor('x', 254, 257, 104.5, 3.5, L0, 13)          # 敞廊層一樣
# 廳裡：樓梯井四周的欄杆（落腳平台那一邊開著）
B(266, 313, 99, 100, 65, 69, MARBLE); B(266, 313, 119, 120, 65, 69, MARBLE); B(312, 313, 99, 120, 65, 69, MARBLE)
B(258, 265, 99, 100, 62, 64, STONE); B(258, 265, 119, 120, 62, 64, STONE)

# C 黃金階梯 Scala d'Oro（東翼：敞廊 → 主樓層 → 二樓；跑 x）
#   井 x 148..205、y 316..347；跑道 y 318..329、334..345（中牆 330..333）；下端平台 x 150..161
C(150, 203, 318, 345, 37, 121)
B(148, 149, 316, 347, 34, 121, STONE); B(204, 205, 316, 347, 34, 121, STONE)
B(148, 205, 316, 317, 34, 121, STONE); B(148, 205, 346, 347, 34, 121, STONE)
landsC = doglegs('C', 'x', (318, 329), (334, 345), 150, 162, 1, [(36, 28, 2), (64, 30, 2)], None, 121, (330, 333))
B(162, 189, 330, 333, 34, 121, STONE)
for zf in (36, 64, 94):
    B(150, 161, 318, 345, zf - 2, zf, GOLD_S if zf > 36 else STONE)
for zf in (Z_L0, Z_P1[0], Z_P2[0]):
    cdoor('y', 316, 317, 155.5, 4, zf, 14)        # 每層從平台出去
cdoor('y', 304, 307, 155.5, 4, L0, 14)            # 敞廊 → 前廳
B(148, 205, 308, 315, 34, 36, STONE)              # 前廳的地
# 金色拱頂（黃金階梯的名字）：井頂那一層天花
B(150, 203, 318, 345, 121, 121, GOLD_S)

# D 西翼北端的樓梯（地面 → 敞廊 → 投票廳；跑 x）
#   井 x 36..91、y 33..52；跑道 y 33..40、43..50（中牆 41..42）；下端平台 x 36..43
C(36, 91, 33, 52, G0, 64)
B(36, 91, 51, 52, G0, 64, STONE); B(90, 91, 33, 52, G0, 64, STONE)
landsD = doglegs('D', 'x', (33, 40), (43, 50), 36, 44, 1, [(0, 36, 2), (36, 28, 2)], None, 64, (41, 42))
B(44, 79, 41, 42, G0, 47, STONE)
B(44, 71, 41, 42, 48, 69, STONE)
B(36, 43, 33, 50, 34, 36, STONE); B(36, 43, 33, 50, 62, 64, STONE)
cdoor('y', 51, 52, 39.5, 3.5, G0, 13); cdoor('y', 51, 52, 39.5, 3.5, L0, 13)
B(44, 91, 31, 32, 65, 69, MARBLE); B(44, 91, 51, 52, 65, 69, MARBLE); B(90, 91, 31, 52, 65, 69, MARBLE)
B(36, 43, 51, 52, 62, 64, STONE)

# ════ 門（房間 ↔ 柱廊）════
# 西翼房間：朝外柱廊（牆 y 29..32）與中庭柱廊（牆 y 69..72）
for z0 in (G0, L0):
    for cx in (100, 146, 206, 244):
        cdoor('y', 29, 32, cx, 3.5, z0, 14)
    for cx in (66, 146, 206, 244):
        cdoor('y', 69, 72, cx, 3.5, z0, 14)
    for cx in (148,):
        cdoor('x', 116, 117, 50, 3, z0, 13); cdoor('x', 176, 177, 50, 3, z0, 13); cdoor('x', 230, 233, 50, 3, z0, 13); cdoor('x', 254, 257, 50, 3, z0, 13)
    # 南翼房間：朝 Molo 柱廊（牆 x 325..328）、中庭柱廊（x 254..257）
    for cy in (60, 130, 178, 225, 266, 293):
        cdoor('x', 325, 328, cy, 3.5, z0, 14)
    for cy in (60, 130, 178, 225, 266, 293):
        cdoor('x', 254, 257, cy, 3.5, z0, 14)
    for ya in (98, 139, 156, 200, 250):
        cdoor('y', ya, ya + 1, 318, 3, z0, 13)
    cdoor('y', 280, 283, 318, 3, z0, 13)
    # 東翼房間：朝中庭柱廊（牆 y 304..307）
    for cx in (32, 85, 128, 230):
        cdoor('y', 304, 307, cx, 3.5, z0, 14)
    for xa in (60, 110, 206):
        cdoor('x', xa, xa + 1, 336, 3, z0, 13)
    if z0 == L0: cdoor('x', 325, 328, 336, 3.5, z0, 14)          # 東南角的房間朝 Molo 柱廊（底層那裡是地牢，不開）
# 敞廊層東翼：x 112..147 那一間接前廳；前廳 x 148..205 y 308..315
cdoor('y', 304, 307, 290, 3.5, L0, 14)            # 東南角（地牢上面）那一間
# 敞廊層的地牢那一塊是辦公室：拆掉底層的牢房牆（只在底層）
# Porta del Frumento：Molo 柱廊 → 南翼 → 中庭柱廊 的穿堂（底層，y 140..155）
C(254, 328, 141, 154, G0, 26)
# 紙門通道 → 福斯卡里門廊：通道已挖；北端樓上那一間的門
cdoor('y', 92, 95, 16, 4, L0, 13)                  # 北端樓上那一間 → 門廊樓上的敞廊
cdoor('x', 30, 35, 60, 3, L0, 13)                  # 北端樓上那一間 → 西翼敞廊層房間
# 東翼底層北端：門廊東端（福斯卡里拱門以東是中庭）

# ════ 主樓層的門 ════
cdoor('x', 230, 233, 45, 4, Z_U0, 18)              # 投票廳 ↔ 大議會廳
cdoor('y', 280, 283, 300, 4, Z_U0, 18)             # 大議會廳 ↔ 東翼主樓層
cdoor('y', 280, 283, 330, 4, Z_U0, 16)
for xa in (60, 110, 146, 206, 256, 300):
    for zf in (Z_P1[0], Z_P2[0]):
        cdoor('x', xa, xa + 1, 296, 3.5, zf, 15)
        cdoor('x', xa, xa + 1, 356, 3, zf, 14)
cdoor('x', 32, 35, 70, 3.5, Z_U0, 14)              # 投票廳 → 北端屋頂平台
# 閣樓（Piombi）不開門（真的是從東翼的小梯上去；這一版不做）

# ════ 立面 ════
def diaper_face(axis, pos, s0, s1, z0, z1):
    """粉白菱格（外面那一格）：白石的斜格線（每 10 格）、中間粉紅、格心一點白。"""
    for s in range(s0, s1 + 1):
        for z in range(z0, z1 + 1):
            xx, yy = (s, pos) if axis == 'x' else (pos, s)
            if g[xx, yy, z] == 0: continue
            d1 = (s + z) % 12; d2 = (s - z) % 12
            c = MARBLE if (d1 == 0 or d2 == 0) else (STONE if (s % 12 == 6 and z % 12 == 0) or (s % 12 == 0 and z % 12 == 6) else PINK)
            g[xx, yy, z] = c


# 上半的牆：小廣場 y 5..8（外面 y 5）、Molo x 351..354（外面 x 354）
# 窗（哥德大尖窗）：大議會廳、投票廳的窗台 z 74、起拱 98
WIN_W = [58.0, 100.0, 142.0, 244.0, 286.0, 328.0]
for c in WIN_W:
    opening('y-', 5, c, 7, 74, 98, 1.3, 4, mull=True)
WIN_M = [36.0, 86.0, 196.0, 246.0]
for c in WIN_M:
    opening('x+', 354, c, 7, 74, 98, 1.3, 4, mull=True)
for c in (304.0, 340.0):                                            # 東翼那一段：兩扇矮的（主樓層）＋上面兩扇小的（二樓）
    opening('x+', 354, c, 6, 70, 83, 1.3, 4, mull=True)
    opening('x+', 354, c, 4, 100, 109, 1.3, 4)
for c in (61.0, 221.0):                                             # 頂上的小圓窗
    opening('x+', 354, c, 3.5, 108, 111.5, 1.0, 4)
for c in (79.0, 307.0):
    opening('y-', 5, c, 3.5, 108, 111.5, 1.0, 4)
diaper_face('y', 354, 5, 368, 65, 119)
diaper_face('x', 5, 32, 354, 65, 119)
# 再畫一次窗框（菱格蓋掉了）
for c in WIN_W: opening('y-', 5, c, 7, 74, 98, 1.3, 4, mull=True)
for c in WIN_M: opening('x+', 354, c, 7, 74, 98, 1.3, 4, mull=True)
for c in (304.0, 340.0):
    opening('x+', 354, c, 6, 70, 83, 1.3, 4, mull=True); opening('x+', 354, c, 4, 100, 109, 1.3, 4)
for c in (61.0, 221.0): opening('x+', 354, c, 3.5, 108, 111.5, 1.0, 4)
for c in (79.0, 307.0): opening('y-', 5, c, 3.5, 108, 111.5, 1.0, 4)
# 簷口（挑出一格）
B(355, 355, 5, 368, 120, 121, MARBLE); B(32, 355, 4, 4, 120, 121, MARBLE)
B(32, 354, 5, 5, 120, 121, MARBLE); B(354, 354, 5, 368, 120, 121, MARBLE)
# 角上的細柱（扭繩紋的角柱）
for (xa, ya) in ((354, 5), (354, 368), (32, 5)):
    for z in range(65, 122):
        g[xa, ya, z] = MARBLE if z % 3 else PINK

# ── 屋頂 ──
def roof():
    H = np.full((SX, SY), -1, np.int32)
    rects = [(230, 354, 5, 283, 2.5), (32, 233, 5, 95, 2.5), (0, 354, 280, 368, 2.5)]
    X, Y = np.meshgrid(np.arange(SX), np.arange(SY), indexing='ij')
    for x0, x1, y0, y1, k in rects:
        inside = (X >= x0) & (X <= x1) & (Y >= y0) & (Y <= y1)
        d = np.minimum(np.minimum(X - x0, x1 - X), np.minimum(Y - y0, y1 - Y))
        h = 122 + (d / k).astype(np.int32)
        H = np.where(inside, np.maximum(H, h), H)
    for x in range(SX):
        for y in range(SY):
            h = H[x, y]
            if h < 0: continue
            dx_dom = True
            col = SEAM if ((x + y) % 5 == 0) else LEAD
            for z in range(max(122, h - 2), h + 1):
                if z == h: g[x, y, z] = col
                elif g[x, y, z] == 0 or z >= 124: g[x, y, z] = LEAD
    # 屋脊
    for x in range(1, SX - 1):
        for y in range(1, SY - 1):
            h = H[x, y]
            if h > 124 and h >= H[x - 1, y] and h >= H[x + 1, y] and h >= H[x, y - 1] and h >= H[x, y + 1]:
                g[x, y, h] = SEAM
    return H


Hroof = roof()
# 閣樓：天花上、屋頂下挖空（Piombi）
for x in range(SX):
    for y in range(SY):
        h = Hroof[x, y]
        if h >= 127:
            g[x, y, 124:h - 2] = 0



def balcony(face, c, color_top):
    """中央大陽台（Molo 1404、小廣場 1536）：挑出 5 格的陽台、欄杆、兩邊的墩與尖頂、上面的山花與正義女神像。"""
    if face == 'x+':
        def P(a, b, s0, s1, z0, z1, col): B(354 + a, 354 + b, s0, s1, z0, z1, col)   # a/b：往外幾格（0 ＝ 牆面）
        sgn = 1
    else:
        def P(a, b, s0, s1, z0, z1, col): B(s0, s1, 5 - b, 5 - a, z0, z1, col)
        sgn = -1
    w = 9
    opening(face, 354 if face == 'x+' else 5, c, w, 65, 100, 1.3, 4, glass=False, mull=False)   # 陽台門：開著（出得去陽台）
    P(1, 5, int(c - 17), int(c + 17), 62, 64, MARBLE)                  # 陽台板
    for k in range(int(c - 15), int(c + 16), 6): P(1, 3, k, k + 1, 56, 61, STONE)   # 托架
    P(5, 5, int(c - 17), int(c + 17), 65, 70, MARBLE)                  # 欄杆
    P(1, 5, int(c - 17), int(c - 17), 65, 70, MARBLE); P(1, 5, int(c + 17), int(c + 17), 65, 70, MARBLE)
    for k in range(int(c - 16), int(c + 17), 2): P(5, 5, k, k, 66, 69, 0)
    P(5, 5, int(c - 16), int(c + 16), 66, 66, MARBLE)
    for sx in (-1, 1):                                                 # 兩邊的墩 ＋ 尖頂
        s0 = int(c + sx * (w + 3)) - (2 if sx > 0 else 0); s1 = s0 + 2
        P(0, 2, s0, s1, 65, 128, MARBLE)
        P(0, 1, s0, s1, 129, 136, PINK); P(0, 0, s0 + 1, s0 + 1, 137, 140, GOLD_S)
        for z in range(72, 124, 10): P(2, 2, s0, s1, z, z + 4, DARK)     # 壁龕
        for z in range(76, 120, 10): P(2, 2, s0 + 1, s0 + 1, z, z + 2, STONE)   # 龕裡的小像
    for dz in range(0, 14):                                            # 尖山花（窗頂上）
        hw = max(1, 11 - dz)
        P(0, 1, int(c - hw), int(c + hw), 112 + dz, 112 + dz, MARBLE if dz % 4 else PINK)
    P(1, 1, int(c - 4), int(c + 4), 113, 120, LAPIS)                   # 聖馬可之獅（藍底金獅）
    P(1, 1, int(c - 3), int(c + 2), 115, 118, GOLD); P(1, 1, int(c + 2), int(c + 3), 117, 119, GOLD)
    P(0, 1, int(c - 2), int(c + 2), 126, 127, MARBLE)                  # 正義女神像：座
    P(0, 1, int(c - 1), int(c + 1), 128, 139, MARBLE)                  # 身
    P(0, 1, int(c - 3), int(c + 3), 135, 136, MARBLE)                  # 臂
    P(1, 1, int(c + 3), int(c + 3), 133, 141, GOLD_S)                  # 劍
    P(0, 1, int(c), int(c), 140, 142, MARBLE)                          # 頭


balcony('x+', 141.0, GOLD)
balcony('y-', 193.0, GOLD)

# 雉堞（鏤空的白石雉堞：每 6 格一座葉形）
def cresting(axis, pos, inward, s0, s1):
    for s in range(s0, s1 + 1):
        k = (s - s0) % 6
        for t in (pos, pos + inward):
            xx, yy = (s, t) if axis == 'x' else (t, s)
            g[xx, yy, 122] = MARBLE; g[xx, yy, 123] = MARBLE
            if k in (1, 2, 3):
                g[xx, yy, 124] = MARBLE; g[xx, yy, 125] = MARBLE
            if k == 2:
                g[xx, yy, 126] = MARBLE; g[xx, yy, 127] = PINK; g[xx, yy, 128] = MARBLE


cresting('x', 5, 1, 32, 354)
cresting('y', 354, -1, 5, 368)
for (xa, ya) in ((351, 5), (351, 365), (32, 5)):                    # 角上的小亭
    B(xa, xa + 3, ya, ya + 3, 122, 131, MARBLE); B(xa + 1, xa + 2, ya + 1, ya + 2, 132, 137, PINK); B(xa + 1, xa + 1, ya + 1, ya + 1, 138, 140, GOLD_S)

# ── 中庭立面（西、南：磚＋白石尖窗；東：Rizzo 白石兩排窗）──
def paint(axis, pos, s0, s1, z0, z1, col):
    for s in range(s0, s1 + 1):
        for z in range(z0, z1 + 1):
            xx, yy = (s, pos) if axis == 'x' else (pos, s)
            if g[xx, yy, z]: g[xx, yy, z] = col


paint('x', 95, 30, 235, 65, 119, BRICK)
paint('y', 230, 90, 285, 65, 119, BRICK)
paint('y', 32, 5, 95, 65, 121, BRICK)            # 投票廳北牆（朝大教堂、屋頂平台）
for c in range(52, 230, 34):
    opening('y+', 95, c + 0.0, 6, 76, 96, 1.3, 4, mull=True)
for c in range(102, 272, 36):
    opening('x-', 230, c + 0.0, 6, 76, 96, 1.3, 4, mull=True)
for c in (24.0, 72.0):
    opening('x-', 32, c, 5, 76, 94, 1.3, 4)
paint('x', 280, 4, 235, 65, 119, MARBLE)
for c in range(16, 226, 26):                     # Rizzo 立面：主樓層、二樓各一排圓頭窗，窗間壁柱
    opening('y-', 280, c + 0.0, 5, 70, 84, 1.0, 4)
    opening('y-', 280, c + 0.0, 5, 100, 112, 1.0, 4)
    B(c + 12, c + 13, 280, 280, 65, 119, STONE)
for z in (92, 120):                                # 中庭各面的白石帶與簷口
    B(4, 235, 279, 279, z, z + 1, MARBLE)
B(36, 229, 96, 96, 120, 121, MARBLE); B(229, 229, 96, 279, 120, 121, MARBLE)
B(36, 229, 96, 96, 62, 64, MARBLE); B(229, 229, 96, 279, 62, 64, MARBLE); B(4, 229, 279, 279, 62, 64, MARBLE)
B(36, 229, 96, 96, 34, 36, MARBLE); B(229, 229, 96, 279, 34, 36, MARBLE); B(4, 229, 279, 279, 34, 36, MARBLE)

# ── 河邊立面（Rio，y 368 外面）：白石、每層一排窗 ──
paint('x', 368, 0, 354, 1, 121, STONE)
for c in range(14, 344, 22):
    cc = c + 0.0
    opening('y+', 368, cc, 2, 10, 17, 0, 4, glass=False)            # 地牢的小窗（加鐵條）
    for z in range(10, 17, 2): B(c - 2, c + 2, 368, 368, z, z, DARK)
    opening('y+', 368, cc, 4, 41, 53, 1.0, 4)
    opening('y+', 368, cc, 5, 70, 85, 1.0, 4)
    opening('y+', 368, cc, 5, 100, 113, 1.0, 4)
for z in (34, 62, 92):
    B(0, 354, 369, 369, z, z + 1, MARBLE)
B(0, 354, 369, 369, 120, 121, MARBLE)
paint('y', 0, 5, 368, 1, 121, BRICK)                                # 北面（貼著大教堂，看不太到）

# ── 紙門 Porta della Carta（x 4..31，從 y 0 到 y 10）──
B(4, 31, 0, 10, 0, 92, MARBLE)
C(10, 25, 0, 10, 1, 30)
for z in range(30, 42):                                              # 尖拱頂
    hw = 8 * math.sqrt(max(0.0, 1 - ((z - 30) / 12.0) ** 2) ) if z < 42 else 0
    C(int(17.5 - hw), int(17.5 + hw) - 1, 0, 10, z, z)
B(4, 8, 0, 0, 0, 92, PINK); B(27, 31, 0, 0, 0, 92, PINK)            # 兩邊的墩（粉紅）
for z in range(8, 88, 14):
    B(5, 7, 0, 0, z, z + 9, DARK); B(28, 30, 0, 0, z, z + 9, DARK)   # 壁龕
    B(6, 6, 0, 0, z + 1, z + 7, MARBLE); B(29, 29, 0, 0, z + 1, z + 7, MARBLE)   # 美德像
B(9, 26, 0, 0, 44, 52, LAPIS)                                        # 總督跪在聖馬可之獅前
B(12, 15, 0, 0, 45, 50, MARBLE); B(18, 24, 0, 0, 45, 49, GOLD); B(23, 24, 0, 0, 49, 51, GOLD)
B(9, 26, 0, 0, 54, 76, DARK)                                         # 大花窗
for k in range(9, 27, 3): B(k, k, 0, 0, 54, 76, MARBLE)
for z in range(56, 77, 5): B(9, 26, 0, 0, z, z, MARBLE)
for z in range(76, 92):                                              # 尖頂
    hw = max(0, int(13 * (1 - (z - 76) / 16.0)))
    B(17 - hw, 18 + hw, 0, 0, z, z, MARBLE if z % 3 else PINK)
B(16, 19, 0, 2, 92, 94, MARBLE); B(17, 18, 0, 2, 95, 104, MARBLE); B(15, 20, 0, 2, 100, 101, MARBLE)   # 正義女神（坐像）
B(15, 15, 0, 0, 98, 103, GOLD_S)
for xa in (5, 29):                                                   # 兩邊的尖塔
    B(xa, xa + 1, 0, 2, 92, 102, MARBLE); B(xa, xa, 0, 0, 103, 106, GOLD_S)
C(10, 25, 1, 10, 1, 29)

# ── 福斯卡里拱門（y 180..195，x 4..35；開口 x 9..26 圓拱）──
B(4, 35, 180, 195, 0, 84, MARBLE)
for z in range(0, 84, 4): B(4, 35, 180, 180, z, z + 1, PINK); B(4, 35, 195, 195, z, z + 1, PINK)   # 紅白相間
C(9, 26, 180, 195, 1, 28)
for z in range(28, 38):
    hw = 9 * math.sqrt(max(0.0, 1 - ((z - 28) / 9.5) ** 2))
    C(int(17.5 - hw), int(17.5 + hw) - 1, 180, 195, z, z)
for xa in (4, 31):                                                   # 兩邊壁龕裡的亞當、夏娃
    B(xa + 1, xa + 3, 195, 195, 40, 58, DARK); B(xa + 2, xa + 2, 195, 195, 42, 55, STONE)
for k, xa in enumerate(range(5, 34, 4)):                             # 頂上一排尖塔與小像
    B(xa, xa + 1, 186, 189, 85, 92 + (k % 2) * 6, MARBLE); B(xa, xa, 187, 188, 93 + (k % 2) * 6, 97 + (k % 2) * 6, GOLD_S if k % 2 else MARBLE)

# 屋頂上的威尼斯漏斗煙囪（東翼）
for (xa, ya) in ((40, 300), (120, 352), (200, 300), (280, 352)):
    top = Hroof[xa, ya] + 1
    B(xa, xa + 3, ya, ya + 3, top - 3, top + 8, BRICK)
    B(xa - 1, xa + 4, ya - 1, ya + 4, top + 9, top + 12, BRICK)
    B(xa, xa + 3, ya, ya + 3, top + 10, top + 12, DARK)
# 北端屋頂平台（紙門後面那一塊，z 62–64 是地板）＋ 女兒牆；福斯卡里門廊：單坡屋頂
B(4, 31, 11, 95, 64, 64, STONE_S)
for y in range(96, 196):
    for x in range(0, 36):
        h = 72 - int(x * 8 / 35)
        if ARCO[0] <= y <= ARCO[1] and 4 <= x <= 35: continue
        for z in range(65, h + 1): g[x, y, z] = LEAD if z == h or z == h - 1 else STONE
B(0, 3, 196, 279, 72, 73, MARBLE)
B(0, 1, 5, 95, 65, 68, MARBLE)

# ── 中庭：鋪地、井 ──
for x in range(4, 230):
    for y in range(96, 280):
        if x < 36 and y < 196: continue
        if g[x, y, 0] and not g[x, y, 1]:
            g[x, y, 0] = MARBLE if (x % 24 == 0 or y % 24 == 0) else (STONE_S if (x // 6 + y // 6) % 2 else STONE)
for (wx, wy) in ((100.5, 187.5), (170.5, 187.5)):
    for x in range(int(wx - 10), int(wx + 11)):
        for y in range(int(wy - 10), int(wy + 11)):
            r = math.hypot(x + 0.5 - wx, y + 0.5 - wy)
            oct_r = max(abs(x + 0.5 - wx), abs(y + 0.5 - wy), (abs(x + 0.5 - wx) + abs(y + 0.5 - wy)) / 1.3)
            if oct_r <= 9: g[x, y, 1] = MARBLE
            if oct_r <= 8: g[x, y, 2] = MARBLE
            if oct_r <= 6.5:
                for z in range(3, 9):
                    mt[x, y, z] = BRONZE if (z != 6 or oct_r > 5.8) else BRONZE_D
                if oct_r <= 4.5:
                    mt[x, y, 3:9] = 0
                    g[x, y, 2] = DARK
                mt[x, y, 9] = BRONZE if 5.2 <= oct_r else 0

# ── 室內：地板、天花、牆面裝飾 ──
def floor_pattern(x0, x1, y0, y1, z, kind):
    for x in range(x0, x1 + 1):
        for y in range(y0, y1 + 1):
            if g[x, y, z] == 0 or g[x, y, z + 1] != 0: continue
            if kind == 'hall':
                a = (x + y) % 16; b = (x - y) % 16
                g[x, y, z] = MARBLE if (a == 0 or b == 0) else (PINK if ((x + y) // 16 + (x - y) // 16) % 2 else PORPH)
            elif kind == 'room':
                g[x, y, z] = PINK if (x // 4 + y // 4) % 2 else STONE
            elif kind == 'portico':
                if (36 <= x <= 229 and 96 <= y <= 279) or (4 <= x <= 35 and 196 <= y <= 279): continue
                g[x, y, z] = STONE_S if (x // 8 + y // 8) % 2 else STONE


floor_pattern(36, 229, 9, 91, 64, 'hall')
floor_pattern(234, 350, 9, 279, 64, 'hall')
floor_pattern(4, 350, 284, 364, 64, 'room'); floor_pattern(4, 350, 284, 364, 94, 'room')
floor_pattern(4, 350, 9, 364, 36, 'room')
floor_pattern(4, 350, 9, 364, 0, 'portico')


def ceiling(x0, x1, y0, y1, z, kind):
    for x in range(x0, x1 + 1):
        for y in range(y0, y1 + 1):
            if g[x, y, z] == 0 or g[x, y, z - 1] != 0: continue
            if kind == 'gilt':
                g[x, y, z] = GOLD_S if (x % 14 == 0 or y % 14 == 0) else (WOOD if (x // 14 + y // 14) % 2 else DARK)
            elif kind == 'beam':
                g[x, y, z] = WOOD if (x % 4 == 0) else WOOD_D


ceiling(36, 229, 9, 91, 122, 'gilt'); ceiling(234, 350, 9, 279, 122, 'gilt')
ceiling(4, 350, 284, 364, 122, 'gilt'); ceiling(4, 350, 284, 364, 92, 'beam')
ceiling(4, 350, 9, 364, 62, 'beam'); ceiling(4, 350, 9, 364, 34, 'beam')

# 大議會廳：東牆的天堂圖（Tintoretto）、總督席、長椅、一圈總督像的飾帶
rng = np.random.RandomState(1588)
PAL = [PORPH, BRICK, PINK, LAPIS, GOLD, GOLD_S, WOOD, DARK, SEAM, STONE_S, 182, 173, 210, 109]
for x in range(244, 341):
    for z in range(78, 117):
        if not g[x, 280, z]: continue
        edge = x in (244, 340) or z in (78, 116)
        g[x, 280, z] = GOLD_S if edge else int(PAL[(rng.randint(0, len(PAL)) if rng.rand() < 0.6 else (((x - 244) // 6 + (z - 78) // 5) % len(PAL)))])
B(268, 316, 260, 279, 65, 65, WOOD); B(270, 314, 262, 279, 66, 66, WOOD)   # 總督席的台（兩階）
B(285, 299, 276, 279, 67, 74, WOOD_D); B(290, 294, 276, 279, 75, 78, GOLD_S)
for xb in (248, 262, 322, 336):                                     # 長椅（沿長邊兩排一組）
    B(xb, xb + 1, 24, 250, 65, 66, WOOD); B(xb + 4, xb + 5, 24, 250, 65, 66, WOOD)
for (fx, fy) in ([(233, y) for y in range(9, 280)] + [(351, y) for y in range(9, 280)] + [(x, 8) for x in range(234, 351)]):
    for z in range(112, 120):                                   # 總督像的飾帶（一圈）
        if g[fx, fy, z]:
            s_ = fy if fx in (233, 351) else fx
            g[fx, fy, z] = GOLD_S if (s_ % 9 == 0 or z in (112, 119)) else (DARK if (s_ // 3) % 3 else PORPH)
# 投票廳：大幅海戰畫（勒班陀）在北、南兩端
for y in range(14, 88):
    for z in range(80, 112):
        edge = y in (14, 87) or z in (80, 111)
        c = GOLD_S if edge else int(PAL[((y * 7 + z * 3) // 5 + rng.randint(0, 3)) % len(PAL)])
        if g[35, y, z]: g[35, y, z] = c
        if g[230, y, z]: g[230, y, z] = c
# 東翼房間：護牆板（木）一圈
for zf in (Z_P1[0], Z_P2[0]):
    for x in range(4, 351):
        for y in range(284, 365):
            if g[x, y, zf] == 0 and g[x, y, zf - 1]:
                for dx, dy in ((1, 0), (-1, 0), (0, 1), (0, -1)):
                    if g[x + dx, y + dy, zf + 2]:
                        for z in range(zf, zf + 5):
                            if g[x + dx, y + dy, z] in (STONE,): g[x + dx, y + dy, z] = WOOD

# ── 收尾：玻璃格不留實心、青銅不留主體 ──
g[gl] = 0
g[mt > 0] = 0
gl[g > 0] = False

os.makedirs(OUT, exist_ok=True)
np.savez_compressed(os.path.join(OUT, 'grid.npz'), g=g, gl=gl, mt=mt)


def dump(arr, path, col=None):
    xs, ys, zs = np.nonzero(arr)
    cs = arr[xs, ys, zs] if col is None else np.full(len(xs), col)
    with open(path, 'w', encoding='utf-8', newline='\n') as f:
        f.write(''.join('%d,%d,%d,%d\n' % t for t in zip(xs.tolist(), ys.tolist(), zs.tolist(), cs.tolist())))
    return len(xs)


nb = dump(g, os.path.join(OUT, 'body.txt'))
ng = dump(gl, os.path.join(OUT, 'glass.txt'), GLASS)
nm = dump(mt, os.path.join(OUT, 'metal.txt'))
zmax = int(np.nonzero(g.any(axis=(0, 1)))[0].max())
print('body %d  glass %d  metal %d  zmax %d' % (nb, ng, nm, zmax))
print('landings B', landsB, 'C', landsC, 'D', landsD)
