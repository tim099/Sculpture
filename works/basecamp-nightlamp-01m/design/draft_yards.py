# 新圖紙 15 帆桁 v1（階段十四，TASK-0538）：plan.json yards ＋ 組裝件 export list ＋ 三件桅杆子作品 export list（links=none）
#   ⇒ masks/yards/<帆桁>.vox.txt（子作品自己的座標）、rig_points_yards.json（固定點）、yards_placement.json（子作品、模型）、
#     verify_yards.json、sheet15_yards_v1.png
# 用法：python -I draft_yards.py <design 資料夾> <組裝件 list> <後桅 list> <主桅 list> <前桅 list>
#   · 每根帆桁一件子作品（沒轉、沿 y），在桅杆子作品裡放成外部模型（造船規格 §5）：pivot ＝ 帆桁中心那一格（gaff／boom ＝ 後桅在 jaws 高度的軸心）、
#     rotate ＝ 0,0,−brace（右舷那一頭往前）。
#   · 截面、錐度、端色、固定點的定義照憲法號 draft_yards.py／draft_yard_models.py（arm、earing、sling、jackstay；gaff／boom 的 jaws、end、top<k>）。
#   · 碰撞：轉過之後每一格的格心＋八個角，不准落在組裝件的實心裡（自己那根桅除外 —— 帆桁貼著桅）。
import sys, os, json, hashlib, math
import numpy as np
from PIL import Image, ImageDraw

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import draft_planking as DP      # noqa: E402

YC = 160
FT, IN = 3.048, 0.254           # 一呎、一吋幾格（0.1 m）


def rotz(p, c, deg):
    t = math.radians(deg)
    dx, dy = p[0] - c[0], p[1] - c[1]
    return [c[0] + dx * math.cos(t) - dy * math.sin(t), c[1] + dx * math.sin(t) + dy * math.cos(t), p[2]]


