# 階段三十三：帆桁改外部模型（每根一件子作品，用模型引用 ⇒ 可以任意轉；遊戲裡跟著風向轉）
#   輸入：plan.json 的 yards／brace 段、四件桅杆子作品（標記 帆桁:begin 的桅本身＋現在的樣子）、masks/yards、masks/brace、
#         rig_points_yards_square.json（沒轉的固定點）、rig_points_yards.json（現在轉過的固定點）
#   ⇒ masks/yard_models/<帆桁>.vox.txt（子作品自己的座標）、masks/yard_models/carve_<桅>.vox.txt（從桅杆子作品刻掉的，帶顏色守門）、
#      rig_points_yard_models.json（固定點，owner ＝ 帆桁子作品、world ＝ 沒轉時的組裝件座標）、yard_models_placement.json、verify_yard_models.json
# 用法：python -I draft_yard_models.py <design 資料夾>
#   · 子作品裡放的是「沒轉」的帆桁：截面、錐度、端色照 draft_yards.py，但不扣跟桅重疊的格（獨立的零件要完整）
#   · 模型 pivot ＝ 子作品裡 `pivot` 那一格的格心：方帆桁與 spritsail ＝ 帆桁中心那一格；gaff／boom ＝ 後桅軸心在 jaws 高度那一格（繞桅轉）
#   · 轉角照 plan.json brace（方帆桁；gaff／boom／spritsail 0）—— 繞世界 z 軸
import sys, os, json, hashlib, math, subprocess
import numpy as np

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from draft_masts import export_list   # noqa: E402
from draft_yards import FT, IN, YC     # noqa: E402

PREFIX = 'basecamp-frigate-constitution-01m-yard-'
LINK = {'fore': '前桅', 'main': '主桅', 'mizzen': '後桅', 'bowsprit': '艏斜桅'}


def has_mark(work, name):
    r = subprocess.run(['senate', 'cmd', 'sculpture', '--arg', 'op=work', '--arg', 'sub=marks', '--arg', 'work=' + work],
                       capture_output=True, text=True, encoding='utf-8', errors='replace')
    return r.returncode == 0 and name.split(':')[0] in r.stdout


def load_list(p):
    a = np.loadtxt(p, delimiter=',', comments='#', dtype=np.int64, ndmin=2, encoding='utf-8')
    return {(int(x), int(y), int(z)): int(c) for x, y, z, c in a}


def rotz(p, c, deg):
    t = math.radians(deg)
    dx, dy = p[0] - c[0], p[1] - c[1]
    return [c[0] + dx * math.cos(t) - dy * math.sin(t), c[1] + dx * math.sin(t) + dy * math.cos(t), p[2]]


