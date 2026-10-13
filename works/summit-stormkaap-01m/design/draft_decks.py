# 新圖紙 04 甲板、砲門、clamp（TASK-0547 階段四）：plan.json 的 lines ＋ framing ＋ decks ⇒ 船殼與五件甲板子作品的清單、圖紙、verify_decks.json。
# 用法：python -I -X utf8 -B draft_decks.py <design 資料夾>
#   · 從夜隼號 draft_decks.py（TASK-0529 階段四）改：兩層甲板＋一段後甲板 → 五層（下甲板、上甲板、halfdek、kampanje、bak）；兩排砲門；
#     砲門的開口只量到船邊（|dy| ≥ 船殼半寬 − 8），⛔ 不橫切整艘船（船中有艙壁、艙口圍板）。
#   · 船殼現況照設計重建（sk_state：階段二、三的清單，兩階段結果帳都驗過 作品＝設計）。
#   · 甲板高度（格心 x+0.5 的舷弧 sheer）：板那一格 ＝ floor(sheer + 偏移) − 1（板頂 ＝ sheer + 偏移）。
#     下甲板 −20、上甲板 0、halfdek ＋20、kampanje ＋38、bak ＋20 —— 跟 lines.upper.tiers 的 rise 同一套。
#   · 甲板板 ＝ 那一層、船殼體積裡、船殼作品沒有格的地方（含肋骨之間的縫）；扣艙口、桅孔。舷弧格子化的階往下補一格（夜隼號 🩸）。
#   · 橫樑：每 beam_spacing 格一根、跟肋骨同欄（sided 3）、板下 3 格；艙口、桅孔裡斷開，艙口兩側加 carling。
#   · clamp（船殼）：肋骨內面那一層（深度 1+moulded < d ≤ 1+moulded+√2）、橫樑底下 clamp_tall 格。
#   · 砲門（船殼）：開口 x 中心 ±3、z 板頂 ＋ sill 起 height 格；刻開口裡船殼的格（帶原色守門）；開口外一圈、肋骨那一層的空格補框（lining）。
#   · 艙壁（各自那一層的子作品）：halfdek 前緣、kampanje 前緣、bak 後緣，2 格厚，中線開一扇門。
#   · 封閉空腔：全部組起來之後跟外面不通的空氣 ⇒ 補實（歸下甲板作品）。
#   · 重跑逐位元組相同。
import sys, os, json, hashlib
import numpy as np
from PIL import Image, ImageDraw
from scipy import ndimage

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from draft_lines import font
from draft_hull import build
from sk_state import state_after

NZ4 = 180
DECKS = ('lower', 'upper', 'half', 'kamp', 'bak')


def lst(pts, col):
    if np.isscalar(col): col = np.full(len(pts), col)
    return ''.join(f"{a},{b},{c},{k}\n" for (a, b, c), k in zip(pts, col))


def pal(k):
    return (int(((k >> 5) & 7) * 255 / 7), int(((k >> 2) & 7) * 255 / 7), int((k & 3) * 255 / 3))


def layer_mask(dist, lo, hi):
    return (dist > lo) & (dist <= hi + 1e-9)


