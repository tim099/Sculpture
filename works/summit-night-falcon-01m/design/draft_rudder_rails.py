# 新圖紙 06 舵、船頭欄杆、開窗（TASK-0529 階段六）：plan.json 的 rudder_rails ⇒ 清單、verify_rudder_rails.json。
# 用法：python -I -X utf8 -B draft_rudder_rails.py <design 資料夾>
#   · 現況照設計重建（階段二～五的清單；窗廊照固定框換回世界座標、左舷照 160 − y 鏡）—— 每一階段的結果帳都驗過 作品＝設計。
#   · 開窗（Tim 2026-10-13「窗戶部分可以直接開孔 這樣可以看到內構」）：
#       船尾窗 ⇒ 刻掉船殼裡的玻璃（後面本來就是艙房）；
#       窗廊 ⇒ 刻掉窗廊作品裡窗後面那一段（玻璃＋本體），船殼兩舷同一個 (x, z) 從外面刻到艙房空氣。
#   · 舵（子作品 rudder，at 0,0,0）：每一欄 (y, z)：前緣 ＝ 那一欄船殼最後面那格的前一格（貼著艉柱）；
#     只在船殼最後面那格還貼著艉柱的高度（counter 還沒往後伸出去）⇒ 頂端收在 counter 底下（憲法號同）。
#     寬度沿 z 從底寬收到頂寬；厚 3（|dy| ≤ 1），最後 thin 格收成 1；水線以下船底色。
#     pintle／gudgeon 帶：凸 1 格（|dy| 2），舵上到離後緣 2 格、船殼上往前 gud 格。
#   · 船頭欄杆（加進船頭作品）：每舷上下兩道（折線 (x, z)，半寬從船身線性收到 knee 旁），2 格高 1 格厚、6 連通；
#     支柱 head timbers 連上下兩道。全部避開現況的格（翅膀、knee、船殼）。
#   · 重跑逐位元組相同。
import sys, os, json, hashlib
import numpy as np
from scipy import ndimage

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from draft_lines import Hull, YC
from draft_decks import read_list

NX, NY, NZ = 384, 161, 90


def rebuild(d):
    """回傳 dict：作品名 → 世界座標色陣列（窗廊兩舷各一份）。"""
    W = {k: np.zeros((NX, NY, NZ), np.int16) for k in ('hull', 'main', 'quarter', 'head', 'stern_deco', 'gallery_S', 'gallery_P')}
    def app(tgt, o, origin=(0, 0, 0), mirror=False):
        a = read_list(os.path.join(d, o['file'])); p = a[:, :3] + np.asarray(origin)
        if mirror: p[:, 1] = 160 - p[:, 1]
        if o['op'] == 'carvevox':
            assert (tgt[tuple(p.T)] == a[:, 3]).all(); tgt[tuple(p.T)] = 0
        else:
            if not o.get('overwrite'): assert (tgt[tuple(p.T)] == 0).all()
            tgt[tuple(p.T)] = a[:, 3]
    for o in json.load(open(os.path.join(d, 'verify_hull.json'), encoding='utf-8'))['stamp_order']: app(W['hull'], dict(o, op='stampvox'))
    for o in json.load(open(os.path.join(d, 'verify_planking.json'), encoding='utf-8'))['stamp_order']: app(W['hull'], o)
    V = json.load(open(os.path.join(d, 'verify_decks.json'), encoding='utf-8'))['stamp_order']
    for sub, key in (('hull', 'hull'), ('main', 'main'), ('quarter', 'quarter')):
        for o in V[sub]: app(W[key], o)
    S = json.load(open(os.path.join(d, 'verify_stern_head.json'), encoding='utf-8'))['stamp_order']
    for o in S['hull']: app(W['hull'], o)
    for o in S['head']: app(W['head'], o)
    for o in S['stern_deco']: app(W['stern_deco'], o)
    for o in S['quarter_gallery']:
        app(W['gallery_S'], o, o['origin_world']); app(W['gallery_P'], o, o['origin_world'], mirror=True)
    return W


