# 蠍子號 新圖紙 06（TASK-0023 步驟 8）：索具、帆、旗 ⇒ rig_plan.json（固定點、繩、帆、meta）、rig_meta.tsv、verify_rigging.json、sheet06_rigging_v1.png
#   出處：海鷗號 claude-felucca-01m/design/draft_rigging.py（它出自杉心號 basecamp-piragua-01m 的 rig_plan 格式：拉丁帆 tack ＝ 帆桁 fore、clew 自由、bind 邊 0；
#         帆自己的繩標 kind=sheet／tack＋sail；長旗 kind=flag flag=pennant；靜索只拉在帆的另一舷）——改成一根桅一面帆。
#   改的地方：帆的 head 不在帆桁尖，照步驟 3 的桅帆表（layout.rig.sail：前緣 ＝ 帆桁 × luff_frac、後緣／帆腳照前緣的比例）取最近的 jackstay；
#            clew 照三邊解出來（在帆桁那一舷的鉛直面上、帆桁下面）；繩腳都落在兩張划手座之間的舷頂；tack 往下綁船首低平台。
#   用法：python -I -X utf8 draft_rigging.py [--probe=clew_z=-20] [--probe=shroud_side=-1]
#   · 長旗掛在帆桁尖（v1 桅頂，離帆桁 0.98 格）。
#   · 讀前面每一步的設計清單與 yards_lateen.json／yards_placement.json；不讀作品 ⇒ 落格之後重跑一樣。
#   · 讀數：每個固定點在它那件作品的實心格上；繩兩端的世界座標；平面帆（還沒模擬的三角形）離船的格最近幾格；繩有沒有穿過帆；帆裝三段（Ship_Rigging §9.1）。
#     掛好之後的帆布與繩的讀數在落格之後由 CLI 量（work sub=sails／ropes、ropecheck）與 tools/check_sails_sim.py。
import sys, os, json, math, hashlib
import numpy as np
from scipy.spatial import cKDTree
from PIL import Image, ImageDraw, ImageFont

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import lines as HL

sys.stdout.reconfigure(encoding='utf-8')
TAR, HEMP, SAIL, RED = '#2b2620', '#a08458', '#f2ead8', '#7a1a14'


def V(d):
    return d['v'] if isinstance(d, dict) and 'v' in d else d


def load(fn):
    a = np.loadtxt(os.path.join(HERE, fn), delimiter=',', comments='#', dtype=np.int32, ndmin=2)
    return {(int(x), int(y), int(z)): int(c) for x, y, z, c in a}


