# 餘燼號 階段三：上層砲門＋塗裝（plan.json ports_upper／paint）
#   輸入：餘燼號船殼（標記 船殼:end 那一刻）＋ 憲法號 design/source_ports.json（下層砲門的框，只拿來圈範圍）
#   ⇒ masks/ports/upper_carve.vox.txt（上層開口，carvevox 帶顏色守門）、masks/paint/paint.vox.txt（換色，stampvox overwrite=1）、
#      verify_ports.json、sheet03_ports_paint_v1.png
# 用法：python -I draft_ports.py <design 資料夾>
#   · 上層開口 ＝ 下層開口（從船殼量：框外擴 2 格裡、|dy| ≥ 10 沒有任何格的 (x, z)）往上 plan.band.height；刻掉那一格 (x, z+h) 的 |dy| ≥ 10 的格
#   · 塗裝：下層白帶（外緣那一格是 255 的 (x, z)，x ≥ paint.side_x_from）→ 暗紅；同一組 (x, z+h) 的外緣格 → 暗紅（上層帶）；兩條帶在每一欄的上下各一格外緣 → 金
#   · 船尾（x < side_x_from）的白線這一階段不動，船尾另一張圖紙
import sys, os, json, hashlib
import numpy as np
from PIL import Image, ImageDraw

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import draft_profile as DP   # noqa: E402

W = 'basecamp-ember-01m'
YC = 160


def export_mark(work, mark):
    import subprocess, tempfile
    with tempfile.TemporaryDirectory() as d:
        out = os.path.join(d, 'w.txt').replace('\\', '/')
        r = subprocess.run(['senate', 'cmd', 'sculpture', '--arg', 'op=export', '--arg', 'format=list', '--arg', 'work=' + work, '--arg', 'out=' + out,
                            '--arg', 'links=none', '--arg', 'mark=' + mark], capture_output=True, text=True, encoding='utf-8', errors='replace')
        if r.returncode != 0 or not os.path.exists(out):
            raise SystemExit('匯出失敗：' + (r.stdout + r.stderr)[-600:])
        return np.loadtxt(out, delimiter=',', comments='#', dtype=np.int32, ndmin=2, encoding='utf-8')


