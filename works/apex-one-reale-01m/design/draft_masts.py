# 皇家號 新圖紙 03（TASK-0699）：桅、三角帆桁、帆、靜索、旗 ⇒ 清單、帆桁固定點與擺法、繩帆計畫、圖紙 sheet03、讀數 verify_masts.json
#   用法：python -I -X utf8 draft_masts.py [--probe=yard_z=main:-140]
#   · 只讀 plan.json、船殼與階段二的清單（兩階段都證過 ＝ 作品），不碰作品。
#   · 桅：整船的框（720×321×460、at 0,0,0）；跟船殼重疊的格不放（桅坐在船殼上）；穿過甲板-main 的那幾格從甲板刻掉（桅孔，桅把孔填滿）。
#   · 三角帆桁：每根一件緊框的子作品（前端低、後端高的斜桿），固定點 pivot（吊點）／fore／peak；當外部模型放在桅子作品裡，rotate 0、在桅的左舷側。
#   · --probe：反向對照用（只印讀數、⛔ 不寫檔）。yard_x／yard_z=<桅>:<格> ⇒ 那根帆桁整根平移（yard_z=main:-140 ⇒ 前端落進船殼與甲板，要報撞到）。
import sys, os, json, math, hashlib
import numpy as np
from PIL import Image, ImageDraw, ImageFont

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import lines as HL

sys.stdout.reconfigure(encoding='utf-8')
SX, SY, SZ = 720, 321, 460
YC = 160


def V(d):
    return d['v'] if isinstance(d, dict) and 'v' in d else d


def font(sz):
    for f in ('C:/Windows/Fonts/msjh.ttc', 'C:/Windows/Fonts/msyh.ttc', 'C:/Windows/Fonts/arial.ttf'):
        if os.path.exists(f):
            return ImageFont.truetype(f, sz)
    return ImageFont.load_default()


