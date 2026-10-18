# 新圖紙 07：槳（造船規格 §9.10、§9.10.1、§9.10.2）⇒ 兩件槳元件（下層／上層，通用部件 0.05 m）、100 支的擺法 oars_placement.json、讀數 verify_oars.json
#   用法：python -I -X utf8 -B draft_oars.py [--probe=drop=S-L05] [--probe=sink=S-U05:3]
#   · 雙層（dromon）：下層每舷 25 支從外板的槳口伸出去（槳手坐在甲板下、站艙底走道）；上層每舷 25 支從舷牆的槳口伸出去（槳手站主甲板），錯半個位。
#     槳口是 draft_hull.py 開的洞（plan.json oars）。
#   · 槳元件：沿 +y（y 0 ＝ 槳柄端 → 槳葉末端），畫在「掃到一半」的姿勢（垂直於船身、往外往下 angle_deg）；固定點 pivot（槳靠在槳口的那一格）、blade、seat。
#     右舷原樣、左舷 mirror=y（繞 pivot 翻）。上層照舷弧每支補一個傾角（rotate x）⇒ 槳葉中心落在水線（下層的槳口高度一樣、不用補）。
#   · 讀數：模型格心＋八角不落在船的實心、也不落在其他模型裡；槳葉中心離水面；seat 那一格腳下實心、頭上 14 格空（遊戲 standZ）；槳口旁 8 格內有船殼（遊戲的掛點）；兩舷支數一樣。
#   · --probe：反向對照（只印讀數，不寫檔）。drop=S-L05 ⇒ 少一支；sink=S-U05:3 ⇒ 那一支往下沉 3 格（要報碰撞）。
import os, sys, json, math, hashlib
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import numpy as np
import dro

D = dro.D
P = dro.PLAN
O = P['oars']
YC, YM = dro.YC, dro.YM
WL = float(P['waterline_z'])                  # 水面（z 0 ＝ 龍骨底、吃水 1.1 m）
M5 = 0.05
VH = json.load(open(os.path.join(D, 'verify_hull.json'), encoding='utf-8')); ZAIR = VH['zair']
VU = json.load(open(os.path.join(D, 'verify_upper.json'), encoding='utf-8'))
VR = json.load(open(os.path.join(D, 'verify_rig.json'), encoding='utf-8'))
VM = json.load(open(os.path.join(D, 'verify_models.json'), encoding='utf-8'))
HEAD = 14                                      # 遊戲 40_crew.js standZ：站的那一格＋往上 13 格要空


def rot(rx, ry, rz):
    a, b, c = (math.radians(v) for v in (rx, ry, rz))
    Rx = np.array([[1, 0, 0], [0, math.cos(a), -math.sin(a)], [0, math.sin(a), math.cos(a)]])
    Ry = np.array([[math.cos(b), 0, math.sin(b)], [0, 1, 0], [-math.sin(b), 0, math.cos(b)]])
    Rz = np.array([[math.cos(c), -math.sin(c), 0], [math.sin(c), math.cos(c), 0], [0, 0, 1]])
    return Rz @ Ry @ Rx


def xform(pts, m):                             # 跟 placements.py、引擎同一套
    s = float(m['scale']) if not isinstance(m['scale'], (list, tuple)) else np.asarray(m['scale'], float)
    q = np.asarray(pts, float) - np.asarray(m['pivot'], float)
    if 'y' in m.get('mirror', ''):
        q[:, 1] = -q[:, 1]
    if 'x' in m.get('mirror', ''):
        q[:, 0] = -q[:, 0]
    return (rot(*m['rotate']) @ (q * s).T).T + np.asarray(m['at'], float)


def load(path):
    return np.loadtxt(os.path.join(D, path), delimiter=',', comments='#', dtype=int, ndmin=2)


CORN = np.array([[dx, dy, dz] for dx in (0, 1) for dy in (0, 1) for dz in (0, 1)], float)


def world_cells(a, m):
    c = a[:, :3].astype(float)
    w = xform(np.vstack([c + 0.5] + [c + CORN[i] for i in range(8)]), m)
    return np.floor(w).astype(int), len(c)


