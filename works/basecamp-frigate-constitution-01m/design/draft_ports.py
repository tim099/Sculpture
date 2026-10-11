# 新圖紙 06（TASK-0490）：gun deck 砲門 —— plan.json 的 gunports 段 ＋ source_ports.json（11 號讀數）＋ 作品現況
#   ⇒ 刻穿外板與肋骨的 carve 盒子（masks/ports/carve_boxes.json）、砲門框的 3D 格子清單（masks/ports/lining.vox.txt）、
#     新圖紙 06（plan.json gunports.sheet；v1 sheet06_ports_v1.png、v1.2 sheet06_ports_v2.png）、verify_ports.json。
#   ⚠ 會清空 masks/ports/ 再寫 ⇒ 之後要重跑 draft_ports_touchup.py（細修清單也住那裡）。
# 用法：python -I draft_ports.py <design 資料夾>
#   · 開口：格中心落在讀數框裡的格（方砲門每一列同一個 x 範圍；船頭那個：gunports.bow_shape ＝ vertical ⇒ 平行四邊形的外框、兩側垂直（v1.2），
#     沒給 ⇒ 每一列照上下兩緣內插（v1））；兩舷鏡像。
#   · 刻：開口裡、屬於舷側的格（外板、方肋、cant）全刻 —— 從外面看得到船艙；hawse／knighthead／橫材／結構色碰到就拆盒子。
#   · 框：開口外一圈、肋骨那一層（molded 線往內 m(z)）的空格補 141（port sill／lintel／port timber）；
#     v1.2 再補「牆不能有洞」（wall_holes：相鄰開口刻到多深，牆就要實心到多深）。
#   · 讀「階段八第一刀之前」的作品（plan.json gunports.world_upto；空 ＝ 現況，雕之前用）。
import sys, os, json, glob, hashlib
import numpy as np
from PIL import Image, ImageDraw

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), 'tools'))
import draft_frames as DF          # noqa: E402
import draft_planking as DP        # noqa: E402
from replay import replay          # noqa: E402

YC = DP.YC
PLANK_COLORS = {36, 168, 255}


def cell_rows(z0, z1):
    """格中心在 [z0, z1] 的 z。"""
    return list(range(int(np.ceil(z0 - 0.5)), int(np.floor(z1 - 0.5)) + 1))


def x_span(a, b):
    return int(np.ceil(a - 0.5)), int(np.floor(b - 0.5))


