# 康塞普西翁號 步驟 16（TASK-0969；Tim 2026-10-27「希望可以參考模型 圖紙 船身做出一些裝飾 曲線」）：裝飾 —— 側廊第二層、側廊底下的金托架、船尾走廊的金托架、鏡板窗之間的金壁柱與窗楣、船頭彎的 head rail
#   新寫（框架照 draft_deco.py：組裝件扣掉本件當成船、outer／aft 兩張表、both() 照 |dy| 兩舷一起放）；wale 的曲線與砲門金框是船殼的漆，在 draft_ports.py（paint.wales.sheer、paint.wreath）
#   輸入：plan.json ornament（＋stern_deco.quarter_gallery／balcony、espolon、figurehead、stern）＋ 組裝件現在的格子（CLI 匯出，扣掉 -ornament 自己）
#   輸出：masks/deco/ornament.vox.txt（世界座標、at 0,0,0）、verify_ornament.json、sheet07_ornament_v1.png
#   用法：python -I -X utf8 draft_ornament.py <design>
#   · 只放進空格：組裝件已經有的格不蓋（撞到幾格照實數 blocked）；擋到砲門開口前面的格照實數（ports_covered）
import sys, os, json, math, hashlib
import numpy as np
from PIL import Image, ImageDraw

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), 'tools'))
import lines as HL
import layout as LY
from draft_lines import font, palette_rgb
from draft_ports import stern_windows
from wio import export_list

GOLD, GLASS, WOOD, TRIM, BLUE = 248, 87, 141, 136, 6
HULL = 'apex-two-galeon-01m'


