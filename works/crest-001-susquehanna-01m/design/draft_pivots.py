# 蘇士奎哈納號（crest-001，TASK-0697）階段八之二：10 吋迴旋砲（模型 meta mount=pivot，造船規格 §4.5）—— crest-001 自己寫的（光榮號沒有迴旋砲）。
#   型、取樣、擺法跟 draft_guns.py 同一套（模型座標 world ＝ at ＋ Rz(rotate) · mirror_y( scale · (Q − pivot) )）；
#   遊戲的轉軸 ＝ breech ＋ 砲軸 × meta pivot（Blockside 21_gunnery.js gunMountInit），z ＝ 模型外框底；每個 ports 角度繞它轉。
#   找位置：plan.guns.pivots 每一門在 x × |dy| 的範圍裡逐格試 ——
#     ① 每個角度砲口都在船殼外形外面（draft_lines.hull_volume 的實心）；② 每個角度的砲門 ＝ 砲管那一段水平 r 格內、砲口高度 ±4 的船殼格（之後刻掉）；
#     ③ 扣掉全部砲門之後，每個角度模型的取樣點都不碰現況（組裝件 links=all＋模型外框＋先放好的砲）；④ 輪子著地（不夠 ⇒ 墊木，同 draft_guns）。
#     條件：輪子著地 ≥ 75%（墊木補剩下的）；排序：刻的格少 ＞ 輪子著地多 ＞ 離中線近。
#   輸出：masks/guns/pivot_carve.vox.txt（船殼刻，第 4 欄 ＝ 現在的色、守門）、verify_pivots.json（每門 host、at、rotate、mirror、scale、pivot、meta、讀數）
#   用法：python -I -X utf8 draft_pivots.py <design> [--base=<快取.npz>]
import sys, os, json, math
import numpy as np

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import hull_lines as HL
import layout as LY
import mio as DB
import draft_guns as DG
from draft_lines import hull_volume

NX, NY, NZ = 1300, 400, 260


