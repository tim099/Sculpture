# 餘燼號 階段五：甲板（plan.json decks_build）
#   憲法號的甲板子作品（links=none，只要甲板本身：橫樑、甲板板、carlings、艙口、肘、柱子…）照船殼的同一套換算搬過來：
#     拉長 S：x < 439 不動；439 ≤ x ≤ 471 原地＋複製到 +33、+66；x ≥ 472 推 +66
#   orlop／berth／下層砲甲板 ＝ S(憲法號 orlop／berth／gun)；上層砲甲板 ＝ S(憲法號 spar)（高度不動）；上甲板 ＝ S(憲法號 spar) 抬 +23，船腰打開＋欄杆
#   poop deck 新做：x ≤ poop.x_front 的船艙裡、z top 一層甲板板＋橫樑；後桅孔；前緣欄杆（中間留梯口）
#   ⇒ masks/decks/<名>.vox.txt（世界座標，子作品 at 0,0,0）、verify_decks.json、sheet06_decks_v1.png
# 用法：python -I draft_decks.py <design 資料夾>
#   · 跟船殼重疊的格不放（記數）；量：各層之間重疊 0、跟船殼連通、組裝件元件數與空腔
import sys, os, json, math, hashlib, subprocess, tempfile
import numpy as np
from scipy import ndimage
from PIL import Image, ImageDraw

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import draft_profile as DP   # noqa: E402
from draft_ports import export_mark   # noqa: E402

W = 'basecamp-ember-01m'
CON = 'basecamp-frigate-constitution-01m'
YC = 160


def stretch_x(x, St):
    x0, L, n = St['x_from'], St['length'], St['copies']
    if x < x0:
        return [x]
    if x < x0 + L:
        return [x + L * k for k in range(n + 1)]
    return [x + L * n]


