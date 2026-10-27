# 飛魚號 步驟 8（TASK-0971）：channels（兩舷一件）、桅／艏斜桅／船殼的固定點、靜索、ratlines（橫繩組）、帆（斜桁主帆、topsail、staysail、jib）、帆自己的繩、旗、meta
#   出處：ame-labelle-01m/design/draft_rigging.py（拉貝爾號；它又出自收穫號 階段七）—— 結構（channels、桅上的點、繩、wpt、穿實心的讀數、輸出）照抄，
#   改成單桅 sloop：
#     · 一根桅（後傾 14°）：channels 的 x 照桅在舷頂高度的軸；backstay 的 deadeye 另外往後（backstay_aft）
#     · 前支索落在艏斜桅根（forestay_t）、上桅支索落在艏斜桅頂；bobstay 落在艏柱前緣（沒有船首喙）
#     · 帆：mainsail（四角綁 gaff／boom 模型，只有 leech 自由）＋ main sheet；topsail（帆腳 sheet 綁下帆桁 earing）；staysail、jib（luff 沿支索、clew 自由、兩舷 sheet）
#     · 旗：紅旗掛 gaff 峰、白長旗掛桅頂
#   輸入：plan.json（rigging、rig_build、masts）＋ yards_placement.json（帆桁模型）＋ 組裝件現在的格子（CLI 匯出）
#   輸出：masks/rigging/channels.vox.txt（世界座標，at 0,0,0）、rigging_plan.json（固定點、繩、橫繩組、帆、meta）、textures/ensign.png、verify_rigging.json
#   用法：python -I -X utf8 draft_rigging.py <design> [--probe=nometa=<繩名>]（反向對照：拿掉一條繩的 meta，看報不報；⛔ 不寫檔）
import sys, os, json, math, hashlib
import numpy as np
from PIL import Image

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), 'tools'))
import lines as HL
import layout as LY
from wio import export_list

KEY = 'main'
LK = '主桅'