class Ports:
    def __init__(s, design):
        s.design = design
        s.plan = json.load(open(os.path.join(design, 'plan.json'), encoding='utf-8'))
        s.P = s.plan['ports_upper']
        s.C = s.plan['paint']
        s.h = s.plan['band']['height']
        a = export_mark(W, s.P['world_mark'])
        assert len(a) == s.P['world_voxels'], ('船殼現況跟 plan 記的不一樣', len(a))
        s.H = {(int(x), int(y), int(z)): int(c) for x, y, z, c in a}
        s.read = {'world': len(s.H)}

    def boxes(s):
        sp = json.load(open(os.path.join(DP.CON_DESIGN, 'source_ports.json'), encoding='utf-8'))
        B = [(p['n'], p['X_aft'], p['X_fwd'], p['sill'], p['lintel']) for p in sp['ports_gun_deck']]
        bv = s.P['bow_box']          # 憲法號 v1.2 船頭砲門（兩側垂直）的外框
        B.append((15, bv['x'][0], bv['x'][1], bv['z'][0], bv['z'][1]))
        return B

    def openings(s):
        dmin = s.P['dy_min']
        s.open = {'S': {}, 'P': {}}
        for n, xa, xb, za, zb in s.boxes():
            for side, sg in (('S', 1), ('P', -1)):
                cells = []
                for x in range(int(xa) - 2, int(xb) + 3):
                    for z in range(int(za) - 2, int(zb) + 3):
                        if not any((x, YC + sg * dy, z) in s.H for dy in range(dmin, 160)):
                            cells.append((x, z))
                s.open[side][n] = cells
        # 兩舷對稱（P 舷是 S 舷照 y 鏡過去的同一組 (x, z)）
        s.read['openings_S'] = sum(len(v) for v in s.open['S'].values())
        s.read['openings_P'] = sum(len(v) for v in s.open['P'].values())
        s.read['openings_mirror_diff'] = sum(len(set(s.open['S'][n]) ^ set(s.open['P'][n])) for n in s.open['S'])
        s.read['openings_per_port_S'] = {n: len(v) for n, v in s.open['S'].items()}

    def carve(s):
        dmin = s.P['dy_min']
        s.cut = {}
        for side, sg in (('S', 1), ('P', -1)):
            for n, L in s.open[side].items():
                for x, z in L:
                    zz = z + s.h
                    for dy in range(dmin, 160):
                        k = (x, YC + sg * dy, zz)
                        if k in s.H:
                            s.cut[k] = s.H[k]
        cols = {}
        for c in s.cut.values():
            cols[c] = cols.get(c, 0) + 1
        s.read['carve'] = len(s.cut)
        s.read['carve_colors'] = dict(sorted(cols.items()))
        # 每一個上層開口的 z 都要在插入段裡
        zs = [k[2] for k in s.cut]
        s.read['carve_z'] = [min(zs), max(zs)]
        assert s.plan['band']['cut_z'] <= min(zs) and max(zs) < s.plan['band']['cut_z'] + s.h, '上層開口跑出插入段'

    def outer(s, x, z, sg, H):
        ys = [YC + sg * dy for dy in range(1, 160) if (x, YC + sg * dy, z) in H]
        if not ys:
            return None
        return max(ys) if sg > 0 else min(ys)

    def paint(s):
        after = {k: c for k, c in s.H.items() if k not in s.cut}
        x0 = s.C['side_x_from']
        red, gold, white = s.C['band'], s.C['line'], 255
        s.pt = {}
        s.band_cols = {}
        for side, sg in (('S', 1), ('P', -1)):
            for x in range(x0, 700):
                low = []
                for z in range(s.C['low_z'][0], s.C['low_z'][1] + 1):
                    y = s.outer(x, z, sg, after)
                    if y is not None and after[(x, y, z)] == white:
                        low.append(z)
                if not low:
                    continue
                s.band_cols[(side, x)] = (min(low), max(low))
                for z in low:
                    y = s.outer(x, z, sg, after)
                    s.pt[(x, y, z)] = red
                    zu = z + s.h
                    yu = s.outer(x, zu, sg, after)
                    if yu is not None and after[(x, yu, zu)] in (36,):
                        s.pt[(x, yu, zu)] = red
                for zl, zh in ((min(low), max(low)), (min(low) + s.h, max(low) + s.h)):
                    for z in (zl - 1, zh + 1):
                        y = s.outer(x, z, sg, after)
                        if y is not None and after[(x, y, z)] == 36 and (x, y, z) not in s.pt:
                            s.pt[(x, y, z)] = gold
        # 下層白帶裡不是外緣的 255（砲門開口側面那幾格）也換紅 —— 不然從斜面看得到白邊
        for k, c in after.items():
            if c == white and k[0] >= x0 and s.C['low_z'][0] <= k[2] <= s.C['low_z'][1] and k not in s.pt:
                s.pt[k] = red
        before = {}
        for k in s.pt:
            before[after[k]] = before.get(after[k], 0) + 1
        to = {}
        for c in s.pt.values():
            to[c] = to.get(c, 0) + 1
        s.read['paint'] = len(s.pt)
        s.read['paint_from'] = dict(sorted(before.items()))
        s.read['paint_to'] = dict(sorted(to.items()))
        s.read['white_left_side'] = sum(1 for k, c in after.items() if c == white and k[0] >= x0 and k not in s.pt)
        s.read['white_left_stern'] = sum(1 for k, c in after.items() if c == white and k[0] < x0)
        s.after = after

    def write(s):
        files = {}
        for sub, name, D, head in (('ports', 'upper_carve', s.cut, '上層砲門開口（carvevox，行尾顏色守門；世界座標 at 0,0,0）'),
                                   ('paint', 'paint', s.pt, '塗裝換色（stampvox overwrite=1；世界座標 at 0,0,0）')):
            out = os.path.join(s.design, 'masks', sub)
            os.makedirs(out, exist_ok=True)
            p = os.path.join(out, name + '.vox.txt')
            rows = sorted((k[0], k[1], k[2], c) for k, c in D.items())
            open(p, 'w', encoding='utf-8', newline='\n').write('# %s（%d 格）\n' % (head, len(rows)) + '\n'.join('%d,%d,%d,%d' % r for r in rows) + '\n')
            files[name] = {'cells': len(rows), 'sha256': hashlib.sha256(open(p, 'rb').read()).hexdigest()}
        return files

    def sheet(s, path):
        em = dict(s.after)
        em.update(s.pt)
        im = DP.Ember.side_image(None, em, '', 165, 2, 80, 700)
        W_, H_ = im.width + 40, im.height + 110
        out = Image.new('RGB', (W_, H_), (250, 249, 244))
        d = ImageDraw.Draw(out)
        d.text((20, 12), '餘燼號 新圖紙 03 v1：上層砲門（下層開口 ＋ %d）＋ 塗裝（白帶 → 暗紅 %d、上層同形狀的帶、上下緣金線 %d）' % (s.h, s.C['band'], s.C['line']),
               font=DP.font(20), fill=(30, 30, 30))
        d.text((20, 44), '右舷側面、1 格 ＝ 2 px；上層刻 %d 格、換色 %d 格；船尾（x < %d）這一階段不動' % (len(s.cut), len(s.pt), s.C['side_x_from']), font=DP.font(14), fill=(80, 80, 80))
        out.paste(im, (20, 80))
        out.save(path)


def main():
    sys.stdout.reconfigure(encoding='utf-8')
    design = os.path.abspath(sys.argv[1])
    P = Ports(design)
    P.openings()
    P.carve()
    P.paint()
    v = {'read': P.read}
    v['files'] = P.write()
    P.sheet(os.path.join(design, 'sheet03_ports_paint_v1.png'))
    after = dict(P.after)
    after.update(P.pt)
    v['expect_after'] = len(after)
    v['structure_after'] = DP.Ember.structure(None, after)
    json.dump(v, open(os.path.join(design, 'verify_ports.json'), 'w', encoding='utf-8', newline='\n'), ensure_ascii=False, indent=1)
    print(json.dumps(v, ensure_ascii=False, indent=1))


if __name__ == '__main__':
    main()
