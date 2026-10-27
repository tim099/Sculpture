# 澤漢號 步驟 6（TASK-0966）：裝飾 —— 船首喙（knee of head＋每舷兩根 head rail）、船首像（荷蘭紅獅 leeuw）、
#   窄 hek 上的金色海公雞（Zeehaen ＝ 海公雞，換色）、W p.160 的圓形假砲門（looze poorten，兩舷船頭船尾各一個，換色）
#   輸入：plan.json（deco）＋ 作品現況（船殼從 CLI 匯出：船頭外緣、船尾面、舷側外緣都照作品的格子量，⛔ 不拿設計陣列當作品）
#   輸出：masks/deco/head.vox.txt、figurehead.vox.txt（世界座標，at 0,0,0）、paint.vox.txt（船殼 stampvox overwrite=1：換色）、
#         verify_deco.json、sheet05_deco_v1.png
#   用法：python -I -X utf8 draft_deco.py <design> [--probe=emblem_dy=<船寬方向偏移>]（反向對照：公雞往一舷偏，⛔ 不寫檔）
#   · 出處：ame-labelle-01m/design/draft_deco.py（船首喙、讀作品的量法、圖）；船首像、hek 的圖、假砲門是本船的（拉貝爾號的百合花、假艉廊拿掉）。
import sys, os, json, math, hashlib
import numpy as np
from PIL import Image, ImageDraw

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), 'tools'))
import lines as HL
import layout as LY
from draft_lines import font, palette_rgb
from wio import export_list

# 海公雞（由上往下；G 金、R 紅冠、.空）—— 9 寬 × 10 高，面朝船的右舷（從船尾看往左）
COCK = ['..RR.....',
        '.RGG.....',
        'RGGGG....',
        '..GGG..GG',
        '..GGGGGG.',
        '.GGGGGGGG',
        '..GGGGGG.',
        '...GGGG..',
        '...G..G..',
        '..GG.GG..']


def smoothstep(t):
    t = min(1.0, max(0.0, t))
    return t * t * (3 - 2 * t)


def bez(p0, p1, p2, n=80):
    for i in range(n + 1):
        t = i / n
        yield tuple((1 - t) ** 2 * a + 2 * (1 - t) * t * b + t * t * c for a, b, c in zip(p0, p1, p2))


def lion(F):
    """紅獅（局部 u 往船頭、v 船寬、w 往上）：趴在 knee 上、頭抬起來往前看。回傳 {(u, v, w): 色}。"""
    R, G, T = F['red'], F['gold'], F['tongue']
    c = {}

    def box(u0, u1, v0, v1, w0, w1, col):
        for u in range(u0, u1 + 1):
            for v in range(v0, v1 + 1):
                for w in range(w0, w1 + 1):
                    c[(u, v, w)] = col
    box(0, 9, -2, 2, 1, 4, R)          # 身體
    box(1, 2, -2, -2, 0, 0, R); box(1, 2, 2, 2, 0, 0, R)      # 後腿
    box(8, 10, -2, -2, 0, 0, R); box(8, 10, 2, 2, 0, 0, R)    # 前腿往前伸
    box(8, 11, -3, 3, 3, 8, G)         # 鬃毛
    box(11, 13, -2, 2, 4, 7, R)        # 臉
    box(14, 14, -1, 1, 4, 5, R)        # 鼻吻
    box(14, 14, 0, 0, 3, 3, T)         # 舌頭
    box(10, 12, -1, 1, 9, 9, G)        # 冠
    c[(10, -1, 10)] = G; c[(10, 1, 10)] = G; c[(12, 0, 10)] = G
    box(0, 0, 0, 0, 5, 7, R)           # 尾巴往上翹
    box(0, 1, 0, 0, 8, 8, G)           # 尾巴尖的鬃
    return c


def disc(r):
    """半徑 r 的圓（中心 0,0；格心判斷）—— 兩個方向逐格對稱。"""
    out = []
    for a in range(-int(r) - 1, int(r) + 2):
        for b in range(-int(r) - 1, int(r) + 2):
            if a * a + b * b <= r * r:
                out.append((a, b))
    return out


