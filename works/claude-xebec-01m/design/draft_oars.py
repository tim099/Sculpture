# 利劍號 新圖紙 10（TASK-0022 步驟 13）：槳 —— 每舷 9 支，從舷牆的槳門伸出去（引用蠍子號的槳元件、一支一個外部模型）
#   ⇒ oars_placement.json、verify_oars.json、sheet10_oars_v1.png、masks/oars/oars_rest.vox.txt（18 支靜止時的世界格，只給 verifier 對照、不落格）
#   出處：蠍子號 claude-galiot-01m/design/draft_oars.py（槳元件的固定點 pivot／blade／seat、模型 at ＝ pivot、右舷原樣、左舷 mirror=y、rotate 的 x 角補到槳葉中心落在水面、
#         槳手照遊戲 40_crew.js oarCrew 模擬）＋ 持火號 erina-dromon-01m/design/draft_oars.py（從船殼的槳口伸出去：pivot 在洞底往上、y 在殼的中間、每支照槳口高度補傾角、
#         元件角度用 pivot→槳葉中心的實際角度）＋ 本船 draft_helm.py（實心照前面每一步的設計清單與模型、砲／後座／迴旋砲 arc、遊戲砲手站位、走路格、繩、帆布）。
#   改的地方：
#     · 不新做槳：元件格子照 CLI export 的清單（masks/oars_src/，唯讀快取），固定點照來源作品的 anchors.json。
#     · 划槳整個行程都量：遊戲 31_drive.js oarAnim 的姿勢 —— 相位 φ、掃 θ ＝ −sg·stroke·cos φ（繞 pivot 的直立軸）、抬 α ＝ sg·dip·max(0, −sin φ)（繞沿船身的軸），
#       swM ＝ Rz(θ)·Rx(α)（21_gunnery.js modelLocal：先抬再掃）；每 phase_step 度一個姿勢＋靜止。碰撞、砲、後座、迴旋砲 arc、錨與吊錨木、繩、帆布每個姿勢都量。
#     · 槳手：照 oarCrew 排（seat 起沿「pivot ← blade」平面方向每 6 格一個、standNear 6 格內、standZ 頭上 14 格、z 在 [min(seat,pivot)−14, max+2]、
#       避開 CREW_BLOCK 的外框外擴 1 格；砲班先排 ⇒ 砲手站位先佔掉）；再量主甲板走路格主群、梯子、hoist、絞盤、艙蓋、爐灶、送藥手那一圈。
#   用法：python -I -X utf8 draft_oars.py [--probe=sink=S05[:格]] [--probe=drop=P09] [--probe=stroke=<度>] [--probe=rowers=<人>] [--probe=lift=<格>]
#     反向對照不寫檔：那一支往下沉 ⇒ 只有它報撞船；少一支 ⇒ 那一舷 8 支、槳手少 3；掃的角度加大 ⇒ 撞砲；每支多一人 ⇒ 擋送藥手／走路；槳柄貼著洞底 ⇒ 撞槳門下緣。
import sys, os, json, math, hashlib
import numpy as np
from scipy import ndimage
from scipy.spatial import cKDTree
from PIL import Image, ImageDraw, ImageFont

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import lines as HL
import draft_guns as DG
from draft_gear import Model, corners, hit, mark, grid_of
from draft_helm import Anchor

V = HL.V
TAGS = ['air', 'hull', 'deck', 'ladder', 'beak', 'platform', 'glass', 'mast', 'gun-post', 'magazine', 'awning', 'yard', 'gun', 'gear', 'cathead', 'rudder', 'tiller', 'anchor']
CREW_TALL, CREW_SLAB = 20, 14       # 遊戲 40_crew.js：比 20 格高的模型只看腳到頭那 14 格
HEAD = 14                           # 40_crew.js standNear(…, 14, …)


def load(fn):
    a = np.loadtxt(os.path.join(HERE, fn), delimiter=',', comments='#', dtype=np.int32, ndmin=2)
    return {(int(x), int(y), int(z)): int(c) for x, y, z, c in a}


def r3(v):
    return [round(float(c), 3) for c in v]


def Rx(a):
    c, s = math.cos(math.radians(a)), math.sin(math.radians(a))
    return np.array([[1, 0, 0], [0, c, -s], [0, s, c]])


def Rz(a):
    c, s = math.cos(math.radians(a)), math.sin(math.radians(a))
    return np.array([[c, -s, 0], [s, c, 0], [0, 0, 1]])


