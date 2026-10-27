# 澤漢號 步驟 7（TASK-0966）；出處 ame-labelle-01m/design/draft_masts.py（拉貝爾號；它出自收穫號 階段六）：本船用回 cofa（plan.rig_build.tops，荷蘭的圓桅樓）、圖的範圍換本船。
# 原檔頭：收穫號 階段六（TASK-0595）：桅（下桅＋cofa＋上桅）、艏斜桅、lateen 帆桁子作品、方帆桁擺放（沿用憲法號的帆桁元件、沿長度縮放）、船頭牆給艏斜桅開孔
#   輸入：plan.json（masts、rig_build、decks_build）＋ 組裝件現在的格子（CLI 匯出：船殼＋甲板＋梯子＋裝飾）
#   輸出：masks/masts/<桅>.vox.txt（桅子作品，世界座標、at 0,0,0）、masks/yards/lateen-<桅>.vox.txt ＋ yards_lateen.json（lateen 子作品的局部座標與固定點）、
#         masks/bowsprit_hole/carve.vox.txt（船殼要刻的格，帶刻之前的顏色守門）、yards_placement.json（每根帆桁模型的 at／pivot／rotate／scale／meta）、
#         verify_masts.json、sheet06_masts_v1.png
#   用法：python -I -X utf8 draft_masts.py <design> [--probe=pivot=<帆桁名>:<dz>]（反向對照：某根帆桁的吊點偏幾格，⛔ 不寫檔）
import sys, os, json, math, hashlib
import numpy as np
from PIL import Image, ImageDraw

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), 'tools'))
import lines as HL
import layout as LY
from draft_lines import font, palette_rgb
from wio import export_list

CELL = 0.1


