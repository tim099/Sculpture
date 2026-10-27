# 拉貝爾號 步驟 6（TASK-0965）：裝飾 —— 船首喙（knee of head＋每舷兩根 head rail）、船首像（Mlle de Fontanges）、
#   假艉廊（fausses bouteilles，兩舷）、tableau 上三朵金百合（換色）
#   輸入：plan.json（deco）＋ 作品現況（船殼從 CLI 匯出：船頭外緣、船尾面、船尾側面都照作品的格子量，⛔ 不拿設計陣列當作品）
#   輸出：masks/deco/head.vox.txt、figurehead.vox.txt、bouteilles.vox.txt（世界座標，at 0,0,0）、fleurs_paint.vox.txt（船殼 stampvox overwrite=1）、
#         verify_deco.json、sheet05_deco_v1.png
#   用法：python -I -X utf8 draft_deco.py <design> [--probe=fleur_dy=<船寬方向偏移>]（反向對照：百合花整排往一舷偏，⛔ 不寫檔）
#         [--hull=<船殼帳>]（TASK-1045：船殼改了還沒落格 ⇒ 拿 tools/hull_expected.py 組的帳當船殼）
#   · TASK-1045：plan 有 deco.head.platform ⇒ 船首喙改成 beakhead 平台版（head_platform：喙甲板、側板、欄杆、head 寬帶、cheek、填縫）；knee 只到平台底、herpes 不畫
#   · 收穫號的 draft_deco.py 是 galleon 的 espolón 與 galleries，本船重寫；出處只有讀作品的 wio（calli-cosecha-01m/design/tools/wio.py）。
import sys, os, json, math, hashlib
import numpy as np
from PIL import Image, ImageDraw

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), 'tools'))
import lines as HL
import layout as LY
from draft_lines import font, palette_rgb
from wio import export_list

FLEUR = ['...#...',      # 由上往下（v1 5×7 看起來像三叉戟 ⇒ 7×7）
         '..###..',
         '#..#..#',
         '##.#.##',
         '.#####.',
         '...#...',
         '..###..']


def smoothstep(t):
    t = min(1.0, max(0.0, t))
    return t * t * (3 - 2 * t)


def bez(p0, p1, p2, n=80):
    for i in range(n + 1):
        t = i / n
        yield tuple((1 - t) ** 2 * a + 2 * (1 - t) * t * b + t * t * c for a, b, c in zip(p0, p1, p2))


