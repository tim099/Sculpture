# 利劍號 新圖紙 06（TASK-0022 步驟 8）：索具、帆、旗 ⇒ rig_plan.json（固定點、繩、帆、meta）、rig_meta.tsv、verify_rigging.json、sheet06_rigging_v1.png
#   出處：蠍子號 claude-galiot-01m/design/draft_rigging.py（拉丁帆 tack ＝ 帆桁 fore、head ＝ 前緣長那一點最近的 jackstay、clew 照三邊解、bind 邊 0；
#         帆自己的繩標 kind=sheet／tack＋sail；長旗 kind=flag flag=pennant、不寫 mast；靜索只拉在帆的另一舷）——改成三根桅三面帆。
#   改的地方：沒有划手座 ⇒ 繩腳照 plan 的 x 取那一欄舷頂最外一格；tack 綁的地方照 plan（主甲板板、長喙上緣）；
#            固定點可以在船殼、主甲板、長喙、船尾平台、三根桅。
#   用法：python -I -X utf8 draft_rigging.py [--probe=clew_z_main=-60] [--probe=shroud_side=-1] [--probe=leech_ratio_mizzen=0.7] [--probe=hound_on_face=1]
#   · 讀前面每一步的設計清單與 yards_lateen.json／yards_placement.json；不讀作品 ⇒ 落格之後重跑一樣。
#   · 讀數：每個固定點在它那件的實心格上；繩兩端；平面帆（還沒模擬的三角形）離船（含三根桅、別根帆桁）最近幾格；繩有沒有穿過帆；繩的直線穿過幾格實心；帆裝三段。
import sys, os, json, math, hashlib
import numpy as np
from scipy.spatial import cKDTree
from PIL import Image, ImageDraw, ImageFont

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import lines as HL

sys.stdout.reconfigure(encoding='utf-8')
TAR, HEMP, SAIL, RED = '#2b2620', '#a08458', '#f2ead8', '#7a1a14'
V = HL.V
ORDER = ['mizzen', 'main', 'fore']
NAMES = {'mizzen': '後桅', 'main': '主桅', 'fore': '前桅'}


OWN_R = 2       # 繩的端點那一件、端點 2 格以內的格不算穿（v1 5 格：靜索綁在桅面那一格，往下 3–4 格都在桅裡；v2 綁在桅面外）
SURF_R = 3      # 繩面離實心的讀數：端點 3 格以內不算
GAFF_SET = 2   # Ship_Rigging §9.1：sail=gaff 預設戰鬥帆才張（2）；set 只在跟預設不同時寫


def load(fn):
    a = np.loadtxt(os.path.join(HERE, fn), delimiter=',', comments='#', dtype=np.int32, ndmin=2)
    return {(int(x), int(y), int(z)): int(c) for x, y, z, c in a}


