# 出處：erina-tradewind-01m/design/draft_rigging.py（TASK-1097 信風號；TASK-1151 改寫成好旅號 caravela redonda）
#   三角帆的掛法照 erina-oxford-01m/design/draft_rigging.py（TASK-0972 牛津號 mizzen-lateen）
# 好旅號 步驟 8（TASK-1151）：channels（兩舷一件）、桅／艏斜桅／船殼／甲板的固定點、靜索、ratlines（橫繩組）、帆、帆自己的繩、旗、meta
#   輸入：plan.json（rigging、rig_build、masts）＋ verify_masts.json ＋ 組裝件現在的格子與 parts（CLI 匯出：帆桁模型的固定點世界座標）
#   輸出：masks/rigging/channels.vox.txt、rigging_plan.json、textures/*.png、verify_rigging.json
#   用法：python -I -X utf8 draft_rigging.py <design> [--probe=nometa=<繩名>]（反向對照：拿掉一條繩的 meta；⛔ 不寫檔）
#   跟信風號不同：四根桅 —— 前桅 course＋topsail（方帆）、主／後／最後桅各一面三角帆（tack ＝ 帆桁前端、head ＝ 尾端、clew ＝ 尾端下面的舷頂上，
#   帆緣綁在帆桁上；sail=gaff；tack 拉到帆桁前端正下方的甲板、sheet 兩舷綁舷頂）；沒有艏帆；桅樓只有前桅；國旗掛最後桅三角帆桁的尾端。
import sys, os, json, math, hashlib, subprocess, tempfile
import numpy as np
from PIL import Image

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), 'tools'))
import lines as HL
import layout as LY
from wio import export_list

HULL = 'summit-boaviagem-01m'
ASM = HULL + '-assembly'
LINK = {'fore': '前桅', 'main': '主桅', 'mizzen': '後桅', 'bonav': '最後桅', 'bowsprit': '艏斜桅'}
MAST_META = {'bonav': 'bonaventure'}
LATEEN = ('main', 'mizzen', 'bonav')


def parts_points():
    with tempfile.TemporaryDirectory() as d:
        out = os.path.join(d, 'p.json').replace('\\', '/')
        r = subprocess.run(['senate', 'cmd', 'sculpture', '--arg', 'op=export', '--arg', 'format=parts', '--arg', 'work=' + ASM, '--arg', 'out=' + out],
                           capture_output=True, text=True, encoding='utf-8', errors='replace')
        if r.returncode != 0:
            raise SystemExit(r.stdout[-800:])
        P = json.load(open(out, encoding='utf-8'))
    return {m['path']: m['points'] for m in P['models']}


