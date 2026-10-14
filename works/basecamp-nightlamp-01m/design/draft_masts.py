# 新圖紙 14 桅杆 v1（階段十三，TASK-0538）：plan.json masts（軸、斜度、總高）＋ mastworks（比例、半徑、顏色）＋ 組裝件 export list（草稿開著）＋ 船殼 export list
#   ⇒ masks/masts/{fore,main,mizzen,bowsprit}.vox.txt（各一件子作品、船殼座標、關聯 at 0,0,0）、masks/masts/hull_bowsprit_carve.vox.txt（船殼要刻的，帶顏色）、
#     verify_masts.json、sheet14_masts_v1.png
# 用法：python -I draft_masts.py <design 資料夾> <組裝件 export list> <船殼 export list>
#   · 每根桅一條斜的軸：X(z) ＝ Xm − (z − Zref)·tan(rake)，Zref ＝ 上甲板在 Xm 的走的那一格 —— 跟甲板開桅孔同一條（draft_decks.mast_X）。
#   · 下桅踩在 keelson 上（step 3 格）；下桅到 hounds 是圓的、masthead 方的；topmast、topgallant 疊在前一節前面；tops 水平 D 形。
#   · 只放在空著的格；桅杆碰到現有格 ⇒ 不放、數出來。bowsprit：碰到船殼 ⇒ 船殼刻掉（另一份清單）、碰到別的（船首像、甲板）⇒ 跟往上抬到不碰。
import sys, os, json, hashlib, math
import numpy as np
from scipy import ndimage
from PIL import Image, ImageDraw

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import draft_planking as DP      # noqa: E402

YC = 160


