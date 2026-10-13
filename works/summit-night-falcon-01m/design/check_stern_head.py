# 階段五讀數（落格之後）：讀組裝件 export list（⛔ 不讀設計陣列）。
# 用法：python -I -X utf8 -B check_stern_head.py <design 資料夾> <組裝件 export format=list 的檔>
#   · 船尾窗：x < 70 的玻璃色格 ⇒ 兩舷各自的 |dy| 範圍與 z 範圍，跟 plan 比；每一格玻璃前面（船尾那側）一格是空的（縮進）、後面一格是空的（艙房）。
#   · 窗廊：玻璃色格在 y > 100 與 y < 60 的兩群，(x, z) 一樣、y 互為 160 − y。
#   · 船首像：x > 艏柱面的格，有幾格落在圖紙的船殼體積裡（應為 0）；最前面到 x 幾。
#   · 反向對照：整份 y 偏 3 ⇒ 船尾窗右舷的 |dy| 範圍報 3。
import sys, os, json
import numpy as np

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from draft_lines import Hull, YC


def windows(pts, glass, dy_shift=0):
    P = pts.copy(); P[:, 1] += dy_shift
    g = P[(P[:, 3] == glass) & (P[:, 0] < 70) & (np.abs(P[:, 1] - YC) <= 24)]   # 🩸 第一版沒擋 |dy|：窗廊的玻璃（|dy| 30）也在 x < 70
    out = {}
    for side, m in (('S', g[:, 1] > YC), ('P', g[:, 1] < YC)):
        q = g[m]; dy = np.abs(q[:, 1] - YC)
        out[side] = {'dy': sorted(set(dy.tolist())), 'z': [int(q[:, 2].min()), int(q[:, 2].max())], 'n': int(len(q))}
    return out, g


def main():
    d, lst = sys.argv[1], sys.argv[2]
    plan = json.load(open(os.path.join(d, 'plan.json'), encoding='utf-8'))
    S = plan['stern_head']; C = S['colors']; H = Hull(plan)
    pts = np.loadtxt(lst, delimiter=',', dtype=int, comments='#')
    occ = set(map(tuple, pts[:, :3].tolist()))
    w, g = windows(pts, C['glass'])
    want_dy = sorted(set(v for a, b in S['stern_windows']['dy'] for v in range(a, b + 1)))
    # 每一欄 (y, z)：最外那格玻璃的前面（船尾那側）空、最裡那格的後面是空氣（艙房）
    # 🩸 第一版逐格算：斜面補的那格玻璃前後本來就是玻璃，數字看起來像一半不合格
    cols = {}
    for x, y, z, c in g: cols.setdefault((y, z), []).append(x)
    recess = sum(1 for (y, z), xs in cols.items() if (min(xs) - 1, y, z) not in occ)
    behind_ok = sum(1 for (y, z), xs in cols.items() if (max(xs) + 1, y, z) not in occ)
    w3, _ = windows(pts, C['glass'], dy_shift=3)
    rev = w3['S']['dy'][0] - w['S']['dy'][0]
    # 窗廊：x > 62 的玻璃（船尾窗在 x < 70，但 y 範圍不同：窗廊在船身外 |dy| ≥ 25）
    qg = pts[(pts[:, 3] == C['glass']) & (np.abs(pts[:, 1] - YC) >= 25)]
    s_set = set(map(tuple, qg[qg[:, 1] > YC][:, :3].tolist())); p_set = set(map(tuple, qg[qg[:, 1] < YC][:, :3].tolist()))
    mirror_miss = len({(x, 160 - y, z) for x, y, z in s_set} ^ p_set)
    # 船首像
    fx = pts[pts[:, 0] > 276]
    inside = 0
    for x, y, z, c in fx:
        hb = float(H.hb(x + 0.5, z + 0.5))
        if not np.isnan(hb) and abs(y - YC) <= hb: inside += 1
    R = {'stern_windows': w, 'stern_windows_dy_match': w['S']['dy'] == want_dy and w['P']['dy'] == want_dy,
         'stern_windows_z_match': w['S']['z'] == S['stern_windows']['z'] and w['P']['z'] == S['stern_windows']['z'],
         'glass_recessed_front_empty': {'ok': recess, 'of': len(cols)}, 'glass_cabin_air_behind': {'ok': behind_ok, 'of': len(cols)},
         'reverse_y3_starboard_dy_shift': rev,
         'quarter_gallery_glass': {'starboard': len(s_set), 'port': len(p_set), 'mirror_mismatch': mirror_miss},
         'figurehead': {'voxels_forward_of_x276': int(len(fx)), 'inside_hull_volume': inside, 'x_max': int(fx[:, 0].max())},
         'total_voxels': int(len(pts))}
    with open(os.path.join(d, 'verify_stern_head_post.json'), 'w', encoding='utf-8', newline='\n') as fo:
        json.dump(R, fo, ensure_ascii=False, indent=2, sort_keys=True); fo.write('\n')
    print(json.dumps(R, ensure_ascii=False))


if __name__ == '__main__':
    main()