class Decks:
    def __init__(s, design):
        s.design = design
        s.plan = json.load(open(os.path.join(design, 'plan.json'), encoding='utf-8'))
        s.B = s.plan['decks_build']
        s.St = s.plan['stretch']
        a = export_mark(W, s.B['world_mark'])
        assert len(a) == s.B['world_voxels'], ('船殼現況跟 plan 記的不一樣', len(a))
        s.H = {(int(x), int(y), int(z)): int(c) for x, y, z, c in a}
        s.read = {'hull': len(s.H)}
        s.decks = {}
        s.dropped = {}

    def con(self, sub):
        a = DP.export_list(CON + '-' + sub)
        return {(int(x), int(y), int(z)): int(c) for x, y, z, c in a}

    def from_con(s):
        src = {}
        for nm, D in s.B['from_constitution'].items():
            if D['source'] not in src:
                src[D['source']] = s.con(D['source'])
                s.read['con_' + D['source']] = len(src[D['source']])
            cells = {}
            for (x, y, z), c in src[D['source']].items():
                for xx in stretch_x(x, s.St):
                    cells[(xx, y, z + D['dz'])] = c
            if D.get('knee_shift'):
                # 懸肘（104、z < knee_z_max、|dy| ≥ knee_dy）原本貼著憲法號 z − dz 那一層的牆；抬上來之後那裡是插入段（牆比較窄）
                # ⇒ 往內挪 outer(x, z − dz) − outer(x, z) 格，讓它貼回現在的牆
                K = D['knee_shift']
                moved = {}
                nmv = 0
                for (x, y, z), c in list(cells.items()):
                    if c == K['color'] and z < K['z_max'] and abs(y - YC) >= K['dy_min']:
                        sg = 1 if y > YC else -1
                        o0, o1 = s.outer(x, z - D['dz'], sg), s.outer(x, z, sg)
                        dd = max(0, o0 - o1) if (o0 is not None and o1 is not None) else 0
                        del cells[(x, y, z)]
                        moved[(x, y - sg * dd, z)] = c
                        nmv += dd > 0
                cells.update(moved)
                s.read['knee_cells_' + nm] = len(moved)
                s.read['knee_cells_shifted_' + nm] = nmv
            drop = [k for k in cells if k in s.H]
            for k in drop:
                del cells[k]
            s.dropped[nm] = len(drop)
            s.decks[nm] = cells

    def outer(s, x, z, sg):
        if not hasattr(s, '_outer'):
            s._outer = {}
            for (xx, y, zz) in s.H:
                k = (xx, zz, 1 if y > YC else -1)
                d = abs(y - YC)
                if d > s._outer.get(k, -1):
                    s._outer[k] = d
        return s._outer.get((x, z, sg))

    def deck_top(s, x):
        # 上甲板的甲板面：直接從甲板板（plank 色）量，每一欄最高那一格（船腰切掉之前量）
        return s.tops[x]

    def waist(s):
        Wt = s.B['waist']
        cells = s.decks['spar']
        xa, xb, g = Wt['x'][0], Wt['x'][1], Wt['gangway_dy']
        s.tops = {}
        for (x, y, z), c in cells.items():
            if c == Wt['plank']:
                s.tops[x] = max(s.tops.get(x, -1), z)
        s.read['spar_top_in_waist'] = sorted(set(s.tops[x] for x in range(xa - 1, xb + 2)))
        cut = [k for k in cells if xa <= k[0] <= xb and abs(k[1] - YC) < g]
        for k in cut:
            del cells[k]
        s.read['waist_removed'] = len(cut)
        rail = {}
        post, cap, h = Wt['post_color'], Wt['cap_color'], Wt['rail_h']

        def put(k, c):
            if k not in s.H and k not in cells:
                rail[k] = c
        # 船腰兩側（gangway 內緣）
        for sg in (1, -1):
            y = YC + sg * g
            for x in range(xa, xb + 1):
                zt = s.deck_top(x)
                for z in range(zt + 1, zt + h):
                    if (x - xa) % 3 == 0:
                        put((x, y, z), post)
                put((x, y, zt + h), post)
        # quarterdeck 前緣、forecastle 後緣（breastwork），金頂
        for x in (xa - 1, xb + 1):
            zt = s.deck_top(x)
            for y in range(YC - g, YC + g + 1):
                for z in range(zt + 1, zt + h):
                    if (y - YC) % 3 == 0:
                        put((x, y, z), post)
                put((x, y, zt + h), cap)
        cells.update(rail)
        s.read['waist_rail'] = len(rail)

    def poop(s):
        P = s.B['poop']
        zt, xf = P['z_top'], P['x_front']
        # 船艙裡的空氣（z zt 那一層、x ≤ xf，從中線往外 flood）
        air = set()
        stack = [(P['seed_x'], YC)]
        while stack:
            x, y = stack.pop()
            if (x, y) in air or x > xf or x < 80 or (x, y, zt) in s.H:
                continue
            air.add((x, y))
            stack += [(x + 1, y), (x - 1, y), (x, y + 1), (x, y - 1)]
        mx, my, mr = P['mizzen_hole']
        cells = {}
        for x, y in air:
            if (x - mx) ** 2 + (y - my) ** 2 <= mr * mr:
                continue
            cells[(x, y, zt)] = P['plank']
            if x in P['beams_x'] or x == xf:
                for z in range(zt - P['beam_depth'], zt):
                    if (x, y, z) not in s.H:
                        cells[(x, y, z)] = P['beam']
        # 前緣欄杆（中間留梯口）
        ys = sorted(y for (x, y) in air if x == xf)
        for y in ys:
            if abs(y - YC) <= P['stair_gap']:
                continue
            for z in range(zt + 1, zt + P['rail_h']):
                if (y - YC) % 3 == 0:
                    cells[(xf, y, z)] = P['post']
            cells[(xf, y, zt + P['rail_h'])] = P['cap']
        s.dropped['poop'] = sum(1 for k in cells if k in s.H)          # 第一版前緣欄杆 14 格插進舊 cap rail／poop 牆（z 148 是空氣、上面不是）
        s.decks['poop'] = {k: c for k, c in cells.items() if k not in s.H}
        s.read['poop_air_cells'] = len(air)

    def verify(s):
        v = {'dropped_overlap_hull': s.dropped, 'cells': {k: len(c) for k, c in s.decks.items()}}
        names = list(s.decks)
        ov = {}
        for i in range(len(names)):
            for j in range(i + 1, len(names)):
                n = sum(1 for k in s.decks[names[i]] if k in s.decks[names[j]])
                if n:
                    ov[names[i] + '×' + names[j]] = n
        v['overlap_between_decks'] = ov
        v['overlap_hull'] = {k: sum(1 for kk in D if kk in s.H) for k, D in s.decks.items()}
        # 露到船外（比那一欄、那一層、那一舷的船殼外緣還外面）
        def outside(k):
            o = s.outer(k[0], k[2], 1 if k[1] > YC else -1)
            return o is not None and abs(k[1] - YC) > o
        v['outside_hull'] = {k: sum(1 for kk in D if outside(kk)) for k, D in s.decks.items()}
        v['mirror_mismatch'] = {k: sum(1 for (x, y, z), c in D.items() if D.get((x, 320 - y, z)) != c) for k, D in s.decks.items()}
        # 組裝件預期（船殼＋四b 的裝飾＋甲板）
        deco = json.load(open(os.path.join(s.design, 'deco_placement.json'), encoding='utf-8'))
        R = dict(s.H)
        for nm in ('quarter_gallery', 'stern_walk', 'stern_deco'):
            o = deco[nm]['origin']
            for line in open(os.path.join(s.design, 'masks', 'deco', nm + '.vox.txt'), encoding='utf-8'):
                if line.startswith('#') or not line.strip():
                    continue
                x, y, z, c = map(int, line.split(','))
                R[(x + o[0], y + o[1], z + o[2])] = c
                if nm == 'quarter_gallery':
                    R[(x + o[0], 320 - (y + o[1]), z + o[2])] = c
        base = len(R)
        assert base == s.B['assembly_before'], ('組裝件現況（算的）跟 plan 記的不一樣', base)
        for D in s.decks.values():
            R.update(D)
        v['assembly_expect'] = len(R)
        v['structure_expect'] = DP.Ember.structure(None, R)
        # 每層都要接到船殼
        arr = np.array(sorted(R))
        lo = arr.min(0)
        A = np.zeros(tuple(arr.max(0) - lo + 1), bool)
        A[tuple((arr - lo).T)] = True
        lab, n = ndimage.label(A)
        hl = lab[tuple(np.array(next(iter(s.H))) - lo)]
        v['not_connected'] = {k: sum(1 for kk in D if lab[tuple(np.array(kk) - lo)] != hl) for k, D in s.decks.items()}
        s.R = R
        return v

    def write(s):
        out = os.path.join(s.design, 'masks', 'decks')
        os.makedirs(out, exist_ok=True)
        files = {}
        for nm, D in s.decks.items():
            p = os.path.join(out, nm + '.vox.txt')
            rows = sorted((k[0], k[1], k[2], c) for k, c in D.items())
            open(p, 'w', encoding='utf-8', newline='\n').write('# 甲板 %s（世界座標，子作品 at 0,0,0）（%d 格）\n' % (nm, len(rows)) + '\n'.join('%d,%d,%d,%d' % r for r in rows) + '\n')
            files[nm] = {'cells': len(rows), 'sha256': hashlib.sha256(open(p, 'rb').read()).hexdigest()}
        return files

    def sheet(s, path):
        # 從上往下看：每一層各畫一張（那一層的格，最上面那格的顏色）
        names = ['lower', 'upper', 'spar', 'poop']
        sc, x0, x1, y0, y1 = 1, 80, 760, 90, 231
        Wd, Hd = (x1 - x0) * sc, (y1 - y0) * sc
        im = Image.new('RGB', (Wd * 2 + 60, (Hd + 40) * 2 + 70), (250, 249, 244))
        d = ImageDraw.Draw(im)
        d.text((20, 10), '餘燼號 新圖紙 06 v1：甲板（從上往下看；灰 ＝ 船殼）', font=DP.font(18), fill=(30, 30, 30))
        px = im.load()
        hullxy = {}
        for (x, y, z) in s.H:
            hullxy[(x, y)] = 1
        for i, nm in enumerate(names):
            ox, oy = 20 + (i % 2) * (Wd + 20), 50 + (i // 2) * (Hd + 40)
            d.text((ox, oy), nm, font=DP.font(14), fill=(60, 60, 60))
            top = {}
            for (x, y, z), c in s.decks[nm].items():
                if (x, y) not in top or z > top[(x, y)][0]:
                    top[(x, y)] = (z, c)
            for (x, y) in hullxy:
                if x0 <= x < x1 and y0 <= y < y1:
                    px[ox + (x - x0) * sc, oy + 20 + (y1 - 1 - y) * sc] = (200, 200, 200)
            for (x, y), (z, c) in top.items():
                if x0 <= x < x1 and y0 <= y < y1:
                    px[ox + (x - x0) * sc, oy + 20 + (y1 - 1 - y) * sc] = DP.rgb(c)
        im = im.resize((im.width * 2, im.height * 2), Image.NEAREST)
        im.save(path)


def main():
    sys.stdout.reconfigure(encoding='utf-8')
    design = os.path.abspath(sys.argv[1])
    D = Decks(design)
    D.from_con()
    D.waist()
    D.poop()
    v = {'read': D.read}
    v.update(D.verify())
    v['files'] = D.write()
    D.sheet(os.path.join(design, 'sheet06_decks_v1.png'))
    json.dump(v, open(os.path.join(design, 'verify_decks.json'), 'w', encoding='utf-8', newline='\n'), ensure_ascii=False, indent=1)
    print(json.dumps({k: v[k] for k in v if k != 'files'}, ensure_ascii=False, indent=1))


if __name__ == '__main__':
    main()
