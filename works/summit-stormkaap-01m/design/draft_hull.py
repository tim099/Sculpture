# 新圖紙 02 骨架與肋骨（TASK-0547 階段二）：plan.json 的 lines（含 upper）＋ framing ⇒ 每根木料一份格子清單、圖紙、verify_hull.json。
# 用法：python -I -X utf8 -B draft_hull.py <design 資料夾>
#   · 從夜隼號 draft_hull.py（TASK-0529 階段二）改：框與中線讀 plan.frame；艉柱只到翼艉板（荷蘭船的艉柱高 ＝ 翼艉板，Witsen）；圖紙比例照框縮。
#   · 船殼曲面照 draft_lines.Hull；格 k 的格心 k+0.5。
#   · 深度 d ＝ 格心到最近船外格的距離（EDT；頂面往上複製 ⇒ 舷牆頂不算船外，殼不長蓋子）。
#     d ≤ 1 ＝ 外板那一層（階段三才鋪，這裡只留空）；1 < d ≤ 1 + moulded ＝ 肋骨那一層。
#   · 骨架（實心木料，照順序認領、一格只屬一根）：龍骨 → 艏柱 → 艉柱 → deadwood（船殼半寬 ≤ deadwood_hb 的地方肋骨放不下，整個截面是木料）。
#   · 肋骨：x ≡ 船中站 (mod spacing) 那 sided 欄。
#   · 艉柱後面那一段（x < stern.x）不立肋骨，改成橫的 transom：z ≡ 翼艉板 (mod spacing) 那 sided 層，沿肋骨層繞過船尾、在中線釘上艉柱
#     （夜隼號 🩸：直的 counter timber 腳下沒有東西接 ⇒ 散件）。
#   · 每根木料只留跟整船主體 6 連通的那一塊；丟掉的格數照實記在 verify_hull.json（dropped_fragments）。
#   · 重跑逐位元組相同（清單照 x→y→z 排；PIL 不帶時間；json 排序鍵）。
import sys, os, json, hashlib
import numpy as np
from PIL import Image, ImageDraw
from scipy import ndimage

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from draft_lines import Hull, font