def palette_rgb(i):
    return ((i >> 5 & 7) * 255 // 7, (i >> 2 & 7) * 255 // 7, (i & 3) * 255 // 3)


def load(path):
    return np.loadtxt(path, delimiter=',', comments='#', dtype=np.int32, ndmin=2, encoding='utf-8')


def fmt(p):
    return '%g,%g,%g' % tuple(round(float(v), 2) for v in p)


class Mast:
    def __init__(self, key, m):
        self.key = key
        self.m = m
        self.rk = math.tan(math.radians(m['rake_deg']))
        self.y = YC + m['dy']
        self.z0 = 3
        self.ztop = int(self.z0 + m['length'] * math.cos(math.radians(m['rake_deg'])))

    def ax(self, z):
        return self.m['heel_x'] + (z - self.z0) * self.rk

    def r(self, z):
        t = (z - self.z0) / max(1, self.ztop - self.z0)
        return self.m['r_foot'] + (self.m['r_top'] - self.m['r_foot']) * t


def build_mast(M, blk, C):
    a = {}
    for z in range(M.z0, M.ztop + 1):
        cx = M.ax(z + 0.5)
        top_blk = z > M.ztop - blk
        r = M.r(z) + (1.0 if top_blk else 0.0)
        for x in range(int(cx - r) - 1, int(cx + r) + 2):
            for y in range(int(M.y - r) - 1, int(M.y + r) + 2):
                if (x + 0.5 - cx) ** 2 + (y - M.y) ** 2 <= r * r:
                    a[(x, y, z)] = C['gold'] if z >= M.ztop - 1 else (C['block'] if top_blk else C['mast'])
    return a


def build_yard(Y):
    """回傳 (格 dict, 框 size, 固定點 local)。前端 fore 在 (3+dx, 3, 3)、頂 peak 在 (3, 3, 3+dz)。"""
    a = math.radians(Y['angle_deg'])
    dxl, dzl = int(round(Y['length'] * math.cos(a))), int(round(Y['length'] * math.sin(a)))
    F = np.array([3 + dxl, 3, 3], float)
    Pk = np.array([3, 3, 3 + dzl], float)
    size = [dxl + 7, 7, dzl + 7]
    f = Y['sling_frac']
    piv = np.round(F + f * (Pk - F)).astype(int)
    cells = {}
    d = Pk - F
    L2 = float(d @ d)
    for x in range(size[0]):
        for z in range(size[2]):
            p = np.array([x + 0.5, 3.5, z + 0.5])
            t = float(np.clip((p - F - 0.5) @ d / L2, 0, 1))
            q = F + 0.5 + t * d
            r = 0.9 + 0.9 * max(0.0, 1 - abs(t - f) / 0.35)
            for y in range(size[1]):
                pp = np.array([x + 0.5, y + 0.5, z + 0.5])
                if float(((pp - q) ** 2).sum()) <= r * r:
                    band = abs(t - f) < 0.15 and int(t * Y['length']) % 10 < 2
                    cells[(x, y, z)] = 244 if band else 136
    anchors = {'pivot': piv.tolist(), 'fore': F.astype(int).tolist(), 'peak': Pk.astype(int).tolist()}
    for k, v in anchors.items():
        assert tuple(v) in cells, (k, v)
    return cells, size, anchors


def lys_png(path, w, h, bg, fg, step, border=True):
    im = Image.new('RGBA', (w, h), bg)
    px = im.load()
    glyph = ['..#..', '#.#.#', '#####', '..#..', '.###.']
    for oy in range(2, h - 4, step):
        for ox in range(2 + (oy // step % 2) * (step // 2), w - 4, step):
            for gy, row in enumerate(glyph):
                for gx, ch in enumerate(row):
                    if ch == '#':
                        px[ox + gx, oy + gy] = fg
    if border:
        for x in range(w):
            px[x, 0] = fg
            px[x, h - 1] = fg
        for y in range(h):
            px[0, y] = fg
            px[w - 1, y] = fg
    im.save(path)


def main():
    probe = {}
    for s in sys.argv[1:]:
        if s.startswith('--probe='):
            k, v = s[len('--probe='):].split('=')
            probe[k] = v
    plan = HL.load_plan(HERE)
    R = plan['rig']
    C = V(R['colors'])
    blk = int(V(R['masthead_block']))
    masts = {k: Mast(k, m) for k, m in V(R['masts']).items()}
    # 現況（船殼＋階段二各件）
    occ = {}
    layers = {'hull': load(os.path.join(HERE, 'masks', 'hull', 'hull_01.vox.txt'))}
    for nm in ('deck', 'apostis', 'rambade', 'eperon', 'stern', 'ladders'):
        layers[nm] = load(os.path.join(HERE, 'masks', 'upper', nm + '.vox.txt'))
    paint = load(os.path.join(HERE, 'masks', 'paint', 'stern.vox.txt'))
    for nm, arr in layers.items():
        for x, y, z, c in arr.tolist():
            occ[(x, y, z)] = (nm, c)
    out = {'masts': {}, 'holes': []}
    mast_cells = {}
    for k, M in masts.items():
        a = build_mast(M, blk, C)
        clash = {}
        keep = {}
        for p, c in a.items():
            o = occ.get(p)
            if o is None:
                keep[p] = c
            elif o[0] == 'hull':
                continue
            elif o[0] == 'deck':
                out['holes'].append((p, o[1]))
                keep[p] = c
            else:
                clash[o[0]] = clash.get(o[0], 0) + 1
        mast_cells[k] = keep
        out['masts'][k] = {'cells': len(keep), 'top_z': M.ztop, 'axis_x_deck': round(M.ax(28), 2), 'dy': M.m['dy'], 'clash_other_pieces': clash}
    # 帆桁
    YD = V(R['yards'])
    yards = {}
    for k, Y in YD.items():
        M = masts[k]
        cells, size, anc = build_yard(Y)
        zs = M.ztop - blk - 3
        r_here = M.r(zs)
        sy = M.y + Y['side'] * (int(math.ceil(r_here)) + 3)
        at = [M.ax(zs + 0.5), sy + 0.5, zs + 0.5]
        for ai, pk in ((0, 'yard_x'), (2, 'yard_z')):
            if probe.get(pk, '').startswith(k + ':'):
                at[ai] += float(probe[pk].split(':')[1])
        piv = [anc['pivot'][0] + 0.5, anc['pivot'][1] + 0.5, anc['pivot'][2] + 0.5]
        world = {n: [at[i] + (v[i] + 0.5 - piv[i]) for i in range(3)] for n, v in anc.items()}
        yards[k] = {'cells': cells, 'size': size, 'anchors': anc, 'at': at, 'pivot': piv, 'world': world, 'Y': Y}
    # 帆桁、桅掃過的地方有沒有撞到別的實心（離自己吊點 7 格內、自己的桅不算）
    allsolid = set(occ) | {p for k in mast_cells for p in mast_cells[k]}
    out['yards'] = {}
    for k, yd in yards.items():
        hits = 0
        own = set(mast_cells[k])
        for (x, y, z) in yd['cells']:
            wp = (int(math.floor(yd['at'][0] + x + 0.5 - yd['pivot'][0])), int(math.floor(yd['at'][1] + y + 0.5 - yd['pivot'][1])),
                  int(math.floor(yd['at'][2] + z + 0.5 - yd['pivot'][2])))
            if wp in allsolid and wp not in own:
                hits += 1
        w = yd['world']
        out['yards'][k] = {'length_m': round(yd['Y']['length'] * 0.1, 1), 'fore': [round(v, 1) for v in w['fore']], 'peak': [round(v, 1) for v in w['peak']],
                           'sling': [round(v, 1) for v in w['pivot']], 'cells': len(yd['cells']), 'hits_other_solid': hits}
    # 帆（三角，平面取樣：撞到實心幾點）
    sails, ropes, anchors = [], [], []
    for k, yd in yards.items():
        Lk = V(R['masts'])[k]['link']
        cl = yd['Y']['clew']
        clew = [cl[0] + 0.5, yd['at'][1], cl[1] + 0.5]
        F, Pk = np.array(yd['world']['fore']), np.array(yd['world']['peak'])
        Cw = np.array(clew)
        hit = 0
        own = set(mast_cells[k])
        for u in np.linspace(0, 1, 60):
            for v in np.linspace(0, 1 - u, max(2, int(60 * (1 - u)))):
                p = F + u * (Pk - F) + v * (Cw - F)
                c = tuple(int(math.floor(t)) for t in p)
                if c in allsolid and c not in own:
                    hit += 1
        nm = yd['Y']['sail']
        sails.append({'name': nm, 'corners': ['model:%s/yard-%s/fore' % (Lk, k), 'model:%s/yard-%s/peak' % (Lk, k), fmt(clew)],
                      'corner_names': ['tack', 'head', 'clew'], 'bind': [0], 'free': ['clew'], 'meta': {'kind': 'sail', 'mast': k, 'sail': 'gaff'}})
        out['yards'][k]['sail'] = {'name': nm, 'head_m': round(float(np.linalg.norm(Pk - F)) * 0.1, 1), 'leech_m': round(float(np.linalg.norm(Pk - Cw)) * 0.1, 1),
                                   'foot_m': round(float(np.linalg.norm(Cw - F)) * 0.1, 1), 'plane_hits': hit}
    # 固定點：桅上 hound、桅頂（長旗）；槳架縱樑上的 shroud／sheet 腳；甲板與撞角上的 tack
    D = {k: V(v) for k, v in plan['layout'].items()}
    L = HL.Lines(plan)
    sh = lambda x: int(np.floor(L.sheer(np.array([x + 0.5]))[0]))
    rail_top = lambda x: sh(x) + int(D['rail_above_sheer'])
    ah = int(D['apostis_half'])
    for k, M in masts.items():
        Lk = V(R['masts'])[k]['link']
        zh = M.ztop - blk - 1
        for s_, sg in (('P', -1), ('S', 1)):
            # 那一層桅最外那一格
            cand = [p for p in mast_cells[k] if p[2] == zh and (p[1] - M.y) * sg > 0]
            p = max(cand, key=lambda q: (q[1] - M.y) * sg)
            anchors.append({'work': 'mast-' + k, 'name': 'hound-' + s_, 'at': list(p)})
            for i, x in enumerate(V(R['shrouds'])[k], 1):
                nmA = 'shroud-%s-%s%d' % (k, s_, i)
                anchors.append({'work': 'apostis', 'name': nmA, 'at': [x, YC + sg * (ah - 1), rail_top(x)]})
                ropes.append({'name': '%s-shroud-%s%d' % (k, s_, i), 'from': '%s/hound-%s' % (Lk, s_), 'to': '舷外槳架/' + nmA, 'slack': 1.0,
                              'thickness': 0.8, 'color': '#2b2620', 'group': 'standing/shrouds', 'meta': {'kind': 'shroud'}})
            xb = V(R['sheet_belay_x'])[k]
            nmB = 'belay-%s-sheet-%s' % (k, s_)
            anchors.append({'work': 'apostis', 'name': nmB, 'at': [xb, YC + sg * (ah - 1), rail_top(xb)]})
            ropes.append({'name': '%s.sheet-%s' % (yards[k]['Y']['sail'], s_), 'from': 'sail:%s/clew' % yards[k]['Y']['sail'], 'to': '舷外槳架/' + nmB,
                          'slack': 1.03, 'thickness': 0.5, 'color': '#a08458', 'group': 'running/sheets', 'meta': {'kind': 'sheet', 'sail': yards[k]['Y']['sail']}})
        top = [p for p in mast_cells[k] if p[2] == M.ztop]
        tx = round(sum(p[0] for p in top) / len(top), 1)
        out['masts'][k]['truck'] = [tx, M.y, M.ztop]
    # tack：主帆 ⇒ 中央走道前端頂上；前帆 ⇒ 撞角尖的金球
    deck = layers['deck']
    cz = max(z for x, y, z, c in deck.tolist() if x == 548 and y == YC)
    anchors.append({'work': 'deck-main', 'name': 'tack-main', 'at': [548, YC, cz]})
    ep = layers['eperon']
    tip = max((x, z) for x, y, z, c in ep.tolist() if y == YC)
    anchors.append({'work': 'eperon', 'name': 'tack-fore', 'at': [tip[0], YC, tip[1]]})
    ropes.append({'name': 'main-lateen.tack', 'from': 'sail:main-lateen/tack', 'to': '甲板-main/tack-main', 'slack': 1.0, 'thickness': 0.5, 'color': '#a08458',
                  'group': 'running/tacks', 'meta': {'kind': 'tack', 'sail': 'main-lateen'}})
    ropes.append({'name': 'fore-lateen.tack', 'from': 'sail:fore-lateen/tack', 'to': '撞角/tack-fore', 'slack': 1.0, 'thickness': 0.5, 'color': '#a08458',
                  'group': 'running/tacks', 'meta': {'kind': 'tack', 'sail': 'fore-lateen'}})
    # 旗：兩根桅頂的長旗（紅底金百合）、主帆桁頂的王旗（白底金百合）
    FL = V(R['flags'])
    pl, ph = FL['pennant']
    for k, M in masts.items():
        tx, ty, tz = out['masts'][k]['truck']
        sails.append({'name': '%s-pennant' % k, 'corners': [fmt([tx + 0.5, ty + 0.5, tz]), fmt([tx - pl, ty + 0.5, tz - 1]), fmt([tx + 0.5, ty + 0.5, tz - ph])],
                      'corner_names': ['head', 'fly', 'foot'], 'bind': [2], 'free': [1], 'meta': {'kind': 'flag', 'flag': 'pennant', 'mast': k},
                      'color': '#b60000', 'texture': 'textures/pennant.png', 'fullness': 1.04})
    ew, eh = FL['ensign']
    yd = yards['main']
    pk_loc = yd['anchors']['peak']
    pk = np.array(yd['world']['peak'])
    sails.append({'name': 'ensign', 'corners': ['model:主桅/yard-main/peak', fmt(pk - [ew, 0, 0]), fmt(pk - [ew, 0, eh]),
                                                'model:主桅/yard-main/%d,%d,%d' % (pk_loc[0], pk_loc[1], pk_loc[2] - eh)],
                  'corner_names': ['head', 'fly-top', 'fly-foot', 'foot'], 'bind': [3], 'free': [2, 1], 'meta': {'kind': 'flag', 'flag': 'ensign'},
                  'color': '#ffffff', 'texture': 'textures/ensign.png', 'fullness': 1.04})
    out['ropes'] = len(ropes)
    out['sails'] = len(sails)
    out['holes'] = {'cells': len(out['holes'])}
    if probe:
        print(json.dumps({'probe': probe, 'yards': {k: {'hits_other_solid': v['hits_other_solid'], 'plane_hits': v['sail']['plane_hits']} for k, v in out['yards'].items()}}, ensure_ascii=False))
        return
    # 寫檔
    mk = os.path.join(HERE, 'masks')
    os.makedirs(os.path.join(mk, 'masts'), exist_ok=True)
    os.makedirs(os.path.join(mk, 'yards'), exist_ok=True)
    os.makedirs(os.path.join(HERE, 'textures'), exist_ok=True)
    lists = []

    def wlist(fn, cells, head):
        with open(fn, 'w', encoding='utf-8', newline='\n') as f:
            f.write(head + '\n')
            f.write('\n'.join('%d,%d,%d,%d' % (p[0], p[1], p[2], c) for p, c in sorted(cells.items())) + '\n')
        lists.append({'file': os.path.relpath(fn, HERE).replace('\\', '/'), 'cells': len(cells), 'sha256': hashlib.sha256(open(fn, 'rb').read()).hexdigest()})

    for k, cells in mast_cells.items():
        wlist(os.path.join(mk, 'masts', k + '.vox.txt'), cells, '# 皇家號 %s 桅（draft_masts.py）x,y,z,color —— at 0,0,0、整船的框 720×321×460' % k)
    holes = {}
    for k in masts:
        for p in mast_cells[k]:
            o = occ.get(p)
            if o and o[0] == 'deck':
                holes[p] = o[1]
    wlist(os.path.join(mk, 'masts', 'deck_holes.vox.txt'), holes, '# 皇家號 甲板-main 的桅孔（carvevox 帶顏色守門）x,y,z,color')
    for k, yd in yards.items():
        wlist(os.path.join(mk, 'yards', k + '.vox.txt'), yd['cells'], '# 皇家號 %s 三角帆桁（draft_masts.py）x,y,z,color —— 自己的框 %s' % (k, yd['size']))
    yj = {k: {'size': yd['size'], 'anchors': yd['anchors'], 'at': [round(v, 3) for v in yd['at']], 'pivot': yd['pivot'], 'mast_link': V(R['masts'])[k]['link'],
              'meta': {'kind': 'yard', 'mast': k, 'yard': 'gaff', 'rig': 'lateen', 'sail': yd['Y']['sail'], 'length_m': round(yd['Y']['length'] * 0.1, 1),
                       'pivot_anchor': 'pivot', 'turn_axis': 'z', 'rotate_z_deg': 0}} for k, yd in yards.items()}
    with open(os.path.join(HERE, 'yards.json'), 'w', encoding='utf-8', newline='\n') as f:
        json.dump(yj, f, ensure_ascii=False, indent=1)
    with open(os.path.join(HERE, 'rig_plan.json'), 'w', encoding='utf-8', newline='\n') as f:
        json.dump({'anchors': anchors, 'ropes': ropes, 'sails': sails}, f, ensure_ascii=False, indent=1)
    lys_png(os.path.join(HERE, 'textures', 'ensign.png'), ew, eh, (245, 245, 240, 255), (255, 182, 0, 255), 8)
    lys_png(os.path.join(HERE, 'textures', 'pennant.png'), 64, 8, (182, 0, 0, 255), (255, 182, 0, 255), 10, border=False)
    out['lists'] = lists
    with open(os.path.join(HERE, 'verify_masts.json'), 'w', encoding='utf-8', newline='\n') as f:
        json.dump(out, f, ensure_ascii=False, indent=1)
    sheet(plan, occ, paint, mast_cells, yards, sails, ropes, anchors, out, os.path.join(HERE, 'sheet03_rig_v1.png'))
    print(json.dumps({k: v for k, v in out.items() if k != 'lists'}, ensure_ascii=False, indent=1))


def sheet(plan, occ, paint, mast_cells, yards, sails, ropes, anchors, out, path):
    s = 1.6
    x0, x1, z1 = 30, 720, 420
    W, H = int((x1 - x0) * s) + 100, int(z1 * s) + 200
    img = Image.new('RGB', (W, H), (246, 242, 230))
    d = ImageDraw.Draw(img)
    f1, f2, f3 = font(28), font(18), font(14)
    d.text((40, 14), '皇家號 La Réale 新圖紙 03：桅、三角帆、靜索、旗（右舷看；船頭朝右）　0.1 m／格', fill=(20, 20, 40), font=f1)
    base = int(z1 * s) + 70
    P = lambda x, z: (50 + (x - x0) * s, base - z * s)
    side = {}
    for (x, y, z), (nm, c) in occ.items():
        k = (x, z)
        if k not in side or y > side[k][0]:
            side[k] = (y, c)
    for m in mast_cells.values():
        for (x, y, z), c in m.items():
            if (x, z) not in side or y > side[(x, z)][0]:
                side[(x, z)] = (y, c)
    for (x, z), (y, c) in side.items():
        a, b = P(x, z + 1)
        d.rectangle([a, b, a + s, b + s], fill=palette_rgb(c))
    wl = plan['waterline']['z']
    d.line([P(x0, wl + 1), P(x1, wl + 1)], fill=(40, 110, 200))
    for k, yd in yards.items():
        w = yd['world']
        d.line([P(w['fore'][0], w['fore'][2]), P(w['peak'][0], w['peak'][2])], fill=(145, 72, 0), width=4)
    for sl in sails:
        if sl['meta']['kind'] == 'sail':
            k = sl['meta']['mast']
            w = yards[k]['world']
            cl = [float(v) for v in sl['corners'][2].split(',')]
            d.polygon([P(w['fore'][0], w['fore'][2]), P(w['peak'][0], w['peak'][2]), P(cl[0], cl[2])], outline=(120, 100, 70), fill=(242, 234, 216))
            d.line([P(w['fore'][0], w['fore'][2]), P(w['peak'][0], w['peak'][2])], fill=(145, 72, 0), width=4)
    an = {(a['work'], a['name']): a['at'] for a in anchors}
    wk = {'主桅': 'mast-main', '前桅': 'mast-fore', '舷外槳架': 'apostis', '甲板-main': 'deck-main', '撞角': 'eperon'}
    for r in ropes:
        def ept(e):
            if e.startswith('sail:'):
                nm, c = e[5:].split('/')
                sl = next(q for q in sails if q['name'] == nm)
                i = sl['corner_names'].index(c)
                if sl['corners'][i].startswith('model:'):
                    k = sl['meta']['mast']
                    p = yards[k]['world'][sl['corners'][i].split('/')[-1]]
                    return p[0], p[2]
                p = [float(v) for v in sl['corners'][i].split(',')]
                return p[0], p[2]
            lk, nm = e.split('/')
            p = an[(wk[lk], nm)]
            return p[0], p[2]
        (ax_, az), (bx, bz) = ept(r['from']), ept(r['to'])
        d.line([P(ax_, az), P(bx, bz)], fill=(43, 38, 32) if 'shroud' in r['name'] else (160, 132, 88), width=1)
    for x in range(50, x1, 50):
        d.text(P(x, -2), str(x), fill=(80, 80, 80), font=f3)
    y0 = base + 30
    yl = out['yards']
    for i, k in enumerate(('main', 'fore')):
        m, y = out['masts'][k], yl[k]
        d.text((40, y0 + i * 24), '%s：桅頂 z %d（%.1f m）、甲板處 x %.1f、偏中線 %d；帆桁 %.1f m、吊點 %s、前端 %s、頂 %s；帆 前緣 %.1f／後緣 %.1f／帆腳 %.1f m'
               % ({'main': '主桅', 'fore': '前桅'}[k], m['top_z'], m['top_z'] * 0.1, m['axis_x_deck'], m['dy'], y['length_m'], y['sling'], y['fore'], y['peak'],
                  y['sail']['head_m'], y['sail']['leech_m'], y['sail']['foot_m']), fill=(60, 60, 60), font=f3)
    img.save(path)


if __name__ == '__main__':
    main()
