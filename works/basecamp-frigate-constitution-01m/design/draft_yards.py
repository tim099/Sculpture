# 新圖紙 14（帆桁，貼進各桅杆子作品）：plan.json 的 yards 段 ＋ 四件桅杆子作品（標記 帆桁:begin）＋ 組裝件其他部件
#   ⇒ masks/yards/{fore,main,mizzen,bowsprit}.vox.txt（子作品 at 0,0,0，世界座標）、design/rig_points_yards.json（固定點）、
#      verify_yards.json、sheet14_yards_v1.png
# 用法：python -I draft_yards.py <design 資料夾>
#   · 帆桁水平、跟中線垂直，貼在那一段桅的前面（中心 x ＝ 那一層桅的最前緣 ＋ 0.5 ＋ r ⇒ 最後面那排格貼著桅）
#   · 錐度照 Steel 1794 的四分點；yardarm 端 1 格原木色
#   · gaff／boom 貼在後桅後面；spritsail yard 掛在 bowsprit 底下、cap 內側
import sys, os, json, hashlib, math, subprocess
import numpy as np
from scipy import ndimage
from PIL import Image, ImageDraw

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import draft_planking as DP        # noqa: E402
import draft_decks as DD           # noqa: E402
from draft_masts import export_list, ASSEMBLY   # noqa: E402

YC = 160
FT, IN = 3.048, 0.254


def has_mark(work, name):
    r = subprocess.run(['senate', 'cmd', 'sculpture', '--arg', 'op=work', '--arg', 'sub=marks', '--arg', 'work=' + work],
                       capture_output=True, text=True, encoding='utf-8', errors='replace')
    return r.returncode == 0 and name.split(':')[0] in r.stdout


