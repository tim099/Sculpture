# 皇家號 新圖紙 06（TASK-0705）：槳 ⇒ 槳元件清單（通用部件，0.05 m）、64 支的擺法 oars_placement.json、讀數 verify_oars.json
#   用法：python -I -X utf8 draft_oars.py [--probe=drop_oar=S05] [--probe=sink=S05:3]
#   · 槳元件（造船規格 §2.2、§9.10）：沿 +y（槳柄端 y 0 → 槳葉末端），畫在「掃到一半」的姿勢（垂直於船身、往外往下 angle_deg）；
#     固定點 pivot（槳靠在槳座的那一格）、blade（槳葉末端）、seat（第一個槳手坐的那一格）。右舷原樣、左舷 mirror=y（繞 pivot 翻）。
#   · 每張划手座一支：pivot 落在槳座（tolet，x ＝ 座的中心）船尾那一側 x_off、槳架縱樑頂上 pivot_lift 格；第一個槳手坐在座上（x −1）。
#   · 讀數：模型格心＋八角不落在船的實心（draft_guns.collide）；槳葉中心離水線；seat 那一格空、腳下是划手座；槳座旁 8 格內有縱樑（遊戲的掛點）。
#   · --probe：反向對照（只印讀數）。drop_oar=S05 ⇒ 少一支；sink=S05:3 ⇒ 那一支往下沉 3 格（要報碰撞）。
import sys, os, json, math, hashlib
import numpy as np

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
sys.path.insert(0, os.path.join(HERE, 'tools'))
import lines as HL
import wio
import draft_guns as DG

sys.stdout.reconfigure(encoding='utf-8')
YC = 160
M5 = 0.05                                   # 元件一格幾公尺


def V(d):
    return d['v'] if isinstance(d, dict) and 'v' in d else d


def ld(p):
    return np.loadtxt(os.path.join(HERE, p), delimiter=',', comments='#', dtype=np.int32, ndmin=2, encoding='utf-8')


def oar_cells(O):
    """回傳 (格 dict, size, 固定點)。x 中心 3.5；y 0 ＝ 槳柄端；z 照斜率。"""
    yi = int(round(O['inboard_m'] / M5))              # 槳座在 y yi
    yo = int(round(O['outboard_m'] / M5))
    L = yi + yo
    tn = math.tan(math.radians(O['angle_deg']))
    zt = math.ceil(yo * tn + O['blade_w_m'] / M5 / 2 + 3)   # 槳座的 z：讓槳葉下緣 ≥ 3
    zc = lambda y: zt - (y - yi) * tn
    size = [7, L + 3, int(math.ceil(zc(0) + 4))]
    d0, d1 = O['loom_d_m']
    yb = L - int(round(O['blade_m'] / M5))
    cells = {}
    for y in range(0, L + 1):
        c = zc(y + 0.5)
        if y < yb:
            r = (d0 + (d1 - d0) * min(1.0, y / max(1, yb))) / M5 / 2
            for x in range(size[0]):
                for z in range(size[2]):
                    if (x + 0.5 - 3.5) ** 2 + (z + 0.5 - c) ** 2 <= max(r, 0.9) ** 2:
                        cells[(x, y, z)] = 104 if abs(y - yi) <= 2 else 141
        else:                                          # 槳葉：一格厚（x 3）、寬 blade_w、往外漸寬一點
            hw = O['blade_w_m'] / M5 / 2 * (0.8 + 0.2 * (y - yb) / max(1, L - yb))
            for z in range(size[2]):
                if abs(z + 0.5 - c) <= hw:
                    cells[(3, y, z)] = 141
    piv = (3, yi, int(math.floor(zc(yi + 0.5))))
    tip = (3, L, int(math.floor(zc(L + 0.5))))
    seat = (3, yi - int(round(O['seat_in_m'] / M5)), None)
    assert piv in cells and tip in cells, (piv, tip)
    return cells, size, {'pivot': list(piv), 'blade': list(tip)}, zc, yi, L