def main():
    sys.stdout.reconfigure(encoding='utf-8')
    design = sys.argv[1]
    probe = [a.split('=', 1)[1] for a in sys.argv[2:] if a.startswith('--probe')]
    plan = HL.load_plan(design)
    L = HL.Lines(plan)
    YC = L.YC
    RB = plan['rig_build']
    C = RB['colors']
    WORKS = os.path.dirname(os.path.dirname(os.path.abspath(design)))
    A = export_list('abigail-fluyt-01m-assembly', None, links=None)
    own = set()                                                  # 本階段自己的件（重產時扣掉，別把自己當成船）
    for nm in ('mast-fore', 'mast-main', 'mast-mizzen', 'bowsprit'):
        if os.path.exists(os.path.join(WORKS, 'abigail-fluyt-01m-' + nm, 'work.json')):
            own |= set(map(tuple, export_list('abigail-fluyt-01m-' + nm, None)[:, :3].tolist()))
    occ = {tuple(r[:3]): r[3] for r in A.tolist() if tuple(r[:3]) not in own}
    hull = {tuple(r[:3]): r[3] for r in export_list('abigail-fluyt-01m', '裝飾:end').tolist()}   # 開艏斜桅孔之前的船殼（重產時孔的清單才不會變空）
    occ.update({k: c for k, c in hull.items() if k not in occ})   # 刻掉的那幾格在「船」裡照樣算（讓艏斜桅自己決定要不要佔）
    M = {m['key']: m for m in LY.masts(plan, L)}
    parts = {}
    skipped = {}

    def put(part, x, y, z, c):
        k = (int(x), int(y), int(z))
        if k in occ:
            skipped[part] = skipped.get(part, 0) + 1
            return
        parts.setdefault(part, {})[k] = c

    # ── 桅：下桅（腳 → 下桅頂，半徑從 r0 收到 r1）、cofa、上桅、桅頂一點金 ──
    for key, m in M.items():
        r0, r1 = RB['mast_r'][key]
        zh, zt, zp = int(math.floor(m['heel'])) + 1, int(math.floor(m['lower_top'])), int(math.floor(m['platform']))
        part = 'mast-' + key
        for z in range(zh, zt + 1):
            r = r0 + (r1 - r0) * (z - zh) / max(1, zt - zh)
            xa = float(LY.mast_axis_x(plan, key, z + 0.5, L))
            for x in range(int(xa - r) - 1, int(xa + r) + 2):
                for dy in range(0, int(r) + 1):
                    if (x - xa) ** 2 + dy ** 2 <= r * r:
                        put(part, x, YC + dy, z, C['mast'])
                        put(part, x, YC - dy, z, C['mast'])
        CT = RB.get('crosstrees', {}).get(key)
        if CT:                                                   # 桅頂橫桁：trestletrees 沿 x（兩根，dy ±(r+1)）、crosstrees 沿 y（兩根，x 軸 ±(r+1)），一格厚
            xa = float(LY.mast_axis_x(plan, key, zp + 0.5, L))
            rr = int(math.floor(r1)) + 1                             # 緊貼桅頂（v1 ceil＋1 ⇒ 空一格，兩組橫桁浮空；Ship_Masts §5 的坑）
            for t in range(-CT, CT + 1):
                for sg in (1, -1):
                    put(part, round(xa) + t, YC + sg * rr, zp, C['top'])
                    put(part, round(xa) + sg * rr, YC + t, zp + 1, C['top'])
        R_top = RB.get('tops', {}).get(key)
        if R_top:
            xa = float(LY.mast_axis_x(plan, key, zp + 0.5, L))
            for x in range(int(xa - R_top) - 1, int(xa + R_top) + 2):
                for dy in range(0, R_top + 1):
                    d = math.hypot(x - xa, dy)
                    for z in range(zp - 1, zp + RB['tops']['rim_h'] + 1):
                        c = None
                        if z <= zp and d <= R_top:
                            c = C['top']
                        elif z > zp and R_top - 1.5 <= d <= R_top:
                            h = z - zp
                            c = C['rim_cap'] if h == RB['tops']['rim_h'] else (C['rim_band'] if h in (3, 4) else C['top'])
                        if c is not None:
                            put(part, x, YC + dy, z, c)
                            put(part, x, YC - dy, z, c)
        if key in RB['topmast_r']:
            t0, t1 = RB['topmast_r'][key]
            zt2 = int(math.floor(m['truck']))
            for z in range(zp + 1, zt2 + 1):
                r = t0 + (t1 - t0) * (z - zp - 1) / max(1, zt2 - zp - 1)
                xa = float(LY.mast_axis_x(plan, key, z + 0.5, L))
                for x in range(int(xa - r) - 1, int(xa + r) + 2):
                    for dy in range(0, int(r) + 1):
                        if (x - xa) ** 2 + dy ** 2 <= r * r:
                            c = C['truck'] if z == zt2 else C['mast']
                            put(part, x, YC + dy, z, c)
                            put(part, x, YC - dy, z, c)
    # ── 艏斜桅：圓桿（半徑 r0 → r1）；船頭牆在它半徑 ＋0.5 內的格要刻掉（開孔）；甲板板、梯子優先（不放） ──
    B = LY.bowsprit(plan)
    a = math.radians(B['angle'])
    u = (math.cos(a), 0.0, math.sin(a))
    br0, br1 = RB['bowsprit_r']
    hole = {}
    X0, Z0 = B['x0'] + 0.5, B['z0'] + 0.5
    for x in range(int(B['x0']) - 4, int(B['x1']) + 5):
        for z in range(int(B['z0']) - 4, int(B['z1']) + 5):
            px, pz = x + 0.5 - X0, z + 0.5 - Z0
            t = px * u[0] + pz * u[2]
            if t < 0 or t > B['len']:
                continue
            r = br0 + (br1 - br0) * t / B['len']
            dxz2 = (px - t * u[0]) ** 2 + (pz - t * u[2]) ** 2
            for dy in range(0, int(r) + 2):
                d2 = dxz2 + dy * dy
                for yy in {YC + dy, YC - dy}:
                    k = (x, yy, z)
                    if d2 <= (r + 0.5) ** 2 and k in hull:
                        hole[k] = hull[k]
                    if k in hull and d2 <= (r + 0.5) ** 2:
                        parts.setdefault('bowsprit', {})[k] = C['mast']   # 孔整個由艏斜桅填滿 —— v1 牆裡那段跳過 ⇒ 斷開；v2 孔比桿大半格 ⇒ 牆裡 10 個小空腔
                    elif d2 <= r * r and k not in hull:
                        put('bowsprit', x, yy, z, C['mast'])
    # ── lateen 帆桁子作品（局部座標）：斜桿，前端低（x 大）、後端高（x 0）；固定點 pivot／sling／fore／peak／jackstay-k ──
    lat = {}
    for ld in RB['lateen']:
        Lc = ld['len_m'] / CELL
        an = math.radians(ld['angle_deg'])
        ca, sa = math.cos(an), math.sin(an)
        W_ = int(math.ceil(Lc * ca)) + 6
        H_ = int(math.ceil(Lc * sa)) + 6
        yc = 3
        P = lambda s: (3 + (Lc - s) * ca, yc, 3 + s * sa)       # s ＝ 從前端量的長度：前端 (W−3, …, 3)、後端 (3, …, H−3)
        cells = {}
        hs = ld['hoist_frac'] * Lc
        for x in range(0, W_):
            for z in range(0, H_):
                px, pz = x + 0.5 - 3, z + 0.5 - 3
                s = Lc - (px * ca) + 0.0
                # 投影到桿軸：軸方向 (−ca, sa)，原點在前端 (Lc·ca, 0)
                vx, vz = x + 0.5 - (3 + Lc * ca), z + 0.5 - 3
                s = -vx * ca + vz * sa
                if s < -0.5 or s > Lc + 0.5:
                    continue
                d2 = (vx + s * ca) ** 2 + (vz - s * sa) ** 2
                r = 1.0 + 0.7 * max(0.0, 1 - abs(s - hs) / max(hs, Lc - hs))
                for dy in range(0, 2):
                    if d2 + dy * dy <= r * r:
                        cells[(x, yc + dy, z)] = C['top']
                        cells[(x, yc - dy, z)] = C['top']

        def near(s, top=False):
            px, _, pz = P(s)
            best = min((k for k in cells if k[1] == yc), key=lambda k: (k[0] + 0.5 - px) ** 2 + (k[2] + 0.5 - pz) ** 2 - (0.01 * k[2] if top else 0))
            if top:
                z = best[2]
                while (best[0], yc, z + 1) in cells:
                    z += 1
                best = (best[0], yc, z)
            return list(best)
        anchors = {'pivot': near(hs), 'sling': near(hs, True), 'fore': near(1.0), 'peak': near(Lc - 1.0)}
        for k_, s in enumerate(np.arange(8.0, Lc - 4, 8.0)):
            anchors['jackstay-%02d' % (k_ + 1)] = near(float(s), True)
        lat[ld['mast']] = {'cells': cells, 'size': [W_, 7, H_], 'anchors': anchors, 'len_cells': Lc, 'angle': ld['angle_deg'], 'sail': ld['sail'], 'hoist': hs}
    # ── 帆桁擺放（外部模型）──
    place = []
    for yd in RB['yards']:
        if yd['mast'] == 'bowsprit':
            t = yd['at_t'] * B['len']
            px, pz = B['x0'] + 0.5 + t * u[0], B['z0'] + 0.5 + t * u[2] - yd['drop']
            tgt_len = plan['masts']['rows'][-1]['yards']['spritsail'] / CELL
        else:
            m = M[yd['mast']]
            z = m['yards'][yd['yard']]['z']
            key = yd['mast']
            r_here = RB['mast_r'][key][1] if z <= m['lower_top'] else RB['topmast_r'][key][1]
            px = float(LY.mast_axis_x(plan, key, z, L)) + r_here + 3.5
            pz = z
            tgt_len = m['yards'][yd['yard']]['len']
        sy = round(tgt_len / yd['src_len'], 4)
        sa = json.load(open(os.path.join(WORKS, yd['src_work'], 'anchors.json'), encoding='utf-8'))['anchors']
        pv = next(a_['at'] for a_ in sa if a_['name'] == 'pivot')
        place.append({'name': yd['name'], 'mast': yd['mast'], 'work': yd['src_work'], 'at': [round(px, 2), YC + 0.5, round(pz, 2)],
                      'pivot': [pv[0] + 0.5, pv[1] + 0.5, pv[2] + 0.5], 'rotate': [0, 0, yd['brace']], 'scale': [1, sy, 1],
                      'meta': {'kind': 'yard', 'mast': yd['mast'], 'yard': yd['yard'], 'sail': yd['sail'], 'length_m': round(tgt_len * CELL, 2),
                               'pivot_anchor': 'pivot', 'turn_axis': 'z', 'rotate_z_deg': yd['brace']}})
    for key, l_ in lat.items():
        m = M[key]
        zh = m['heel'] + 0.85 * (m['lower_top'] - m['heel'])
        r_here = RB['mast_r'][key][1]
        xa = float(LY.mast_axis_x(plan, key, zh, L))
        pv = l_['anchors']['pivot']
        place.append({'name': 'yard-%s-lateen' % key, 'mast': key, 'work': 'abigail-fluyt-01m-yard-%s-lateen' % key,
                      'at': [round(xa, 2), round(YC + 0.5 - (r_here + 2.5), 2), round(zh, 2)], 'pivot': [pv[0] + 0.5, pv[1] + 0.5, pv[2] + 0.5],
                      'rotate': [0, 0, 0], 'scale': [1, 1, 1],
                      'meta': {'kind': 'yard', 'mast': key, 'yard': 'gaff', 'sail': l_['sail'], 'length_m': round(l_['len_cells'] * CELL, 2), 'rig': 'lateen',
                               'pivot_anchor': 'pivot', 'turn_axis': 'z', 'rotate_z_deg': 0}})
    if probe:
        nm, dz = probe[0].split('=')[1].split(':')
        for p_ in place:
            if p_['name'] == nm:
                p_['at'][2] += float(dz)

    # ── 讀數 ──
    R = {'parts': {}, 'skipped_on_ship': skipped, 'bowsprit_hole_cells': len(hole)}
    for nm, cells in parts.items():
        ks = set(cells)
        R['parts'][nm] = {'cells': len(ks), 'mirror_diff': sum(1 for (x, y, z), c in cells.items() if cells.get((x, 2 * YC - y, z)) != c)}
    # 每根桅在每層甲板那一格：桅的截面要整個落在孔裡（＝ 桅格沒有被甲板佔掉 ⇒ skipped 0 就是）；cofa 有沒有撞到別的東西也在 skipped
    # 帆桁：每根的兩端（世界座標，轉了 brace 之後）、離最近的「別根桅」軸多遠、lateen 後端伸出船尾多少
    ends = {}
    for p_ in place:
        if p_['name'].endswith('lateen'):
            l_ = lat[p_['mast']]
            pv = np.array(p_['pivot'])
            def wpt(a_):
                v = np.array([a_[0] + 0.5, a_[1] + 0.5, a_[2] + 0.5]) - pv
                return (np.array(p_['at']) + v).round(1).tolist()
            ends[p_['name']] = {'fore': wpt(l_['anchors']['fore']), 'peak': wpt(l_['anchors']['peak']), 'pivot': p_['at']}
        else:
            half = p_['meta']['length_m'] / CELL / 2
            th = math.radians(p_['rotate'][2])
            c, s = p_['at'], (math.sin(th), math.cos(th))
            ends[p_['name']] = {'P': [round(c[0] + half * s[0], 1), round(c[1] - half * s[1], 1), c[2]], 'S': [round(c[0] - half * s[0], 1), round(c[1] + half * s[1], 1), c[2]], 'pivot': c}
    R['yard_ends'] = ends
    # 帆桁穿過船上的格嗎：沿線每 0.5 格取樣、半徑約 1 內有實心就算（離自己的吊點 7 格內不算 ⇒ 那是貼著桅的地方）
    solid = set(occ) | {k for cells in parts.values() for k in cells}
    clash = {}
    for nm, e in ends.items():
        a_, b_ = (e['fore'], e['peak']) if 'peak' in e else (e['P'], e['S'])
        a_, b_, pv_ = np.array(a_, float), np.array(b_, float), np.array(e['pivot'], float)
        n = int(np.linalg.norm(b_ - a_) / 0.5) + 1
        hits = set()
        for t in np.linspace(0, 1, n):
            q = a_ + (b_ - a_) * t
            if np.linalg.norm(q - pv_) < 7:
                continue
            for dx in (-1, 0, 1):
                for dy in (-1, 0, 1):
                    for dz in (-1, 0, 1):
                        k = (int(math.floor(q[0] + dx * 0.8)), int(math.floor(q[1] + dy * 0.8)), int(math.floor(q[2] + dz * 0.8)))
                        if k in solid:
                            hits.add(k)
        clash[nm] = len(hits)
    R['yard_clash_cells'] = clash
    stern_x = float(L.x_aft(47))
    R['lateen_overhang_m'] = {k: round((stern_x - v['peak'][0]) * CELL, 2) for k, v in ends.items() if 'peak' in v}
    R['yards'] = place
    R['lateen'] = {k: {'size': v['size'], 'cells': len(v['cells']), 'anchors': v['anchors']} for k, v in lat.items()}
    R['masts'] = {k: {'heel': round(m['heel'], 1), 'platform': round(m['platform'], 1), 'truck': round(m['truck'], 1), 'x': m['x']} for k, m in M.items()}
    if probe:
        print(json.dumps({'probe': probe[0], 'yard_clash_cells': clash}, ensure_ascii=False))
        return
    # ── 寫檔 ──
    def dump(path, cells, head):
        with open(path, 'w', encoding='utf-8', newline='\n') as f:
            f.write(head)
            for k in sorted(cells):
                f.write('%d,%d,%d,%d\n' % (k[0], k[1], k[2], cells[k]))
        return [len(cells), hashlib.sha256(open(path, 'rb').read()).hexdigest()]
    for sub in ('masts', 'yards', 'bowsprit_hole'):
        os.makedirs(os.path.join(design, 'masks', sub), exist_ok=True)
    R['lists'] = {}
    for nm, cells in parts.items():
        R['lists'][nm] = dump(os.path.join(design, 'masks', 'masts', nm + '.vox.txt'), cells, '# 澤漢號 %s（draft_masts.py；世界座標，at 0,0,0）\n' % nm)
    for key, l_ in lat.items():
        R['lists']['lateen-' + key] = dump(os.path.join(design, 'masks', 'yards', 'lateen-%s.vox.txt' % key), l_['cells'], '# 澤漢號 %s lateen 帆桁（局部座標）\n' % key)
    R['lists']['bowsprit_hole'] = dump(os.path.join(design, 'masks', 'bowsprit_hole', 'carve.vox.txt'), hole, '# 澤漢號 船頭牆給艏斜桅開孔（carvevox；第 4 欄 ＝ 刻之前的顏色）\n')
    with open(os.path.join(design, 'yards_placement.json'), 'w', encoding='utf-8', newline='\n') as f:
        json.dump(place, f, ensure_ascii=False, indent=1)
    with open(os.path.join(design, 'yards_lateen.json'), 'w', encoding='utf-8', newline='\n') as f:
        json.dump({k: {'size': v['size'], 'anchors': v['anchors'], 'len_m': round(v['len_cells'] * CELL, 2), 'angle_deg': v['angle'], 'sail': v['sail']} for k, v in lat.items()}, f, ensure_ascii=False, indent=1)
    # 圖：側面（船＋桅＋帆桁的線）
    sc = 2.5
    im = Image.new('RGB', (int(470 * sc) + 80, int(360 * sc) + 120), (250, 248, 240))
    d = ImageDraw.Draw(im)
    d.text((20, 10), '澤漢號 新圖紙 06：桅、桅樓、艏斜桅、帆桁（側面，從右舷看）　v1', fill=(0, 0, 0), font=font(18))
    X = lambda x: 40 + (x - 20) * sc
    Z = lambda z: 50 + (360 - z) * sc
    best = {}
    for (x, y, z), c in list(occ.items()) + [(k, c) for cells in parts.values() for k, c in cells.items()]:
        if y >= YC and y > best.get((x, z), (-1, 0))[0]:
            best[(x, z)] = (y, c)
    for (x, z), (y, c) in best.items():
        d.rectangle([X(x), Z(z + 1), X(x + 1), Z(z)], fill=palette_rgb(int(c)))
    for nm, e in ends.items():
        if 'peak' in e:
            d.line([X(e['fore'][0]), Z(e['fore'][2]), X(e['peak'][0]), Z(e['peak'][2])], fill=(120, 60, 20), width=3)
        else:
            d.line([X(e['P'][0]), Z(e['P'][2]), X(e['S'][0]), Z(e['S'][2])], fill=(120, 60, 20), width=3)
            d.ellipse([X(e['pivot'][0]) - 3, Z(e['pivot'][2]) - 3, X(e['pivot'][0]) + 3, Z(e['pivot'][2]) + 3], fill=(200, 0, 0))
    im.save(os.path.join(design, 'sheet06_masts_v1.png'))
    with open(os.path.join(design, 'verify_masts.json'), 'w', encoding='utf-8', newline='\n') as f:
        json.dump(R, f, ensure_ascii=False, indent=1)
    print(json.dumps({k: v for k, v in R.items() if k not in ('yards', 'lateen', 'lists')}, ensure_ascii=False))


if __name__ == '__main__':
    main()
