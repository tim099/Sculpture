# 收穫號 階段五（TASK-0594）：船首喙（espolón＋cutwater＋head rails）、船首像（死神見習生）、船尾陽台＋quarter galleries、船名板、三盞船尾燈
#   輸入：plan.json（espolon、figurehead、stern_deco）＋ 組裝件現在的格子（CLI 匯出 ⇒ 船殼＋甲板＋梯子，佔用與貼面都照它算）
#   輸出：masks/deco/<部件>.vox.txt（世界座標、at 0,0,0）、verify_deco.json、sheet05_deco_v1.png
#   用法：python -I -X utf8 draft_deco.py <design> [--probe=shift=<部件>:<dy>]（反向對照：某一件整件往 y 推幾格，⛔ 不寫檔）
#   · 部件都是兩舷一起產（照 |dy| 算 ⇒ 對稱）；只有船名板的字不對稱（照實報鏡像差）。
import sys, os, json, math, hashlib
import numpy as np
from PIL import Image, ImageDraw

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), 'tools'))
import lines as HL
import layout as LY
from draft_lines import font, palette_rgb
from wio import export_list

BLACK, PINK, GOLD, GLASS, WOOD, TRIM, DECK, PALE, SHAFT, BLADE = 36, 242, 248, 87, 141, 136, 209, 254, 132, 219

FONT = {  # 3×5，列由上往下
    'L': ['X..', 'X..', 'X..', 'X..', 'XXX'], 'A': ['.X.', 'X.X', 'XXX', 'X.X', 'X.X'], 'C': ['.XX', 'X..', 'X..', 'X..', '.XX'],
    'O': ['.X.', 'X.X', 'X.X', 'X.X', '.X.'], 'S': ['.XX', 'X..', '.X.', '..X', 'XX.'], 'E': ['XXX', 'X..', 'XX.', 'X..', 'XXX'],
    'H': ['X.X', 'X.X', 'XXX', 'X.X', 'X.X'], ' ': ['.', '.', '.', '.', '.'],
}


