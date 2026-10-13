# 階段十五：舵與舵輪 —— 舵改外部模型（轉軸＝前緣格心連線）；舵輪兩件子作品（會轉的／不會轉的，0.02 m）當外部模型擺上後甲板
# 設計 plan.json helm（出處 provenance helm、helm.scar、helm.parts、helm.rudder）；現況 nf_state stage14（全部子作品；舵改模型後不再是格）。
# 子作品座標（同憲法號 -wheel）：x 沿船長（輪軸，船頭 +x）、y 橫向、z 上，z 0 ＝ 甲板面上第一層；輪軸中心線 y CY、z axle_z（格心）。
# 疤：輪轂朝船尾那一面（x 0）照旗的隼剪影刻 depth 格、底下那一格換成淺色（作者決定，見 provenance helm.scar）。
# 擺法：x 在 place.x_search 裡每 step 試，at ＝ 輪軸中心的世界座標（y 80.5 ＝ 中線格心）；要求兩件模型的取樣點都不在實心格（舵除外）、
#   底座底面每個取樣點正下方是實心（四角著地）；離 x_target 最近的那個。
# 舵：轉軸 hinge_bot → hinge_top（格心），量 ±max_deg 時舵的格（轉過去）落在別的實心格的有幾個（現況扣掉舵）。
# 輸出：masks/helm/{wheel,stand}.vox.txt、verify_helm.json
# 用法：python -I -X utf8 -B draft_helm.py <design 資料夾>
import sys, os, json, math
import numpy as np
from PIL import Image

sys.stdout.reconfigure(encoding='utf-8')
D = os.path.abspath(sys.argv[1] if len(sys.argv) > 1 else os.path.dirname(__file__))
sys.path.insert(0, D)
from nf_state import state_after, NX, NY, NZ

plan = json.load(open(os.path.join(D, 'plan.json'), encoding='utf-8'))
HP = plan['helm']
SX, SY, SZ = HP['size']
CY, AZ = HP['CY'], HP['axle_z']
COL = HP['colors']


class Part:
    def __init__(s):
        s.cells = {}

    def put(s, k, c, over=False):
        x, y, z = k
        if not (0 <= x < SX and 0 <= y < SY and 0 <= z < SZ):
            raise ValueError(('框外', k))
        if k in s.cells and not over:
            return
        s.cells[k] = c


def rad(y, z):
    return math.hypot(y + 0.5 - CY, z + 0.5 - AZ)


def falcon_mask():
    im = Image.open(os.path.join(D, HP['scar']['texture'])).convert('RGBA')
    W_, H_ = im.size
    px = im.load()
    from collections import Counter
    bg = Counter(px[x, y] for x in range(W_) for y in range(H_)).most_common(1)[0][0]
    pts = [(x, y) for x in range(W_) for y in range(H_) if px[x, y] != bg]
    xs = [p[0] for p in pts]; ys = [p[1] for p in pts]
    cx, cy = (min(xs) + max(xs) + 1) / 2.0, (min(ys) + max(ys) + 1) / 2.0
    on = set(pts)
    return on, cx, cy


