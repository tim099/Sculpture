# 收穫號 階段七（TASK-0596）：channels（兩舷一件）、桅／艏斜桅／船殼／甲板／船首喙的固定點、靜索、ratlines、帆（方帆、spritsail、lateen）、帆自己的繩、旗、meta
#   輸入：plan.json（rigging、rig_build、masts）＋ yards_placement.json／yards_lateen.json（帆桁模型）＋ 組裝件現在的格子（CLI 匯出）
#   輸出：masks/rigging/channels.vox.txt（世界座標，at 0,0,0）、rigging_plan.json（固定點、繩、帆、meta）、textures/*.png、verify_rigging.json
#   用法：python -I -X utf8 draft_rigging.py <design> [--probe=nometa=<繩名>]（反向對照：拿掉一條繩的 meta，看 check 報不報；⛔ 不寫檔）
#   · 結構參考 gura-tridente-01m/design/draft_rigging.py（channels＋deadeye、桅上的 hound／stay-head、ratlines 用子繩、帆角綁帆桁模型、帆自己的繩帶 meta）
import sys, os, json, math, hashlib
import numpy as np
from PIL import Image

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), 'tools'))
import lines as HL
import layout as LY
from wio import export_list

LINK = {'fore': '前桅', 'main': '主桅', 'mizzen': '後桅', 'bonaventure': 'bonaventure', 'bowsprit': '艏斜桅'}


