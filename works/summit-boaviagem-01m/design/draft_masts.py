# 出處：erina-tradewind-01m/design/draft_masts.py（TASK-1097 信風號；TASK-1151 改寫成好旅號 caravela redonda）
#   三角帆桁的元件與擺法照 erina-oxford-01m/design/draft_masts.py（TASK-0972 牛津號後桅三角帆桁）
# 好旅號 步驟 7（TASK-1151）：四根桅、艏斜桅（船頭開孔）、帆桁（外部模型的擺法）、三根三角帆桁元件
#   前桅：下桅＋桅樓＋上桅（方帆兩面）；主桅：單根＋小桅樓；後桅、最後桅：單根 —— 主、後、最後桅各掛一根三角帆桁（〔源〕Domingues 2009）
#   三角帆桁：自己一件子作品（沿 x、前端 +x、中段粗兩頭細），模型 pivot ＝ 吊點、at ＝ 桅在吊點高度的左舷外側、rotate y ＝ 斜角（前端往下）；
#             meta yard=gaff＋rig=lateen＋固定點 fore（Ship_Masts §5：只標 gaff 會甩出舷外）
#   方帆桁：照 Ship_Setup §2.1 縮放風暴角號的元件
#   輸入：plan.json（masts、rig_build）＋ 組裝件現在的格子（CLI 匯出；扣掉本階段自己的件 ⇒ 重產穩定）
#   輸出：masks/masts/<桅>.vox.txt、masks/bowsprit_hole/<件>.vox.txt、masks/yards/<帆桁>.vox.txt、yard_lateen_anchors.json、yards_placement.json、verify_masts.json
#   用法：python -I -X utf8 draft_masts.py <design>
import sys, os, json, math
import numpy as np

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), 'tools'))
import lines as HL
import layout as LY
from wio import export_list

HULL = 'summit-boaviagem-01m'
ASM = HULL + '-assembly'
OWN_LINKS = ('主桅', '前桅', '後桅', '最後桅', '艏斜桅', '支索板')
MASTS = ('fore', 'main', 'mizzen', 'bonav')
LATEEN = ('main', 'mizzen', 'bonav')
MAST_META = {'bonav': 'bonaventure'}   # 遊戲的 mast 值（收穫號 calli-cosecha-01m 的第四根桅也標 bonaventure）


def occupied():
    """組裝件現在的格子、藏掉本階段自己的關聯 ⇒ dict（同信風號：⛔ 不拿上一輪的清單去扣）。"""
    lk = json.load(open(os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))), ASM, 'links.json'), encoding='utf-8'))
    names = {l['name'] for l in lk.get('links', lk)}
    hide = ','.join(n for n in OWN_LINKS if n in names)
    W = export_list(ASM, None, links=None, hide_links=hide or None)
    return {(int(x), int(y), int(z)): int(c) for x, y, z, c in W.tolist()}


def cyl(cells, color, p0, p1, r0, r1, yc):
    """沿 p0 → p1（x, z 平面上的線，y ＝ 中線）畫一根圓桿：每一格離軸的距離 ≤ 那一段的半徑。"""
    (x0, z0), (x1, z1) = p0, p1
    L = math.hypot(x1 - x0, z1 - z0)
    ux, uz = (x1 - x0) / L, (z1 - z0) / L
    rmax = max(r0, r1) + 1
    xa, xb = int(math.floor(min(x0, x1) - rmax)), int(math.ceil(max(x0, x1) + rmax))
    za, zb = int(math.floor(min(z0, z1) - rmax)), int(math.ceil(max(z0, z1) + rmax))
    for x in range(xa, xb + 1):
        for z in range(za, zb + 1):
            dx, dz = x + 0.5 - x0, z + 0.5 - z0
            t = dx * ux + dz * uz
            if t < 0 or t > L:
                continue
            px, pz = dx - t * ux, dz - t * uz
            r = r0 + (r1 - r0) * t / L
            for y in range(int(yc - r - 1), int(yc + r + 2)):
                dy = y - yc
                if px * px + pz * pz + dy * dy <= r * r:
                    cells[(x, y, z)] = color


def lateen_yard(n, r_mid, color):
    """三角帆桁元件：沿 x（0 ＝ 尾端 peak、n−1 ＝ 前端 fore）、中段粗兩頭細；框 n × w × w、軸在 (·, h, h)。"""
    h = int(math.ceil(r_mid)) + 1
    w = 2 * h + 1
    cells = {}
    for x in range(n):
        t = abs((x + 0.5) / n - 0.5) * 2
        r = r_mid - (r_mid - 0.9) * t
        for y in range(w):
            for z in range(w):
                if (y - h) ** 2 + (z - h) ** 2 <= r * r:
                    cells[(x, y, z)] = color
    return cells, h, w