def main():
    d = sys.argv[1]
    plan = json.load(open(os.path.join(d, 'plan.json'), encoding='utf-8'))
    Dk = plan['decks']; C = Dk['colors']; moulded = plan['framing']['moulded']
    H, solid, dist, own, names, layer, aft, dropped = build(plan)
    NX, NY, YC = H.NX, H.NY, H.YC
    pad = lambda a, v: np.concatenate([a, np.full(a.shape[:2] + (NZ4 - a.shape[2],), v, a.dtype)], axis=2)
    solid, dist = pad(solid, False), pad(dist, 99.0)
    hull = state_after(d, 'stage3', nz=NZ4)['hull']
    X = np.arange(NX)[:, None, None]; Y = np.arange(NY)[None, :, None]; Z = np.arange(NZ4)[None, None, :]
    DY = np.abs(Y - YC)
    xc = np.arange(NX) + 0.5
    sh = H.sheer(xc)
    lv, inx = {}, {}
    for k in DECKS:
        o = Dk['levels'][k]
        lv[k] = np.floor(sh + o['offset']).astype(int) - 1
        if 'x_max' in o: inx[k] = xc <= o['x_max']
        elif 'x_min' in o: inx[k] = xc >= o['x_min']
        else: inx[k] = np.ones(NX, bool)
    LV = lambda k: lv[k][:, None, None]
    INX = lambda k: inx[k][:, None, None]

    # ── 艙口、桅孔 ──
    hatch_open = {k: np.zeros((NX, NY, NZ4), bool) for k in DECKS}
    hatch_ring = {k: np.zeros((NX, NY, NZ4), bool) for k in DECKS}
    carl = {k: np.zeros((NX, NY, NZ4), bool) for k in DECKS}
    for h in Dk['hatches']:
        k = h['deck']; x0, x1, w = h['x'][0], h['x'][1], h['dy']
        ix = (X >= x0) & (X <= x1); iy = DY <= w
        hatch_open[k] |= ix & iy
        ring = (X >= x0 - 1) & (X <= x1 + 1) & (DY <= w + 1) & ~(ix & iy)
        hatch_ring[k] |= ring & (Z >= LV(k) + 1) & (Z <= LV(k) + Dk['coaming_height']) & INX(k)
        carl[k] |= (X >= x0 - 1) & (X <= x1 + 1) & (DY == w + 1)
    mast = np.zeros((NX, NY, NZ4), bool)
    for m in Dk['masts_provisional']['list']:
        mast |= ((X + 0.5 - m['x']) ** 2 + (Y + 0.5 - (YC + 0.5)) ** 2) <= m['hole_r'] ** 2

    # ── 砲門（船殼）──
    xs3 = np.arange(NX) + 0.5; zs3 = np.arange(NZ4) + 0.5
    HB = np.nan_to_num(H.hb(xs3[:, None], zs3[None, :]), nan=0.0)[:, None, :]       # (NX,1,NZ4) 船殼半寬
    opening = np.zeros((NX, NY, NZ4), bool); ring_p = np.zeros((NX, NY, NZ4), bool); ports_info = []
    for row in Dk['ports']:
        k = row['deck']
        for xcen in row['x']:
            xa, xb = xcen - 3, xcen + 3
            L = int(lv[k][xcen])
            za, zb = L + 1 + row['sill'], L + row['sill'] + row['height']
            near_side = (DY + 0.5 >= HB - 8)
            box = (X >= xa) & (X <= xb) & (Z >= za) & (Z <= zb) & near_side
            opening |= box
            ring_p |= (X >= xa - 1) & (X <= xb + 1) & (Z >= za - 1) & (Z <= zb + 1) & near_side & ~box
            ports_info.append({'row': row['name'], 'x': [int(xa), int(xb)], 'z': [int(za), int(zb)], 'deck': k, 'deck_plank_z': L,
                               'rail_top_z': round(float(H.top(xcen + 0.5)), 2)})
    carve = opening & (hull > 0)
    hull2 = hull.copy(); hull2[carve] = 0
    lining = ring_p & layer_mask(dist, 1.0, 1.0 + moulded) & solid & (hull2 == 0)
    hull2[lining] = C['lining']

    # ── clamp（船殼）：橫樑底下 ──
    bm = Dk['beam_moulded']
    clamp = np.zeros((NX, NY, NZ4), bool)
    for k in DECKS:
        clamp |= INX(k) & (Z >= LV(k) - bm - Dk['clamp_tall']) & (Z <= LV(k) - bm - 1)
    clamp &= layer_mask(dist, 1.0 + moulded, 1.0 + moulded + Dk['clamp_depth']) & solid & (hull2 == 0) & ~opening
    lab_c, n_c = ndimage.label(clamp)
    touch = ndimage.binary_dilation(hull2 > 0, structure=ndimage.generate_binary_structure(3, 1))
    keep = np.isin(lab_c, np.unique(lab_c[clamp & touch]))
    clamp_dropped = int((clamp & ~keep).sum()); clamp &= keep
    hull2[clamp] = C['clamp']
    hold2 = solid & (hull2 == 0)

    # ── 甲板（子作品）──
    out = {k: {} for k in DECKS}
    taken = np.zeros((NX, NY, NZ4), bool)
    bx = (np.arange(NX)[:, None, None] - Dk['beam_x0']) % Dk['beam_spacing'] < Dk['beam_sided']
    for k in DECKS:
        L = LV(k); Lr = np.where(inx[k], lv[k], 10 ** 6)
        low = np.minimum(Lr, np.minimum(np.roll(Lr, 1), np.roll(Lr, -1)))
        low = np.where(low > 10 ** 5, lv[k], low)[:, None, None]
        plank = INX(k) & (Z <= L) & (Z >= low) & hold2 & ~hatch_open[k] & ~mast & ~taken
        beam = INX(k) & bx & (Z >= L - bm) & (Z <= L - 1) & hold2 & ~hatch_open[k] & ~mast & ~taken & ~plank
        carling = INX(k) & carl[k] & (Z >= L - bm) & (Z <= L - 1) & hold2 & ~taken & ~plank & ~beam
        coam = hatch_ring[k] & hold2 & ~taken
        for nm, m, c in (('plank', plank, C['plank']), ('beam', beam, C['beam']), ('carling', carling, C['beam']), ('coaming', coam, C['coaming'])):
            out[k][nm] = (m, c); taken |= m
    # 艙壁：x 一欄 2 格厚，從下面那層板頂上一格到上面那層板下一格；中線開門
    for b in Dk['bulkheads']:
        lo_k, hi_k, owner = b['below'], b['above'], b['work']
        xs_ = np.arange(b['x'][0], b['x'][1] + 1)
        m = np.zeros((NX, NY, NZ4), bool)
        for x_ in xs_:
            m[x_, :, lv[lo_k][x_] + 1: lv[hi_k][x_]] = True
        door = (DY <= b['door_dy']) & (Z >= LV(lo_k) + 1) & (Z <= LV(lo_k) + b['door_h'])
        m &= hold2 & ~taken & ~door
        out[owner]['bulkhead_' + b['name']] = (m, C['bulkhead']); taken |= m
    # 每件甲板只留主體：沒接上最大那一塊、又小於 frag_max 格的碎片丟掉（照實記）
    # 🩸 第一版下甲板 3 塊：船頭艏柱旁 5 格板被艏柱切開，另有兩個補實的小口袋（1、6 格）掛在下甲板名下卻沒碰到它
    frag_dropped = {}
    for k in DECKS:
        u = np.zeros((NX, NY, NZ4), bool)
        for nm, (m, c) in out[k].items(): u |= m
        lab_k, n_k = ndimage.label(u)
        if n_k <= 1: continue
        sz = ndimage.sum(u, lab_k, range(1, n_k + 1)); big = int(np.argmax(sz)) + 1
        small = (lab_k != big) & u & np.isin(lab_k, [i + 1 for i in range(n_k) if sz[i] < Dk['frag_max']])
        if small.any():
            frag_dropped[k] = int(small.sum())
            for nm in list(out[k]): out[k][nm] = (out[k][nm][0] & ~small, out[k][nm][1])
            taken &= ~small
    allv0 = (hull2 > 0) | taken
    cav = ndimage.binary_fill_holes(allv0) & ~allv0
    # 補實的口袋：碰到哪一件（6 鄰）的格最多就歸哪一件；哪件甲板都沒碰到 ⇒ 歸船殼
    lab_v, n_v = ndimage.label(cav)
    cav_to = {k: np.zeros((NX, NY, NZ4), bool) for k in ('hull',) + DECKS}
    st6 = ndimage.generate_binary_structure(3, 1)
    for i in range(1, n_v + 1):
        piece = lab_v == i
        ring = ndimage.binary_dilation(piece, structure=st6) & ~piece
        best, bn = 'hull', 0
        for k in DECKS:
            u = np.zeros((NX, NY, NZ4), bool)
            for nm, (m, c) in out[k].items(): u |= m
            n_ = int((ring & u).sum())
            if n_ > bn: best, bn = k, n_
        cav_to[best] |= piece
    for k in DECKS:
        if cav_to[k].any(): out[k]['cavity_fill'] = (cav_to[k], C['beam'])
    taken |= cav
    hull2[cav_to['hull']] = C['beam']

    # ── 清單 ──
    subs = ('hull',) + DECKS
    order = {s: [] for s in subs}
    for s in subs:
        od = os.path.join(d, 'masks', 'decks', s); os.makedirs(od, exist_ok=True)
        for f in os.listdir(od): os.remove(os.path.join(od, f))

    def emit(sub, name, mask, col, op='stampvox', guard=None):
        pts = np.argwhere(mask)
        if len(pts) == 0: return
        text = lst(pts, guard[tuple(pts.T)]) if op == 'carvevox' else lst(pts, col)
        fn = name + '.vox.txt'
        open(os.path.join(d, 'masks', 'decks', sub, fn), 'w', encoding='utf-8', newline='\n').write(text)
        order[sub].append({'name': name, 'op': op, 'file': 'masks/decks/' + sub + '/' + fn, 'at': [0, 0, 0], 'expect_pixels': int(len(pts)),
                           'sha256': hashlib.sha256(text.encode('utf-8')).hexdigest()})

    emit('hull', 'ports_carve', carve, None, op='carvevox', guard=hull)
    emit('hull', 'ports_lining', lining, C['lining'])
    emit('hull', 'clamps', clamp, C['clamp'])
    emit('hull', 'cavity_fill', cav_to['hull'], C['beam'])
    for k in DECKS:
        for nm, (m, c) in out[k].items(): emit(k, nm, m, c)

    # ── 讀數 ──
    dk = {}
    for k in DECKS:
        a = np.zeros((NX, NY, NZ4), np.int16)
        for nm, (m, c) in out[k].items(): a[m] = c
        dk[k] = a
    allv = hull2 > 0
    for k in DECKS: allv = allv | (dk[k] > 0)
    lab, ncomp = ndimage.label(allv)
    holes = int((ndimage.binary_fill_holes(allv) & ~allv).sum())
    comp = lambda a: int(ndimage.label(a > 0)[1])
    mir = lambda a: int((a != a[:, ::-1, :]).sum())
    overl = {}
    for i, a in enumerate(('hull',) + DECKS):
        for b in (('hull',) + DECKS)[i + 1:]:
            A = hull2 > 0 if a == 'hull' else dk[a] > 0; B = dk[b] > 0
            n = int((A & B).sum())
            if n: overl[a + '×' + b] = n
    through = int((opening & allv).sum())
    lintel_ok = []
    for pi in ports_info:
        xa, xb = pi['x']; za, zb = pi['z']
        side = np.arange(NY) > YC + 3
        above = hull2[xa:xb + 1, :, zb + 1][:, side].any(axis=1).all()
        below = hull2[xa:xb + 1, :, za - 1][:, side].any(axis=1).all()
        lintel_ok.append(bool(above and below))
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
    # 淨高（格）：每一層板頂 → 上面那一層橫樑底（船中與各段代表站）
    def head(lo_k, hi_k, x_):
        return int(lv[hi_k][x_] - bm - (lv[lo_k][x_] + 1))
    R = {'stamp_order': order,
         'levels_plank_z': {k: {str(x): int(lv[k][x]) for x in (110, 150, 200, 300, 400, 500, 530) if inx[k][x]} for k in DECKS},
         'headroom_vox': {'lower→upper x300': head('lower', 'upper', 300), 'upper→half x200': head('upper', 'half', 200),
                          'half→kamp x140': head('half', 'kamp', 140), 'upper→bak x500': head('upper', 'bak', 500)},
         'ports': ports_info, 'ports_per_side': len(ports_info), 'ports_lintel_and_sill_planked': lintel_ok,
         'clamp_dropped_fragments': clamp_dropped, 'cavity_filled': int(cav.sum()),
         'cavity_filled_by_work': {k: int(v.sum()) for k, v in cav_to.items() if v.any()}, 'deck_fragments_dropped': frag_dropped,
         'counts': dict({'hull_carve': int(carve.sum()), 'hull_lining': int(lining.sum()), 'hull_clamps': int(clamp.sum()), 'hull_after': int((hull2 > 0).sum())},
                        **{'deck_' + k: int((dk[k] > 0).sum()) for k in DECKS}, assembly_total=int(allv.sum())),
         'checks': dict({'overlaps': overl, 'decks_outside_hull_volume': int((allv & (hull2 == 0) & ~solid).sum()),
                         'ports_see_through_remaining': through, 'port_wall_holes': wall_holes,
                         'components_assembly': int(ncomp), 'enclosed_cavity_assembly': holes, 'components_hull': comp(hull2), 'mirror_hull': mir(hull2)},
                        **{'components_' + k: comp(dk[k]) for k in DECKS}, **{'mirror_' + k: mir(dk[k]) for k in DECKS})}
    with open(os.path.join(d, 'verify_decks.json'), 'w', encoding='utf-8', newline='\n') as fo:
        json.dump(R, fo, ensure_ascii=False, indent=2, sort_keys=True); fo.write('\n')
    draw(H, R, hull2, dk, lv, inx, os.path.join(d, 'sheet04_decks_v1.png'))
    print(json.dumps({k: R[k] for k in ('headroom_vox', 'ports_per_side', 'counts', 'checks', 'clamp_dropped_fragments', 'cavity_filled', 'cavity_filled_by_work', 'deck_fragments_dropped')}, ensure_ascii=False, indent=1))
    print('lintel_ok', sum(R['ports_lintel_and_sill_planked']), '/', len(R['ports_lintel_and_sill_planked']))


