# 階段六讀數（落格之後）：讀組裝件 export list。
# 用法：python -I -X utf8 -B check_rudder_rails.py <design 資料夾> <組裝件 export format=list 的檔>
#   · 結果帳：rebuild（階段二～五）＋ 階段六清單（刻要原色對、貼要原本空；窗廊照鏡像）vs export。
#   · 船尾窗：每扇窗的每一格 (y, z)，從船尾外面（x 40）往前到艙房（x 75）之間，第一格實心在不在艙房那一頭（x ≥ 70）—— 看得進去。
#   · 窗廊窗：(x, z) 從 y 120 到 y 90 整條空（兩舷）。
#   · 舵：中線那一欄每個 z，舵後緣（從船尾往前第一格）離圖紙「艉柱面 − 舵寬」多少（照設計 −1..+1）。
#   · 欄杆：右舷金色欄杆在 x 258、x 283 的 z 範圍，跟 plan 的 from／to 比。
#   · 反向對照：整份偏 3（x 一次、z 一次、y 一次）⇒ 舵前緣、欄杆高度、船尾窗 |dy| 各報 3。
import sys, os, json
import numpy as np

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from draft_lines import Hull, YC
from draft_rudder_rails import rebuild, read_list

NX, NY, NZ = 384, 161, 90


def grid(pts, dx=0, dy=0, dz=0):
    g = np.zeros((NX + 8, NY + 8, NZ + 8), np.int16)
    g[pts[:, 0] + dx, pts[:, 1] + dy, pts[:, 2] + dz] = pts[:, 3]
    return g[:NX, :NY, :NZ]


def rudder_front(H, g, R):
    """舵的後緣（中線那一欄從船尾往前第一格實心）vs 圖紙：艉柱面 post_face(z) − 舵寬(z)。
    🩸 第一版量前緣：舵前緣貼著艉柱、兩者在水下都是 254 —— 從作品分不出哪格是舵。"""
    out = []
    for zz in (2, 6, 10, 14):
        xs = np.nonzero(g[30:75, YC, zz])[0]
        t = min(1.0, zz / max(1, R['z_taper'])); width = R['w_bottom'] + (R['w_top'] - R['w_bottom']) * t
        ref = float(H.post_face(zz + 0.5)) - width
        out.append({'z': zz, 'gap': round(int(xs.min()) + 30 - ref, 3) if len(xs) else None})
    return out


def rail_z(g, rail_col, x):
    zs = np.nonzero((g[x, YC + 1:, :] == rail_col).any(axis=0))[0]
    return [int(zs.min()), int(zs.max())] if len(zs) else None


def stern_dy(g, plan):
    W = plan['stern_head']['stern_windows']; ok = []
    for dy in range(1, 25):
        y = YC + dy; good = 0
        for zz in range(W['z'][0], W['z'][1] + 1):
            xs = np.nonzero(g[40:76, y, zz])[0]
            if len(xs) == 0 or xs.min() + 40 >= 70: good += 1
        if good == W['z'][1] - W['z'][0] + 1: ok.append(dy)
    return ok


