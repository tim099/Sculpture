# 餘燼號 階段九 船首像「浴火的鳳凰」（plan.json head_build.figurehead；新圖紙 10b）—— 原創設計
#   站在 knee 尖端（knee 前緣最高那格的上面）：身體往前上方傾、頭抬起看前方（在艏斜桅底下）、翅膀往後往上張開、
#   尾羽像火舌一樣順著 cutwater 前緣往下流（黃 → 橘 → 紅 → 暗紅：從火到餘燼）。
#   每個部位是一組膠囊／球（帶符號距離 ≤ 0 ＝ 在裡面），只放在現況（組裝件藏起這一階段的關聯 ＋ 本階段的 knee 與兩舷裝飾）是空氣的格；
#   撞到的照部位記數（不硬塞）。左右對稱：dy ＝ y − 160 只用 |dy|，鏡像差應為 0。
#   ⇒ masks/head/figurehead.vox.txt（世界座標、子作品 at 0,0,0）、verify_figurehead.json、sheet10b_figurehead_v1.png
# 用法：python -I draft_figurehead.py <design 資料夾>（先跑 draft_head.py）
import sys, os, json, hashlib, math, collections
import numpy as np
from scipy import ndimage
from PIL import Image, ImageDraw

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import draft_profile as DP                               # noqa: E402
from draft_ladders import existing_links, export_hidden  # noqa: E402

YC = 160
PAPER, INK = (250, 248, 240), (30, 30, 30)


def load_vox(p):
    return np.loadtxt(p, delimiter=',', comments='#', dtype=np.int32, ndmin=2, encoding='utf-8')


def seg_dist(p, a, b):
    """點 p 到線段 ab 的距離與參數 t（p: (...,3)）"""
    a, b = np.asarray(a, float), np.asarray(b, float)
    ab = b - a
    L2 = ab @ ab
    if L2 == 0:                                    # 球（兩端同一點）
        return np.linalg.norm(p - a, axis=-1), np.zeros(p.shape[:-1])
    t = np.clip(((p - a) @ ab) / L2, 0, 1)
    q = a + t[..., None] * ab
    return np.linalg.norm(p - q, axis=-1), t


