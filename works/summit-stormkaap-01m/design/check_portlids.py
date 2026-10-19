# 砲門蓋板讀數（TASK-0736）—— 照光榮號 kaguya-gloire-01m/design/tools/check_portlids.py（kaguya，TASK-0719）改；夜隼號、風暴角號共用（兩份檔逐位元組相同，船從 portlids_placement.json 讀）。
#   跟光榮號不一樣：蓋板好幾件、砲好幾種、掛在好幾層甲板；船尾的蓋板鉸鏈沿 y（照擺法算，不寫死軸）。
#   現況 ＝ 引擎匯出的組裝件（links=all）＋ 模型外框（export format=parts；砲、蓋板自己不算 —— 砲照網格的取樣點另外量）。
#   取樣（造船規格 §4.2）：每格格心＋八個角（0.3／0.7）；「碰撞點」＝ 落在對方佔用格裡的取樣點（兩個方向都算）。
#   每片量：開著 ∩ 船、開著 ∩ 推出去的砲、蓋板底比砲高幾格；關上（繞 hinge-a 格心、沿 hinge-a → hinge-b 照右手定則轉 −close_deg，同 Blockside 62_ports.js）∩ 船（%）、
#     關上 ∩ 縮回 house 格的砲；關上中心在鉸鏈下面幾格、往外幾格；縮回的砲 ∩ 船；關上不碰砲最少要縮幾格；反向對照 house 0、P 舷改 mirror=y。
#   掛上去之後（子作品在的話）：子作品 ↔ 清單逐格逐色、書卡、固定點、每個模型的擺法與 meta ↔ placement、引擎算的鉸鏈點與外框 ↔ 這裡算的。
#   輸出：verify_portlids.json。重跑逐位元組相同（同一份現況）。
#   用法：python -I -X utf8 -B check_portlids.py <design> [--asm=<組裝件 links=all 匯出清單>] [--parts=<format=parts 匯出>]（不給 ⇒ 現場匯出）
import sys, os, json, math, tempfile, subprocess
import numpy as np

sys.stdout.reconfigure(encoding='utf-8')
D = os.path.abspath(sys.argv[1])
WORKS = os.path.dirname(os.path.dirname(D))
OPT = dict(a[2:].split('=', 1) for a in sys.argv[2:] if a.startswith('--'))
SKIP_KINDS = ('gun', 'portlid')
OFFS = np.array([[0.5, 0.5, 0.5]] + [[0.3 + 0.4 * (k & 1), 0.3 + 0.4 * ((k >> 1) & 1), 0.3 + 0.4 * ((k >> 2) & 1)] for k in range(8)])
PL = json.load(open(os.path.join(D, 'portlids_placement.json'), encoding='utf-8'))
HULL = next(iter(PL['lids'].values()))['parent_work']
ASM = HULL + '-assembly'
CARD = json.load(open(os.path.join(WORKS, ASM, 'work.json'), encoding='utf-8'))
NX, NY, NZ = CARD['size_x'], CARD['size_y'], CARD['size_z']
OUT = {'S': np.array([0, 1, 0.]), 'P': np.array([0, -1, 0.]), 'A': np.array([-1, 0, 0.])}


def cli(args):
    return subprocess.run(['senate', 'cmd', 'sculpture'] + [a for kv in args for a in ('--arg', kv)], capture_output=True, text=True, encoding='utf-8', errors='replace')


def export_list(work, links=None):
    with tempfile.TemporaryDirectory() as d:
        out = os.path.join(d, 'a.txt').replace('\\', '/')
        r = cli(['op=export', 'format=list', 'work=' + work, 'out=' + out] + (['links=' + links] if links else []))
        if r.returncode != 0:
            raise SystemExit('匯出失敗：' + (r.stdout + r.stderr)[-800:])
        return np.loadtxt(out, delimiter=',', comments='#', dtype=np.int32, ndmin=2, encoding='utf-8')


