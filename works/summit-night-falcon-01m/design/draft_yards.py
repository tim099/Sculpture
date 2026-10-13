# 新圖紙 08 帆桁（TASK-0529 階段八）：plan.json 的 yards ⇒ 每根帆桁一件子作品的清單、固定點、模型擺放、verify_yards.json。
# 用法：python -I -X utf8 -B draft_yards.py <design 資料夾>
#   · 現況照 nf_state.state_after('stage7') 重建（桅的格從桅杆子作品量）。
#   · 方帆桁（沿 y、水平、跟中線垂直）：長 ＝ 型寬 × course_over_beam × over_course（取奇數 ⇒ 中心那一格兩邊一樣長）；
#     半徑 ＝ 掛它那一節桅的跟部半徑 × d_over_mast，往兩端照 taper 收、不小於 r_min；軸在格心上 ⇒ 核心那一排一定在。
#     高度 ＝ z_ref（top 平台／中桅 crosstrees／truck）＋ z_off；貼在那一節桅最前緣的前面（中線那一排背面那格 ＝ 桅最前格 ＋ 1）。
#     pivot ＝ 帆桁中心那一格。
#   · gaff／boom：子作品裡做成「水平的直桿」（從主桅後緣往船尾），斜度交給模型 rotate 的 y 分量；pivot ＝ 主桅在 jaws 高度的軸心那一格（繞桅轉）。
#     boom 的 jaws 高度：上翹 angle 之後，boom 下緣離它底下最高那一格 ≥ clear_below 的最低整數。
#   · 模型：放在桅杆子作品裡（跟著桅走）；at ＝ pivot 那一格的格心（世界座標 ＝ 桅杆子作品座標），pivot ＝ 同一點的子作品座標。
#   · 固定點（子作品座標）：方帆桁 arm-P／S、earing-P／S、sling、jackstay-P／S<n>、pivot；gaff throat／peak／top<n>、boom jaws／end／top<n>、pivot。
#     轉過之後的預期位置（世界座標）寫在 verify 的 anchors_expect —— 套用後拿引擎匯出的點來對（引擎的旋轉 vs 我這裡的旋轉）。
#   · 重跑逐位元組相同。
import sys, os, json, hashlib, math
import numpy as np
from scipy import ndimage

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from draft_lines import YC
from nf_state import state_after, occupancy

LINK = {'fore': '前桅', 'main': '主桅'}


def odd(v):
    n = int(round(v))
    return n if n % 2 else (n + 1 if v > n else n - 1)


def rot(p, c, ry, rz):
    """繞 c：先繞 y（ry 度）、再繞 z（rz 度）—— 引擎 rotate 的順序是 X、Y、Z（都繞作品的軸）。"""
    x, y, z = p[0] - c[0], p[1] - c[1], p[2] - c[2]
    b = math.radians(ry); x, z = x * math.cos(b) + z * math.sin(b), -x * math.sin(b) + z * math.cos(b)
    g = math.radians(rz); x, y = x * math.cos(g) - y * math.sin(g), x * math.sin(g) + y * math.cos(g)
    return [c[0] + x, c[1] + y, c[2] + z]


