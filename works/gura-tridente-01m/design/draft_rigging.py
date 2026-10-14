# 三叉戟號 階段七（TASK-0560）索具與帆：channels（右舷一件＋鏡像）、桅／艏斜桅／船殼的固定點、靜索、ratlines、帆（方帆、spanker、三角帆）、帆自己的繩、旗、meta
#   輸入：plan.json（rigging、masts、masts_build）＋ verify_masts.json（帆桁模型上的點，世界座標）＋ 現況（deco_base.stage7_base：船殼＋甲板＋階段五＋桅）
#   輸出：masks/rigging/channels.vox.txt（子作品座標）、rigging_plan.json（channels 框與固定點、各作品的固定點、繩、帆、meta）、textures/ensign.png、verify_rigging.json
#   用法：python -I -X utf8 draft_rigging.py <design> [--base=<快取.npz>]
import sys, os, json, math
import numpy as np
from PIL import Image

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import hull_lines as HL
import layout as LY
import deco_base as DB

YC = 200
LINK = {'main': '主桅', 'fore': '前桅', 'mizzen': '後桅', 'bowsprit': '艏斜桅'}


def ensign_png(path):
    """西班牙海軍旗（1785）：紅黃紅（1:2:1）＋黃帶上靠旗桿那側一面簡化的盾與冠（像素畫 60×40）。"""
    W, H = 60, 40
    red, yel, gold, white, dark = (198, 11, 30), (255, 196, 0), (201, 151, 0), (240, 240, 240), (120, 0, 10)
    im = Image.new('RGBA', (W, H), red)
    px = im.load()
    for y in range(10, 30):
        for x in range(W):
            px[x, y] = yel
    # 盾（中心 x 15、y 21；寬 10、高 12）：四分（紅／白）＋金邊
    for y in range(15, 28):
        for x in range(10, 21):
            dx, dy = x - 15, y - 21
            inside = abs(dx) <= 5 and (dy <= 3 or abs(dx) <= 5 - (dy - 3))
            if not inside:
                continue
            edge = abs(dx) == 5 or dy == -6 or (dy > 3 and abs(dx) == 5 - (dy - 3))
            q = (dx < 0) == (dy < 0)
            px[x, y] = gold if edge else (dark if q else white)
    for x in range(11, 20):                                          # 冠
        px[x, 13] = gold
    for x in (11, 13, 15, 17, 19):
        px[x, 12] = gold
    px[15, 11] = gold
    im.save(path)


