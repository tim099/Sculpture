# 新圖紙 12 梯子（階段十一，TASK-0538；v2 加了沿 Y 的走道梯）：plan.json ladders ＋ 組裝件的 export list（梯子加進來之前）
#   ⇒ masks/ladders/ladders.vox.txt（子作品 -ladders、船殼座標、關聯 at 0,0,0）、masks/ladders/scuttles_carve.vox.txt（上甲板子作品開梯口，carvevox 帶顏色）、
#     ladder_points.json（每座 4 個給遊戲的點：<名>.foot／.lo／.hi／.head）、verify_ladders.json、sheet12_ladders_v1.png
# 用法：python -I draft_ladders.py <design 資料夾> <組裝件 export list>
#   · 一座梯子：最上一欄 xe 貼著上一層的邊（甲板的前緣／後緣、梯口的一邊），往 d 斜下；欄 t 的側板上緣 zs(t) ＝ floor(zcap − slope·t)，側板高 band 格；
#     踏板每 rise 格一階、佔 run 欄，在兩根側板之間。底下那一層的甲板面 zl 從現況量（那一欄梯子中線往下第一格實心 ＋ 1）。
#   · 每一座都量：梯子每一格是空氣、踏板上方 headroom 格是空氣（只量到上一層甲板底下）、梯腳外 landing 欄是空氣、梯腳兩根側板踩在實心上。
#   · 給遊戲的點（造船規格 §9）：都取「腳踩的那一格」＝ 地板或踏板上面第一格空氣、梯子中線那一列；
#     lo／hi ＝ 最低／最高那一階；foot ＝ 梯腳往 d 走、第一段連續 3 欄地板一樣高、上面 ≥ 3 格空氣的第一欄；head ＝ 梯頂往 −d 走、同樣條件。
#   · v2：梯子可以沿 Y 走（L['axis'] ＝ 'y'：ae ＝ 最上一列的 y、cc ＝ 梯子中線的 x）—— 走道內緣往船中斜下到上甲板；
#     沿 X 的照舊（xe、yc）。程式裡一律用「沿梯 a、橫跨 c」兩個座標，只在 at() 換成世界座標。
import sys, os, json, hashlib
import numpy as np
from scipy import ndimage
from PIL import Image, ImageDraw

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import draft_planking as DP      # noqa: E402

NX, NY, NZ = 1024, 320, 260