def build(plan):
    H = Hull(plan)
    NX, NY, NZ, YC = H.NX, H.NY, H.NZ, H.YC
    F = plan['framing']
    x = np.arange(NX) + 0.5; z = np.arange(NZ) + 0.5
    X, Z = np.meshgrid(x, z, indexing='ij')
    hb = H.hb(X, Z)                                                     # (NX, NZ)
    dy = np.abs(np.arange(NY) - YC).astype(float)
    hbn = np.nan_to_num(hb, nan=-1)
    solid = (hbn[:, None, :] >= 0) & (dy[None, :, None] <= hbn[:, None, :])
    top_ext = 8
    ext = np.concatenate([solid, np.zeros((NX, NY, top_ext), bool)], axis=2)
    colany = solid.any(axis=1)
    for xi in range(NX):
        if not colany[xi].any(): continue
        zt = np.where(colany[xi])[0].max()
        for k in range(1, top_ext + 1): ext[xi, :, zt + k] |= solid[xi, :, zt]
    d = ndimage.distance_transform_edt(ext)[:, :, :NZ]

    Y = np.arange(NY)[None, :, None]
    Xc = (np.arange(NX) + 0.5)[:, None, None]; Zc = (np.arange(NZ) + 0.5)[None, None, :]
    DY = np.abs(Y - YC)
    own = np.zeros((NX, NY, NZ), np.int16)
    names = [None]

    def claim(name, mask):
        m = mask & solid & (own == 0)
        names.append(name); own[m] = len(names) - 1
        return int(m.sum())

    bh = F['backbone_half']
    claim('keel', (Zc < H.rab) & (Xc >= H.kx0) & (Xc <= H.kx1) & (DY <= bh))
    # 艏柱：前緣往裡 sided 格，加上船頭底下那段弧往上 sided 格 —— 🩸 第一版只有前者：底部那段弧幾乎是水平的，
    # 每升一層前緣往前跳約 4 格 ⇒ z 0／1／2 那三小塊只靠邊角相接（艏柱 4 塊）
    zb = H.st_rz - H.st_rz * np.sqrt(np.clip(1 - ((Xc - H.st_x0) / H.st_rx) ** 2, 0, 1))
    claim('stem', (DY <= bh) & ((Xc >= H.stem_face(Zc) - H.st_sid) | ((Xc > H.kx1) & (Zc < zb + H.st_sid))))
    claim('sternpost', (DY <= bh) & (Xc <= H.post_face(Zc) + H.sp_sid) & (Zc <= H.trz + F['sternpost_above_wing']))
    dw = np.nan_to_num(hb, nan=99)[:, None, :] <= F['deadwood_hb']
    claim('deadwood_aft', dw & (Xc < H.xm))
    claim('deadwood_fwd', dw & (Xc >= H.xm))
    for dn, host in (('deadwood_aft', 'sternpost'), ('deadwood_fwd', 'stem')):
        m = own == names.index(dn)
        lab_, n_ = ndimage.label(m)
        if n_ > 1:
            sz = ndimage.sum(m, lab_, range(1, n_ + 1)); keep = int(np.argmax(sz)) + 1
            own[m & (lab_ != keep)] = names.index(host)

    layer = solid & (d > 1.0) & (d <= 1.0 + F['moulded']) & (own == 0)
    st_ = F['stern']
    aft = np.broadcast_to(np.arange(NX)[:, None, None] < st_['x'], (NX, NY, NZ))
    sp, sd, x0 = F['spacing'], F['sided'], F['station_x']
    xi = np.arange(NX)[:, None, None]
    for k in sorted(set(((np.arange(NX) - x0) // sp).tolist())):
        xs = x0 + k * sp
        m = layer & ~aft & (xi >= xs) & (xi < xs + sd)
        if m.any(): claim('f%+03d' % k, m)
    zi = np.arange(NZ)[None, None, :]
    for k in range(-20, 20):
        zs = H.trz + k * st_['spacing']
        m = layer & aft & (zi >= zs) & (zi < zs + st_['sided'])
        if m.any(): claim('tr%+03d' % k, m)
    lab, n = ndimage.label(own > 0)
    main = lab[tuple(np.argwhere(own == names.index('keel'))[0])]
    stray = (own > 0) & (lab != main)
    dropped = {}
    for i in np.unique(own[stray]):
        dropped[names[i]] = int((stray & (own == i)).sum())
    own[stray] = 0
    return H, solid, d, own, names, layer, aft, dropped


BACKBONE = ('keel', 'stem', 'sternpost', 'deadwood_aft', 'deadwood_fwd')


def piece_lists(own, names, colors):
    out = []
    for i in range(1, len(names)):
        pts = np.argwhere(own == i)
        if len(pts) == 0: continue
        kind = 'backbone' if names[i] in BACKBONE else ('counter' if names[i].startswith('tr') else 'frame')
        col = colors[kind]
        text = ''.join(f"{a},{b},{c},{col}\n" for a, b, c in pts)
        out.append((names[i], kind, pts, text))
    return out


def readings(H, solid, own, names, pieces, layer, dropped):
    allw = own > 0
    lab, ncomp = ndimage.label(allw)
    holes = int((ndimage.binary_fill_holes(allw) & ~allw).sum())
    mirror = int(((own > 0) != (own[:, ::-1, :] > 0)).sum()) if H.NY == 2 * H.YC + 1 else -1
    per = {}
    for name, kind, pts, text in pieces:
        m = np.zeros(own.shape, bool); m[tuple(pts.T)] = True
        _, nc = ndimage.label(m)
        per[name] = {'kind': kind, 'voxels': int(len(pts)), 'components': int(nc),
                     'x': [int(pts[:, 0].min()), int(pts[:, 0].max())], 'z': [int(pts[:, 2].min()), int(pts[:, 2].max())],
                     'sha256': hashlib.sha256(text.encode('utf-8')).hexdigest()}
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
        'structure': {'components_6conn': int(ncomp), 'enclosed_cavity_voxels': holes, 'mirror_diff': mirror,
                      'pieces_with_more_than_one_component': sorted(k for k, v in per.items() if v['components'] != 1),
                      'note_transom_halves': 'tr+NN 在中線被艉柱隔成左右兩半時，每根應為 2 塊（艉柱以上那幾層是整根）'},
        'frame_top_gap_vox': {'min': round(min(top_gap), 3), 'max': round(max(top_gap), 3)} if top_gap else None,
        'layer_unclaimed_between_stations': int((layer & (own == 0)).sum()),
        'solid_voxels_of_hull_volume': int(solid.sum()),
        'dropped_fragments': {'total': int(sum(dropped.values())), 'by_piece': dropped},
    }


def draw_sheet(H, R, own, names, plan, path):
    NX, NY, NZ, YC = H.NX, H.NY, H.NZ, H.YC
    S = 2.2; W, Hh = 1700, 1180
    im = Image.new('RGB', (W, Hh), (250, 248, 242)); g = ImageDraw.Draw(im)
    ink, grey = (30, 30, 30), (170, 170, 170)
    BB, FR, CT = (110, 70, 20), (180, 130, 80), (200, 90, 60)
    g.text((20, 12), "風暴角號 Stormkaap　新圖紙 02　骨架與肋骨（側面／俯視／船中剖面）　0.1 m／格　summit 2026-10-13　（設計）", fill=ink, font=font(24))
    kinds = np.zeros(own.shape, np.int8)
    for i in range(1, len(names)):
        n = names[i]
        kinds[own == i] = 1 if n in BACKBONE else (3 if n.startswith('tr') else 2)
    colmap = {1: BB, 2: FR, 3: CT}
    # 側面：從 +y（右舷）看，每一 (x,z) 取 y 最大那一格
    top = 60; base = top + NZ * S; ox = 20
    g.text((ox, top - 4), "側面（從右舷看；只畫 y " + str(YC) + " 以上那一半最外面的格）", fill=ink, font=font(18))
    half = kinds[:, YC:, :]
    has = half.any(axis=1)
    last = half.shape[1] - 1 - np.argmax(half[:, ::-1, :] > 0, axis=1)
    for xi_, zi_ in np.argwhere(has):
        k = half[xi_, last[xi_, zi_], zi_]
        x0, y0 = ox + xi_ * S, base - (zi_ + 1) * S
        g.rectangle([x0, y0, x0 + S, y0 + S], fill=colmap[int(k)])
    g.line([(ox, base - H.dwl * S), (ox + NX * S, base - H.dwl * S)], fill=(30, 90, 200), width=1)
    g.text((ox + 2, base - H.dwl * S + 2), "DWL", fill=(30, 90, 200), font=font(14))
    # 俯視：每一 (x,y) 最高那一格的種類（只畫船寬那一段）
    ys = np.where(kinds.any(axis=(0, 2)))[0]; y0_, y1_ = int(ys.min()), int(ys.max())
    top2 = base + 30; S3 = 2.2
    g.text((ox, top2), "俯視（每一欄最高那一格；肋骨每 " + str(plan['framing']['spacing']) + " 格一根、" + str(plan['framing']['sided']) + " 格寬）", fill=ink, font=font(18))
    has2 = kinds.any(axis=2)
    hi = NZ - 1 - np.argmax(kinds[:, :, ::-1] > 0, axis=2)
    for xi_, yi_ in np.argwhere(has2):
        k = kinds[xi_, yi_, hi[xi_, yi_]]
        x0, y0 = ox + xi_ * S, top2 + 30 + (yi_ - y0_) * S3
        g.rectangle([x0, y0, x0 + S, y0 + S3], fill=colmap[int(k)])
    # 船中剖面
    xm = int(H.xm); S2 = 3.0; cx = 1380; b3 = Hh - 30
    sl = own[xm]
    zt_sec = int(np.argwhere(sl > 0)[:, 1].max())
    g.text((cx - 300, b3 - zt_sec * S2 - 40), "x " + str(xm) + " 剖面（灰線 ＝ 船殼外緣；外板那一層階段三才鋪）", fill=ink, font=font(16))
    for yi_, zi_ in np.argwhere(sl > 0):
        k = kinds[xm, yi_, zi_]
        g.rectangle([cx + (yi_ - YC) * S2, b3 - (zi_ + 1) * S2, cx + (yi_ - YC + 1) * S2, b3 - zi_ * S2], fill=colmap[int(k)])
    zz = np.arange(NZ * 4) / 4 + 0.125
    hbz = H.hb(np.full(zz.shape, xm + 0.5), zz)
    for sgn in (-1, 1):
        seg = [(cx + (sgn * h + 0.5) * S2, b3 - z_ * S2) for h, z_ in zip(hbz, zz) if not np.isnan(h)]
        if len(seg) > 1: g.line(seg, fill=grey, width=1)
    tx, ty = 20, top2 + 30 + (y1_ - y0_ + 1) * S3 + 30
    c = R['counts']; s = R['structure']
    lines = ["讀數（verify_hull.json）",
             "骨架（龍骨／艏柱／艉柱／deadwood）" + str(c['backbone']) + " 格　肋骨 " + str(c['frames']) + " 格　transom " + str(c['counter']) + " 格",
             "合計 " + str(c['total']) + " 格、" + str(c['n_pieces']) + " 根　6 連通元件 " + str(s['components_6conn']) + "　封閉空腔 " + str(s['enclosed_cavity_voxels']) + " 格",
             "左右差 " + str(s['mirror_diff']) + "　不只一塊的木料 " + str(len(s['pieces_with_more_than_one_component'])) + " 根　丟掉的碎片 " + str(R['dropped_fragments']['total']) + " 格",
             "肋骨頂離舷牆頂 " + (str(R['frame_top_gap_vox']['min']) + "～" + str(R['frame_top_gap_vox']['max']) + " 格" if R['frame_top_gap_vox'] else "—")]
    for i, s_ in enumerate(lines): g.text((tx, ty + i * 26), s_, fill=ink, font=font(18 if i else 22))
    for i, (lab_, col) in enumerate((("骨架", BB), ("肋骨", FR), ("transom（艉柱後面，橫的）", CT))):
        g.rectangle([tx, ty + 140 + i * 24, tx + 16, ty + 156 + i * 24], fill=col); g.text((tx + 24, ty + 138 + i * 24), lab_, fill=ink, font=font(16))
    im.save(path, optimize=False)


def main():
    d = sys.argv[1]
    plan = json.load(open(os.path.join(d, 'plan.json'), encoding='utf-8'))
    H, solid, dist, own, names, layer, aft, dropped = build(plan)
    pieces = piece_lists(own, names, plan['framing']['colors'])
    R = readings(H, solid, own, names, pieces, layer, dropped)
    R['framing'] = {k: plan['framing'][k] for k in ('spacing', 'sided', 'moulded', 'station_x')}
    od = os.path.join(d, 'masks', 'frames'); os.makedirs(od, exist_ok=True)
    order = []
    for name, kind, pts, text in pieces:
        fn = name + '.vox.txt'
        with open(os.path.join(od, fn), 'w', encoding='utf-8', newline='\n') as fo:
            fo.write(text)
        order.append({'name': name, 'file': 'masks/frames/' + fn, 'at': [0, 0, 0], 'expect_pixels': int(len(pts))})
    R['stamp_order'] = order
    draw_sheet(H, R, own, names, plan, os.path.join(d, 'sheet02_frames_v1.png'))
    with open(os.path.join(d, 'verify_hull.json'), 'w', encoding='utf-8', newline='\n') as fo:
        json.dump(R, fo, ensure_ascii=False, indent=2, sort_keys=True); fo.write('\n')
    print(json.dumps({k: R[k] for k in ('counts', 'structure', 'frame_top_gap_vox', 'layer_unclaimed_between_stations', 'dropped_fragments')}, ensure_ascii=False, indent=1))


if __name__ == '__main__':
    main()