def main():
    sys.stdout.reconfigure(encoding='utf-8')
    design = sys.argv[1]
    plan = HL.load_plan(design)
    L = HL.Lines(plan)
    YC = L.YC
    WORKS = os.path.dirname(os.path.dirname(os.path.abspath(design)))
    A = export_list(HULL + '-assembly', None, links=None)
    if os.path.exists(os.path.join(WORKS, HULL + '-ornament', 'work.json')):     # 已經落過一次 ⇒ 扣掉自己（重跑才會逐位元組相同）
        own = set(map(tuple, export_list(HULL + '-ornament', None)[:, :3].tolist()))
        A = A[np.array([tuple(r) not in own for r in A[:, :3].tolist()], bool)]
    occ = set(map(tuple, A[:, :3].tolist()))
    aft, outer = {}, {}
    for x, y, z in A[:, :3].tolist():
        if x < 220 and x < aft.get((y, z), 10 ** 6):
            aft[(y, z)] = x
        dy = abs(y - YC)
        if dy > outer.get((x, z), -1):
            outer[(x, z)] = dy
    O = plan['ornament']
    cells, blocked = {}, {}

    def both(part, x, dy, z, c):
        for y in {YC + dy, YC - dy}:
            k = (int(x), int(y), int(z))
            if k in occ:
                blocked[part] = blocked.get(part, 0) + 1
            elif k not in cells:
                cells[k] = (c, part)

    # ── 側廊第二層（疊在第一層的紅頂上；開間、窗、壁柱照第一層的寫法，外伸少一格） ──
    G = O['gallery2']
    bay = lambda x: (x - G['x0']) // 8
    fy = {}
    for x in range(G['x0'], G['x1'] + 1):
        vs = [outer[(x, z)] for z in range(G['z0'] + 4, G['z1'] + 1) if (x, z) in outer]
        if vs:
            fy[bay(x)] = max(fy.get(bay(x), -1), max(vs) + G['out'])
    w0, w1 = G['win']
    for x in range(G['x0'], G['x1'] + 1):
        if bay(x) not in fy:
            continue
        F, bx = fy[bay(x)], (x - G['x0']) % 8
        for z in range(G['z0'], G['z1'] + G['roof_h'] + 1):
            hz = min(z, G['z1'])
            o = outer.get((x, hz))
            if o is None:
                continue
            ext = F - o
            if z <= G['z0'] + 3:                                          # 底下一節往外收（同第一層）
                out = max(1, round(ext * (z - G['z0'] + 1) / 4.0))
            elif z > G['z1']:                                             # 頂：每層往裡收 1、兩頭各收 2 ⇒ 拱
                k = z - G['z1']
                out, inset = max(0, ext - k), 2 * k
                if x < G['x0'] + inset or x > G['x1'] - inset or out == 0:
                    continue
            else:
                out = ext
            win = w0 <= z <= w1 and (bx in (2, 3, 4, 5) if z < w1 else bx in (3, 4))
            for d in range(1, out + 1):
                face = d == out
                c = BLUE
                if z > G['z1']:
                    c = GOLD if z == G['z1'] + 1 else G['roof']
                elif z in (G['z0'] + 3, G['z1']):
                    c = GOLD
                elif face and win:
                    c = GLASS                                             # 畫上去的窗（同第一層 v1；後面是側廊的實心）
                elif face and 1 <= bx <= 6 and w0 - 1 <= z <= w1 + 1:
                    c = GOLD                                              # 窗框（拱的兩肩也是金）
                elif face and bx in (0, 7):
                    c = TRIM
                both('gallery2', x, o + d, z, c)
    # ── 第一層側廊底下的金托架：每個開間兩端；上面頂到側廊的面、往下收成 0 ──
    Q = plan['stern_deco']['quarter_gallery']
    C = O['corbels']
    nb = (Q['x1'] - Q['x0'] + 1) // 8
    cols = [Q['x0'] + i for i in range(C['w'])] + [Q['x1'] - i for i in range(C['w'])]
    for k in range(1, nb):
        cols += [Q['x0'] + 8 * k - 1 - i for i in range(C['w'] // 2)] + [Q['x0'] + 8 * k + i for i in range(C['w'] - C['w'] // 2)]
    for x in sorted(set(cols)):
        face = max([outer[(x, z)] for z in range(Q['z0'] + 5, Q['z1'] + 1) if (x, z) in outer] or [0])
        for z in range(Q['z0'] + 3, Q['z0'] - C['len'] - 1, -1):
            o = outer.get((x, z)) if z < Q['z0'] else None
            if z >= Q['z0']:                                              # 側廊底下往外收的那一節：從船殼量（側廊的格會被 both 擋掉 ⇒ 只填外面那塊三角）
                o = min(outer.get((x, zz), 999) for zz in range(Q['z0'] - 1, Q['z0'] - 3, -1))
                reach = face - o
            else:
                if o is None:
                    continue
                reach = int(round((face - o) * (1 - (Q['z0'] - z) / float(C['len'] + 1)) ** 1.3))
            for d in range(1, reach + 1):
                both('corbel', x, o + d, z, GOLD if d >= reach - 1 else WOOD)   # 外面兩格金（看得到的那一面）
    # ── 船尾走廊底下的金托架（原本木斜撐之間） ──
    bal, BC = plan['stern_deco']['balcony'], O['balcony_corbels']
    zf, dep = bal['floor_z'], bal['depth']
    for dy in range(BC['dy_off'], bal['half'], BC['dy_every']):
        for ddy in (dy, dy + 1):
            for j in range(BC['len']):
                z = zf - 1 - j
                fz = aft.get((YC + ddy, z))
                if fz is None:
                    continue
                reach = int(round(dep * (1 - j / float(BC['len'])) ** 1.2))
                for x in range(fz - reach, fz):
                    both('balcony_corbel', x, ddy, z, GOLD if x == fz - reach else WOOD)
    # ── 鏡板的金壁柱與窗楣 ──
    wins = [w for w in stern_windows(plan, YC) if w['kind'] == 'window']
    rows = {}
    for w in wins:
        rows.setdefault(w['deck'], []).append(w)
    for dk, ws in rows.items():
        ws.sort(key=lambda w: w['y0'])
        z0, z1 = ws[0]['z0'], ws[0]['z1']
        ys = {ws[0]['y0'] - 2, ws[-1]['y1'] + 2}
        for a, b in zip(ws, ws[1:]):
            m = (a['y1'] + b['y0']) / 2.0
            ys |= {int(math.floor(m)), int(math.ceil(m))}                 # 縫是偶數格 ⇒ 中間兩格（兩舷才對稱）
        for y in ys:
            for z in range(z0 - 1, z1 + 2):
                fz = aft.get((y, z))
                if fz is not None:
                    both('pilaster', fz - 1, abs(y - YC), z, GOLD)
        for w in ws:
            for y in range(w['y0'] - 1, w['y1'] + 2):
                fz = aft.get((y, z1 + 2))
                if fz is not None:
                    both('pilaster', fz - 1, abs(y - YC), z1 + 2, GOLD)
    # ── 船頭的 head rail：船頭側面往前往下彎、接到喙上的欄杆頂；喙上的 head timber ──
    E, F_, H = plan['espolon'], plan['figurehead'], O['head_rails']
    xs0 = int(math.floor(float(L.x_stem(80)) + 0.5)) - 1
    zt = E['deck_top_z']
    wpar = lambda x: E['half_at_tip'] + (E['half_at_stem'] - E['half_at_tip']) * (1 - (x - xs0) / float(E['len_beyond_stem'])) ** E['taper_pow']
    rail_at = []
    for r in H['rails']:
        p0, p2 = (H['x_h'], r['z_h']), (H['x_e'], r['z_e'])
        p1 = ((p0[0] + p2[0]) / 2.0, min(p0[1], p2[1]) - H['sag'])
        dy0 = outer.get((H['x_h'], r['z_h']), 0) + 1
        dye = int(math.floor(wpar(H['x_e']) + 0.5))
        at = {}
        for i in range(0, 801):
            t = i / 800.0
            x = (1 - t) ** 2 * p0[0] + 2 * t * (1 - t) * p1[0] + t * t * p2[0]
            z = (1 - t) ** 2 * p0[1] + 2 * t * (1 - t) * p1[1] + t * t * p2[1]
            xi, zi = int(math.floor(x + 0.5)), max(zt + 1, int(math.floor(z + 0.5)))
            dy = int(math.floor(dy0 + (dye - dy0) * t + 0.5))
            dy = max([dy] + [outer[(xi, zz)] + 1 for zz in range(zi, zi + H['thick']) if (xi, zz) in outer])
            at.setdefault(xi, []).append((zi, dy))
        for xi, v in at.items():                                          # 同一柱取的那幾個 z、dy 都放 ⇒ 斜的地方面相接
            for zi, dy in v:
                for zz in range(zi, zi + H['thick']):
                    both('head_rail', xi, dy, zz, GOLD if zz == zi + H['thick'] - 1 else WOOD)
        rail_at.append(at)
    up = rail_at[0]
    for x in H['timbers']:                                                # head timber：喙的甲板直立撐到上面那條（只放空格 ⇒ 下面那條、喙的欄杆照舊）
        if x not in up:
            continue
        zu, dy = min(up[x])
        for z in range(zt + 1, zu):
            both('head_timber', x, dy, z, GOLD)

    # ── 讀數 ──
    ports = LY.ports(plan)
    cov = 0
    for (x, y, z), (c, part) in cells.items():
        if any(p['x0'] <= x <= p['x1'] and p['z0'] <= z <= p['z1'] and abs(y - YC) >= 6 for p in ports):
            cov += 1
    by = {}
    for (c, part) in cells.values():
        by[part] = by.get(part, 0) + 1
    keys = set(cells)
    mirror = sum(1 for (x, y, z) in keys if (x, 2 * YC - y, z) not in keys or cells[(x, 2 * YC - y, z)][0] != cells[(x, y, z)][0])
    R = {'cells': len(cells), 'by_part': by, 'blocked': blocked, 'ports_covered': cov, 'mirror_diff': mirror,
         'colors': {int(c): n for c, n in sorted({c: sum(1 for v in cells.values() if v[0] == c) for c in {v[0] for v in cells.values()}}.items())}}
    od = os.path.join(design, 'masks', 'deco')
    os.makedirs(od, exist_ok=True)
    path = os.path.join(od, 'ornament.vox.txt')
    with open(path, 'w', encoding='utf-8', newline='\n') as f:
        f.write('# 康塞普西翁號 裝飾（步驟 16：側廊第二層、托架、壁柱與窗楣、head rail；世界座標，at 0,0,0）\n')
        for k in sorted(cells):
            f.write('%d,%d,%d,%d\n' % (k[0], k[1], k[2], cells[k][0]))
    R['list'] = [len(cells), hashlib.sha256(open(path, 'rb').read()).hexdigest()]
    # 圖紙：船尾四分之一（右舷側面 x 140–240）、船尾正面、船頭側面（x 580–660）；組裝件灰、裝飾照色
    sc = 4
    views = [('船尾右舷側面 x 140–240、z 100–170', 140, 240, 100, 170), ('船頭右舷側面 x 575–665、z 75–145', 575, 665, 75, 145)]
    zl, zh = 100, 170                                                   # 船尾正面
    Wp = sum((b - a + 1) * sc + 40 for _, a, b, _, _ in views) + (2 * 60 + 1) * sc + 80
    Hp = (zh - zl + 1) * sc + 120
    im = Image.new('RGB', (Wp, Hp), (250, 248, 240))
    d = ImageDraw.Draw(im)
    d.text((20, 10), '康塞普西翁號 圖紙 07：裝飾（步驟 16）　%d 格；撞到 %s；擋砲門 %d；鏡像差 %d' % (len(cells), json.dumps(blocked, ensure_ascii=False), cov, mirror), fill=(0, 0, 0), font=font(16))
    Acol = {tuple(r[:3]): int(r[3]) for r in A.tolist()}
    allc = dict(Acol)
    for k, (c, part) in cells.items():
        allc[k] = c
    side = {}
    for (x, y, z), c in allc.items():
        if y >= YC and y > side.get((x, z), (-1, 0))[0]:
            side[(x, z)] = (y, c)
    back = {}
    for (x, y, z), c in allc.items():
        if x < back.get((y, z), (10 ** 6, 0))[0]:
            back[(y, z)] = (x, c)
    ox, oy = 20, 50
    for title, a, b, vl, vh in views:
        d.text((ox, oy - 18), title, fill=(40, 40, 40), font=font(13))
        for x in range(a, b + 1):
            for z in range(vl, vh + 1):
                v = side.get((x, z))
                if v:
                    k = (x, v[0], z)
                    col = palette_rgb(v[1]) if k in cells else tuple(int(0.55 * q + 0.45 * 200) for q in palette_rgb(v[1]))
                    X, Y = ox + (x - a) * sc, oy + (vh - z) * sc
                    d.rectangle([X, Y, X + sc - 1, Y + sc - 1], fill=col)
        ox += (b - a + 1) * sc + 40
    d.text((ox, oy - 18), '船尾正面（從船尾看）', fill=(40, 40, 40), font=font(13))
    for y in range(YC - 60, YC + 61):
        for z in range(zl, zh + 1):
            v = back.get((y, z))
            if v:
                k = (v[0], y, z)
                col = palette_rgb(v[1]) if k in cells else tuple(int(0.55 * q + 0.45 * 200) for q in palette_rgb(v[1]))
                X, Y = ox + (y - YC + 60) * sc, oy + (zh - z) * sc
                d.rectangle([X, Y, X + sc - 1, Y + sc - 1], fill=col)
    im.save(os.path.join(design, 'sheet07_ornament_v1.png'))
    with open(os.path.join(design, 'verify_ornament.json'), 'w', encoding='utf-8', newline='\n') as f:
        json.dump(R, f, ensure_ascii=False, indent=1)
    print(json.dumps(R, ensure_ascii=False))


if __name__ == '__main__':
    main()