def parts():
    if 'parts' in OPT:
        return json.load(open(OPT['parts'], encoding='utf-8'))['models']
    with tempfile.TemporaryDirectory() as d:
        out = os.path.join(d, 'p.json').replace('\\', '/')
        r = cli(['op=export', 'format=parts', 'work=' + ASM, 'out=' + out])
        if r.returncode != 0:
            raise SystemExit(r.stdout[-800:])
        return json.load(open(out, encoding='utf-8'))['models']


def rotz(v, g):
    c, s = round(math.cos(math.radians(g)), 12), round(math.sin(math.radians(g)), 12)
    return np.stack([v[:, 0] * c - v[:, 1] * s, v[:, 0] * s + v[:, 1] * c, v[:, 2]], 1)


def place(Q, m):
    """模型座標 ⇒ 組裝件：at ＋ Rz(rotate) · mirror_y(scale · (Q − pivot))（這裡只有繞 z 轉）。"""
    assert m['rotate'][0] == 0 and m['rotate'][1] == 0, m
    sc = m['scale'] if isinstance(m['scale'], list) else [m['scale']] * 3
    q = (np.asarray(Q, float) - np.array(m['pivot'], float)) * np.array(sc, float)
    if m['mirror'] == 'y':
        q[:, 1] = -q[:, 1]
    return rotz(q, m['rotate'][2]) + np.array(m['at'], float)


def turn(P, c, k, deg):
    """繞過 c、方向 k 的軸照右手定則轉 deg 度（Rodrigues）。"""
    k = k / np.linalg.norm(k)
    t = math.radians(deg)
    v = P - c
    return c + v * math.cos(t) + np.cross(k, v) * math.sin(t) + np.outer(v @ k, k) * (1 - math.cos(t))


def key(i):
    return (i[:, 0].astype(np.int64) * 1000 + i[:, 1]) * 1000 + i[:, 2]


def cells_of(P):
    return np.unique(key(np.floor(P).astype(np.int64)))


def cross_hits(A, B):
    return int(np.isin(key(np.floor(A).astype(np.int64)), cells_of(B)).sum()), int(np.isin(key(np.floor(B).astype(np.int64)), cells_of(A)).sum())