def oar_cells(S):
    """一件槳元件：回傳 (格 dict, size, 固定點, zc, yi, L)。x 中心 3.5；y 0 ＝ 槳柄端；z 照斜率。"""
    yi = int(round(S['inboard_m'] / M5))
    yo = int(round(S['outboard_m'] / M5))
    L = yi + yo
    tn = math.tan(math.radians(S['angle_deg']))
    zt = math.ceil(yo * tn + S['blade_w_m'] / M5 / 2 + 3) + S.get('z_pad', 0)   # z_pad：框往下多留幾格（下層的 seat 在槳座下 1.1 m，固定點要落在框裡）
    zc = lambda y: zt - (y - yi) * tn
    size = [7, L + 1, int(math.ceil(zc(0) + 4))]
    d0, d1 = S['loom_d_m']
    yb = L - int(round(S['blade_m'] / M5))
    cells = {}
    for y in range(0, L + 1):
        c = zc(y + 0.5)
        if y < yb:
            r = (d0 + (d1 - d0) * min(1.0, y / max(1, yb))) / M5 / 2
            for x in range(size[0]):
                for z in range(size[2]):
                    if (x + 0.5 - 3.5) ** 2 + (z + 0.5 - c) ** 2 <= max(r, 0.9) ** 2:
                        cells[(x, y, z)] = P['colors']['beam'] if y < 6 else P['colors']['castle']   # 槳柄端（手握的地方）深一點
        else:                                          # 槳葉：一格厚（x 3）、寬 blade_w、往外漸寬一點
            hw = S['blade_w_m'] / M5 / 2 * (0.8 + 0.2 * (y - yb) / max(1, L - yb))
            for z in range(size[2]):
                if abs(z + 0.5 - c) <= hw:
                    cells[(3, y, z)] = P['colors']['castle']
    piv = (3, yi, int(math.floor(zc(yi + 0.5))))
    tip = (3, L, int(math.floor(zc(L + 0.5))))
    assert piv in cells and tip in cells, (piv, tip)
    bmid = (3, L - int(round(S['blade_m'] / M5 / 2)), int(math.floor(zc(L - S['blade_m'] / M5 / 2))))
    return cells, size, {'pivot': list(piv), 'blade': list(tip)}, bmid


