# 新圖紙 22（帆桁轉角度 brace）：plan.json 的 brace 段 ＋ yards 段 ＋ 組裝件的現況
#   ⇒ masks/brace/<桅>_carve.vox.txt（刻掉的舊方帆桁，帶顏色守門）、masks/brace/<桅>_stamp.vox.txt（轉過的方帆桁）、
#      rig_points_yards.json（覆寫成轉過的；轉之前那份另存 rig_points_yards_square.json）、verify_brace.json、sheet22_brace_v1.png
# 用法：python -I draft_brace.py <design 資料夾>
#   · 只轉前／主／後桅的方帆桁（course／crossjack／topsail／topgallant／royal）；gaff、boom、spritsail yard 不動
#   · 每根繞自己的中心（xc, 160）水平轉 θ：右舷那一頭往前（＋x）⇒ 帆面對著從右舷後方吹來的預設風
#   · 截面、錐度、yardarm 端色、固定點的定義都跟 draft_yards.py 一樣，只是沿著轉過的軸量
#   · 現況 ＝ 組裝件現在的樣子扣掉舊方帆桁（舊的會先刻掉）；跟現況重疊的格不放（記數）
import sys, os, json, hashlib, math
import numpy as np
from scipy import ndimage
from PIL import Image, ImageDraw

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import draft_planking as DP        # noqa: E402
import draft_decks as DD           # noqa: E402
from draft_masts import export_list, ASSEMBLY   # noqa: E402
from draft_yards import FT, IN, YC  # noqa: E402

MASTS = ('fore', 'main', 'mizzen')


def load_list(p):
    a = np.loadtxt(p, delimiter=',', comments='#', dtype=np.int64, ndmin=2, encoding='utf-8')
    return {(int(x), int(y), int(z)): int(c) for x, y, z, c in a}


