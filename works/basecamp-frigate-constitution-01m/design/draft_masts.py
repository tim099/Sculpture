# 新圖紙 11（桅杆子作品）：plan.json 的 masts 段（軸照 deckworks.masts）＋ 組裝件 draft=1 的現況（船殼＋舷牆草稿＋甲板＋房間）
#   ⇒ masks/masts/{fore,main,mizzen,bowsprit}.vox.txt（子作品尺寸 ＝ 船殼、at=0,0,0）、masks/masts/hull_bowsprit_carve.vox.txt（船殼要刻的）、
#      verify_masts.json、sheet11_masts_v1.png
# 用法：python -I draft_masts.py <design 資料夾>
#   · 每根桅一條斜的軸：X(z) ＝ x_gun − (z − z_ref)·tan(rake)（甲板的桅孔就是照這條開的）；所有節都跟這條軸平行，往前（u）偏
#   · 下桅踩在 keelson／deadwood 上（step 3 格）；tops 是水平的平台（D 形、前緣圓）
#   · 只放在空著的格；碰到現有格的數出來（bowsprit 穿過船頭那段 ⇒ 船殼刻掉，清單另外寫）
import sys, os, json, glob, hashlib, math, subprocess, tempfile
import numpy as np
from PIL import Image, ImageDraw

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import draft_planking as DP        # noqa: E402
import draft_decks as DD           # noqa: E402

FT, IN = 3.048, 0.254              # 1 ft ＝ 3.048 格、1 inch ＝ 0.254 格
YC = 160
ASSEMBLY = 'basecamp-frigate-constitution-01m-assembly'
HULL = 'basecamp-frigate-constitution-01m'


def export_list(work, draft=True, links=None, hide_links=None, mark=None):
    with tempfile.TemporaryDirectory() as d:
        out = os.path.join(d, 'w.txt').replace('\\', '/')
        args = ['senate', 'cmd', 'sculpture', '--arg', 'op=export', '--arg', 'format=list', '--arg', 'work=' + work, '--arg', 'out=' + out]
        if draft:
            args += ['--arg', 'draft=1']
        if links:
            args += ['--arg', 'links=' + links]
        if hide_links:
            args += ['--arg', 'hide_links=' + hide_links]
        if mark:
            args += ['--arg', 'mark=' + mark]
        r = subprocess.run(args, capture_output=True, text=True, encoding='utf-8', errors='replace')
        if r.returncode != 0 or not os.path.exists(out):
            raise SystemExit('匯出失敗：' + (r.stdout + r.stderr)[-600:])
        a = np.loadtxt(out, delimiter=',', comments='#', dtype=np.int32, ndmin=2, encoding='utf-8')
    return a