def main():
    probe = {}
    for s in sys.argv[1:]:
        if s.startswith('--probe='):
            k, v = s[len('--probe='):].split('=')
            probe[k] = v
    # 船的實心（船殼含槳口、甲板、上層結構、桅）＋其他模型佔的格
    SOLID = np.zeros((dro.NX, dro.NY, dro.NZ), bool)
    for f in ['lists/hull.txt', 'lists/deck_main.txt', 'lists/deck_hold.txt'] + [VU[k]['file'] for k in ('forecastle', 'castles', 'fittings', 'magazine', 'ladders')] + [VR['masts'][k]['file'] for k in VR['masts']]:
        a = load(f); SOLID[a[:, 0], a[:, 1], a[:, 2]] = True
    HULL = np.zeros_like(SOLID); a = load('lists/hull.txt'); HULL[a[:, 0], a[:, 1], a[:, 2]] = True
    MOD = np.zeros_like(SOLID)
    for m in VM:
        ij, _ = world_cells(load(m['file']), m)
        ok = (ij >= 0).all(1) & (ij[:, 0] < dro.NX) & (ij[:, 1] < dro.NY) & (ij[:, 2] < dro.NZ)
        MOD[ij[ok, 0], ij[ok, 1], ij[ok, 2]] = True
    BLK = SOLID | MOD
    comps = {}
    for bank in ('lower', 'upper'):
        cells, size, anc, bmid = oar_cells(O[bank])
        src = np.array([[x, y, z, c] for (x, y, z), c in sorted(cells.items())])
        comps[bank] = dict(cells=cells, size=size, anc=anc, bmid=bmid, src=src, piv=[anc['pivot'][0] + 0.5, anc['pivot'][1] + 0.5, anc['pivot'][2] + 0.5])
    out = []
    for j in range(O['per_side']):
        for bank in ('lower', 'upper'):
            S, Cm = O[bank], comps[bank]
            x0 = O['x_first'] + j * O['dx'] + (O['upper_offset'] if bank == 'upper' else 0)
            z0 = O['z_lower'] if bank == 'lower' else ZAIR[x0] + O['upper_dz']
            hp = O['h'] if bank == 'lower' else O.get('upper_h', O['h'])
            for side, sg in (('S', 1), ('P', -1)):
                name = 'oar-%s-%s%02d' % (side, 'L' if bank == 'lower' else 'U', j + 1)
                if probe.get('drop') == name[4:] or name[6:] in O.get('skip', []):
                    continue
                # 槳口的洞：x0..x0+w−1、z0..z0+h−1；pivot ＝ 洞的中心、y 在殼的最外兩格中間（槳靠在槳口下緣的槳栓上）
                ys = [y for y in (range(YC + 1, dro.NY) if sg > 0 else range(0, YC))
                      if any(HULL[x, y, z] for x in range(x0 - 1, x0 + O['w'] + 1) for z in range(z0 - 1, z0 + hp + 1))]
                yo = max(ys) if sg > 0 else min(ys)
                at = [x0 + O['w'] / 2, float(yo) if sg > 0 else float(yo + 1), z0 + O['pivot_dz']]   # 槳靠在槳口下緣上（槳柄往裡往上翹、洞的上半是讓它穿過去的）
                sk = probe.get('sink', '')
                if sk.startswith(name[4:] + ':'):
                    at[2] -= float(sk.split(':')[1])
                # 傾角：槳葉中心落在水面（下層的槳口高度一樣 ⇒ 差不到半度就不補；上層照舷弧補）。元件裡 pivot→槳葉中心的實際角度（格子取整過）
                dy_, dz_ = Cm['bmid'][1] + 0.5 - Cm['piv'][1], Cm['piv'][2] - (Cm['bmid'][2] + 0.5)
                Lb = math.hypot(dy_, dz_) * 0.5                                    # 世界格（元件 0.05 m、scale 0.5）
                need = math.degrees(math.asin(min(1.0, (at[2] - WL) / Lb)))
                dlt = round(need - math.degrees(math.atan2(dz_, dy_)), 1)
                if bank == 'lower' and abs(dlt) < 0.5:
                    dlt = 0.0
                m = dict(at=at, pivot=Cm['piv'], scale=0.5, rotate=[-dlt * sg, 0, 0], mirror='' if sg > 0 else 'y')
                ij, n = world_cells(Cm['src'], m)
                ok = (ij >= 0).all(1) & (ij[:, 0] < dro.NX) & (ij[:, 1] < dro.NY) & (ij[:, 2] < dro.NZ)
                hit = np.zeros(len(ij), bool); hit[ok] = BLK[ij[ok, 0], ij[ok, 1], ij[ok, 2]]
                cell_hit = hit.reshape(9, n).any(0)
                bad = np.unique(ij[hit], axis=0)[:4].tolist()
                bm = xform(np.array([[Cm['bmid'][0] + 0.5, Cm['bmid'][1] + 0.5, Cm['bmid'][2] + 0.5]]), m)[0]
                # 槳手：槳口往船裡 seat_in_m；下層站艙底走道（hold z＋1）、上層站主甲板
                ys_ = int(math.floor(at[1] - sg * S['seat_in_m'] / 0.1 + (0 if sg > 0 else -1)))
                xs_ = x0
                zs_ = P['deck_hold']['z'] + 1 if bank == 'lower' else ZAIR[xs_]
                foot = bool(SOLID[xs_, ys_, zs_ - 1])
                headc = [z for z in range(zs_, zs_ + HEAD) if SOLID[xs_, ys_, z]]
                hang = bool(HULL[int(at[0]) - 8:int(at[0]) + 9, int(at[1]) - 8:int(at[1]) + 9, int(at[2]) - 8:int(at[2]) + 9].any())
                out.append({'name': name, 'bank': bank, 'side': side, 'port_x': x0, 'port_z': z0, 'at': [round(v, 3) for v in at], 'tilt_deg': dlt,
                            'rotate': m['rotate'], 'mirror': m['mirror'], 'collide': int(cell_hit.sum()), 'collide_sample': bad,
                            'blade_mid_minus_water': round(bm[2] - WL, 2), 'blade_mid_y_off': round(abs(bm[1] - YM), 1),
                            'seat_world': [xs_, ys_, zs_], 'seat_foot': foot, 'seat_head_blocked': headc[:3], 'hang_hull': hang})
    # 元件座標裡的 seat（照右舷第一支換算）
    for bank, Cm in comps.items():
        o0 = next(o for o in out if o['side'] == 'S' and o['bank'] == bank)
        m = dict(at=o0['at'], pivot=Cm['piv'], scale=0.5, rotate=o0['rotate'], mirror='')
        sw = np.array(o0['seat_world'], float) + 0.5
        loc = (rot(*m['rotate']).T @ (sw - np.array(m['at']))) / 0.5 + np.array(Cm['piv'])
        Cm['anc']['seat'] = np.floor(loc).astype(int).tolist()
    # 照遊戲排一次槳手（40_crew.js oarCrew → standNear／standZ／blocked）：seat 固定點換到世界 ⇒ 半徑 6 格內、z 照 seat 與 pivot 上下找；
    # 要避的模型 ＝ 沒標 block=false 的（槳、門不避；火藥桶沒有取用點也不避），外框外擴 1 格、腳底往下 3 格到外框頂。⚠ 砲班先排、佔掉的格這裡沒算（匯入檢查才算）。
    BB = [m['bbox'] for m in VM if (m['meta'] or {}).get('kind') not in ('oar', 'door', 'powder')]

    def blocked(x, y, z):
        return any(math.floor(b[0][0]) - 1 <= x <= math.ceil(b[1][0]) + 1 and math.floor(b[0][1]) - 1 <= y <= math.ceil(b[1][1]) + 1 and b[0][2] - 3 <= z <= b[1][2] for b in BB)

    def stand_z(x, y, z0, z1):
        for z in range(z1, z0 - 1, -1):
            if 0 < z < dro.NZ - HEAD and SOLID[x, y, z - 1] and not SOLID[x, y, z:z + HEAD].any():
                return z
        return -1
    taken = set()
    for o in out:
        Cm = comps[o['bank']]
        m = dict(at=o['at'], pivot=Cm['piv'], scale=0.5, rotate=o['rotate'], mirror=o['mirror'])
        s0 = xform(np.array([np.array(Cm['anc']['seat'], float) + 0.5]), m)[0]
        z0, z1 = int(math.floor(min(s0[2], o['at'][2]))) - 14, int(math.floor(max(s0[2], o['at'][2]))) + 2
        o['rower'] = None
        for r in range(7):
            for dy in range(-r, r + 1):
                for dx in range(-r, r + 1):
                    if o['rower'] or max(abs(dx), abs(dy)) != r:
                        continue
                    x, y = int(math.floor(s0[0])) + dx, int(math.floor(s0[1])) + dy
                    if (x, y) in taken:
                        continue
                    z = stand_z(x, y, z0, z1)
                    if z >= 0 and not blocked(x, y, z):
                        taken.add((x, y)); o['rower'] = [x, y, z]
    R = {'components': {b: {'size': c['size'], 'cells': len(c['cells']), 'anchors': c['anc'], 'length_m': round((c['size'][1] - 1) * M5, 2),
                            'angle_deg': O[b]['angle_deg']} for b, c in comps.items()},
         'oars': len(out), 'per_side': {s: sum(1 for o in out if o['side'] == s) for s in 'SP'},
         'per_bank': {b: sum(1 for o in out if o['bank'] == b) for b in ('lower', 'upper')},
         'collide_total': sum(o['collide'] for o in out),
         'seat_cell_bad': [o['name'] for o in out if not o['seat_foot'] or o['seat_head_blocked']],   # 設計的那一格（遊戲還會在旁邊 6 格內找）
         'rowers_game': [sum(1 for o in out if o['rower']), len(out)],
         'rowers_where': {b: sorted(set(o['rower'][2] for o in out if o['rower'] and o['bank'] == b)) for b in ('lower', 'upper')},
         'rower_missing': [o['name'] for o in out if not o['rower']],
         'hang_bad': [o['name'] for o in out if not o['hang_hull']],
         'blade_mid_minus_water': {b: [min(o['blade_mid_minus_water'] for o in out if o['bank'] == b), max(o['blade_mid_minus_water'] for o in out if o['bank'] == b)] for b in ('lower', 'upper')},
         'tilt_deg': [min(o['tilt_deg'] for o in out), max(o['tilt_deg'] for o in out)],
         'rowers': sum(O[o['bank']]['rowers'] for o in out)}
    nz = {o['name']: [o['collide'], o['collide_sample']] for o in out if o['collide']}
    if probe:
        print(json.dumps({'probe': probe, **{k: v for k, v in R.items() if k != 'components'}, 'nonzero': nz}, ensure_ascii=False))
        return
    for b, c in comps.items():
        fn = os.path.join(D, 'lists', 'oar_%s.txt' % b)
        dro.write_list(fn, c['cells'], '持火號 槳（%s；通用部件 0.05 m；draft_oars.py）' % b)
        R['components'][b]['file'] = 'lists/oar_%s.txt' % b
        R['components'][b]['sha256'] = hashlib.sha256(open(fn, 'rb').read()).hexdigest()
    meta = lambda o: {'kind': 'oar', 'rowers': O[o['bank']]['rowers'], 'side': o['side'], 'stroke_deg': O[o['bank']]['stroke_deg'], 'dip_deg': O[o['bank']]['dip_deg'], 'bank': o['bank']}
    json.dump({'note': 'draft_oars.py；at ＝ pivot 的落點；左舷 mirror=y（繞 pivot）；上層 rotate x ＝ 照舷弧補的傾角', 'cfg_base': O['cfg_base'],
               'pivot': {b: c['piv'] for b, c in comps.items()}, 'oars': [{**o, 'meta': meta(o)} for o in out]},
              open(os.path.join(D, 'oars_placement.json'), 'w', encoding='utf-8', newline='\n'), ensure_ascii=False, indent=1)
    json.dump({**R, 'nonzero': nz, 'detail': out}, open(os.path.join(D, 'verify_oars.json'), 'w', encoding='utf-8', newline='\n'), ensure_ascii=False, indent=1)
    print(json.dumps({**R, 'nonzero': nz}, ensure_ascii=False, indent=1))


if __name__ == '__main__':
    main()
