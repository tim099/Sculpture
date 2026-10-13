# 階段四 底肋・keelson 的讀數（TASK-0538）：結果帳＋原圖探針＋反向對照 ⇒ verify_floors_stage4.json
# 用法：python -I floors_check.py <design 資料夾> <export list 檔>
#   · 結果帳：作品 export list 逐格對階段一～四全部清單（含顏色）。
#   · 原圖探針（都在原圖重新找線心，不用設計時的追線）：
#       keelson 頂 vs B（側面圖）、keelson 底 vs A（側面圖虛線，密一點量）、
#       底肋頭 vs narrowing（半寬圖）、落在站上的四片底肋（Ø、4、8、12）外緣 vs 橫切面圖那一站的線。
#   · 反向對照：前兩組 Z 偏 3 格、後兩組半寬偏 3 格，探針要報 3。
import sys, os, json
import numpy as np
from PIL import Image

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.dirname(HERE))
sys.path.insert(0, HERE)
import draft_lines as DL   # noqa: E402
from keel_check import read_list, compare   # noqa: E402

Image.MAX_IMAGE_PIXELS = None


def nearest_run(arr1d, base, exp, maxw):
    idx = np.where(arr1d)[0]
    if len(idx) == 0:
        return None
    rs = np.split(idx, np.where(np.diff(idx) > 1)[0] + 1)
    c = [base + r.mean() for r in rs if len(r) <= maxw]
    return min(c, key=lambda v: abs(v - exp)) if c else None


