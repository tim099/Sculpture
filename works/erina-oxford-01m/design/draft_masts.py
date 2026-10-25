# 牛津號 階段六（TASK-0972）：桅（下桅＋桅樓＋上桅＋上桅帆桅）、艏斜桅（船頭開孔）、帆桁（外部模型的擺法；後桅三角帆桁新做）
#   輸入：plan.json（masts、rig_build）＋ 組裝件現在的格子（CLI 匯出；扣掉本階段自己的件 ⇒ 重產穩定）
#   輸出：masks/masts/<桅>.vox.txt（桅子作品，世界座標）、masks/yards/lateen.vox.txt＋yard_lateen_anchors.json（新元件，自己的座標）、
#         masks/bowsprit_hole/<件>.vox.txt（船殼、艏樓甲板要刻掉的格，帶顏色守門）、yards_placement.json、verify_masts.json
#   用法：python -I -X utf8 draft_masts.py <design>
#   結構參考 calli-cosecha-01m/design/draft_masts.py（桅照傾斜軸、桅樓圓台、艏斜桅開孔整個填滿、帆桁照現有元件縮放）；幾何是本船的。
import sys, os, json, math
import numpy as np

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), 'tools'))
import lines as HL
import layout as LY
from wio import export_list

HULL = 'erina-oxford-01m'
ASM = HULL + '-assembly'
OWN = ('mast-', 'bowsprit', 'yard-')


