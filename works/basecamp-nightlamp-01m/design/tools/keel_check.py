# 階段一 龍骨的讀數（TASK-0538）：結果帳（作品＝設計）＋ 原圖探針（新圖紙＝原圖）＋ 反向對照 ⇒ verify_keel_stage1.json
# 用法：python -I keel_check.py <design 資料夾> <export list 檔>
#   · 結果帳：作品 export format=list 逐格對 masks/keel/*.vox.txt（含顏色）；先做正向／負向對照，確定這把尺會說話。
#   · 原圖探針：從 Pl. LI 側面圖上的線出發（掃描找線心），換成作品座標，量到作品龍骨面的距離（格）。
#   · 反向對照：換算的錨點故意偏 3 格，探針要報 3。
import sys, os, json
import numpy as np
from PIL import Image

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.dirname(HERE))
import draft_lines as DL   # noqa: E402

Image.MAX_IMAGE_PIXELS = None


def read_list(path):
    d = {}
    for ln in open(path, encoding='utf-8'):
        ln = ln.strip()
        if not ln or ln.startswith('#'):
            continue
        x, y, z, c = (int(v) for v in ln.split(',')[:4])
        d[(x, y, z)] = c
    return d


def compare(design_cells, work):
    miss = [k for k in design_cells if k not in work]
    extra = [k for k in work if k not in design_cells]
    color = [k for k in design_cells if k in work and work[k] != design_cells[k]]
    return len(miss), len(extra), len(color)


def line_center(dark, ox, oy, x=None, y=None, near=None, win=12):
    """在 x 欄（找水平線）或 y 列（找垂直線）上，找離 near 最近的黑段中心"""
    if x is not None:
        col = dark[near - win - oy:near + win - oy, x - ox]
        idx = np.where(col)[0]
        base = near - win
    else:
        row = dark[y - oy, near - win - ox:near + win - ox]
        idx = np.where(row)[0]
        base = near - win
    if len(idx) == 0:
        return None
    runs = np.split(idx, np.where(np.diff(idx) > 1)[0] + 1)
    cs = [base + r.mean() for r in runs]
    return float(min(cs, key=lambda c: abs(c - near)))


