# 直接出處：apex-two-galeon-01m/design/draft_ports.py（康塞普西翁號，TASK-0969）—— 作品 id、persona、尺寸、單號、船名換成聖羅曼號（TASK-0970）；下面那行是康塞普西翁號那時寫的出處
# 直接出處：gura-pinas-01m/design/draft_ports.py（藍鯊號，TASK-0967）—— 作品 id、persona、尺寸、單號、船名換成聖羅曼號（TASK-0970）；下面那行是藍鯊號那時寫的出處
# 出處：calli-cosecha-01m/design/draft_ports.py（收穫號，照抄後改成聖羅曼號 —— TASK-0970）
# 聖羅曼號 階段三（TASK-0592）：砲門、塗裝（黑底＋砲列玫瑰粉帶＋金線、船樓菱格、金舷頂）、船尾窗與追擊砲門
#   輸入：plan.json（ports／paint／stern）＋ 船殼（draft_lines.hull_volume 算的那一份 ⇒ 跟作品逐格相同，階段二結果帳證過）
#   輸出：masks/ports/carve.vox.txt（carvevox，帶刻之前的顏色守門）、masks/ports/paint.vox.txt（stampvox overwrite=1：換色）、
#         verify_ports.json、sheet03_ports_paint_v1.png
#   用法：python -I -X utf8 draft_ports.py <design> [--probe=skip_port=<層>:<序號>]   （probe：少開一個砲門重量，⛔ 不寫檔）
#   · 結構照 gura-tridente-01m/design/draft_ports.py（開口、reveal、船尾面的「從最後面往前那一段牆」、對稱取整的窗）；配色與菱格是本船的。
import sys, os, json, math, hashlib
import numpy as np
from PIL import Image, ImageDraw

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import lines as HL
import layout as LY
from draft_lines import hull_volume, shell_colors, font, palette_rgb


def wale_rows(plan, w, xs):
    """一條 wale 的玫瑰粉那幾列：z 範圍（含端點）＝ 甲板面 ＋ dz .. ＋ h − 1（照甲板舷弧）；陣列吃 x。
    聖羅曼號（Tim 2026-10-27「船身做出一些裝飾 曲線」）：plan paint.wales.sheer 有的話，再加 wale 自己多出來的舷弧（1618 Table 4：wale 比甲板翹）：
      船中 mid_x 往兩頭照 ((離船中) ÷ (到那一頭))^pow 加到 aft／fwd 格（過了那一頭照那一頭）× 這一條的 sheer_k；
      這一條有 z_max ⇒ 頂超過 z_max 的那幾柱不畫（wale 收進船樓的菱格帶底下）⇒ lo 回 −1。"""
    xa = np.atleast_1d(xs)
    lo = np.array([int(LY.deck_z(plan, w['deck'], x + 0.5)) + w['dz'] for x in xa])
    sh = plan['paint']['wales'].get('sheer')
    if sh and w.get('sheer_k', 1):
        m = sh['mid_x']
        u = np.where(xa < m, np.clip((m - xa) / float(m - sh['aft_x']), 0, 1), np.clip((xa - m) / float(sh['fwd_x'] - m), 0, 1))
        lo = lo + np.floor(np.where(xa < m, sh['aft'], sh['fwd']) * w.get('sheer_k', 1) * u ** sh['pow'] + 0.5).astype(int)
    if 'z_max' in w:
        lo = np.where(lo + w['h'] - 1 > w['z_max'], -1, lo)
    return lo, np.where(lo < 0, -2, lo + w['h'] - 1)


