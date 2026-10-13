# 新圖紙 02 骨架與肋骨（TASK-0529 階段二）：plan.json 的 lines（含 upper）＋ framing ⇒ 每根木料一份格子清單、圖紙、verify_hull.json。
# 用法：python -I -X utf8 -B draft_hull.py <design 資料夾>
#   · 船殼曲面照 draft_lines.Hull（v2：舷牆頂、後甲板）；格 k 的格心 k+0.5。
#   · 深度 d ＝ 格心到最近船外格的距離（EDT；頂面往上複製 ⇒ 舷牆頂不算船外，殼不長蓋子）。
#     d ≤ 1 ＝ 外板那一層（階段三才鋪，這裡只留空）；1 < d ≤ 1 + moulded ＝ 肋骨那一層。
#   · 骨架（實心木料，照順序認領、一格只屬一根）：龍骨 → 艏柱 → 艉柱 → deadwood（船殼半寬 ≤ deadwood_hb 的地方肋骨放不下，整個截面是木料）。
#   · 肋骨：x ≡ 船中站 (mod spacing) 那 sided 欄。
#   · 艉柱後面那一段（x < stern.x）不立肋骨，改成橫的 transom：z ≡ 翼艉板 (mod spacing) 那 sided 層，沿肋骨層繞過船尾、在中線釘上艉柱。
#     🩸 第一版用直的 counter timber：船尾在翼艉板那層只有艉柱那麼寬，counter timber 腳下沒有東西接 ⇒ 散件 878 格。
#   · 每根木料只留跟整船主體 6 連通的那一塊；丟掉的格數照實記在 verify_hull.json（dropped_fragments）。
#   · 重跑逐位元組相同（清單照 x→y→z 排；PIL 不帶時間；json 排序鍵）。
import sys, os, json, math, hashlib
import numpy as np
from PIL import Image, ImageDraw
from scipy import ndimage

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from draft_lines import Hull, YC, font

NX, NY, NZ = 384, 161, 72


