# 蘇士奎哈納號（crest-001，TASK-0697）：本檔抄自光榮號 kaguya-gloire-01m/design/draft_decks.py（kaguya）—— 下面註解裡的「蘇士奎哈納號」原文是光榮號，改過的地方另外註明
# 蘇士奎哈納號 階段四（TASK-0609）：甲板（faux-pont、兩層砲甲板、上甲板）、艙口、梯子、桅孔、煙囪孔（遊戲用的大致構造）
#   抄自三叉戟號 gura-tridente-01m/design/draft_decks.py（gura，TASK-0557）；改：沒有 poop、faux-pont 只鋪前後兩段（中間是機艙）、煙囪孔
#   輸入：plan.json（decks、decks_build、masts）＋ 船殼（draft_lines.hull_volume ＝ 作品；艙裡 ＝ 外形實心扣掉 4 格牆）
#   輸出：masks/decks/<層>.vox.txt（甲板子作品，世界座標、at 0,0,0）、masks/ladders/<上面那層>.vox.txt ＋ ladder_points.json（梯子子作品的固定點）、
#         verify_decks.json、sheet04_decks_v1.png
#   用法：python -I -X utf8 draft_decks.py <design> [--probe drop_ladder=<梯名>]（反向對照：少一座梯子，梯子點讀數要少那一座；⛔ 不寫檔）
import sys, os, json, math, hashlib
import numpy as np
from PIL import Image, ImageDraw

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import hull_lines as HL
import layout as LY
from draft_lines import hull_volume, shell_colors, font, palette_rgb