class Yards:
    def __init__(s, design, asm_list, mast_lists):
        s.design = design
        s.plan = json.load(open(os.path.join(design, 'plan.json'), encoding='utf-8'))
        s.Y = s.plan['yards']
        s.occ = DP.read_list(asm_list)
        assert len(s.occ) == s.Y['assembly_cells'], ('組裝件格數對不上', len(s.occ))
        s.sha = {'assembly': hashlib.sha256(open(asm_list, 'rb').read()).hexdigest()}
        s.mast = {}
        for m, p in mast_lists.items():
            s.mast[m] = set(DP.read_list(p))
            assert len(s.mast[m]) == s.Y['mast_cells'][m], ('桅杆格數對不上', m, len(s.mast[m]))
            s.sha[m] = hashlib.sha256(open(p, 'rb').read()).hexdigest()
        s.members = {}
        s.points = []

    def radius(s, r0, sf):
        T = s.Y['taper']
        return r0 * float(np.interp(sf, T['s'], T['k']))

    def xs_at(s, m, z):
        return [x for (x, y, zz) in s.mast[m] if zz == z and abs(y - YC) <= 6]

    def anchor(s, member, name, p, kind):
        s.points.append({'member': member, 'name': name, 'kind': kind, 'side': 'P' if p[1] < YC else ('S' if p[1] > YC else 'CL'),
                         'world': [int(c) for c in p]})

    # ── 橫桁（沿 y、沒轉）──
    def yard(s, Y):
        H = s.Y['heights'][Y['mast']]
        z0 = H[Y['below']] - Y['dz']
        L, r0, arm = Y['len'], Y['r'], Y['arm']
        xf = max(s.xs_at(Y['mast'], z0))
        xc = xf + 0.5 + r0
        half = L / 2
        col = s.Y['colors']
        cells = {}
        for dy in range(-int(math.floor(half)), int(math.floor(half)) + 1):
            sf = min(abs(dy) / half, 1.0)
            r = max(s.radius(r0, sf), 0.5)
            tip = abs(dy) > half - 1
            for x in range(int(math.floor(xc - r)) - 1, int(math.ceil(xc + r)) + 2):
                for z in range(int(math.floor(z0 - r)) - 1, int(math.ceil(z0 + r)) + 2):
                    if (x - xc) ** 2 + (z - z0) ** 2 <= r * r + 0.15 or (abs(x - xc) < 0.51 and z == z0):
                        cells[(x, YC + dy, z)] = col['tip'] if tip else col['spar']
        nm = Y['name']
        top = lambda dy: (int(round(xc)), YC + dy, int(math.floor(z0 + max(s.radius(r0, min(abs(dy) / half, 1)), 0.5) + 0.15)))
        e = int(math.floor(half))
        ea = int(round(half - arm))
        s.anchor(nm, 'arm-P', (int(round(xc)), YC - e, z0), 'yardarm')
        s.anchor(nm, 'arm-S', (int(round(xc)), YC + e, z0), 'yardarm')
        s.anchor(nm, 'earing-P', top(-ea), 'earing')
        s.anchor(nm, 'earing-S', top(ea), 'earing')
        s.anchor(nm, 'sling', top(0), 'sling')
        for dy in range(s.Y['jackstay_spacing'], ea, s.Y['jackstay_spacing']):
            s.anchor(nm, 'jackstay-P%d' % dy, top(-dy), 'jackstay')
            s.anchor(nm, 'jackstay-S%d' % dy, top(dy), 'jackstay')
        pv = (int(round(xc)), YC, z0)
        assert pv in cells, (nm, 'pivot 不在帆桁的格上')
        s.members[nm] = {'mast': Y['mast'], 'tier': Y['tier'], 'label': Y['label'], 'cells': cells, 'pivot': pv,
                         'angle': s.Y['brace_deg'][Y['tier']], 'len': L, 'r': r0, 'sail': Y.get('sail', nm),
                         'log': {'z': z0, 'mast_front_x': xf, 'center_x': round(xc, 2), 'earing_dy': ea, 'arm_dy': e}}

    # ── gaff／boom（x–z 平面裡往船尾斜的桿）──
    def spar_cells(s, p0, d, L, r0, r1):
        col = s.Y['colors']
        d = np.array(d, float) / np.linalg.norm(d)
        p0 = np.array(p0, float)
        lo = np.minimum(p0, p0 + d * L) - r0 - 2
        hi = np.maximum(p0, p0 + d * L) + r0 + 2
        cells = {}
        for x in range(int(lo[0]), int(hi[0]) + 1):
            for y in range(YC - int(r0) - 2, YC + int(r0) + 3):
                for z in range(int(lo[2]), int(hi[2]) + 1):
                    q = np.array([x, y, z], float) - p0
                    u = q @ d
                    if not (-0.6 <= u <= L):
                        continue
                    r = max(r0 + (r1 - r0) * u / L, 0.5)
                    perp = np.linalg.norm(q - d * u)
                    if perp * perp <= r * r + 0.15:
                        cells[(x, y, z)] = col['tip'] if u > L - 1 else col['spar']
        return cells

    def hits(s, cells, own):
        return sum(1 for k in cells if k in s.occ and k not in s.mast[own])

    def spanker(s):
        Sp = s.Y['spanker']
        log = {}
        # boom：jaws 從 z_from 往上試，長度取到末端 X ≥ end_x_min，要不碰（自己那根桅除外）
        B = Sp['boom']
        a = math.radians(B['angle_deg'])
        d = (-math.cos(a), 0, math.sin(a))
        tried = []
        for z in range(B['z_from'], B['z_from'] + 30):
            xs = s.xs_at('mizzen', z)
            xb = min(xs)
            p0 = (xb - 0.5, YC, z)
            L = (p0[0] - B['end_x_min']) / math.cos(a)
            c = s.spar_cells(p0, d, L, B['r'], B['r'] * B['taper_end'])
            h = s.hits(c, 'mizzen')
            tried.append([z, h])
            if h == 0:
                break
        assert h == 0, ('boom 找不到不碰的高度', tried)
        s.add_spar('spanker-boom', 'boom', p0, d, L, B, c, xs)
        log['boom'] = {'tried_z_hits': tried, 'jaws_z': z, 'length': round(L, 1)}
        # gaff：jaws 從 z_from 往下、每個高度照角度試，取第一個不碰的
        G = Sp['gaff']
        tried = []
        best = None
        for z in range(G['z_from'], G['z_min'] - 1, -1):
            xs = s.xs_at('mizzen', z)
            xb = min(xs)
            p0 = (xb - 0.5, YC, z)
            for ang in G['angles_deg']:
                a = math.radians(ang)
                d = (-math.cos(a), 0, math.sin(a))
                c = s.spar_cells(p0, d, G['len'], G['r'], G['r'] * G['taper_end'])
                h = s.hits(c, 'mizzen')
                # 也不准穿進後桅自己（jaws 那一端貼著除外）：格心在後桅的格上、離 jaws 超過 2 格
                hm = sum(1 for k in c if k in s.mast['mizzen'] and abs(k[2] - z) > 2)
                tried.append([z, ang, h, hm])
                if h == 0 and hm == 0:
                    best = (z, ang, p0, d, c, xs)
                    break
            if best:
                break
        assert best, ('gaff 找不到不碰的高度與角度', tried[-10:])
        z, ang, p0, d, c, xs = best
        s.add_spar('spanker-gaff', 'gaff', p0, d, G['len'], G, c, xs)
        log['gaff'] = {'tried': tried, 'jaws_z': z, 'angle_deg': ang, 'length': G['len']}
        s.spanker_log = log

    def add_spar(s, nm, tier, p0, d, L, G, cells, xs):
        d = np.array(d, float)
        p0 = np.array(p0, float)
        pts = [('jaws', p0), ('end', p0 + d * (L - 0.5))]
        for u in np.arange(8, L - 1, 8):
            pts.append(('top%d' % int(u), p0 + d * u + np.array([0, 0, G['r'] * 0.9])))
        for n, p in pts:
            s.anchor(nm, n, tuple(int(round(c)) for c in p), n.rstrip('0123456789'))
        mid = (min(xs) + max(xs)) / 2
        s.members[nm] = {'mast': 'mizzen', 'tier': tier, 'label': '後桅 spanker ' + tier, 'cells': cells,
                         'pivot': (int(math.floor(mid)), YC, int(p0[2])), 'angle': 0, 'len': L, 'r': G['r'], 'sail': 'spanker',
                         'log': {'jaws': [round(float(c), 1) for c in p0], 'end': [round(float(c), 1) for c in p0 + d * L], 'mast_x': [min(xs), max(xs)]}}

    def build(s):
        for Y in s.Y['yards']:
            s.yard(Y)
        s.spanker()

    def place(s):
        s.place = []
        col = {}
        for nm, M in s.members.items():
            pv = M['pivot']
            ks = np.array(sorted(M['cells']) + [pv])
            lo, hi = ks.min(0) - 1, ks.max(0) + 1
            M['origin'] = [int(c) for c in lo]
            M['size'] = [int(c) for c in hi - lo + 1]
            at = [pv[i] + 0.5 for i in range(3)]
            pivot = [pv[i] - M['origin'][i] + 0.5 for i in range(3)]
            rz = -M['angle']
            meta = {'kind': 'yard', 'mast': M['mast'], 'yard': M['tier'], 'length_ft': round(M['len'] / FT, 1), 'diameter_in': round(2 * M['r'] / IN, 1),
                    'pivot_anchor': 'pivot', 'turn_axis': 'z', 'rotate_z_deg': rz}
            if M['sail']:
                meta['sail'] = M['sail']
            s.place.append({'member': nm, 'work': s.Y['prefix'] + nm, 'title': '夜燈號 帆桁 ' + M['label'], 'host': s.Y['works'][M['mast']],
                            'link': s.Y['links'][M['mast']], 'model': 'yard-' + nm, 'origin': M['origin'], 'size': M['size'],
                            'cells': len(M['cells']), 'at': at, 'pivot': pivot, 'rotate': [0, 0, rz], 'meta': meta})
            # 轉過之後：格心＋八個角落在組裝件實心（自己那根桅除外）的格數
            hit_c, hit_k = 0, 0
            own = s.mast[M['mast']]
            for k in M['cells']:
                q = rotz([k[0] + 0.5, k[1] + 0.5, k[2] + 0.5], at, rz)
                cc = tuple(int(math.floor(v)) for v in q)
                if cc in s.occ and cc not in own:
                    hit_c += 1
                for dx in (-0.5, 0.5):
                    for dy in (-0.5, 0.5):
                        for dz in (-0.5, 0.5):
                            q2 = rotz([k[0] + 0.5 + dx, k[1] + 0.5 + dy, k[2] + 0.5 + dz], at, rz)
                            c2 = tuple(int(math.floor(v - 1e-9)) for v in q2)
                            if c2 in s.occ and c2 not in own:
                                hit_k += 1
            col[nm] = {'center_hits': hit_c, 'corner_hits': hit_k}
            for p in s.points:
                if p['member'] == nm:
                    p['owner'] = s.Y['prefix'] + nm
                    p['local'] = [p['world'][i] - M['origin'][i] for i in range(3)]
                    p['braced'] = [round(v, 3) for v in rotz([p['world'][i] + 0.5 for i in range(3)], at, rz)]
            s.points.append({'member': nm, 'name': 'pivot', 'kind': 'pivot', 'side': 'CL', 'world': list(pv), 'owner': s.Y['prefix'] + nm,
                             'local': [pv[i] - M['origin'][i] for i in range(3)], 'braced': at})
        return col

    def checks(s):
        v = {}
        for nm, M in s.members.items():
            ks = set(M['cells'])
            # 一塊（6 連通）
            seen, stack = set(), [next(iter(ks))]
            while stack:
                k = stack.pop()
                if k in seen:
                    continue
                seen.add(k)
                for dd in ((1, 0, 0), (-1, 0, 0), (0, 1, 0), (0, -1, 0), (0, 0, 1), (0, 0, -1)):
                    n = (k[0] + dd[0], k[1] + dd[1], k[2] + dd[2])
                    if n in ks and n not in seen:
                        stack.append(n)
            mir = sum(1 for (x, y, z) in ks if (x, 2 * YC - y, z) not in ks)
            pts_in = all(tuple(p['world']) in ks or p['kind'] in ('pivot',) for p in s.points if p['member'] == nm and p['kind'] in ('yardarm', 'pivot'))
            v[nm] = {'cells': len(ks), 'components_ok': len(seen) == len(ks), 'mirror_missing': mir, 'arm_points_on_cells': pts_in}
        return v

    def write(s, v):
        out = os.path.join(s.design, 'masks', 'yards')
        os.makedirs(out, exist_ok=True)
        files = {}
        for P in s.place:
            M = s.members[P['member']]
            o = M['origin']
            rows = sorted((k[0] - o[0], k[1] - o[1], k[2] - o[2], c) for k, c in M['cells'].items())
            p = os.path.join(out, P['member'] + '.vox.txt')
            open(p, 'w', encoding='utf-8', newline='\n').write('# %s —— 沒轉的帆桁（%s 自己的座標；組裝件座標 ＝ 這裡 ＋ %s）（%d 格）\n' % (
                P['member'], P['work'], ','.join(map(str, o)), len(rows)) + '\n'.join('%d,%d,%d,%d' % r for r in rows) + '\n')
            files[P['member']] = {'cells': len(rows), 'sha256': hashlib.sha256(open(p, 'rb').read()).hexdigest()}
        rp = os.path.join(s.design, 'rig_points_yards.json')
        json.dump({'note': '帆桁子作品的固定點（階段十四）：local ＝ 子作品座標（sub=anchor 用）；world ＝ 沒轉時的組裝件座標；braced ＝ 模型轉過之後的格心（組裝件座標）。'
                           'P ＝ y < 160（左舷）', 'points': s.points}, open(rp, 'w', encoding='utf-8', newline='\n'), ensure_ascii=False, indent=1)
        files['rig_points'] = {'points': len(s.points), 'sha256': hashlib.sha256(open(rp, 'rb').read()).hexdigest()}
        pp = os.path.join(s.design, 'yards_placement.json')
        json.dump({'placements': s.place}, open(pp, 'w', encoding='utf-8', newline='\n'), ensure_ascii=False, indent=1)
        files['placement'] = {'sha256': hashlib.sha256(open(pp, 'rb').read()).hexdigest()}
        v['files'] = files
        json.dump(v, open(os.path.join(s.design, 'verify_yards.json'), 'w', encoding='utf-8', newline='\n'), ensure_ascii=False, indent=1)