def head_platform(plan, PF, occ, side, put, YC, parts):
    """TASK-1045（Ship_Ends §4.3、§4.4；做法照 apex-two-galeon-01m 的 espolon／head_band／cheeks，程式本船重寫）：
    喙的甲板跟船殼切口底下的平台同高、連成一整片（船殼佔的格 put 會跳過）、外伸那一段包側板（底下不封、最前面那一欄封）、
    平台邊的欄杆（底欄、柱子只在最外那一層每 post_every 格一根、金扶手）、head 寬帶（艙壁上角彎到船首像後面）、cheek 兩條金線。
    回傳讀數。"""
    bx = int(plan['lines']['beakhead']['x'])
    zt, th = PF['top_z'], PF['thick']
    x0, x1 = bx, PF['tip_x']
    R = {}

    def half(x):
        t = (x - x0) / float(x1 - x0)
        return PF['half_tip'] + (PF['half_from'] - PF['half_tip']) * (1 - t) ** PF['pow']
    # 平台：喙的甲板（zt − th + 1 .. zt）；E[x] ＝ 平台頂那一層最外的 |dy|（喙或船殼，取大的）
    E, over = {}, {}
    for x in range(x0, x1 + 1):
        h = int(math.floor(half(x) + 0.5))
        hs = side.get((x, zt), -1)
        E[x] = max(h, hs)
        over[x] = h > hs
        for dy in range(0, h + 1):
            for z in range(zt - th + 1, zt + 1):
                for sg in (1, -1):
                    put('head', x, YC + sg * dy, z, PF['deck_color'])
    # 側板：只在喙比船殼寬的那一段；跟下一欄的 E 之間補齊（斜的地方不留縫），最前面那一欄 E[x1 + 1] 當 0 ⇒ 整片封
    zs0 = PF['skirt_to_z']
    for x in range(x0, x1 + 1):
        if not over[x]:
            continue
        nxt = E.get(x + 1, 0) if x < x1 else 0
        for dy in range(min(E[x], nxt), E[x] + 1):
            for z in range(zs0, zt - th + 1):
                c = PF['gold'] if z in (zs0, zt - th) else PF['skirt_color']
                for sg in (1, -1):
                    put('head', x, YC + sg * dy, z, c)
    # 欄杆：沿 E 走到 rail_end、前端橫一道；底欄 zt＋1、扶手 zt＋rail_h（金）、柱子 zt＋2 .. zt＋rail_h−1
    RL = PF['rail']
    xe = RL['x_end']
    zb, zc = zt + 1, zt + RL['h']
    for x in range(x0, xe + 1):
        nxt = E[x + 1] if x < xe else E[x]
        for dy in range(min(E[x], nxt), E[x] + 1):
            for sg in (1, -1):
                put('head', x, YC + sg * dy, zb, RL['color'])
                put('head', x, YC + sg * dy, zc, PF['gold'])
        if (x - x0) % RL['post_every'] == 0:
            for z in range(zb + 1, zc):
                for sg in (1, -1):
                    put('head', x, YC + sg * E[x], z, RL['color'])
    for dy in range(0, E[xe] + 1):
        for sg in (1, -1):
            put('head', xe, YC + sg * dy, zb, RL['color'])
            put('head', xe, YC + sg * dy, zc, PF['gold'])
            if dy % RL['post_every'] == 0:
                for z in range(zb + 1, zc):
                    put('head', xe, YC + sg * dy, z, RL['color'])
    # head 寬帶：上緣兩段拋物線（艙壁上角 → 最低點斜率 0 → 船首像後面）、帶高 h、1 格厚；dy 從艙壁那一欄船殼的最外一格照 t^p 收到 dy_e
    #   （起點跟艙壁角的船殼同一個 dy ⇒ 面貼面接上；外一格只有斜角相碰 ⇒ 浮空）
    B = PF['band']
    dy0 = side.get((x0 - 1, B['z_h']), 0)

    def btop(x):
        if x <= B['x_l']:
            return B['z_l'] + (B['z_h'] - B['z_l']) * ((B['x_l'] - x) / float(B['x_l'] - B['x_h'])) ** 2
        return B['z_l'] + (B['z_e'] - B['z_l']) * ((x - B['x_l']) / float(B['x_e'] - B['x_l'])) ** 2

    def bdy(x):
        t = (x - B['x_h']) / float(B['x_e'] - B['x_h'])
        return dy0 + (B['dy_e'] - dy0) * t ** B['dy_pow']
    band_lo = 99
    for x in range(B['x_h'], B['x_e'] + 1):
        ztop_ = int(math.floor(btop(x) + 0.5))
        d0 = int(math.floor(bdy(x) + 0.5))
        d1 = int(math.floor(bdy(x + 1) + 0.5)) if x < B['x_e'] else d0
        for dy in range(min(d0, d1), max(d0, d1) + 1) if d1 < d0 else (d0,):
            for z in range(ztop_ - B['h'] + 1, ztop_ + 1):
                c = PF['gold'] if z in (ztop_, ztop_ - B['h'] + 1) else B['fill']
                for sg in (1, -1):
                    put('head', x, YC + sg * dy, z, c)
        band_lo = min(band_lo, ztop_ - B['h'] + 1)
    R['band_bottom_min_z'] = band_lo
    R['rail_top_z'] = zc
    # cheek：船頭兩側貼著船殼外一格的金線（照 x 線性往下），dy 跳格的地方補齊
    for ch in PF['cheeks']:
        prev = None
        for x in range(ch['x0'], ch['x1'] + 1):
            z = int(math.floor(ch['z0'] + (ch['z1'] - ch['z0']) * (x - ch['x0']) / float(ch['x1'] - ch['x0']) + 0.5))
            if (x, z) not in side:
                continue
            d = side[(x, z)] + 1
            for dy in (range(d, prev + 1) if prev is not None and prev > d else (d,)):
                for sg in (1, -1):
                    put('head', x, YC + sg * dy, z, PF['gold'])
            prev = d
    # 封閉的小空腔（側板、平台、船殼圍出來的縫）：框裡從框邊灌，灌不到的空格補進喙（Ship_Ends §4.3 espolon_cavity_filled）
    from scipy import ndimage
    fx0, fx1, fy0, fy1, fz0, fz1 = x0 - 3, x1 + 3, YC - 30, YC + 30, zs0 - 4, zc + 12
    sol = np.zeros((fx1 - fx0 + 1, fy1 - fy0 + 1, fz1 - fz0 + 1), bool)
    for src in (occ, parts['head']):
        for (x, y, z) in src:
            if fx0 <= x <= fx1 and fy0 <= y <= fy1 and fz0 <= z <= fz1:
                sol[x - fx0, y - fy0, z - fz0] = True
    lab, n = ndimage.label(~sol)
    edge = set(np.unique(np.concatenate([lab[0].ravel(), lab[-1].ravel(), lab[:, 0].ravel(), lab[:, -1].ravel(), lab[:, :, 0].ravel(), lab[:, :, -1].ravel()])))
    filled = 0
    for i in range(1, n + 1):
        if i in edge:
            continue
        for xi, yi, zi in np.argwhere(lab == i):
            put('head', xi + fx0, yi + fy0, zi + fz0, PF['skirt_color'])
            filled += 1
    R['cavity_filled'] = filled
    return R