class YardModels:
    def __init__(s, design):
        s.design = design
        s.plan = json.load(open(os.path.join(design, 'plan.json'), encoding='utf-8'))
        s.Y = s.plan['yards']
        s.B = s.plan['brace']
        s.read = {}
        s.mast, s.now = {}, {}
        for m, w in s.Y['works'].items():
            mk = s.Y['base']['mark'] if has_mark(w, s.Y['base']['mark']) else None
            a = export_list(w, draft=False, links='none', mark=mk)
            s.mast[m] = {(int(x), int(y), int(z)) for x, y, z, c in a}
            b = export_list(w, draft=False, links='none')
            s.now[m] = {(int(x), int(y), int(z)): int(c) for x, y, z, c in b}
            s.read[m] = {'mark': mk, 'mast_at_mark': len(s.mast[m]), 'now': len(s.now[m])}
        s.members = {}     # 名字 → {mast, cells{world: color}, pivot(world cell), anchors[], angle, ...}

    def radius(s, r0, sf):
        T = s.Y['taper']
        return r0 * float(np.interp(sf, T['s'], T['k']))

    def xs_at(s, m, z):
        return [x for (x, y, zz) in s.mast[m] if zz == z and abs(y - YC) <= 6]

    def angle(s, name):
        for tier, deg in s.B['angle_deg'].items():
            if name.endswith('-' + tier):
                return deg
        return 0

    # ── 橫桁（沿 y，沒轉）：同 draft_yards.py Yards.yard，只是不扣重疊 ──
    def yard(s, Y, xc=None):
        L = Y['ft'] * FT
        r0 = Y['in'] * IN / 2
        z0 = Y['z']
        if xc is None:
            xc = max(s.xs_at(Y['mast'], z0)) + 0.5 + r0
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
        s.members[Y['name']] = {'mast': Y['mast'], 'kind': 'square' if Y['mast'] != 'bowsprit' else 'spritsail', 'cells': cells,
                                'pivot': (int(round(xc)), YC, z0), 'axis': [round(xc, 3), YC, z0], 'angle': s.angle(Y['name']) if Y['mast'] != 'bowsprit' else 0,
                                'ft': Y['ft'], 'in': Y['in']}

    # ── gaff／boom（x–z 平面裡斜的）：同 draft_yards.py Yards.spar ──
    def spar(s, name, p0, d, L, r0, r1):
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

    def build(s):
        for Y in s.Y['yards']:
            s.yard(Y)
        Sp = s.Y['spanker']
        for nm, G in (('spanker-gaff', Sp['gaff']), ('spanker-boom', Sp['boom'])):
            L = G['ft'] * FT
            r0 = G['in'] * IN / 2
            z = G['jaws_z']
            xs = s.xs_at('mizzen', z)
            xb = min(xs)
            a = math.radians(G['angle_deg'])
            cells = s.spar(nm, (xb - 0.5, YC, z), (-math.cos(a), 0, math.sin(a)), L, r0, r0 * G['taper_end'])
            mid = (min(xs) + max(xs)) / 2       # 後桅在 jaws 高度的軸心 ⇒ gaff／boom 繞桅轉
            s.members[nm] = {'mast': 'mizzen', 'kind': nm.split('-')[1], 'cells': cells, 'pivot': (int(math.floor(mid)), YC, z),
                             'axis': [mid + 0.5, YC + 0.5, z], 'angle': 0, 'ft': G['ft'], 'in': G['in'], 'mast_x': [min(xs), max(xs)]}
        # spritsail：中心 x 照 draft_yards.py（cap 往內 inboard_of_cap、吊在 bowsprit 底下）
        Ss = s.Y['spritsail']
        Bp = s.plan['masts']['bowsprit']
        h0, h1 = np.array(Bp['heel'], float), np.array(Bp['over_stem'], float)
        dd = (h1 - h0) / np.linalg.norm(h1 - h0)
        cap = h0 + dd * Bp['length'] * FT
        xs = int(round(cap[0] - Ss['inboard_of_cap']))
        r0 = Ss['in'] * IN / 2
        bmin = min(z for (xx, y, z) in s.mast['bowsprit'] if xx == xs and abs(y - YC) <= 1)
        Y = {'mast': 'bowsprit', 'name': 'spritsail', 'ft': Ss['ft'], 'in': Ss['in'], 'arm_ft': Ss['arm_ft'], 'z': int(round(bmin - 0.5 - r0))}
        s.yard(Y, xc=(xs - 0.5 - r0) + 0.5 + r0)

    def compare_old(s):
        # 正向對照：子作品裡的格 ⊇ 當初貼進桅杆的沒轉帆桁（masks/yards），多出來的只能是當初跟桅重疊被扣掉的
        v = {}
        for m in s.Y['works']:
            old = load_list(os.path.join(s.design, 'masks', 'yards', m + '.vox.txt'))
            gen = {}
            for nm, M in s.members.items():
                if M['mast'] == m:
                    gen.update(M['cells'])
            miss = [k for k in old if k not in gen]
            colr = [k for k in old if k in gen and gen[k] != old[k]]
            extra = [k for k in gen if k not in old]
            extra_in_mast = sum(1 for k in extra if k in s.mast[m])
            v[m] = {'old_square': len(old), 'generated': len(gen), 'missing': len(miss), 'color_diff': len(colr), 'extra': len(extra),
                    'extra_inside_mast_at_mark': extra_in_mast}
        return v

    def carve_lists(s):
        # 現在桅杆子作品裡的帆桁：方帆桁 ＝ masks/brace/<桅>_stamp（轉過的）；gaff／boom ＝ masks/yards/mizzen 裡在桅後面的；spritsail ＝ masks/yards/bowsprit
        s.carve = {}
        v = {}
        for m in s.Y['works']:
            if m in ('fore', 'main', 'mizzen'):
                L = load_list(os.path.join(s.design, 'masks', 'brace', m + '_stamp.vox.txt'))
                if m == 'mizzen':
                    old = load_list(os.path.join(s.design, 'masks', 'yards', 'mizzen.vox.txt'))
                    for nm in ('spanker-gaff', 'spanker-boom'):
                        for k in s.members[nm]['cells']:
                            if k in old:
                                L[k] = old[k]
            else:
                L = load_list(os.path.join(s.design, 'masks', 'yards', m + '.vox.txt'))
            now = s.now[m]
            absent = sum(1 for k in L if k not in now)
            wrong = sum(1 for k in L if k in now and now[k] != L[k])
            s.carve[m] = L
            # 刻完之後剩下的格裡，帆桁的顏色還有幾格（spar 36 只有帆桁用；tip 177 跟桅同色，不數）
            left36 = sum(1 for k, c in now.items() if c == s.Y['colors']['spar'] and k not in L)
            v[m] = {'carve': len(L), 'absent_now': absent, 'color_mismatch_now': wrong, 'after': len(now) - len(L), 'spar_color_left': left36}
        return v

    def anchors(s):
        sq = json.load(open(os.path.join(s.design, 'rig_points_yards_square.json'), encoding='utf-8'))['points']
        cur = {p['name']: p for p in json.load(open(os.path.join(s.design, 'rig_points_yards.json'), encoding='utf-8'))['points']}
        assert {p['name'] for p in sq} == set(cur), '兩份固定點名字不一樣'
        s.points = []
        for p in sq:
            mem, pt = p['name'].split('.', 1)
            s.points.append({'name': pt, 'old': p['name'], 'owner': PREFIX + mem, 'member': mem, 'kind': p['kind'], 'side': p['side'],
                             'world': p['world'], 'now': cur[p['name']]['world']})
        for nm, M in s.members.items():
            s.points.append({'name': 'pivot', 'old': None, 'owner': PREFIX + nm, 'member': nm, 'kind': 'pivot', 'side': 'CL',
                             'world': list(M['pivot']), 'now': None})

    def place(s):
        s.place = []
        dev = {}
        for nm, M in s.members.items():
            pv = M['pivot']
            ks = np.array(sorted(M['cells']) + [pv])     # gaff／boom 的 pivot 在桅軸上、不在桿上 ⇒ 外框要包到它（固定點要落在作品裡）
            lo, hi = ks.min(0) - 1, ks.max(0) + 1
            M['origin'] = [int(c) for c in lo]
            M['size'] = [int(c) for c in hi - lo + 1]
            if M['kind'] in ('square', 'spritsail'):
                assert pv in M['cells'], (nm, 'pivot 不在帆桁的格上', pv)
            at = [pv[i] + 0.5 for i in range(3)]
            pivot = [pv[i] - M['origin'][i] + 0.5 for i in range(3)]
            rz = -M['angle']      # 右舷那一頭（+y）往前（+x）⇒ 從上往下看順時針 ⇒ 繞 z 負角
            tier = nm.split('-', 1)[-1]
            meta = {'kind': 'yard', 'mast': M['mast'], 'yard': tier, 'length_ft': M['ft'], 'diameter_in': M['in'],
                    'pivot_anchor': 'pivot', 'turn_axis': 'z', 'rotate_z_deg': rz}
            sail = {'spanker-gaff': 'spanker', 'spanker-boom': 'spanker'}.get(nm, nm if M['kind'] == 'square' and nm != 'mizzen-crossjack' else '')
            if sail:
                meta['sail'] = sail
            s.place.append({'member': nm, 'work': PREFIX + nm, 'host': s.Y['works'][M['mast']], 'link': LINK[M['mast']], 'model': 'yard-' + nm,
                            'origin': M['origin'], 'size': M['size'], 'cells': len(M['cells']), 'at': at, 'pivot': pivot, 'rotate': [0, 0, rz],
                            'pivot_world_cell': list(pv), 'axis_exact': M['axis'], 'meta': meta})
            # 預期：固定點轉過去的位置 vs 現在（轉過、取整的）固定點，格心對格心
            ds = []
            for p in s.points:
                if p['member'] != nm or p['now'] is None:
                    continue
                q = rotz([p['world'][i] + 0.5 for i in range(3)], at, rz)
                n = [p['now'][i] + 0.5 for i in range(3)]
                ds.append(math.dist(q, n))
                p['expect'] = [round(c, 4) for c in q]
            dev[nm] = round(max(ds), 3) if ds else None
        return dev

    def write(s, v):
        out = os.path.join(s.design, 'masks', 'yard_models')
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
        for m, L in s.carve.items():
            rows = sorted((k[0], k[1], k[2], c) for k, c in L.items())
            p = os.path.join(out, 'carve_' + m + '.vox.txt')
            open(p, 'w', encoding='utf-8', newline='\n').write('# %s —— 從 %s 刻掉的帆桁（carvevox，行尾顏色守門；世界座標 at 0,0,0）（%d 格）\n' % (
                m, s.Y['works'][m], len(rows)) + '\n'.join('%d,%d,%d,%d' % r for r in rows) + '\n')
            files['carve_' + m] = {'cells': len(rows), 'sha256': hashlib.sha256(open(p, 'rb').read()).hexdigest()}
        rp = os.path.join(s.design, 'rig_points_yard_models.json')
        json.dump({'note': '帆桁子作品的固定點（階段三十三）：名字 ＝ 舊名去掉「帆桁名.」；world ＝ 沒轉時的組裝件座標（子作品座標 ＝ world − origin）；'
                           'now ＝ 改模型之前（轉過、取整）的位置；expect ＝ 模型轉過之後的格心（組裝件座標）；pivot ＝ 模型繞的那一格',
                   'points': s.points}, open(rp, 'w', encoding='utf-8', newline='\n'), ensure_ascii=False, indent=1)
        files['rig_points'] = {'points': len(s.points), 'sha256': hashlib.sha256(open(rp, 'rb').read()).hexdigest()}
        pp = os.path.join(s.design, 'yard_models_placement.json')
        json.dump({'placements': s.place}, open(pp, 'w', encoding='utf-8', newline='\n'), ensure_ascii=False, indent=1)
        files['placement'] = {'sha256': hashlib.sha256(open(pp, 'rb').read()).hexdigest()}
        v['files'] = files
        json.dump(v, open(os.path.join(s.design, 'verify_yard_models.json'), 'w', encoding='utf-8', newline='\n'), ensure_ascii=False, indent=1)


def main():
    sys.stdout.reconfigure(encoding='utf-8')
    design = os.path.abspath(sys.argv[1])
    Y = YardModels(design)
    Y.build()
    v = {'read': Y.read}
    v['compare_old_square'] = Y.compare_old()
    v['carve'] = Y.carve_lists()
    Y.anchors()
    v['anchor_max_dev_cells'] = Y.place()
    v['members'] = {P['member']: {k: P[k] for k in ('cells', 'size', 'origin', 'at', 'pivot', 'rotate')} for P in Y.place}
    v['total_cells_in_subworks'] = sum(P['cells'] for P in Y.place)
    v['total_carved'] = sum(len(L) for L in Y.carve.values())
    v['anchors'] = len(Y.points)
    Y.write(v)
    print(json.dumps({k: v[k] for k in v if k != 'files'}, ensure_ascii=False, indent=1))


if __name__ == '__main__':
    main()