class Ladders:
    def __init__(s, design, asm_list):
        s.design = design
        s.plan = json.load(open(os.path.join(design, 'plan.json'), encoding='utf-8'))
        s.P = s.plan['ladders']
        w = DP.read_list(asm_list)
        assert len(w) == s.P['assembly_cells'], ('組裝件格數對不上', len(w), s.P['assembly_cells'])
        s.asm_sha = hashlib.sha256(open(asm_list, 'rb').read()).hexdigest()
        s.Wc = w
        s.W = np.zeros((NX, NY, NZ), bool)
        for (x, y, z) in w:
            s.W[x, y, z] = True
        # 梯口：上甲板子作品的板（顏色守門）
        upper = DP.read_list(os.path.join(design, 'masks', 'decks', 'upper.vox.txt'))
        s.carve = {}
        for sc in s.P['scuttles']:
            for (x, y, z), c in upper.items():
                if sc['X'][0] <= x <= sc['X'][1] and abs(y - 160) <= sc['dy']:
                    s.carve[(x, y, z)] = c
        for c in s.carve:
            s.W[c] = False
        s.cells, s.points, s.rows = {}, {}, []

    @staticmethod
    def axis(L):
        """回 (沿梯起點 ae, 橫跨中線 cc, 是不是沿 Y)"""
        if L.get('axis', 'x') == 'y':
            return L['ae'], L['cc'], True
        return L['xe'], L['yc'], False

    @staticmethod
    def at(a, c, z, ay):
        return (c, a, z) if ay else (a, c, z)

    def floor_below(s, x, y, z):
        """(x, y) 這一欄從 z 往下第一格實心 ＋ 1（走的那一格）。"""
        for zz in range(z, 0, -1):
            if s.W[x, y, zz - 1] or (x, y, zz - 1) in s.cells:
                return zz
        return None

    def free(s, c):
        return not s.W[c] and c not in s.cells

    def flat_from(s, a, d, c, zhint, ay=False):
        """從沿梯座標 a 往 d 走：第一段連續 3 欄走的那一格一樣高、上面 ≥ 3 格空氣 ⇒ 回第一欄 (a, z)。"""
        for k in range(0, 40):
            ok = True
            zs = []
            for j in range(3):
                aa = a + d * (k + j)
                x, y, _ = s.at(aa, c, 0, ay)
                z = s.floor_below(x, y, zhint + 6)
                if z is None or any(not s.free(s.at(aa, c, z + h, ay)) for h in range(3)):
                    ok = False
                    break
                zs.append(z)
            if ok and len(set(zs)) == 1:
                return a + d * k, zs[0]
        return None

    def build_one(s, L):
        G = s.P['geometry']
        C = s.P['colors']
        slope = G['rise'] / G['run']
        ae, cc, ay = s.axis(L)
        d = L['d']

        def A(a, c, z):
            return s.at(a, c, z, ay)
        c0, c1 = cc - G['width'] // 2, cc + G['width'] // 2
        # 上一層：梯頂那一欄往 −d 一欄的走的那一格
        zu = s.floor_below(*A(ae - d, cc, L['z_hint_top'] + 4))
        zcap = zu + G['cap_up']
        cells = {}
        cols = []
        t = 0
        while True:
            zs = int(np.floor(zcap - slope * t))
            a = ae + d * t
            zl = s.floor_below(*A(a, cc, zs))
            if zl is None:
                return None, '梯子底下沒有地板 a %d' % a
            lo = max(zl, zs - G['band'] + 1)
            for c in (c0, c1):
                for z in range(lo, zs + 1):
                    cells[A(a, c, z)] = C['stringer']
            cols.append((t, a, zs, zl))
            if zs - G['band'] + 1 <= zl:
                break
            t += 1
            if t > 60:
                return None, '太長'
        R = len(cols)
        zfoot = cols[-1][3]
        treads = []
        j = 0
        while True:
            zt = zcap - G['rise'] * j - G['rise']
            if zt < zfoot + 2:
                break
            for tt in (G['run'] * j + 1, G['run'] * j + 2):
                if tt >= R:
                    continue
                a = ae + d * tt
                for c in range(c0 + 1, c1):
                    cells[A(a, c, zt)] = C['tread']
            treads.append((ae + d * (G['run'] * j + 1), zt))
            j += 1
        bad = [c for c in cells if not s.free(c)]
        if bad:
            return None, '梯子撞到 %d 格（第一格 %s）' % (len(bad), bad[0])
        af = cols[-1][1]
        if not all(s.W[A(af, c, zfoot - 1)] for c in (c0, c1)):
            return None, '梯腳底下不是實心'
        head = []
        for t, a, zs, zl in cols:
            for c in range(c0 + 1, c1):
                for z in range(zs + 1, min(zs + 1 + G['headroom'], zu - 1)):
                    if A(a, c, z) not in cells and not s.free(A(a, c, z)):
                        head.append(A(a, c, z))
        if head:
            return None, '頭頂撞到 %d 格（第一格 %s）' % (len(head), head[0])
        land = [A(af + d * k, c, z) for k in range(1, G['landing'] + 1) for c in range(c0, c1 + 1) for z in range(zfoot, zfoot + G['headroom'])]
        land = [c for c in land if not s.free(c)]
        if land:
            return None, '梯腳外撞到 %d 格（第一格 %s）' % (len(land), land[0])
        return dict(cells=cells, cols=cols, treads=treads, zcap=zcap, zu=zu, zfoot=zfoot, af=af, c=[c0, c1], ay=ay), None

    def build(s):
        for L in s.P['list']:
            got, why = s.build_one(L)
            if not got:
                s.rows.append({'name': L['name'], 'placed': False, 'why': why})
                continue
            s.cells.update(got['cells'])
            ae, cc, ay = s.axis(L)
            d = L['d']
            tr = got['treads']
            lo = s.at(tr[-1][0], cc, tr[-1][1] + 1, ay)
            hi = s.at(tr[0][0], cc, tr[0][1] + 1, ay)
            f = s.flat_from(got['af'] + d, d, cc, got['zfoot'], ay)
            h = s.flat_from(ae - d, -d, cc, got['zu'], ay)
            assert f and h, ('站不住', L['name'], f, h)
            pts = {'foot': s.at(f[0], cc, f[1], ay), 'lo': lo, 'hi': hi, 'head': s.at(h[0], cc, h[1], ay)}
            for k, p in pts.items():
                s.points['%s.%s' % (L['name'], k)] = [int(v) for v in p]
            s.rows.append({'name': L['name'], 'placed': True, 'axis': 'y' if ay else 'x', 'ae': ae, 'af': got['af'], 'cc': cc, 'd': d, 'c': got['c'],
                           'zcap': got['zcap'], 'zfoot': got['zfoot'], 'rise': got['zcap'] - got['zfoot'], 'treads': len(tr),
                           'cells': len(got['cells']), 'points': {k: [int(v) for v in p] for k, p in pts.items()}})

    def verify(s):
        v = {'cells': len(s.cells), 'placed': sum(1 for r in s.rows if r['placed']), 'of': len(s.rows),
             'scuttle_carve': len(s.carve), 'overlap_world': sum(1 for c in s.cells if s.W[c])}
        xs = [c[0] for c in s.cells]
        xa, xb = min(xs) - 3, max(xs) + 4
        A = s.W[xa:xb].copy()
        for c in s.cells:
            A[c[0] - xa, c[1], c[2]] = True
        lab, n = ndimage.label(A)
        base = set(np.unique(lab[s.W[xa:xb]])) - {0}
        fl = [c for c in s.cells if lab[c[0] - xa, c[1], c[2]] not in base]
        v['floating'] = len(fl)
        v['mirror_missing'] = sum(1 for (x, y, z) in s.cells if (x, 320 - y, z) not in s.cells)
        # v2：走道梯兩舷故意前後錯開（同一發橫向的砲彈不會同時打斷兩舷）⇒ 「該成對」的那幾座另外量鏡像
        asym = set()
        for r in s.rows:
            if r['placed'] and r.get('axis') == 'y':
                asym |= {c for c in s.cells if r['c'][0] <= c[0] <= r['c'][1] and min(r['ae'], r['af']) <= c[1] <= max(r['ae'], r['af'])}
        v['mirror_missing_paired'] = sum(1 for (x, y, z) in s.cells if (x, y, z) not in asym and (x, 320 - y, z) not in s.cells)
        v['asymmetric_cells'] = len(asym)
        # 點：腳踩的那一格是空氣、底下是實心
        bad = []
        for k, p in s.points.items():
            x, y, z = p
            if not s.free((x, y, z)) or not (s.W[x, y, z - 1] or (x, y, z - 1) in s.cells):
                bad.append(k)
        v['points'] = len(s.points)
        v['points_not_standing'] = bad
        v['expect_assembly_after'] = s.P['assembly_cells'] - len(s.carve) + len(s.cells)
        s.v = v

    def write(s):
        out = os.path.join(s.design, 'masks', 'ladders')
        os.makedirs(out, exist_ok=True)
        s.files = {}
        for name, cells, note in (('ladders', s.cells, '梯子 %d 座（子作品 -ladders；船殼座標；stampvox at=0,0,0）' % sum(1 for r in s.rows if r['placed'])),
                                  ('scuttles_carve', s.carve, '上甲板子作品開梯口（carvevox at=0,0,0，帶顏色守門）')):
            p = os.path.join(out, name + '.vox.txt')
            body = ''.join('%d,%d,%d,%d\n' % (c[0], c[1], c[2], v) for c, v in sorted(cells.items()))
            open(p, 'w', encoding='utf-8', newline='\n').write('# 夜燈號 %s —— %s（新圖紙 12 %s，draft_ladders.py 產；%d 格）\n' % (name, note, s.P.get('version', 'v1'), len(cells)) + body)
            s.files[name] = {'cells': len(cells), 'sha256': hashlib.sha256(open(p, 'rb').read()).hexdigest()}
        json.dump({'note': '梯子給遊戲的點（造船規格 §9：<梯名>.foot／.lo／.hi／.head，腳踩的那一格）；船殼座標 ＝ 子作品座標（關聯 at 0,0,0）',
                   'points': s.points}, open(os.path.join(s.design, 'ladder_points.json'), 'w', encoding='utf-8', newline='\n'), ensure_ascii=False, indent=1)