class Figure:
    def __init__(s, design):
        s.design = design
        s.plan = json.load(open(os.path.join(design, 'plan.json'), encoding='utf-8'))
        s.H = s.plan['head_build']
        s.F = s.H['figurehead']
        have = set(existing_links(s.H['assembly']))
        s.hidden = [h for h in s.H['hide_links'] if h in have]
        a = export_hidden(s.H['assembly'], s.hidden)
        assert len(a) == s.H['assembly_voxels'], ('組裝件現況對不上', len(a))
        bx = s.F['box']
        s.x0, s.x1, s.z0, s.z1 = bx['x'][0], bx['x'][1], bx['z'][0], bx['z'][1]
        s.y0, s.y1 = YC - bx['half_y'], YC + bx['half_y']
        m = a[(a[:, 0] >= s.x0 - 2) & (a[:, 0] <= s.x1 + 2) & (a[:, 2] >= s.z0 - 2) & (a[:, 2] <= s.z1 + 2)]
        s.W = {(int(x), int(y), int(z)): int(c) for x, y, z, c in m}
        s.read = {'hidden': s.hidden, 'voxels': int(len(a))}
        # 本階段另外兩件（knee、兩舷裝飾）
        hd = os.path.join(design, 'masks', 'head')
        s.knee = {(int(x), int(y), int(z)): int(c) for x, y, z, c in load_vox(os.path.join(hd, 'knee.vox.txt'))}
        sb = s.H['subworks']['side']['box']
        ax, ay, az = sb['at']
        my = 321 - ay - sb['size'][1]
        s.side = {}
        for x, y, z, c in load_vox(os.path.join(hd, 'side.vox.txt')):
            s.side[(int(x + ax), int(y + ay), int(z + az))] = int(c)
            s.side[(int(x + ax), int(sb['size'][1] - 1 - y + my), int(z + az))] = int(c)
        s.solid = set(s.W) | set(s.knee) | set(s.side)
        s.col = s.H['colors']
        s.cells, s.part = {}, {}
        s.hit = collections.Counter()

    def knee_front(s):
        """cutwater 前緣：每一層 z 中線那欄 knee 最前面那格的 x"""
        f = {}
        for (x, y, z) in s.knee:
            if y == YC:
                f[z] = max(f.get(z, -1), x)
        return f

    def build(s):
        F, C = s.F, s.col
        kf = s.knee_front()
        ztop = max(kf)
        s.tip = [kf[ztop], YC, ztop]
        xs = np.arange(s.x0, s.x1 + 1)
        ys = np.arange(s.y0, s.y1 + 1)
        zs = np.arange(s.z0, s.z1 + 1)
        X, Y, Z = np.meshgrid(xs, ys, zs, indexing='ij')
        P = np.stack([X, np.abs(Y - YC), Z], -1).astype(float)     # 用 |dy| ⇒ 左右對稱
        Pn = P.copy()
        best = np.full(X.shape, np.inf)
        colr = np.zeros(X.shape, np.int32)
        part = np.zeros(X.shape, np.int32)
        names = ['']

        def put(d, c, name, prio):
            """d ≤ 0 的格歸這個部位（prio 大的先放；同一格只給第一個）"""
            nonlocal best
            names.append(name)
            k = len(names) - 1
            m = (d <= 0) & (part == 0)
            colr[m] = c if np.isscalar(c) else c[m]
            part[m] = k

        def capsule(a, b, r0, r1, sy=1.0):
            q = Pn.copy()
            q[..., 1] = q[..., 1] / sy
            aa = np.array(a, float)
            bb = np.array(b, float)
            aa[1] /= sy
            bb[1] /= sy
            d, t = seg_dist(q, aa, bb)
            return d - (r0 + (r1 - r0) * t), t

        # 順序 ＝ 優先：眼 → 喙 → 頭 → 頸 → 冠 → 身體 → 翅膀 → 尾羽
        hd = F['head']
        for e in hd['eyes']:
            d, _ = capsule(e, e, 0.75, 0.75)
            put(d, C['black'], 'eye', 0)
        d, t = capsule(hd['beak'][0], hd['beak'][1], hd['beak_r'][0], hd['beak_r'][1])
        put(d, C['gold'], 'beak', 0)
        d, _ = capsule(hd['center'], hd['center'], hd['r'], hd['r'], sy=hd['sy'])
        put(d, C['orange'], 'head', 0)
        nk = F['neck']
        d, _ = capsule(nk[0], nk[1], nk[2], nk[3], sy=hd['sy'])
        put(d, C['orange'], 'neck', 0)
        for cr in F['crest']:
            d, t = capsule(cr[0], cr[1], cr[2], cr[3])
            put(d, np.where(t > 0.6, C['gold'], C['red2']), 'crest', 0)
        bd = F['body']
        d, t = capsule(bd['a'], bd['b'], bd['r'], bd['r2'], sy=bd['sy'])
        ax = np.array(bd['b'], float) - np.array(bd['a'], float)
        nrm = np.array([ax[2], 0.0, -ax[0]]) / math.hypot(ax[0], ax[2])      # 往前下方（胸口那一面）
        rel = Pn - np.array(bd['a'], float)
        off = rel @ nrm
        bcol = np.where(off > bd['chest'], C['gold'], np.where(off < -bd['back'], C['red2'], C['orange']))
        put(d, bcol, 'body', 0)
        # 翅膀：一片羽膜（v1 是一把分開的羽毛棒 ⇒ 散成 31 塊、浮空 48）—— 平面過肩膀 R、翼尖 T、後下角 E；
        #   面內用「繞 R 的角度 u（0 ＝ R→T、1 ＝ R→E）」與「離 R 的距離 ρ」：ρ ≤ 外緣（|RT| 到 |RE| 線性 ＋ bulge·sin πu）；
        #   外緣那一圈（ρ／外緣 > notch）只留每根羽毛的中段 ⇒ 後緣是一排羽尖
        wg = F['wing']
        R = np.array(wg['root'], float)
        T = np.array(wg['tip'], float)
        E = np.array(wg['end'], float)
        e1 = (T - R) / np.linalg.norm(T - R)
        nrm = np.cross(T - R, E - R)
        nrm /= np.linalg.norm(nrm)
        e2 = np.cross(nrm, e1)
        rel = Pn - R
        dpl = np.abs(rel @ nrm)
        a1, a2 = rel @ e1, rel @ e2
        th = np.arctan2(a2, a1)
        thE = math.atan2((E - R) @ e2, (E - R) @ e1)
        u = th / thE
        rho = np.hypot(a1, a2)
        LT, LE = np.linalg.norm(T - R), np.linalg.norm(E - R)
        outer = LT + (LE - LT) * np.clip(u, 0, 1) + wg['bulge'] * np.sin(np.pi * np.clip(u, 0, 1))
        rr = rho / outer
        fr = (u * wg['feathers']) % 1.0
        inside = (dpl <= wg['thick']) & (u >= -0.02) & (u <= 1.02) & (rr <= 1.0)
        notch = (rr > wg['notch']) & ((fr < wg['gap']) | (fr > 1 - wg['gap']))
        m = inside & ~notch
        lead = (np.abs(a2) <= 1.0) & (a1 >= 0)                 # 前緣（R→T 那一條）金
        c = np.where(lead | (rr > wg['bands'][1]), C['gold'], np.where(rr > wg['bands'][0], C['red2'], C['orange']))
        put(np.where(m, -1.0, 1.0), c, 'wing', 0)
        # 尾羽：火舌順著 cutwater 前緣往下（每一條是一串小膠囊；前緣 ＋ off、正弦擺動）
        tl = F['tail']
        for tg in tl['tongues']:
            dy, z_top, z_bot, off, amp, lam, ph, r0, r1 = (tg[k] for k in ('dy', 'z_top', 'z_bot', 'off', 'amp', 'wave', 'phase', 'r_top', 'r_bot'))
            zz = np.arange(z_top, z_bot - 0.01, -0.5)
            pts = []
            for z in zz:
                zi = int(round(z))
                xf = kf.get(zi, kf[min(kf, key=lambda q: abs(q - zi))])
                tt = (z_top - z) / (z_top - z_bot)
                pts.append([xf + off + amp * math.sin(2 * math.pi * (z_top - z) / lam + ph) * tt, abs(dy), z])
            for j in range(len(pts) - 1):
                tt = j / (len(pts) - 1)
                d, _ = capsule(pts[j], pts[j + 1], r0 + (r1 - r0) * tt, r0 + (r1 - r0) * (tt + 1 / len(pts)))
                band = tl['bands']
                c = C['yellow'] if tt < band[0] else C['orange'] if tt < band[1] else C['red2'] if tt < band[2] else C['red']
                put(d, c, 'tail', 0)
        # 落格（避開現況）
        for (i, j, k) in np.argwhere(part > 0):
            key = (int(xs[i]), int(ys[j]), int(zs[k]))
            nm = names[part[i, j, k]]
            if key in s.solid:
                s.hit[nm] += 1
                continue
            s.cells[key] = int(colr[i, j, k])
            s.part[key] = nm

    def verify(s):
        v = {'read': s.read, 'knee_tip': s.tip, 'cells': len(s.cells), 'by_part': dict(collections.Counter(s.part.values())),
             'colors': {str(c): sum(1 for q in s.cells.values() if q == c) for c in sorted(set(s.cells.values()))},
             'hit_existing': dict(s.hit),
             'mirror_mismatch': sum(1 for (x, y, z), c in s.cells.items() if s.cells.get((x, 2 * YC - y, z)) != c),
             'bbox': [[min(k[a] for k in s.cells), max(k[a] for k in s.cells)] for a in range(3)]}
        # 連通：鳳凰＋本階段兩件＋現況，跟現況連成一塊
        keys = list(s.solid) + list(s.cells)
        lo = np.min(np.array(keys), 0) - 1
        hi = np.max(np.array(keys), 0) + 2
        A = np.zeros(tuple(hi - lo), bool)
        for k in keys:
            A[k[0] - lo[0], k[1] - lo[1], k[2] - lo[2]] = True
        lab, n = ndimage.label(A)
        base = set(lab[k[0] - lo[0], k[1] - lo[1], k[2] - lo[2]] for k in s.solid)
        fl = [k for k in s.cells if lab[k[0] - lo[0], k[1] - lo[1], k[2] - lo[2]] not in base]
        v['floating'] = {'n': len(fl), 'by_part': dict(collections.Counter(s.part[k] for k in fl))}
        # 只看鳳凰自己：幾塊
        B = np.zeros_like(A)
        for k in s.cells:
            B[k[0] - lo[0], k[1] - lo[1], k[2] - lo[2]] = True
        v['own_components'] = int(ndimage.label(B)[1])
        s.v = v
        return v

    def write(s):
        p = os.path.join(s.design, 'masks', 'head', 'figurehead.vox.txt')
        rows = sorted((k[0], k[1], k[2], c) for k, c in s.cells.items())
        open(p, 'w', encoding='utf-8', newline='\n').write(
            '# figurehead —— 餘燼號 船首像「浴火的鳳凰」（世界座標，at=0,0,0；%d 格）\n' % len(rows) + '\n'.join('%d,%d,%d,%d' % r for r in rows) + '\n')
        s.v['file'] = {'cells': len(rows), 'sha256': hashlib.sha256(open(p, 'rb').read()).hexdigest()}


