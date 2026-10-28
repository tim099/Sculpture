# 澤漢號 步驟 8（TASK-0966）：出處 ame-labelle-01m/design/draft_rigging.py（拉貝爾號；它出自收穫號）—— 本船：上桅 shrouds／futtock 綁桅樓籃子（plan.rig_build.tops）、下桅繩梯 climb＝1（head 在桅樓平台）、繫索點與 bobstay 高度改讀 plan、旗換荷蘭三色旗。
# 原檔頭：拉貝爾號 步驟 8：channels（兩舷一件）、桅／艏斜桅／船殼／甲板／船首喙的固定點、靜索、ratlines（橫繩組）、帆（方帆、spritsail、lateen）、帆自己的繩、旗、meta
#   出處：calli-cosecha-01m/design/draft_rigging.py（收穫號 階段七）；改的地方：
#     · 沒有桅樓 ⇒ 上桅 shrouds、futtock 綁桅頂橫桁兩端；main topmast stay 綁前桅橫桁後端
#     · ratlines 改成橫繩組（Ship_Rigging §6，TASK-0678；收穫號那時候還是一條一條的子繩）⇒ 輸出 ratline_sets，tools/rigging_apply.py ratlines 那一步下 sub=ratlines
#     · channels 每根桅自己的 spacing、在舷頂那兩格（砲門頂上面）；沒有 bonaventure；旗換成法國的白底三朵金百合
#   輸入：plan.json（rigging、rig_build、masts）＋ yards_placement.json／yards_lateen.json（帆桁模型）＋ 組裝件現在的格子（CLI 匯出）
#   輸出：masks/rigging/channels.vox.txt（世界座標，at 0,0,0）、rigging_plan.json（固定點、繩、橫繩組、帆、meta）、textures/*.png、verify_rigging.json
#   用法：python -I -X utf8 draft_rigging.py <design> [--probe=nometa=<繩名>]（反向對照：拿掉一條繩的 meta，看報不報；⛔ 不寫檔）
import sys, os, json, math, hashlib
import numpy as np
from PIL import Image

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), 'tools'))
import lines as HL
import layout as LY
from wio import export_list

LINK = {'fore': '前桅', 'main': '主桅', 'mizzen': '後桅', 'bowsprit': '艏斜桅'}
MASTS = ('fore', 'main', 'mizzen')