def main():
    sys.stdout.reconfigure(encoding='utf-8')
    design = sys.argv[1]
    probe = [a.split('=', 1)[1] for a in sys.argv[2:] if a.startswith('--probe')]
    plan = HL.load_plan(design)
    L = HL.Lines(plan)
    YC = L.YC
    D = plan['deco']
    hull_list = next((a.split('=', 1)[1] for a in sys.argv[2:] if a.startswith('--hull=')), None)
    if hull_list:
        # TASK-1045：船殼改了還沒落格 ⇒ 拿 tools/hull_expected.py 組的帳當船殼
        W = np.loadtxt(hull_list, delimiter=',', comments='#', dtype=np.int32, ndmin=2, encoding='utf-8')
    else:
        W = export_list('ame-labelle-01m', None)
    occ = {(x, y, z): c for x, y, z, c in W.tolist()}
    # 船頭外緣：中線那一欄每個 z 最前面的格
    bow = {}
    for (x, y, z) in occ:
        if y == YC and x > 150:
            bow[z] = max(bow.get(z, -1), x)
    # 船尾面：每個 (y, z) 最後面那一格（x < 75）
    aft = {}
    for (x, y, z) in occ:
        if x < 75 and x < aft.get((y, z), 999):
            aft[(y, z)] = x
    # 右舷外緣：每個 (x, z) 最大的 dy
    side = {}
    for (x, y, z) in occ:
        if y > YC:
            side[(x, z)] = max(side.get((x, z), 0), y - YC)

    parts = {'head': {}, 'figurehead': {}, 'bouteilles': {}}

    def put(part, x, y, z, c):
        k = (int(x), int(y), int(z))
        if k in occ:
            return
        parts[part][k] = c

    # ── 船首喙：knee of head（中線 3 格厚）──
    H = D['head']
    ext_max, z0k, z1k, ztop = H['ext'], H['z_from'], H['z_full'], H['z_top']
    PF = H.get('platform')
    if PF:
        # TASK-1045：knee 只到平台底（平台另外鋪）
        ztop = PF['top_z'] - PF['thick']
    tip_x = None
    for z in range(z0k, ztop + 1):
        if z not in bow:
            continue
        ext = ext_max * smoothstep((z - z0k) / float(z1k - z0k)) if z <= H['z_tip_top'] else H['ext_upper']
        xe = bow[z] + int(round(ext))
        for x in range(bow[z] + 1, xe + 1):
            for dy in (-1, 0, 1):
                c = H['gold'] if (z >= H['z_tip_top'] - 1 and x >= xe - 2 and z <= H['z_tip_top']) else H['color']
                put('head', x, YC + dy, z, c)
        if z == H['z_tip_top']:
            tip_x = xe
    RP = None
    if PF:
        tip_x = PF['tip_x']
        RP = head_platform(plan, PF, occ, side, put, YC, parts)
    # head rails：每舷兩根（2 格高、1 格厚），從船頭舷牆掃到 knee 的前端（TASK-1045 平台版：herpes 換成平台欄杆＋head 寬帶）
    for r in ([] if PF else H['rails']):
        zs, ze = r['z_hull'], r['z_tip']
        xs = bow[zs] - 2
        hb0 = side.get((xs, zs), 10)
        for sgn in (1, -1):
            for (x, y, z) in bez((xs, hb0 + 1, zs), (xs + r['mid_dx'], r['mid_dy'], zs - 1), (tip_x - r['tip_back'], 2, ze)):
                for dz in (0, 1):
                    put('head', round(x), YC + sgn * round(y), round(z) + dz, H['rail_color'])

    # ── 船首像：Mlle de Fontanges（立在 knee 前端上面，直立；局部 u 往船頭、v 船寬、w 往上）──
    F = D['figurehead']
    bx, bz = tip_x - F['back'], (PF['top_z'] if PF else H['z_tip_top']) + 1
    for w, row in enumerate(F['rows']):
        for (u0, u1, vh, c) in row:
            for u in range(u0, u1 + 1):
                for v in range(-vh, vh + 1):
                    put('figurehead', bx + u, YC + v, bz + w, c)

    # ── 假艉廊（fausses bouteilles）：船尾兩舷各一座，貼在舷外 ──
    B = D['bouteille']
    for x in range(B['x0'] - 2, B['x1'] + 3):
        for z in range(B['z_bot'] - 3, B['z_top'] + 4):
            hb = side.get((x, z))
            if hb is None:
                continue
            core = B['x0'] <= x <= B['x1'] and B['z0'] <= z <= B['z1']
            cap = (B['x0'] + 2 <= x <= B['x1'] - 2) and (B['z1'] < z <= B['z_top'])
            drop = (B['x0'] + 2 <= x <= B['x1'] - 2) and (B['z_bot'] <= z < B['z0'])
            fin = x == (B['x0'] + B['x1']) // 2 and B['z_bot'] - 3 <= z < B['z_bot']
            if not (core or cap or drop or fin):
                continue
            depth = B['depth'] if core else (B['depth'] - 1 if (cap or drop) else 1)
            for d in range(1, depth + 1):
                c = B['color']
                if core and (z in (B['z0'], B['z1']) or x in (B['x0'], B['x1'])):
                    c = B['gold']
                if (cap and z == B['z_top']) or fin:
                    c = B['gold']
                if core and d == depth and any(a0 <= x <= a1 for a0, a1 in B['windows_x']) and B['win_z'][0] <= z <= B['win_z'][1]:
                    c = B['glass_color']
                for sgn in (1, -1):
                    put('bouteilles', x, YC + sgn * (hb + d), z, c)

    # ── 三朵金百合：船尾面那一層換色 ──
    FL = D['fleurs']
    shift = int(probe[0].split('=')[1]) if probe else 0
    paint = {}
    for dyc in FL['dy']:
        for i, row in enumerate(FLEUR):
            z = FL['z_top'] - i
            for j, ch in enumerate(row):
                if ch != '#':
                    continue
                y = YC + dyc + shift + j - len(row) // 2
                x = aft.get((y, z))
                if x is None:
                    continue
                if x > float(L.x_aft(z + 0.5)) + 2:      # 只換船尾面那一層（同 draft_ports 的 tableau）
                    continue
                if occ[(x, y, z)] != FL['color']:
                    paint[(x, y, z)] = FL['color']

    # ── 讀數 ──
    R = {'parts': {k: len(v) for k, v in parts.items()}, 'fleur_cells': len(paint), 'tip_x': tip_x}
    if RP:
        R['platform'] = RP
    allp = {}
    for k, v in parts.items():
        for kk in v:
            allp[kk] = allp.get(kk, 0) + 1
    R['overlap_between_parts'] = sum(1 for v in allp.values() if v > 1)
    R['overlap_hull'] = sum(1 for k in allp if k in occ)
    R['mirror_diff'] = {k: sum(1 for (x, y, z), c in v.items() if v.get((x, 2 * YC - y, z)) != c) for k, v in parts.items()}
    R['fleur_mirror_diff'] = sum(1 for (x, y, z), c in paint.items() if paint.get((x, 2 * YC - y, z)) != c)
    # 艏斜桅會不會撞到船首喙、船首像：沿桅軸、半徑 2.5 格內的格
    BS = LY.bowsprit(plan)
    a = math.radians(BS['angle'])
    clash = 0
    for (x, y, z) in list(parts['figurehead']) + list(parts['head']):
        t = (x + 0.5 - BS['x0']) * math.cos(a) + (z + 0.5 - BS['z0']) * math.sin(a)
        px, pz = BS['x0'] + t * math.cos(a), BS['z0'] + t * math.sin(a)
        if 0 <= t <= BS['len'] and math.hypot(x + 0.5 - px, z + 0.5 - pz) ** 2 + (y - YC) ** 2 <= 2.5 ** 2:
            clash += 1
    R['bowsprit_clash'] = clash
    if probe:
        print(json.dumps({'probe': probe[0], 'fleur_cells': len(paint), 'fleur_mirror_diff': R['fleur_mirror_diff']}, ensure_ascii=False))
        return
    out = os.path.join(design, 'masks', 'deco')
    os.makedirs(out, exist_ok=True)
    R['lists'] = {}

    def dump(name, cells, head):
        p = os.path.join(out, name + '.vox.txt')
        with open(p, 'w', encoding='utf-8', newline='\n') as f:
            f.write(head)
            for k in sorted(cells):
                f.write('%d,%d,%d,%d\n' % (k[0], k[1], k[2], cells[k]))
        R['lists'][name] = [len(cells), hashlib.sha256(open(p, 'rb').read()).hexdigest()]
    for k, v in parts.items():
        dump(k, v, '# 拉貝爾號 %s（draft_deco.py；世界座標，at 0,0,0）\n' % k)
    dump('fleurs_paint', paint, '# 拉貝爾號 tableau 三朵金百合（船殼 stampvox overwrite=1：換色）\n')
    # 圖：右舷側面（船頭、船尾）＋船尾正面
    sc = 6
    im = Image.new('RGB', (1500, 520), (250, 248, 240))
    d = ImageDraw.Draw(im)
    d.text((10, 6), 'La Belle sheet 05 deco v1 (bow side, stern side, stern face)', fill=(0, 0, 0), font=font(14))
    allc = dict(occ)
    for (x, y, z), c in paint.items():
        allc[(x, y, z)] = c
    for v in parts.values():
        allc.update(v)

    def side_view(ox, oy, xr, zr):
        best = {}
        for (x, y, z), c in allc.items():
            if xr[0] <= x <= xr[1] and zr[0] <= z <= zr[1] and y >= YC and y >= best.get((x, z), (-1, 0))[0]:
                best[(x, z)] = (y, c)
        for (x, z), (y, c) in best.items():
            X, Y = ox + (x - xr[0]) * sc, oy + (zr[1] - z) * sc
            d.rectangle([X, Y, X + sc - 1, Y + sc - 1], fill=palette_rgb(int(c)))
    side_view(10, 40, (196, 250), (10, 60))
    side_view(360, 40, (48, 100), (10, 60))
    best = {}
    for (x, y, z), c in allc.items():
        if x < 75 and x <= best.get((y, z), (999, 0))[0]:
            best[(y, z)] = (x, c)
    for (y, z), (x, c) in best.items():
        X, Y = 700 + (y - (YC - 30)) * sc, 40 + (60 - z) * sc
        d.rectangle([X, Y, X + sc - 1, Y + sc - 1], fill=palette_rgb(int(c)))
    im.save(os.path.join(design, 'sheet05_deco_v1.png'))
    with open(os.path.join(design, 'verify_deco.json'), 'w', encoding='utf-8', newline='\n') as f:
        json.dump(R, f, ensure_ascii=False, indent=1)
    print(json.dumps(R, ensure_ascii=False))


if __name__ == '__main__':
    main()
