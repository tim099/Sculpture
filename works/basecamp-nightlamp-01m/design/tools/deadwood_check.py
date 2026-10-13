# 階段三 deadwood・apron 的讀數（TASK-0538）：結果帳＋原圖探針＋反向對照 ⇒ verify_deadwood_stage3.json
# 用法：python -I deadwood_check.py <design 資料夾> <export list 檔>
#   · 結果帳：作品 export list 逐格對階段一～三全部清單（含顏色）。
#   · 原圖探針：在 Pl. LI 側面圖某一欄重新找線心（不用設計時的追線）—— B（實線）與 A（虛線），換成作品座標，
#     量到作品中線 y 160 那一欄的面：船尾 deadwood 頂（＝ B）、船頭 deadwood／apron 分界（＝ A）、apron 頂（＝ B）。
#   · 反向對照：換算錨點 Z 偏 3 格，探針要報 3。
import sys, os, json
import numpy as np
from PIL import Image

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.dirname(HERE))
sys.path.insert(0, HERE)
import draft_lines as DL   # noqa: E402
from keel_check import read_list, compare   # noqa: E402

Image.MAX_IMAGE_PIXELS = None


def main():
    design, lst = sys.argv[1], sys.argv[2]
    plan, R, B, ship = DL.load(design)
    xs, zs, T, hb_max, _ = DL.hull_table(ship)
    k, cpm, X, Z, Yh = DL.scale_of(plan, ship, hb_max)
    Sc = plan['scale']
    X0, Zk = Sc['X_of_x0'], Sc['Z_of_keel_top']
    work = read_list(lst)
    des = {}
    for sub, parts in (('keel', ('shoe', 'keel')), ('posts', ('sternpost', 'inner_post', 'stem', 'gripe')),
                       ('deadwood', ('aft_deadwood', 'fore_deadwood', 'apron'))):
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
    a = np.array(B['line_A_cutting_down']['x_z'], float)
    b = np.array(B['line_B_keelson_top']['x_z'], float)

    def col(Xc):
        return sorted((z, cc) for (x, y, z), cc in work.items() if x == Xc and y == 160)

    def find(px, py_exp, win, maxw):
        cc = dark[int(py_exp) - win - oy:int(py_exp) + win - oy, int(px) - ox]
        idx = np.where(cc)[0]
        if len(idx) == 0:
            return None
        rs = np.split(idx, np.where(np.diff(idx) > 1)[0] + 1)
        cand = [int(py_exp) - win + r.mean() for r in rs if len(r) <= maxw]
        return min(cand, key=lambda v: abs(v - py_exp)) if cand else None

    def run(dZ=0.0):
        res = []
        toZ = lambda py: Zk + dZ + (kt - py) / pxm * cpm
        # A 是虛線：點之間有空白，密一點量
        probes = [('aft_B', x, 'B') for x in np.arange(1.0, 7.51, 0.5)] + \
                 [('fore_A', x, 'A') for x in np.arange(33.75, 37.01, 0.05)] + \
                 [('fore_B', x, 'B') for x in np.arange(33.75, 38.26, 0.25)]
        for name, xm, line in probes:
            Xc = int(np.floor(X0 + xm * cpm))
            xc = (Xc + 0.5 - X0) / cpm                          # 作品這一欄的格中心
            px = x0p + xc * pxm
            zexp = float(np.interp(xc, *(b.T if line == 'B' else a.T)))
            g = find(px, kt - zexp * pxm, 14, 12 if line == 'B' else 6)
            cl = col(Xc)
            if g is None or not cl:
                res.append({'probe': name, 'x': round(xc, 3), 'note': '這一欄找不到線（±14 px）或作品這欄沒有格'})
                continue
            Zw = toZ(g)
            if name == 'aft_B':
                face = max(z for z, cc in cl if cc == 209) + 1
            elif name == 'fore_A':
                f = [z for z, cc in cl if cc == 209]
                face = (max(f) + 1) if f else None
            else:
                f = [z for z, cc in cl if cc == 173 and (z + 0.5 - Zk) / cpm < 5.0]   # 帶子（B 碰 rabbet 以上）不算
                face = (max(f) + 1) if f else None
            if face is None:
                res.append({'probe': name, 'x': round(xc, 3), 'note': '作品這欄沒有那個面'})
                continue
            res.append({'probe': name, 'x': round(xc, 3), 'X': Xc, 'line_py': round(float(g), 1), 'work_Z': round(Zw, 2), 'face_Z': int(face), 'dev_cells': round(Zw - face, 2)})
        return res

    base = run()
    out['probes'] = base
    summ = {}
    for name in ('aft_B', 'fore_A', 'fore_B'):
        d = [p['dev_cells'] for p in base if p['probe'] == name and 'dev_cells' in p]
        summ[name] = {'n': len(d), 'skipped': sum(1 for p in base if p['probe'] == name and 'dev_cells' not in p),
                      'min': round(min(d), 2) if d else None, 'max': round(max(d), 2) if d else None}
    alld = [abs(p['dev_cells']) for p in base if 'dev_cells' in p]
    summ['all'] = {'n': len(alld), 'max_abs': round(max(alld), 2), 'mean_abs': round(float(np.mean(alld)), 2)}
    out['probe_summary'] = summ
    sh = run(dZ=3.0)
    ka = {(p['probe'], p['x']): p for p in base if 'dev_cells' in p}
    rev = {}
    for q in sh:
        kk = (q['probe'], q['x'])
        if 'dev_cells' in q and kk in ka:
            rev.setdefault(q['probe'], set()).add(round(q['dev_cells'] - ka[kk]['dev_cells'], 2))
    out['reverse_Z+3'] = {kk: sorted(v) for kk, v in rev.items()}
    dump = lambda o: json.dumps(o, ensure_ascii=False, indent=1, default=lambda v: v.item())
    open(os.path.join(design, 'verify_deadwood_stage3.json'), 'w', encoding='utf-8').write(dump(out))
    print(dump({kk: v for kk, v in out.items() if kk != 'probes'}))


if __name__ == '__main__':
    main()