def stern_windows(plan, YC):
    out = []
    for row in plan['stern']['rows']:
        n, w, h, half = row['n'], row['w'], row['h'], row['half']
        assert w % 2 == 1, '船尾窗寬要奇數（才能對中線對稱）'
        if 'ref_x' in row:     # 從一段甲板的最高處量（追擊砲站的那一段；階段八：船尾最後那一階比 x 130 高 1 格，砲管頂到門楣）
            zc = max(int(LY.deck_z(plan, row['deck'], x + 0.5)) for x in range(row['ref_x'][0], row['ref_x'][1] + 1)) + row['sill']
        else:      # 甲板高量在船尾哪個 x（收穫號寫死 130；聖羅曼號 plan.stern.z_ref_x）
            zc = int(LY.deck_z(plan, row['deck'], plan['stern'].get('z_ref_x', 130))) + row['sill']
        cs = np.linspace(-half + w / 2.0, half - w / 2.0, n)
        for j, c in enumerate(cs):
            k = int(math.floor(abs(c) + 0.5)) * (1 if c >= 0 else -1)   # 對稱取整：±c ⇒ ±k
            y0 = YC + k - (w - 1) // 2
            kind = 'door' if row.get('door_j') == j + 1 else row['kind']      # 步驟 17：那一扇換成走出 stern walk 的門（門洞在 plan.stern.doors，draft_ports 刻；門板 draft_doors.py 擺）
            out.append({'deck': row['deck'], 'j': j + 1, 'y0': y0, 'y1': y0 + w - 1, 'z0': zc, 'z1': zc + h - 1, 'kind': kind})
    return out