def draw(H, R, hull2, dk, lv, inx, path):
    NX, NY, YC = H.NX, H.NY, H.YC
    S = 2.2; W, Hh = 1700, 1240
    im = Image.new('RGB', (W, Hh), (250, 248, 242)); g = ImageDraw.Draw(im); ink = (30, 30, 30)
    g.text((20, 12), "風暴角號 Stormkaap　新圖紙 04　甲板、砲門、clamp（側面／中線縱剖面／剖面）　0.1 m／格　summit 2026-10-13　（設計）", fill=ink, font=font(22))
    allc = hull2.copy()
    for k in DECKS: allc = np.where(dk[k] > 0, dk[k], allc)
    # 側面（右舷外面看）
    top = 50; base = top + NZ4 * S; ox = 20
    g.text((ox, top), "側面（從右舷看，最外面那一格）", fill=ink, font=font(16))
    half = allc[:, YC:, :]
    hasv = (half > 0).any(axis=1)
    last = half.shape[1] - 1 - np.argmax(half[:, ::-1, :] > 0, axis=1)
    for xi, zi in np.argwhere(hasv):
        g.rectangle([ox + xi * S, base - (zi + 1) * S, ox + xi * S + S, base - zi * S], fill=pal(int(half[xi, last[xi, zi], zi])))
    # 中線縱剖面（y ＝ YC＋12，避開中線艙口邊緣）—— 甲板層、艙壁、艙口
    top2 = base + 20; base2 = top2 + NZ4 * S
    ys = YC + 12
    g.text((ox, top2), "縱剖面 y " + str(ys) + "（中線往右舷 1.2 m）", fill=ink, font=font(16))
    for xi, zi in np.argwhere(allc[:, ys, :] > 0):
        g.rectangle([ox + xi * S, base2 - (zi + 1) * S, ox + xi * S + S, base2 - zi * S], fill=pal(int(allc[xi, ys, zi])))
    # 三個剖面
    S2 = 2.6
    for i, x_ in enumerate((140, 200, 300, 500)):
        cx = 260 + i * 380; b3 = Hh - 30
        g.text((cx - 130, b3 - 170 * S2 - 4), "x " + str(x_), fill=ink, font=font(16))
        for yi, zi in np.argwhere(allc[x_] > 0):
            g.rectangle([cx + (yi - YC) * S2, b3 - (zi + 1) * S2, cx + (yi - YC + 1) * S2, b3 - zi * S2], fill=pal(int(allc[x_, yi, zi])))
    c = R['counts']; k_ = R['checks']
    lines = ["讀數（verify_decks.json）",
             "砲門每舷 " + str(R['ports_per_side']) + "　刻 " + str(c['hull_carve']) + "　框 " + str(c['hull_lining']) + "　clamp " + str(c['hull_clamps']),
             "甲板 下 " + str(c['deck_lower']) + "／上 " + str(c['deck_upper']) + "／halfdek " + str(c['deck_half']) + "／kampanje " + str(c['deck_kamp']) + "／bak " + str(c['deck_bak']) + "　組裝 " + str(c['assembly_total']),
             "元件 " + str(k_['components_assembly']) + "　空腔 " + str(k_['enclosed_cavity_assembly']) + "　重疊 " + str(sum(k_['overlaps'].values())) + "　砲門透光剩 " + str(k_['ports_see_through_remaining']) + "　砲門牆洞 " + str(k_['port_wall_holes'])]
    for i, s_ in enumerate(lines): g.text((ox + 1000, top2 + 10 + i * 24), s_, fill=ink, font=font(16 if i else 18))
    im.save(path, optimize=False)


if __name__ == '__main__':
    main()