def main():
    d, lst = sys.argv[1], sys.argv[2]
    plan = json.load(open(os.path.join(d, 'plan.json'), encoding='utf-8'))
    H = Hull(plan); RR = plan['rudder_rails']; C = RR['colors']
    V = json.load(open(os.path.join(d, 'verify_rudder_rails.json'), encoding='utf-8'))
    Wd = rebuild(d)
    key = {'hull': 'hull', 'head': 'head', 'rudder': 'rudder'}
    Wd['rudder'] = np.zeros_like(Wd['hull'])
    G = plan['stern_head']['quarter_gallery']
    for sub, L in V['stamp_order'].items():
        for o in L:
            a = read_list(os.path.join(d, o['file'])); p = a[:, :3] + np.asarray(o['origin_world'])
            tg = [Wd['gallery_S'], Wd['gallery_P']] if sub == 'quarter_gallery' else [Wd[key[sub]]]
            for k, t in enumerate(tg):
                q = p.copy()
                if k == 1: q[:, 1] = 160 - q[:, 1]
                if o['op'] == 'carvevox':
                    assert (t[tuple(q.T)] == a[:, 3]).all(); t[tuple(q.T)] = 0
                else:
                    assert (t[tuple(q.T)] == 0).all(); t[tuple(q.T)] = a[:, 3]
    want = np.zeros((NX, NY, NZ), np.int16)
    for v in Wd.values():
        assert not ((want > 0) & (v > 0)).any(); want = np.where(v > 0, v, want)
    pts = np.loadtxt(lst, delimiter=',', dtype=int, comments='#')
    got = grid(pts)
    ledger = {'design': int((want > 0).sum()), 'work': int(len(pts)), 'missing': int(((want > 0) & (got == 0)).sum()),
              'extra': int(((got > 0) & (want == 0)).sum()), 'color_diff': int(((want > 0) & (got > 0) & (want != got)).sum())}
    # 窗廊窗
    wins = []; xw = G['x'][0] + G['pilaster']
    for i in range(G['n']): wins.append((xw, xw + G['win_w'] - 1)); xw += G['win_w'] + G['pilaster']
    seeS = seeP = tot = 0
    for (xa, xb) in wins:
        for zz in range(G['win_z'][0], G['win_z'][1] + 1):
            for xx in range(xa, xb + 1):
                if zz == G['win_z'][1] and xx in (xa, xb): continue
                tot += 1; seeS += int(not got[xx, YC + 10:121, zz].any()); seeP += int(not got[xx, 40:YC - 9, zz].any())
    want_dy = sorted(set(v for a, b in plan['stern_head']['stern_windows']['dy'] for v in range(a, b + 1)))
    sd = stern_dy(got, plan); sd3 = stern_dy(grid(pts, dy=3), plan)
    rf = rudder_front(H, got, RR['rudder']); rf3 = rudder_front(H, grid(pts, dx=3), RR['rudder'])
    rz = np.nonzero((got[:, YC, :] == C['bottom']) | (got[:, YC, :] == C['black']))
    rud_cells = np.argwhere(Wd['rudder'] > 0)
    up = rail_z(got, C['rail'], 258), rail_z(got, C['rail'], 283)
    up3 = rail_z(grid(pts, dz=3), C['rail'], 258), rail_z(grid(pts, dz=3), C['rail'], 283)
    R = {'ledger': ledger,
         'stern_windows_open_dy': sd, 'stern_windows_open_match': sd == want_dy,
         'gallery_windows_see_through': {'starboard': seeS, 'port': seeP, 'of': tot},
         'rudder_aft_edge_vs_drawing': rf, 'rudder_z_range_from_design_cells': [int(rud_cells[:, 2].min()), int(rud_cells[:, 2].max())],
         'rails_z_at_x258_x283': up,
         'reverse_offset3': {'rudder_aft_edge_dx': [round(a['gap'] - b['gap'], 3) for a, b in zip(rf, rf3)],
                             'rails_dz': [up3[0][0] - up[0][0], up3[1][0] - up[1][0]],
                             'stern_dy': (sd3[0] - sd[0]) if sd and sd3 else None}}
    R['reverse_all_report_3'] = all(abs(abs(v) - 3) < 1e-9 for v in R['reverse_offset3']['rudder_aft_edge_dx']) and R['reverse_offset3']['rails_dz'] == [3, 3] and R['reverse_offset3']['stern_dy'] == 3
    with open(os.path.join(d, 'verify_rudder_rails_post.json'), 'w', encoding='utf-8', newline='\n') as fo:
        json.dump(R, fo, ensure_ascii=False, indent=2, sort_keys=True); fo.write('\n')
    print(json.dumps(R, ensure_ascii=False))


if __name__ == '__main__':
    main()
