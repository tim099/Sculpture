# 新圖紙 10 繫繩點（TASK-0529 階段十）：plan.json 的 belaying ⇒ fife rails＋bitts＋main sheet horse（一件、中線）、舷牆 pin rails（一舷＋鏡像）的清單與 pin 固定點、verify_belaying.json。
# 用法：python -I -X utf8 -B draft_belaying.py <design 資料夾>
#   · 現況照 nf_state.state_after('stage9')。甲板面 zdeck(x) ＝ 甲板作品在 dy＋10 那一欄最高格＋1（後甲板優先）。
#   · fife：桅孔 x 後 aft 格一根橫 rail（2 寬）、兩側 ±half_width（2 寬）往前到桅孔前 fwd 格接 bitts（3×3、甲板上 bitt_tall）；rail 甲板面 ＋above；
#     橫 rail 底下柱（兩角 2×2、中線 2×1）；bitts 頂下 2 格一根鐵 cross pin 前後各伸 1 格（比 rail 高一格）；pins：橫 rail 後排 dy ±2、±5（避開柱），側 rail 內排每 3 格。
#   · 舷牆 pin rails（右舷）：每一欄在 甲板面＋port_scan 那一層，只看船殼作品，從中線往外第一個實心 ＝ 舷牆內面；沒有 ＝ 砲門／開口。
#     連續 ≥ min_run 欄、甲板面不跳（相鄰差 ≤ 2）、內面 |dy| ≥ 15 的一段 ＝ 空檔；空檔裡從頭起每段 ≤ max_len、兩頭讓 end_gap 舖 rail。
#     rail：甲板面＋above（船腰 7、後甲板 6）、貼內面 deep 格；pins 在最裡那一排、每 pin_every 格；rail 兩頭底下各一格肘。
#   · pin：rail 上 up 格、下 down 格；固定點 ＝ pin 最上那一格。
#   · 每一格都要落在空的格上（assert）；重跑逐位元組相同。
import sys, os, json, hashlib
import numpy as np
from scipy import ndimage

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from draft_lines import YC
from nf_state import state_after, occupancy, NX, NY, NZ


