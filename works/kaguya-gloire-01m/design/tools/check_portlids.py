# 光榮號 砲門蓋板讀數（TASK-0719；kaguya 自己寫的）—— 把調查時的三支唯讀量法（scratchpad gunport/tools 的 lid_fit.py、port_faces.py、gun_runin.py）收成一支，
#   改成量**組裝件現況**、照 portlids_placement.json 的擺法（14–17 號套了 rz；sculpt 那份開／關碰撞沒套 rz）。
#   現況 ＝ 引擎匯出的組裝件（links=all：船殼、鐵甲帶、channels、甲板子作品裡的砲墊木…）＋ 模型外框（export format=parts；砲、蓋板自己不算 —— 砲照網格的取樣點另外量）。
#   取樣（造船規格 §4.2，同 draft_guns.py）：每格格心＋八個角（0.3／0.7）；「碰撞點」＝ 落在對方佔用格裡的取樣點（蓋板 ↔ 砲兩個方向都算）。
#   每片量：
#   · 開著（模型的樣子）：蓋板 ∩ 船、蓋板 ∩ 推出去的砲、蓋板底比砲高幾格。
#   · 關上（照遊戲的寫法 62_ports.js：繞 hinge-a 格心、沿 hinge-a → hinge-b 照右手定則轉 −close_deg）：蓋板 ∩ 船（佔幾 %）、蓋板 ∩ 縮回 house 格的砲；
#     蓋板中心在鉸鏈下面幾格、往外幾格（往上或往船裡 ⇒ 方向反了）。
#   · 縮回 house 格的砲 ∩ 船；關上不碰砲最少要縮幾格（0.5 一步）。
#   · 反向對照：house 0（砲推出去就關）⇒ 碰；P 舷改用 mirror=y ⇒ 往上關；14–17 號 rz 改 0 ⇒ 看船頭那一端。
#   · 掛上去之後（子作品在的話）：子作品匯出 ↔ lid.txt 逐格逐色、書卡、hinge-a／hinge-b、34 個模型的擺法與 meta ↔ portlids_placement.json、
#     引擎算的鉸鏈點（parts 的 points）與外框 ↔ 這裡算的。
#   輸出：verify_portlids.json。重跑逐位元組相同。
#   用法：python -I -X utf8 tools/check_portlids.py <design> [--base=<組裝件格子的快取.npz>]
import sys, os, json, math, tempfile, subprocess
import numpy as np

sys.stdout.reconfigure(encoding='utf-8')
D = os.path.abspath(sys.argv[1])
sys.path.insert(0, D)
import mio as DB

WORKS = os.path.dirname(os.path.dirname(D))
NX, NY, NZ = 1200, 400, 260
GUN_WORK = 'basecamp-ember-01m-gun-long32'
SKIP_KINDS = ('gun', 'portlid')
OFFS = np.array([[0.5, 0.5, 0.5]] + [[0.3 + 0.4 * (k & 1), 0.3 + 0.4 * ((k >> 1) & 1), 0.3 + 0.4 * ((k >> 2) & 1)] for k in range(8)])
PL = json.load(open(os.path.join(D, 'portlids_placement.json'), encoding='utf-8'))
LID = PL['lid']


def cli(args):
    return subprocess.run(['senate', 'cmd', 'sculpture'] + [a for kv in args for a in ('--arg', kv)], capture_output=True, text=True, encoding='utf-8', errors='replace')


def parts():
    with tempfile.TemporaryDirectory() as d:
        out = os.path.join(d, 'p.json').replace('\\', '/')
        r = cli(['op=export', 'format=parts', 'work=' + DB.ASM, 'out=' + out])
        if r.returncode != 0:
            raise SystemExit(r.stdout[-800:])
        return json.load(open(out, encoding='utf-8'))['models']


def rotz(v, g):
    c, s = round(math.cos(math.radians(g)), 12), round(math.sin(math.radians(g)), 12)
    return np.stack([v[:, 0] * c - v[:, 1] * s, v[:, 0] * s + v[:, 1] * c, v[:, 2]], 1)


def place(Q, m):
    """模型座標 ⇒ 組裝件：at ＋ Rz(rotate) · mirror_y(scale · (Q − pivot))（同 draft_guns.py；這裡只有繞 z 轉）。"""
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
    """A、B 兩組取樣點：A 落在 B 佔用格裡的點數、B 落在 A 佔用格裡的點數。"""
    return int(np.isin(key(np.floor(A).astype(np.int64)), cells_of(B)).sum()), int(np.isin(key(np.floor(B).astype(np.int64)), cells_of(A)).sum())


