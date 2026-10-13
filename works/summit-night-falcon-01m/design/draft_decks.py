# 新圖紙 04 甲板與砲門（TASK-0529 階段四）：plan.json 的 lines（v2）＋ framing ＋ planking ＋ decks ⇒ 三件作品的清單、圖紙、verify_decks.json。
# 用法：python -I -X utf8 -B draft_decks.py <design 資料夾>
#   · 船殼現況照設計重建：masks/frames（階段二）＋ masks/planking（階段三：刻、貼、換色照順序）—— 兩階段的結果帳都驗過 作品＝設計。
#   · 甲板高度（格心 x+0.5 的舷弧 sheer）：主甲板板那一格 ＝ floor(sheer) − 1（板頂 ＝ 舷弧）；
#     後甲板 x ≤ 斷口：甲板板 ＝ floor(sheer + rise) − 1；底下的艙房地板（cabin sole）＝ 主甲板 − cabin_drop。
#   · 甲板板 ＝ 那一層、船殼體積裡、船殼作品沒有格的地方（含肋骨之間的縫 ⇒ 封住縫的頂）；扣艙口、桅孔。
#   · 橫樑：每 beam_spacing 格一根、跟肋骨同欄（sided 2）、板下 2 格；艙口裡斷開、兩側加 carling；桅孔裡斷開。
#   · clamp（船殼作品）：肋骨內面那一格（深度 3 < d ≤ 4）、橫樑底下 2 格，沿船長；橫樑擱在它上面。
#   · 砲門（船殼作品）：開口 x 站−1..站+3（切掉站上那根肋骨）、z 甲板＋1＋sill 起 height 格；刻開口裡船殼那一側的格（帶原色守門）；
#     開口外一圈、肋骨那一層（1 < d ≤ 3）的空格補 port sill／lintel／port timber。
#   · 斷口艙壁（後甲板作品）：x ＝ 斷口那一欄，從艙房地板上一格到後甲板板下一格。
#   · 重跑逐位元組相同。
import sys, os, json, hashlib
import numpy as np
from PIL import Image, ImageDraw
from scipy import ndimage

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from draft_lines import YC, font
from draft_hull import build, NX, NY, NZ

NZ4 = 80


def read_list(path):
    a = np.loadtxt(path, delimiter=',', dtype=int, comments='#', ndmin=2)
    return a


def hull_now(d):
    col = np.zeros((NX, NY, NZ4), np.int16)
    vh = json.load(open(os.path.join(d, 'verify_hull.json'), encoding='utf-8'))
    for o in vh['stamp_order']:
        a = read_list(os.path.join(d, o['file'])); col[a[:, 0], a[:, 1], a[:, 2]] = a[:, 3]
    vp = json.load(open(os.path.join(d, 'verify_planking.json'), encoding='utf-8'))
    for o in vp['stamp_order']:
        a = read_list(os.path.join(d, o['file']))
        if o['op'] == 'carvevox': col[a[:, 0], a[:, 1], a[:, 2]] = 0
        else: col[a[:, 0], a[:, 1], a[:, 2]] = a[:, 3]
    return col


def lst(pts, col):
    if np.isscalar(col): col = np.full(len(pts), col)
    return ''.join(f"{a},{b},{c},{k}\n" for (a, b, c), k in zip(pts, col))