def main():
    design, lst = sys.argv[1], sys.argv[2]
    plan, R, B, ship = DL.load(design)
    xs, zs, T, hb_max, _ = DL.hull_table(ship)
    k, cpm, X, Z, Yh = DL.scale_of(plan, ship, hb_max)
    Sc = plan['scale']
    work = read_list(lst)
    des = {}
    for part in ('shoe', 'keel'):
        des.update(read_list(os.path.join(design, 'masks', 'keel', part + '.vox.txt')))

    out = {'work_cells': len(work), 'design_cells': len(des)}
    # 正向／負向對照：這把尺看得到「缺一格」與「顏色不同」嗎？
    w2 = dict(work)
    k0 = next(iter(des))
    del w2[k0]
    k1 = list(des)[1]
    w2[k1] = 1
    out['ruler_check'] = {'drop_one_and_recolor_one': compare(des, w2), 'expect': [1, 0, 1]}
    m, e, c = compare(des, work)
    out['ledger'] = {'missing': m, 'extra': e, 'color_diff': c}

    # 原圖探針
    plate = os.path.join(design, '..', '..', '..', 'references', 'chapman-architectura-navalis-1768', 'PlLI_Engelsk_Ostindiefarare.tif')
    ox, oy = 800, 6500
    img = Image.open(plate).crop((ox, oy, 10400, 7000))
    dark = ~np.array(img)
    pxm, x0p, kt = R['px_per_m'], R['datum']['x0_px'], R['datum']['keel_top_py']

    def to_work(px, py, dX=0.0, dZ=0.0):
        x = (px - x0p) / pxm
        z = (kt - py) / pxm
        return Sc['X_of_x0'] + dX + x * cpm, Sc['Z_of_keel_top'] + dZ + z * cpm

    # 作品的面：某一欄（x 格）的頂面／底面／分界；某一層（z 格）的前面／後面 —— 都在中線 y 160 量
    def col_faces(xc):
        zz = sorted(z for (x, y, z) in work if x == xc and y == 160)
        return zz

    def row_faces(zc):
        xx = sorted(x for (x, y, z) in work if z == zc and y == 160)
        return (xx[0], xx[-1] + 1) if xx else (None, None)

    probes = []

    def run(dX=0.0, dZ=0.0):
        res = []
        # 水平線：龍骨頂（6756 附近）、龍骨／護龍骨分界（6838）、底（6863）
        for px in (2000, 3000, 4000, 5000, 6000, 7000, 8000, 9000):
            for name, near, face in (('keel_top', 6756, 'top'), ('shoe_top', 6839, 'split'), ('bottom', 6863, 'bottom')):
                c = line_center(dark, ox, oy, x=px, near=near)
                if c is None:
                    continue
                Xw, Zw = to_work(px, c, dX, dZ)
                zz = col_faces(int(np.floor(Xw)))
                if not zz:
                    res.append({'probe': name, 'px': px, 'py': round(c, 1), 'note': '作品這欄沒有格'})
                    continue
                fz = {'top': zz[-1] + 1, 'bottom': zz[0], 'split': min(z for z in zz if work[(int(np.floor(Xw)), 160, z)] == 177)}[face]
                res.append({'probe': name, 'px': px, 'py': round(c, 1), 'work_Z': round(Zw, 2), 'face_Z': fz, 'dev_cells': round(Zw - fz, 2)})
        # 垂直線：龍骨前端（9443）、護龍骨前端（9480）、後端（黑帶右緣）
        for name, near, rows, zc_of in (('keel_fore', 9443, (6770, 6790, 6810, 6825), None),
                                         ('shoe_fore', 9480, (6845, 6852), None)):
            for py in rows:
                c = line_center(dark, ox, oy, y=py, near=near, win=8)
                if c is None:
                    continue
                Xw, Zw = to_work(c, py, dX, dZ)
                a, b = row_faces(int(np.floor(Zw)))
                if b is None:
                    continue
                res.append({'probe': name, 'px': round(c, 1), 'py': py, 'work_X': round(Xw, 2), 'face_X': b, 'dev_cells': round(Xw - b, 2)})
        for py in (6770, 6790, 6810, 6830, 6850):
            # 黑帶（寬 ~33 px）右緣：在列上找最寬的黑段，取右緣
            row = dark[py - oy, 1650 - ox:1850 - ox]
            idx = np.where(row)[0]
            runs = np.split(idx, np.where(np.diff(idx) > 1)[0] + 1)
            r = max(runs, key=len)
            if len(r) < 25:                               # 黑帶被鐵件蓋住的列：最寬的黑段不是黑帶 ⇒ 不量（照實記）
                res.append({'probe': 'aft_end', 'py': py, 'band_px': len(r), 'note': '這一列黑帶被蓋住（最寬黑段 < 25 px），跳過'})
                continue
            edge = 1650 + r[-1] + 0.5
            Xw, Zw = to_work(edge, py, dX, dZ)
            a, b = row_faces(int(np.floor(Zw)))
            if a is None:
                continue
            res.append({'probe': 'aft_end', 'px': round(edge, 1), 'py': py, 'band_px': len(r), 'work_X': round(Xw, 2), 'face_X': a, 'dev_cells': round(Xw - a, 2)})
        return res

    base = run()
    out['probes'] = base
    devs = [abs(p['dev_cells']) for p in base if 'dev_cells' in p]
    out['probe_summary'] = {'n': len(devs), 'max_abs_dev_cells': round(max(devs), 2), 'mean_abs_dev_cells': round(float(np.mean(devs)), 2)}
    for name in ('keel_top', 'shoe_top', 'bottom', 'keel_fore', 'shoe_fore', 'aft_end'):
        d = [p['dev_cells'] for p in base if p['probe'] == name and 'dev_cells' in p]
        out['probe_summary'][name] = {'n': len(d), 'min': round(min(d), 2), 'max': round(max(d), 2)} if d else None
    # 反向對照：錨點偏 3 格（X 偏 ⇒ 兩端那幾根要報 ±3；Z 偏 ⇒ 水平那幾根要報 3）
    sx = run(dX=3.0)
    sz = run(dZ=3.0)

    def delta(a, b, name):
        ka = {(p['probe'], p['px'] if p['probe'] in ('keel_top', 'shoe_top', 'bottom') else p['py']): p for p in a if 'dev_cells' in p}
        out_ = []
        for q in b:
            key = (q['probe'], q['px'] if q['probe'] in ('keel_top', 'shoe_top', 'bottom') else q['py'])
            if q['probe'] == name and 'dev_cells' in q and key in ka:
                out_.append(round(q['dev_cells'] - ka[key]['dev_cells'], 2))
        return out_
    out['reverse'] = {'X+3': {n: sorted(set(delta(base, sx, n))) for n in ('keel_fore', 'shoe_fore', 'aft_end')},
                      'Z+3': {n: sorted(set(delta(base, sz, n))) for n in ('keel_top', 'shoe_top', 'bottom')}}
    json.dump(out, open(os.path.join(design, 'verify_keel_stage1.json'), 'w', encoding='utf-8'), ensure_ascii=False, indent=1)
    print(json.dumps({kk: v for kk, v in out.items() if kk != 'probes'}, ensure_ascii=False, indent=1))


if __name__ == '__main__':
    main()
