# 出處：calli-cosecha-01m/design/draft_deco.py（收穫號）的框架 —— 部件換成荷蘭 pinas 的（TASK-0967 步驟 6）
# 藍鯊號 步驟 6：船首喙（galjoen＋cutwater＋head rail）、船首像（紅獅子）、船尾走廊＋兩舷側廊、hackebort（藍鯊紋章＋名帶）、船尾燈
#   輸入：plan.json（espolon、figurehead、stern_deco）＋ 組裝件現在的格子（CLI 匯出 ⇒ 船殼＋甲板＋梯子＋玻璃，佔用與貼面都照它算）
#   輸出：masks/deco/<部件>.vox.txt（世界座標、at 0,0,0）、verify_deco.json、sheet05_deco_v1.png
#   用法：python -I -X utf8 draft_deco.py <design> [--probe=shift=<部件>:<dy>]（反向對照：某一件整件往 y 推幾格，⛔ 不寫檔）
#   · galjoen、獅子、船尾走廊、側廊兩舷一起產（照 |dy| 算 ⇒ 對稱）；hackebort 的鯊魚與字不對稱（照實報鏡像差）。
#   · 側廊的窗是畫上去的（87，後面是側廊的實心）—— 只有鏡板的窗是真的玻璃（-stern-glass，material=glass）
import sys, os, json, math, hashlib
import numpy as np
from PIL import Image, ImageDraw

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), 'tools'))
import lines as HL
import layout as LY
from draft_lines import font, palette_rgb
from wio import export_list

BLACK, GOLD, GLASS, WOOD, TRIM, DECK, BLUE = 36, 248, 87, 141, 136, 209, 6
PARTS = ('galjoen', 'figurehead', 'stern-deco', 'hackebort')

FONT = {  # 3×5，列由上往下
    'B': ['XX.', 'X.X', 'XX.', 'X.X', 'XX.'], 'L': ['X..', 'X..', 'X..', 'X..', 'XXX'], 'A': ['.X.', 'X.X', 'XXX', 'X.X', 'X.X'],
    'U': ['X.X', 'X.X', 'X.X', 'X.X', 'XXX'], 'W': ['X.X', 'X.X', 'XXX', 'XXX', 'X.X'], 'E': ['XXX', 'X..', 'XX.', 'X..', 'XXX'],
    'H': ['X.X', 'X.X', 'XXX', 'X.X', 'X.X'], 'I': ['XXX', '.X.', '.X.', '.X.', 'XXX'], ' ': ['.', '.', '.', '.', '.'],
}


def chain6(pts):
    """相鄰兩點（x 差 1）連成 6 連通：先往前一格、再在新的那一欄補 dy 與 z（船頭往前收 ⇒ 補的格在新那一欄的船殼外面）"""
    out = []
    for i, p in enumerate(pts):
        if i:
            _, y, z = out[-1]
            x1, y1, z1 = p
            while y != y1:
                out.append((x1, y, z))
                y += 1 if y1 > y else -1
            while z != z1:
                out.append((x1, y, z))
                z += 1 if z1 > z else -1
        out.append(p)
    return out