class Ports:
    def __init__(s, design):
        s.design = design
        s.W = os.path.dirname(os.path.abspath(design))
        s.plan = json.load(open(os.path.join(design, 'plan.json'), encoding='utf-8'))
        s.P = s.plan['gunports']
        s.src = json.load(open(os.path.join(design, s.P['source']), encoding='utf-8'))
        upto = s.P.get('world_upto') or None
        s.world = {k: v[0] for k, v in replay(s.W, upto=upto).items()}
        s.m_of = DF.moulded_fn(s.plan['framing'])
        # 船殼表（跟外板同一份）
        s.M = DP.Model(design)
        s.M.cx.world = s.world
        s.M.lines()
        s.M.hull()
        s.members()

    def hb(s, x, z):
        return float(s.M.H[x - DP.X0, z])

    def members(s):
        """每一格屬於誰：階段六的木料名、階段七的外板、其餘 141 ＝ 方肋（底肋、futtocks、chock）、其他顏色 ＝ 結構。"""
        lab = {}
        for f in glob.glob(os.path.join(s.design, 'masks', 'ends', '*.vox.txt')):
            name = os.path.basename(f)[:-8]
            for line in open(f, encoding='utf-8'):
                if line.strip() and not line.startswith('#'):
                    x, y, z = (int(v) for v in line.split(',')[:3])
                    lab[(x, y, z)] = name
        for f in glob.glob(os.path.join(s.design, 'masks', 'planking', '*.vox.txt')):
            kind = 'structure-paint' if os.path.basename(f).startswith('paint_struct') else 'plank'
            for line in open(f, encoding='utf-8'):
                if line.strip() and not line.startswith('#'):
                    x, y, z = (int(v) for v in line.split(',')[:3])
                    lab[(x, y, z)] = kind
        s.lab = lab

    def kind(s, c):
        if c not in s.world:
            return None
        n = s.lab.get(c)
        if n is None:
            return 'frame' if s.world[c] == 141 else 'structure'
        if n == 'plank':
            return 'plank'
        if n.startswith('B-cant') or n.startswith('S-cant'):
            return 'cant'
        return n            # 其他階段六木料、structure-paint ⇒ 不准刻

    # ───────── 開口 ─────────
    def openings(s):
        out = []
        for p in s.src['ports_gun_deck']:
            rows = cell_rows(p['sill'], p['lintel'])
            xa, xb = x_span(p['X_aft'], p['X_fwd'])
            out.append({'n': p['n'], 'kind': 'square', 'rows': {z: (xa, xb) for z in rows},
                        'read': {'X_aft': p['X_aft'], 'X_fwd': p['X_fwd'], 'sill': p['sill'], 'lintel': p['lintel']}})
        b = s.src['bow_port']
        zb, zt = b['bottom']['Z'], b['top']['Z']
        rows = {}
        for z in cell_rows(zb, zt):
            if s.P.get('bow_shape') == 'vertical':
                # v1.2（Tim 2026-10-11「船頭的炮窗 試著雕刻成垂直的吧」＋示意圖）：兩側垂直 ＝ 平行四邊形的外框
                rows[z] = x_span(min(b['bottom']['X_aft'], b['top']['X_aft']), max(b['bottom']['X_fwd'], b['top']['X_fwd']))
                continue
            t = (z + 0.5 - zb) / (zt - zb)
            rows[z] = x_span(b['bottom']['X_aft'] + t * (b['top']['X_aft'] - b['bottom']['X_aft']),
                             b['bottom']['X_fwd'] + t * (b['top']['X_fwd'] - b['bottom']['X_fwd']))
        out.append({'n': 15, 'kind': 'bow', 'rows': rows,
                    'read': {'bottom': b['bottom'], 'top': b['top']}})
        s.ports = out

    def plan_cuts(s):
        """每個砲門每舷：開口裡的格分成「准刻」與「不准刻」；盒子（AABB）只能含准刻的格與空氣，含到不准刻的就拆。"""
        allowed = set(s.P['carve_members'])
        s.cuts, s.blocked = [], []
        for p in s.ports:
            for side in (1, -1):
                carve, bad = set(), []
                for z, (xa, xb) in p['rows'].items():
                    for x in range(xa, xb + 1):
                        for d in range(0, DP.NDY):
                            c = (x, YC + side * d, z)
                            k = s.kind(c)
                            if k is None:
                                continue
                            (carve.add(c) if k in allowed else bad.append((c, k)))
                if bad:
                    # 不准刻的格在開口裡 ⇒ 記下來（它們留著；盒子要避開）
                    s.blocked.append({'port': p['n'], 'side': side, 'cells': len(bad), 'kinds': sorted({k for _, k in bad})})
                bads = {c for c, _ in bad}
                for box in s.boxes_for(carve, bads):
                    s.cuts.append({'port': p['n'], 'side': side, 'box': box,
                                   'expect': sum(1 for c in carve if s.inside(c, box))})
                p.setdefault('carve', {})[side] = carve

    @staticmethod
    def inside(c, b):
        return b[0] <= c[0] <= b[1] and b[2] <= c[1] <= b[3] and b[4] <= c[2] <= b[5]

    def boxes_for(s, carve, bads):
        """先試一個 AABB；含到不准刻的格 ⇒ 每一列（z）一個；還含到 ⇒ 每一欄（x,z）一個。"""
        def aabb(cells):
            a = np.array(sorted(cells))
            return [int(a[:, 0].min()), int(a[:, 0].max()), int(a[:, 1].min()), int(a[:, 1].max()), int(a[:, 2].min()), int(a[:, 2].max())]

        def ok(b):
            return not any(s.inside(c, b) for c in bads) and all(
                (c in carve) or (c not in s.world) for c in s.cells_in(b))
        if not carve:
            return []
        b = aabb(carve)
        if ok(b):
            return [b]
        out = []
        for z in sorted({c[2] for c in carve}):
            row = {c for c in carve if c[2] == z}
            b = aabb(row)
            if ok(b):
                out.append(b)
                continue
            for x in sorted({c[0] for c in row}):
                col = {c for c in row if c[0] == x}
                b = aabb(col)
                if not ok(b):
                    raise SystemExit('一欄的盒子也含到不准刻的格：%s' % b)
                out.append(b)
        return out

    def cells_in(s, b):
        for x in range(b[0], b[1] + 1):
            for y in range(b[2], b[3] + 1):
                for z in range(b[4], b[5] + 1):
                    yield (x, y, z)

    # ───────── 砲門框 ─────────
    def lining(s):
        """開口外一圈（左右 x−1／x+1、上下 z−1／z+1）在肋骨那一層（hb − m(z) ≤ |dy| < hb）的空格 ⇒ 141。"""
        carved = set()
        for p in s.ports:
            for side in (1, -1):
                carved |= p['carve'][side]
        fill = {}
        for p in s.ports:
            rows = p['rows']
            zs = sorted(rows)
            ring = set()
            for z in zs:
                xa, xb = rows[z]
                ring.add((xa - 1, z))
                ring.add((xb + 1, z))
            for z, zz in ((zs[0] - 1, zs[0]), (zs[-1] + 1, zs[-1])):
                xa, xb = rows[zz]
                for x in range(xa - 1, xb + 2):
                    ring.add((x, z))
            for (x, z) in ring:
                h = s.hb(x, z)
                m = float(s.m_of(z + 0.5))
                for d in range(int(np.floor(h - m)), int(np.ceil(h))):
                    if not (h - m <= d + 0.0 and d < h):
                        continue
                    for side in (1, -1):
                        c = (x, YC + side * d, z)
                        if c in s.world and c not in carved:
                            continue
                        if c in carved:
                            continue
                        fill[c] = s.P['lining_color']
                p.setdefault('ring', len(ring))
        s.fill = fill
        s.wall_holes(carved)

    def wall_holes(s, carved):
        """v1.2：開口四面那一圈的牆不能有洞 —— 相鄰開口那一欄刻到多深（最內的 dy），牆那一欄從這個深度到它自己的外緣每一格都要是實心，
        空的補 141。v1 只補肋骨那一層（hb − m(z)），cant 那一帶的肋骨比 m(z) 深，船頭砲門後壁留過一道看得進船艙的縫（v1.1 手補 6 格）。"""
        def occ(c):
            return (c in s.world and c not in carved) or c in s.fill
        s.hole_fill = {}
        for p in s.ports:
            rows = p['rows']
            zs = sorted(rows)
            ring = {}                                   # 牆那一欄 (x, z) → 相鄰開口那一欄 (x, z)
            for z in zs:
                xa, xb = rows[z]
                ring[(xa - 1, z)] = (xa, z)
                ring[(xb + 1, z)] = (xb, z)
            for z, zz in ((zs[0] - 1, zs[0]), (zs[-1] + 1, zs[-1])):
                xa, xb = rows[zz]
                for x in range(xa - 1, xb + 2):
                    ring.setdefault((x, z), (min(max(x, xa), xb), zz))
            n = 0
            for (x, z), (ax, az) in ring.items():
                for side in (1, -1):
                    dug = [d for d in range(DP.NDY) if (ax, YC + side * d, az) in p['carve'][side]]
                    wall = [d for d in range(DP.NDY) if occ((x, YC + side * d, z))]
                    if not dug or not wall:
                        continue
                    for d in range(max(min(wall), min(dug)), max(wall) + 1):
                        c = (x, YC + side * d, z)
                        if not occ(c):
                            s.hole_fill[c] = s.P['lining_color']
                            n += 1
            p['wall_holes'] = n
        s.fill.update(s.hole_fill)

    # ───────── 輸出 ─────────
    def write(s):
        out = os.path.join(s.design, 'masks', 'ports')
        os.makedirs(out, exist_ok=True)
        for f in glob.glob(os.path.join(out, '*')):
            os.remove(f)
        boxes = [{'port': c['port'], 'side': c['side'], 'x1': c['box'][0], 'x2': c['box'][1], 'y1': c['box'][2], 'y2': c['box'][3],
                  'z1': c['box'][4], 'z2': c['box'][5], 'expect': c['expect']} for c in s.cuts]
        json.dump({'note': '階段八砲門：每個盒子 carve 一刀，讀回刻掉的格數 ＝ expect（盒子裡只有准刻的格與空氣）', 'boxes': boxes},
                  open(os.path.join(out, 'carve_boxes.json'), 'w', encoding='utf-8', newline='\n'), ensure_ascii=False, indent=1)
        p = os.path.join(out, 'lining.vox.txt')
        body = '\n'.join('%d,%d,%d,%d' % (c[0], c[1], c[2], v) for c, v in sorted(s.fill.items()))
        open(p, 'w', encoding='utf-8', newline='\n').write('# lining —— 砲門框（port sill／lintel／port timber）補在肋骨那一層的空格（%d 格，at=0,0,0）\n' % len(s.fill) + body + '\n')
        s.lining_sha = hashlib.sha256(open(p, 'rb').read()).hexdigest()
        s.boxes = boxes