def build(plan):
    H = Hull(plan)
    F = plan['framing']
    x = np.arange(NX) + 0.5; z = np.arange(NZ) + 0.5
    X, Z = np.meshgrid(x, z, indexing='ij')
    hb = H.hb(X, Z)                                                     # (NX, NZ)
    dy = np.abs(np.arange(NY) - YC).astype(float)
    hbn = np.nan_to_num(hb, nan=-1)
    solid = (hbn[:, None, :] >= 0) & (dy[None, :, None] <= hbn[:, None, :])
    # 頂面開口：每一欄最上面那一層往上複製（跟 draft_lines 殼的預覽同一招）
    top_ext = 8
    ext = np.concatenate([solid, np.zeros((NX, NY, top_ext), bool)], axis=2)
    for xi in range(NX):
        col = solid[xi]
        if not col.any(): continue
        zt = np.where(col.any(axis=0))[0].max()
        for k in range(1, top_ext + 1):
            if zt + k < NZ + top_ext: ext[xi, :, zt + k] |= col[:, zt]
    d = ndimage.distance_transform_edt(ext)[:, :, :NZ]

    Y = np.arange(NY)[None, :, None]
    Xc = (np.arange(NX) + 0.5)[:, None, None]; Zc = (np.arange(NZ) + 0.5)[None, None, :]
    DY = np.abs(Y - YC)
    own = np.zeros((NX, NY, NZ), np.int16)        # 0 空；>0 木料編號
    names = [None]

    def claim(name, mask):
        m = mask & solid & (own == 0)
        names.append(name); own[m] = len(names) - 1
        return int(m.sum())

    # ── 骨架 ──
    claim('keel', (Zc < H.rab) & (Xc >= H.kx0) & (Xc <= H.kx1) & (DY <= F['backbone_half']))
    claim('stem', (DY <= F['backbone_half']) & (Xc >= H.stem_face(Zc) - H.st_sid))
    claim('sternpost', (DY <= F['backbone_half']) & (Xc <= H.post_face(Zc) + H.sp_sid) & (Zc <= H.deck_side(Xc)))
    dw = np.nan_to_num(hb, nan=99)[:, None, :] <= F['deadwood_hb']
    claim('deadwood_aft', dw & (Xc < H.xm))
    claim('deadwood_fwd', dw & (Xc >= H.xm))
    # deadwood 只留最大那一塊；其餘碎片貼在艏柱內側／艉柱兩旁（apron 那一帶）⇒ 歸給隔壁那根柱子
    for dn, host in (('deadwood_aft', 'sternpost'), ('deadwood_fwd', 'stem')):
        m = own == names.index(dn)
        lab_, n_ = ndimage.label(m)
        if n_ > 1:
            sz = ndimage.sum(m, lab_, range(1, n_ + 1)); keep = int(np.argmax(sz)) + 1
            own[m & (lab_ != keep)] = names.index(host)

    # ── 肋骨層 ──
    layer = solid & (d > 1.0) & (d <= 1.0 + F['moulded']) & (own == 0)
    # 艉柱後面那一段 —— 用座標判斷、兩舷對稱（⛔ 不用 EDT 的最近點方向：平手時兩舷挑的不同 ⇒ 第一版左右差 360 格）
    st_ = F['stern']
    aft = np.broadcast_to(np.arange(NX)[:, None, None] < st_['x'], (NX, NY, NZ))
    sp, sd, x0 = F['spacing'], F['sided'], F['station_x']
    xi = np.arange(NX)[:, None, None]
    in_frame = ((xi - x0) % sp) < sd
    stations = sorted(set(((np.arange(NX) - x0) // sp).tolist()))
    for k in stations:
        xs = x0 + k * sp
        m = layer & ~aft & (xi >= xs) & (xi < xs + sd)
        if m.any(): claim('f%+03d' % k, m)
    zi = np.arange(NZ)[None, None, :]
    for k in range(-10, 20):
        zs = H.trz + k * st_['spacing']
        m = layer & aft & (zi >= zs) & (zi < zs + st_['sided'])
        if m.any(): claim('tr%+03d' % k, m)
    # 只留跟主體相連的那一塊（主體 ＝ 含龍骨的那個 6 連通元件）
    lab, n = ndimage.label(own > 0)
    main = lab[tuple(np.argwhere(own == names.index('keel'))[0])]
    stray = (own > 0) & (lab != main)
    dropped = {}
    for i in np.unique(own[stray]):
        dropped[names[i]] = int((stray & (own == i)).sum())
    own[stray] = 0
    return H, solid, d, own, names, layer, aft, dropped


def piece_lists(own, names, colors):
    out = []
    for i in range(1, len(names)):
        pts = np.argwhere(own == i)
        if len(pts) == 0: continue
        kind = 'backbone' if names[i] in ('keel', 'stem', 'sternpost', 'deadwood_aft', 'deadwood_fwd') else ('counter' if names[i].startswith('tr') else 'frame')
        col = colors[kind]
        text = ''.join(f"{a},{b},{c},{col}\n" for a, b, c in pts)
        out.append((names[i], kind, pts, text))
    return out


def readings(H, solid, own, names, pieces, layer, aft, plan, dropped):
    F = plan['framing']
    allw = own > 0
    lab, ncomp = ndimage.label(allw)
    holes = int((ndimage.binary_fill_holes(allw) & ~allw).sum())
    mirror = int(((own > 0) != (own[:, ::-1, :] > 0)).sum())
    per = {}
    for name, kind, pts, text in pieces:
        m = np.zeros(own.shape, bool); m[tuple(pts.T)] = True
        _, nc = ndimage.label(m)
        per[name] = {'kind': kind, 'voxels': int(len(pts)), 'components': int(nc),
                     'x': [int(pts[:, 0].min()), int(pts[:, 0].max())], 'z': [int(pts[:, 2].min()), int(pts[:, 2].max())],
                     'sha256': hashlib.sha256(text.encode('utf-8')).hexdigest()}
    # 肋骨層有多少格沒被任何一根認領（站與站之間的空檔，照設計是空的）
    frames_total = sum(v['voxels'] for v in per.values() if v['kind'] != 'backbone')
    # 每根肋骨的頂：離舷牆頂差多少（格心 z 最大值 vs top(x)）
    top_gap = []
    for name, v in per.items():
        if v['kind'] != 'frame': continue
        pts = np.argwhere(own == names.index(name))
        for xx in np.unique(pts[:, 0]):
            zt = pts[pts[:, 0] == xx][:, 2].max() + 0.5
            top_gap.append(float(H.top(xx + 0.5)) - zt)
    return {
        'pieces': per,
        'counts': {'backbone': sum(v['voxels'] for v in per.values() if v['kind'] == 'backbone'),
                   'frames': sum(v['voxels'] for v in per.values() if v['kind'] == 'frame'),
                   'counter': sum(v['voxels'] for v in per.values() if v['kind'] == 'counter'),
                   'total': int(allw.sum()), 'n_pieces': len(per)},
        'structure': {'components_6conn': int(ncomp), 'enclosed_cavity_voxels': holes, 'mirror_diff_y_vs_160_minus_y': mirror,
                      'pieces_with_more_than_one_component': sorted(k for k, v in per.items() if v['components'] != 1),
        'note_transom_halves': 'tr+NN 在中線被艉柱隔成左右兩半（兩半各自釘在艉柱上），每根應為 2 塊'},
        'frame_top_gap_vox': {'min': round(min(top_gap), 3), 'max': round(max(top_gap), 3)} if top_gap else None,
        'layer_unclaimed_between_stations': int((layer & (own == 0)).sum()),
        'solid_voxels_of_hull_volume': int(solid.sum()),
        'dropped_fragments': {'total': int(sum(dropped.values())), 'by_piece': dropped},
    }


def draw_sheet(H, R, own, names, path):
    S = 4; W, Hh = 1700, 1080
    im = Image.new('RGB', (W, Hh), (250, 248, 242)); g = ImageDraw.Draw(im)
    ink, grey = (30, 30, 30), (170, 170, 170)
    BB, FR, CT = (110, 70, 20), (180, 130, 80), (200, 90, 60)
    g.text((20, 12), "夜隼號 Night Falcon　新圖紙 02　骨架與肋骨（側面／俯視／船中剖面）　0.1 m／格　summit 2026-10-13　（設計）", fill=ink, font=font(24))
    kinds = np.zeros(own.shape, np.int8)
    for i in range(1, len(names)):
        n = names[i]
        kinds[own == i] = 1 if n in ('keel', 'stem', 'sternpost', 'deadwood_aft', 'deadwood_fwd') else (3 if n.startswith('tr') else 2)
    colmap = {1: BB, 2: FR, 3: CT}
    # 側面：從 +y（右舷）看，每一 (x,z) 取 y 最大那一格
    top = 60; base = top + 72 * S; ox = 40
    g.text((ox, top - 4), "側面（從右舷看；只畫 y 80 以上那一半最外面的格）", fill=ink, font=font(18))
    half = kinds[:, YC:, :]
    has = half.any(axis=1)
    last = half.shape[1] - 1 - np.argmax(half[:, ::-1, :] > 0, axis=1)
    for xi_, zi_ in np.argwhere(has):
        k = half[xi_, last[xi_, zi_], zi_]
        x0, y0 = ox + xi_ * S, base - (zi_ + 1) * S
        g.rectangle([x0, y0, x0 + S - 1, y0 + S - 1], fill=colmap[int(k)])
    g.line([(ox, base - H.dwl * S), (ox + NX * S, base - H.dwl * S)], fill=(30, 90, 200), width=1)
    g.text((ox + 2, base - H.dwl * S + 2), "DWL", fill=(30, 90, 200), font=font(14))
    # 俯視：從上往下，每一 (x,y) 最高那一格的種類
    top2 = base + 40; S3 = 2.5
    g.text((ox, top2), "俯視（每一欄最高那一格；肋骨每 " + str(R['framing']['spacing']) + " 格一根、" + str(R['framing']['sided']) + " 格寬）", fill=ink, font=font(18))
    has2 = kinds.any(axis=2)
    hi = NZ - 1 - np.argmax(kinds[:, :, ::-1] > 0, axis=2)
    for xi_, yi_ in np.argwhere(has2):
        k = kinds[xi_, yi_, hi[xi_, yi_]]
        x0, y0 = ox + xi_ * S, top2 + 30 + yi_ * S3
        g.rectangle([x0, y0, x0 + S - 1, y0 + S3], fill=colmap[int(k)])
    # 船中剖面
    xm = int(H.xm); S2 = 6; cx = 1250; b3 = 1050
    g.text((cx - 250, b3 - 50 * S2 - 34), "x " + str(xm) + " 剖面（肋骨那一欄；灰 ＝ 外板那一層，階段三才鋪）", fill=ink, font=font(18))
    sl = own[xm]
    for yi_ in range(NY):
        for zi_ in range(NZ):
            if sl[yi_, zi_] > 0:
                k = kinds[xm, yi_, zi_]
                g.rectangle([cx + (yi_ - YC) * S2, b3 - (zi_ + 1) * S2, cx + (yi_ - YC + 1) * S2 - 1, b3 - zi_ * S2 - 1], fill=colmap[int(k)])
    hbz = H.hb(np.full(NZ * 4, xm + 0.5), np.arange(NZ * 4) / 4 + 0.125)
    for sgn in (-1, 1):
        seg = [(cx + (sgn * h + 0.5) * S2, b3 - zz * S2) for h, zz in zip(hbz, np.arange(NZ * 4) / 4 + 0.125) if not np.isnan(h)]
        if len(seg) > 1: g.line(seg, fill=grey, width=1)
    # 圖例＋讀數
    tx, ty = 40, 780
    c = R['counts']; s = R['structure']
    lines = ["讀數（verify_hull.json）",
             "骨架（龍骨／艏柱／艉柱／deadwood）" + str(c['backbone']) + " 格　肋骨 " + str(c['frames']) + " 格　transom " + str(c['counter']) + " 格　合計 " + str(c['total']) + " 格、" + str(c['n_pieces']) + " 根",
             "6 連通元件 " + str(s['components_6conn']) + "　封閉空腔 " + str(s['enclosed_cavity_voxels']) + " 格　左右差 " + str(s['mirror_diff_y_vs_160_minus_y']) + "　不只一塊的木料 " + str(len(s['pieces_with_more_than_one_component'])) + " 根",
             "肋骨頂離舷牆頂 " + (str(R['frame_top_gap_vox']['min']) + "～" + str(R['frame_top_gap_vox']['max']) + " 格" if R['frame_top_gap_vox'] else "—")]
    for i, s_ in enumerate(lines): g.text((tx, ty + i * 26), s_, fill=ink, font=font(18 if i else 24))
    for i, (lab_, col) in enumerate((("骨架", BB), ("肋骨", FR), ("transom（艉柱後面，橫的）", CT))):
        g.rectangle([tx, ty + 120 + i * 24, tx + 16, ty + 136 + i * 24], fill=col); g.text((tx + 24, ty + 118 + i * 24), lab_, fill=ink, font=font(16))
    im.save(path, optimize=False)


def main():
    d = sys.argv[1]
    plan = json.load(open(os.path.join(d, 'plan.json'), encoding='utf-8'))
    H, solid, dist, own, names, layer, aft, dropped = build(plan)
    pieces = piece_lists(own, names, plan['framing']['colors'])
    R = readings(H, solid, own, names, pieces, layer, aft, plan, dropped)
    R['framing'] = {k: plan['framing'][k] for k in ('spacing', 'sided', 'moulded', 'station_x')}
    od = os.path.join(d, 'masks', 'frames'); os.makedirs(od, exist_ok=True)
    order = []
    for name, kind, pts, text in pieces:
        fn = name + '.vox.txt'
        with open(os.path.join(od, fn), 'w', encoding='utf-8', newline='\n') as fo:
            fo.write(text)
        order.append({'name': name, 'file': 'masks/frames/' + fn, 'at': [0, 0, 0], 'expect_pixels': int(len(pts))})
    R['stamp_order'] = order
    draw_sheet(H, R, own, names, os.path.join(d, 'sheet02_frames_v1.png'))
    with open(os.path.join(d, 'verify_hull.json'), 'w', encoding='utf-8', newline='\n') as fo:
        json.dump(R, fo, ensure_ascii=False, indent=2, sort_keys=True); fo.write('\n')
    print(json.dumps({k: R[k] for k in ('counts', 'structure', 'frame_top_gap_vox', 'layer_unclaimed_between_stations', 'dropped_fragments')}, ensure_ascii=False, indent=1))


if __name__ == '__main__':
    main()
