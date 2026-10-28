# 出處：erina-oxford-01m/design/draft_rigging.py（TASK-0972 牛津號；TASK-1097 抄來改成信風號 brig）
# 信風號 階段七（TASK-0972）：channels（兩舷一件）、桅／艏斜桅／船殼／甲板的固定點、靜索、ratlines（橫繩組）、帆、帆自己的繩、旗、meta
#   輸入：plan.json（rigging、rig_build、masts）＋ verify_masts.json（每節桅的前移量）＋ 組裝件現在的格子與 parts（CLI 匯出：帆桁模型的固定點世界座標）
#   輸出：masks/rigging/channels.vox.txt、rigging_plan.json（固定點、繩、橫繩組、帆、meta）、textures/*.png、verify_rigging.json
#   用法：python -I -X utf8 draft_rigging.py <design> [--probe=nometa=<繩名>]（反向對照：拿掉一條繩的 meta；⛔ 不寫檔）
#   來源：calli-cosecha-01m/design/draft_rigging.py（channels＋deadeye、桅上的 hound／stay-head、帆角綁帆桁模型、帆自己的繩帶 meta）；
#         本船改的：帆桁模型的點從 parts 匯出讀（不自己算旋轉）、ratlines 用橫繩組（climb=1 的落腳點照甲板與桅樓量）、英國紅 ensign。
import sys, os, json, math, hashlib, subprocess, tempfile
import numpy as np
from PIL import Image

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), 'tools'))
import lines as HL
import layout as LY
from wio import export_list

HULL = 'erina-tradewind-01m'
ASM = HULL + '-assembly'
LINK = {'fore': '前桅', 'main': '主桅', 'mizzen': '後桅', 'bowsprit': '艏斜桅'}


def parts_points():
    with tempfile.TemporaryDirectory() as d:
        out = os.path.join(d, 'p.json').replace('\\', '/')
        r = subprocess.run(['senate', 'cmd', 'sculpture', '--arg', 'op=export', '--arg', 'format=parts', '--arg', 'work=' + ASM, '--arg', 'out=' + out],
                           capture_output=True, text=True, encoding='utf-8', errors='replace')
        if r.returncode != 0:
            raise SystemExit(r.stdout[-800:])
        P = json.load(open(out, encoding='utf-8'))
    return {m['path']: m['points'] for m in P['models']}


