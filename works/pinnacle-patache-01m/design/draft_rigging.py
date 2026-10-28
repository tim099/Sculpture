# 直接出處：apex-two-galeon-01m/design/draft_rigging.py（康塞普西翁號，TASK-0969）—— 作品 id、persona、尺寸、單號、船名換成聖羅曼號（TASK-0970）；下面那行是康塞普西翁號那時寫的出處
# 直接出處：gura-pinas-01m/design/draft_rigging.py（藍鯊號，TASK-0967）—— 作品 id、persona、尺寸、單號、船名換成聖羅曼號（TASK-0970）；下面那行是藍鯊號那時寫的出處
# 出處：calli-cosecha-01m/design/draft_rigging.py（收穫號）的框架 —— 改成荷蘭 pinas 的帆裝（TASK-0970 步驟 8）
# 聖羅曼號 步驟 8：channels（兩舷一件）、桅／艏斜桅／船殼／甲板／船首喙的固定點、靜索、ratlines（橫繩組）、帆、帆自己的繩、旗、meta
#   ⚠ 聖羅曼號改：四根桅（bonaventure：shrouds 2、支索、第二面三角帆 —— 照收穫號 draft_rigging）、勃艮第十字（船尾旗＋兩面 course，照收穫號 cross_png）、
#     channels 的間距／起點／舷頂下幾格可以每根桅不同、主桅繩梯落腳在第三層甲板、船頭的 x 上限照 plan、喙子作品 galjoen → espolon
#   輸入：plan.json（rigging、rig_build、masts）＋ yards_placement.json／yards_lateen.json（帆桁模型）＋ 組裝件現在的格子（CLI 匯出）
#   輸出：masks/rigging/channels.vox.txt（世界座標，at 0,0,0）、rigging_plan.json（固定點、繩、橫繩組、帆、meta）、textures/*.png、verify_rigging.json
#   用法：python -I -X utf8 draft_rigging.py <design> [--probe=nometa=<繩名>]（反向對照：拿掉一條繩的 meta，看 check 報不報；⛔ 不寫檔）
#   · 跟收穫號不同的：三根桅都有中桅、前桅與主桅再加上桅（上桅支索、上桅帆）、後中桅帆（kruiszeil）、斜桅頂帆（boven blinde）；
#     ratlines 改用橫繩組（Ship_Rigging §6，TASK-0678：只標最前、最後那兩根 shroud ＋ 間距；下桅那組 climb=1 ⇒ 遊戲裡爬得上去）
import sys, os, json, math, hashlib
import numpy as np
from PIL import Image

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), 'tools'))
import lines as HL
import layout as LY
from wio import export_list

LINK = {'fore': '前桅', 'main': '主桅', 'mizzen': '後桅', 'bowsprit': '艏斜桅'}
MASTS = ('fore', 'main')                                   # 有桅樓與中桅的（聖羅曼號：後桅只有下桅）
ALL = MASTS + ('mizzen',)                                         # 有 shrouds 的（聖羅曼號：後桅只有下桅 ＝ 康塞普西翁號 bonaventure 那一套）
DECK_OF = {'fore': 'castillo', 'main': 'main'}       # 下桅繩梯落腳的那一層（舷牆內側；聖羅曼號：主桅在船腰）


