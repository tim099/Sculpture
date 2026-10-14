# 階段七 外板・wale・塗裝・吃水刻度的讀數（TASK-0538）：結果帳＋獨立對照＋反向對照 ⇒ verify_planking_stage7.json
# 用法：python -I planking_check.py <design 資料夾> <export list 檔>
#   · 結果帳：作品（或草稿）export list 逐格對階段一～六清單 ＋ 階段七清單（照落子順序蓋上去，含顏色）。
#   · 獨立對照（另一張圖）：船中那一欄外板外緣 vs 半寬圖船中那一欄的「最大寬」線 5.15 —— 外板取 1 格（0.078 底圖 m）、原圖 0.13，預期短 ≈ 0.05。
#   · 刻度：每個數字的白格數 ＝ 字形格數；鏡像差（位置 0、顏色只在刻度）。
#   · 反向對照：外板往外偏 3 格 ⇒ 船中外緣那組報 +3 格。
import sys, os, json
import numpy as np

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.dirname(HERE))
from draft_planking import read_list, GLYPH   # noqa: E402
import draft_lines as DL   # noqa: E402

ORDER = ['paint_struct', 'fill_cavities', 'plank_x040_149', 'plank_x150_249', 'plank_x250_349', 'plank_x350_449',
         'plank_x450_549', 'plank_x550_699', 'wales']


def compare(a, b):
    return (sum(1 for k in a if k not in b), sum(1 for k in b if k not in a),
            sum(1 for k, c in a.items() if k in b and b[k] != c))


def main():
    design, lst = sys.argv[1], sys.argv[2]
    plan, R, B, ship = DL.load(design)
    xs, zs, T, hb_max, _ = DL.hull_table(ship)
    k, cpm, X, Z, Yh = DL.scale_of(plan, ship, hb_max)
    P = plan['planking']
    work = read_list(lst)
    des = {}
    for sub in ('keel', 'posts', 'deadwood', 'floors', 'frames', 'ends'):
        for fn in sorted(os.listdir(os.path.join(design, 'masks', sub))):
            des.update(read_list(os.path.join(design, 'masks', sub, fn)))
    plank = {}
    for n in ORDER:
        p = os.path.join(design, 'masks', 'planking', n + '.vox.txt')
        if os.path.exists(p):
            L = read_list(p)
            des.update(L)
            if n != 'paint_struct' and n != 'fill_cavities':
                plank.update(L)
    out = {'work_cells': len(work), 'design_cells': len(des)}
    w2 = dict(work)
    del w2[next(iter(des))]
    w2[list(des)[-1]] = 1
    out['ruler_check'] = {'drop_one_and_recolor_one': compare(des, w2), 'expect': [1, 0, 1]}
    m, e, c = compare(des, work)
    out['ledger'] = {'missing': m, 'extra': e, 'color_diff': c}

    # 獨立對照：船中站那一欄（x 18.919），外板最外那一格的外緣（底圖 m）vs 半寬圖
    Xm = int(round(float(X(18.919))))
    line = 5.15

    def midship(dy_shift=0):
        dys = [abs(y - 160) + dy_shift for (x, y, z) in plank if x == Xm]
        face = (max(dys) + 0.5) / cpm
        return {'X': Xm, 'plank_outer_m': round(face, 3), 'half_breadth_line_m': line,
                'diff_m': round(face - line, 3), 'diff_cells': round((face - line) * cpm, 2)}
    out['midship_vs_half_breadth'] = midship()
    out['midship_vs_half_breadth']['expect'] = '外板 1 格 0.078 vs 原圖 0.13 ⇒ 約 −0.05 m（−0.67 格）'
    out['reverse_control'] = {'plank_out_3_cells': midship(3), 'expect_diff_cells_change': 3.0}

    # 刻度：白格數、鏡像
    white = {(x, y, z) for (x, y, z), c in work.items() if c == P['colors']['marks']}
    per = sum(sum(r.count('1') for r in GLYPH[ch]) for n in P['draft_marks']['meters'] for ch in str(n))
    out['marks'] = {'white_cells': len(white),
                    'expect': per * len(P['draft_marks']['where']) * len(P['draft_marks']['sides'])}
    pos = sum(1 for (x, y, z) in work if (x, 320 - y, z) not in work)
    col = sum(1 for (x, y, z), c in work.items() if (x, 320 - y, z) in work and work[(x, 320 - y, z)] != c)
    out['mirror'] = {'position_missing': pos, 'color_diff_cells': col, 'expect_color_diff_cells': len(white ^ {(x, 320 - y, z) for (x, y, z) in white})}
    dump = lambda o: json.dumps(o, ensure_ascii=False, indent=1, default=lambda v: v.item())
    open(os.path.join(design, 'verify_planking_stage7.json'), 'w', encoding='utf-8').write(dump(out))
    print(dump(out))


if __name__ == '__main__':
    main()
