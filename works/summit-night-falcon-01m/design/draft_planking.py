# 新圖紙 03 外板、插板槽、塗裝（TASK-0529 階段三）：plan.json 的 lines（v2）＋ framing ＋ planking ⇒ 清單、圖紙、verify_planking.json。
# 用法：python -I -X utf8 -B draft_planking.py <design 資料夾>
#   · 階段二的設計照 draft_hull.build 重算（作品＝那份設計，階段二結果帳已驗）。
#   · 插板槽（中線、穿過龍骨）：先刻 —— 龍骨與肋骨在 y 80、x 槽範圍、z 0..槽頂 的格（carvevox，帶顏色守門）；
#     再貼槽壁（y 79／81）、兩端的 headledge（槽前後各一欄）、槽頂蓋。槽裡通海（從龍骨底的開口），⛔ 不算船艙。
#   · 外板 ＝ 船殼曲面那一層（深度 d ≤ max_depth ＝ √2）裡還沒被骨架、肋骨認領的格；照 x 每 chunk_x 格一份清單。z ≤ 水線那幾層塗船底色、以上塗船身色。
#   · 舷牆頂蓋（cap rail）：肋骨層＋外板層每一欄最高那一格的上面一格（蓋在肋骨頂與外板頂上）。
#   · 結構塗裝：骨架露在船外的那一層（船外 ＝ 船殼體積外的空格＋槽裡）照同一條水線上色（stampvox overwrite=1，清單帶原色守門 —— 見 verify）。
#   · 漏水：船艙（船殼體積內、沒被任何東西佔、不是槽裡）跟船外在 z < 主甲板最低點的範圍內 6 連通 ⇒ 不是 0 就停。
#   · 重跑逐位元組相同。
import sys, os, json, hashlib
import numpy as np
from PIL import Image, ImageDraw
from scipy import ndimage

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from draft_lines import YC, font
from draft_hull import build, NX, NY, NZ

NZ3 = NZ + 2      # 舷牆頂蓋會比船殼頂高一格


def lst(pts, col):
    if np.isscalar(col): col = np.full(len(pts), col)
    return ''.join(f"{a},{b},{c},{k}\n" for (a, b, c), k in zip(pts, col))


