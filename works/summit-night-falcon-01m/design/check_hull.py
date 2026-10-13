# 階段二讀數（作品落格之後）：圖紙那一邊出發的探針 ＋ 反向對照 ＋ 疊圖。
# 用法：python -I -X utf8 -B check_hull.py <design 資料夾> <作品 export format=list 的檔> [疊圖檔名後綴]
#   · 給了後綴 ⇒ 只出疊圖 overlays/stage2_work_vs_lines_<後綴>.png（重產某個時間點的樣子用；讀數不寫）。
#   · 探針點從新圖紙 01 v2 的曲面取（top(x)、DWL 半寬），⛔ 不從遮罩取（遮罩問作品永遠是「有」）。
#   · 量的是作品：每個探針位置上，肋骨最高那一格的格心離舷牆頂多少、DWL 那一層最外面的格心離船殼外面多少。
#   · 反向對照：把作品清單整份偏 3 格（z 或 y）再量一次 ⇒ 每根探針都要剛好多報 3。
import sys, os, json
import numpy as np
from PIL import Image, ImageDraw

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from draft_lines import Hull, YC, font

PROBE_X = [95, 135, 175, 215, 245]          # 肋骨站（f-16、f-08、f+00、f+08、f+14 的第一欄）
PROBE_ENDS_Z = [0, 1, 2, 3, 10, 25, 40]      # 沿艏柱前緣／艉柱後緣（中線那一格）
# 🩸 第一版只有肋骨站的探針 ⇒ 船頭底下（forefoot，x 253–261、z 0–3）作品是空的、讀數照樣全過；疊圖目視才看到。


def load(path):
    a = np.loadtxt(path, delimiter=',', dtype=int, comments='#')
    return a


def measure(H, pts, dz=0, dy=0):
    P = pts.copy(); P[:, 2] += dz; P[:, 1] += dy
    out = []
    for x in PROBE_X:
        col = P[P[:, 0] == x]
        side = col[col[:, 1] >= YC]                             # 右舷：照圖紙的中線分（⛔ 不跟著作品偏）
        ztop = side[:, 2].max() + 0.5
        top_gap = float(H.top(x + 0.5)) - ztop                  # 舷牆頂 − 肋骨頂格心
        wl = side[side[:, 2] == int(H.dwl)]
        y_out = wl[:, 1].max() + 0.5 - (YC + 0.5)               # 最外面那格的格心離圖紙中線（y 80.5）
        # 🩸 第一版減的是 YC + 0.5 + dy（偏移後的中線）⇒ 尺跟著作品一起動，反向對照 y 偏 3 報 0
        hb = float(H.hb(x + 0.5, H.dwl + 0.5))
        out.append({'x': x, 'top_gap': round(top_gap, 3), 'dwl_gap': round(hb - y_out, 3)})
    return out


def measure_ends(H, pts, dx=0):
    """中線那一格（y 80）沿艏柱、艉柱：圖紙的面 − 作品最外那格的外緣（格 k 的外緣 ＝ k+1／k）。"""
    P = pts.copy(); P[:, 0] += dx
    mid = P[P[:, 1] == YC]
    out = []
    for z in PROBE_ENDS_Z:
        row = mid[mid[:, 2] == z]
        xf = float(H.stem_face(z + 0.5)); xa = float(H.aft_limit(z + 0.5))
        out.append({'z': z, 'stem_gap': round(xf - (row[:, 0].max() + 1), 3) if len(row) else None,
                    'stern_gap': round((row[:, 0].min()) - xa, 3) if len(row) else None})
    return out


def main():
    d, lst = sys.argv[1], sys.argv[2]
    suffix = sys.argv[3] if len(sys.argv) > 3 else ''
    plan = json.load(open(os.path.join(d, 'plan.json'), encoding='utf-8'))
    H = Hull(plan)
    pts = load(lst)
    base = measure(H, pts)
    offz = measure(H, pts, dz=3)
    offy = measure(H, pts, dy=3)
    ends = measure_ends(H, pts); ends3 = measure_ends(H, pts, dx=3)
    rev_ends = [{'z': a['z'], 'stem_shift': round(a['stem_gap'] - b['stem_gap'], 3), 'stern_shift': round(b['stern_gap'] - a['stern_gap'], 3)} for a, b in zip(ends, ends3)]
    rev = [{'x': a['x'], 'top_shift': round(a['top_gap'] - b['top_gap'], 3), 'dwl_shift': round(a['dwl_gap'] - c['dwl_gap'], 3)}
           for a, b, c in zip(base, offz, offy)]
    R = {'probes': base, 'reverse_offset3': rev, 'probes_ends': ends, 'reverse_ends_offset3': rev_ends,
         'reverse_ends_all_report_3': all(abs(r['stem_shift'] - 3) < 1e-9 and abs(r['stern_shift'] - 3) < 1e-9 for r in rev_ends),
         'reverse_all_report_3': all(abs(abs(r['top_shift']) - 3) < 1e-9 and abs(abs(r['dwl_shift']) - 3) < 1e-9 for r in rev),
         'note': 'top_gap ＝ 舷牆頂 − 肋骨頂格心（照設計 0..1）；dwl_gap ＝ DWL 那層船殼外面 − 肋骨最外那格的格心（照設計 1..2：外板 1 格＋半格）'}
    # 疊圖：圖紙 01 v2 側面輪廓（線）＋ 作品從右舷看的格（每 (x,z) 有沒有）
    S = 4; W, Hh = 1640, 420; ox, base_y = 40, 380
    im = Image.new('RGB', (W, Hh), (250, 248, 242)); g = ImageDraw.Draw(im)
    g.text((20, 10), "階段二 作品（右舷看、格）疊新圖紙 01 v2 側面（線）—— 探針：x " + "、".join(str(x) for x in PROBE_X), fill=(30, 30, 30), font=font(18))
    occ = np.zeros((384, 72), bool)
    side = pts[pts[:, 1] >= YC]
    occ[side[:, 0], side[:, 2]] = True
    for xi, zi in np.argwhere(occ):
        g.rectangle([ox + xi * S, base_y - (zi + 1) * S, ox + xi * S + S - 1, base_y - zi * S - 1], fill=(180, 130, 80))
    from draft_lines import profile_points
    def P(x, z): return (ox + x * S, base_y - z * S)
    g.line(profile_points(H, P), fill=(30, 30, 30), width=2)
    for x in PROBE_X:
        g.line([P(x + 0.5, -2), P(x + 0.5, float(H.top(x + 0.5)) + 3)], fill=(200, 40, 40), width=1)
    od = os.path.join(d, '..', 'overlays'); os.makedirs(od, exist_ok=True)
    im.save(os.path.join(od, 'stage2_work_vs_lines' + ('_' + suffix if suffix else '') + '.png'), optimize=False)
    if suffix: print('overlay only'); return
    with open(os.path.join(d, 'verify_hull_post.json'), 'w', encoding='utf-8', newline='\n') as fo:
        json.dump(R, fo, ensure_ascii=False, indent=2, sort_keys=True); fo.write('\n')
    print(json.dumps(R, ensure_ascii=False, indent=1))


if __name__ == '__main__':
    main()
