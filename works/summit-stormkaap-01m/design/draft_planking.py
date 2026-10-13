# 新圖紙 03 外板、wales、塗裝（TASK-0547 階段三）：plan.json 的 lines ＋ framing ＋ planking ⇒ 清單、圖紙、verify_planking.json。
# 用法：python -I -X utf8 -B draft_planking.py <design 資料夾>
#   · 從夜隼號 draft_planking.py（TASK-0529 階段三）改：沒有插板槽；多了 wales（船殼外面一格、沿舷弧走的深色厚板帶）；
#     船底／藻帶／船身三段塗裝，藻帶上下緣照 x 起伏（鬼船：水線附近長滿東西，邊緣不會是直線）。
#   · 階段二的設計照 draft_hull.build 重算（作品＝那份設計，階段二結果帳已驗）。
#   · 外板 ＝ 船殼曲面那一層（深度 d ≤ √2）裡還沒被骨架、肋骨認領的格（夜隼號 🩸：只取 d ≤ 1 ⇒ 斜面上散成碎片）。
#   · wales ＝ 船殼外面、離船殼 ≤ √2 的格，在 sheer(x) ＋ [lo, hi) 那一段；不跑到艉板後面、艏柱前面。
#   · 舷牆頂蓋：肋骨層＋外板層每一欄最高那一格的上面一格（只取最高殼格在舷牆頂附近的欄）。
#   · 結構塗裝：骨架露在船外的那一層照同一套塗裝換色（stampvox overwrite=1，verify 記原色）。
#   · 漏水：船艙（船殼體積內、沒被佔）跟船外在 z < 下甲板 的範圍內 6 連通 ⇒ 不是 0 就停。
#   · 重跑逐位元組相同。
import sys, os, json, hashlib
import numpy as np
from PIL import Image, ImageDraw
from scipy import ndimage

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from draft_lines import font
from draft_hull import build, BACKBONE


def lst(pts, col):
    if np.isscalar(col): col = np.full(len(pts), col)
    return ''.join(f"{a},{b},{c},{k}\n" for (a, b, c), k in zip(pts, col))


def pal(k):
    return (int(((k >> 5) & 7) * 255 / 7), int(((k >> 2) & 7) * 255 / 7), int((k & 3) * 255 / 3))


def band_edges(Pl, x):
    """藻帶的下緣、上緣（z，連續值）：水線附近，照 x 起伏（幾個 sin 疊起來；決定論的，重跑一樣）。"""
    b = Pl['algae']
    x = np.asarray(x, float)
    lo = b['lo'] + sum(a * np.sin(x / w + p) for a, w, p in b['lo_wave'])
    hi = b['hi'] + sum(a * np.sin(x / w + p) for a, w, p in b['hi_wave'])
    return lo, hi


