# 餘燼號 階段四a：船尾 —— poop 加高、三層船尾窗、四個船尾砲門、船尾塗裝（plan.json stern）
#   輸入：餘燼號船殼（標記 上層砲門:end）
#   ⇒ masks/stern/{poop_add,openings_carve,paint}.vox.txt、verify_stern.json、sheet04_stern_v1.png
# 用法：python -I draft_stern.py <design 資料夾>
#   · poop：x ≤ x_front 的每一欄，照 z ref_z 那一層的牆組成（那一欄沒有 ⇒ 借最近一欄）從現在的頂往上疊到 top_z − 1，top_z 一層 cap（104，內外各多 1）；舊 cap rail 留著當線腳
#   · 窗與砲門：船尾面（每個 (y, z) 最後面那一格）往船頭刻，刻到碰到空氣（最多 max_depth 格；碰不到就不刻、記數）
#   · 塗裝：x < side_x_from 的船尾與 quarter —— 剩下的白 → 金；兩條砲門帶延伸到船尾（帶的高度取 x ＝ side_x_from 那一欄），上下緣金；每個窗與砲門外面一圈 → 金框
import sys, os, json, hashlib, subprocess, tempfile
import numpy as np
from PIL import Image, ImageDraw

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import draft_profile as DP   # noqa: E402
from draft_ports import export_mark   # noqa: E402

W = 'basecamp-ember-01m'
YC = 160


