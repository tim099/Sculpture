# 新圖紙 07 帆桁（TASK-0547 階段七）：plan.json 的 yards ⇒ 每根帆桁一件子作品的清單、固定點、模型擺放、verify_yards.json。
# 用法：python -I -X utf8 -B draft_yards.py <design 資料夾>
#   · 從夜隼號 draft_yards.py（TASK-0529 階段八）改：長度改讀 Witsen 的 voet；多了 lateen（斜掛在後桅左舷）與斜桅下的兩根。
#   · 現況：船 ＝ sk_state 重播到 stage6a（z < 200）；桅、斜桅、channels ＝ masks/masts/ 的清單（＋channels 鏡像）——
#     check_masts.py 量過這個聯集 ＝ 組裝件匯出（差 0）。桅的高度（平台、crosstrees、桅頂）照 verify_masts.json 的 info。
#   · 方帆桁（沿 y、水平）：長 ＝ voet × voet_to_grid 取奇數；半徑 ＝ 掛它那一節桅徑 / 2 × d_over_mast，往兩端照 taper 收、不小於 r_min；
#     貼在那一節桅最前緣的前面（中線那一排背面那格 ＝ 那幾層桅最前格 ＋ 1）；pivot ＝ 帆桁中心那一格。
#   · spritsail：掛在斜桅底下、從腳往外 s_frac 處；帆桁頂面那一層比那幾欄斜桅最低的格低 gap 格。sprit topsail：貼在斜桅頂桅的前面。
#   · lateen：子作品裡是水平的直桿（沿 x、在後桅左舷 side_dy），斜度交給模型 rotate 的 y（＋＝ 前端往下）；pivot ＝ 帆桁中點那一格（吊點）。
#     吊點高度：轉好之後每一格底下離最近的實心 ≥ head_clear、而且不撞任何格的最低整數（從 z_min 往上找）。
#   · 模型：放在桅杆子作品裡（後桅、主桅、前桅、船首斜桅），at ＝ pivot 那一格的格心（世界 ＝ 桅杆子作品座標），pivot ＝ 同一點的子作品座標。
#   · 固定點（子作品座標）：方帆桁 arm-P／S、earing-P／S、sling、jackstay-P／S<n>、pivot；lateen arm-F／A、earing-F／A、sling、top<n>、pivot。
#     轉過之後的預期位置（世界座標）寫在 anchors_expect —— 套用後拿引擎匯出的點來對。
#   · 重跑逐位元組相同。
import sys, os, json, hashlib, math
import numpy as np
from scipy import ndimage

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from sk_state import state_after, occupancy

LINK = {'mizzen': '後桅', 'main': '主桅', 'fore': '前桅', 'bowsprit': '船首斜桅'}
HOST = {'mizzen': '-mast-mizzen', 'main': '-mast-main', 'fore': '-mast-fore', 'bowsprit': '-bowsprit'}
NZ = 576


def odd(v):
    n = int(round(v))
    return n if n % 2 else (n + 1 if v > n else n - 1)


def rot(p, c, ry, rz):
    """繞 c：先繞 y（ry 度）、再繞 z（rz 度）—— 引擎 rotate 的順序是 X、Y、Z（都繞作品的軸）。"""
    x, y, z = p[0] - c[0], p[1] - c[1], p[2] - c[2]
    b = math.radians(ry); x, z = x * math.cos(b) + z * math.sin(b), -x * math.sin(b) + z * math.cos(b)
    g = math.radians(rz); x, y = x * math.cos(g) - y * math.sin(g), x * math.sin(g) + y * math.cos(g)
    return [c[0] + x, c[1] + y, c[2] + z]


def load(p):
    return np.loadtxt(p, delimiter=',', dtype=int, comments='#', ndmin=2)