def main():
    base = next((a.split('=', 1)[1] for a in sys.argv[2:] if a.startswith('--base=')), None)
    # ── 蓋板（子作品自己的座標，開著）──
    L = np.loadtxt(os.path.join(D, LID['file']), delimiter=',', comments='#', dtype=np.int32, ndmin=2, encoding='utf-8')
    lid_samp = (L[:, :3].astype(float)[:, None, :] + OFFS[None]).reshape(-1, 3)
    ha = np.array([LID['anchors']['hinge-a']], float) + 0.5
    hb = np.array([LID['anchors']['hinge-b']], float) + 0.5
    corners = np.array([[x, y, z] for x in (0, LID['size'][0]) for y in (0, LID['size'][1]) for z in (0, LID['size'][2])], float)
    # ── 砲（網格的取樣點；擺法照 deck-lower 的 models.json）──
    G = DB.export_list(GUN_WORK, None)
    gun_samp = (G[:, :3].astype(float)[:, None, :] + OFFS[None]).reshape(-1, 3)
    gan = {a['name']: a['at'] for a in json.load(open(os.path.join(WORKS, GUN_WORK, 'anchors.json'), encoding='utf-8'))['anchors']}
    host_models = json.load(open(os.path.join(WORKS, PL['rows'][0]['host_work'], 'models.json'), encoding='utf-8'))['models']
    gun_by_id = {(m.get('meta') or {}).get('id'): m for m in host_models if (m.get('meta') or {}).get('kind') == 'gun'}
    # ── 現況 ──
    if base and os.path.exists(base):
        occ = np.load(base)['occ']
    else:
        A = DB.export_list(DB.ASM, 'all')
        A = A[A[:, 2] < NZ]
        occ = np.zeros((NX, NY, NZ), bool)
        occ[A[:, 0], A[:, 1], A[:, 2]] = True
        if base:
            np.savez_compressed(base, occ=occ)
    nvox = int(occ.sum())
    PM = parts()
    boxes = [m for m in PM if (m.get('meta') or {}).get('kind') not in SKIP_KINDS]
    for m in boxes:
        b = m['box']
        occ[max(0, int(math.floor(b[0]))):int(math.ceil(b[3])), max(0, int(math.floor(b[1]))):int(math.ceil(b[4])),
            max(0, int(math.floor(b[2]))):min(NZ, int(math.ceil(b[5])))] = True

    def in_ship(P):
        i = np.floor(P).astype(int)
        return int(occ[i[:, 0], i[:, 1], i[:, 2]].sum())

    def closed(m, cd):
        a, b = place(ha, m)[0], place(hb, m)[0]
        return turn(place(lid_samp, m), a, b - a, -cd), a, b

    rows = []
    for r in PL['rows']:
        side = 1 if r['side'] == 'S' else -1
        cd, house = r['meta']['close_deg'], r['meta']['house']
        g = gun_by_id[r['meta']['lid_of']]
        assert g['name'] == r['gun_model'], (r['model'], g['name'])
        gw = place(gun_samp, g)
        mz, br = place(np.array([gan['muzzle']], float) + 0.5, g)[0], place(np.array([gan['breech']], float) + 0.5, g)[0]
        ax = (mz - br) / np.linalg.norm(mz - br)
        assert abs(ax[2]) < 1e-9, (g['name'], '砲軸不水平')
        gin = gw - ax[None] * house
        op = place(lid_samp, r)
        cl, a, b = closed(r, cd)
        # 開著：蓋板底比砲高幾格（蓋板正下方那幾欄的砲）
        foot = set(map(tuple, np.floor(op[:, :2]).astype(int).tolist()))
        gi = np.floor(gw[:, :2]).astype(int)
        under = np.array([tuple(v) in foot for v in gi.tolist()])
        clear = round(float(op[:, 2].min() - gw[under, 2].max()), 2) if under.any() else None
        # 關上：中心在鉸鏈哪裡
        cc = cl.mean(0)
        hc = (a + b) / 2
        # 關上不碰砲最少要縮幾格
        min_pull = None
        for k2 in range(0, 41):
            if sum(cross_hits(cl, gw - ax[None] * (k2 * 0.5))) == 0:
                min_pull = k2 * 0.5
                break
        oh = cross_hits(op, gw)
        ch = cross_hits(cl, gin)
        c0 = cross_hits(cl, gw)
        rec = {'model': r['model'], 'lid_of': r['meta']['lid_of'], 'gun_model': g['name'], 'side': r['side'], 'port': r['port'],
               'at': r['at'], 'rotate': r['rotate'][2], 'close_deg': cd, 'house': house, 'samples': len(op),
               'hinge_a': [round(float(v), 3) for v in a], 'hinge_b': [round(float(v), 3) for v in b],
               'open': {'hits_ship': in_ship(op), 'hits_gun': oh[0] + oh[1], 'clear_above_gun': clear,
                        'box': [round(float(v), 3) for v in np.r_[place(corners, r).min(0), place(corners, r).max(0)]]},
               'closed': {'hits_ship': in_ship(cl), 'ship_pct': round(100.0 * in_ship(cl) / len(cl), 2), 'hits_gun_housed': ch[0] + ch[1],
                          'center_in_ship': bool(in_ship(cc[None])),
                          'center_below_hinge': round(float(hc[2] - cc[2]), 2), 'center_out_of_hinge': round(float((cc[1] - hc[1]) * side), 2)},
               'gun': {'housed_hits_ship': in_ship(gin), 'min_pull_clear_lid': min_pull, 'need_pull': r['gun']['need_pull']},
               'reverse': {'house0_closed_hits_gun': c0[0] + c0[1]}}
        if r['side'] == 'P':                                    # 反向對照：P 舷用 mirror=y（rotate 照 S 舷的 rz 反號）⇒ a→b 還是 +x ⇒ 往上關
            mm = dict(r, rotate=[0, 0, round(r['rotate'][2] - 180, 3)], mirror='y')      # 180 − rz ⇒ 鏡像那一種寫法是 −rz（S 舷 rz 反號）
            clm, am, bm = closed(mm, cd)
            ccm = clm.mean(0)
            rec['reverse']['mirror_y'] = {'center_below_hinge': round(float((am[2] + bm[2]) / 2 - ccm[2]), 2), 'hits_ship': in_ship(clm),
                                          'open_same_cells': bool(np.array_equal(cells_of(place(lid_samp, mm)), cells_of(op)))}
        if r['rotate'][2] not in (0, 180):                      # 反向對照：rz 改 0
            m0 = dict(r, rotate=[0, 0, 0 if side > 0 else 180])
            cl0, _, _ = closed(m0, cd)
            rec['reverse']['rz0'] = {'open_hits_ship': in_ship(place(lid_samp, m0)), 'closed_hits_ship': in_ship(cl0)}
        rows.append(rec)
        print('%s %s open 船 %d 砲 %d（高出 %s）｜closed 船 %d（%.2f%%）砲 %d（house %d；最少 %s）｜中心 下 %.2f 外 %.2f｜反向 house0 %d' % (
            r['model'], r['meta']['lid_of'], rec['open']['hits_ship'], rec['open']['hits_gun'], clear, rec['closed']['hits_ship'], rec['closed']['ship_pct'],
            rec['closed']['hits_gun_housed'], house, min_pull, rec['closed']['center_below_hinge'], rec['closed']['center_out_of_hinge'],
            rec['reverse']['house0_closed_hits_gun']), flush=True)

    # ── 掛上去之後：子作品、固定點、模型 ──
    applied = None
    if cli(['op=work', 'sub=show', 'work=' + LID['work']]).returncode == 0:
        W = DB.export_list(LID['work'], None)
        want = {(x, y, z): c for x, y, z, c in L.tolist()}
        have = {(x, y, z): c for x, y, z, c in W.tolist()}
        card = json.load(open(os.path.join(WORKS, LID['work'], 'work.json'), encoding='utf-8'))
        anc = {x['name']: x['at'] for x in json.load(open(os.path.join(WORKS, LID['work'], 'anchors.json'), encoding='utf-8'))['anchors']}
        hm = {m['name']: m for m in host_models}
        pm = {m['path']: m for m in PM}
        bad, pts_d, box_d = [], 0.0, 0.0
        for r, rec in zip(PL['rows'], rows):
            m = hm.get(r['model'])
            if m is None:
                bad.append(r['model'] + '：沒有')
                continue
            mt = {k: v for k, v in (m.get('meta') or {}).items() if k != 'id'}
            same = (m['work'] == r['source_work'] and m['at'] == r['at'] and m['pivot'] == r['pivot'] and m['rotate'] == r['rotate'] and
                    m['scale'] == [r['scale']] * 3 and m['mirror'] in ('', 'none') and mt == r['meta'] and m.get('enabled', True))
            if not same:
                bad.append(r['model'] + '：擺法或 meta 跟 placement 不一樣')
            p = pm.get('甲板-lower/' + r['model'])
            if p is None:
                bad.append(r['model'] + '：parts 裡沒有')
                continue
            pts_d = max(pts_d, float(np.abs(np.array(p['points']['hinge-a']) - np.array(rec['hinge_a'])).max()),
                        float(np.abs(np.array(p['points']['hinge-b']) - np.array(rec['hinge_b'])).max()))
            box_d = max(box_d, float(np.abs(np.array(p['box']) - np.array(rec['open']['box'])).max()))
        lids_in_host = sorted(m['name'] for m in host_models if (m.get('meta') or {}).get('kind') == 'portlid')
        applied = {'work': LID['work'], 'cells': len(have), 'missing': sum(1 for k in want if k not in have), 'extra': sum(1 for k in have if k not in want),
                   'color_diff': sum(1 for k, v in want.items() if k in have and have[k] != v),
                   'card': {'parent_work': card.get('parent_work'), 'tags': card.get('tags'), 'meters_per_voxel': card.get('meters_per_voxel'),
                            'size': [card.get('size_x'), card.get('size_y'), card.get('size_z')]},
                   'anchors': {k: anc.get(k) for k in sorted(LID['anchors'])}, 'anchors_ok': all(anc.get(k) == v for k, v in LID['anchors'].items()),
                   'models': len(lids_in_host), 'models_bad': bad, 'parts_hinge_max_diff': round(pts_d, 4), 'parts_box_max_diff': round(box_d, 4),
                   'with_id': sum(1 for m in host_models if (m.get('meta') or {}).get('kind') == 'portlid' and 'id' in m['meta'])}
        print('掛上去：子作品 %d 格（缺 %d 多 %d 色差 %d）固定點 %s；模型 %d 個、不一樣 %d；parts 鉸鏈差 %.4f、外框差 %.4f' % (
            applied['cells'], applied['missing'], applied['extra'], applied['color_diff'], applied['anchors_ok'], applied['models'], len(bad), pts_d, box_d))

    tot = lambda f: sum(f(x) for x in rows)
    summary = {'lids': len(rows), 'open_hits_ship': tot(lambda x: x['open']['hits_ship']), 'open_hits_gun': tot(lambda x: x['open']['hits_gun']),
               'closed_hits_ship': tot(lambda x: x['closed']['hits_ship']), 'closed_hits_gun_housed': tot(lambda x: x['closed']['hits_gun_housed']),
               'gun_housed_hits_ship': tot(lambda x: x['gun']['housed_hits_ship']),
               'closed_ship_pct_max': max(x['closed']['ship_pct'] for x in rows),
               'center_below_hinge': [min(x['closed']['center_below_hinge'] for x in rows), max(x['closed']['center_below_hinge'] for x in rows)],
               'center_out_of_hinge': [min(x['closed']['center_out_of_hinge'] for x in rows), max(x['closed']['center_out_of_hinge'] for x in rows)],
               'open_clear_above_gun': [min(x['open']['clear_above_gun'] for x in rows if x['open']['clear_above_gun'] is not None),
                                        max(x['open']['clear_above_gun'] for x in rows if x['open']['clear_above_gun'] is not None)],
               'house_slack': [min(x['house'] - x['gun']['min_pull_clear_lid'] for x in rows), max(x['house'] - x['gun']['min_pull_clear_lid'] for x in rows)],
               'close_deg': [min(x['close_deg'] for x in rows), max(x['close_deg'] for x in rows)], 'house': sorted({x['house'] for x in rows}),
               'reverse_house0_lids_hit': sum(1 for x in rows if x['reverse']['house0_closed_hits_gun'] > 0),
               'reverse_mirror_y_up': sum(1 for x in rows if x['side'] == 'P' and x['reverse']['mirror_y']['center_below_hinge'] < 0),
               'reverse_mirror_y_same_open': sum(1 for x in rows if x['side'] == 'P' and x['reverse']['mirror_y']['open_same_cells'])}
    out = {'note': 'tools/check_portlids.py（TASK-0719）—— 現況 ＝ 組裝件 links=all（%d 格，z < %d）＋ 模型外框 %d（不含 kind=%s）；蓋板 %s（%d 格 × 9 取樣點）' % (
                   nvox, NZ, len(boxes), '／'.join(SKIP_KINDS), LID['file'], len(L)),
           'gun_work': GUN_WORK, 'gun_samples': len(gun_samp), 'rows': rows, 'summary': summary, 'applied': applied}
    with open(os.path.join(D, 'verify_portlids.json'), 'w', encoding='utf-8', newline='\n') as f:
        json.dump(out, f, ensure_ascii=False, indent=1, sort_keys=True)
        f.write('\n')
    print('合計', json.dumps(summary, ensure_ascii=False, sort_keys=True))


if __name__ == '__main__':
    main()
