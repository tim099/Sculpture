# 階段八讀數（落格之後）：讀引擎匯出的東西 —— 六件帆桁子作品與兩件桅的 export list、組裝件 export list、組裝件 export parts。
# 用法：python -I -X utf8 -B check_yards.py <design 資料夾> <匯出資料夾>
#   匯出資料夾裡：yard-<帆桁>.list.txt、mast-fore／mast-main.list.txt、assembly.list.txt、parts.json
#   · 結果帳：每件子作品 export vs masks/yards 清單（缺、多、顏色不同）。
#   · 固定點：引擎轉過的點（parts 的 models[].points，組裝件座標）vs 我這邊 rot() 算的 anchors_expect —— 兩條路算同一個旋轉。
#   · 從圖紙取的探針（plan 的數字，不讀 draft 的結果）：
#       方帆桁 —— 中線那一排的高度 vs z_ref＋z_off；y 的長度 vs 型寬 × 比例；背面離桅最前格的空隙（應 0）。
#       gaff／boom —— 引擎點 pivot→peak、pivot→end 的仰角（pivot 在桿的軸線上） vs plan；boom 尾端 x vs 組裝件最後一格 − overhang；boom 下緣離底下最高那一格（≥ clear_below）。
#   · 反向對照：子作品整份 x 偏 3 ⇒ 空隙報 3；z 偏 3 ⇒ 高度報 3；peak 繞 pivot 多轉 3° ⇒ 仰角報 3。
import sys, os, json, math
import numpy as np

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from draft_lines import YC
from draft_yards import odd, rot


def load(p):
    return np.loadtxt(p, delimiter=',', dtype=int, comments='#', ndmin=2)


def sq_probe(P, Y, plan, cells, mast, dx=0, dz=0):
    """cells：子作品座標；P：placement（origin）。回傳 高度、長度、空隙。"""
    w = cells[:, :3] + np.asarray(P['origin']) + np.array([dx, 0, dz])
    S = plan['masts'][Y['mast']]
    zplan = {'top': S['top_z'], 'crosstrees': S['topmast_head_z'] - S['tm_doubling'], 'truck': S['truck_z']}[Y['z_ref']] + Y['z_off']
    c = w[w[:, 1] == YC]
    zc = float(c[:, 2].mean())
    L = int(w[:, 1].max() - w[:, 1].min() + 1)
    Lp = odd(odd(plan['yards']['beam'] * plan['yards']['course_over_beam']) * Y['over_course'])
    rows = np.unique(c[:, 2])
    mrow = mast[(mast[:, 1] == YC) & np.isin(mast[:, 2], rows)]
    front = int(mrow[:, 0].max())
    gap = int(c[:, 0].min()) - front - 1
    return {'z': round(zc, 3), 'z_plan': zplan, 'z_err': round(zc - zplan, 3), 'length': L, 'length_plan': Lp, 'gap_to_mast': gap}


def elev(a, b):
    return math.degrees(math.atan2(b[2] - a[2], a[0] - b[0]))


