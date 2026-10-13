# 階段六 船頭船尾骨架的讀數（TASK-0538）：結果帳＋探針＋反向對照 ⇒ verify_ends_stage6.json
# 用法：python -I ends_check.py <design 資料夾> <export list 檔>
#   · 結果帳：作品 export list 逐格對階段一～六全部清單（含顏色）。
#   · 原圖探針（原圖重新找線心）：船尾落在站上的四片（16、20、22、24）外緣 vs 橫切面圖那一站。
#   · 作品＝設計（不是原圖）：船頭各片外緣 vs 船殼 molded（Ship.hb）；船尾板後面 vs 船尾輪廓（stern_outline）。
#   · 反向對照：半寬偏 3 格／X 偏 3 格。
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
    Sc = plan['scale']
    X0, Zk = Sc['X_of_x0'], Sc['Z_of_keel_top']
    work = read_list(lst)
    des = {}
    groups = (('keel', ('shoe', 'keel')), ('posts', ('sternpost', 'inner_post', 'stem', 'gripe')),
              ('deadwood', ('aft_deadwood', 'fore_deadwood', 'apron')))
    for sub, parts in groups:
        for p in parts:
            des.update(read_list(os.path.join(design, 'masks', sub, p + '.vox.txt')))
    for sub in ('floors', 'frames', 'ends'):
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
    ox, oy = 7000, 1000
    dark = ~np.array(Image.open(plate).crop((ox, oy, 9900, 4300)))
    pxm = R['px_per_m']
    bpc, bpk = B['body_plan']['centre_px'], B['body_plan']['keel_top_py']
    E = plan['ends']
    ends = {fn[:-8]: set(read_list(os.path.join(design, 'masks', 'ends', fn))) for fn in os.listdir(os.path.join(design, 'masks', 'ends'))}

    def run(dY=0.0, dX=0.0):
        res = []
        for n, sname in ((-16, '16'), (-20, '20'), (-22, '22'), (-24, '24')):
            cs = ends['r%+03d' % n]
            Xc = sorted({x for (x, y, z) in cs})[1]
            sec = np.array(B['body_plan']['sections_z_hb'][sname], float)
            col = {(y, z) for (x, y, z) in cs if x == Xc and y <= 160}
            for Zc in sorted({z for (y, z) in col})[::3]:
                zc = (Zc + 0.5 - Zk) / cpm
                if zc > min(9.5, sec[-1, 0]) or zc < 1.0:
                    continue
                dys = [160 - y for (y, z) in col if z == Zc]
                hexp = float(np.interp(zc, sec[:, 0], sec[:, 1]))
                if hexp < 0.4:
                    continue
                py = int(round(bpk - zc * pxm))
                pxe = bpc - hexp * pxm
                row = dark[py - oy, int(pxe) - 10 - ox:int(pxe) + 10 - ox]
                g = nearest_run(row, int(pxe) - 10, pxe, 8)
                if g is None:
                    res.append({'probe': 'aft_frame_outer_vs_section', 'n': n, 'Z': Zc, 'note': '這一列找不到線（±10 px）'})
                    continue
                Hw = (bpc - g) / pxm * cpm + dY
                face = max(dys) + 0.5
                res.append({'probe': 'aft_frame_outer_vs_section', 'n': n, 'Z': Zc, 'line_px': round(float(g), 1), 'work_hb_cells': round(Hw, 2), 'face_hb_cells': face, 'dev_cells': round(Hw - face, 2)})
        # 作品＝設計：船頭各片外緣 vs Ship.hb（同一欄、同一層）
        for n in range(E['fore_n'][0], E['fore_n'][1] + 1):
            name = 'r%+03d' % n
            if name not in ends:
                continue
            cs = ends[name]
            Xc = sorted({x for (x, y, z) in cs})[1]
            x = (Xc + 0.5 - X0) / cpm
            for Zc in sorted({z for (xx, y, z) in cs if xx == Xc})[::4]:
                zc = (Zc + 0.5 - Zk) / cpm
                hb = float(ship.hb(np.array([x]), zc)[0])
                if not np.isfinite(hb):
                    continue
                dys = [abs(y - 160) for (xx, y, z) in cs if xx == Xc and z == Zc]
                res.append({'probe': 'fore_frame_outer_vs_design', 'n': n, 'Z': Zc, 'design_hb_cells': round(hb * cpm + dY, 2), 'face_hb_cells': max(dys) + 0.5,
                            'dev_cells': round(hb * cpm + dY - (max(dys) + 0.5), 2)})
        # 作品＝設計：船尾板後面 vs 船尾輪廓
        st = ends['stern_timbers'] | ends['wing_transom'] | ends.get('r-28', set()) | ends.get('r-29', set()) | ends.get('r-30', set())
        for Zc in sorted({z for (x, y, z) in ends['stern_timbers']})[::4]:
            zc = (Zc + 0.5 - Zk) / cpm
            xa = float(ship.stern_x_of_z(min(zc, ship.stern_outline[-1, 1])))
            xsz = [x for (x, y, z) in st if z == Zc and y == 160]
            if not xsz:
                continue
            res.append({'probe': 'stern_face_vs_outline', 'Z': Zc, 'design_X': round(X0 + xa * cpm + dX, 2), 'face_X': min(xsz),
                        'dev_cells': round(X0 + xa * cpm + dX - min(xsz), 2)})
        return res

    base = run()
    out['probes'] = base
    summ = {}
    for name in ('aft_frame_outer_vs_section', 'fore_frame_outer_vs_design', 'stern_face_vs_outline'):
        d = [p['dev_cells'] for p in base if p['probe'] == name and 'dev_cells' in p]
        summ[name] = {'n': len(d), 'skipped': sum(1 for p in base if p['probe'] == name and 'dev_cells' not in p),
                      'min': round(min(d), 2) if d else None, 'max': round(max(d), 2) if d else None,
                      'mean_abs': round(float(np.mean(np.abs(d))), 2) if d else None}
    out['probe_summary'] = summ
    key = lambda p: (p['probe'], p.get('n'), p.get('Z'))
    rev = {}
    for shift, kw in (('Y+3', {'dY': 3.0}), ('X+3', {'dX': 3.0})):
        ka = {key(p): p for p in base if 'dev_cells' in p}
        for q in run(**kw):
            if 'dev_cells' in q and key(q) in ka:
                rev.setdefault(shift + ' ' + q['probe'], set()).add(round(q['dev_cells'] - ka[key(q)]['dev_cells'], 2))
    out['reverse'] = {kk: sorted(v) for kk, v in rev.items()}
    dump = lambda o: json.dumps(o, ensure_ascii=False, indent=1, default=lambda v: v.item())
    open(os.path.join(design, 'verify_ends_stage6.json'), 'w', encoding='utf-8').write(dump(out))
    print(dump({kk: v for kk, v in out.items() if kk != 'probes'}))


if __name__ == '__main__':
    main()
