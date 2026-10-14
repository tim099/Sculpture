# 三叉戟號 階段六（TASK-0559）桅與帆桁：前、主、後桅＋艏斜桅（每根一件子作品，整船的框、at 0,0,0）；帆桁每根一件子作品（沒轉，沿 y），當模型放進它的桅子作品
#   輸入：plan.json（masts、masts_build、decks_build.mast_r）＋「階段六之前」（deco_base.stage6_base：船殼讀標記 艏斜桅開口:begin ＋ 甲板 ＋ 階段五的部件）
#   輸出：masks/masts/{main,fore,mizzen,bowsprit}.vox.txt（世界座標）、masks/masts/hull_carve.vox.txt（艏斜桅穿過船殼那幾格；carvevox 顏色守門）、
#         masks/yards/<帆桁>.vox.txt（帆桁子作品座標）、masts_placement.json（子作品、帆桁框、固定點、模型 at／pivot／rotate／meta）、verify_masts.json、sheet07_masts_v1.png
#   用法：python -I -X utf8 draft_masts.py <design> [--base=<快取.npz>] [--probe=<帆桁名>:<角度>]（probe：那根帆桁換一個 brace 角，印 arm 端點的世界座標；⛔ 不寫檔）
import sys, os, json, math
import numpy as np
from scipy import ndimage
from PIL import Image, ImageDraw

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import hull_lines as HL
import layout as LY
import deco_base as DB
from draft_lines import font, palette_rgb

YC = 200
HULL = 'gura-tridente-01m'
NAMES = {'main': '主桅', 'fore': '前桅', 'mizzen': '後桅', 'bowsprit': '艏斜桅'}


def interp_k(MB, s):
    return float(np.interp(s, MB['yards']['taper_s'], MB['yards']['taper_k']))