def main():
    sys.stdout.reconfigure(encoding='utf-8')
    probe = dict(a[len('--probe='):].split('=', 1) for a in sys.argv[1:] if a.startswith('--probe='))
    plan = HL.load_plan(HERE)
    YC = int(plan['space']['yc'])
    AX, AY, AZ = [int(v) for v in plan['space']['assembly']]
    SH = (AX, AY, AZ)
    WL = int(plan['waterline']['z'])
    O = {k: V(v) for k, v in plan['oars'].items() if k != 'src'}
    SURF = WL + O['water_surface_dz']
    STROKE = float(probe.get('stroke', O['stroke_deg']))                  # 掃的上限；每支從這裡往下找第一個整個行程都不撞的（--probe=stroke ⇒ 全部固定用它、不找）
    STROKE_MIN = float(O['stroke_min'])
    DIP = float(O['dip_deg'])
    NROW = int(probe.get('rowers', O['rowers']))
    LIFT = float(probe.get('lift', O['pivot_lift']))
    SC = float(O['scale'])
    GBG = {k: V(v) for k, v in plan['guns_build'].items() if not k.endswith('src')}

    # ── 步驟 13 以前的實心（設計清單＋模型；draft_helm.py 同一份＋步驟 11 的舵、舵柄、錨、吊錨木、平台刻掉的格）──
    LAB = np.zeros(SH, np.uint8)

    def put(tag, cells):
        c = np.array(sorted(cells), int)
        if len(c):
            LAB[c[:, 0], c[:, 1], c[:, 2]] = TAGS.index(tag)
    hull = load('masks/hull/hull_01.vox.txt')
    hull.update(load('masks/step6/hull_paint.vox.txt'))
    decks = {k: load('masks/decks/%s.vox.txt' % k) for k in ('hold', 'main', 'quarter')}
    for d in decks.values():
        put('deck', d)
    put('ladder', set(load('masks/ladders/main.vox.txt')) | set(load('masks/ladders/quarter.vox.txt')))
    put('beak', load('masks/deco/beak.vox.txt'))
    put('platform', load('masks/deco/platform.vox.txt'))
    put('glass', load('masks/deco/glass.vox.txt'))
    for m in ('mizzen', 'main', 'fore'):
        put('mast', load('masks/masts/%s.vox.txt' % m))
    put('gun-post', set(load('masks/guns/posts_main.vox.txt')) | set(load('masks/guns/posts_quarter.vox.txt')))
    put('magazine', load('masks/gear/magazine.vox.txt'))
    put('hull', hull)
    put('awning', load('masks/deco/awning.vox.txt'))
    yardw = set()
    for p in json.load(open(os.path.join(HERE, 'yards_placement.json'), encoding='utf-8')):
        off = [int(round(p['at'][i] - p['pivot'][i])) for i in range(3)]
        yardw |= {(x + off[0], y + off[1], z + off[2]) for (x, y, z) in load('masks/yards/lateen-%s.vox.txt' % p['mast'])}
    put('yard', yardw)
    carve = load('masks/helm/platform_carve.vox.txt')
    for k in carve:
        LAB[k] = 0
    cathead = load('masks/helm/cathead.vox.txt')
    put('cathead', cathead)
    STAND_TAGS = [TAGS.index(t) for t in ('hull', 'deck', 'ladder', 'beak', 'platform', 'glass', 'mast', 'gun-post', 'magazine', 'cathead')]
    STAND = np.isin(LAB, STAND_TAGS)                                       # 遊戲站位用的格子（navBase：船的格；外部模型不算）
    HP = json.load(open(os.path.join(HERE, 'helm_placement.json'), encoding='utf-8'))
    rud = load('masks/helm/rudder.vox.txt')                                # 舵、舵柄：at ＝ pivot、scale 1 ⇒ 清單就是世界格（靜止）
    til = load('masks/helm/tiller.vox.txt')
    sel = [k for k in rud if LAB[k] == 0]
    put('rudder', sel)
    put('tiller', [k for k in til if LAB[k] == 0])
    asrc = np.loadtxt(os.path.join(HERE, 'masks', 'helm_src', HP['anchors'][0]['work'] + '.vox.txt'), delimiter=',', comments='#', dtype=np.int32, ndmin=2)[:, :3].astype(float)
    anchors = []
    for a in HP['anchors']:
        g = Anchor(asrc, a['pivot'], a['scale'], a['rotate'][2], bool(a['mirror']))
        P = np.floor(g.world(g.centers, a['at'])).astype(int)
        s_ = LAB[P[:, 0], P[:, 1], P[:, 2]] == 0
        LAB[P[s_, 0], P[s_, 1], P[s_, 2]] = TAGS.index('anchor')
        anchors.append((a, g, P))

    # ── 砲（格、外框、後座、迴旋砲 arc 掃過的格、射線、砲手站位；draft_helm.py 同一套）──
    gun_t = {k: DG.Gun(k, t, GBG['search']['inset']) for k, t in GBG['types'].items()}
    gun_rows = [r for r in json.load(open(os.path.join(HERE, 'guns_placement.json'), encoding='utf-8'))['rows'] if r.get('at') is not None]
    recoil_cells = np.zeros(SH, bool)
    sweep_cells = np.zeros(SH, bool)
    gcells = np.zeros(SH, bool)
    gun_box, crew_spots, muzzles = [], [], []
    RC = GBG['recoil']
    for r in gun_rows:
        g = gun_t[r['type']]
        mir = r['side'] == 'P'
        mark(gcells, g.world(g.centers, r['at'], r['phi'], mir))
        gun_box.append((r['name'], np.array(r['bbox'][0], float), np.array(r['bbox'][1], float)))
        dist = max(RC['min'], g.barrel_len * RC['k'])
        ax = g.axis(r['phi'], mir)
        part = g.barrel_samples if r['swivel'] else g.samples
        for t in np.arange(0.5, dist + 1e-9, 0.5):
            mark(recoil_cells, g.world(part, np.array(r['at'], float) - ax * t, r['phi'], mir))
        if r['swivel'] and r.get('arc'):
            a0, a1 = [int(v) for v in r['arc'].split(',')]
            for a in range(a0, a1 + 1, GBG['sweep_step_deg']):
                mark(sweep_cells, g.world(g.samples, r['at'], float(a), mir))
        for a in r['crew']['at']:
            crew_spots.append((r['name'], r['deck'], [float(v) for v in a]))
        muzzles.append((r['name'], g.world(g.anchors['muzzle'][None], r['at'], r['phi'], mir)[0]))
    LAB[gcells & (LAB == 0)] = TAGS.index('gun')
    recoil_cells &= ~gcells
    sweep_cells &= ~gcells
    RAYG = np.zeros(SH, bool)                                             # 砲口射線（加農砲一條、迴旋砲 arc 每 sweep_step_deg 一條）經過的格
    for r in gun_rows:
        g = gun_t[r['type']]
        mir = r['side'] == 'P'
        angs, far = [r['phi']], GBG['ray_len']
        if r['swivel'] and r.get('arc'):
            a0, a1 = [int(v) for v in r['arc'].split(',')]
            angs, far = list(range(a0, a1 + 1, GBG['sweep_step_deg'])), 40.0
        for a in angs:
            mz = g.world(g.anchors['muzzle'][None], r['at'], float(a), mir)[0]
            mark(RAYG, mz[None] + np.arange(0.5, far + 1e-9, 0.25)[:, None] * g.axis(float(a), mir)[None])

    # ── 步驟 10 的甲板物件（模型的格、外框）──
    GP = json.load(open(os.path.join(HERE, 'gear_placement.json'), encoding='utf-8'))
    gear = []
    for m in GP['models']:
        src = np.loadtxt(os.path.join(HERE, 'masks', 'gear_src', m['work'] + '.vox.txt'), delimiter=',', comments='#', dtype=np.int32, ndmin=2)[:, :3].astype(float)
        g = Model(src, m['pivot'], m['scale'], m['rotate'])
        gear.append(m)
        if m['host'] == 'magazine':
            continue
        P = np.floor(g.world(g.centers, m['at'])).astype(int)
        s_ = LAB[P[:, 0], P[:, 1], P[:, 2]] == 0
        LAB[P[s_, 0], P[s_, 1], P[s_, 2]] = TAGS.index('gear')

    # ── 繩（步驟 8 的直線）、帆布（步驟 8 export 的 obj 頂點）──
    RE = json.load(open(os.path.join(HERE, 'verify_rigging.json'), encoding='utf-8'))['rope_ends']
    RT = {r_['name']: r_['thickness'] for r_ in json.load(open(os.path.join(HERE, 'rig_plan.json'), encoding='utf-8'))['ropes']}
    ropes = [(nm, np.array(e['from'], float), np.array(e['to'], float), RT.get(nm, 0.5) / 2.0) for nm, e in sorted(RE.items())]
    CV, CO, cloth_files = [], [], {}
    for rel in plan['gear'].get('cloth_objs', []):
        fn = os.path.normpath(os.path.join(HERE, rel))
        if not os.path.exists(fn):
            cloth_files[rel] = None
            continue
        cloth_files[rel] = hashlib.sha256(open(fn, 'rb').read()).hexdigest()[:16]
        cur = None
        for line in open(fn, encoding='utf-8'):
            if line.startswith('o '):
                cur = ('sail:' + line.split('#', 1)[1].strip()) if line.startswith('o sail_') and '#' in line else ('sail:' + line[2:].strip() if line.startswith('o sail_') else None)
            elif line.startswith('v ') and cur:
                x, y, z = map(float, line.split()[1:4])
                CV.append((x, z, y))
                CO.append(cur)
    ctree = cKDTree(np.array(CV)) if CV else None

    def rope_clear(C):
        best = [1e9, None]
        for nm, a, b, rad in ropes:
            if min(a[0], b[0]) - 60 > C[:, 0].max() or max(a[0], b[0]) + 60 < C[:, 0].min():
                continue
            dmin = float(DG.seg_points_dist(a, b, C).min()) - 0.5 - rad
            if dmin < best[0]:
                best = [round(dmin, 2), nm]
        return best

    def cloth_clear(C):
        if ctree is None:
            return None
        d_, i_ = ctree.query(C)
        k = int(np.argmin(d_))
        return [round(float(d_[k]), 2), CO[int(i_[k])]]
    AC = np.array(sorted({tuple(k) for _, _, P in anchors for k in P.tolist()} | set(cathead)), float) + 0.5
    atree = cKDTree(AC)
    GC = np.argwhere(gcells) + 0.5
    gtree = cKDTree(GC)
    MZ = np.array([m for _, m in muzzles])
    mtree = cKDTree(MZ)

    # ════ 槳元件（共用件，CLI export 的清單＋來源作品的固定點）════
    W_ = O['work']
    srcf = os.path.join('masks', 'oars_src', W_ + '.vox.txt')
    comp = np.loadtxt(os.path.join(HERE, srcf), delimiter=',', comments='#', dtype=np.int32, ndmin=2)
    cc = comp[:, :3].astype(float)
    A = json.load(open(os.path.join(HERE, '..', '..', W_, 'anchors.json'), encoding='utf-8'))
    A = {a['name']: np.array(a['at'], float) for a in A.get('anchors', A)}
    PIV = A['pivot'] + 0.5                                               # 元件裡的 pivot 點（那一格的中心；蠍子號同）
    yb = int(cc[:, 1].max() + 1 - round(O['blade_m'] / 0.05))             # 槳葉起點（來源作品的槳葉長；元件格 0.05 m）
    BL = cc[cc[:, 1] >= yb]
    BC = BL.mean(0) + 0.5                                                  # 槳葉中心
    col = cc[(cc[:, 1] == A['pivot'][1]) & (cc[:, 0] == A['pivot'][0])]
    loom_below = PIV[2] - col[:, 2].min()                                  # pivot 那一截槳柄：pivot 往下到槳柄底（元件格）
    loom_above = col[:, 2].max() + 1 - PIV[2]
    dy_, dz_ = BC[1] - PIV[1], PIV[2] - BC[2]
    ang0 = math.degrees(math.atan2(dz_, dy_))                              # 元件裡 pivot→槳葉中心的實際角度（往下為正）
    Lb = math.hypot(dy_, dz_) * SC                                         # 世界格
    SAMP = corners(cc)                                                     # 格心＋八角（內縮 0.2）
    CENT = cc + 0.5
    BLs = corners(BL)

    def xform(P, at, rx, mir):
        q = (np.asarray(P, float) - PIV) * SC
        if mir:
            q = q * np.array([1.0, -1.0, 1.0])
        return (Rx(rx) @ q.T).T + np.asarray(at, float)

    # 姿勢（31_drive.js oarAnim）：靜止＋每 phase_step 度
    PH = list(range(0, 360, int(O['phase_step_deg'])))

    def pose_mats(sg, stroke):
        out = [('rest', np.eye(3), 0.0, 0.0)]
        for ph in PH:
            t = math.radians(ph)
            th = -sg * stroke * math.cos(t)
            al = sg * DIP * max(0.0, -math.sin(t))
            out.append((ph, Rz(th) @ Rx(al), th, al))
        return out

    # ════ 每支槳：槳門 → pivot、傾角 ════
    ports = [p for p in json.load(open(os.path.join(HERE, 'verify_lines.json'), encoding='utf-8'))['ports'] if p['kind'] == 'oar']
    ports.sort(key=lambda p: p['x'][0])
    assert len(ports) == V(plan['oars_plan'])['per_side']
    drop = probe.get('drop')
    sk = probe.get('sink', '')
    sink_n, sink_d = (sk.split(':') + ['3'])[:2] if sk else (None, '0')
    oars = []
    for i, p in enumerate(ports, 1):
        x0, x1 = p['x']
        z0, z1 = p['z']
        xm = (x0 + x1 + 1) / 2.0
        wall = sorted(y for (x, y, z) in hull if x == (x0 + x1) // 2 and z == z0 - 1 and y > YC)   # 槳門下緣那一層的舷牆（右舷）
        y_s = (wall[0] + wall[-1] + 1) / 2.0                                # 牆厚的中間（持火號：y 在殼的最外兩格中間）
        zp = z0 + LIFT + loom_below * SC
        for side, sg in (('S', 1), ('P', -1)):
            nm = 'oar-%s%02d' % (side, i)
            if drop == nm[4:]:
                continue
            at = np.array([xm, y_s if sg > 0 else 2 * YC + 1 - y_s, zp - (float(sink_d) if sink_n == nm[4:] else 0.0)])
            need = math.degrees(math.asin(min(1.0, (at[2] - SURF) / Lb)))
            dl = round(need - ang0, 3)
            rx = -dl if sg > 0 else dl
            oars.append({'name': nm, 'i': i, 'side': side, 'sg': sg, 'port': p, 'wall_y': [wall[0], wall[-1]], 'at': at, 'tilt': dl, 'rx': rx, 'mir': sg < 0})

    # ════ 量：靜止與整個行程 ════
    def lab_hits(Q):
        i = np.floor(Q).astype(int)
        ok = np.all((i >= 0) & (i < np.array(SH)), -1)
        lab = np.full(len(Q), 255, np.uint8)
        lab[ok] = LAB[i[ok, 0], i[ok, 1], i[ok, 2]]
        by = {}
        for v, n in zip(*np.unique(lab[lab != 0], return_counts=True)):
            by['out-of-frame' if v == 255 else TAGS[v]] = int(n)
        rc = int(hit(Q, recoil_cells).sum())
        sw = int(hit(Q, sweep_cells).sum())
        if rc:
            by['recoil'] = rc
        if sw:
            by['swivel-arc'] = sw
        return by
    # ── 每一對槳的掃角：從 stroke_deg 往下每 1° 試，取第一個「整個行程撞船、砲、後座、迴旋砲 arc、錨、吊錨木、舵… 都是 0」的（兩舷都要過）──
    stroke_of, stroke_tried = {}, {}
    for i in sorted({o['i'] for o in oars}):
        pair = [o for o in oars if o['i'] == i]
        tried = []
        cands = [STROKE] if 'stroke' in probe else [float(v) for v in range(int(STROKE), int(STROKE_MIN) - 1, -1)]
        pick = cands[-1]
        for st in cands:
            worst = 0
            for o in pair:
                W0 = xform(SAMP, o['at'], o['rx'], o['mir'])
                for key, M, th, al in pose_mats(o['sg'], st)[1:]:
                    worst = max(worst, sum(lab_hits((M @ (W0 - o['at']).T).T + o['at']).values()))
            tried.append([st, worst])
            if worst == 0:
                pick = st
                break
        stroke_of[i] = pick
        stroke_tried[i] = tried
    occ_rest, occ_pose = {}, {}
    rest_cells = {}
    for o in oars:
        o['stroke'] = stroke_of[o['i']]
        W0 = xform(SAMP, o['at'], o['rx'], o['mir'])
        C0 = xform(CENT, o['at'], o['rx'], o['mir'])
        B0 = xform(BLs, o['at'], o['rx'], o['mir'])
        o['seat_w'] = xform((A['seat'] + 0.5)[None], o['at'], o['rx'], o['mir'])[0]
        o['blade_w'] = xform((A['blade'] + 0.5)[None], o['at'], o['rx'], o['mir'])[0]
        o['bc_w'] = xform(BC[None], o['at'], o['rx'], o['mir'])[0]
        poses, worst = [], {}
        rope_b, cloth_b, anc_b, gun_b, mz_b, ray_n = [1e9, None, None], [1e9, None, None], [1e9, None], [1e9, None], [1e9, None], {}
        dip_min = None
        for key, M, th, al in pose_mats(o['sg'], o['stroke']):
            Q = (M @ (W0 - o['at']).T).T + o['at']
            Cq = (M @ (C0 - o['at']).T).T + o['at']
            by = lab_hits(Q)
            n = sum(by.values())
            poses.append({'phase': key, 'theta': round(th, 2), 'alpha': round(al, 2), 'hits': n, 'by': by})
            for k_, v_ in by.items():
                worst[k_] = max(worst.get(k_, 0), v_)
            ci = set(map(tuple, np.floor(Cq).astype(int).tolist()))
            if key == 'rest':
                rest_cells[o['name']] = ci
                for k_ in ci:
                    occ_rest.setdefault(k_, set()).add(o['name'])
            else:
                for k_ in ci:
                    occ_pose.setdefault(key, {}).setdefault((o['side'], k_), set()).add(o['name'])
            rn = int(sum(RAYG[k_] for k_ in ci if all(0 <= k_[j] < SH[j] for j in range(3))))
            if rn:
                ray_n[str(key)] = rn
            r_ = rope_clear(Cq)
            if r_[0] < rope_b[0]:
                rope_b = r_ + [key]
            c_ = cloth_clear(Cq)
            if c_ and c_[0] < cloth_b[0]:
                cloth_b = c_ + [key]
            da = float(atree.query(Cq)[0].min())
            if da < anc_b[0]:
                anc_b = [round(da, 2), key]
            dg = float(gtree.query(Cq)[0].min())
            if dg < gun_b[0]:
                gun_b = [round(dg, 2), key]
            dm = float(mtree.query(Cq)[0].min())
            if dm < mz_b[0]:
                mz_b = [round(dm, 2), key]
            if key != 'rest' and abs(al) >= DIP - 1e-6:
                Bq = (M @ (B0 - o['at']).T).T + o['at']
                dip_min = round((float(Bq[:, 2].min()) - SURF) * 0.1, 3)
        o['poses'] = poses
        o['worst_by'] = worst
        o['rest_hits'] = poses[0]['hits']
        o['stroke_hits_max'] = max(p_['hits'] for p_ in poses[1:])
        o['rope'], o['cloth'], o['anchor_cathead'], o['gun_cells'], o['muzzle'], o['ray_cells'] = rope_b, cloth_b, anc_b, gun_b, mz_b, ray_n
        o['blade_center_minus_water_m'] = round((o['bc_w'][2] - SURF) * 0.1, 3)
        o['blade_low_minus_water_m'] = round((float(B0[:, 2].min()) - SURF) * 0.1, 3)
        o['blade_top_minus_water_m'] = round((float(B0[:, 2].max()) - SURF) * 0.1, 3)
        o['blade_low_at_full_dip_m'] = dip_min
        o['pivot_above_water_m'] = round((o['at'][2] - SURF) * 0.1, 3)
        # 槳門：洞那幾格（下緣到上緣、舷牆厚那幾欄）在全船實心裡要是空的；槳的格心有穿過洞
        sg = o['sg']
        wy = o['wall_y'] if sg > 0 else [2 * YC - o['wall_y'][1], 2 * YC - o['wall_y'][0]]
        hole = [(x, y, z) for x in range(o['port']['x'][0], o['port']['x'][1] + 1) for y in range(wy[0], wy[1] + 1) for z in range(o['port']['z'][0], o['port']['z'][1] + 1)]
        o['hole_cells'] = len(hole)
        o['hole_not_empty'] = [list(k) for k in hole if LAB[k]]
        o['oar_cells_in_hole'] = sum(1 for k in rest_cells[o['name']] if k in set(hole))
        ip = np.floor(o['at']).astype(int)
        o['hull_cells_r8'] = int(np.isin(LAB[ip[0] - 8:ip[0] + 9, ip[1] - 8:ip[1] + 9, ip[2] - 8:ip[2] + 9], [TAGS.index('hull')]).sum())   # 遊戲把槳掛在 pivot 旁 8 格內的船格
    rest_overlap = sorted({'+'.join(sorted(v)) for v in occ_rest.values() if len(v) > 1})
    pose_overlap = sorted({'%s:%s' % (k, '+'.join(sorted(v))) for k, d_ in occ_pose.items() for v in d_.values() if len(v) > 1})[:10]
    mirror_diff = 0
    for o in oars:
        if o['side'] == 'S':
            q = 'oar-P' + o['name'][5:]
            if q in rest_cells:
                mirror_diff += len({(x, 2 * YC - y, z) for (x, y, z) in rest_cells[o['name']]} ^ rest_cells[q])

    # ════ 槳手（遊戲 40_crew.js oarCrew；砲班先排）════
    def gridget(x, y, z):
        return 0 <= x < SH[0] and 0 <= y < SH[1] and 0 <= z < SH[2] and bool(STAND[x, y, z])

    def standZ(x, y, za, zb, head=HEAD):
        for z in range(zb, za - 1, -1):
            if not gridget(x, y, z - 1) or gridget(x, y, z):
                continue
            if any(gridget(x, y, z + h) for h in range(1, head)):
                continue
            return z
        return -1
    VG = json.load(open(os.path.join(HERE, 'verify_gear.json'), encoding='utf-8'))
    keg_boxes = [(np.array(k[0]), np.array(k[1])) for h_ in VG['hoist'].values() for k in h_['kegs_box']]
    tl = (np.array(sorted(til), float).min(0), np.array(sorted(til), float).max(0) + 1)
    boxes = ([(a, b_) for _, a, b_ in gun_box] + [(np.array(m['bbox'][0]), np.array(m['bbox'][1])) for m in gear if m['host'] != 'magazine' and m['meta'].get('kind') != 'door']
             + keg_boxes + [tl] + [(np.array(a['bbox'][0]), np.array(a['bbox'][1])) for a in HP['anchors']])
    rud_arr = np.array(sorted(rud), float)

    def blocked(x, y, z):
        for lo, hi in boxes:
            if math.floor(lo[0]) - 1 <= x <= math.ceil(hi[0]) + 1 and math.floor(lo[1]) - 1 <= y <= math.ceil(hi[1]) + 1 and lo[2] - 3 <= z <= hi[2]:
                return True
        sl = rud_arr[(rud_arr[:, 2] >= z) & (rud_arr[:, 2] <= z + CREW_SLAB)]      # 舵（比 20 格高）只看腳到頭那一段
        return bool(len(sl) and sl[:, 0].min() - 1 <= x <= sl[:, 0].max() + 1 and sl[:, 1].min() - 1 <= y <= sl[:, 1].max() + 1)
    taken = {(int(math.floor(a[0])), int(math.floor(a[1]))) for _, _, a in crew_spots}
    crew_xy = set(taken)
    for o in oars:
        pv, bl, s0 = o['at'], o['blade_w'], o['seat_w']
        dx, dy = pv[0] - bl[0], pv[1] - bl[1]
        dl = math.hypot(dx, dy) or 1.0
        dx, dy = dx / dl, dy / dl
        za, zb = int(math.floor(min(s0[2], pv[2]))) - 14, int(math.floor(max(s0[2], pv[2]))) + 2
        rw = []
        for k in range(NROW):
            tx, ty = int(math.floor(s0[0] + dx * 6 * k)), int(math.floor(s0[1] + dy * 6 * k))
            got = None
            for rr in range(0, 7):
                for ddy in range(-rr, rr + 1):
                    for ddx in range(-rr, rr + 1):
                        if got or max(abs(ddx), abs(ddy)) != rr or (tx + ddx, ty + ddy) in taken:
                            continue
                        z = standZ(tx + ddx, ty + ddy, za, zb)
                        if z >= 0 and not blocked(tx + ddx, ty + ddy, z):
                            got = (tx + ddx, ty + ddy, z)
                if got:
                    break
            if got:
                taken.add(got[:2])
                rw.append({'at': [got[0] + 0.5, got[1] + 0.5, got[2]], 'target': [tx, ty], 'moved': max(abs(got[0] - tx), abs(got[1] - ty)), 'dy': round(abs(got[1] + 0.5 - (YC + 0.5)), 1),
                           'under': TAGS[int(LAB[got[0], got[1], got[2] - 1])]})
        o['rowers'] = rw

    # ── 走路格（遊戲 42_hands.js navBuild；draft_helm.py 同一套：x0 ＝ 外框 hx0 − 4（奇數）、每 2 格、甲板 meta floor −2～+3、頭上 12 格、8 鄰、高差 ≤ 3）──
    DM = {}
    for line in open(os.path.join(HERE, 'decks_meta.tsv'), encoding='utf-8'):
        f_ = line.rstrip('\n').split('\t')
        if len(f_) >= 3 and f_[0] == 'link':
            m_ = json.loads(f_[2])
            if m_.get('kind') == 'deck':
                DM[m_['deck']] = DG.poly(m_['floor'])
    awn = load('masks/deco/awning.vox.txt')
    hx0 = int(min(np.argwhere(LAB.any(axis=(1, 2)))[0][0], min(k[0] for k in awn)))   # draft_helm.py 同（外框起點）

    def nav(dk, x0):
        Fp = DM[dk]
        NC = DG.NAV_C
        Z = {}
        for x in range(x0 + NC, int(Fp[-1][0]) + NC + 1, NC):
            if x < Fp[0][0] - 0.5:
                continue
            f = DG.polyZ(Fp, x)
            if f is None:
                continue
            for y in range(NC, AY - NC, NC):
                z = -1
                for zz in range(f + 3, f - 3, -1):
                    if STAND[x, y, zz - 1] and not STAND[x, y, zz:zz + DG.NAV_HEAD].any():
                        z = zz
                        break
                if z < 0 or blocked(x, y, z):
                    continue
                Z[(x, y)] = z
        comp_, sizes = {}, []
        for k in sorted(Z):
            if k in comp_:
                continue
            cid = len(sizes)
            comp_[k] = cid
            q, n_ = [k], 0
            while q:
                a = q.pop()
                n_ += 1
                for ex, ey in ((1, 0), (-1, 0), (0, 1), (0, -1), (1, 1), (1, -1), (-1, 1), (-1, -1)):
                    b2 = (a[0] + ex * NC, a[1] + ey * NC)
                    if b2 not in Z or b2 in comp_ or abs(Z[b2] - Z[a]) > DG.NAV_DZ:
                        continue
                    if ex and ey and ((a[0] + ex * NC, a[1]) not in Z or (a[0], a[1] + ey * NC) not in Z):
                        continue
                    comp_[b2] = cid
                    q.append(b2)
            sizes.append(n_)
        return Z, comp_, sizes, (int(np.argmax(sizes)) if sizes else -1)

    def in_main(p, Z, c, big, x0):
        NC = DG.NAV_C
        k = (x0 + int(round((p[0] - x0) / NC)) * NC, int(round(p[1] / NC)) * NC)
        cands = [(k[0] + ex, k[1] + ey) for ex in (0, -NC, NC) for ey in (0, -NC, NC)]
        return any(c.get(q) == big for q in cands if q in Z and abs(Z[q] - p[2]) <= DG.NAV_DZ)
    LP = json.load(open(os.path.join(HERE, 'ladder_points.json'), encoding='utf-8'))
    lad_pts = [(nm, pk, p_) for nm, L_ in sorted(LP.items()) for pk, p_ in sorted(L_['points'].items())] + \
              [('hoist:' + path.rsplit('/', 1)[1], 'head_stand', h_['head_stand']) for path, h_ in sorted(VG['hoist'].items()) if h_.get('head_stand')]
    lanes = [(path.rsplit('/', 1)[1], h_['lane']) for path, h_ in sorted(VG['hoist'].items()) if h_.get('lane')]
    gear_chk = [(m['name'], np.array(m['bbox'][0]), np.array(m['bbox'][1])) for m in gear if m['host'] == 'main']
    # 送藥手（23_powder.js makeMonkeys）：每一對砲（同一層、同一個砲口 x）一個，站 (round(砲口 x), CY ± 9) 旁 4 格內；放藥位置 ＝ 砲尾往船裡 7 格（gunDropAt）
    pairs = {}
    for r in gun_rows:
        mz = dict(muzzles)[r['name']]
        pairs.setdefault((r['deck'], int(round(mz[0]))), []).append(r)
    MK = O['monkey']
    monkey_t = []
    for i_, (k_, rs) in enumerate(pairs.items()):
        x = k_[1]
        r0 = rs[0]
        g = gun_t[r0['type']]
        mir = r0['side'] == 'P'
        ax = g.axis(r0['phi'], mir)
        if abs(ax[0]) > abs(ax[1]):
            br = g.world(g.anchors['breech'][None], r0['at'], r0['phi'], mir)[0]
            x = int(round(br[0] - (6 if ax[0] > 0 else -6)))
        monkey_t.append((k_[0], x, YC + (MK['dy'] if i_ % 2 else -MK['dy'])))
    drops = []
    for r in gun_rows:
        g = gun_t[r['type']]
        mir = r['side'] == 'P'
        br = g.world(g.anchors['breech'][None], r['at'], r['phi'], mir)[0]
        ax = g.axis(r['phi'], mir)
        if abs(ax[0]) > abs(ax[1]):
            drops.append((r['name'], int(math.floor(br[0] - (1 if ax[0] > 0 else -1) * 7)), int(math.floor(br[1]))))
        else:
            drops.append((r['name'], int(math.floor(br[0])) + 3, int(math.floor(br[1] - (1 if r['side'] == 'S' else -1) * 7))))
    navr = {}
    for par, x0 in (('odd_game', hx0 - 4), ('even', (hx0 - 4) // 2 * 2)):
        Z, c, s, b = nav('main', x0)
        navr[par] = {'x0': x0, 'main_points': s[b] if s else 0, 'groups_ge12': sum(1 for v in s if v >= 12),
                     'rowers_not_in_main': [[o['name'], r_['at']] for o in oars for r_ in o['rowers'] if not in_main(r_['at'], Z, c, b, x0)]}
    MF = DM['main']
    LC = O['ladder_clear']
    rchk = {'not_on_main_deck': [], 'near_ladder_or_hoist': [], 'in_hoist_lane': [], 'in_gear_box': [], 'in_monkey_ring': [], 'on_gun_drop': [], 'on_gun_crew': []}
    dmin_crew = [1e9, None]
    for o in oars:
        for r_ in o['rowers']:
            x, y, z = int(math.floor(r_['at'][0])), int(math.floor(r_['at'][1])), int(r_['at'][2])
            fz = DG.polyZ(MF, x)
            if r_['under'] != 'deck' or fz is None or not fz - 2 <= z <= fz + 3:
                rchk['not_on_main_deck'].append([o['name'], r_['at'], r_['under'], fz])
            for nm, pk, p_ in lad_pts:
                if abs(p_[2] - z) <= 3 and max(abs(p_[0] - x), abs(p_[1] - y)) < LC:
                    rchk['near_ladder_or_hoist'].append([o['name'], nm, pk])
            for nm, ln in lanes:
                if ln[0] <= x <= ln[2] and ln[1] <= y <= ln[3]:
                    rchk['in_hoist_lane'].append([o['name'], nm])
            for nm, lo, hi in gear_chk:
                if math.floor(lo[0]) - 1 <= x <= math.ceil(hi[0]) + 1 and math.floor(lo[1]) - 1 <= y <= math.ceil(hi[1]) + 1 and lo[2] - 3 <= z <= hi[2]:
                    rchk['in_gear_box'].append([o['name'], nm])
            for dk, mx, my in monkey_t:
                if dk == 'main' and max(abs(mx - x), abs(my - y)) <= MK['r']:
                    rchk['in_monkey_ring'].append([o['name'], [mx, my]])
            for gn, dx_, dy_2 in drops:
                if (dx_, dy_2) == (x, y):
                    rchk['on_gun_drop'].append([o['name'], gn])
            if (x, y) in crew_xy:
                rchk['on_gun_crew'].append(o['name'])
            for gn, dk, a in crew_spots:
                if dk == 'main':
                    d_ = math.hypot(a[0] - r_['at'][0], a[1] - r_['at'][1])
                    if d_ < dmin_crew[0]:
                        dmin_crew = [round(d_, 2), o['name'], gn]

    # ════ 讀數 ════
    R = {'probe': probe or None}
    R['component'] = {'work': W_, 'src_list': srcf, 'src_sha256': hashlib.sha256(open(os.path.join(HERE, srcf), 'rb').read()).hexdigest(), 'cells': int(len(comp)),
                      'size_cells': [int(v) for v in (cc.max(0) + 1)], 'anchors': {k: [int(c) for c in v] for k, v in A.items()},
                      'length_m': round((cc[:, 1].max() + 1) * 0.05, 2), 'inboard_m': round(PIV[1] * 0.05, 2), 'outboard_m': round((cc[:, 1].max() + 1 - PIV[1]) * 0.05, 2),
                      'blade_rows_from_y': yb, 'blade_m': round((cc[:, 1].max() + 1 - yb) * 0.05, 2), 'blade_center': r3(BC), 'angle_pivot_to_blade_center_deg': round(ang0, 3),
                      'pivot_to_blade_center_world_cells': round(Lb, 3), 'loom_below_pivot_world': round(loom_below * SC, 3), 'loom_above_pivot_world': round(loom_above * SC, 3)}
    R['stroke_search'] = {'max': STROKE, 'min': STROKE_MIN, 'chosen': {str(i): v for i, v in stroke_of.items()}, 'tried_first_hit': {str(i): t[:-1][-1:] if len(t) > 1 else [] for i, t in stroke_tried.items()},
                          'tried': {str(i): t for i, t in stroke_tried.items()}}
    R['params'] = {'stroke_deg_max': STROKE, 'dip_deg': DIP, 'rowers': NROW, 'pivot_lift': LIFT, 'scale': SC, 'surface_z': SURF, 'phase_step_deg': O['phase_step_deg'], 'poses': len(PH) + 1}
    R['read'] = {'labels': {TAGS[v]: int(n) for v, n in zip(*np.unique(LAB[LAB != 0], return_counts=True))}, 'recoil_cells': int(recoil_cells.sum()), 'swivel_sweep_cells': int(sweep_cells.sum()),
                 'ray_cells': int(RAYG.sum()), 'crew_spots': len(crew_spots), 'cloth_files': cloth_files, 'ropes': len(ropes), 'hx0': hx0}
    R['per_side'] = {s: sum(1 for o in oars if o['side'] == s) for s in 'SP'}
    R['rest'] = {'hits_total': sum(o['rest_hits'] for o in oars), 'oar_oar_overlap': rest_overlap, 'mirror_diff_cells': mirror_diff}
    R['stroke'] = {'hits_max': max(o['stroke_hits_max'] for o in oars), 'by_tag_worst': {}, 'oar_oar_overlap_same_side': pose_overlap,
                   'nonzero': [[o['name'], p_['phase'], p_['theta'], p_['alpha'], p_['by']] for o in oars for p_ in o['poses'][1:] if p_['hits']][:20]}
    for o in oars:
        for k_, v_ in o['worst_by'].items():
            R['stroke']['by_tag_worst'][k_] = max(R['stroke']['by_tag_worst'].get(k_, 0), v_)
    R['hole'] = {'cells_each': sorted({o['hole_cells'] for o in oars}), 'not_empty': [[o['name'], o['hole_not_empty'][:3]] for o in oars if o['hole_not_empty']],
                 'oar_cells_in_hole_min': min(o['oar_cells_in_hole'] for o in oars)}
    R['clearance'] = {'rope_min': min((o['rope'] + [o['name']] for o in oars), key=lambda v: v[0]),
                      'cloth_min': min((o['cloth'] + [o['name']] for o in oars if o['cloth'][1]), key=lambda v: v[0], default=None),
                      'anchor_cathead_min': min((o['anchor_cathead'] + [o['name']] for o in oars), key=lambda v: v[0]),
                      'gun_cells_min': min((o['gun_cells'] + [o['name']] for o in oars), key=lambda v: v[0]),
                      'muzzle_min': min((o['muzzle'] + [o['name']] for o in oars), key=lambda v: v[0]),
                      'gun_ray_cells': {o['name']: o['ray_cells'] for o in oars if o['ray_cells']}}
    R['water'] = {'pivot_above_water_m': [min(o['pivot_above_water_m'] for o in oars), max(o['pivot_above_water_m'] for o in oars)],
                  'blade_center_minus_water_m': [min(o['blade_center_minus_water_m'] for o in oars), max(o['blade_center_minus_water_m'] for o in oars)],
                  'blade_low_minus_water_m_rest': [min(o['blade_low_minus_water_m'] for o in oars), max(o['blade_low_minus_water_m'] for o in oars)],
                  'blade_top_minus_water_m_rest': [min(o['blade_top_minus_water_m'] for o in oars), max(o['blade_top_minus_water_m'] for o in oars)],
                  'blade_low_minus_water_m_full_dip': [min(o['blade_low_at_full_dip_m'] for o in oars), max(o['blade_low_at_full_dip_m'] for o in oars)],
                  'tilt_deg': [min(o['tilt'] for o in oars), max(o['tilt'] for o in oars)],
                  'entry_angle_deg': [round(ang0 + min(o['tilt'] for o in oars), 2), round(ang0 + max(o['tilt'] for o in oars), 2)]}
    R['hang'] = {'hull_cells_r8_min': min(o['hull_cells_r8'] for o in oars)}
    want = NROW * len(oars)
    R['rowers'] = {'want': want, 'placed': sum(len(o['rowers']) for o in oars), 'moved_max': max((r_['moved'] for o in oars for r_ in o['rowers']), default=None),
                   'dy_range': [min((r_['dy'] for o in oars for r_ in o['rowers']), default=None), max((r_['dy'] for o in oars for r_ in o['rowers']), default=None)],
                   'z': sorted({r_['at'][2] for o in oars for r_ in o['rowers']}), 'checks': rchk, 'nearest_gun_crew': dmin_crew, 'nav_main': navr,
                   'monkey_targets': [[dk, x, y] for dk, x, y in monkey_t if dk == 'main']}
    R['problems'] = (R['rest']['hits_total'] + R['stroke']['hits_max'] + len(rest_overlap) + len(pose_overlap) + mirror_diff + (R['per_side']['S'] != R['per_side']['P'])
                     + len(R['hole']['not_empty']) + (R['hole']['oar_cells_in_hole_min'] == 0) + (R['hang']['hull_cells_r8_min'] == 0)
                     + (R['clearance']['rope_min'][0] < O['rope_min']) + bool(R['clearance']['cloth_min'] and R['clearance']['cloth_min'][0] < O['cloth_min'])
                     + sum(1 for o in oars if abs(o['blade_center_minus_water_m']) > O['blade_tol_m'])
                     + (R['rowers']['placed'] != want) + sum(len(v) for v in rchk.values()) + len(navr['odd_game']['rowers_not_in_main']) + max(0, navr['odd_game']['groups_ge12'] - 1))
    if probe:
        print(json.dumps({'probe': probe, 'problems': R['problems'], 'per_side': R['per_side'], 'rest_hits': {o['name']: o['poses'][0]['by'] for o in oars if o['rest_hits']},
                          'stroke_hits_max': R['stroke']['hits_max'], 'stroke_chosen': R['stroke_search']['chosen'], 'stroke_by_tag_worst': R['stroke']['by_tag_worst'], 'stroke_worst_by_oar': {o['name']: o['worst_by'] for o in oars if o['worst_by']},
                          'rowers': {k: R['rowers'][k] for k in ('want', 'placed', 'moved_max', 'dy_range')}, 'rower_checks': {k: v for k, v in rchk.items() if v},
                          'nav_rowers_not_in_main': navr['odd_game']['rowers_not_in_main'][:6], 'water': R['water'], 'clearance': {k: R['clearance'][k] for k in ('rope_min', 'gun_cells_min', 'muzzle_min')}},
                         ensure_ascii=False, default=str))
        return
    R['oars'] = {o['name']: {'port_x': o['port']['x'], 'port_z': o['port']['z'], 'wall_y': o['wall_y'], 'at': r3(o['at']), 'tilt_deg': o['tilt'], 'rotate_x': round(o['rx'], 3),
                             'rest_hits': o['rest_hits'], 'stroke_hits_max': o['stroke_hits_max'], 'worst_by': o['worst_by'], 'pivot_above_water_m': o['pivot_above_water_m'],
                             'blade_center_minus_water_m': o['blade_center_minus_water_m'], 'blade_low_minus_water_m': o['blade_low_minus_water_m'], 'blade_low_at_full_dip_m': o['blade_low_at_full_dip_m'],
                             'seat_world': r3(o['seat_w']), 'blade_world': r3(o['blade_w']), 'rowers': o['rowers'], 'hole_cells': o['hole_cells'], 'oar_cells_in_hole': o['oar_cells_in_hole'],
                             'hull_cells_r8': o['hull_cells_r8'], 'rope': o['rope'], 'cloth': o['cloth'], 'anchor_cathead': o['anchor_cathead'], 'gun_cells': o['gun_cells'], 'muzzle': o['muzzle'],
                             'gun_ray_cells': o['ray_cells']} for o in oars}

    # ════ 輸出 ════
    od = os.path.join(HERE, 'masks', 'oars')
    os.makedirs(od, exist_ok=True)
    lists = {}
    col_ = {tuple(k): int(c) for k, c in zip(comp[:, :3].tolist(), comp[:, 3].tolist())}
    rest_vox = {}
    for o in oars:
        C0 = np.floor(xform(CENT, o['at'], o['rx'], o['mir'])).astype(int)
        for k, src_k in zip(map(tuple, C0.tolist()), map(tuple, comp[:, :3].tolist())):
            rest_vox.setdefault(k, col_[src_k])
    p = os.path.join(od, 'oars_rest.vox.txt')
    with open(p, 'w', encoding='utf-8', newline='\n') as f:
        f.write('# 利劍號 18 支槳靜止時的世界格（元件格心 floor；只給 verifier 對照，⛔ 不落格 —— 槳是外部模型；draft_oars.py）\n')
        for (x, y, z), c in sorted(rest_vox.items()):
            f.write('%d,%d,%d,%d\n' % (x, y, z, c))
    lists['masks/oars/oars_rest.vox.txt'] = [len(rest_vox), hashlib.sha256(open(p, 'rb').read()).hexdigest()]
    meta = lambda o: {'kind': 'oar', 'rowers': NROW, 'side': o['side'], 'stroke_deg': int(o['stroke']) if o['stroke'] == int(o['stroke']) else o['stroke'], 'dip_deg': int(DIP) if DIP == int(DIP) else DIP}
    place = {'note': 'draft_oars.py 的結果：外部模型掛在 host 作品裡（船殼的框 ⇒ 世界座標）；at ＝ pivot 的落點、pivot ＝ 元件 pivot 那一格的中心；右舷原樣、左舷 mirror=y（先翻再轉）、rotate x 補到槳葉中心落在水面',
             'host': O['host'], 'component': {'work': W_, 'anchors': {k: [int(c) for c in v] for k, v in A.items()}, 'src_sha256': R['component']['src_sha256']},
             'models': [{'name': o['name'], 'work': W_, 'at': r3(o['at']), 'pivot': r3(PIV), 'scale': SC, 'rotate': [round(o['rx'], 3), 0, 0], 'mirror': 'y' if o['mir'] else '',
                         'meta': meta(o)} for o in sorted(oars, key=lambda o: (o['side'] != 'S', o['i']))]}
    with open(os.path.join(HERE, 'oars_placement.json'), 'w', encoding='utf-8', newline='\n') as f:
        json.dump(place, f, ensure_ascii=False, indent=1)
    lists['oars_placement.json'] = [len(place['models']), hashlib.sha256(open(os.path.join(HERE, 'oars_placement.json'), 'rb').read()).hexdigest()]
    sheet(plan, LAB, oars, xform, CENT, gun_box, crew_spots, R, YC, SURF, STROKE, monkey_t)
    lists['sheet10_oars_v1.png'] = [None, hashlib.sha256(open(os.path.join(HERE, 'sheet10_oars_v1.png'), 'rb').read()).hexdigest()]
    R['lists'] = lists
    with open(os.path.join(HERE, 'verify_oars.json'), 'w', encoding='utf-8', newline='\n') as f:
        json.dump(R, f, ensure_ascii=False, indent=1, default=lambda v: v.item() if hasattr(v, 'item') else str(v))
    short = {k: R[k] for k in ('per_side', 'rest', 'hole', 'water', 'hang', 'problems')}
    short['stroke'] = {k: R['stroke'][k] for k in ('hits_max', 'by_tag_worst', 'oar_oar_overlap_same_side')}
    short['clearance'] = {k: v for k, v in R['clearance'].items()}
    short['rowers'] = {k: R['rowers'][k] for k in ('want', 'placed', 'moved_max', 'dy_range', 'z', 'nearest_gun_crew')}
    short['rowers']['checks'] = {k: len(v) for k, v in rchk.items()}
    short['rowers']['nav'] = {p_: {k: v[k] if k != 'rowers_not_in_main' else len(v[k]) for k in v} for p_, v in navr.items()}
    print(json.dumps(short, ensure_ascii=False, default=str))
    print(json.dumps(lists, ensure_ascii=False))


def sheet(plan, LAB, oars, xform, CENT, gun_box, crew_spots, R, YC, SURF, STROKE, monkey_t):
    """圖紙 10：(a) 右舷俯視 x 140–370（主甲板高度那一層的船殼、6l 砲外框、砲手、槳靜止與掃到 ±stroke、槳手、送藥手那一圈）；
    (b) oar-S05 那一欄的橫剖面（船殼、槳靜止與抬到 dip、水面、槳手）。"""
    try:
        f = ImageFont.truetype('/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf', 14)
    except OSError:
        f = ImageFont.load_default()
    s = 5
    W_, H_ = 240 * s + 80, 110 * s + 90 * s + 160
    im = Image.new('RGB', (W_, H_), (250, 248, 242))
    d = ImageDraw.Draw(im)
    d.text((20, 10), '%s - new sheet 10: oars through the oar ports (TASK-0022 step 13; draft_oars.py)' % plan['title_en'], fill=(0, 0, 0), font=f)
    ox, oy = 40, 50
    x0, x1, y0, y1 = 140, 380, YC, YC + 110
    hullT, deckT = 1, 2
    zl = 47
    for x in range(x0, x1):
        for y in range(y0, y1):
            v = int(LAB[x, y, zl])
            if v:
                d.rectangle([ox + (x - x0) * s, oy + (y1 - 1 - y) * s, ox + (x - x0) * s + s - 1, oy + (y1 - 1 - y) * s + s - 1], fill=(150, 150, 150) if v == hullT else (200, 190, 170))
    for nm, lo, hi in gun_box:
        if lo[1] > YC and lo[0] < x1 and hi[0] > x0 and lo[2] < 60:
            d.rectangle([ox + (lo[0] - x0) * s, oy + (y1 - hi[1]) * s, ox + (hi[0] - x0) * s, oy + (y1 - lo[1]) * s], outline=(170, 40, 40), width=2)
    for nm, dk, a in crew_spots:
        if dk == 'main' and a[1] > YC and x0 <= a[0] < x1:
            d.ellipse([ox + (a[0] - x0) * s - 4, oy + (y1 - a[1]) * s - 4, ox + (a[0] - x0) * s + 4, oy + (y1 - a[1]) * s + 4], fill=(170, 40, 40))
    for dk, mx, my in monkey_t:
        if dk == 'main' and my > YC and x0 <= mx < x1:
            d.rectangle([ox + (mx - 4 - x0) * s, oy + (y1 - my - 5) * s, ox + (mx + 5 - x0) * s, oy + (y1 - my + 4) * s], outline=(120, 60, 160), width=1)
    for o in oars:
        if o['side'] != 'S':
            continue
        C0 = xform(CENT, o['at'], o['rx'], o['mir'])
        for th, colr in ((-o['stroke'], (190, 170, 120)), (o['stroke'], (190, 170, 120)), (0.0, (110, 70, 20))):
            Q = (Rz(th) @ (C0 - o['at']).T).T + o['at']
            for q in Q[::3]:
                if x0 <= q[0] < x1 and y0 <= q[1] < y1:
                    d.point((ox + (q[0] - x0) * s, oy + (y1 - q[1]) * s), fill=colr)
        for r_ in o['rowers']:
            a = r_['at']
            d.ellipse([ox + (a[0] - x0) * s - 4, oy + (y1 - a[1]) * s - 4, ox + (a[0] - x0) * s + 4, oy + (y1 - a[1]) * s + 4], fill=(30, 130, 40))
        d.text((ox + (o['at'][0] - x0) * s - 12, oy + (y1 - y0) * s + 4), o['name'][4:], fill=(0, 0, 0), font=f)
    d.text((ox, oy + (y1 - y0) * s + 24), '(a) starboard, plan at z %d: hull grey, 6l boxes red, gun crew red dots, rowers green, oars at rest brown / at +-stroke (per oar) light, monkey ring purple' % zl, fill=(0, 0, 0), font=f)
    # (b) 橫剖面
    o = next(o for o in oars if o['name'] == 'oar-S05')
    xc = int(math.floor(o['at'][0]))
    oy2 = oy + (y1 - y0) * s + 60
    za, zb, ya, yb = 10, 100, YC - 10, YC + 130
    s2 = 5
    for y in range(ya, yb):
        for z in range(za, zb):
            v = int(LAB[xc, y, z])
            if v:
                d.rectangle([ox + (y - ya) * s2, oy2 + (zb - 1 - z) * s2, ox + (y - ya) * s2 + s2 - 1, oy2 + (zb - 1 - z) * s2 + s2 - 1], fill=(150, 150, 150) if v == hullT else (200, 190, 170))
    C0 = xform(CENT, o['at'], o['rx'], o['mir'])
    for al, colr in ((12.0, (190, 170, 120)), (0.0, (110, 70, 20))):
        Q = (Rx(al) @ (C0 - o['at']).T).T + o['at']
        for q in Q:
            d.point((ox + (q[1] - ya) * s2, oy2 + (zb - q[2]) * s2), fill=colr)
    d.line([ox, oy2 + (zb - SURF) * s2, ox + (yb - ya) * s2, oy2 + (zb - SURF) * s2], fill=(60, 120, 220), width=1)
    for r_ in o['rowers']:
        a = r_['at']
        d.rectangle([ox + (a[1] - ya) * s2 - 2, oy2 + (zb - a[2] - 14) * s2, ox + (a[1] - ya) * s2 + 2, oy2 + (zb - a[2]) * s2], outline=(30, 130, 40), width=2)
    d.text((ox, oy2 + (zb - za) * s2 + 6), '(b) section at x %d (oar-S05): oar at rest / lifted %g deg, water line blue, rowers green (14 cells tall)' % (xc, 12), fill=(0, 0, 0), font=f)
    d.text((ox, oy2 + (zb - za) * s2 + 26), 'oars %s  rowers %d/%d  rest hits %d  stroke hits max %d  blade centre - water %s m  problems %d' % (
        R['per_side'], R['rowers']['placed'], R['rowers']['want'], R['rest']['hits_total'], R['stroke']['hits_max'], [float(v) for v in R['water']['blade_center_minus_water_m']], R['problems']), fill=(0, 0, 0), font=f)
    im.save(os.path.join(HERE, 'sheet10_oars_v1.png'))


if __name__ == '__main__':
    main()
