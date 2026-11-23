# 海鷗號 新圖紙 06（TASK-0024 步驟 8）：索具、帆、旗 ⇒ rig_plan.json（固定點、繩、帆、meta）、rig_meta.tsv、verify_rigging.json、sheet06_rigging_v1.png
#   出處：杉心號 basecamp-piragua-01m/design/draft_rig.py 的 rig_plan 格式（拉丁帆：tack ＝ 帆桁 fore、head ＝ peak、clew 自由、bind 邊 0；
#         帆自己的繩標 kind=sheet／tack＋sail；長旗 kind=flag flag=pennant），改成兩桅兩帆；固定點一律在實際的格子上（Ship_Rigging §6）。
#   用法：python -I -X utf8 draft_rigging.py [--probe=clew_main_z=-20]
#   · 讀前面每一步的設計清單（船殼、甲板、桅、桿）與 yards_lateen.json／yards_placement.json；不讀作品 ⇒ 落格之後重跑一樣。
#   · 讀數：每個固定點在它那件作品的實心格上；繩兩端的世界座標；平面帆（還沒模擬的三角形）離船的格最近幾格、有沒有穿過桅；
#     帆裝三段（Ship_Rigging §9.1）。掛好之後的帆布與繩的讀數在落格之後由 CLI 量（work sub=sails／ropes、ropecheck）。
import sys, os, json, math, hashlib
import numpy as np
from scipy.spatial import cKDTree
from PIL import Image, ImageDraw, ImageFont

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import lines as HL
import rig

sys.stdout.reconfigure(encoding='utf-8')
YC = 80
TAR, HEMP, SAIL = '#2b2620', '#a08458', '#f2ead8'


def load(fn):
    a = np.loadtxt(os.path.join(HERE, fn), delimiter=',', comments='#', dtype=np.int32, ndmin=2)
    return {(int(x), int(y), int(z)): int(c) for x, y, z, c in a}


