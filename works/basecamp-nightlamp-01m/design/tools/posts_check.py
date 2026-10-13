# 階段二 船頭柱・gripe・船尾柱・內艉柱的讀數（TASK-0538）：結果帳＋原圖探針＋反向對照 ⇒ verify_posts_stage2.json
# 用法：python -I posts_check.py <design 資料夾> <export list 檔>
#   · 結果帳：作品 export list 逐格對「階段一＋階段二」全部清單（含顏色）。
#   · 原圖探針：在 Pl. LI 側面圖某一列（某個高度）重新找線心（不用設計時的追線），換成作品座標，
#     量到作品中線 y 160 那一層同一高度的面：船頭 rabbet／船頭柱前面／外緣，船尾 後面／L1／rabbet。
#   · 反向對照：換算錨點 X 偏 3 格，探針要報 3。
import sys, os, json
import numpy as np
from PIL import Image

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.dirname(HERE))
sys.path.insert(0, HERE)
import draft_lines as DL   # noqa: E402
import draft_posts as DP   # noqa: E402
from keel_check import read_list, compare   # noqa: E402

Image.MAX_IMAGE_PIXELS = None


def runs_on_row(dark, ox, oy, py, x0, x1):
    r = dark[py - oy, x0 - ox:x1 - ox]
    idx = np.where(r)[0]
    if len(idx) == 0:
        return []
    rs = np.split(idx, np.where(np.diff(idx) > 1)[0] + 1)
    return [(x0 + g.mean(), len(g), x0 + g[0], x0 + g[-1] + 1) for g in rs]