def stern_walks(plan, L, S, A, design, both, walk_info):
    """TASK-1027（照康塞普西翁號步驟 17／19）：兩層 stern walk（San Felipe／OcCre 模型：開放的走廊從船尾繞過兩角、沿兩舷往前到 x_end；欄杆、金扶手、底下一排金托架）——
    取代階段五的船尾陽台＋兩舷 quarter galleries（側廊的窗改成船殼上的窗：plan.stern.side_windows，在 draft_ports.py）。"""
    from scipy import ndimage
    YC = L.YC
    for T in S['walks']:
        f, dep, rh = T['floor_z'], T['dep'], T['rail_h']
        xl, xh = T['x_from'], T['x_end']
        yl, yh = YC - 80, YC + 80
        ox = xl - dep
        X_ = np.arange(xh - xl + 1 + 2 * dep)[:, None] + ox
        Y_ = np.arange(yh - yl + 1)[None, :] + yl

        def env(zq):                                                     # 那一層的船殼外形：照線形（窗、門刻出來的凹口不算外面；照格子 ⇒ 托架落進窗洞裡浮空）
            hb_ = L.hb(np.broadcast_to(X_ + 0.5, (X_.shape[0], Y_.shape[1])), np.full((X_.shape[0], Y_.shape[1]), zq + 0.5))
            return (np.abs(Y_ - YC) <= hb_) & (zq <= L.top_z(X_ + 0.5) + 0.5)
        E = env(f)
        dist, (ix, iy) = ndimage.distance_transform_edt(~E, return_indices=True)
        W_ = (~E) & (dist <= dep) & (X_ <= xh)
        ring = W_ & (dist > dep - 1.5)                                   # 外緣 1.5 格 ⇒ 斜的地方兩格相接（6 連通；dep − 1 只有斜角相接 ⇒ 扶手斷成單格）
        Ez = {}                                                          # 地板以下每一層的船（填滿內部）：托架往裡接到那一層的船殼
        for k in range(1, T['bracket_len'] + 2):
            Ez[f - k] = env(f - k)
        ring |= W_ & (X_ == xh)                                          # 走廊的前端封一片欄杆
        hx, hy = ix + ox, np.abs(iy + yl - YC)
        per = hy + (hx - int(np.floor(float(L.x_aft(f + 0.5)))))         # 沿走廊的位置（船尾面 ≈ |dy|、兩舷 ≈ 往前的 x）⇒ 托架每 every 一組
        brk = (np.mod(per + T.get('bracket_off', 0), T['bracket_every']) < 2) & W_      # bracket_off：整組錯開（上層走廊正中間那組會撞到下層的門頂）
        pe = T.get('post_every', 3)                                      # 欄杆柱只在最外那一層、沿走廊每 pe 格一根（康塞普西翁號步驟 19：外緣 2 層各隔一格一根 ⇒ 前後錯開、看過去一整片）
        ay = np.abs(Y_ - YC)
        face = ((hx - X_) > (ay - hy)) | (X_ == xh)                      # 船尾面（在最近那格船殼的後面）與前端那一片照 |dy| 排、兩舷（在外側）照 x 排 ⇒ 間距均勻
        post = ring & ((dist > dep - 1) | (X_ == xh)) & (np.mod(np.where(face, ay, X_), pe) == 0)
        op_ = os.path.join(design, 'masks', 'deco', 'ornament.vox.txt')     # 鏡板的金壁柱（ornament，疊在本階段上面）站在欄杆這一圈裡 ⇒ 那一格柱子讓開
        orn = set(map(tuple, np.loadtxt(op_, delimiter=',', comments='#', dtype=np.int64, ndmin=2, encoding='utf-8')[:, :3].tolist())) if os.path.exists(op_) else set()
        n0 = 0
        for xi, yi in np.argwhere(W_):
            x, y = int(X_[xi, 0]), int(Y_[0, yi])
            dy = y - YC
            if dy < 0:
                continue                                                 # 只算右舷 ⇒ both() 鏡到左舷
            both('stern-deco', x, dy, f, GOLD if ring[xi, yi] else WOOD)
            if not Ez[f - 1][xi, yi]:
                both('stern-deco', x, dy, f - 1, GOLD if ring[xi, yi] else WOOD)    # 地板 2 格厚：外緣下面那一條金（腰線）；只有外緣 ⇒ 船殼往外鼓的那段被圍成封閉空腔
            if ring[xi, yi]:
                for z in range(f + 1, f + rh + 1):
                    if z == f + rh:
                        both('stern-deco', x, dy, z, GOLD)               # 扶手
                    elif z == f + 1:
                        both('stern-deco', x, dy, z, BLACK)              # 底欄
                    elif post[xi, yi] and (x, y, z) not in orn and (x, 2 * YC - y, z) not in orn:
                        both('stern-deco', x, dy, z, PINK)               # 欄杆柱（玫瑰粉，同階段五的陽台）
            if brk[xi, yi]:                                              # 托架：從地板底下往下收成 0（外面那一格金）；裡面接到那一層的船殼
                for k in range(1, T['bracket_len'] + 1):
                    reach = dep * (1 - k / float(T['bracket_len'] + 1)) ** 1.2
                    if dist[xi, yi] <= reach and not Ez[f - 1 - k][xi, yi]:
                        both('stern-deco', x, dy, f - 1 - k, GOLD if dist[xi, yi] > reach - 1.2 else WOOD)
            n0 += 1
        walk_info.append({'floor_z': f, 'footprint_S': n0})


