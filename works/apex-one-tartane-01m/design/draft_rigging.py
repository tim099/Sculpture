# 塔爾塔納 步驟 8（TASK-1299）：channels（支索板＋deadeyes）、船尾旗桿、固定點、靜索、ratlines 橫繩組（climb=1）、雙拉丁帆＋foc、帆索、托斯卡納國旗＋長旗、meta
#   用法：python -I -X utf8 draft_rigging.py <design> [--probe=nometa=<繩名>]
import sys, os, json, math, hashlib
import numpy as np
from PIL import Image

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), 'tools'))
import lines as HL
import layout as LY
from wio import export_list

LINK = {'fore': '桅-fore', 'main': '桅-main', 'bowsprit': '桅-bowsprit'}


def tuscany_ensign_png(path, W, H):
    """托斯卡納大公國聖斯德望騎士團旗（白底 #ece9e0 ＋ 紅色八角十字 stefano；對齊 Blockside 77_colours.js）。"""
    pw, ph = W * 4, H * 4
    im = Image.new('RGBA', (pw, ph), (236, 233, 224, 255))
    px = im.load()
    R, w0, w1, dv = 0.36, 0.03, 0.18, 0.12
    for py in range(ph):
        Y = (py + 0.5) / ph
        for px_i in range(pw):
            X = 2.0 * (px_i + 0.5) / pw
            dx, dy = abs(X - 1.0), abs(Y - 0.5)
            al, ac = max(dx, dy), min(dx, dy)
            if al <= R and ac <= w0 + (w1 - w0) * al / R and al <= R - dv + dv * ac / w1:
                px[px_i, py] = (184, 26, 23, 255)
    im.save(path)


