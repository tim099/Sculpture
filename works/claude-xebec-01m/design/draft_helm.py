# 利劍號 新圖紙 09（TASK-0022 步驟 11）：舵（艉柱舵）、舵柄、兩隻錨、吊錨木 ⇒ masks/helm/{rudder,tiller,cathead,platform_carve}.vox.txt、helm_placement.json、verify_helm.json、sheet09_helm_v1.png
#   出處：蠍子號 claude-galiot-01m/design/draft_helm.py（舵、舵柄各一件整船框的子作品、模型 at ＝ pivot ＝ 鉸鏈點；鉸鏈取「每一層都在艉柱後面 gap 格以上」
#         的支撐直線、總縫最小；舵 meta kind=rudder＋hinge／axis＋spin、舵柄 kind=tiller＋spin_pivot／spin_axis 跟舵同一條軸；錨環頂掛在吊錨木底下、往舷外推到零碰撞）
#         ＋ 星辰號 claude-baghlah-01m/design/draft_helm.py（舵頭穿過去的那一件：刻掉舵頭轉一圈掃過的格；錨的位置用搜尋、每一個試過的都記下來；讀數每 1°）
#         ＋ 本船 draft_gear.py（實心照前面每一步的設計清單、模型、砲／後座／迴旋砲 arc、遊戲砲手站位、走路格、hoist 梯頭、繩、帆布）。
#   改的地方：
#     · 舵形：Chapman No.17 側視沒有畫舵（艉柱外緣那條線後面只有 AP 垂線，船底線停在艉柱腳 px 644、兩條線之間沒有封閉輪廓）⇒ 舵葉寬照 Navarro 1749 的 jabeque
#       （下段寬、上段窄，中間一段收）；舵厚照 Chapman 船尾視圖 D 中線那一條（23 px）。
#     · 這艘的船尾平台從艉柱頭往後伸、平台板在艉柱後面 z 64–68：舵頭要升到船尾頂（z 75）以上舵柄才伸得到後甲板 ⇒ 舵頭穿過平台前緣，
#       刻掉舵頭（±max_deg 每 1°）掃到的平台格（masks/helm/platform_carve.vox.txt；落格時 carvevox 進船尾平台子作品）。
#     · 舵柄長度用搜尋：從 tip_search 最長往短試，取第一個「每 5° 掃不碰實心／模型、離繩 ≥ rope_min、離帆布 ≥ cloth_min、離砲手 ≥ crew_clear_min、
#       遊戲舵手站得到（40_crew.js helmGripOf＋standNear 重寫）」的。
#     · 錨：憲法號 bower × scale，S／P 一對（P ＝ y 鏡像），錨環頂掛在吊錨木（stampvox 進主甲板子作品）底下；x 從 x_try 前往後試，取第一個兩舷都過的：
#       碰船／模型 0、錨冠在水線上 ≥ crown_wl_min_m、不擋砲的射線（加農砲一條、迴旋砲 arc 每 5°）、不碰後座與迴旋砲掃過的格、離繩 ≥ rope_min、
#       離帆布 ≥ cloth_min、在最後一個槳門 ＋ oar_pad 的前面。船殼固定點 hawse-S／P 在錨那一欄、主甲板面 ＋ hawse_dz 那一層船殼最外一格。
#     · 走路格照遊戲 42_hands.js navBuild：x0 ＝ 外框 hx0 − 4（奇數）、每 2 格一點、甲板 meta floor −2～+3、頭上 12 格、8 鄰、高差 ≤ 3；另報偶數 x0 對照。
#   用法：python -I -X utf8 draft_helm.py [--probe=gap=<格>] [--probe=nocarve=1] [--probe=tip=<x>] [--probe=anchor_dy=<格>] [--probe=anchor_x=<x>] [--probe=anchor_scale=<s>] [--probe=binnacle=<x>,<y>]
#     反向對照不寫檔：縫改小（舵要撞艉柱）；不刻平台（舵頭要撞平台）；舵柄指定長度（太長要撞砲手／砲）；錨往船裡推（要撞船）；指定錨的 x、換錨的 scale；
#     羅經櫃試別的位置（看撞、走路格、舵手看不看得到）。
import sys, os, json, math, hashlib
from collections import deque
import numpy as np
from scipy import ndimage
from scipy.spatial import cKDTree
from PIL import Image, ImageDraw, ImageFont

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import lines as HL
import draft_guns as DG
from draft_gear import Model, corners, hit, mark, grid_of, box_cells
from draft_lines import palette_rgb

V = HL.V
TAGS = ['air', 'hull', 'deck', 'ladder', 'beak', 'platform', 'glass', 'mast', 'gun-post', 'magazine', 'awning', 'yard', 'gun', 'gear', 'cathead']
CREW_TALL, CREW_SLAB = 20, 14       # 遊戲 40_crew.js：比 20 格高的模型只看腳到頭那 14 格


def load(fn):
    a = np.loadtxt(os.path.join(HERE, fn), delimiter=',', comments='#', dtype=np.int32, ndmin=2)
    return {(int(x), int(y), int(z)): int(c) for x, y, z, c in a}


def r3(v):
    return [round(float(c), 3) for c in v]


def rodrigues(P, origin, axis, deg):
    """點 P 繞過 origin、方向 axis（單位）的軸轉 deg 度（右手定則）。"""
    k = np.asarray(axis, float)
    t = math.radians(deg)
    v = np.asarray(P, float) - origin
    c, s = math.cos(t), math.sin(t)
    return origin + v * c + np.cross(k, v) * s + np.outer(v @ k, k) * (1 - c)


class Anchor(Model):
    """CLI 外部模型＋mirror=y（先在 pivot 那裡翻 y，再轉）。"""

    def __init__(s, cells, pivot, scale, rot, mirror):
        s.mirror = mirror
        Model.__init__(s, cells, pivot, scale, rot)

    def world(s, P, at):
        q = (np.asarray(P, float) - s.pivot) * s.scale
        if s.mirror:
            q = q * np.array([1.0, -1.0, 1.0])
        c, sn = math.cos(math.radians(s.rot)), math.sin(math.radians(s.rot))
        return np.stack([q[..., 0] * c - q[..., 1] * sn + at[0], q[..., 0] * sn + q[..., 1] * c + at[1], q[..., 2] + at[2]], -1)