def lst(pts, col):
    if np.isscalar(col): col = np.full(len(pts), col)
    return ''.join(f"{a},{b},{c},{k}\n" for (a, b, c), k in zip(pts, col))


def connect6(cells):
    """把只靠邊角相接的連續格補成 6 連通（一次只動一軸）。"""
    out = []
    for c in cells:
        if out:
            p = list(out[-1])
            for ax in range(3):
                while p[ax] != c[ax]:
                    p[ax] += 1 if c[ax] > p[ax] else -1
                    out.append(tuple(p))
        else:
            out.append(tuple(c))
    return out


def main():
    d = sys.argv[1]
    plan = json.load(open(os.path.join(d, 'plan.json'), encoding='utf-8'))
    RR = plan['rudder_rails']; C = RR['colors']; H = Hull(plan)
    W = rebuild(d)
    occ = np.zeros((NX, NY, NZ), bool)
    for v in W.values(): occ |= v > 0
    X = np.arange(NX)[:, None, None]; Y = np.arange(NY)[None, :, None]; Z = np.arange(NZ)[None, None, :]
    x = np.arange(NX) + 0.5; z = np.arange(NZ) + 0.5
    hbv = H.hb(*np.meshgrid(x, z, indexing='ij'))
    vol = (~np.isnan(hbv))[:, None, :] & (np.abs(Y - YC) <= np.nan_to_num(hbv, nan=-1)[:, None, :])
    glass = plan['stern_head']['colors']['glass']
    # ── 開窗 ──
    hull = W['hull']
    stern_glass = (hull == glass)
    G = plan['stern_head']['quarter_gallery']; gx0 = G['x'][0]
    wins = []; xw = gx0 + G['pilaster']
    for i in range(G['n']):
        wins.append((xw, xw + G['win_w'] - 1)); xw += G['win_w'] + G['pilaster']
    gal_cut = np.zeros(occ.shape, bool); hull_cut = np.zeros(occ.shape, bool)
    gS = W['gallery_S']
    for (xa, xb) in wins:
        for zz in range(G['win_z'][0], G['win_z'][1] + 1):
            for xx in range(xa, xb + 1):
                if zz == G['win_z'][1] and xx in (xa, xb): continue         # 拱頂那一排只有中間兩格
                ys = np.nonzero(gS[xx, :, zz])[0]
                gal_cut[xx, ys, zz] = True                                   # 窗後面那一段窗廊（玻璃＋本體）
                # 船殼：右舷從最外那格往裡刻到艙房空氣（左舷照 160 − y）
                yh = np.nonzero(hull[xx, YC:, zz])[0]
                if len(yh) == 0: continue
                # 從最外那格往裡 depth 格以內的船殼格全刻（外板、肋骨、clamp）
                # 🩸 第一版刻到第一格空氣就停：外板與肋骨之間有縫，更裡面那道後甲板 clamp（z 38）沒刻到 ⇒ 拱頂那一格不透光
                yo = YC + yh.max()
                for yy in range(yo - G['open_depth'], yo + 1):
                    if hull[xx, yy, zz] > 0: hull_cut[xx, yy, zz] = True; hull_cut[xx, 160 - yy, zz] = True
    hull_carve = stern_glass | hull_cut
    gal_local_cut = np.argwhere(gal_cut) - np.asarray(G['frame_at'])
    # ── 舵 ──
    R = RR['rudder']; rud = np.zeros(occ.shape, np.int16); post_tol = R['post_tol']
    zmax_used = -1
    for zz in range(0, R['z_max'] + 1):
        t = min(1.0, zz / max(1, R['z_taper']))
        width = R['w_bottom'] + (R['w_top'] - R['w_bottom']) * t
        if zz > R['stock_from']: width = R['stock_w']
        # 前緣：中線那一欄現況最後面那格（含船尾裝飾的窗台線、簷線）的前一格
        # 🩸 第一版照「收在 counter 底下」（憲法號）—— 夜隼號是方艉、艉板跟艉柱幾乎平行，counter 幾乎不往外伸，停不下來（爬到 z 33）⇒ 改成方艉船的掛法：舵掛在艉板外、舵柱上到後甲板
        hx = np.nonzero(occ[:, YC, zz])[0]
        if len(hx) == 0: continue
        xf = hx.min()
        xa = int(round(xf - width)); zmax_used = zz
        for xx in range(xa, xf):
            for dy in (-1, 0, 1):
                thin = xx < xa + R['thin']
                if thin and dy != 0: continue
                rud[xx, YC + dy, zz] = C['bottom'] if zz <= plan['planking']['paint_waterline_z'] else C['black']
    # pintle／gudgeon 帶
    for zb in R['pintles']:
        hx = np.nonzero(hull[:, YC, zb])[0]; xf = hx.min()
        rx = np.nonzero(rud[:, YC, zb])[0]
        if len(rx) == 0: continue
        for xx in range(rx.min() + 2, xf + R['gud']):
            for sgn in (1, -1):
                yy = YC + sgn * 2
                if not occ[xx, yy, zb] and not vol[xx, yy, zb]: rud[xx, yy, zb] = C['iron']
    rud[occ & (rud > 0)] = 0
    # ── 船頭欄杆 ──
    HR = RR['head_rails']; rails = np.zeros(occ.shape, np.int16)
    def hull_hb_at(xx, zz):
        ys = np.nonzero(occ[xx, YC:, zz] & (W['hull'][xx, YC:, zz] > 0))[0]
        return int(ys.max()) if len(ys) else 0
    rail_paths = {}
    for r in HR['rails']:
        (x0, z0), (x1, z1) = r['from'], r['to']
        yb0 = hull_hb_at(x0, z0) + 1; yb1 = r['dy_end']
        pts = []
        n = 4 * (x1 - x0) + 1
        for i in range(n):
            u = i / (n - 1)
            xx = x0 + (x1 - x0) * u; zz = z0 + (z1 - z0) * u
            dy = yb0 + (yb1 - yb0) * u + r['bulge'] * np.sin(np.pi * u)
            xi_, zi_ = int(np.floor(xx)), int(round(zz))
            # 每一點至少在那個 (x, z) 現況最外那格的外面一格 —— 🩸 第一版只照線性內插，下道後端那幾格算進船身裡、被丟掉 ⇒ 後端 4 格斷開
            yo = np.nonzero(occ[xi_, YC:, zi_] | occ[xi_, YC:, zi_ + 1])[0]
            dy = max(dy, (yo.max() + 1) if len(yo) else 0)
            pts.append((xi_, int(round(YC + dy)), zi_))
        cells = connect6([p for i, p in enumerate(pts) if i == 0 or p != pts[i - 1]])
        rail_paths[r['name']] = cells
        for (xx, yy, zz) in cells:
            for k in range(r['tall']):
                for yv in (yy, 160 - yy):
                    rails[xx, yv, zz + k] = C['rail']
    for xt in HR['timbers']:
        up = [c for c in rail_paths['upper'] if c[0] == xt]; lo = [c for c in rail_paths['lower'] if c[0] == xt]
        if not up or not lo: continue
        yy = lo[0][1]; za = lo[0][2] + 2; zb = up[0][2] - 1
        for zz in range(za, zb + 1):
            for yv in (yy, 160 - yy): rails[xt, yv, zz] = C['timber']
    rails_dropped = int((occ & (rails > 0)).sum())
    dropped_where = {}
    for xx, yy, zz in np.argwhere(occ & (rails > 0)):
        who = [k for k, v in W.items() if v[xx, yy, zz] > 0][0]
        dropped_where[who] = dropped_where.get(who, 0) + 1
    rails[occ & (rails > 0)] = 0
    # ── 清單 ──
    order = {'hull': [], 'quarter_gallery': [], 'head': [], 'rudder': []}
    for sub in order:
        od = os.path.join(d, 'masks', 'rudder_rails', sub); os.makedirs(od, exist_ok=True)
        for f in os.listdir(od): os.remove(os.path.join(od, f))
    def emit(sub, name, pts, cols, op='stampvox', origin=(0, 0, 0)):
        if len(pts) == 0: return
        text = lst(np.asarray(pts), cols)
        fn = name + '.vox.txt'
        open(os.path.join(d, 'masks', 'rudder_rails', sub, fn), 'w', encoding='utf-8', newline='\n').write(text)
        order[sub].append({'name': name, 'op': op, 'file': 'masks/rudder_rails/' + sub + '/' + fn, 'at': [0, 0, 0], 'voxels': int(len(pts)),
                           'origin_world': list(origin), 'sha256': hashlib.sha256(text.encode('utf-8')).hexdigest()})
    hp = np.argwhere(hull_carve); emit('hull', 'windows_open_carve', hp, hull[tuple(hp.T)], op='carvevox')
    gp = np.argwhere(gal_cut); emit('quarter_gallery', 'windows_open_carve', gp - np.asarray(G['frame_at']), gS[tuple(gp.T)], op='carvevox', origin=tuple(G['frame_at']))
    rp = np.argwhere(rails > 0); emit('head', 'head_rails', rp, rails[tuple(rp.T)])
    up_ = np.argwhere(rud > 0); emit('rudder', 'rudder', up_, rud[tuple(up_.T)])
    # ── 讀數 ──
    after = occ.copy()
    after[hull_carve] = False; after[gal_cut] = False
    gal_cut_P = gal_cut[:, ::-1, :]; after[gal_cut_P & (W['gallery_P'] > 0)] = False
    newv = (rails > 0) | (rud > 0)
    allv = after | newv
    lab, nc = ndimage.label(allv)
    holes = int((ndimage.binary_fill_holes(allv) & ~allv).sum())
    # 開窗透光：每扇窗廊窗的每一格 (x, z)，右舷從 y 120 往裡走到艙房空氣（船殼體積裡的空格）之前都是空的
    see = 0; tot = 0
    for (xa, xb) in wins:
        for zz in range(G['win_z'][0], G['win_z'][1] + 1):
            for xx in range(xa, xb + 1):
                if zz == G['win_z'][1] and xx in (xa, xb): continue
                tot += 1
                see += int(not allv[xx, YC + 10:121, zz].any())               # 窗外 → 窗廊 → 船殼 → 艙房（|dy| 10）整條空
    Rj = {'stamp_order': order,
          'counts': {'hull_carve': int(hull_carve.sum()), 'hull_carve_stern_glass': int(stern_glass.sum()), 'hull_carve_gallery_tunnels': int(hull_cut.sum()),
                     'gallery_carve_one_side': int(gal_cut.sum()), 'head_rails': int((rails > 0).sum()), 'rudder': int((rud > 0).sum()),
                     'assembly_after': int(allv.sum())},
          'rudder': {'z_top': zmax_used, 'components': int(ndimage.label(rud > 0)[1])},
          'rails': {'components_with_head': int(ndimage.label((rails > 0) | (W['head'] > 0))[1]), 'cells_dropped_by_overlap': rails_dropped, 'dropped_hit': dropped_where},
          'structure': {'components_assembly': int(nc), 'enclosed_cavity_assembly': holes,
                        'mirror_shape_assembly': int((allv != allv[:, ::-1, :]).sum()),
                        'overlap_new_vs_now': int((newv & after).sum())},
          'gallery_windows_see_into_cabin': {'ok': see, 'of': tot}}
    with open(os.path.join(d, 'verify_rudder_rails.json'), 'w', encoding='utf-8', newline='\n') as fo:
        json.dump(Rj, fo, ensure_ascii=False, indent=2, sort_keys=True); fo.write('\n')
    print(json.dumps({k: Rj[k] for k in ('counts', 'rudder', 'rails', 'structure', 'gallery_windows_see_into_cabin')}, ensure_ascii=False, indent=1))


if __name__ == '__main__':
    main()