def main():
    d = sys.argv[1]
    plan = json.load(open(os.path.join(d, 'plan.json'), encoding='utf-8'))
    Dk = plan['decks']; C = Dk['colors']; up = plan['lines']['upper']; q = up['quarterdeck']
    H, solid, dist, own, names, layer, aft, dropped = build(plan)
    pad = lambda a, v: np.concatenate([a, np.full(a.shape[:2] + (NZ4 - NZ,), v, a.dtype)], axis=2)
    solid, dist = pad(solid, False), pad(dist, 99.0)
    hull = hull_now(d)
    X = np.arange(NX)[:, None, None]; Y = np.arange(NY)[None, :, None]; Z = np.arange(NZ4)[None, None, :]
    DY = np.abs(Y - YC)
    xc = np.arange(NX) + 0.5
    brk = q['x_break']
    zf_main = np.floor(H.sheer(xc)).astype(int)                 # 主甲板板頂（第一格空氣）
    lv_main = zf_main - 1
    lv_qd = np.floor(H.sheer(xc) + q['rise']).astype(int) - 1
    lv_cabin = lv_main - Dk['cabin_drop']
    aftz = np.arange(NX) <= brk
    hold = solid & (hull == 0)
    # 每一層：哪幾欄、板在哪一層
    decks = {'main': (~aftz, lv_main), 'cabin': (aftz, lv_cabin), 'quarter': (aftz, lv_qd)}
    LV = lambda key: decks[key][1][:, None, None]
    INX = lambda key: decks[key][0][:, None, None]

    # ── 艙口、桅孔 ──
    hatch_open = {k: np.zeros((NX, NY, NZ4), bool) for k in decks}
    hatch_ring = {k: np.zeros((NX, NY, NZ4), bool) for k in decks}
    carl = {k: np.zeros((NX, NY, NZ4), bool) for k in decks}
    for h in Dk['hatches']:
        k = h['deck']; x0, x1, w = h['x'][0], h['x'][1], h['dy']
        inx = (X >= x0) & (X <= x1); iny = DY <= w
        hatch_open[k] |= inx & iny
        ring = (X >= x0 - 1) & (X <= x1 + 1) & (DY <= w + 1) & ~(inx & iny)
        hatch_ring[k] |= ring & (Z >= LV(k) + 1) & (Z <= LV(k) + Dk['coaming_height']) & INX(k)
        carl[k] |= (X >= x0 - 1) & (X <= x1 + 1) & (DY == w + 1)
    mr = Dk['masts_provisional']
    mast = np.zeros((NX, NY, NZ4), bool)
    for mx in (mr['main'], mr['fore']):
        mast |= ((X - mx) ** 2 + (Y - YC) ** 2) <= mr['hole_r'] ** 2

    # ── 砲門（船殼）──
    P = Dk['ports']
    opening = np.zeros((NX, NY, NZ4), bool); ring_p = np.zeros((NX, NY, NZ4), bool); ports_info = []
    for s in P['stations']:
        xa, xb = s + P['x_from_station'], s + P['x_from_station'] + P['width'] - 1
        key = 'cabin' if s + 1 <= brk else 'main'
        L = int(decks[key][1][s + 1])
        za, zb = L + 1 + P['sill'], L + P['sill'] + P['height']
        box = (X >= xa) & (X <= xb) & (Z >= za) & (Z <= zb) & (DY >= 4)
        opening |= box
        rb = (X >= xa - 1) & (X <= xb + 1) & (Z >= za - 1) & (Z <= zb + 1) & (DY >= 4) & ~box
        ring_p |= rb
        ports_info.append({'station': s, 'x': [int(xa), int(xb)], 'z': [int(za), int(zb)], 'deck': key, 'deck_plank_z': L,
                           'top_z': round(float(H.top(s + 1.5)), 2)})
    carve = opening & (hull > 0)
    hull2 = hull.copy(); hull2[carve] = 0
    lining = ring_p & layer_mask(dist, 1.0, 1.0 + plan['framing']['moulded']) & solid & (hull2 == 0)
    hull2[lining] = C['lining']

    # ── clamp（船殼）──
    clamp = np.zeros((NX, NY, NZ4), bool)
    for k in decks:
        clamp |= INX(k) & (Z >= LV(k) - 2 - Dk['clamp_tall']) & (Z <= LV(k) - 3)
    # 深度 3 < d ≤ 3+√2（跟外板同一招，斜的內面才連得起來）；碰不到船殼的碎塊不放
    # 🩸 第一版 3 < d ≤ 4：船頭、船尾斜的內面上 16 塊 2–4 格的碎片
    clamp &= layer_mask(dist, 3.0, 3.0 + Dk['clamp_depth']) & solid & (hull2 == 0) & ~opening
    lab_c, n_c = ndimage.label(clamp)
    touch = ndimage.binary_dilation(hull2 > 0, structure=ndimage.generate_binary_structure(3, 1))
    keep = np.isin(lab_c, np.unique(lab_c[clamp & touch]))
    clamp_dropped = int((clamp & ~keep).sum()); clamp &= keep
    hull2[clamp] = C['clamp']
    hold2 = solid & (hull2 == 0)

    # ── 甲板（子作品）──
    out = {'main': {}, 'quarter': {}}
    taken = np.zeros((NX, NY, NZ4), bool)
    bx = (np.arange(NX)[:, None, None] - Dk['beam_x0']) % Dk['beam_spacing'] < Dk['beam_sided']
    for k, work in (('main', 'main'), ('cabin', 'main'), ('quarter', 'quarter')):
        inx, L = INX(k), LV(k)
        # 舷弧格子化之後每隔一段高一格 ⇒ 階的地方往下補一格（跟兩旁較低的那一欄齊），兩段才面接面
        # 🩸 第一版只放 z ＝ L：主甲板 10 段、艙房地板 6 段、後甲板 5 段，段與段只靠邊角相接
        Lr = decks[k][1]
        low = np.minimum(Lr, np.minimum(np.roll(Lr, 1), np.roll(Lr, -1)))[:, None, None]
        plank = inx & (Z <= L) & (Z >= low) & hold2 & ~hatch_open[k] & ~mast & ~taken
        beam = inx & bx & (Z >= L - 2) & (Z <= L - 1) & hold2 & ~hatch_open[k] & ~mast & ~taken & ~plank
        carling = inx & carl[k] & (Z >= L - 2) & (Z <= L - 1) & hold2 & ~taken & ~plank & ~beam
        coam = hatch_ring[k] & hold2 & ~taken
        for nm, m, c in (('plank', plank, C['plank']), ('beam', beam, C['beam']), ('carling', carling, C['beam']), ('coaming', coam, C['coaming'])):
            out[work][k + '_' + nm] = (m, c); taken |= m
    # 斷口艙壁：x ＝ 斷口，艙房地板上一格 → 後甲板板下一格
    bh = (X == brk) & (Z >= LV('cabin') + 1) & (Z <= LV('quarter') - 1) & hold2 & ~taken
    out['quarter']['break_bulkhead'] = (bh, C['bulkhead']); taken |= bh
    # 封閉空腔補實（憲法號同一招）：船殼＋兩層甲板組起來之後、跟外面不通的空氣 ⇒ 歸主甲板作品，橫樑色
    allv0 = (hull2 > 0) | taken
    cav = ndimage.binary_fill_holes(allv0) & ~allv0
    out['main']['cavity_fill'] = (cav, C['beam']); taken |= cav

    # ── 清單 ──
    order = {'hull': [], 'main': [], 'quarter': []}
    for sub in order:
        od = os.path.join(d, 'masks', 'decks', sub); os.makedirs(od, exist_ok=True)
        for f in os.listdir(od): os.remove(os.path.join(od, f))

    def emit(sub, name, mask, col, op='stampvox', guard=None):
        pts = np.argwhere(mask)
        if len(pts) == 0: return
        text = lst(pts, guard[tuple(pts.T)]) if op == 'carvevox' else lst(pts, col)
        fn = name + '.vox.txt'
        open(os.path.join(d, 'masks', 'decks', sub, fn), 'w', encoding='utf-8', newline='\n').write(text)
        order[sub].append({'name': name, 'op': op, 'file': 'masks/decks/' + sub + '/' + fn, 'at': [0, 0, 0], 'voxels': int(len(pts)),
                           'sha256': hashlib.sha256(text.encode('utf-8')).hexdigest()})

    emit('hull', 'ports_carve', carve, None, op='carvevox', guard=hull)
    emit('hull', 'ports_lining', lining, C['lining'])
    emit('hull', 'clamps', clamp, C['clamp'])
    for sub in ('main', 'quarter'):
        for nm, (m, c) in out[sub].items(): emit(sub, nm, m, c)

    # ── 讀數 ──
    dm = np.zeros((NX, NY, NZ4), np.int16); dq = np.zeros((NX, NY, NZ4), np.int16)
    for nm, (m, c) in out['main'].items(): dm[m] = c
    for nm, (m, c) in out['quarter'].items(): dq[m] = c
    allv = (hull2 > 0) | (dm > 0) | (dq > 0)
    lab, ncomp = ndimage.label(allv)
    holes = int((ndimage.binary_fill_holes(allv) & ~allv).sum())
    comp = lambda a: int(ndimage.label(a > 0)[1])
    mir = lambda a: int((a != a[:, ::-1, :]).sum())
    # 砲門透光：開口範圍裡（那一側所有 |dy| ≥ 4）還剩幾格（船殼＋甲板）
    through = int((opening & allv).sum())
    # 開口上面那一列要有外板（lintel 外面），下面那一列也是
    lintel_ok = []
    for pi in ports_info:
        xa, xb = pi['x']; zb = pi['z'][1]; za = pi['z'][0]
        side = (Y[0, :, 0] > YC + 3)
        above = hull2[xa:xb + 1, :, zb + 1][:, side].any(axis=1).all()
        below = hull2[xa:xb + 1, :, za - 1][:, side].any(axis=1).all()
        lintel_ok.append(bool(above and below))
    # 牆不能有洞：開口外一圈每一欄，從開口那一側的最外格到肋骨內面都實心
    wall_holes = 0
    for pi in ports_info:
        xa, xb = pi['x']; za, zb = pi['z']
        for x_ in range(xa - 1, xb + 2):
            for z_ in range(za - 1, zb + 2):
                if xa <= x_ <= xb and za <= z_ <= zb: continue
                col = hull2[x_, YC + 4:, z_]
                ys = np.nonzero(col)[0]
                if len(ys) == 0: wall_holes += 1; continue
                seg = col[ys.min():ys.max() + 1]
                wall_holes += int((seg == 0).sum())
    # 淨高（格）：艙房地板頂 → 後甲板橫樑底；船中主甲板 → 舷牆頂
    xs_cab = [x for x in range(60, brk + 1) if solid[x].any()]
    head_cabin = [int(lv_qd[x] - 2 - (lv_cabin[x] + 1)) for x in xs_cab]
    R = {'stamp_order': order,
         'levels': {'main_plank_z_at': {str(x): int(lv_main[x]) for x in (140, 175, 210, 250)},
                    'cabin_plank_z_at': {str(x): int(lv_cabin[x]) for x in (70, 100, 130)},
                    'quarter_plank_z_at': {str(x): int(lv_qd[x]) for x in (70, 100, 130)}},
         'headroom_cabin_vox': {'min': min(head_cabin), 'max': max(head_cabin)},
         'ports': ports_info, 'ports_lintel_and_sill_planked': lintel_ok,
         'clamp_dropped_fragments': clamp_dropped, 'cavity_filled': int(cav.sum()),
         'counts': {'hull_carve': int(carve.sum()), 'hull_lining': int(lining.sum()), 'hull_clamps': int(clamp.sum()),
                    'hull_after': int((hull2 > 0).sum()), 'deck_main': int((dm > 0).sum()), 'deck_quarter': int((dq > 0).sum()),
                    'assembly_total': int(allv.sum())},
         'checks': {'overlap_hull_deckmain': int(((hull2 > 0) & (dm > 0)).sum()), 'overlap_hull_deckquarter': int(((hull2 > 0) & (dq > 0)).sum()),
                    'overlap_decks': int(((dm > 0) & (dq > 0)).sum()),
                    'decks_outside_hull_volume': int((((dm > 0) | (dq > 0)) & ~solid).sum()),
                    'ports_see_through_remaining': through, 'port_wall_holes': wall_holes,
                    'components_assembly': int(ncomp), 'enclosed_cavity_assembly': holes,
                    'components_hull': comp(hull2), 'components_deck_main': comp(dm), 'components_deck_quarter': comp(dq),
                    'mirror_hull': mir(hull2), 'mirror_deck_main': mir(dm), 'mirror_deck_quarter': mir(dq)}}
    with open(os.path.join(d, 'verify_decks.json'), 'w', encoding='utf-8', newline='\n') as fo:
        json.dump(R, fo, ensure_ascii=False, indent=2, sort_keys=True); fo.write('\n')
    draw(H, R, hull2, dm, dq, opening, Dk, os.path.join(d, 'sheet04_decks_v1.png'))
    print(json.dumps({k: R[k] for k in ('headroom_cabin_vox', 'counts', 'checks', 'clamp_dropped_fragments', 'cavity_filled')}, ensure_ascii=False, indent=1))