def main():
    probe = dict(a[len('--probe='):].split('=') for a in sys.argv[1:] if a.startswith('--probe='))
    plan = HL.load_plan(HERE)
    YC = int(plan['space']['yc'])
    RG = {k: V(v) for k, v in plan['rigging'].items() if k != 'src'}
    RIG = V(plan['layout']['rig'])
    BE = V(plan['layout']['benches'])
    hull = load('masks/hull/hull_01.vox.txt')
    hull.update(load('masks/step6/hull_paint.vox.txt'))
    hole = load('masks/masts/deck_hole.vox.txt')
    deck = {k: c for k, c in load('masks/decks/deck_main.vox.txt').items() if k not in hole}
    bow = load('masks/decks/bow.vox.txt')
    mast = load('masks/masts/main.vox.txt')
    others = {}
    for fn in ('masks/deco/spur.vox.txt', 'masks/deco/poop.vox.txt', 'masks/deco/awning.vox.txt'):
        others.update(load(fn))
    LAT = json.load(open(os.path.join(HERE, 'yards_lateen.json'), encoding='utf-8'))['main']
    PL = json.load(open(os.path.join(HERE, 'yards_placement.json'), encoding='utf-8'))[0]
    WORKS = {'hull': (hull, '船殼'), 'bow': (bow, '甲板-main/船首平台'), 'mast-main': (mast, '主桅')}
    YARD = 'model:主桅/%s' % PL['name']

    def yard_world(an):
        a = LAT['anchors'][an]
        return [a[i] + 0.5 - PL['pivot'][i] + PL['at'][i] for i in range(3)]

    benches = [int(round(BE['first_x'] + BE['pitch'] * i)) for i in range(int(BE['n']))]
    seat_x = {x for b in benches for x in range(b - BE['w'] // 2, b - BE['w'] // 2 + BE['w'])}

    def between_benches(x):
        """離 x 最近、兩張座正中間的那一欄（繩腳不落在座底下）。"""
        mids = [int(math.floor((a + b) / 2)) for a, b in zip(benches, benches[1:])]
        return min(mids, key=lambda m: (abs(m - x), m))

    def after_bench(x):
        """離 x 最近、緊接在一張座後面（船頭那一側）的那一欄：往船頭有 7 格沒有座與腳踏（腳踏在下一張座往後 5 格）⇒ 往前上拉的繩貼著舷頂起來不碰東西。"""
        return min((b - BE['w'] // 2 + BE['w'] for b in benches), key=lambda m: (abs(m - x), m))

    def rail_cell(x, side):
        """(x) 那一欄舷頂最外一格（side +1 右舷、−1 左舷）。"""
        ys = [k for k in hull if k[0] == x and (k[1] - YC) * side > 2]
        zt = max(k[2] for k in ys)
        y = max((k[1] for k in ys if k[2] == zt), key=lambda v: (v - YC) * side)
        return (x, y, zt)

    def mast_face(z, side):
        cs = [k for k in mast if k[2] == z]
        y = max((k[1] for k in cs), key=lambda v: (v - YC) * side)
        xs = sorted(k[0] for k in cs if k[1] == y)
        return (xs[len(xs) // 2], y, z)

    anchors, ropes, sails = [], [], []

    def anchor(work, name, at):
        cells, link = WORKS[work]
        assert tuple(at) in cells, (work, name, at)
        anchors.append({'work': work, 'name': name, 'at': list(at)})
        return '%s/%s' % (link, name)

    def rope(name, a, b, slack, th, color, group, meta=None):
        ropes.append({'name': name, 'from': a, 'to': b, 'slack': slack, 'thickness': th, 'color': color, 'group': group, 'meta': meta or {}})

    # ── 帆：tack ＝ 帆桁 fore、head ＝ 前緣長那一點最近的 jackstay、clew 照三邊解（帆桁那一舷的鉛直面、帆桁下面）──
    sv = RIG['masts']['main']['sail']
    tack_w = yard_world('fore')
    Lc = LAT['len_m'] * 10
    want = Lc * sv['luff_frac']
    js = {n: (int(n.split('-')[1]) * 8.0) for n in LAT['anchors'] if n.startswith('jackstay-')}
    head_an = min(js, key=lambda n: (abs(js[n] + 1.0 - want), n))   # fore 在 s＝1；jackstay-k 在 s＝8k
    head_w = yard_world(head_an)
    luff = math.dist((tack_w[0], tack_w[2]), (head_w[0], head_w[2]))
    leech, foot = luff * sv['leech_ratio'], luff * sv['foot_ratio']
    a_t = math.acos((foot ** 2 + luff ** 2 - leech ** 2) / (2 * foot * luff))
    ang_th = math.atan2(head_w[2] - tack_w[2], head_w[0] - tack_w[0])
    ang = ang_th + a_t                                      # 往帆桁下面那一側轉（tack 在船頭、head 在後上 ⇒ 加角度往後下）
    clew = [tack_w[0] + foot * math.cos(ang), PL['at'][1], tack_w[2] + foot * math.sin(ang) + float(probe.get('clew_z', 0))]
    sails.append({'name': 'main-lateen', 'corners': ['%s/fore' % YARD, '%s/%s' % (YARD, head_an), '%.1f,%.1f,%.1f' % tuple(clew)],
                  'corner_names': ['tack', 'head', 'clew'], 'bind': [0], 'free': ['clew'], 'color': SAIL,
                  'meta': {'kind': 'sail', 'mast': 'main', 'sail': 'gaff', 'set': '1'}})
    # ── 靜索：只拉在帆的另一舷（帆桁掛在左舷 ⇒ 靜索在右舷）；上端 hound 在桅那一面、calcet 底下；下端舷頂最外一格、兩張座中間 ──
    side = int(probe.get('shroud_side', RG['shrouds']['side']))
    sd = 'S' if side > 0 else 'P'
    top_z = max(k[2] for k in mast) + 1
    h = anchor('mast-main', 'hound-' + sd, mast_face(top_z - RG['shrouds']['hound_below_top'], side))
    for i, x in enumerate(RG['shrouds']['feet_x'], 1):
        xb = between_benches(x)
        rope('main-shroud-%s%d' % (sd, i), h, anchor('hull', 'shroud-main-%s%d' % (sd, i), rail_cell(xb, side)), 1.0, 0.5, TAR, 'standing/shrouds', {'kind': 'shroud'})
    # ── sheet：clew 往後下綁兩舷舷頂（兩張座中間）；tack：帆桁 fore 往下綁船首低平台的板 ──
    xs = after_bench(int(round(clew[0])) - RG['sheet_aft'])
    for s_, nm in ((-1, 'P'), (1, 'S')):
        rope('main-lateen.sheet-%s' % nm, 'sail:main-lateen/clew', anchor('hull', 'belay-main-sheet-%s' % nm, rail_cell(xs, s_)), 1.03, 0.4, HEMP,
             'running/sheets', {'kind': 'sheet', 'sail': 'main-lateen'})
    # tack 落點（v2）：v1 落在帆桁 fore 正下方 (335,116,25)，步驟 9 的 8l（中線、寬 0.75 m）從 x 328 起 ⇒ tack 離砲 1.0 格；
    #   改成 rigging.tack：8l 左舷、離 8l 的障礙框（外擴 1 格）2 格以上、離左舷 pierrier 的掃掠圈（半徑約 9.3 格）3 格以上
    TK = RG['tack']
    tx, ty = int(TK['x']), YC + int(TK['dy'])
    tz = max(k[2] for k in bow if k[0] == tx and k[1] == ty and k[2] < 27)        # 平台板最上一格（胸牆不算）
    rope('main-lateen.tack', '%s/fore' % YARD, anchor('bow', 'tack-main', (tx, ty, tz)), 1.0, 0.5, HEMP, 'running/tacks', {'kind': 'tack', 'sail': 'main-lateen'})
    # ── 長旗：帆桁尖（penna）——hoist 沿帆桁最後一段（peak → 往前 1 m 那一個 jackstay）、fly 往下風（預設風往 +x）；紅、不是國旗 ⇒ 不寫 nation。
    #    v1 掛桅頂：桅頂正下方 8 格就是帆桁吊點，長旗垂下來離帆桁 0.98 格（往前飄碰到往前下的那一段、往後飄碰到往後上的那一段）⇒ 改帆桁尖：尖的正下方是空的 ──
    PN = RG['pennant']
    pk = yard_world('peak')
    hoist = min((n for n in js if js[n] <= Lc - 1 - PN['hoist_cells']), key=lambda n: (-js[n], n))
    sails.append({'name': 'pennant', 'corners': ['%s/peak' % YARD, '%.1f,%.1f,%.1f' % (pk[0] + PN['len_m'] * 10, pk[1], pk[2] - 0.5), '%s/%s' % (YARD, hoist)],
                  'corner_names': ['head', 'fly', 'foot'], 'bind': [2], 'free': [1], 'color': RED, 'fullness': 1.04,
                  'meta': {'kind': 'flag', 'flag': 'pennant'}})
    # ↑ v2 拿掉 mast：遊戲（77_colours.js teamFlagsSetup，TASK-1208）看到作品自己有 mast=main 的旗 ⇒ 船掛國籍時主桅頂那面國旗收起來，
    #   可是這面長旗沒有 nation、沒有貼圖 uv、換不成國旗 ⇒ 整艘船不掛國旗（verifier8）；長旗掛在帆桁尖、不在桅頂，本來就不該佔主桅的旗位

    # ── 讀數（平面的帆：三角形；掛好之後的布另外量）──
    yard_cells = set()
    for (x, y, z) in load('masks/yards/lateen-main.vox.txt'):
        yard_cells.add((int(round(x + 0.5 - PL['pivot'][0] + PL['at'][0] - 0.5)), int(round(y + 0.5 - PL['pivot'][1] + PL['at'][1] - 0.5)),
                        int(round(z + 0.5 - PL['pivot'][2] + PL['at'][2] - 0.5))))
    ship = set(hull) | set(deck) | set(bow) | set(mast) | set(others)
    tree = cKDTree(np.array(sorted(ship), float) + 0.5)
    R = {'probe': probe or None, 'anchors': len(anchors), 'ropes': len(ropes), 'sails': len(sails), 'head_anchor': head_an,
         'sail_sides_m': {'luff': round(luff * 0.1, 2), 'leech': round(leech * 0.1, 2), 'foot': round(foot * 0.1, 2)},
         'sail_sides_design_m': {'luff': round(LAT['len_m'] * sv['luff_frac'], 2), 'leech': round(LAT['len_m'] * sv['luff_frac'] * sv['leech_ratio'], 2),
                                 'foot': round(LAT['len_m'] * sv['luff_frac'] * sv['foot_ratio'], 2)},
         'clew_above_deck_m': round((clew[2] - 20) * 0.1, 2), 'sail_plane': {}, 'rope_ends': {}, 'rope_feet_on_bench': []}
    pts_w = {}
    for s in sails:
        P = []
        for c in s['corners']:
            P.append(yard_world(c.rsplit('/', 1)[1]) if c.startswith('model:') else [float(v) for v in c.split(',')])
        pts_w[s['name']] = P
        A, B, Cc = (np.array(p) for p in P)
        samp = np.array([A + u * (B - A) + v * (Cc - A) for u in np.linspace(0, 1, 80) for v in np.linspace(0, 1, 80) if u + v <= 1])
        d, _ = tree.query(samp)
        inside_yard = sum(1 for p in samp if tuple(int(np.floor(q)) for q in p) in yard_cells)
        R['sail_plane'][s['name']] = {'corners': [[round(v, 1) for v in p] for p in P], 'min_dist_to_ship_cells': round(float(d.min()), 2),
                                      'samples_in_yard_cells': inside_yard, 'area_m2': round(0.5 * float(np.linalg.norm(np.cross(B - A, Cc - A))) * 0.01, 2)}
    table = {}
    for k, nm in ((1, '收帆'), (2, '戰鬥帆'), (3, '滿帆')):
        table[nm] = [s['name'] for s in sails if s['meta']['kind'] == 'sail' and int(s['meta']['set']) <= k]
    R['sail_sets'] = table

    def endpoint(e):
        if e.startswith('model:'):
            return yard_world(e.rsplit('/', 1)[1])
        if e.startswith('sail:'):
            nm, cn = e[5:].split('/')
            s = next(s for s in sails if s['name'] == nm)
            return pts_w[nm][s['corner_names'].index(cn)]
        link, an = e.rsplit('/', 1)
        a = next(a for a in anchors if WORKS[a['work']][1] == link and a['name'] == an)
        return [v + 0.5 for v in a['at']]

    for r in ropes:
        a, b = endpoint(r['from']), endpoint(r['to'])
        R['rope_ends'][r['name']] = {'from': [round(v, 1) for v in a], 'to': [round(v, 1) for v in b], 'len_m': round(math.dist(a, b) * 0.1, 2)}
        # 直線（拉直、還沒下垂）穿過幾格實心（兩端那一格不算）
        pa, pb = np.array(a), np.array(b)
        n = int(math.dist(a, b) * 4) + 2
        hit = {tuple(int(np.floor(q)) for q in pa + t * (pb - pa)) for t in np.linspace(0, 1, n)}
        hit -= {tuple(int(np.floor(q)) for q in pa), tuple(int(np.floor(q)) for q in pb)}
        own = set()                                         # 繩從它自己綁的那一件出來（桅面往下、帆桁 fore 往下）那幾格不算：只算端點 5 格以內、端點那一件的格
        for e, p in ((r['from'], a), (r['to'], b)):
            part = yard_cells if e.startswith('model:') else (set(WORKS[next(w for w in WORKS if e.startswith(WORKS[w][1] + '/'))][0]) if not e.startswith('sail:') else set())
            own |= {k for k in hit if k in part and math.dist([v + 0.5 for v in k], p) <= 5}
        R['rope_ends'][r['name']]['straight_line_solid_cells'] = len((hit & (ship | yard_cells)) - own)
        R['rope_ends'][r['name']]['own_part_cells_near_end'] = len(own)
    for an in anchors:
        if an['work'] == 'hull' and an['at'][0] in seat_x:
            R['rope_feet_on_bench'].append(an['name'])

    def tri_dist(p, A, B, Cc):
        A, B, Cc, p = (np.array(v) for v in (A, B, Cc, p))
        n = np.cross(B - A, Cc - A)
        n = n / np.linalg.norm(n)
        q = p - np.dot(p - A, n) * n
        v0, v1, v2 = Cc - A, B - A, q - A
        d00, d01, d11, d20, d21 = v0 @ v0, v0 @ v1, v1 @ v1, v2 @ v0, v2 @ v1
        den = d00 * d11 - d01 * d01
        u = (d11 * d20 - d01 * d21) / den
        v = (d00 * d21 - d01 * d20) / den
        return abs(float(np.dot(p - A, n))) if (u >= 0 and v >= 0 and u + v <= 1) else None

    cross = {}
    for r in ropes:
        a, b = np.array(endpoint(r['from'])), np.array(endpoint(r['to']))
        for s in sails:
            if s['meta']['kind'] != 'sail' or r['meta'].get('sail') == s['name']:
                continue
            ds = [tri_dist(a + t * (b - a), *pts_w[s['name']]) for t in np.linspace(0.02, 0.98, 100)]
            ds = [d for d in ds if d is not None]
            if ds and min(ds) < 1.0:
                cross.setdefault(r['name'], []).append(s['name'])
    R['ropes_through_flat_sail'] = cross
    R['problems'] = (len(cross) + len(R['rope_feet_on_bench']) + sum(1 for s in sails if s['meta']['kind'] == 'sail' and R['sail_plane'][s['name']]['min_dist_to_ship_cells'] < 1.0)
                     + sum(1 for v in R['rope_ends'].values() if v['straight_line_solid_cells']) + (not table['收帆']) + (not table['戰鬥帆']))
    if probe:
        print(json.dumps({k: R[k] for k in ('probe', 'problems', 'sail_plane', 'ropes_through_flat_sail', 'clew_above_deck_m')}
                         | {'rope_hits': {k: v['straight_line_solid_cells'] for k, v in R['rope_ends'].items()}}, ensure_ascii=False))
        return
    with open(os.path.join(HERE, 'rig_plan.json'), 'w', encoding='utf-8', newline='\n') as f:
        json.dump({'anchors': anchors, 'ropes': ropes, 'sails': sails}, f, ensure_ascii=False, indent=1)
    rows_ = [('sail', s['name'], s['meta']) for s in sails] + [('rope', r['name'], r['meta']) for r in ropes if r.get('meta')]
    with open(os.path.join(HERE, 'rig_meta.tsv'), 'w', encoding='utf-8', newline='\n') as f:
        f.write(''.join('%s\t%s\t%s\n' % (a, b, json.dumps(c, ensure_ascii=False, separators=(',', ':'))) for a, b, c in rows_))
    R['sha256'] = {f: hashlib.sha256(open(os.path.join(HERE, f), 'rb').read()).hexdigest() for f in ('rig_plan.json', 'rig_meta.tsv')}
    with open(os.path.join(HERE, 'verify_rigging.json'), 'w', encoding='utf-8', newline='\n') as f:
        json.dump(R, f, ensure_ascii=False, indent=1)
    # 圖紙 06：右舷側面（船＋桅＋帆桁＋帆的三角形＋繩的直線）
    AX, AY, AZ = [int(v) for v in plan['space']['assembly']]
    s_ = 3
    img = Image.new('RGB', (AX * s_ + 80, AZ * s_ + 80), (246, 242, 230))
    d = ImageDraw.Draw(img)
    f = ImageFont.load_default()
    d.text((30, 10), '%s - new sheet 06: rigging (flat sail before simulation, straight ropes). main-lateen set 1 (luff %.1f / leech %.1f / foot %.1f m), pennant, %d shrouds %s, sheets P/S, tack to bow platform'
           % (plan['title_en'], luff * 0.1, leech * 0.1, foot * 0.1, len(RG['shrouds']['feet_x']), sd), fill=(20, 20, 40), font=f)
    oy = 40 + AZ * s_

    def Pt(x, z):
        return (40 + x * s_, oy - z * s_)
    for (x, y, z) in sorted(ship | yard_cells):
        if y >= YC - 5:
            d.rectangle([40 + x * s_, oy - (z + 1) * s_, 40 + x * s_ + s_ - 1, oy - z * s_ - 1], fill=(170, 150, 120))
    for s in sails:
        d.polygon([Pt(p[0], p[2]) for p in pts_w[s['name']]], outline=(160, 30, 30) if s['meta']['kind'] == 'flag' else (60, 60, 160))
    for r in ropes:
        e = R['rope_ends'][r['name']]
        d.line([Pt(e['from'][0], e['from'][2]), Pt(e['to'][0], e['to'][2])], fill=(90, 70, 40))
    for x in range(0, AX + 1, 20):
        d.text((40 + x * s_ - 6, oy + 6), str(x), fill=(80, 80, 80), font=f)
    img.save(os.path.join(HERE, 'sheet06_rigging_v1.png'))
    print(json.dumps({k: v for k, v in R.items()}, ensure_ascii=False))


if __name__ == '__main__':
    main()
