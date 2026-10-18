# 蘇士奎哈納號（crest-001，TASK-0697）：本檔抄自光榮號 kaguya-gloire-01m/design/draft_fittings.py（kaguya）—— 下面註解裡的「蘇士奎哈納號」原文是光榮號，改過的地方另外註明
# 蘇士奎哈納號 階段九（TASK-0614）甲板上的零件 —— 抄自三叉戟號 gura-tridente-01m/design/draft_fittings.py（gura）。
#   改：共用讀本船的 mio.py、框 1200；本階段的舵（模型 `舵`）也不算現況；舵輪沒有 poop ⇒ 擺在後桅後面（plan.json fittings）。
# 原檔說明：
#   三叉戟號 階段九（TASK-0562）甲板上的零件：舵輪、羅經櫃、主絞盤、小艇 —— 全部借現成的子作品當外部模型，掛在 甲板-spar
#   來源與 pivot、scale 照餘燼號（basecamp 階段十七、十八、二十）：舵輪 ＝ 憲法號 -wheel（雙舵輪）、羅經櫃／主絞盤／小艇 ＝ 餘燼號那幾件。
#   擺法（同砲、同餘燼號）：轉角 0、x 每 0.5 格試；模型每格格心＋八角不落在「組裝件 links=all ＋ 所有模型外框（砲、帆桁、燈籠）＋ 已擺的零件」；
#   腳下：最底層取樣點正下方要是實心（小艇：龍骨擱在甲板上，著地比例照實記）；保留區：梯子在 spar 那一端（foot／head）前後 6、兩側 4 格。
#   舵輪：中線、poop 前緣（x 228）前面留 0.8 m 給舵手站 ⇒ 從 x start 往船頭第一個；羅經櫃：舵輪外框前緣再往前 gap 格起第一個；
#   主絞盤：中線、四周 clear 格甲板以上淨空，取離 target 最近的；小艇：兩舷 y ＝ 200.5 ± dy（P 舷 mirror=y），兩艘同一個 x，取離 target 最近的。
#   舵索 2 條：鼓輪固定點 → 正下方甲板面（同憲法號／餘燼號）。
#   輸出：fittings_placement.json、verify_fittings.json。用法：python -I -X utf8 draft_fittings.py <design>
import sys, os, json, math, tempfile, subprocess
import numpy as np

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import hull_lines as HL
import layout as LY
import mio as DB

NX, NY, NZ = 1300, 400, 260   # 蘇士奎哈納號改：框 1300
OFFS = np.array([[0.5, 0.5, 0.5]] + [[0.3 + 0.4 * (k & 1), 0.3 + 0.4 * ((k >> 1) & 1), 0.3 + 0.4 * ((k >> 2) & 1)] for k in range(8)])


def parts():
    with tempfile.TemporaryDirectory() as d:
        out = os.path.join(d, 'p.json').replace('\\', '/')
        r = subprocess.run(['senate', 'cmd', 'sculpture', '--arg', 'op=export', '--arg', 'format=parts', '--arg', 'work=' + DB.ASM, '--arg', 'out=' + out],
                           capture_output=True, text=True, encoding='utf-8', errors='replace')
        if r.returncode != 0:
            raise SystemExit(r.stdout[-800:])
        return json.load(open(out, encoding='utf-8'))['models']