def render_sheet(P, path):
    """新圖紙 06：右舷側面（每一欄最外面那一格）＋開口（刻掉的格標紅）＋讀數框（藍）。只畫 X 170..670、Z 70..115。"""
    X0s, X1s, Z0s, Z1s, sc = 170, 670, 70, 116, 4
    W, H = X1s - X0s, Z1s - Z0s
    img = np.full((H, W, 3), 250, np.uint8)
    carved = set()
    for p in P.ports:
        carved |= p['carve'][1]
    for x in range(X0s, X1s):
        for z in range(Z0s, Z1s):
            best = None
            for d in range(DP.NDY - 1, -1, -1):
                c = (x, YC + d, z)
                if c in carved:
                    best = (230, 60, 50)
                    break
                if c in P.fill:
                    best = (200, 160, 110)
                    break
                if c in P.world:
                    best = DP.rgb332(P.world[c]) if P.world[c] in PLANK_COLORS else (200, 185, 160)
                    break
            if best:
                img[Z1s - 1 - z, x - X0s] = best
    im = Image.fromarray(img).resize((W * sc, H * sc), Image.NEAREST)
    d = ImageDraw.Draw(im)

    def Pt(X, Z):
        return ((X - X0s) * sc, (Z1s - Z) * sc)
    for p in P.ports:
        r = p['read']
        if p['kind'] == 'square':
            d.rectangle([Pt(r['X_aft'], r['lintel']), Pt(r['X_fwd'], r['sill'])], outline=(30, 80, 220), width=2)
        else:
            t, b = r['top'], r['bottom']
            d.polygon([Pt(b['X_aft'], b['Z']), Pt(b['X_fwd'], b['Z']), Pt(t['X_fwd'], t['Z']), Pt(t['X_aft'], t['Z'])], outline=(30, 80, 220))
    ver = 'v2  bow port: vertical sides (outer box of the drawing parallelogram)' if P.P.get('bow_shape') == 'vertical' else 'v1'
    d.text((8, 8), 'sheet 06 %s  gun deck ports  (red: carved cells, starboard;  blue: drawing 11 port outlines;  tan: lining fill)' % ver, fill=(0, 0, 0))
    im.save(path)