def old_balcony_galleries(YC, S, aft, outer, occ, both):
    """階段五的船尾陽台＋兩舷 quarter galleries（plan 沒有 stern_deco.walks 時）。"""
    bal = S['balcony']
    zf, dep, hb = bal['floor_z'], bal['depth'], bal['half']
    for dy in range(0, hb + 1):
        fxa = aft.get((YC + dy, zf))
        if fxa is None:
            continue
        for x in range(fxa - dep, fxa):
            both('stern-deco', x, dy, zf, WOOD)
        xo = fxa - dep
        for z in range(zf + 1, zf + bal['rail_h'] + 1):
            cap = z == zf + bal['rail_h']
            if cap or dy % 3 == 0 or dy == hb:
                both('stern-deco', xo, dy, z, GOLD if cap else PINK)
        if dy == hb:
            for z in range(zf + 1, zf + bal['rail_h'] + 1):
                fz = aft.get((YC + dy, z), fxa)                        # espejo 往後倒：每一層的船尾位置不同（v1 用地板那一層 ⇒ 上面幾層的欄杆跑進船殼）
                for x in range(xo, min(fxa, fz)):
                    if z == zf + bal['rail_h'] or (x - xo) % 2 == 0:
                        both('stern-deco', x, dy, z, GOLD if z == zf + bal['rail_h'] else PINK)
        if dy % 8 == 0:                                                # 托架：斜撐接回 espejo
            for j, z in enumerate(range(zf - 4, zf)):
                fz = aft.get((YC + dy, z))
                if fz is not None:
                    for x in range(fz - 1 - j, fz):
                        both('stern-deco', x, dy, z, WOOD)
    # ── quarter galleries（兩舷，伸出 4 格；下面一節收成 0、上面一個圓頂） ──
    Q = S['quarter_gallery']
    for x in range(Q['x0'], Q['x1'] + 1):
        for z in range(Q['z0'], Q['z1'] + Q['roof_h'] + 1):
            hz = min(z, Q['z1'])
            o = outer.get((x, hz))
            if o is None or (x, YC + o, hz) not in occ:
                continue
            if z <= Q['z0'] + 4:
                out = max(1, round(Q['out'] * (z - Q['z0'] + 1) / 5.0))
            elif z > Q['z1']:
                k = z - Q['z1']
                out = max(0, Q['out'] - k)
                inset = 2 * k
                if x < Q['x0'] + inset or x > Q['x1'] - inset or out == 0:
                    continue
            else:
                out = Q['out']
            for d in range(1, out + 1):
                face = d == out
                c = BLACK
                if z > Q['z1']:
                    c = GOLD if z == Q['z1'] + 1 else PINK
                elif z in (Q['z0'] + 4, Q['z1']):
                    c = GOLD
                elif 99 <= z <= 103:
                    c = PINK if 100 <= z <= 102 else GOLD
                elif face and ((92 <= z <= 97) or (106 <= z <= 111)) and (x - Q['x0']) % 8 in (3, 4, 5):
                    c = GLASS
                elif face and ((91 <= z <= 98) or (105 <= z <= 112)) and (x - Q['x0']) % 8 in (2, 3, 4, 5, 6):
                    c = GOLD
                both('stern-deco', x, o + d, z, c)