def main():
    sys.stdout.reconfigure(encoding='utf-8')
    design = os.path.abspath(sys.argv[1])
    works = os.path.dirname(os.path.dirname(design))
    plan = HL.load_plan(design)
    FB = plan['fittings']
    mags = ','.join(R['link'] for R in plan['magazines']['rooms'].values())
    A = DB.export_list(DB.ASM, 'all', ('hide_links=' + mags,))             # 本階段的彈藥庫不算（在貨艙、碰不到上甲板；藏起來 ⇒ 套用之後重跑讀到的還是同一份）
    A = A[A[:, 2] < NZ]
    occ = np.zeros((NX, NY, NZ), bool)
    occ[A[:, 0], A[:, 1], A[:, 2]] = True
    deck = occ.copy()                                                     # 腳下判斷只看格子（不算模型外框）
    WD = FB['wheel'].get('deck', 'gun')                                    # 蘇士奎哈納號：舵輪、羅經櫃在艉樓甲板（plan.fittings.wheel.deck）
    own = {'甲板-%s/%s' % (WD if n in ('舵輪', '羅經櫃') else 'gun', n) for n in ('舵輪', '羅經櫃', '主絞盤', '小艇-S', '小艇-P')}
    PM = [m for m in parts() if m['path'] not in own and m['path'] != '舵' and not m['path'].startswith('彈藥庫-')]                      # 本階段自己掛的不算（套用之後重跑讀到的還是同一份）
    for m in PM:
        b = m['box']
        occ[max(0, int(math.floor(b[0]))):int(math.ceil(b[3])), max(0, int(math.floor(b[1]))):int(math.ceil(b[4])),
            max(0, int(math.floor(b[2]))):min(NZ, int(math.ceil(b[5])))] = True
    reserved = np.zeros((NX, NY), bool)
    LP = json.load(open(os.path.join(design, 'ladder_points.json'), encoding='utf-8'))
    res_list = []
    for nm, L in sorted(LP.items()):
        for end, lvl in (('head', L['up']), ('foot', L['lo'])):
            if lvl in ('gun', WD):   # 蘇士奎哈納號改：露天甲板 ＝ gun
                x, y, _ = L['points'][end]
                reserved[x - 6:x + 7, y - 4:y + 5] = True
                res_list.append([nm, end, x, y])

    src = {}
    for k, T in FB['types'].items():
        C = DB.export_list(T['work'], None)
        an = json.load(open(os.path.join(works, T['work'], 'anchors.json'), encoding='utf-8'))['anchors'] if os.path.exists(
            os.path.join(works, T['work'], 'anchors.json')) else []
        bot = C[C[:, 2] == C[:, 2].min()]
        src[k] = {'samp': (C[:, :3].astype(float)[:, None, :] + OFFS[None]).reshape(-1, 3),
                  'bot': np.array([[x + 0.5, y + 0.5, 0.5] for x, y, _ in bot[:, :3]]), 'z0': int(C[:, 2].min()),
                  'an': {a['name']: a['at'] for a in an}, 'cells': len(C), 'size': [int(v) for v in C[:, :3].max(0) + 1]}

    def world(k, Q, at, mir):
        T = FB['types'][k]
        q = (Q - np.array(T['pivot'], float)) * T['scale']
        if mir:
            q[:, 1] = -q[:, 1]
        return q + np.asarray(at, float)

    def test(k, at, mir, clear=0):
        W = world(k, src[k]['samp'], at, mir)
        i = np.floor(W).astype(int)
        if (occ[i[:, 0], i[:, 1], i[:, 2]]).any():
            return None
        if reserved[i[:, 0], i[:, 1]].any():
            return None
        b = np.floor(world(k, src[k]['bot'], at, mir)).astype(int)
        sup = int(deck[b[:, 0], b[:, 1], b[:, 2] - 1].sum())
        lo, hi = W.min(0), W.max(0)
        if clear:
            x0, x1 = int(lo[0]) - clear, int(math.ceil(hi[0])) + clear
            y0, y1 = int(lo[1]) - clear, int(math.ceil(hi[1])) + clear
            z0 = int(at[2])
            if occ[x0:x1, y0:y1, z0:int(math.ceil(hi[2]))].any() or reserved[x0:x1, y0:y1].any():
                return None
        return {'support': [sup, len(b)], 'box': [round(float(v), 3) for v in list(lo) + list(hi)]}

    def commit(k, at, mir):
        i = np.floor(world(k, src[k]['samp'], at, mir)).astype(int)
        occ[i[:, 0], i[:, 1], i[:, 2]] = True

    def zdeck(x, lvl='gun'):
        return float(LY.deck_z(plan, lvl, x)) + 1.0

    rows, log = [], {}
    yc = plan['space']['yc'] + 0.5
    # 舵輪
    W_ = FB['wheel']
    got = None
    for kx in range(int((W_['x_to'] - W_['x_from']) / 0.5) + 1):
        x = W_['x_from'] + kx * 0.5
        at = [x, yc, zdeck(x, WD)]
        r = test('wheel', at, False)
        if r and r['support'][0] == r['support'][1]:
            got = (at, r)
            break
    assert got, '舵輪擺不下'
    commit('wheel', got[0], False)
    rows.append({'model': '舵輪', 'type': 'wheel', 'host': '甲板-' + WD, 'at': got[0], 'mirror': 'none', **got[1]})
    wheel_front = got[1]['box'][3]
    # 羅經櫃
    B_ = FB['binnacle']
    got = None
    for kx in range(200):
        x = math.ceil(wheel_front + B_['gap']) + kx * 0.5
        at = [x, yc, zdeck(x, WD)]
        r = test('binnacle', at, False)
        if r and r['support'][0] == r['support'][1]:
            got = (at, r)
            break
    assert got, '羅經櫃擺不下'
    commit('binnacle', got[0], False)
    rows.append({'model': '羅經櫃', 'type': 'binnacle', 'host': '甲板-' + WD, 'at': got[0], 'mirror': 'none', **got[1]})
    # 主絞盤
    C_ = FB['capstan']
    cands, why = [], {'no': 0}
    for kx in range(int((C_['x_to'] - C_['x_from']) / 0.5) + 1):
        x = C_['x_from'] + kx * 0.5
        at = [x, yc, zdeck(x)]
        r = test('capstan', at, False, clear=C_['clear'])
        if r and r['support'][0] == r['support'][1]:
            cands.append((abs(x - C_['target']), at, r))
        else:
            why['no'] += 1
    assert cands, '主絞盤擺不下'
    _, at, r = min(cands, key=lambda c: (c[0], c[1][0]))
    commit('capstan', at, False)
    rows.append({'model': '主絞盤', 'type': 'capstan', 'host': '甲板-gun', 'at': at, 'mirror': 'none', 'candidates': len(cands), **r})
    log['capstan_range'] = [min(c[1][0] for c in cands), max(c[1][0] for c in cands)]
    # 小艇（兩舷同一個 x）
    S_ = FB['boats']
    cands = []
    for kx in range(int((S_['x_to'] - S_['x_from']) / 0.5) + 1):
        x = S_['x_from'] + kx * 0.5
        z = zdeck(x)
        rs = []
        for sgn, mir in ((1, False), (-1, True)):
            at = [x, yc + sgn * S_['dy'], z]
            rr = test('boat', at, mir)
            if not rr:
                break
            rs.append((at, mir, rr))
        if len(rs) == 2 and min(r_[2]['support'][0] for r_ in rs) > 0:
            cands.append((abs(x - S_['target']), x, rs))
    assert cands, '小艇擺不下'
    _, xb, rs = min(cands, key=lambda c: (c[0], c[1]))
    for (at, mir, rr), nm in zip(rs, ('小艇-S', '小艇-P')):
        commit('boat', at, mir)
        rows.append({'model': nm, 'type': 'boat', 'host': '甲板-gun', 'at': at, 'mirror': 'y' if mir else 'none', **rr})
    log['boat_range'] = [min(c[1] for c in cands), max(c[1] for c in cands)]
    # 舵索
    wr = rows[0]
    ropes = []
    for nm in ('drum-rope-a', 'drum-rope-b'):
        p = world('wheel', np.array([src['wheel']['an'][nm]], float) + 0.5, wr['at'], False)[0]
        ropes.append({'name': 'wheel-' + nm.replace('drum-', ''), 'from': 'model:甲板-%s/舵輪/' % WD + nm,
                      'to': '%.1f,%.1f,%.1f' % (p[0], p[1], zdeck(p[0], WD)), 'color': '#a08458', 'thickness': 0.35, 'slack': 1, 'group': 'steering'})
    for r in rows:
        T = FB['types'][r['type']]
        r.update({'work': T['work'], 'pivot': T['pivot'], 'scale': T['scale'], 'meta': T['meta']})
        r['at'] = [round(v, 3) for v in r['at']]
    out = {'note': 'draft_fittings.py（階段九）—— 現況 ＝ 組裝件 links=all（%d 格）＋ 模型外框 %d' % (len(A), len(PM)),
           'types': {k: {'work': FB['types'][k]['work'], 'cells': v['cells'], 'size': v['size']} for k, v in src.items()},
           'rows': rows, 'ropes': ropes, 'reserved_ladder_ends': res_list, 'ranges': log}
    with open(os.path.join(design, 'verify_fittings.json'), 'w', encoding='utf-8', newline='\n') as f:
        json.dump(out, f, ensure_ascii=False, indent=1, sort_keys=True)
        f.write('\n')
    for r in rows:
        print(r['model'], 'at', r['at'], r['mirror'], 'support', r['support'], 'box', r['box'])
    print('舵索', [(x['name'], x['to']) for x in ropes], '範圍', log)


if __name__ == '__main__':
    main()
