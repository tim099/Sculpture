# 階段七讀數（落格之後）：讀組裝件 export list。
# 用法：python -I -X utf8 -B check_masts.py <design 資料夾> <組裝件 export format=list 的檔>
#   · 結果帳：nf_state.state_after('stage7') vs export。
#   · 桅軸：每根桅在幾個高度，以圖紙的軸（桅孔中心 ＋ 後傾）為中心、±6 格的窗裡取格的 x 平均，跟圖紙比（應 < 0.5 格）。
#     窗只用來切出那一根桅，量的是作品的格。
#   · 艏斜桅：x 300 那一欄、中線、177 色格的 z 平均 vs 圖紙那條 22° 線。
#   · 反向對照：整份偏 3（x 一次、z 一次）⇒ 桅軸、艏斜桅各報 3。
import sys, os, json, math
import numpy as np

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from draft_lines import YC
from nf_state import state_after, NX, NY, NZ


def grid(pts, dx=0, dz=0):
    g = np.zeros((NX + 8, NY, NZ + 8), np.int16)
    g[pts[:, 0] + dx, pts[:, 1], pts[:, 2] + dz] = pts[:, 3]
    return g[:NX, :, :NZ]


def mast_axes(g, M, rig):
    out = []
    for name in ('fore', 'main'):
        S = M[name]; a = math.radians(S['rake_deg']); zd = rig[name]['zdeck']
        for z in (zd + 10, zd + 60, S['top_z'] - 6):
            ref = S['x'] + 0.5 - (z - zd) * math.tan(a)
            lo = int(ref - 6); xs = np.nonzero(g[lo:lo + 13, YC, z] == M['colors']['spar'])[0]
            out.append({'mast': name, 'z': z, 'ref_x': round(ref, 3), 'got_x': round(float(xs.mean() + lo + 0.5), 3) if len(xs) else None})
    return out


def bowsprit_z(g, M, rig):
    B = rig['bowsprit']; x = 300
    t = (x + 0.5 - B['heel'][0]) / (B['end'][0] - B['heel'][0])
    ref = B['heel'][2] + t * (B['end'][2] - B['heel'][2])
    zs = np.nonzero(g[x, YC, :] == M['colors']['spar'])[0]
    zs = zs[np.abs(zs + 0.5 - ref) < 5]
    return {'x': x, 'ref_z': round(ref, 3), 'got_z': round(float(zs.mean() + 0.5), 3) if len(zs) else None}


def main():
    d, lst = sys.argv[1], sys.argv[2]
    plan = json.load(open(os.path.join(d, 'plan.json'), encoding='utf-8'))
    M = plan['masts']
    V = json.load(open(os.path.join(d, 'verify_masts.json'), encoding='utf-8')); rig = V['rig_points']
    W = state_after(d, 'stage7')
    want = np.zeros((NX, NY, NZ), np.int16)
    for k, v in W.items():
        assert not ((want > 0) & (v > 0)).any(), k
        want = np.where(v > 0, v, want)
    pts = np.loadtxt(lst, delimiter=',', dtype=int, comments='#')
    got = grid(pts)
    ledger = {'design': int((want > 0).sum()), 'work': int(len(pts)), 'missing': int(((want > 0) & (got == 0)).sum()),
              'extra': int(((got > 0) & (want == 0)).sum()), 'color_diff': int(((want > 0) & (got > 0) & (want != got)).sum())}
    ma = mast_axes(got, M, rig); ma3 = mast_axes(grid(pts, dx=3), M, rig)
    bz = bowsprit_z(got, M, rig); bz3 = bowsprit_z(grid(pts, dz=3), M, rig)
    rev = [round(b['got_x'] - a['got_x'], 3) for a, b in zip(ma, ma3)] + [round(bz3['got_z'] - bz['got_z'], 3)]
    R = {'ledger': ledger, 'mast_axes': ma, 'mast_axis_max_err': round(max(abs(m['got_x'] - m['ref_x']) for m in ma), 3),
         'bowsprit': bz, 'bowsprit_err': round(abs(bz['got_z'] - bz['ref_z']), 3),
         'reverse_offset3': rev, 'reverse_all_report_3': all(abs(v - 3) < 1e-9 for v in rev)}
    with open(os.path.join(d, 'verify_masts_post.json'), 'w', encoding='utf-8', newline='\n') as fo:
        json.dump(R, fo, ensure_ascii=False, indent=2, sort_keys=True); fo.write('\n')
    print(json.dumps(R, ensure_ascii=False))


if __name__ == '__main__':
    main()