def main():
    sys.stdout.reconfigure(encoding='utf-8')
    design = sys.argv[1]
    cache = next((a.split('=', 1)[1] for a in sys.argv[2:] if a.startswith('--base=')), None)
    plan = HL.load_plan(design)
    RG = plan['rigging']
    MB = plan['masts_build']
    if cache and os.path.exists(cache):
        G = np.load(cache)['G']
    else:
        G = DB.stage7_base()
        if cache:
            np.savez_compressed(cache, G=G)
    S = G > 0
    VM = json.load(open(os.path.join(design, 'verify_masts.json'), encoding='utf-8'))
    YP = VM['yard_points']
    spars = {m['key']: m for m in LY.mast_spars(plan)}
    rows = {r['key']: r for r in plan['masts']['rows']}

    def ax(key, seg, z):
        """桅軸（跟 draft_masts.py 同一套：下桅照 layout，上桅、頂桅往前錯開）。"""
        r0, rt0, rg0 = MB['r'][key]
        rh = r0 * MB['taper']['lower_head']
        rth = rt0 * MB['taper']['top_head']
        a = float(LY.mast_axis_x(plan, key, z))
        if seg == 'lower':
            return a
        a += int(round(rh + rt0 + 0.5))
        if seg == 'top':
            return a
        return a + int(round(rth + rg0 + 0.5))

    def rad(key, seg, z):
        r0, rt0, rg0 = MB['r'][key]
        return {'lower': r0 * MB['taper']['lower_head'], 'top': rt0 * MB['taper']['top_head'], 'tg': rg0 * MB['taper']['tg_head']}[seg]

    def outer_dy(x, z):
        ys = np.nonzero(S[x, YC:YC + 120, z])[0]
        return int(ys.max()) if len(ys) else None

    def rail(x):
        """舷頂（右舷最外那一格）：(x, dy, z)。"""
        col = S[x, YC:YC + 120, :]
        z = int(np.nonzero(col.any(0))[0].max())
        return [x, int(np.nonzero(col[:, z])[0].max()), z]

    anchors = {'hull': {}, 'channels': {}, 'main': {}, 'fore': {}, 'mizzen': {}, 'bowsprit': {}}
    # ── channels（右舷一件）：每根桅一塊板（上甲板砲門頂往上）、外緣一排 deadeye ──
    CH = RG['channels']
    chan = {}
    dead = {}
    for key in ('main', 'fore', 'mizzen'):
        n = CH['shrouds'][key] + CH['backstays'][key] + 1
        x0 = rows[key]['x'] + CH['fwd']
        zc = int(LY.deck_z(plan, 'spar', rows[key]['x'])) + CH['above_deck']
        xs = [x0 - i * CH['spacing'] for i in range(n)]
        lo_x, hi_x = min(xs) - 3, max(xs) + 3
        last = None
        out_by_x = {}
        for x in range(lo_x, hi_x + 1):
            o = [outer_dy(x, z) for z in (zc - 1, zc)]
            o = [v for v in o if v is not None]
            out_by_x[x] = max(o) if o else last
            last = out_by_x[x]
        for x in range(hi_x, lo_x - 1, -1):                             # 砲門那幾欄量不到 ⇒ 借旁邊那一欄
            if out_by_x[x] is None:
                out_by_x[x] = out_by_x.get(x + 1)
        for x in range(lo_x, hi_x + 1):
            o = out_by_x[x]
            for dy in range(o + 1, o + CH['width'] + 1):
                for z in (zc - 1, zc):
                    chan[(x, YC + dy, z)] = CH['color']
        dead[key] = []
        for i, x in enumerate(xs):
            dyo = out_by_x[x] + CH['width'] - 1
            for ddx in (-1, 0, 1):
                for z in range(zc + 1, zc + 4):
                    chan[(x + ddx, YC + dyo, z)] = CH['deadeye']
            dead[key].append([x, YC + dyo, zc + 3])
    over = sum(1 for k in chan if S[k])
    org, size = DB.bbox(chan)
    for key, pts in dead.items():
        for i, p in enumerate(pts, 1):
            anchors['channels']['deadeye-%s-%d' % (key, i)] = [p[0] - org[0], p[1] - org[1], p[2] - org[2]]
    # ── 桅上的點（世界座標：桅子作品 at 0,0,0）──
    for key in ('main', 'fore', 'mizzen'):
        sp = spars[key]
        A = anchors[key]
        zp, zxt, ztr = sp['platform'], sp['crosstrees'], sp['truck']
        zh = zp - 5
        rL = MB['r'][key][0] * (MB['taper']['lower_head'] + (1 - MB['taper']['lower_head']) * 0.1)
        for s_, sg in (('S', 1), ('P', -1)):
            A['hound-' + s_] = [int(round(ax(key, 'lower', zh))), YC + sg * (int(math.ceil(rL)) + 1), zh]
            A['futtock-' + s_] = [int(round(ax(key, 'lower', zp - 30))), YC + sg * (int(math.ceil(MB['r'][key][0])) + 1), zp - 30]
            rT = MB['r'][key][1]
            A['tm-hound-' + s_] = [int(round(ax(key, 'top', zxt - 4))), YC + sg * (int(math.ceil(rT * MB['taper']['top_head'])) + 1), zxt - 4]
        A['stay-head'] = [int(round(ax(key, 'lower', zh) + MB['r'][key][0] * MB['taper']['lower_head'])) + 1, YC, zh]
        A['tm-stay-head'] = [int(round(ax(key, 'top', zxt - 4) + rad(key, 'top', zxt))) + 1, YC, zxt - 4]
        ztg = (sp['yard_z']['topgallant'] + ztr) // 2
        A['tg-stay-head'] = [int(round(ax(key, 'tg', ztg) + MB['r'][key][2])) + 1, YC, ztg]
        for s_, sg in (('S', 1), ('P', -1)):
            A['tg-hound-' + s_] = [int(round(ax(key, 'tg', ztg))), YC + sg * (int(math.ceil(MB['r'][key][2])) + 1), ztg]
        W, Dp = MB['top'][key]
        xc = ax(key, 'lower', zp)
        hw = W / 2.0
        A['top-aft'] = [int(math.ceil(xc - (1 - MB['top']['fwd']) * Dp)), YC, zp]
        ntm = RG['topmast_shrouds'][key]
        for i in range(ntm):
            x = int(round(xc - 0.25 * Dp + i * (0.45 * Dp) / max(1, ntm - 1)))
            for s_, sg in (('S', 1), ('P', -1)):
                A['rim-%s-%d' % (s_, i + 1)] = [x, YC + sg * (int(hw) - 1), zp]
                A['rim-low-%s-%d' % (s_, i + 1)] = [x, YC + sg * (int(hw) - 1), zp - 1]
        spread = MB['crosstrees'][key]
        for j, dx in enumerate((-4, 4)):
            for s_, sg in (('S', 1), ('P', -1)):
                A['xtree-%s-%d' % (s_, j + 1)] = [int(round(ax(key, 'top', zxt) + dx)), YC + sg * spread, zxt]
        A['xtree-aft'] = [int(round(ax(key, 'top', zxt) - 4)), YC, zxt]
    # 主桅、前桅腳（mizzen stay、main stay 的下端）
    for key, nm in (('fore', 'mainstay-foot'), ('main', 'mizzenstay-foot')):
        z = int(LY.deck_z(plan, 'spar', rows[key]['x'])) + 3
        anchors[key][nm] = [int(math.floor(ax(key, 'lower', z) - MB['r'][key][0])) - 1, YC, z]
    # ── 艏斜桅上的點 ──
    BS = plan['masts']['bowsprit']
    BB = MB['bowsprit']
    ang = math.radians(BS['angle_deg'])
    u = np.array([math.cos(ang), 0.0, math.sin(ang)])
    w = np.array([-math.sin(ang), 0.0, math.cos(ang)])
    Hh = np.array([BS['heel_x'], YC, BS['heel_z']], float)
    Lb = BS['length']
    rb = lambda s: BB['r'][0] + (BB['r'][1] - BB['r'][0]) * s / Lb
    cell = lambda p: [int(round(p[0])), int(round(p[1])), int(round(p[2]))]
    B = anchors['bowsprit']
    B['forestay-foot'] = cell(Hh + 0.3 * Lb * u + (rb(0.3 * Lb) + 1) * w)
    B['cap-top'] = cell(Hh + (Lb - 2) * u + (rb(Lb) + 2.2) * w)
    sj0 = Lb * BB['jib_start']
    Jh = Hh + sj0 * u + (BB['r'][0] + (BB['r'][1] - BB['r'][0]) * BB['jib_start'] + BB['jib_r'][0]) * w
    B['jib-end'] = cell(Jh + (BS['jibboom'] - 2) * u + (BB['jib_r'][1] + 1) * w)
    for s_, sg in (('S', 1), ('P', -1)):
        p = Hh + 0.45 * Lb * u
        B['side-' + s_] = cell(p + np.array([0, sg * (rb(0.45 * Lb) + 1), 0]))
    for i, f in enumerate((0.55, 0.66, 0.77), 1):
        B['bob-%d' % i] = cell(Hh + f * Lb * u - (rb(f * Lb) + 1) * w)
    # ── 船殼上的點（兩舷各一）：帆腳索與 tack 的 belay、艏斜桅 shroud ──
    H = anchors['hull']
    for nm, x in RG['belay'].items():
        p = rail(x)
        H['belay-%s-S' % nm] = [p[0], YC + p[1], p[2]]
        H['belay-%s-P' % nm] = [p[0], YC - p[1], p[2]]
    for s_, sg in (('S', 1), ('P', -1)):
        x, z = RG['bowsprit_shroud_hull']
        H['bs-shroud-' + s_] = [x, YC + sg * outer_dy(x, z), z]

    # ── 繩 ──
    ropes = []
    C = RG['colors']

    def rope(name, a, b, group, th, slack=1.0, color=None, meta=None):
        ropes.append({'name': name, 'from': a, 'to': b, 'group': group, 'thickness': th, 'slack': slack, 'color': color or C['standing'], 'meta': meta})
    for key in ('main', 'fore', 'mizzen'):
        L = LINK[key]
        ns, nb = CH['shrouds'][key], CH['backstays'][key]
        for s_, chl in (('S', 'channels'), ('P', 'channels-鏡像')):
            for i in range(1, ns + 1):
                rope('%s-shroud-%s-%d' % (key, s_, i), '%s/deadeye-%s-%d' % (chl, key, i), '%s/hound-%s' % (L, s_), 'standing/shrouds', RG['thick']['shroud'][key])
            for i in range(1, RG['topmast_shrouds'][key] + 1):
                rope('%s-topmast-shroud-%s-%d' % (key, s_, i), '%s/rim-%s-%d' % (L, s_, i), '%s/tm-hound-%s' % (L, s_), 'standing/topmast-shrouds', RG['thick']['topmast_shroud'])
                rope('%s-futtock-%s-%d' % (key, s_, i), '%s/rim-low-%s-%d' % (L, s_, i), '%s/futtock-%s' % (L, s_), 'standing/futtock-shrouds', RG['thick']['futtock'])
            for j in (1, 2):
                rope('%s-topgallant-shroud-%s-%d' % (key, s_, j), '%s/xtree-%s-%d' % (L, s_, j), '%s/tg-hound-%s' % (L, s_), 'standing/topgallant-shrouds', RG['thick']['tg_shroud'])
            for b in range(1, nb + 1):
                rope('%s-topmast-backstay-%s-%d' % (key, s_, b), '%s/deadeye-%s-%d' % (chl, key, ns + b), '%s/tm-hound-%s' % (L, s_), 'standing/backstays', RG['thick']['backstay'])
            rope('%s-topgallant-backstay-%s' % (key, s_), '%s/deadeye-%s-%d' % (chl, key, ns + nb + 1), '%s/tg-hound-%s' % (L, s_), 'standing/backstays', RG['thick']['tg_backstay'])
    stays = [('fore-stay', '前桅/stay-head', '艏斜桅/forestay-foot', RG['thick']['stay']),
             ('fore-topmast-stay', '前桅/tm-stay-head', '艏斜桅/cap-top', RG['thick']['tm_stay']),
             ('jib-stay', '前桅/tg-stay-head', '艏斜桅/jib-end', RG['thick']['tg_stay']),
             ('main-stay', '主桅/stay-head', '前桅/mainstay-foot', RG['thick']['stay']),
             ('main-topmast-stay', '主桅/tm-stay-head', '前桅/top-aft', RG['thick']['tm_stay']),
             ('main-topgallant-stay', '主桅/tg-stay-head', '前桅/xtree-aft', RG['thick']['tg_stay']),
             ('mizzen-stay', '後桅/stay-head', '主桅/mizzenstay-foot', RG['thick']['tm_stay']),
             ('mizzen-topmast-stay', '後桅/tm-stay-head', '主桅/top-aft', RG['thick']['tg_stay']),
             ('mizzen-topgallant-stay', '後桅/tg-stay-head', '主桅/xtree-aft', RG['thick']['tg_stay'])]
    for nm, a, b, th in stays:
        rope(nm, a, b, 'standing/stays', th)
    for i in (1, 2, 3):
        rope('bobstay-%d' % i, '船頭-knee/bobstay-%d' % i, '艏斜桅/bob-%d' % i, 'standing/bowsprit', RG['thick']['bobstay'])
    for s_ in ('S', 'P'):
        rope('bowsprit-shroud-' + s_, '船殼/bs-shroud-' + s_, '艏斜桅/side-' + s_, 'standing/bowsprit', RG['thick']['bobstay'])
    # ratlines：一階一條子繩，從第一根 shroud 拉到最後一根（同一個比例 ⇒ 同一個高度）
    RL = RG['ratlines']

    def wpt(spec):
        frame, nm = spec.split('/', 1)
        if frame in ('channels', 'channels-鏡像'):
            a = anchors['channels'][nm]
            p = [a[0] + org[0], a[1] + org[1], a[2] + org[2]]
            if frame == 'channels-鏡像':
                p[1] = 2 * YC - p[1]
            return np.array(p, float) + 0.5
        key = {v: k for k, v in LINK.items()}.get(frame)
        if key:
            return np.array(anchors[key][nm], float) + 0.5
        if frame == '船殼':
            return np.array(anchors['hull'][nm], float) + 0.5
        raise KeyError(spec)
    nrat = 0
    for key in ('main', 'fore', 'mizzen'):
        for s_ in ('S', 'P'):
            for kind, first, last, every, start, th in (
                    ('lower', '%s-shroud-%s-1' % (key, s_), '%s-shroud-%s-%d' % (key, s_, CH['shrouds'][key]), RL['lower_every'], RL['start'], RL['lower_th']),
                    ('topmast', '%s-topmast-shroud-%s-1' % (key, s_), '%s-topmast-shroud-%s-%d' % (key, s_, RG['topmast_shrouds'][key]), RL['topmast_every'], 3, RL['topmast_th'])):
                ra = next(r for r in ropes if r['name'] == first)
                rb_ = next(r for r in ropes if r['name'] == last)
                La = np.linalg.norm(wpt(ra['to']) - wpt(ra['from']))
                Lb_ = np.linalg.norm(wpt(rb_['to']) - wpt(rb_['from']))
                d = start
                k = 1
                while d < La * RL['stop']:
                    t = d / La
                    pa = wpt(ra['from']) + t * (wpt(ra['to']) - wpt(ra['from']))
                    pb = wpt(rb_['from']) + (d / Lb_) * (wpt(rb_['to']) - wpt(rb_['from']))
                    if np.linalg.norm(pa - pb) >= RL['min_len']:
                        rope('ratline-%s-%s-%s-%02d' % (kind, key, s_, k), 'rope:%s/%.4f' % (first, t), 'rope:%s/%.4f' % (last, min(1.0, d / Lb_)),
                             'ratlines/' + kind, th)
                        nrat += 1
                    d += every
                    k += 1
    # ── 帆 ──
    sails = []
    SL = RG['sails']

    def ypt(yard, nm):
        return np.array(YP[yard][nm], float)

    def sail(name, corners, bind, free, meta, fullness=None, color=None, texture=None, names=None):
        sails.append({'name': name, 'corners': corners, 'corner_names': names, 'bind': bind, 'free': free, 'meta': meta,
                      'fullness': fullness or SL['fullness'], 'color': color or SL['color'], 'texture': texture})
    below = {'topsail': 'course', 'topgallant': 'topsail', 'royal': 'topgallant'}
    for key in ('fore', 'main', 'mizzen'):
        for yk in ('course', 'topsail', 'topgallant', 'royal'):
            yard = '%s-%s' % (key, yk)
            if yard not in YP:
                continue
            L = LINK[key]
            hp, hs = 'model:%s/yard-%s/earing-P' % (L, yard), 'model:%s/yard-%s/earing-S' % (L, yard)
            if yk == 'course':
                cps = []
                for s_ in ('S', 'P'):
                    e = ypt(yard, 'earing-' + s_)
                    pv = ypt(yard, 'pivot')
                    p = pv + SL['course_in'] * (e - pv)
                    p[2] = SL['course_clew_z']
                    cps.append('%.2f,%.2f,%.2f' % tuple(p))
            else:
                lower = '%s-%s' % (key, below[yk]) if key != 'mizzen' or yk != 'topsail' else 'mizzen-crossjack'
                cps = []
                for s_ in ('S', 'P'):
                    e = ypt(lower, 'earing-' + s_)
                    pv = ypt(lower, 'pivot')
                    p = e + SL['clew_in'] * (pv - e)
                    p[2] += 2
                    cps.append('%.2f,%.2f,%.2f' % tuple(p))
            sail(yard, [hp, hs, cps[0], cps[1]], [0], ['clew_s', 'clew_p'], {'kind': 'sail', 'mast': key, 'sail': yk},
                 names=['head_p', 'head_s', 'clew_s', 'clew_p'])
            if yk == 'course':
                for s_, c in (('S', 'clew_s'), ('P', 'clew_p')):
                    rope('%s.sheet-%s' % (yard, s_), 'sail:%s/%s' % (yard, c), '船殼/belay-%s-sheet-%s' % (key, s_), 'running/sheets', RG['thick']['course_sheet'],
                         SL['course_sheet_slack'], C['running'], {'kind': 'sheet', 'sail': yard})
                    rope('%s.tack-%s' % (yard, s_), 'sail:%s/%s' % (yard, c), '船殼/belay-%s-tack-%s' % (key, s_), 'running/tacks', RG['thick']['course_sheet'],
                         SL['course_tack_slack'], C['running'], {'kind': 'tack', 'sail': yard})
            else:
                lower = '%s-%s' % (key, below[yk]) if key != 'mizzen' or yk != 'topsail' else 'mizzen-crossjack'
                for s_, c in (('S', 'clew_s'), ('P', 'clew_p')):
                    rope('%s.sheet-%s' % (yard, s_), 'sail:%s/%s' % (yard, c), 'model:%s/yard-%s/earing-%s' % (L, lower, s_), 'running/sheets',
                         RG['thick']['sheet'], 1.0, C['running'], {'kind': 'sheet', 'sail': yard})
    sail('spanker', ['model:後桅/yard-mizzen-gaff/throat', 'model:後桅/yard-mizzen-gaff/peak', 'model:後桅/yard-mizzen-boom/end', 'model:後桅/yard-mizzen-boom/jaws'],
         [0, 2, 3], [], {'kind': 'sail', 'mast': 'mizzen', 'sail': 'gaff'}, names=['throat', 'peak', 'clew', 'tack'])
    # 三角帆：tack 在 stay 下端、head 在 stay 上 75%（登記成前桅的固定點）、clew 自由，sheet 綁船頭舷頂兩舷
    for nm, stay, belay, meta in (('fore-topmast-staysail', 'fore-topmast-stay', 'fts', {'kind': 'sail', 'mast': 'fore', 'sail': 'staysail', 'set': 2}),
                                  ('jib', 'jib-stay', 'jib', {'kind': 'sail', 'mast': 'bowsprit', 'sail': 'jib'})):
        st = next(r for r in ropes if r['name'] == stay)
        st['slack'] = 1.0
        top, foot = wpt(st['from']), wpt(st['to'])
        head = foot + SL['jib_head'] * (top - foot)
        anchors['fore'][nm + '.head'] = [int(math.floor(head[0])), int(math.floor(head[1])), int(math.floor(head[2]))]
        clew = foot + SL['jib_clew'][0] * (top - foot)
        clew[0] -= SL['jib_clew'][1]
        clew[2] -= SL['jib_clew'][2]
        sail(nm, [st['to'], '前桅/%s.head' % nm, '%.2f,%.2f,%.2f' % tuple(clew)], [0], ['clew'], meta, fullness=SL['jib_fullness'], names=['tack', 'head', 'clew'])
        for s_ in ('S', 'P'):
            rope('%s.sheet-%s' % (nm, s_), 'sail:%s/clew' % nm, '船殼/belay-%s-%s' % (belay, s_), 'running/sheets', RG['thick']['sheet'], 1.0, C['running'],
                 {'kind': 'sheet', 'sail': nm})
    # 旗：船尾旗掛 gaff 頂（旗桿那一邊跟著 gaff 走）、長旗掛主桅頂
    FL = RG['flags']
    pk = ypt('mizzen-gaff', 'peak')
    MPL = json.load(open(os.path.join(design, 'masts_placement.json'), encoding='utf-8'))
    peak_local = next(y for y in MPL['yards'] if y['name'] == 'mizzen-gaff')['anchors']['peak']
    ew, eh = FL['ensign']
    sail('ensign', ['model:後桅/yard-mizzen-gaff/peak', '%.2f,%.2f,%.2f' % (pk[0] - ew, pk[1], pk[2]), '%.2f,%.2f,%.2f' % (pk[0] - ew, pk[1], pk[2] - eh),
                    'model:後桅/yard-mizzen-gaff/%d,%d,%d' % (peak_local[0], peak_local[1], peak_local[2] - eh)],
         [3], [2, 1], {'kind': 'flag', 'flag': 'ensign'}, color=FL['ensign_color'], texture='textures/ensign.png', fullness=1.04)
    tz = spars['main']['truck']
    tx = ax('main', 'tg', tz)
    pl_, ph = FL['pennant']
    sail('pennant', ['%.2f,%.2f,%.2f' % (tx + 0.5, YC + 0.5, tz - 1), '%.2f,%.2f,%.2f' % (tx - pl_, YC + 0.5, tz - 2), '%.2f,%.2f,%.2f' % (tx + 0.5, YC + 0.5, tz - 1 - ph)],
         [2], [1], {'kind': 'flag', 'flag': 'pennant', 'mast': 'main'}, color=FL['pennant_color'], fullness=1.04)
    os.makedirs(os.path.join(design, 'textures'), exist_ok=True)
    ensign_png(os.path.join(design, 'textures', 'ensign.png'))

    # ── 讀數與寫檔 ──
    n, h = DB.write_local(os.path.join(design, 'masks', 'rigging', 'channels.vox.txt'), chan, org, '# 三叉戟號 channels 右舷（三塊板＋deadeye；子作品座標，左舷 ＝ mirror=y 關聯）\n')
    groups = {}
    for r in ropes:
        groups[r['group']] = groups.get(r['group'], 0) + 1
    metas = []
    for s in sails:
        metas.append(['sail', s['name'], s['meta']])
    for r in ropes:
        if r['meta']:
            metas.append(['rope', r['name'], r['meta']])
    names = [r['name'] for r in ropes]
    R = {'channels': {'cells': n, 'sha256': h, 'at': org, 'size': size, 'at_mirror': [org[0], DB.mirror_at_y(org[1], size[1]), org[2]], 'overlap_base': over},
         'anchors': {k: len(v) for k, v in anchors.items()}, 'ropes': len(ropes), 'ratlines': nrat, 'groups': groups, 'sails': len(sails),
         'meta': {'sails': sum(1 for m in metas if m[0] == 'sail'), 'ropes': sum(1 for m in metas if m[0] == 'rope')}, 'dup_rope_names': len(names) - len(set(names))}
    out = {'channels': {'work': 'gura-tridente-01m-channels', 'title': '三叉戟號 channels（右舷一件）', 'at': org, 'size': size, 'at_mirror': R['channels']['at_mirror'],
                        'links': ['channels', 'channels-鏡像']},
           'anchors': anchors, 'anchor_works': {'hull': 'gura-tridente-01m', 'channels': 'gura-tridente-01m-channels', 'main': 'gura-tridente-01m-mast-main',
                                                'fore': 'gura-tridente-01m-mast-fore', 'mizzen': 'gura-tridente-01m-mast-mizzen', 'bowsprit': 'gura-tridente-01m-bowsprit'},
           'ropes': ropes, 'sails': sails, 'meta': metas, 'wind': RG['wind'], 'sail_seconds': RG['sail_seconds']}
    with open(os.path.join(design, 'rigging_plan.json'), 'w', encoding='utf-8', newline='\n') as f:
        json.dump(out, f, ensure_ascii=False, indent=1, default=lambda o: o.item())
    with open(os.path.join(design, 'verify_rigging.json'), 'w', encoding='utf-8', newline='\n') as f:
        json.dump(R, f, ensure_ascii=False, indent=1, default=lambda o: o.item())
    print(json.dumps(R, ensure_ascii=False, default=lambda o: o.item()))


if __name__ == '__main__':
    main()