def render_sheet(Y, path):
    """上：右舷側面（x–z）＝ 組裝件剪影淡色＋帆桁（沒轉）黑；下：從上往下看（x–y）＝ 帆桁轉過之後（brace）。"""
    X0, X1, Z1, Yh = 40, 1000, 620, 320
    top = np.full((Z1, X1 - X0, 3), 250, np.uint8)
    plan = np.full((Yh, X1 - X0, 3), 250, np.uint8)
    for (x, y, z) in Y.occ:
        if X0 <= x < X1:
            if z < Z1:
                top[Z1 - 1 - z, x - X0] = (215, 208, 196)
            plan[y, x - X0] = (215, 208, 196)
    for P in Y.place:
        M = Y.members[P['member']]
        for (x, y, z), c in M['cells'].items():
            if X0 <= x < X1 and z < Z1:
                top[Z1 - 1 - z, x - X0] = DP.rgb332(c)
            q = rotz([x + 0.5, y + 0.5, z], P['at'], P['rotate'][2])
            xx, yy = int(q[0]), int(q[1])
            if X0 <= xx < X1 and 0 <= yy < Yh:
                plan[yy, xx - X0] = DP.rgb332(c)
    for p in Y.points:
        if p['kind'] in ('earing', 'jaws', 'end', 'sling'):
            x, z = p['world'][0], p['world'][2]
            if X0 <= x < X1 and z < Z1:
                top[max(0, Z1 - 3 - z):Z1 + 2 - z, max(0, x - X0 - 2):x - X0 + 3] = (200, 60, 30)
    im = Image.fromarray(np.vstack([top, np.full((12, X1 - X0, 3), 255, np.uint8), plan[::-1]]))
    dr = ImageDraw.Draw(im)
    dr.text((6, 4), 'sheet 15 v1  yards (starboard profile, unbraced; red = earings/slings/jaws/ends)', fill=(0, 0, 0))
    dr.text((6, Z1 + 16), 'plan view from above (starboard up), yards braced', fill=(0, 0, 0))
    im.save(path)