def main():
    probe = dict(a[len('--probe='):].split('=') for a in sys.argv[1:] if a.startswith('--probe='))
    plan = HL.load_plan(HERE)
    YC = int(plan['space']['yc'])
    RG = {k: V(v) for k, v in plan['rigging'].items() if k != 'src'}
    hull = load('masks/hull/hull_01.vox.txt')
    hull.update(load('masks/step6/hull_paint.vox.txt'))
    deck = load('masks/decks/main.vox.txt')
    beak = load('masks/deco/beak.vox.txt')
    platform = load('masks/deco/platform.vox.txt')
    others = {}
    for fn in ('masks/decks/hold.vox.txt', 'masks/decks/quarter.vox.txt', 'masks/ladders/main.vox.txt', 'masks/ladders/quarter.vox.txt',
               'masks/deco/glass.vox.txt'):
        others.update(load(fn))
    awning = load('masks/deco/awning.vox.txt')   # deco 模型（可隱藏）：帆碰到篷不算穿船，但要報（蠍子號 check_sails_sim 同一套）
    masts = {m: load('masks/masts/%s.vox.txt' % m) for m in ORDER}
    LAT = json.load(open(os.path.join(HERE, 'yards_lateen.json'), encoding='utf-8'))
    PL = {p['mast']: p for p in json.load(open(os.path.join(HERE, 'yards_placement.json'), encoding='utf-8'))}
    WORKS = {'hull': (hull, '船殼'), 'deck-main': (deck, '甲板-main'), 'beak': (beak, '長喙'), 'platform': (platform, '船尾平台')}
    for m in ORDER:
        WORKS['mast-' + m] = (masts[m], NAMES[m])
    YARD = {m: 'model:%s/%s' % (NAMES[m], PL[m]['name']) for m in ORDER}

    def yard_world(m, an):
        a = LAT[m]['anchors'][an]
        p = PL[m]
        return [a[i] + 0.5 - p['pivot'][i] + p['at'][i] for i in range(3)]

    def yard_cells(m):
        p = PL[m]
        out = set()
        for (x, y, z) in load('masks/yards/lateen-%s.vox.txt' % m):
            out.add((int(round(x - p['pivot'][0] + p['at'][0])), int(round(y - p['pivot'][1] + p['at'][1])), int(round(z - p['pivot'][2] + p['at'][2]))))
        return out
    ycells = {m: yard_cells(m) for m in ORDER}

    def rail_cell(x, side):
        ys = [k for k in hull if k[0] == x and (k[1] - YC) * side > 2]
        zt = max(k[2] for k in ys)
        y = max((k[1] for k in ys if k[2] == zt), key=lambda v: (v - YC) * side)
        return (x, y, zt)

    def mast_face(m, z, side):
        cs = [k for k in masts[m] if k[2] == z]
        y = max((k[1] for k in cs), key=lambda v: (v - YC) * side)
        xs = sorted(k[0] for k in cs if k[1] == y)
        return (xs[len(xs) // 2], y + (0 if probe.get('hound_on_face') else side), z)                    # 桅面外那一格（空格）：v1 綁在桅面那一格 ⇒ 前桅靜索幾乎貼著往前傾的桅往下，前 5 格在桅裡（verifier8）

    def top_cell(cells, x, y, zmax=10 ** 6):
        zs = [k[2] for k in cells if k[0] == x and k[1] == y and k[2] < zmax]
        return (x, y, max(zs))

    anchors, ropes, sails = [], [], []

    def anchor(work, name, at, beside=False):
        cells, link = WORKS[work]
        if beside:                                                      # Ship_Rigging §6：hounds ＝ 桅側那一格（空格，緊貼著那一件的實心）
            assert tuple(at) not in cells and any((at[0] + dx, at[1] + dy, at[2] + dz) in cells for dx, dy, dz in
                                                  ((1, 0, 0), (-1, 0, 0), (0, 1, 0), (0, -1, 0), (0, 0, 1), (0, 0, -1))), (work, name, at)
        else:
            assert tuple(at) in cells, (work, name, at)
        anchors.append({'work': work, 'name': name, 'at': list(at)})
        return '%s/%s' % (link, name)

    def rope(name, a, b, slack, th, color, group, meta=None):
        ropes.append({'name': name, 'from': a, 'to': b, 'slack': slack, 'thickness': th, 'color': color, 'group': group, 'meta': meta or {}})

    YS = {m: V(plan['rig_build']['yard'])[m].get('side', -1) for m in ORDER}    # 帆桁掛在桅的哪一舷
    geo = {}
    for m in ORDER:
        RM = RG[m]
        side = int(probe.get('shroud_side', -YS[m]))                           # 靜索拉在帆的另一舷
        sd = 'S' if side > 0 else 'P'
        sv = dict(RG['sail_shape'], **RM.get('sail_shape', {}))
        sv.update({k[:-len(m) - 1]: float(v) for k, v in probe.items() if k in ('leech_ratio_' + m, 'foot_ratio_' + m)})
        tack_w = yard_world(m, 'fore')
        Lc = LAT[m]['len_m'] * 10
        want = Lc * sv['luff_frac']
        js = {n: (int(n.split('-')[1]) * 8.0) for n in LAT[m]['anchors'] if n.startswith('jackstay-')}
        head_an = min(js, key=lambda n: (abs(js[n] + 1.0 - want), n))
        head_w = yard_world(m, head_an)
        luff = math.dist((tack_w[0], tack_w[2]), (head_w[0], head_w[2]))
        leech, foot = luff * sv['leech_ratio'], luff * sv['foot_ratio']
        a_t = math.acos((foot ** 2 + luff ** 2 - leech ** 2) / (2 * foot * luff))
        ang = math.atan2(head_w[2] - tack_w[2], head_w[0] - tack_w[0]) + a_t
        clew = [tack_w[0] + foot * math.cos(ang), PL[m]['at'][1], tack_w[2] + foot * math.sin(ang) + float(probe.get('clew_z_' + m, 0))]
        nm = '%s-lateen' % m
        sails.append({'name': nm, 'corners': ['%s/fore' % YARD[m], '%s/%s' % (YARD[m], head_an), '%.1f,%.1f,%.1f' % tuple(clew)],
                      'corner_names': ['tack', 'head', 'clew'], 'bind': [0], 'free': ['clew'], 'color': SAIL, 'fullness': RG['sail_fullness'],
                      'meta': {'kind': 'sail', 'mast': m, 'sail': 'gaff'} | ({'set': str(RM['set'])} if RM['set'] != GAFF_SET else {})})
        geo[m] = {'head_anchor': head_an, 'luff': luff, 'leech': leech, 'foot': foot, 'clew': clew}
        # 靜索：帆的另一舷；上端在桅那一面、calcet 底下；下端舷頂最外一格
        top_z = max(k[2] for k in masts[m]) + 1
        h = anchor('mast-' + m, 'hound-' + sd, mast_face(m, top_z - RM['hound_below_top'], side), beside=not probe.get('hound_on_face'))
        for i, x in enumerate(RM['shroud_feet_x'], 1):
            rope('%s-shroud-%s%d' % (m, sd, i), h, anchor('hull', 'shroud-%s-%s%d' % (m, sd, i), rail_cell(x, side)), 1.0, RM['shroud_th'], TAR,
                 'standing/shrouds', {'kind': 'shroud'})
        # sheet：clew 往後綁兩舷（船殼舷頂或船尾平台欄杆）
        for s_, nmS in ((-1, 'P'), (1, 'S')):
            sw, sx = RM['sheet_to'], RM['sheet_x']
            if sw == 'hull':
                at = rail_cell(sx, s_)
            else:
                ys = [k for k in platform if k[0] == sx and (k[1] - YC) * s_ > 0]
                y = max((k[1] for k in ys), key=lambda v: (v - YC) * s_)
                at = top_cell(platform, sx, y)
            rope('%s.sheet-%s' % (nm, nmS), 'sail:%s/clew' % nm, anchor(sw, '%s-sheet-%s' % (m, nmS), at), 1.03, 0.4, HEMP,
                 'running/sheets', {'kind': 'sheet', 'sail': nm})
        TK = RM['tack']
        tx, ty = int(TK['x']), YC + int(TK['dy'])
        rope('%s.tack' % nm, '%s/fore' % YARD[m], anchor(TK['work'], 'tack-' + m, top_cell(WORKS[TK['work']][0], tx, ty)), 1.0, 0.5, HEMP,
             'running/tacks', {'kind': 'tack', 'sail': nm})
    # 長旗：主帆桁尖，hoist 沿帆桁最後 1 m；不寫 nation、也不寫 mast（蠍子號的坑）
    PN = RG['pennant']
    m = PN['yard']
    pk = yard_world(m, 'peak')
    js = {n: (int(n.split('-')[1]) * 8.0) for n in LAT[m]['anchors'] if n.startswith('jackstay-')}
    Lc = LAT[m]['len_m'] * 10
    hoist = min((n for n in js if js[n] <= Lc - 1 - PN['hoist_cells']), key=lambda n: (-js[n], n))
    sails.append({'name': 'pennant', 'corners': ['%s/peak' % YARD[m], '%.1f,%.1f,%.1f' % (pk[0] - PN['len_m'] * 10 * 0 + PN['len_m'] * 10, pk[1], pk[2] - 0.5), '%s/%s' % (YARD[m], hoist)],
                  'corner_names': ['head', 'fly', 'foot'], 'bind': [2], 'free': [1], 'color': RED, 'fullness': 1.04,
                  'meta': {'kind': 'flag', 'flag': 'pennant'}})

    # ── 讀數 ──
    ship = set(hull) | set(deck) | set(beak) | set(platform) | set(others)
    for m_ in ORDER:
        ship |= set(masts[m_])
    allyard = set().union(*ycells.values())
    tree_ship = cKDTree(np.array(sorted(ship), float) + 0.5)
    tree_awn = cKDTree(np.array(sorted(awning), float) + 0.5)
    R = {'probe': probe or None, 'anchors': len(anchors), 'ropes': len(ropes), 'sails': len(sails), 'sail_geo': {}, 'sail_plane': {}, 'rope_ends': {}}
    pts_w = {}

    def corner_w(c):
        if c.startswith('model:'):
            mm = next(k for k in ORDER if c.startswith(YARD[k]))
            return yard_world(mm, c.rsplit('/', 1)[1])
        return [float(v) for v in c.split(',')]
    for s in sails:
        P = [corner_w(c) for c in s['corners']]
        pts_w[s['name']] = P
        A, B, Cc = (np.array(p) for p in P)
        samp = np.array([A + u * (B - A) + v * (Cc - A) for u in np.linspace(0, 1, 90) for v in np.linspace(0, 1, 90) if u + v <= 1])
        d, ix = tree_ship.query(samp)
        shipl = tree_ship.data
        mm = s['meta'].get('mast') or PN['yard']
        others_y = allyard - ycells[mm]
        ty_ = cKDTree(np.array(sorted(others_y), float) + 0.5)
        dy_, _ = ty_.query(samp)
        R['sail_plane'][s['name']] = {'corners': [[round(v, 1) for v in p] for p in P], 'min_dist_to_ship_cells': round(float(d.min()), 2),
                                      'nearest_ship': {'sail': [round(float(v), 1) for v in samp[d.argmin()]], 'cell': [int(v) for v in shipl[ix[d.argmin()]] - 0.5]},
                                      'min_dist_to_other_yards_cells': round(float(dy_.min()), 2),
                                      'min_dist_to_awning_deco_cells': round(float(tree_awn.query(samp)[0].min()), 2),
                                      'area_m2': round(0.5 * float(np.linalg.norm(np.cross(B - A, Cc - A))) * 0.01, 2)}
    for m in ORDER:
        g = geo[m]
        R['sail_geo'][m] = {'head_anchor': g['head_anchor'], 'luff_m': round(g['luff'] * 0.1, 2), 'leech_m': round(g['leech'] * 0.1, 2), 'foot_m': round(g['foot'] * 0.1, 2),
                            'clew': [round(v, 1) for v in g['clew']]}
    R['sail_sets'] = {nm: [s['name'] for s in sails if s['meta']['kind'] == 'sail' and int(s['meta'].get('set', GAFF_SET)) <= k] for k, nm in ((1, '收帆'), (2, '戰鬥帆'), (3, '滿帆'))}

    def endpoint(e):
        if e.startswith('model:'):
            return corner_w(e)
        if e.startswith('sail:'):
            nm, cn = e[5:].split('/')
            s = next(s for s in sails if s['name'] == nm)
            return pts_w[nm][s['corner_names'].index(cn)]
        link, an = e.rsplit('/', 1)
        a = next(a for a in anchors if WORKS[a['work']][1] == link and a['name'] == an)
        return [v + 0.5 for v in a['at']]
    solid_arr = np.array(sorted(ship | allyard | set(awning)), float) + 0.5
    tree_solid = cKDTree(solid_arr)
    for r in ropes:
        a, b = endpoint(r['from']), endpoint(r['to'])
        pa, pb = np.array(a), np.array(b)
        n = int(math.dist(a, b) * 4) + 2
        hit = {tuple(int(np.floor(q)) for q in pa + t * (pb - pa)) for t in np.linspace(0, 1, n)}
        own = set()
        for e, p in ((r['from'], a), (r['to'], b)):
            if e.startswith('model:'):
                part = allyard
            elif e.startswith('sail:'):
                part = set()
            else:
                part = set(WORKS[next(w for w in WORKS if e.startswith(WORKS[w][1] + '/'))][0])
            own |= {k for k in hit if k in part and math.dist([v + 0.5 for v in k], p) <= OWN_R}
        R['rope_ends'][r['name']] = {'from': [round(v, 1) for v in a], 'to': [round(v, 1) for v in b], 'len_m': round(math.dist(a, b) * 0.1, 2),
                                     'straight_line_solid_cells': len((hit & (ship | allyard | set(awning))) - own), 'own_part_cells_near_end': len(own),
                                     'hit_sample': sorted((hit & (ship | allyard | set(awning))) - own)[:6]}
        # 繩面離實心（格是方塊：點到方塊的距離 − 繩半徑）；端點 SURF_R 格以內不算（帆桁尾端 3 格粗、繩從那裡繞下來）⇒ < 0 ＝ 繩的表面穿進格子（直線量，還沒下垂）
        L_ = math.dist(a, b)
        ts = [t for t in np.linspace(0, 1, int(L_ * 4) + 2) if SURF_R < t * L_ < L_ - SURF_R]
        if ts:
            Q = np.array([pa + t * (pb - pa) for t in ts])
            _, ix = tree_solid.query(Q, k=8)
            C = solid_arr[ix]
            dbox = np.linalg.norm(np.maximum(np.abs(Q[:, None, :] - C) - 0.5, 0), axis=2).min(1)
            R['rope_ends'][r['name']]['surface_clear_cells'] = round(float(dbox.min() - r['thickness'] / 2), 2)

    def tri_dist(p, A, B, Cc):
        A, B, Cc, p = (np.array(v) for v in (A, B, Cc, p))
        nrm = np.cross(B - A, Cc - A)
        nrm = nrm / np.linalg.norm(nrm)
        q = p - np.dot(p - A, nrm) * nrm
        v0, v1, v2 = Cc - A, B - A, q - A
        d00, d01, d11, d20, d21 = v0 @ v0, v0 @ v1, v1 @ v1, v2 @ v0, v2 @ v1
        den = d00 * d11 - d01 * d01
        u = (d11 * d20 - d01 * d21) / den
        v = (d00 * d21 - d01 * d20) / den
        return abs(float(np.dot(p - A, nrm))) if (u >= 0 and v >= 0 and u + v <= 1) else None
    cross = {}
    for r in ropes:
        a, b = np.array(endpoint(r['from'])), np.array(endpoint(r['to']))
        for s in sails:
            if s['meta']['kind'] != 'sail' or r['meta'].get('sail') == s['name']:
                continue
            ds = [tri_dist(a + t * (b - a), *pts_w[s['name']]) for t in np.linspace(0.02, 0.98, 120)]
            ds = [d for d in ds if d is not None]
            if ds and min(ds) < 1.0:
                cross.setdefault(r['name'], []).append(s['name'])
    R['ropes_through_flat_sail'] = cross
    R['problems'] = (len(cross) + sum(1 for s in sails if s['meta']['kind'] == 'sail' and (R['sail_plane'][s['name']]['min_dist_to_ship_cells'] < 1.0 or R['sail_plane'][s['name']]['min_dist_to_other_yards_cells'] < 1.0))
                     + sum(1 for v in R['rope_ends'].values() if v['straight_line_solid_cells']) + sum(1 for v in R['rope_ends'].values() if v.get('surface_clear_cells', 1) < 0) + (not R['sail_sets']['收帆']) + (not R['sail_sets']['戰鬥帆']))
    if probe:
        print(json.dumps({k: R[k] for k in ('probe', 'problems', 'sail_plane', 'ropes_through_flat_sail')} | {'rope_hits': {k: v['straight_line_solid_cells'] for k, v in R['rope_ends'].items() if v['straight_line_solid_cells']}}, ensure_ascii=False))
        return
    with open(os.path.join(HERE, 'rig_plan.json'), 'w', encoding='utf-8', newline='\n') as f:
        json.dump({'anchors': anchors, 'ropes': ropes, 'sails': sails}, f, ensure_ascii=False, indent=1)
    rows_ = [('sail', s['name'], s['meta']) for s in sails] + [('rope', r['name'], r['meta']) for r in ropes if r.get('meta')]
    with open(os.path.join(HERE, 'rig_meta.tsv'), 'w', encoding='utf-8', newline='\n') as f:
        f.write(''.join('%s\t%s\t%s\n' % (a, b, json.dumps(c, ensure_ascii=False, separators=(',', ':'))) for a, b, c in rows_))
    R['sha256'] = {f: hashlib.sha256(open(os.path.join(HERE, f), 'rb').read()).hexdigest() for f in ('rig_plan.json', 'rig_meta.tsv')}
    with open(os.path.join(HERE, 'verify_rigging.json'), 'w', encoding='utf-8', newline='\n') as f:
        json.dump(R, f, ensure_ascii=False, indent=1)
    AX, AY, AZ = [int(v) for v in plan['space']['assembly']]
    s_ = 2
    img = Image.new('RGB', (AX * s_ + 80, AZ * s_ + 80), (246, 242, 230))
    d = ImageDraw.Draw(img)
    f = ImageFont.load_default()
    d.text((30, 10), '%s - new sheet 06: rigging (flat lateen sails before simulation, straight ropes); shrouds on the side away from each sail; sheets P/S; tacks; pennant on the main yard peak' % plan['title_en'], fill=(20, 20, 40), font=f)
    oy = 40 + AZ * s_
    Pt = lambda x, z: (40 + x * s_, oy - z * s_)
    for (x, y, z) in sorted(ship | allyard):
        if y >= YC - 8:
            d.rectangle([40 + x * s_, oy - (z + 1) * s_, 40 + x * s_ + s_ - 1, oy - z * s_ - 1], fill=(170, 150, 120))
    for s in sails:
        d.polygon([Pt(p[0], p[2]) for p in pts_w[s['name']]], outline=(160, 30, 30) if s['meta']['kind'] == 'flag' else (60, 60, 160))
    for r in ropes:
        e = R['rope_ends'][r['name']]
        d.line([Pt(e['from'][0], e['from'][2]), Pt(e['to'][0], e['to'][2])], fill=(90, 70, 40))
    img.save(os.path.join(HERE, 'sheet06_rigging_v1.png'))
    print(json.dumps(R, ensure_ascii=False))


if __name__ == '__main__':
    main()