def main():
    sys.stdout.reconfigure(encoding='utf-8')
    probe = dict(a[len('--probe='):].split('=', 1) for a in sys.argv[1:] if a.startswith('--probe='))
    plan = HL.load_plan(HERE)
    YC = int(plan['space']['yc'])
    AX, AY, AZ = [int(v) for v in plan['space']['assembly']]
    SH = (AX, AY, AZ)
    WL = int(plan['waterline']['z'])
    HB = plan['helm']
    RU, TI, AN, CV_ = HB['rudder'], HB['tiller'], HB['anchor'], HB['carve']
    GBG = {k: V(v) for k, v in plan['guns_build'].items() if not k.endswith('src')}
    ROPE_MIN = GBG['rope_min_cells']

    # ── 步驟 11 以前的實心（設計清單；跟 draft_gear.py 同一份＋步驟 10 的彈藥庫）：每一格記它是哪一件 ──
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
    platform = load('masks/deco/platform.vox.txt')
    put('platform', platform)
    put('glass', load('masks/deco/glass.vox.txt'))
    for m in ('mizzen', 'main', 'fore'):
        put('mast', load('masks/masts/%s.vox.txt' % m))
    put('gun-post', set(load('masks/guns/posts_main.vox.txt')) | set(load('masks/guns/posts_quarter.vox.txt')))
    put('magazine', load('masks/gear/magazine.vox.txt'))
    put('hull', hull)
    awning = set(load('masks/deco/awning.vox.txt'))
    put('awning', awning)
    yardw = set()
    for p in json.load(open(os.path.join(HERE, 'yards_placement.json'), encoding='utf-8')):
        off = [int(round(p['at'][i] - p['pivot'][i])) for i in range(3)]
        yardw |= {(x + off[0], y + off[1], z + off[2]) for (x, y, z) in load('masks/yards/lateen-%s.vox.txt' % p['mast'])}
    put('yard', yardw)
    STAND_TAGS = [TAGS.index(t) for t in ('hull', 'deck', 'ladder', 'beak', 'platform', 'glass', 'mast', 'gun-post', 'magazine')]

    # ── 砲（格、外框、後座、迴旋砲 arc 掃過的格、砲手站位；draft_gear.py 同一套）──
    gun_t = {k: DG.Gun(k, t, GBG['search']['inset']) for k, t in GBG['types'].items()}
    gun_rows = [r for r in json.load(open(os.path.join(HERE, 'guns_placement.json'), encoding='utf-8'))['rows'] if r.get('at') is not None]
    recoil_cells = np.zeros(SH, bool)
    sweep_cells = np.zeros(SH, bool)
    gun_box, crew_spots = [], []
    RC = GBG['recoil']
    gcells = np.zeros(SH, bool)
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
    LAB[gcells & (LAB == 0)] = TAGS.index('gun')
    recoil_cells &= ~gcells
    sweep_cells &= ~gcells

    def gun_rays():
        """每一門砲的射線（加農砲一條、迴旋砲 arc 每 sweep_step_deg 一條；draft_guns.py ray 的取樣：砲口起每 0.25 格）。"""
        out = []
        for r in gun_rows:
            g = gun_t[r['type']]
            mir = r['side'] == 'P'
            angs = [r['phi']]
            far = GBG['ray_len']
            if r['swivel'] and r.get('arc'):
                a0, a1 = [int(v) for v in r['arc'].split(',')]
                angs = list(range(a0, a1 + 1, GBG['sweep_step_deg']))
                far = 40.0
            for a in angs:
                mz = g.world(g.anchors['muzzle'][None], r['at'], float(a), mir)[0]
                d = g.axis(float(a), mir)
                t = np.arange(0.5, far + 1e-9, 0.25)
                out.append((r['name'], a, mz[None] + t[:, None] * d[None]))
        return out
    RAYS = gun_rays()

    # ── 步驟 10 的甲板物件（模型的格）──
    GP = json.load(open(os.path.join(HERE, 'gear_placement.json'), encoding='utf-8'))
    src_cache = {}

    def gsrc(w):
        if w not in src_cache:
            src_cache[w] = np.loadtxt(os.path.join(HERE, 'masks', 'gear_src', w + '.vox.txt'), delimiter=',', comments='#', dtype=np.int32, ndmin=2)[:, :3].astype(float)
        return src_cache[w]
    gear = []
    for m in GP['models']:
        g = Model(gsrc(m['work']), m['pivot'], m['scale'], m['rotate'])
        gear.append((m, g))
        if m['host'] == 'magazine':
            continue
        P = np.floor(g.world(g.centers, m['at'])).astype(int)
        sel = LAB[P[:, 0], P[:, 1], P[:, 2]] == 0
        LAB[P[sel, 0], P[sel, 1], P[sel, 2]] = TAGS.index('gear')
    binn = next(((m, g) for m, g in gear if m['meta'].get('kind') == 'binnacle'), None)

    # ── 繩（步驟 8 的直線）、帆布（步驟 8 export 的 obj 頂點）──
    RE = json.load(open(os.path.join(HERE, 'verify_rigging.json'), encoding='utf-8'))['rope_ends']
    RT = {r_['name']: r_['thickness'] for r_ in json.load(open(os.path.join(HERE, 'rig_plan.json'), encoding='utf-8'))['ropes']}
    ropes = [(nm, np.array(e['from'], float), np.array(e['to'], float), RT.get(nm, 0.5) / 2.0) for nm, e in sorted(RE.items())]

    def rope_clear(C):
        best = [1e9, None]
        for nm, a, b, rad in ropes:
            if min(a[0], b[0]) - 40 > C[:, 0].max() or max(a[0], b[0]) + 40 < C[:, 0].min():
                continue
            dmin = float(DG.seg_points_dist(a, b, C).min()) - 0.5 - rad
            if dmin < best[0]:
                best = [round(dmin, 2), nm]
        return best
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
                cur = 'sail:' + line.split('#', 1)[1].strip() if line.startswith('o sail_') and '#' in line else ('sail:' + line[2:].strip() if line.startswith('o sail_') else None)
            elif line.startswith('v ') and cur:
                x, y, z = map(float, line.split()[1:4])
                CV.append((x, z, y))
                CO.append(cur)
    ctree = cKDTree(np.array(CV)) if CV else None

    def cloth_clear(P):
        if ctree is None:
            return None
        d_, i_ = ctree.query(P)
        k = int(np.argmin(d_))
        return [round(float(d_[k]), 2), CO[int(i_[k])]]

    # ════ 舵 ════
    gap = RU['gap']['v'] + float(probe.get('gap', 0))
    aft = {}
    for (x, y, z) in hull:
        if y == YC:
            aft[z] = min(aft.get(z, 999), x)
    z0 = RU['z0']['v']
    fz0, fz1 = RU['fit_z']['v']
    best = None
    for k in range(0, 2001):
        bb = -2.0 + k * 0.001
        a0 = min(aft[z] - gap - bb * (z + 0.5) for z in range(fz0, fz1 + 1))
        tot = sum(aft[z] - gap - (a0 + bb * (z + 0.5)) for z in range(fz0, fz1 + 1))
        if best is None or tot < best[0] - 1e-9:
            best = (tot, bb, a0)
    _, b, a0 = best

    def Lx(z):
        return a0 + b * (z + 0.5)
    axis = np.array([b, 0.0, 1.0])
    axis = axis / np.linalg.norm(axis)
    hinge = np.array([Lx(z0 - 1) + b * 0.5, YC + 0.5, float(z0)])          # 最低那層底面的鉸鏈點
    CH, TH, CO_ = RU['chord']['v'], RU['thick']['v'], RU['colors']['v']
    zt = TI['zt']['v']
    ztop = zt + 1                                                         # 舵頭頂 ＝ 舵柄上面那一層（舵柄穿過舵頭）
    straps = set(RU['straps']['v'])

    def chord(z):
        if z >= CH['head_from']:
            return CH['head']
        if z <= CH['low_top']:
            return CH['low']
        if z >= CH['up_from']:
            return CH['up']
        return CH['low'] + (CH['up'] - CH['low']) * (z - CH['low_top']) / float(CH['up_from'] - CH['low_top'])
    rud = {}
    for z in range(z0, ztop + 1):
        lz = Lx(z)
        ch = chord(z)
        for x in range(int(math.floor(lz - ch)), int(math.floor(lz)) + 1):
            if not lz - ch <= x + 0.5 < lz:                                # 格心在 [鉸鏈 − 弦長, 鉸鏈) 裡
                continue
            fwd = x + 1 > lz - TH['fwd_cols']                                  # 靠鉸鏈那幾欄 3 格厚，後緣那一段 1 格（收薄）
            for dy in (range(-TH['half'], TH['half'] + 1) if fwd or z >= CH['head_from'] else (0,)):
                c = CO_['head'] if z >= CH['head_from'] else (CO_['below'] if z <= WL else CO_['above'])
                if z in straps and fwd:
                    c = CO_['iron']
                rud[(x, YC + dy, z)] = c
    top_layer = sorted(k for k in rud if k[2] == ztop and k[1] == YC)
    stock_top = top_layer[-1]                                             # 舵頭頂、最靠船頭那一格

    # ── 舵頭穿過船尾平台：刻掉舵（±max_deg 每 1°，格心＋八角內縮 0.2）掃到的平台格 ──
    MD = RU['max_deg']['v']
    ARC1 = list(range(-MD, MD + 1, 1))
    ARC5 = list(range(-MD, MD + 1, 5))
    Prud = corners(np.array(sorted(rud), float))
    carve = {}
    if not probe.get('nocarve'):
        for a in ARC1:
            Q = np.floor(rodrigues(Prud, hinge, axis, a)).astype(int)
            for q in set(map(tuple, Q.tolist())):
                if q in platform:
                    carve[q] = platform[q]
    for k in carve:
        LAB[k] = 0
    plat_left = {k: c for k, c in platform.items() if k not in carve}

    def sweep(cells, angs, extra=None):
        """cells 繞鉸鏈轉，每個角度：取樣點落在哪幾種實心（照 LAB）、後座、迴旋砲掃過的格、extra（新放的東西）。"""
        P = corners(np.array(sorted(cells), float))
        out = []
        for a in angs:
            Q = rodrigues(P, hinge, axis, a)
            i = np.floor(Q).astype(int)
            ok = np.all((i >= 0) & (i < np.array(SH)), -1)
            lab = np.full(len(Q), 255, np.uint8)
            lab[ok] = LAB[i[ok, 0], i[ok, 1], i[ok, 2]]
            by = {}
            for v, n in zip(*np.unique(lab[lab != 0], return_counts=True)):
                by['out-of-frame' if v == 255 else TAGS[v]] = int(n)
            rc = int(hit(Q, recoil_cells).sum())
            sc = int(hit(Q, sweep_cells).sum())
            if rc:
                by['recoil'] = rc
            if sc:
                by['swivel-arc'] = sc
            if extra is not None:
                e = int(hit(Q, extra).sum())
                if e:
                    by['new'] = e
            out.append({'deg': a, 'hits': sum(by.values()), 'by': by})
        return out

    # ════ 舵柄：搜長度 ════
    x_head = stock_top[0] + 1                                            # 舵柄從舵頭的船頭面起
    hdr = TI['deep_cells']['v']

    def tiller_cells(tip):
        til = {}
        mid = x_head + int((tip - x_head) * TI['wide_frac']['v'])
        for x in range(x_head, tip + 1):
            ys = range(-1, 2) if x <= mid else (0,)
            c = TI['colors']['v']['grip'] if x > tip - TI['grip']['v'] else TI['colors']['v']['wood']
            for dy in ys:
                til[(x, YC + dy, zt)] = c
                if x < x_head + hdr:
                    til[(x, YC + dy, zt + 1)] = c
        head_aft = min(k[0] for k in rud if k[2] == zt and k[1] == YC)
        til[(head_aft - 1, YC, zt)] = TI['colors']['v']['wood']            # 舵柄穿過舵頭（榫眼），舵頭後面露 1 格
        return {k: c for k, c in til.items() if k not in rud}

    # 遊戲站位用的格子（navBase：船的格；外部模型不算）＋站位要避開的模型（40_crew.js CREW_BLOCK：每一種 kind 預設都擋；門、艙蓋是通道）
    STAND = np.isin(LAB, STAND_TAGS)
    hx0 = int(min(np.argwhere(LAB.any(axis=(1, 2)))[0][0], min(k[0] for k in awning)))

    def gridget(G, x, y, z):
        return 0 <= x < SH[0] and 0 <= y < SH[1] and 0 <= z < SH[2] and bool(G[x, y, z])

    def standZ(G, x, y, za, zb, head):
        for z in range(zb, za - 1, -1):
            if not gridget(G, x, y, z - 1) or gridget(G, x, y, z):
                continue
            if any(gridget(G, x, y, z + h) for h in range(1, head)):
                continue
            return z
        return -1
    block_boxes = [(a, b_) for n_, a, b_ in gun_box] + [(np.array(m['bbox'][0]), np.array(m['bbox'][1])) for m, g in gear
                                                         if m['host'] != 'magazine' and m['meta'].get('kind') != 'door']

    def blocked(x, y, z, boxes):
        for lo, hi in boxes:
            if math.floor(lo[0]) - 1 <= x <= math.ceil(hi[0]) + 1 and math.floor(lo[1]) - 1 <= y <= math.ceil(hi[1]) + 1 and lo[2] - 3 <= z <= hi[2]:
                return True
        return False

    def bbox_of(cells, ext=1):
        a = np.array(sorted(cells), float)
        return a.min(0), a.max(0) + ext

    def helmsman(til, extra_boxes):
        """40_crew.js helmGripOf ①（獨立舵柄 kind=tiller）：握把 ＝ [floor(外框 x1), cy, 外框 z1]、z0 ＝ floor(外框 z0) − 12、z1 ＝ ceil(外框 z1)；
        舵手站握把往前 2 格（standNear：半徑 4 一圈一圈找、頭上 14 格、不在模型外框擋的地方、不跟砲手同一欄）。"""
        lo, hi = bbox_of(til)
        grip = [int(math.floor(hi[0])), YC, float(hi[2])]
        za, zb = int(math.floor(lo[2])) - 12, int(math.ceil(hi[2]))
        taken = {(int(math.floor(a[0])), int(math.floor(a[1]))) for _, _, a in crew_spots}
        boxes = block_boxes + extra_boxes
        x0_, y0_ = grip[0] + 2, grip[1]
        for rr in range(0, 5):
            for dy in range(-rr, rr + 1):
                for dx in range(-rr, rr + 1):
                    if max(abs(dx), abs(dy)) != rr or (x0_ + dx, y0_ + dy) in taken:
                        continue
                    z = standZ(STAND, x0_ + dx, y0_ + dy, za, zb, 14)
                    if z >= 0 and not blocked(x0_ + dx, y0_ + dy, z, boxes):
                        return {'grip': grip, 'z_range': [za, zb], 'spot': [x0_ + dx + 0.5, y0_ + dy + 0.5, z], 'ring': rr}
        return {'grip': grip, 'z_range': [za, zb], 'spot': None}

    def tiller_eval(tip):
        til = tiller_cells(tip)
        sw = sweep(til, ARC5)
        C = np.array(sorted(til), float) + 0.5
        rc, cl, crew_min = [1e9, None], [1e9, None], [1e9, None]
        tops = []
        for a in ARC5:
            Q = rodrigues(C, hinge, axis, a)
            r_ = rope_clear(Q)
            if r_[0] < rc[0]:
                rc = r_ + [a]
            c_ = cloth_clear(Q)
            if c_ and c_[0] < cl[0]:
                cl = c_ + [a]
            tops.append(Q)
        Qa = np.concatenate(tops)
        zlo, zhi = Qa[:, 2].min() - 0.5, Qa[:, 2].max() + 0.5
        for gn, dk, s in crew_spots:                                       # 砲手的身體（腳 z 到 z ＋14）跟舵柄掃過的高度重疊 ⇒ 量水平距離
            if s[2] <= zhi and s[2] + 14 >= zlo:
                d = float(np.hypot(Qa[:, 0] - s[0], Qa[:, 1] - s[1]).min())
                if d < crew_min[0]:
                    crew_min = [round(d, 2), gn, s]
        hm = helmsman(til, [])
        return til, {'tip': tip, 'sweep_hits': sum(s['hits'] for s in sw), 'sweep_first': [s for s in sw if s['hits']][:2], 'rope_clear': rc,
                     'cloth_clear': cl if cl[1] else None, 'crew_clear': crew_min if crew_min[1] else None, 'helmsman': hm}

    def tiller_ok(e):
        return (e['sweep_hits'] == 0 and e['rope_clear'][0] >= ROPE_MIN and (e['cloth_clear'] is None or e['cloth_clear'][0] >= TI['cloth_min']['v'])
                and (e['crew_clear'] is None or e['crew_clear'][0] >= TI['crew_clear_min']['v']) and e['helmsman']['spot'] is not None)
    t_hi, t_lo = TI['tip_search']['v']
    tried = []
    tip_list = [int(probe['tip'])] if 'tip' in probe else list(range(t_hi, t_lo - 1, -1))
    til = te = None
    for tip in tip_list:
        til_, e = tiller_eval(tip)
        tried.append([tip, e['sweep_hits'], e['rope_clear'][0], e['cloth_clear'][0] if e['cloth_clear'] else None,
                      e['crew_clear'][0] if e['crew_clear'] else None, e['crew_clear'][1] if e['crew_clear'] else None, e['helmsman']['spot'] is not None])
        if tiller_ok(e) or 'tip' in probe:
            til, te = til_, e
            break
    if til is None and probe.get('tiller_debug'):
        print(json.dumps({'tried': tried, 'last': e}, ensure_ascii=False, default=str))
        return
    if til is None:
        raise SystemExit('✗ 舵柄搜不到合格的長度：%s' % json.dumps(tried[:12], ensure_ascii=False))
    tip = te['tip']
    tiller_end = (tip, YC, zt)

    # ════ 錨 ════
    asrc = np.loadtxt(os.path.join(HERE, 'masks', 'helm_src', AN['work'] + '.vox.txt'), delimiter=',', comments='#', dtype=np.int32, ndmin=2)[:, :3].astype(float)
    SC, PV, ROT = float(probe.get('anchor_scale', AN['scale']['v'])), AN['pivot']['v'], AN['rotate']['v']
    A_S = Anchor(asrc, PV, SC, ROT, False)
    A_P = Anchor(asrc, PV, SC, -ROT, True)
    oars = [p for p in json.load(open(os.path.join(HERE, 'verify_lines.json'), encoding='utf-8'))['ports'] if p['kind'] == 'oar']
    oar_x1 = max(p['x'][1] for p in oars)
    main_floor = DG.poly(next(json.loads(l.split('\t')[2]) for l in open(os.path.join(HERE, 'decks_meta.tsv'), encoding='utf-8')
                              if l.startswith('link\t') and '"deck":"main"' in l)['floor'])
    OBJ = (LAB != 0) | gcells

    def hang(x, side, g, cat_dy=0):
        """x 那一欄 side 舷：舷頂最外一格 rail、吊錨木（rail 往裡 1 格起、往外到錨環外 1 格；x−half..x+half、rail 頂上 h 格）、錨環頂往外推到零碰撞。"""
        col = [k for k in hull if k[0] == x and (k[1] - YC) * side > 0]
        top = max(k[2] for k in col)
        rail = max((k for k in col if k[2] == top), key=lambda k: abs(k[1] - YC))
        CA = AN['cathead']['v']
        for off in np.arange(1.0, AN['off_max']['v'] + 1e-9, 0.5):
            ring_y = rail[1] + 0.5 + side * off
            at = (x + 0.5, ring_y, float(top + 1))
            if hit(g.world(g.samples, at), OBJ).any():
                continue
            at = (x + 0.5, ring_y - side * float(probe.get('anchor_dy', 0)), float(top + 1))   # 反向對照：找到之後再往船裡推
            ye = int(math.floor(ring_y)) + side * 1
            cat = {}
            for xx in range(x - CA['half_x'], x + CA['half_x'] + 1):
                for yy in range(min(rail[1] - side, ye), max(rail[1] - side, ye) + 1):
                    for zz in range(top + 1, top + 1 + CA['h']):
                        if not OBJ[xx, yy, zz]:
                            cat[(xx, yy, zz)] = CA['color']
            return {'x': x, 'side': side, 'rail': list(rail), 'off': float(off), 'at': at, 'cat': cat}
        return None

    def anchor_eval(h, g):
        at = h['at']
        P = g.world(g.samples, at)
        C = g.world(g.centers, at)
        cat = np.array(sorted(h['cat']), float) + 0.5 if h['cat'] else np.zeros((0, 3))
        catG = np.zeros(SH, bool)
        for k in h['cat']:
            catG[k] = True
        cells = set(map(tuple, np.floor(C).astype(int).tolist())) | set(h['cat'])
        ray_hits = []
        for gn, a, Q in RAYS:
            i = np.floor(Q).astype(int)
            n = sum(1 for q in map(tuple, i.tolist()) if q in cells)
            if n:
                ray_hits.append([gn, a, n])
        lo, hi = g.bbox(at)
        allC = np.concatenate([C, cat])
        hz = DG.polyZ(main_floor, h['x']) + AN['hawse_dz']['v']
        hc = [k for k in hull if k[0] == h['x'] and k[2] == hz and (k[1] - YC) * h['side'] > 0]
        hawse = max(hc, key=lambda k: abs(k[1] - YC)) if hc else None
        e = {'x': h['x'], 'at': r3(at), 'off_rail_cells': h['off'], 'rail_cell': h['rail'], 'hits_solid_or_model': int(hit(P, OBJ).sum()),
             'hits_recoil': int(hit(P, recoil_cells).sum()), 'hits_swivel_arc': int(hit(P, sweep_cells).sum()) + int(sum(sweep_cells[k] or recoil_cells[k] for k in h['cat'])),
             'cathead_cells': len(h['cat']), 'cathead_on_rail': all(OBJ[k[0], k[1], k[2] - 1] for k in h['cat'] if (k[1] - h['rail'][1]) * h['side'] <= 0 and k[2] == h['rail'][2] + 1),
             'anchor_hits_cathead': int(hit(P, catG).sum()), 'gun_rays_blocked': ray_hits,
             'crown_z': round(float(P[:, 2].min()), 2), 'crown_above_wl_m': round((float(P[:, 2].min()) - (WL + 1)) * 0.1, 2),
             'height_m': round(float(P[:, 2].max() - P[:, 2].min()) * 0.1, 2), 'bbox': [r3(lo), r3(hi)],
             'rope_clear': rope_clear(allC), 'cloth_clear': cloth_clear(allC), 'oar_port_x1': oar_x1, 'aft_end_minus_oar': round(float(lo[0]) - oar_x1, 2),
             'hawse': list(hawse) if hawse else None}
        e['ok'] = bool(e['hits_solid_or_model'] == 0 and e['hits_recoil'] == 0 and e['hits_swivel_arc'] == 0 and e['anchor_hits_cathead'] == 0 and not ray_hits
                       and e['cathead_on_rail'] and e['crown_above_wl_m'] >= AN['crown_wl_min_m']['v'] and e['rope_clear'][0] >= ROPE_MIN
                       and (e['cloth_clear'] is None or e['cloth_clear'][0] >= TI['cloth_min']['v']) and e['aft_end_minus_oar'] >= AN['oar_pad']['v'] and hawse is not None)
        return e
    xs_try = [int(probe['anchor_x'])] if 'anchor_x' in probe else list(range(AN['x_try']['v'][0], AN['x_try']['v'][1] - 1, AN['x_try']['v'][2]))
    atried, achosen = [], None
    for x in xs_try:
        hS, hP = hang(x, 1, A_S), hang(x, -1, A_P)
        if not hS or not hP:
            atried.append([x, 'no-offset'])
            continue
        eS, eP = anchor_eval(hS, A_S), anchor_eval(hP, A_P)
        why = []
        for e in (eS, eP):
            for k, bad in (('solid', e['hits_solid_or_model']), ('recoil', e['hits_recoil']), ('swivel-arc', e['hits_swivel_arc']), ('rays', len(e['gun_rays_blocked'])),
                           ('crown', e['crown_above_wl_m'] < AN['crown_wl_min_m']['v']), ('rope', e['rope_clear'][0] < ROPE_MIN),
                           ('cloth', e['cloth_clear'] is not None and e['cloth_clear'][0] < TI['cloth_min']['v']), ('oar', e['aft_end_minus_oar'] < AN['oar_pad']['v'])):
                if bad:
                    why.append('%s:%s' % ('S' if e is eS else 'P', k))
        atried.append([x, eS['off_rail_cells'], eP['off_rail_cells'], eS['crown_above_wl_m'], eP['crown_above_wl_m'], why[:6]])
        if eS['ok'] and eP['ok']:
            achosen = (hS, hP, eS, eP)
            break
    if achosen is None and probe:
        print(json.dumps({'probe': probe, 'tiller': te, 'tiller_tried': tried, 'anchor_tried': atried}, ensure_ascii=False, default=str))
        return
    if achosen is None:
        raise SystemExit('✗ 錨找不到位置：%s' % json.dumps(atried, ensure_ascii=False))
    hS, hP, eS, eP = achosen
    cathead = dict(hS['cat'])
    cathead.update(hP['cat'])
    hawse = {'hawse-S': eS['hawse'], 'hawse-P': eP['hawse']}

    # ════ 讀數 ════
    R = {'probe': probe or None, 'read': {'labels': {TAGS[v]: int(n) for v, n in zip(*np.unique(LAB[LAB != 0], return_counts=True))},
                                           'recoil_cells': int(recoil_cells.sum()), 'swivel_sweep_cells': int(sweep_cells.sum()), 'gun_rays': len(RAYS),
                                           'crew_spots': len(crew_spots), 'cloth_files': cloth_files, 'ropes': len(ropes),
                                           'anchor_src_sha256': hashlib.sha256(open(os.path.join(HERE, 'masks', 'helm_src', AN['work'] + '.vox.txt'), 'rb').read()).hexdigest()[:16]}}
    gaps = {z: round(aft[z] - Lx(z), 2) for z in range(fz0, fz1 + 1)}
    R['hinge'] = {'hinge': r3(hinge), 'axis': [round(float(v), 4) for v in axis], 'rake_deg': round(math.degrees(math.atan2(-b, 1)), 1),
                  'post_aft_x_by_z': {str(z): aft[z] for z in range(fz0, fz1 + 1, 6)},
                  'gap_post_to_hinge_cells': {'min': min(gaps.values()), 'max': max(gaps.values()), 'by_z': {str(z): gaps[z] for z in range(fz0, fz1 + 1, 6)}}}
    # 新放的東西：舵柄、吊錨木、兩隻錨（舵掃的時候要避開）
    NEW = np.zeros(SH, bool)
    for k in list(til) + list(cathead):
        NEW[k] = True
    for h, g in ((hS, A_S), (hP, A_P)):
        mark(NEW, g.world(g.centers, h['at']))
    NEW_R = NEW.copy()
    for k in til:
        NEW_R[k] = False                                                   # 舵柄跟舵一起轉，不算
    rsw = sweep(rud, ARC1, NEW_R)
    plab = np.zeros(SH, np.int32)
    for k in plat_left:
        plab[k] = 1
    pcomp = ndimage.label(plab)[1]
    st = np.array(stock_top, float) + 0.5
    near = np.argwhere(STAND[int(st[0]) - 9:int(st[0]) + 10, int(st[1]) - 9:int(st[1]) + 10, int(st[2]) - 9:int(st[2]) + 10]) + np.array([int(st[0]) - 9, int(st[1]) - 9, int(st[2]) - 9])
    dd = np.abs(near - np.floor(st)).max(axis=1) if len(near) else np.array([99])
    nb = near[np.argmin(np.linalg.norm(near + 0.5 - st, axis=1))] if len(near) else None
    R['rudder'] = {'cells': len(rud), 'z': [z0, ztop], 'stock_top': list(stock_top), 'below_wl_cells': sum(1 for k in rud if k[2] <= WL),
                   'length_along_axis_m': round((ztop + 1 - z0) / float(axis[2]) * 0.1, 2),
                   'chord_by_z': {str(z): len({k[0] for k in rud if k[2] == z and k[1] == YC}) for z in (z0, 10, 20, WL, 34, CH['up_from'], 50, 62, ztop)},
                   'thick_y': [min(k[1] for k in rud) - YC, max(k[1] for k in rud) - YC],
                   'components': int(ndimage.label(grid_of(set(rud), SH))[1]), 'mirror_diff': sum(1 for (x, y, z), c in rud.items() if rud.get((x, 2 * YC - y, z)) != c),
                   'at_rest_hits': rsw[MD]['hits'], 'sweep_1deg_hits_max': max(s['hits'] for s in rsw), 'sweep_5deg': [s for s in rsw if s['deg'] in ARC5],
                   'sweep_1deg_nonzero': [s for s in rsw if s['hits']][:6]}
    Crud = np.array(sorted(rud), float) + 0.5
    rr_, rcl_ = [1e9, None], [1e9, None]
    for a in ARC5:
        Q = rodrigues(Crud, hinge, axis, a)
        r_ = rope_clear(Q)
        if r_[0] < rr_[0]:
            rr_ = r_ + [a]
        c_ = cloth_clear(Q)
        if c_ and c_[0] < rcl_[0]:
            rcl_ = c_ + [a]
    R['rudder']['rope_clear'] = rr_
    R['rudder']['cloth_clear'] = rcl_ if rcl_[1] else None
    R['stock_top_foot'] = {'game_anchorNear_r8_found': bool(len(near) and dd.min() <= 8), 'nearest': nb.tolist() if nb is not None else None,
                           'nearest_tag': TAGS[LAB[tuple(nb)]] if nb is not None else None, 'nearest_dist': round(float(np.linalg.norm(nb + 0.5 - st)), 2) if nb is not None else None}
    R['platform_carve'] = {'work': CV_['work'], 'cells': len(carve), 'x': [min(k[0] for k in carve), max(k[0] for k in carve)] if carve else None,
                           'y': [min(k[1] for k in carve), max(k[1] for k in carve)] if carve else None, 'z': [min(k[2] for k in carve), max(k[2] for k in carve)] if carve else None,
                           'platform_cells_before_after': [len(platform), len(plat_left)], 'platform_components_after': int(pcomp),
                           'mirror_diff': sum(1 for (x, y, z) in carve if (x, 2 * YC - y, z) not in carve)}
    tl = bbox_of(til)
    R['tiller'] = {'cells': len(til), 'x': [min(k[0] for k in til), max(k[0] for k in til)], 'z': [min(k[2] for k in til), max(k[2] for k in til)], 'end': list(tiller_end),
                   'length_from_axis_m': round((tip + 1 - Lx(zt)) * 0.1, 2), 'z_over_quarterdeck_floor_m': None,
                   'search_tried': tried, 'chosen': {k: te[k] for k in ('tip', 'rope_clear', 'cloth_clear', 'crew_clear')},
                   'mirror_diff': sum(1 for (x, y, z), c in til.items() if til.get((x, 2 * YC - y, z)) != c),
                   'components_with_rudder': int(ndimage.label(grid_of(set(til) | set(rud), SH))[1])}
    tsw = sweep(til, ARC1)
    R['tiller']['sweep_1deg_hits_max'] = max(s['hits'] for s in tsw)
    R['tiller']['sweep_5deg'] = [s for s in tsw if s['deg'] in ARC5]
    ends = [rodrigues(np.array([[tip + 1.0, YC + 0.5, zt + 0.5]]), hinge, axis, a)[0] for a in (-MD, 0, MD)]
    R['tiller']['end_at_-max_0_+max'] = [r3(e) for e in ends]
    QF = DG.poly(next(json.loads(l.split('\t')[2]) for l in open(os.path.join(HERE, 'decks_meta.tsv'), encoding='utf-8')
                      if l.startswith('link\t') and '"deck":"quarter"' in l)['floor'])
    R['tiller']['z_over_quarterdeck_floor_m'] = {str(x): round((zt - DG.polyZ(QF, x)) * 0.1, 2) for x in (74, 80, 88, tip) if DG.polyZ(QF, x) is not None}
    # 舵手（遊戲 40_crew.js）：加上舵、舵柄、錨的外框之後重找
    extra_boxes = [tl] + [Anchor_b for Anchor_b in ((np.array(eS['bbox'][0]), np.array(eS['bbox'][1])), (np.array(eP['bbox'][0]), np.array(eP['bbox'][1])))]
    hm = helmsman(til, extra_boxes)
    R['helmsman'] = hm
    # 羅經櫃：舵手眼睛（腳 ＋16 格）看羅經櫃頂中心，中間穿過幾格船（桅）
    def sight(spot, mg):
        m, g = mg
        lo, hi = np.array(m['bbox'][0]), np.array(m['bbox'][1])
        eye = np.array([spot[0], spot[1], spot[2] + 16.0])
        tgt = np.array([(lo[0] + hi[0]) / 2, (lo[1] + hi[1]) / 2, hi[2] + 0.5])
        t = np.linspace(0, 1, 400)[:, None]
        Q = eye + (tgt - eye) * t
        i = np.floor(Q).astype(int)
        tags = {}
        for q in set(map(tuple, i.tolist())):
            v = LAB[q]
            if v and v != TAGS.index('gear'):
                tags[TAGS[v]] = tags.get(TAGS[v], 0) + 1
        return {'eye': r3(eye), 'binnacle_top': r3(tgt), 'dist_m': round(float(np.linalg.norm(tgt[:2] - eye[:2])) * 0.1, 2), 'cells_in_between': tags}
    if hm['spot'] and binn:
        R['binnacle_sight'] = dict(sight(hm['spot'], binn), binnacle_bbox=binn[0]['bbox'])
    # 錨
    R['anchors'] = {'model': {'work': AN['work'], 'scale': SC, 'pivot': PV, 'rotate': ROT, 'shank_m': round((asrc[:, 2].max() - asrc[:, 2].min() + 1) * 0.1 * SC, 2),
                              'stock_m': round((asrc[:, 0].max() - asrc[:, 0].min() + 1) * 0.1 * SC, 2), 'arms_m': round((asrc[:, 1].max() - asrc[:, 1].min() + 1) * 0.1 * SC, 2)},
                    'tried': atried, 'S': eS, 'P': eP, 'hawse': hawse,
                    'mirror_diff_cells': len({(x, 2 * YC - y, z) for (x, y, z) in set(map(tuple, np.floor(A_S.world(A_S.centers, hS['at'])).astype(int).tolist()))}
                                             ^ set(map(tuple, np.floor(A_P.world(A_P.centers, hP['at'])).astype(int).tolist()))),
                    'cathead_mirror_diff': sum(1 for (x, y, z) in cathead if (x, 2 * YC - y, z) not in cathead),
                    'cathead_components': int(ndimage.label(grid_of(set(cathead), SH))[1])}
    for e, h, g in ((eS, hS, A_S), (eP, hP, A_P)):
        ring = g.world(np.array([[23.5, 16.5, 56.5]]) if AN['work'].endswith('constitution-01m-anchor') else np.array([PV]), h['at'])[0]
        nb2 = np.argwhere((STAND | grid_of(set(cathead), SH))[int(ring[0]) - 8:int(ring[0]) + 9, int(ring[1]) - 8:int(ring[1]) + 9, int(ring[2]) - 8:int(ring[2]) + 9])
        e['ring_world'] = r3(ring)
        lo_, hi_ = np.floor(np.array(e['bbox'][0])).astype(int) - 6, np.ceil(np.array(e['bbox'][1])).astype(int) + 6
        sub_ = np.argwhere(STAND[lo_[0]:hi_[0], lo_[1]:hi_[1], lo_[2]:hi_[2]]) + lo_
        e['nearest_ship_cells'] = round(float(cKDTree(sub_ + 0.5).query(g.world(g.centers, h['at']))[0].min()), 2) if len(sub_) else None
        e['game_ring_foot_r8'] = bool(len(nb2))
    # 彼此重疊：舵／舵柄／錨／吊錨木
    occ = {}
    for nm, cells in (('rudder', set(rud)), ('tiller', set(til)), ('cathead', set(cathead)),
                      ('anchor-S', set(map(tuple, np.floor(A_S.world(A_S.centers, hS['at'])).astype(int).tolist()))),
                      ('anchor-P', set(map(tuple, np.floor(A_P.world(A_P.centers, hP['at'])).astype(int).tolist())))):
        for k in cells:
            occ.setdefault(k, []).append(nm)
    R['overlap_new'] = sorted({'+'.join(v) for v in occ.values() if len(v) > 1})
    R['cathead_on_old_solid'] = sum(1 for k in cathead if OBJ[k])

    # ── 走路格（遊戲 42_hands.js navBuild：x0 ＝ hx0 − 4、每 2 格、甲板 meta floor −2～+3、頭上 12 格、8 鄰、高差 ≤ 3）──
    DM = {}
    for line in open(os.path.join(HERE, 'decks_meta.tsv'), encoding='utf-8'):
        f_ = line.rstrip('\n').split('\t')
        if len(f_) >= 3 and f_[0] == 'link':
            m_ = json.loads(f_[2])
            if m_.get('kind') == 'deck':
                DM[m_['deck']] = DG.poly(m_['floor'])
    VG = json.load(open(os.path.join(HERE, 'verify_gear.json'), encoding='utf-8'))
    keg_boxes = [(np.array(k[0]), np.array(k[1])) for h_ in VG['hoist'].values() for k in h_['kegs_box']]
    LP = json.load(open(os.path.join(HERE, 'ladder_points.json'), encoding='utf-8'))
    STAND_after = STAND.copy()                                             # 刻掉平台、加了吊錨木
    for k in cathead:
        STAND_after[k] = True
    STAND_before = STAND.copy()                                            # 步驟 10 結束時的船
    for k in carve:
        STAND_before[k] = True
    # 比 20 格高的模型（舵）：只擋腳到頭那一段的佔用格 ⇒ 每一層甲板照 floor 取那一段的外框
    rud_arr = np.array(sorted(rud), float)
    boxes_before = block_boxes + keg_boxes
    boxes_after_base = boxes_before + [tl, (np.array(eS['bbox'][0]), np.array(eS['bbox'][1])), (np.array(eP['bbox'][0]), np.array(eP['bbox'][1]))]

    def nav(dk, G, boxes, x0):
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
                    if G[x, y, zz - 1] and not G[x, y, zz:zz + DG.NAV_HEAD].any():
                        z = zz
                        break
                if z < 0 or blocked(x, y, z, boxes):
                    continue
                sl = rud_arr[(rud_arr[:, 2] >= z) & (rud_arr[:, 2] <= z + CREW_SLAB)] if boxes is not boxes_before else np.zeros((0, 3))
                if len(sl) and sl[:, 0].min() - 1 <= x <= sl[:, 0].max() + 2 and sl[:, 1].min() - 1 <= y <= sl[:, 1].max() + 2:
                    continue
                Z[(x, y)] = z
        comp, sizes = {}, []
        for k in sorted(Z):
            if k in comp:
                continue
            cid = len(sizes)
            comp[k] = cid
            q, n_ = [k], 0
            while q:
                a = q.pop()
                n_ += 1
                for dx, dy in ((1, 0), (-1, 0), (0, 1), (0, -1), (1, 1), (1, -1), (-1, 1), (-1, -1)):
                    b2 = (a[0] + dx * NC, a[1] + dy * NC)
                    if b2 not in Z or b2 in comp or abs(Z[b2] - Z[a]) > DG.NAV_DZ:
                        continue
                    if dx and dy and ((a[0] + dx * NC, a[1]) not in Z or (a[0], a[1] + dy * NC) not in Z):
                        continue
                    comp[b2] = cid
                    q.append(b2)
            sizes.append(n_)
        big = int(np.argmax(sizes)) if sizes else -1
        return Z, comp, sizes, big

    def in_main(p, Z, c, big, x0):
        NC = DG.NAV_C
        k = (x0 + int(round((p[0] - x0) / NC)) * NC, int(round(p[1] / NC)) * NC)
        cands = [(k[0] + dx, k[1] + dy) for dx in (0, -NC, NC) for dy in (0, -NC, NC)]
        return any(c.get(q) == big for q in cands if q in Z and abs(Z[q] - p[2]) <= DG.NAV_DZ)
    navr = {}
    for par, x0 in (('odd_game', hx0 - 4), ('even', (hx0 - 4) // 2 * 2)):
        navr[par] = {'x0': x0}
        for dk in sorted(DM):
            Z0, c0, s0, b0 = nav(dk, STAND_before, boxes_before, x0)
            Z1, c1, s1, b1 = nav(dk, STAND_after, boxes_after_base, x0)
            crew_out = [[gn, a] for gn, d_, a in crew_spots if d_ == dk and not in_main(a, Z1, c1, b1, x0)]
            crew_out0 = [[gn, a] for gn, d_, a in crew_spots if d_ == dk and not in_main(a, Z0, c0, b0, x0)]      # 步驟 10 結束時就不在主群的（不是這一步造成的）
            lad_out = [[nm, pn] for nm, L_ in sorted(LP.items()) for pn in ('foot', 'head')
                       if (L_['lo'] if pn == 'foot' else L_['up']) == dk and not in_main(L_['points'][pn], Z1, c1, b1, x0)]
            hoist_out = [[path.rsplit('/', 1)[1]] for path, h_ in VG['hoist'].items()
                         if h_['head_stand'] and LP[path.rsplit('/', 1)[1]]['up'] == dk and not in_main(h_['head_stand'], Z1, c1, b1, x0)]
            helm_in = None
            if dk == 'quarter' and hm['spot']:
                helm_in = in_main(hm['spot'], Z1, c1, b1, x0)
            navr[par][dk] = {'points_before': len(Z0), 'main_before': s0[b0] if s0 else 0, 'points_after': len(Z1), 'main_after': s1[b1] if s1 else 0,
                             'groups_ge12_before': sum(1 for v in s0 if v >= 12), 'groups_ge12_after': sum(1 for v in s1 if v >= 12),
                             'crew_spots_not_in_main': crew_out, 'crew_spots_not_in_main_before': crew_out0, 'ladder_points_not_in_main': lad_out, 'hoist_heads_not_in_main': hoist_out, 'helmsman_in_main': helm_in}
    R['nav'] = navr
    R['hx0'] = hx0
    # 梯子點：梯腳、梯頭那一柱（站的格往上 14 格）沒有新放的格、不在新模型（舵柄、錨）的外框裡
    newG = grid_of(set(cathead) | set(til) | set(rud), SH)
    for h, g in ((hS, A_S), (hP, A_P)):
        mark(newG, g.world(g.centers, h['at']))
    R['ladder_points_blocked'] = [[nm, pk] for nm, L_ in sorted(LP.items()) for pk, p in sorted(L_['points'].items())
                                  if newG[p[0], p[1], p[2]:p[2] + 14].any() or blocked(p[0], p[1], p[2], [tl] + extra_boxes[1:])]
    # 整艘船（站人的格，刻掉平台、加了吊錨木之後）還是一塊
    R['ship_components_after'] = int(ndimage.label(STAND_after)[1])

    # ── probe：羅經櫃試別的位置（不寫檔）──
    if 'binnacle' in probe and binn:
        bx, by = [float(v) for v in probe['binnacle'].split(',')]
        m, g = binn
        tp = {}
        for (x, y, z) in decks['quarter']:
            tp[(x, y)] = max(tp.get((x, y), -1), z + 1)
        bot = g.world(g.bottom, (bx, by, 0.0))
        under = [tp[c] for c in set(map(tuple, np.floor(bot[:, :2]).astype(int).tolist())) if c in tp]
        zb = None
        OB2 = OBJ.copy()
        OB2[LAB == TAGS.index('gear')] = False                            # 甲板物件的格拿掉（原本的羅經櫃不擋它自己）
        for z in range(min(under) if under else 60, (min(under) if under else 60) + 20):
            if hit(g.world(g.samples, (bx, by, float(z))), OB2 | NEW).any():
                continue
            bl = g.world(g.bottom, (bx, by, float(z)))
            bl[:, 2] -= 0.5
            if hit(bl, OB2).any():
                zb = z
                break
        at = (bx, by, float(zb if zb is not None else 0))
        P = g.world(g.samples, at)
        lo, hi = g.bbox(at)
        Qt = np.concatenate([rodrigues(corners(np.array(sorted(til), float)), hinge, axis, a) for a in ARC5])
        mm = dict(m, at=list(at), bbox=[r3(lo), r3(hi)])
        bb_ = [b_ for b_ in block_boxes if not (abs(b_[0][0] - m['bbox'][0][0]) < 1e-6 and abs(b_[0][1] - m['bbox'][0][1]) < 1e-6)] + [(lo, hi), tl]
        Zq, cq, sq, bq = nav('quarter', STAND_after, bb_ + keg_boxes, hx0 - 4)
        hm2 = helmsman(til, [(lo, hi)] + extra_boxes[1:])
        out = {'probe': probe, 'at': r3(at), 'bbox': [r3(lo), r3(hi)], 'hits_solid_or_new': int(hit(P, OB2 | NEW).sum()), 'hits_recoil_or_arc': int(hit(P, recoil_cells | sweep_cells).sum()),
               'tiller_sweep_in_box': int(((Qt >= lo - 0.0) & (Qt <= hi)).all(-1).sum()),
               'crew_in_box': [gn for gn, dk, a in crew_spots if lo[0] - 1 <= a[0] <= hi[0] + 1 and lo[1] - 1 <= a[1] <= hi[1] + 1 and lo[2] - 3 <= a[2] <= hi[2]],
               'quarter_groups_ge12': sum(1 for v in sq if v >= 12), 'quarter_main': sq[bq] if sq else 0,
               'crew_not_in_main': [gn for gn, dk, a in crew_spots if dk == 'quarter' and not in_main(a, Zq, cq, bq, hx0 - 4)],
               'helmsman': hm2, 'sight': sight(hm2['spot'], (mm, g)) if hm2['spot'] else None, 'rope_clear': rope_clear(g.world(g.centers, at)),
               'cloth_clear': cloth_clear(g.world(g.centers, at))}
        print(json.dumps(out, ensure_ascii=False))
        return

    R['problems'] = (R['rudder']['sweep_1deg_hits_max'] + R['rudder']['components'] - 1 + R['rudder']['mirror_diff'] + R['tiller']['sweep_1deg_hits_max']
                     + (te['rope_clear'][0] < ROPE_MIN) + bool(te['crew_clear'] and te['crew_clear'][0] < TI['crew_clear_min']['v'])
                     + bool(te['cloth_clear'] and te['cloth_clear'][0] < TI['cloth_min']['v'])
                     + (R['hinge']['gap_post_to_hinge_cells']['min'] < gap - 1e-6) + (not R['stock_top_foot']['game_anchorNear_r8_found'])
                     + (R['platform_carve']['platform_components_after'] != 1) + R['platform_carve']['mirror_diff'] + (hm['spot'] is None)
                     + sum(0 if e['ok'] else 1 for e in (eS, eP)) + sum(0 if e['game_ring_foot_r8'] else 1 for e in (eS, eP))
                     + R['anchors']['mirror_diff_cells'] + R['anchors']['cathead_mirror_diff'] + len(R['overlap_new']) + R['cathead_on_old_solid']
                     + (R['rudder']['rope_clear'][0] < ROPE_MIN) + bool(R['rudder']['cloth_clear'] and R['rudder']['cloth_clear'][0] < TI['cloth_min']['v'])
                     + len(R['ladder_points_blocked']) + (R['ship_components_after'] != 1) + (R['tiller']['components_with_rudder'] != 1)
                     + sum(len([c for c in v['crew_spots_not_in_main'] if c not in v['crew_spots_not_in_main_before']]) + len(v['ladder_points_not_in_main']) + len(v['hoist_heads_not_in_main']) + max(0, v['groups_ge12_after'] - 1)
                           + (v['helmsman_in_main'] is False) for v in navr['odd_game'].values() if isinstance(v, dict)))
    if probe:
        print(json.dumps({'probe': probe, 'problems': R['problems'], 'hinge': R['hinge'], 'rudder_sweep_nonzero': R['rudder']['sweep_1deg_nonzero'],
                          'carve_cells': len(carve), 'tiller': {k: R['tiller'][k] for k in ('end', 'length_from_axis_m', 'chosen', 'sweep_1deg_hits_max')},
                          'tiller_sweep_nonzero': [s for s in tsw if s['hits']][:4], 'helmsman': hm,
                          'anchors': {'tried': atried[-4:], 'S': {k: eS[k] for k in ('x', 'at', 'hits_solid_or_model', 'crown_above_wl_m', 'gun_rays_blocked', 'ok')},
                                      'P': {k: eP[k] for k in ('x', 'at', 'hits_solid_or_model', 'crown_above_wl_m', 'gun_rays_blocked', 'ok')}}}, ensure_ascii=False))
        return

    # ════ 輸出 ════
    od = os.path.join(HERE, 'masks', 'helm')
    os.makedirs(od, exist_ok=True)
    lists = {}

    def write(nm, part, title):
        p = os.path.join(od, nm + '.vox.txt')
        with open(p, 'w', encoding='utf-8', newline='\n') as f:
            f.write('# 利劍號 %s（世界座標、at 0,0,0；draft_helm.py）\n' % title)
            for (x, y, z), c in sorted(part.items()):
                f.write('%d,%d,%d,%d\n' % (x, y, z, c))
        lists['masks/helm/' + nm + '.vox.txt'] = [len(part), hashlib.sha256(open(p, 'rb').read()).hexdigest()]
    write('rudder', rud, '舵（舵葉＋舵頭；子作品 %s、外部模型 kind=rudder）' % RU['work'])
    write('tiller', til, '舵柄（子作品 %s、外部模型 kind=tiller）' % TI['work'])
    write('cathead', cathead, '吊錨木（兩舷；stampvox 進 %s）' % AN['cathead_work'])
    write('platform_carve', carve, '船尾平台要刻掉的格（舵頭穿過去；carvevox 進 %s）' % CV_['work'])
    hz = {'hinge_x': round(float(hinge[0]), 4), 'hinge_y': round(float(hinge[1]), 4), 'hinge_z': round(float(hinge[2]), 4),
          'axis_x': round(float(axis[0]), 4), 'axis_y': 0.0, 'axis_z': round(float(axis[2]), 4)}
    spin = {'spin': 'rudder', 'spin_k': MD, 'spin_min': -MD, 'spin_max': MD, 'spin_lag': 0.3}
    P_ = r3(hinge)
    place = {'note': 'draft_helm.py 的結果（世界座標；子作品都用船殼的框、at 0,0,0 ⇒ 模型 at ＝ pivot ＝ 鉸鏈點）',
             'rudder': {'work': RU['work'], 'title': RU['title'], 'model': RU['model'], 'host': HB['assembly'], 'at': P_, 'pivot': P_, 'scale': 1,
                        'anchors': {'stock-top': list(stock_top)}, 'meta': dict({'kind': 'rudder', 'max_deg': MD, 'turn_axis': 'hinge'}, **hz, **spin),
                        'list': 'helm/rudder'},
             'tiller': {'work': TI['work'], 'title': TI['title'], 'model': TI['model'], 'host': HB['assembly'], 'at': P_, 'pivot': P_, 'scale': 1,
                        'anchors': {'tiller-end': list(tiller_end)},
                        'meta': dict({'kind': 'tiller', 'spin_pivot_x': hz['hinge_x'], 'spin_pivot_y': hz['hinge_y'], 'spin_pivot_z': hz['hinge_z'],
                                      'spin_axis_x': hz['axis_x'], 'spin_axis_y': 0.0, 'spin_axis_z': hz['axis_z']}, **spin), 'list': 'helm/tiller'},
             'anchors': [{'name': '錨-S', 'host': AN['host'], 'host_work': AN['cathead_work'], 'work': AN['work'], 'at': eS['at'], 'pivot': PV, 'scale': SC, 'rotate': [0, 0, ROT], 'mirror': '',
                          'meta': dict(AN['meta']['v']), 'bbox': eS['bbox']},
                         {'name': '錨-P', 'host': AN['host'], 'host_work': AN['cathead_work'], 'work': AN['work'], 'at': eP['at'], 'pivot': PV, 'scale': SC, 'rotate': [0, 0, -ROT], 'mirror': 'y',
                          'meta': dict(AN['meta']['v']), 'bbox': eP['bbox']}],
             'hull_anchors': {'work': HB['hull_work'], 'points': hawse},
             'cathead': {'work': AN['cathead_work'], 'list': 'helm/cathead', 'cells': len(cathead)},
             'carve': {'work': CV_['work'], 'list': 'helm/platform_carve', 'cells': len(carve)}}
    with open(os.path.join(HERE, 'helm_placement.json'), 'w', encoding='utf-8', newline='\n') as f:
        json.dump(place, f, ensure_ascii=False, indent=1)
    lists['helm_placement.json'] = [None, hashlib.sha256(open(os.path.join(HERE, 'helm_placement.json'), 'rb').read()).hexdigest()]
    R['lists'] = lists
    with open(os.path.join(HERE, 'verify_helm.json'), 'w', encoding='utf-8', newline='\n') as f:
        json.dump(R, f, ensure_ascii=False, indent=1)
    sheet(plan, LAB, rud, til, carve, cathead, (hS, A_S), (hP, A_P), hinge, axis, Lx, R, YC, WL, gun_box, crew_spots, binn, MD, zt, tip)
    short = {k: R[k] for k in ('hinge', 'stock_top_foot', 'platform_carve', 'helmsman', 'overlap_new', 'ladder_points_blocked', 'ship_components_after', 'problems')}
    short['rudder'] = {k: R['rudder'][k] for k in ('cells', 'z', 'stock_top', 'chord_by_z', 'length_along_axis_m', 'sweep_1deg_hits_max', 'components', 'mirror_diff', 'rope_clear', 'cloth_clear')}
    short['tiller'] = {k: R['tiller'][k] for k in ('cells', 'x', 'z', 'end', 'length_from_axis_m', 'chosen', 'sweep_1deg_hits_max', 'z_over_quarterdeck_floor_m', 'components_with_rudder')}
    short['anchors'] = {s: {k: R['anchors'][s][k] for k in ('x', 'at', 'off_rail_cells', 'crown_above_wl_m', 'nearest_ship_cells', 'rope_clear', 'cloth_clear', 'aft_end_minus_oar', 'hawse', 'ok')} for s in ('S', 'P')}
    short['binnacle_sight'] = R.get('binnacle_sight')
    short['nav'] = {p: {dk: {k: v[k] for k in ('main_before', 'main_after', 'groups_ge12_after', 'helmsman_in_main')} for dk, v in d.items() if isinstance(v, dict)} for p, d in navr.items()}
    print(json.dumps(short, ensure_ascii=False))
    print(json.dumps(lists, ensure_ascii=False))


def sheet(plan, LAB, rud, til, carve, cathead, AS, AP, hinge, axis, Lx, R, YC, WL, gun_box, crew_spots, binn, MD, zt, tip):
    """圖紙 09：(a) 船尾中線剖面（舵、舵柄、艉柱、平台刻掉的格、鉸鏈線、水線）；(b) 後甲板俯視（舵柄 ±max 的弧、舵手、3l 砲外框、砲手、羅經櫃、後桅）；
    (c) 船首俯視（兩隻錨的外框、吊錨木、hawse）；(c') 船首右舷側視（錨、吊錨木、水線）。"""
    try:
        f = ImageFont.truetype('/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf', 14)
    except OSError:
        f = ImageFont.load_default()
    W_, H_ = 1700, 1330
    im = Image.new('RGB', (W_, H_), (250, 248, 242))
    d = ImageDraw.Draw(im)
    d.text((20, 10), '%s - new sheet 09: rudder, tiller, anchors (TASK-0022 step 11; draft_helm.py)' % plan['title_en'], fill=(0, 0, 0), font=f)
    base = {1: (120, 120, 120), 2: (160, 140, 110), 5: (150, 110, 90), 7: (90, 70, 50), 10: (200, 160, 160), 12: (60, 60, 60), 13: (80, 140, 80)}

    def cc(k):
        if k in rud:
            return palette_rgb(rud[k])
        if k in til:
            return (200, 140, 30)
        if k in carve:
            return (230, 40, 40)
        if k in cathead:
            return (40, 90, 200)
        v = int(LAB[k])
        return base.get(v, (175, 175, 175)) if v else None

    def panel(ox, oy, xr, vr, s, get, title):
        d.text((ox, oy - 20), title, fill=(0, 0, 0), font=f)
        for x in range(*xr):
            for v in range(*vr):
                c = get(x, v)
                if c is not None:
                    px, py = ox + (x - xr[0]) * s, oy + (vr[1] - 1 - v) * s
                    d.rectangle([px, py, px + s - 1, py + s - 1], fill=c)
        return lambda x, v: (ox + (x - xr[0]) * s, oy + (vr[1] - v) * s)
    ta = panel(30, 60, (40, 112), (0, 96), 7, lambda x, z: cc((x, YC, z)), '(a) centre line y %d: rudder, tiller, post, platform carve (red), hinge axis, waterline' % YC)
    p0, p1 = ta(Lx(-0.5), 0), ta(Lx(94.5), 95)
    d.line([p0, p1], fill=(0, 0, 220), width=1)
    d.line([ta(40, WL + 1), ta(112, WL + 1)], fill=(60, 120, 220), width=1)

    def top_q(x, y):
        for z in range(zt + 2, 55, -1):
            c = cc((x, y, z))
            if c is not None:
                return c
        return None
    tb = panel(560, 60, (55, 125), (95, 166), 8, top_q, '(b) quarterdeck from above: tiller arc +-%d deg, helmsman (green), 3l boxes, gun crew (blue), binnacle' % MD)
    for a in (-MD, 0, MD):
        q = rodrigues(np.array([[tip + 1.0, YC + 0.5, zt + 0.5]]), hinge, axis, a)[0]
        h0 = (Lx(zt), YC + 0.5)
        d.line([tb(*h0), tb(q[0], q[1])], fill=(200, 30, 30), width=2)
    for n_, a, b_ in gun_box:
        if a[0] < 125 and b_[0] > 55:
            d.rectangle([tb(a[0], b_[1]), tb(b_[0], a[1])], outline=(80, 80, 80), width=2)
    for gn, dk, a in crew_spots:
        if 55 < a[0] < 125:
            p = tb(a[0], a[1])
            d.ellipse([p[0] - 4, p[1] - 4, p[0] + 4, p[1] + 4], fill=(40, 60, 200))
    if binn:
        lo, hi = binn[0]['bbox']
        d.rectangle([tb(lo[0], hi[1]), tb(hi[0], lo[1])], outline=(220, 110, 0), width=2)
    hm = R['helmsman']['spot']
    if hm:
        p = tb(hm[0], hm[1])
        d.ellipse([p[0] - 5, p[1] - 5, p[0] + 5, p[1] + 5], fill=(30, 160, 60))

    def top_b(x, y):
        for z in range(70, 25, -1):
            c = cc((x, y, z))
            if c is not None:
                return c
        return None
    tc = panel(30, 760, (360, 470), (78, 184), 4, top_b, '(c) bow from above: anchors (red boxes), catheads (blue), hawse (x)')
    for h, g in (AS, AP):
        lo, hi = g.bbox(h['at'])
        d.rectangle([tc(lo[0], hi[1]), tc(hi[0], lo[1])], outline=(200, 30, 30), width=2)
    for k in ('S', 'P'):
        hw = R['anchors']['hawse']['hawse-' + k]
        if hw:
            p = tc(hw[0] + 0.5, hw[1] + 0.5)
            d.line([p[0] - 6, p[1] - 6, p[0] + 6, p[1] + 6], fill=(0, 0, 0), width=2)
            d.line([p[0] - 6, p[1] + 6, p[0] + 6, p[1] - 6], fill=(0, 0, 0), width=2)
    h, g = AS
    lo, hi = g.bbox(h['at'])
    xa, xb = int(lo[0]) - 15, int(hi[0]) + 15
    A_cells = set(map(tuple, np.floor(g.world(g.centers, h['at'])).astype(int).tolist()))

    def side_s(x, z):
        for y in range(AS[0]['rail'][1] + 30, YC - 1, -1):
            if (x, y, z) in A_cells:
                return (200, 30, 30)
            c = cc((x, y, z))
            if c is not None:
                return c
        return None
    td = panel(620, 760, (xa, xb), (20, 75), 7, side_s, "(c') starboard bow from outside: anchor-S, cathead, waterline")
    d.line([td(xa, WL + 1), td(xb, WL + 1)], fill=(60, 120, 220), width=1)
    tl = R['tiller']
    rr = R['rudder']
    d.text((30, 1250), '\n'.join([
        'rudder: z %d-%d, hinge %s, axis %s (rake %.1f deg), stock-top %s, sweep +-%d deg hits max %d; platform carve %d cells' % (
            rr['z'][0], rr['z'][1], R['hinge']['hinge'], R['hinge']['axis'], R['hinge']['rake_deg'], rr['stock_top'], MD, rr['sweep_1deg_hits_max'], R['platform_carve']['cells']),
        'tiller: x %d-%d, z %d-%d, %.2f m from the axis, sweep hits max %d; helmsman %s' % (tl['x'][0], tl['x'][1], tl['z'][0], tl['z'][1], tl['length_from_axis_m'],
                                                                                         tl['sweep_1deg_hits_max'], hm),
        'anchors: %s x %.2g at S %s / P %s; hawse %s' % (R['anchors']['model']['work'], R['anchors']['model']['scale'], R['anchors']['S']['at'], R['anchors']['P']['at'],
                                                    R['anchors']['hawse'])]), fill=(0, 0, 0), font=f)
    im.save(os.path.join(HERE, 'sheet09_helm_v1.png'), optimize=False)


if __name__ == '__main__':
    main()