def build_wheel():
    P = Part()
    rim, boss = HP['rim'], HP['boss']
    # 輪轂（含疤之前的實心）
    for x in range(boss['x'][0], boss['x'][1] + 1):
        for y in range(SY):
            for z in range(SZ):
                if rad(y, z) <= boss['r']:
                    P.put((x, y, z), COL['boss'])
    # 輪緣
    for x in range(rim['x'][0], rim['x'][1] + 1):
        for y in range(SY):
            for z in range(SZ):
                if rim['r_in'] <= rad(y, z) <= rim['r_out']:
                    P.put((x, y, z), COL['wheel'])
    # 輪幅＋把手（king spoke 朝正上）
    xm = [(rim['x'][0] + rim['x'][1]) // 2, (rim['x'][0] + rim['x'][1]) // 2 + 1]
    for k in range(HP['spokes']):
        th = math.pi / 2 + 2 * math.pi * k / HP['spokes']
        uy, uz = math.cos(th), math.sin(th)
        for y in range(SY):
            for z in range(SZ):
                dy, dz = abs(y + 0.5 - CY), z + 0.5 - AZ        # 輪幅左右對稱 ⇒ 用 |dy| 判（v1 水平那兩根剛好壓在門檻上，浮點讓兩舷判得不一樣，差 145 格）
                t = dy * uy + dz * uz
                d = abs(-dy * uz + dz * uy)
                if boss['r'] - 1 <= t <= rim['r_in'] + 0.5 and d <= HP['spoke_half']:
                    for x in xm:
                        P.put((x, y, z), COL['wheel'])
                elif rim['r_out'] - 0.5 <= t <= HP['handle_r'] and d <= HP['handle_half']:
                    for x in range(rim['x'][0], rim['x'][1] + 1):
                        if abs(x + 0.5 - (rim['x'][0] + rim['x'][1] + 1) / 2.0) <= HP['handle_half']:
                            P.put((x, y, z), COL['wheel'])
    # 輪軸、鼓輪
    for x in range(boss['x'][1] + 1, HP['stanchion']['x'][1][1] + 1):
        for y in range(SY):
            for z in range(SZ):
                if rad(y, z) <= HP['axle_r']:
                    P.put((x, y, z), COL['iron'])
    dr = HP['drum']
    for x in range(dr['x'][0], dr['x'][1] + 1):
        for y in range(SY):
            for z in range(SZ):
                r = rad(y, z)
                if r <= dr['r']:
                    P.put((x, y, z), COL['iron'] if x in dr['x'] else COL['wheel'], over=True)
    # 疤：輪轂船尾那一面
    on, fcx, fcy = falcon_mask()
    sc = HP['scar']
    scar = []
    for y in range(SY):
        for z in range(SZ):
            if rad(y, z) > boss['r'] - 0.5:
                continue
            u = abs(CY - (y + 0.5)) / sc['scale'] + fcx     # 剪影左右對稱 ⇒ 用 |dy| 取右半邊（從船尾看右手是 −y ⇒ 圖的 +x）
            v = (AZ - (z + 0.5)) / sc['scale'] + fcy
            if (int(math.floor(u)), int(math.floor(v))) in on:
                scar.append((y, z))
    x0 = boss['x'][0]
    for y, z in scar:
        for d in range(sc['depth']):
            del P.cells[(x0 + d, y, z)]
        P.cells[(x0 + sc['depth'], y, z)] = sc['color']
    AY, AZi = int(math.floor(CY)), int(math.floor(AZ))
    pts = {'axle': (x0 + sc['depth'], AY, AZi), 'hub-aft': (x0, AY, AZi),
           'drum-rope-a': ((dr['x'][0] + dr['x'][1]) // 2, AY, AZi + int(dr['r'])), 'drum-rope-b': ((dr['x'][0] + dr['x'][1]) // 2, AY, AZi - int(dr['r']))}
    return P, pts, len(scar)


def build_stand():
    P = Part()
    st, b = HP['stanchion'], HP['base']
    for x in range(b['x'][0], b['x'][1] + 1):
        for y in range(SY):
            if abs(y + 0.5 - CY) <= b['half_y']:
                for z in range(b['z'][0], b['z'][1] + 1):
                    P.put((x, y, z), COL['base'])
    for xa, xb in st['x']:
        for x in range(xa, xb + 1):
            for y in range(SY):
                if abs(y + 0.5 - CY) > st['half_y']:
                    continue
                for z in range(b['z'][1] + 1, st['top'] + 1):
                    if rad(y, z) <= HP['axle_r']:
                        continue                                  # 輪軸穿過的孔
                    P.put((x, y, z), COL['iron'] if z >= st['top'] - 1 else COL['stand'])
    pts = {'base': ((b['x'][0] + b['x'][1]) // 2, int(math.floor(CY)), 0)}
    return P, pts


def components(cells):
    S = set(cells); seen = set(); n = 0
    for c in S:
        if c in seen:
            continue
        n += 1; st = [c]; seen.add(c)
        while st:
            x, y, z = st.pop()
            for d in ((1, 0, 0), (-1, 0, 0), (0, 1, 0), (0, -1, 0), (0, 0, 1), (0, 0, -1)):
                q = (x + d[0], y + d[1], z + d[2])
                if q in S and q not in seen:
                    seen.add(q); st.append(q)
    return n


def write(P, name, title):
    path = os.path.join(D, 'masks', 'helm', name + '.vox.txt')
    os.makedirs(os.path.dirname(path), exist_ok=True)
    with open(path, 'w', encoding='utf-8', newline='\n') as f:
        f.write('# 夜隼號' + title + '（draft_helm.py，0.02 m）x,y,z,color —— at 0,0,0\n')
        for k, c in sorted(P.cells.items()):
            f.write('%d,%d,%d,%d\n' % (k[0], k[1], k[2], c))
    return 'masks/helm/' + name + '.vox.txt'


def rot_axis(P, o, u, deg):
    """Rodrigues：點 P（N×3）繞過 o、方向 u 的軸轉 deg。"""
    th = math.radians(deg); u = u / np.linalg.norm(u)
    v = P - o
    return o + v * math.cos(th) + np.cross(u, v) * math.sin(th) + np.outer(v @ u, u) * (1 - math.cos(th))


def main():
    PW, wpts, nscar = build_wheel()
    PS, spts = build_stand()
    fw = write(PW, 'wheel', '舵輪（會轉的：輪、輪幅、輪轂與疤、輪軸、鼓輪）')
    fs = write(PS, 'stand', '舵輪座（底座、兩根支柱）')
    asym = lambda P: sum(1 for (x, y, z), c in P.cells.items() if P.cells.get((x, int(2 * CY - 1 - y), z)) != c)
    print('wheel', len(PW.cells), 'stand', len(PS.cells), 'scar', nscar, 'asym', asym(PW), asym(PS), 'comp', components(PW.cells), components(PS.cells))

    W = state_after(D, 'stage14')
    occ = np.zeros((NX, NY, NZ), bool)
    for k, v in W.items():
        if k != 'rudder':
            occ |= v > 0
    Q = W['quarter']
    S = HP['scale']
    pivot = np.array([SX / 2.0, CY, AZ])
    offs = np.array([[0.5, 0.5, 0.5]] + [[0.15 + 0.7 * (k & 1), 0.15 + 0.7 * ((k >> 1) & 1), 0.15 + 0.7 * ((k >> 2) & 1)] for k in range(8)])
    samp = lambda P: (np.array(sorted(P.cells), float)[:, None, :] + offs[None]).reshape(-1, 3)
    sw, ss = samp(PW), samp(PS)
    bot = np.array([[x + ox, y + oy, 0.0] for (x, y, z) in PS.cells if z == 0 for ox in (0.25, 0.75) for oy in (0.25, 0.75)])

    def place(A, at):
        return (A - pivot) * S + np.asarray(at)

    def hits(Wp):
        i = np.floor(Wp).astype(int)
        return int(occ[i[:, 0], i[:, 1], i[:, 2]].sum())

    pl = HP['place']
    cands = []
    x = pl['x_search'][0]
    while x <= pl['x_search'][1] + 1e-9:
        xs = range(int(math.floor(x - SX / 2 * S)), int(math.ceil(x + SX / 2 * S)) + 1)
        tops = {int(np.nonzero(Q[xx, yy, :])[0].max()) for xx in xs for yy in range(74, 88) if Q[xx, yy, :].any()}
        for t in sorted(tops):
            at = (x, 80.5, t + 1 + AZ * S)
            if hits(place(sw, at)) or hits(place(ss, at)):
                continue
            b = np.floor(place(bot, at)).astype(int)
            sup = int(occ[b[:, 0], b[:, 1], b[:, 2] - 1].sum())
            if sup == len(b):
                cands.append((abs(x - pl['x_target']), x, at, t))
        x += pl['step']
    if not cands:
        raise SystemExit('後甲板上找不到四角著地、不撞的位置')
    _, xbest, at, t = min(cands)
    print('helm at', at, 'deck_top', t, 'candidates', len(cands), 'x range', min(c[1] for c in cands), max(c[1] for c in cands))

    # ── 舵：轉軸放在前緣那一面（前緣格的格面，不是格心）；gudgeon（前緣面之前的 73）搬回船殼；bearding ＝ 轉 ±max_deg 會掃進別的格的那些格刻掉 ──
    R = HP['rudder']
    RW = W['rudder']
    rc = np.argwhere(RW > 0)
    face = {}
    for z in sorted(set(rc[:, 2].tolist())):
        s_ = rc[(rc[:, 2] == z) & (rc[:, 1] == 80) & (RW[tuple(rc.T)] != 73)]
        face[z] = int(s_[:, 0].max()) + 1
    fixed = {tuple(c) for c in rc if c[0] >= face[c[2]]}
    o = np.array(R['hinge_bot'], float); top = np.array(R['hinge_top'], float); u = top - o
    def sweep_hits(cells, degs):
        m = np.array(sorted(cells))
        rs_ = (m[:, None, :].astype(float) + offs[None]).reshape(-1, 3)
        bad = set()
        for deg in degs:
            i = np.floor(rot_axis(rs_, o, u, deg)).astype(int)
            h = np.array([bool(occ[tuple(q)]) or tuple(q) in fixed for q in i]).reshape(-1, 9).any(1)
            bad |= {tuple(c) for c in m[h]}
        return bad
    mov = np.array(sorted({tuple(c) for c in rc} - fixed))
    degs = (-R['max_deg'], -20, 20, R['max_deg'])
    # 不削（bearding 量過會把斜的舵柱切成 2–3 塊，見 notes 階段十五）；改量「轉過去穿進別的格多深」：
    #   每格 5×5×5 取樣，轉 deg 之後落在實心（現況扣舵、加回 gudgeon）的取樣點，所在那一格離最近空格的距離（EDT；1 ＝ 表面那一層）
    from scipy import ndimage
    solid = occ.copy()
    for k in fixed:
        solid[k] = True
    x0_, y0_ = 30, 50
    sub = solid[x0_:x0_ + 70, y0_:y0_ + 60, 0:70]
    depth = ndimage.distance_transform_edt(sub)
    g5 = (np.arange(5) + 0.5) / 5
    o5 = np.array([[a_, b2, c_] for a_ in g5 for b2 in g5 for c_ in g5])
    rs5 = (mov[:, None, :].astype(float) + o5[None]).reshape(-1, 3)
    after = {}
    for deg in degs:
        i = np.floor(rot_axis(rs5, o, u, deg)).astype(int)
        h = sub[i[:, 0] - x0_, i[:, 1] - y0_, i[:, 2]]
        d = depth[i[h, 0] - x0_, i[h, 1] - y0_, i[h, 2]]
        after[str(deg)] = {'samples_in_solid': int(h.sum()), 'samples': len(rs5), 'rudder_cells_touching': int(h.reshape(-1, 125).any(1).sum()),
                           'samples_deeper_than_surface': int((d > 1.0).sum()), 'max_edt': round(float(d.max()), 2) if len(d) else 0.0}
    beard = set()
    keep = {tuple(c) for c in mov}
    carve = sorted(fixed | beard)
    fc = os.path.join(D, 'masks', 'helm', 'rudder_carve.vox.txt')
    with open(fc, 'w', encoding='utf-8', newline='\n') as f:
        f.write('# 舵：刻掉 gudgeon（搬回船殼）＋ bearding（draft_helm.py）x,y,z,color —— 舵子作品座標 ＝ 世界\n')
        for k in carve:
            f.write('%d,%d,%d,%d\n' % (k[0], k[1], k[2], int(RW[k])))
    fg = os.path.join(D, 'masks', 'helm', 'gudgeons_hull.vox.txt')
    with open(fg, 'w', encoding='utf-8', newline='\n') as f:
        f.write('# gudgeon（從舵子作品搬回船殼，draft_helm.py）x,y,z,color —— 船殼座標 ＝ 世界\n')
        for k in sorted(fixed):
            assert W['hull'][k] == 0
            f.write('%d,%d,%d,%d\n' % (k[0], k[1], k[2], int(RW[k])))
    turn = {'face_x_by_z': {str(z): x for z, x in face.items()}, 'gudgeons_to_hull': len(fixed),
            'rudder_after': len(keep), 'rudder_after_components': components(keep), 'sweep': after, 'files': {'carve': 'masks/helm/rudder_carve.vox.txt', 'gudgeons': 'masks/helm/gudgeons_hull.vox.txt'}}
    print('rudder', json.dumps({k: v_ for k, v_ in turn.items() if k != 'face_x_by_z'}, ensure_ascii=False))
    un = u / np.linalg.norm(u)
    out = {'note': 'draft_helm.py（階段十五）—— 現況 nf_state stage14（舵以外）',
           'wheel': {'work': HP['wheel_work'], 'file': fw, 'cells': len(PW.cells), 'scar_cells': nscar, 'anchors': {k: list(v) for k, v in wpts.items()}},
           'stand': {'work': HP['stand_work'], 'file': fs, 'cells': len(PS.cells), 'anchors': {k: list(v) for k, v in spts.items()}},
           'size': HP['size'], 'mpv': HP['mpv'], 'scale': S, 'pivot': pivot.tolist(), 'at': [round(v, 4) for v in at], 'deck_top': t, 'host': 'summit-night-falcon-01m-deck-quarter',
           'models': [{'name': '舵輪', 'work': HP['wheel_work'], 'meta': {'kind': 'wheel', 'turn_axis': 'x', 'pivot_anchor': 'axle'}},
                      {'name': '舵輪座', 'work': HP['stand_work'], 'meta': {'kind': 'wheel_stand'}}],
           'stamp_order': {'hull': [{'name': 'gudgeons', 'op': 'stampvox', 'file': 'masks/helm/gudgeons_hull.vox.txt', 'at': [0, 0, 0], 'origin_world': [0, 0, 0], 'voxels': len(fixed)}],
                           'rudder': [{'name': 'rudder_gudgeons_out', 'op': 'carvevox', 'file': 'masks/helm/rudder_carve.vox.txt', 'at': [0, 0, 0], 'origin_world': [0, 0, 0], 'voxels': len(carve)}]},
           'rudder': {'work': 'summit-night-falcon-01m-rudder', 'model': '舵', 'host': 'summit-night-falcon-01m-assembly', 'unlink': '舵',
                      'pivot': o.tolist(), 'at': o.tolist(), 'anchors': {'stock-top': R['stock_top']},
                      'meta': {'kind': 'rudder', 'turn_axis': 'hinge', 'max_deg': R['max_deg'],
                               'hinge_x': o[0], 'hinge_y': o[1], 'hinge_z': o[2],
                               'axis_x': round(float(un[0]), 4), 'axis_y': 0, 'axis_z': round(float(un[2]), 4)},
                      'rake_deg': round(math.degrees(math.atan2(-u[0], u[2])), 2), 'turn': turn}}
    with open(os.path.join(D, 'verify_helm.json'), 'w', encoding='utf-8', newline='\n') as f:
        json.dump(out, f, ensure_ascii=False, indent=1)


if __name__ == '__main__':
    main()