def main():
    sys.stdout.reconfigure(encoding='utf-8')
    design = sys.argv[1]
    probe = [a.split('=', 1)[1] for a in sys.argv[2:] if a.startswith('--probe')]
    plan = HL.load_plan(design)
    L = HL.Lines(plan)
    YC = L.YC
    WORKS = os.environ.get('SCULPT_WORKS') or os.path.dirname(os.path.dirname(os.path.abspath(design)))
    YP = json.load(open(os.path.join(design, 'yards_placement.json'), encoding='utf-8'))
    M = {m['key']: m for m in LY.masts(plan, L)}
    B = LY.bowsprit(plan, L)

    # 讀取現況船殼＋甲板＋桅佔位（扣除自己支索板／旗桿以免重 run 自遮）
    A = export_list('apex-one-tartane-01m-assembly', None, links=None)
    own = set()
    for sub in ('channels', 'flagstaff'):
        if os.path.exists(os.path.join(WORKS, f'apex-one-tartane-01m-{sub}', 'work.json')):
            own |= set(map(tuple, export_list(f'apex-one-tartane-01m-{sub}', None)[:, :3].tolist()))
    occ = {tuple(r[:3]) for r in A.tolist()} - own
    hull = {tuple(r[:3]) for r in export_list('apex-one-tartane-01m', None).tolist()}

    hout, htop = {}, {}
    for x, y, z in hull:
        d = abs(y - YC)
        if d > hout.get((x, z), -1):
            hout[(x, z)] = d
        htop[x] = max(htop.get(x, -1), z)

    ax = lambda key, z: float(LY.mast_axis_x(plan, key, z + 0.5, L))
    anchors = {k: {} for k in ('hull', 'channels', 'flagstaff', 'fore', 'main', 'bowsprit', 'deck-main')}

    # ── 1. channels 支索板與 deadeye（fore 3 道 @ x=[259,254,249]、main 4 道 @ x=[157,153,149,145]）──
    COL_CHAN, COL_DEAD = 68, 104
    chan = {}
    ch_cfg = {
        'fore': [259, 254, 249],
        'main': [157, 153, 149, 145],
    }
    for mk, xs_list in ch_cfg.items():
        zc = htop[xs_list[0]] - 2
        for x in range(min(xs_list) - 2, max(xs_list) + 3):
            o = max(hout.get((x, zc - 1), -1), hout.get((x, zc), -1))
            if o < 0:
                continue
            for dy in range(o + 1, o + 3):
                for z in (zc - 1, zc):
                    for y in (YC + dy, YC - dy):
                        if (x, y, z) not in occ:
                            chan[(x, y, z)] = COL_CHAN
        for i, x in enumerate(xs_list, 1):
            o = max(hout.get((x, zc - 1), -1), hout.get((x, zc), -1))
            dyo = o + 2
            for ddx in (-1, 0, 1):
                for z in range(zc + 1, zc + 3):
                    for y in (YC + dyo, YC - dyo):
                        if (x + ddx, y, z) not in occ:
                            chan[(x + ddx, y, z)] = COL_DEAD
            anchors['channels']['deadeye-%s-S-%d' % (mk, i)] = [x, YC + dyo, zc + 2]
            anchors['channels']['deadeye-%s-P-%d' % (mk, i)] = [x, YC - dyo, zc + 2]

    # ── 2. 船尾國旗桿 flagstaff（立於 quarter 艉甲板 x=90, y=96, z=36..68 —— 離舵柄/舵葉與船名牌皆留空間）──
    flagstaff = {}
    for z in range(36, 69):
        pt = (90, YC, z)
        if pt not in occ:
            flagstaff[pt] = 68 if z in (36, 37, 68) else 141
    anchors['flagstaff']['top'] = [90, YC, 68]
    anchors['flagstaff']['bot'] = [90, YC, 50]

    # ── 3. 桅與斜桅上的固定點 ──
    for mk, frac in (('fore', 0.72), ('main', 0.78)):
        m = M[mk]
        A_ = anchors[mk]
        z_hnd = int(round(m['heel'] + frac * (m['truck'] - m['heel'])))
        xh = int(round(ax(mk, z_hnd)))
        for s_, sg in (('S', 1), ('P', -1)):
            A_['hound-' + s_] = [xh, YC + sg * 2, z_hnd + 1]
            # 繩梯上踏點：立於腮木（z_hnd-1..z_hnd）上方 z_hnd+1（頭上全程空）
            A_['rat-head-' + s_] = [xh, YC + sg * 2, z_hnd + 1]
        A_['stay-head'] = [xh + 2, YC, z_hnd + 2]
        zt = int(round(m['calcet']))
        xt = int(round(ax(mk, zt)))
        A_['calcet'] = [xt, YC, zt]
        ztop = int(round(m['truck']))
        xtop = int(round(ax(mk, ztop)))
        A_['truck'] = [xtop, YC, ztop]
        A_['outer-stay'] = [xtop, YC, ztop - 3]
        A_['backstay-S'] = [xh - 1, YC + 2, z_hnd + 1]
        A_['backstay-P'] = [xh - 1, YC - 2, z_hnd + 1]

    # 主甲板繩梯下踏點（過舷牆內側甲板上，腳下實心、頭上開闊）& 主桅千斤索 tack 固定點
    for s_, sg in (('S', 1), ('P', -1)):
        # main shroud center x=151, main deck inside half-width ≈ 21 ⇒ y = YC ± 19, z = 25 (standing on main z=24)
        anchors['deck-main']['rat-foot-main-' + s_] = [151, YC + sg * 19, 25]
        # fore shroud center x=254, main deck at x=254: check z_main(254)=27, standing inside bulwark at y = YC ± 10
        anchors['deck-main']['rat-foot-fore-' + s_] = [254, YC + sg * 10, 28]
    anchors['deck-main']['tack-main'] = [202, YC, int(LY.deck_z(plan, 'main', 202.5)) + 1]
    anchors['deck-main']['mainstay-foot'] = [223, YC, int(LY.deck_z(plan, 'main', 223.5)) + 1]

    # bowsprit 點
    a_b = math.radians(B['angle'])
    u_b = np.array([math.cos(a_b), 0.0, math.sin(a_b)])
    w_b = np.array([-math.sin(a_b), 0.0, math.cos(a_b)])
    Hh = np.array([B['x0'] + 0.5, YC + 0.5, B['z0'] + 0.5])
    Lb = B['len']
    cell = lambda p: [int(math.floor(p[0])), int(math.floor(p[1])), int(math.floor(p[2]))]
    BA = anchors['bowsprit']
    BA['tack-fore'] = cell(Hh + 0.32 * Lb * u_b + 1.5 * w_b)
    BA['inner-stay'] = cell(Hh + 0.52 * Lb * u_b + 1.5 * w_b)
    BA['jib-tack'] = cell(Hh + 0.94 * Lb * u_b + 1.5 * w_b)
    BA['tip'] = cell(Hh + 0.98 * Lb * u_b + 1.0 * w_b)
    BA['bob'] = cell(Hh + 0.62 * Lb * u_b - 1.5 * w_b)
    for s_, sg in (('S', 1), ('P', -1)):
        BA['side-' + s_] = cell(Hh + 0.50 * Lb * u_b + np.array([0.0, sg * 2.0, 0.0]))

    # 船殼點：bobstay 錨於實體艏柱上（⛔ 不錨 deco-船首像！）、bs-shroud、各帆 sheet 繫柱
    anchors['hull']['bobstay'] = [265, YC, 30]
    for s_, sg in (('S', 1), ('P', -1)):
        anchors['hull']['bs-shroud-' + s_] = [258, YC + sg * hout[(258, 35)], 35]
        # main-lateen sheet（x=114 quarter rail z=42）
        anchors['hull']['belay-main-sheet-' + s_] = [114, YC + sg * hout[(114, 42)], 42]
        # fore-lateen sheet（x=218 waist rail z=32）
        z_f = htop[218]
        anchors['hull']['belay-fore-sheet-' + s_] = [218, YC + sg * hout[(218, z_f)], z_f]
        # foc sheet（x=256 bow rail z=35）
        z_j = htop[256]
        anchors['hull']['belay-foc-sheet-' + s_] = [256, YC + sg * hout[(256, z_j)], z_j]

    # ── 4. 繩（靜索＋帆自己的動索）──
    C_STAND, C_RUN, C_RAT = '#2b2620', '#a08458', '#2b2620'
    ropes = []

    def rope(name, fr, to, grp, th, slack=1.0, color=C_STAND, meta=None):
        ropes.append({'name': name, 'from': fr, 'to': to, 'group': grp, 'thickness': th, 'slack': slack, 'color': color, 'meta': meta})

    for mk, xs_list in ch_cfg.items():
        Lk = LINK[mk]
        for s_ in ('S', 'P'):
            for i in range(1, len(xs_list) + 1):
                rope('%s-shroud-%s-%d' % (mk, s_, i),
                     '支索板/deadeye-%s-%s-%d' % (mk, s_, i),
                     '%s/hound-%s' % (Lk, s_),
                     'standing/shrouds', 0.45)

    # 支索 stays 與 斜桅索具
    rope('main-stay', '桅-main/stay-head', '甲板-main/mainstay-foot', 'standing/stays', 0.65, 1.0)
    rope('fore-stay-inner', '桅-fore/stay-head', '桅-bowsprit/inner-stay', 'standing/stays', 0.55, 1.0)
    rope('fore-stay-outer', '桅-fore/outer-stay', '桅-bowsprit/tip', 'standing/stays', 0.45, 1.0)
    rope('bobstay', 'hull/bobstay', '桅-bowsprit/bob', 'standing/bowsprit', 0.50, 1.0)
    for s_ in ('S', 'P'):
        rope('bowsprit-shroud-' + s_, 'hull/bs-shroud-' + s_, '桅-bowsprit/side-' + s_, 'standing/bowsprit', 0.40, 1.0)

    # 橫繩組 ratlines（下桅標 climb=1＋foot＋head，Ship_Rigging §6）
    rsets = []
    for mk, xs_list in ch_cfg.items():
        Lk = LINK[mk]
        for s_ in ('S', 'P'):
            rsets.append({
                'name': '%s-lower-%s' % (mk, s_),
                'rope_a': '%s-shroud-%s-1' % (mk, s_),
                'rope_b': '%s-shroud-%s-%d' % (mk, s_, len(xs_list)),
                'step': 4, 'start': 6, 'stop': 14, 'min_span': 4, 'thickness': 0.25,
                'group': 'ratlines/lower',
                'climb': 1,
                'foot': '甲板-main/rat-foot-%s-%s' % (mk, s_),
                'head': '%s/rat-head-%s' % (Lk, s_),
            })

    # ── 5. 帆（main-lateen [set=1], fore-lateen [set=2], foc [set=3]）與 旗（ensign=tuscany, pennant）──
    sails = []
    # main-lateen (mestre)
    sails.append({
        'name': 'main-lateen',
        'corners': ['model:桅-main/yard-main-lateen/fore', 'model:桅-main/yard-main-lateen/peak', '114.50,96.50,47.50'],
        'corner_names': ['tack', 'head', 'clew'],
        'bind': [0], 'free': ['clew'],
        'fullness': 1.06, 'color': '#f2ead8',
        'meta': {'kind': 'sail', 'mast': 'main', 'sail': 'gaff', 'set': 1},
    })
    rope('main-lateen.tack', 'sail:main-lateen/tack', '甲板-main/tack-main', 'running/tacks', 0.40, 1.02, C_RUN, {'kind': 'tack', 'sail': 'main-lateen'})
    for s_ in ('S', 'P'):
        rope('main-lateen.sheet-' + s_, 'sail:main-lateen/clew', 'hull/belay-main-sheet-' + s_, 'running/sheets', 0.40, 1.03, C_RUN, {'kind': 'sheet', 'sail': 'main-lateen'})
    rope('main-lateen.halyard', '桅-main/calcet', 'model:桅-main/yard-main-lateen/sling', 'running/halyards', 0.45, 1.0, C_RUN, {'kind': 'halyard', 'sail': 'main-lateen'})

    # fore-lateen (trinquet)
    sails.append({
        'name': 'fore-lateen',
        'corners': ['model:桅-fore/yard-fore-lateen/fore', 'model:桅-fore/yard-fore-lateen/peak', '224.50,96.50,38.50'],
        'corner_names': ['tack', 'head', 'clew'],
        'bind': [0], 'free': ['clew'],
        'fullness': 1.06, 'color': '#f2ead8',
        'meta': {'kind': 'sail', 'mast': 'fore', 'sail': 'gaff', 'set': 2},
    })
    rope('fore-lateen.tack', 'sail:fore-lateen/tack', '桅-bowsprit/tack-fore', 'running/tacks', 0.35, 1.02, C_RUN, {'kind': 'tack', 'sail': 'fore-lateen'})
    for s_ in ('S', 'P'):
        rope('fore-lateen.sheet-' + s_, 'sail:fore-lateen/clew', 'hull/belay-fore-sheet-' + s_, 'running/sheets', 0.35, 1.03, C_RUN, {'kind': 'sheet', 'sail': 'fore-lateen'})
    rope('fore-lateen.halyard', '桅-fore/calcet', 'model:桅-fore/yard-fore-lateen/sling', 'running/halyards', 0.40, 1.0, C_RUN, {'kind': 'halyard', 'sail': 'fore-lateen'})

    # foc (bowsprit staysail along taut outer stay)
    sails.append({
        'name': 'foc',
        'corners': ['291.50,96.50,111.50', '桅-bowsprit/jib-tack', '295.50,96.50,48.50'],
        'corner_names': ['head', 'tack', 'clew'],
        'bind': [0], 'free': ['clew'],
        'fullness': 1.05, 'color': '#f2ead8',
        'meta': {'kind': 'sail', 'mast': 'bowsprit', 'sail': 'staysail', 'set': 3},
    })
    rope('foc.halyard', '桅-fore/outer-stay', 'sail:foc/head', 'running/halyards', 0.30, 1.0, C_RUN, {'kind': 'halyard', 'sail': 'foc'})
    for s_ in ('S', 'P'):
        rope('foc.sheet-' + s_, 'sail:foc/clew', 'hull/belay-foc-sheet-' + s_, 'running/sheets', 0.30, 1.03, C_RUN, {'kind': 'sheet', 'sail': 'foc'})

    # 旗：ensign（托斯卡納利佛諾紅八角十字白旗，掛船尾旗桿 旗桿/top..旗桿/bot）＋ pennant（主桅頂）
    os.makedirs(os.path.join(design, 'textures'), exist_ok=True)
    tuscany_ensign_png(os.path.join(design, 'textures', 'ensign.png'), 24, 14)
    sails.append({
        'name': 'ensign',
        'corners': ['旗桿/top', '66.50,96.50,68.50', '66.50,96.50,50.50', '旗桿/bot'],
        'corner_names': ['top_h', 'top_f', 'bot_f', 'bot_h'],
        'bind': [3], 'free': ['top_f', 'bot_f'],
        'fullness': 1.04, 'color': '#ffffff', 'texture': 'textures/ensign.png',
        'meta': {'kind': 'flag', 'flag': 'ensign', 'nation': 'tuscany'},
    })
    tz_m = int(round(M['main']['truck']))
    tx_m = int(round(ax('main', tz_m)))
    sails.append({
        'name': 'pennant',
        'corners': ['%d.50,%d.50,%d.50' % (tx_m, YC, tz_m - 1), '%d.50,%d.50,%d.50' % (tx_m - 30, YC, tz_m - 2), '%d.50,%d.50,%d.50' % (tx_m, YC, tz_m - 5)],
        'corner_names': ['top_h', 'tip', 'bot_h'],
        'bind': [2], 'free': ['tip'],
        'fullness': 1.04, 'color': '#b81a17',
        'meta': {'kind': 'flag', 'flag': 'pennant', 'mast': 'main'},
    })

    metas = [['sail', s['name'], s['meta']] for s in sails] + [['rope', r['name'], r['meta']] for r in ropes if r['meta']]
    if probe:
        nm = probe[0].split('=')[1]
        metas = [m for m in metas if not (m[0] == 'rope' and m[1] == nm)]

    need = [r['name'] for r in ropes if r['name'].split('.')[0] in {s['name'] for s in sails} and '.' in r['name']]
    have = {m[1] for m in metas if m[0] == 'rope'}

    # 檢查固定點是否穿進不相干的實心或靜索穿過船殼
    def wpt(spec):
        fr, nm = spec.split('/', 1)
        part = {'支索板': 'channels', '旗桿': 'flagstaff', 'hull': 'hull', '甲板-main': 'deck-main',
                '桅-fore': 'fore', '桅-main': 'main', '桅-bowsprit': 'bowsprit'}[fr]
        return np.array(anchors[part][nm], float) + 0.5

    solid = set(occ) | set(chan) | set(flagstaff)
    thru = {}
    for r in ropes:
        if r['from'].startswith(('sail:', 'model:')) or r['to'].startswith(('sail:', 'model:')):
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

    R = {
        'channels': {'cells': len(chan), 'mirror_diff': sum(1 for (x, y, z), c in chan.items() if chan.get((x, 2 * YC - y, z)) != c)},
        'flagstaff': {'cells': len(flagstaff)},
        'anchors': {k: len(v) for k, v in anchors.items()},
        'ropes': len(ropes), 'ratline_sets': len(rsets), 'sails': len(sails),
        'sail_ropes_without_meta': sorted(set(need) - have),
        'dup_rope_names': len(ropes) - len({r['name'] for r in ropes}),
        'ropes_through_solid': thru,
    }
    if probe:
        print(json.dumps({'probe': probe[0], 'sail_ropes_without_meta': R['sail_ropes_without_meta']}, ensure_ascii=False))
        return

    os.makedirs(os.path.join(design, 'masks', 'rigging'), exist_ok=True)
    for fn, dct, hdr in (
        ('channels.vox.txt', chan, '# 塔爾塔納 兩舷支索板＋deadeye (at 0,0,0)\n'),
        ('flagstaff.vox.txt', flagstaff, '# 塔爾塔納 船尾國旗桿 (at 0,0,0)\n'),
    ):
        p = os.path.join(design, 'masks', 'rigging', fn)
        with open(p, 'w', encoding='utf-8', newline='\n') as fh:
            fh.write(hdr)
            for (x, y, z), c in sorted(dct.items()):
                fh.write('%d,%d,%d,%d\n' % (x, y, z, c))

    works = {
        'hull': 'apex-one-tartane-01m',
        'channels': 'apex-one-tartane-01m-channels',
        'flagstaff': 'apex-one-tartane-01m-flagstaff',
        'fore': 'apex-one-tartane-01m-mast-fore',
        'main': 'apex-one-tartane-01m-mast-main',
        'bowsprit': 'apex-one-tartane-01m-bowsprit',
        'deck-main': 'apex-one-tartane-01m-deck-main',
    }
    out = {'anchors': anchors, 'anchor_works': works, 'ropes': ropes, 'ratline_sets': rsets,
           'sails': sails, 'meta': metas, 'wind': [4.5, -1.5, 0.0], 'sail_seconds': 3}
    with open(os.path.join(design, 'rigging_plan.json'), 'w', encoding='utf-8', newline='\n') as fh:
        json.dump(out, fh, ensure_ascii=False, indent=1, default=lambda o: o.item())
    with open(os.path.join(design, 'verify_rigging.json'), 'w', encoding='utf-8', newline='\n') as fh:
        json.dump(R, fh, ensure_ascii=False, indent=1, default=lambda o: o.item())
    print(json.dumps(R, ensure_ascii=False, default=lambda o: o.item()))


if __name__ == '__main__':
    main()
