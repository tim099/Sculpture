# 階段七讀數（落格之後）：讀引擎匯出的東西 —— 十件帆桁子作品、三根桅與船首斜桅的 export list、組裝件 export list、組裝件 export parts。
# 用法：python -I -X utf8 -B check_yards.py <design 資料夾> <匯出資料夾>
#   匯出資料夾裡：yard-<帆桁>.list.txt、mast-<桅>.list.txt、bowsprit.list.txt、assembly.list.txt、parts.json
#   從夜隼號 check_yards.py（TASK-0529 階段八）改：gaff／boom 換成 lateen；多了斜桅下兩根。
#   · 結果帳：每件子作品 export vs masks/yards 清單（缺、多、顏色不同）。
#   · 固定點：引擎轉過的點（parts 的 models[].points，組裝件座標）vs draft 用 rot() 算的 anchors_expect —— 兩條路算同一個旋轉。
#   · 從 plan 取的探針（不讀 draft 的結果）：桅的高度 ＝ 引擎匯出的桅最低一格（桅腳，check_masts 量過 ＝ 支撐上一格）＋ plan 的長度。
#       方帆桁 —— 中線那一排的高度 vs z_ref＋z_off；y 的長度 vs voet × voet_to_grid（取奇數）；背面離那一節桅最前格的空隙（應 0）。
#       spritsail —— x vs 斜桅從腳往外 s_frac 處；頂面離斜桅最低格的空隙 vs gap；sprit topsail —— 高度 vs 斜桅頂桅頂 ＋ z_off、空隙 0。
#       lateen —— 引擎點 pivot→arm-A 的仰角 vs angle_deg；底面離組裝件那一欄底下最高那一格 vs head_clear（前端一點＋沿整根軸線取樣的最小值）；長度 arm-A→arm-F。
#   · 反向對照：子作品整份 x 偏 3 ⇒ 空隙報 3（sprit 那根 x 報 3）；z 偏 3 ⇒ 高度報 3；arm-A 繞 pivot 多轉 3° ⇒ 仰角報 3；前端抬 3 ⇒ 淨空報 3。
import sys, os, json, math
import numpy as np

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from draft_yards import odd, rot


def load(p):
    return np.loadtxt(p, delimiter=',', dtype=int, comments='#', ndmin=2)


def heights(plan, m, heel):
    M = {x['name']: x for x in plan['masts']['list']}[m]
    hounds = heel + M['L_low'] - M['head']
    tm_top = hounds + M['L_top']
    if M.get('L_tg'):
        cross = tm_top - M['head_top'] - 1; truck = tm_top - M['head_top'] + M['L_tg'] - 1
    else:
        cross = None; truck = tm_top - 1
    return {'platform': hounds - 1, 'crosstrees': cross, 'truck': truck}


def sq_probe(YC, P, cells, spar, zplan, Lp, dx=0, dz=0):
    w = cells[:, :3] + np.asarray(P['origin']) + np.array([dx, 0, dz])
    c = w[w[:, 1] == YC]
    zc = float(c[:, 2].mean())
    L = int(w[:, 1].max() - w[:, 1].min() + 1)
    rows = np.unique(c[:, 2])
    mrow = spar[(spar[:, 1] == YC) & np.isin(spar[:, 2], rows)]
    gap = int(c[:, 0].min()) - int(mrow[:, 0].max()) - 1
    return {'z': round(zc, 3), 'z_plan': zplan, 'z_err': round(zc - zplan, 3), 'length': L, 'length_plan': Lp, 'gap_to_spar': gap}


def elev_aft(a, b):
    """a → b，b 在 a 的船尾側（−x）：往上為正。"""
    return math.degrees(math.atan2(b[2] - a[2], a[0] - b[0]))


