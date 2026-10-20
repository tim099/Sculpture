# 越嶺號 階段六（TASK-0763）：槳 ⇒ masks/oars/{inner,outer}.vox.txt（兩件新通用部件，0.05 m）、oars_placement.json、verify_oars.json
#   用法：python -I -X utf8 draft_oars.py [--probe=drop=S05i] [--probe=sink=S05i:3]
#   · 照造船規格 §9.10、§9.10.1（皇家號）：一支槳一個外部模型、畫在「掃到一半」的姿勢（垂直於船身、槳葉中心落在水面）；右舷原樣、左舷 mirror=y。
#   · 每座 2 人各持一槳（alla sensile）：靠走道那位用長槳（inner）、靠舷那位用短槳（outer）；槳柄靠在縱樑頂、槳栓旁一格。
#   · 量：每支模型格心＋八角不落在船的實心（船殼、階段二～五、武器與錨模型）；seat 那一格空、腳下實心；槳座旁 8 格內有縱樑；左右支數；槳葉中心離水。
import sys, os, json, math, hashlib
import numpy as np

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import lines as HL
import draft_guns as DG

sys.stdout.reconfigure(encoding='utf-8')
SX, SY, SZ = 360, 161, 230
CLR_X, CLR_Z = 0.9, 1.0   # 槳柄中心離槳栓、離縱樑頂幾格：0.05 m 的格心在半徑內就算、格子本身多伸出半格角（v1 每支擦到縱樑頂與槳栓 20–30 點）


def V(d):
    return d['v'] if isinstance(d, dict) and 'v' in d else d


def oar_component(o, blade, pose, seat_dx_world):
    """槳元件（0.05 m）：x 槳柄中線 xc、y 沿槳往外（y 0 ＝ 槳柄端）、z 往上；回 cells、anchors、size、θ。"""
    k = 20.0                                                     # 一公尺幾格
    Lc, Li = o['len_m'] * k, o['inboard_m'] * k
    lb = blade['len_m'] * k
    out_to_blade_c = (o['len_m'] - o['inboard_m'] - blade['len_m'] / 2) * 10   # 世界格（0.1 m）
    th = math.asin((pose['pivot_z'] + CLR_Z - pose['water_z']) / out_to_blade_c)
    d = np.array([math.cos(th), -math.sin(th)])
    xc = 2
    zp = (Lc - Li) * math.sin(th) + 4
    O = np.array([0.5, zp + Li * math.sin(th)])                  # 槳柄端（y, z）
    W = xc + 2 * seat_dx_world + 3
    H = int(math.ceil(O[1] + 3))
    Ly = int(math.ceil(Lc * math.cos(th))) + 2
    cells = {}
    for y in range(Ly):
        for z in range(H):
            q = np.array([y + 0.5, z + 0.5]) - O
            s = float(q @ d)
            e = float(q[0] * d[1] - q[1] * d[0])
            if not (0 <= s <= Lc):
                continue
            for x in range(0, 5):
                dx = x + 0.5 - (xc + 0.5)
                if s >= Lc - lb:                                 # 槳葉：直立、1 格厚
                    if abs(dx) <= 0.5 and abs(e) <= blade['w_m'] * k / 2:
                        cells[(x, y, z)] = 141
                else:
                    r = 0.8 if s < Li * 0.4 else (0.95 if s < Li + 30 else 0.9)
                    if math.hypot(dx, e) <= r:
                        cells[(x, y, z)] = 68 if abs(s - Li) <= 3 else (104 if s < Li * 0.4 else 173)
    def on_line(s):
        p = O + d * s
        c = (xc, int(math.floor(p[0])), int(math.floor(p[1])))
        if c not in cells:
            c = min(cells, key=lambda t: (t[0] - xc) ** 2 + (t[1] + 0.5 - p[0]) ** 2 + (t[2] + 0.5 - p[1]) ** 2)
        return c
    piv = on_line(Li)
    bl = on_line(Lc - 0.5)
    exact = (xc + 0.5, float((O + d * Li)[0]), float((O + d * Li)[1]))      # 模型的 pivot 用中心線上的精確點
    return cells, {'pivot': piv, 'blade': bl, '_exact': exact}, (W, Ly, H), th