def main():
    sys.stdout.reconfigure(encoding='utf-8')
    design = sys.argv[1]
    probe = [a.split('=', 1)[1] for a in sys.argv[2:] if a.startswith('--probe')]
    plan = HL.load_plan(design)
    L = HL.Lines(plan)
    YC = L.YC
    x0, ylo, S, dist = hull_volume(L, plan)
    wall, col = shell_colors(plan, S, dist)
    PA = plan['paint']
    BAND, GOLD, BLACK, REVEAL, GLASS = PA['band'], PA['gold'], PA['base'], PA['reveal'], PA['glass']
    nx, ny, nz = wall.shape
    dy_of = np.arange(ny) + ylo - YC
    xs_all = np.arange(nx) + x0
    zz = np.arange(nz)[None, :]

    ports = LY.ports(plan)
    skip = None
    if probe:
        k, i = probe[0].split('=')[1].split(':')
        skip = (k, int(i))
    carve = np.zeros(wall.shape, bool)
    ring = np.zeros(wall.shape, bool)
    for p in ports:
        if skip and (p['deck'], p['i']) == skip:
            continue
        for side in (1, -1):
            ysel = (dy_of * side) >= 6
            xs = slice(p['x0'] - x0, p['x1'] - x0 + 1)
            zs = slice(p['z0'], p['z1'] + 1)
            carve[xs, :, zs] |= wall[xs, :, zs] & ysel[None, :, None]
            xr = slice(p['x0'] - 1 - x0, p['x1'] + 2 - x0)
            zr = slice(p['z0'] - 1, p['z1'] + 2)
            ring[xr, :, zr] |= wall[xr, :, zr] & ysel[None, :, None]
    ring &= ~carve

    # ── 塗裝：外板那一層（dist ≤ 1）照高度換色；只換黑 36（水線下灰白不動） ──
    outer = wall & (dist <= 1.0) & (col == plan['hull_build']['side_color'])     # 只換水線上的外板色（收穫號 ＝ 黑 36；聖羅曼號 ＝ 褐 136）
    paint = np.zeros(wall.shape, np.uint8)
    for w in PA['wales']['rows']:
        lo, hi = wale_rows(plan, w, xs_all)
        inband = (zz >= lo[:, None]) & (zz <= hi[:, None])
        edge = (zz == lo[:, None] - 1) | (zz == hi[:, None] + 1)
        paint[outer & inband[:, None, :]] = BAND
        if w.get('edge', True):      # 荷蘭船的腰板不描金（聖羅曼號 edge false）
            paint[outer & edge[:, None, :]] = GOLD
    # 船樓菱格（只照 x、z 算 ⇒ 兩舷對稱）；radius < 0 ⇒ 不畫菱格、整片 bg（聖羅曼號的藍舷牆）
    LZ = PA['lozenge']
    per, rad = LZ['period'], LZ['radius']
    u = np.abs((xs_all[:, None] % per) - per // 2)
    for r in LZ['rows']:
        a, b = LY.deck_span(plan, L, r['deck'])
        inx = (xs_all >= a) & (xs_all <= b)
        v = np.abs((zz - r['z0']) % per - per // 2)
        dia = (u + v) <= r.get('radius', rad)
        rows = (zz >= r['z0']) & (zz <= r['z1'])
        m = inx[:, None] & rows
        paint[outer & (m & dia)[:, None, :]] = r.get('color', LZ['color'])
        paint[outer & (m & ~dia)[:, None, :]] = r.get('bg', BLACK)
        edge = inx[:, None] & ((zz == r['z0'] - 1) | (zz == r['z1'] + 1))
        paint[outer & edge[:, None, :]] = GOLD
    # 步驟 17：船尾 counter 的扇形（San Felipe 模型）—— 艉柱線往後外伸的那一片外板：以 (中線, zc) 為心每 deg 度一條金線、線之間兩色輪流
    CF = PA.get('counter_fan')
    fan = np.zeros(wall.shape, bool)
    if CF:
        xp = np.array([float(L.x_post(z + 0.5)) for z in range(nz)])
        behind = (xs_all[:, None] + 0.5) < xp[None, :] + CF['dx']
        zr_ = (zz >= CF['z0']) & (zz <= CF['z1'])
        dyc = np.abs(dy_of)[None, :, None] + 0.5
        dzc = (np.arange(nz) + 0.5 - CF['zc'])[None, None, :]
        ang = np.degrees(np.arctan2(dyc, np.maximum(dzc, 0.5)))
        k = np.floor(ang / CF['deg'] + 0.5)
        ray = np.hypot(dyc, dzc) * np.abs(np.sin(np.radians(ang - k * CF['deg']))) <= CF['line']
        sector = np.where(np.floor(ang / CF['deg']) % 2 == 0, np.uint8(CF['colors'][0]), np.uint8(CF['colors'][1]))
        fan = outer & (behind & zr_)[:, None, :]
        paint[fan] = np.broadcast_to(sector, wall.shape)[fan]
        paint[fan & np.broadcast_to(ray, wall.shape)] = GOLD
        paint[outer & (behind & (zz == CF['z1'] + 1))[:, None, :]] = GOLD      # 扇形頂的金邊
    # 步驟 17：船頭的 beakhead（lines.beakhead 切出來的艙壁與平台）—— OcCre／San Felipe 模型的船頭：
    #   艙壁朝前那一面：金邊框、甲板高度兩條金線、船首樓舷牆那一段的菱格（照 y 排）、兩扇拱門（深色木、金框）、中間一個圓窗；平台頂面：甲板色、外緣金
    BH, PB = plan['lines'].get('beakhead'), PA.get('beakhead')
    if BH and PB:
        xb, zb = BH['x'], BH['z']
        face = outer & ~np.roll(S, -1, axis=0) & (xs_all >= xb - 4)[:, None, None] & (zz >= zb)[:, None, :]
        yy = dy_of[None, :, None]
        z3 = np.arange(nz)[None, None, :]
        paint[face] = BLACK
        fan |= face                                                       # 艙壁朝前那一面不畫 wale（讀數「帶子裡還是黑的」跟扇形一起扣）
        r = next(r for r in LZ['rows'] if r['deck'] == 'castillo')        # 菱格：船首樓舷牆那一段（z 照側面那一條、x 換成 y）
        uy = np.abs((np.abs(yy) % per) - per // 2)
        vz = np.abs((z3 - r['z0']) % per - per // 2)
        band = face & (z3 >= r['z0']) & (z3 <= r['z1'])
        paint[band & ((uy + vz) <= rad)] = r.get('color', LZ['color'])
        paint[band & ((uy + vz) > rad)] = r.get('bg', BLACK)
        for zg in PB['gold_z'] + [r['z0'] - 1, r['z1'] + 1]:
            paint[face & (z3 == zg)] = GOLD
        nb = np.zeros(wall.shape, bool)                                   # 邊框：上下左右有一格不是艙壁面
        for ax, sh in ((1, 1), (1, -1), (2, 1), (2, -1)):
            nb |= face & ~np.roll(face, sh, axis=ax)
        paint[nb] = GOLD
        for dr in PB.get('painted_doors', []):                                          # 拱門：寬 w、高 h，頂上 w//2 列收成半圓；外一圈金
            for sg in (1, -1):
                cy = sg * dr['dy']
                hw = dr['w'] / 2.0
                zc_ = dr['z0'] + dr['h'] - hw
                for zq in range(dr['z0'], dr['z0'] + dr['h'] + 2):
                    for yq in range(int(math.floor(cy - hw - 1)), int(math.ceil(cy + hw + 1)) + 1):
                        dyy = yq - cy
                        rr = math.hypot(dyy, max(0.0, zq + 0.5 - zc_))
                        inside_ = abs(dyy) <= hw - 0.5 and zq < dr['z0'] + dr['h'] and (zq + 0.5 <= zc_ or rr <= hw - 0.5)
                        rim = (abs(dyy) <= hw + 0.5 and (zq + 0.5 <= zc_ or rr <= hw + 0.5)) and not inside_
                        sel = face & (yy == yq) & (z3 == zq)
                        if inside_:
                            paint[sel] = PB['door_color']
                        elif rim and zq >= dr['z0']:
                            paint[sel] = GOLD
        po = PB['port']
        rr = np.hypot(yy, z3 + 0.5 - po['z'])
        paint[face & (rr <= po['r'])] = po['color']
        paint[face & (rr > po['r']) & (rr <= po['r'] + 1)] = GOLD
        plat = outer & (zz == zb - 1)[:, None, :] & (xs_all >= xb)[:, None, None]
        paint[plat] = PB['deck_color']
        if PB.get('platform_edge_gold', True):                          # 步驟 17 v2：喙的平台從艙壁前面接上來 ⇒ 船殼平台的外緣在整片平台中間，不描金
            edge = plat & (~np.roll(S, 1, axis=1) | ~np.roll(S, -1, axis=1) | ~np.roll(S, -1, axis=0))
            paint[edge] = GOLD
    # 舷頂最上一格（外板那一層）金
    topz = np.array([int(math.floor(float(L.top_z(x + 0.5)) + 0.5)) for x in xs_all])
    cap = np.zeros(wall.shape, bool)
    for xi in range(nx):
        zt = min(nz - 1, topz[xi])
        cap[xi, :, zt] = outer[xi, :, zt]
    paint[cap] = GOLD
    # 砲門的金框（聖羅曼號 paint.wreath）：那幾層的砲門，紅框（離開口 1 格）外面再一圈（離開口 2 格）金
    WR = PA.get('wreath')
    if WR:
        wreath = np.zeros(wall.shape, bool)
        for p in ports:
            if p['deck'] not in WR['decks'] or (skip and (p['deck'], p['i']) == skip):
                continue
            for side in (1, -1):
                ysel = (dy_of * side) >= 6
                xr = slice(p['x0'] - 2 - x0, p['x1'] + 3 - x0)
                zr = slice(p['z0'] - 2, p['z1'] + 3)
                wreath[xr, :, zr] |= outer[xr, :, zr] & ysel[None, :, None]
        wreath &= ~ring & ~carve
        paint[wreath] = WR['color']
    paint[ring] = REVEAL

    # ── 船尾面：每個 (y, z) 從最後面往前那一段牆 ──
    first = np.full((ny, nz), -1, int)
    face_max = plan['stern'].get('face_x_max', 170)        # 船尾面：從最後面往前第一格的 x 要小於這個（收穫號寫死 170）
    for yi in range(ny):
        for z in range(nz):
            c = np.nonzero(wall[:, yi, z])[0]
            if len(c) and c[0] + x0 < face_max:
                first[yi, z] = c[0]
    windows = stern_windows(plan, YC)
    glass = np.zeros(wall.shape, bool)
    frame = np.zeros(wall.shape, bool)
    stern_open = np.zeros(wall.shape, bool)
    chase = np.zeros(wall.shape, bool)              # 船尾追擊砲門（整段刻穿、沒有玻璃）⇒ 步驟 19 封玻璃時不算窗
    for wdw in windows:
        if wdw['kind'] == 'door':
            continue
        for yi in range(wdw['y0'] - ylo, wdw['y1'] - ylo + 1):
            for z in range(wdw['z0'], wdw['z1'] + 1):
                f = first[yi, z]
                if f < 0:
                    continue
                run = [f]
                while run[-1] + 1 < nx and wall[run[-1] + 1, yi, z]:
                    run.append(run[-1] + 1)
                if wdw['kind'] == 'port':
                    for xi in run:
                        stern_open[xi, yi, z] = True
                        chase[xi, yi, z] = True
                else:
                    stern_open[f, yi, z] = True
                    if len(run) > 1:
                        glass[run[1], yi, z] = True
                        for xi in run[2:]:      # 玻璃後面的牆刻穿 ⇒ 看得進艙裡（Ship_Materials 窗的玻璃：後面要是空的；收穫號把玻璃漆在牆裡、後面還是實心）
                            stern_open[xi, yi, z] = True
        for yi in range(wdw['y0'] - 1 - ylo, wdw['y1'] + 2 - ylo):
            for z in range(wdw['z0'] - 1, wdw['z1'] + 2):
                if wdw['y0'] - ylo <= yi <= wdw['y1'] - ylo and wdw['z0'] <= z <= wdw['z1']:
                    continue
                f = first[yi, z]
                if f >= 0:
                    frame[f, yi, z] = True
    # 步驟 17：stern walk 後面兩舷的窗（plan.stern.side_windows）—— 跟船尾窗同一套：從舷外往裡那一段牆，最外一格刻開、第二格玻璃、後面刻穿到艙裡；外面一圈金框
    side_wins = []
    for r in plan['stern'].get('side_windows', []):
        for xw in r['x0s']:
            zc = int(LY.deck_z(plan, r['deck'], xw + r['w'] / 2.0)) + r['sill']
            side_wins.append({'deck': r['deck'], 'x0': xw, 'x1': xw + r['w'] - 1, 'z0': zc, 'z1': zc + r['h'] - 1})
    for wdw in side_wins:
        for sgn in (1, -1):
            order = range(ny - 1, -1, -1) if sgn > 0 else range(ny)

            def run_at(xi, z):
                rr = []
                for yi in order:
                    if wall[xi, yi, z]:
                        rr.append(yi)
                    elif rr:
                        break
                return rr
            for x in range(wdw['x0'] - 1, wdw['x1'] + 2):
                for z in range(wdw['z0'] - 1, wdw['z1'] + 2):
                    rr = run_at(x - x0, z)
                    if not rr:
                        continue
                    if wdw['x0'] <= x <= wdw['x1'] and wdw['z0'] <= z <= wdw['z1']:
                        stern_open[x - x0, rr[0], z] = True
                        if len(rr) > 1:
                            glass[x - x0, rr[1], z] = True
                            for yi in rr[2:]:
                                stern_open[x - x0, yi, z] = True
                    else:
                        frame[x - x0, rr[0], z] = True
    win = (stern_open | glass) & ~chase             # 步驟 19：有玻璃的窗洞（船尾窗＋兩舷的窗），門洞刻之前
    open_pre_door = stern_open.copy()
    # 步驟 17：真的門洞（Tim 2026-10-27「開真的可以打開的門(第一人稱模式可以走出去) 船尾有陽台的地方也可以開門出去」）——
    #   門洞那幾欄（y0..y1 × z0..z1）整段牆刻穿；門板（比門洞每邊大一格、直立）擺在門洞外面：船尾的牆往後倒 ⇒ 門板那一面（x ≤ 門板的 x）前面的牆也刻掉 ⇒ 門嵌在凹進去的門廊裡
    door_cut = []
    for dr in plan['stern'].get('doors', []) + (plan['paint'].get('beakhead', {}).get('doors', []) if BH else []):
        for sgn in ((1, -1) if dr.get('dy') else (1,)):
            y0 = YC + sgn * dr.get('dy', 0) - dr['w'] // 2
            y1, z0d, z1d = y0 + dr['w'] - 1, dr['z0'], dr['z0'] + dr['h'] - 1
            ys = range(y0 - ylo, y1 - ylo + 1)
            if dr.get('face', 'aft') == 'aft':                 # 船尾：從後面往前那一段牆
                fx = [first[yi, z] for yi in ys for z in range(z0d, z1d + 1) if first[yi, z] >= 0]
                xd = max(fx) - 1                                # 門板的 x（模型座標的格）：門洞最底下那一格牆的外面一格
                for yi in range(y0 - 1 - ylo, y1 + 2 - ylo):
                    for z in range(z0d, z0d + dr['model_h']):
                        for xi in range(0, xd + 1):
                            if wall[xi, yi, z]:
                                stern_open[xi, yi, z] = True
                for yi in ys:
                    for z in range(z0d, z1d + 1):
                        f = first[yi, z]
                        while 0 <= f < nx and wall[f, yi, z]:
                            stern_open[f, yi, z] = True
                            f += 1
                door_cut.append({'deck': dr['deck'], 'face': 'aft', 'y0': y0, 'y1': y1, 'z0': z0d, 'z1': z1d, 'door_x': int(xd + x0), 'model_h': dr['model_h']})
            else:                                               # 船頭 beakhead 艙壁（朝 +x）：從前面往後那一段牆
                xs_d = []
                for yi in ys:
                    for z in range(z0d, z1d + 1):
                        c = np.nonzero(wall[:, yi, z])[0]
                        f = c[-1] if len(c) else -1
                        xs_d.append(f)
                        while f >= 0 and wall[f, yi, z]:
                            stern_open[f, yi, z] = True
                            f -= 1
                door_cut.append({'deck': dr['deck'], 'face': 'fwd', 'y0': y0, 'y1': y1, 'z0': z0d, 'z1': z1d, 'door_x': int(max(xs_d) + 1 + x0), 'model_h': dr['model_h'], 'model_z0': dr.get('model_z0', z0d)})
                for yi in range(y0 - 1 - ylo, y1 + 2 - ylo):    # 門洞外一圈金框＋頂上半圓的拱（艙壁朝前那一面）
                    for z in range(z0d, z1d + 6):
                        dyy = yi + ylo - (y0 + y1) / 2.0
                        arch = z > z1d and abs(math.hypot(dyy, z - z1d) - (dr['w'] / 2.0 + 1)) < 0.7
                        rim = z <= z1d and abs(dyy) > (dr['w'] - 1) / 2.0
                        if arch or rim or z == z1d + 1:
                            c = np.nonzero(wall[:, yi, z])[0]
                            if len(c):
                                frame[c[-1], yi, z] = True
    # 步驟 19（Tim 2026-10-27「玻璃好像有縫」）：玻璃改成窗洞裡「從船外數進來第二層」—— 窗洞的格照 6 連通量離船外的距離，距離 1 的那一層整層是玻璃。
    #   v1 一柱一柱放「從外往裡第二格」：直的牆一樣，斜的牆（船尾兩個轉角）上相鄰兩柱的玻璃只在斜角相碰、轉角的船尾窗跟舷窗之間空一格 ⇒ 空氣從斜角鑽過去（tools/glass_seal.py：漏 6 片）。
    #   距離每走一步只變 1 ⇒ 從船外（距離 0）走到艙裡一定踩過距離 1 那一層 ⇒ 那一層封得住；牆只有 1 格厚、外面那格就貼著艙裡 ⇒ 那一格也是玻璃。
    from scipy import ndimage
    st6 = ndimage.generate_binary_structure(3, 1)
    acc = lambda a, ax: np.maximum.accumulate(a, axis=ax)
    racc = lambda a, ax: np.flip(acc(np.flip(a, ax), ax), ax)
    enc = acc(wall, 0) & racc(wall, 0) & acc(wall, 1) & racc(wall, 1)
    reg = win & ~(stern_open & ~open_pre_door)      # 門洞刻穿的格不算窗
    d = np.full(wall.shape, -1, int)
    front = reg & ndimage.binary_dilation(~wall & ~enc, st6)
    k = 0
    while front.any():
        d[front] = k
        k += 1
        front = reg & (d < 0) & ndimage.binary_dilation(front, st6)
    newglass = reg & ((d == 1) | ((d == 0) & ndimage.binary_dilation(~wall & enc, st6)))
    opn = reg & ~newglass                           # 斜的地方距離 1 那一層會轉折、夾住 1 格跟哪邊都不通的空氣（組裝件封閉空腔 2 格，最上排轉角那扇）⇒ 填成玻璃
    newglass |= opn & ~ndimage.binary_propagation(~wall, structure=st6, mask=opn | ~wall)
    R_glass_v1 = int(glass.sum())
    glass = (glass & ~reg) | newglass
    stern_open = (stern_open | reg) & ~newglass
    carve |= stern_open
    glass &= ~carve
    carve |= glass                      # 玻璃從船殼拿出來、另做一件子作品（關聯 meta material=glass）⇒ masks/glass/stern_glass.vox.txt
    paint[frame & ~carve] = GOLD
    paint[carve] = 0
    changes = (paint > 0) & wall & (paint != col)

    # ── 讀數 ──
    after = wall & ~carve
    acol = col.copy()
    acol[changes] = paint[changes]
    R = {'carve_cells': int(carve.sum()), 'paint_cells': int(changes.sum()),
         'carve_by_color': {int(c): int(n) for c, n in zip(*np.unique(col[carve], return_counts=True))},
         'paint_to': {int(c): int(n) for c, n in zip(*np.unique(acol[changes], return_counts=True))},
         'after_cells': int(after.sum())}
    see = []
    for p in ports:
        for side in (1, -1):
            ysel = (dy_of * side) >= 6
            blk = after[p['x0'] - x0:p['x1'] - x0 + 1, :, p['z0']:p['z1'] + 1] & ysel[None, :, None]
            if blk.any():
                see.append({'deck': p['deck'], 'i': p['i'], 'side': 'S' if side > 0 else 'P', 'solid': int(blk.sum())})
    R['ports_not_open'] = see
    chasers = [w for w in windows if w['kind'] == 'port']
    st_closed = []
    for w in chasers:
        blk = after[:max(1, face_max - x0), w['y0'] - ylo:w['y1'] - ylo + 1, w['z0']:w['z1'] + 1]
        # 從船尾往前看：每個 (y, z) 第一段牆要整段刻穿 ⇒ 那一欄在牆範圍內沒有實心
        cnt = 0
        for yi in range(w['y0'] - ylo, w['y1'] - ylo + 1):
            for z in range(w['z0'], w['z1'] + 1):
                f = first[yi, z]
                if f >= 0 and after[f, yi, z]:
                    cnt += 1
        if cnt:
            st_closed.append({'y0': w['y0'], 'solid_first': cnt})
    R['stern_ports_not_open'] = st_closed
    # wale 的高度裡、外板那一層還是黑的（船頭朝前的面也算 —— 漏漆會在這裡現形）
    left_black = 0
    for w in PA['wales']['rows']:
        lo, hi = wale_rows(plan, w, xs_all)
        for xi in range(nx):
            m = after[xi, :, lo[xi]:hi[xi] + 1] & (dist[xi, :, lo[xi]:hi[xi] + 1] <= 1.0) & (acol[xi, :, lo[xi]:hi[xi] + 1] == BLACK) & ~fan[xi, :, lo[xi]:hi[xi] + 1]   # 步驟 17：counter 的扇形蓋過 wale（扇形自己有 136 那一色）
            left_black += int(m.sum())
    R['band_black_left'] = left_black
    R['mirror_diff'] = int((after != after[:, ::-1, :]).sum() + ((acol * after) != (acol * after)[:, ::-1, :]).sum())
    R['windows'] = windows
    R['side_windows'] = side_wins
    R['doors'] = door_cut
    R['side_windows_glass'] = int(sum(glass[w['x0'] - x0:w['x1'] - x0 + 1, :, w['z0']:w['z1'] + 1].sum() for w in side_wins))
    R['ports_total'] = len(ports) * 2 + len(chasers)
    R['glass_cells'], R['glass_cells_v1'] = int(glass.sum()), R_glass_v1     # 步驟 19：窗洞第二層整層是玻璃（v1 一柱一格）
    if probe:
        print(json.dumps({'probe': probe[0], 'ports_not_open': see}, ensure_ascii=False))
        return
    out = os.path.join(design, 'masks', 'ports')
    os.makedirs(out, exist_ok=True)

    def dump(path, mask, colors, head):
        idx = np.argwhere(mask)
        with open(path, 'w', encoding='utf-8', newline='\n') as f:
            f.write(head)
            for xi, yi, z in idx:
                f.write('%d,%d,%d,%d\n' % (xi + x0, yi + ylo, z, colors[xi, yi, z]))
        return len(idx), hashlib.sha256(open(path, 'rb').read()).hexdigest()
    n1, h1 = dump(os.path.join(out, 'carve.vox.txt'), carve, col, '# 聖羅曼號 砲門與船尾開口（carvevox；第 4 欄 ＝ 刻之前的顏色，守門）\n')
    n2, h2 = dump(os.path.join(out, 'paint.vox.txt'), changes, acol, '# 聖羅曼號 塗裝（stampvox overwrite=1：換色；不含刻掉的格）\n')
    gcol = np.where(glass, np.uint8(GLASS), np.uint8(0))
    og = os.path.join(design, 'masks', 'glass')
    os.makedirs(og, exist_ok=True)
    n3, h3 = dump(os.path.join(og, 'stern_glass.vox.txt'), glass, gcol, '# 聖羅曼號 船尾窗玻璃（1 格厚、後面是空的；子作品 -stern-glass，關聯 meta material=glass）\n')
    R['lists'] = {'carve': [n1, h1], 'paint': [n2, h2], 'glass': [n3, h3]}
    # 圖紙：右舷側面＋船尾正面
    sc = 2.0
    Wp = int(nx * sc) + 120 + int(ny * sc) + 80
    Hp = int(nz * sc) + 160
    im = Image.new('RGB', (Wp, Hp), (250, 248, 240))
    d = ImageDraw.Draw(im)
    d.text((40, 16), '聖羅曼號 新圖紙 03：砲門、塗裝、船尾窗　v1　（帶 %d、金 %d、reveal %d、玻璃 %d）' % (BAND, GOLD, REVEAL, GLASS), fill=(0, 0, 0), font=font(20))
    oy = 60
    for xi in range(nx):
        for z in range(nz):
            ys = np.nonzero(after[xi, :, z])[0]
            if len(ys):
                c = palette_rgb(int(acol[xi, ys[-1], z]))
                X, Y = 40 + xi * sc, oy + (nz - 1 - z) * sc
                d.rectangle([X, Y, X + sc, Y + sc], fill=c)
    ox = 40 + int(nx * sc) + 60
    for yi in range(ny):
        for z in range(nz):
            xs = np.nonzero(after[:, yi, z])[0]
            if len(xs):
                c = palette_rgb(int(acol[xs[0], yi, z]))
                X, Y = ox + yi * sc, oy + (nz - 1 - z) * sc
                d.rectangle([X, Y, X + sc, Y + sc], fill=c)
    d.text((40, oy + nz * sc + 10), '右舷側面（船頭在右）　　船尾正面（從船尾看，左手 ＝ −y ＝ 左舷 P）', fill=(40, 40, 40), font=font(14))
    d.text((40, oy + nz * sc + 34), '刻 %d 格、換色 %d 格；砲門 %d（看不穿的 %d）、船尾追擊 %d（沒刻穿的 %d）；帶子裡外板還是黑的 %d 格；鏡像差 %d' % (
        R['carve_cells'], R['paint_cells'], len(ports) * 2, len(see), len(chasers), len(st_closed), left_black, R['mirror_diff']), fill=(0, 0, 0), font=font(14))
    im.save(os.path.join(design, 'sheet03_ports_paint_v1.png'))
    with open(os.path.join(design, 'verify_ports.json'), 'w', encoding='utf-8', newline='\n') as f:
        json.dump(R, f, ensure_ascii=False, indent=1)
    print(json.dumps({k: v for k, v in R.items() if k != 'windows'}, ensure_ascii=False))


if __name__ == '__main__':
    main()