def main():
    design = sys.argv[1]
    P = Ports(design)
    P.openings()
    P.plan_cuts()
    P.lining()
    P.write()
    tot = sum(c['expect'] for c in P.cuts)
    kinds = {}
    for p in P.ports:
        for side in (1, -1):
            for c in p['carve'][side]:
                k = P.kind(c)
                kinds[k] = kinds.get(k, 0) + 1
    per = []
    for p in P.ports:
        zs = sorted(p['rows'])
        per.append({'n': p['n'], 'kind': p['kind'], 'z': [zs[0], zs[-1]], 'x_rows': {str(z): list(p['rows'][z]) for z in zs},
                    'carve': [len(p['carve'][1]), len(p['carve'][-1])], 'wall_holes': p['wall_holes'], 'read': p['read']})
    v = {'title': P.P['title'], 'task': P.P['task'], 'world_upto': P.P.get('world_upto', ''), 'world_voxels': len(P.world),
         'bow_shape': P.P.get('bow_shape', 'parallelogram'),
         'ports': per, 'carve_boxes': len(P.cuts), 'carve_cells': tot, 'carve_by_kind': kinds,
         'blocked_in_openings': P.blocked, 'lining_cells': len(P.fill), 'lining_wall_holes': len(P.hole_fill), 'lining_sha256': P.lining_sha,
         'expect_after': len(P.world) - tot + len(P.fill)}
    json.dump(v, open(os.path.join(design, 'verify_ports.json'), 'w', encoding='utf-8', newline='\n'), ensure_ascii=False, indent=1)
    render_sheet(P, os.path.join(design, P.P.get('sheet', 'sheet06_ports_v1.png')))
    print(json.dumps({k: v[k] for k in ('world_voxels', 'bow_shape', 'carve_boxes', 'carve_cells', 'carve_by_kind', 'blocked_in_openings', 'lining_cells', 'lining_wall_holes', 'expect_after')}, ensure_ascii=False))


if __name__ == '__main__':
    main()
