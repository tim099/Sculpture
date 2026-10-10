# 新圖紙 04 肋骨圖（TASK-0485）：plan.json 的 framing 段 ＋ 新圖紙 03 的船殼（draft_lines.Hull）⇒ 雙肋兩片的遮罩、肋骨圖、對照圖、verify_frames.json。
# 用法：python -I draft_frames.py <design 資料夾>
#   · 每個肋位兩片：plane A ＝ 底肋那一片（x 欄 round(X)−1..+1，沿用階段四）、plane B 貼在船頭側（round(X)+2..+4）。
#   · 一格屬於肋骨 ⇔ |dy| ≥ 3、在 molded 線內、離 molded 線 ≤ m(z)、z 不超過舷頂；屬於哪一段看它最近的 molded 線點的弧長（從龍骨側面 z=7 起量）。
#   · plane A 有底肋的站：弧長 ≤ 底肋頭（36）那段是階段四的底肋，這裡不重產；其餘照產。
#   · 遮罩給 `stampimg facing=x+`（u→Z、v→Y 且 v 翻轉）；一張遮罩多色（每段一色）。
import sys, os, json, math
import numpy as np
from PIL import Image

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import draft as D            # noqa: E402
import draft_lines as DL     # noqa: E402

YC = DL.YC


def moulded_fn(F):
    zz = np.array([p[0] for p in F['moulded_z']], float)
    mm = np.array([p[1] for p in F['moulded_z']], float)
    return lambda z: float(np.interp(z, zz, mm))


def sheer_fit(F):
    pts = np.array([[p[1], p[2]] for p in F['sheer_points']], float)
    c = np.polyfit(pts[:, 0], pts[:, 1], 2)
    res = pts[:, 1] - np.polyval(c, pts[:, 0])
    return c, res


def members_for(F, plane, arc_end):
    """這一片的分段；短於 min_piece_arc 的尾段併進上一段。"""
    ms = [list(m) for m in F['members'][plane]]
    out = []
    for name, a0, a1, col in ms:
        if a0 >= arc_end:
            break
        out.append([name, a0, min(a1, arc_end), col])
    if len(out) >= 2 and out[-1][2] - out[-1][1] < F['min_piece_arc']:
        out[-2][2] = out[-1][2]
        out.pop()
    return out


def plane_cells(hull, F, m_of, Xp, top, floor_set=None, floor_head=None):
    """一片肋骨在 Y-Z 平面的格（dy, z, 段序）。floor_set ＝ 這一站底肋的 (dy, z)（plane A 有底肋時）。"""
    sec = hull.section(Xp, 7.0, top)
    seg = np.diff(sec, axis=0)
    arc = np.r_[0.0, np.cumsum(np.hypot(seg[:, 0], seg[:, 1]))]
    arc_end = float(arc[-1])
    cells = {}
    # 上限含 floor(top)：中心在舷頂以下的那一格也要（v1 少跑一格 ⇒ 肋骨頂比 sheer 矮 1–2 格，verifier 量到的）
    for z in range(8, int(math.floor(top)) + 1):
        zc = z + 0.5
        if zc > top:
            continue
        hbz = hull.hb(Xp, [zc])[0]
        if np.isnan(hbz):
            continue
        for dy in range(F['keep_clear_dy'] + 1, int(hbz) + 1):
            yc = float(dy)
            if yc >= hbz:
                continue
            d = np.hypot(sec[:, 0] - yc, sec[:, 1] - zc)
            i = int(np.argmin(d))
            if d[i] > m_of(zc):
                continue
            s = float(arc[i])
            if floor_set is not None and (s <= floor_head or (dy, z) in floor_set):
                continue
            cells[(dy, z)] = s
    # 補單格針孔：帶子很薄（舷頂附近 m≈1.85）時，最近頂點的取樣會漏掉夾在中間的一格（v1：f+9 B、f+13 B 在 z 119）
    holes = {}
    for (dy, z), s in cells.items():
        for c, pair in (((dy, z + 1), ((dy, z), (dy, z + 2))), ((dy + 1, z), ((dy, z), (dy + 2, z)))):
            if c in cells or c in holes or not all(p in cells for p in pair):
                continue
            if floor_set is not None and c in floor_set:
                continue
            # 不看 molded 線：缺口多半落在新圖紙 03 船殼舷頂附近（z≈121）那個往內凹的小折角外面，美觀優先直接補平
            if c[1] + 0.5 <= top:
                holes[c] = s
    cells.update(holes)
    return cells, arc_end, sec


