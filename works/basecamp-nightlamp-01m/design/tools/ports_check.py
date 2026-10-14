# 階段八 砲門的讀數（跟 draft_ports.py 不共用量法）
# 用法：python -I ports_check.py <design 資料夾> <刻之前的 export list> <刻之後的 export list> [--shift-x N] [--no-lining]
#   · 結果帳：刻之後 ＝ 刻之前 − carve ＋ lining（逐格含顏色）。
#   · 開口邊 vs 原圖讀數：每舷、每個砲門，在刻之後的作品裡找「從船外沿 y 一路看到中線附近都沒有實心」的 (x, z)（透光），
#     取它的外框，跟讀數框（線心換成格）比：格的邊 − 讀數，四邊各一個數。--shift-x 把讀數往 +X 偏 N 格（反向對照）。
#   · 牆不能有洞：每一格刻掉的格，往 ±x、±z 的鄰格要嘛也刻掉了、要嘛是實心（看不進肋骨之間的縫）。--no-lining 假裝框沒補（反向對照）。
#   · 刻掉的格原本的顏色只准是黑外板 36、肋骨 141。
import sys, os, json
import numpy as np


def read_list(p):
    out = {}
    for ln in open(p, encoding='utf-8'):
        ln = ln.strip()
        if ln and ln[0] != '#':
            x, y, z, c = (int(v) for v in ln.split(',')[:4])
            out[(x, y, z)] = c
    return out


def main():
    a = sys.argv[1:]
    shift = 0.0
    if '--shift-x' in a:
        i = a.index('--shift-x')
        shift = float(a[i + 1])
        del a[i:i + 2]
    no_lining = '--no-lining' in a
    a = [v for v in a if v != '--no-lining']
    design, before_p, after_p = a
    plan = json.load(open(os.path.join(design, 'plan.json'), encoding='utf-8'))
    Sc = plan['scale']
    cpm = json.load(open(os.path.join(design, 'verify_lines.json'), encoding='utf-8'))['k'] * Sc['cells_per_m']   # 底圖 1 m 幾格
    src = json.load(open(os.path.join(design, plan['gunports']['source']), encoding='utf-8'))
    carve = read_list(os.path.join(design, 'masks', 'ports', 'carve.vox.txt'))
    lining = read_list(os.path.join(design, 'masks', 'ports', 'lining.vox.txt'))
    before = read_list(before_p)
    after = read_list(after_p)
    if no_lining:
        after = {c: v for c, v in after.items() if c not in lining}
    out = {'cpm': cpm, 'shift_x': shift, 'no_lining': no_lining}

    # 結果帳
    exp = {c: v for c, v in before.items() if c not in carve}
    exp.update(lining)
    out['ledger'] = {'after_cells': len(after), 'expected_cells': len(exp),
                     'missing': sum(1 for c in exp if c not in after),
                     'extra': sum(1 for c in after if c not in exp),
                     'color_diff': sum(1 for c, v in exp.items() if c in after and after[c] != v)}
    out['carve_guard'] = {'colors_before': {str(k): v for k, v in zip(*np.unique([before.get(c, -1) for c in carve], return_counts=True))},
                          'color_mismatch_vs_list': sum(1 for c, v in carve.items() if before.get(c) != v)}

    # 開口邊（透光）
    occ = set(after)
    YC = 160
    res = []
    worst = 0.0
    for p in src['ports']:
        Xa = Sc['X_of_x0'] + p['x_aft'] * cpm + shift
        Xf = Sc['X_of_x0'] + p['x_fwd'] * cpm + shift
        Zs = Sc['Z_of_keel_top'] + p['z_sill'] * cpm
        Zl = Sc['Z_of_keel_top'] + p['z_lintel'] * cpm
        for side in (1, -1):
            lit = []
            for x in range(int(Xa) - 6, int(Xf) + 7):
                for z in range(int(Zs) - 6, int(Zl) + 7):
                    # 這一欄有船殼（d 3..75 之間至少一格在刻之前是實心），而且刻之後整條都空 ⇒ 透光
                    had = any((x, YC + side * d, z) in before for d in range(3, 76))
                    if had and not any((x, YC + side * d, z) in occ for d in range(3, 76)):
                        lit.append((x, z))
            if not lit:
                res.append({'n': p['n'], 'side': side, 'lit': 0})
                worst = max(worst, 99)
                continue
            L = np.array(lit)
            # 格 X 佔 [X, X+1)（格中心 X+0.5，跟 draft_planking.Model.xb 同一個約定）
            e = {'aft': float(L[:, 0].min() - Xa), 'fwd': float(L[:, 0].max() + 1 - Xf),
                 'sill': float(L[:, 1].min() - Zs), 'lintel': float(L[:, 1].max() + 1 - Zl)}
            full = (L[:, 0].max() - L[:, 0].min() + 1) * (L[:, 1].max() - L[:, 1].min() + 1)
            res.append({'n': p['n'], 'side': side, 'lit': len(lit), 'rect_full': bool(full == len(lit)),
                        'edge_minus_read': {k: round(v, 2) for k, v in e.items()}})
            worst = max(worst, max(abs(v) for v in e.values()))
    out['openings'] = res
    out['openings_max_abs_edge_diff'] = round(worst, 2)
    out['openings_all_rect'] = all(r.get('rect_full') for r in res)

    # 牆不能有洞
    # 開口那幾欄 (x, z)（任一舷有刻的）；鄰格落在開口欄裡的不算 —— 牆是斜的，開口裡上下兩列的深度本來就錯開。
    # 空的鄰格分三種（d ＝ 離中線幾格、o ＝ 那一欄這一舷最外面的實心）：d > o ⇒ 船外（斜的船殼面外面）；
    # o − 3 ≤ d ≤ o ⇒ 肋骨那一層（從砲門看得進肋骨之間的縫 ⇒ 洞）；d < o − 3 ⇒ 船艙裡（牆的內面）。只有中間那種算洞。
    cols = {(x, z) for (x, y, z) in carve}

    def outer(x, z, side):
        for d in range(75, -1, -1):
            if (x, YC + side * d, z) in occ:
                return d
        return None
    cls = {'exterior': 0, 'frame_layer': 0, 'interior': 0}
    holes = set()
    for (x, y, z) in carve:
        side = 1 if y > YC else -1
        for dx, dz in ((1, 0), (-1, 0), (0, 1), (0, -1)):
            n = (x + dx, y, z + dz)
            if (n[0], n[2]) in cols or n in occ:
                continue
            d, o = abs(y - YC), outer(n[0], n[2], side)
            k = 'exterior' if o is None or d > o else ('frame_layer' if d >= o - 3 else 'interior')
            cls[k] += 1
            if k == 'frame_layer':
                holes.add(n)
    out['wall_holes'] = {'count': len(holes), 'empty_neighbours': cls, 'examples': sorted(holes)[:10]}
    print(json.dumps(out, ensure_ascii=False, indent=1, default=lambda v: v.item()))


if __name__ == '__main__':
    main()