class Yards:
    def __init__(s, design):
        s.design = design
        s.plan = json.load(open(os.path.join(design, 'plan.json'), encoding='utf-8'))
        s.P = s.plan['yards']
        B = s.P['base']
        oth = export_list(ASSEMBLY, draft=False, hide_links=','.join(B['hide_links']))
        s.mast = {}
        s.read = {'others': int(len(oth))}
        tot = len(oth)
        for k, w in s.P['works'].items():
            mk = B['mark'] if has_mark(w, B['mark']) else None
            a = export_list(w, draft=False, links='none', mark=mk)
            s.mast[k] = {(int(x), int(y), int(z)) for x, y, z, c in a}
            s.read[k] = {'mark': mk, 'voxels': int(len(a))}
            tot += len(a)
        assert tot == B['assembly_voxels'], ('讀到的現況格數對不上', tot, B['assembly_voxels'])
        s.occ = {(int(x), int(y), int(z)) for x, y, z, c in oth}
        for k in s.mast:
            s.occ |= s.mast[k]
        s.cells = {k: {} for k in s.P['works']}      # 每件子作品要加的格
        s.kind = {}
        s.members = []
        s.anchors = []

    def put(s, work, k, c, member):
        if k in s.occ or any(k in s.cells[w] for w in s.cells):
            return
        if not (0 <= k[0] < 1024 and 0 <= k[1] < 320 and 0 <= k[2] < 800):
            raise SystemExit('帆桁出界：%s %s' % (member, k))
        s.cells[work][k] = c
        s.kind[k] = member

    def radius(s, r0, sfrac):
        T = s.P['taper']
        return r0 * float(np.interp(sfrac, T['s'], T['k']))

    def mast_front(s, mast, z):
        xs = [x for (x, y, zz) in s.mast[mast] if zz == z and abs(y - YC) <= 6]
        return max(xs)

    def mast_back(s, mast, z):
        xs = [x for (x, y, zz) in s.mast[mast] if zz == z and abs(y - YC) <= 6]
        return min(xs)

    # ── 橫桁（沿 y）──
    def yard(s, Y):
        L = Y['ft'] * FT
        r0 = Y['in'] * IN / 2
        arm = Y['arm_ft'] * FT
        z0 = Y['z']
        xf = s.mast_front(Y['mast'], z0)
        xc = xf + 0.5 + r0
        half = L / 2
        col = s.P['colors']
        n = 0
        for dy in range(-int(math.floor(half)), int(math.floor(half)) + 1):
            sf = min(abs(dy) / half, 1.0)
            r = max(s.radius(r0, sf), 0.5)
            tip = abs(dy) > half - 1
            for x in range(int(math.floor(xc - r)) - 1, int(math.ceil(xc + r)) + 2):
                for z in range(int(math.floor(z0 - r)) - 1, int(math.ceil(z0 + r)) + 2):
                    if (x - xc) ** 2 + (z - z0) ** 2 <= r * r + 0.15 or (abs(x - xc) < 0.51 and z == z0):
                        s.put(Y['mast'], (x, YC + dy, z), col['tip'] if tip else col['spar'], Y['name'])
                        n += 1
        # 固定點：yardarm 兩端、帆上緣兩角（yardarm 內端）、slings、帆上緣每隔幾格（jackstay）
        top = lambda dy: (int(round(xc)), YC + dy, int(math.floor(z0 + max(s.radius(r0, min(abs(dy) / half, 1)), 0.5) + 0.15)))
        e = int(math.floor(half))
        ea = int(round(half - arm))
        pts = [('arm-P', (int(round(xc)), YC - e, z0), 'yardarm'), ('arm-S', (int(round(xc)), YC + e, z0), 'yardarm'),
               ('earing-P', top(-ea), 'earing'), ('earing-S', top(ea), 'earing'), ('sling', top(0), 'sling')]
        sp = s.P['jackstay_spacing']
        for dy in range(sp, ea, sp):
            pts += [('jackstay-P%d' % dy, top(-dy), 'jackstay'), ('jackstay-S%d' % dy, top(dy), 'jackstay')]
        for nm, p, kd in pts:
            s.anchors.append({'name': '%s.%s' % (Y['name'], nm), 'owner': s.P['works'][Y['mast']], 'member': Y['name'], 'kind': kd,
                              'side': 'P' if p[1] < YC else ('S' if p[1] > YC else 'CL'), 'world': list(p)})
        s.members.append({'name': Y['name'], 'mast': Y['mast'], 'length_cells': round(L, 1), 'r_center': round(r0, 2), 'arm_cells': round(arm, 1),
                          'center': [round(xc, 2), YC, z0], 'mast_front_x': xf, 'y_range': [YC - e, YC + e], 'cells': n})

    # ── 斜的桿（gaff／boom，在 x–z 平面裡）──
    def spar(s, work, name, p0, d, L, r0, r1, anchor_every=None, ends=('jaws', 'end')):
        col = s.P['colors']
        d = np.array(d, float) / np.linalg.norm(d)
        p0 = np.array(p0, float)
        lo = np.minimum(p0, p0 + d * L) - r0 - 2
        hi = np.maximum(p0, p0 + d * L) + r0 + 2
        n = 0
        for x in range(int(lo[0]), int(hi[0]) + 1):
            for y in range(YC - int(r0) - 2, YC + int(r0) + 3):
                for z in range(int(lo[2]), int(hi[2]) + 1):
                    q = np.array([x, y, z], float) - p0
                    u = q @ d
                    if not (-0.6 <= u <= L):            # 起點多留半格：jaws 貼著桅（v1 從桅後緣再退 r 起算、u < 0 切掉 ⇒ 差 1 格浮空）
                        continue
                    r = max(r0 + (r1 - r0) * u / L, 0.5)
                    perp = np.linalg.norm(q - d * u)
                    if perp * perp <= r * r + 0.15:
                        s.put(work, (x, y, z), col['tip'] if u > L - 1 else col['spar'], name)
                        n += 1
        pts = [(ends[0], p0), (ends[1], p0 + d * (L - 0.5))]
        if anchor_every:
            for u in np.arange(anchor_every, L - 1, anchor_every):
                pts.append(('top%d' % int(u), p0 + d * u + np.array([0, 0, r0 * 0.9])))
        for nm, p in pts:
            q = tuple(int(round(c)) for c in p)
            s.anchors.append({'name': '%s.%s' % (name, nm), 'owner': s.P['works'][work], 'member': name, 'kind': nm.rstrip('0123456789'),
                              'side': 'CL', 'world': list(q)})
        s.members.append({'name': name, 'work': work, 'length_cells': round(L, 1), 'r': [round(r0, 2), round(r1, 2)],
                          'from': [round(float(c), 1) for c in p0], 'to': [round(float(c), 1) for c in p0 + d * L], 'cells': n})

    def build(s):
        for Y in s.P['yards']:
            s.yard(Y)
        Sp = s.P['spanker']
        for nm, G in (('spanker-gaff', Sp['gaff']), ('spanker-boom', Sp['boom'])):
            L = G['ft'] * FT
            r0 = G['in'] * IN / 2
            z = G['jaws_z']
            xb = s.mast_back('mizzen', z)
            a = math.radians(G['angle_deg'])
            p0 = (xb - 0.5, YC, z)
            s.spar('mizzen', nm, p0, (-math.cos(a), 0, math.sin(a)), L, r0, r0 * G['taper_end'], anchor_every=8)
        # spritsail yard：bowsprit 底下、cap 內側
        Ss = s.P['spritsail']
        bw = s.mast['bowsprit']
        # bowsprit 本體的末端（cap）：照 plan.json masts.bowsprit 從 heel 沿軸量全長（整件子作品最前面是 flying jibboom 的尖，不能拿來用）
        Bp = s.plan['masts']['bowsprit']
        h0, h1 = np.array(Bp['heel'], float), np.array(Bp['over_stem'], float)
        dd = (h1 - h0) / np.linalg.norm(h1 - h0)
        cap = h0 + dd * Bp['length'] * FT
        s.cap = [round(float(c), 1) for c in cap]
        xs = int(round(cap[0] - Ss['inboard_of_cap']))
        # bowsprit 本體的末端（不是 jibboom）：bowsprit 截面在 x 的底面 z
        r0 = Ss['in'] * IN / 2
        bmin = lambda x: min(z for (xx, y, z) in bw if xx == x and abs(y - YC) <= 1)
        s.sprit_x = xs
        Y = {'mast': 'bowsprit', 'name': 'spritsail', 'ft': Ss['ft'], 'in': Ss['in'], 'arm_ft': Ss['arm_ft'], 'z': int(round(bmin(xs) - 0.5 - r0))}
        # 吊在 bowsprit 底下：中心 x 固定在 xs（不是「桅的前緣」）
        s._front_override = xs - 0.5 - r0
        orig = s.mast_front
        s.mast_front = lambda mast, z: s._front_override
        s.yard(Y)
        s.mast_front = orig

    def verify(s):
        v = {'read': s.read}
        v['members'] = s.members
        v['cells'] = {k: len(c) for k, c in s.cells.items()}
        v['total_new'] = sum(len(c) for c in s.cells.values())
        new = {}
        for c in s.cells.values():
            new.update(c)
        v['overlap'] = sum(1 for k in new if k in s.occ)
        # 浮空：每根帆桁要 6 連通接到它那根桅（或 bowsprit）
        fl = {}
        for w, cells in s.cells.items():
            pts = set(cells) | s.mast[w]
            arr = np.array(sorted(pts))
            lo = arr.min(0)
            hi = arr.max(0)
            A = np.zeros(tuple(hi - lo + 1), bool)
            A[tuple((arr - lo).T)] = True
            lab, n = ndimage.label(A)
            ml = set(lab[tuple((np.array(sorted(s.mast[w])) - lo).T)])
            bad = [k for k in cells if lab[tuple(np.array(k) - lo)] not in ml]
            fl[w] = len(bad)
        v['floating_by_work'] = fl
        mm = {}
        for k, c in new.items():
            if new.get((k[0], 2 * YC - k[1], k[2])) != c:
                mm[s.kind[k]] = mm.get(s.kind[k], 0) + 1
        v['mirror_mismatch'] = mm
        v['anchors'] = len(s.anchors)
        v['expect_assembly_after'] = s.P['base']['assembly_voxels'] + v['total_new']
        # 不同桅的帆桁之間最近距離（x 方向，看會不會互相打架）
        ys = {}
        for m in s.members:
            ys[m['name']] = m
        s.v = v
        return v

    def write(s):
        out = os.path.join(s.design, 'masks', 'yards')
        os.makedirs(out, exist_ok=True)
        s.files = {}
        for w, cells in s.cells.items():
            p = os.path.join(out, w + '.vox.txt')
            rows = sorted((k[0], k[1], k[2], c) for k, c in cells.items())
            open(p, 'w', encoding='utf-8', newline='\n').write('# %s —— 帆桁（貼進 %s，世界座標，at=0,0,0）（%d 格）\n' % (w, s.P['works'][w], len(rows))
                                                               + '\n'.join('%d,%d,%d,%d' % r for r in rows) + '\n')
            s.files[w] = {'cells': len(rows), 'sha256': hashlib.sha256(open(p, 'rb').read()).hexdigest()}
        rp = os.path.join(s.design, 'rig_points_yards.json')
        json.dump({'note': s.P['anchor_note'], 'points': s.anchors}, open(rp, 'w', encoding='utf-8', newline='\n'), ensure_ascii=False, indent=1)
        s.files['rig_points'] = {'points': len(s.anchors), 'sha256': hashlib.sha256(open(rp, 'rb').read()).hexdigest()}