class Masts:
    def __init__(s, design):
        s.design = design
        s.plan = json.load(open(os.path.join(design, 'plan.json'), encoding='utf-8'))
        s.P = s.plan['masts']
        s.AX = s.plan['deckworks']['masts']
        # 現況要讀「桅杆加進來之前」：組裝件藏起桅杆那幾條關聯、船殼讀標記（bowsprit 開口刻之前）—— 套用之後重跑才逐位元組一樣
        B = s.P['base']
        a = export_list(ASSEMBLY, draft=False, hide_links=','.join(B['hide_links']))
        s.occ = {(int(x), int(y), int(z)): int(c) for x, y, z, c in a}
        h = export_list(HULL, draft=False, links='none', mark=B['hull_mark'])
        s.hull = {(int(x), int(y), int(z)) for x, y, z, c in h}
        for x, y, z, c in h:
            s.occ[(int(x), int(y), int(z))] = int(c)
        s.world_count = len(s.occ)
        assert s.world_count == B['voxels'], ('讀到的現況格數對不上 masts.base.voxels', s.world_count, B['voxels'])
        s.parts = {}                                   # name → {(x,y,z): color}
        s.log = {}

    # ───────── 幾何 ─────────
    def frame(s, m):
        a = s.AX[m]
        th = math.radians(a['rake_deg'])
        d = np.array([-math.sin(th), 0.0, math.cos(th)])          # 往上（往船尾倒）
        f = np.array([math.cos(th), 0.0, math.sin(th)])           # 往前
        X = lambda z: a['x_gun'] - (z - s.AX['z_ref']) * math.tan(th)
        return th, d, f, X

    def keelson_top(s, x, zmax=60):
        zs = [z for z in range(zmax, -1, -1) if (x, YC, z) in s.occ]
        return zs[0] if zs else None

    def add(s, part, cells, color, why):
        n = 0
        for c in cells:
            if c in s.parts[part]:
                continue
            s.parts[part][c] = color
            n += 1
        s.log[part].setdefault('members', {})
        s.log[part]['members'][why] = s.log[part]['members'].get(why, 0) + n

    def scan(s, H, d, f, s0, s1, rmax, test):
        """沿軸 s0..s1、半徑 rmax 的外框裡每一格做 test(s, u, v) ⇒ 格子清單。"""
        p0, p1 = H + s0 * d, H + s1 * d
        xs = range(int(math.floor(min(p0[0], p1[0]) - rmax - 2)), int(math.ceil(max(p0[0], p1[0]) + rmax + 2)) + 1)
        zs = range(int(math.floor(min(p0[2], p1[2]) - rmax - 2)), int(math.ceil(max(p0[2], p1[2]) + rmax + 2)) + 1)
        ys = range(int(math.floor(YC - rmax - 1)), int(math.ceil(YC + rmax + 1)) + 1)
        out = []
        for x in xs:
            for z in zs:
                w0 = np.array([x, 0.0, z]) - H
                sp = float(w0 @ d)
                if sp < s0 - 0.5 or sp > s1 + 0.5:
                    continue
                u = float(w0 @ f)
                for y in ys:
                    if test(sp, u, y - YC):
                        out.append((x, y, z))
        return out

    # ───────── 一根桅 ─────────
    def mast(s, m):
        P = s.P['masts'][m]
        C = s.P['colors']
        s.parts[m] = {}
        s.log[m] = {}
        th, d, f, X = s.frame(m)
        L, r0 = P['lower'][0] * FT, P['lower'][1] * IN / 2
        mh = P['masthead'] * FT
        T, rt = P['topmast'][0] * FT, P['topmast'][1] * IN / 2
        th_ = P['topmast_head'] * FT
        Gl, rg = P['topgallant'][0] * FT, P['topgallant'][1] * IN / 2
        tp = s.P['taper']
        # 跟：keelson／deadwood 頂上 3 格的 step
        xk = int(round(X(30)))
        zk = s.keelson_top(xk)
        zh = zk + 4
        H = np.array([X(zh), 0.0, zh])
        s.log[m]['keelson_top'] = zk
        s.log[m]['heel'] = [round(H[0], 2), zh]
        step = []
        for x in range(int(H[0] - r0 - 2), int(H[0] + r0 + 3)):
            hw = int(r0 + 2)
            for y in range(YC - hw, YC + hw + 1):
                for z in range(zk + 1, zh):
                    step.append((x, y, z))
        s.add(m, step, C['step'], 'step')
        # 下桅：spar deck 以下等粗，往上收到 hounds（masthead 底）；masthead 方的
        z_spar = s.plan['interior']['decks']['spar']['segments'][1][2]
        s_spar = (z_spar - zh) / math.cos(th)
        s_hounds = L - mh
        h_head = r0 * tp['lower_head']

        def r_lower(sp):
            if sp <= s_spar:
                return r0
            t = min(1.0, (sp - s_spar) / max(1e-6, s_hounds - s_spar))
            return r0 + (h_head - r0) * t
        cells = s.scan(H, d, f, 0, s_hounds, r0, lambda sp, u, v: u * u + v * v <= r_lower(sp) ** 2)
        s.add(m, cells, C['spar'], 'lower')
        cells = s.scan(H, d, f, s_hounds, L, h_head + 1, lambda sp, u, v: abs(u) <= h_head and abs(v) <= h_head)
        s.add(m, cells, C['black'], 'masthead')
        # 鐵箍：spar deck 以上每 every 格一圈
        hp = s.P['hoops']
        k0 = math.ceil((s_spar + 2) / hp['every'])
        rings = []
        for k in range(k0, int(s_hounds // hp['every']) + 1):
            sk = k * hp['every']
            rings += s.scan(H, d, f, sk - 0.5, sk + 0.5, r0 + 1, lambda sp, u, v, sk=sk: abs(sp - sk) <= 0.5 and r_lower(sp) ** 2 < u * u + v * v <= (r_lower(sp) + 0.75) ** 2)
        s.add(m, rings, hp['color'], 'hoops')
        # topmast（在 masthead 前面）、cap
        u_tm = h_head + rt + 0.5
        cells = s.scan(H, d, f, L - 1, L + 2, max(h_head, u_tm + rt) + 3,
                       lambda sp, u, v: -h_head - 1.5 <= u <= u_tm + rt + 1.5 and abs(v) <= h_head + 1.5)
        s.add(m, cells, C['black'], 'cap')
        Ht = H + u_tm * f
        s_t0 = s_hounds
        s_th = s_t0 + T - th_
        h2 = rt * tp['topmast_head']

        def r_top(sp):
            t = min(1.0, max(0.0, (sp - s_t0) / max(1e-6, s_th - s_t0)))
            return rt + (h2 - rt) * t
        cells = s.scan(Ht, d, f, s_t0, s_th, rt, lambda sp, u, v: u * u + v * v <= r_top(sp) ** 2)
        s.add(m, cells, C['spar'], 'topmast')
        cells = s.scan(Ht, d, f, s_th, s_t0 + T, h2 + 1, lambda sp, u, v: abs(u) <= h2 and abs(v) <= h2)
        s.add(m, cells, C['black'], 'topmast_head')
        # topgallant／royal（在 topmast head 前面）＋ truck
        u_tg = h2 + rg + 0.5
        Hg = Ht + u_tg * f
        s_g0, s_g1 = s_th, s_th + Gl
        cells = s.scan(Hg, d, f, s_g0, s_g1, rg + 0.6,
                       lambda sp, u, v: u * u + v * v <= (max(0.6, rg + (rg * tp['topgallant_head'] - rg) * (sp - s_g0) / Gl)) ** 2)
        s.add(m, cells, C['spar'], 'topgallant')
        cells = s.scan(Hg, d, f, s_g1, s_g1 + 1.4, rg + 2, lambda sp, u, v: u * u + v * v <= (rg + 1.2) ** 2)
        s.add(m, cells, C['truck'], 'truck')
        cells = s.scan(Ht, d, f, s_t0 + T - 1, s_t0 + T + 1.5, u_tg + rg + 3,
                       lambda sp, u, v: -h2 - 1 <= u <= u_tg + rg + 1 and abs(v) <= h2 + 1)
        s.add(m, cells, C['black'], 'topmast_cap')
        # top（水平、D 形、前緣圓）＋ 黑邊、lubber's hole、trestletrees／crosstrees
        p_h = H + s_hounds * d
        z_top = int(round(p_h[2]))
        W, D_ = P['top'][0] * FT, P['top'][1] * FT
        xc = p_h[0] + (u_tm / 2) * math.cos(th)
        lub_a0, lub_a1 = -h_head - 3 - u_tm / 2, u_tm / 2 + rt + 3
        lub_w = max(h_head, rt) + 0.18 * W

        def in_top(a, v):
            if a < -D_ / 2 or a > D_ / 2:
                return False
            if a <= 0:
                return abs(v) <= W / 2
            return abs(v) <= W / 2 * math.sqrt(max(0.0, 1 - (a / (D_ / 2)) ** 2))
        plat, rim = [], []
        for x in range(int(xc - D_ / 2 - 2), int(xc + D_ / 2 + 3)):
            for y in range(int(YC - W / 2 - 2), int(YC + W / 2 + 3)):
                a, v = x - xc, y - YC
                if not in_top(a, v) or (lub_a0 <= a <= lub_a1 and abs(v) <= lub_w):
                    continue
                for z in (z_top - 1, z_top):
                    plat.append((x, y, z))
                if any(not in_top(a + da, v + dv) for da, dv in ((1, 0), (-1, 0), (0, 1), (0, -1))):
                    rim.append((x, y, z_top + 1))
        s.add(m, plat, C['top'], 'top')
        s.add(m, rim, C['black'], 'top_rim')
        tt = []
        v1 = int(math.floor(h_head)) + 1                            # 緊貼 masthead 外面那一格（v1.1：主桅 round 成 5／6、空一格 ⇒ top 浮在空中）
        for x in range(int(xc - D_ / 2 + 2), int(xc + D_ / 2 - 1)):
            for v in (v1, v1 + 1):
                for sg in (1, -1):
                    for z in (z_top - 3, z_top - 2):
                        tt.append((x, YC + sg * v, z))
        hw = int(W / 2 - 3)
        for a in (-D_ / 3, 0.0 + u_tm, D_ / 3):
            for y in range(YC - hw, YC + hw + 1):
                for x in (int(round(xc + a)), int(round(xc + a)) + 1):
                    for z in (z_top - 3, z_top - 2):
                        tt.append((x, y, z))
        s.add(m, tt, C['black'], 'trestle_cross_trees')
        # topmast crosstrees（topmast head 底下）
        p2 = Ht + s_th * d
        z2 = int(round(p2[2]))
        span = P['crosstrees'] * FT
        ct = []
        for a in (-3, 2, 6):
            for y in range(YC - int(span / 2), YC + int(span / 2) + 1):
                ct.append((int(round(p2[0] + a)), y, z2 - 1))
        for x in range(int(p2[0] - 5), int(p2[0] + 8)):
            for sg in (1, -1):
                ct.append((x, int(round(YC + sg * (h2 + 1))), z2 - 1))
        s.add(m, ct, C['black'], 'crosstrees')
        s.log[m]['heights'] = {'heel': zh, 'spar_deck': z_spar, 'top': z_top, 'topmast_crosstrees': z2,
                               'truck': int(round((Hg + s_g1 * d)[2])), 'lower_head': int(round((H + L * d)[2]))}
        s.log[m]['radii_cells'] = {'lower': round(r0, 2), 'masthead_half': round(h_head, 2), 'topmast': round(rt, 2), 'topgallant': round(rg, 2),
                                   'hole': s.AX[m]['r']}

    # ───────── bowsprit ─────────
    def bowsprit(s):
        B = s.P['bowsprit']
        C = s.P['colors']
        s.parts['bowsprit'] = {}
        s.log['bowsprit'] = {}
        H = np.array([B['heel'][0], 0.0, B['heel'][1]])
        Q = np.array([B['over_stem'][0], 0.0, B['over_stem'][1]])
        d = (Q - H) / np.linalg.norm(Q - H)
        n = np.array([-d[2], 0.0, d[0]])                           # 往上的法向
        phi = math.degrees(math.atan2(d[2], d[0]))
        Lb, rb = B['length'] * FT, B['dia'] * IN / 2
        tp = s.P['taper']['bowsprit_head']
        rb_end = rb * tp
        rf = lambda sp: rb + (rb_end - rb) * max(0.0, min(1.0, sp / Lb))
        cells = s.scan(H, d, n, 0, Lb, rb, lambda sp, u, v: u * u + v * v <= rf(sp) ** 2)
        s.add('bowsprit', cells, C['spar'], 'bowsprit')
        hp = s.P['hoops']
        rings = []
        for k in range(1, int(Lb // hp['every'])):
            sk = k * hp['every']
            rings += s.scan(H, d, n, sk - 0.5, sk + 0.5, rb + 1, lambda sp, u, v, sk=sk: abs(sp - sk) <= 0.5 and rf(sp) ** 2 < u * u + v * v <= (rf(sp) + 0.75) ** 2)
        s.add('bowsprit', rings, hp['color'], 'hoops')
        # 跟底下的 step（坐在 spar deck 上）
        z_deck = DD.seg_z(s.plan['interior']['decks']['spar']['segments'], int(round(H[0])))
        st = []
        for x in range(int(H[0] - 3), int(H[0] + 4)):
            for y in range(YC - int(rb + 1), YC + int(rb + 1) + 1):
                zb = H[2] + (x - H[0]) * d[2] / d[0] - rb
                for z in range(z_deck, int(math.floor(zb)) + 1):
                    st.append((x, y, z))
        s.add('bowsprit', st, C['step'], 'step')
        # jibboom、flying jibboom：疊在上一節上面、同一個斜度
        Lj, rj, ovj = B['jibboom'][0] * FT, B['jibboom'][1] * IN / 2, B['jibboom'][2]
        Hj = H + (rb_end + rj + 0.4) * n + (Lb - ovj * Lj) * d
        cells = s.scan(Hj, d, n, 0, Lj, rj, lambda sp, u, v: u * u + v * v <= (rj - 0.25 * rj * sp / Lj) ** 2)
        s.add('bowsprit', cells, C['spar'], 'jibboom')
        Lf, rfl, ovf = B['flying_jibboom'][0] * FT, B['flying_jibboom'][1] * IN / 2, B['flying_jibboom'][2]
        rj_end = rj * 0.75
        Hf = Hj + (rj_end + rfl + 0.3) * n + (Lj - ovf * Lf) * d
        cells = s.scan(Hf, d, n, 0, Lf, rfl + 0.6, lambda sp, u, v: u * u + v * v <= max(0.6, rfl - 0.4 * rfl * sp / Lf) ** 2)
        s.add('bowsprit', cells, C['spar'], 'flying_jibboom')
        # bowsprit cap（jibboom 從裡面穿過）
        cells = s.scan(H, d, n, Lb - 1.5, Lb + 1.5, rb + 2 * rj + 4,
                       lambda sp, u, v: -rb_end - 1 <= u <= rb_end + 2 * rj + 1.5 and abs(v) <= rb_end + 1)
        s.add('bowsprit', cells, C['black'], 'cap')
        tipj = Hj + Lj * d
        tipf = Hf + Lf * d
        s.log['bowsprit'].update({'steeve_deg': round(phi, 2), 'length_cells': round(Lb, 1), 'r': round(rb, 2),
                                  'bowsprit_tip': [round(float(v), 1) for v in (H + Lb * d)[[0, 2]]],
                                  'jibboom_tip': [round(float(v), 1) for v in tipj[[0, 2]]],
                                  'flying_jibboom_tip': [round(float(v), 1) for v in tipf[[0, 2]]]})

    # ───────── 碰撞：只放在空著的格；bowsprit 碰到船殼的 ⇒ 船殼刻掉 ─────────
    def resolve(s):
        s.carve = set()
        s.collide = {}
        allm = {}
        for p, cells in s.parts.items():
            hit = [c for c in cells if c in s.occ]
            by = {}
            for c in hit:
                k = 'hull' if c in s.hull else 'deck/rooms'
                by[k] = by.get(k, 0) + 1
            s.collide[p] = by
            if p == 'bowsprit':
                for c in hit:
                    if c in s.hull:
                        s.carve.add(c)
                for c in [c for c in hit if c not in s.hull]:
                    del cells[c]
            else:
                for c in hit:
                    del cells[c]
            for c in cells:
                if c in allm:
                    raise SystemExit('兩件桅杆重疊 @ %s（%s／%s）' % (c, allm[c], p))
                allm[c] = p
        s.carve_by_color = {}
        for c in s.carve:
            k = str(s.occ[c])
            s.carve_by_color[k] = s.carve_by_color.get(k, 0) + 1

    def verify(s):
        v = {'world_voxels_assembly_draft': s.world_count, 'parts': {}}
        for p, cells in s.parts.items():
            a = np.array(list(cells.keys()))
            mir = sum(1 for (x, y, z) in cells if (x, 2 * YC - y, z) not in cells)
            v['parts'][p] = {'cells': len(cells), 'mirror_mismatch': mir, 'collided_skipped': s.collide.get(p, {}),
                             'bbox': [a.min(0).tolist(), a.max(0).tolist()], 'log': s.log[p]}
        v['hull_carve_for_bowsprit'] = {'cells': len(s.carve), 'by_color': s.carve_by_color,
                                        'x_range': [min(c[0] for c in s.carve), max(c[0] for c in s.carve)] if s.carve else None}
        v['total_new'] = sum(len(c) for c in s.parts.values())
        s.v = v
        return v

    def write(s):
        out = os.path.join(s.design, 'masks', 'masts')
        os.makedirs(out, exist_ok=True)
        for f in glob.glob(os.path.join(out, '*')):
            os.remove(f)
        s.files = {}
        for p, cells in s.parts.items():
            path = os.path.join(out, p + '.vox.txt')
            sw = s.P['subworks'][p]
            rows = ['%d,%d,%d,%d' % (x, y, z, c) for (x, y, z), c in sorted(cells.items())]
            open(path, 'w', encoding='utf-8', newline='\n').write('# %s —— %s（子作品 %s；%d 格，at=0,0,0）\n' % (p, sw['title'], sw['id'], len(rows)) + '\n'.join(rows) + '\n')
            s.files[p] = {'cells': len(rows), 'sha256': hashlib.sha256(open(path, 'rb').read()).hexdigest()}
        path = os.path.join(out, 'hull_bowsprit_carve.vox.txt')
        rows = ['%d,%d,%d,%d' % (x, y, z, s.occ[(x, y, z)]) for (x, y, z) in sorted(s.carve)]
        open(path, 'w', encoding='utf-8', newline='\n').write('# hull_bowsprit_carve —— 船殼要刻掉的格（bowsprit 穿過船頭那段；carvevox，at=0,0,0；%d 格）\n' % len(rows) + '\n'.join(rows) + '\n')
        s.files['hull_bowsprit_carve'] = {'cells': len(rows), 'sha256': hashlib.sha256(open(path, 'rb').read()).hexdigest()}


# ───────── 圖紙 11 ─────────
def project(cells_colors, axis, w, h, origin):
    """cells_colors：[(x,y,z,c)]；axis ＝ 'y'（從 y > 160 那一舷看：取 y 最大）或 'x'（從船頭看：取 x 最大）。回傳 RGB。"""
    img = np.zeros((h, w, 3), np.uint8)
    img[:] = DD.PAPER
    a = np.array(cells_colors, dtype=np.int32)
    if axis == 'y':
        u, depth = a[:, 0] - origin[0], a[:, 1]
    else:
        u, depth = a[:, 1] - origin[0], a[:, 0]
    zz = a[:, 2] - origin[1]
    ok = (u >= 0) & (u < w) & (zz >= 0) & (zz < h)
    a, u, zz, depth = a[ok], u[ok], zz[ok], depth[ok]
    order = np.argsort(depth)                                       # 後畫的蓋前面的 ⇒ 最外面那一格在最上層
    lut = np.array([DP.rgb332(i) for i in range(256)], np.uint8)
    img[h - 1 - zz[order], u[order]] = lut[a[order, 3]]
    return img


def render_sheet(K, path):
    f12, f14, f18 = DD._font(13), DD._font(15), DD._font(20)
    base = [(x, y, z, c) for (x, y, z), c in K.occ.items() if (x, y, z) not in K.carve]
    masts = [(x, y, z, c) for p in K.parts.values() for (x, y, z), c in p.items()]
    allc = base + masts
    sc = 1.0
    side = Image.fromarray(project(allc, 'y', 1000, 700, (90, 0))).resize((1000, 700), Image.NEAREST)
    front = Image.fromarray(project(allc, 'x', 160, 700, (80, 0))).resize((160 * 2, 700 * 2 // 2), Image.NEAREST)
    # 主桅 top 近看（從上往下）：top 那一層附近的格
    m = K.v['parts']['main']['log']['heights']
    zt = m['top']
    near = [(x, y, z, c) for (x, y, z, c) in masts if zt - 4 <= z <= zt + 2 and 300 <= x <= 400]
    topv = np.zeros((90, 100, 3), np.uint8)
    topv[:] = DD.PAPER
    lut = np.array([DP.rgb332(i) for i in range(256)], np.uint8)
    for x, y, z, c in sorted(near, key=lambda t: t[2]):
        if 115 <= y < 205 and 300 <= x < 400:
            topv[204 - y, x - 300] = lut[c]
    topim = Image.fromarray(topv).resize((400, 360), Image.NEAREST)
    # 主桅 masthead 近看（側面）
    mh = [(x, y, z, c) for (x, y, z, c) in allc if zt - 30 <= z <= zt + 70 and 320 <= x <= 380]
    mhim = Image.fromarray(project(mh, 'y', 60, 100, (320, zt - 30))).resize((240, 400), Image.NEAREST)
    W = 1000 + 2 * 160 + 120
    H = 60 + 700 + 40 + 420 + 120
    can = Image.new('RGB', (W, H), DD.PAPER)
    dr = ImageDraw.Draw(can)
    dr.text((20, 10), K.P['title'], font=f18, fill=DD.INK)
    dr.text((20, 36), '左：側面（從 y > 160 那一舷看，1 格 ＝ 1 px）　右：從船頭看　下：主桅 top 從上往下看、主桅 masthead 側面近看（4×）', font=f12, fill=DD.INK)
    can.paste(side, (20, 60))
    can.paste(front, (1040, 60))
    for z in range(0, 701, 100):
        dr.text((2, 60 + 700 - z - 7), str(z), font=f12, fill=(130, 130, 130))
    y0 = 60 + 700 + 30
    dr.text((20, y0), '主桅 top（z %d，從上往下看；x 300–400）' % zt, font=f14, fill=DD.INK)
    can.paste(topim, (20, y0 + 22))
    dr.text((450, y0), '主桅 masthead（側面 4×）', font=f14, fill=DD.INK)
    can.paste(mhim, (450, y0 + 22))
    tx, ty = 730, y0 + 26
    for p in ('main', 'fore', 'mizzen'):
        L = K.v['parts'][p]['log']
        hgt = L['heights']
        dr.text((tx, ty), '%s：跟 z %d、top z %d、topmast crosstrees z %d、truck z %d（%d 格）' % (p, hgt['heel'], hgt['top'], hgt['topmast_crosstrees'], hgt['truck'], K.v['parts'][p]['cells']), font=f12, fill=DD.INK)
        ty += 20
        rr = L['radii_cells']
        dr.text((tx + 14, ty), '半徑：下桅 %.2f（桅孔 %.1f）、masthead 半邊 %.2f、topmast %.2f、topgallant %.2f' % (rr['lower'], rr['hole'], rr['masthead_half'], rr['topmast'], rr['topgallant']), font=f12, fill=(80, 80, 80))
        ty += 24
    b = K.v['parts']['bowsprit']['log']
    dr.text((tx, ty), 'bowsprit：斜度 %.1f°、長 %.0f 格、尖端 x,z %s；jibboom %s；flying %s（%d 格）' % (b['steeve_deg'], b['length_cells'], b['bowsprit_tip'], b['jibboom_tip'], b['flying_jibboom_tip'], K.v['parts']['bowsprit']['cells']), font=f12, fill=DD.INK)
    ty += 24
    hc = K.v['hull_carve_for_bowsprit']
    dr.text((tx, ty), '船殼要刻掉（bowsprit 穿過船頭）：%d 格，x %s，顏色 %s' % (hc['cells'], hc['x_range'], hc['by_color']), font=f12, fill=DD.INK)
    ty += 24
    for p, e in K.v['parts'].items():
        if e['collided_skipped']:
            dr.text((tx, ty), '%s 碰到現有的格（沒放）：%s' % (p, e['collided_skipped']), font=f12, fill=(170, 60, 40))
            ty += 20
    can = can.crop((0, 0, W, max(ty, y0 + 22 + 400) + 20))
    can.save(path)


def main():
    design = sys.argv[1]
    sys.stdout.reconfigure(encoding='utf-8')
    K = Masts(design)
    for m in ('main', 'fore', 'mizzen'):
        K.mast(m)
    K.bowsprit()
    K.resolve()
    v = K.verify()
    K.write()
    v['files'] = K.files
    json.dump(v, open(os.path.join(design, 'verify_masts.json'), 'w', encoding='utf-8', newline='\n'), ensure_ascii=False, indent=1)
    render_sheet(K, os.path.join(design, 'sheet11_masts_v1.png'))
    print(json.dumps({p: {k: e[k] for k in ('cells', 'mirror_mismatch', 'collided_skipped')} | {'heights': e['log'].get('heights'), 'members': e['log'].get('members')}
                      for p, e in v['parts'].items()}, ensure_ascii=False, indent=1))
    print(json.dumps({k: v[k] for k in ('hull_carve_for_bowsprit', 'total_new')}, ensure_ascii=False))
    print(json.dumps(v['parts']['bowsprit']['log'], ensure_ascii=False))


if __name__ == '__main__':
    main()