def cross_png(path, W, H, field, red, ragged=True):
    """勃艮第十字：底色上一個紅色鋸齒交叉（兩條對角線，每隔幾格凸一個節）。"""
    im = Image.new('RGBA', (W, H), field)
    px = im.load()
    for x in range(W):
        for y in range(H):
            u, v = x / (W - 1.0), y / (H - 1.0)
            for d in (abs(u - v), abs(u - (1 - v))):
                if d * min(W, H) <= 1.6:
                    px[x, y] = red
    if ragged:
        for k in range(3, min(W, H) - 3, 6):                             # 鋸齒：沿兩條對角線每 6 格一個突起
            for (x, y) in ((round(k * W / H), k), (W - 1 - round(k * W / H), k)):
                for dx, dy in ((2, -1), (-2, 1), (2, 0), (-2, 0)):
                    xx, yy = int(x + dx), int(y + dy)
                    if 0 <= xx < W and 0 <= yy < H:
                        px[xx, yy] = red
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
    A = export_list('calli-cosecha-01m-assembly', None, links=None)
    own = set()
    if os.path.exists(os.path.join(WORKS, 'calli-cosecha-01m-channels', 'work.json')):
        own = set(map(tuple, export_list('calli-cosecha-01m-channels', None)[:, :3].tolist()))
    occ = {tuple(r[:3]) for r in A.tolist()} - own
    hull = {tuple(r[:3]) for r in export_list('calli-cosecha-01m', None).tolist()}
    hout = {}
    for x, y, z in hull:
        d = abs(y - YC)
        if d > hout.get((x, z), -1):
            hout[(x, z)] = d

    def top_z(x):
        return int(math.floor(float(L.top_z(x + 0.5)) + 0.5))

    def mast_r(key, z):
        m = M[key]
        r0, r1 = RB['mast_r'][key]
        if z <= m['lower_top'] or key not in RB['topmast_r']:
            zh, zt = math.floor(m['heel']) + 1, math.floor(m['lower_top'])
            return r0 + (r1 - r0) * (z - zh) / max(1, zt - zh)
        t0, t1 = RB['topmast_r'][key]
        zp, zt2 = math.floor(m['platform']), math.floor(m['truck'])
        return t0 + (t1 - t0) * (z - zp - 1) / max(1, zt2 - zp - 1)

    ax = lambda key, z: float(LY.mast_axis_x(plan, key, z + 0.5, L))
    anchors = {k: {} for k in ('hull', 'channels', 'fore', 'main', 'mizzen', 'bonaventure', 'bowsprit', 'deck-puente', 'deck-toldilla', 'espolon')}
    # ── channels（兩舷一件）＋ deadeye ──
    CH = RG['channels']
    chan, skipped = {}, 0
    for key in ('fore', 'main', 'mizzen', 'bonaventure'):
        xm = M[key]['x']
        n = CH['shrouds'][key] + CH['backstays'].get(key, 0)
        xs = [xm - CH['first_aft'] - i * CH['spacing'] for i in range(n)]
        zc = top_z(xm) - CH['below_rail']
        for x in range(min(xs) - 3, max(xs) + 4):
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
            o = max(hout.get((x, zc - 1), -1), hout.get((x, zc), -1))
            dyo = o + CH['width']
            for ddx in (-1, 0, 1):
                for z in range(zc + 1, zc + 4):
                    for y in (YC + dyo, YC - dyo):
                        chan[(x + ddx, y, z)] = RG['colors']['deadeye']
            anchors['channels']['deadeye-%s-S-%d' % (key, i)] = [x, YC + dyo, zc + 3]
            anchors['channels']['deadeye-%s-P-%d' % (key, i)] = [x, YC - dyo, zc + 3]
    # ── 桅上的點（桅子作品世界座標）──
    for key in ('fore', 'main', 'mizzen', 'bonaventure'):
        m = M[key]
        A_ = anchors[key]
        zp = int(math.floor(m['platform']))
        zh = zp - 5 if key in RB['tops'] else int(math.floor(m['lower_top'])) - 4
        r = mast_r(key, zh)
        for s_, sg in (('S', 1), ('P', -1)):
            A_['hound-' + s_] = [int(round(ax(key, zh))), YC + sg * (int(math.ceil(r)) + 1), zh]
        A_['stay-head'] = [int(math.floor(ax(key, zh) + r)) + 1, YC, zh]
        if key in RB['topmast_r']:
            zf = zp - 25
            for s_, sg in (('S', 1), ('P', -1)):
                A_['futtock-' + s_] = [int(round(ax(key, zf))), YC + sg * (int(math.ceil(mast_r(key, zf))) + 1), zf]
            zt = int(math.floor(m['truck'])) - 8
            rt = mast_r(key, zt)
            for s_, sg in (('S', 1), ('P', -1)):
                A_['tm-hound-' + s_] = [int(round(ax(key, zt))), YC + sg * (int(math.ceil(rt)) + 1), zt]
            A_['tm-stay-head'] = [int(math.floor(ax(key, zt) + rt)) + 1, YC, zt]
            R_ = RB['tops'][key]
            xc = ax(key, zp)
            for i, f in enumerate((-0.45, 0.0, 0.45), 1):
                dx = f * R_
                dy = int(math.floor(math.sqrt(R_ * R_ - dx * dx))) - 1
                for s_, sg in (('S', 1), ('P', -1)):
                    A_['rim-%s-%d' % (s_, i)] = [int(round(xc + dx)), YC + sg * dy, zp]
                    A_['rim-low-%s-%d' % (s_, i)] = [int(round(xc + dx)), YC + sg * dy, zp - 1]
            A_['top-aft'] = [int(math.ceil(xc - R_)) + 1, YC, zp]
    for key, nm, deck in (('fore', 'mainstay-foot', 'castillo'), ('main', 'mizzenstay-foot', 'puente'), ('mizzen', 'bonstay-foot', 'alcazar')):
        z = int(LY.deck_z(plan, deck, M[key]['x'] + 0.5)) + 3
        anchors[key][nm] = [int(math.floor(ax(key, z) - mast_r(key, z))) - 1, YC, z]
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
    BA['forestay-foot'] = cell(Hh + 0.35 * Lb * u + (rb(0.35 * Lb) + 1) * w)
    BA['cap-top'] = cell(Hh + (Lb - 3) * u + (rb(Lb) + 1.5) * w)
    for s_, sg in (('S', 1), ('P', -1)):
        BA['side-' + s_] = cell(Hh + 0.45 * Lb * u + np.array([0, sg * (rb(0.45 * Lb) + 1), 0]))
    for i, f in enumerate((0.5, 0.65), 1):
        BA['bob-%d' % i] = cell(Hh + f * Lb * u - (rb(f * Lb) + 1) * w)
    # ── 船首喙的 bobstay 腳：cutwater 最前面那一格 ──
    esp = {tuple(r[:3]) for r in export_list('calli-cosecha-01m-espolon', None).tolist()}
    for i, z in enumerate((50, 62), 1):
        xf = max(x for (x, y, zz) in esp if y == YC and zz == z)
        anchors['espolon']['bobstay-%d' % i] = [xf, YC, z]
    # ── 船殼上的點：舷頂（那一欄最外那一格）——帆腳索、tack、lateen sheet、艏斜桅 shroud ──
    def rail(x, dy_cap=None):
        z = max(zz for (xx, zz) in hout if xx == x)
        o = hout[(x, z)]
        if dy_cap is not None:
            o = min(o, dy_cap)
            while (x, YC + o, z) not in hull and o > 0:
                o -= 1
        return [x, o, z]
    H = anchors['hull']
    SL = RG['sails']
    belay = {}
    for key in ('fore', 'main'):
        belay['%s-sheet' % key] = min(495, M[key]['x'] - SL['sheet_aft'])
        belay['%s-tack' % key] = min(495, M[key]['x'] + SL['tack_fwd'])
    belay['sprit'] = 490
    belay['mizzen-lateen'] = 112
    for nm, x in belay.items():
        p = rail(x)
        H['belay-%s-S' % nm] = [p[0], YC + p[1], p[2]]
        H['belay-%s-P' % nm] = [p[0], YC - p[1], p[2]]
    for s_, sg in (('S', 1), ('P', -1)):                               # bonaventure 的 sheet：船尾舷頂（避開三盞燈 y ±18）
        y = YC + sg * 24
        x = min(xx for (xx, yy, zz) in hull if yy == y and zz == 133)
        H['belay-bonaventure-lateen-' + s_] = [x, y, 133]
        H['bs-shroud-' + s_] = [495, YC + sg * hout[(495, 95)], 95]
    # 甲板上的 lateen tack
    for key, (deck, x) in SL['lateen_tack'].items():
        z = int(LY.deck_z(plan, deck, x + 0.5)) + 1
        anchors['deck-' + deck]['tack-%s' % key] = [x, YC, z]

    # ── 繩 ──
    C = RG['colors']
    T = RG['thick']
    ropes = []

    def rope(name, a_, b_, group, th, slack=1.0, color=None, meta=None):
        ropes.append({'name': name, 'from': a_, 'to': b_, 'group': group, 'thickness': th, 'slack': slack, 'color': color or C['standing'], 'meta': meta})
    for key in ('fore', 'main', 'mizzen', 'bonaventure'):
        Lk = LINK[key]
        ns, nb = CH['shrouds'][key], CH['backstays'].get(key, 0)
        for s_ in ('S', 'P'):
            for i in range(1, ns + 1):
                rope('%s-shroud-%s-%d' % (key, s_, i), '支索板/deadeye-%s-%s-%d' % (key, s_, i), '%s/hound-%s' % (Lk, s_), 'standing/shrouds', T['shroud'])
            for b in range(1, nb + 1):
                rope('%s-topmast-backstay-%s-%d' % (key, s_, b), '支索板/deadeye-%s-%s-%d' % (key, s_, ns + b), '%s/tm-hound-%s' % (Lk, s_), 'standing/backstays', T['backstay'])
            if key in RB['topmast_r']:
                for i in range(1, RG['topmast_shrouds'] + 1):
                    rope('%s-topmast-shroud-%s-%d' % (key, s_, i), '%s/rim-%s-%d' % (Lk, s_, i), '%s/tm-hound-%s' % (Lk, s_), 'standing/topmast-shrouds', T['topmast_shroud'])
                    rope('%s-futtock-%s-%d' % (key, s_, i), '%s/rim-low-%s-%d' % (Lk, s_, i), '%s/futtock-%s' % (Lk, s_), 'standing/futtock-shrouds', T['futtock'])
    for nm, a_, b_, th in (('fore-stay', '前桅/stay-head', '艏斜桅/forestay-foot', T['stay']),
                           ('fore-topmast-stay', '前桅/tm-stay-head', '艏斜桅/cap-top', T['tm_stay']),
                           ('main-stay', '主桅/stay-head', '前桅/mainstay-foot', T['stay']),
                           ('main-topmast-stay', '主桅/tm-stay-head', '前桅/top-aft', T['tm_stay']),
                           ('mizzen-stay', '後桅/stay-head', '主桅/mizzenstay-foot', T['tm_stay']),
                           ('bonaventure-stay', 'bonaventure/stay-head', '後桅/bonstay-foot', T['tm_stay'])):
        rope(nm, a_, b_, 'standing/stays', th)
    for i in (1, 2):
        rope('bobstay-%d' % i, '船首喙/bobstay-%d' % i, '艏斜桅/bob-%d' % i, 'standing/bowsprit', T['bobstay'])
    for s_ in ('S', 'P'):
        rope('bowsprit-shroud-' + s_, '船殼/bs-shroud-' + s_, '艏斜桅/side-' + s_, 'standing/bowsprit', T['bobstay'])

    def wpt(spec):
        fr, nm = spec.split('/', 1)
        part = {'支索板': 'channels', '船殼': 'hull', '船首喙': 'espolon', '甲板-puente': 'deck-puente', '甲板-toldilla': 'deck-toldilla'}.get(fr)
        if part is None:
            part = {v: k for k, v in LINK.items()}[fr]
        return np.array(anchors[part][nm], float) + 0.5
    RL = RG['ratlines']
    nrat = 0
    for key in ('fore', 'main', 'mizzen'):
        for s_ in ('S', 'P'):
            sets = [('lower', '%s-shroud-%s-1' % (key, s_), '%s-shroud-%s-%d' % (key, s_, CH['shrouds'][key]), RL['every'], RL['th'])]
            if key in RB['topmast_r']:
                sets.append(('topmast', '%s-topmast-shroud-%s-1' % (key, s_), '%s-topmast-shroud-%s-%d' % (key, s_, RG['topmast_shrouds']), RL['tm_every'], RL['tm_th']))
            for kind, first, last, every, th in sets:
                ra = next(r for r in ropes if r['name'] == first)
                rb_ = next(r for r in ropes if r['name'] == last)
                La = np.linalg.norm(wpt(ra['to']) - wpt(ra['from']))
                Lb_ = np.linalg.norm(wpt(rb_['to']) - wpt(rb_['from']))
                d, k = RL['start'], 1
                while d < La * RL['stop']:
                    pa = wpt(ra['from']) + (d / La) * (wpt(ra['to']) - wpt(ra['from']))
                    pb = wpt(rb_['from']) + min(1.0, d / Lb_) * (wpt(rb_['to']) - wpt(rb_['from']))
                    if np.linalg.norm(pa - pb) >= RL['min_len']:
                        rope('ratline-%s-%s-%s-%02d' % (kind, key, s_, k), 'rope:%s/%.4f' % (first, d / La), 'rope:%s/%.4f' % (last, min(1.0, d / Lb_)), 'ratlines/' + kind, th)
                        nrat += 1
                    d += every
                    k += 1
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
    for key in ('fore', 'main'):
        Lk = LINK[key]
        cy, ty = 'yard-%s-course' % key, 'yard-%s-topsail' % key
        cps = []
        for s_ in ('S', 'P'):
            e, pv = model_pt(cy, 'earing-' + s_), np.array(next(y for y in YP if y['name'] == cy)['at'])
            p = pv + SL['course_in'] * (e - pv)
            p[2] = top_z(int(p[0])) + SL['course_clew_above_rail']
            cps.append(fmt(p))
        nm = '%s-course' % key
        sail(nm, ['model:%s/%s/earing-P' % (Lk, cy), 'model:%s/%s/earing-S' % (Lk, cy), cps[0], cps[1]], [0], ['clew_s', 'clew_p'],
             {'kind': 'sail', 'mast': key, 'sail': 'course'}, ['head_p', 'head_s', 'clew_s', 'clew_p'],
             texture='textures/cross_course.png' if nm in SL['cross_texture'] else None)
        for s_, c in (('S', 'clew_s'), ('P', 'clew_p')):
            rope('%s.sheet-%s' % (nm, s_), 'sail:%s/%s' % (nm, c), '船殼/belay-%s-sheet-%s' % (key, s_), 'running/sheets', T['course_sheet'], 1.02, C['running'], {'kind': 'sheet', 'sail': nm})
            rope('%s.tack-%s' % (nm, s_), 'sail:%s/%s' % (nm, c), '船殼/belay-%s-tack-%s' % (key, s_), 'running/tacks', T['tack'], 1.02, C['running'], {'kind': 'tack', 'sail': nm})
        cps = []
        for s_ in ('S', 'P'):
            e, pv = model_pt(cy, 'earing-' + s_), np.array(next(y for y in YP if y['name'] == cy)['at'])
            p = e + SL['clew_in'] * (pv - e)
            p[2] += 2
            cps.append(fmt(p))
        nm = '%s-topsail' % key
        sail(nm, ['model:%s/%s/earing-P' % (Lk, ty), 'model:%s/%s/earing-S' % (Lk, ty), cps[0], cps[1]], [0], ['clew_s', 'clew_p'],
             {'kind': 'sail', 'mast': key, 'sail': 'topsail'}, ['head_p', 'head_s', 'clew_s', 'clew_p'])
        for s_, c in (('S', 'clew_s'), ('P', 'clew_p')):
            rope('%s.sheet-%s' % (nm, s_), 'sail:%s/%s' % (nm, c), 'model:%s/%s/earing-%s' % (Lk, cy, s_), 'running/sheets', T['sheet'], 1.0, C['running'], {'kind': 'sheet', 'sail': nm})
    cps = []
    for s_ in ('S', 'P'):
        e, pv = model_pt('yard-spritsail', 'earing-' + s_), np.array(next(y for y in YP if y['name'] == 'yard-spritsail')['at'])
        p = e + SL['clew_in'] * (pv - e)
        p[2] -= SL['sprit_drop']
        cps.append(fmt(p))
    sail('spritsail', ['model:艏斜桅/yard-spritsail/earing-P', 'model:艏斜桅/yard-spritsail/earing-S', cps[0], cps[1]], [0], ['clew_s', 'clew_p'],
         {'kind': 'sail', 'mast': 'bowsprit', 'sail': 'spritsail'}, ['head_p', 'head_s', 'clew_s', 'clew_p'])
    for s_, c in (('S', 'clew_s'), ('P', 'clew_p')):
        rope('spritsail.sheet-%s' % s_, 'sail:spritsail/%s' % c, '船殼/belay-sprit-%s' % s_, 'running/sheets', T['sheet'], 1.02, C['running'], {'kind': 'sheet', 'sail': 'spritsail'})
    for key in ('mizzen', 'bonaventure'):
        Lk = LINK[key]
        nm = '%s-lateen' % key
        yn = 'yard-%s-lateen' % key
        cx, cz = SL['lateen_clew'][key]
        sail(nm, ['model:%s/%s/fore' % (Lk, yn), 'model:%s/%s/peak' % (Lk, yn), fmt([cx + 0.5, YC + 0.5, cz + 0.5])], [0], ['clew'],
             {'kind': 'sail', 'mast': key, 'sail': 'gaff'}, ['tack', 'head', 'clew'])
        bel = 'belay-%s-lateen' % key
        for s_ in ('S', 'P'):
            rope('%s.sheet-%s' % (nm, s_), 'sail:%s/clew' % nm, '船殼/%s-%s' % (bel, s_), 'running/sheets', T['sheet'], 1.03, C['running'], {'kind': 'sheet', 'sail': nm})
        deck = SL['lateen_tack'][key][0]
        rope('%s.tack' % nm, 'sail:%s/tack' % nm, '甲板-%s/tack-%s' % (deck, key), 'running/tacks', T['tack'], 1.0, C['running'], {'kind': 'tack', 'sail': nm})
    # 旗
    FL = RG['flags']
    ew, eh = FL['ensign']
    LAT = json.load(open(os.path.join(design, 'yards_lateen.json'), encoding='utf-8'))
    pk_loc = LAT['bonaventure']['anchors']['peak']
    pyp = next(y for y in YP if y['name'] == 'yard-bonaventure-lateen')
    pk = np.array(pyp['at']) + (np.array(pk_loc, float) + 0.5 - np.array(pyp['pivot']))
    sail('ensign', ['model:bonaventure/yard-bonaventure-lateen/peak', fmt(pk - [ew, 0, 0]), fmt(pk - [ew, 0, eh]),
                    'model:bonaventure/yard-bonaventure-lateen/%d,%d,%d' % (pk_loc[0], pk_loc[1], pk_loc[2] - eh)],
         [3], [2, 1], {'kind': 'flag', 'flag': 'ensign'}, None, fullness=1.04, color='#ffffff', texture='textures/ensign.png')
    tz = math.floor(M['main']['truck'])
    tx = ax('main', tz)
    pl_, ph = FL['pennant']
    sail('pennant', [fmt([tx + 0.5, YC + 0.5, tz - 1]), fmt([tx - pl_, YC + 0.5, tz - 2]), fmt([tx + 0.5, YC + 0.5, tz - 1 - ph])],
         [2], [1], {'kind': 'flag', 'flag': 'pennant', 'mast': 'main'}, None, fullness=1.04, color=FL['pennant_color'])
    cross_png(os.path.join(design, 'textures', 'ensign.png'), 36, 24, (245, 245, 240, 255), (190, 20, 30, 255))
    cross_png(os.path.join(design, 'textures', 'cross_course.png'), 64, 56, (242, 234, 216, 255), (170, 25, 35, 255))

    metas = [['sail', s['name'], s['meta']] for s in sails] + [['rope', r['name'], r['meta']] for r in ropes if r['meta']]
    if probe:
        nm = probe[0].split('=')[1]
        metas = [m for m in metas if not (m[0] == 'rope' and m[1] == nm)]
    # ── 讀數 ──
    names = [r['name'] for r in ropes]
    need = [r['name'] for r in ropes if r['name'].split('.')[0] in {s['name'] for s in sails} and '.' in r['name']]
    have = {m[1] for m in metas if m[0] == 'rope'}
    R = {'channels': {'cells': len(chan), 'skipped_on_ship': skipped, 'mirror_diff': sum(1 for (x, y, z), c in chan.items() if chan.get((x, 2 * YC - y, z)) != c)},
         'anchors': {k: len(v) for k, v in anchors.items()}, 'ropes': len(ropes), 'ratlines': nrat,
         'groups': {g: sum(1 for r in ropes if r['group'] == g) for g in sorted({r['group'] for r in ropes})},
         'sails': len(sails), 'meta': {'sails': sum(1 for m in metas if m[0] == 'sail'), 'ropes': len(have)},
         'sail_ropes_without_meta': sorted(set(need) - have), 'dup_rope_names': len(names) - len(set(names)),
         'anchors_in_solid': sorted('%s/%s' % (k, n) for k, v in anchors.items() for n, p in v.items() if tuple(p) in occ and k not in ('hull', 'espolon'))}
    if probe:
        print(json.dumps({'probe': probe[0], 'sail_ropes_without_meta': R['sail_ropes_without_meta']}, ensure_ascii=False))
        return
    os.makedirs(os.path.join(design, 'masks', 'rigging'), exist_ok=True)
    p = os.path.join(design, 'masks', 'rigging', 'channels.vox.txt')
    with open(p, 'w', encoding='utf-8', newline='\n') as f:
        f.write('# 收穫號 channels 兩舷（支索板＋deadeye；世界座標，at 0,0,0）\n')
        for k in sorted(chan):
            f.write('%d,%d,%d,%d\n' % (k[0], k[1], k[2], chan[k]))
    R['channels']['sha256'] = hashlib.sha256(open(p, 'rb').read()).hexdigest()
    works = {'hull': 'calli-cosecha-01m', 'channels': 'calli-cosecha-01m-channels', 'bowsprit': 'calli-cosecha-01m-bowsprit', 'espolon': 'calli-cosecha-01m-espolon',
             'deck-puente': 'calli-cosecha-01m-deck-puente', 'deck-toldilla': 'calli-cosecha-01m-deck-toldilla'}
    for k in ('fore', 'main', 'mizzen', 'bonaventure'):
        works[k] = 'calli-cosecha-01m-mast-' + k
    out = {'anchors': anchors, 'anchor_works': works, 'ropes': ropes, 'sails': sails, 'meta': metas, 'wind': RG['wind'], 'sail_seconds': RG['sail_seconds']}
    with open(os.path.join(design, 'rigging_plan.json'), 'w', encoding='utf-8', newline='\n') as f:
        json.dump(out, f, ensure_ascii=False, indent=1, default=lambda o: o.item())
    with open(os.path.join(design, 'verify_rigging.json'), 'w', encoding='utf-8', newline='\n') as f:
        json.dump(R, f, ensure_ascii=False, indent=1, default=lambda o: o.item())
    print(json.dumps(R, ensure_ascii=False, default=lambda o: o.item()))


if __name__ == '__main__':
    main()
