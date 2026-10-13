# 階段二讀數（作品落格之後）：結果帳 ＋ 圖紙那一邊出發的探針 ＋ 反向對照 ＋ 疊圖。
# 用法：python -I -X utf8 -B check_hull.py <design 資料夾> <作品 export format=list 的檔>
#   · 從夜隼號 check_hull.py（TASK-0529 階段二）改：框、中線讀 plan.frame；結果帳併進來（stamp_order 的聯集 vs 作品清單，含顏色）。
#   · 探針點從新圖紙 01 的曲面取（top(x)、DWL 半寬、艏柱前緣、艉柱後緣），⛔ 不從遮罩取（遮罩問作品永遠是「有」）。
#   · 量的是作品：每個探針位置上，肋骨最高那一格的格心離舷牆頂多少、DWL 那一層最外面的格心離船殼外面多少；中線那一格離艏柱前緣／艉柱後緣多少。
#   · 反向對照：把作品清單整份偏 3 格（z、y、x）再量一次 ⇒ 每根探針都要剛好多報 3。基準一律是圖紙（夜隼號 🩸：拿偏移後的中線當基準，尺跟著作品動，報 0）。
import sys, os, json
import numpy as np
from PIL import Image, ImageDraw

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from draft_lines import Hull, font, profile_points

PROBE_X = [160, 230, 300, 370, 440, 503]          # 肋骨站 f-20、f-10、f+00、f+10、f+20、f+29 的第一欄
PROBE_ENDS_Z = [0, 2, 5, 10, 30, 50, 78]          # 沿艏柱前緣／艉柱後緣（中線那一格）；78 ＝ 翼艉板下面


def measure(H, pts, dz=0, dy=0):
    P = pts.copy(); P[:, 2] += dz; P[:, 1] += dy
    out = []
    for x in PROBE_X:
        col = P[P[:, 0] == x]
        side = col[col[:, 1] >= H.YC]
        ztop = side[:, 2].max() + 0.5
        wl = side[side[:, 2] == int(H.dwl)]
        y_out = wl[:, 1].max() + 0.5 - (H.YC + 0.5)
        hb = float(H.hb(x + 0.5, H.dwl + 0.5))
        out.append({'x': x, 'top_gap': round(float(H.top(x + 0.5)) - ztop, 3), 'dwl_gap': round(hb - y_out, 3)})
    return out


def measure_ends(H, pts, dx=0):
    P = pts.copy(); P[:, 0] += dx
    mid = P[P[:, 1] == H.YC]
    out = []
    for z in PROBE_ENDS_Z:
        row = mid[mid[:, 2] == z]
        xf = float(H.stem_face(z + 0.5)); xa = float(H.aft_limit(z + 0.5))
        out.append({'z': z, 'stem_gap': round(xf - (row[:, 0].max() + 1), 3) if len(row) else None,
                    'stern_gap': round(row[:, 0].min() - xa, 3) if len(row) else None})
    return out


def ledger(d, V, work):
    exp = {}
    for o in V['stamp_order']:
        a = np.loadtxt(os.path.join(d, o['file']), delimiter=',', dtype=int, comments='#', ndmin=2)
        for x, y, z, c in a:
            k = (int(x), int(y), int(z))
            if k in exp: raise ValueError('清單之間重複：%s' % (k,))
            exp[k] = int(c)
    got = {(int(x), int(y), int(z)): int(c) for x, y, z, c in work}
    miss = [k for k in exp if k not in got]; extra = [k for k in got if k not in exp]
    diffc = [k for k in exp if k in got and got[k] != exp[k]]
    return {'expected': len(exp), 'work': len(got), 'missing': len(miss), 'extra': len(extra), 'color_diff': len(diffc)}


def main():
    d, lst = sys.argv[1], sys.argv[2]
    plan = json.load(open(os.path.join(d, 'plan.json'), encoding='utf-8'))
    H = Hull(plan)
    work = np.loadtxt(lst, delimiter=',', dtype=int, comments='#', ndmin=2)
    V = json.load(open(os.path.join(d, 'verify_hull.json'), encoding='utf-8'))
    pts = work[:, :3]
    base = measure(H, pts); offz = measure(H, pts, dz=3); offy = measure(H, pts, dy=3)
    ends = measure_ends(H, pts); ends3 = measure_ends(H, pts, dx=3)
    rev = [{'x': a['x'], 'top_shift': round(a['top_gap'] - b['top_gap'], 3), 'dwl_shift': round(a['dwl_gap'] - c['dwl_gap'], 3)} for a, b, c in zip(base, offz, offy)]
    rev_ends = [{'z': a['z'], 'stem_shift': round(a['stem_gap'] - b['stem_gap'], 3), 'stern_shift': round(b['stern_gap'] - a['stern_gap'], 3)} for a, b in zip(ends, ends3)]
    R = {'ledger': ledger(d, V, work),
         'probes': base, 'reverse_offset3': rev, 'probes_ends': ends, 'reverse_ends_offset3': rev_ends,
         'reverse_all_report_3': all(abs(abs(r['top_shift']) - 3) < 1e-9 and abs(abs(r['dwl_shift']) - 3) < 1e-9 for r in rev),
         'reverse_ends_all_report_3': all(abs(r['stem_shift'] - 3) < 1e-9 and abs(r['stern_shift'] - 3) < 1e-9 for r in rev_ends),
         'note': 'top_gap ＝ 舷牆頂 − 肋骨頂格心（照設計 0..1）；dwl_gap ＝ DWL 那層船殼外面 − 肋骨最外那格的格心（照設計 1..2：外板 1 格＋半格）；stem／stern_gap ＝ 圖紙的面 − 作品最外那格的外緣'}
    # 疊圖：圖紙 01 側面輪廓（線）＋ 作品從右舷看的格
    S = 2.0; W, Hh = 1540, 420; ox, base_y = 20, 395
    im = Image.new('RGB', (W, Hh), (250, 248, 242)); g = ImageDraw.Draw(im)
    g.text((20, 8), "階段二 作品（右舷看、格）疊新圖紙 01 側面（線）—— 紅線 ＝ 探針 x " + "、".join(str(x) for x in PROBE_X), fill=(30, 30, 30), font=font(16))
    occ = np.zeros((H.NX, H.NZ), bool)
    side = pts[pts[:, 1] >= H.YC]
    occ[side[:, 0], side[:, 2]] = True
    for xi, zi in np.argwhere(occ):
        g.rectangle([ox + xi * S, base_y - (zi + 1) * S, ox + xi * S + S - 1, base_y - zi * S - 1], fill=(180, 130, 80))
    def P(x, z): return (ox + x * S, base_y - z * S)
    g.line(profile_points(H, P), fill=(30, 30, 30), width=1)
    for x in PROBE_X:
        g.line([P(x + 0.5, -2), P(x + 0.5, float(H.top(x + 0.5)) + 3)], fill=(200, 40, 40), width=1)
    od = os.path.join(d, '..', 'overlays'); os.makedirs(od, exist_ok=True)
    im.save(os.path.join(od, 'stage2_work_vs_lines.png'), optimize=False)
    with open(os.path.join(d, 'verify_hull_post.json'), 'w', encoding='utf-8', newline='\n') as fo:
        json.dump(R, fo, ensure_ascii=False, indent=2, sort_keys=True); fo.write('\n')
    print(json.dumps(R, ensure_ascii=False, indent=1))


if __name__ == '__main__':
    main()
