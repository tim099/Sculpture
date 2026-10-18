# 蘇士奎哈納號（crest-001，TASK-0697）：本檔抄自光榮號 kaguya-gloire-01m/design/draft_rigging.py（kaguya）—— 下面註解裡的「蘇士奎哈納號」原文是光榮號，改過的地方另外註明
# 蘇士奎哈納號 階段七（TASK-0612）索具與帆：channels（右舷一件＋鏡像）、桅／艏斜桅／船殼／knee 的固定點、靜索、ratlines、帆（方帆、spanker、三角帆）、帆自己的繩、旗（法國三色旗）、meta
#   抄自三叉戟號 gura-tridente-01m/design/draft_rigging.py（gura，TASK-0560）；改：船的現況從本船清單組（mio）、後桅 stay 下端改綁主桅煙囪頂以上（原版綁在主桅腳會穿過後煙囪）、
#   bobstay 下端登記在本船 knee（船頭）上、旗是法國三色旗、讀數多「每條繩（拉直）碰不碰船上的格」
#   輸出：masks/rigging/channels.vox.txt（子作品座標）、rigging_plan.json、textures/{ensign,pennant}.png、verify_rigging.json
#   用法：python -I -X utf8 draft_rigging.py <design> [--probe=nometa=<繩名>]（反向對照：那一條繩不標 meta，讀數要報出那一條；⛔ 不寫檔）
import sys, os, json, math
import numpy as np
from PIL import Image

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import hull_lines as HL
import layout as LY
import mio

YC = 200
LINK = {'main': '主桅', 'fore': '前桅', 'mizzen': '後桅', 'bowsprit': '艏斜桅'}
HULL = 'crest-001-susquehanna-01m'


def tricolour_png(path, W, H):
    """法國三色旗：藍白紅直條（1:1:1），第 0 欄 ＝ 旗桿那一邊（角 0 → 角 1 ＝ 旗桿 → 旗尾）。"""
    blue, white, red = (0, 35, 149), (255, 255, 255), (237, 41, 57)
    im = Image.new('RGBA', (W, H), white)
    px = im.load()
    for x in range(W):
        c = blue if x < W / 3.0 else white if x < 2 * W / 3.0 else red
        for y in range(H):
            px[x, y] = c
    im.save(path)


def stars_stripes_png(path, W, H):
    """蘇士奎哈納號加的：1853 年的美國國旗（31 星、13 條紅白條；1851-07-04 起 31 星）—— 像素畫 W×H，第 0 欄 ＝ 旗桿那一邊。
    canton：寬 0.4、高 7 條（7/13）；31 星排 6 列（5,5,5,5,5,6 交錯的簡化排法）一顆一格白點。"""
    red, white, blue = (178, 34, 52), (255, 255, 255), (60, 59, 110)
    im = Image.new('RGBA', (W, H), white)
    px = im.load()
    for y in range(H):
        stripe = int(y * 13 / H)
        for x in range(W):
            px[x, y] = red if stripe % 2 == 0 else white
    cw, ch = int(round(W * 0.4)), int(round(H * 7 / 13.0))
    for y in range(ch):
        for x in range(cw):
            px[x, y] = blue
    rows_ = [5, 5, 5, 5, 5, 6]
    for r, n in enumerate(rows_):
        yy = int((r + 0.6) * ch / (len(rows_) + 0.2))
        for k in range(n):
            xx = int((k + 0.6 + (0.5 if n == 5 and r % 2 else 0)) * cw / (6 + 0.2))
            if 0 <= xx < cw and 0 <= yy < ch:
                px[xx, yy] = white
    im.save(path)