def cross_png(path, W, H, field, red, ragged=True):
    """勃艮第十字：底色上一個紅色鋸齒交叉（兩條對角線，每隔幾格凸一個節）—— 出處：calli-cosecha-01m/design/draft_rigging.py。"""
    im = Image.new('RGBA', (W, H), field)
    px = im.load()
    for x in range(W):
        for y in range(H):
            u, v = x / (W - 1.0), y / (H - 1.0)
            for dd in (abs(u - v), abs(u - (1 - v))):
                if dd * min(W, H) <= 1.6:
                    px[x, y] = red
    if ragged:
        for k in range(3, min(W, H) - 3, 6):
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
    A = export_list('pinnacle-patache-01m-assembly', None, links=None)
    own = set()
    if os.path.exists(os.path.join(WORKS, 'pinnacle-patache-01m-channels', 'work.json')):
        own = set(map(tuple, export_list('pinnacle-patache-01m-channels', None)[:, :3].tolist()))
    occ = {tuple(r[:3]) for r in A.tolist()} - own
    hull = {tuple(r[:3]) for r in export_list('pinnacle-patache-01m', None).tolist()}
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
        if 'tg_heel' in m and z > m['tm_top']:
            g0, g1 = RB['tgallant_r'][key]
            za, zb = math.floor(m['tg_heel']) + 1, math.floor(m['truck'])
            return g0 + (g1 - g0) * (z - za) / max(1, zb - za)
        t0, t1 = RB['topmast_r'][key]
        zp, zt2 = math.floor(m['platform']), math.floor(m['tm_top'])
        return t0 + (t1 - t0) * (z - zp - 1) / max(1, zt2 - zp - 1)

    ax = lambda key, z: float(LY.mast_axis_x(plan, key, z + 0.5, L))
    anchors = {k: {} for k in ('hull', 'channels', 'fore', 'main', 'mizzen', 'bowsprit', 'deck-tolda', 'espolon')}      # 聖羅曼號
    # ── channels（兩舷一件）＋ deadeye ──
    CH = RG['channels']
    chan, skipped = {}, 0
    for key in ALL:
        xm = M[key]['x']
        n = CH['shrouds'][key] + CH['backstays'].get(key, 0)
        xs = [xm - CH['first_aft'][key] - i * CH['spacing'][key] for i in range(n)]
        zc = top_z(xm) - CH['below_rail'][key]
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
    for key in ALL:
        m = M[key]
        A_ = anchors[key]
        zp = int(math.floor(m['platform']))
        zh = zp - 5 if key in RB['tops'] else int(math.floor(m['lower_top'])) - 4      # bonaventure 沒有桅樓 ⇒ hound 在下桅頂往下 4（收穫號）
        r = mast_r(key, zh)
        for s_, sg in (('S', 1), ('P', -1)):
            A_['hound-' + s_] = [int(round(ax(key, zh))), YC + sg * (int(math.ceil(r)) + 1), zh]
        A_['stay-head'] = [int(math.floor(ax(key, zh) + r)) + 1, YC, zh]
        if key not in MASTS:
            continue
        zf = zp - 25
        for s_, sg in (('S', 1), ('P', -1)):
            A_['futtock-' + s_] = [int(round(ax(key, zf))), YC + sg * (int(math.ceil(mast_r(key, zf))) + 1), zf]
        zt = int(math.floor(m['tm_top'])) - (8 if 'tg_heel' not in m else 4)
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
        if 'tg_heel' in m:                                                 # 十字桅頂架兩端（上桅 shroud 的下端）、上桅的 hound 與 stay-head
            zc_ = int(math.floor(m['tm_top'])) - 1
            xa_ = ax(key, zc_)
            cr = RB['crosstree_r']
            for s_, sg in (('S', 1), ('P', -1)):
                for j, dx in enumerate((-1, 1), 1):
                    A_['ct-%s-%d' % (s_, j)] = [int(xa_) + dx, YC + sg * cr, zc_]
            A_['ct-aft'] = [int(xa_) - cr, YC, zc_]
            zg = int(math.floor(m['truck'])) - 5
            rg = mast_r(key, zg)
            for s_, sg in (('S', 1), ('P', -1)):
                A_['tg-hound-' + s_] = [int(round(ax(key, zg))), YC + sg * (int(math.ceil(rg)) + 1), zg]
            A_['tg-stay-head'] = [int(math.floor(ax(key, zg) + rg)) + 1, YC, zg]
    for key, nm, deck in (('fore', 'mainstay-foot', 'castillo'), ('main', 'mizzenstay-foot', 'main')):      # 聖羅曼號：主支索綁前桅（castillo 上）、後桅支索綁主桅（主甲板上）
        z = int(LY.deck_z(plan, deck, M[key]['x'] + 0.5)) + 3
        anchors[key][nm] = [int(math.floor(ax(key, z) - mast_r(key, z))) - 1, YC, z]
    # ── 艏斜桅上的點（含斜桅頂桅的頂）──
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
    if 'sprit_top' in RB:      # 聖羅曼號：沒有斜桅頂桅 ⇒ 不登記
        ST = RB['sprit_top']
        ts = Lb - ST['at_from_tip']
        sx = Hh[0] + ts * u[0]
        st_len = next(r for r in plan['masts']['rows'] if r['key'] == 'bowsprit')['sprit_top_m'] / 0.1
        sz0 = Hh[2] + ts * u[2] + rb(ts) - 1.0
        BA['sprit-top'] = [int(math.floor(sx)), YC, int(math.floor(sz0 + st_len)) - 1]
    # ── 船首喙的 bobstay 腳：cutwater 最前面那一格 ──
    gal = {tuple(r[:3]) for r in export_list('pinnacle-patache-01m-espolon', None).tolist()}
    for i, z in enumerate(RG.get('bobstay_z', (55, 70)), 1):      # 聖羅曼號：喙在 z 6–36 ⇒ 高度照 plan
        xf = max(x for (x, y, zz) in gal if y == YC and zz == z)
        anchors['espolon']['bobstay-%d' % i] = [xf, YC, z]
    # ── 船殼上的點：舷頂（那一欄最外那一格）——帆腳索、tack、三角帆 sheet、艏斜桅 shroud ──
    def rail(x):
        z = max(zz for (xx, zz) in hout if xx == x)
        return [x, hout[(x, z)], z]
    H = anchors['hull']
    SL = RG['sails']
    belay = {}
    BX = SL['bow_belay_max_x']                                              # 船頭那一欄的上限（收穫號／藍鯊號寫死 495）
    for key in ('fore', 'main'):
        belay['%s-sheet' % key] = min(BX, M[key]['x'] - SL['sheet_aft'])
        belay['%s-tack' % key] = min(BX, M[key]['x'] + SL['tack_fwd'])
    belay['sprit'] = SL['sprit_belay_x']
    belay['mizzen-lateen'] = SL['lateen_sheet_x']['mizzen']
    for nm, x in belay.items():
        p = rail(x)
        H['belay-%s-S' % nm] = [p[0], YC + p[1], p[2]]
        H['belay-%s-P' % nm] = [p[0], YC - p[1], p[2]]
    zb = top_z(BX) - 1
    for s_, sg in (('S', 1), ('P', -1)):
        H['bs-shroud-' + s_] = [BX, YC + sg * hout[(BX, zb)], zb]
        if 'bonaventure_sheet_dy' not in SL:      # 聖羅曼號：沒有 bonaventure
            continue
        y = YC + sg * SL['bonaventure_sheet_dy']                          # bonaventure 的 sheet：船尾舷頂（避開三盞燈；收穫號）
        zr = max(zz for (xx, yy, zz) in hull if yy == y)
        H['belay-bonaventure-lateen-' + s_] = [min(xx for (xx, yy, zz) in hull if yy == y and zz == zr), y, zr]
    for key, (deck, x) in SL['lateen_tack'].items():
        z = int(LY.deck_z(plan, deck, x + 0.5)) + 1
        anchors['deck-' + deck]['tack-%s' % key] = [x, YC, z]

    # ── 繩 ──
    C = RG['colors']
    T = RG['thick']
    ropes = []

    def rope(name, a_, b_, group, th, slack=1.0, color=None, meta=None):
        ropes.append({'name': name, 'from': a_, 'to': b_, 'group': group, 'thickness': th, 'slack': slack, 'color': color or C['standing'], 'meta': meta})
    for key in ALL:
        Lk = LINK[key]
        ns, nb = CH['shrouds'][key], CH['backstays'].get(key, 0)
        for s_ in ('S', 'P'):
            for i in range(1, ns + 1):
                rope('%s-shroud-%s-%d' % (key, s_, i), '支索板/deadeye-%s-%s-%d' % (key, s_, i), '%s/hound-%s' % (Lk, s_), 'standing/shrouds', T['shroud'] if key in MASTS else T['backstay'])
            if key not in MASTS:
                continue
            for b in range(1, nb + 1):
                rope('%s-topmast-backstay-%s-%d' % (key, s_, b), '支索板/deadeye-%s-%s-%d' % (key, s_, ns + b), '%s/tm-hound-%s' % (Lk, s_), 'standing/backstays', T['backstay'])
            for i in range(1, RG['topmast_shrouds'] + 1):
                rope('%s-topmast-shroud-%s-%d' % (key, s_, i), '%s/rim-%s-%d' % (Lk, s_, i), '%s/tm-hound-%s' % (Lk, s_), 'standing/topmast-shrouds', T['topmast_shroud'])
                rope('%s-futtock-%s-%d' % (key, s_, i), '%s/rim-low-%s-%d' % (Lk, s_, i), '%s/futtock-%s' % (Lk, s_), 'standing/futtock-shrouds', T['futtock'])
            if 'tg_heel' in M[key]:
                for j in range(1, RG['tgallant_shrouds'] + 1):
                    rope('%s-topgallant-shroud-%s-%d' % (key, s_, j), '%s/ct-%s-%d' % (Lk, s_, j), '%s/tg-hound-%s' % (Lk, s_), 'standing/topgallant-shrouds', T['tgallant_shroud'])
    for nm, a_, b_, th in (('fore-stay', '前桅/stay-head', '艏斜桅/forestay-foot', T['stay']),
                           ('fore-topmast-stay', '前桅/tm-stay-head', '艏斜桅/cap-top', T['tm_stay']),
                           ('main-stay', '主桅/stay-head', '前桅/mainstay-foot', T['stay']),
                           ('main-topmast-stay', '主桅/tm-stay-head', '前桅/top-aft', T['tm_stay']),
                           ('mizzen-stay', '後桅/stay-head', '主桅/mizzenstay-foot', T['tm_stay'])):      # 聖羅曼號：沒有上桅、後中桅、bonaventure 的支索
        rope(nm, a_, b_, 'standing/stays', th)
    for i in (1, 2):
        rope('bobstay-%d' % i, '船首喙/bobstay-%d' % i, '艏斜桅/bob-%d' % i, 'standing/bowsprit', T['bobstay'])
    for s_ in ('S', 'P'):
        rope('bowsprit-shroud-' + s_, '船殼/bs-shroud-' + s_, '艏斜桅/side-' + s_, 'standing/bowsprit', T['bobstay'])

    # ── ratlines：橫繩組（Ship_Rigging §6）；下桅那組是繩梯（foot ＝ 舷牆內側的甲板、head ＝ 桅頂平台靠這一舷的邊）──
    RL = RG['ratlines']
    ratsets, climb_bad = [], []

    def stand_ok(p):
        x, y, z = p
        return (x, y, z - 1) in occ and all((x, y, z + k) not in occ for k in range(0, 7))
    for key in MASTS:
        m = M[key]
        for s_, sg in (('S', 1), ('P', -1)):
            ns = CH['shrouds'][key]
            d1, dn = anchors['channels']['deadeye-%s-%s-1' % (key, s_)], anchors['channels']['deadeye-%s-%s-%d' % (key, s_, ns)]
            xm_ = int(round((d1[0] + dn[0]) / 2.0))
            zf_ = int(LY.deck_z(plan, DECK_OF[key], xm_ + 0.5)) + 1
            dyw = next(d for d in range(8, 60) if (xm_, YC + sg * d, zf_) in occ)   # 離中線 8 格起往外第一格實心 ＝ 舷牆內面（v1 從 0 起 ⇒ 主桅那組先撞到主桅本身）
            foot = [xm_, YC + sg * (dyw - 3), zf_]
            zp = int(math.floor(m['platform']))
            head = [int(round(ax(key, zp))), YC + sg * (RB['tops'][key] - 3), zp + 1]
            for nm_, p in (('foot', foot), ('head', head)):
                if not stand_ok(p):
                    climb_bad.append('%s-lower-%s.%s %s' % (key, s_, nm_, p))
            ratsets.append({'name': '%s-lower-%s' % (key, s_), 'rope_a': '%s-shroud-%s-1' % (key, s_), 'rope_b': '%s-shroud-%s-%d' % (key, s_, ns),
                            'step': RL['step'], 'start': RL['lower']['start'], 'stop': RL['lower']['stop'], 'min_span': RL['min_span'],
                            'thickness': RL['th'], 'color': RL['color'], 'group': 'ratlines/lower', 'climb': 1,
                            'foot': '%d,%d,%d' % tuple(foot), 'head': '%d,%d,%d' % tuple(head)})
            ratsets.append({'name': '%s-topmast-%s' % (key, s_), 'rope_a': '%s-topmast-shroud-%s-1' % (key, s_),
                            'rope_b': '%s-topmast-shroud-%s-%d' % (key, s_, RG['topmast_shrouds']),
                            'step': RL['step'], 'start': RL['topmast']['start'], 'stop': RL['topmast']['stop'], 'min_span': RL['min_span'],
                            'thickness': RL['tm_th'], 'color': RL['color'], 'group': 'ratlines/topmast'})

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
    yat = lambda nm: np.array(next(y for y in YP if y['name'] == nm)['at'])
    sails = []

    def sail(name, corners, bind, free, meta, names, fullness=None, color=None, texture=None):
        sails.append({'name': name, 'corners': corners, 'corner_names': names, 'bind': bind, 'free': free, 'meta': meta,
                      'fullness': fullness or SL['fullness'], 'color': color or C['sail'], 'texture': texture})
    fmt = lambda p: '%.2f,%.2f,%.2f' % tuple(p)
    os.makedirs(os.path.join(design, 'textures'), exist_ok=True)
    SET = RG['sail_set']

    def square(nm, host, yname, lower_yard, clews, kind, sheet_to):
        meta = {'kind': 'sail', 'mast': 'bowsprit' if host == '艏斜桅' else nm.split('-')[0], 'sail': kind}
        if kind in SET:
            meta['set'] = SET[kind]
        sail(nm, ['model:%s/%s/earing-P' % (host, yname), 'model:%s/%s/earing-S' % (host, yname), clews[0], clews[1]], [0], ['clew_s', 'clew_p'],
             meta, ['head_p', 'head_s', 'clew_s', 'clew_p'])
        for s_, c in (('S', 'clew_s'), ('P', 'clew_p')):
            rope('%s.sheet-%s' % (nm, s_), 'sail:%s/%s' % (nm, c), sheet_to(s_), 'running/sheets', T['sheet'], 1.0, C['running'], {'kind': 'sheet', 'sail': nm})

    def clews_above(lower):                                             # 帆腳 ＝ 下一根帆桁的 earing 往中間收一點、往上 2 格
        out = []
        for s_ in ('S', 'P'):
            e, pv = model_pt(lower, 'earing-' + s_), yat(lower)
            p = e + SL['clew_in'] * (pv - e)
            p[2] += 2
            out.append(fmt(p))
        return out
    for key in ('fore', 'main'):
        Lk = LINK[key]
        cy, ty, gy = 'yard-%s-course' % key, 'yard-%s-topsail' % key, 'yard-%s-topgallant' % key
        cps = []
        for s_ in ('S', 'P'):
            e, pv = model_pt(cy, 'earing-' + s_), yat(cy)
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
        square('%s-topsail' % key, Lk, ty, cy, clews_above(cy), 'topsail', lambda s_, cy=cy, Lk=Lk: 'model:%s/%s/earing-%s' % (Lk, cy, s_))
        if any(y['name'] == gy for y in YP):      # 聖羅曼號：沒有上桅帆
            square('%s-topgallant' % key, Lk, gy, ty, clews_above(ty), 'topgallant', lambda s_, ty=ty, Lk=Lk: 'model:%s/%s/earing-%s' % (Lk, ty, s_))
    # 後中桅帆（kruiszeil）：帆腳綁後桅桅樓邊
    if any(y['name'] == 'yard-mizzen-topsail' for y in YP):      # 聖羅曼號：沒有後中桅帆
        rimc = []
        for s_ in ('S', 'P'):
            p = np.array(anchors['mizzen']['rim-%s-2' % s_], float) + 0.5
            p[2] += 2
            rimc.append(fmt(p))
        square('mizzen-topsail', '後桅', 'yard-mizzen-topsail', None, rimc, 'topsail', lambda s_: '後桅/rim-%s-2' % s_)
    # 斜桅帆（blinde）與斜桅頂帆（boven blinde）
    cps = []
    for s_ in ('S', 'P'):
        e, pv = model_pt('yard-spritsail', 'earing-' + s_), yat('yard-spritsail')
        p = e + SL['clew_in'] * (pv - e)
        p[2] -= SL['sprit_drop']
        cps.append(fmt(p))
    square('spritsail', '艏斜桅', 'yard-spritsail', None, cps, 'spritsail', lambda s_: '船殼/belay-sprit-%s' % s_)
    if any(y['name'] == 'yard-sprit-topsail' for y in YP):      # 聖羅曼號：沒有斜桅頂帆
        square('sprit-topsail', '艏斜桅', 'yard-sprit-topsail', 'yard-spritsail', clews_above('yard-spritsail'), 'sprit_topsail',
               lambda s_: 'model:艏斜桅/yard-spritsail/earing-%s' % s_)
    # 兩面三角帆（mesana、contramesana；照收穫號）
    for key in [k for k in ('mizzen', 'bonaventure') if k in SL['lateen_clew']]:      # 聖羅曼號：一面三角帆
        Lk = LINK[key]
        nm, yn = '%s-lateen' % key, 'yard-%s-lateen' % key
        cx, cz = SL['lateen_clew'][key]
        sail(nm, ['model:%s/%s/fore' % (Lk, yn), 'model:%s/%s/peak' % (Lk, yn), fmt([cx + 0.5, YC + 0.5, cz + 0.5])], [0], ['clew'],
             {'kind': 'sail', 'mast': key, 'sail': 'gaff'}, ['tack', 'head', 'clew'])
        for s_ in ('S', 'P'):
            rope('%s.sheet-%s' % (nm, s_), 'sail:%s/clew' % nm, '船殼/belay-%s-lateen-%s' % (key, s_), 'running/sheets', T['sheet'], 1.03, C['running'], {'kind': 'sheet', 'sail': nm})
        deck = SL['lateen_tack'][key][0]
        rope('%s.tack' % nm, 'sail:%s/tack' % nm, '甲板-%s/tack-%s' % (deck, key), 'running/tacks', T['tack'], 1.0, C['running'], {'kind': 'tack', 'sail': nm})
    # 旗：船尾旗（勃艮第十字）掛在 bonaventure 三角帆桁後端、主桅頂長旗
    FL = RG['flags']
    ew, eh = FL['ensign']
    LAT = json.load(open(os.path.join(design, 'yards_lateen.json'), encoding='utf-8'))
    ek = 'bonaventure' if 'bonaventure' in LINK else 'mizzen'      # 聖羅曼號：船尾旗掛在後桅三角帆桁後端
    Lk, yn = LINK[ek], 'yard-%s-lateen' % ek
    pk_loc = LAT[ek]['anchors']['peak']
    pyp = next(y for y in YP if y['name'] == yn)
    pk = np.array(pyp['at']) + (np.array(pk_loc, float) + 0.5 - np.array(pyp['pivot']))
    sail('ensign', ['model:%s/%s/peak' % (Lk, yn), fmt(pk - [ew, 0, 0]), fmt(pk - [ew, 0, eh]),
                    'model:%s/%s/%d,%d,%d' % (Lk, yn, pk_loc[0], pk_loc[1], pk_loc[2] - eh)],
         [3], [2, 1], {'kind': 'flag', 'flag': 'ensign'}, None, fullness=1.04, color='#ffffff', texture='textures/ensign.png')
    tz = math.floor(M['main']['truck'])
    tx = ax('main', tz)
    pl_, ph = FL['pennant']
    sail('pennant', [fmt([tx + 0.5, YC + 0.5, tz - 1]), fmt([tx - pl_, YC + 0.5, tz - 2]), fmt([tx + 0.5, YC + 0.5, tz - 1 - ph])],
         [2], [1], {'kind': 'flag', 'flag': 'pennant', 'mast': 'main'}, None, fullness=1.04, color=FL['pennant_color'])
    cross_png(os.path.join(design, 'textures', 'ensign.png'), ew, eh, (245, 245, 240, 255), (190, 20, 30, 255))
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
         'anchors': {k: len(v) for k, v in anchors.items()}, 'ropes': len(ropes), 'ratline_sets': len(ratsets), 'climb_bad': climb_bad,
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
        f.write('# 聖羅曼號 channels 兩舷（支索板＋deadeye；世界座標，at 0,0,0）\n')
        for k in sorted(chan):
            f.write('%d,%d,%d,%d\n' % (k[0], k[1], k[2], chan[k]))
    R['channels']['sha256'] = hashlib.sha256(open(p, 'rb').read()).hexdigest()
    works = {'hull': 'pinnacle-patache-01m', 'channels': 'pinnacle-patache-01m-channels', 'bowsprit': 'pinnacle-patache-01m-bowsprit', 'espolon': 'pinnacle-patache-01m-espolon',
             'deck-tolda': 'pinnacle-patache-01m-deck-tolda'}      # 聖羅曼號
    for k in ALL:
        works[k] = 'pinnacle-patache-01m-mast-' + k
    out = {'anchors': anchors, 'anchor_works': works, 'ropes': ropes, 'ratlines': ratsets, 'sails': sails, 'meta': metas, 'wind': RG['wind'], 'sail_seconds': RG['sail_seconds']}
    with open(os.path.join(design, 'rigging_plan.json'), 'w', encoding='utf-8', newline='\n') as f:
        json.dump(out, f, ensure_ascii=False, indent=1, default=lambda o: o.item())
    with open(os.path.join(design, 'verify_rigging.json'), 'w', encoding='utf-8', newline='\n') as f:
        json.dump(R, f, ensure_ascii=False, indent=1, default=lambda o: o.item())
    print(json.dumps(R, ensure_ascii=False, default=lambda o: o.item()))


if __name__ == '__main__':
    main()