def main():
    d, ex = sys.argv[1], sys.argv[2]
    plan = json.load(open(os.path.join(d, 'plan.json'), encoding='utf-8'))
    Yp = plan['yards']; k = Yp['voet_to_grid']; YC = plan['frame']['YC']
    V = json.load(open(os.path.join(d, 'verify_yards.json'), encoding='utf-8'))
    parts = json.load(open(os.path.join(ex, 'parts.json'), encoding='utf-8'))
    spar = {m: load(os.path.join(ex, 'mast-%s.list.txt' % m)) for m in ('mizzen', 'main', 'fore')}
    spar['bowsprit'] = load(os.path.join(ex, 'bowsprit.list.txt'))
    asm = load(os.path.join(ex, 'assembly.list.txt'))
    PL = {p['member']: p for p in V['placements']}
    R = {'ledger': {}, 'square': {}, 'sprit': {}, 'reverse': {}}
    cells = {nm: load(os.path.join(ex, 'yard-%s.list.txt' % nm)) for nm in PL}
    # 結果帳
    for nm, P in PL.items():
        want = {tuple(r[:3]): r[3] for r in load(os.path.join(d, P['file']))}
        got = {tuple(r[:3]): r[3] for r in cells[nm]}
        R['ledger'][nm] = {'list': len(want), 'work': len(got), 'missing': sum(1 for q in want if q not in got),
                           'extra': sum(1 for q in got if q not in want), 'color_diff': sum(1 for q in want if q in got and got[q] != want[q])}
    # 固定點：引擎 vs rot()
    eng = {m['name'][len('yard-'):]: m for m in parts['models'] if m['name'].startswith('yard-')}
    dev = []
    for nm, E in V['anchors_expect'].items():
        pts = dict(eng[nm]['points']) if isinstance(eng[nm]['points'], list) else eng[nm]['points']
        assert set(pts) == set(E), (nm, set(pts) ^ set(E))
        dev += [math.dist(pts[a], q) for a, q in E.items()]
    R['anchors'] = {'compared': len(dev), 'max_dev': round(max(dev), 6), 'yard_models': len(eng), 'models_ok': sum(1 for m in eng.values() if m['state'] == 'ok'),
                    'meta_kind_yard': sum(1 for m in eng.values() if m['meta'].get('kind') == 'yard'),
                    'meta_sail_matches_plan': sum(1 for nm, m in eng.items() if m['meta'].get('sail') == Yp['sail_of'][nm])}
    # 方帆桁（桅上）
    for Y in Yp['square']:
        nm = Y['name']; m = Y['mast']
        H = heights(plan, m, int(spar[m][:, 2].min()))
        zp = H[Y['z_ref']] + Y['z_off']; Lp = odd(Y['voet'] * k)
        args = (YC, PL[nm], cells[nm], spar[m], zp, Lp)
        R['square'][nm] = b0 = sq_probe(*args)
        a = sq_probe(*args, dx=3); b = sq_probe(*args, dz=3)
        R['reverse'][nm] = [a['gap_to_spar'] - b0['gap_to_spar'], round(b['z'] - b0['z'], 3)]
    # 斜桅下兩根
    B = plan['masts']['bowsprit']; S = {y['name']: y for y in Yp['sprit']}; th = math.radians(B['steeve'])
    tipz = B['heel'][1] + math.sin(th) * B['L']
    Y = S['sprit-topsail']
    zp = int(tipz) + B['L_sprit_top'] - 1 + Y['z_off']
    args = (YC, PL['sprit-topsail'], cells['sprit-topsail'], spar['bowsprit'], zp, odd(Y['voet'] * k))
    R['sprit']['sprit-topsail'] = b0 = sq_probe(*args)
    R['reverse']['sprit-topsail'] = [sq_probe(*args, dx=3)['gap_to_spar'] - b0['gap_to_spar'], round(sq_probe(*args, dz=3)['z'] - b0['z'], 3)]
    Y = S['spritsail']

    def sprit_probe(dx=0, dz=0):
        w = cells['spritsail'][:, :3] + np.asarray(PL['spritsail']['origin']) + np.array([dx, 0, dz])
        c = w[w[:, 1] == YC]
        xc = float(c[:, 0].mean()) + 0.5
        xs = np.unique(c[:, 0]); bs = spar['bowsprit']
        low = int(bs[(bs[:, 1] == YC) & np.isin(bs[:, 0], xs)][:, 2].min())
        return {'x': round(xc, 3), 'x_plan': round(B['heel'][0] + math.cos(th) * Y['s_frac'] * B['L'], 3), 'top_gap_to_bowsprit': low - int(c[:, 2].max()) - 1,
                'gap_plan': Y['gap'], 'length': int(w[:, 1].max() - w[:, 1].min() + 1), 'length_plan': odd(Y['voet'] * k)}
    R['sprit']['spritsail'] = s0 = sprit_probe()
    R['reverse']['spritsail'] = [round(sprit_probe(dx=3)['x'] - s0['x'], 3), -(sprit_probe(dz=3)['top_gap_to_bowsprit'] - s0['top_gap_to_bowsprit'])]
    # lateen
    Lt = Yp['lateen']; lp = dict(eng['mizzen-lateen']['points']) if isinstance(eng['mizzen-lateen']['points'], list) else eng['mizzen-lateen']['points']
    r0 = {x['name']: x for x in plan['masts']['list']}['mizzen']['d_low'] / 2 * Lt['d_over_mast']
    rend = max(r0 * Yp['taper']['k'][-1], Yp['r_min'])
    col = {}
    for x, y, z, c in asm:
        col.setdefault((int(x), int(y)), []).append(int(z))

    def clear(pf, lift=0):
        x, y = int(math.floor(pf[0])), int(math.floor(pf[1]))
        zb = pf[2] + lift - rend
        below = [z for z in col.get((x, y), []) if z + 1 <= zb]
        return round(zb - (max(below) + 1), 3) if below else None
    def clear_axis(lift=0):
        # 沿引擎的 arm-F → arm-A 軸線每 0.5 格取樣：半徑照 plan 的錐度（中點 r0、兩端 r0 × taper 末端），底面離那一欄底下最高那一格
        A, F_ = np.array(lp['arm-A']), np.array(lp['arm-F']); Ln = float(np.linalg.norm(A - F_)); best = None
        for i in range(int(Ln * 2) + 1):
            t = i / (Ln * 2); q = F_ + (A - F_) * t
            sf = abs(t - 0.5) * 2
            r = max(r0 * float(np.interp(sf, Yp['taper']['s'], Yp['taper']['k'])), Yp['r_min'])
            x, y = int(math.floor(q[0])), int(math.floor(q[1])); zb = q[2] + lift - r
            below = [z for z in col.get((x, y), []) if z + 1 <= zb]
            if below:
                g = zb - (max(below) + 1)
                if best is None or g < best[0]: best = (round(float(g), 3), x, y, int(max(below)))
        return best
    el = elev_aft(lp['pivot'], lp['arm-A'])
    R['lateen'] = {'elev_deg': round(el, 4), 'plan': Lt['angle_deg'], 'fore_end_clear': clear(lp['arm-F']), 'min_clear_along_axis': clear_axis(), 'clear_plan': Lt['head_clear'],
                   'length_axis': round(math.dist(lp['arm-A'], lp['arm-F']) + 1, 3), 'length_plan': odd(Lt['voet'] * k),
                   'side_y': lp['pivot'][1], 'side_plan': YC + Lt['side_dy'] + 0.5}
    R['reverse']['lateen'] = [round(elev_aft(lp['pivot'], rot(lp['arm-A'], lp['pivot'], 3, 0)) - el, 4), round(clear(lp['arm-F'], 3) - R['lateen']['fore_end_clear'], 3),
                             round(clear_axis(3)[0] - R['lateen']['min_clear_along_axis'][0], 3)]
    flat = [v for vs in R['reverse'].values() for v in vs]
    R['reverse_all_report_3'] = all(abs(v - 3) < 0.05 for v in flat); R['reverse_n'] = len(flat)
    R['assembly_voxels'] = int(len(asm))
    with open(os.path.join(d, 'verify_yards_post.json'), 'w', encoding='utf-8', newline='\n') as fo:
        json.dump(R, fo, ensure_ascii=False, indent=2, sort_keys=True); fo.write('\n')
    print(json.dumps(R, ensure_ascii=False, indent=1))


if __name__ == '__main__':
    main()