def main():
    d = sys.argv[1]
    plan = json.load(open(os.path.join(d, 'plan.json'), encoding='utf-8'))
    B = plan['belaying']; C = B['colors']; M = plan['masts']
    W = state_after(d, 'stage9'); occ = occupancy(W)
    hull = W['hull'] > 0

    def zdeck(x):
        for k in ('quarter', 'main'):
            c = np.nonzero(W[k][x, YC + 10, :])[0]
            if len(c): return int(c.max()) + 1, k
        return None, None

    fife = {}; side = {}; anchors = {'fife': [], 'side': []}
    def put(D, c, col):
        assert not occ[c], ('撞到現況', c)
        assert c not in D or D[c] == col, ('自己重疊不同色', c)
        D[c] = col
    # ── fife rails ──
    F = B['fife']; P = B['pin']
    rails = {}
    for m in ('main', 'fore'):
        xm = M[m]['x']; zd, _ = zdeck(xm); zr = zd + F['above_deck']
        xa, xf, hw = xm - F['aft_of_mast'], xm + F['fwd_of_mast'], F['half_width']
        for x in range(xa, xa + F['rail_wide']):
            for dy in range(-hw, hw + 1): put(fife, (x, YC + dy, zr), C['rail'])
        for sg in (1, -1):
            for x in range(xa, xf):
                for dy in (hw - 1, hw): put(fife, (x, YC + sg * dy, zr), C['rail'])
            for x in range(xf, xf + F['bitt']):
                for dy in (hw - 1, hw, hw + 1):
                    for z in range(zdeck(x)[0], zd + F['bitt_tall']): put(fife, (x, YC + sg * dy, z), C['bitt'])   # 🩸 第一版從桅那一格的甲板面起 ⇒ 舷弧往前升、x 213 撞進甲板
            for x in (xf - 1, xf + F['bitt']):
                put(fife, (x, YC + sg * hw, zd + F['bitt_tall'] - 2), C['cross'])   # 🩸 第一版 −3 ＝ rail 那一層，後端那格落在側 rail 最後一格上
        for x in range(xa, xa + F['rail_wide']):
            for dy in (-hw, -hw + 1, 0, hw - 1, hw):
                for z in range(zdeck(x)[0], zr): put(fife, (x, YC + dy, z), C['bitt'])
        def pin(D, x, y, tag, L, owner):
            for z in list(range(zr + 1, zr + P['up'] + 1)) + list(range(zr - P['down'], zr)): put(D, (x, y, z), C['pin'])
            L.append((tag, (x, y, zr + P['up'])))
        pl = []
        for k, dy in enumerate((-5, -2, 2, 5)):                     # 🩸 第一版 0、±3、±6：rail 底下那兩格撞到柱（中線、±6）⇒ 避開柱
            pin(fife, xa, YC + dy, 'fife-%s-aft%d' % (m, k + 1), pl, 'fife')
        for sg, sd in ((1, 'S'), (-1, 'P')):
            for k, x in enumerate(range(xa + 3, xf - 1, F['pin_every'])):
                pin(fife, x, YC + sg * (hw - 1), 'fife-%s-%s%d' % (m, sd, k + 1), pl, 'fife')
        anchors['fife'] += [(n, c, 'pin') for n, c in pl]
        rails['fife-' + m] = {'deck_z': zd, 'rail_z': zr, 'x': [xa, xf + F['bitt'] - 1], 'pins': len(pl)}
    # ── horse ──
    Hs = B['horse']; zd, _ = zdeck(Hs['x']); zh = zd + Hs['above_deck']
    for dy in range(-Hs['half_width'], Hs['half_width'] + 1): put(fife, (Hs['x'], YC + dy, zh), C['horse'])
    for dy in (-Hs['half_width'], Hs['half_width']):
        for z in range(zd, zh): put(fife, (Hs['x'], YC + dy, z), C['horse'])
    anchors['fife'].append(('horse', (Hs['x'], YC, zh), 'horse'))
    rails['horse'] = {'deck_z': zd, 'z': zh}
    # ── 舷牆 pin rails（右舷）──
    S = B['side']
    occ_nc = np.zeros_like(occ)
    for k, v in W.items():
        if not k.startswith('channels'): occ_nc |= v > 0
    def inner(x, z):
        # 舷牆內面 ＝ 從中線往外第一個實心，而且那一格要是船殼作品的 ——
        # 🩸 第一版只看船殼：船尾 x 61 前面站著別的作品（船尾裝飾），rail 撞上去
        ys = np.nonzero(occ_nc[x, YC + 5:YC + 35, z])[0]
        if not len(ys): return None
        y = int(ys.min()) + 5
        return y if hull[x, YC + y, z] else None
    cols = []
    for x in range(55, 270):
        zd, k = zdeck(x)
        cols.append((x, zd, k, inner(x, zd + S['port_scan_above_deck']) if zd else None))
    runs = []; cur = []
    for c in cols:
        ok = c[3] is not None and c[3] >= 15 and (not cur or abs(c[1] - cur[-1][1]) <= 2)
        if ok: cur.append(c)
        else:
            if len(cur) >= S['min_run']: runs.append(cur)
            cur = [c] if (c[3] is not None and c[3] >= 15) else []
    if len(cur) >= S['min_run']: runs.append(cur)
    n = 0; gaps = []; skipped = []
    for run in runs:
        x0, x1 = run[0][0], run[-1][0]
        gaps.append([x0, x1])
        # 空檔平均切成 k 根（🩸 第一版從頭鋪、尾巴剩 5 格也鋪一根 ⇒ 1 根 pin 的短 rail）
        g = S['end_gap']; use = x1 - x0 + 1 - 2 * g
        k = -(-(use + 2 * g) // (S['max_len'] + 2 * g)); ln = (use - (k - 1) * 2 * g) // k
        for j in range(k):
            x = x0 + g + j * (ln + 2 * g); xe = x + ln - 1
            mid = (x + xe) // 2; zd, k = zdeck(mid)
            zr = zd + (S['qd_above_deck'] if k == 'quarter' else S['waist_above_deck'])
            n += 1; cells = 0
            iys = {xx: inner(xx, zr) for xx in range(x, xe + 1)}
            assert None not in iys.values(), ('rail 那一層沒有舷牆', x, xe, zr)
            # v2：pin 要在「rail 那一層到上面 4 層」最靠裡的內面再往裡一格 —— 🩸 v1 只量 rail 那一層：頂蓋（104）往裡伸 2 格，整根 rail 跟 pin 頭都縮在頂蓋底下，
            #     從船裡拉下來的繩在最後 1.2–1.7 格撞到頂蓋（9 條）⇒ rail 往裡延伸到 pin 那一排
            band = {xx: min(v for v in (inner(xx, z) for z in range(zr, zr + 5)) if v is not None) for xx in range(x, xe + 1)}
            for xx in range(x, xe + 1):
                # 🩸 第一版每一欄只貼自己那一欄的內面 2 格 ⇒ 舷牆內面相鄰差 2 格的地方，兩欄沒有共用的面（階梯病，第四次）⇒ 往裡補到鄰欄最深那一格
                lo = min(min(iys[v] for v in (xx - 1, xx, xx + 1) if v in iys) - S['deep'], band[xx] - 1)
                for dy in range(lo, iys[xx]): put(side, (xx, YC + dy, zr), C['rail']); cells += 1
            for xx in (x, xe):
                iy = min(inner(xx, zr - 1), iys[xx])   # 🩸 用 rail 那一層的內面 ⇒ 舷牆往下往內傾時撞進舷牆；只用下一層的 ⇒ 往外傾時肘離開 rail 自己一塊（5 個）⇒ 取淺的那個
                put(side, (xx, YC + iy - 1, zr - 1), C['rail'])
            pk = 0
            for xx in range(x + 1, xe, S['pin_every']):
                iy = min(inner(xx, zr) - S['deep'], band[xx] - 1) + S['deep']; y = YC + iy - S['deep']
                zs = list(range(zr + 1, zr + P['up'] + 1)) + list(range(zr - P['down'], zr))
                # 🩸 第一版沒檢查：船尾 x 61 的舷牆在 z 53 以上變厚（141 伸到 dy 19），pin 上半截撞進去 ⇒ 每一格都要在那一層內面的裡面，不行就整根不放
                if any((inner(xx, z) or 99) <= iy - S['deep'] for z in zs):
                    skipped.append([xx, y, zr]); continue
                for z in zs: put(side, (xx, y, z), C['pin'])
                pk += 1; anchors['side'].append(('pinrail-%d.pin-%d' % (n, pk), (xx, y, zr + P['up']), 'pin'))
            rails['pinrail-%d' % n] = {'x': [x, xe], 'deck_z': zd, 'deck': k, 'rail_z': zr, 'pins': pk}
    # ── 補空腔：rail 端、舷牆、頂蓋往裡伸的那一圈圍出 1–2 格的口袋 ⇒ 填 rail 色（只會在右舷；左舷由鏡像關聯跟著）──
    def cavity():
        v = occ.copy()
        for D in (fife, side): v[tuple(np.array(list(D)).T)] = True
        sp = np.array(list(side)); sp[:, 1] = 160 - sp[:, 1]; v[tuple(sp.T)] = True
        return np.argwhere(ndimage.binary_fill_holes(v) & ~v & ~(ndimage.binary_fill_holes(occ) & ~occ))
    filled = []
    for c in cavity():
        c = tuple(int(v) for v in c)
        if c[1] > YC: put(side, c, C['rail']); filled.append(list(c))
    assert len(cavity()) == 0, ('補完還有空腔', cavity().tolist())
    # ── 輸出 ──
    out = {}; so = {}
    for key, D, sub in (('fiferails', fife, B['fife']), ('belaying_side', side, B['side'])):
        a = np.array([[*k, v] for k, v in sorted(D.items())])
        fa = np.asarray(sub['frame_at']); fs = np.asarray(sub['frame_size'])
        loc = a[:, :3] - fa
        assert (loc >= 0).all() and (loc < fs).all(), (key, '出框', loc.min(0), loc.max(0))
        text = ''.join('%d,%d,%d,%d\n' % (r[0], r[1], r[2], r[3]) for r in np.column_stack([loc, a[:, 3]]))
        od = os.path.join(d, 'masks', 'belaying'); os.makedirs(od, exist_ok=True)
        open(os.path.join(od, key + '.vox.txt'), 'w', encoding='utf-8', newline='\n').write(text)
        so[key] = [{'name': key, 'op': 'stampvox', 'file': 'masks/belaying/%s.vox.txt' % key, 'at': [0, 0, 0], 'voxels': int(len(a)),
                    'origin_world': list(map(int, fa)), 'sha256': hashlib.sha256(text.encode('utf-8')).hexdigest()}]
        v1 = os.path.join(od, key + '_v1.vox.txt')
        if os.path.exists(v1):       # v1 已經落過格（凍結的紀錄）：重播 ＝ 貼 v1 → 刻 v1（帶原色）→ 貼 v2
            t1 = open(v1, encoding='utf-8').read(); n1 = sum(1 for l in t1.splitlines() if l.strip())
            h1 = hashlib.sha256(t1.encode('utf-8')).hexdigest()
            so[key] = [{'name': key + '_v1', 'op': 'stampvox', 'file': 'masks/belaying/%s_v1.vox.txt' % key, 'at': [0, 0, 0], 'voxels': n1, 'origin_world': list(map(int, fa)), 'sha256': h1},
                       {'name': key + '_v1_carve', 'op': 'carvevox', 'file': 'masks/belaying/%s_v1.vox.txt' % key, 'at': [0, 0, 0], 'voxels': n1, 'origin_world': list(map(int, fa)), 'sha256': h1}] + so[key]
        g = np.zeros((NX, NY, NZ), bool); g[tuple(a[:, :3].T)] = True
        out[key] = {'cells': int(len(a)), 'by_color': {str(int(c)): int((a[:, 3] == c).sum()) for c in np.unique(a[:, 3])},
                    'components_own': int(ndimage.label(g)[1]), 'local_min': loc.min(0).tolist(), 'local_max': loc.max(0).tolist()}
    # 結構：加進現況之後（右舷＋鏡像）
    newv = np.zeros((NX, NY, NZ), bool)
    for D in (fife, side): newv[tuple(np.array(list(D)).T)] = True
    sideP = np.zeros_like(newv); sideP[tuple(np.array(list(side)).T)] = True; sideP = sideP[:, ::-1, :]
    assert not (sideP & (occ | newv)).any(), '鏡像那一舷撞到'
    allv = occ | newv | sideP
    lab, nc = ndimage.label(allv)
    out['structure'] = {'components_assembly': int(nc), 'cavity_assembly': int((ndimage.binary_fill_holes(allv) & ~allv).sum()),
                        'mirror_shape_assembly': int((allv != allv[:, ::-1, :]).sum()), 'assembly_after': int(allv.sum())}
    fa = {'fife': B['fife']['frame_at'], 'side': B['side']['frame_at']}
    R = {'stamp_order': so, 'counts': out, 'rails': rails, 'bulwark_gaps': gaps, 'pins_skipped': skipped, 'cavity_filled': filled,
         'anchors': {k: [{'name': nm, 'world': list(c), 'at': [c[i] - fa[k][i] for i in range(3)], 'kind': kd} for nm, c, kd in L] for k, L in anchors.items()}}
    with open(os.path.join(d, 'verify_belaying.json'), 'w', encoding='utf-8', newline='\n') as fo:
        json.dump(R, fo, ensure_ascii=False, indent=2, sort_keys=True); fo.write('\n')
    print(json.dumps({'counts': out, 'rails': rails, 'gaps': gaps, 'pins_skipped': skipped, 'cavity_filled': filled, 'anchors': {k: len(v) for k, v in anchors.items()}}, ensure_ascii=False))


if __name__ == '__main__':
    main()