def ensign_png(path, W, H):
    """英國紅旗（red ensign）：紅底、左上角（靠旗桿那一邊的上半）白底聖喬治紅十字。"""
    s = 4
    im = Image.new('RGBA', (W * s, H * s), (190, 22, 30, 255))
    px = im.load()
    cw, ch = W * s // 2, H * s // 2
    for x in range(cw):
        for y in range(ch):
            px[x, y] = (244, 244, 240, 255)
    for x in range(cw):
        for y in range(ch // 2 - 2, ch // 2 + 2):
            px[x, y] = (200, 16, 30, 255)
    for y in range(ch):
        for x in range(cw // 2 - 2, cw // 2 + 2):
            px[x, y] = (200, 16, 30, 255)
    im.save(path)


def main():
    sys.stdout.reconfigure(encoding='utf-8')
    design = sys.argv[1]
    probe = [a.split('=', 1)[1] for a in sys.argv[2:] if a.startswith('--probe')]
    plan = HL.load_plan(design)
    L = HL.Lines(plan)
    YC = L.YC
    RG = plan['rigging']
    RB = plan['rig_build']
    WORKS = os.path.dirname(os.path.dirname(os.path.abspath(design)))
    YP = json.load(open(os.path.join(design, 'yards_placement.json'), encoding='utf-8'))
    M = {m['key']: m for m in LY.masts(plan, L)}
    m = M[KEY]
    A = export_list('gura-flyingfish-01m-assembly', None, links=None)
    own = set()
    if os.path.exists(os.path.join(WORKS, 'gura-flyingfish-01m-channels', 'work.json')):
        own = set(map(tuple, export_list('gura-flyingfish-01m-channels', None)[:, :3].tolist()))
    occ = {tuple(r[:3]) for r in A.tolist()} - own
    hull = {tuple(r[:3]) for r in export_list('gura-flyingfish-01m', None).tolist()}
    hout = {}
    for x, y, z in hull:
        d = abs(y - YC)
        if d > hout.get((x, z), -1):
            hout[(x, z)] = d
    htop = {}
    for x, y, z in hull:
        htop[x] = max(htop.get(x, -1), z)

    def mast_r(z):
        r0, r1 = RB['mast_r'][KEY]
        if z <= m['lower_top']:
            zh, zt = math.floor(m['heel']) + 1, math.floor(m['lower_top'])
            return r0 + (r1 - r0) * (z - zh) / max(1, zt - zh)
        t0, t1 = RB['topmast_r'][KEY]
        zp, zt2 = math.floor(m['platform']), math.floor(m['truck'])
        return t0 + (t1 - t0) * (z - zp - 1) / max(1, zt2 - zp - 1)

    ax = lambda z: float(LY.mast_axis_x(plan, KEY, z + 0.5, L))
    anchors = {k: {} for k in ('hull', 'channels', 'main', 'bowsprit')}
    # ── channels（兩舷一件）＋ deadeye：舷頂那兩格的舷外 ──
    CH = RG['channels']
    xr = int(round(ax(40)))                                          # 桅在舷頂高度的 x
    xs = [xr - CH['first_aft'] - i * CH['spacing'] for i in range(CH['shrouds'])] + [xr - CH['backstay_aft']]
    chan, skipped = {}, 0
    for lo, hi in ((min(xs[:-1]) - 2, max(xs[:-1]) + 2), (xs[-1] - 2, xs[-1] + 2)):
        for x in range(lo, hi + 1):
            zc = htop[x] - CH['below_rail']
            o = max(hout.get((x, zc - 1), -1), hout.get((x, zc), -1))
            if o < 0:
                continue
            for dy in range(o + 1, o + CH['width'] + 1):
                for z in (zc - 1, zc):
                    for y in (YC + dy, YC - dy):
                        if (x, y, z) in occ:
                            skipped += 1
                        else:
                            chan[(x, y, z)] = RG['colors']['channel']
    for i, x in enumerate(xs, 1):
        zc = htop[x] - CH['below_rail']
        o = max(hout.get((x, zc - 1), -1), hout.get((x, zc), -1))
        dyo = o + CH['width']
        for ddx in (-1, 0, 1):
            for z in range(zc + 1, zc + 4):
                for y in (YC + dyo, YC - dyo):
                    chan[(x + ddx, y, z)] = RG['colors']['deadeye']
        anchors['channels']['deadeye-S-%d' % i] = [x, YC + dyo, zc + 3]
        anchors['channels']['deadeye-P-%d' % i] = [x, YC - dyo, zc + 3]
    # ── 桅上的點（桅子作品世界座標）──
    CT = RB['crosstrees'][KEY]
    MA = anchors['main']
    zp = int(math.floor(m['platform']))
    zh = zp - 3
    r = mast_r(zh)
    for s_, sg in (('S', 1), ('P', -1)):
        MA['hound-' + s_] = [int(round(ax(zh))), YC + sg * (int(math.floor(r)) + 1), zh]
    MA['stay-head'] = [int(math.floor(ax(zh) + r)) + 1, YC, zh]
    rr = int(math.floor(RB['mast_r'][KEY][1])) + 1
    xa = round(ax(zp))
    zf = zp - 12
    for s_, sg in (('S', 1), ('P', -1)):
        MA['futtock-' + s_] = [int(round(ax(zf))), YC + sg * (int(math.floor(mast_r(zf))) + 1), zf]
    zt = int(math.floor(m['truck'])) - 5
    rt = mast_r(zt)
    for s_, sg in (('S', 1), ('P', -1)):
        MA['tm-hound-' + s_] = [int(round(ax(zt))), YC + sg * (int(math.floor(rt)) + 1), zt]
    MA['tm-stay-head'] = [int(math.floor(ax(zt) + rt)) + 1, YC, zt]
    for i, dx in enumerate((rr, -rr), 1):
        for s_, sg in (('S', 1), ('P', -1)):
            MA['xtree-%s-%d' % (s_, i)] = [xa + dx, YC + sg * (CT + 1), zp + 1]
            MA['xtree-low-%s-%d' % (s_, i)] = [xa + dx, YC + sg * (CT + 1), zp]
    # ── 艏斜桅上的點 ──
    B = LY.bowsprit(plan)
    a = math.radians(B['angle'])
    u = np.array([math.cos(a), 0.0, math.sin(a)])
    w = np.array([-math.sin(a), 0.0, math.cos(a)])
    Hh = np.array([B['x0'] + 0.5, YC + 0.5, B['z0'] + 0.5])
    Lb = B['len']
    br0, br1 = RB['bowsprit_r']
    rb = lambda s: br0 + (br1 - br0) * s / Lb
    cell = lambda p: [int(math.floor(p[0])), int(math.floor(p[1])), int(math.floor(p[2]))]
    BA = anchors['bowsprit']
    SL = RG['sails']
    tf = SL['forestay_t'] * Lb
    BA['forestay-foot'] = cell(Hh + tf * u + (rb(tf) + 1) * w)
    BA['cap-top'] = cell(Hh + (Lb - 3) * u + (rb(Lb) + 1.5) * w)
    for s_, sg in (('S', 1), ('P', -1)):
        BA['side-' + s_] = cell(Hh + 0.45 * Lb * u + np.array([0, sg * (rb(0.45 * Lb) + 1), 0]))
    BA['bob-1'] = cell(Hh + 0.75 * Lb * u - (rb(0.75 * Lb) + 1) * w)
    # ── 船殼上的點 ──
    H = anchors['hull']
    zb = 30
    H['bobstay-foot'] = [max(x for (x, y, z) in hull if y == YC and z == zb), YC, zb]      # 艏柱前緣
    zs = max(z for (x, y, z) in hull if y == YC and x < 90)
    H['mainsheet'] = [min(x for (x, y, z) in hull if y == YC and z == zs), YC, zs]         # 船尾舷頂中線
    for s_, sg in (('S', 1), ('P', -1)):
        H['bs-shroud-' + s_] = [205, YC + sg * hout[(205, htop[205])], htop[205]]

    def rail(x):
        z = htop[x]
        return [x, hout[(x, z)], z]
    for nm, x in (('staysail', SL['staysail_sheet_x']), ('jib', SL['jib_sheet_x'])):
        p = rail(x)
        H['belay-%s-S' % nm] = [p[0], YC + p[1], p[2]]
        H['belay-%s-P' % nm] = [p[0], YC - p[1], p[2]]

    # ── 繩 ──
    C = RG['colors']
    T = RG['thick']
    ropes = []

    def rope(name, a_, b_, group, th, slack=1.0, color=None, meta=None):
        ropes.append({'name': name, 'from': a_, 'to': b_, 'group': group, 'thickness': th, 'slack': slack, 'color': color or C['standing'], 'meta': meta})
    ns = CH['shrouds']
    for s_ in ('S', 'P'):
        for i in range(1, ns + 1):
            rope('main-shroud-%s-%d' % (s_, i), '支索板/deadeye-%s-%d' % (s_, i), '%s/hound-%s' % (LK, s_), 'standing/shrouds', T['shroud'])
        rope('main-topmast-backstay-%s-1' % s_, '支索板/deadeye-%s-%d' % (s_, ns + 1), '%s/tm-hound-%s' % (LK, s_), 'standing/backstays', T['backstay'])
        for i in range(1, RG['topmast_shrouds'] + 1):
            rope('main-topmast-shroud-%s-%d' % (s_, i), '%s/xtree-%s-%d' % (LK, s_, i), '%s/tm-hound-%s' % (LK, s_), 'standing/topmast-shrouds', T['topmast_shroud'])
            rope('main-futtock-%s-%d' % (s_, i), '%s/xtree-low-%s-%d' % (LK, s_, i), '%s/futtock-%s' % (LK, s_), 'standing/futtock-shrouds', T['futtock'])
    rope('fore-stay', '%s/stay-head' % LK, '艏斜桅/forestay-foot', 'standing/stays', T['stay'])
    rope('jib-stay', '%s/tm-stay-head' % LK, '艏斜桅/cap-top', 'standing/stays', T['tm_stay'])
    rope('bobstay-1', '船殼/bobstay-foot', '艏斜桅/bob-1', 'standing/bowsprit', T['bobstay'])
    for s_ in ('S', 'P'):
        rope('bowsprit-shroud-' + s_, '船殼/bs-shroud-' + s_, '艏斜桅/side-' + s_, 'standing/bowsprit', T['bobstay'])
    RL = RG['ratlines']
    rsets = [{'name': 'main-lower-%s' % s_, 'rope_a': 'main-shroud-%s-1' % s_, 'rope_b': 'main-shroud-%s-%d' % (s_, ns),
              'step': RL['step'], 'start': RL['start'], 'stop': RL['stop'], 'min_span': RL['min_span'], 'thickness': RL['th'], 'group': 'ratlines/lower'} for s_ in ('S', 'P')]

    def wpt(spec):
        fr, nm = spec.split('/', 1)
        part = {'支索板': 'channels', '船殼': 'hull', '艏斜桅': 'bowsprit', LK: 'main'}[fr]
        return np.array(anchors[part][nm], float) + 0.5

    # ── 艏帆的 head：支索上 72%／78% 那一點（登記在主桅子作品；支索 slack 1 拉直 ⇒ luff 沿著它）──
    for nm, stay, f in (('staysail', 'fore-stay', SL['staysail_head']), ('jib', 'jib-stay', SL['jib_head'])):
        rp = next(r_ for r_ in ropes if r_['name'] == stay)
        lo, hi = wpt(rp['to']), wpt(rp['from'])
        MA[nm + '.head'] = cell(lo + f * (hi - lo))

    # ── 帆 ──
    def src_anchors(work):
        return {x['name']: x['at'] for x in json.load(open(os.path.join(WORKS, work, 'anchors.json'), encoding='utf-8'))['anchors']}

    def model_pt(yname, anchor):
        p = next(y for y in YP if y['name'] == yname)
        loc = np.array(src_anchors(p['work'])[anchor], float) + 0.5
        v = (loc - np.array(p['pivot'])) * np.array(p['scale'])
        th = math.radians(p['rotate'][2])
        v = np.array([v[0] * math.cos(th) - v[1] * math.sin(th), v[0] * math.sin(th) + v[1] * math.cos(th), v[2]])
        return np.array(p['at']) + v
    sails = []

    def sail(name, corners, bind, free, meta, names, fullness=None, color=None, texture=None):
        sails.append({'name': name, 'corners': corners, 'corner_names': names, 'bind': bind, 'free': free, 'meta': meta,
                      'fullness': fullness or SL['fullness'], 'color': color or C['sail'], 'texture': texture})
    fmt = lambda p: '%.2f,%.2f,%.2f' % tuple(p)
    os.makedirs(os.path.join(design, 'textures'), exist_ok=True)
    # mainsail：throat、peak（gaff）、clew（boom end）、tack（boom jaws）；綁 gaff、boom、桅三條邊
    g, bm = 'model:%s/yard-main-gaff/' % LK, 'model:%s/yard-main-boom/' % LK
    sail('mainsail', [g + 'throat', g + 'peak', bm + 'end', bm + 'jaws'], [0, 2, 3], [], {'kind': 'sail', 'mast': KEY, 'sail': 'gaff'},
         ['throat', 'peak', 'clew', 'tack'])
    rope('mainsail.sheet', bm + SL['mainsheet_boom'], '船殼/mainsheet', 'running/sheets', T['main_sheet'], 1.05, C['running'], {'kind': 'sheet', 'sail': 'mainsail'})
    # topsail：帆頂釘在 topsail 帆桁兩個 earing 之間、帆腳兩角自由，sheet 綁下帆桁同舷的 earing
    cy, ty = 'yard-main-crossjack', 'yard-main-topsail'
    cps = []
    for s_ in ('S', 'P'):
        e, pv = model_pt(cy, 'earing-' + s_), np.array(next(y for y in YP if y['name'] == cy)['at'])
        p = e + SL['clew_in'] * (pv - e)
        p[2] += 2
        cps.append(fmt(p))
    nm = 'main-topsail'
    sail(nm, ['model:%s/%s/earing-P' % (LK, ty), 'model:%s/%s/earing-S' % (LK, ty), cps[0], cps[1]], [0], ['clew_s', 'clew_p'],
         {'kind': 'sail', 'mast': KEY, 'sail': 'topsail'}, ['head_p', 'head_s', 'clew_s', 'clew_p'])
    for s_, c in (('S', 'clew_s'), ('P', 'clew_p')):
        rope('%s.sheet-%s' % (nm, s_), 'sail:%s/%s' % (nm, c), 'model:%s/%s/earing-%s' % (LK, cy, s_), 'running/sheets', T['sheet'], 1.0, C['running'], {'kind': 'sheet', 'sail': nm})
    # staysail、jib：tack（艏斜桅）、head（支索上）、clew 自由；兩舷 sheet
    for nm, tack, kind, clew in (('staysail', '艏斜桅/forestay-foot', 'staysail', SL['staysail_clew']), ('jib', '艏斜桅/cap-top', 'jib', SL['jib_clew'])):
        sail(nm, [tack, '%s/%s.head' % (LK, nm), fmt([clew[0] + 0.5, YC + 0.5, clew[1] + 0.5])], [0], ['clew'],
             {'kind': 'sail', 'mast': 'bowsprit', 'sail': kind}, ['tack', 'head', 'clew'], fullness=1.06)
        for s_ in ('S', 'P'):
            rope('%s.sheet-%s' % (nm, s_), 'sail:%s/clew' % nm, '船殼/belay-%s-%s' % (nm, s_), 'running/sheets', T['sheet'], 1.04, C['running'], {'kind': 'sheet', 'sail': nm})
    for r_ in ropes:                                                 # 艏帆的 luff 沿支索 ⇒ 那兩條支索拉直
        if r_['name'] in ('fore-stay', 'jib-stay'):
            r_['slack'] = 1.0
    # 旗：紅旗掛 gaff 峰（luff 沿 gaff 往下到 top-128）、白長旗掛桅頂
    FL = RG['flags']
    ew, eh = FL['ensign']
    pk = model_pt('yard-main-gaff', 'peak')
    lu = model_pt('yard-main-gaff', FL['ensign_luff_anchor'])
    sail('ensign', [g + 'peak', fmt(pk - [ew, 0, 0]), fmt(pk - [ew, 0, eh]), g + FL['ensign_luff_anchor']],
         [3], [2, 1], {'kind': 'flag', 'flag': 'ensign'}, None, fullness=1.04, color='#be161e', texture='textures/ensign.png')
    tz = math.floor(m['truck'])
    tx = ax(tz)
    pl_, ph = FL['pennant']
    sail('pennant', [fmt([tx + 0.5, YC + 0.5, tz - 1]), fmt([tx - pl_, YC + 0.5, tz - 2]), fmt([tx + 0.5, YC + 0.5, tz - 1 - ph])],
         [2], [1], {'kind': 'flag', 'flag': 'pennant', 'mast': KEY}, None, fullness=1.04, color=FL['pennant_color'])
    ensign_png(os.path.join(design, 'textures', 'ensign.png'), ew, eh)

    metas = [['sail', s['name'], s['meta']] for s in sails] + [['rope', r_['name'], r_['meta']] for r_ in ropes if r_['meta']]
    if probe:
        nmp = probe[0].split('=')[1]
        metas = [mm for mm in metas if not (mm[0] == 'rope' and mm[1] == nmp)]
    # ── 讀數 ──
    names = [r_['name'] for r_ in ropes]
    need = [r_['name'] for r_ in ropes if r_['name'].split('.')[0] in {s['name'] for s in sails} and '.' in r_['name']]
    have = {mm[1] for mm in metas if mm[0] == 'rope'}
    # 帆裝三段（Ship_Rigging §9.1）：set 或照 sail 的預設
    dflt = {'topsail': 1, 'jib': 1, 'topgallant': 2, 'gaff': 2}
    lvl = {s['name']: s['meta'].get('set', dflt.get(s['meta'].get('sail'), 3)) for s in sails if s['meta']['kind'] == 'sail'}
    R = {'channels': {'cells': len(chan), 'skipped_on_ship': skipped, 'deadeye_x': xs, 'mirror_diff': sum(1 for (x, y, z), c in chan.items() if chan.get((x, 2 * YC - y, z)) != c)},
         'anchors': {k: len(v) for k, v in anchors.items()}, 'ropes': len(ropes), 'ratline_sets': len(rsets),
         'groups': {gg: sum(1 for r_ in ropes if r_['group'] == gg) for gg in sorted({r_['group'] for r_ in ropes})},
         'sails': len(sails), 'meta': {'sails': sum(1 for mm in metas if mm[0] == 'sail'), 'ropes': len(have)},
         'sail_ropes_without_meta': sorted(set(need) - have), 'dup_rope_names': len(names) - len(set(names)),
         'anchors_in_solid': sorted('%s/%s' % (k, n) for k, v in anchors.items() for n, p in v.items() if tuple(p) in occ and k != 'hull'),
         'sail_sets': {str(k): sorted(n for n, v in lvl.items() if v <= k) for k in (1, 2, 3)}}
    solid = set(occ) | set(chan)
    thru = {}
    for r_ in ropes:
        if r_['from'].startswith(('sail:', 'model:', 'rope:')) or r_['to'].startswith(('sail:', 'model:', 'rope:')):
            continue
        a_, b_ = wpt(r_['from']), wpt(r_['to'])
        n = int(np.linalg.norm(b_ - a_) / 0.5) + 1
        hits = set()
        for t in np.linspace(0, 1, n):
            q = a_ + (b_ - a_) * t
            if np.linalg.norm(q - a_) < 3 or np.linalg.norm(q - b_) < 3:
                continue
            k = (int(math.floor(q[0])), int(math.floor(q[1])), int(math.floor(q[2])))
            if k in solid:
                hits.add(k)
        if hits:
            thru[r_['name']] = len(hits)
    R['ropes_through_solid'] = thru
    if probe:
        print(json.dumps({'probe': probe[0], 'sail_ropes_without_meta': R['sail_ropes_without_meta']}, ensure_ascii=False))
        return
    os.makedirs(os.path.join(design, 'masks', 'rigging'), exist_ok=True)
    p = os.path.join(design, 'masks', 'rigging', 'channels.vox.txt')
    with open(p, 'w', encoding='utf-8', newline='\n') as f:
        f.write('# 飛魚號 channels 兩舷（支索板＋deadeye；世界座標，at 0,0,0）\n')
        for k in sorted(chan):
            f.write('%d,%d,%d,%d\n' % (k[0], k[1], k[2], chan[k]))
    R['channels']['sha256'] = hashlib.sha256(open(p, 'rb').read()).hexdigest()
    works = {'hull': 'gura-flyingfish-01m', 'channels': 'gura-flyingfish-01m-channels', 'bowsprit': 'gura-flyingfish-01m-bowsprit', 'main': 'gura-flyingfish-01m-mast-main'}
    out = {'anchors': anchors, 'anchor_works': works, 'ropes': ropes, 'ratline_sets': rsets, 'sails': sails, 'meta': metas, 'wind': RG['wind'], 'sail_seconds': RG['sail_seconds']}
    with open(os.path.join(design, 'rigging_plan.json'), 'w', encoding='utf-8', newline='\n') as f:
        json.dump(out, f, ensure_ascii=False, indent=1, default=lambda o: o.item())
    with open(os.path.join(design, 'verify_rigging.json'), 'w', encoding='utf-8', newline='\n') as f:
        json.dump(R, f, ensure_ascii=False, indent=1, default=lambda o: o.item())
    print(json.dumps(R, ensure_ascii=False, default=lambda o: o.item()))


if __name__ == '__main__':
    main()