def main():
    probe = {}
    for s in sys.argv[1:]:
        if s.startswith('--probe='):
            k, v = s[len('--probe='):].split('=')
            probe[k] = v
    plan = HL.load_plan(HERE)
    O = V(plan['oars'])
    D = {k: V(v) for k, v in plan['layout'].items()}
    L_ = HL.Lines(plan)
    sh = lambda x: int(np.floor(L_.sheer(np.array([x + 0.5]))[0]))
    rail_top = lambda x: sh(x) + int(D['rail_above_sheer'])
    seat_top = lambda x: sh(x) + int(D['seat_above_sheer'])
    benches = [int(round(D['bench_first_x'] + D['bench_pitch'] * i)) for i in range(int(D['bench_count']))]
    ah = int(D['apostis_half'])
    cells, size, anc, zc, yi, Ltot = oar_cells(O)
    sc = O['scale']
    # 船的實心（船殼＋前五階段的格）
    occ_l = [wio.load_lists(os.path.join(HERE, 'masks', 'hull'))]
    for nm in ('deck', 'apostis', 'rambade', 'eperon', 'stern', 'ladders'):
        occ_l.append(ld('masks/upper/%s.vox.txt' % nm))
    for nm in ('main', 'fore'):
        occ_l.append(ld('masks/masts/%s.vox.txt' % nm))
    for nm in ('rudder', 'hold', 'magazine', 'ladder'):
        occ_l.append(ld('masks/hold/%s.vox.txt' % nm))
    allc = np.concatenate(occ_l)
    occ = set(map(tuple, allc[:, :3].tolist()))
    occ_k = np.array(sorted((x * 1000 + y) * 1000 + z for (x, y, z) in occ), dtype=np.int64)
    rail = set(map(tuple, ld('masks/upper/apostis.vox.txt')[:, :3].tolist()))
    deckc = {tuple(r[:3]): r[3] for r in ld('masks/upper/deck.vox.txt').tolist()}
    # seat：槳座往船裡 seat_in_m、那張座頂上一格（世界）⇒ 換回元件座標（pivot 對齊後，世界 1 格 ＝ 元件 2 格）
    src = np.array([[x, y, z, c] for (x, y, z), c in sorted(cells.items())])
    piv_l = [anc['pivot'][0] + 0.5, anc['pivot'][1] + 0.5, anc['pivot'][2] + 0.5]
    wl = plan['waterline']['z']
    out = []
    for side, sg in (('S', 1), ('P', -1)):
        for i, xc in enumerate(benches, 1):
            name = 'oar-%s%02d' % (side, i)
            if probe.get('drop_oar') == side + '%02d' % i:
                continue
            x = xc + O['x_off']
            at = [x + 0.5, YC + sg * (ah - 1) + 0.5, rail_top(x) + 1 + O['pivot_lift']]
            sk = probe.get('sink', '')
            if sk.startswith(side + '%02d:' % i):
                at[2] -= float(sk.split(':')[1])
            # 左舷 ＝ 繞 pivot 鏡 y：元件 y 翻向 ⇒ 用 rotate 180 再鏡 x 等價於鏡 y；讀數照鏡 y 算（rotz(180) 後 x 也翻，元件對 x 中線對稱 ⇒ 同一組格）
            deg = 0 if sg > 0 else 180
            n = DG.collide(occ_k, src, sc, piv_l, at, deg)
            bw = DG.anchor_world(anc['blade'], sc, piv_l, at, deg)
            bc = DG.anchor_world([3, Ltot - int(round(O['blade_m'] / M5 / 2)), int(math.floor(zc(Ltot - O['blade_m'] / M5 / 2)))], sc, piv_l, at, deg)
            st = seat_top(xc)                                             # 座高照那張座的中心量（座是一整塊、跟著 xc 的舷頂）
            seat_w = (xc - 1, YC + sg * (ah - 1 - int(round(O['seat_in_m'] / 0.1))), st + 1)
            hang = any((x + dx, YC + sg * (ah - 1) + dy, rail_top(x) + dz) in rail for dx in range(-8, 9) for dy in (-1, 0, 1) for dz in (-2, -1, 0))
            out.append({'name': name, 'side': side, 'bench_x': xc, 'at': [round(v, 3) for v in at], 'deg': deg, 'mirror': '' if sg > 0 else 'y',
                        'collide': n, 'blade_tip_z': round(bw[2], 2), 'blade_mid_z_minus_wl': round(bc[2] - (wl + 1), 2),
                        'seat_world': list(seat_w), 'seat_empty': seat_w not in occ, 'seat_on_bench': deckc.get((seat_w[0], seat_w[1], seat_w[2] - 1)) == 160,
                        'hang_rail': hang})
    # 元件座標裡的 seat（照右舷那一支換算：世界的 seat ⇒ 元件）
    o0 = next(o for o in out if o['side'] == 'S')
    sw = np.array(o0['seat_world'], float) + 0.5
    seat_l = np.floor(np.array(piv_l) + (sw - np.array(o0['at'])) / sc).astype(int).tolist()
    anc['seat'] = seat_l
    R = {'component': {'size': size, 'cells': len(cells), 'anchors': anc, 'length_m': round(Ltot * M5, 2)},
         'oars': len(out), 'per_side': {s: sum(1 for o in out if o['side'] == s) for s in 'SP'},
         'collide_total': sum(o['collide'] for o in out), 'seat_bad': sum(1 for o in out if not (o['seat_empty'] and o['seat_on_bench'])),
         'hang_bad': sum(1 for o in out if not o['hang_rail']),
         'blade_mid_minus_wl': [min(o['blade_mid_z_minus_wl'] for o in out), max(o['blade_mid_z_minus_wl'] for o in out)]}
    if probe:
        print(json.dumps({'probe': probe, **{k: v for k, v in R.items() if k != 'component'},
                          'nonzero': {o['name']: o['collide'] for o in out if o['collide']}}, ensure_ascii=False))
        return
    os.makedirs(os.path.join(HERE, 'masks', 'oars'), exist_ok=True)
    fn = os.path.join(HERE, 'masks', 'oars', 'oar.vox.txt')
    with open(fn, 'w', encoding='utf-8', newline='\n') as f:
        f.write('# 槳（通用部件，draft_oars.py）x,y,z,color —— 0.05 m、框 %s、at 0,0,0\n' % size)
        f.write('\n'.join('%d,%d,%d,%d' % (x, y, z, c) for (x, y, z), c in sorted(cells.items())) + '\n')
    R['component']['sha256'] = hashlib.sha256(open(fn, 'rb').read()).hexdigest()
    meta = lambda o: {'kind': 'oar', 'rowers': O['rowers'], 'side': o['side'], 'stroke_deg': O['stroke_deg'], 'dip_deg': O['dip_deg']}
    with open(os.path.join(HERE, 'oars_placement.json'), 'w', encoding='utf-8', newline='\n') as f:
        json.dump({'note': 'draft_oars.py；at ＝ pivot 的落點；左舷 mirror=y（繞 pivot）', 'work': O['work'], 'scale': sc, 'pivot': piv_l,
                   'oars': [{**o, 'meta': meta(o)} for o in out]}, f, ensure_ascii=False, indent=1)
    with open(os.path.join(HERE, 'verify_oars.json'), 'w', encoding='utf-8', newline='\n') as f:
        json.dump({**R, 'detail': out}, f, ensure_ascii=False, indent=1)
    print(json.dumps(R, ensure_ascii=False, indent=1))


if __name__ == '__main__':
    main()