def occupied():
    """組裝件現在的格子、藏掉本階段自己的關聯（主桅、前桅、後桅、艏斜桅、支索板）⇒ dict。
    🩸 v1 是「匯出整艘、再扣掉自己的清單」：第一次跑時桅還沒放、上一輪的清單卻在 ⇒ 扣掉的其實是船殼 ⇒ 艏斜桅的孔少算 73 格（link_overlap 73）。"""
    lk = json.load(open(os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))), ASM, 'links.json'), encoding='utf-8'))
    names = {l['name'] for l in lk.get('links', lk)}
    hide = ','.join(n for n in ('主桅', '前桅', '後桅', '艏斜桅', '支索板') if n in names)
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
    # ── 三根桅 ──
    for k in ('main', 'fore', 'mizzen'):
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
            # 每節頂一個 cap（黑）把下一節接住
            if i + 1 < len(st):
                zc = z1 - 2
                nxt = M[k + ('_top' if i == 0 else '_tg')]['r'][0]
                xc = float(Y.mast_x(k, zc)) + offs
                for x in range(int(xc - r[1] - 1), int(xc + r[1] + 2 * nxt + 4)):
                    for y in range(int(YC - r[1] - 1), int(YC + r[1] + 2)):
                        for z in (zc, zc + 1):
                            dx = x + 0.5 - (xc + 0.5)
                            if abs(y - YC) <= r[1] + 0.5 and -r[1] - 0.5 <= dx <= r[1] + 2 * nxt + 1.5:
                                cells[(x, y, z)] = C['cap']
        # 桅樓：下桅頂下面的圓台（2 格厚）＋ 外緣一圈矮欄（2 格高、黑頂）
        zt = m['z_top']
        rt = RB['tops'][k]
        xc = float(Y.mast_x(k, zt)) + st[1][4] / 2.0 if len(st) > 1 else float(Y.mast_x(k, zt))
        for x in range(int(xc - rt - 1), int(xc + rt + 2)):
            for y in range(YC - rt - 1, YC + rt + 2):
                d2 = (x + 0.5 - (xc + 0.5)) ** 2 + (y - YC) ** 2
                if d2 <= rt * rt:
                    for z in (zt - 2, zt - 1):
                        cells.setdefault((x, y, z), C['top'])
                    if d2 >= (rt - 1.2) ** 2:
                        cells[(x, y, zt)] = C['top']
                        cells[(x, y, zt + 1)] = C['rim']
        # 上桅頭的 crosstrees（十字兩根，2 格厚）
        if len(st) > 2:
            zc = st[1][2] - M[k + '_top']['head'] - 1
            xc2 = float(Y.mast_x(k, zc)) + st[1][4]
            rc = int(rt * 0.6)                                      # 整數 ⇒ 兩舷對稱（v1 用小數，y 範圍 89..102 不對稱、鏡像差 8）
            for x in range(int(xc2 - rc), int(xc2 + rc + 1)):
                for y in range(YC - rc, YC + rc + 1):
                    if abs(y - YC) <= 1 or abs(x + 0.5 - (xc2 + 0.5)) <= 1:
                        for z in (zc - 1, zc):
                            cells.setdefault((x, y, z), C['top'])
        drop = [c for c in cells if c in occ]
        for c in drop:
            del cells[c]
        parts[k] = cells
        R['masts'][k] = {'cells': len(cells), 'skipped_occupied': len(drop), 'stages': [(s[0], s[1], s[2], round(s[4], 1)) for s in st],
                         'top_z': zt, 'truck_z': st[-1][2]}
    # ── 艏斜桅：桿沿仰角，船殼與艏樓甲板被它穿過的格 ⇒ 刻掉、由艏斜桅填滿 ──
    b = M['bowsprit']
    p0 = Y.bow['p0']
    p1 = Y.bow_point(1.0)
    bs = {}
    cyl(bs, C['mast'], (p0[0] + 0.5, p0[1]), (p1[0] + 0.5, p1[1]), b['r'][0], b['r'][1], YC)
    hole = {k: v for k, v in bs.items() if k in occ}
    parts['bowsprit'] = bs
    R['bowsprit'] = {'cells': len(bs), 'hole_cells': len(hole), 'p0': p0, 'p1': [round(p1[0], 1), round(p1[1], 1)]}
    # 開孔分給哪一件：照 occ 的顏色猜不出來 ⇒ 用各件自己的清單判
    own_lists = {
        HULL: None, HULL + '-deck-fc': None, HULL + '-deck-gun': None, HULL + '-ladders-fc': None,
    }
    holes, left = {}, set(hole)
    for w in own_lists:
        S = {(int(x), int(y), int(z)): int(c) for x, y, z, c in export_list(w, None).tolist()}     # 那一件現在的格（已經刻過的不再刻）
        hit = {k: S[k] for k in hole if k in S}
        if hit:
            holes[w] = hit
            left -= set(hit)
    R['bowsprit']['hole_by_work'] = {w: len(v) for w, v in holes.items()}
    R['bowsprit']['hole_unassigned'] = len(left)
    # ── 帆桁擺法（外部模型；方帆桁照元件的 pivot、等比縮放；後桅三角帆桁新做）──
    yards = Y.yards()
    place = []
    for k, y in yards.items():
        if k == 'mizzen_lateen':
            continue
        src, slen, kind = RB['yard_src'][k]
        s = round(y['len'] / slen, 4)
        if y['on'] == 'bowsprit':
            x, z = y['x'], y['z']
            mast = 'bowsprit'
        else:
            base = y['mast']
            st = Y.masts[base]['stages']
            si = {'main': 0, 'fore': 0, 'mizzen': 0}[base]
            on = y['on']
            si = 0 if on in ('main', 'fore', 'mizzen') else (1 if on.endswith('_top') else 2)
            off = R['masts'][base]['stages'][si][3]
            r = st[si][3][0] if isinstance(st[si][3], list) else st[si][3][0]
            x = float(Y.mast_x(base, y['z'])) + off + r + 2.5
            z = y['z']
            mast = base
        place.append({'name': 'yard-' + (RB['sail_of_yard'][k] or k), 'host': 'bowsprit' if mast == 'bowsprit' else mast, 'source_work': src, 'scale': s,
                      'at': [round(x + 0.5, 2), YC + 0.5, z + 0.5], 'rotate': [0, 0, 0],
                      'meta': {'kind': 'yard', 'mast': mast, 'yard': kind, 'sail': RB['sail_of_yard'][k], 'length_m': round(y['len'] * 0.1, 2),
                               'pivot_anchor': 'pivot', 'turn_axis': 'z', 'rotate_z_deg': 0}})
    # 後桅三角帆桁：新元件（沿 x、前端 +x），140 × 5 × 5、0.1 m；中段粗兩頭細
    yl = M['yards']['mizzen_lateen']
    n = yl['len']
    lat = {}
    for x in range(n):
        t = abs((x + 0.5) / n - 0.5) * 2
        r = 2.0 - 0.9 * t
        for y in range(5):
            for z in range(5):
                if (y - 2) ** 2 + (z - 2) ** 2 <= r * r:
                    lat[(x, y, z)] = C['yard']
    piv = int(round(n * (1 - yl['sling_frac'])))                 # 吊點：前端往後 sling_frac
    anchors = {'pivot': [piv, 2, 2], 'sling': [piv, 2, 4], 'fore': [n - 2, 2, 2], 'peak': [1, 2, 2], 'earing-F': [n - 4, 2, 2], 'earing-A': [3, 2, 2]}
    for i, x in enumerate(range(3, n - 2, 8)):
        anchors['top-%02d' % i] = [x, 2, 2]
    c = yards['mizzen_lateen']
    m = Y.masts['mizzen']
    r = m['stages'][0][3][0]
    place.append({'name': 'yard-mizzen-lateen', 'host': 'mizzen', 'source_work': HULL + '-yard-mizzen-lateen', 'scale': 1,
                  'pivot': [piv + 0.5, 2.5, 2.5], 'at': [round(float(Y.mast_x('mizzen', c['z'])) + 0.5, 2), YC - (r + 3) + 0.5, c['z'] + 0.5], 'rotate': [0, yl['angle_deg'], 0],
                  'meta': {'kind': 'yard', 'mast': 'mizzen', 'yard': 'gaff', 'rig': 'lateen', 'sail': 'mizzen-lateen', 'length_m': round(n * 0.1, 2),
                           'pivot_anchor': 'pivot', 'turn_axis': 'z', 'rotate_y_deg': yl['angle_deg'], 'rotate_z_deg': 0}})
    R['yards'] = place
    R['lateen'] = {'cells': len(lat), 'anchors': anchors}
    # ── 寫檔 ──
    od = os.path.join(design, 'masks', 'masts')
    os.makedirs(od, exist_ok=True)
    for k, cells in parts.items():
        with open(os.path.join(od, k + '.vox.txt'), 'w', encoding='utf-8', newline='\n') as f:
            f.write('# 牛津號 %s（draft_masts.py；世界座標，at 0,0,0）\n' % k)
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
    with open(os.path.join(oy, 'lateen.vox.txt'), 'w', encoding='utf-8', newline='\n') as f:
        f.write('# 牛津號 後桅三角帆桁（自己的座標：沿 x、前端 +x）\n')
        for (x, y, z) in sorted(lat):
            f.write('%d,%d,%d,%d\n' % (x, y, z, lat[(x, y, z)]))
    with open(os.path.join(design, 'yard_lateen_anchors.json'), 'w', encoding='utf-8', newline='\n') as f:
        json.dump(anchors, f, ensure_ascii=False, indent=1)
    with open(os.path.join(design, 'yards_placement.json'), 'w', encoding='utf-8', newline='\n') as f:
        json.dump(place, f, ensure_ascii=False, indent=1)
    with open(os.path.join(design, 'verify_masts.json'), 'w', encoding='utf-8', newline='\n') as f:
        json.dump(R, f, ensure_ascii=False, indent=1)
    print(json.dumps({k: v for k, v in R.items() if k not in ('yards', 'lateen')}, ensure_ascii=False))
    print('yards', len(place), 'lateen cells', len(lat))


if __name__ == '__main__':
    main()