def main():
    # ── 蓋板（每件子作品自己的座標，開著）──
    LS = {}
    for w, L in PL['lids'].items():
        A = np.loadtxt(os.path.join(D, L['file']), delimiter=',', comments='#', dtype=np.int32, ndmin=2, encoding='utf-8')
        LS[w] = {'list': A, 'samp': (A[:, :3].astype(float)[:, None, :] + OFFS[None]).reshape(-1, 3),
                 'ha': np.array([L['anchors']['hinge-a']], float) + 0.5, 'hb': np.array([L['anchors']['hinge-b']], float) + 0.5,
                 'corners': np.array([[x, y, z] for x in (0, L['size'][0]) for y in (0, L['size'][1]) for z in (0, L['size'][2])], float)}
    # ── 砲（各層甲板 models.json；網格取樣點照砲的來源作品）──
    host_models = {h: json.load(open(os.path.join(WORKS, h, 'models.json'), encoding='utf-8'))['models'] for h in sorted({r['host_work'] for r in PL['rows']})}
    gun_by_id = {(m.get('meta') or {}).get('id'): m for ms in host_models.values() for m in ms if (m.get('meta') or {}).get('kind') == 'gun'}
    GS, GA = {}, {}
    for w in sorted({gun_by_id[r['meta']['lid_of']]['work'] for r in PL['rows']}):
        G = export_list(w)
        GS[w] = (G[:, :3].astype(float)[:, None, :] + OFFS[None]).reshape(-1, 3)
        GA[w] = {a['name']: a['at'] for a in json.load(open(os.path.join(WORKS, w, 'anchors.json'), encoding='utf-8'))['anchors']}
    # ── 現況 ──
    A = np.loadtxt(OPT['asm'], delimiter=',', comments='#', dtype=np.int32, ndmin=2, encoding='utf-8') if 'asm' in OPT else export_list(ASM, 'all')
    A = A[A[:, 2] < NZ]
    occ = np.zeros((NX, NY, NZ), bool)
    occ[A[:, 0], A[:, 1], A[:, 2]] = True
    nvox = int(occ.sum())
    PM = parts()
    boxes = [m for m in PM if (m.get('meta') or {}).get('kind') not in SKIP_KINDS]
    for m in boxes:
        b = m['box']
        occ[max(0, int(math.floor(b[0]))):int(math.ceil(b[3])), max(0, int(math.floor(b[1]))):int(math.ceil(b[4])),
            max(0, int(math.floor(b[2]))):min(NZ, int(math.ceil(b[5])))] = True

    def in_ship(P):
        i = np.floor(P).astype(int)
        ok = (i[:, 0] >= 0) & (i[:, 0] < NX) & (i[:, 1] >= 0) & (i[:, 1] < NY) & (i[:, 2] >= 0) & (i[:, 2] < NZ)
        return int(occ[i[ok, 0], i[ok, 1], i[ok, 2]].sum())

    def closed(m, cd):
        S = LS[m['source_work']]
        a, b = place(S['ha'], m)[0], place(S['hb'], m)[0]
        return turn(place(S['samp'], m), a, b - a, -cd), a, b

    rows = []
    for r in PL['rows']:
        S = LS[r['source_work']]
        u = OUT[r['side']]
        cd, house = r['meta']['close_deg'], r['meta']['house']
        g = gun_by_id[r['meta']['lid_of']]
        assert g['name'] == r['gun_model'], (r['model'], g['name'])
        gw = place(GS[g['work']], g)
        mz = place(np.array([GA[g['work']]['muzzle']], float) + 0.5, g)[0]
        br = place(np.array([GA[g['work']]['breech']], float) + 0.5, g)[0]
        ax = (mz - br) / np.linalg.norm(mz - br)
        assert abs(ax[2]) < 1e-9, (g['name'], '砲軸不水平')
        gin = gw - ax[None] * house
        op = place(S['samp'], r)
        cl, a, b = closed(r, cd)
        # 開著：蓋板底比砲高幾格（蓋板正下方那幾欄的砲）
        foot = set(map(tuple, np.floor(op[:, :2]).astype(int).tolist()))
        gi = np.floor(gw[:, :2]).astype(int)
        under = np.array([tuple(v) in foot for v in gi.tolist()])
        clear = round(float(op[:, 2].min() - gw[under, 2].max()), 2) if under.any() else None
        cc = cl.mean(0)
        hc = (a + b) / 2
        min_pull = None
        for k2 in range(0, 41):
            if sum(cross_hits(cl, gw - ax[None] * (k2 * 0.5))) == 0:
                min_pull = k2 * 0.5
                break
        oh, ch, c0 = cross_hits(op, gw), cross_hits(cl, gin), cross_hits(cl, gw)
        oc = place(S['corners'], r)
        rec = {'model': r['model'], 'host_work': r['host_work'], 'lid_of': r['meta']['lid_of'], 'gun_model': g['name'], 'side': r['side'], 'source_work': r['source_work'],
               'at': r['at'], 'rotate': r['rotate'][2], 'close_deg': cd, 'house': house, 'samples': len(op),
               'hinge_a': [round(float(v), 3) for v in a], 'hinge_b': [round(float(v), 3) for v in b],
               'open': {'hits_ship': in_ship(op), 'hits_gun': oh[0] + oh[1], 'clear_above_gun': clear,
                        'box': [round(float(v), 3) for v in np.r_[oc.min(0), oc.max(0)]]},
               'closed': {'hits_ship': in_ship(cl), 'ship_pct': round(100.0 * in_ship(cl) / len(cl), 2), 'hits_gun_housed': ch[0] + ch[1],
                          'center_in_ship': bool(in_ship(cc[None])),
                          'center_below_hinge': round(float(hc[2] - cc[2]), 2), 'center_out_of_hinge': round(float((cc - hc) @ u), 2)},
               'gun': {'housed_hits_ship': in_ship(gin), 'min_pull_clear_lid': min_pull, 'need_pull': r['gun']['need_pull']},
               'reverse': {'house0_closed_hits_gun': c0[0] + c0[1]}}
        if r['side'] == 'P':                                    # 反向對照：P 舷用 mirror=y（rotate 照 S 舷的 rz）⇒ a→b 還是往船頭 ⇒ 往上關
            mm = dict(r, rotate=[0, 0, round(r['rotate'][2] - 180, 3)], mirror='y')
            clm, am, bm = closed(mm, cd)
            rec['reverse']['mirror_y'] = {'center_below_hinge': round(float((am[2] + bm[2]) / 2 - clm.mean(0)[2]), 2), 'hits_ship': in_ship(clm),
                                          'open_same_cells': bool(np.array_equal(cells_of(place(S['samp'], mm)), cells_of(op)))}
        rows.append(rec)
        print('%s %s open 船 %d 砲 %d（高出 %s）｜closed 船 %d（%.2f%%）砲 %d（house %d；最少 %s）｜中心 下 %.2f 外 %.2f｜縮回的砲碰船 %d｜反向 house0 %d' % (
            r['model'], r['meta']['lid_of'], rec['open']['hits_ship'], rec['open']['hits_gun'], clear, rec['closed']['hits_ship'], rec['closed']['ship_pct'],
            rec['closed']['hits_gun_housed'], house, min_pull, rec['closed']['center_below_hinge'], rec['closed']['center_out_of_hinge'],
            rec['gun']['housed_hits_ship'], rec['reverse']['house0_closed_hits_gun']), flush=True)

    # ── 掛上去之後：子作品、固定點、模型 ──
    applied = {}
    link_of = {l['work']: l['name'] for l in json.load(open(os.path.join(WORKS, ASM, 'links.json'), encoding='utf-8'))['links']}
    pm = {m['path']: m for m in PM}
    for w, L in sorted(PL['lids'].items()):
        if cli(['op=work', 'sub=show', 'work=' + w]).returncode != 0:
            continue
        Wl = export_list(w)
        want = {(x, y, z): c for x, y, z, c in LS[w]['list'].tolist()}
        have = {(x, y, z): c for x, y, z, c in Wl.tolist()}
        card = json.load(open(os.path.join(WORKS, w, 'work.json'), encoding='utf-8'))
        anc = {x['name']: x['at'] for x in json.load(open(os.path.join(WORKS, w, 'anchors.json'), encoding='utf-8'))['anchors']}
        applied[w] = {'cells': len(have), 'missing': sum(1 for k in want if k not in have), 'extra': sum(1 for k in have if k not in want),
                      'color_diff': sum(1 for k, v in want.items() if k in have and have[k] != v),
                      'card': {'parent_work': card.get('parent_work'), 'tags': card.get('tags'), 'meters_per_voxel': card.get('meters_per_voxel'),
                               'size': [card.get('size_x'), card.get('size_y'), card.get('size_z')]},
                      'anchors': {k: anc.get(k) for k in sorted(L['anchors'])}, 'anchors_ok': all(anc.get(k) == v for k, v in L['anchors'].items())}
    if applied:
        bad, pts_d, box_d = [], 0.0, 0.0
        for r, rec in zip(PL['rows'], rows):
            m = next((x for x in host_models[r['host_work']] if x['name'] == r['model']), None)
            if m is None:
                bad.append(r['model'] + '@' + r['host_work'] + '：沒有')
                continue
            mt = {k: v for k, v in (m.get('meta') or {}).items() if k != 'id'}
            same = (m['work'] == r['source_work'] and m['at'] == r['at'] and m['pivot'] == r['pivot'] and m['rotate'] == r['rotate'] and
                    m['scale'] == [r['scale']] * 3 and m['mirror'] in ('', 'none') and mt == r['meta'] and m.get('enabled', True))
            if not same:
                bad.append(r['model'] + '@' + r['host_work'] + '：擺法或 meta 跟 placement 不一樣')
            p = pm.get(link_of[r['host_work']] + '/' + r['model'])
            if p is None:
                bad.append(r['model'] + '@' + r['host_work'] + '：parts 裡沒有')
                continue
            pts_d = max(pts_d, float(np.abs(np.array(p['points']['hinge-a']) - np.array(rec['hinge_a'])).max()),
                        float(np.abs(np.array(p['points']['hinge-b']) - np.array(rec['hinge_b'])).max()))
            box_d = max(box_d, float(np.abs(np.array(p['box']) - np.array(rec['open']['box'])).max()))
        lids_in = sum(1 for ms in host_models.values() for m in ms if (m.get('meta') or {}).get('kind') == 'portlid')
        applied['models'] = {'count': lids_in, 'bad': bad, 'parts_hinge_max_diff': round(pts_d, 4), 'parts_box_max_diff': round(box_d, 4)}
        print('掛上去：', json.dumps(applied, ensure_ascii=False, sort_keys=True))

    tot = lambda f: sum(f(x) for x in rows)
    rng = lambda f, xs: [min(f(x) for x in xs), max(f(x) for x in xs)] if xs else None
    clr = [x for x in rows if x['open']['clear_above_gun'] is not None]
    summary = {'lids': len(rows), 'open_hits_ship': tot(lambda x: x['open']['hits_ship']), 'open_hits_gun': tot(lambda x: x['open']['hits_gun']),
               'closed_hits_ship': tot(lambda x: x['closed']['hits_ship']), 'closed_hits_gun_housed': tot(lambda x: x['closed']['hits_gun_housed']),
               'gun_housed_hits_ship': tot(lambda x: x['gun']['housed_hits_ship']),
               'closed_ship_pct_max': max(x['closed']['ship_pct'] for x in rows), 'closed_center_in_ship': tot(lambda x: int(x['closed']['center_in_ship'])),
               'center_below_hinge': rng(lambda x: x['closed']['center_below_hinge'], rows), 'center_out_of_hinge': rng(lambda x: x['closed']['center_out_of_hinge'], rows),
               'open_clear_above_gun': rng(lambda x: x['open']['clear_above_gun'], clr),
               'house_slack': rng(lambda x: x['house'] - x['gun']['min_pull_clear_lid'], [x for x in rows if x['gun']['min_pull_clear_lid'] is not None]),
               'min_pull_none': sum(1 for x in rows if x['gun']['min_pull_clear_lid'] is None),
               'close_deg': rng(lambda x: x['close_deg'], rows), 'house': sorted({x['house'] for x in rows}),
               'reverse_house0_lids_hit': sum(1 for x in rows if x['reverse']['house0_closed_hits_gun'] > 0),
               'reverse_mirror_y_up': sum(1 for x in rows if x['side'] == 'P' and x['reverse']['mirror_y']['center_below_hinge'] < 0),
               'reverse_mirror_y_same_open': sum(1 for x in rows if x['side'] == 'P' and x['reverse']['mirror_y']['open_same_cells']),
               'P': sum(1 for x in rows if x['side'] == 'P')}
    out = {'note': 'check_portlids.py（TASK-0736）—— 現況 ＝ %s links=all（%d 格，z < %d）＋ 模型外框 %d（不含 kind=%s）；蓋板 %s' % (
                   ASM, nvox, NZ, len(boxes), '／'.join(SKIP_KINDS), {w: L['file'] for w, L in sorted(PL['lids'].items())}),
           'gun_samples': {w: len(v) for w, v in sorted(GS.items())}, 'rows': rows, 'summary': summary, 'applied': applied or None}
    with open(os.path.join(D, 'verify_portlids.json'), 'w', encoding='utf-8', newline='\n') as f:
        json.dump(out, f, ensure_ascii=False, indent=1, sort_keys=True)
        f.write('\n')
    print('合計', json.dumps(summary, ensure_ascii=False, sort_keys=True))


if __name__ == '__main__':
    main()