class Brace:
    def __init__(s, design):
        s.design = design
        s.plan = json.load(open(os.path.join(design, 'plan.json'), encoding='utf-8'))
        s.Y = s.plan['yards']
        s.B = s.plan['brace']
        cur = export_list(ASSEMBLY, draft=False)
        s.read = {'assembly_now': int(len(cur))}
        assert len(cur) == s.B['base']['assembly_voxels'], ('組裝件現況跟 plan 記的不一樣', len(cur))
        # 桅本身（帆桁加進來之前那一刀的狀態），用來量桅的前緣
        s.mast = {}
        for m in MASTS:
            a = export_list(s.Y['works'][m], draft=False, links='none', mark=s.Y['base']['mark'])
            s.mast[m] = {(int(x), int(y), int(z)) for x, y, z, c in a}
        # 舊帆桁：masks/yards/<桅>.vox.txt 裡、在桅的前面那一半（mizzen 那份還有 gaff／boom，在桅後面）
        s.old = {}
        for m in MASTS:
            L = load_list(os.path.join(design, 'masks', 'yards', m + '.vox.txt'))
            cx = {}
            for (x, y, z) in s.mast[m]:
                if abs(y - YC) <= 6:
                    lo, hi = cx.get(z, (10 ** 9, -1))
                    cx[z] = (min(lo, x), max(hi, x))
            keep = {}
            for k, c in L.items():
                zz = min(cx, key=lambda z: abs(z - k[2]))
                mid = (cx[zz][0] + cx[zz][1]) / 2
                if k[0] > mid:
                    keep[k] = c
            s.old[m] = keep
        old_all = set().union(*[set(v) for v in s.old.values()])
        s.occ = {(int(x), int(y), int(z)) for x, y, z, c in cur} - old_all
        s.read['old_square_yard_cells'] = {m: len(v) for m, v in s.old.items()}
        s.cells = {m: {} for m in MASTS}
        s.kind = {}
        s.skipped = {}
        s.skipped_cells = []
        s.members, s.anchors = [], []

    def radius(s, r0, sf):
        T = s.Y['taper']
        return r0 * float(np.interp(sf, T['s'], T['k']))

    def mast_front(s, mast, z):
        return max(x for (x, y, zz) in s.mast[mast] if zz == z and abs(y - YC) <= 6)

    def rmin(s, th):
        # 轉了角度的細截面：0.5 會變成只靠斜角相接的階梯（6 連通斷掉）；斜線上的格心離軸 ≤ 0.71 ⇒ 取 0.75。角度 0 照 draft_yards.py 的 0.5
        return 0.5 if th == 0 else s.B['rmin_braced']

    def angle(s, name):
        for tier, deg in s.B['angle_deg'].items():
            if name.endswith('-' + tier):
                return deg
        raise KeyError(name)

    def put(s, m, k, c, name):
        if k in s.occ or any(k in s.cells[w] for w in s.cells):
            if k in s.occ:
                s.skipped[name] = s.skipped.get(name, 0) + 1
                s.skipped_cells.append((k, name))
            return
        s.cells[m][k] = c
        s.kind[k] = name

    def yard(s, Y):
        L = Y['ft'] * FT
        r0 = Y['in'] * IN / 2
        arm = Y['arm_ft'] * FT
        z0 = Y['z']
        xf = s.mast_front(Y['mast'], z0)
        xc = xf + 0.5 + r0
        half = L / 2
        th = math.radians(s.angle(Y['name']))
        d = np.array([math.sin(th), math.cos(th)])          # 沿帆桁（u ＞ 0 ＝ 右舷那一頭）
        nrm = np.array([math.cos(th), -math.sin(th)])       # 水平、垂直帆桁
        col = s.Y['colors']
        R = half + 2
        for x in range(int(xc - R * abs(d[0])) - 4, int(xc + R * abs(d[0])) + 5):
            for y in range(int(YC - R) - 1, int(YC + R) + 2):
                q = np.array([x - xc, y - YC])
                u = float(q @ d)
                if abs(u) > half + 0.5:
                    continue
                w = float(q @ nrm)
                sf = min(abs(u) / half, 1.0)
                r = max(s.radius(r0, sf), s.rmin(th))
                if abs(w) > r + 1:
                    continue
                tip = abs(u) > half - 1
                for z in range(int(math.floor(z0 - r)) - 1, int(math.ceil(z0 + r)) + 2):
                    if (w * w + (z - z0) ** 2 <= r * r + 0.15 or (abs(w) < 0.51 and z == z0)) and abs(u) <= half:
                        s.put(Y['mast'], (x, y, z), col['tip'] if tip else col['spar'], Y['name'])
        # 固定點（定義同 draft_yards.py：yardarm 兩端、earing、sling、jackstay），沿轉過的軸
        def at(u, zz):
            return [int(round(xc + u * d[0])), int(round(YC + u * d[1])), zz]

        def top(u):
            return at(u, int(math.floor(z0 + max(s.radius(r0, min(abs(u) / half, 1)), 0.5) + 0.15)))   # 固定點高度照 draft_yards.py（0.5），不受 rmin 影響
        e = int(math.floor(half))
        ea = int(round(half - arm))
        pts = [('arm-P', at(-e, z0), 'yardarm'), ('arm-S', at(e, z0), 'yardarm'), ('earing-P', top(-ea), 'earing'), ('earing-S', top(ea), 'earing'),
               ('sling', top(0), 'sling')]
        sp = s.Y['jackstay_spacing']
        for dy in range(sp, ea, sp):
            pts += [('jackstay-P%d' % dy, top(-dy), 'jackstay'), ('jackstay-S%d' % dy, top(dy), 'jackstay')]
        for nm, p, kd in pts:
            s.anchors.append({'name': '%s.%s' % (Y['name'], nm), 'owner': s.Y['works'][Y['mast']], 'member': Y['name'], 'kind': kd,
                              'side': 'P' if nm.split('-')[-1].startswith('P') else ('S' if nm.split('-')[-1].startswith('S') else 'CL'), 'world': p})
        s.members.append({'name': Y['name'], 'mast': Y['mast'], 'angle_deg': s.angle(Y['name']), 'center': [round(xc, 2), YC, z0],
                          'arm_S': at(e, z0), 'arm_P': at(-e, z0), 'swing_x': round(e * d[0], 1)})

    def build(s):
        for Y in s.Y['yards']:
            s.yard(Y)
        # 不轉的固定點（gaff、boom、spritsail）照舊
        old = json.load(open(os.path.join(s.design, 'rig_points_yards.json'), encoding='utf-8'))
        s.old_points = old
        moved = {a['name'] for a in s.anchors}
        sq = {Y['name'] for Y in s.Y['yards']}
        s.kept = [p for p in old['points'] if p['member'] not in sq]
        s.anchors += s.kept
        assert len(s.anchors) == len(old['points']), (len(s.anchors), len(old['points']))
        assert {p['name'] for p in s.anchors} == {p['name'] for p in old['points']}

    def verify(s):
        v = {'read': s.read, 'members': s.members, 'skipped_overlap': s.skipped}
        v['new_cells'] = {m: len(c) for m, c in s.cells.items()}
        v['old_cells'] = {m: len(c) for m, c in s.old.items()}
        v['delta'] = sum(v['new_cells'].values()) - sum(v['old_cells'].values())
        fl = {}
        for m, cells in s.cells.items():
            pts = set(cells) | s.mast[m]
            arr = np.array(sorted(pts))
            lo = arr.min(0)
            A = np.zeros(tuple(arr.max(0) - lo + 1), bool)
            A[tuple((arr - lo).T)] = True
            lab, n = ndimage.label(A)
            ml = set(lab[tuple((np.array(sorted(s.mast[m])) - lo).T)])
            fl[m] = sum(1 for k in cells if lab[tuple(np.array(k) - lo)] not in ml)
        v['floating_by_mast'] = fl
        v['anchors'] = len(s.anchors)
        v['anchors_moved'] = len(s.anchors) - len(s.kept)
        v['expect_assembly_after'] = s.B['base']['assembly_voxels'] + v['delta']
        s.v = v
        return v

    def write(s):
        out = os.path.join(s.design, 'masks', 'brace')
        os.makedirs(out, exist_ok=True)
        s.files = {}
        for m in MASTS:
            for tag, cells in (('carve', s.old[m]), ('stamp', s.cells[m])):
                p = os.path.join(out, '%s_%s.vox.txt' % (m, tag))
                rows = sorted((k[0], k[1], k[2], c) for k, c in cells.items())
                open(p, 'w', encoding='utf-8', newline='\n').write('# %s —— %s（%s，世界座標，at=0,0,0）（%d 格）\n' % (
                    m, '舊方帆桁（carvevox，行尾顏色守門）' if tag == 'carve' else '轉過的方帆桁（stampvox）', s.Y['works'][m], len(rows))
                    + '\n'.join('%d,%d,%d,%d' % r for r in rows) + '\n')
                s.files['%s_%s' % (m, tag)] = {'cells': len(rows), 'sha256': hashlib.sha256(open(p, 'rb').read()).hexdigest()}
        sq = os.path.join(s.design, 'rig_points_yards_square.json')
        if not os.path.exists(sq):
            json.dump(s.old_points, open(sq, 'w', encoding='utf-8', newline='\n'), ensure_ascii=False, indent=1)
        rp = os.path.join(s.design, 'rig_points_yards.json')
        json.dump({'note': s.old_points['note'] + '；2026-10-12 起方帆桁照 brace 轉過（draft_brace.py 覆寫；轉之前那份在 rig_points_yards_square.json）',
                   'points': s.anchors}, open(rp, 'w', encoding='utf-8', newline='\n'), ensure_ascii=False, indent=1)
        s.files['rig_points'] = {'points': len(s.anchors), 'sha256': hashlib.sha256(open(rp, 'rb').read()).hexdigest()}