def main():
    probe = dict(a[len('--probe='):].split('=') for a in sys.argv[1:] if a.startswith('--probe='))
    plan = HL.load_plan(HERE)
    hull = load('masks/hull/hull_01.vox.txt')
    deck = load('masks/decks/deck_main.vox.txt')
    mm = load('masks/masts/main.vox.txt')
    mf = load('masks/masts/fore.vox.txt')
    ts = load('masks/masts/tack_spar.vox.txt')
    LAT = json.load(open(os.path.join(HERE, 'yards_lateen.json'), encoding='utf-8'))
    PL = {p['mast']: p for p in json.load(open(os.path.join(HERE, 'yards_placement.json'), encoding='utf-8'))}
    WORKS = {'hull': (hull, '船殼'), 'deck': (deck, '甲板-main'), 'mast-main': (mm, '主桅'), 'mast-fore': (mf, '前桅'), 'tack-spar': (ts, '船頭桿')}

    def yard_world(key, an):
        p = PL[key]
        a = LAT[key]['anchors'][an]
        return [a[i] + 0.5 - p['pivot'][i] + p['at'][i] for i in range(3)]

    def rail_cell(x, side):
        """(x) 那一欄舷頂最外一格（side +1 右舷、−1 左舷）。"""
        ys = [k for k in hull if k[0] == x and (k[1] - YC) * side > 2]
        zt = max(k[2] for k in ys)
        y = max((k[1] for k in ys if k[2] == zt), key=lambda v: (v - YC) * side)
        return (x, y, zt)

    def mast_face(cells, z, side):
        cs = [k for k in cells if k[2] == z]
        y = max((k[1] for k in cs), key=lambda v: (v - YC) * side)
        xs = sorted(k[0] for k in cs if k[1] == y)
        return (xs[len(xs) // 2], y, z)

    anchors = []

    def anchor(work, name, at):
        cells, link = WORKS[work]
        assert tuple(at) in cells, (work, name, at)
        anchors.append({'work': work, 'name': name, 'at': list(at)})
        return '%s/%s' % (link, name)

    ropes, sails = [], []

    def rope(name, a, b, slack, th, color, group, meta=None):
        ropes.append({'name': name, 'from': a, 'to': b, 'slack': slack, 'thickness': th, 'color': color, 'group': group, 'meta': meta or {}})

    # ── 靜索：每根桅 2 條，只拉在「帆的另一舷」（主帆在主桅左舷 ⇒ 主桅靜索在右舷；前帆在前桅右舷 ⇒ 前桅靜索在左舷）——
    #    三角帆船帆那一舷的靜索會穿過帆，實船是把那一舷的鬆掉、拉另一舷（設計決定；v1 兩舷都拉，平面帆讀數抓到三條穿過帆）。
    #    上端 hound 在桅的那一面、下端在舷頂最外一格 ──
    rows = rig.mast_rows(plan)
    hz = {'main': rows['main']['top_z'] - 14, 'fore': rows['fore']['top_z'] - 12}
    # 主桅 v1 x 76／88：步驟 13 的槳栓立在 x 76 的舷頂上 ⇒ 靜索會從槳栓穿出來 ⇒ 78／90
    for key, cells, side, sd, xs in (('main', mm, 1, 'S', (78, 90)), ('fore', mf, 1, 'S', (126, 132))):
        h = anchor('mast-' + key, 'hound-' + sd, mast_face(cells, hz[key], side))
        for i, x in enumerate(xs, 1):
            rope('%s-shroud-%s%d' % (key, sd, i), h, anchor('hull', 'shroud-%s-%s%d' % (key, sd, i), rail_cell(x, side)), 1.0, 0.4, TAR, 'standing/shrouds', {'kind': 'shroud'})
    # ── 帆：tack ＝ 帆桁 fore、head ＝ peak、clew 自由（帆腳往後下），bind 邊 0（沿帆桁）──
    clew = {'main': [30.5, PL['main']['at'][1], 25.0 + float(probe.get('clew_main_z', 0))],
            'fore': [140.5, PL['fore']['at'][1], 35.0]}
    for key, link, setv in (('main', '主桅', '1'), ('fore', '前桅', '3')):
        nm = '%s-lateen' % key
        sails.append({'name': nm, 'corners': ['model:%s/yard-%s-lateen/fore' % (link, key), 'model:%s/yard-%s-lateen/peak' % (link, key),
                                              '%.1f,%.1f,%.1f' % tuple(clew[key])],
                      'corner_names': ['tack', 'head', 'clew'], 'bind': [0], 'free': ['clew'], 'color': SAIL,
                      'meta': {'kind': 'sail', 'mast': key, 'sail': 'gaff', 'set': setv}})
        bx = {'main': 26, 'fore': 136}[key]
        for side, sd in ((-1, 'P'), (1, 'S')):
            rope('%s.sheet-%s' % (nm, sd), 'sail:%s/clew' % nm, anchor('hull', 'belay-%s-sheet-%s' % (key, sd), rail_cell(bx, side)), 1.03, 0.35, HEMP,
                 'running/sheets', {'kind': 'sheet', 'sail': nm})
    # tack：主帆往下綁船頭平台、前帆綁船頭桿尖
    tm = anchor('deck', 'tack-main', (128, 77, 9))
    rope('main-lateen.tack', 'model:主桅/yard-main-lateen/fore', tm, 1.0, 0.4, HEMP, 'running/tacks', {'kind': 'tack', 'sail': 'main-lateen'})
    tip = max(ts, key=lambda k: (k[0], -abs(k[1] - (YC + 2)), -k[2]))
    tf = anchor('tack-spar', 'tack-fore', tip)
    rope('fore-lateen.tack', 'model:前桅/yard-fore-lateen/fore', tf, 1.0, 0.4, HEMP, 'running/tacks', {'kind': 'tack', 'sail': 'fore-lateen'})
    # ── 長旗：主桅頂，紅（設計決定：不是國旗 ⇒ 不寫 nation）──
    top = rows['main']['top_z']
    sails.append({'name': 'pennant', 'corners': ['84.5,80.5,%.1f' % (top + 2.0), '62.5,80.5,%.1f' % (top + 1.0), '84.5,80.5,%.1f' % (top - 0.5)],
                  'corner_names': ['head', 'fly', 'foot'], 'bind': [2], 'free': [1], 'color': '#7a1a14', 'fullness': 1.04,
                  'meta': {'kind': 'flag', 'flag': 'pennant', 'mast': 'main'}})

    # ── 讀數（平面的帆：三角形；掛好之後的布另外量）──
    ship = set(hull) | set(deck) | set(mm) | set(mf) | set(ts)
    tree = cKDTree(np.array(sorted(ship), float) + 0.5)
    R = {'probe': probe or None, 'anchors': len(anchors), 'ropes': len(ropes), 'sails': len(sails), 'sail_plane': {}, 'rope_ends': {}}
    pts_w = {}
    for s in sails:
        P = []
        for c in s['corners']:
            if c.startswith('model:'):
                key = 'main' if '主桅' in c else 'fore'
                P.append(yard_world(key, c.rsplit('/', 1)[1]))
            else:
                P.append([float(v) for v in c.split(',')])
        pts_w[s['name']] = P
        A, B, Cc = (np.array(p) for p in P)
        samp = [A + u * (B - A) + v * (Cc - A) for u in np.linspace(0, 1, 60) for v in np.linspace(0, 1, 60) if u + v <= 1]
        d, _ = tree.query(np.array(samp))
        own = mm if s['meta'].get('mast') == 'main' else mf
        R['sail_plane'][s['name']] = {'corners': [[round(v, 1) for v in p] for p in P], 'min_dist_to_ship_cells': round(float(d.min()), 2),
                                      'area_m2': round(0.5 * float(np.linalg.norm(np.cross(B - A, Cc - A))) * 0.01, 2)}
    # 帆裝三段（Ship_Rigging §9.1）：每面帆的段數 ＝ set；第 k 段張段數 ≤ k 的
    table = {}
    for k, nm in ((1, '收帆'), (2, '戰鬥帆'), (3, '滿帆')):
        table[nm] = [s['name'] for s in sails if s['meta']['kind'] == 'sail' and int(s['meta']['set']) <= k]
    R['sail_sets'] = table

    # 繩兩端的世界座標（固定點 ＝ 格心；帆角照上面的點）
    def endpoint(e):
        if e.startswith('model:'):
            key = 'main' if '主桅' in e else 'fore'
            return yard_world(key, e.rsplit('/', 1)[1])
        if e.startswith('sail:'):
            nm, cn = e[5:].split('/')
            s = next(s for s in sails if s['name'] == nm)
            return pts_w[nm][s['corner_names'].index(cn)]
        link, an = e.split('/')
        a = next(a for a in anchors if WORKS[a['work']][1] == link and a['name'] == an)
        return [v + 0.5 for v in a['at']]
    for r in ropes:
        a, b = endpoint(r['from']), endpoint(r['to'])
        R['rope_ends'][r['name']] = {'from': [round(v, 1) for v in a], 'to': [round(v, 1) for v in b], 'len_m': round(math.dist(a, b) * 0.1, 2)}
    # 繩有沒有穿過帆（平面三角形）：每條繩 100 點取樣，到每面帆平面三角形的距離
    def tri_dist(p, A, B, Cc):
        A, B, Cc, p = (np.array(v) for v in (A, B, Cc, p))
        n = np.cross(B - A, Cc - A); n = n / np.linalg.norm(n)
        q = p - np.dot(p - A, n) * n
        v0, v1, v2 = Cc - A, B - A, q - A
        d00, d01, d11, d20, d21 = v0 @ v0, v0 @ v1, v1 @ v1, v2 @ v0, v2 @ v1
        den = d00 * d11 - d01 * d01
        u = (d11 * d20 - d01 * d21) / den
        v = (d00 * d21 - d01 * d20) / den
        inside = u >= 0 and v >= 0 and u + v <= 1
        return abs(float(np.dot(p - A, n))) if inside else None
    cross = {}
    for r in ropes:
        a, b = np.array(endpoint(r['from'])), np.array(endpoint(r['to']))
        for s in sails:
            if s['meta']['kind'] != 'sail' or r['meta'].get('sail') == s['name']:
                continue
            P = pts_w[s['name']]
            ds = [tri_dist(a + t * (b - a), *P) for t in np.linspace(0.02, 0.98, 100)]
            ds = [d for d in ds if d is not None]
            if ds and min(ds) < 1.0:
                cross.setdefault(r['name'], []).append(s['name'])
    R['ropes_through_flat_sail'] = cross
    if probe:
        print(json.dumps({k: R[k] for k in ('probe', 'sail_plane', 'ropes_through_flat_sail')}, ensure_ascii=False))
        return
    plan_out = {'anchors': anchors, 'ropes': ropes, 'sails': sails}
    with open(os.path.join(HERE, 'rig_plan.json'), 'w', encoding='utf-8', newline='\n') as f:
        json.dump(plan_out, f, ensure_ascii=False, indent=1)
    rows_ = [('sail', s['name'], s['meta']) for s in sails] + [('rope', r['name'], r['meta']) for r in ropes if r.get('meta')]
    with open(os.path.join(HERE, 'rig_meta.tsv'), 'w', encoding='utf-8', newline='\n') as f:
        f.write(''.join('%s\t%s\t%s\n' % (a, b, json.dumps(c, ensure_ascii=False, separators=(',', ':'))) for a, b, c in rows_))
    R['sha256'] = {f: hashlib.sha256(open(os.path.join(HERE, f), 'rb').read()).hexdigest() for f in ('rig_plan.json', 'rig_meta.tsv')}
    with open(os.path.join(HERE, 'verify_rigging.json'), 'w', encoding='utf-8', newline='\n') as f:
        json.dump(R, f, ensure_ascii=False, indent=1)
    # 圖紙 06：側面（船＋桅＋帆的三角形＋繩直線）
    s_ = 5
    W, H = 190, 180
    img = Image.new('RGB', (W * s_ + 80, H * s_ + 80), (246, 242, 230))
    d = ImageDraw.Draw(img)
    f = ImageFont.load_default()
    d.text((30, 10), 'al-Nawras - new sheet 06: rigging (flat sails before simulation, straight ropes). main-lateen set 1, fore-lateen set 3, pennant', fill=(20, 20, 40), font=f)
    oy = 40 + H * s_

    def P(x, z):
        return (40 + x * s_, oy - z * s_)
    for (x, y, z) in sorted(ship):
        if y >= YC:
            d.rectangle([40 + x * s_, oy - (z + 1) * s_, 40 + x * s_ + s_ - 1, oy - z * s_ - 1], fill=(170, 150, 120))
    for s in sails:
        pts = [P(p[0], p[2]) for p in pts_w[s['name']]]
        d.polygon(pts, outline=(120, 30, 30) if s['meta']['kind'] == 'flag' else (60, 60, 140))
    for r in ropes:
        e = R['rope_ends'][r['name']]
        d.line([P(e['from'][0], e['from'][2]), P(e['to'][0], e['to'][2])], fill=(90, 70, 40))
    img.save(os.path.join(HERE, 'sheet06_rigging_v1.png'))
    print(json.dumps({k: v for k, v in R.items() if k not in ('rope_ends',)}, ensure_ascii=False))


if __name__ == '__main__':
    main()