def render_sheet(Y, path):
    f12, f14, f18 = DD._font(13), DD._font(15), DD._font(20)
    a = export_list(ASSEMBLY, draft=False)
    D = {(int(x), int(y), int(z)): int(c) for x, y, z, c in a}
    for c in Y.cells.values():
        D.update(c)
    xs = np.array([k[0] for k in D])
    # 側面（從 y > 160 那一舷看）與正面（從船頭看，觀者左手邊 ＝ +y）：每 2 格 1 px 的縮圖不夠細 ⇒ 1 格 1 px
    xa, xb, za, zb = 0, 980, 0, 660
    side = np.zeros((zb - za, xb - xa, 3), np.uint8)
    side[:] = DD.PAPER
    depth = np.full((zb - za, xb - xa), -1)
    for (x, y, z), c in D.items():
        if xa <= x < xb and za <= z < zb and y > depth[zb - 1 - z, x - xa]:
            depth[zb - 1 - z, x - xa] = y
            side[zb - 1 - z, x - xa] = DP.rgb332(c)
    front = np.zeros((zb - za, 320, 3), np.uint8)
    front[:] = DD.PAPER
    fd = np.full((zb - za, 320), -1)
    for (x, y, z), c in D.items():
        if za <= z < zb and x > fd[zb - 1 - z, 319 - y]:
            fd[zb - 1 - z, 319 - y] = x
            front[zb - 1 - z, 319 - y] = DP.rgb332(c)
    new = set()
    for c in Y.cells.values():
        new |= set(c)
    W = 60 + (xb - xa) + 50 + 320 + 60
    H = 80 + (zb - za) + 200
    can = Image.new('RGB', (W, H), DD.PAPER)
    dr = ImageDraw.Draw(can)
    dr.text((60, 12), Y.P['title'], font=f18, fill=DD.INK)
    dr.text((60, 40), '正交投影、每格 1 px；左：從 y > 160 那一舷看；右：從船頭看（觀者左手邊 ＝ y > 160）；紅點 ＝ 固定點（給繩索與帆）', font=f12, fill=DD.INK)
    can.paste(Image.fromarray(side), (60, 66))
    can.paste(Image.fromarray(front), (60 + (xb - xa) + 50, 66))
    for p in Y.anchors:
        x, y, z = p['world']
        if p['kind'] in ('yardarm', 'earing', 'sling', 'jaws', 'end', 'top'):
            px, pz = 60 + (x - xa), 66 + (zb - 1 - z)
            dr.ellipse([px - 1, pz - 1, px + 1, pz + 1], fill=(220, 30, 30))
            fx = 60 + (xb - xa) + 50 + (319 - y)
            dr.ellipse([fx - 1, pz - 1, fx + 1, pz + 1], fill=(220, 30, 30))
    for z in range(0, zb, 100):
        dr.text((22, 66 + zb - 1 - z - 7), str(z), font=f12, fill=(130, 130, 130))
    for x in range(0, xb, 100):
        dr.text((60 + x - 8, 66 + zb + 2), str(x), font=f12, fill=(130, 130, 130))
    y = 66 + zb + 26
    v = Y.v
    for m in v['members']:
        pass
    lines = ['帆桁 %d 根＋gaff、boom、spritsail yard；新加 %d 格（%s）；固定點 %d 個；重疊 %d、浮空 %s；組裝件預期 %d' % (
        len(Y.P['yards']), v['total_new'], '、'.join('%s %d' % kv for kv in v['cells'].items()), v['anchors'], v['overlap'], v['floating_by_work'], v['expect_assembly_after'])]
    row = []
    for m in v['members']:
        row.append('%s %.0f 格 r%.1f' % (m['name'], m['length_cells'], m.get('r_center', m.get('r', [0])[0] if isinstance(m.get('r'), list) else 0)))
    for i in range(0, len(row), 6):
        lines.append('、'.join(row[i:i + 6]))
    lines.append('出處：Martin《Close Up》附錄 A（1815）、Steel 1794 錐度；高度照作品 mast-probe 的「升起」位置（收下的記在 plan.json yards.yards[].z_lowered）')
    for t in lines:
        dr.text((60, y), t, font=f12, fill=DD.INK)
        y += 20
    can = can.crop((0, 0, W, y + 20))
    can.save(path)


def main():
    design = sys.argv[1]
    sys.stdout.reconfigure(encoding='utf-8')
    Y = Yards(design)
    Y.build()
    v = Y.verify()
    Y.write()
    v['files'] = Y.files
    json.dump(v, open(os.path.join(design, 'verify_yards.json'), 'w', encoding='utf-8', newline='\n'), ensure_ascii=False, indent=1)
    render_sheet(Y, os.path.join(design, 'sheet14_yards_v1.png'))
    print(json.dumps({k: v[k] for k in ('read', 'cells', 'total_new', 'overlap', 'floating_by_work', 'mirror_mismatch', 'anchors', 'expect_assembly_after')}, ensure_ascii=False, indent=1))
    for m in v['members']:
        print(json.dumps(m, ensure_ascii=False))


if __name__ == '__main__':
    main()