class Yards:
    def __init__(s, d):
        s.d = d
        s.plan = json.load(open(os.path.join(d, 'plan.json'), encoding='utf-8'))
        s.P = s.plan['yards']; s.M = {m['name']: m for m in s.plan['masts']['list']}; s.B = s.plan['masts']['bowsprit']
        F = s.plan['frame']; s.NX, s.NY, s.YC = F['NX'], F['NY'], F['YC']
        VM = json.load(open(os.path.join(d, 'verify_masts.json'), encoding='utf-8'))
        s.info = VM['info']
        s.occ = np.zeros((s.NX, s.NY, NZ), bool)
        s.occ[:, :, :200] = occupancy(state_after(d, 'stage6a', nz=200))
        s.part = {}
        for k in ('mizzen', 'main', 'fore', 'bowsprit', 'channels'):
            a = load(os.path.join(d, VM['stamp_order'][k][0]['file']))[:, :3]
            s.part[k] = a; s.occ[tuple(a.T)] = True
        chp = s.part['channels'].copy(); chp[:, 1] = s.NY - 1 - chp[:, 1]; s.occ[tuple(chp.T)] = True
        s.members = {}

    def radius(s, r0, sf):
        T = s.P['taper']
        return max(r0 * float(np.interp(sf, T['s'], T['k'])), s.P['r_min'])

    def zref(s, m, ref):
        I, M = s.info[m], s.M[m]
        if ref == 'platform': return I['hounds_z'] - 1
        if ref == 'crosstrees': return I['topmast_top_z'] - M['head_top'] - 1
        if ref == 'truck': return (I['tg_top_z'] or I['topmast_top_z']) - 1
        raise ValueError(ref)

    def length(s, voet):
        return odd(voet * s.P['voet_to_grid'])

    def front_x(s, pts, zs):
        """那幾層、中線那一排最前面那一格的 x。"""
        sel = pts[(pts[:, 1] == s.YC) & np.isin(pts[:, 2], zs)]
        return int(sel[:, 0].max())

    def square_cells(s, xi, zi, L, r0, arm, col):
        YC = s.YC; h = (L - 1) // 2
        k = int(math.floor(math.sqrt(r0 * r0 + 0.15)))
        cells = {}
        for dy in range(-h, h + 1):
            r = s.radius(r0, abs(dy) / h)
            for dx in range(-k - 1, k + 2):
                for dz in range(-k - 1, k + 2):
                    if dx * dx + dz * dz <= r * r + 0.15:
                        cells[(xi + dx, YC + dy, zi + dz)] = col['tip'] if abs(dy) == h else col['spar']
        top = lambda dy: (xi, YC + dy, max(z for (x, y, z) in cells if x == xi and y == YC + dy))
        ea = int(round(h - arm))
        pts = [('arm-P', (xi, YC - h, zi), 'yardarm'), ('arm-S', (xi, YC + h, zi), 'yardarm'),
               ('earing-P', top(-ea), 'earing'), ('earing-S', top(ea), 'earing'), ('sling', top(0), 'sling')]
        sp = s.P['jackstay_spacing']
        for dy in range(sp, ea, sp):
            pts += [('jackstay-P%d' % dy, top(-dy), 'jackstay'), ('jackstay-S%d' % dy, top(dy), 'jackstay')]
        pts.append(('pivot', (xi, YC, zi), 'pivot'))
        return cells, pts, k

    def add(s, name, host, tier, label, cells, pts, pivot, ry, extra):
        s.members[name] = dict({'mast': host, 'tier': tier, 'label': label, 'cells': cells, 'anchors': pts, 'pivot': pivot,
                                'ry': float(ry), 'rz': float(s.P['rotate_z_deg'])}, **extra)

    # ── 方帆桁（桅上）──
    def square(s, Y):
        m = Y['mast']; M = s.M[m]; col = s.P['colors']
        L = s.length(Y['voet']); r0 = M[Y['mast_d']] / 2 * Y['d_over_mast']
        zi = s.zref(m, Y['z_ref']) + Y['z_off']
        k = int(math.floor(math.sqrt(r0 * r0 + 0.15)))
        front = s.front_x(s.part[m], list(range(zi - k, zi + k + 1)))
        xi = front + 1 + k
        cells, pts, _ = s.square_cells(xi, zi, L, r0, L * Y['arm_over_L'], col)
        s.add(Y['name'], m, Y['name'].split('-', 1)[1], Y['label'], cells, pts, (xi, s.YC, zi), 0.0,
              {'length': L, 'r0': round(r0, 4), 'z': zi, 'mast_front_x': front, 'k': k, 'z_ref': Y['z_ref']})

    # ── 斜桅下兩根 ──
    def sprit(s):
        B = s.B; col = s.P['colors']; bp = s.part['bowsprit']
        Ys = {y['name']: y for y in s.P['sprit']}
        # spritsail：斜桅外段底下
        Y = Ys['spritsail']; L = s.length(Y['voet']); r0 = B['d'] / 2 * Y['d_over_spar']
        th = math.radians(B['steeve']); sx = Y['s_frac'] * B['L']
        xi = int(math.floor(B['heel'][0] + math.cos(th) * sx))
        k = int(math.floor(math.sqrt(r0 * r0 + 0.15)))
        # 🩸 第一版窗開到 xi ± (k＋1)，比帆桁自己佔的欄（xi ± k）寬一欄 ⇒ 抓到更低的那一欄、實際空隙 2（check_yards 量到；plan 1）
        cols = bp[(bp[:, 1] == s.YC) & (bp[:, 0] >= xi - k) & (bp[:, 0] <= xi + k)]
        zi = int(cols[:, 2].min()) - Y['gap'] - 1 - k          # 帆桁頂面那一層（zi＋k）＝ 斜桅最低格 − gap − 1
        cells, pts, _ = s.square_cells(xi, zi, L, r0, L * Y['arm_over_L'], col)
        s.add('spritsail', 'bowsprit', 'spritsail', Y['label'], cells, pts, (xi, s.YC, zi), 0.0,
              {'length': L, 'r0': round(r0, 4), 'z': zi, 'bowsprit_low_z': int(cols[:, 2].min()), 'k': k})
        # sprit topsail：斜桅頂桅頂下 z_off、貼在它前面
        Y = Ys['sprit-topsail']; L = s.length(Y['voet']); r0 = B['d_sprit_top'] / 2 * Y['d_over_spar']
        zi = s.info['bowsprit']['sprit_top_z'] - 1 + Y['z_off']
        k = int(math.floor(math.sqrt(r0 * r0 + 0.15)))
        front = s.front_x(bp, list(range(zi - k, zi + k + 1)))
        xi = front + 1 + k
        cells, pts, _ = s.square_cells(xi, zi, L, r0, L * Y['arm_over_L'], col)
        s.add('sprit-topsail', 'bowsprit', 'sprit-topsail', Y['label'], cells, pts, (xi, s.YC, zi), 0.0,
              {'length': L, 'r0': round(r0, 4), 'z': zi, 'mast_front_x': front, 'k': k})

    # ── lateen：水平直桿沿 x，斜度給模型 ──
    def lateen_cells(s, Y, zs):
        M = s.M[Y['mast']]; col = s.P['colors']
        L = s.length(Y['voet']); h = (L - 1) // 2; r0 = M['d_low'] / 2 * Y['d_over_mast']
        xc = int(math.floor(M['x'])); yc = s.YC + Y['side_dy']
        k = int(math.ceil(r0)) + 1
        cells = {}
        for dx in range(-h, h + 1):
            r = s.radius(r0, abs(dx) / h)
            for dy in range(-k, k + 1):
                for dz in range(-k, k + 1):
                    if dy * dy + dz * dz <= r * r + 0.15:
                        cells[(xc + dx, yc + dy, zs + dz)] = col['tip'] if abs(dx) == h else col['spar']
        return cells, L, h, r0, xc, yc

    def lateen(s):
        Y = s.P['lateen']; ry = Y['angle_deg']
        top_lim = s.info[Y['mast']]['hounds_z'] - 1
        tried = []
        for zs in range(Y['z_min'], top_lim):
            cells, L, h, r0, xc, yc = s.lateen_cells(Y, zs)
            at = (xc + 0.5, yc + 0.5, zs + 0.5)
            hit = 0; clear = 10 ** 9
            for c in cells:
                q = rot([c[i] + 0.5 for i in range(3)], at, ry, 0)
                g = tuple(int(math.floor(v)) for v in q)
                if s.occ[g]: hit += 1
                col_ = np.nonzero(s.occ[g[0], g[1], :g[2]])[0]
                if len(col_): clear = min(clear, (q[2] - 0.5) - (col_.max() + 0.5))
            if hit == 0 and clear >= Y['head_clear']:
                break
            tried.append((zs, hit, round(clear, 2)))
        else:
            raise SystemExit('lateen 找不到吊點高度：' + json.dumps(tried[-5:]))
        col = s.P['colors']
        topz = lambda x: max(z for (xx, y, z) in cells if xx == x and y == yc)
        ea = int(round(h * (1 - 0.03)))
        pts = [('arm-F', (xc + h, yc, zs), 'yardarm'), ('arm-A', (xc - h, yc, zs), 'yardarm'),
               ('earing-F', (xc + ea, yc, topz(xc + ea)), 'earing'), ('earing-A', (xc - ea, yc, topz(xc - ea)), 'earing'),
               ('sling', (xc, yc, topz(xc)), 'sling')]
        sp = s.P['jackstay_spacing']
        for du in range(sp, ea, sp):
            pts += [('top-F%d' % du, (xc + du, yc, topz(xc + du)), 'top'), ('top-A%d' % du, (xc - du, yc, topz(xc - du)), 'top')]
        pts.append(('pivot', (xc, yc, zs), 'pivot'))
        s.lateen_probe = {'sling_z': zs, 'rejected_below': len(tried), 'last_rejected': tried[-1] if tried else None, 'min_clear': round(clear, 3)}
        s.add(Y['name'], Y['mast'], 'lateen', Y['label'], cells, pts, (xc, yc, zs), ry,
              {'length': L, 'r0': round(r0, 4), 'z': zs, 'side_dy': Y['side_dy']})

    def build(s):
        for Y in s.P['square']: s.square(Y)
        s.lateen(); s.sprit()

    def place(s):
        s.place_ = []; s.expect = {}
        pre = s.plan['work']
        for nm, M in s.members.items():
            ks = np.array(sorted(M['cells']) + [M['pivot']])
            lo, hi = ks.min(0) - 1, ks.max(0) + 1
            M['origin'] = [int(c) for c in lo]; M['size'] = [int(c) for c in hi - lo + 1]
            pv = M['pivot']
            at = [pv[i] + 0.5 for i in range(3)]
            pivot = [pv[i] - M['origin'][i] + 0.5 for i in range(3)]
            meta = {'kind': 'yard', 'mast': M['mast'], 'yard': M['tier'], 'length_m': round(M['length'] * 0.1, 2),
                    'diameter_m': round(2 * M['r0'] * 0.1, 3), 'pivot_anchor': 'pivot', 'turn_axis': 'z', 'rotate_z_deg': M['rz'],
                    'sail': s.P['sail_of'][nm]}
            if M['ry']: meta['rotate_y_deg'] = M['ry']
            s.place_.append({'member': nm, 'work': s.P['prefix'] + nm, 'host': pre + HOST[M['mast']], 'link': LINK[M['mast']],
                             'model': 'yard-' + nm, 'title': '風暴角號 帆桁 %s（%.1f m）' % (M['label'], M['length'] * 0.1),
                             'origin': M['origin'], 'size': M['size'], 'cells': len(M['cells']), 'at': at, 'pivot': pivot,
                             'rotate': [0, M['ry'], M['rz']], 'meta': meta})
            s.expect[nm] = {a: [round(c, 4) for c in rot([p[i] + 0.5 for i in range(3)], at, M['ry'], M['rz'])] for a, p, kd in M['anchors']}

    def measure(s):
        """轉好之後（格心照 rot 轉、取所在的格）撞到現況幾格；帆桁之間互撞幾格；每根自己 6 連通幾塊。"""
        R = {}; placed = {}
        for nm, M in s.members.items():
            at = [M['pivot'][i] + 0.5 for i in range(3)]
            g = set()
            for c in M['cells']:
                q = rot([c[i] + 0.5 for i in range(3)], at, M['ry'], M['rz'])
                g.add(tuple(int(math.floor(v)) for v in q))
            placed[nm] = g
            ks = np.array(sorted(M['cells'])); lo = ks.min(0)
            b = np.zeros(tuple(ks.max(0) - lo + 1), bool); b[tuple((ks - lo).T)] = True
            R[nm] = {'cells': len(M['cells']), 'components_6': int(ndimage.label(b)[1]),
                     'rotated_hits_ship': int(sum(1 for p in g if s.occ[p])), 'z_min': min(p[2] for p in g), 'z_max': max(p[2] for p in g),
                     'x_min': min(p[0] for p in g), 'x_max': max(p[0] for p in g), 'y_min': min(p[1] for p in g), 'y_max': max(p[1] for p in g)}
        ns = list(placed); pair = {}
        for i, a in enumerate(ns):
            for b in ns[i + 1:]:
                n = len(placed[a] & placed[b])
                if n: pair[a + '×' + b] = n
        inframe = all(0 <= p[0] < s.NX and 0 <= p[1] < s.NY and 0 <= p[2] < NZ for g in placed.values() for p in g)
        return {'each': R, 'yard_pairs': pair, 'all_in_frame': inframe}

    def write(s, v):
        out = os.path.join(s.d, 'masks', 'yards'); os.makedirs(out, exist_ok=True)
        for f in os.listdir(out): os.remove(os.path.join(out, f))
        for P in s.place_:
            M = s.members[P['member']]; o = M['origin']
            rows = sorted((k[0] - o[0], k[1] - o[1], k[2] - o[2], c) for k, c in M['cells'].items())
            text = ''.join('%d,%d,%d,%d\n' % r for r in rows)
            fn = P['member'] + '.vox.txt'
            open(os.path.join(out, fn), 'w', encoding='utf-8', newline='\n').write(text)
            P['file'] = 'masks/yards/' + fn
            P['sha256'] = hashlib.sha256(text.encode('utf-8')).hexdigest()
            P['anchors'] = [{'name': a, 'at': [p[i] - o[i] for i in range(3)], 'world': list(p), 'kind': kd} for a, p, kd in M['anchors']]
        v['placements'] = s.place_
        v['anchors_expect'] = s.expect
        with open(os.path.join(s.d, 'verify_yards.json'), 'w', encoding='utf-8', newline='\n') as fo:
            json.dump(v, fo, ensure_ascii=False, indent=2, sort_keys=True); fo.write('\n')


def main():
    d = sys.argv[1]
    Y = Yards(d); Y.build(); Y.place()
    mem = {nm: {k: M[k] for k in M if k not in ('cells', 'anchors')} for nm, M in Y.members.items()}
    for v in mem.values(): v['pivot'] = list(v['pivot'])
    v = {'members': mem, 'lateen_probe': Y.lateen_probe, 'measure': Y.measure(),
         'counts': {'subworks': len(Y.members), 'cells': sum(len(M['cells']) for M in Y.members.values()),
                    'anchors': sum(len(M['anchors']) for M in Y.members.values())}}
    Y.write(v)
    print(json.dumps({k: v[k] for k in ('members', 'lateen_probe', 'measure', 'counts')}, ensure_ascii=False, indent=1))


if __name__ == '__main__':
    main()
