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
    occ_arg = next((a.split('=', 1)[1] for a in sys.argv[2:] if a.startswith('--occ=')), None)
    if occ_arg:       # 步驟 17：設計還沒落格時拿本機清單當組裝件（同 draft_deco.py --occ）；⛔ 正式產清單一律從組裝件讀
        A = np.concatenate([np.loadtxt(p_, delimiter=',', comments='#', dtype=np.int32, ndmin=2, encoding='utf-8')[:, :4] for p_ in occ_arg.split(';')])
    else:
        A = export_list(HULL + '-assembly', None, links=None)
    if not occ_arg and os.path.exists(os.path.join(WORKS, HULL + '-ornament', 'work.json')):     # 已經落過一次 ⇒ 扣掉自己（重跑才會逐位元組相同）
        own = set(map(tuple, export_list(HULL + '-ornament', None)[:, :3].tolist()))
        for nm in ('espolon', 'figurehead', 'stern-deco', 'hackebort'):    # 步驟 17：自己的格也屬於別的件（之前重疊了）⇒ 不扣 ⇒ 這次會讓開（v1 一扣就把重疊的格當成空的、永遠重疊下去）
            p_ = os.path.join(design, 'masks', 'deco', nm + '.vox.txt')
            if os.path.exists(p_):
                own -= set(map(tuple, np.loadtxt(p_, delimiter=',', comments='#', dtype=np.int64, ndmin=2, encoding='utf-8')[:, :3].tolist()))
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
    Hh = np.loadtxt(occ_arg.split(';')[0], delimiter=',', comments='#', dtype=np.int32, ndmin=2, encoding='utf-8') if occ_arg else export_list(HULL, None)
    outer_h = {}                                                         # 步驟 17：只算船殼的最外面（cheek、寬帶貼船殼用）—— 照組裝件算會貼到錨架外面（離船殼 50 格浮空）
    for x, y, z in Hh[:, :3].tolist():
        dy = abs(y - YC)
        if dy > outer_h.get((x, z), -1):
            outer_h[(x, z)] = dy
    cells, blocked = {}, {}

    def both(part, x, dy, z, c):
        for y in {YC + dy, YC - dy}:
            k = (int(x), int(y), int(z))
            if k in occ:
                blocked[part] = blocked.get(part, 0) + 1
            elif k not in cells:
                cells[k] = (c, part)

    # 步驟 17：側廊第二層、側廊底下與船尾走廊底下的托架拿掉 —— 兩層 stern walk（draft_deco.py stern_deco.walks）取代，托架在走廊底下
    # ── 鏡板的金壁柱與窗楣 ──
    wins = [w for w in stern_windows(plan, YC) if w['kind'] in ('window', 'door')]     # 步驟 17：門也算一格（壁柱照排在門的兩旁），門頂不放窗楣
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
            if w['kind'] == 'door':
                continue
            for y in range(w['y0'] - 1, w['y1'] + 2):
                fz = aft.get((y, z1 + 2))
                if fz is not None:
                    both('pilaster', fz - 1, abs(y - YC), z1 + 2, GOLD)
    # ── 步驟 17：船頭的 head rail（San Felipe 模型：每舷三條，從船頭側面往前往下彎、再往上接到船首像後面；三條之間一排直立的金格柵）＋ 船頭兩側的 cheek 金線 ──
    E, F_, H = plan['espolon'], plan['figurehead'], O['head_rails']
    xs0 = int(math.floor(float(L.x_stem(80)) + 0.5)) - 1
    zt = E['deck_top_z']
    wpar = lambda x: E['half_at_tip'] + (E['half_at_stem'] - E['half_at_tip']) * (1 - (x - xs0) / float(E['len_beyond_stem'])) ** E['taper_pow']
    rail_at = []
    for r in H['rails']:
        xh, xl, xe = r['x_h'], r['x_l'], H['x_e']
        dy0 = outer.get((xh, r['z_h']), 0) + 1
        dye = int(math.floor(wpar(xe) + 0.5))
        at = {}
        for i in range(0, 1201):                                          # 兩段拋物線：起點 ⇒ 最低點（x_l, z_l，斜率 0）⇒ 船首像後面 ⇒ U 形
            t = i / 1200.0
            x = xh + (xe - xh) * t
            if x <= xl:
                z = r['z_l'] + (r['z_h'] - r['z_l']) * ((xl - x) / float(xl - xh)) ** 2
            else:
                z = r['z_l'] + (r['z_e'] - r['z_l']) * ((x - xl) / float(xe - xl)) ** 2
            xi, zi = int(math.floor(x + 0.5)), max(zt + 1, int(math.floor(z + 0.5)))
            dy = int(math.floor(dy0 + (dye - dy0) * t ** H.get('dy_pow', 1.0) + 0.5))
            dy = max([dy] + [outer[(xi, zz)] + 1 for zz in range(zi, zi + H['thick']) if (xi, zz) in outer])
            at.setdefault(xi, []).append((zi, dy))
        for xi, v in at.items():                                          # 同一柱取的那幾個 z、dy 都放 ⇒ 斜的地方面相接
            for zi, dy in v:
                for zz in range(zi, zi + H['thick']):
                    both('head_rail', xi, dy, zz, GOLD if zz == zi + H['thick'] - 1 else WOOD)
        rail_at.append(at)
    HB = O.get('head_band')
    band_at = {}
    if HB:            # OcCre 船頭特寫：最上面那條是一整條寬帶 —— 深色底、上下金邊、中間一條金色卷草（波浪＋波峰波谷各一點），從艙壁的上角彎下去接到船首像後面
        xh, xl, xe = HB['x_h'], HB['x_l'], HB['x_e']
        dy0 = outer_h.get((xh, HB['z_h'] - HB['h'] // 2), 0) + 1
        for i in range(0, 2401):
            t = i / 2400.0
            x = xh + (xe - xh) * t
            if x <= xl:
                z = HB['z_l'] + (HB['z_h'] - HB['z_l']) * ((xl - x) / float(xl - xh)) ** 2
            else:
                z = HB['z_l'] + (HB['z_e'] - HB['z_l']) * ((x - xl) / float(xe - xl)) ** 2
            xi, zi = int(math.floor(x + 0.5)), int(math.floor(z + 0.5))
            dy = int(math.floor(dy0 + (HB['dy_e'] - dy0) * t ** HB.get('dy_pow', 1.0) + 0.5))
            dy = max([dy] + [outer_h[(xi, zz)] + 1 for zz in range(zi - HB['h'] + 1, zi + 1) if (xi, zz) in outer_h])
            band_at.setdefault(xi, set()).add((zi, dy))
        P_, A_ = HB['period'], HB['amp']
        mid = (HB['h'] - 1) / 2.0
        for xi, v in band_at.items():
            wave = mid + A_ * math.sin(2 * math.pi * xi / P_)
            ph = (xi % P_) / float(P_)
            for zi, dy in v:
                for k in range(HB['h']):                                  # k 0 ＝ 下緣
                    zz = zi - HB['h'] + 1 + k
                    if k in (0, HB['h'] - 1):
                        c = GOLD
                    elif abs(k - wave) < 0.6 or (abs(ph - 0.25) < 0.07 and k == int(round(mid + A_ + 1))) or (abs(ph - 0.75) < 0.07 and k == int(round(mid - A_ - 1))):
                        c = GOLD                                          # 卷草：波浪線＋波峰上、波谷下各一個金點（渦卷的頭）
                    else:
                        c = HB['fill']
                    both('head_band', xi, dy, zz, c)
                    both('head_band', xi, dy - 1, zz, GOLD if k in (0, HB['h'] - 1) else HB['fill'])   # 裡面那一層（朝船）
    low_r = rail_at[-1] if rail_at else {}
    for x in H['timbers']:                                                # 喙上的 head timber：喙的甲板直立撐到寬帶（或最下面那條欄杆）的底
        tgt = band_at.get(x) or low_r.get(x)
        if not tgt:
            continue
        zu, dy = min((zi - (HB['h'] - 1 if x in band_at else 0), d) for zi, d in tgt)
        for z in range(zt + 1, zu):
            both('head_timber', x, dy, z, GOLD)
    for ck in O.get('cheeks', {}).get('rows', []):                        # cheek：船頭兩側貼著船殼往前、往下彎進艏柱的金線（凸出 1 格）
        for x in range(ck['x0'], xs0 + 1):
            t = (x - ck['x0']) / float(max(1, xs0 - ck['x0']))
            z = int(math.floor(ck['z0'] + (ck['z1'] - ck['z0']) * t ** 2 + 0.5))
            for zz in (z, z + 1):
                o = outer_h.get((x, zz))
                if o is not None:
                    both('cheek', x, o + 1, zz, GOLD)
        for x in range(xs0 + 1, xs0 + 1 + ck.get('ext', 0)):              # 步驟 17：過了艏柱沿 knee 兩側再往前（knee 半寬 cutwater_half ⇒ 貼在外面一格）
            for zz in (ck['z1'], ck['z1'] + 1):
                both('cheek', x, E['cutwater_half'] + 1, zz, GOLD)

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