def render_sheet(F, path):
    """每座梯子一張側剖面（梯子中線那一片）：現況淡色、梯子原色、四個點標字。"""
    sc = 5
    tiles = []
    for r in F.rows:
        if not r['placed']:
            continue
        ay = r['axis'] == 'y'
        aa, ab = min(r['ae'], r['af']) - 12, max(r['ae'], r['af']) + 13
        za, zb = r['zfoot'] - 5, r['zcap'] + 10
        cc = r['cc']
        img = np.full((zb - za, ab - aa, 3), 250, np.uint8)
        for ia, a in enumerate(range(aa, ab)):
            for iz, z in enumerate(range(zb - 1, za - 1, -1)):
                c = F.cells.get(F.at(a, cc, z, ay)) or F.cells.get(F.at(a, r['c'][0], z, ay))
                if c:
                    img[iz, ia] = DP.rgb332(c)
                elif F.W[F.at(a, cc, z, ay)]:
                    img[iz, ia] = (205, 198, 185)
        im = Image.fromarray(img).resize(((ab - aa) * sc, (zb - za) * sc), Image.NEAREST)
        dr = ImageDraw.Draw(im)
        for k, p in r['points'].items():
            pa = p[1] if ay else p[0]
            px, pz = (pa - aa + 0.5) * sc, (zb - p[2] - 0.5) * sc
            dr.ellipse([px - 4, pz - 4, px + 4, pz + 4], outline=(220, 30, 30), width=2)
            dr.text((px + 5, pz - 12), k, fill=(220, 30, 30))
        dr.text((4, 4), '%s  %s %d->%d (%s %d)  z %d->%d  %d steps' % (r['name'], 'y' if ay else 'x', r['ae'], r['af'], 'x' if ay else 'y', cc,
                                                                    r['zcap'], r['zfoot'], r['treads']), fill=(0, 0, 0))
        tiles.append(im)
    W = max(t.size[0] for t in tiles) * 2 + 30
    rows = [tiles[i:i + 2] for i in range(0, len(tiles), 2)]
    H = sum(max(t.size[1] for t in rw) + 10 for rw in rows)
    can = Image.new('RGB', (W, H), (255, 255, 255))
    y = 0
    for rw in rows:
        x = 0
        for t in rw:
            can.paste(t, (x, y))
            x += t.size[0] + 20
        y += max(t.size[1] for t in rw) + 10
    can.save(path)


def main():
    design, asm = sys.argv[1], sys.argv[2]
    F = Ladders(design, asm)
    F.build()
    F.verify()
    F.write()
    F.v['files'] = F.files
    F.v['ladders'] = F.rows
    F.v['assembly_list_sha256'] = F.asm_sha
    json.dump(F.v, open(os.path.join(design, 'verify_ladders.json'), 'w', encoding='utf-8', newline='\n'), ensure_ascii=False, indent=1)
    if any(r['placed'] for r in F.rows):
        render_sheet(F, os.path.join(design, 'sheet12_ladders_%s.png' % F.P.get('version', 'v1')))
    print(json.dumps({k: F.v[k] for k in F.v if k not in ('ladders', 'files')}, ensure_ascii=False))
    for r in F.rows:
        print(json.dumps({k: r[k] for k in r if k != 'points'}, ensure_ascii=False))


if __name__ == '__main__':
    main()