class Yards:
    def __init__(s, d):
        s.d = d
        s.plan = json.load(open(os.path.join(d, 'plan.json'), encoding='utf-8'))
        s.P = s.plan['yards']; s.M = s.plan['masts']
        s.W = state_after(d, 'stage7'); s.occ = occupancy(s.W)
        s.members = {}

    def radius(s, r0, sf):
        T = s.P['taper']
        return max(r0 * float(np.interp(sf, T['s'], T['k'])), s.P['r_min'])

    def zref(s, m, ref):
        S = s.M[m]
        return {'top': S['top_z'], 'crosstrees': S['topmast_head_z'] - S['tm_doubling'], 'truck': S['truck_z']}[ref]

    # ── 方帆桁 ──
    def square(s, Y):
        m = Y['mast']; A = s.W['mast_' + m]; S = s.M[m]; col = s.P['colors']
        Lc = odd(s.P['beam'] * s.P['course_over_beam'])
        L = odd(Lc * Y['over_course']); h = (L - 1) // 2
        r0 = S[Y['mast_r']][0] * Y['d_over_mast']
        zi = s.zref(m, Y['z_ref']) + Y['z_off']
        k = int(math.floor(math.sqrt(r0 * r0 + 0.15)))
        rows = [z for z in range(zi - k, zi + k + 1)]
        front = max(int(np.nonzero(A[:, YC, z])[0].max()) for z in rows)          # 那幾層桅在中線的最前格
        xi = front + 1 + k
        arm = L * Y['arm_over_L']
        cells = {}
        for dy in range(-h, h + 1):
            r = s.radius(r0, abs(dy) / h)
            tip = abs(dy) == h
            for dx in range(-k - 1, k + 2):
                for dz in range(-k - 1, k + 2):
                    if dx * dx + dz * dz <= r * r + 0.15:
                        cells[(xi + dx, YC + dy, zi + dz)] = col['tip'] if tip else col['spar']
        top = lambda dy: (xi, YC + dy, max(z for (x, y, z) in cells if x == xi and y == YC + dy))
        ea = int(round(h - arm))
        pts = [('arm-P', (xi, YC - h, zi), 'yardarm'), ('arm-S', (xi, YC + h, zi), 'yardarm'),
               ('earing-P', top(-ea), 'earing'), ('earing-S', top(ea), 'earing'), ('sling', top(0), 'sling')]
        sp = s.P['jackstay_spacing']
        for dy in range(sp, ea, sp):
            pts += [('jackstay-P%d' % dy, top(-dy), 'jackstay'), ('jackstay-S%d' % dy, top(dy), 'jackstay')]
        pts.append(('pivot', (xi, YC, zi), 'pivot'))
        s.members[Y['name']] = {'mast': m, 'kind': 'square', 'tier': Y['name'].split('-', 1)[1], 'label': Y['label'], 'cells': cells,
                                'pivot': (xi, YC, zi), 'ry': 0.0, 'rz': float(s.P['rotate_z_deg']), 'anchors': pts,
                                'length': L, 'r0': round(r0, 4), 'arm': round(arm, 2), 'z': zi, 'mast_front_x': front, 'k': k}

    # ── gaff／boom：水平直桿，斜度給模型 ──
    def rod(s, name, m, zj, ang, L, r0, r1, ends):
        A = s.W['mast_' + m]; col = s.P['colors']
        xs = np.nonzero(A[:, YC, zj])[0]
        aft = int(xs.min()); px = int(math.floor((xs.min() + xs.max()) / 2))     # 軸心那一格（basecamp 同：(min+max)/2 取 floor）
        Pc = (px + 0.5, YC + 0.5, zj + 0.5)
        a = Pc[0] - aft                                                          # 軸心到後緣（格心 → 後緣格的後面那個面）
        cells = {}
        kk = int(math.ceil(max(r0, r1))) + 1
        for x in range(int(math.floor(Pc[0] - a - L)) - 1, aft + 1):
            u = Pc[0] - (x + 0.5)
            if not (a - 0.5 <= u <= a + L): continue
            t = (u - a) / L
            r = max(r0 + (r1 - r0) * t, s.P['r_min'])
            for dy in range(-kk, kk + 1):
                for dz in range(-kk, kk + 1):
                    if dy * dy + dz * dz <= r * r + 0.15:
                        cells[(x, YC + dy, zj + dz)] = col['tip'] if u > a + L - 1 else col['spar']
        xa = max(x for (x, y, z) in cells); xb = min(x for (x, y, z) in cells)
        topz = lambda x: max(z for (xx, y, z) in cells if xx == x and y == YC)
        pts = [(ends[0], (xa, YC, topz(xa) if ends[0] == 'throat' else zj), ends[0]), (ends[1], (xb, YC, zj), ends[1])]
        sp = s.P['jackstay_spacing']
        for du in range(sp, L - 1, sp):
            x = int(math.floor(Pc[0] - a - du))
            pts.append(('top%d' % du, (x, YC, topz(x)), 'top'))
        pts.append(('pivot', (px, YC, zj), 'pivot'))
        s.members[name] = {'mast': m, 'kind': name.split('-')[1], 'tier': name.split('-', 1)[1], 'label': 'main ' + name.split('-')[1], 'cells': cells,
                           'pivot': (px, YC, zj), 'ry': float(ang), 'rz': float(s.P['rotate_z_deg']), 'anchors': pts,
                           'length': L, 'r0': round(r0, 4), 'r1': round(r1, 4), 'jaws_z': zj, 'mast_aft_x': aft, 'axis_to_aft': round(a, 3)}

    def build(s):
        for Y in s.P['square']:
            s.square(Y)
        Bm, G = s.P['boom'], s.P['gaff']
        m = Bm['mast']; S = s.M[m]; A = s.W['mast_' + m]
        others = s.occ & ~(A > 0)
        # boom：尾端 ＝ 現況最後面那一格往後 overhang；長 ＝ 從主桅後緣到那裡（沿斜度）；jaws 高度往上找到下緣都離底下 ≥ clear_below
        xs_all = np.nonzero(s.occ.any((1, 2)))[0]; x_stern = int(xs_all.min())
        rb = S['r_lower'][0] * Bm['d_over_mast']; tb = math.radians(Bm['angle_deg'])
        for zj in range(30, 120):
            xs = np.nonzero(A[:, YC, zj])[0]; aft = int(xs.min()); px = int(math.floor((xs.min() + xs.max()) / 2))
            a = px + 0.5 - aft
            # 水平距離：pivot → 尾端 ＝ (a + L) cos(tb) ⇒ L ＝ (px + 0.5 − x_end) / cos(tb) − a
            Lb = (px + 0.5 - (x_stern - Bm['overhang'])) / math.cos(tb) - a
            ok = True
            for x in range(x_stern - Bm['overhang'], aft):
                u = (px + 0.5 - (x + 0.5)) / math.cos(tb)
                if u < a: continue
                zc = zj + 0.5 + u * math.sin(tb)
                r = max(rb + (rb * Bm['taper_end'] - rb) * min(max((u - a) / Lb, 0), 1), s.P['r_min'])
                below = np.nonzero(others[x, YC - 3:YC + 4, :int(zc)].any(0))[0]
                if len(below) and (zc - r) - (below.max() + 1) < Bm['clear_below']:
                    ok = False; break
            if ok: break
        Lb_i = int(round(Lb))
        s.boom_probe = {'x_stern': x_stern, 'x_end': x_stern - Bm['overhang'], 'jaws_z': zj, 'length_exact': round(Lb, 3)}
        s.rod('main-boom', m, zj, Bm['angle_deg'], Lb_i, rb, rb * Bm['taper_end'], ('jaws', 'end'))
        zg = S['top_z'] - G['jaws_below_top']
        rg = S['r_lower'][0] * G['d_over_mast']
        Lg = int(round(Lb_i * G['over_boom']))
        s.rod('main-gaff', m, zg, G['angle_deg'], Lg, rg, rg * G['taper_end'], ('throat', 'peak'))

    def place(s):
        s.place = []; s.expect = {}
        for nm, M in s.members.items():
            ks = np.array(sorted(M['cells']) + [M['pivot']])
            lo, hi = ks.min(0) - 1, ks.max(0) + 1
            M['origin'] = [int(c) for c in lo]; M['size'] = [int(c) for c in hi - lo + 1]
            pv = M['pivot']
            at = [pv[i] + 0.5 for i in range(3)]
            pivot = [pv[i] - M['origin'][i] + 0.5 for i in range(3)]
            meta = {'kind': 'yard', 'mast': M['mast'], 'yard': M['tier'], 'length_m': round(M['length'] * 0.1, 2),
                    'diameter_m': round(2 * M['r0'] * 0.1, 3), 'pivot_anchor': 'pivot', 'turn_axis': 'z', 'rotate_z_deg': M['rz']}
            if M['ry']:
                meta['rotate_y_deg'] = M['ry']
            s.place.append({'member': nm, 'work': s.P['prefix'] + nm, 'host': s.plan['work'] + '-mast-' + M['mast'], 'link': LINK[M['mast']],
                            'model': 'yard-' + nm, 'title': '夜隼號 帆桁 %s（%.1f m）' % (M['label'], M['length'] * 0.1),
                            'origin': M['origin'], 'size': M['size'], 'cells': len(M['cells']), 'at': at, 'pivot': pivot,
                            'rotate': [0, M['ry'], M['rz']], 'meta': meta})
            s.expect[nm] = {a: [round(c, 4) for c in rot([p[i] + 0.5 for i in range(3)], at, M['ry'], M['rz'])] for a, p, kd in M['anchors']}

    def measure(s):
        """模型轉好之後的樣子（格心照 rot 轉、取最近的格）跟現況的關係：撞到哪一件幾格；每根帆桁自己 6 連通幾塊。"""
        R = {}
        names = {k: v > 0 for k, v in s.W.items()}
        for nm, M in s.members.items():
            at = [M['pivot'][i] + 0.5 for i in range(3)]
            hit = {}
            for c in M['cells']:
                q = rot([c[i] + 0.5 for i in range(3)], at, M['ry'], M['rz'])
                g = tuple(int(math.floor(v)) for v in q)
                for k, v in names.items():
                    if v[g]: hit[k] = hit.get(k, 0) + 1
            ks = np.array(sorted(M['cells'])); lo = ks.min(0)
            b = np.zeros(tuple(ks.max(0) - lo + 1), bool); b[tuple((ks - lo).T)] = True
            R[nm] = {'cells': len(M['cells']), 'components_6': int(ndimage.label(b)[1]), 'rotated_hits': hit}
        return R

    def write(s, v):
        out = os.path.join(s.d, 'masks', 'yards'); os.makedirs(out, exist_ok=True)
        for f in os.listdir(out): os.remove(os.path.join(out, f))
        files = {}
        for P in s.place:
            M = s.members[P['member']]; o = M['origin']
            rows = sorted((k[0] - o[0], k[1] - o[1], k[2] - o[2], c) for k, c in M['cells'].items())
            text = ''.join('%d,%d,%d,%d\n' % r for r in rows)
            fn = P['member'] + '.vox.txt'
            open(os.path.join(out, fn), 'w', encoding='utf-8', newline='\n').write(text)
            P['file'] = 'masks/yards/' + fn
            P['sha256'] = hashlib.sha256(text.encode('utf-8')).hexdigest()
            P['anchors'] = [{'name': a, 'at': [p[i] - o[i] for i in range(3)], 'world': list(p), 'kind': kd} for a, p, kd in M['anchors']]
        v['placements'] = s.place
        v['anchors_expect'] = s.expect
        with open(os.path.join(s.d, 'verify_yards.json'), 'w', encoding='utf-8', newline='\n') as fo:
            json.dump(v, fo, ensure_ascii=False, indent=2, sort_keys=True); fo.write('\n')


def main():
    d = sys.argv[1]
    Y = Yards(d); Y.build(); Y.place()
    mem = {nm: {k: M[k] for k in M if k not in ('cells', 'anchors')} for nm, M in Y.members.items()}
    for v in mem.values(): v['pivot'] = list(v['pivot'])
    v = {'members': mem, 'boom_probe': Y.boom_probe, 'measure': Y.measure(),
         'counts': {'subworks': len(Y.members), 'cells': sum(len(M['cells']) for M in Y.members.values()),
                    'anchors': sum(len(M['anchors']) for M in Y.members.values())}}
    Y.write(v)
    print(json.dumps({k: v[k] for k in ('members', 'boom_probe', 'measure', 'counts')}, ensure_ascii=False, indent=1))


if __name__ == '__main__':
    main()
