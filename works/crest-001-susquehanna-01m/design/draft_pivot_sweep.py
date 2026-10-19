# 蘇士奎哈納號（crest-001）階段八之三：迴旋砲砲門之間的柱子拿掉（Tim 2026-10-20：「另外中間的竿子在砲旋轉時會穿透 應該可以移除?」）
#   draft_pivots.py 只在每個 ports 角度刻一個砲門（船頭 0／∓45°、船尾 −20／0／20°）；遊戲換砲門時砲照 rate 轉過中間的角度 ⇒ 砲管穿過兩個砲門之間的舷牆柱。
#   這一支：擺法照 verify_pivots.json（不重找位置），相鄰兩個砲門角度之間每 STEP° 照 draft_pivots.py 同一條規則刻 ——
#     砲管那一段（砲口往後 back 格到往前 front 格）水平 r 格內、砲口高度 ±4 的船殼格（mio.hull_now；已經刻掉的不算）⇒ 兩個砲門連成一個口子。
#   刻完再查：每個角度（含中間）模型的取樣點碰不碰現況（組裝件 links=all 的格 ＋ 模型外框；迴旋砲自己、別的迴旋砲不算）⇒ 讀數照列。
#   輸出：masks/guns/pivot_sweep_carve.vox.txt（船殼 carvevox，第 4 欄 ＝ 現在的色、守門）、verify_pivot_sweep.json
#   用法：python -I -X utf8 draft_pivot_sweep.py <design>
import sys, os, json, math
import numpy as np

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import hull_lines as HL
import mio as DB
import draft_guns as DG

NX, NY, NZ = 1300, 400, 260
STEP = 2.5                                                                # 設計決定：每 2.5°（砲管 r 4.5 格、離轉軸 ~20 格 ⇒ 相鄰兩刀重疊一大半，口子邊緣平順）
OFFS = np.array([[0.5, 0.5, 0.5]] + [[0.3 + 0.4 * (k & 1), 0.3 + 0.4 * ((k >> 1) & 1), 0.3 + 0.4 * ((k >> 2) & 1)] for k in range(8)])


def main():
    sys.stdout.reconfigure(encoding='utf-8')
    design = os.path.abspath(sys.argv[1])
    DG.WORKS = os.path.dirname(os.path.dirname(design))
    plan = HL.load_plan(design)
    GN = plan['guns']
    PP = GN['pivot_port']
    VP = json.load(open(os.path.join(design, 'verify_pivots.json'), encoding='utf-8'))
    T = GN['types']['pivot10']
    C = DB.export_list(T['work'], None)
    an = DG.anchors_of(T['work'])
    piv = np.array(VP['type']['pivot'], float)
    sc = VP['type']['scale']
    samp = (C[:, :3].astype(float)[:, None, :] + OFFS[None]).reshape(-1, 3)
    hull = {(x, y, z): c for x, y, z, c in DB.hull_now(design).tolist()}
    mask = os.path.join(design, 'masks', 'guns', 'pivot_sweep_carve.vox.txt')
    if os.path.exists(mask):                                              # mio.hull_now 已經扣掉這一支上次的輸出 ⇒ 加回來再算（重跑逐位元組相同）
        for x, y, z, c in np.loadtxt(mask, delimiter=',', comments='#', dtype=np.int32, ndmin=2, encoding='utf-8').reshape(-1, 4).tolist():
            hull[(x, y, z)] = c

    A = DB.export_list(DB.ASM, 'all')
    A = A[A[:, 2] < NZ]
    occ = np.zeros((NX, NY, NZ), bool)
    occ[A[:, 0], A[:, 1], A[:, 2]] = True
    for m in DG.parts_boxes():                                            # 模型外框（迴旋砲自己不算：下面每門照它在各角度的取樣點量）
        mt = m.get('meta') or {}
        if mt.get('kind') in DG.SKIP_KINDS or mt.get('mount') == 'pivot':
            continue
        b = m['box']
        occ[max(0, int(math.floor(b[0]))):int(math.ceil(b[3])), max(0, int(math.floor(b[1]))):int(math.ceil(b[4])),
            max(0, int(math.floor(b[2]))):min(NZ, int(math.ceil(b[5])))] = True

    def placed(at, rot, mir, a, c, pts):
        q = (pts - piv) * sc
        if mir:
            q[:, 1] = -q[:, 1]
        w = DG.rotz(q, rot) + np.asarray(at)
        w[:, 0] -= c[0]
        w[:, 1] -= c[1]
        w = DG.rotz(w, a)
        w[:, 0] += c[0]
        w[:, 1] += c[1]
        return w

    def pt(nm, at, rot, mir, a, c):
        return placed(at, rot, mir, a, c, np.array(an[nm], float)[None] + 0.5)[0]

    carve_all, rows = {}, []
    for r in VP['rows']:
        at, rot, mir, c = r['at'], r['rotate'][2], r['mirror'] == 'y', r['center'][:2]
        ports = sorted(float(v) for v in r['meta']['ports'].split(','))
        angs = sorted({round(a, 3) for a0, a1 in zip(ports, ports[1:]) for a in np.arange(a0, a1 + 1e-9, STEP)} | set(ports))
        mid = [a for a in angs if a not in ports]
        carve = {}
        for a in mid:
            mz, bz = pt('muzzle', at, rot, mir, a, c), pt('breech', at, rot, mir, a, c)
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
        for k in carve:
            occ[k] = False
        carve_all.update(carve)
        hits = {}
        for a in angs:                                                    # 刻完：每個角度（砲門 ＋ 中間）模型碰到的格
            i = np.floor(placed(at, rot, mir, a, c, samp)).astype(int)
            h = occ[i[:, 0], i[:, 1], i[:, 2]]
            if h.any():
                hits['%g' % a] = len({tuple(v) for v in i[h].tolist()})
        rows.append({'model': r['model'], 'ports': ports, 'mid': mid, 'carve_cells': len(carve), 'hits_after': hits,
                     'z': [min(k[2] for k in carve), max(k[2] for k in carve)] if carve else None})
    od = os.path.join(design, 'masks', 'guns')
    with open(os.path.join(od, 'pivot_sweep_carve.vox.txt'), 'w', encoding='utf-8', newline='\n') as f:
        f.write('# 蘇士奎哈納號 迴旋砲砲門之間的柱子（draft_pivot_sweep.py；船殼 carvevox，第 4 欄 ＝ 現在的色、守門）\n')
        for k in sorted(carve_all):
            f.write('%d,%d,%d,%d\n' % (k + (carve_all[k],)))
    out = {'note': 'draft_pivot_sweep.py（階段八之三）—— 現況 ＝ 組裝件 links=all（%d 格）＋ 模型外框（迴旋砲除外）；每 %g°' % (len(A), STEP),
           'rows': rows, 'carve_cells': len(carve_all)}
    with open(os.path.join(design, 'verify_pivot_sweep.json'), 'w', encoding='utf-8', newline='\n') as f:
        json.dump(out, f, ensure_ascii=False, indent=1, sort_keys=True)
        f.write('\n')
    print(json.dumps(out, ensure_ascii=False))


if __name__ == '__main__':
    main()