def ensign_png(path, W, H):
    """英國紅 ensign（1660 年代）：紅底、左上角白底紅聖喬治十字。"""
    im = Image.new('RGBA', (W, H), (200, 32, 30, 255))
    px = im.load()
    cw, ch = W * 5 // 12, H // 2
    for x in range(cw):
        for y in range(ch):
            px[x, y] = (245, 245, 240, 255)
            if abs(x - cw // 2) <= 1 or abs(y - ch // 2) <= 1:
                px[x, y] = (200, 32, 30, 255)
    im.save(path)


def main():
    sys.stdout.reconfigure(encoding='utf-8')
    design = sys.argv[1]
    probe = [a.split('=', 1)[1] for a in sys.argv[2:] if a.startswith('--probe')]
    plan = HL.load_plan(design)
    L = HL.Lines(plan)
    Y = LY.Layout(plan, L)
    YC = L.YC
    RG = plan['rigging']
    RB = plan['rig_build']
    MS = plan['masts']
    VM = json.load(open(os.path.join(design, 'verify_masts.json'), encoding='utf-8'))
    PP = parts_points()
    WORKS = os.path.dirname(os.path.dirname(os.path.abspath(design)))
    A = export_list(ASM, None, links=None)
    own = set()
    if os.path.exists(os.path.join(WORKS, HULL + '-channels', 'work.json')):
        own = set(map(tuple, export_list(HULL + '-channels', None)[:, :3].tolist()))
    occ = {tuple(r[:3]) for r in A.tolist()} - own
    hull = {tuple(r[:3]) for r in export_list(HULL, None).tolist()}
    hout = {}
    for x, y, z in hull:
        d = abs(y - YC)
        if d > hout.get((x, z), -1):
            hout[(x, z)] = d

    def top_z(x):
        return int(math.floor(float(L.top_z(x + 0.5)) + 0.5))

    def stage(key, i):
        nm, z0, z1, off = VM['masts'][key]['stages'][i]
        r = (MS[key]['r'] if i == 0 else MS[key + ('_top' if i == 1 else '_tg')]['r'])
        return z0, z1, off, r

    def mast_r(key, z, i=0):
        z0, z1, off, r = stage(key, i)
        return r[0] + (r[1] - r[0]) * (z - z0) / max(1, z1 - z0)

    def ax(key, z, i=0):
        return float(Y.mast_x(key, z + 0.5)) + stage(key, i)[2]

    anchors = {k: {} for k in ('hull', 'channels', 'fore', 'main', 'mizzen', 'bowsprit', 'deck-qd')}
    # ── channels（兩舷一件）＋ deadeye ──
    CH = RG['channels']
    chan, skipped = {}, 0
    for key in ('fore', 'main', 'mizzen'):
        xm = Y.masts[key]['x0']
        n = CH['shrouds'][key] + CH['backstays'].get(key, 0)
        xs = [xm - CH['first_aft'] - i * CH['spacing'] for i in range(n)]
        # 那一段船殼實際最上面那一列的最低處（照格子量，⛔ 照設計的舷頂線 top_z：差一格那幾欄量不到船殼 ⇒ deadeye 落在中線、浮空 2 塊）
        zc = min(max(z for (xx, z) in hout if xx == x) for x in range(min(xs) - 3, max(xs) + 4)) - CH['below_rail']
        for x in range(min(xs) - 3, max(xs) + 4):
            o = max(hout.get((x, z_), -1) for z_ in range(zc - CH.get('layers', 2) + 1, zc + 1))
            if o < 0:
                continue
            for dy in range(o + 1, o + CH['width'] + 1):
                for z in range(zc - CH.get('layers', 2) + 1, zc + 1):
                    for y in (YC + dy, YC - dy):
                        if (x, y, z) in occ:
                            skipped += 1
                        else:
                            chan[(x, y, z)] = RG['colors']['channel']
        for i, x in enumerate(xs, 1):
            o = max(hout.get((x, z_), -1) for z_ in range(zc - CH.get('layers', 2) + 1, zc + 1))
            assert o >= 0, ('deadeye 那一欄量不到船殼', key, i, x, zc)
            dyo = o + CH['width']
            for ddx in (-1, 0, 1):
                for z in range(zc + 1, zc + 4):
                    for y in (YC + dyo, YC - dyo):
                        chan[(x + ddx, y, z)] = RG['colors']['deadeye']
            anchors['channels']['deadeye-%s-S-%d' % (key, i)] = [x, YC + dyo, zc + 3]
            anchors['channels']['deadeye-%s-P-%d' % (key, i)] = [x, YC - dyo, zc + 3]
    # ── 桅上的點（桅子作品＝世界座標）──
    tops = {}
    for key in ('fore', 'main', 'mizzen'):
        A_ = anchors[key]
        zt = VM['masts'][key]['top_z']
        rt = RB['tops'][key]
        zh = zt - 5
        r = mast_r(key, zh)
        for s_, sg in (('S', 1), ('P', -1)):
            A_['hound-' + s_] = [int(round(ax(key, zh))), YC + sg * (int(math.ceil(r)) + 1), zh]
        A_['stay-head'] = [int(math.floor(ax(key, zh) + r)) + 1, YC, zh]
        zf = zt - 22
        for s_, sg in (('S', 1), ('P', -1)):
            A_['futtock-' + s_] = [int(round(ax(key, zf))), YC + sg * (int(math.ceil(mast_r(key, zf))) + 1), zf]
        off1 = stage(key, 1)[2]
        xc = float(Y.mast_x(key, zt + 0.5)) + off1 / 2.0
        tops[key] = (xc, zt, rt)
        for i, f in enumerate((-0.45, 0.0, 0.45), 1):
            dx = f * rt
            dy = int(math.ceil(math.sqrt(rt * rt - dx * dx))) + 1          # 桅樓外緣外第一格（v1 floor ⇒ 後桅樓 r 10 時前緣那兩點落在桅樓的格裡）
            for s_, sg in (('S', 1), ('P', -1)):
                A_['rim-%s-%d' % (s_, i)] = [int(math.floor(xc + dx + 0.5)), YC + sg * dy, zt - 1]
                A_['rim-low-%s-%d' % (s_, i)] = [int(math.floor(xc + dx + 0.5)), YC + sg * dy, zt - 2]
        A_['top-aft'] = [int(math.floor(xc - rt)) - 1, YC, zt - 1]
        # 上桅頭（crosstrees 下面）
        z0, z1, off, rr = stage(key, 1)
        head = MS[key + '_top']['head']
        ztm = z1 - head - 4 if head else z1 - 6
        rtm = mast_r(key, ztm, 1)
        for s_, sg in (('S', 1), ('P', -1)):
            A_['tm-hound-' + s_] = [int(round(ax(key, ztm, 1))), YC + sg * (int(math.ceil(rtm)) + 1), ztm]
        A_['tm-stay-head'] = [int(math.floor(ax(key, ztm, 1) + rtm)) + 1, YC, ztm]
    # 支索的下端
    zf = int(math.floor(float(L.deck_z('fc', 274)))) + 4
    anchors['fore']['mainstay-foot'] = [int(math.floor(ax('fore', zf) - mast_r('fore', zf))) - 1, YC, zf]
    zm = 62
    anchors['main']['mizzenstay-foot'] = [int(math.floor(ax('main', zm) - mast_r('main', zm))) - 1, YC, zm]
    # ── 艏斜桅上的點 ──
    b = MS['bowsprit']
    a = math.radians(b['steeve_deg'])
    u = np.array([math.cos(a), 0.0, math.sin(a)])
    w = np.array([-math.sin(a), 0.0, math.cos(a)])
    Hh = np.array([b['heel'][0] + 0.5, YC + 0.5, b['heel'][1]])
    Lb = b['len']
    rb = lambda s: b['r'][0] + (b['r'][1] - b['r'][0]) * s / Lb
    cell = lambda p: [int(math.floor(p[0])), int(math.floor(p[1])), int(math.floor(p[2]))]
    BA = anchors['bowsprit']
    BA['forestay-foot'] = cell(Hh + 0.45 * Lb * u + (rb(0.45 * Lb) + 1) * w)
    BA['cap-top'] = cell(Hh + (Lb - 3) * u + (rb(Lb) + 1.5) * w)
    for s_, sg in (('S', 1), ('P', -1)):
        BA['side-' + s_] = cell(Hh + 0.55 * Lb * u + np.array([0, sg * (rb(0.55 * Lb) + 1), 0]))
    BA['bob-1'] = cell(Hh + 0.55 * Lb * u - (rb(0.55 * Lb) + 1) * w)
    # ── 船殼上的點 ──
    def rail(x):
        z = max(zz for (xx, zz) in hout if xx == x)
        return [x, hout[(x, z)], z]
    H = anchors['hull']
    SL = RG['sails']
    belay = {}
    for key in ('fore', 'main'):
        xm = Y.masts[key]['x0']
        belay['%s-sheet' % key] = xm - SL['sheet_aft']
        belay['%s-tack' % key] = min(300, xm + SL['tack_fwd'])
    belay['sprit'] = 300
    belay['mizzen-lateen'] = 42
    for nm, x in belay.items():
        p = rail(x)
        H['belay-%s-S' % nm] = [p[0], YC + p[1], p[2]]
        H['belay-%s-P' % nm] = [p[0], YC - p[1], p[2]]
    # 艏斜桅 shroud、bobstay：船頭外板（艏柱前緣往下）
    xs_ = max(x for (x, z) in hout if z == 52)
    for s_, sg in (('S', 1), ('P', -1)):
        H['bs-shroud-' + s_] = [xs_ - 6, YC + sg * hout[(xs_ - 6, 56)], 56]
    zb = 40
    H['bobstay-1'] = [max(x for (x, z) in hout if z == zb), YC, zb]
    # 後桅三角帆 tack：帆桁前端正下方的後甲板
    lat = PP['後桅/yard-mizzen-lateen']
    fx = int(math.floor(lat['fore'][0]))
    anchors['deck-qd']['tack-mizzen'] = [fx, YC, int(math.floor(float(L.deck_z('qd', fx + 0.5)))) + 1]

    # ── 繩 ──
    C = RG['colors']
    T = RG['thick']
    ropes = []

    def rope(name, a_, b_, group, th, slack=1.0, color=None, meta=None):
        ropes.append({'name': name, 'from': a_, 'to': b_, 'group': group, 'thickness': th, 'slack': slack, 'color': color or C['standing'], 'meta': meta})
    for key in ('fore', 'main', 'mizzen'):
        Lk = LINK[key]
        ns, nb = CH['shrouds'][key], CH['backstays'].get(key, 0)
        for s_ in ('S', 'P'):
            for i in range(1, ns + 1):
                rope('%s-shroud-%s-%d' % (key, s_, i), '支索板/deadeye-%s-%s-%d' % (key, s_, i), '%s/hound-%s' % (Lk, s_), 'standing/shrouds', T['shroud'])
            for bb in range(1, nb + 1):
                rope('%s-topmast-backstay-%s-%d' % (key, s_, bb), '支索板/deadeye-%s-%s-%d' % (key, s_, ns + bb), '%s/tm-hound-%s' % (Lk, s_), 'standing/backstays', T['backstay'])
            for i in range(1, RG['topmast_shrouds'] + 1):
                rope('%s-topmast-shroud-%s-%d' % (key, s_, i), '%s/rim-%s-%d' % (Lk, s_, i), '%s/tm-hound-%s' % (Lk, s_), 'standing/topmast-shrouds', T['topmast_shroud'])
                rope('%s-futtock-%s-%d' % (key, s_, i), '%s/rim-low-%s-%d' % (Lk, s_, i), '%s/futtock-%s' % (Lk, s_), 'standing/futtock-shrouds', T['futtock'])
    for nm, a_, b_, th in (('fore-stay', '前桅/stay-head', '艏斜桅/forestay-foot', T['stay']),
                           ('fore-topmast-stay', '前桅/tm-stay-head', '艏斜桅/cap-top', T['tm_stay']),
                           ('main-stay', '主桅/stay-head', '前桅/mainstay-foot', T['stay']),
                           ('main-topmast-stay', '主桅/tm-stay-head', '前桅/top-aft', T['tm_stay']),
                           ('mizzen-stay', '後桅/stay-head', '主桅/mizzenstay-foot', T['tm_stay']),
                           ('mizzen-topmast-stay', '後桅/tm-stay-head', '主桅/top-aft', T['tm_stay'])):
        rope(nm, a_, b_, 'standing/stays', th)
    rope('bobstay-1', '船首喙/bobstay-1', '艏斜桅/bob-1', 'standing/bowsprit', T['bobstay'])      # 步驟 6 起綁在 cutwater 前緣（以前綁艏柱，會穿過 beakhead 平台）
    for s_ in ('S', 'P'):
        rope('bowsprit-shroud-' + s_, '船殼/bs-shroud-' + s_, '艏斜桅/side-' + s_, 'standing/bowsprit', T['bobstay'])
    # ── 橫繩組（ratlines；lower 是繩梯：foot 舷牆內側的甲板、head 桅樓靠這一舷的邊）──
    RL = RG['ratlines']
    ratl = []
    for key in ('fore', 'main', 'mizzen'):
        ns = CH['shrouds'][key]
        xm = Y.masts[key]['x0']
        xmid = xm - CH['first_aft'] - (ns - 1) * CH['spacing'] // 2
        SP = plan['decks_build']['spans']
        deck = next(d for d in ('poop', 'qd', 'fc', 'gun') if SP[d][0] <= xmid <= SP[d][1])   # 那一欄最上面的甲板
        zfl = int(math.floor(float(L.deck_z(deck, xmid + 0.5))))
        xc, zt, rt = tops[key]
        for s_, sg in (('S', 1), ('P', -1)):
            o = hout[(xmid, min(zfl + 4, top_z(xmid) - 1))]
            foot = [xmid, YC + sg * (o - 3 - 2), zfl + 1]
            head = [int(math.floor(xc + 0.5)), YC + sg * (rt - 2), zt]
            ratl.append({'name': '%s-lower-%s' % (key, s_), 'rope_a': '%s-shroud-%s-1' % (key, s_), 'rope_b': '%s-shroud-%s-%d' % (key, s_, ns),
                         'step': RL['step'], 'start': RL['start'], 'stop': RL['stop'], 'min_span': RL['min_span'], 'thickness': RL['th'],
                         'group': 'ratlines/lower', 'climb': 1, 'foot': '%d,%d,%d' % tuple(foot), 'head': '%d,%d,%d' % tuple(head)})
            ratl.append({'name': '%s-topmast-%s' % (key, s_), 'rope_a': '%s-topmast-shroud-%s-1' % (key, s_), 'rope_b': '%s-topmast-shroud-%s-%d' % (key, s_, RG['topmast_shrouds']),
                         'step': RL['tm_step'], 'start': RL['tm_start'], 'stop': RL['tm_stop'], 'min_span': RL['min_span'], 'thickness': RL['tm_th'],
                         'group': 'ratlines/topmast', 'climb': 0})
    # ── 帆 ──
    sails = []

    def sail(name, corners, bind, free, meta, names, fullness=None, color=None, texture=None):
        sails.append({'name': name, 'corners': corners, 'corner_names': names, 'bind': bind, 'free': free, 'meta': meta,
                      'fullness': fullness or SL['fullness'], 'color': color or C['sail'], 'texture': texture})
    fmt = lambda p: '%.2f,%.2f,%.2f' % tuple(p)
    pt = lambda path, k: np.array(PP[path][k], float)
    os.makedirs(os.path.join(design, 'textures'), exist_ok=True)
    for key in ('fore', 'main'):
        Lk = LINK[key]
        cy, ty, gy = 'yard-%s-course' % key, 'yard-%s-topsail' % key, 'yard-%s-topgallant' % key
        cps = []
        for s_ in ('S', 'P'):
            e, pv = pt(Lk + '/' + cy, 'earing-' + s_), pt(Lk + '/' + cy, 'pivot')
            p = pv + SL['course_in'] * (e - pv)
            p[2] = top_z(int(p[0])) + SL['course_clew_above_rail']
            cps.append(fmt(p))
        nm = '%s-course' % key
        sail(nm, ['model:%s/%s/earing-P' % (Lk, cy), 'model:%s/%s/earing-S' % (Lk, cy), cps[0], cps[1]], [0], ['clew_s', 'clew_p'],
             {'kind': 'sail', 'mast': key, 'sail': 'course'}, ['head_p', 'head_s', 'clew_s', 'clew_p'])
        for s_, c in (('S', 'clew_s'), ('P', 'clew_p')):
            rope('%s-sheet-%s' % (nm, s_), 'sail:%s/%s' % (nm, c), '船殼/belay-%s-sheet-%s' % (key, s_), 'running/sheets', T['course_sheet'], 1.02, C['running'], {'kind': 'sheet', 'sail': nm})
            rope('%s-tack-%s' % (nm, s_), 'sail:%s/%s' % (nm, c), '船殼/belay-%s-tack-%s' % (key, s_), 'running/tacks', T['tack'], 1.02, C['running'], {'kind': 'tack', 'sail': nm})
        for up, lo, kind in ((ty, cy, 'topsail'), (gy, ty, 'topgallant')):
            cps = []
            for s_ in ('S', 'P'):
                e, pv = pt(Lk + '/' + lo, 'earing-' + s_), pt(Lk + '/' + lo, 'pivot')
                p = e + SL['clew_in'] * (pv - e)
                p[2] += 2
                cps.append(fmt(p))
            nm = '%s-%s' % (key, kind)
            sail(nm, ['model:%s/%s/earing-P' % (Lk, up), 'model:%s/%s/earing-S' % (Lk, up), cps[0], cps[1]], [0], ['clew_s', 'clew_p'],
                 {'kind': 'sail', 'mast': key, 'sail': kind}, ['head_p', 'head_s', 'clew_s', 'clew_p'])
            for s_, c in (('S', 'clew_s'), ('P', 'clew_p')):
                rope('%s-sheet-%s' % (nm, s_), 'sail:%s/%s' % (nm, c), 'model:%s/%s/earing-%s' % (Lk, lo, s_), 'running/sheets', T['sheet'], 1.0, C['running'], {'kind': 'sheet', 'sail': nm})
    # 後上桅帆：帆腳綁 crossjack
    cps = []
    for s_ in ('S', 'P'):
        e, pv = pt('後桅/yard-crossjack', 'earing-' + s_), pt('後桅/yard-crossjack', 'pivot')
        p = e + SL['clew_in'] * (pv - e)
        p[2] += 2
        cps.append(fmt(p))
    sail('mizzen-topsail', ['model:後桅/yard-mizzen-topsail/earing-P', 'model:後桅/yard-mizzen-topsail/earing-S', cps[0], cps[1]], [0], ['clew_s', 'clew_p'],
         {'kind': 'sail', 'mast': 'mizzen', 'sail': 'topsail'}, ['head_p', 'head_s', 'clew_s', 'clew_p'])
    for s_, c in (('S', 'clew_s'), ('P', 'clew_p')):
        rope('mizzen-topsail-sheet-%s' % s_, 'sail:mizzen-topsail/%s' % c, 'model:後桅/yard-crossjack/earing-%s' % s_, 'running/sheets', T['sheet'], 1.0, C['running'], {'kind': 'sheet', 'sail': 'mizzen-topsail'})
    # spritsail
    cps = []
    for s_ in ('S', 'P'):
        e, pv = pt('艏斜桅/yard-spritsail', 'earing-' + s_), pt('艏斜桅/yard-spritsail', 'pivot')
        p = e + SL['clew_in'] * (pv - e)
        p[2] -= SL['sprit_drop']
        cps.append(fmt(p))
    sail('spritsail', ['model:艏斜桅/yard-spritsail/earing-P', 'model:艏斜桅/yard-spritsail/earing-S', cps[0], cps[1]], [0], ['clew_s', 'clew_p'],
         {'kind': 'sail', 'mast': 'bowsprit', 'sail': 'course', 'set': RG['sail_set']['spritsail']}, ['head_p', 'head_s', 'clew_s', 'clew_p'])
    for s_, c in (('S', 'clew_s'), ('P', 'clew_p')):
        rope('spritsail-sheet-%s' % s_, 'sail:spritsail/%s' % c, '船殼/belay-sprit-%s' % s_, 'running/sheets', T['sheet'], 1.02, C['running'], {'kind': 'sheet', 'sail': 'spritsail'})
    # 後桅三角帆：tack ＝ 帆桁前端、head ＝ peak、clew ＝ 帆桁後端下面（船尾舷頂上）
    pk = lat['peak']
    cx = int(math.floor(pk[0])) + SL['lateen_clew_dx']
    clew = [cx + 0.5, YC + 0.5, top_z(cx) + SL['lateen_clew_above_rail'] + 0.5]
    sail('mizzen-lateen', ['model:後桅/yard-mizzen-lateen/fore', 'model:後桅/yard-mizzen-lateen/peak', fmt(clew)], [0], ['clew'],
         {'kind': 'sail', 'mast': 'mizzen', 'sail': 'gaff'}, ['tack', 'head', 'clew'])
    for s_ in ('S', 'P'):
        rope('mizzen-lateen-sheet-%s' % s_, 'sail:mizzen-lateen/clew', '船殼/belay-mizzen-lateen-%s' % s_, 'running/sheets', T['sheet'], 1.03, C['running'], {'kind': 'sheet', 'sail': 'mizzen-lateen'})
    rope('mizzen-lateen-tack', 'sail:mizzen-lateen/tack', '甲板-qd/tack-mizzen', 'running/tacks', T['tack'], 1.0, C['running'], {'kind': 'tack', 'sail': 'mizzen-lateen'})
    # 旗
    FL = RG['flags']
    ew, eh = FL['ensign']
    DA = json.load(open(os.path.join(design, 'deco_anchors.json'), encoding='utf-8'))['ensign_staff']
    fh = np.array(DA['flag-head'], float) + 0.5                                   # 船尾旗桿（步驟 6；以前暫掛在後桅三角帆桁後端）
    sail('ensign', ['船尾旗桿/flag-head', fmt(fh - [ew, 0, 0]), fmt(fh - [ew, 0, eh]), '船尾旗桿/flag-foot'],
         [3], [2, 1], {'kind': 'flag', 'flag': 'ensign'}, None, fullness=1.04, color='#ffffff', texture='textures/ensign.png')
    tz = VM['masts']['main']['truck_z']
    tx = ax('main', tz, 2)
    pl_, ph = FL['pennant']
    sail('pennant', [fmt([tx + 0.5, YC + 0.5, tz - 1]), fmt([tx - pl_, YC + 0.5, tz - 2]), fmt([tx + 0.5, YC + 0.5, tz - 1 - ph])],
         [2], [1], {'kind': 'flag', 'flag': 'pennant', 'mast': 'main'}, None, fullness=1.04, color=FL['pennant_color'])
    ensign_png(os.path.join(design, 'textures', 'ensign.png'), 36, 24)

    metas = [['sail', s['name'], s['meta']] for s in sails] + [['rope', r['name'], r['meta']] for r in ropes if r['meta']]
    if probe:
        nm = probe[0].split('=')[1]
        metas = [m for m in metas if not (m[0] == 'rope' and m[1] == nm)]
    # ── 讀數 ──
    names = [r['name'] for r in ropes]
    sail_names = {s['name'] for s in sails if s['meta']['kind'] == 'sail'}
    need = [r['name'] for r in ropes if r['from'].startswith('sail:') or r['to'].startswith('sail:')]
    have = {m[1] for m in metas if m[0] == 'rope'}
    bad_sail_ref = [m[1] for m in metas if m[0] == 'rope' and m[2].get('sail') not in sail_names]
    R = {'channels': {'cells': len(chan), 'skipped_on_ship': skipped, 'mirror_diff': sum(1 for (x, y, z), c in chan.items() if chan.get((x, 2 * YC - y, z)) != c)},
         'anchors': {k: len(v) for k, v in anchors.items()}, 'ropes': len(ropes), 'ratline_groups': len(ratl),
         'groups': {g: sum(1 for r in ropes if r['group'] == g) for g in sorted({r['group'] for r in ropes})},
         'sails': len(sails), 'meta': {'sails': sum(1 for m in metas if m[0] == 'sail'), 'ropes': len(have)},
         'sail_ropes_without_meta': sorted(set(need) - have), 'rope_meta_sail_unknown': bad_sail_ref, 'dup_rope_names': len(names) - len(set(names)),
         'anchors_in_solid': sorted('%s/%s' % (k, n) for k, v in anchors.items() for n, p in v.items() if tuple(p) in occ and k not in ('hull',))}
    if probe:
        print(json.dumps({'probe': probe[0], 'sail_ropes_without_meta': R['sail_ropes_without_meta']}, ensure_ascii=False))
        return
    os.makedirs(os.path.join(design, 'masks', 'rigging'), exist_ok=True)
    p = os.path.join(design, 'masks', 'rigging', 'channels.vox.txt')
    with open(p, 'w', encoding='utf-8', newline='\n') as f:
        f.write('# 信風號 channels 兩舷（支索板＋deadeye；世界座標，at 0,0,0）\n')
        for k in sorted(chan):
            f.write('%d,%d,%d,%d\n' % (k[0], k[1], k[2], chan[k]))
    R['channels']['sha256'] = hashlib.sha256(open(p, 'rb').read()).hexdigest()
    works = {'hull': HULL, 'channels': HULL + '-channels', 'bowsprit': HULL + '-bowsprit', 'deck-qd': HULL + '-deck-qd'}
    for k in ('fore', 'main', 'mizzen'):
        works[k] = HULL + '-mast-' + k
    out = {'anchors': anchors, 'anchor_works': works, 'ropes': ropes, 'ratlines': ratl, 'sails': sails, 'meta': metas, 'wind': RG['wind'], 'sail_seconds': RG['sail_seconds']}
    with open(os.path.join(design, 'rigging_plan.json'), 'w', encoding='utf-8', newline='\n') as f:
        json.dump(out, f, ensure_ascii=False, indent=1, default=lambda o: o.item())
    with open(os.path.join(design, 'verify_rigging.json'), 'w', encoding='utf-8', newline='\n') as f:
        json.dump(R, f, ensure_ascii=False, indent=1, default=lambda o: o.item())
    print(json.dumps(R, ensure_ascii=False, default=lambda o: o.item()))


if __name__ == '__main__':
    main()