def render_sheet(Bc, path):
    f12, f18 = DD._font(13), DD._font(20)
    xa, xb, ya, yb = 120, 680, 20, 300
    sc = 2
    img = np.zeros((yb - ya, xb - xa, 3), np.uint8)
    img[:] = DD.PAPER
    old = set().union(*[set(v) for v in Bc.old.values()])
    for m in MASTS:
        for (x, y, z) in Bc.old[m]:
            if xa <= x < xb and ya <= y < yb:
                img[yb - 1 - y, x - xa] = (205, 200, 190)
    for m in MASTS:
        for (x, y, z), c in Bc.cells[m].items():
            if xa <= x < xb and ya <= y < yb:
                img[yb - 1 - y, x - xa] = DP.rgb332(c)
    for m in MASTS:
        for (x, y, z) in Bc.mast[m]:
            if xa <= x < xb and ya <= y < yb and abs(y - YC) <= 8:
                img[yb - 1 - y, x - xa] = (120, 110, 100)
    top = Image.fromarray(img).resize(((xb - xa) * sc, (yb - ya) * sc), Image.NEAREST)
    can = Image.new('RGB', (top.size[0] + 80, top.size[1] + 200), DD.PAPER)
    dr = ImageDraw.Draw(can)
    dr.text((40, 12), Bc.B['title'], font=f18, fill=DD.INK)
    dr.text((40, 40), '俯視（船頭朝右、右舷朝上；x %d–%d、y %d–%d，每格 %d px）：淡灰 ＝ 轉之前的方帆桁、黑／原木 ＝ 轉過的' % (xa, xb - 1, ya, yb - 1, sc), font=f12, fill=DD.INK)
    can.paste(top, (40, 66))
    y = 66 + top.size[1] + 14
    v = Bc.v
    lines = ['角度：' + '、'.join('%s %d°' % kv for kv in Bc.B['angle_deg'].items()) + '；右舷那一頭往前',
             '格數：舊 %s → 新 %s（差 %+d）；跟現況重疊不放 %s；浮空 %s；組裝件預期 %d' % (v['old_cells'], v['new_cells'], v['delta'], v['skipped_overlap'] or 0, v['floating_by_mast'], v['expect_assembly_after']),
             '固定點 %d（轉過 %d、gaff／boom／spritsail 照舊 %d）' % (v['anchors'], v['anchors_moved'], v['anchors'] - v['anchors_moved'])]
    for m in v['members']:
        if m['name'].endswith(('course', 'crossjack')):
            lines.append('%s：中心 %s、yardarm 往前／往後擺 %.1f 格' % (m['name'], m['center'], m['swing_x']))
    for t in lines:
        dr.text((40, y), t, font=f12, fill=DD.INK)
        y += 20
    can.crop((0, 0, can.size[0], y + 12)).save(path)


def main():
    design = sys.argv[1]
    sys.stdout.reconfigure(encoding='utf-8')
    Bc = Brace(design)
    Bc.build()
    v = Bc.verify()
    Bc.write()
    v['files'] = Bc.files
    json.dump(v, open(os.path.join(design, 'verify_brace.json'), 'w', encoding='utf-8', newline='\n'), ensure_ascii=False, indent=1)
    render_sheet(Bc, os.path.join(design, 'sheet22_brace_v1.png'))
    print(json.dumps({k: v[k] for k in v if k not in ('members', 'files')}, ensure_ascii=False))


if __name__ == '__main__':
    main()