def main():
    sys.stdout.reconfigure(encoding='utf-8')
    design = sys.argv[1]
    probe = [a.split('=', 1)[1] for a in sys.argv[2:] if a.startswith('--probe')]
    plan = HL.load_plan(design)
    L = HL.Lines(plan)
    YC = L.YC
    x0, ylo, S, dist = hull_volume(L, plan)
    wall, col, _armor = shell_colors(plan, S, dist, x0, ylo)
    inside = S & ~wall
    nx, ny, nz = S.shape
    X = np.arange(nx) + x0
    Y = np.arange(ny) + ylo
    DY = Y - YC
    B = plan['decks_build']
    rows = {r['key']: r for r in plan['decks']['rows']}
    zdeck = {k: LY.deck_z(plan, k, X).astype(int) for k in rows}

    # ── 開口：艙口、梯子口、桅孔（每層各自） ──
    hole = {k: np.zeros((nx, ny), bool) for k in rows}                 # (x, y) 平面上的開口；甲板板與橫樑都不放
    coam = {k: np.zeros((nx, ny), bool) for k in rows}                 # 圍欄（甲板面上 h 格）
    for h in B['hatches']:
        m = (X[:, None] >= h['x0']) & (X[:, None] <= h['x1']) & (np.abs(DY)[None, :] <= h['half'])
        ring = (X[:, None] >= h['x0'] - 1) & (X[:, None] <= h['x1'] + 1) & (np.abs(DY)[None, :] <= h['half'] + 1) & ~m
        for k in B['hatch_decks']:
            hole[k] |= m
            coam[k] |= ring
    LD = B['ladders']
    ladders = []
    for pr in LD['pairs']:
        for name, xs in pr['at']:
            ladders.append({'name': '%s-%s' % (name, pr['up']), 'lo': pr['lo'], 'up': pr['up'], 'xs': xs, 'dir': 1, 'yc': YC})
    if probe:
        drop = probe[0].split('=')[1]
        ladders = [l for l in ladders if l['name'] != drop]
    th = LD['tread_half']
    for ld in ladders:
        s = ld['dir']
        xa, xb = sorted((ld['xs'] + s * 4, ld['xs'] + s * 16))
        m = (X[:, None] >= xa) & (X[:, None] <= xb) & (np.abs(Y - ld['yc'])[None, :] <= th + 2)
        hole[ld['up']] |= m
        side = (X[:, None] >= xa) & (X[:, None] <= xb) & (np.abs(Y - ld['yc'])[None, :] == th + 3)
        low_end = (X[:, None] == ld['xs'] + s * 3) & (np.abs(Y - ld['yc'])[None, :] <= th + 3)
        coam[ld['up']] |= side | low_end
    for k in rows:
        for m in plan['masts']['rows']:
            zz = zdeck[k]
            hit = LY.mast_hit(plan, m['key'], X[:, None], Y[None, :], zz[:, None])
            if m['key'] == 'mizzen' and k == 'orlop':
                continue                                           # 後桅腳立在 faux-pont 上（不開孔）
            hole[k] |= hit
        for f in plan['funnels']['rows']:
            if k in B['funnel_decks']:
                hole[k] |= LY.funnel_hit(plan, f['key'], X[:, None], Y[None, :])
    for k in rows:
        coam[k] &= ~hole[k]

    # ── 甲板：甲板板（那一層的艙裡）＋橫樑＋圍欄 ──
    decks = {}
    for k, r in rows.items():
        cell = np.zeros(S.shape, np.uint8)
        plank_c = B['plank']['weather'] if k in ('gun',) else B['plank']['gun']   # 蘇士奎哈納號改：露天甲板 ＝ gun deck   # 蘇士奎哈納號：艉樓、艏樓也是露天甲板
        span = (X >= r.get('x_from', -1e9)) & (X <= r.get('x_to', 1e9))
        for a, b in r.get('skip', []):
            span &= ~((X >= a) & (X <= b))
        bm = B['beam']
        for xi in range(nx):
            if not span[xi]:
                continue
            z = zdeck[k][xi]
            row = inside[xi, :, z] & ~hole[k][xi]
            cell[xi, row, z] = plank_c
            sg = B.get('shaft_gap')   # 蘇士奎哈納號加的：明輪軸那一段不放橫樑
            if (X[xi] % bm['every']) < bm['w'] and not (sg and k == 'gun' and sg['x0'] <= X[xi] <= sg['x1']):
                for dz in range(1, bm['depth'] + 1):
                    rb = inside[xi, :, z - dz] & ~hole[k][xi]
                    cell[xi, rb & (cell[xi, :, z - dz] == 0), z - dz] = bm['color']
            for dz in range(1, B['coaming']['h'] + 1):
                rc = inside[xi, :, z + dz] & coam[k][xi]
                cell[xi, rc, z + dz] = B['coaming']['color']
        decks[k] = cell
    # ── 梯子：踏板每 rise 格一階、每階往前 run 格；兩側 stringer（4 格高，接到上下兩層甲板）──
    LC = LD['color']
    lad = {}
    pts = {}
    for ld in ladders:
        up, lo = ld['up'], ld['lo']
        cell = lad.setdefault(up, np.zeros(S.shape, np.uint8))
        s = ld['dir']
        xs = ld['xs']
        xi0 = xs - x0
        zl = int(zdeck[lo][xi0])
        zu_head = int(zdeck[up][xs + s * 18 - x0])
        n = int((zu_head - zl - 2) // LD['rise'])
        yc_i = ld['yc'] - ylo
        for kk in range(0, n + 2):
            xa = xs + s * LD['run'] * kk
            xr = sorted((xa, xa + s * (LD['run'] - 1)))
            zt = zl + LD['rise'] * kk
            for xx in range(xr[0], xr[1] + 1):
                if 1 <= kk <= n:
                    cell[xx - x0, yc_i - th:yc_i + th + 1, zt] = LC
                zlo, zhi = (zl + 1, zl + 3) if kk == 0 else (zt - 3, min(zt, zu_head) if kk <= n else zu_head)
                if kk == n + 1:
                    zlo, zhi = zl + LD['rise'] * n - 3, zu_head
                for z in range(zlo, zhi + 1):
                    for yy in (yc_i - th - 1, yc_i + th + 1):
                        cell[xx - x0, yy, z] = LC
        P = {'foot': [xs - s, ld['yc'], zl + 1], 'lo': [xs + s * LD['run'], ld['yc'], zl + LD['rise'] + 1],
             'hi': [xs + s * LD['run'] * n, ld['yc'], zl + LD['rise'] * n + 1], 'head': [xs + s * 18, ld['yc'], zu_head + 1]}
        pts[ld['name']] = {'up': up, 'lo': lo, 'points': P, 'steps': n}
    anyd = np.zeros(S.shape, bool)
    for c in decks.values():
        anyd |= c > 0
    for k in lad:
        lad[k][anyd] = 0                                           # 甲板優先：stringer 碰到甲板板、艙壁那幾格不放

    # ── 封閉空腔：船殼＋甲板＋梯子組起來被封死的空氣 ⇒ 填進高度最近的那一層甲板（橫樑色）。
    #    來源：甲板舷弧取整，船尾最後一欄的甲板板比旁邊高一格、底下夾著橫樑與船尾牆（第一版量到 2 個、179 格）
    from scipy import ndimage
    uni = wall.copy()
    for c in list(decks.values()) + list(lad.values()):
        uni |= c > 0
    cav = ndimage.binary_fill_holes(uni) & ~uni
    labc, ncav = ndimage.label(cav)
    filled = []
    for i in range(1, ncav + 1):
        idx = np.argwhere(labc == i)
        xm, zm = int(np.median(idx[:, 0])), float(np.median(idx[:, 2]))
        k = min(rows, key=lambda kk: abs(zdeck[kk][xm] - zm))
        decks[k][labc == i] = B['beam']['color']
        filled.append({'deck': k, 'cells': int(len(idx)), 'x': [int(idx[:, 0].min() + x0), int(idx[:, 0].max() + x0)], 'z': [int(idx[:, 2].min()), int(idx[:, 2].max())]})
    # ── 讀數 ──
    R = {'decks': {}, 'ladders': {}, 'problems': []}
    solid_hull = wall.copy()
    allc = np.zeros(S.shape, np.int16)
    for k, c in decks.items():
        m = c > 0
        R['decks'][k] = {'cells': int(m.sum()), 'hull_overlap': int((m & solid_hull).sum()), 'outside_hull': int((m & ~S).sum()),
                         'colors': {int(a): int(b) for a, b in zip(*np.unique(c[m], return_counts=True))}, 'mirror_diff': int((m != m[:, ::-1, :]).sum())}
        allc += m
    for k, c in lad.items():
        m = c > 0
        R['ladders'][k] = {'cells': int(m.sum()), 'hull_overlap': int((m & solid_hull).sum()), 'deck_overlap': int(sum(int((m & (d > 0)).sum()) for d in decks.values())),
                           'mirror_diff': int((m != m[:, ::-1, :]).sum())}
        allc += m
    R['overlap_between_parts'] = int((allc > 1).sum())
    # 梯子點：那一格是空的、腳下那一格是實心（甲板板或踏板）、頭頂 14 格空
    every = np.zeros(S.shape, bool)
    every |= wall
    for c in list(decks.values()) + list(lad.values()):
        every |= c > 0
    bad = []
    for nm, v in pts.items():
        for pk, (px, py, pz) in v['points'].items():
            xi_, yi_ = px - x0, py - ylo
            ok_air = not every[xi_, yi_, pz]
            ok_floor = bool(every[xi_, yi_, pz - 1])
            head = int(every[xi_, yi_, pz:pz + 14].sum())
            if not (ok_air and ok_floor) or head:
                bad.append((nm, pk, ok_air, ok_floor, head))
    R['ladder_points'] = pts
    R['ladder_point_problems'] = bad
    R['ladder_count'] = len(pts)
    R['holes'] = {k: int(hole[k].sum()) for k in rows}
    R['cavities_filled'] = filled
    if probe:
        print(json.dumps({'probe': probe[0], 'ladder_count': len(pts), 'names': sorted(pts)}, ensure_ascii=False))
        return
    # ── 寫檔 ──
    def dump(path, c, head):
        idx = np.argwhere(c > 0)
        with open(path, 'w', encoding='utf-8', newline='\n') as f:
            f.write(head)
            for xi_, yi_, z in idx:
                f.write('%d,%d,%d,%d\n' % (xi_ + x0, yi_ + ylo, z, c[xi_, yi_, z]))
        return [int(len(idx)), hashlib.sha256(open(path, 'rb').read()).hexdigest()]
    od, ol = os.path.join(design, 'masks', 'decks'), os.path.join(design, 'masks', 'ladders')
    os.makedirs(od, exist_ok=True)
    os.makedirs(ol, exist_ok=True)
    R['lists'] = {}
    for k, c in decks.items():
        R['lists']['deck-' + k] = dump(os.path.join(od, k + '.vox.txt'), c, '# 蘇士奎哈納號 甲板 %s（draft_decks.py；世界座標，at 0,0,0）\n' % k)
    for k, c in lad.items():
        R['lists']['ladders-' + k] = dump(os.path.join(ol, k + '.vox.txt'), c, '# 蘇士奎哈納號 梯子（上到 %s；世界座標，at 0,0,0）\n' % k)
    with open(os.path.join(design, 'ladder_points.json'), 'w', encoding='utf-8', newline='\n') as f:
        json.dump(pts, f, ensure_ascii=False, indent=1)
    # 圖：每層甲板從上往下看（開口、圍欄、桅孔）＋中線縱剖面
    sc = 1.0
    keys = list(rows)
    Hp = 80 + len(keys) * (ny + 30) + nz + 60
    im = Image.new('RGB', (int(nx * sc) + 120, Hp), (250, 248, 240))
    d = ImageDraw.Draw(im)
    d.text((40, 16), '蘇士奎哈納號 新圖紙 04：甲板、艙口、梯子、桅孔、煙囪孔　v1（每層從上往下看；最下面 ＝ 中線縱剖面）', fill=(0, 0, 0), font=font(18))
    for i, k in enumerate(keys):
        oy = 60 + i * (ny + 30)
        d.text((40, oy - 2), '%s z %d' % (rows[k]['name'].split('（')[0], rows[k]['z']), fill=(0, 0, 0), font=font(12))
        top = decks[k].max(axis=2)
        if k in lad:
            top = np.where(lad[k].max(axis=2) > 0, 200, top)
        for xi_ in range(nx):
            for yi_ in range(ny):
                v = top[xi_, yi_]
                if v:
                    d.point((100 + xi_, oy + yi_), fill=palette_rgb(int(v)) if v != 200 else (0, 90, 200))
    oy = 60 + len(keys) * (ny + 30)
    yc_i = YC - ylo
    for xi_ in range(nx):
        for z in range(nz):
            c = 0
            if wall[xi_, yc_i, z]:
                c = col[xi_, yc_i, z]
            for dd in list(decks.values()) + list(lad.values()):
                if dd[xi_, yc_i, z]:
                    c = dd[xi_, yc_i, z]
            if c:
                d.point((100 + xi_, oy + nz - z), fill=palette_rgb(int(c)))
    im.save(os.path.join(design, 'sheet04_decks_v1.png'))
    with open(os.path.join(design, 'verify_decks.json'), 'w', encoding='utf-8', newline='\n') as f:
        json.dump(R, f, ensure_ascii=False, indent=1)
    print(json.dumps({k: v for k, v in R.items() if k not in ('ladder_points',)}, ensure_ascii=False))


if __name__ == '__main__':
    main()