def galjoen_v2(V, F, xs0, Hl, L, YC, put, both, R):
    """TASK-0967 船頭 v2（Tim 2026-10-28「967 參考 TASK-1045 船頭…優化一下」「可以只優化船頭」「開個門可以走到船頭」）：
    照 Witsen 1671 的 galjoen（研究筆記 references/research_pinas_bow_2026-10-28.md）——
    平台（uitlegger 上的格柵、側板、前面一欄封）從艏柱往前漸升；knee 從首柱填到平台底；每側三條 regelingen 從 cathead 底下沿船頭兩舷往前、
    跟著平台往上收到 es 底下；4 根 head timber（knies，第 1 根貼艏柱、每 2 呎一根）；兩道 cheek 夾一條 trailboard（kam）；
    最上一條 rail 的後端是撐 cathead 的金人頭（mans hooft）；cathead；獅子背上 2'2" 的 es 渦卷。
    船殼的外形只拿船殼算（Ship_Ends §4.4：拿組裝件算 ⇒ 貼到錨架外面）。回傳平台頂 z 的函式（獅子的腳踩在上面）。"""
    hout, hfwd, htop = {}, {}, {}
    for x, y, z, c in Hl.tolist():
        if x < 470:
            continue
        dy = abs(y - YC)
        if dy > hout.get((x, z), -1):
            hout[(x, z)] = dy
        if dy == 0 and x > hfwd.get(z, -1):
            hfwd[z] = x
        if z > htop.get(x, -1):
            htop[x] = z
    ho = lambda x, z: hout.get((x, min(z, htop.get(x, z))), -1)        # 舷頂以上 ⇒ 照舷頂那一格的半寬（rail 沿著降下來的船首上緣走，不會跑到中線）
    lin_c = {}

    def inhull(x, dy, z):
        """作品的格 ∪ 線形外形 —— bak 底下的砲門（x 513–518）整欄刻開，只看作品會把平台鋪進艙裡"""
        if dy <= hout.get((x, z), -1):
            return True
        if (x, z) not in lin_c:
            top = float(L.top_z(x + 0.5))
            lin_c[(x, z)] = float(L.hb(np.array([x + 0.5]), np.array([z + 0.5]))[0]) if z + 0.5 <= top + 0.5 else -1.0
        return dy <= lin_c[(x, z)]
    P = V['platform']
    th = P['thick']
    tip = xs0 + V['len_beyond_stem']
    x_from = P['x_from']
    ztf = lambda x: P['top_z'] + int(math.floor(P['rise'] * max(0.0, min(1.0, (x - xs0) / float(tip - xs0))) ** P['rise_pow'] + 0.5))
    hw = lambda x: P['half_tip'] + (P['half_root'] - P['half_tip']) * max(0.0, (tip - x) / float(tip - x_from)) ** P['taper_pow']
    # ── 平台：中間格柵（每 3 格一條深色）、最外兩格素的甲板色；船殼佔的格跳過 ⇒ 圍著圓船頭接成一圈 ──
    edge = {}
    for x in range(x_from, tip + 1):
        w = int(math.floor(hw(x) + 0.5))
        zt = ztf(x)
        for dy in range(0, w + 1):
            for z in range(zt - th + 1, zt + 1):
                if inhull(x, dy, z):
                    continue
                grate = z == zt and dy <= w - 2 and (x % 3 == 0 or dy % 3 == 0)
                both('galjoen', x, dy, z, TRIM if (z < zt or grate) else DECK)
        if not inhull(x, w, zt):
            edge[x] = w
    # ── 側板：平台外緣往下包 skirt.h 格、上下兩條金；寬度往前收的地方補台階（面相接）；最前面那一欄整片封、底下不封 ──
    S = P['skirt']
    for x in sorted(edge):
        e = edge[x]
        e2 = edge.get(x + 1, e)
        zt = ztf(x)
        zs0 = zt - th - S['h'] + 1
        dys = range(0, e + 1) if x == tip else range(min(e, e2), e + 1)
        for dy in dys:
            for z in range(zs0, zt - th + 1):
                if not inhull(x, dy, z):
                    both('galjoen', x, dy, z, GOLD if z in (zs0, zt - th) and dy == e else TRIM)
    # ── knee（scheg）：首柱前緣填到前緣曲線（從 from_z 的首柱掃到喙尖往後 back 格的平台底）；只填到那一欄的平台底；水線（wl）以下跟船底同色 ──
    K = V['knee']
    tipk = tip - K['back']
    z0k, z1k = K['from_z'], ztf(tipk) - th
    prof = {}
    for z in range(z0k, z1k + 1):
        u = (z - z0k) / float(z1k - z0k)
        xa = hfwd.get(z, xs0) + 1
        xf = int(math.floor(xa + (tipk - xa) * u ** K['pow'] + 0.5))
        for x in range(xa, max(xa, xf) + 1):
            if z <= ztf(x) - th:
                prof[(x, z)] = K['below'] if z < K['wl'] else TRIM
    # trailboard：knee 兩側沿前下緣往裡 K['line'] 格一條金線（水線上 2 格起）
    edge2 = [(x, z) for (x, z) in prof if ((x + 1, z) not in prof and z < ztf(x + 1) - th) or ((x, z - 1) not in prof and x > hfwd.get(z - 1, -10 ** 6))]
    dist = {p: 0 for p in edge2}
    q = list(edge2)
    while q:
        nq = []
        for (x, z) in q:
            for ddx in (-1, 0, 1):
                for ddz in (-1, 0, 1):
                    n = (x + ddx, z + ddz)
                    if n in prof and n not in dist:
                        dist[n] = dist[(x, z)] + 1
                        nq.append(n)
        q = nq
    side = {}
    for (x, z), c in prof.items():
        for dy in range(0, K['half'] + 1):
            gl = dy == K['half'] and dist.get((x, z)) == K['line'] and z >= K['line_from_z']
            both('galjoen', x, dy, z, GOLD if gl else c)
            if dy == K['half'] and not gl:
                side[(x, z)] = c
    # ── cheek（W：兩道 kniehout，6 呎與 5½ 呎）：船頭兩舷貼著船殼往前、過了首柱沿 knee 兩側再往前（不超過 knee 那一高度的前緣往裡 2 格）──
    R['cheeks'] = []
    cz = []
    for ch in V['cheeks']:
        pts = []
        for x in range(ch['x0'], ch['x1'] + 1):
            t = (x - ch['x0']) / float(ch['x1'] - ch['x0'])
            z = int(round(ch['z0'] - ch['drop'] * t ** ch['pow']))
            if x <= hfwd.get(z, -1):
                dy = max(hout.get((x, z), -1), hout.get((x, z + 1), -1)) + 1
            elif (x + 2, z) in prof and (x + 2, z + 1) in prof:
                dy = K['half'] + 1
            else:
                break
            pts.append((x, dy, z))
        cells = chain6(pts)
        inside = 0
        for (x, dy, z) in cells:
            for zz in (z, z + 1):
                if dy > hout.get((x, zz), -1):
                    both('galjoen', x, dy, zz, GOLD)
                else:
                    inside += 1                                       # 從船殼側轉到 knee 側那一步補的格落在首柱裡 ⇒ 不放（船殼本身接得上）
        cz.append({x: z for (x, dy, z) in pts})
        R['cheeks'].append({'cells': len(cells), 'x': [pts[0][0], pts[-1][0]], 'in_hull_dropped': inside})
    # kam（W：兩道 cheek 中間雕花的 trailboard）：knee 側面、兩道 cheek 中間那一段 —— 底色＋每 4 格一個金點的卷草
    KM = V['kam']
    nk = 0
    hi, lo = cz[0], cz[1]
    for x in sorted(set(hi) & set(lo)):
        for z in range(lo[x] + 2, hi[x]):
            if (x, z) in side:
                both('galjoen', x, K['half'], z, KM['dot'] if (x + 2 * z) % 4 == 0 else KM['color'])
                nk += 1
    R['kam_cells_per_side'] = nk
    # ── regelingen（W p.86–87：每側 3 條）：平台外緣上 h 格（平台還在船殼裡的地方 ⇒ 貼船殼外一格）；後段往 cathead 底下翹 up·((x_l − x)/(x_l − x_h))²；
    #    2 格高（下面 color、上面金）——遊戲：最上一條在平台上 8 格、條與條之間 1 格縫 ⇒ 第一人稱踩不上去（W 的格柵在中間那條的頂，這裡照遊戲抬高）──
    R['rails'] = []
    tops, rz = {}, []
    for r in V['rails']:
        pts = []
        for x in range(r['x_h'], r['x_e'] + 1):
            bump = r['up'] * ((r['x_l'] - x) / float(r['x_l'] - r['x_h'])) ** 2 if x < r['x_l'] else 0.0
            z = ztf(x) + r['h'] + int(math.floor(bump + 0.5))
            dy = max(edge.get(x, -1), ho(x, z) + 1, ho(x, z + 1) + 1)
            pts.append((x, dy, z))
        cells = chain6(pts)
        for (x, dy, z) in cells:
            both('galjoen', x, dy, z, r['color'])
            both('galjoen', x, dy, z + 1, GOLD)
            if x in edge and dy == edge[x]:
                tops[x] = max(tops.get(x, -1), z + 1)
        rz.append(pts)
        R['rails'].append({'cells': len(cells), 'above_deck': sorted({z - ztf(x) for (x, dy, z) in pts if x in edge})[:3]})
    # head timber（knies）：第 1 根貼艏柱、之後每 every 格一根，n 根；平台外緣、從平台面立到最上一條 rail
    HT = V['timbers']
    nt = []
    for k in range(HT['n']):
        x = xs0 + 1 + k * HT['every']
        if x in tops:
            for z in range(ztf(x) + 1, tops[x]):
                both('galjoen', x, edge[x], z, HT['color'])
            nt.append(x)
    R['timbers'] = nt
    # 撐 cathead 的金人頭（mans hooft）：最上一條 rail 的後端
    MH = V['mans_head']
    x_, dy_, z_ = rz[-1][0]
    cx, cdy, czz = x_ + MH['dx'], dy_ + MH['ddy'], z_ + MH['dz']
    for x in range(int(cx - 3), int(cx + 4)):
        for dy in range(int(cdy - 3), int(cdy + 4)):
            for z in range(int(czz - 3), int(czz + 4)):
                if (x + 0.5 - cx) ** 2 + (dy - cdy) ** 2 + (z + 0.5 - czz) ** 2 <= MH['r'] ** 2 and dy > ho(x, z):
                    both('galjoen', x, dy, z, GOLD)
    # cathead（W：比欄杆外突 2 呎、8 × 10 吋）：bak 前角舷外一根方木、斜往前往外；端面金
    CT = V['cathead']
    a = math.radians(CT['deg'])
    dy0 = ho(CT['x'], CT['z'])                                           # 基點：bak 前角那一欄的舷外；從這裡沿（sin, cos）方向每半格取一次 ⇒ 方木一整根連著
    cat = {}
    for i in range(0, 2 * CT['len'] + 1):
        t = i / 2.0
        for j in range(-2 * CT['half'], 2 * CT['half'] + 1):
            dd = j / 2.0
            x = int(math.floor(CT['x'] + t * math.sin(a) + dd * math.cos(a) + 0.5))
            dy = int(math.floor(dy0 + t * math.cos(a) - dd * math.sin(a) + 0.5))
            for z in range(CT['z'] - CT['half'], CT['z'] + CT['half'] + 1):
                if dy > ho(x, z):
                    cat[(x, dy, z)] = GOLD if t >= CT['len'] - 1 else CT['color']
    for (x, dy, z), c in cat.items():
        both('galjoen', x, dy, z, c)
    R['cathead_cells_per_side'] = len(cat)
    # es（W：獅子背上 2'2" 的渦卷）：獅子身體中段上 h 格一圈金環（中線兩格厚）、一根金柱接回獅背 —— regelingen 收到它底下
    ES = V['es']
    xr, ln, rs = F['x'], F['len'], F['raise']
    zc = lambda x: ztf(x) + 4 + rs * (x - xr) / float(ln)
    ex = xr + ES['dx']
    back = int(zc(ex) + 3.2)
    ez = back + ES['h']
    for x in range(int(ex - ES['r'] - 2), int(ex + ES['r'] + 3)):
        for z in range(int(ez - ES['r'] - 2), int(ez + ES['r'] + 3)):
            d = math.hypot(x - ex, z - ez)
            if ES['r'] - 0.7 <= d <= ES['r'] + 0.7:
                for dy in (0, 1):
                    both('galjoen', x, dy, z, GOLD)
    for z in range(back + 1, int(ez - ES['r'] + 1)):
        for dy in (0, 1):
            both('galjoen', ex, dy, z, GOLD)
    R.update({'top_z': [ztf(xs0), ztf(tip)], 'tip': tip, 'edge_x': [min(edge), max(edge)], 'knee_cells_2d': len(prof), 'es': [ex, ez]})
    return ztf