def layer_mask(dist, lo, hi):
    return (dist > lo) & (dist <= hi + 1e-9)


def pal(k):
    return (int(((k >> 5) & 7) * 255 / 7), int(((k >> 2) & 7) * 255 / 7), int((k & 3) * 255 / 3))


def draw(H, R, hull, dm, dq, opening, Dk, path):
    S = 4; W, Hh = 1700, 1130
    im = Image.new('RGB', (W, Hh), (250, 248, 242)); g = ImageDraw.Draw(im); ink = (30, 30, 30)
    g.text((20, 12), "夜隼號 Night Falcon　新圖紙 04　甲板與砲門（側面／俯視／剖面）　0.1 m／格　summit 2026-10-13　（設計）", fill=ink, font=font(24))
    allc = np.where(dm > 0, dm, np.where(dq > 0, dq, hull))
    # 側面（右舷外面看）
    top = 60; base = top + 76 * S; ox = 40
    g.text((ox, top - 4), "側面（從右舷看，最外面那一格；砲門看得進船艙）", fill=ink, font=font(18))
    half = allc[:, YC:, :]
    hasv = (half > 0).any(axis=1)
    last = half.shape[1] - 1 - np.argmax(half[:, ::-1, :] > 0, axis=1)
    for xi, zi in np.argwhere(hasv):
        k = int(half[xi, last[xi, zi], zi])
        g.rectangle([ox + xi * S, base - (zi + 1) * S, ox + xi * S + S - 1, base - zi * S - 1], fill=pal(k))
    # 俯視：甲板（主＋後）每一欄最高那一格
    t2 = base + 30; S3 = 2.6
    g.text((ox, t2), "俯視（甲板子作品；艙口、桅孔是空的）", fill=ink, font=font(18))
    dd = np.where(dq > 0, dq, dm)
    hi = (dd > 0).any(axis=2)
    zt = dd.shape[2] - 1 - np.argmax(dd[:, :, ::-1] > 0, axis=2)
    for xi, yi in np.argwhere(hi):
        k = int(dd[xi, yi, zt[xi, yi]])
        g.rectangle([ox + xi * S, t2 + 30 + yi * S3, ox + xi * S + S - 1, t2 + 30 + yi * S3 + S3], fill=pal(k))
    for nm, mx in (('主桅（暫定）', Dk['masts_provisional']['main']), ('前桅（暫定）', Dk['masts_provisional']['fore'])):
        g.text((ox + mx * S - 30, t2 + 30 + 114 * S3 + 4), nm, fill=(150, 60, 60), font=font(14))
    # 剖面：x 116（艙房＋後甲板）與 x 186（船腰）
    for i, (xs_, title) in enumerate(((117, "x 117 剖面（艙房裡的砲門、後甲板）"), (187, "x 187 剖面（船腰的砲門、主甲板）"))):
        S2 = 5; cx_ = 700 + i * 520; b3 = 1100
        g.text((cx_ - 200, b3 - 66 * S2 - 30), title, fill=ink, font=font(18))
        for yi in range(NY):
            for zi in range(NZ4):
                k = int(allc[xs_, yi, zi])
                if k: g.rectangle([cx_ + (yi - YC) * S2, b3 - (zi + 1) * S2, cx_ + (yi - YC + 1) * S2 - 1, b3 - zi * S2 - 1], fill=pal(k))
    c = R['counts']; ch = R['checks']
    lines = ["讀數（verify_decks.json）",
             "船殼：刻 " + str(c['hull_carve']) + "　砲門框 " + str(c['hull_lining']) + "　clamp " + str(c['hull_clamps']) + "　→ " + str(c['hull_after']),
             "主甲板 " + str(c['deck_main']) + "　後甲板 " + str(c['deck_quarter']) + "　組起來 " + str(c['assembly_total']),
             "重疊 " + str(ch['overlap_hull_deckmain'] + ch['overlap_hull_deckquarter'] + ch['overlap_decks']) + "　元件 " + str(ch['components_assembly']) + "　空腔 " + str(ch['enclosed_cavity_assembly']) + "　砲門透光剩 " + str(ch['ports_see_through_remaining']) + "　牆洞 " + str(ch['port_wall_holes']),
             "艙房淨高 " + str(R['headroom_cabin_vox']['min']) + "～" + str(R['headroom_cabin_vox']['max']) + " 格"]
    for i, s_ in enumerate(lines): g.text((40, 760 + i * 26), s_, fill=ink, font=font(18 if i else 24))
    im.save(path, optimize=False)


if __name__ == '__main__':
    main()