def write_mask_multi(path, cells_yzc):
    ys = [c[0] for c in cells_yzc]
    zs = [c[1] for c in cells_yzc]
    y0, z0 = min(ys), min(zs)
    h, w = max(ys) - y0 + 1, max(zs) - z0 + 1
    a = np.zeros((h, w, 4), np.uint8)
    for y, z, col in cells_yzc:
        r, g, b = D.palette_rgb(col)
        a[h - 1 - (y - y0), z - z0] = (r, g, b, 255)
    Image.fromarray(a, 'RGBA').save(path)
    return y0, z0, w, h


def main():
    design = sys.argv[1]
    plan = json.load(open(os.path.join(design, 'plan.json'), encoding='utf-8'))
    src = json.load(open(os.path.join(design, 'source_lines.json'), encoding='utf-8'))
    vl = json.load(open(os.path.join(design, 'verify_lines.json'), encoding='utf-8'))
    F = plan['framing']
    L = plan['lines']
    hull = DL.Hull(plan, src)
    C, polys = D.build(plan)
    m_of = moulded_fn(F)
    sc, sres = sheer_fit(F)
    floors = {r['f']: r for r in vl['floors']}
    fx0, fsp = L['frames']['x0'], L['frames']['spacing']

    mdir = os.path.join(design, 'masks', 'frames')
    os.makedirs(mdir, exist_ok=True)
    out = {'sheer': {'coef': [float(v) for v in sc], 'residuals': {p[0]: round(float(r), 2) for p, r in zip(F['sheer_points'], sres)}},
           'moulded_z': F['moulded_z'], 'planes': []}
    bcells = {}
    for f in range(F['f_from'], F['f_to'] + 1):
        X = fx0 + fsp * f
        for plane in ('A', 'B'):
            off = 0 if plane == 'A' else F['plane_b_offset']
            x0 = int(round(X)) - F['sided'] // 2 + off
            Xp = X + off
            hull_top = hull.section(Xp, 0, L['z_max'])[-1][1]
            top = min(float(np.polyval(sc, Xp)), float(hull_top))
            fset = head = None
            if plane == 'A' and f in floors:
                cs, _ = DL.floor_cells(hull, plan, C, X)
                fset = set(cs)
                head = L['floor']['head_arc']
            cells, arc_end, sec = plane_cells(hull, F, m_of, Xp, top, fset, head)
            if not cells:
                continue
            if plane == 'B':
                bcells[f] = set(cells)
            mem = members_for(F, plane, arc_end)
            yzc, counts = [], {}
            for (dy, z), s in cells.items():
                k = next(j for j, mm in enumerate(mem) if s <= mm[2] or j == len(mem) - 1)
                name, col = mem[k][0], mem[k][3]
                for sg in (1, -1):
                    yzc.append((YC + sg * dy, z, col))
                counts[name] = counts.get(name, 0) + 2
            png = 'design/masks/frames/f%+03d%s.png' % (f, plane)
            y0, z0, w, h = write_mask_multi(os.path.join(design, png.split('/', 1)[1]), yzc)
            out['planes'].append({'f': f, 'plane': plane, 'X': round(Xp, 2), 'x_cells': [x0, x0 + F['sided'] - 1], 'top': round(top, 2),
                                  'arc_end': round(arc_end, 1), 'members': [[mm[0], round(mm[1], 1), round(mm[2], 1), mm[3]] for mm in mem],
                                  'cells_yz': len(yzc), 'counts': counts, 'has_floor': fset is not None,
                                  'stamp': {'png': png, 'at': '%d,%d,%d' % (x0, y0, z0), 'facing': 'x+', 'thickness': F['sided'], 'expect_pixels': len(yzc)}})
    # chock：plane B 跟下一站底肋貼齊（中間 0 格）、兩站都有底肋時，keelson 底下中線那一格（y 158..162、z 8..keelson 底−1）
    # 被龍骨、keelson、兩片底肋與 plane B 的 dy=±3 四面封死 ⇒ 看不到，匯出時卻多一層內殼（v1 量到 5 個、共 300 格）。填 141。
    ks = vl['keelson']['stamp']
    ka = np.array(Image.open(os.path.join(design, ks['png'].split('/', 1)[1])).convert('RGBA'))
    kx0, _, kz0 = [int(v) for v in ks['at'].split(',')]
    kb = {}
    for u in range(ka.shape[1]):
        rows = np.where(ka[:, u, 3] >= 128)[0]
        if len(rows):
            kb[kx0 + u] = kz0 + int(rows.min())
    pl = {(p['f'], p['plane']): p for p in out['planes']}
    out['chocks'] = []
    for f in sorted(floors):
        if f + 1 not in floors or (f, 'B') not in pl:
            continue
        bx0, bx1 = pl[(f, 'B')]['x_cells']
        if bx1 + 1 != floors[f + 1]['x_cells'][0]:
            continue
        side = F['keep_clear_dy'] + 1
        if not all((side, z) in bcells[f] for x in range(bx0, bx1 + 1) for z in range(8, kb[x])):
            continue      # 側牆（dy=±3）底下有缺口 ⇒ 空腔通到外面，不是封死的，不填
        for x in range(bx0, bx1 + 1):
            out['chocks'].append({'f': f, 'x': x, 'y': [YC - 2, YC + 2], 'z': [8, kb[x] - 1], 'color': 141})
    render(design, plan, src, hull, C, polys, F, m_of, sc, out)
    json.dump(out, open(os.path.join(design, 'verify_frames.json'), 'w', encoding='utf-8'), ensure_ascii=False, indent=1)
    n = sum(p['cells_yz'] for p in out['planes'])
    print(json.dumps(out['sheer'], ensure_ascii=False))
    print('planes', len(out['planes']), 'cells_yz', n, 'voxels', n * F['sided'])