def portugal_png(path, W, H):
    """葡萄牙 1660 年代的旗（〔設計〕簡化）：白底、中間王徽 —— 紅邊框、白底上五個藍色小盾（quinas）排成十字；冠省略。"""
    im = Image.new('RGBA', (W, H), (240, 238, 228, 255))
    px = im.load()
    cx, cy = W // 2, H // 2
    sw, sh = W // 3, int(H * 0.6)
    x0, y0 = cx - sw // 2, cy - sh // 2
    for x in range(x0, x0 + sw):
        for y in range(y0, y0 + sh):
            edge = min(x - x0, x0 + sw - 1 - x, y - y0, y0 + sh - 1 - y)
            px[x, y] = (190, 30, 30, 255) if edge < 2 else (245, 245, 240, 255)
    q = max(2, sw // 6)
    for dx, dy in ((0, 0), (-1, 0), (1, 0), (0, -1), (0, 1)):
        qx, qy = cx + dx * (q + 1), cy + dy * (q + 1)
        for x in range(qx - q // 2, qx - q // 2 + q):
            for y in range(qy - q // 2, qy - q // 2 + q):
                px[x, y] = (25, 50, 140, 255)
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
        return max(zz for (xx, zz) in hout if xx == x)          # 那一欄船殼實際最上一格

    def stage(key, i):
        nm, z0, z1, off = VM['masts'][key]['stages'][i]
        r = MS[key]['r'] if i == 0 else MS[key + '_top']['r']
        return z0, z1, off, r

    def mast_r(key, z, i=0):
        z0, z1, off, r = stage(key, i)
        return r[0] + (r[1] - r[0]) * (z - z0) / max(1, z1 - z0)

    def ax(key, z, i=0):
        return float(Y.mast_x(key, z + 0.5)) + stage(key, i)[2]

    anchors = {k: {} for k in ('hull', 'channels', 'fore', 'main', 'mizzen', 'bonav', 'bowsprit', 'deck-gun', 'deck-qd')}
    # ── channels（兩舷一件）＋ deadeye ──
    CH = RG['channels']
    chan, skipped = {}, 0
    for key in ('fore', 'main', 'mizzen', 'bonav'):
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
    # 前桅：桅樓、上桅（同信風號）
    tops = {}
    key = 'fore'
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
    ztm = z1 - MS[key + '_top']['head'] - 4
    rtm = mast_r(key, ztm, 1)
    for s_, sg in (('S', 1), ('P', -1)):
        A_['tm-hound-' + s_] = [int(round(ax(key, ztm, 1))), YC + sg * (int(math.ceil(rtm)) + 1), ztm]
    A_['tm-stay-head'] = [int(math.floor(ax(key, ztm, 1) + rtm)) + 1, YC, ztm]
    zf = int(math.floor(float(L.deck_z('fc', Y.masts['fore']['x0'] + 0.5)))) + 4
    anchors['fore']['mainstay-foot'] = [int(math.floor(ax('fore', zf) - mast_r('fore', zf))) - 1, YC, zf]
    # 三角帆桅：hounds 在三角帆桁吊點下 hound_below 格、stay-head 在桅前面
    for key in LATEEN:
        A_ = anchors[key]
        zs = Y.yards()[key + '_lateen']['z']
        zh = int(zs) - RG['hound_below']
        r = mast_r(key, zh)
        for s_, sg in (('S', 1), ('P', -1)):
            A_['hound-' + s_] = [int(round(ax(key, zh))), YC + sg * (int(math.ceil(r)) + 1), zh]
        A_['stay-head'] = [int(math.floor(ax(key, zh) + r)) + 1, YC, zh]
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
    fs = RG['sails']
    BA['forestay-foot'] = cell(Hh + plan['masts']['rig']['forestay_frac'] * Lb * u + (rb(plan['masts']['rig']['forestay_frac'] * Lb) + 1) * w)
    BA['cap-top'] = cell(Hh + (Lb - 3) * u + (rb(Lb) + 2.5) * w)
    for s_, sg in (('S', 1), ('P', -1)):
        BA['side-' + s_] = cell(Hh + 0.55 * Lb * u + np.array([0, sg * (rb(0.55 * Lb) + 1), 0]))
    BA['bob-1'] = cell(Hh + 0.55 * Lb * u - (rb(0.55 * Lb) + 1) * w)
    # ── 船殼上的點 ──
    def rail(x):
        z = top_z(x)
        return [x, hout[(x, z)], z]
    H = anchors['hull']
    belay = {'fore-sheet': Y.masts['fore']['x0'] - fs['sheet_aft'], 'fore-tack': Y.masts['fore']['x0'] + fs['tack_fwd']}
    pt = lambda path, k: np.array(PP[path][k], float)
    clews = {}
    for key in LATEEN:
        pk = pt('%s/yard-%s-lateen' % (LINK[key], key), 'peak')
        cx = max(int(math.floor(pk[0])) + fs['lateen_clew_dx'], min(x for (x, z) in hout) + 3)   # 最後桅帆桁尾端伸出船尾 ⇒ clew 最多到船尾板前 3 格（sheet 綁船尾欄杆）
        clews[key] = [cx + 0.5, YC + 0.5, top_z(cx) + fs['lateen_clew_above_rail'] + 0.5]
        belay['%s-lateen' % key] = cx + fs['lateen_sheet_fwd']
    for nm, x in belay.items():
        p = rail(x)
        H['belay-%s-S' % nm] = [p[0], YC + p[1], p[2]]
        H['belay-%s-P' % nm] = [p[0], YC - p[1], p[2]]
    xs_ = max(x for (x, z) in hout if z == fs['bs_shroud_z'])
    for s_, sg in (('S', 1), ('P', -1)):
        H['bs-shroud-' + s_] = [xs_ - 6, YC + sg * hout[(xs_ - 6, fs['bs_shroud_z'])], fs['bs_shroud_z']]
    # 三角帆的 tack：帆桁前端正下方那一層甲板的中線
    SP = plan['decks_build']['spans']
    tacks = {}
    for key in LATEEN:
        fx = int(math.floor(pt('%s/yard-%s-lateen' % (LINK[key], key), 'fore')[0]))
        deck = 'qd' if SP['qd'][0] <= fx <= SP['qd'][1] else 'gun'
        anchors['deck-' + deck]['tack-' + key] = [fx, YC, int(math.floor(float(L.deck_z(deck, fx + 0.5)))) + 1]
        tacks[key] = '甲板-%s/tack-%s' % (deck, key)

    # ── 繩 ──
    C = RG['colors']
    T = RG['thick']
    ropes = []

    def rope(name, a_, b_, group, th, slack=1.0, color=None, meta=None):
        ropes.append({'name': name, 'from': a_, 'to': b_, 'group': group, 'thickness': th, 'slack': slack, 'color': color or C['standing'], 'meta': meta})
    for key in ('fore', 'main', 'mizzen', 'bonav'):
        Lk = LINK[key]
        ns, nb = CH['shrouds'][key], CH['backstays'].get(key, 0)
        for s_ in ('S', 'P'):
            for i in range(1, ns + 1):
                rope('%s-shroud-%s-%d' % (key, s_, i), '支索板/deadeye-%s-%s-%d' % (key, s_, i), '%s/hound-%s' % (Lk, s_), 'standing/shrouds', T['shroud'])
            for bb in range(1, nb + 1):
                rope('%s-topmast-backstay-%s-%d' % (key, s_, bb), '支索板/deadeye-%s-%s-%d' % (key, s_, ns + bb), '%s/tm-hound-%s' % (Lk, s_), 'standing/backstays', T['backstay'])
    for s_ in ('S', 'P'):
        for i in range(1, RG['topmast_shrouds'] + 1):
            rope('fore-topmast-shroud-%s-%d' % (s_, i), '前桅/rim-%s-%d' % (s_, i), '前桅/tm-hound-%s' % s_, 'standing/topmast-shrouds', T['topmast_shroud'])
            rope('fore-futtock-%s-%d' % (s_, i), '前桅/rim-low-%s-%d' % (s_, i), '前桅/futtock-%s' % s_, 'standing/futtock-shrouds', T['futtock'])
    for nm, a_, b_, th in (('fore-stay', '前桅/stay-head', '艏斜桅/forestay-foot', T['stay']),
                           ('fore-topmast-stay', '前桅/tm-stay-head', '艏斜桅/cap-top', T['tm_stay']),
                           ('main-stay', '主桅/stay-head', '前桅/mainstay-foot', T['stay'])):
        rope(nm, a_, b_, 'standing/stays', th)
    rope('bobstay-1', '船首/bobstay-1', '艏斜桅/bob-1', 'standing/bowsprit', T['bobstay'])
    for s_ in ('S', 'P'):
        rope('bowsprit-shroud-' + s_, '船殼/bs-shroud-' + s_, '艏斜桅/side-' + s_, 'standing/bowsprit', T['bobstay'])
    # ── 橫繩組：前桅 lower 是繩梯（foot 舷牆內側的甲板、head 桅樓靠這一舷的邊）、topmast；主桅 lower（沒有桅樓 ⇒ 不標 climb）──
    RL = RG['ratlines']
    ratl = []
    for key in ('fore', 'main'):
        ns = CH['shrouds'][key]
        xm = Y.masts[key]['x0']
        xmid = xm - CH['first_aft'] - (ns - 1) * CH['spacing'] // 2
        deck = next(d for d in ('qd', 'fc', 'gun') if SP[d][0] <= xmid <= SP[d][1])
        zfl = int(math.floor(float(L.deck_z(deck, xmid + 0.5))))
        for s_, sg in (('S', 1), ('P', -1)):
            g = {'name': '%s-lower-%s' % (key, s_), 'rope_a': '%s-shroud-%s-1' % (key, s_), 'rope_b': '%s-shroud-%s-%d' % (key, s_, ns),
                 'step': RL['step'], 'start': RL['start'], 'stop': RL['stop'], 'min_span': RL['min_span'], 'thickness': RL['th'],
                 'group': 'ratlines/lower', 'climb': 0}
            if key in tops:
                xc, zt, rt = tops[key]
                o = hout[(xmid, min(zfl + 4, top_z(xmid) - 1))]
                g.update({'climb': 1, 'foot': '%d,%d,%d' % (xmid, YC + sg * (o - 3 - 2), zfl + 1), 'head': '%d,%d,%d' % (int(math.floor(xc + 0.5)), YC + sg * (rt - 2), zt)})
            ratl.append(g)
            if key == 'fore':
                ratl.append({'name': 'fore-topmast-%s' % s_, 'rope_a': 'fore-topmast-shroud-%s-1' % s_, 'rope_b': 'fore-topmast-shroud-%s-%d' % (s_, RG['topmast_shrouds']),
                             'step': RL['tm_step'], 'start': RL['tm_start'], 'stop': RL['tm_stop'], 'min_span': RL['min_span'], 'thickness': RL['tm_th'],
                             'group': 'ratlines/topmast', 'climb': 0})
    # ── 帆 ──
    sails = []

    def sail(name, corners, bind, free, meta, names, fullness=None, color=None, texture=None):
        sails.append({'name': name, 'corners': corners, 'corner_names': names, 'bind': bind, 'free': free, 'meta': meta,
                      'fullness': fullness or fs['fullness'], 'color': color or C['sail'], 'texture': texture})
    fmt = lambda p: '%.2f,%.2f,%.2f' % tuple(p)
    os.makedirs(os.path.join(design, 'textures'), exist_ok=True)
    # 前帆（course）：帆腳在舷頂上 course_clew_above_rail、sheet 往後、tack 往前綁舷頂
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
    # 前上桅帆：帆腳綁前帆桁同舷的 earing 旁
    up, lo = 'yard-fore-topsail', 'yard-fore-course'
    cps = []
    for s_ in ('S', 'P'):
        e, pv = pt('前桅/' + lo, 'earing-' + s_), pt('前桅/' + lo, 'pivot')
        p = e + fs['clew_in'] * (pv - e)
        p[2] += 2
        cps.append(fmt(p))
    nm = 'fore-topsail'
    sail(nm, ['model:前桅/%s/earing-P' % up, 'model:前桅/%s/earing-S' % up, cps[0], cps[1]], [0], ['clew_s', 'clew_p'],
         {'kind': 'sail', 'mast': 'fore', 'sail': 'topsail'}, ['head_p', 'head_s', 'clew_s', 'clew_p'])
    for s_, c in (('S', 'clew_s'), ('P', 'clew_p')):
        rope('%s-sheet-%s' % (nm, s_), 'sail:%s/%s' % (nm, c), 'model:前桅/%s/earing-%s' % (lo, s_), 'running/sheets', T['sheet'], 1.0, C['running'], {'kind': 'sheet', 'sail': nm})
    # 三角帆 ×3：tack ＝ 帆桁前端、head ＝ 帆桁尾端、clew ＝ 尾端下面的舷頂上；帆緣（邊 0）綁帆桁、clew 自由
    for key in LATEEN:
        yk = '%s/yard-%s-lateen' % (LINK[key], key)
        nm = '%s-lateen' % key
        meta = {'kind': 'sail', 'mast': MAST_META.get(key, key), 'sail': 'gaff'}
        if key in fs.get('lateen_set', {}):
            meta['set'] = fs['lateen_set'][key]
        sail(nm, ['model:%s/fore' % yk, 'model:%s/peak' % yk, fmt(clews[key])], [0], ['clew'], meta, ['tack', 'head', 'clew'])
        for s_ in ('S', 'P'):
            rope('%s-sheet-%s' % (nm, s_), 'sail:%s/clew' % nm, '船殼/belay-%s-%s' % (nm, s_), 'running/sheets', T['sheet'], 1.03, C['running'], {'kind': 'sheet', 'sail': nm})
        rope('%s-tack' % nm, 'sail:%s/tack' % nm, tacks[key], 'running/tacks', T['tack'], 1.0, C['running'], {'kind': 'tack', 'sail': nm})
    # 旗：葡萄牙國旗掛最後桅三角帆桁的尾端，旗邊垂直往下（下角是帆桁模型裡 peak 正下方那一點 ⇒ 跟著帆桁轉；照三叉戟號），只綁旗邊、飛邊兩角放開（free 1、2）
    #   ⛔ 以前下角綁帆桁上往前的 top-02、四角全綁 ⇒ 旗邊沿帆桁斜下去、梯形、兩頭釘死不會飄（erina 2026-11-01，Tim 回報信風號同一個毛病）
    FL = RG['flags']
    ew, eh = FL['ensign']
    YB = '最後桅/yard-bonav-lateen'
    pk = pt(YB, 'peak')
    sail('ensign', ['model:%s/peak' % YB, fmt(pk - [ew, 0, 0]), fmt(pk - [ew, 0, eh]), 'model:%s/%s' % (YB, ','.join('%g' % c for c in FL['ensign_luff_model']))],
         [3], [1, 2], {'kind': 'flag', 'flag': 'ensign'}, None, fullness=1.04, color='#f0eee4', texture='textures/ensign.png')
    portugal_png(os.path.join(design, 'textures', 'ensign.png'), 36, 24)

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
        f.write('# 好旅號 channels 兩舷（支索板＋deadeye；世界座標，at 0,0,0）\n')
        for k in sorted(chan):
            f.write('%d,%d,%d,%d\n' % (k[0], k[1], k[2], chan[k]))
    R['channels']['sha256'] = hashlib.sha256(open(p, 'rb').read()).hexdigest()
    works = {'hull': HULL, 'channels': HULL + '-channels', 'bowsprit': HULL + '-bowsprit', 'deck-gun': HULL + '-deck-gun', 'deck-qd': HULL + '-deck-qd'}
    for k in ('fore', 'main', 'mizzen', 'bonav'):
        works[k] = HULL + '-mast-' + k
    anchors = {k: v for k, v in anchors.items() if v}
    works = {k: v for k, v in works.items() if k in anchors}
    out = {'anchors': anchors, 'anchor_works': works, 'ropes': ropes, 'ratlines': ratl, 'sails': sails, 'meta': metas, 'wind': RG['wind'], 'sail_seconds': RG['sail_seconds']}
    with open(os.path.join(design, 'rigging_plan.json'), 'w', encoding='utf-8', newline='\n') as f:
        json.dump(out, f, ensure_ascii=False, indent=1, default=lambda o: o.item())
    with open(os.path.join(design, 'verify_rigging.json'), 'w', encoding='utf-8', newline='\n') as f:
        json.dump(R, f, ensure_ascii=False, indent=1, default=lambda o: o.item())
    print(json.dumps(R, ensure_ascii=False, default=lambda o: o.item()))


if __name__ == '__main__':
    main()