def main():
    sys.stdout.reconfigure(encoding='utf-8')
    design = sys.argv[1]
    cache = next((a.split('=', 1)[1] for a in sys.argv[2:] if a.startswith('--base=')), None)
    probe = next((a.split('=', 1)[1] for a in sys.argv[2:] if a.startswith('--probe=')), None)
    plan = HL.load_plan(design)
    MB = plan['masts_build']
    C = MB['colors']
    SPAR, BLACK, TOP, TRUCK, STEP = C['spar'], C['black'], C['top'], C['truck'], C['step']
    if cache and os.path.exists(cache):
        z = np.load(cache)
        G, H, hull_when = z['G'], z['H'], str(z['when'])
    else:
        G, H, hull_when = DB.stage6_base('艏斜桅開口:begin', nz=260)
        if cache:
            np.savez_compressed(cache, G=G, H=H, when=hull_when)
    S = G > 0
    ZB = S.shape[2]
    HS = np.zeros_like(S)
    HS[H[:, 0], H[:, 1], H[:, 2]] = True                               # 船殼那一份（艏斜桅只准刻船殼）

    def solid(x, y, z):
        return z < ZB and S[x, y, z]

    spars = {m['key']: m for m in LY.mast_spars(plan)}
    rows = {r['key']: r for r in plan['masts']['rows']}
    deck_keys = [r['key'] for r in plan['decks']['rows']]
    poop_to = next(r for r in plan['decks']['rows'] if r['key'] == 'poop').get('x_to', 9999)

    parts = {k: {} for k in ('main', 'fore', 'mizzen', 'bowsprit')}
    carve = {}
    hit_other = {k: 0 for k in parts}
    HITS = {}

    def put(key, x, y, z, c, force=False):
        k = (x, y, z)
        if solid(x, y, z):
            if key == 'bowsprit' and HS[x, y, z]:
                carve[k] = int(G[x, y, z])
            else:
                hit_other[key] += 1
                HITS.setdefault(key, []).append((x, y, z, int(G[x, y, z])))
                return
        if k in parts[key] and not force:
            return
        parts[key][k] = c

    geo = {}

    def build(key):                                                  # 每根桅一個函式範圍 ⇒ 底下的軸心／半徑函式綁住自己的數（v1 寫在迴圈裡，迴圈跑完全部指到後桅 —— 晚綁定）
        sp, rw = spars[key], rows[key]
        r0, rt0, rg0 = MB['r'][key]
        rh = r0 * MB['taper']['lower_head']
        rth = rt0 * MB['taper']['top_head']
        rgh = rg0 * MB['taper']['tg_head']
        x0 = rw['x']
        # 這根桅穿過的最高那層甲板（在桅的 x）
        tops = [int(LY.deck_z(plan, k, x0)) for k in deck_keys if k != 'poop' or x0 <= poop_to]
        z_td = max(tops) + 1
        zp, zlt, zxt, ztt, ztr = sp['platform'], sp['lower_top'], sp['crosstrees'], sp['top_top'], sp['truck']

        def ax_L(z, key=key):
            return float(LY.mast_axis_x(plan, key, z))
        dLT = int(round(rh + rt0 + 0.5))
        dTG = int(round(rth + rg0 + 0.5))

        def ax_T(z):
            return ax_L(z) + dLT

        def ax_G(z):
            return ax_T(z) + dTG

        def r_L(z):
            if z <= z_td:
                return r0
            if z >= zp:
                return rh
            return r0 + (rh - r0) * (z - z_td) / float(zp - z_td)

        def r_T(z):
            return rth if z >= zxt else rt0 + (rth - rt0) * (z - zp) / float(zxt - zp)

        def r_G(z):
            return rg0 + (rgh - rg0) * (z - zxt) / float(ztr - zxt)
        geo[key] = {'ax': {'lower': ax_L, 'top': ax_T, 'tg': ax_G}, 'r': {'lower': r_L, 'top': r_T, 'tg': r_G},
                    'z': {'heel': sp['heel'], 'deck_top': z_td, 'platform': zp, 'lower_top': zlt, 'crosstrees': zxt, 'top_top': ztt, 'truck': ztr}}

        def disc(z, xc, r, col, yc=YC):
            R = int(math.ceil(r)) + 1
            for x in range(int(math.floor(xc)) - R, int(math.ceil(xc)) + R + 1):
                for dy in range(-R, R + 1):
                    if (x - xc) ** 2 + dy * dy <= r * r:
                        put(key, x, yc + dy, z, col)
        # 桅腳：plan 的 heel 往上找第一層「整圈都空」的格（前桅那裡船底 deadwood 往上收、實心到 z 21；後桅立在 orlop 上，舷弧讓那裡的甲板面高 2 格）
        heel = sp['heel']
        while any(solid(x, YC + dy, heel) for x in range(int(ax_L(heel)) - 8, int(ax_L(heel)) + 9) for dy in range(-8, 9)
                  if LY.mast_hit(plan, key, x, YC + dy, heel)):
            heel += 1
        geo[key]['z']['heel_eff'] = heel
        # 下桅：甲板那一段照 layout.mast_hit（甲板孔就是它開的 ⇒ 剛好填滿），上面收到 masthead；masthead 黑；上甲板以上每 12 格一圈黑箍
        for z in range(heel, zlt + 1):
            if z <= z_td:
                for x in range(int(ax_L(z)) - 8, int(ax_L(z)) + 9):
                    for dy in range(-8, 9):
                        if LY.mast_hit(plan, key, x, YC + dy, z):
                            put(key, x, YC + dy, z, SPAR)
            else:
                col = BLACK if z >= zp else SPAR
                hoop = z < zp - 3 and z > z_td + 2 and (z - z_td) % MB['hoop_every'] == 0
                disc(z, ax_L(z), r_L(z) + (0.6 if hoop else 0.0), BLACK if hoop else col)
        # 上桅（在下桅前面）、頂桅（在上桅前面），各自的 masthead 黑
        for z in range(zp, ztt + 1):
            disc(z, ax_T(z), r_T(z), BLACK if z >= zxt else SPAR)
        for z in range(zxt, ztr + 1):
            disc(z, ax_G(z), r_G(z), SPAR)
        for z in (ztr + 1, ztr + 2):
            disc(z, ax_G(ztr), r_G(ztr) + 1.2, TRUCK)                      # truck
        # top（平台 2 格厚、前緣圓、黑邊）＋ 底下的 trestletrees／crosstrees
        W, Dp = MB['top'][key]
        fw = MB['top']['fwd']
        xc = ax_L(zp)
        xa, xf = xc - (1 - fw) * Dp, xc + fw * Dp
        hw = W / 2.0

        def in_top(x, dy):
            if x < xa or x > xf or abs(dy) > hw:
                return False
            if x > xf - hw:
                return (x - (xf - hw)) ** 2 + dy * dy <= hw * hw
            return True
        for z in (zp - 1, zp):
            for x in range(int(math.floor(xa)), int(math.ceil(xf)) + 1):
                for dy in range(-int(hw) - 1, int(hw) + 2):
                    if not in_top(x, dy):
                        continue
                    if (x - ax_L(z)) ** 2 + dy * dy <= r_L(z) ** 2 or (z >= zp and (x - ax_T(z)) ** 2 + dy * dy <= r_T(z) ** 2):
                        continue
                    rim = not all(in_top(x + a, dy + b) for a, b in ((1, 0), (-1, 0), (0, 1), (0, -1)))
                    put(key, x, YC + dy, z, BLACK if rim else TOP)
        for z in (zp - 3, zp - 2):
            for x in range(int(math.floor(xa)) + 1, int(math.ceil(xf))):
                for dy in (int(math.ceil(rh)) + 1, int(math.ceil(rh)) + 2):
                    for s in (1, -1):
                        if in_top(x, s * dy):
                            put(key, x, YC + s * dy, z, BLACK)                     # trestletrees
            for xb in (xc - 0.3 * Dp, xc + 0.15 * Dp, xc + 0.45 * Dp):
                for x in (int(round(xb)), int(round(xb)) + 1):
                    for dy in range(-int(hw) + 2, int(hw) - 1):
                        if in_top(x, dy) and (x - ax_L(z)) ** 2 + dy * dy > r_L(z) ** 2:
                            put(key, x, YC + dy, z, BLACK)                     # crosstrees
        # caps：下桅頂（套住上桅）、上桅頂（套住頂桅）
        for (z1, ra, rb, axa, axb) in ((zlt, rh, rt0, ax_L, ax_T), (ztt, rth, rg0, ax_T, ax_G)):
            for z in range(z1 - 2, z1 + 1):
                for x in range(int(math.floor(axa(z) - ra)) - 1, int(math.ceil(axb(z) + rb)) + 2):
                    for dy in range(-int(math.ceil(max(ra, rb))) - 1, int(math.ceil(max(ra, rb))) + 2):
                        inb = (x - axb(z)) ** 2 + dy * dy <= (r_T(z) if axb is ax_T else r_G(z)) ** 2
                        if not inb:
                            put(key, x, YC + dy, z, BLACK, force=True)
        # 上桅頂的 crosstrees
        spread = MB['crosstrees'][key]
        for z in (zxt - 1, zxt):
            for x in range(int(round(ax_T(z))) - 6, int(round(ax_T(z))) + 7):
                for s in (1, -1):
                    for dy in (int(math.ceil(rth)) + 1, int(math.ceil(rth)) + 2):
                        put(key, x, YC + s * dy, z, BLACK)
            for xb in (ax_T(z) - 4, ax_T(z) + 4):
                for x in (int(round(xb)), int(round(xb)) + 1):
                    for dy in range(-spread, spread + 1):
                        if (x - ax_T(z)) ** 2 + dy * dy > r_T(z) ** 2:
                            put(key, x, YC + dy, z, BLACK)

    for key in ('main', 'fore', 'mizzen'):
        build(key)

    # ── 艏斜桅＋jib-boom＋根部墊木 ──
    BS = plan['masts']['bowsprit']
    BB = MB['bowsprit']
    ang = math.radians(BS['angle_deg'])
    u = np.array([math.cos(ang), 0.0, math.sin(ang)])
    w = np.array([-math.sin(ang), 0.0, math.cos(ang)])
    Hh = np.array([BS['heel_x'], YC, BS['heel_z']], float)
    Lb, Lj = BS['length'], BS['jibboom']
    rb0, rb1 = BB['r']
    rj0, rj1 = BB['jib_r']
    sj0 = Lb * BB['jib_start']
    Jh = Hh + sj0 * u + (rb0 + (rb1 - rb0) * BB['jib_start'] + rj0) * w   # jib-boom 的軸：貼在艏斜桅上面

    def spar_cells(P0, L, ra, rb):
        out = []
        lo = np.minimum(P0, P0 + L * u) - 8
        hi = np.maximum(P0, P0 + L * u) + 8
        for x in range(int(lo[0]), int(hi[0]) + 1):
            for z in range(int(lo[2]), int(hi[2]) + 1):
                for dy in range(-8, 9):
                    q = np.array([x, YC + dy, z], float) - P0
                    s = float(q @ u)
                    if s < 0 or s > L:
                        continue
                    d = np.linalg.norm(q - s * u)
                    if d <= ra + (rb - ra) * s / L:
                        out.append((x, YC + dy, z, s))
        return out
    for x, y, z, s in spar_cells(Hh, Lb, rb0, rb1):
        put('bowsprit', x, y, z, BLACK if s > Lb - 4 else SPAR)
    for x, y, z, s in spar_cells(Jh, Lj, rj0, rj1):
        put('bowsprit', x, y, z, SPAR)
    # cap：艏斜桅頂端套住 jib-boom
    for x, y, z, s in spar_cells(Hh + (Lb - 4) * u, 4, rb1 + 1.2, rb1 + 1.2):
        put('bowsprit', x, y, z, BLACK)
    for x, y, z, s in spar_cells(Jh + (Lb - 4 - sj0) * u, 4, rj0 + 1.2, rj0 + 1.2):
        put('bowsprit', x, y, z, BLACK)
    # 墊木：根部底下到上甲板（每一欄從甲板面往上填到艏斜桅底）
    sx0, sx1, sh = BB['step']
    step = 0
    colmin = {}
    for (x, y, z) in parts['bowsprit']:
        colmin[(x, y)] = min(z, colmin.get((x, y), 10 ** 6))
    for x in range(sx0, sx1 + 1):
        for dy in range(-sh, sh + 1):
            if (x, YC + dy) not in colmin:
                continue
            zb = colmin[(x, YC + dy)] - 1
            z = zb
            while z > 0 and not solid(x, YC + dy, z):
                z -= 1
            for zz in range(z + 1, zb + 1):
                if (x, YC + dy, zz) not in parts['bowsprit']:
                    parts['bowsprit'][(x, YC + dy, zz)] = STEP
                    step += 1

    # ── 帆桁（每根一件子作品；沒轉、沿 y）──
    YD = MB['yards']
    yards = []

    def seg_of(key, yk):
        return 'lower' if yk in ('course', 'crossjack') else 'top' if yk == 'topsail' else 'tg'
    for key in ('fore', 'main', 'mizzen'):
        for yk, (L, src) in rows[key]['yards'].items():
            if yk in ('gaff', 'boom'):
                continue
            L = int(L) | 1                                               # 奇數 ⇒ 有正中那一格
            zy = spars[key]['yard_z'][yk]
            sg = seg_of(key, yk)
            rr = L / float(YD['dia_ratio']) / 2.0
            R = max(1, int(math.ceil(rr)))
            xm = geo[key]['ax'][sg](zy) + geo[key]['r'][sg](zy)
            yards.append({'name': '%s-%s' % (key, yk), 'mast': key, 'yard': yk, 'L': L, 'r': rr, 'R': R, 'z': zy, 'x': int(math.floor(xm)) + R + 1,
                          'sail': None if yk == 'crossjack' else '%s-%s' % (key, yk), 'src': src})
    sps = Lb * MB['spritsail']['at']
    Lsp = int(BS['spritsail_yard']) | 1
    rsp = Lsp / float(YD['dia_ratio']) / 2.0
    Rsp = max(1, int(math.ceil(rsp)))
    csp = Hh + sps * u - (rb0 + (rb1 - rb0) * sps / Lb + Rsp + 1) * w
    yards.append({'name': 'bowsprit-spritsail', 'mast': 'bowsprit', 'yard': 'spritsail', 'L': Lsp, 'r': rsp, 'R': Rsp, 'z': int(round(csp[2])), 'x': int(round(csp[0])),
                  'sail': None, 'src': 'spritsail yard 79-10 ＝ 22.24 m（Mejías Tavero 1793）'})
    ycells = {}
    for yd in yards:
        L, R, rr = yd['L'], yd['R'], yd['r']
        c = (L - 1) // 2
        arm = int(round(L * YD['arm'][yd['yard']]))
        cells = {}
        for y in range(L):
            s = abs(y - c) / float(c)
            r = max(0.5, rr * interp_k(MB, s))
            for x in range(2 * R + 1):
                for z in range(2 * R + 1):
                    if (x - R) ** 2 + (z - R) ** 2 <= r * r:
                        cells[(x, y, z)] = YD['colors']['tip'] if y in (0, L - 1) else YD['colors']['spar']
        an = {'pivot': [R, c, R], 'sling': [R, c, R + 1], 'arm-P': [R, 1, R], 'arm-S': [R, L - 2, R],
              'earing-P': [R, arm, R + 1], 'earing-S': [R, L - 1 - arm, R + 1]}
        k = YD['jackstay']
        while c - k > arm:
            an['jackstay-P%d' % k] = [R, c - k, R + 1]
            an['jackstay-S%d' % k] = [R, c + k, R + 1]
            k += YD['jackstay']
        theta = YD['brace'][yd['yard']]
        yd.update({'frame': [2 * R + 1, L, 2 * R + 1], 'anchors': an, 'arm': arm, 'rotate_z': theta,
                   'model_at': [yd['x'] + 0.5, YC + 0.5, yd['z'] + 0.5], 'pivot': [R + 0.5, c + 0.5, R + 0.5]})
        ycells[yd['name']] = cells
    # spanker gaff、boom：jaws 貼在後桅後面、沿 −x（往船尾），角度做進格子（遊戲只繞 z 轉）；pivot ＝ 後桅在 jaws 高度的軸心那一格
    for yk in ('gaff', 'boom'):
        SPK = MB['spanker'][yk]
        L = int(rows['mizzen']['yards'][yk][0])
        zj = SPK['jaws_z']
        axm = geo['mizzen']['ax']['lower'](zj)
        xj = axm - geo['mizzen']['r']['lower'](zj) - 1.0
        phi = math.radians(SPK['angle'])
        d = np.array([-math.cos(phi), 0.0, math.sin(phi)])
        P0 = np.array([xj, YC, zj + 0.0])
        cw = {}
        for x in range(int(xj - L * math.cos(phi)) - 4, int(xj) + 3):
            for z in range(zj - 4, int(zj + L * math.sin(phi)) + 5):
                for dy in range(-3, 4):
                    q = np.array([x, YC + dy, z], float) - P0
                    s = float(q @ d)
                    if s < 0 or s > L:
                        continue
                    r = SPK['r'] * (1 - (1 - SPK['taper']) * s / L)
                    if np.linalg.norm(q - s * d) <= max(0.5, r):
                        cw[(x, YC + dy, z)] = YD['colors']['spar']
        pv = (int(math.floor(axm)), YC, zj)
        allx = [k[0] for k in cw] + [pv[0]]
        ally = [k[1] for k in cw]
        allz = [k[2] for k in cw] + [pv[2]]
        org = [min(allx), min(ally), min(allz)]
        size = [max(allx) - org[0] + 1, max(ally) - org[1] + 1, max(allz) - org[2] + 1]
        loc = {(x - org[0], y - org[1], z - org[2]): c for (x, y, z), c in cw.items()}

        def top_at(s):
            p = P0 + s * d
            x = int(round(p[0]))
            zs = [k[2] for k in cw if k[0] == x and k[1] == YC]
            return [x - org[0], YC - org[1], max(zs) - org[2]] if zs else None
        an = {'pivot': [pv[0] - org[0], YC - org[1], zj - org[2]]}
        if yk == 'gaff':
            an['throat'] = top_at(1.0)
            an['peak'] = top_at(L - 1.0)
            k = 8
            while k < L - 4:
                an['top-%d' % k] = top_at(float(k))
                k += 8
        else:
            an['jaws'] = top_at(1.0)
            an['end'] = top_at(L - 1.0)
            k = 8
            while k < L - 4:
                an['foot-%d' % k] = top_at(float(k))
                k += 8
        an = {k2: v for k2, v in an.items() if v is not None}
        yards.append({'name': 'mizzen-%s' % yk, 'mast': 'mizzen', 'yard': yk, 'L': L, 'r': SPK['r'], 'z': zj, 'sail': 'spanker',
                      'frame': size, 'anchors': an, 'rotate_z': 0, 'model_at': [pv[0] + 0.5, YC + 0.5, zj + 0.5],
                      'pivot': [an['pivot'][0] + 0.5, an['pivot'][1] + 0.5, an['pivot'][2] + 0.5], 'origin': org, 'src': rows['mizzen']['yards'][yk][1]})
        ycells['mizzen-%s' % yk] = loc

    # ── 模型上的點（世界座標）：繞 pivot 轉 rotate_z ──
    def world_pts(yd, theta=None):
        th = math.radians(yd['rotate_z'] if theta is None else theta)
        out = {}
        for nm, (ax, ay, az) in yd['anchors'].items():
            px, py, pz = ax + 0.5 - yd['pivot'][0], ay + 0.5 - yd['pivot'][1], az + 0.5 - yd['pivot'][2]
            out[nm] = [round(yd['model_at'][0] + px * math.cos(th) - py * math.sin(th), 3),
                       round(yd['model_at'][1] + px * math.sin(th) + py * math.cos(th), 3), round(yd['model_at'][2] + pz, 3)]
        return out
    if probe:
        nm, deg = probe.split(':')
        yd = next(v for v in yards if v['name'] == nm)
        a, b = world_pts(yd), world_pts(yd, float(deg))
        print(json.dumps({'probe': probe, 'arm-S': [a['arm-S'], b['arm-S']], 'arm-P': [a['arm-P'], b['arm-P']],
                          'moved': round(math.dist(a['arm-S'], b['arm-S']), 3)}, ensure_ascii=False))
        return

    # ── 讀數 ──
    for k, v in HITS.items():
        a = np.array(v)
        zs, cs = np.unique(a[:, 2], return_counts=True)
        print('撞到', k, len(v), 'x', a[:, 0].min(), a[:, 0].max(), 'z', dict(zip(zs.tolist(), cs.tolist())), '色', dict(zip(*[t.tolist() for t in np.unique(a[:, 3], return_counts=True)])), 'hull', int(sum(HS[x, y, z] for x, y, z, c in v)))
    R = {'hull_read': hull_when, 'cells': {k: len(v) for k, v in parts.items()}, 'hull_carve': len(carve), 'hit_other': hit_other, 'step': step}
    over = {}
    keys = list(parts)
    for i, a in enumerate(keys):
        for b in keys[i + 1:]:
            over['%s×%s' % (a, b)] = len(set(parts[a]) & set(parts[b]))
    R['overlap_between'] = over
    # 甲板孔：每一層甲板在桅那裡、mast_hit 圈裡的格（甲板那幾層 z）要嘛是甲板、要嘛是桅
    holes = {}
    for key in ('main', 'fore', 'mizzen'):
        miss = 0
        for z in range(geo[key]['z']['heel_eff'], geo[key]['z']['deck_top'] + 1):
            xa = LY.mast_axis_x(plan, key, z)
            for x in range(int(xa) - 8, int(xa) + 9):
                for dy in range(-8, 9):
                    if LY.mast_hit(plan, key, x, YC + dy, z) and not solid(x, YC + dy, z) and (x, YC + dy, z) not in parts[key]:
                        miss += 1
        holes[key] = miss
    R['deck_hole_unfilled'] = holes
    asym = {k: sum(1 for (x, y, z), c in v.items() if v.get((x, 2 * YC - y, z)) != c) for k, v in parts.items()}
    R['asym'] = asym
    # 連通（現況 ＋ 四件 − 刻）：每件的格都要連到現況；空腔 —— 每件各自的外框（往外多 3 格）裡量
    R['floating'], R['cavities'] = {}, {}
    for k, v in parts.items():
        a = np.array(list(v.keys()))
        lo = np.maximum(a.min(0) - 3, 0)
        hi = a.max(0) + 4
        U = np.zeros(tuple(hi - lo), bool)
        zz = min(hi[2], ZB)
        if zz > lo[2]:
            U[:, :, :zz - lo[2]] = S[lo[0]:hi[0], lo[1]:hi[1], lo[2]:zz]
        for q in carve:
            if all(lo[i] <= q[i] < hi[i] for i in range(3)):
                U[q[0] - lo[0], q[1] - lo[1], q[2] - lo[2]] = False
        Ub = U.copy()
        for o in parts.values():
            for q in o:
                if all(lo[i] <= q[i] < hi[i] for i in range(3)):
                    U[q[0] - lo[0], q[1] - lo[1], q[2] - lo[2]] = True
        lab, _ = ndimage.label(U)
        bl = set(np.unique(lab[Ub]).tolist()) - {0}
        R['floating'][k] = sum(1 for q in v if lab[q[0] - lo[0], q[1] - lo[1], q[2] - lo[2]] not in bl)
        R['cavities'][k] = int((ndimage.binary_fill_holes(U) & ~U).sum() - (ndimage.binary_fill_holes(Ub) & ~Ub).sum())
    R['heights'] = {k: {**geo[k]['z']} for k in geo}
    R['bowsprit'] = {'tip': [round(float(v), 1) for v in Hh + Lb * u], 'jib_tip': [round(float(v), 1) for v in Jh + Lj * u]}
    R['yards'] = [{k: v for k, v in yd.items() if k not in ('anchors',)} for yd in yards]
    R['yard_points'] = {yd['name']: world_pts(yd) for yd in yards}
    R['yard_asym'] = {}
    for yd in yards:
        cl = ycells[yd['name']]
        if yd['yard'] in ('gaff', 'boom'):
            R['yard_asym'][yd['name']] = sum(1 for (x, y, z) in cl if (x, 2 * (YC - yd['origin'][1]) - y, z) not in cl)
        else:
            R['yard_asym'][yd['name']] = sum(1 for (x, y, z) in cl if (x, yd['L'] - 1 - y, z) not in cl)
    # ── 寫檔 ──
    out = os.path.join(design, 'masks', 'masts')
    os.makedirs(out, exist_ok=True)
    lists = {}
    for k, v in parts.items():
        lists[k] = DB.write_local(os.path.join(out, k + '.vox.txt'), v, [0, 0, 0], '# 三叉戟號 %s（世界座標；子作品 at 0,0,0）\n' % NAMES[k])
    lists['hull_carve'] = DB.write_local(os.path.join(out, 'hull_carve.vox.txt'), carve, [0, 0, 0], '# 三叉戟號 艏斜桅穿過船殼那幾格（carvevox；第 4 欄 ＝ 刻之前的顏色，守門）\n') if carve else [0, None]
    for yd in yards:
        lists['yard:' + yd['name']] = DB.write_local(os.path.join(design, 'masks', 'yards', yd['name'] + '.vox.txt'), ycells[yd['name']], [0, 0, 0],
                                                     '# 三叉戟號 帆桁 %s（子作品座標，沒轉、沿 %s）\n' % (yd['name'], 'x' if yd['yard'] in ('gaff', 'boom') else 'y'))
    R['lists'] = lists
    place = {'masts': {k: {'work': '%s-%s' % (HULL, 'bowsprit' if k == 'bowsprit' else 'mast-' + k), 'title': '三叉戟號 %s' % NAMES[k], 'link': NAMES[k]} for k in parts},
             'yards': []}
    for yd in yards:
        ft = yd['L'] * 0.1 / 0.3048
        din = 2 * yd['r'] * 0.1 / 0.0254
        meta = {'kind': 'yard', 'mast': yd['mast'], 'yard': yd['yard'], 'length_ft': round(ft, 2), 'diameter_in': round(din, 1), 'pivot_anchor': 'pivot',
                'turn_axis': 'z', 'rotate_z_deg': yd['rotate_z']}
        if yd['sail']:
            meta['sail'] = yd['sail']
        place['yards'].append({'name': yd['name'], 'work': '%s-yard-%s' % (HULL, yd['name']), 'parent': place['masts'][yd['mast']]['work'],
                               'title': '三叉戟號 帆桁 %s（%.1f m）' % (yd['name'], yd['L'] * 0.1), 'frame': yd['frame'], 'anchors': yd['anchors'],
                               'model': {'name': 'yard-' + yd['name'], 'at': yd['model_at'], 'pivot': yd['pivot'], 'rotate': [0, 0, yd['rotate_z']], 'scale': 1, 'meta': meta}})
    with open(os.path.join(design, 'masts_placement.json'), 'w', encoding='utf-8', newline='\n') as f:
        json.dump(place, f, ensure_ascii=False, indent=1, default=lambda o: o.item())
    # ── 圖紙：側面（右舷看）＋ 正面（從船頭看），帆桁畫沒轉的樣子（灰線）──
    sc = 0.9
    X0, X1, Z0, Z1 = 0, 1000, 0, 760
    Wp = int((X1 - X0) * sc) + int(400 * sc) + 140
    Hp = int((Z1 - Z0) * sc) + 140
    im = Image.new('RGB', (Wp, Hp), (250, 248, 240))
    d = ImageDraw.Draw(im)
    d.text((30, 12), '三叉戟號 新圖紙 07：桅與帆桁（側面、從船頭看）　v1　帆桁畫沒轉的樣子', fill=(0, 0, 0), font=font(20))
    oy = 50
    side = {}
    proj = S.any(1)
    for x, z in np.argwhere(proj[X0:X1, :]):
        side[(x + X0, z)] = (60, 60, 60)
    for v in parts.values():
        for (x, y, z), c in v.items():
            side[(x, z)] = palette_rgb(c)
    for (x, z), c in side.items():
        X, Y = 30 + (x - X0) * sc, oy + (Z1 - z) * sc
        d.rectangle([X, Y, X + sc, Y + sc], fill=c)
    for yd in yards:
        if yd['yard'] in ('gaff', 'boom'):
            org = yd['origin']
            for (x, y, z) in ycells[yd['name']]:
                X, Y = 30 + (x + org[0] - X0) * sc, oy + (Z1 - z - org[2]) * sc
                d.rectangle([X, Y, X + sc, Y + sc], fill=(30, 30, 30))
        else:
            X, Y = 30 + (yd['x'] - X0) * sc, oy + (Z1 - yd['z']) * sc
            d.rectangle([X - 2, Y - 1, X + 2, Y + 1], fill=(200, 0, 0))
    ox = 30 + int((X1 - X0) * sc) + 60
    front = {}
    projf = S.any(0)
    for y, z in np.argwhere(projf):
        front[(y, z)] = (60, 60, 60)
    for v in parts.values():
        for (x, y, z), c in v.items():
            front[(y, z)] = palette_rgb(c)
    for yd in yards:
        if yd['yard'] in ('gaff', 'boom'):
            continue
        c = (yd['L'] - 1) // 2
        for y in range(YC - c, YC + c + 1):
            front[(y, yd['z'])] = (30, 30, 30)
    for (y, z), c in front.items():
        X, Y = ox + y * sc, oy + (Z1 - z) * sc
        d.rectangle([X, Y, X + sc, Y + sc], fill=c)
    d.text((30, oy + (Z1 - Z0) * sc + 10), '主桅 truck z %d、前桅 %d、後桅 %d；艏斜桅尖 x %.0f、jib-boom 尖 x %.0f；帆桁 %d 根（紅點 ＝ 方帆桁中心）' % (
        geo['main']['z']['truck'], geo['fore']['z']['truck'], geo['mizzen']['z']['truck'], R['bowsprit']['tip'][0], R['bowsprit']['jib_tip'][0], len(yards)), fill=(0, 0, 0), font=font(16))
    im.save(os.path.join(design, 'sheet07_masts_v1.png'))
    with open(os.path.join(design, 'verify_masts.json'), 'w', encoding='utf-8', newline='\n') as f:
        json.dump(R, f, ensure_ascii=False, indent=1, default=lambda o: o.item())
    print(json.dumps({k: R[k] for k in ('hull_read', 'cells', 'hull_carve', 'hit_other', 'step', 'overlap_between', 'deck_hole_unfilled', 'asym', 'floating',
                                         'cavities', 'bowsprit', 'yard_asym')}, ensure_ascii=False, default=lambda o: o.item()))


if __name__ == '__main__':
    main()
