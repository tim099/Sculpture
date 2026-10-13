# 新圖紙 11 帆（TASK-0529 階段十一）：plan.json 的 sails ⇒ 帆 8 面、帆腳索、風、verify_sails.json。
# 用法：python -I -X utf8 -B draft_sails.py <design 資料夾>
#   · 點、pin、碰撞照 draft_running.Run（stage10 的格＋帆桁模型）；動索已用的 pin 不再用。
#   · 方帆：角 head_p、head_s（帆桁模型的 earing）、clew_s、clew_p（座標）；邊 0 釘住、clew free。
#     course 的 clew 初始 ＝ earing 往中線收 spread、z foot_z；sheet 往後、tack 往前落 pin。topsail 以上 clew 初始 ＝ 下一根帆桁同舷 earing ＋ dz，sheet 綁那個 earing。
#   · 主帆：gaff throat／peak、boom clew／tack 四角都釘，邊 0、2、3 釘住。
#   · 三角帆：tack ＝ stay 下端的固定點、head ＝ stay 上 head_f 的座標、clew ＝ tack 往船尾 foot_ratio × luff、上翹 foot_up_deg；邊 0 釘住、clew free；兩舷 sheet 落 pin。
#   · 檢查：三角帆的 clew 在自己 luff 之下；foot 與 clew 在裡面那一根 stay 的 luff 之上 ≥ stack_margin；
#           平的布（模擬之前）每 0.5 格取樣、離釘住的邊 > 1.2 格的點，落在實心（格或帆桁）的數；帆腳索碰撞同動索（中段要 0）。
#   · 重跑逐位元組相同。
import sys, os, json, math
import numpy as np

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from draft_lines import YC
from draft_running import Run, G


def seg_dist(p, a, b):
    p, a, b = np.asarray(p), np.asarray(a), np.asarray(b); ab = b - a
    t = np.clip((p - a) @ ab / (ab @ ab), 0, 1); return float(np.linalg.norm(p - (a + t * ab)))


