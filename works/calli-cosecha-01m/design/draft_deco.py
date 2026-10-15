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


def main():
    sys.stdout.reconfigure(encoding='utf-8')
    design = sys.argv[1]
    probe = [a.split('=', 1)[1] for a in sys.argv[2:] if a.startswith('--probe')]
    plan = HL.load_plan(design)
    L = HL.Lines(plan)
    YC = L.YC
    A = export_list('calli-cosecha-01m-assembly', None, links=None)
    # 船 ＝ 組裝件扣掉本階段自己的四件（已經落過一次的話）—— v1 沒扣 ⇒ 重產時把舊裝飾當成船、新裝飾被大量跳過、galleries 往外長
    own = set()
    for nm in ('espolon', 'figurehead', 'stern-deco', 'name-board'):
        if os.path.exists(os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(design))), 'calli-cosecha-01m-' + nm, 'work.json')):
            W_ = export_list('calli-cosecha-01m-' + nm, None)
            own |= set(map(tuple, W_[:, :3].tolist()))
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
    for x in range(xs0 + 1, tip + 1):
        w = int(math.floor(wpar(x) + 0.5))
        for dy in range(0, w + 1):
            for z in range(zt - th + 1, zt + 1):
                both('espolon', x, dy, z, DECK if z == zt else BLACK)
        for z in range(zt + 1, zt + 1 + E['rail_h']):
            cap = z == zt + E['rail_h']
            if x > plan['figurehead']['x'] - 6:
                continue                                              # head rail 停在船首像前面（v1 跟船首像的斗篷重疊 12 格）
            if cap or (x - xs0) % E['stanchion_every'] == 0:
                both('espolon', x, w, z, GOLD if cap else WOOD)
            if cap:                                                   # 寬度往前收的地方補台階 ⇒ 頂條面相接（v1 只在斜角相接，柱子之間一段段浮空）
                w2 = int(math.floor(wpar(x + 1) + 0.5))
                for dy in range(w2, w):
                    both('espolon', x, dy, z, GOLD)
    z_cw0 = E['cutwater_from_z']
    for z in range(z_cw0, zt - th + 1):
        u = (z - z_cw0) / float(zt - th + 1 - z_cw0)
        xa = fwd.get(z, xs0) + 1
        xf = int(math.floor(xa + (tip - xa) * u ** E['cutwater_pow'] + 0.5))
        for x in range(max(xa, xf - E['cutwater_band']), max(xa, xf) + 1):    # 沿前緣的一條帶子（v1 從艏柱填到前緣 ⇒ 一大塊黑三角，太笨重）
            for dy in range(0, E['cutwater_half'] + 1):
                both('espolon', x, dy, z, PINK if xf - x == 2 and dy == E['cutwater_half'] else BLACK)
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