class Stern:
    def __init__(s, design):
        s.design = design
        s.plan = json.load(open(os.path.join(design, 'plan.json'), encoding='utf-8'))
        s.S = s.plan['stern']
        a = export_mark(W, s.S['world_mark'])
        assert len(a) == s.S['world_voxels'], ('船殼現況跟 plan 記的不一樣', len(a))
        s.H = {(int(x), int(y), int(z)): int(c) for x, y, z, c in a}
        s.read = {'world': len(s.H)}

    # ── poop ──
    def poop(s):
        Pp = s.S['poop']
        xf, zr, zt = Pp['x_front'], Pp['ref_z'], Pp['top_z']
        prof = {}
        for (x, y, z), c in s.H.items():
            if z == zr and x <= xf:
                prof.setdefault(x, []).append((y, c))
        top = {}
        for (x, y, z) in s.H:
            if x <= xf:
                top[x] = max(top.get(x, -1), z)
        xs = sorted(top)
        borrowed = 0
        s.add = {}
        for x in xs:
            pr = prof.get(x)
            if not pr:
                for d in range(1, 12):
                    pr = prof.get(x - d) or prof.get(x + d)
                    if pr:
                        borrowed += 1
                        break
            if not pr:
                continue
            for z in range(top[x] + 1, zt):
                for y, c in pr:
                    s.add[(x, y, z)] = c
            for y, c in pr:
                for yy in (y - 1, y, y + 1):
                    k = (x, yy, zt)
                    if k not in s.add:
                        s.add[k] = Pp['cap_color']
        assert not any(k in s.H for k in s.add), 'poop 撞到現況'
        s.read['poop_add'] = len(s.add)
        s.read['poop_cols'] = len(xs)
        s.read['poop_cols_borrowed'] = borrowed
        s.read['poop_top_before'] = [min(top.values()), max(top.values())]

    # ── 窗與砲門 ──
    def openings(s):
        G = dict(s.H)
        G.update(s.add)
        aft = {}
        for (x, y, z) in G:
            if x < s.S['face_x_max']:
                k = (y, z)
                if k not in aft or x < aft[k]:
                    aft[k] = x
        s.aft = aft
        s.cut = {}
        s.frames = []
        skipped = 0
        md = s.S['max_depth']
        for tier in s.S['tiers']:
            for w in tier['openings']:
                nm, (d0, d1), (z0, z1) = w['name'], w['dy'], w['z']
                cz = w.get('carve_z', w['z']) if w.get('carve', True) else None
                for sg in ((1, -1) if d0 > 0 else (1,)):
                    box = []
                    for dy in range(d0, d1 + 1):
                        y = YC + sg * dy
                        for z in range(z0, z1 + 1):
                            box.append((y, z))
                    s.frames.append((tier['name'], nm, sg, box))
                    for y, z in box:
                        if cz is None or not (cz[0] <= z <= cz[1]) or (y, z) not in aft:
                            continue
                        x = aft[(y, z)]
                        run = []
                        while (x, y, z) in G and len(run) <= md:
                            run.append((x, y, z))
                            x += 1
                        if (x, y, z) in G:          # 刻不穿 ⇒ 不刻
                            skipped += 1
                            continue
                        for k in run:
                            s.cut[k] = G[k]
        s.read['openings_carve'] = len(s.cut)
        s.read['openings_not_through'] = skipped
        cols = {}
        for c in s.cut.values():
            cols[c] = cols.get(c, 0) + 1
        s.read['openings_carve_colors'] = dict(sorted(cols.items()))
        s.G = {k: c for k, c in G.items() if k not in s.cut}

    # ── 塗裝 ──
    def paint(s):
        C = s.S['paint']
        G = s.G
        x0 = C['side_x_from']
        red, gold = C['band'], C['line']
        s.pt = {}
        # 兩條帶在 x0 那一欄（S 舷外緣）的高度
        zs = [z for z in range(80, 140) if any(G.get((x0, y, z)) == red for y in range(YC + 1, 320))]
        lo = [z for z in zs if z < 109]
        bands = [(min(lo), max(lo)), (min(lo) + 23, max(lo) + 23)]
        s.read['stern_bands'] = bands

        def surf_cells():
            out = set()
            for (y, z), x in s.aft_after().items():
                out.add((x, y, z))
            for x in range(s.S['face_x_min'], x0):
                for z in range(60, 200):
                    for sg in (1, -1):
                        ys = [YC + sg * d for d in range(1, 160) if (x, YC + sg * d, z) in G]
                        if ys:
                            out.add((x, max(ys) if sg > 0 else min(ys), z))
            return out
        surf = surf_cells()
        for k in surf:
            c = G[k]
            if k[0] >= x0:
                continue
            z = k[2]
            if c == 255:
                s.pt[k] = gold
                continue
            if c != 36:
                continue
            for zl, zh in bands:
                if zl <= z <= zh:
                    s.pt[k] = red
                elif z in (zl - 1, zh + 1):
                    s.pt[k] = gold
        # 剩下的白（不在表面上的、例如窗台下面那幾格）也換金
        for k, c in G.items():
            if c == 255 and k not in s.pt:
                s.pt[k] = gold
        # 窗與砲門的金框：開口外一圈（同一個 (y, z) 平面上）在船尾面的那一格
        aft = s.aft_after()
        ring = 0
        for tier, nm, sg, box in s.frames:
            B = set(box)
            for y, z in box:
                for dy, dz in ((1, 0), (-1, 0), (0, 1), (0, -1), (1, 1), (1, -1), (-1, 1), (-1, -1)):
                    q = (y + dy, z + dz)
                    if q in B or q not in aft:
                        continue
                    k = (aft[q], q[0], q[1])
                    if G.get(k) in (36, red, 104) and s.pt.get(k) != gold:
                        s.pt[k] = gold
                        ring += 1
        s.read['paint'] = len(s.pt)
        s.read['paint_frames'] = ring
        to = {}
        for c in s.pt.values():
            to[c] = to.get(c, 0) + 1
        s.read['paint_to'] = dict(sorted(to.items()))
        s.read['white_left'] = sum(1 for k, c in G.items() if c == 255 and k not in s.pt)

    def aft_after(s):
        if getattr(s, '_aft2', None) is None:
            aft = {}
            for (x, y, z) in s.G:
                if x < s.S['face_x_max']:
                    k = (y, z)
                    if k not in aft or x < aft[k]:
                        aft[k] = x
            s._aft2 = aft
        return s._aft2

    def write(s):
        files = {}
        for name, D, head in (('poop_add', s.add, 'poop 加高（stampvox；世界座標 at 0,0,0）'),
                              ('openings_carve', s.cut, '船尾窗與船尾砲門（carvevox，行尾顏色守門）'),
                              ('paint', s.pt, '船尾塗裝（stampvox overwrite=1）')):
            out = os.path.join(s.design, 'masks', 'stern')
            os.makedirs(out, exist_ok=True)
            p = os.path.join(out, name + '.vox.txt')
            rows = sorted((k[0], k[1], k[2], c) for k, c in D.items())
            open(p, 'w', encoding='utf-8', newline='\n').write('# %s（%d 格）\n' % (head, len(rows)) + '\n'.join('%d,%d,%d,%d' % r for r in rows) + '\n')
            files[name] = {'cells': len(rows), 'sha256': hashlib.sha256(open(p, 'rb').read()).hexdigest()}
        return files

    def result(s):
        R = dict(s.G)
        R.update(s.pt)
        return R

    def sheet(s, path):
        R = s.result()
        sc = 4
        ys, zs = (100, 221), (60, 170)
        aft = {}
        for (x, y, z), c in R.items():
            if x < s.S['face_x_max']:
                k = (y, z)
                if k not in aft or x < aft[k][0]:
                    aft[k] = (x, c)
        Wd, Hd = (ys[1] - ys[0]) * sc, (zs[1] - zs[0]) * sc
        im = Image.new('RGB', (max(Wd + 40, 900), Hd + 120), (250, 249, 244))
        d = ImageDraw.Draw(im)
        px = im.load()
        for (y, z), (x, c) in aft.items():
            if ys[0] <= y < ys[1] and zs[0] <= z < zs[1]:
                col = DP.rgb(c)
                X0, Y0 = 20 + (ys[1] - 1 - y) * sc, 90 + (zs[1] - 1 - z) * sc     # 從船尾往船頭看：觀者左手邊 ＝ −y
                for i in range(sc):
                    for j in range(sc):
                        px[X0 + i, Y0 + j] = col
        d.text((20, 12), '餘燼號 新圖紙 04a v1：船尾（從正後方看；每個 (y, z) 最後面那一格）', font=DP.font(20), fill=(30, 30, 30))
        d.text((20, 44), 'poop 加高到 z %d、窗三層、船尾砲門 4；刻 %d、加 %d、換色 %d' % (s.S['poop']['top_z'], len(s.cut), len(s.add), len(s.pt)),
               font=DP.font(14), fill=(80, 80, 80))
        im.save(path)


def main():
    sys.stdout.reconfigure(encoding='utf-8')
    design = os.path.abspath(sys.argv[1])
    St = Stern(design)
    St.poop()
    St.openings()
    St.paint()
    v = {'read': St.read}
    v['files'] = St.write()
    R = St.result()
    v['expect_after'] = len(R)
    v['structure_after'] = DP.Ember.structure(None, R)
    mm = sum(1 for (x, y, z), c in R.items() if R.get((x, 320 - y, z)) != c)
    v['mirror_mismatch'] = mm
    St.sheet(os.path.join(design, 'sheet04_stern_v1.png'))
    json.dump(v, open(os.path.join(design, 'verify_stern.json'), 'w', encoding='utf-8', newline='\n'), ensure_ascii=False, indent=1)
    print(json.dumps({k: v[k] for k in v if k != 'files'}, ensure_ascii=False, indent=1))


if __name__ == '__main__':
    main()