class Masts:
    def __init__(s, design, asm_list, hull_list):
        s.design = design
        s.plan = json.load(open(os.path.join(design, 'plan.json'), encoding='utf-8'))
        s.M = s.plan['masts']
        s.P = s.plan['mastworks']
        s.occ = DP.read_list(asm_list)
        assert len(s.occ) == s.P['assembly_cells'], ('組裝件格數對不上', len(s.occ), s.P['assembly_cells'])
        s.hull = set(DP.read_list(hull_list))
        assert len(s.hull) == s.P['hull_cells'], ('船殼格數對不上', len(s.hull))
        s.sha = {'assembly': hashlib.sha256(open(asm_list, 'rb').read()).hexdigest(), 'hull': hashlib.sha256(open(hull_list, 'rb').read()).hexdigest()}
        dk = json.load(open(os.path.join(design, 'decks.json'), encoding='utf-8'))
        s.X0d, s.upper = dk['X0'], dk['decks']['upper']
        s.spar = dk['decks']['spar']
        m = DP.Model(design)
        s.cpm, s.X0, s.Zk = m.cx.cpm, m.cx.X0, m.cx.Zk
        s.parts, s.log = {}, {}

    def frame(s, m):
        th = math.radians(s.M['rake_deg'][m])
        Xm = s.X0 + s.M['x'][m] * s.cpm
        Zref = int(s.upper[int(round(Xm)) - s.X0d])
        X = lambda z: Xm - (z - Zref) * math.tan(th)
        d = np.array([-math.sin(th), 0.0, math.cos(th)])
        f = np.array([math.cos(th), 0.0, math.sin(th)])
        return th, d, f, X

    def scan(s, H, d, f, s0, s1, rmax, test):
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

    def add(s, part, cells, color, why):
        n = 0
        for c in cells:
            if c not in s.parts[part]:
                s.parts[part][c] = color
                n += 1
        s.log[part].setdefault('members', {})
        s.log[part]['members'][why] = s.log[part]['members'].get(why, 0) + n

    def mast(s, m):
        P, C, R = s.P, s.P['colors'], s.P['ratios']
        s.parts[m], s.log[m] = {}, {}
        th, d, f, X = s.frame(m)
        xk = int(round(X(30)))
        zk = next(z for z in range(59, 0, -1) if (xk, YC, z) in s.occ and (xk, YC, z + 1) not in s.occ)   # keelson 頂（下甲板以下、中線往下第一格實心）
        zh = zk + 1 + P['step']
        H = np.array([X(zh), 0.0, zh])
        Ztruck = s.Zk + s.M['lengths_above_keel'][m] * s.cpm
        S = (Ztruck - zh) / math.cos(th)
        L1 = R['lower'] * S
        sh1 = R['hounds'] * L1
        L2 = R['topmast'] * L1
        sh2 = sh1 + R['hounds'] * L2
        r0 = P['radius'][m]
        rh = r0 * R['head_taper']
        rt = r0 * R['topmast_r']
        rt2 = rt * R['head_taper']
        rg = rt * R['topgallant_r']
        # step
        hw = int(r0 + 2)
        step = [(x, y, z) for x in range(int(H[0] - r0 - 2), int(H[0] + r0 + 3)) for y in range(YC - hw, YC + hw + 1) for z in range(zk + 1, zh)]
        s.add(m, step, C['step'], 'step')
        # 下桅：上甲板以下等粗、往上收到 hounds；masthead 方的
        z_up = int(s.upper[int(round(X(100))) - s.X0d])
        s_up = (z_up - zh) / math.cos(th)
        rl = lambda sp: r0 if sp <= s_up else r0 + (rh - r0) * min(1.0, (sp - s_up) / max(1e-6, sh1 - s_up))
        s.add(m, s.scan(H, d, f, 0, sh1, r0, lambda sp, u, v: u * u + v * v <= rl(sp) ** 2), C['spar'], 'lower')
        # masthead 方的那一段從 hounds 往下 2 格起 —— trestletrees 在 top 底下一格，要貼著方的面（v1 前桅 top 跟圓的那段只有斜角相接、自己浮成一塊）
        s.add(m, s.scan(H, d, f, sh1 - 2, L1, rh + 1, lambda sp, u, v: abs(u) <= rh and abs(v) <= rh), C['black'], 'masthead')
        hp = P['hoops']
        rings = []
        for k in range(int(math.ceil((s_up + 3) / hp['every'])), int(sh1 // hp['every']) + 1):
            sk = k * hp['every']
            rings += s.scan(H, d, f, sk - 0.5, sk + 0.5, r0 + 1, lambda sp, u, v, sk=sk: abs(sp - sk) <= 0.5 and rl(sp) ** 2 < u * u + v * v <= (rl(sp) + 0.75) ** 2)
        s.add(m, rings, C['black'], 'hoops')
        # cap＋topmast（在 masthead 前面）
        u_tm = rh + rt + 0.5
        s.add(m, s.scan(H, d, f, L1 - 1, L1 + 1.5, u_tm + rt + 3, lambda sp, u, v: -rh - 1.5 <= u <= u_tm + rt + 1.5 and abs(v) <= rh + 1.5), C['black'], 'cap')
        Ht = H + u_tm * f
        rtf = lambda sp: rt + (rt2 - rt) * min(1.0, max(0.0, (sp - sh1) / max(1e-6, sh2 - sh1)))
        s.add(m, s.scan(Ht, d, f, sh1, sh2, rt, lambda sp, u, v: u * u + v * v <= rtf(sp) ** 2), C['spar'], 'topmast')
        s.add(m, s.scan(Ht, d, f, sh2 - 2, sh1 + L2, rt2 + 1, lambda sp, u, v: abs(u) <= rt2 and abs(v) <= rt2), C['black'], 'topmast_head')
        # topgallant／royal（在 topmast head 前面）＋ truck
        u_tg = rt2 + rg + 0.5
        Hg = Ht + u_tg * f
        Lg = S - sh2
        s.add(m, s.scan(Hg, d, f, sh2, S - 1.5, rg + 0.6, lambda sp, u, v: u * u + v * v <= max(0.6, rg * (1 - 0.35 * (sp - sh2) / Lg)) ** 2), C['spar'], 'topgallant')
        s.add(m, s.scan(Hg, d, f, S - 1.5, S, rg + 2, lambda sp, u, v: u * u + v * v <= (rg + 1.0) ** 2), C['black'], 'truck')
        s.add(m, s.scan(Ht, d, f, sh1 + L2 - 1, sh1 + L2 + 1.5, u_tg + rg + 3, lambda sp, u, v: -rt2 - 1 <= u <= u_tg + rg + 1 and abs(v) <= rt2 + 1), C['black'], 'topmast_cap')
        # top：水平 D 形（前緣圓）、lubber's hole、trestletrees／crosstrees
        p_h = H + sh1 * d
        z_top = int(round(p_h[2]))
        W = R['top_w'] * L1
        D_ = R['top_d'] * W
        xc = p_h[0] + (u_tm / 2) * math.cos(th)
        lub_a0, lub_a1 = -rh - 2 - u_tm / 2, u_tm / 2 + rt + 2
        lub_w = max(rh, rt) + 0.15 * W

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
                plat.append((x, y, z_top))
                if any(not in_top(a + da, v + dv) for da, dv in ((1, 0), (-1, 0), (0, 1), (0, -1))):
                    rim.append((x, y, z_top + 1))
        s.add(m, plat, C['top'], 'top')
        s.add(m, rim, C['black'], 'top_rim')
        tt = []
        v1 = int(math.floor(rh)) + 1
        for x in range(int(xc - D_ / 2 + 2), int(xc + D_ / 2 - 1)):
            for v in (v1, v1 + 1):
                for sg in (1, -1):
                    tt.append((x, YC + sg * v, z_top - 1))
        hw2 = int(W / 2 - 3)
        for a in (-D_ / 3, u_tm, D_ / 3):
            for y in range(YC - hw2, YC + hw2 + 1):
                tt.append((int(round(xc + a)), y, z_top - 1))
        s.add(m, tt, C['black'], 'trestle_cross_trees')
        p2 = Ht + sh2 * d
        z2 = int(round(p2[2]))
        span = R['crosstrees'] * W
        ct = []
        for a in (-2, 2):
            for y in range(YC - int(span / 2), YC + int(span / 2) + 1):
                ct.append((int(round(p2[0] + a)), y, z2 - 1))
        v2 = int(math.floor(rt2)) + 1
        for x in range(int(p2[0] - 3), int(p2[0] + 4)):
            for sg in (1, -1):
                ct.append((x, YC + sg * v2, z2 - 1))
        s.add(m, ct, C['black'], 'crosstrees')
        s.log[m].update({'keelson_top': zk, 'heel': [round(float(H[0]), 2), zh], 'span_cells': round(S, 1),
                         'lengths': {'lower': round(L1, 1), 'topmast': round(L2, 1), 'topgallant_royal': round(Lg, 1)},
                         'heights': {'top': z_top, 'crosstrees': z2, 'truck': int(round((Hg + S * d)[2]))},
                         'radii': {'lower': r0, 'head_half': round(rh, 2), 'topmast': round(rt, 2), 'topgallant': round(rg, 2)},
                         'top_size': [round(W, 1), round(D_, 1)]})

    def bowsprit(s):
        B, C, R = s.P['bowsprit'], s.P['colors'], s.P['ratios']
        cpm = s.cpm
        phi = math.radians(s.M['bowsprit']['angle_deg'])
        d = np.array([math.cos(phi), 0.0, math.sin(phi)])
        n = np.array([-math.sin(phi), 0.0, math.cos(phi)])
        Xh = B['heel_X']
        rb = B['r']
        Lb = s.M['bowsprit']['outboard'] * cpm + (B['stem_X'] - Xh) / math.cos(phi)
        Lj = s.M['bowsprit']['jibboom_outboard'] * cpm / R['jib_out']
        rj = rb * R['jib_r']
        best = None
        for zh in range(B['heel_Z_min'], B['heel_Z_min'] + 25):
            H = np.array([Xh, 0.0, zh])
            rf = lambda sp: rb + (rb * R['bowsprit_end'] - rb) * max(0.0, min(1.0, sp / Lb))
            cells = s.scan(H, d, n, 0, Lb, rb, lambda sp, u, v: u * u + v * v <= rf(sp) ** 2)
            Hj = H + (rb * R['bowsprit_end'] + rj + 0.4) * n + (Lb - (1 - R['jib_out']) * Lj) * d
            jcells = s.scan(Hj, d, n, 0, Lj, rj, lambda sp, u, v: u * u + v * v <= max(0.6, rj - 0.35 * rj * sp / Lj) ** 2)
            cap = s.scan(H, d, n, Lb - 1.5, Lb + 1.5, rb + 2 * rj + 4,
                         lambda sp, u, v: -rb * R['bowsprit_end'] - 1 <= u <= rb * R['bowsprit_end'] + 2 * rj + 1.5 and abs(v) <= rb * R['bowsprit_end'] + 1)
            allc = set(cells) | set(jcells) | set(cap)
            other = [c for c in allc if c in s.occ and c not in s.hull]
            if not other:
                best = (zh, H, cells, jcells, cap, Hj)
                break
        assert best, 'bowsprit 抬到頂也還碰到船首像／甲板'
        zh, H, cells, jcells, cap, Hj = best
        s.parts['bowsprit'], s.log['bowsprit'] = {}, {}
        s.add('bowsprit', cells, C['spar'], 'bowsprit')
        s.add('bowsprit', jcells, C['spar'], 'jibboom')
        s.add('bowsprit', cap, C['black'], 'cap')
        # 跟底下的 step：坐在前甲板上
        zd = int(s.spar[Xh - s.X0d])
        st = []
        for x in range(Xh - 3, Xh + 4):
            zb = H[2] + (x - Xh) * math.tan(phi) - rb
            for y in range(YC - int(rb + 1), YC + int(rb + 1) + 1):
                for z in range(zd, int(math.floor(zb)) + 1):
                    st.append((x, y, z))
        s.add('bowsprit', st, C['step'], 'step')
        s.log['bowsprit'].update({'heel': [Xh, zh], 'heel_Z_tried_from': B['heel_Z_min'], 'steeve_deg': s.M['bowsprit']['angle_deg'],
                                  'length': round(Lb, 1), 'jibboom_length': round(Lj, 1),
                                  'bowsprit_tip_XZ': [round(float(v), 1) for v in (H + Lb * d)[[0, 2]]],
                                  'jibboom_tip_XZ': [round(float(v), 1) for v in (Hj + Lj * d)[[0, 2]]]})

    def resolve(s):
        s.carve = {}
        s.collide = {}
        seen = {}
        for p, cells in s.parts.items():
            hit = [c for c in cells if c in s.occ]
            by = {}
            for c in hit:
                k = 'hull' if c in s.hull else 'other'
                by[k] = by.get(k, 0) + 1
                if p == 'bowsprit' and c in s.hull:
                    s.carve[c] = s.occ[c]
                else:
                    del cells[c]
            s.collide[p] = by
            for c in cells:
                assert c not in seen, ('兩件重疊', c, seen.get(c), p)
                seen[c] = p

    def check(s):
        """每一件自己 1 塊？放進去之後（刻掉船殼那幾格）全部 1 塊、空腔 0？鏡像？"""
        s.checks = {}
        for p, cells in s.parts.items():
            a = np.array(list(cells))
            lo = a.min(0) - 1
            g = np.zeros(a.max(0) - lo + 2, bool)
            g[tuple((a - lo).T)] = True
            _, n = ndimage.label(g)
            mir = sum(1 for (x, y, z) in cells if (x, 320 - y, z) not in cells)
            s.checks[p] = {'cells': len(cells), 'components_self': int(n), 'mirror_missing': mir}
        allc = set(s.occ) - set(s.carve)
        for cells in s.parts.values():
            allc |= set(cells)
        a = np.array(list(allc))
        lo = a.min(0) - 1
        g = np.zeros(a.max(0) - lo + 2, bool)
        g[tuple((a - lo).T)] = True
        _, s.n_total = ndimage.label(g)
        pad = np.pad(g, 1)
        lab, _ = ndimage.label(~pad)
        s.cav = int(((lab != lab[0, 0, 0]) & ~pad).sum())
        s.total = len(allc)

    def write(s):
        out = os.path.join(s.design, 'masks', 'masts')
        os.makedirs(out, exist_ok=True)
        s.files = {}
        lists = dict(s.parts)
        lists['hull_bowsprit_carve'] = s.carve
        for name, cells in lists.items():
            p = os.path.join(out, name + '.vox.txt')
            body = ''.join('%d,%d,%d,%d\n' % (c[0], c[1], c[2], v) for c, v in sorted(cells.items()))
            note = '船殼要刻的（bowsprit 穿過船頭；carvevox 帶顏色守門）' if name == 'hull_bowsprit_carve' else '子作品、船殼座標、關聯 at 0,0,0；stampvox at=0,0,0'
            open(p, 'w', encoding='utf-8', newline='\n').write('# 夜燈號 %s —— %s（新圖紙 14 v1，draft_masts.py 產；%d 格）\n' % (name, note, len(cells)) + body)
            s.files[name] = {'cells': len(cells), 'sha256': hashlib.sha256(open(p, 'rb').read()).hexdigest()}


def render_sheet(F, path):
    """右舷側面（y > 160 每一欄最外面那一格）：現況淡色、桅杆原色。"""
    sc = 1
    X0, X1, Z1 = 40, 1000, 560
    img = np.full((Z1, X1 - X0, 3), 250, np.uint8)
    base = np.zeros((X1 - X0, Z1), bool)
    for (x, y, z) in F.occ:
        if X0 <= x < X1 and z < Z1:
            base[x - X0, z] = True
    img[base.T[::-1]] = (215, 208, 196)
    for p, cells in F.parts.items():
        for (x, y, z), c in cells.items():
            if X0 <= x < X1 and z < Z1:
                img[Z1 - 1 - z, x - X0] = DP.rgb332(c)
    im = Image.fromarray(img)
    ImageDraw.Draw(im).text((6, 4), 'sheet 14 v1  masts & bowsprit (starboard profile, bow right)', fill=(0, 0, 0))
    im.save(path)


def main():
    design, asm, hull = sys.argv[1], sys.argv[2], sys.argv[3]
    F = Masts(design, asm, hull)
    for m in ('mizzen', 'main', 'fore'):
        F.mast(m)
    F.bowsprit()
    F.resolve()
    F.check()
    F.write()
    v = {'title': F.P['title'], 'base': F.sha, 'log': F.log, 'collide_dropped_or_carved': F.collide, 'checks': F.checks,
         'hull_carve': len(F.carve), 'components_after': int(F.n_total), 'cavities_after': F.cav,
         'expect_assembly_after': F.total, 'files': F.files}
    json.dump(v, open(os.path.join(design, 'verify_masts.json'), 'w', encoding='utf-8', newline='\n'), ensure_ascii=False, indent=1)
    render_sheet(F, os.path.join(design, 'sheet14_masts_v1.png'))
    print(json.dumps({k: v[k] for k in ('collide_dropped_or_carved', 'checks', 'hull_carve', 'components_after', 'cavities_after', 'expect_assembly_after')}, ensure_ascii=False))
    for k, l in F.log.items():
        print(k, json.dumps({a: b for a, b in l.items() if a != 'members'}, ensure_ascii=False))


if __name__ == '__main__':
    main()