def main():
    sys.stdout.reconfigure(encoding='utf-8')
    design = sys.argv[1]
    probe = [a.split('=', 1)[1] for a in sys.argv[2:] if a.startswith('--probe')]
    plan = HL.load_plan(design)
    L = HL.Lines(plan)
    YC = L.YC
    occ_arg = next((a.split('=', 1)[1] for a in sys.argv[2:] if a.startswith('--occ=')), None)
    if occ_arg:       # TASK-1027（照康塞普西翁號）：設計還沒落格時拿本機清單當「船」（--occ=<清單;清單…>：船殼帳＋甲板＋梯子…）；⛔ 正式產清單一律從組裝件讀
        A = np.concatenate([np.loadtxt(p_, delimiter=',', comments='#', dtype=np.int32, ndmin=2, encoding='utf-8')[:, :4] for p_ in occ_arg.split(';')])
    else:
        A = export_list('calli-cosecha-01m-assembly', None, links=None)
    # 船 ＝ 組裝件扣掉本階段自己的四件（已經落過一次的話）—— v1 沒扣 ⇒ 重產時把舊裝飾當成船、新裝飾被大量跳過、galleries 往外長
    #   TASK-1027：疊在上面的 ornament（draft_ornament.py）、門板也扣掉 ⇒ 重產本階段逐位元組相同
    own = set()
    for nm in (() if occ_arg else ('espolon', 'figurehead', 'stern-deco', 'name-board', 'ornament')):
        if os.path.exists(os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(design))), 'calli-cosecha-01m-' + nm, 'work.json')):
            W_ = export_list('calli-cosecha-01m-' + nm, None)
            own |= set(map(tuple, W_[:, :3].tolist()))
    sg_path = os.path.join(design, 'masks', 'glass', 'stern_glass.vox.txt')
    if os.path.exists(sg_path) and not occ_arg:       # TASK-1027：船尾窗的玻璃子作品也扣掉（窗是空的，玻璃子作品落了之後重跑才逐位元組相同）
        own |= set(map(tuple, np.loadtxt(sg_path, delimiter=',', comments='#', dtype=np.int64, ndmin=2, encoding='utf-8')[:, :3].tolist()))
    keep = np.array([tuple(r) not in own for r in A[:, :3].tolist()], bool) if own else np.ones(len(A), bool)
    A = A[keep]
    occ = set(map(tuple, A[:, :3].tolist()))
    # 每個 (y, z) 船尾最後面那一格、每個 (x, z) 最外那一格的 |dy|、每個 (y, z) 船頭最前面那一格（只看 x ≥ 400）
    aft, outer, fwd = {}, {}, {}
    for x, y, z in A[:, :3].tolist():
        if x < 200:
            k = (y, z)
            if x < aft.get(k, 10 ** 6):
                aft[k] = x
        dy = abs(y - YC)
        if dy > outer.get((x, z), -1):
            outer[(x, z)] = dy
        if x >= 400 and y == YC and x > fwd.get(z, -1):
            fwd[z] = x
    parts = {}

    def put(part, x, y, z, c):
        parts.setdefault(part, {})[(int(x), int(y), int(z))] = c

    def both(part, x, dy, z, c):
        put(part, x, YC + dy, z, c)
        put(part, x, YC - dy, z, c)

    # ── 船首喙 ──
    E = plan['espolon']
    xs0 = int(math.floor(float(L.x_stem(80)) + 0.5)) - 1           # 艏柱前緣那一格（z 57.5 以上直立）＝ 500
    tip = xs0 + E['len_beyond_stem']
    zt, th = E['deck_top_z'], E['thick']
    wpar = lambda x: E['half_at_tip'] + (E['half_at_stem'] - E['half_at_tip']) * (1 - (x - xs0) / float(E['len_beyond_stem'])) ** E['taper_pow']
    x_d0 = E.get('deck_from_x', xs0 + 1)                               # TASK-1027：從 beakhead 艙壁前面起鋪 ⇒ 跟船殼的平台連成一整片（船殼佔的格照樣跳過）

    def wdeck(x):
        if x <= xs0:                                                     # 艙壁到艏柱：從艙壁的半寬收到喙根的半寬
            return E['half_at_stem'] + (E.get('half_at_deck_from', E['half_at_stem']) - E['half_at_stem']) * (xs0 - x) / float(max(1, xs0 - x_d0))
        return wpar(x)
    zsk = E.get('skirt_from_z')
    for x in range(x_d0, tip + 1):
        w = int(math.floor(wdeck(x) + 0.5))
        for dy in range(0, w + 1):
            for z in range(zt - th + 1, zt + 1):
                both('espolon', x, dy, z, DECK if z == zt else BLACK)
        if zsk is not None:                                              # TASK-1027 側板：甲板邊往下包到 skirt_from_z（側面看是一整塊；底下不封 ⇒ 沒有封閉空腔），最前面那一欄整片封
            wn = int(math.floor(wdeck(x + 1) + 0.5)) if x < tip else 0
            for z in range(zsk, zt - th + 1):
                for dy in range(min(wn, w), w + 1):
                    both('espolon', x, dy, z, GOLD if z in (zsk, zt - th) else BLACK)
        for z in range(zt + 1, zt + 1 + E['rail_h']):
            cap = z == zt + E['rail_h']
            if x > plan['figurehead']['x'] - 6:
                continue                                              # head rail 停在船首像前面（v1 跟船首像的斗篷重疊 12 格）
            if cap or (x - xs0) % E['stanchion_every'] == 0:
                both('espolon', x, w, z, GOLD if cap else WOOD)
            if cap:                                                   # 寬度往前收的地方補台階 ⇒ 頂條面相接（v1 只在斜角相接，柱子之間一段段浮空）
                w2 = int(math.floor(wdeck(x + 1) + 0.5))
                for dy in range(w2, w):
                    both('espolon', x, dy, z, GOLD)
    z_cw0 = E['cutwater_from_z']
    cw_top = E.get('cutwater_to_z', zt - th + 1)                         # TASK-1027：knee 頂到平台底（skirt_from_z）、前緣在 cutwater_tip_x 接上 ⇒ 平台前段懸空伸出去
    cw_tip = E.get('cutwater_tip_x', tip)
    for z in range(z_cw0, cw_top):
        u = (z - z_cw0) / float(cw_top - z_cw0)
        xa = fwd.get(z, xs0) + 1
        xf = int(math.floor(xa + (cw_tip - xa) * u ** E['cutwater_pow'] + 0.5))
        for x in range(max(xa, xf - E['cutwater_band']), max(xa, xf) + 1):    # 沿前緣的一條帶子（v1 從艏柱填到前緣 ⇒ 一大塊黑三角，太笨重）
            for dy in range(0, E['cutwater_half'] + 1):
                if dy == E['cutwater_half'] and z >= E.get('trail_from_z', 999) and xf - x in E.get('trail_off', ()):
                    c = GOLD                                           # TASK-1027：knee 兩側的金線（trailboard），沿前緣往裡 trail_off 格
                elif 'trail_off' in E and z < plan['hull_build']['bottom_top_z']:
                    c = plan['hull_build']['bottom_color']            # TASK-1027：水線以下跟船底同色（knee 填成一整片之後露出來）
                else:
                    c = PINK if xf - x == 2 and dy == E['cutwater_half'] else BLACK
                both('espolon', x, dy, z, c)
    # ── 船首像：死神見習生（兜帽斗篷、粉髮、立在中線的鐮刀）——站在喙尖的甲板上 ──
    F = plan['figurehead']
    fx, zb = F['x'], F['z_base']
    for z in range(0, 17):
        r = 4.2 - 1.2 * z / 16.0
        cx = fx + 0.12 * z
        for x in range(int(cx - r) - 1, int(cx + r) + 2):
            for dy in range(0, int(r) + 1):
                if ((x + 0.5 - cx) / (0.8 * r)) ** 2 + (dy / r) ** 2 <= 1.0:
                    both('figurehead', x, dy, zb + z, PINK if z <= 1 else BLACK)
    hcx, hcz, hr = fx + 2.4, zb + 19.5, 2.9
    for z in range(int(hcz - hr), int(hcz + hr) + 1):
        for x in range(int(hcx - hr) - 1, int(hcx + hr) + 2):
            for dy in range(0, int(hr) + 1):
                if (x + 0.5 - hcx) ** 2 + dy ** 2 + (z + 0.5 - hcz) ** 2 <= hr * hr:
                    face = (x + 0.5 - hcx) >= 1.2 and dy <= 1 and hcz - 2 <= z + 0.5 <= hcz + 0.8
                    both('figurehead', x, dy, z, PALE if face else BLACK)
    for z in range(zb + 14, zb + 19):                                  # 粉髮從兜帽兩側垂下來
        both('figurehead', int(hcx + 1), 3, z, PINK)
    for x in range(fx + 3, fx + 6):                                   # 袖子：從斗篷前面伸出去、握在鐮刀柄上（一塊面相接；v1 斜一格一格 ⇒ 手浮空）
        for dy in (0, 1):
            for z in (zb + 11, zb + 12):
                both('figurehead', x, dy, z, BLACK)
    both('figurehead', fx + 5, 1, zb + 13, PALE)
    sx = fx + 6
    for z in range(zb, zb + 31):                                       # 柄從喙的甲板面起（v1 從 zb＋1 起 ⇒ 底下空一格）
        put('figurehead', sx, YC, z, SHAFT)
    prev = zb + 30
    for k in range(0, 10):                                             # 刀刃：從柄頂往前、往下彎；每一段往上補到前一段 ⇒ 面相接
        zz = zb + 30 - int(k * k / 7.0)
        for z in range(zz - 1, max(zz, prev) + 1):
            put('figurehead', sx + 1 + k, YC, z, BLADE)
        prev = zz
    put('figurehead', sx, YC, zb + 31, GOLD)
    # ── 船尾陽台（puente 船長室那排窗下面） ──
    S = plan['stern_deco']
    walk_info = []
    if 'walks' in S:
        stern_walks(plan, L, S, A, design, both, walk_info)
    else:
        old_balcony_galleries(YC, S, aft, outer, occ, both)
    # ── 船名板（espejo、alcázar 那排窗上面；比 espejo 往外一格） ──
    NB = S['name_board']
    text = NB['text']
    wtxt = sum(len(FONT[ch][0]) for ch in text) + (len(text) - 1)
    half = wtxt // 2 + 2
    for dy in range(-half, half + 1):
        for z in range(NB['z0'], NB['z1'] + 1):
            fa = aft.get((YC + dy, z))
            if fa is None:
                continue
            border = dy in (-half, half) or z in (NB['z0'], NB['z1'])
            put('name-board', fa - 1, YC + dy, z, PINK if border else BLACK)
    ycur = YC - wtxt // 2
    for ch in text:                                                    # 從船尾看左手 ＝ −y ⇒ 第一個字在 y 最小那邊
        g = FONT[ch]
        for c in range(len(g[0])):
            for r in range(5):
                if g[r][c] == 'X':
                    z = NB['z1'] - 1 - r
                    fa = aft.get((ycur + c, z))
                    put('name-board', fa - 1, ycur + c, z, GOLD)
        ycur += len(g[0]) + 1
    # TASK-1027（照康塞普西翁號步驟 17 v2）：喙的側板貼著船殼的那幾格會跟船殼圍出 1 格的縫（封閉空腔）⇒ 喙的範圍外擴 3 格的框裡，船＋所有部件填滿內部、多出來的空格補進喙
    espolon_filled = None
    if plan['espolon'].get('skirt_from_z') is not None and parts.get('espolon'):
        from scipy import ndimage
        ek = np.array(list(parts['espolon'].keys()))
        lo_, hi_ = ek.min(axis=0) - 3, ek.max(axis=0) + 4
        G = np.zeros(tuple(hi_ - lo_), bool)
        for src in (occ, *[set(c) for c in parts.values()]):
            for (x, y, z) in src:
                if lo_[0] <= x < hi_[0] and lo_[1] <= y < hi_[1] and lo_[2] <= z < hi_[2]:
                    G[x - lo_[0], y - lo_[1], z - lo_[2]] = True
        holes = ndimage.binary_fill_holes(G) & ~G
        for xi, yi, zi in np.argwhere(holes):
            put('espolon', xi + lo_[0], yi + lo_[1], zi + lo_[2], BLACK)
        espolon_filled = int(holes.sum())
    # 裝飾不蓋船的格（船殼、甲板、梯子優先）：落在佔用格上的照實數出來、不放（gallery 圓頂在船尾肩膀上用 z1 那一層的外緣，碰到更上面的船殼）
    skipped = {}
    for nm in list(parts):
        bad = [k for k in parts[nm] if k in occ]
        skipped[nm] = len(bad)
        for k in bad:
            del parts[nm][k]
    if probe:
        nm, dv = probe[0].split('=')[1].split(':')
        parts[nm] = {(x, y + int(dv), z): c for (x, y, z), c in parts[nm].items()}

    # ── 讀數 ──
    R = {'parts': {}, 'skipped_on_ship': skipped}
    if espolon_filled is not None:
        R['espolon_cavity_filled'] = espolon_filled
    if walk_info:
        R['stern_walks'] = walk_info
    allk = {}
    for nm, cells in parts.items():
        ks = set(cells)
        ov = len(ks & occ)
        touch = sum(1 for (x, y, z) in ks if any(n in occ for n in ((x + 1, y, z), (x - 1, y, z), (x, y + 1, z), (x, y - 1, z), (x, y, z + 1), (x, y, z - 1))))
        mir = sum(1 for (x, y, z), c in cells.items() if cells.get((x, 2 * YC - y, z)) != c)
        cross = sum(1 for k in ks if k in allk)
        for k in ks:
            allk[k] = nm
        bb = np.array(list(ks))
        R['parts'][nm] = {'cells': len(ks), 'overlap_ship': ov, 'overlap_other_parts': cross, 'cells_touching_ship': touch, 'mirror_diff': mir,
                          'bbox': [bb.min(axis=0).tolist(), bb.max(axis=0).tolist()],
                          'colors': {int(c): int(n) for c, n in zip(*np.unique(np.array(list(cells.values())), return_counts=True))}}
    # 艏斜桅那一條線（半徑 2.5）有沒有被喙、像擋到
    B = LY.bowsprit(plan)
    a = math.radians(B['angle'])
    hit = 0
    for (x, y, z) in allk:
        t = (x + 0.5 - B['x0']) * math.cos(a) + (z + 0.5 - B['z0']) * math.sin(a)
        if 0 <= t <= B['len']:
            px, pz = B['x0'] + t * math.cos(a), B['z0'] + t * math.sin(a)
            if (x + 0.5 - px) ** 2 + (y - YC) ** 2 + (z + 0.5 - pz) ** 2 <= 3.0 ** 2:
                hit += 1
    R['bowsprit_clearance_hits'] = hit
    LA = S['lanterns']
    R['lanterns'] = []
    for dy in LA['dy']:
        z = int(L.top_z(LA['x'] + 0.5))
        R['lanterns'].append({'dy': dy, 'at': [LA['x'] + 0.5, YC + dy + 0.5, z + 1], 'on_solid': (LA['x'], YC + dy, z) in occ, 'air_above': (LA['x'], YC + dy, z + 1) not in occ and (LA['x'], YC + dy, z + 1) not in allk})
    if probe:
        print(json.dumps({'probe': probe[0], 'parts': {k: {kk: v[kk] for kk in ('overlap_ship', 'mirror_diff', 'cells_touching_ship')} for k, v in R['parts'].items()}}, ensure_ascii=False))
        return
    od = os.path.join(design, 'masks', 'deco')
    os.makedirs(od, exist_ok=True)
    R['lists'] = {}
    for nm, cells in parts.items():
        p = os.path.join(od, nm + '.vox.txt')
        with open(p, 'w', encoding='utf-8', newline='\n') as f:
            f.write('# 收穫號 %s（draft_deco.py；世界座標，at 0,0,0）\n' % nm)
            for (x, y, z) in sorted(cells):
                f.write('%d,%d,%d,%d\n' % (x, y, z, cells[(x, y, z)]))
        R['lists'][nm] = [len(cells), hashlib.sha256(open(p, 'rb').read()).hexdigest()]
    # 圖：船頭側面、船尾正面、船尾側面
    sc = 6
    im = Image.new('RGB', (1500, 900), (250, 248, 240))
    d = ImageDraw.Draw(im)
    d.text((20, 10), '收穫號 新圖紙 05：船首喙、船首像、船尾陽台、quarter galleries、船名板　v1', fill=(0, 0, 0), font=font(18))

    def side_view(ox, oy, xr, zr, cells_iter, flip=False):
        best = {}
        for (x, y, z), c in cells_iter:
            if y < YC:
                continue
            k = (x, z)
            if y > best.get(k, (-1, 0))[0]:
                best[k] = (y, c)
        for (x, z), (y, c) in best.items():
            if xr[0] <= x <= xr[1] and zr[0] <= z <= zr[1]:
                X = ox + (x - xr[0]) * sc
                Y = oy + (zr[1] - z) * sc
                d.rectangle([X, Y, X + sc - 1, Y + sc - 1], fill=palette_rgb(int(c)))
    hullcells = [((x, y, z), c) for x, y, z, c in A.tolist() if x >= 470 or x <= 150]
    deco = [(k, c) for nm, cells in parts.items() for k, c in cells.items()]
    side_view(20, 50, (470, 590), (15, 110), hullcells + deco)
    d.text((20, 50 + 96 * sc), '船頭（右舷側面）', fill=(0, 0, 0), font=font(14))
    # 船尾正面：每個 (y, z) 最後面那一格
    best = {}
    for (x, y, z), c in hullcells + deco:
        if x > 150:
            continue
        k = (y, z)
        if x < best.get(k, (10 ** 6, 0))[0]:
            best[k] = (x, c)
    ox, oy, s2 = 800, 50, 5
    for (y, z), (x, c) in best.items():
        if 60 <= z <= 140 and 110 <= y <= 210:
            X = ox + (y - 110) * s2
            Y = oy + (140 - z) * s2
            d.rectangle([X, Y, X + s2 - 1, Y + s2 - 1], fill=palette_rgb(int(c)))
    d.text((ox, oy + 82 * s2), '船尾正面（從船尾看，左手 ＝ −y）', fill=(0, 0, 0), font=font(14))
    im.save(os.path.join(design, 'sheet05_deco_v1.png'))
    with open(os.path.join(design, 'verify_deco.json'), 'w', encoding='utf-8', newline='\n') as f:
        json.dump(R, f, ensure_ascii=False, indent=1)
    print(json.dumps({k: v for k, v in R.items() if k != 'lists'}, ensure_ascii=False))


if __name__ == '__main__':
    main()