def main():
    d = sys.argv[1]
    plan = json.load(open(os.path.join(d, 'plan.json'), encoding='utf-8'))
    Pl = plan['planking']; C = Pl['colors']; Fc = plan['framing']['colors']
    H, solid, dist, own, names, layer, aft, dropped = build(plan)
    pad = lambda a, v=False: np.concatenate([a, np.full(a.shape[:2] + (NZ3 - NZ,), v, a.dtype)], axis=2)
    solid, own, dist = pad(solid), pad(own, 0), pad(dist, 99.0)
    kind_bb = np.isin(own, [names.index(n) for n in ('keel', 'stem', 'sternpost', 'deadwood_aft', 'deadwood_fwd')])
    stage2 = own > 0
    col2 = np.zeros(own.shape, np.int16)
    col2[stage2] = Fc['frame']; col2[kind_bb] = Fc['backbone']
    X = np.arange(NX)[:, None, None]; Y = np.arange(NY)[None, :, None]; Z = np.arange(NZ3)[None, None, :]

    # ── 插板槽 ──
    T = Pl['trunk']; tx0, tx1, tz = T['x'][0], T['x'][1], T['top_z']
    inx = (X >= tx0) & (X <= tx1)
    slot = inx & (Y == YC) & (Z <= tz)                                   # 槽裡（通海）
    carve = slot & stage2                                                 # 要刻掉的階段二格（龍骨、底肋）
    walls = inx & ((Y == YC - 1) | (Y == YC + 1)) & (Z >= H.rab) & (Z <= tz) & ~stage2
    heads = ((X == tx0 - 1) | (X == tx1 + 1)) & (np.abs(Y - YC) <= 1) & (Z >= H.rab) & (Z <= tz) & ~stage2
    capT = (X >= tx0 - 1) & (X <= tx1 + 1) & (np.abs(Y - YC) <= 1) & (Z == tz + 1) & ~stage2
    trunk = walls | heads | capT

    # ── 外板 ──
    # 外板：深度 ≤ √2（跟船外共用一個面，或只隔一條邊）—— 🩸 第一版只取 d ≤ 1，斜面上變階梯、58 塊 1–4 格的碎片只靠邊角相接（不漏水，但 6 連通是散的）
    plank = solid & (dist <= Pl['max_depth'] + 1e-9) & ~stage2 & ~slot & ~trunk
    wl = Pl['paint_waterline_z']
    pcol = np.where(Z <= wl, C['bottom'], C['topsides']).astype(np.int16) * np.ones(own.shape, np.int16)
    # ── 舷牆頂蓋：肋骨層＋外板層每一欄最高那一格的上面一格 ──
    shell = (solid & (dist <= 1.0 + plan['framing']['moulded'])) | stage2 & ~kind_bb
    has = shell.any(axis=2)
    ztop = NZ3 - 1 - np.argmax(shell[:, :, ::-1], axis=2)
    cap = np.zeros(own.shape, bool)
    # 只蓋舷牆頂那一圈：那一欄最高的殼格要到舷牆頂附近（⛔ 船艙中間那幾欄的最高殼格是船底，蓋上去會變成艙底一塊板）
    rail = has & (ztop + 0.5 > H.top(np.arange(NX) + 0.5)[:, None] - 1.5)
    xs, ys = np.nonzero(rail)
    cap[xs, ys, ztop[xs, ys] + 1] = True
    cap &= ~(solid & ~shell)
    occupied = stage2 & ~carve | trunk | plank
    cap &= ~occupied

    # ── 結構塗裝：骨架露在船外的格 ──
    after = (stage2 & ~carve) | trunk | plank | cap
    outside = (~solid & ~after) | slot
    nb = np.zeros(own.shape, bool)
    for ax in range(3):
        for sh in (1, -1):
            nb |= np.roll(outside, sh, axis=ax)
    expo = kind_bb & ~carve & nb
    ecol = np.where(Z <= wl, C['bottom'], C['topsides']).astype(np.int16) * np.ones(own.shape, np.int16)

    # ── 漏水 ──
    zl = int(np.floor(H.sh['z_low']))                                   # 主甲板最低點以下才量（上面是開的）
    empty = ~after
    lab, n = ndimage.label(empty[:, :, :zl])
    out_lab = lab[0, 0, 0]
    hold = solid[:, :, :zl] & empty[:, :, :zl] & ~slot[:, :, :zl]
    leak = int((hold & (lab == out_lab)).sum())

    # ── 清單 ──
    od = os.path.join(d, 'masks', 'planking'); os.makedirs(od, exist_ok=True)
    for f in os.listdir(od): os.remove(os.path.join(od, f))
    order = []

    def emit(name, mask, colarr, op='stampvox', guard=None, overwrite=False):
        pts = np.argwhere(mask)
        if len(pts) == 0: return
        if op == 'carvevox': text = lst(pts, guard[tuple(pts.T)])
        else: text = lst(pts, colarr[tuple(pts.T)] if not np.isscalar(colarr) else colarr)
        fn = name + '.vox.txt'
        open(os.path.join(od, fn), 'w', encoding='utf-8', newline='\n').write(text)
        e = {'name': name, 'op': op, 'file': 'masks/planking/' + fn, 'at': [0, 0, 0], 'voxels': int(len(pts)),
             'sha256': hashlib.sha256(text.encode('utf-8')).hexdigest()}
        if overwrite: e['overwrite'] = 1; e['guard_colors'] = sorted(set(int(v) for v in guard[tuple(pts.T)]))
        order.append(e)

    emit('trunk_slot_carve', carve, None, op='carvevox', guard=col2)
    emit('trunk', trunk, T['color'])
    cx = Pl['chunk_x']
    for x0 in range(0, NX, cx):
        emit('plank_x%03d' % x0, plank & (X >= x0) & (X < x0 + cx), pcol)
    emit('cap_rail', cap, C['cap'])
    emit('paint_structure', expo, ecol, guard=col2, overwrite=True)

    # ── 讀數 ──
    final = np.zeros(own.shape, np.int16)
    final[stage2 & ~carve] = col2[stage2 & ~carve]
    final[trunk] = T['color']; final[plank] = pcol[plank]; final[cap] = C['cap']; final[expo] = ecol[expo]
    occ = final > 0
    labA, nA = ndimage.label(occ)
    holes = int((ndimage.binary_fill_holes(occ) & ~occ).sum())
    mirror = int((final != final[:, ::-1, :]).sum())
    R = {'stamp_order': order,
         'counts': {'carve': int(carve.sum()), 'trunk': int(trunk.sum()), 'plank': int(plank.sum()), 'cap': int(cap.sum()),
                    'paint_structure': int(expo.sum()), 'stage2': int(stage2.sum()), 'final_total': int(occ.sum())},
         'expected_total_after': int(stage2.sum() - carve.sum() + trunk.sum() + plank.sum() + cap.sum()),
         'structure': {'components_6conn': int(nA), 'enclosed_cavity_voxels': holes, 'mirror_diff_y_vs_160_minus_y': mirror},
         'leak': {'hold_cells_reached_from_outside': leak, 'z_below': zl, 'hold_cells': int(hold.sum())},
         'final_colors': {str(k): int((final == k).sum()) for k in sorted(set(final[occ].tolist()))},
         'trunk': {'x': [tx0, tx1], 'top_z': tz, 'slot_cells_open_to_sea': int(slot.sum())}}
    if leak != 0:
        print('LEAK', leak); json.dump(R['leak'], sys.stdout); sys.exit(1)

    # ── 圖紙 ──
    pal = lambda k: (int(((k >> 5) & 7) * 255 / 7), int(((k >> 2) & 7) * 255 / 7), int((k & 3) * 255 / 3))
    S = 4; W, Hh = 1700, 980
    im = Image.new('RGB', (W, Hh), (250, 248, 242)); g = ImageDraw.Draw(im)
    ink = (30, 30, 30)
    g.text((20, 12), "夜隼號 Night Falcon　新圖紙 03　外板、插板槽、塗裝（側面／船中剖面／槽）　0.1 m／格　summit 2026-10-13　（設計）", fill=ink, font=font(24))
    top = 60; base = top + 74 * S; ox = 40
    g.text((ox, top - 4), "側面（從右舷看，最外面那一格的顏色）", fill=ink, font=font(18))
    half = final[:, YC:, :]
    hasv = (half > 0).any(axis=1)
    last = half.shape[1] - 1 - np.argmax(half[:, ::-1, :] > 0, axis=1)
    for xi, zi in np.argwhere(hasv):
        k = int(half[xi, last[xi, zi], zi])
        g.rectangle([ox + xi * S, base - (zi + 1) * S, ox + xi * S + S - 1, base - zi * S - 1], fill=pal(k))
    g.line([(ox, base - (H.dwl) * S), (ox + NX * S, base - H.dwl * S)], fill=(30, 90, 200), width=1)
    # 船中剖面
    xm = int(H.xm); S2 = 6; cx_, b3 = 1250, 950
    g.text((cx_ - 250, b3 - 50 * S2 - 34), "x " + str(xm) + " 剖面（肋骨那一欄；插板槽在中線）", fill=ink, font=font(18))
    for yi in range(NY):
        for zi in range(NZ3):
            k = int(final[xm, yi, zi])
            if k: g.rectangle([cx_ + (yi - YC) * S2, b3 - (zi + 1) * S2, cx_ + (yi - YC + 1) * S2 - 1, b3 - zi * S2 - 1], fill=pal(k))
    # 槽：中線縱剖面（y 80）
    g.text((40, 420), "中線縱剖面 y 80（x " + str(tx0 - 20) + "–" + str(tx1 + 20) + "）：龍骨上的槽、槽兩端、槽頂", fill=ink, font=font(18))
    S4 = 6; ox4, b4 = 40, 600
    for xi in range(tx0 - 20, tx1 + 21):
        for zi in range(0, tz + 6):
            k = int(final[xi, YC, zi])
            if k: g.rectangle([ox4 + (xi - tx0 + 20) * S4, b4 - (zi + 1) * S4, ox4 + (xi - tx0 + 21) * S4 - 1, b4 - zi * S4 - 1], fill=pal(k))
            elif slot[xi, YC, zi]: g.rectangle([ox4 + (xi - tx0 + 20) * S4, b4 - (zi + 1) * S4, ox4 + (xi - tx0 + 21) * S4 - 1, b4 - zi * S4 - 1], fill=(160, 200, 230))
    g.text((ox4, b4 + 8), "淺藍 ＝ 槽裡（通海）", fill=(80, 120, 160), font=font(14))
    c = R['counts']
    lines = ["讀數（verify_planking.json）",
             "刻（槽）" + str(c['carve']) + "　槽 " + str(c['trunk']) + "　外板 " + str(c['plank']) + "　頂蓋 " + str(c['cap']) + "　結構塗裝 " + str(c['paint_structure']) + "（換色、不加格）",
             "完成後 " + str(c['final_total']) + " 格　6 連通元件 " + str(R['structure']['components_6conn']) + "　封閉空腔 " + str(R['structure']['enclosed_cavity_voxels']) + "　左右差 " + str(R['structure']['mirror_diff_y_vs_160_minus_y']),
             "漏水（z < " + str(zl) + "）：船艙 " + str(R['leak']['hold_cells']) + " 格裡被船外走到的 " + str(leak) + " 格"]
    for i, s_ in enumerate(lines): g.text((40, 700 + i * 26), s_, fill=ink, font=font(18 if i else 24))
    for i, (lab_, k) in enumerate((("船底 " + str(C['bottom']), C['bottom']), ("船身 " + str(C['topsides']), C['topsides']), ("頂蓋／槽 " + str(C['cap']), C['cap']), ("肋骨 " + str(Fc['frame']), Fc['frame']))):
        g.rectangle([40 + i * 180, 820, 56 + i * 180, 836], fill=pal(k), outline=ink); g.text((64 + i * 180, 818), lab_, fill=ink, font=font(16))
    im.save(os.path.join(d, 'sheet03_planking_v1.png'), optimize=False)
    with open(os.path.join(d, 'verify_planking.json'), 'w', encoding='utf-8', newline='\n') as fo:
        json.dump(R, fo, ensure_ascii=False, indent=2, sort_keys=True); fo.write('\n')
    print(json.dumps({k: R[k] for k in ('counts', 'expected_total_after', 'structure', 'leak', 'final_colors', 'trunk')}, ensure_ascii=False, indent=1))


if __name__ == '__main__':
    main()
