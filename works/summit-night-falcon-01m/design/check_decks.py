# 階段四讀數（落格之後）：讀組裝件 export list（船殼＋兩層甲板現組；⛔ 不讀設計陣列）。
# 用法：python -I -X utf8 -B check_decks.py <design 資料夾> <組裝件 export format=list 的檔>
#   · 砲門：右舷每個站附近，(x, z) 從 |dy| 4 到船外整條都是空的 ⇒ 開口；量開口的 x、z 範圍，跟 plan 算出來的比。
#   · 甲板板頂：y 88 那一欄、幾個 x，甲板最上面那一格的頂（z+1）離舷弧（加後甲板 rise）多少 —— 照設計 0..1。
#   · 艙口：開口範圍裡、甲板那幾層還剩幾格。
#   · 漏水：最低的砲門下緣以下（z < 那一格），船艙跟船外通不通。
#   · 反向對照：整份偏 3（x 一次、z 一次）⇒ 開口與板頂各報 3。
import sys, os, json
import numpy as np
from scipy import ndimage

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from draft_lines import Hull, YC

NX, NY, NZ = 384, 161, 84


def occ_of(pts, dx=0, dz=0):
    o = np.zeros((NX + 8, NY, NZ + 4), bool)
    o[pts[:, 0] + dx, pts[:, 1], pts[:, 2] + dz] = True
    return o[:NX, :, :NZ]


def ports_measured(H, plan, o):
    """開口 ＝ 右舷 (x, z) 從 |dy| 4 到船外整條空、而且上下左右 7 格內都碰得到船殼（四面圍住的洞）—— 只看作品本身。
    🩸 第一版用「船殼外面那條線上下有格」＋圖紙的船殼體積過濾：船尾 counter 底下的船外空氣被算進來；
       作品偏 3 格做反向對照時，圖紙體積跟作品對不齊，x 95 報 −7。"""
    P = plan['decks']['ports']; out = []
    line = o[:, YC + 4:, :].any(axis=1)                 # (x, z) 那條線上有沒有格
    for s in P['stations']:
        xs, zs = [], []
        for x in range(s - 8, s + 12):
            for z in range(8, 70):
                if line[x, z]: continue
                up = line[x, z + 1:z + 8].any(); dn = line[x, max(0, z - 7):z].any()
                lf = line[max(0, x - 7):x, z].any(); rt = line[x + 1:x + 8, z].any()
                if up and dn and lf and rt: xs.append(x); zs.append(z)
        out.append({'station': s, 'x': [min(xs), max(xs)] if xs else None, 'z': [min(zs), max(zs)] if zs else None})
    return out


def deck_tops(H, plan, o):
    q = plan['lines']['upper']['quarterdeck']; res = []
    for x in (80, 100, 125, 150, 200, 230, 255):
        col = o[x, YC + 8, :]          # 🩸 第一版 y 95：船頭 x 255 那裡已經是船殼那一層，量到的是舷牆頂蓋（報 −11）
        # 最上面那一塊甲板（從舷牆頂往下找第一格）
        zs = np.nonzero(col)[0]
        zt = zs.max() + 1
        ref = float(H.sheer(x + 0.5)) + (q['rise'] if x <= q['x_break'] else 0)
        res.append({'x': x, 'top_face_z': int(zt), 'sheer_ref': round(ref, 3), 'gap': round(ref - zt, 3)})
    return res


def main():
    d, lst = sys.argv[1], sys.argv[2]
    plan = json.load(open(os.path.join(d, 'plan.json'), encoding='utf-8'))
    H = Hull(plan)
    V = json.load(open(os.path.join(d, 'verify_decks.json'), encoding='utf-8'))
    pts = np.loadtxt(lst, delimiter=',', dtype=int, comments='#')
    o = occ_of(pts)
    pm = ports_measured(H, plan, o)
    want = {p['station']: p for p in V['ports']}
    pdiff = [{'station': p['station'], 'dx0': p['x'][0] - want[p['station']]['x'][0], 'dx1': p['x'][1] - want[p['station']]['x'][1],
              'dz0': p['z'][0] - want[p['station']]['z'][0], 'dz1': p['z'][1] - want[p['station']]['z'][1]} for p in pm]
    pm3 = ports_measured(H, plan, occ_of(pts, dx=3))
    rev_ports = [b['x'][0] - a['x'][0] for a, b in zip(pm, pm3)]
    dt = deck_tops(H, plan, o); dt3 = deck_tops(H, plan, occ_of(pts, dz=3))
    rev_decks = [round(a['gap'] - b['gap'], 3) for a, b in zip(dt, dt3)]
    # 艙口
    hrem = {}
    for h in plan['decks']['hatches']:
        x0, x1, w = h['x'][0], h['x'][1], h['dy']
        sub = o[x0:x1 + 1, YC - w:YC + w + 1, 25:60]   # z 25 起：主艙口底下 z ≤ 23 是插板槽頂、companion 底下 z 22–23 是艙房地板
        hrem[h['name']] = int(sub.sum())
    # 漏水：最低砲門下緣以下
    zl = min(p['z'][0] for p in V['ports'])
    x = np.arange(NX) + 0.5; z = np.arange(zl) + 0.5
    hb = H.hb(*np.meshgrid(x, z, indexing='ij'))
    dyv = np.abs(np.arange(NY) - YC)[None, :, None]
    vol = (~np.isnan(hb))[:, None, :] & (dyv <= np.nan_to_num(hb, nan=-1)[:, None, :])
    T = plan['planking']['trunk']
    X = np.arange(NX)[:, None, None]; Y = np.arange(NY)[None, :, None]; Zz = np.arange(zl)[None, None, :]
    slot = (X >= T['x'][0]) & (X <= T['x'][1]) & (Y == YC) & (Zz <= T['top_z'])
    empty = ~o[:, :, :zl]; lab, _ = ndimage.label(empty)
    hold = vol & empty & ~slot
    leak = int((hold & (lab == lab[0, 0, 0])).sum())
    R = {'ports_measured': pm, 'ports_vs_plan': pdiff, 'ports_all_match': all(v == 0 for p in pdiff for k, v in p.items() if k != 'station'),
         'reverse_ports_dx3': rev_ports, 'deck_tops': dt, 'reverse_decks_dz3': rev_decks,
         'reverse_all_report_3': all(v == 3 for v in rev_ports) and all(abs(v - 3) < 1e-9 for v in rev_decks),
         'hatches_remaining_voxels': hrem,
         'leak_below_lowest_sill': {'z_below': zl, 'hold_cells': int(hold.sum()), 'reached_from_outside': leak},
         'total_voxels': int(len(pts))}
    with open(os.path.join(d, 'verify_decks_post.json'), 'w', encoding='utf-8', newline='\n') as fo:
        json.dump(R, fo, ensure_ascii=False, indent=2, sort_keys=True); fo.write('\n')
    print(json.dumps(R, ensure_ascii=False))


if __name__ == '__main__':
    main()