def main():
    sys.stdout.reconfigure(encoding='utf-8')
    design = os.path.abspath(sys.argv[1])
    Y = Yards(design, sys.argv[2], {'mizzen': sys.argv[3], 'main': sys.argv[4], 'fore': sys.argv[5]})
    Y.build()
    v = {'base': Y.sha}
    v['collide_after_brace'] = Y.place()
    v['members'] = Y.checks()
    v['spanker'] = Y.spanker_log
    v['placements'] = {P['member']: {k: P[k] for k in ('cells', 'size', 'origin', 'at', 'pivot', 'rotate')} for P in Y.place}
    v['total_cells'] = sum(P['cells'] for P in Y.place)
    v['anchors'] = len(Y.points)
    v['yard_log'] = {nm: M['log'] for nm, M in Y.members.items()}
    Y.write(v)
    render_sheet(Y, os.path.join(design, 'sheet15_yards_v1.png'))
    print(json.dumps({k: v[k] for k in ('collide_after_brace', 'members', 'total_cells', 'anchors', 'yard_log')}, ensure_ascii=False, indent=1))
    print(json.dumps({k: {kk: vv for kk, vv in v['spanker'][k].items() if kk != 'tried'} for k in v['spanker']}, ensure_ascii=False))


if __name__ == '__main__':
    main()