def us_pennant_png(path, W, H):
    """蘇士奎哈納號加的：commission pennant —— 旗桿那一段（1/4）藍底白點，後面上紅下白（設計決定）。"""
    red, white, blue = (178, 34, 52), (255, 255, 255), (60, 59, 110)
    im = Image.new('RGBA', (W, H), white)
    px = im.load()
    for x in range(W):
        for y in range(H):
            if x < W // 4:
                px[x, y] = white if (x % 4 == 2 and y == H // 2) else blue
            else:
                px[x, y] = red if y < H // 2 else white
    im.save(path)


def main():
    sys.stdout.reconfigure(encoding='utf-8')
    design = sys.argv[1]
    probe = next((a.split('=', 1)[1] for a in sys.argv[2:] if a.startswith('--probe=')), None)
    plan = HL.load_plan(design)
    RG = plan['rigging']
    MB = plan['masts_build']
    G, _H = mio.stage_base(design, ('decks', 'ladders', 'deco', 'masts', 'paddles'), nz=260)   # 蘇士奎哈納號改：加明輪罩（兩舷）與明輪
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

    anchors = {'hull': {}, 'channels': {}, 'main': {}, 'fore': {}, 'mizzen': {}, 'bowsprit': {}, 'head': {}}
    # ── channels（右舷一件）：每根桅一塊板（上甲板砲門頂往上）、外緣一排 deadeye ──
    CH = RG['channels']
    chan = {}
    dead = {}
    for key in ('main', 'fore', 'mizzen'):
        n = CH['shrouds'][key] + CH['backstays'][key] + 1
        x0 = rows[key]['x'] + CH['fwd']
        zc = int(LY.deck_z(plan, 'gun', rows[key]['x'])) + CH['above_deck']   # 蘇士奎哈納號改：露天甲板叫 gun
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
    org, size = mio.bbox(chan)
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
    for key, nm, zz in (('fore', 'mainstay-foot', RG.get('mainstay_foot_z')), ('main', 'mizzenstay-foot', RG['mizzenstay_foot_z'])):   # 蘇士奎哈納號改：main stay 下端也可以指定高度
        z = zz or int(LY.deck_z(plan, 'gun', rows[key]['x'])) + 3      # 後桅 stay：主桅腳那一點 ⇒ 繩穿過後煙囪 ⇒ 改綁主桅上、煙囪頂以上
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
    for i, f in enumerate(RG['bob_at'], 1):
        B['bob-%d' % i] = cell(Hh + f * Lb * u - (rb(f * Lb) + 1) * w)
    # knee（船頭）上的 bobstay 下端：knee 前緣那一格（從 deco 清單讀）
    hk = np.loadtxt(os.path.join(design, 'masks', 'deco', 'head.vox.txt'), delimiter=',', comments='#', dtype=np.int32, ndmin=2, encoding='utf-8')
    for i, z in enumerate(RG['bobstay_knee_z'], 1):
        c = hk[(hk[:, 1] == YC) & (hk[:, 2] == z)]
        anchors['head']['bobstay-%d' % i] = [int(c[:, 0].max()), YC, int(z)]
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
    for i in range(1, len(RG['bob_at']) + 1):
        rope('bobstay-%d' % i, '船頭/bobstay-%d' % i, '艏斜桅/bob-%d' % i, 'standing/bowsprit', RG['thick']['bobstay'])
    for s_ in ('S', 'P'):
        rope('bowsprit-shroud-' + s_, '船殼/bs-shroud-' + s_, '艏斜桅/side-' + s_, 'standing/bowsprit', RG['thick']['bobstay'])
    # ratlines：橫繩組（造船規格 §6，TASK-0678）—— 只記兩條母繩（最前、最後那根 shroud）＋間距；下桅那幾組標繩梯（climb=1）
    #   蘇士奎哈納號改：光榮號原本一階一條子繩（舊做法），這裡整段換掉
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
        if frame == '船頭':
            return np.array(anchors['head'][nm], float) + 0.5
        raise KeyError(spec)

    def standable(x, y, z):
        return bool(S[x, y, z - 1]) and not S[x, y, z:z + 8].any()
    ratline_groups = []
    nrat = 0
    for key in ('main', 'fore', 'mizzen'):
        for s_, sg in (('S', 1), ('P', -1)):
            for kind, first, last in (('lower', '%s-shroud-%s-1' % (key, s_), '%s-shroud-%s-%d' % (key, s_, CH['shrouds'][key])),
                                      ('topmast', '%s-topmast-shroud-%s-1' % (key, s_), '%s-topmast-shroud-%s-%d' % (key, s_, RG['topmast_shrouds'][key]))):
                g = dict(RL[kind])
                g.update({'name': '%s-%s-%s' % (key, kind, s_), 'rope_a': first, 'rope_b': last, 'color': C['standing'], 'group': 'ratlines/' + kind})
                if kind == 'lower':
                    ra = next(r for r in ropes if r['name'] == first)
                    rb_ = next(r for r in ropes if r['name'] == last)
                    xm = int(round((wpt(ra['from'])[0] + wpt(rb_['from'])[0]) / 2.0))
                    zd = int(LY.deck_z(plan, 'gun', xm)) + 1
                    dy = 1
                    while not S[xm, YC + sg * dy, zd]:
                        dy += 1                                                   # 走到舷牆內側那一格
                    foot = None
                    for back in range(2, 8):
                        q = (xm, YC + sg * (dy - back), zd)
                        if standable(*q):
                            foot = list(q)
                            break
                    sp = spars[key]
                    W, Dp = MB['top'][key]
                    zp = sp['platform']
                    xc = ax(key, 'lower', zp)
                    head = None
                    for hx in (int(round(xc - 0.15 * Dp)), int(round(xc - 0.25 * Dp)), int(round(xc))):
                        for hy in range(int(W / 2.0) - 3, 3, -1):
                            q = (hx, YC + sg * hy, zp + 1)
                            if standable(*q):
                                head = list(q)
                                break
                        if head:
                            break
                    g.update({'climb': 1, 'foot': foot, 'head': head})
                ratline_groups.append(g)
                nrat += 1
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
    # 蘇士奎哈納號：gaff 是三叉戟號 gaff 的模型（等比縮）⇒ 局部座標是來源元件的座標；旗高 eh 換成來源的格數 ＝ eh ÷ 縮放
    gy = next(y for y in MPL['yards'] if y['name'] == 'mizzen-gaff')
    src = {v['name']: v for v in json.load(open(MB['yards']['source_placement'], encoding='utf-8'))['yards']}[MB['yards']['source']['mizzen-gaff']]
    peak_local = src['anchors']['peak']
    ew, eh = FL['ensign']
    eh_local = int(round(eh / gy['model']['scale'][2]))
    sail('ensign', ['model:後桅/yard-mizzen-gaff/peak', '%.2f,%.2f,%.2f' % (pk[0] - ew, pk[1], pk[2]), '%.2f,%.2f,%.2f' % (pk[0] - ew, pk[1], pk[2] - eh),
                    'model:後桅/yard-mizzen-gaff/%d,%d,%d' % (peak_local[0], peak_local[1], peak_local[2] - eh_local)],
         [3], [2, 1], {'kind': 'flag', 'flag': 'ensign'}, color=FL['ensign_color'], texture='textures/ensign.png', fullness=1.04)
    tz = spars['main']['truck']
    tx = ax('main', 'tg', tz)
    pl_, ph = FL['pennant']
    sail('pennant', ['%.2f,%.2f,%.2f' % (tx + 0.5, YC + 0.5, tz - 1), '%.2f,%.2f,%.2f' % (tx - pl_, YC + 0.5, tz - 2), '%.2f,%.2f,%.2f' % (tx + 0.5, YC + 0.5, tz - 1 - ph)],
         [2], [1], {'kind': 'flag', 'flag': 'pennant', 'mast': 'main'}, color=FL['pennant_color'], texture='textures/pennant.png', fullness=1.04)
    os.makedirs(os.path.join(design, 'textures'), exist_ok=True)
    stars_stripes_png(os.path.join(design, 'textures', 'ensign.png'), 60, 40)   # 蘇士奎哈納號改：1853 年的美國國旗
    us_pennant_png(os.path.join(design, 'textures', 'pennant.png'), 120, 4)

    # ── 讀數與寫檔 ──
    if probe:
        nm = probe.split('=', 1)[1]
        for r in ropes:
            if r['name'] == nm:
                r['meta'] = None
    n, h = (len(chan), None) if probe else mio.write_local(os.path.join(design, 'masks', 'rigging', 'channels.vox.txt'), chan, org, '# 蘇士奎哈納號 channels 右舷（三塊板＋deadeye；子作品座標，左舷 ＝ mirror=y 關聯）\n')
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
    R = {'channels': {'cells': n, 'sha256': h, 'at': org, 'size': size, 'at_mirror': [org[0], mio.mirror_at_y(org[1], size[1]), org[2]], 'overlap_base': over},
         'anchors': {k: len(v) for k, v in anchors.items()}, 'ropes': len(ropes), 'ratline_groups': nrat, 'ratline_climb': [[g['name'], g.get('foot'), g.get('head')] for g in ratline_groups if g.get('climb')], 'groups': groups, 'sails': len(sails),
         'meta': {'sails': sum(1 for m in metas if m[0] == 'sail'), 'ropes': sum(1 for m in metas if m[0] == 'rope')}, 'dup_rope_names': len(names) - len(set(names))}
    # 每條繩（拉直的兩端連線）碰到船上的格（含桅、煙囪、船首像；兩端各 3 格內不算）—— 子繩（ratlines）不量
    def endpoint(spec):
        if spec.startswith('model:'):
            _, rest = spec.split(':', 1)
            frame, yd, nm = rest.split('/')
            return np.array(YP[yd.replace('yard-', '')][nm], float)
        if spec.startswith('sail:') or spec.startswith('rope:'):
            return None
        if ',' in spec:
            return np.array([float(v) for v in spec.split(',')])
        return wpt(spec)
    rope_hits = {}
    for r in ropes:
        a, b = endpoint(r['from']), endpoint(r['to'])
        if a is None or b is None:
            continue
        n_ = int(np.linalg.norm(b - a) * 2) + 1
        hits = set()
        for t in np.linspace(0, 1, n_):
            c = a + (b - a) * t
            if min(np.linalg.norm(c - a), np.linalg.norm(c - b)) < 3:
                continue
            q = (int(math.floor(c[0])), int(math.floor(c[1])), int(math.floor(c[2])))
            if 0 <= q[2] < S.shape[2] and S[q]:
                hits.add(q)
        if hits:
            rope_hits[r['name']] = len(hits)
    no_meta = [r['name'] for r in ropes if r['group'] in ('running/sheets', 'running/tacks') and not r['meta']]
    R['rope_hits'] = rope_hits
    R['sail_ropes_without_meta'] = no_meta
    if probe:
        print(json.dumps({'probe': probe, 'sail_ropes_without_meta': no_meta}, ensure_ascii=False))
        return
    out = {'channels': {'work': HULL + '-channels', 'title': '蘇士奎哈納號 channels（右舷一件）', 'at': org, 'size': size, 'at_mirror': R['channels']['at_mirror'],
                        'links': ['channels', 'channels-鏡像']},
           'anchors': anchors, 'anchor_works': {'hull': HULL, 'channels': HULL + '-channels', 'main': HULL + '-mast-main',
                                                'fore': HULL + '-mast-fore', 'mizzen': HULL + '-mast-mizzen', 'bowsprit': HULL + '-bowsprit', 'head': HULL + '-head'},
           'ropes': ropes, 'ratline_groups': ratline_groups, 'sails': sails, 'meta': metas, 'wind': RG['wind'], 'sail_seconds': RG['sail_seconds']}
    with open(os.path.join(design, 'rigging_plan.json'), 'w', encoding='utf-8', newline='\n') as f:
        json.dump(out, f, ensure_ascii=False, indent=1, default=lambda o: o.item())
    with open(os.path.join(design, 'verify_rigging.json'), 'w', encoding='utf-8', newline='\n') as f:
        json.dump(R, f, ensure_ascii=False, indent=1, default=lambda o: o.item())
    print(json.dumps(R, ensure_ascii=False, default=lambda o: o.item()))


if __name__ == '__main__':
    main()
