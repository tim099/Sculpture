# 階段五 方肋骨的讀數（TASK-0538）：結果帳＋原圖探針＋反向對照 ⇒ verify_frames_stage5.json
# 用法：python -I frames_check.py <design 資料夾> <export list 檔>
#   · 結果帳：作品 export list 逐格對階段一～五全部清單（含顏色）。
#   · 原圖探針（原圖重新找線心）：
#       落在站上的四片（Ø、4、8、12）肋骨外緣 vs 橫切面圖那一站（底肋頭以上到 z 9.8）；
#       肋骨頂 vs 側面圖船腰的舷牆頂（後甲板盡頭 x 13.48 以前船頭那段；舷牆頂 ＝ 照圖 wale ＋ 2.99 是設計假設，這組量它）。
#   · 反向對照：半寬偏 3 格／Z 偏 3 格。
import sys, os, json
import numpy as np
from PIL import Image

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.dirname(HERE))
sys.path.insert(0, HERE)
import draft_lines as DL   # noqa: E402
from keel_check import read_list, compare   # noqa: E402
from floors_check import nearest_run   # noqa: E402

Image.MAX_IMAGE_PIXELS = None


def main():
    design, lst = sys.argv[1], sys.argv[2]
    plan, R, B, ship = DL.load(design)
    xs, zs, T, hb_max, _ = DL.hull_table(ship)
    k, cpm, X, Z, Yh = DL.scale_of(plan, ship, hb_max)
    Sc, Fl, Fr = plan['scale'], plan['floors'], plan['frames']
    X0, Zk = Sc['X_of_x0'], Sc['Z_of_keel_top']
    work = read_list(lst)
    des = {}
    groups = (('keel', ('shoe', 'keel')), ('posts', ('sternpost', 'inner_post', 'stem', 'gripe')),
              ('deadwood', ('aft_deadwood', 'fore_deadwood', 'apron')))
    for sub, parts in groups:
        for p in parts:
            des.update(read_list(os.path.join(design, 'masks', sub, p + '.vox.txt')))
    for sub in ('floors', 'frames'):
        for fn in sorted(os.listdir(os.path.join(design, 'masks', sub))):
            des.update(read_list(os.path.join(design, 'masks', sub, fn)))
    out = {'work_cells': len(work), 'design_cells': len(des)}
    w2 = dict(work)
    del w2[next(iter(des))]
    w2[list(des)[-1]] = 1
    out['ruler_check'] = {'drop_one_and_recolor_one': compare(des, w2), 'expect': [1, 0, 1]}
    m, e, c = compare(des, work)
    out['ledger'] = {'missing': m, 'extra': e, 'color_diff': c}

    plate = os.path.join(design, '..', '..', '..', 'references', 'chapman-architectura-navalis-1768', 'PlLI_Engelsk_Ostindiefarare.tif')
    ox, oy = 800, 1000
    dark = ~np.array(Image.open(plate).crop((ox, oy, 11000, 8200)))
    pxm, x0p, kt = R['px_per_m'], R['datum']['x0_px'], R['datum']['keel_top_py']
    bpc, bpk = B['body_plan']['centre_px'], B['body_plan']['keel_top_py']
    frames = {n: set(read_list(os.path.join(design, 'masks', 'frames', 'r%+03d.vox.txt' % n))) for n in range(Fr['n'][0], Fr['n'][1] + 1)}
    floors = {n: set(read_list(os.path.join(design, 'masks', 'floors', 'f%+03d.vox.txt' % n))) for n in (0, -4, -8, -12)}

    def run(dZ=0.0, dY=0.0):
        res = []
        for n, sname in ((0, 'mid'), (-4, '4'), (-8, '8'), (-12, '12')):
            cs = frames[n]
            Xc = sorted({x for (x, y, z) in cs})[1]
            sec = np.array(B['body_plan']['sections_z_hb']['mid_L' if sname == 'mid' else sname], float)
            col = {(y, z) for (x, y, z) in cs | floors[n] if x == Xc and y <= 160}
            for Zc in sorted({z for (y, z) in col})[::3]:
                zc = (Zc + 0.5 - Zk) / cpm
                if zc > min(9.8, sec[-1, 0]) or zc < 1.5:
                    continue
                dys = [160 - y for (y, z) in col if z == Zc]
                hexp = float(np.interp(zc, sec[:, 0], sec[:, 1]))
                py = int(round(bpk - zc * pxm))
                pxe = bpc - hexp * pxm
                row = dark[py - oy, int(pxe) - 10 - ox:int(pxe) + 10 - ox]
                g = nearest_run(row, int(pxe) - 10, pxe, 8)
                if g is None:
                    res.append({'probe': 'frame_outer_vs_section', 'n': n, 'Z': Zc, 'note': '這一列找不到線（±10 px）'})
                    continue
                Hw = (bpc - g) / pxm * cpm + dY
                face = max(dys) + 0.5
                res.append({'probe': 'frame_outer_vs_section', 'n': n, 'Z': Zc, 'line_px': round(float(g), 1), 'work_hb_cells': round(Hw, 2), 'face_hb_cells': face, 'dev_cells': round(Hw - face, 2)})
        # 肋骨頂 vs 側面圖船腰舷牆頂
        for n, cs in frames.items():
            xf = Fl['frame_x0'] + n * Fl['frame_spacing']
            if xf < plan['silhouette']['qd_break_x'] + 1.0:
                continue
            Xc = sorted({x for (x, y, z) in cs})[1]
            xc = (Xc + 0.5 - X0) / cpm
            ztop_design = float(ship.top(xc))
            px = int(round(x0p + xc * pxm))
            pye = kt - ztop_design * pxm
            col = dark[int(pye) - 15 - oy:int(pye) + 15 - oy, px - ox]
            g = nearest_run(col, int(pye) - 15, pye, 10)
            top = max(z for (x, y, z) in cs if x == Xc) + 1
            if g is None:
                res.append({'probe': 'frame_top_vs_rail', 'n': n, 'note': '這一欄找不到線（±15 px）'})
                continue
            Zw = Zk + dZ + (kt - g) / pxm * cpm
            res.append({'probe': 'frame_top_vs_rail', 'n': n, 'x': round(xc, 3), 'line_py': round(float(g), 1), 'work_Z': round(Zw, 2), 'face_Z': top, 'dev_cells': round(Zw - top, 2)})
        return res

    base = run()
    out['probes'] = base
    summ = {}
    for name in ('frame_outer_vs_section', 'frame_top_vs_rail'):
        d = [p['dev_cells'] for p in base if p['probe'] == name and 'dev_cells' in p]
        summ[name] = {'n': len(d), 'skipped': sum(1 for p in base if p['probe'] == name and 'dev_cells' not in p),
                      'min': round(min(d), 2) if d else None, 'max': round(max(d), 2) if d else None,
                      'mean_abs': round(float(np.mean(np.abs(d))), 2) if d else None}
    alld = [abs(p['dev_cells']) for p in base if 'dev_cells' in p]
    summ['all'] = {'n': len(alld), 'max_abs': round(max(alld), 2), 'mean_abs': round(float(np.mean(alld)), 2)}
    out['probe_summary'] = summ
    key = lambda p: (p['probe'], p.get('n'), p.get('Z'))
    rev = {}
    for shift, kw in (('Z+3', {'dZ': 3.0}), ('Y+3', {'dY': 3.0})):
        ka = {key(p): p for p in base if 'dev_cells' in p}
        for q in run(**kw):
            if 'dev_cells' in q and key(q) in ka:
                rev.setdefault(shift + ' ' + q['probe'], set()).add(round(q['dev_cells'] - ka[key(q)]['dev_cells'], 2))
    out['reverse'] = {kk: sorted(v) for kk, v in rev.items()}
    dump = lambda o: json.dumps(o, ensure_ascii=False, indent=1, default=lambda v: v.item())
    open(os.path.join(design, 'verify_frames_stage5.json'), 'w', encoding='utf-8').write(dump(out))
    print(dump({kk: v for kk, v in out.items() if kk != 'probes'}))


if __name__ == '__main__':
    main()