def main():
    d = sys.argv[1]
    plan = json.load(open(os.path.join(d, 'plan.json'), encoding='utf-8')); S = plan['sails']
    r = Run(d); r.yard_anchors(); r.mast_anchors(); r.pins(); r.build()
    run_ropes = r.ropes; r.ropes = []
    stays = {x['name']: x for x in json.load(open(os.path.join(d, 'verify_rigging.json'), encoding='utf-8'))['ropes'] if x['kind'] == 'stay'}
    sails = []; checks = {}
    def sail(name, corners, names, world, bind, free, fullness, note):
        sails.append({'name': name, 'corners': corners, 'corner_names': names, 'corners_world': [[round(float(c), 4) for c in w] for w in world],
                      'bind': bind, 'free': free, 'fullness': fullness, 'color': S['color'], 'note': note})
        for n, w in zip(names, world): r.pt['sail:%s/%s' % (name, n)] = list(w)
    # ── 方帆 ──
    C = S['course']
    for nm, spec in S['square'].items():
        P = r.Y[nm]
        hp, hs = r.ymodel(nm, 'earing-P'), r.ymodel(nm, 'earing-S')
        if spec['lower'] is None:
            def clew(e): return [e[0], YC + 0.5 + C['spread'] * (e[1] - YC - 0.5), C['foot_z'] + 0.5]
            cs, cp = clew(r.pt[hs]), clew(r.pt[hp])
            note = 'course：sheet 往後（rail %d）、tack 往前（rail %d）落 pin' % (C['sheet_rail'], C['tack_rail'])
        else:
            ls, lp = r.ymodel(spec['lower'], 'earing-S'), r.ymodel(spec['lower'], 'earing-P')
            cs = [r.pt[ls][0], r.pt[ls][1], r.pt[ls][2] + S['topsail_clew_dz']]; cp = [r.pt[lp][0], r.pt[lp][1], r.pt[lp][2] + S['topsail_clew_dz']]
            note = 'sheet 綁下一根帆桁（%s）同舷的 earing' % spec['lower']
        sail(nm, [hp, hs, G(cs), G(cp)], ['head_p', 'head_s', 'clew_s', 'clew_p'], [r.pt[hp], r.pt[hs], cs, cp], '0', 'clew_s,clew_p', S['fullness']['square'], note)
        for sd, cl in (('S', 'clew_s'), ('P', 'clew_p')):
            a = 'sail:%s/%s' % (nm, cl)
            if spec['lower'] is None:
                for kind, rn, sl in (('sheet', C['sheet_rail'], C['sheet_slack']), ('tack', C['tack_rail'], C['tack_slack'])):
                    # 🩸 v1 從舷外的 clew 直落舷牆裡的 pin ⇒ 穿過舷牆 9／23 個取樣（同 brace 那一題）⇒ 經頂蓋內緣上方的導點
                    pin = r.pick(r.rail(rn, sd), r.pt[a][0]); lead = r.lead(pin); r.pt[G(lead)] = lead
                    grp = 'running/sheets' if kind == 'sheet' else 'running/tacks'
                    r.rope('%s-%s-%s' % (nm, kind, sd), a, G(lead), 'sheet', grp, sl)
                    r.ropes[-1]['thickness'] = S['sheet_thickness']['course']
                    r.rope('%s-%s-lead-%s' % (nm, kind, sd), G(lead), pin, 'fall', grp)
            else:
                r.rope('%s-sheet-%s' % (nm, sd), a, r.ymodel(spec['lower'], 'earing-' + sd), 'sheet', 'running/sheets')
                r.ropes[-1]['thickness'] = S['sheet_thickness']['topsail']
    # ── 主帆 ──
    M = S['mainsail']
    cn = [r.ymodel('main-gaff', M['throat']), r.ymodel('main-gaff', M['peak']), r.ymodel('main-boom', M['clew']), r.ymodel('main-boom', M['tack'])]
    sail('mainsail', cn, ['throat', 'peak', 'clew', 'tack'], [r.pt[c] for c in cn], '0,2,3', '', S['fullness']['mainsail'], 'gaff、boom、桅三條邊釘住，只有 leech 自由')
    # ── 三角帆 ──
    luffs = []
    for H in S['head']:
        st = stays[H['stay']]
        T, Tw, Hw = st['to'], np.array(st['to_world']), np.array(st['from_world'])     # stay：from ＝ 桅上（高）、to ＝ 艏斜桅（低）
        Ll = float(np.linalg.norm(Hw - Tw)); head = Tw + H['head_f'] * (Hw - Tw)
        a = math.radians(H['foot_up_deg']); fl = H['foot_ratio'] * H['head_f'] * Ll
        clew = Tw + np.array([-math.cos(a), 0, math.sin(a)]) * fl
        luff_z = lambda x, A=Tw, B=Hw: A[2] + (A[0] - x) / (A[0] - B[0]) * (B[2] - A[2])
        ck = {'clew_below_own_luff': round(float(luff_z(clew[0]) - clew[2]), 3)}
        if luffs:
            inner = luffs[-1]
            m = min(float(p[2] - inner(p[0])) for p in [Tw + (clew - Tw) * t for t in np.linspace(0, 1, 41)])
            ck['foot_above_inner_luff_min'] = round(m, 3)
            assert m >= S['stack_margin'], (H['name'], '疊到裡面那一面', m)
        assert ck['clew_below_own_luff'] > 10, (H['name'], ck)
        luffs.append(luff_z)
        checks[H['name']] = ck
        sail(H['name'], [T, G(head), G(clew)], ['tack', 'head', 'clew'], [Tw, head, clew], '0', 'clew', S['fullness']['head'], 'luff（邊 0）沿 %s' % H['stay'])
        for sd in ('S', 'P'):
            pin = r.pick(r.rail(H['sheet_rail'], sd), clew[0])
            r.rope('%s-sheet-%s' % (H['name'], sd), 'sail:%s/clew' % H['name'], pin, 'sheet', 'running/sheets')
            r.ropes[-1]['thickness'] = S['sheet_thickness']['head']
    # ── 桅間支索帆（階段十七：main staysail；不跟艏斜桅那一疊比疊放，掛在另一條 stay）──
    for H in S.get('staysails', []):
        st = stays[H['stay']]
        Lw, Hw = np.array(st['to_world']), np.array(st['from_world'])
        # tack 沿 stay 往上 tack_f（v1 綁在前桅腳 aft-low：模擬後 tack 上方的布鼓進往後傾的前桅 21 格）
        Tw = Lw + H.get('tack_f', 0.0) * (Hw - Lw); T = G(Tw) if H.get('tack_f') else st['to']
        Ll = float(np.linalg.norm(Hw - Lw)); head = Lw + H['head_f'] * (Hw - Lw)
        a = math.radians(H['foot_up_deg']); fl = H['foot_ratio'] * (H['head_f'] - H.get('tack_f', 0.0)) * Ll
        clew = Tw + np.array([-math.cos(a), 0, math.sin(a)]) * fl
        luff_z = lambda x, A=Lw, B=Hw: A[2] + (A[0] - x) / (A[0] - B[0]) * (B[2] - A[2])
        ck = {'clew_below_own_luff': round(float(luff_z(clew[0]) - clew[2]), 3), 'clew': [round(float(c), 3) for c in clew], 'head': [round(float(c), 3) for c in head]}
        assert ck['clew_below_own_luff'] > 10, (H['name'], ck)
        checks[H['name']] = ck
        sail(H['name'], [T, G(head), G(clew)], ['tack', 'head', 'clew'], [Tw, head, clew], '0', 'clew', S['fullness']['head'], 'luff（邊 0）沿 %s（桅間支索帆）' % H['stay'])
        for sd in ('S', 'P'):
            pin = r.pick(r.rail(H['sheet_rail'], sd), clew[0])
            r.rope('%s-sheet-%s' % (H['name'], sd), 'sail:%s/clew' % H['name'], pin, 'sheet', 'running/sheets')
            r.ropes[-1]['thickness'] = S['sheet_thickness']['head']
    # ── 平的布碰撞 ──
    world = {k: v > 0 for k, v in r.W.items()}
    cloth = {}
    for sl in sails:
        W = [np.array(w, float) for w in sl['corners_world']]; n = len(W)
        bound = [int(b) for b in sl['bind'].split(',') if b != '']
        pts = []
        if n == 4:
            for u in np.linspace(0, 1, 60):
                for v in np.linspace(0, 1, 60):
                    pts.append((1 - u) * (1 - v) * W[0] + u * (1 - v) * W[1] + u * v * W[2] + (1 - u) * v * W[3])
        else:
            for u in np.linspace(0, 1, 60):
                for v in np.linspace(0, 1 - u, max(2, int(60 * (1 - u)))):
                    pts.append(W[0] + u * (W[1] - W[0]) + v * (W[2] - W[0]))
        hit = {}
        for p in pts:
            if any(seg_dist(p, W[b], W[(b + 1) % n]) < 1.2 for b in bound): continue
            c = tuple(int(math.floor(x)) for x in p)
            for k, v in world.items():
                if v[c]: hit[k] = hit.get(k, 0) + 1
        cloth[sl['name']] = hit
    r.ropes_sails = r.ropes
    mid, land = r.collide()
    V = {'wind': S['wind'], 'seconds': S['seconds'], 'sails': sails, 'ropes': r.ropes, 'head_checks': checks, 'flat_cloth_hits': cloth,
         'rope_hits_mid': mid, 'rope_landing_cells': land, 'pins_used_by_sails': sorted(set(r.used) - set(x for x in r.used if x in {q['to'] for q in run_ropes}))}
    with open(os.path.join(d, 'verify_sails.json'), 'w', encoding='utf-8', newline='\n') as fo:
        json.dump(V, fo, ensure_ascii=False, indent=2, sort_keys=True); fo.write('\n')
    print(json.dumps({k: V[k] for k in ('head_checks', 'flat_cloth_hits', 'rope_hits_mid', 'rope_landing_cells', 'pins_used_by_sails')}, ensure_ascii=False, indent=1))
    print('sails', len(sails), 'ropes', len(r.ropes))


if __name__ == '__main__':
    main()