# ───────────────────────── 畫圖 ─────────────────────────
def render(design, plan, src, hull, C, polys, F, m_of, sc, out):
    L = plan['lines']
    sh = D.Sheet(2440, 1560)
    planes = {(p['f'], p['plane']): p for p in out['planes']}

    def cells_of_plane(p):
        a = np.array(Image.open(os.path.join(design, p['stamp']['png'].split('/', 1)[1])).convert('RGBA'))
        H = a.shape[0]
        y0, z0 = [int(v) for v in p['stamp']['at'].split(',')][1:]
        res = []
        for r in range(H):
            for u in range(a.shape[1]):
                if a[r, u, 3] >= 128:
                    res.append((y0 + (H - 1 - r) - YC, z0 + u, tuple(int(v) for v in a[r, u, :3])))
        return res

    # 左上：船中 f+00 的雙肋（左半 plane A 含底肋、右半 plane B），疊 15 號外緣與內面讀數
    bp = D.Panel(sh, 80, 100, -72, 72, -6, 130, 5.0)
    bp.grid(minor=10, major=50, label_x=20, label_z=20)
    f0 = 0
    fl = [r for r in json.load(open(os.path.join(design, 'verify_lines.json'), encoding='utf-8'))['floors'] if r['f'] == f0][0]
    fa = np.array(Image.open(os.path.join(design, fl['stamp']['png'].split('/', 1)[1])).convert('RGBA'))
    fy0, fz0 = [int(v) for v in fl['stamp']['at'].split(',')][1:]
    for r in range(fa.shape[0]):
        for u in range(fa.shape[1]):
            dy = fy0 + (fa.shape[0] - 1 - r) - YC
            if fa[r, u, 3] >= 128 and dy <= 0:
                z = fz0 + u
                bp.poly([(dy - 0.5, z), (dy + 0.5, z), (dy + 0.5, z + 1), (dy - 0.5, z + 1)], fill=D.palette_rgb(141))
    for key, side in (((f0, 'A'), -1), ((f0, 'B'), 1)):
        for dy, z, rgb in cells_of_plane(planes[key]):
            if dy * side > 0:
                bp.poly([(dy - 0.5, z), (dy + 0.5, z), (dy + 0.5, z + 1), (dy - 0.5, z + 1)], fill=rgb)
    for key, side in (((f0, 'A'), -1), ((f0, 'B'), 1)):
        sec = hull.section(planes[key]['X'], 0, planes[key]['top'])
        bp.line([(side * h, z) for h, z in sec], D.RED, 2.0)
    hb15, z15 = hull.m15
    kt = L['d15_keel_top_ft']
    for h, z in src['d15']['inner_face_ft']:
        for sg in (-1, 1):
            bp.cross(sg * h * 3.048, 8 + (z - kt) * 3.048, color=(40, 110, 200), r=3)
    bp.line([(-2.5, 0), (2.5, 0), (2.5, 8), (-2.5, 8), (-2.5, 0)], D.INK, 1.2)
    for p in (planes[(f0, 'A')], planes[(f0, 'B')]):
        side = -1 if p['plane'] == 'A' else 1
        sec = hull.section(p['X'], 7.0, p['top'])
        seg = np.diff(sec, axis=0)
        arc = np.r_[0.0, np.cumsum(np.hypot(seg[:, 0], seg[:, 1]))]
        for name, a0, a1, col in p['members']:
            for a in (a0,):
                if a <= 0:
                    continue
                i = int(np.searchsorted(arc, a))
                h, z = sec[min(i, len(sec) - 1)]
                bp.line([(side * (h + 1.5), z), (side * (h - 4.5), z)], D.INK, 1.4)
            i = int(np.searchsorted(arc, (a0 + min(a1, arc[-1])) / 2))
            h, z = sec[min(i, len(sec) - 1)]
            # 標在船殼內側（往中線那邊），左半邊才不會被面板邊界切掉
            bp.label(side * h, z, name, dx=-side * 30, dy=0, size=12, anchor='rm' if side > 0 else 'lm', leader=False)
    bp.commit()
    sh.text(80, 24, '新圖紙 04　肋骨圖 v1（Framing）', 26, bold=True)
    sh.text(80, 62, '左上：船中 Ø 肋位的雙肋（左半＝plane A：底肋＋2nd／4th futtock＋long top timber；右半＝plane B：1st／3rd futtock＋short top timber）｜右上：肋骨 moulded 隨高度｜下：側面肋骨與舷頂 sheer', 15, color=D.CONSTR)
    sh.text(80 + 72 * 5, 100 + 136 * 5 + 30, '橫剖面　每格 5 px｜紅＝molded 線（肋骨外面）、藍十字＝15 號肋骨內面讀數、短橫線＝接頭', 13, anchor='ma', color=D.CONSTR)

    # 右上：moulded 隨高度（橫軸放大 60 px／格）
    ox, oy, kx, kz = 1000, 100, 60.0, 5.0
    d = sh.d
    S = D.SS
    for gx in range(0, 6):
        d.line([((ox + gx * kx) * S, oy * S), ((ox + gx * kx) * S, (oy + 136 * kz) * S)], fill=D.GRID5 if gx % 1 == 0 else D.GRID1, width=S)
        sh.text(ox + gx * kx, oy + 136 * kz + 8, '%d' % gx, 12, anchor='ma', color=D.CONSTR)
    for gz in range(0, 131, 10):
        d.line([(ox * S, (oy + (130 - gz) * kz) * S), ((ox + 5 * kx) * S, (oy + (130 - gz) * kz) * S)], fill=D.GRID1, width=S)
        sh.text(ox - 8, oy + (130 - gz) * kz - 7, 'Z %d' % gz, 12, anchor='ra', color=D.CONSTR)
    zz = np.arange(8, 128.1, 0.5)
    pts = [((ox + m_of(z) * kx) * S, (oy + (130 - z) * kz) * S) for z in zz]
    d.line(pts, fill=D.RED, width=3 * S)
    O = np.array(src['d15']['points_ft']) * 3.048
    for h, z in src['d15']['inner_face_ft']:
        P = np.array([h, z]) * 3.048
        dd = min(np.linalg.norm(P - (O[i] + max(0, min(1, np.dot(P - O[i], O[i + 1] - O[i]) / np.dot(O[i + 1] - O[i], O[i + 1] - O[i]))) * (O[i + 1] - O[i]))) for i in range(len(O) - 1))
        zc = 8 + (z - kt) * 3.048
        x, y = ox + dd * kx, oy + (130 - zc) * kz
        d.line([((x - 5) * S, y * S), ((x + 5) * S, y * S)], fill=(40, 110, 200), width=2 * S)
        d.line([(x * S, (y - 5) * S), (x * S, (y + 5) * S)], fill=(40, 110, 200), width=2 * S)
    sh.text(ox + 2.5 * kx, oy + 136 * kz + 30, 'moulded（格）　紅＝設計 m(z)、藍十字＝15 號（肋骨內面到外緣的垂直距離）；Z 66 以上為設計決定', 13, anchor='ma', color=D.CONSTR)

    # 右上旁：分段表
    tx, ty = 1400, 110
    sh.text(tx, ty, '分段（弧長從龍骨側面沿 molded 線量，格）', 16, bold=True)
    yy = ty + 32
    for plane, title in (('A', 'plane A（底肋那一片，x 欄 round(X)−1..+1）'), ('B', 'plane B（船頭側，x 欄 round(X)+2..+4）')):
        sh.text(tx, yy, title, 14, bold=True)
        yy += 24
        for name, a0, a1, col in F['members'][plane]:
            sh.d.rectangle([tx * S, (yy + 3) * S, (tx + 16) * S, (yy + 17) * S], fill=D.palette_rgb(col), outline=D.INK, width=S)
            sh.text(tx + 24, yy, '%s　%s–%s　色 %d' % (name, a0, '舷頂' if a1 > 999 else a1, col), 14)
            yy += 22
        yy += 10
    sh.text(tx, yy, '短於 %d 格的尾段併進上一段；|dy| ≤ %d 留給龍骨／keelson／deadwood／apron' % (F['min_piece_arc'], F['keep_clear_dy']), 13, color=D.CONSTR)
    yy += 22
    sh.text(tx, yy, '舷頂 sheer：二次擬合 11 號 1、2、5–9 站頂＋15 號船中頂（殘差 ≤ %.1f 格）' % max(abs(v) for v in out['sheer']['residuals'].values()), 13, color=D.CONSTR)

    # 下：側面
    pp = D.Panel(sh, 80, 1000, 110, 710, -10, 136, 3.4)
    pp.grid(label_x=50, label_z=20)
    D.draw_parts_v2(pp, plan, C, polys, dashed=False)
    for p in out['planes']:
        x0, x1 = p['x_cells']
        a = np.array(Image.open(os.path.join(design, p['stamp']['png'].split('/', 1)[1])).convert('RGBA'))
        z0 = int(p['stamp']['at'].split(',')[2])
        cols = {}
        for u in range(a.shape[1]):
            colmask = a[:, u, 3] >= 128
            if colmask.any():
                cols[z0 + u] = tuple(int(v) for v in a[np.argmax(colmask), u, :3])
        for z, rgb in cols.items():
            pp.poly([(x0, z), (x1 + 1, z), (x1 + 1, z + 1), (x0, z + 1)], fill=rgb)
    for r in json.load(open(os.path.join(design, 'verify_lines.json'), encoding='utf-8'))['floors']:
        x0, x1 = r['x_cells']
        pp.poly([(x0, 8), (x1 + 1, 8), (x1 + 1, r['z_max'] + 1), (x0, r['z_max'] + 1)], fill=D.palette_rgb(141))
    xs = np.arange(180, 620, 1.0)
    pp.line([(x, float(np.polyval(sc, x))) for x in xs], D.RED, 2.0)
    for lab, x, z in F['sheer_points']:
        pp.cross(x, z, color=(40, 110, 200), r=5)
    pp.commit()
    sh.text(80 + 300 * 3.4, 1000 + 146 * 3.4 + 26, '側面　肋位 f%+d…f%+d、每站雙肋兩片（共 %d 片）｜紅＝舷頂 sheer、藍十字＝原圖站頂讀數' % (
        F['f_from'], F['f_to'], len(out['planes'])), 13, anchor='ma', color=D.CONSTR)
    # 圖框（D.title_block 的日期與參考那一行是 01／02 號圖的，這張自己寫）
    x, y, w = 1300, 860, 990
    sh.d.rectangle([x * D.SS, y * D.SS, (x + w) * D.SS, (y + 88) * D.SS], outline=D.INK, width=2 * D.SS)
    sh.text(x + 12, y + 10, F['title'], 19, bold=True)
    sh.text(x + 12, y + 38, '肋骨圖　雙肋 sided 3＋3 格、moulded 3.6→1.8 格、肋位 f%+d…f%+d' % (F['f_from'], F['f_to']), 14)
    sh.text(x + 12, y + 60, '設計：%s　%s　%s　｜船殼＝新圖紙 03；厚度＝15 號讀數；分段參考 18 世紀雙肋通例（見 plan.json framing.provenance）' % (plan['author'], F['date'], F['task']), 13, color=D.CONSTR)
    sh.save(os.path.join(design, 'sheet04_frames_v1.png'))


if __name__ == '__main__':
    main()
