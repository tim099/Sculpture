# 出處：erina-oxford-01m/design/draft_rigging.py（TASK-0972 牛津號；TASK-1097 抄來改成信風號 brig）
# 信風號 步驟 8（TASK-1097）：channels（兩舷一件）、桅／艏斜桅／船殼／甲板的固定點、靜索、ratlines（橫繩組）、帆、帆自己的繩、旗、meta
#   輸入：plan.json（rigging、rig_build、masts）＋ verify_masts.json（每節桅的前移量、三角帆桿的軸）＋ 組裝件現在的格子與 parts（CLI 匯出：帆桁模型的固定點世界座標）
#   輸出：masks/rigging/channels.vox.txt、rigging_plan.json（固定點、繩、橫繩組、帆、meta）、textures/*.png、verify_rigging.json
#   用法：python -I -X utf8 draft_rigging.py <design> [--probe=nometa=<繩名>]（反向對照：拿掉一條繩的 meta；⛔ 不寫檔）
#   跟牛津號不同：兩根桅；主桅沒有主橫帆（主上桅帆的帆腳綁 crossjack）；主帆 gaff＋boom 三條邊釘住（照飛魚號 gura-flyingfish-01m 的掛法）；
#   艏帆 ＝ 前支索帆（前支索）＋三角帆（前上桅支索 → 三角帆桿），head 在支索 75% 處；沒有斜桅帆、三角帆桁、船尾旗桿；船旗掛斜桁尖（1707 年以後的英國紅旗）。
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
LINK = {'fore': '前桅', 'main': '主桅', 'bowsprit': '艏斜桅'}


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
    """英國紅旗（red ensign，1707–1801）：紅底、左上角 Union（藍底、白斜十字、紅正十字白邊）。"""
    im = Image.new('RGBA', (W, H), (200, 32, 30, 255))
    px = im.load()
    cw, ch = W // 2, H // 2
    for x in range(cw):
        for y in range(ch):
            c = (20, 40, 110, 255)
            if abs(x * ch - y * cw) <= max(cw, ch) * 1.0 or abs(x * ch - (ch - 1 - y) * cw) <= max(cw, ch) * 1.0:
                c = (245, 245, 240, 255)                                   # 聖安德魯白斜十字
            if abs(x - cw // 2) <= 2 or abs(y - ch // 2) <= 2:
                c = (245, 245, 240, 255)                                   # 聖喬治十字的白邊
            if abs(x - cw // 2) <= 1 or abs(y - ch // 2) <= 1:
                c = (200, 32, 30, 255)                                     # 聖喬治紅十字
            px[x, y] = c
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
        return max(zz for (xx, zz) in hout if xx == x)          # 那一欄船殼實際最上一格（⛔ 照設計的舷頂線：小數那幾欄差一格）

    def stage(key, i):
        nm, z0, z1, off = VM['masts'][key]['stages'][i]
        r = (MS[key]['r'] if i == 0 else MS[key + ('_top' if i == 1 else '_tg')]['r'])
        return z0, z1, off, r

    def mast_r(key, z, i=0):
        z0, z1, off, r = stage(key, i)
        return r[0] + (r[1] - r[0]) * (z - z0) / max(1, z1 - z0)

    def ax(key, z, i=0):
        return float(Y.mast_x(key, z + 0.5)) + stage(key, i)[2]

    anchors = {k: {} for k in ('hull', 'channels', 'fore', 'main', 'bowsprit', 'deck-qd')}
    # ── channels（兩舷一件）＋ deadeye ──
    CH = RG['channels']
    chan, skipped = {}, 0
    for key in ('fore', 'main'):
        xm = Y.masts[key]['x0']
        n = CH['shrouds'][key] + CH['backstays'].get(key, 0)
        xs = [xm - CH['first_aft'] - i * CH['spacing'] for i in range(n)]
        zc = min(top_z(x) for x in range(min(xs) - 3, max(xs) + 4)) - CH['below_rail']
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
    for key in ('fore', 'main'):
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
        for i, f in enumerate((-0.4, 0.4), 1):
            dx = f * rt
            dy = int(math.ceil(math.sqrt(rt * rt - dx * dx))) + 1
            for s_, sg in (('S', 1), ('P', -1)):
                A_['rim-%s-%d' % (s_, i)] = [int(math.floor(xc + dx + 0.5)), YC + sg * dy, zt - 1]
                A_['rim-low-%s-%d' % (s_, i)] = [int(math.floor(xc + dx + 0.5)), YC + sg * dy, zt - 2]
        A_['top-aft'] = [int(math.floor(xc - rt)) - 1, YC, zt - 1]
        z0, z1, off, rr = stage(key, 1)
        head = MS[key + '_top']['head']
        ztm = z1 - head - 4 if head else z1 - 6
        rtm = mast_r(key, ztm, 1)
        for s_, sg in (('S', 1), ('P', -1)):
            A_['tm-hound-' + s_] = [int(round(ax(key, ztm, 1))), YC + sg * (int(math.ceil(rtm)) + 1), ztm]
        A_['tm-stay-head'] = [int(math.floor(ax(key, ztm, 1) + rtm)) + 1, YC, ztm]
    # 主支索的下端：前桅後面、艏樓甲板上 0.4 m
    zf = int(math.floor(float(L.deck_z('fc', Y.masts['fore']['x0'] + 0.5)))) + 4
    anchors['fore']['mainstay-foot'] = [int(math.floor(ax('fore', zf) - mast_r('fore', zf))) - 1, YC, zf]
    # ── 艏斜桅、三角帆桿上的點 ──
    b = MS['bowsprit']
    a = math.radians(b['steeve_deg'])
    u = np.array([math.cos(a), 0.0, math.sin(a)])
    w = np.array([-math.sin(a), 0.0, math.cos(a)])
    Hh = np.array([b['heel'][0] + 0.5, YC + 0.5, b['heel'][1]])
    Lb = b['len']
    rb = lambda s: b['r'][0] + (b['r'][1] - b['r'][0]) * s / Lb
    cell = lambda p: [int(math.floor(p[0])), int(math.floor(p[1])), int(math.floor(p[2]))]
    BA = anchors['bowsprit']
    fs = RG['sails']
    BA['forestay-foot'] = cell(Hh + plan['masts']['rig']['forestay_frac'] * Lb * u + (rb(0.3 * Lb) + 1) * w)
    BA['cap-top'] = cell(Hh + (Lb - 3) * u + (rb(Lb) + 2.5) * w)
    for s_, sg in (('S', 1), ('P', -1)):
        BA['side-' + s_] = cell(Hh + 0.55 * Lb * u + np.array([0, sg * (rb(0.55 * Lb) + 1), 0]))
    BA['bob-1'] = cell(Hh + 0.55 * Lb * u - (rb(0.55 * Lb) + 1) * w)
    jb = VM['jibboom']
    jp0, jp1 = np.array([jb['p0'][0], YC + 0.5, jb['p0'][1]]), np.array([jb['p1'][0], YC + 0.5, jb['p1'][1]])
    jrj = plan['masts']['jibboom']['r']
    BA['jib-end'] = cell(jp0 + plan['masts']['rig']['jibstay_frac'] * (jp1 - jp0) + (jrj[1] + 1.2) * w)
    # 支索上的帆頭（帆 head 綁支索 75% 那一格，Ship_Rigging §7）
    def on_line(pa, pb, f):
        return [int(math.floor(pa[i] + (pb[i] - pa[i]) * f)) for i in range(3)]
    F = anchors['fore']
    sh = [F['stay-head'][0] + 0.5, YC + 0.5, F['stay-head'][2] + 0.5]
    ff = [BA['forestay-foot'][0] + 0.5, YC + 0.5, BA['forestay-foot'][2] + 0.5]
    F['staysail.head'] = on_line(ff, sh, fs['head_frac'])
    th = [F['tm-stay-head'][0] + 0.5, YC + 0.5, F['tm-stay-head'][2] + 0.5]
    je = [BA['jib-end'][0] + 0.5, YC + 0.5, BA['jib-end'][2] + 0.5]
    F['jib.head'] = on_line(je, th, fs['head_frac'])
    # ── 船殼上的點 ──
    def rail(x):
        z = top_z(x)
        return [x, hout[(x, z)], z]
    H = anchors['hull']
    belay = {'fore-sheet': Y.masts['fore']['x0'] - fs['sheet_aft'], 'fore-tack': Y.masts['fore']['x0'] + fs['tack_fwd'],
             'staysail': fs['staysail_belay_x'], 'jib': fs['jib_belay_x']}
    for nm, x in belay.items():
        p = rail(x)
        H['belay-%s-S' % nm] = [p[0], YC + p[1], p[2]]
        H['belay-%s-P' % nm] = [p[0], YC - p[1], p[2]]
    xs_ = max(x for (x, z) in hout if z == fs['bs_shroud_z'])
    for s_, sg in (('S', 1), ('P', -1)):
        H['bs-shroud-' + s_] = [xs_ - 6, YC + sg * hout[(xs_ - 6, fs['bs_shroud_z'])], fs['bs_shroud_z']]
    # 主帆 sheet：船尾後甲板中線、taffrail 前 2 格
    mx = int(math.floor(float(L.x_aft(60)))) + 6
    anchors['deck-qd']['mainsheet'] = [mx, YC, int(math.floor(float(L.deck_z('qd', mx + 0.5)))) + 1]

    # ── 繩 ──
    C = RG['colors']
    T = RG['thick']
    ropes = []

    def rope(name, a_, b_, group, th, slack=1.0, color=None, meta=None):
        ropes.append({'name': name, 'from': a_, 'to': b_, 'group': group, 'thickness': th, 'slack': slack, 'color': color or C['standing'], 'meta': meta})
    for key in ('fore', 'main'):
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
                           ('jib-stay', '前桅/tm-stay-head', '艏斜桅/jib-end', T['tm_stay']),
                           ('fore-topmast-stay', '前桅/tm-stay-head', '艏斜桅/cap-top', T['tm_stay']),
                           ('main-stay', '主桅/stay-head', '前桅/mainstay-foot', T['stay']),
                           ('main-topmast-stay', '主桅/tm-stay-head', '前桅/top-aft', T['tm_stay'])):
        rope(nm, a_, b_, 'standing/stays', th)
    rope('bobstay-1', '船首/bobstay-1', '艏斜桅/bob-1', 'standing/bowsprit', T['bobstay'])
    for s_ in ('S', 'P'):
        rope('bowsprit-shroud-' + s_, '船殼/bs-shroud-' + s_, '艏斜桅/side-' + s_, 'standing/bowsprit', T['bobstay'])
    # ── 橫繩組（ratlines；lower 是繩梯：foot 舷牆內側的甲板、head 桅樓靠這一舷的邊）──
    RL = RG['ratlines']
    ratl = []
    SP = plan['decks_build']['spans']
    for key in ('fore', 'main'):
        ns = CH['shrouds'][key]
        xm = Y.masts[key]['x0']
        xmid = xm - CH['first_aft'] - (ns - 1) * CH['spacing'] // 2
        deck = next(d for d in ('qd', 'fc', 'gun') if SP[d][0] <= xmid <= SP[d][1])
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
                      'fullness': fullness or fs['fullness'], 'color': color or C['sail'], 'texture': texture})
    fmt = lambda p: '%.2f,%.2f,%.2f' % tuple(p)
    pt = lambda path, k: np.array(PP[path][k], float)
    os.makedirs(os.path.join(design, 'textures'), exist_ok=True)
    # 前橫帆：帆腳在舷頂上 course_clew_above_rail、sheet 往後、tack 往前綁舷頂
    cy = '前桅/yard-fore-course'
    cps = []
    for s_ in ('S', 'P'):
        e, pv = pt(cy, 'earing-' + s_), pt(cy, 'pivot')
        p = pv + fs['course_in'] * (e - pv)
        p[2] = top_z(int(p[0])) + fs['course_clew_above_rail']
        cps.append(fmt(p))
    nm = 'fore-course'
    sail(nm, ['model:%s/earing-P' % cy, 'model:%s/earing-S' % cy, cps[0], cps[1]], [0], ['clew_s', 'clew_p'],
         {'kind': 'sail', 'mast': 'fore', 'sail': 'course'}, ['head_p', 'head_s', 'clew_s', 'clew_p'])
    for s_, c in (('S', 'clew_s'), ('P', 'clew_p')):
        rope('%s-sheet-%s' % (nm, s_), 'sail:%s/%s' % (nm, c), '船殼/belay-fore-sheet-%s' % s_, 'running/sheets', T['course_sheet'], 1.02, C['running'], {'kind': 'sheet', 'sail': nm})
        rope('%s-tack-%s' % (nm, s_), 'sail:%s/%s' % (nm, c), '船殼/belay-fore-tack-%s' % s_, 'running/tacks', T['tack'], 1.02, C['running'], {'kind': 'tack', 'sail': nm})
    # 上桅帆、頂桅帆：帆腳綁下一根帆桁同舷的 earing 旁（主上桅帆綁 crossjack）
    for key, chain in (('fore', (('topsail', 'yard-fore-topsail', 'yard-fore-course'), ('topgallant', 'yard-fore-topgallant', 'yard-fore-topsail'))),
                       ('main', (('topsail', 'yard-main-topsail', 'yard-main-crossjack'), ('topgallant', 'yard-main-topgallant', 'yard-main-topsail')))):
        Lk = LINK[key]
        for kind, up, lo in chain:
            cps = []
            for s_ in ('S', 'P'):
                e, pv = pt(Lk + '/' + lo, 'earing-' + s_), pt(Lk + '/' + lo, 'pivot')
                p = e + fs['clew_in'] * (pv - e)
                p[2] += 2
                cps.append(fmt(p))
            nm = '%s-%s' % (key, kind)
            sail(nm, ['model:%s/%s/earing-P' % (Lk, up), 'model:%s/%s/earing-S' % (Lk, up), cps[0], cps[1]], [0], ['clew_s', 'clew_p'],
                 {'kind': 'sail', 'mast': key, 'sail': kind}, ['head_p', 'head_s', 'clew_s', 'clew_p'])
            for s_, c in (('S', 'clew_s'), ('P', 'clew_p')):
                rope('%s-sheet-%s' % (nm, s_), 'sail:%s/%s' % (nm, c), 'model:%s/%s/earing-%s' % (Lk, lo, s_), 'running/sheets', T['sheet'], 1.0, C['running'], {'kind': 'sheet', 'sail': nm})
    # 主帆（gaff＋boom）：throat、peak（gaff）、clew ＝ boom end、tack ＝ boom jaws；gaff、boom、桅三條邊釘住，只有 leech 自由
    G, Bm = '主桅/yard-main-gaff', '主桅/yard-main-boom'
    sail('mainsail', ['model:%s/throat' % G, 'model:%s/peak' % G, 'model:%s/end' % Bm, 'model:%s/jaws' % Bm], [0, 2, 3], None,
         {'kind': 'sail', 'mast': 'main', 'sail': 'gaff'}, ['throat', 'peak', 'clew', 'tack'])
    rope('mainsail-sheet', 'model:%s/%s' % (Bm, fs['mainsheet_boom_point']), '甲板-qd/mainsheet', 'running/sheets', T['sheet'], 1.05, C['running'], {'kind': 'sheet', 'sail': 'mainsail'})
    # 艏帆：tack 在支索下端（艏斜桅上）、head 在支索 75% 處、clew 自由、sheet 綁艏樓舷頂兩舷
    for nm, tack, head, kind, stay in (('fore-staysail', '艏斜桅/forestay-foot', '前桅/staysail.head', 'staysail', 'fore-stay'),
                                       ('jib', '艏斜桅/jib-end', '前桅/jib.head', 'jib', 'jib-stay')):
        hd = np.array(F[nm.split('-')[-1] + '.head'] if nm == 'jib' else F['staysail.head'], float) + 0.5
        tk = np.array(BA['jib-end' if nm == 'jib' else 'forestay-foot'], float) + 0.5
        clew = tk + fs['headsail_clew'][kind][0] * (hd - tk)
        clew[0] -= fs['headsail_clew'][kind][1]
        clew[2] = min(clew[2], tk[2] + fs['headsail_clew'][kind][2])
        sail(nm, [tack, head, fmt(clew)], [0], ['clew'], {'kind': 'sail', 'mast': 'bowsprit', 'sail': kind}, ['tack', 'head', 'clew'], fullness=1.06)
        for s_ in ('S', 'P'):
            rope('%s-sheet-%s' % (nm, s_), 'sail:%s/clew' % nm, '船殼/belay-%s-%s' % ('jib' if nm == 'jib' else 'staysail', s_), 'running/sheets', T['sheet'], 1.04, C['running'], {'kind': 'sheet', 'sail': nm})
    # 旗：船旗掛斜桁尖（peak 與往前一點的 top-*，照飛魚號）
    FL = RG['flags']
    ew, eh = FL['ensign']
    pk = pt(G, 'peak')
    sail('ensign', ['model:%s/peak' % G, fmt(pk - [ew, 0, 0]), fmt(pk - [ew, 0, eh]), 'model:%s/%s' % (G, FL['ensign_gaff_point'])],
         [3], None, {'kind': 'flag', 'flag': 'ensign'}, None, fullness=1.04, color='#be161e', texture='textures/ensign.png')
    ensign_png(os.path.join(design, 'textures', 'ensign.png'), 36, 24)

    metas = [['sail', s['name'], s['meta']] for s in sails] + [['rope', r['name'], r['meta']] for r in ropes if r['meta']]
    if probe:
        nm = probe[0].split('=')[1]
        metas = [m for m in metas if not (m[0] == 'rope' and m[1] == nm)]
    # ── 讀數 ──
    names = [r['name'] for r in ropes]
    sail_names = {s['name'] for s in sails if s['meta']['kind'] == 'sail'}
    need = [r['name'] for r in ropes if r['from'].startswith('sail:') or r['to'].startswith('sail:') or (r['meta'] or {}).get('kind') in ('sheet', 'tack')]
    have = {m[1] for m in metas if m[0] == 'rope'}
    bad_sail_ref = [m[1] for m in metas if m[0] == 'rope' and m[2].get('sail') not in sail_names]
    # 帆裝三段（Ship_Rigging §9.1）：有 set 照 set，沒有照 sail 的預設
    dflt = {'topsail': 1, 'jib': 1, 'topgallant': 2, 'gaff': 2}
    lvl = {s['name']: s['meta'].get('set', dflt.get(s['meta']['sail'], 3)) for s in sails if s['meta']['kind'] == 'sail'}
    sets = {k: sorted(n for n, v in lvl.items() if v <= k) for k in (1, 2, 3)}
    R = {'channels': {'cells': len(chan), 'skipped_on_ship': skipped, 'mirror_diff': sum(1 for (x, y, z), c in chan.items() if chan.get((x, 2 * YC - y, z)) != c)},
         'anchors': {k: len(v) for k, v in anchors.items()}, 'ropes': len(ropes), 'ratline_groups': len(ratl),
         'groups': {g: sum(1 for r in ropes if r['group'] == g) for g in sorted({r['group'] for r in ropes})},
         'sails': len(sails), 'meta': {'sails': sum(1 for m in metas if m[0] == 'sail'), 'ropes': len(have)},
         'sail_sets': {'收帆': sets[1], '戰鬥帆': sets[2], '滿帆': sets[3]},
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
    for k in ('fore', 'main'):
        works[k] = HULL + '-mast-' + k
    out = {'anchors': anchors, 'anchor_works': works, 'ropes': ropes, 'ratlines': ratl, 'sails': sails, 'meta': metas, 'wind': RG['wind'], 'sail_seconds': RG['sail_seconds']}
    with open(os.path.join(design, 'rigging_plan.json'), 'w', encoding='utf-8', newline='\n') as f:
        json.dump(out, f, ensure_ascii=False, indent=1, default=lambda o: o.item())
    with open(os.path.join(design, 'verify_rigging.json'), 'w', encoding='utf-8', newline='\n') as f:
        json.dump(R, f, ensure_ascii=False, indent=1, default=lambda o: o.item())
    print(json.dumps(R, ensure_ascii=False, default=lambda o: o.item()))


if __name__ == '__main__':
    main()