def main():
    sys.stdout.reconfigure(encoding='utf-8')
    design = sys.argv[1]
    plan = HL.load_plan(design)
    L = HL.Lines(plan)
    Y = LY.Layout(plan, L)
    YC = L.YC
    RB = plan['rig_build']
    C = RB['colors']
    M = plan['masts']
    occ = occupied()
    parts = {}
    R = {'masts': {}}
    # ── 四根桅 ──
    for k in MASTS:
        m = Y.masts[k]
        cells = {}
        st = m['stages']
        offs = 0.0
        for i, (nm, z0, z1, r) in enumerate(st):
            if i > 0:
                prev_r = st[i - 1][3][1]
                offs += prev_r + r[0] + 0.5                       # 上一節的桅頭前面（doubling）
            xa, xb = float(Y.mast_x(k, z0)) + offs, float(Y.mast_x(k, z1)) + offs
            cyl(cells, C['mast'], (xa + 0.5, z0), (xb + 0.5, z1), r[0], r[1], YC)
            st[i] = (nm, z0, z1, r, offs)
            if i + 1 < len(st):                                   # 下桅頂一個 cap（黑）把上桅接住
                zc = z1 - 2
                nxt = M[k + '_top']['r'][0]
                xc = float(Y.mast_x(k, zc)) + offs
                for x in range(int(xc - r[1] - 1), int(xc + r[1] + 2 * nxt + 4)):
                    for y in range(int(YC - r[1] - 1), int(YC + r[1] + 2)):
                        for z in (zc, zc + 1):
                            dx = x + 0.5 - (xc + 0.5)
                            if abs(y - YC) <= r[1] + 0.5 and -r[1] - 0.5 <= dx <= r[1] + 2 * nxt + 1.5:
                                cells[(x, y, z)] = C['cap']
        if len(st) == 1:                                          # 單根桅：桅頂一個黑 cap（吊點的滑車座）
            z1, r1 = st[0][2], st[0][3][1]
            xc = float(Y.mast_x(k, z1 - 2))
            cyl(cells, C['cap'], (xc + 0.5, z1 - 3), (float(Y.mast_x(k, z1)) + 0.5, z1), r1 + 0.8, r1 + 0.8, YC)
        rt = RB['tops'].get(k, 0)
        zt = m['z_top']
        if rt:                                                    # 桅樓：下桅頂下面的圓台（2 格厚）＋外緣矮欄（黑頂）
            xc = float(Y.mast_x(k, zt)) + (st[1][4] / 2.0 if len(st) > 1 else 0.0)
            zt0 = zt - (RB.get('top_below', {}).get(k, 0))
            for x in range(int(xc - rt - 1), int(xc + rt + 2)):
                for y in range(YC - rt - 1, YC + rt + 2):
                    d2 = (x + 0.5 - (xc + 0.5)) ** 2 + (y - YC) ** 2
                    if d2 <= rt * rt:
                        for z in (zt0 - 2, zt0 - 1):
                            cells.setdefault((x, y, z), C['top'])
                        if d2 >= (rt - 1.2) ** 2:
                            cells[(x, y, zt0)] = C['top']
                            cells[(x, y, zt0 + 1)] = C['rim']
        drop = [c for c in cells if c in occ]
        for c in drop:
            del cells[c]
        parts[k] = cells
        R['masts'][k] = {'cells': len(cells), 'skipped_occupied': len(drop), 'stages': [(s[0], s[1], s[2], round(s[4], 1)) for s in st],
                         'top_z': zt, 'truck_z': st[-1][2]}
    # ── 艏斜桅：桿沿仰角，船殼與艏樓甲板被它穿過的格 ⇒ 刻掉、由艏斜桅填滿；尖一個黑 cap ──
    b = M['bowsprit']
    p0 = Y.bow['p0']
    p1 = Y.bow_point(1.0)
    (dx, dz) = Y.bow['d']
    bs = {}
    cyl(bs, C['mast'], (p0[0] + 0.5, p0[1]), (p1[0] + 0.5, p1[1]), b['r'][0], b['r'][1], YC)
    cyl(bs, C['cap'], (p1[0] + 0.5 - dx * 2, p1[1] - dz * 2), (p1[0] + 0.5, p1[1]), b['r'][1] + 1.0, b['r'][1] + 1.0, YC)
    hole = {k: v for k, v in bs.items() if k in occ}
    parts['bowsprit'] = bs
    R['bowsprit'] = {'cells': len(bs), 'hole_cells': len(hole), 'p0': p0, 'p1': [round(p1[0], 1), round(p1[1], 1)]}
    holes, left = {}, set(hole)
    for w in (HULL, HULL + '-deck-fc', HULL + '-deck-gun', HULL + '-ladders-fc', HULL + '-head'):
        S = {(int(x), int(y), int(z)): int(c) for x, y, z, c in export_list(w, None).tolist()}
        hit = {k: S[k] for k in hole if k in S}
        if hit:
            holes[w] = hit
            left -= set(hit)
    R['bowsprit']['hole_by_work'] = {w: len(v) for w, v in holes.items()}
    R['bowsprit']['hole_unassigned'] = len(left)
    # ── 帆桁擺法 ──
    yards = Y.yards()
    place = []
    lat_cells, lat_anchors = {}, {}
    for k, y in yards.items():
        base = y['mast']
        if y['kind'] == 'lateen':
            yl = M['yards'][k]
            n = int(yl['len'])
            cells, h, w = lateen_yard(n, RB['lateen_r'][base], C['yard'])
            piv = int(round(n * (1 - yl['fwd'])))                   # 吊點：從尾端量 (1 − fwd)
            anc = {'pivot': [piv, h, h], 'sling': [piv, h, 2 * h], 'fore': [n - 2, h, h], 'peak': [1, h, h],
                   'earing-F': [n - 4, h, h], 'earing-A': [3, h, h]}
            for i, x in enumerate(range(3, n - 2, 8)):
                anc['top-%02d' % i] = [x, h, h]
            name = 'yard-%s-lateen' % base
            lat_cells[name] = (cells, n, w)
            lat_anchors[name] = anc
            r = Y.masts[base]['stages'][0][3][0]
            place.append({'name': name, 'host': base, 'source_work': HULL + '-' + name, 'scale': 1,
                          'pivot': [piv + 0.5, h + 0.5, h + 0.5],
                          'at': [round(float(Y.mast_x(base, y['z'])) + 0.5, 2), YC - (r + h + 1) + 0.5, y['z'] + 0.5],
                          'rotate': [0, yl['angle_deg'], 0],
                          'meta': {'kind': 'yard', 'mast': MAST_META.get(base, base), 'yard': 'gaff', 'rig': 'lateen', 'sail': RB['sail_of_yard'][k], 'length_m': round(n * 0.1, 2),
                                   'pivot_anchor': 'pivot', 'turn_axis': 'z', 'rotate_y_deg': yl['angle_deg'], 'rotate_z_deg': 0}})
            continue
        src, slen, kind = RB['yard_src'][k]
        s_ = round(y['len'] / slen, 4)
        st = Y.masts[base]['stages']
        on = y['on']
        si = 0 if on == base else 1
        off = R['masts'][base]['stages'][si][3]
        r = st[si][3][0]
        x = float(Y.mast_x(base, y['z'])) + off + r + 2.5
        place.append({'name': 'yard-' + k.replace('_', '-'), 'host': base, 'source_work': src, 'scale': s_,
                      'at': [round(x + 0.5, 2), YC + 0.5, y['z'] + 0.5], 'rotate': [0, 0, 0],
                      'meta': {'kind': 'yard', 'mast': base, 'yard': kind, 'sail': RB['sail_of_yard'][k], 'length_m': round(y['len'] * 0.1, 2),
                               'pivot_anchor': 'pivot', 'turn_axis': 'z', 'rotate_z_deg': 0}})
    R['yards'] = place
    R['lateen'] = {k: {'cells': len(v[0]), 'len': v[1], 'w': v[2], 'anchors': len(lat_anchors[k])} for k, v in lat_cells.items()}
    # ── 寫檔 ──
    od = os.path.join(design, 'masks', 'masts')
    os.makedirs(od, exist_ok=True)
    for k, cells in parts.items():
        with open(os.path.join(od, k + '.vox.txt'), 'w', encoding='utf-8', newline='\n') as f:
            f.write('# 好旅號 %s（draft_masts.py；世界座標，at 0,0,0）\n' % k)
            for (x, y, z) in sorted(cells):
                f.write('%d,%d,%d,%d\n' % (x, y, z, cells[(x, y, z)]))
    oh = os.path.join(design, 'masks', 'bowsprit_hole')
    os.makedirs(oh, exist_ok=True)
    for f in os.listdir(oh):
        os.remove(os.path.join(oh, f))
    for w, hit in holes.items():
        with open(os.path.join(oh, w + '.vox.txt'), 'w', encoding='utf-8', newline='\n') as f:
            f.write('# 艏斜桅穿過 %s 的格（carvevox，第 4 欄 ＝ 刻之前的顏色）\n' % w)
            for (x, y, z) in sorted(hit):
                f.write('%d,%d,%d,%d\n' % (x, y, z, hit[(x, y, z)]))
    oy = os.path.join(design, 'masks', 'yards')
    os.makedirs(oy, exist_ok=True)
    for name, (cells, n, w) in lat_cells.items():
        with open(os.path.join(oy, name + '.vox.txt'), 'w', encoding='utf-8', newline='\n') as f:
            f.write('# 好旅號 %s（自己的座標：沿 x、前端 +x；框 %d × %d × %d）\n' % (name, n, w, w))
            for (x, y, z) in sorted(cells):
                f.write('%d,%d,%d,%d\n' % (x, y, z, cells[(x, y, z)]))
    with open(os.path.join(design, 'yard_lateen_anchors.json'), 'w', encoding='utf-8', newline='\n') as f:
        json.dump(lat_anchors, f, ensure_ascii=False, indent=1)
    with open(os.path.join(design, 'yards_placement.json'), 'w', encoding='utf-8', newline='\n') as f:
        json.dump(place, f, ensure_ascii=False, indent=1)
    with open(os.path.join(design, 'verify_masts.json'), 'w', encoding='utf-8', newline='\n') as f:
        json.dump(R, f, ensure_ascii=False, indent=1)
    print(json.dumps({k: v for k, v in R.items() if k not in ('yards',)}, ensure_ascii=False))
    print('yards', len(place))


if __name__ == '__main__':
    main()