def main():
    design, lst = sys.argv[1], sys.argv[2]
    plan, R, B, ship = DL.load(design)
    xs, zs, T, hb_max, _ = DL.hull_table(ship)
    k, cpm, X, Z, Yh = DL.scale_of(plan, ship, hb_max)
    Sc = plan['scale']
    X0, Zk = Sc['X_of_x0'], Sc['Z_of_keel_top']
    po = DP.Posts(plan, R, B, ship)
    work = read_list(lst)
    des = {}
    for sub, parts in (('keel', ('shoe', 'keel')), ('posts', ('sternpost', 'inner_post', 'stem', 'gripe'))):
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
    ox, oy = 800, 4800
    dark = ~np.array(Image.open(plate).crop((ox, oy, 11000, 7000)))
    pxm, x0p, kt = R['px_per_m'], R['datum']['x0_px'], R['datum']['keel_top_py']
    px_of = lambda x: x0p + x * pxm

    def row_cells(Zc):
        return sorted((x, col) for (x, y, z), col in work.items() if z == Zc and y == 160)

    def faces(Zc, colA, colB=None):
        """這一層：colA 的最前格＋1、最後格；colA→colB 的交界"""
        r = row_cells(Zc)
        a = [x for x, c in r if c == colA]
        return r, a

    def run(dX=0.0):
        res = []
        toX = lambda px: X0 + dX + (px - x0p) / pxm * cpm
        # ── 船頭：z 0.5..5.0（gripe 外緣只到 5.12）
        for z in np.arange(0.5, 5.01, 0.5):
            py = int(round(kt - z * pxm))
            Zc = int(np.floor(Zk + z * cpm))
            zc = (Zc + 0.5 - Zk) / cpm                              # 作品這一層的格中心高度
            pyc = int(round(kt - zc * pxm))
            rs = runs_on_row(dark, ox, oy, pyc, int(px_of(32.0)), int(px_of(42.5)))
            r = row_cells(Zc)
            stem = [x for x, c in r if c == 177 and x > 400]
            grip = [x for x, c in r if c == 104 and x > 400]
            for name, exp_x, face in (('bow_rabbet', float(ship.rabbet_x(zc)), min(stem) if stem else None),
                                      ('bow_stem_face', float(ship.stem_face_x(zc)), (max(stem) + 1) if stem else None),
                                      ('bow_outer', float(ship.stem_outer_x(zc)), (max(grip) + 1) if grip else None)):
                cand = [g for g in rs if g[1] <= 25 and abs(g[0] - px_of(exp_x)) < 25]
                if not cand or face is None:
                    res.append({'probe': name, 'z': round(zc, 3), 'note': '這一列找不到線（±25 px 內）或作品沒有那個面'})
                    continue
                g = min(cand, key=lambda g: abs(g[0] - px_of(exp_x)))
                Xw = toX(g[0])
                res.append({'probe': name, 'z': round(zc, 3), 'Z': Zc, 'line_px': round(g[0], 1), 'work_X': round(Xw, 2), 'face_X': face, 'dev_cells': round(Xw - face, 2)})
        # ── 船尾：z 0.5..6.5
        for z in np.arange(0.5, 6.51, 0.5):
            Zc = int(np.floor(Zk + z * cpm))
            zc = (Zc + 0.5 - Zk) / cpm
            pyc = int(round(kt - zc * pxm))
            rs = runs_on_row(dark, ox, oy, pyc, int(px_of(-1.0)), int(px_of(2.0)))
            r = row_cells(Zc)
            spost = [x for x, c in r if c == 177 and x < 200]
            inner = [x for x, c in r if c == 173 and x < 200]
            band = [g for g in rs if 25 <= g[1] <= 45 and abs(g[0] - px_of(po.aft_face(zc)) + 16) < 30]
            if band and spost:
                b = max(band, key=lambda g: g[1])
                Xw = toX(b[3])
                res.append({'probe': 'stern_aft_face', 'z': round(zc, 3), 'Z': Zc, 'line_px': round(b[3], 1), 'work_X': round(Xw, 2), 'face_X': min(spost), 'dev_cells': round(Xw - min(spost), 2)})
            else:
                res.append({'probe': 'stern_aft_face', 'z': round(zc, 3), 'note': '黑帶被蓋住或這一層沒有船尾柱'})
            for name, exp_x, face, only_if in (('stern_L1', po.L1(zc), (max(spost) + 1) if spost else None, po.L1(zc) >= po.aft_face(zc) + plan['posts']['sternpost']['min_siding']),
                                               ('stern_rabbet_L3', po.L3(zc), (max(inner) + 1) if inner else None, True)):
                if not only_if:
                    res.append({'probe': name, 'z': round(zc, 3), 'note': '這個高度船尾柱用最小寬度（設計），不量 L1'})
                    continue
                cand = [g for g in rs if g[1] <= 12 and abs(g[0] - px_of(exp_x)) < 12]
                if not cand or face is None:
                    res.append({'probe': name, 'z': round(zc, 3), 'note': '這一列找不到線（±12 px 內）或作品沒有那個面'})
                    continue
                g = min(cand, key=lambda g: abs(g[0] - px_of(exp_x)))
                Xw = toX(g[0])
                res.append({'probe': name, 'z': round(zc, 3), 'Z': Zc, 'line_px': round(g[0], 1), 'work_X': round(Xw, 2), 'face_X': face, 'dev_cells': round(Xw - face, 2)})
        return res

    base = run()
    out['probes'] = base
    summ = {}
    for name in sorted({p['probe'] for p in base}):
        d = [p['dev_cells'] for p in base if p['probe'] == name and 'dev_cells' in p]
        skipped = sum(1 for p in base if p['probe'] == name and 'dev_cells' not in p)
        summ[name] = {'n': len(d), 'skipped': skipped, 'min': round(min(d), 2) if d else None, 'max': round(max(d), 2) if d else None}
    alld = [abs(p['dev_cells']) for p in base if 'dev_cells' in p]
    summ['all'] = {'n': len(alld), 'max_abs': round(max(alld), 2), 'mean_abs': round(float(np.mean(alld)), 2)}
    out['probe_summary'] = summ
    sh = run(dX=3.0)
    ka = {(p['probe'], p['z']): p for p in base if 'dev_cells' in p}
    rev = {}
    for q in sh:
        kk = (q['probe'], q['z'])
        if 'dev_cells' in q and kk in ka:
            rev.setdefault(q['probe'], set()).add(round(q['dev_cells'] - ka[kk]['dev_cells'], 2))
    out['reverse_X+3'] = {kk: sorted(v) for kk, v in rev.items()}
    json.dump(out, open(os.path.join(design, 'verify_posts_stage2.json'), 'w', encoding='utf-8'), ensure_ascii=False, indent=1, default=lambda o: o.item())
    print(json.dumps({kk: v for kk, v in out.items() if kk != 'probes'}, ensure_ascii=False, indent=1, default=lambda o: o.item()))


if __name__ == '__main__':
    main()