def ensign_png(path, W, H):
    """荷蘭三色旗（Statenvlag：紅、白、藍三條橫紋；1660 年代的商船旗）。"""
    im = Image.new('RGBA', (W * 4, H * 4), (248, 248, 244, 255))
    px = im.load()
    for yy in range(H * 4):
        c = (174, 28, 40, 255) if yy < H * 4 // 3 else ((248, 248, 244, 255) if yy < H * 8 // 3 else (33, 70, 139, 255))
        for xx in range(W * 4):
            px[xx, yy] = c
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
    A = export_list('abigail-fluyt-01m-assembly', None, links=None)
    own = set()
    if os.path.exists(os.path.join(WORKS, 'abigail-fluyt-01m-channels', 'work.json')):
        own = set(map(tuple, export_list('abigail-fluyt-01m-channels', None)[:, :3].tolist()))
    occ = {tuple(r[:3]) for r in A.tolist()} - own
    hull = {tuple(r[:3]) for r in export_list('abigail-fluyt-01m', None).tolist()}
    hout = {}
    for x, y, z in hull:
        d = abs(y - YC)
        if d > hout.get((x, z), -1):
            hout[(x, z)] = d
    htop = {}
    for x, y, z in hull:
        htop[x] = max(htop.get(x, -1), z)

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
    anchors = {k: {} for k in ('hull', 'channels', 'fore', 'main', 'mizzen', 'bowsprit', 'deck-main', 'head')}
    # ── channels（兩舷一件）＋ deadeye：舷頂那兩格的舷外 ──
    CH = RG['channels']
    chan, skipped = {}, 0
    for key in MASTS:
        xm = M[key]['x']
        n = CH['shrouds'][key] + CH['backstays'].get(key, 0)
        fa = CH.get('first_aft_by_mast', {}).get(key, CH['first_aft'])     # 本船前桅在船首樓裡 ⇒ 從桅前面起排
        xs = [xm - fa - i * CH['spacing'][key] for i in range(n)]
        zc = htop[xm] - CH['below_rail']
        for x in range(min(xs) - 2, max(xs) + 3):
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
    #   本船有桅樓（plan.rig_build.tops，收穫號的 cofa）⇒ 上桅 shrouds 從籃子邊緣頂上起、futtock 從平台底下起（拉貝爾號是桅頂橫桁兩端）
    TP = RB.get('tops', {})
    for key in MASTS:
        m = M[key]
        A_ = anchors[key]
        zp = TP.get('z', {}).get(key, int(math.floor(m['platform'])))   # 桅樓平台另外指定高度（後桅，同 draft_masts）
        zh = zp - 3 if key in TP else int(math.floor(m['lower_top'])) - 4
        r = mast_r(key, zh)
        for s_, sg in (('S', 1), ('P', -1)):
            A_['hound-' + s_] = [int(round(ax(key, zh))), YC + sg * (int(math.floor(r)) + 1), zh]
        A_['stay-head'] = [int(math.floor(ax(key, zh) + r)) + 1, YC, zh]
        if key in RB['topmast_r']:
            Rt = TP[key]
            xa = round(ax(key, zp))
            zf = zp - 12
            for s_, sg in (('S', 1), ('P', -1)):
                A_['futtock-' + s_] = [int(round(ax(key, zf))), YC + sg * (int(math.floor(mast_r(key, zf))) + 1), zf]
            zt = int(math.floor(m['truck'])) - 5
            rt = mast_r(key, zt)
            for s_, sg in (('S', 1), ('P', -1)):
                A_['tm-hound-' + s_] = [int(round(ax(key, zt))), YC + sg * (int(math.floor(rt)) + 1), zt]
            A_['tm-stay-head'] = [int(math.floor(ax(key, zt) + rt)) + 1, YC, zt]
            # 桅樓籃子這一舷的邊：上桅 shrouds 從籃子頂上一格起（rim 頂 zp＋rim_h，半徑 Rt）、futtock 從平台底下一格（zp − 2；平台 zp−1..zp）
            #   一舷 n 根，前後各 TS_DX 格排開（1 號 ＝ 最前面，同下桅 shroud）；繩梯 head 站在平台上、這一舷的邊往裡 3 格
            n_ts = RG['topmast_shrouds']
            for i in range(1, n_ts + 1):
                dx = RG['topmast_shroud_dx'] * ((n_ts + 1) / 2.0 - i)
                for s_, sg in (('S', 1), ('P', -1)):
                    A_['top-%s-%d' % (s_, i)] = [int(round(xa + dx)), YC + sg * Rt, zp + RB['tops']['rim_h'] + 1]
                    A_['top-low-%s-%d' % (s_, i)] = [int(round(xa + dx)), YC + sg * (Rt - 1), zp - 2]
            for s_, sg in (('S', 1), ('P', -1)):
                A_['climb-head-' + s_] = [xa, YC + sg * (Rt - 3), zp + 1]
            A_['top-aft'] = [xa - Rt - 1, YC, zp + 1]
        elif key in TP:                                          # 有桅樓、沒有上桅（後桅）：只有繩梯 head
            Rt, xa = TP[key], round(ax(key, zp))
            for s_, sg in (('S', 1), ('P', -1)):
                A_['climb-head-' + s_] = [xa, YC + sg * (Rt - 3), zp + 1]
    for key, nm, deck in (('fore', 'mainstay-foot', 'forecastle'), ('main', 'mizzenstay-foot', 'main')):
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
    for i, f in enumerate((RG['bobstay_at'],), 1):     # 一條 bobstay（拉貝爾號 0.75；本船的紅獅趴在 knee 上 ⇒ 0.6，繩從獅子前面過）
        BA['bob-%d' % i] = cell(Hh + f * Lb * u - (rb(f * Lb) + 1) * w)
    # ── 船首喙的 bobstay 腳：knee 最前面那一格 ──
    head = {tuple(r[:3]) for r in export_list('abigail-fluyt-01m-head', None).tolist()}
    for i, z in enumerate((RG['bobstay_head_z'],), 1):
        xf = max(x for (x, y, zz) in head if y == YC and zz == z)
        anchors['head']['bobstay-%d' % i] = [xf + 1, YC, z]          # knee 最前面那一格的前面一格（空氣；繩從這裡往前上，不貼著 knee 往上斜的前緣）

    # ── 船殼上的點：舷頂（那一欄最外那一格）——帆腳索、tack、lateen sheet、艏斜桅 shroud ──
    def rail(x):
        z = htop[x]
        return [x, hout[(x, z)], z]
    H = anchors['hull']
    SL = RG['sails']
    belay = {}
    xmax = SL['belay_x_max']                          # 船頭最後一個繫得住的舷頂 x（拉貝爾號寫死 220）
    for key in ('fore', 'main'):
        belay['%s-sheet' % key] = min(xmax, M[key]['x'] - SL['sheet_aft'][key])
        belay['%s-tack' % key] = min(xmax, M[key]['x'] + SL['tack_fwd'][key])
    belay['sprit'] = SL['sprit_belay_x']
    belay['mizzen-lateen'] = SL['lateen_sheet_x']
    for nm, x in belay.items():
        p = rail(x)
        H['belay-%s-S' % nm] = [p[0], YC + p[1], p[2]]
        H['belay-%s-P' % nm] = [p[0], YC - p[1], p[2]]
    p = rail(SL['bs_shroud_x'])
    for s_, sg in (('S', 1), ('P', -1)):
        H['bs-shroud-' + s_] = [p[0], YC + sg * p[1], p[2]]
    for key, (deck, x) in SL['lateen_tack'].items():
        z = int(LY.deck_z(plan, deck, x + 0.5)) + 1
        anchors['deck-' + deck]['tack-%s' % key] = [x, YC, z]

    # ── 繩 ──
    C = RG['colors']
    T = RG['thick']
    ropes = []

    def rope(name, a_, b_, group, th, slack=1.0, color=None, meta=None):
        ropes.append({'name': name, 'from': a_, 'to': b_, 'group': group, 'thickness': th, 'slack': slack, 'color': color or C['standing'], 'meta': meta})
    for key in MASTS:
        Lk = LINK[key]
        ns, nb = CH['shrouds'][key], CH['backstays'].get(key, 0)
        for s_ in ('S', 'P'):
            for i in range(1, ns + 1):
                rope('%s-shroud-%s-%d' % (key, s_, i), '支索板/deadeye-%s-%s-%d' % (key, s_, i), '%s/hound-%s' % (Lk, s_), 'standing/shrouds', T['shroud'])
            for b in range(1, nb + 1):
                rope('%s-topmast-backstay-%s-%d' % (key, s_, b), '支索板/deadeye-%s-%s-%d' % (key, s_, ns + b), '%s/tm-hound-%s' % (Lk, s_), 'standing/backstays', T['backstay'])
            if key in RB['topmast_r']:
                for i in range(1, RG['topmast_shrouds'] + 1):
                    rope('%s-topmast-shroud-%s-%d' % (key, s_, i), '%s/top-%s-%d' % (Lk, s_, i), '%s/tm-hound-%s' % (Lk, s_), 'standing/topmast-shrouds', T['topmast_shroud'])
                    rope('%s-futtock-%s-%d' % (key, s_, i), '%s/top-low-%s-%d' % (Lk, s_, i), '%s/futtock-%s' % (Lk, s_), 'standing/futtock-shrouds', T['futtock'])
    for nm, a_, b_, th in (('fore-stay', '前桅/stay-head', '艏斜桅/forestay-foot', T['stay']),
                           ('fore-topmast-stay', '前桅/tm-stay-head', '艏斜桅/cap-top', T['tm_stay']),
                           ('main-stay', '主桅/stay-head', '前桅/mainstay-foot', T['stay']),
                           ('main-topmast-stay', '主桅/tm-stay-head', '前桅/top-aft', T['tm_stay']),
                           ('mizzen-stay', '後桅/stay-head', '主桅/mizzenstay-foot', T['tm_stay'])):
        rope(nm, a_, b_, 'standing/stays', th)
    for i in (1,):
        rope('bobstay-%d' % i, '船首喙/bobstay-%d' % i, '艏斜桅/bob-%d' % i, 'standing/bowsprit', T['bobstay'])
    for s_ in ('S', 'P'):
        rope('bowsprit-shroud-' + s_, '船殼/bs-shroud-' + s_, '艏斜桅/side-' + s_, 'standing/bowsprit', T['bobstay'])
    # ratlines：橫繩組（每根桅、每一層、每一舷一組；rope_a ＝ 最前那根 ＝ 1 號）
    RL = RG['ratlines']
    rsets = []
    climb_deck = RL['climb_deck']
    for key in MASTS:
        for s_, sg in (('S', 1), ('P', -1)):
            rs = {'name': '%s-lower-%s' % (key, s_), 'rope_a': '%s-shroud-%s-1' % (key, s_), 'rope_b': '%s-shroud-%s-%d' % (key, s_, CH['shrouds'][key]),
                  'step': RL['step'], 'start': RL['start'], 'stop': RL['stop'], 'min_span': RL['min_span'], 'thickness': RL['th'], 'group': 'ratlines/lower'}
            if key in TP:
                # 繩梯（Ship_Rigging §6）：foot ＝ deadeye 那一段中間往船內、過了舷牆之後的甲板再往內 2 格；head ＝ 桅樓平台這一舷的邊
                xs_ = [anchors['channels']['deadeye-%s-%s-%d' % (key, s_, i)][0] for i in range(1, CH['shrouds'][key] + 1)]
                xf = int(round(sum(xs_) / float(len(xs_))))
                zf_ = int(LY.deck_z(plan, climb_deck[key], xf + 0.5)) + 1
                yi = hout[(xf, zf_)] - plan['hull_build']['wall'] - 2
                rs.update({'climb': 1, 'foot': [xf, YC + sg * yi, zf_], 'head': anchors[key]['climb-head-' + s_]})
            rsets.append(rs)
            if key in RB['topmast_r'] and RG['topmast_shrouds'] >= 3:      # 上桅三根 shroud（桅樓籃子邊上、前後排開）⇒ 做 topmast ratlines（不標 climb：上面沒有站得住的平台）
                rsets.append({'name': '%s-topmast-%s' % (key, s_), 'rope_a': '%s-topmast-shroud-%s-1' % (key, s_), 'rope_b': '%s-topmast-shroud-%s-%d' % (key, s_, RG['topmast_shrouds']),
                              'step': RL['tm_step'], 'start': RL['tm_start'], 'stop': RL['tm_stop'], 'min_span': RL['min_span'], 'thickness': RL['tm_th'], 'group': 'ratlines/topmast'})

    def wpt(spec):
        fr, nm = spec.split('/', 1)
        part = {'支索板': 'channels', '船殼': 'hull', '船首喙': 'head', '甲板-main': 'deck-main'}.get(fr)
        if part is None:
            part = {v: k for k, v in LINK.items()}[fr]
        return np.array(anchors[part][nm], float) + 0.5

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
            p[2] = htop[int(p[0])] + SL['course_clew_above_rail']
            cps.append(fmt(p))
        nm = '%s-course' % key
        sail(nm, ['model:%s/%s/earing-P' % (Lk, cy), 'model:%s/%s/earing-S' % (Lk, cy), cps[0], cps[1]], [0], ['clew_s', 'clew_p'],
             {'kind': 'sail', 'mast': key, 'sail': 'course'}, ['head_p', 'head_s', 'clew_s', 'clew_p'])
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
    for key in ('mizzen',):
        Lk = LINK[key]
        nm = '%s-lateen' % key
        yn = 'yard-%s-lateen' % key
        cx, cz = SL['lateen_clew'][key]
        sail(nm, ['model:%s/%s/fore' % (Lk, yn), 'model:%s/%s/peak' % (Lk, yn), fmt([cx + 0.5, YC + 0.5, cz + 0.5])], [0], ['clew'],
             {'kind': 'sail', 'mast': key, 'sail': 'gaff'}, ['tack', 'head', 'clew'])
        for s_ in ('S', 'P'):
            rope('%s.sheet-%s' % (nm, s_), 'sail:%s/clew' % nm, '船殼/belay-%s-lateen-%s' % (key, s_), 'running/sheets', T['sheet'], 1.03, C['running'], {'kind': 'sheet', 'sail': nm})
        deck = SL['lateen_tack'][key][0]
        rope('%s.tack' % nm, 'sail:%s/tack' % nm, '甲板-%s/tack-%s' % (deck, key), 'running/tacks', T['tack'], 1.0, C['running'], {'kind': 'tack', 'sail': nm})
    # 旗：白底三朵金百合掛在後桅 lateen 帆桁後端；主桅頂長旗
    FL = RG['flags']
    ew, eh = FL['ensign']
    LAT = json.load(open(os.path.join(design, 'yards_lateen.json'), encoding='utf-8'))
    pk_loc = LAT['mizzen']['anchors']['peak']
    pyp = next(y for y in YP if y['name'] == 'yard-mizzen-lateen')
    pk = np.array(pyp['at']) + (np.array(pk_loc, float) + 0.5 - np.array(pyp['pivot']))
    sail('ensign', ['model:後桅/yard-mizzen-lateen/peak', fmt(pk - [ew, 0, 0]), fmt(pk - [ew, 0, eh]),
                    'model:後桅/yard-mizzen-lateen/%d,%d,%d' % (pk_loc[0], pk_loc[1], pk_loc[2] - eh)],
         [3], [2, 1], {'kind': 'flag', 'flag': 'ensign'}, None, fullness=1.04, color='#ffffff', texture='textures/ensign.png')
    tz = math.floor(M['main']['truck'])
    tx = ax('main', tz)
    pl_, ph = FL['pennant']
    sail('pennant', [fmt([tx + 0.5, YC + 0.5, tz - 1]), fmt([tx - pl_, YC + 0.5, tz - 2]), fmt([tx + 0.5, YC + 0.5, tz - 1 - ph])],
         [2], [1], {'kind': 'flag', 'flag': 'pennant', 'mast': 'main'}, None, fullness=1.04, color=FL['pennant_color'])
    ensign_png(os.path.join(design, 'textures', 'ensign.png'), ew, eh)

    metas = [['sail', s['name'], s['meta']] for s in sails] + [['rope', r['name'], r['meta']] for r in ropes if r['meta']]
    if probe:
        nm = probe[0].split('=')[1]
        metas = [m for m in metas if not (m[0] == 'rope' and m[1] == nm)]
    # ── 讀數 ──
    names = [r['name'] for r in ropes]
    need = [r['name'] for r in ropes if r['name'].split('.')[0] in {s['name'] for s in sails} and '.' in r['name']]
    have = {m[1] for m in metas if m[0] == 'rope'}
    R = {'channels': {'cells': len(chan), 'skipped_on_ship': skipped, 'mirror_diff': sum(1 for (x, y, z), c in chan.items() if chan.get((x, 2 * YC - y, z)) != c)},
         'anchors': {k: len(v) for k, v in anchors.items()}, 'ropes': len(ropes), 'ratline_sets': len(rsets),
         'groups': {g: sum(1 for r in ropes if r['group'] == g) for g in sorted({r['group'] for r in ropes})},
         'sails': len(sails), 'meta': {'sails': sum(1 for m in metas if m[0] == 'sail'), 'ropes': len(have)},
         'sail_ropes_without_meta': sorted(set(need) - have), 'dup_rope_names': len(names) - len(set(names)),
         'anchors_in_solid': sorted('%s/%s' % (k, n) for k, v in anchors.items() for n, p in v.items() if tuple(p) in occ and k not in ('hull', 'head'))}
    # 繩穿過船上的格嗎（靜索：兩端各留 3 格不算）
    solid = set(occ) | set(chan)
    thru = {}
    for r in ropes:
        if r['from'].startswith(('sail:', 'model:', 'rope:')) or r['to'].startswith(('sail:', 'model:', 'rope:')):
            continue
        a_, b_ = wpt(r['from']), wpt(r['to'])
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
            thru[r['name']] = len(hits)
    R['ropes_through_solid'] = thru
    if probe:
        print(json.dumps({'probe': probe[0], 'sail_ropes_without_meta': R['sail_ropes_without_meta']}, ensure_ascii=False))
        return
    os.makedirs(os.path.join(design, 'masks', 'rigging'), exist_ok=True)
    p = os.path.join(design, 'masks', 'rigging', 'channels.vox.txt')
    with open(p, 'w', encoding='utf-8', newline='\n') as f:
        f.write('# 澤漢號 channels 兩舷（支索板＋deadeye；世界座標，at 0,0,0）\n')
        for k in sorted(chan):
            f.write('%d,%d,%d,%d\n' % (k[0], k[1], k[2], chan[k]))
    R['channels']['sha256'] = hashlib.sha256(open(p, 'rb').read()).hexdigest()
    works = {'hull': 'abigail-fluyt-01m', 'channels': 'abigail-fluyt-01m-channels', 'bowsprit': 'abigail-fluyt-01m-bowsprit', 'head': 'abigail-fluyt-01m-head',
             'deck-main': 'abigail-fluyt-01m-deck-main'}
    for k in MASTS:
        works[k] = 'abigail-fluyt-01m-mast-' + k
    out = {'anchors': anchors, 'anchor_works': works, 'ropes': ropes, 'ratline_sets': rsets, 'sails': sails, 'meta': metas, 'wind': RG['wind'], 'sail_seconds': RG['sail_seconds']}
    with open(os.path.join(design, 'rigging_plan.json'), 'w', encoding='utf-8', newline='\n') as f:
        json.dump(out, f, ensure_ascii=False, indent=1, default=lambda o: o.item())
    with open(os.path.join(design, 'verify_rigging.json'), 'w', encoding='utf-8', newline='\n') as f:
        json.dump(R, f, ensure_ascii=False, indent=1, default=lambda o: o.item())
    print(json.dumps(R, ensure_ascii=False, default=lambda o: o.item()))


if __name__ == '__main__':
    main()