def main():
    sys.stdout.reconfigure(encoding='utf-8')
    design = os.path.abspath(sys.argv[1])
    DG.WORKS = os.path.dirname(os.path.dirname(design))
    cache = next((a.split('=', 1)[1] for a in sys.argv[2:] if a.startswith('--base=')), None)
    plan = HL.load_plan(design)
    L = HL.Lines(plan)
    GN = plan['guns']
    PP = GN['pivot_port']
    YC = plan['space']['yc']
    T = GN['types']['pivot10']
    C = DB.export_list(T['work'], None)
    an = DG.anchors_of(T['work'])
    ax0 = an['muzzle'][0] + 0.5
    bot = C[C[:, 2] == 0]
    piv = np.array([ax0, float(bot[:, 1].max() + 1), 0.0])
    cells = C[:, :3].astype(float)
    offs = np.array([[0.5, 0.5, 0.5]] + [[0.3 + 0.4 * (k & 1), 0.3 + 0.4 * ((k >> 1) & 1), 0.3 + 0.4 * ((k >> 2) & 1)] for k in range(8)])
    samp = (cells[:, None, :] + offs[None]).reshape(-1, 3)
    bs = np.array([[x + ox, y + oy, 0.0] for x, y, _ in bot[:, :3] for ox in (0.3, 0.7) for oy in (0.3, 0.7)])
    sc = T['scale']
    k_piv = round(13.5 * sc, 3)                     # 轉軸：breech 往砲口 13.5 格（來源座標；砲架中段）× scale
    # 現況
    if cache and os.path.exists(cache):
        z = np.load(cache)
        occ = z['occ']
    else:
        A = DB.export_list(DB.ASM, 'all')
        A = A[A[:, 2] < NZ]
        occ = np.zeros((NX, NY, NZ), bool)
        occ[A[:, 0], A[:, 1], A[:, 2]] = True
        if cache:
            np.savez_compressed(cache, occ=occ)
    for m in DG.parts_boxes():
        if (m.get('meta') or {}).get('kind') in DG.SKIP_KINDS:
            continue
        b = m['box']
        occ[max(0, int(math.floor(b[0]))):int(math.ceil(b[3])), max(0, int(math.floor(b[1]))):int(math.ceil(b[4])),
            max(0, int(math.floor(b[2]))):min(NZ, int(math.ceil(b[5])))] = True
    hull = {}
    for x, y, z, c in DB.hull_now(design).tolist():
        hull[(x, y, z)] = c
    pc = os.path.join(design, 'masks', 'ports', 'carve.vox.txt')                  # 舷側砲門（階段二的清單；還沒刻也當作已經刻了）
    for x, y, z, c in np.loadtxt(pc, delimiter=',', comments='#', dtype=np.int32, ndmin=2, encoding='utf-8').tolist():
        occ[x, y, z] = False
    x0, ylo, S, _dist = hull_volume(L, plan)                                         # 船殼外形（實心）⇒ 砲口在不在外面
    def outside(p):
        i, j, k = int(math.floor(p[0])) - x0, int(math.floor(p[1])) - ylo, int(math.floor(p[2]))
        if i < 0 or j < 0 or i >= S.shape[0] or j >= S.shape[1] or k >= S.shape[2]:
            return True
        return not S[i, j, k]
    G = json.load(open(os.path.join(design, 'verify_guns.json'), encoding='utf-8')) if os.path.exists(os.path.join(design, 'verify_guns.json')) else {'rows': []}
    for r in G['rows']:                                                              # 舷側砲（先放的）也是障礙
        tp = GN['types'][r['type']]
        Cc = DB.export_list(tp['work'], None) if False else None
    rows, carve_all = [], {}

    def placed(at, rot, mir, a=0.0, c=None, pts=samp):
        q = (pts - piv) * sc
        if mir:
            q[:, 1] = -q[:, 1]
        w = DG.rotz(q, rot) + np.asarray(at)
        if a:
            w2 = w.copy()
            w2[:, 0], w2[:, 1] = w[:, 0] - c[0], w[:, 1] - c[1]
            w2 = DG.rotz(w2, a)
            w2[:, 0] += c[0]
            w2[:, 1] += c[1]
            w = w2
        return w

    def pt(nm, at, rot, mir, a=0.0, c=None):
        return placed(at, rot, mir, a, c, np.array(an[nm], float)[None] + 0.5)[0]
    for spec in GN['pivots']:
        side = {'S': 1, 'P': -1, 'C': 1}[spec['side']]
        mir = spec['side'] == 'P'
        rot0 = spec['rot0']
        best = None
        dys = range(spec['dy'][0], spec['dy'][1] + 1) if spec['dy'][1] > spec['dy'][0] else [spec['dy'][0]]
        for x in range(spec['x'][0], spec['x'][1] + 1, 2):
            for dy in dys:
                cx, cy = x + 0.5, YC + 0.5 + side * dy
                zd = float(LY.deck_z(plan, 'gun', x)) + 1
                # 先用 at ＝ 0 算出 breech、砲軸 ⇒ 轉軸 ＝ (cx, cy)：at 平移到讓轉軸落在 (cx, cy, zd)
                b0, m0 = pt('breech', [0, 0, zd], rot0, mir), pt('muzzle', [0, 0, zd], rot0, mir)
                axv = (m0 - b0) / np.linalg.norm(m0 - b0)
                c0 = b0 + axv * k_piv
                at = np.array([cx - c0[0], cy - c0[1], zd])
                cc = (cx, cy)
                carve, ok, sup_min = {}, True, 1.0
                for a in spec['ports']:
                    mz = pt('muzzle', at, rot0, mir, a, cc)
                    if not outside(mz):
                        ok = False
                        break
                    bz = pt('breech', at, rot0, mir, a, cc)
                    d = (mz - bz) / np.linalg.norm(mz - bz)
                    za, zb = int(round(mz[2])) - 4, int(round(mz[2])) + 4
                    for t in np.arange(-PP['back'], PP['front'] + 0.01, 0.5):
                        p = mz + d * t
                        for ix in range(int(p[0]) - 6, int(p[0]) + 7):
                            for iy in range(int(p[1]) - 6, int(p[1]) + 7):
                                if (ix + 0.5 - p[0]) ** 2 + (iy + 0.5 - p[1]) ** 2 > PP['r'] ** 2:
                                    continue
                                for iz in range(za, zb + 1):
                                    if (ix, iy, iz) in hull:
                                        carve[(ix, iy, iz)] = hull[(ix, iy, iz)]
                if not ok:
                    continue
                for a in spec['ports']:
                    W = placed(at, rot0, mir, a, cc)
                    i = np.floor(W).astype(int)
                    if ((i[:, 0] < 0) | (i[:, 1] < 0) | (i[:, 2] < 0) | (i[:, 2] >= NZ)).any():
                        ok = False
                        break
                    h = occ[i[:, 0], i[:, 1], i[:, 2]]
                    if h.any():
                        hk = {tuple(v) for v in i[h].tolist()}
                        if not hk <= set(carve):
                            ok = False
                            break
                    B = placed(at, rot0, mir, a, cc, bs)
                    ib = np.floor(B).astype(int)
                    sup = float(occ[ib[:, 0], ib[:, 1], ib[:, 2] - 1].mean())
                    sup_min = min(sup_min, sup)
                if not ok or sup_min < 0.75:                                       # 輪子要著地（v1 沒這條 ⇒ 船頭那兩門找到「浮在船外」的解）
                    continue
                key = (len(carve), -round(sup_min, 2), dy)
                if best is None or key < best[0]:
                    best = (key, {'at': [round(float(v), 3) for v in at], 'center': [cx, cy, zd], 'carve': carve, 'support_min': round(sup_min, 3),
                                  'muzzles': [[round(float(v), 2) for v in pt('muzzle', at, rot0, mir, a, cc)] for a in spec['ports']]})
        if best is None:
            rows.append({'model': spec['name'], 'fail': True})
            continue
        b = best[1]
        carve_all.update(b['carve'])
        for (ix, iy, iz) in b['carve']:
            occ[ix, iy, iz] = False
        for a in spec['ports']:                                                      # 放好的砲（每個角度）也算障礙
            i = np.floor(placed(b['at'], rot0, mir, a, (b['center'][0], b['center'][1]))).astype(int)
            occ[i[:, 0], i[:, 1], i[:, 2]] = True
        meta = {'kind': 'gun', 'gun': T['code'], 'mount': 'pivot', 'ports': ','.join('%g' % a for a in spec['ports']), 'pivot': k_piv, 'rate': 12,
                'side': spec['side'], 'deck': 'gun'}
        rows.append({'model': spec['name'], 'host_link': '甲板-gun', 'host_work': 'crest-001-susquehanna-01m-deck-gun', 'type': 'pivot10', 'work': T['work'],
                     'at': b['at'], 'rotate': [0, 0, rot0], 'mirror': 'y' if mir else 'none', 'scale': sc, 'pivot': piv.tolist(), 'meta': meta,
                     'center': b['center'], 'muzzles': b['muzzles'], 'carve_cells': len(b['carve']), 'support_min': b['support_min'], 'src': spec['src']})
    od = os.path.join(design, 'masks', 'guns')
    os.makedirs(od, exist_ok=True)
    with open(os.path.join(od, 'pivot_carve.vox.txt'), 'w', encoding='utf-8', newline='\n') as f:
        f.write('# 蘇士奎哈納號 迴旋砲的砲門（draft_pivots.py；船殼 carvevox，第 4 欄 ＝ 現在的色、守門）\n')
        for k in sorted(carve_all):
            f.write('%d,%d,%d,%d\n' % (k + (carve_all[k],)))
    out = {'note': 'draft_pivots.py（階段八之二）', 'type': {'work': T['work'], 'code': T['code'], 'scale': sc, 'pivot': piv.tolist(), 'k_pivot': k_piv},
           'rows': rows, 'carve_cells': len(carve_all)}
    with open(os.path.join(design, 'verify_pivots.json'), 'w', encoding='utf-8', newline='\n') as f:
        json.dump(out, f, ensure_ascii=False, indent=1, sort_keys=True)
        f.write('\n')
    print(json.dumps({'rows': [{k: r.get(k) for k in ('model', 'center', 'muzzles', 'carve_cells', 'support_min', 'fail')} for r in rows], 'carve': len(carve_all)}, ensure_ascii=False))


if __name__ == '__main__':
    main()