def main():
    sys.stdout.reconfigure(encoding='utf-8')
    design = sys.argv[1]
    probe = [a.split('=', 1)[1] for a in sys.argv[2:] if a.startswith('--probe')]
    plan = HL.load_plan(design)
    L = HL.Lines(plan)
    YC = L.YC
    D = plan['deco']
    W = export_list('abigail-fluyt-01m', '裝飾:begin')     # 換色之前的船殼（v1 讀現在的 ⇒ 落格之後重跑換色清單變 0 格，帳對不起來）
    occ = {(x, y, z): c for x, y, z, c in W.tolist()}
    # 船頭外緣：中線那一欄每個 z 最前面的格
    bow = {}
    for (x, y, z) in occ:
        if y == YC and x > 250:
            bow[z] = max(bow.get(z, -1), x)
    # 船尾面：每個 (y, z) 最後面那一格（x < 船尾面範圍）
    SX = plan['paint']['stern_x_max']
    aft = {}
    for (x, y, z) in occ:
        if x < SX and x < aft.get((y, z), 999):
            aft[(y, z)] = x
    # 右舷外緣：每個 (x, z) 最大的 dy
    side = {}
    for (x, y, z) in occ:
        if y > YC:
            side[(x, z)] = max(side.get((x, z), 0), y - YC)

    parts = {'head': {}, 'figurehead': {}}

    def put(part, x, y, z, c):
        k = (int(x), int(y), int(z))
        if k in occ or any(k in v for v in parts.values()):     # 船殼、先放的部件優先（v1 紅獅的腳踩進 knee 4 格）
            return
        parts[part][k] = c

    # ── 船首喙：knee of head（中線 3 格厚）──
    H = D['head']
    ext_max, z0k, z1k, ztop = H['ext'], H['z_from'], H['z_full'], H['z_top']
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
    # head rails：每舷兩根（2 格高、1 格厚），從船頭舷牆掃到 knee 的前端
    for r in H['rails']:
        zs, ze = r['z_hull'], r['z_tip']
        xs = bow[zs] - 2
        hb0 = side.get((xs, zs), 10)
        for sgn in (1, -1):
            for (x, y, z) in bez((xs, hb0 + 1, zs), (xs + r['mid_dx'], r['mid_dy'], zs - 1), (tip_x - r['tip_back'], 2, ze)):
                for dz in (0, 1):
                    put('head', round(x), YC + sgn * round(y), round(z) + dz, H['rail_color'])

    # ── 船首像：紅獅，趴在 knee 前端上面 ──
    F = D['figurehead']
    bx, bz = tip_x - F['back'], H['z_tip_top'] + 1
    for (u, v, w), c in lion(F).items():
        put('figurehead', bx + u, YC + v, bz + w, c)

    # ── 換色：hek 上的海公雞（船尾面那一層）＋ 兩舷的圓形假砲門（舷側外緣那一層）──
    E = D['emblem']
    shift = int(probe[0].split('=')[1]) if probe else 0
    paint = {}
    miss = 0
    for i, row in enumerate(E['rows'] if 'rows' in E else COCK):
        z = E['z_top'] - i
        for j, ch in enumerate(row):
            if ch == '.':
                continue
            y = YC + shift + j - len(row) // 2
            x = aft.get((y, z))
            if x is None or x > float(L.x_aft(z + 0.5)) + 2:      # 只換船尾面那一層（同 draft_ports 的 hek）
                miss += 1
                continue
            col = E['gold'] if ch == 'G' else E['red']
            if occ[(x, y, z)] != col:
                paint[(x, y, z)] = col
    P = D['false_ports']
    fp = 0
    for (xc, zc) in P['at']:
        for (a, b) in disc(P['r']):
            x, z = xc + a, zc + b
            hb = side.get((x, z))
            if hb is None:
                continue
            ring = (a * a + b * b) > (P['r'] - 1) ** 2
            col = P['rim'] if ring else P['hole']
            for sgn in (1, -1):
                k = (x, YC + sgn * hb, z)
                if k in occ and occ[k] != col:
                    paint[k] = col
                    fp += 1

    # ── 讀數 ──
    R = {'parts': {k: len(v) for k, v in parts.items()}, 'emblem_cells': sum(1 for k, c in paint.items() if k[0] < SX), 'emblem_missed': miss,
         'false_port_cells': fp, 'tip_x': tip_x}
    allp = {}
    for k, v in parts.items():
        for kk in v:
            allp[kk] = allp.get(kk, 0) + 1
    R['overlap_between_parts'] = sum(1 for v in allp.values() if v > 1)
    R['overlap_hull'] = sum(1 for k in allp if k in occ)
    R['mirror_diff'] = {k: sum(1 for (x, y, z), c in v.items() if v.get((x, 2 * YC - y, z)) != c) for k, v in parts.items()}
    R['false_port_mirror_diff'] = sum(1 for (x, y, z), c in paint.items() if x >= SX and paint.get((x, 2 * YC - y, z)) != c)
    # hek 的圖本來就不對稱（公雞朝一邊）⇒ 量它在中線兩邊的格數，反向對照看偏移
    R['emblem_left_right'] = [sum(1 for (x, y, z) in paint if x < SX and y < YC), sum(1 for (x, y, z) in paint if x < SX and y > YC)]
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
        print(json.dumps({'probe': probe[0], 'emblem_cells': R['emblem_cells'], 'emblem_missed': miss, 'emblem_left_right': R['emblem_left_right']}, ensure_ascii=False))
        return
    out = os.path.join(design, 'masks', 'deco')
    os.makedirs(out, exist_ok=True)
    for f in os.listdir(out):
        if f.endswith('.vox.txt'):
            os.remove(os.path.join(out, f))
    R['lists'] = {}

    def dump(name, cells, head):
        p = os.path.join(out, name + '.vox.txt')
        with open(p, 'w', encoding='utf-8', newline='\n') as f:
            f.write(head)
            for k in sorted(cells):
                f.write('%d,%d,%d,%d\n' % (k[0], k[1], k[2], cells[k]))
        R['lists'][name] = [len(cells), hashlib.sha256(open(p, 'rb').read()).hexdigest()]
    for k, v in parts.items():
        dump(k, v, '# 澤漢號 %s（draft_deco.py；世界座標，at 0,0,0）\n' % k)
    dump('paint', paint, '# 澤漢號 hek 的海公雞＋圓形假砲門（船殼 stampvox overwrite=1：換色）\n')
    # 圖：右舷側面（船頭、船尾）＋船尾正面
    sc = 5
    im = Image.new('RGB', (1500, 560), (250, 248, 240))
    d = ImageDraw.Draw(im)
    d.text((10, 6), '澤漢號 新圖紙 05：船首喙、紅獅、hek 的海公雞、圓形假砲門（右舷側面船頭／船尾、船尾正面）　v1', fill=(0, 0, 0), font=font(14))
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
    side_view(10, 40, (320, 410), (15, 80))
    side_view(480, 40, (45, 130), (15, 80))
    best = {}
    for (x, y, z), c in allc.items():
        if x < SX and x <= best.get((y, z), (999, 0))[0]:
            best[(y, z)] = (x, c)
    for (y, z), (x, c) in best.items():
        X, Y = 950 + (y - (YC - 40)) * sc, 40 + (80 - z) * sc
        d.rectangle([X, Y, X + sc - 1, Y + sc - 1], fill=palette_rgb(int(c)))
    im.save(os.path.join(design, 'sheet05_deco_v1.png'))
    with open(os.path.join(design, 'verify_deco.json'), 'w', encoding='utf-8', newline='\n') as f:
        json.dump(R, f, ensure_ascii=False, indent=1)
    print(json.dumps({k: v for k, v in R.items() if k != 'lists'}, ensure_ascii=False))


if __name__ == '__main__':
    main()