def main():
    d = sys.argv[1]
    plan = json.load(open(os.path.join(d, 'plan.json'), encoding='utf-8'))
    Pl = plan['planking']; C = Pl['colors']; Fc = plan['framing']['colors']
    H, solid, dist, own, names, layer, aft, dropped = build(plan)
    NX, NY, NZ, YC = H.NX, H.NY, H.NZ, H.YC
    NZ3 = NZ + 2
    pad = lambda a, v=False: np.concatenate([a, np.full(a.shape[:2] + (NZ3 - NZ,), v, a.dtype)], axis=2)
    solid, own, dist = pad(solid), pad(own, 0), pad(dist, 99.0)
    kind_bb = np.isin(own, [names.index(n) for n in BACKBONE])
    stage2 = own > 0
    col2 = np.zeros(own.shape, np.int16)
    col2[stage2] = Fc['frame']; col2[kind_bb] = Fc['backbone']
    X = np.arange(NX)[:, None, None]; Y = np.arange(NY)[None, :, None]; Z = np.arange(NZ3)[None, None, :]
    Zc = Z + 0.5

    # ── 塗裝：船底 → 藻帶 → 船身（藻帶上下緣照 x 起伏）──
    lo, hi = band_edges(Pl, np.arange(NX) + 0.5)
    LO = lo[:, None, None]; HI = hi[:, None, None]
    paint = np.where(Zc < LO, C['bottom'], np.where(Zc < HI, C['algae'], C['topsides'])).astype(np.int16) * np.ones(own.shape, np.int16)

    # ── 外板 ──
    plank = solid & (dist <= Pl['max_depth'] + 1e-9) & ~stage2

    # ── wales：船殼外面一格（離船殼 ≤ √2），沿舷弧 ──
    dout = ndimage.distance_transform_edt(~solid)
    sheer = H.sheer(np.arange(NX) + 0.5)[:, None, None]
    xr = X + 0.5
    inside_ends = (xr >= H.aft_limit(Zc)) & (xr <= H.stem_face(Zc))
    wales = np.zeros(own.shape, bool)
    wale_info = []
    for w in Pl['wales']:
        m = ~solid & (dout <= Pl['max_depth'] + 1e-9) & inside_ends & (Zc >= sheer + w['lo']) & (Zc < sheer + w['hi'])
        wales |= m
        wale_info.append({'name': w['name'], 'voxels': int(m.sum()), 'z_at_midship': [round(float(H.sheer(H.xm)) + w['lo'], 2), round(float(H.sheer(H.xm)) + w['hi'], 2)]})

    # ── 舷牆頂蓋 ──
    shell = (solid & (dist <= 1.0 + plan['framing']['moulded'])) | stage2 & ~kind_bb
    has = shell.any(axis=2)
    ztop = NZ3 - 1 - np.argmax(shell[:, :, ::-1], axis=2)
    rail = has & (ztop + 0.5 > H.top(np.arange(NX) + 0.5)[:, None] - 1.5)
    cap = np.zeros(own.shape, bool)
    xs, ys = np.nonzero(rail)
    cap[xs, ys, ztop[xs, ys] + 1] = True
    cap &= ~(solid & ~shell)
    cap &= ~(stage2 | plank | wales)

    # ── 結構塗裝：骨架露在船外的格 ──
    after = stage2 | plank | cap | wales
    outside = ~solid & ~after
    nb = np.zeros(own.shape, bool)
    for ax in range(3):
        for sh in (1, -1):
            nb |= np.roll(outside, sh, axis=ax)
    expo = kind_bb & nb & (paint != col2)

    # ── 漏水（下甲板以下）──
    zl = int(Pl['leak_below_z'])
    empty = ~after
    lab, n = ndimage.label(empty[:, :, :zl])
    out_lab = lab[0, 0, 0]
    hold = solid[:, :, :zl] & empty[:, :, :zl]
    leak = int((hold & (lab == out_lab)).sum())

    # ── 清單 ──
    od = os.path.join(d, 'masks', 'planking'); os.makedirs(od, exist_ok=True)
    for f in os.listdir(od): os.remove(os.path.join(od, f))
    order = []

    def emit(name, mask, colarr, overwrite=False, guard=None):
        pts = np.argwhere(mask)
        if len(pts) == 0: return
        text = lst(pts, colarr[tuple(pts.T)] if not np.isscalar(colarr) else colarr)
        fn = name + '.vox.txt'
        open(os.path.join(od, fn), 'w', encoding='utf-8', newline='\n').write(text)
        e = {'name': name, 'op': 'stampvox', 'file': 'masks/planking/' + fn, 'at': [0, 0, 0], 'expect_pixels': int(len(pts)),
             'sha256': hashlib.sha256(text.encode('utf-8')).hexdigest()}
        if overwrite: e['overwrite'] = 1; e['guard_colors'] = sorted(set(int(v) for v in guard[tuple(pts.T)]))
        order.append(e)

    cx = Pl['chunk_x']
    for x0 in range(0, NX, cx):
        emit('plank_x%03d' % x0, plank & (X >= x0) & (X < x0 + cx), paint)
    emit('wales', wales, C['wale'])
    emit('cap_rail', cap, C['cap'])
    emit('paint_structure', expo, paint, overwrite=True, guard=col2)

    # ── 讀數 ──
    final = np.zeros(own.shape, np.int16)
    final[stage2] = col2[stage2]
    final[plank] = paint[plank]; final[wales] = C['wale']; final[cap] = C['cap']; final[expo] = paint[expo]
    occ = final > 0
    labA, nA = ndimage.label(occ)
    holes = int((ndimage.binary_fill_holes(occ) & ~occ).sum())
    mirror = int((final != final[:, ::-1, :]).sum()) if NY == 2 * YC + 1 else -1
    R = {'stamp_order': order,
         'counts': {'plank': int(plank.sum()), 'wales': int(wales.sum()), 'cap': int(cap.sum()),
                    'paint_structure': int(expo.sum()), 'stage2': int(stage2.sum()), 'final_total': int(occ.sum())},
         'expected_total_after': int(stage2.sum() + plank.sum() + wales.sum() + cap.sum()),
         'wales': wale_info,
         'algae_band_z': {'lo': [round(float(lo.min()), 2), round(float(lo.max()), 2)], 'hi': [round(float(hi.min()), 2), round(float(hi.max()), 2)]},
         'structure': {'components_6conn': int(nA), 'enclosed_cavity_voxels': holes, 'mirror_diff': mirror},
         'leak': {'hold_cells_reached_from_outside': leak, 'z_below': zl, 'hold_cells': int(hold.sum())},
         'final_colors': {str(k): int((final == k).sum()) for k in sorted(set(final[occ].tolist()))}}
    if leak != 0:
        print('LEAK', leak); json.dump(R['leak'], sys.stdout); sys.exit(1)

    # ── 圖紙 ──
    S = 2.2; W, Hh = 1700, 1000
    im = Image.new('RGB', (W, Hh), (250, 248, 242)); g = ImageDraw.Draw(im)
    ink = (30, 30, 30)
    g.text((20, 12), "風暴角號 Stormkaap　新圖紙 03　外板、wales、塗裝（側面／船中剖面）　0.1 m／格　summit 2026-10-13　（設計）", fill=ink, font=font(24))
    top = 60; base = top + NZ3 * S; ox = 20
    g.text((ox, top - 4), "側面（從右舷看，最外面那一格的顏色；藍線 ＝ DWL）", fill=ink, font=font(18))
    half = final[:, YC:, :]
    hasv = (half > 0).any(axis=1)
    last = half.shape[1] - 1 - np.argmax(half[:, ::-1, :] > 0, axis=1)
    for xi, zi in np.argwhere(hasv):
        k = int(half[xi, last[xi, zi], zi])
        g.rectangle([ox + xi * S, base - (zi + 1) * S, ox + xi * S + S, base - zi * S], fill=pal(k))
    g.line([(ox, base - H.dwl * S), (ox + NX * S, base - H.dwl * S)], fill=(30, 90, 200), width=1)
    xm = int(H.xm); S2 = 3.0; cx_, b3 = 1350, Hh - 30
    g.text((cx_ - 260, b3 - 100 * S2 - 30), "x " + str(xm) + " 剖面（肋骨那一欄）", fill=ink, font=font(16))
    for yi, zi in np.argwhere(final[xm] > 0):
        k = int(final[xm, yi, zi])
        g.rectangle([cx_ + (yi - YC) * S2, b3 - (zi + 1) * S2, cx_ + (yi - YC + 1) * S2, b3 - zi * S2], fill=pal(k))
    c = R['counts']
    lines = ["讀數（verify_planking.json）",
             "外板 " + str(c['plank']) + "　wales " + str(c['wales']) + "　頂蓋 " + str(c['cap']) + "　結構塗裝 " + str(c['paint_structure']) + "（換色、不加格）",
             "完成後 " + str(c['final_total']) + " 格　6 連通元件 " + str(R['structure']['components_6conn']) + "　封閉空腔 " + str(R['structure']['enclosed_cavity_voxels']) + "　左右差 " + str(R['structure']['mirror_diff']),
             "漏水（z < " + str(zl) + "）：船艙 " + str(R['leak']['hold_cells']) + " 格裡被船外走到的 " + str(leak) + " 格",
             "藻帶 下緣 z " + str(R['algae_band_z']['lo']) + "、上緣 z " + str(R['algae_band_z']['hi'])]
    ty = base + 30
    for i, s_ in enumerate(lines): g.text((20, ty + i * 26), s_, fill=ink, font=font(18 if i else 22))
    for i, (lab_, k) in enumerate((("船底 " + str(C['bottom']), C['bottom']), ("藻帶 " + str(C['algae']), C['algae']), ("船身 " + str(C['topsides']), C['topsides']),
                                   ("wales／頂蓋 " + str(C['wale']), C['wale']), ("肋骨 " + str(Fc['frame']), Fc['frame']))):
        g.rectangle([20 + i * 170, ty + 150, 36 + i * 170, ty + 166], fill=pal(k), outline=ink); g.text((44 + i * 170, ty + 148), lab_, fill=ink, font=font(16))
    im.save(os.path.join(d, 'sheet03_planking_v1.png'), optimize=False)
    with open(os.path.join(d, 'verify_planking.json'), 'w', encoding='utf-8', newline='\n') as fo:
        json.dump(R, fo, ensure_ascii=False, indent=2, sort_keys=True); fo.write('\n')
    print(json.dumps({k: R[k] for k in ('counts', 'expected_total_after', 'wales', 'algae_band_z', 'structure', 'leak', 'final_colors')}, ensure_ascii=False, indent=1))


if __name__ == '__main__':
    main()