def main():
    sys.stdout.reconfigure(encoding='utf-8')
    design = sys.argv[1]
    probe = [a.split('=', 1)[1] for a in sys.argv[2:] if a.startswith('--probe')]
    plan = HL.load_plan(design)
    L = HL.Lines(plan)
    YC = L.YC
    WORKS = os.environ.get('SCULPT_WORKS') or os.path.dirname(os.path.dirname(os.path.abspath(design)))   # worktree 只放 design/ ⇒ 作品資料讀共用的那一份
    A = export_list('gura-pinas-01m-assembly', None, links=None)
    # 船 ＝ 組裝件扣掉本步驟自己的件（已經落過一次的話；收穫號 v1 沒扣 ⇒ 重產時把舊裝飾當成船）
    own = set()
    for nm in PARTS:
        if os.path.exists(os.path.join(WORKS, 'gura-pinas-01m-' + nm, 'work.json')):
            own |= set(map(tuple, export_list('gura-pinas-01m-' + nm, None)[:, :3].tolist()))
    if own:
        A = A[np.array([tuple(r) not in own for r in A[:, :3].tolist()], bool)]
    # 側廊 v2 自己改過的格放回去再量（重跑逐位元組相同）：船殼刻掉的窗洞照原色補回、側廊的玻璃拿掉
    gc_path = os.path.join(design, 'masks', 'deco', 'gallery_carve.vox.txt')
    gg_path = os.path.join(design, 'masks', 'glass', 'gallery_glass.vox.txt')
    if os.path.exists(gg_path):
        gg = set(map(tuple, np.loadtxt(gg_path, delimiter=',', comments='#', dtype=np.int64, ndmin=2, encoding='utf-8')[:, :3].tolist()))
        A = A[np.array([tuple(r) not in gg for r in A[:, :3].tolist()], bool)]
    Hl = export_list('gura-pinas-01m', None)
    if os.path.exists(gc_path):
        G0 = np.loadtxt(gc_path, delimiter=',', comments='#', dtype=np.int64, ndmin=2, encoding='utf-8')
        have = set(map(tuple, A[:, :3].tolist()))
        add = np.array([r for r in G0.tolist() if tuple(r[:3]) not in have], dtype=A.dtype).reshape(-1, A.shape[1])
        A = np.concatenate([A, add[:, :A.shape[1]]]) if len(add) else A
        hs = set(map(tuple, Hl[:, :3].tolist()))
        addh = np.array([r for r in G0.tolist() if tuple(r[:3]) not in hs], dtype=Hl.dtype).reshape(-1, Hl.shape[1])
        Hl = np.concatenate([Hl, addh[:, :Hl.shape[1]]]) if len(addh) else Hl
    hull_col = {tuple(r[:3]): int(r[3]) for r in Hl.tolist()}
    hull_cells = set(hull_col)
    GLASS_REAL = int(open(os.path.join(design, 'masks', 'glass', 'stern_glass.vox.txt'), encoding='utf-8').read().splitlines()[1].split(',')[3])   # 跟鏡板的玻璃同一色
    occ = set(map(tuple, A[:, :3].tolist()))
    aft, outer, fwd = {}, {}, {}
    for x, y, z in A[:, :3].tolist():
        if x < 210:
            if x < aft.get((y, z), 10 ** 6):
                aft[(y, z)] = x
        dy = abs(y - YC)
        if dy > outer.get((x, z), -1):
            outer[(x, z)] = dy
        if x >= 400 and y == YC and x > fwd.get(z, -1):
            fwd[z] = x
    parts = {}
    R_v2 = {}

    def put(part, x, y, z, c):
        parts.setdefault(part, {})[(int(x), int(y), int(z))] = c

    def both(part, x, dy, z, c):
        put(part, x, YC + dy, z, c)
        put(part, x, YC - dy, z, c)

    # ── galjoen（船首喙）：甲板＋head rail＋cutwater ──
    E = plan['espolon']
    F = plan['figurehead']
    xs0 = int(math.floor(float(L.x_stem(80)) + 0.5)) - 1           # 艏柱前緣那一格（z 73.6 以上直立）
    if E.get('v2'):                                                   # TASK-0967 船頭 v2：plan 有 espolon.v2 才走（沒有 ⇒ 下面 v1 一格不變）
        ztf = galjoen_v2(E['v2'], F, xs0, Hl, L, YC, put, both, R_v2)
    else:
        tip = xs0 + E['len_beyond_stem']
        zt, th = E['deck_top_z'], E['thick']
        ztf = lambda x: zt
        wpar = lambda x: E['half_at_tip'] + (E['half_at_stem'] - E['half_at_tip']) * (1 - (x - xs0) / float(E['len_beyond_stem'])) ** E['taper_pow']
        for x in range(xs0 + 1, tip + 1):
            w = int(math.floor(wpar(x) + 0.5))
            for dy in range(0, w + 1):
                for z in range(zt - th + 1, zt + 1):
                    both('galjoen', x, dy, z, DECK if z == zt else TRIM)
            for z in range(zt + 1, zt + 1 + E['rail_h']):
                cap = z == zt + E['rail_h']
                if x > F['x'] - 6:
                    continue                                              # head rail 停在獅子後面（收穫號 v1 跟船首像重疊）
                if cap or (x - xs0) % E['stanchion_every'] == 0:
                    both('galjoen', x, w, z, GOLD if cap else WOOD)
                if cap:                                                   # 寬度往前收的地方補台階 ⇒ 頂條面相接（收穫號 v1 只在斜角相接）
                    w2 = int(math.floor(wpar(x + 1) + 0.5))
                    for dy in range(w2, w):
                        both('galjoen', x, dy, z, GOLD)
        z_cw0 = E['cutwater_from_z']
        for z in range(z_cw0, zt - th + 1):
            u = (z - z_cw0) / float(zt - th + 1 - z_cw0)
            xa = fwd.get(z, xs0) + 1
            xf = int(math.floor(xa + (tip - xa) * u ** E['cutwater_pow'] + 0.5))
            for x in range(max(xa, xf - E['cutwater_band']), max(xa, xf) + 1):
                for dy in range(0, E['cutwater_half'] + 1):
                    both('galjoen', x, dy, z, GOLD if xf - x == 2 and dy == E['cutwater_half'] else TRIM)
    # ── 船首像：紅獅子（W p.85：長 9 呎、厚 19 duim、前端翹起 2'7"）——趴在喙尖上、往前往上翹 ──
    xr, ln, ht, rs = F['x'], F['len'], F['half_t'], F['raise']
    xf_ = xr + ln
    zc = lambda x: ztf(x) + 4 + rs * (x - xr) / float(ln)           # 身體中線的高度（v2 的平台往前升 ⇒ 跟著那一欄的平台頂）
    body, mane, crown, eye = F['body'], F['mane'], F['crown'], F['eye']
    for x in range(xr + 2, xf_ - 4):                                   # 身體（橢圓截面：半厚 ht、半高 3.2）
        for z in range(int(zc(x) - 4), int(zc(x) + 5)):
            for dy in range(0, int(ht) + 1):
                if (dy / ht) ** 2 + ((z + 0.5 - zc(x)) / 3.2) ** 2 <= 1.0:
                    both('figurehead', x, dy, z, body)
    hx, hz = xf_ - 3, zc(xf_) + 3                                       # 頭
    mx, mz = xf_ - 6, zc(xf_) + 2                                       # 鬃
    for x in range(xf_ - 11, xf_ + 1):
        for z in range(int(mz - 5), int(hz + 5)):
            for dy in range(0, 4):
                in_head = ((x + 0.5 - hx) / 3.2) ** 2 + (dy / ht) ** 2 + ((z + 0.5 - hz) / 3.2) ** 2 <= 1.0
                in_mane = ((x + 0.5 - mx) / 3.6) ** 2 + (dy / 3.0) ** 2 + ((z + 0.5 - mz) / 4.6) ** 2 <= 1.0
                if in_head:
                    both('figurehead', x, dy, z, body)
                elif in_mane:
                    both('figurehead', x, dy, z, mane)
    ztop = int(hz + 3.2)                                                # 金冠：頭頂一圈、上面一排尖
    for x in range(int(hx) - 2, int(hx) + 3):
        for dy in range(0, 3):
            both('figurehead', x, dy, ztop, crown)
            if (x + dy) % 2 == 0:
                both('figurehead', x, dy, ztop + 1, crown)
    both('figurehead', int(hx) + 2, 1, int(hz) + 1, eye)               # 眼睛
    for x0_, x1_ in ((xr + 3, xr + 6), (xf_ - 9, xf_ - 6)):           # 後腳、前腳：從喙的甲板面往上接到身體
        for x in range(x0_, x1_ + 1):
            for dy in (1, 2):
                for z in range(ztf(x) + 1, int(zc(x)) + 1):
                    both('figurehead', x, dy, z, body)
    for k, z in enumerate(range(int(zc(xr)), int(zc(xr)) + 7)):        # 尾巴：從屁股往後上翹，尾端一撮金
        put('figurehead', xr + 2 - k // 3, YC, z, mane if k >= 5 else body)
        if k and k % 3 == 0:                                            # 往後挪一格的那一階補一格 ⇒ 面相接（v1 只在斜角相接 ⇒ 尾端 1 格浮空）
            put('figurehead', xr + 3 - k // 3, YC, z, mane if k >= 5 else body)
    # ── 船尾走廊（hut 那排窗下面） ──
    S = plan['stern_deco']
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
                both('stern-deco', xo, dy, z, GOLD if cap else BLUE)
        if dy == hb:
            for z in range(zf + 1, zf + bal['rail_h'] + 1):
                fz = aft.get((YC + dy, z), fxa)                        # 鏡板往後倒：每一層的船尾位置不同
                for x in range(xo, min(fxa, fz)):
                    if z == zf + bal['rail_h'] or (x - xo) % 2 == 0:
                        both('stern-deco', x, dy, z, GOLD if z == zf + bal['rail_h'] else BLUE)
        if dy % 8 == 0:                                                # 托架：斜撐接回鏡板
            for j, z in enumerate(range(zf - 4, zf)):
                fz = aft.get((YC + dy, z))
                if fz is not None:
                    for x in range(fz - 1 - j, fz):
                        both('stern-deco', x, dy, z, WOOD)
    # ── 兩舷側廊（伸出 out 格；下面一節收成 0、上面一個銅頂） ──
    #   v2（Tim 2026-10-26「側面窗戶是否也能改成玻璃 且打通到艙內」）：
    #   · 每 8 格一個開間、開間的外面是直立的一片（照這一段船殼最外面那一格 ＋ out）⇒ 窗是方的（v1 外面順著船殼斜 ⇒ 每一格深淺不同、窗歪成 L 形）
    #   · 窗的玻璃另外一份清單（masks/glass/gallery_glass.vox.txt ⇒ -stern-glass 子作品，關聯 material=glass）；
    #     玻璃後面一路刻穿到艙裡：側廊這一段不放格、船殼的牆照 masks/deco/gallery_carve.vox.txt 刻（tools/hull_expected.py 的一步）
    Q = S['quarter_gallery']
    wrows = Q['win_rows']
    obody = {}
    for x in range(Q['x0'], Q['x1'] + 1):
        vs = [outer[(x, z)] for z in range(Q['z0'] + 5, Q['z1'] + 1) if (x, z) in outer and (x, YC + outer[(x, z)], z) in occ]
        if vs:
            obody[x] = max(vs)
    bay = lambda x: (x - Q['x0']) // 8
    fy = {}
    for x, o in obody.items():
        fy[bay(x)] = max(fy.get(bay(x), -1), o + Q['out'])
    gal_glass, gal_shaft = {}, set()
    for x in range(Q['x0'], Q['x1'] + 1):
        for z in range(Q['z0'], Q['z1'] + 1):
            if (x - Q['x0']) % 8 in (3, 4, 5) and any(a_ <= z <= b_ for a_, b_ in wrows) and bay(x) in fy:
                gal_glass[(x, YC + fy[bay(x)], z)] = GLASS_REAL
                gal_shaft.add((x, z))
    for x in range(Q['x0'], Q['x1'] + 1):
        if bay(x) not in fy:
            continue
        F = fy[bay(x)]
        for z in range(Q['z0'], Q['z1'] + Q['roof_h'] + 1):
            hz_ = min(z, Q['z1'])
            o = outer.get((x, hz_))
            if o is None or (x, YC + o, hz_) not in occ:
                continue
            ext = F - o
            if z <= Q['z0'] + 4:
                out = max(1, round(ext * (z - Q['z0'] + 1) / 5.0))
            elif z > Q['z1']:
                k = z - Q['z1']
                out = max(0, ext - k)
                inset = 2 * k
                if x < Q['x0'] + inset or x > Q['x1'] - inset or out == 0:
                    continue
            else:
                out = ext
            for d in range(1, out + 1):
                face = d == out
                if (x, z) in gal_shaft and z <= Q['z1']:
                    continue                                           # 窗：外面那一格是玻璃（另一份清單）、裡面一路空到船殼
                c = BLUE
                if z > Q['z1']:
                    c = GOLD if z == Q['z1'] + 1 else Q['roof']
                elif z in (Q['z0'] + 4, Q['z1']):
                    c = GOLD
                elif face and (x - Q['x0']) % 8 in (2, 3, 4, 5, 6) and any(a_ - 1 <= z <= b_ + 1 for a_, b_ in wrows):
                    c = GOLD
                elif face and (x - Q['x0']) % 8 in (0, 7):
                    c = TRIM                                           # 開間之間的壁柱
                both('stern-deco', x, o + d, z, c)
    # 船殼的牆：窗那一欄從外面往裡刻到第一格空氣（只刻船殼的格；碰到別的件 ⇒ 照實報）
    gal_carve, gal_block = {}, []
    for (x, z) in sorted(gal_shaft):
        for sgn in (1, -1):
            o = outer.get((x, z))
            y = YC + sgn * o
            n = 0
            while (x, y, z) in occ and n < 12:
                if (x, y, z) not in hull_cells:
                    gal_block.append((x, y, z))
                    break
                gal_carve[(x, y, z)] = hull_col[(x, y, z)]
                y -= sgn
                n += 1
            if n >= 12:
                gal_block.append((x, y, z))
    for (x, y, z), c in list(gal_glass.items()):
        gal_glass[(x, 2 * YC - y, z)] = c
    # ── hackebort：鏡板頂上那塊板（順著鏡板往後倒、頂上拱形）；奶油底、藍帶金字、藍鯊紋章 ──
    H = S['hackebort']
    z0, z1, half, af, htop = H['z0'], H['z1'], H['half'], H['arch_from'], H['half_top']
    rake = math.tan(math.radians(plan['lines']['sternpost_rake_deg']['v']))
    zb = z0 - 1                                                         # 坐在船殼頂那一層上
    halfz = lambda z: half if z < af else htop + (half - htop) * math.sqrt(max(0.0, 1 - ((z - af + 0.5) / float(z1 - af + 1)) ** 2))
    base = {}
    for dy in range(-half, half + 1):                                   # 每一欄的船尾位置照船殼頂那一層；船殼頂比板窄的那幾欄照最近的一欄
        b = aft.get((YC + dy, zb))
        if b is None:
            for k in range(1, 6):
                b = aft.get((YC + (dy - k if dy > 0 else dy + k), zb))
                if b is not None:
                    break
        base[dy] = b
    face = {}
    for z in range(z0, z1 + 1):
        hw = halfz(z)
        for dy in range(-half, half + 1):
            if abs(dy) > hw + 1e-9 or base[dy] is None:
                continue
            xf0 = base[dy] - int((z - zb) * rake + 0.5)
            edge = abs(dy) + 1 > hw or z in (z0, z1) or abs(dy) + 1 > halfz(z + 1)
            for t in range(H['thick']):
                put('hackebort', xf0 + t, YC + dy, z, H['border'] if edge else H['field'])
            face[(dy, z)] = xf0
    R_ = H['ribbon']
    for (dy, z), xf0 in face.items():                                   # 名帶（只換最外那一層）
        if R_['z0'] < z < R_['z1'] and abs(dy) < half - 1:
            put('hackebort', xf0, YC + dy, z, R_['color'])
    text = R_['text']
    wtxt = sum(len(FONT[ch][0]) for ch in text) + (len(text) - 1)
    ycur = -(wtxt // 2)
    for ch in text:                                                     # 從船尾看左手 ＝ −y ⇒ 第一個字在 y 最小那邊
        g = FONT[ch]
        for c in range(len(g[0])):
            for r in range(5):
                if g[r][c] == 'X':
                    z = R_['z1'] - 1 - r
                    put('hackebort', face[(ycur + c, z)], YC + ycur + c, z, R_['text_color'])
        ycur += len(g[0]) + 1
    SH = H['shark']                                                     # 藍鯊：頭朝左（−y）
    wsh = len(SH['rows'][0])
    for r, row in enumerate(SH['rows']):
        z = SH['z_top'] - r
        for c, ch in enumerate(row):
            if ch in SH:
                dy = c - wsh // 2
                put('hackebort', face[(dy, z)], YC + dy, z, SH[ch])
    # 裝飾不蓋船的格：落在佔用格上的照實數出來、不放
    skipped = {}
    if R_v2:                                                            # galjoen v2 跟船殼、其他件圍出來的封閉空氣（6 連通、框外擴 3 格）⇒ 補進 galjoen（Ship_Ends §4.3 填縫）
        from scipy import ndimage
        gk = np.array(list(parts['galjoen']))
        lo_, hi_ = gk.min(axis=0) - 3, gk.max(axis=0) + 3
        sol = np.zeros(tuple(hi_ - lo_ + 1), bool)
        for k in list(occ) + [k for nm_ in parts for k in parts[nm_]]:
            if all(lo_[i] <= k[i] <= hi_[i] for i in range(3)):
                sol[k[0] - lo_[0], k[1] - lo_[1], k[2] - lo_[2]] = True
        cav = ndimage.binary_fill_holes(sol) & ~sol
        for (i, j, k) in np.argwhere(cav).tolist():
            put('galjoen', i + lo_[0], j + lo_[1], k + lo_[2], TRIM)
        R_v2['cavity_filled'] = int(cav.sum())
    for nm in list(parts):
        bad = [k for k in parts[nm] if k in occ]
        skipped[nm] = len(bad)
        if bad and R_v2:
            R_v2.setdefault('skipped_sample', {})[nm] = sorted(bad)[:12]
        for k in bad:
            del parts[nm][k]
    if probe:
        nm, dv = probe[0].split('=')[1].split(':')
        parts[nm] = {(x, y + int(dv), z): c for (x, y, z), c in parts[nm].items()}

    # ── 讀數 ──
    R = {'parts': {}, 'skipped_on_ship': skipped}
    if R_v2:
        R['galjoen_v2'] = R_v2
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
    B = LY.bowsprit(plan)                                               # 艏斜桅那一條線（半徑 3）有沒有被喙、獅子擋到
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
        xl = face[(dy, z1)]
        R['lanterns'].append({'dy': dy, 'at': [xl + 1.0, YC + dy + 0.5, z1 + 1], 'on_solid': (xl, YC + dy, z1) in allk,
                              'air_above': (xl, YC + dy, z1 + 1) not in occ and (xl, YC + dy, z1 + 1) not in allk})
    if probe:
        print(json.dumps({'probe': probe[0], 'parts': {k: {kk: v[kk] for kk in ('overlap_ship', 'mirror_diff', 'cells_touching_ship')} for k, v in R['parts'].items()}}, ensure_ascii=False))
        return
    od = os.path.join(design, 'masks', 'deco')
    os.makedirs(od, exist_ok=True)
    R['lists'] = {}
    for nm, cells in parts.items():
        p = os.path.join(od, nm + '.vox.txt')
        with open(p, 'w', encoding='utf-8', newline='\n') as f:
            f.write('# 藍鯊號 %s（draft_deco.py；世界座標，at 0,0,0）\n' % nm)
            for (x, y, z) in sorted(cells):
                f.write('%d,%d,%d,%d\n' % (x, y, z, cells[(x, y, z)]))
        R['lists'][nm] = [len(cells), hashlib.sha256(open(p, 'rb').read()).hexdigest()]
    # 側廊 v2：玻璃與船殼要刻的窗洞
    os.makedirs(os.path.dirname(gg_path), exist_ok=True)
    for path, cells, head in ((gg_path, gal_glass, '# 藍鯊號 側廊窗玻璃（draft_deco.py 側廊 v2；1 格厚、後面一路空到艙裡；併進 -stern-glass 子作品）'),
                              (gc_path, gal_carve, '# 藍鯊號 側廊窗洞：船殼的牆要刻的格（carvevox；第 4 欄 ＝ 刻之前的顏色，守門；tools/hull_expected.py 的一步）')):
        with open(path, 'w', encoding='utf-8', newline='\n') as f:
            f.write(head + '\n')
            for k in sorted(cells):
                f.write('%d,%d,%d,%d\n' % (k + (cells[k],)))
        R['lists'][os.path.basename(path)] = [len(cells), hashlib.sha256(open(path, 'rb').read()).hexdigest()]
    allparts = set(allk)
    left = {k for k in occ if k not in gal_carve}
    deep = {}
    for (x, y, z) in gal_carve:
        k = (x, z, 1 if y > YC else -1)
        deep[k] = min(deep.get(k, 10 ** 6), abs(y - YC))
    shafts = {(x, z, 1 if y > YC else -1) for (x, y, z) in gal_glass}
    reach = sum(1 for (x, z, sg) in shafts if (x, z, sg) in deep and (x, YC + sg * (deep[(x, z, sg)] - 1), z) not in left)
    R['gallery_v2'] = {'glass': len(gal_glass), 'hull_carve': len(gal_carve), 'blocked': [list(b) for b in gal_block[:6]], 'blocked_n': len(gal_block),
                       'glass_on_ship': sum(1 for k in gal_glass if k in occ and k not in gal_carve), 'glass_on_parts': sum(1 for k in gal_glass if k in allparts),
                       'shafts': len(shafts), 'shafts_reach_cabin': reach, 'glass_mirror_diff': sum(1 for (x, y, z) in gal_glass if (x, 2 * YC - y, z) not in gal_glass),
                       'carve_mirror_diff': sum(1 for (x, y, z) in gal_carve if (x, 2 * YC - y, z) not in gal_carve)}
    # 圖：船頭側面、船尾正面
    sc = 6
    im = Image.new('RGB', (1560, 900), (250, 248, 240))
    d = ImageDraw.Draw(im)
    d.text((20, 10), '藍鯊號 新圖紙 05：galjoen、紅獅子、船尾走廊、側廊、hackebort（藍鯊紋章）　v1', fill=(0, 0, 0), font=font(18))
    deco = [(k, c) for nm, cells in parts.items() for k, c in cells.items()]
    hullcells = [((x, y, z), c) for x, y, z, c in A.tolist() if x >= 480 or x <= 200]
    best = {}
    for (x, y, z), c in hullcells + deco:
        if x < 480 or y < YC:
            continue
        if y > best.get((x, z), (-1, 0))[0]:
            best[(x, z)] = (y, c)
    for (x, z), (y, c) in best.items():
        if 480 <= x <= 610 and 15 <= z <= 110:
            X, Y = 20 + (x - 480) * sc, 50 + (110 - z) * sc
            d.rectangle([X, Y, X + sc - 1, Y + sc - 1], fill=palette_rgb(int(c)))
    d.text((20, 50 + 96 * sc), '船頭（右舷側面）', fill=(0, 0, 0), font=font(14))
    best = {}
    for (x, y, z), c in hullcells + deco:
        if x > 200:
            continue
        if x < best.get((y, z), (10 ** 6, 0))[0]:
            best[(y, z)] = (x, c)
    ox, oy, s2 = 840, 50, 6
    for (y, z), (x, c) in best.items():
        if 60 <= z <= 132 and 110 <= y <= 210:
            X, Y = ox + (y - 110) * s2, oy + (132 - z) * s2
            d.rectangle([X, Y, X + s2 - 1, Y + s2 - 1], fill=palette_rgb(int(c)))
    d.text((ox, oy + 74 * s2), '船尾正面（從船尾看，左手 ＝ −y）', fill=(0, 0, 0), font=font(14))
    im.save(os.path.join(design, 'sheet05_deco_v1.png'))
    with open(os.path.join(design, 'verify_deco.json'), 'w', encoding='utf-8', newline='\n') as f:
        json.dump(R, f, ensure_ascii=False, indent=1)
    print(json.dumps({k: v for k, v in R.items() if k != 'lists'}, ensure_ascii=False))


if __name__ == '__main__':
    main()