def main():
    design, lst = sys.argv[1], sys.argv[2]
    plan, R, B, ship = DL.load(design)
    xs, zs, T, hb_max, _ = DL.hull_table(ship)
    k, cpm, X, Z, Yh = DL.scale_of(plan, ship, hb_max)
    Sc, F = plan['scale'], plan['floors']
    X0, Zk = Sc['X_of_x0'], Sc['Z_of_keel_top']
    work = read_list(lst)
    des = {}
    groups = (('keel', ('shoe', 'keel')), ('posts', ('sternpost', 'inner_post', 'stem', 'gripe')),
              ('deadwood', ('aft_deadwood', 'fore_deadwood', 'apron')),
              ('floors', ['keelson'] + ['f%+03d' % n for n in range(F['n'][0], F['n'][1] + 1)]))
    for sub, parts in groups:
        for p in parts:
            des.update(read_list(os.path.join(design, 'masks', sub, p + '.vox.txt')))
    out = {'work_cells': len(work), 'design_cells': len(des)}
    w2 = dict(work)
    del w2[next(iter(des))]
    w2[list(des)[-1]] = 1
    out['ruler_check'] = {'drop_one_and_recolor_one': compare(des, w2), 'expect': [1, 0, 1]}
    m, e, c = compare(des, work)
    out['ledger'] = {'missing': m, 'extra': e, 'color_diff': c}

    plate = os.path.join(design, '..', '..', '..', 'references', 'chapman-architectura-navalis-1768', 'PlLI_Engelsk_Ostindiefarare.tif')
    full = Image.open(plate)
    ox, oy = 800, 1000
    dark = ~np.array(full.crop((ox, oy, 11000, 8200)))
    pxm, x0p, kt, hc = R['px_per_m'], R['datum']['x0_px'], R['datum']['keel_top_py'], R['datum']['half_breadth_centre_py']
    bpc, bpk = B['body_plan']['centre_px'], B['body_plan']['keel_top_py']
    a_ = np.array(B['line_A_cutting_down']['x_z'], float)
    b_ = np.array(B['line_B_keelson_top']['x_z'], float)
    n_ = np.array(B['narrowing_line']['x_hb'], float)
    st = plan['hull']['stations_x']
    xk0, xk1 = st['16'], st['M']
    floors = {}
    for n in range(F['n'][0], F['n'][1] + 1):
        floors[n] = {(x, y, z) for (x, y, z), cc in work.items() if cc == 141 and False}  # 下面再填
    fl_cells = {}
    for n in range(F['n'][0], F['n'][1] + 1):
        fl_cells[n] = set(read_list(os.path.join(design, 'masks', 'floors', 'f%+03d.vox.txt' % n)))
    bycol = {}
    for (x, y, z), cc in work.items():
        bycol.setdefault(x, []).append((y, z, cc))

    st_px = [x0p + v * pxm for v in R['stations_x_m'].values()]         # 側面圖的站線（垂直線）

    def run(dZ=0.0, dY=0.0):
        res = []
        # (a)(b) keelson 頂／底
        for name, tab, step, maxw in (('keelson_top_B', b_, 0.5, 12), ('keelson_bottom_A', a_, 0.05, 6)):
            for xm in np.arange(xk0 + 0.3, xk1 - 0.3, step):
                Xc = int(np.floor(X0 + xm * cpm))
                xc = (Xc + 0.5 - X0) / cpm
                zexp = float(np.interp(xc, tab[:, 0], tab[:, 1]))
                px = int(round(x0p + xc * pxm))
                if min(abs(px - q) for q in st_px) <= 9:
                    res.append({'probe': name, 'x': round(xc, 3), 'note': '這一欄貼著站線（9 px 內；站線本身近 10 px 寬），垂直線的毛邊會被當成線 ⇒ 不量'})
                    continue
                pye = kt - zexp * pxm
                col = dark[int(pye) - 14 - oy:int(pye) + 14 - oy, px - ox]
                g = nearest_run(col, int(pye) - 14, pye, maxw)
                kz = [z for (y, z, cc) in bycol.get(Xc, []) if y == 160 and cc == 209]
                if g is None or not kz:
                    res.append({'probe': name, 'x': round(xc, 3), 'note': '這一欄找不到線（±14 px）或作品沒有 keelson'})
                    continue
                Zw = Zk + dZ + (kt - g) / pxm * cpm
                face = (max(kz) + 1) if name == 'keelson_top_B' else min(kz)
                res.append({'probe': name, 'x': round(xc, 3), 'X': Xc, 'line_py': round(float(g), 1), 'work_Z': round(Zw, 2), 'face_Z': face, 'dev_cells': round(Zw - face, 2)})
        # (c) 底肋頭 vs narrowing（每片中間兩欄）
        for n, cs in fl_cells.items():
            xsn = sorted({x for (x, y, z) in cs})
            Xc = xsn[1]
            xc = (Xc + 0.5 - X0) / cpm
            hexp = float(np.interp(xc, n_[:, 0], n_[:, 1]))
            px = int(round(x0p + xc * pxm))
            pye = hc + hexp * pxm
            col = dark[int(pye) - 14 - oy:int(pye) + 14 - oy, px - ox]
            g = nearest_run(col, int(pye) - 14, pye, 12)
            dys = [abs(y - 160) for (x, y, z) in cs if x == Xc]
            if g is None:
                res.append({'probe': 'floor_head_narrowing', 'n': n, 'note': '這一欄找不到線'})
                continue
            Hw = (g - hc) / pxm * cpm + dY                       # 原圖的半寬（格）
            face = max(dys) + 0.5                                  # 最外那一格的外緣（格中心 ＋ 0.5）
            res.append({'probe': 'floor_head_narrowing', 'n': n, 'X': Xc, 'line_py': round(float(g), 1), 'work_hb_cells': round(Hw, 2), 'face_hb_cells': face, 'dev_cells': round(Hw - face, 2)})
        # (d) 落在站上的底肋外緣 vs 橫切面圖那一站（左半，船尾那半段）
        for n, sname in ((0, 'mid'), (-4, '4'), (-8, '8'), (-12, '12')):
            cs = fl_cells[n]
            Xc = sorted({x for (x, y, z) in cs})[1]
            sec = np.array(B['body_plan']['sections_z_hb']['mid_L' if sname == 'mid' else sname], float)
            for Zc in sorted({z for (x, y, z) in cs if x == Xc})[::2]:
                zc = (Zc + 0.5 - Zk) / cpm
                dys = [abs(y - 160) for (x, y, z) in cs if x == Xc and z == Zc]
                hexp = float(np.interp(zc, sec[:, 0], sec[:, 1]))
                py = int(round(bpk - zc * pxm))
                pxe = bpc - hexp * pxm
                row = dark[py - oy, int(pxe) - 10 - ox:int(pxe) + 10 - ox]
                g = nearest_run(row, int(pxe) - 10, pxe, 8)
                if g is None or hexp < 0.3:
                    res.append({'probe': 'floor_outer_vs_section', 'n': n, 'Z': Zc, 'note': '這一列找不到線（±10 px）或太靠龍骨'})
                    continue
                Hw = (bpc - g) / pxm * cpm + dY
                face = max(dys) + 0.5
                head = max(abs(y - 160) for (x, y, z) in cs if x == Xc)
                if max(dys) >= head:
                    res.append({'probe': 'floor_outer_vs_section', 'n': n, 'Z': Zc, 'note': '這一列被底肋頭（narrowing）切齊，量到的是頭不是船殼 ⇒ 不算', 'face_hb_cells': face, 'line_hb_cells': round(Hw, 2)})
                    continue
                res.append({'probe': 'floor_outer_vs_section', 'n': n, 'Z': Zc, 'line_px': round(float(g), 1), 'work_hb_cells': round(Hw, 2), 'face_hb_cells': face, 'dev_cells': round(Hw - face, 2)})
        return res

    base = run()
    out['probes'] = base
    summ = {}
    for name in ('keelson_top_B', 'keelson_bottom_A', 'floor_head_narrowing', 'floor_outer_vs_section'):
        d = [p['dev_cells'] for p in base if p['probe'] == name and 'dev_cells' in p]
        summ[name] = {'n': len(d), 'skipped': sum(1 for p in base if p['probe'] == name and 'dev_cells' not in p),
                      'min': round(min(d), 2) if d else None, 'max': round(max(d), 2) if d else None,
                      'mean_abs': round(float(np.mean(np.abs(d))), 2) if d else None}
    alld = [abs(p['dev_cells']) for p in base if 'dev_cells' in p]
    summ['all'] = {'n': len(alld), 'max_abs': round(max(alld), 2), 'mean_abs': round(float(np.mean(alld)), 2)}
    out['probe_summary'] = summ

    def key(p):
        return (p['probe'], p.get('x'), p.get('n'), p.get('Z'))
    rev = {}
    for shift, kw in (('Z+3', {'dZ': 3.0}), ('Y+3', {'dY': 3.0})):
        sh = run(**kw)
        ka = {key(p): p for p in base if 'dev_cells' in p}
        for q in sh:
            if 'dev_cells' in q and key(q) in ka:
                rev.setdefault(shift + ' ' + q['probe'], set()).add(round(q['dev_cells'] - ka[key(q)]['dev_cells'], 2))
    out['reverse'] = {kk: sorted(v) for kk, v in rev.items()}
    dump = lambda o: json.dumps(o, ensure_ascii=False, indent=1, default=lambda v: v.item())
    open(os.path.join(design, 'verify_floors_stage4.json'), 'w', encoding='utf-8').write(dump(out))
    print(dump({kk: v for kk, v in out.items() if kk != 'probes'}))


if __name__ == '__main__':
    main()