def render(T, path):
    D = dict(T.W)
    D.update(T.knee)
    D.update(T.side)
    sc = 10
    xa, xb, za, zb = 760, 822, 100, 184
    ya, yb = YC - 22, YC + 23

    def proj(axis):
        if axis == 'side':
            na, nb = xb - xa, zb - za
        elif axis == 'front':
            na, nb = yb - ya, zb - za
        else:
            na, nb = xb - xa, yb - ya
        img = np.zeros((nb, na, 3), np.uint8)
        img[:] = PAPER
        for ia in range(na):
            for ib in range(nb):
                if axis == 'side':
                    ray = [(xa + ia, y, zb - 1 - ib) for y in range(YC + 30, YC - 31, -1)]
                elif axis == 'front':
                    ray = [(x, yb - 1 - ia, zb - 1 - ib) for x in range(xb + 5, xa - 40, -1)]
                else:
                    ray = [(xa + ia, yb - 1 - ib, z) for z in range(zb + 5, za - 1, -1)]
                for k in ray:
                    if k in T.cells:
                        img[ib, ia] = DP.rgb(T.cells[k])
                        break
                    if k in D:                       # 船殼／knee／rails 畫淡一點
                        img[ib, ia] = tuple(int(v * 0.45 + 140) for v in DP.rgb(D[k]))
                        break
        return Image.fromarray(img).resize((na * sc, nb * sc), Image.NEAREST)
    side = proj('side')
    front = proj('front')
    top = proj('top')
    f12, f18 = DP.font(13), DP.font(20)
    W = 50 + side.width + 40 + front.width + 50
    H = 60 + max(side.height, front.height) + 40 + top.height + 140
    can = Image.new('RGB', (W, H), PAPER)
    dr = ImageDraw.Draw(can)
    dr.text((50, 12), '新圖紙 10b v1：船首像「浴火的鳳凰」（原創；彩 ＝ 鳳凰、淡 ＝ 船殼／knee／rails）', font=f18, fill=INK)
    can.paste(side, (50, 50))
    can.paste(front, (50 + side.width + 40, 50))
    y = 50 + max(side.height, front.height) + 20
    dr.text((50, y), '側面（x %d–%d、z %d–%d）／正前方（往船尾看）／俯視' % (xa, xb - 1, za, zb - 1), font=f12, fill=INK)
    can.paste(top, (50, y + 20))
    y += 20 + top.height + 10
    v = T.v
    for t in ('%d 格（%s）；撞到現況不放 %s；鏡像差 %d；浮空 %d；自己 %d 塊' % (
            v['cells'], '、'.join('%s %d' % kv for kv in sorted(v['by_part'].items())), v['hit_existing'], v['mirror_mismatch'],
            v['floating']['n'], v['own_components']),
              'knee 尖端 %s；外框 x %s、y %s、z %s' % (v['knee_tip'], v['bbox'][0], v['bbox'][1], v['bbox'][2])):
        dr.text((50, y), t, font=f12, fill=INK)
        y += 20
    can.save(path)


def main():
    design = sys.argv[1]
    sys.stdout.reconfigure(encoding='utf-8')
    T = Figure(design)
    T.build()
    v = T.verify()
    T.write()
    json.dump(v, open(os.path.join(design, 'verify_figurehead.json'), 'w', encoding='utf-8', newline='\n'), ensure_ascii=False, indent=1)
    render(T, os.path.join(design, 'sheet10b_figurehead_v1.png'))
    print(json.dumps(v, ensure_ascii=False, indent=1))


if __name__ == '__main__':
    main()