def main():
    d, ex = sys.argv[1], sys.argv[2]
    plan = json.load(open(os.path.join(d, 'plan.json'), encoding='utf-8'))
    V = json.load(open(os.path.join(d, 'verify_yards.json'), encoding='utf-8'))
    parts = json.load(open(os.path.join(ex, 'parts.json'), encoding='utf-8'))
    mast = {m: load(os.path.join(ex, 'mast-%s.list.txt' % m)) for m in ('fore', 'main')}
    asm = load(os.path.join(ex, 'assembly.list.txt'))
    PL = {p['member']: p for p in V['placements']}
    SQ = {Y['name']: Y for Y in plan['yards']['square']}
    R = {'ledger': {}, 'square': {}, 'reverse': {}}
    # 結果帳
    for nm, P in PL.items():
        want = {tuple(r[:3]): r[3] for r in load(os.path.join(d, P['file']))}
        got = {tuple(r[:3]): r[3] for r in load(os.path.join(ex, 'yard-%s.list.txt' % nm))}
        R['ledger'][nm] = {'list': len(want), 'work': len(got), 'missing': sum(1 for k in want if k not in got),
                           'extra': sum(1 for k in got if k not in want), 'color_diff': sum(1 for k in want if k in got and got[k] != want[k])}
    # 固定點：引擎 vs rot()
    eng = {m['name'][len('yard-'):]: m for m in parts['models']}
    dev = []; n = 0
    for nm, E in V['anchors_expect'].items():
        pts = eng[nm]['points']
        assert set(pts) == set(E), (nm, set(pts) ^ set(E))
        for a, q in E.items():
            dev.append(math.dist(pts[a], q)); n += 1
    R['anchors'] = {'compared': n, 'max_dev': round(max(dev), 6), 'models': len(parts['models']), 'models_ok': sum(1 for m in parts['models'] if m['state'] == 'ok'),
                    'meta_kind_yard': sum(1 for m in parts['models'] if m['meta'].get('kind') == 'yard')}
    # 方帆桁
    for nm, Y in SQ.items():
        c = load(os.path.join(ex, 'yard-%s.list.txt' % nm))
        R['square'][nm] = sq_probe(PL[nm], Y, plan, c, mast[Y['mast']])
        a = sq_probe(PL[nm], Y, plan, c, mast[Y['mast']], dx=3); b = sq_probe(PL[nm], Y, plan, c, mast[Y['mast']], dz=3)
        R['reverse'][nm] = [a['gap_to_mast'] - R['square'][nm]['gap_to_mast'], round(b['z'] - R['square'][nm]['z'], 3)]
    # gaff／boom
    G, B = plan['yards']['gaff'], plan['yards']['boom']
    gp, bp = eng['main-gaff']['points'], eng['main-boom']['points']
    ga = elev(gp['pivot'], gp['peak']); ba = elev(bp['pivot'], bp['end'])    # 🩸 第一版用 throat→peak：throat 在桿頂面、peak 在軸上 ⇒ 讀 34.2°；軸線過 pivot
    x_stern = int(asm[:, 0].min())
    # boom 下緣：引擎的 jaws→end 線上每一格 x，中心 z − 半徑（plan）vs 組裝件在那一欄 |dy| ≤ 3 最高那一格的頂面
    rb = plan['masts']['main']['r_lower'][0] * B['d_over_mast']
    col = {}
    for x, y, z, c in asm:
        if abs(y - YC) <= 3: col.setdefault(int(x), []).append(int(z))
    worst = None
    L = math.dist(bp['jaws'], bp['end'])
    for x in range(int(math.ceil(bp['end'][0])), int(bp['jaws'][0]) - 3):
        t = (bp['jaws'][0] - (x + 0.5)) / (bp['jaws'][0] - bp['end'][0])
        zc = bp['jaws'][2] + t * (bp['end'][2] - bp['jaws'][2])
        r = rb * (1 + (B['taper_end'] - 1) * t)
        below = [z for z in col.get(x, []) if z < zc]                      # 🩸 第一版取整欄最高 ⇒ 撞到 boom 上面的主桅（後傾到 x 141）
        if below:
            g = (zc - r) - (max(below) + 1)
            if worst is None or g < worst[0]: worst = (round(float(g), 3), int(x), int(max(below)))
    peak3 = rot(gp['peak'], gp['pivot'], 3, 0)
    R['gaff_boom'] = {'gaff_elev_deg': round(ga, 4), 'gaff_plan': G['angle_deg'], 'boom_elev_deg': round(ba, 4), 'boom_plan': B['angle_deg'],
                      'boom_end_x': round(bp['end'][0], 3), 'boom_end_plan': x_stern - B['overhang'], 'x_stern_assembly': x_stern,
                      'boom_min_clearance': worst, 'clear_plan': B['clear_below']}
    R['reverse']['gaff_elev'] = round(elev(gp['pivot'], peak3) - ga, 4)
    flat = [v for k, v in R['reverse'].items() if k != 'gaff_elev' for v in v] + [R['reverse']['gaff_elev']]
    R['reverse_all_report_3'] = all(abs(v - 3) < 0.05 for v in flat)
    R['assembly_voxels'] = int(len(asm))
    with open(os.path.join(d, 'verify_yards_post.json'), 'w', encoding='utf-8', newline='\n') as fo:
        json.dump(R, fo, ensure_ascii=False, indent=2, sort_keys=True); fo.write('\n')
    print(json.dumps(R, ensure_ascii=False, indent=1))


if __name__ == '__main__':
    main()