def main():
    probe = {}
    for a in sys.argv[1:]:
        if a.startswith('--probe='):
            k, v = a[len('--probe='):].split('=', 1)
            probe[k] = v
    plan, L, occ = DG.world()
    YC = L.YC
    tz = np.floor(L.sheer(np.arange(SX) + 0.5)).astype(int)
    oc = {k: V(v) for k, v in plan['oars'].items() if k != 'src'}
    lay = {k: V(v) for k, v in plan['layout'].items() if k != 'src'}
    benches = [lay['benches']['x0'] + lay['benches']['pitch'] * i for i in range(lay['benches']['n'])]
    rail_dy = lay['apostis']['rail_dy']
    # 武器、錨、補給模型的格也算障礙
    mocc = np.zeros_like(occ)
    for f, key in (('guns_placement.json', 'rows'), ('hold_placement.json', 'anchors'), ('hold_placement.json', 'stores')):
        for r in json.load(open(os.path.join(HERE, f), encoding='utf-8'))[key]:
            w = r.get('source_work') or r['work']
            Q = DG.load_list(os.path.join(HERE, 'masks', 'guns', 'bombardella.vox.txt')) if w.endswith('bombardella') else \
                DG.load_list(os.path.join(HERE, 'masks', 'hold', 'anchor.vox.txt')) if w.endswith('anchor-grapnel') else DG.export(w)
            Pw = DG.place((Q[:, :3].astype(float)[:, None, :] + DG.OFFS[None]).reshape(-1, 3), dict(r, mirror=r.get('mirror', '')))
            i = np.floor(Pw).astype(int)
            mocc[i[:, 0], i[:, 1], i[:, 2]] = True
    hold = DG.load_list(os.path.join(HERE, 'masks', 'hold', 'hold.vox.txt'))
    allocc = occ | mocc
    allocc[hold[:, 0], hold[:, 1], hold[:, 2]] = True
    comps = {}
    for kind in ('inner', 'outer'):
        o = oc[kind]
        seat_dx_world = o['seat_dx'] - (o['thole_dx'] - 1)       # 座（xb＋seat_dx）離槳柄（槳栓 −1）幾格
        comps[kind] = oar_component(o, oc['blade'], oc['pose'], seat_dx_world)
    rows, rec = [], []
    drop = probe.get('drop')
    sink = probe.get('sink')
    for side, sg in (('S', 1), ('P', -1)):
        for i, xb in enumerate(benches, 1):
            for kind, tag in (('inner', 'i'), ('outer', 'o')):
                name = 'oar-%s%02d%s' % (side, i, tag)
                if drop == name[4:]:
                    continue
                o = oc[kind]
                cells, anc, size, th = comps[kind]
                xt = xb + o['thole_dx']
                piv_local = np.array(anc['_exact'], float)
                at = [xt - CLR_X, YC + 0.5 + sg * (rail_dy[1] - 0.5), oc['pose']['pivot_z'] + CLR_Z]
                if sink and sink.split(':')[0] == name[4:]:
                    at[2] -= float(sink.split(':')[1])
                # 座：世界 (xb + seat_dx, YC ± seat_dy, 座板頂 ＋ 1) ⇒ 換回元件座標（右舷那一支）
                zseat = int(tz[xb]) + lay['benches']['h'] + 1
                seat_w = np.array([xb + o['seat_dx'] + 0.5, YC + 0.5 + o['seat_dy'], zseat + 0.5])
                at_s = np.array([at[0], YC + 0.5 + (rail_dy[1] - 0.5), at[2]])
                seat_local = (seat_w - at_s) * 2 + piv_local
                m = {'at': at, 'pivot': list(piv_local), 'rotate': [0, 0, 0], 'scale': 0.5, 'mirror': 'y' if sg < 0 else ''}
                S = (np.array(list(cells.keys()), float)[:, None, :] + DG.OFFS[None]).reshape(-1, 3)
                Pw = DG.place(S, m)
                h = DG.hits(allocc, Pw)
                bl = DG.place(np.array([anc['blade']], float) + 0.5, m)[0]
                blade_c = DG.place(np.array([[anc['blade'][0] + 0.5, anc['blade'][1] + 0.5 - 10 * math.cos(th), anc['blade'][2] + 0.5 + 10 * math.sin(th)]]), m)[0]
                seat_world = (int(seat_w[0]), YC + sg * o['seat_dy'], zseat)
                seat_ok = (not allocc[seat_world]) and bool(occ[seat_world[0], seat_world[1], seat_world[2] - 1])
                head_ok = not allocc[seat_world[0], seat_world[1], seat_world[2]:seat_world[2] + 14].any()
                piv_w = np.floor(np.array(at)).astype(int)
                rail_near = bool(occ[max(0, piv_w[0] - 8):piv_w[0] + 9, max(0, piv_w[1] - 8):piv_w[1] + 9, max(0, piv_w[2] - 8):piv_w[2] + 9].any())
                rows.append({'name': name, 'kind': kind, 'side': side, 'at': [round(v, 3) for v in at], 'pivot': [round(v, 3) for v in piv_local],
                             'mirror': 'y' if sg < 0 else 'none', 'seat_local': [int(math.floor(v)) for v in seat_local],
                             'meta': {'kind': 'oar', 'rowers': 1, 'side': side, 'stroke_deg': 30, 'dip_deg': 12}})
                rec.append({'name': name, 'hits': h, 'seat_ok': seat_ok, 'head_ok': head_ok, 'rail_near': rail_near,
                            'blade_center_above_water_m': round(float(blade_c[2] - oc['pose']['water_z']) * 0.1, 3)})
    R = {'oars': len(rows), 'S': sum(1 for r in rows if r['side'] == 'S'), 'P': sum(1 for r in rows if r['side'] == 'P'),
         'hits_total': sum(r['hits'] for r in rec), 'hit_oars': [r['name'] for r in rec if r['hits']],
         'seat_ok': sum(r['seat_ok'] for r in rec), 'head_ok': sum(r['head_ok'] for r in rec), 'rail_near': sum(r['rail_near'] for r in rec),
         'blade_above_water_m': [min(r['blade_center_above_water_m'] for r in rec), max(r['blade_center_above_water_m'] for r in rec)],
         'angle_deg': {k: round(math.degrees(comps[k][3]), 2) for k in comps}}
    if probe:
        print(json.dumps({'probe': probe, **{k: R[k] for k in ('oars', 'S', 'P', 'hits_total', 'hit_oars')}}, ensure_ascii=False))
        return
    # 每一種槳的 seat：照右舷那幾支的中位數（舷弧讓座的高度差一兩格 ⇒ 遊戲在 seat 旁 6 格內往下找站得住的格）
    os.makedirs(os.path.join(HERE, 'masks', 'oars'), exist_ok=True)
    comp_out = {}
    for kind in comps:
        cells, anc, size, th = comps[kind]
        sl = np.median(np.array([r['seat_local'] for r in rows if r['kind'] == kind and r['side'] == 'S']), axis=0).astype(int).tolist()
        size = [max(size[0], sl[0] + 1), size[1], max(size[2], sl[2] + 1)]
        anc = {k: v for k, v in anc.items() if not k.startswith('_')}
        anc['seat'] = tuple(sl)
        fn = os.path.join(HERE, 'masks', 'oars', kind + '.vox.txt')
        with open(fn, 'w', encoding='utf-8', newline='\n') as f:
            f.write('# 槳（%s；fusta alla sensile，%.1f m、舷內 %.1f m、1 人划；通用部件 0.05 m）x,y,z,color —— 元件座標（x 槳柄中線、y 往槳葉、z 往上；掃到一半的姿勢）\n' % (kind, oc[kind]['len_m'], oc[kind]['inboard_m']))
            f.write(''.join('%d,%d,%d,%d\n' % (p[0], p[1], p[2], c) for p, c in sorted(cells.items())))
        comp_out[kind] = {'work': 'kotoko-fusta-01m-oar-' + kind, 'size': size, 'cells': len(cells), 'anchors': {k: list(v) for k, v in anc.items()},
                          'angle_deg': round(math.degrees(th), 2), 'sha256': hashlib.sha256(open(fn, 'rb').read()).hexdigest()}
    with open(os.path.join(HERE, 'oars_placement.json'), 'w', encoding='utf-8', newline='\n') as f:
        json.dump({'host_work': 'kotoko-fusta-01m-apostis', 'components': comp_out, 'rows': rows}, f, ensure_ascii=False, indent=1)
    with open(os.path.join(HERE, 'verify_oars.json'), 'w', encoding='utf-8', newline='\n') as f:
        json.dump({'summary': R, 'rows': rec}, f, ensure_ascii=False, indent=1)
    print(json.dumps(R, ensure_ascii=False, indent=1))


if __name__ == '__main__':
    main()
