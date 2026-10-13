# 階段九讀數（落格之後）：讀引擎匯出的東西 —— 組裝件 export list、channels 子作品 export list、組裝件 sub=ropes 的輸出（存成文字檔）。
# 用法：python -I -X utf8 -B check_rigging.py <design 資料夾> <匯出資料夾>
#   匯出資料夾裡：assembly.list.txt、channels.list.txt、ropes.txt（senate cmd sculpture op=work sub=ropes 的 stdout）
#   · 結果帳：nf_state.state_after('stage9') vs 組裝件 export。
#   · deadeye（從圖紙取的探針）：組裝件裡 104 色、在兩段 channel 的 x 範圍、|dy| > 20 的格，按舷、按 x 分群 ⇒ 每群的 x 中心 vs plan（桅孔 x ＋ first_fwd − spacing·i）；每群格數。
#   · chain plate：73 色，每一欄（x、舷）最低那一格的內側（往中線一格）是不是實心 ＝ 釘在船殼上；channels 子作品 6 連通幾塊。
#   · 繩：引擎解出來的兩端（印到 0.1）與長度（0.01）vs 我這邊算的 —— 兩條路解同一個端點（固定點格心、子繩比例）。
#   · 淨空：bobstay 與 stays 的中段離最近實心格心的距離（EDT），最小值。
#   · 反向對照：deadeye 探針整份 x 偏 3 ⇒ 報 3；繩的預期端點偏 3 ⇒ 報 3。
import sys, os, json, re, math
import numpy as np
from scipy import ndimage

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from draft_lines import YC
from nf_state import state_after, NX, NY, NZ


def load(p):
    return np.loadtxt(p, delimiter=',', dtype=int, comments='#', ndmin=2)


def deadeye_probe(pts, plan, dx=0):
    R = plan['rigging']['channels_v2']; out = {}
    # 🩸 第一版只認顏色：104 也是舷牆頂蓋（整條船長）⇒ 五顆併成一群。deadeye 在船殼外（|dy| ≥ 33；船殼外板最外 |dy| ≈ 30–31）
    de = pts[(pts[:, 3] == plan['rigging']['deadeye']['color']) & (np.abs(pts[:, 1] - YC) >= 33)]
    for m in ('fore', 'main'):
        want = [plan['masts'][m]['x'] + R['first_fwd_of_mast'] - R['spacing'] * i for i in range(R['deadeyes'])]
        for side, sel in (('S', de[:, 1] > YC + 20), ('P', de[:, 1] < YC - 20)):
            c = de[sel & (de[:, 0] >= min(want) - 3) & (de[:, 0] <= max(want) + 3)]
            xs = np.unique(c[:, 0] + dx)
            groups = np.split(xs, np.nonzero(np.diff(xs) > 1)[0] + 1)
            got = [float(np.mean(c[(c[:, 0] + dx >= g[0]) & (c[:, 0] + dx <= g[-1])][:, 0] + dx)) for g in groups]
            n = [int(((c[:, 0] + dx >= g[0]) & (c[:, 0] + dx <= g[-1])).sum()) for g in groups]
            got = sorted(got, reverse=True)
            out[m + '-' + side] = {'plan_x': want, 'got_x': [round(v, 3) for v in got], 'cells': n,
                                   'max_err': round(max(abs(a - b) for a, b in zip(got, want)), 3) if len(got) == len(want) else None}
    return out


def parse_ropes(path):
    R = {}
    pat = re.compile(r'^- ✓ `([^`]+)`［(\w+)］ (.*?) \(([-\d.]+),([-\d.]+),([-\d.]+)\) → (.*?) \(([-\d.]+),([-\d.]+),([-\d.]+)\)｜長 ([\d.]+)')
    for l in open(path, encoding='utf-8'):
        m = pat.match(l.strip())
        if m:
            g = m.groups()
            R[g[0]] = {'state': g[1], 'a': [float(v) for v in g[3:6]], 'b': [float(v) for v in g[7:10]], 'len': float(g[10])}
    return R


def main():
    d, ex = sys.argv[1], sys.argv[2]
    plan = json.load(open(os.path.join(d, 'plan.json'), encoding='utf-8'))
    V = json.load(open(os.path.join(d, 'verify_rigging.json'), encoding='utf-8'))
    W = state_after(d, 'stage9')
    want = np.zeros((NX, NY, NZ), np.int16)
    for k, v in W.items():
        want = np.where(v > 0, v, want)
    pts = load(os.path.join(ex, 'assembly.list.txt'))
    got = np.zeros((NX, NY, NZ), np.int16); got[pts[:, 0], pts[:, 1], pts[:, 2]] = pts[:, 3]
    out = {'ledger': {'design': int((want > 0).sum()), 'work': int(len(pts)), 'missing': int(((want > 0) & (got == 0)).sum()),
                      'extra': int(((got > 0) & (want == 0)).sum()), 'color_diff': int(((want > 0) & (got > 0) & (want != got)).sum())}}
    de = deadeye_probe(pts, plan); de3 = deadeye_probe(pts, plan, dx=3)
    out['deadeyes'] = de
    rev = [round(b - a, 3) for k in de for a, b in zip(de[k]['got_x'], de3[k]['got_x'])]
    # chain plates
    # 🩸 第一版只認顏色：73 也是隼的背、舵的 pintle ⇒ 1,851 格。chain plate 只在兩段 channel 的 x 範圍、舷外 |dy| ≥ 30、channel 底面以下
    pc = plan['rigging']['chain_plate']['color']
    xr = [(r[0], r[1]) for r in (V['deadeyes'][m]['range'] for m in ('fore', 'main'))]
    zb = {m: min(V['deadeyes'][m]['z']) for m in ('fore', 'main')}
    inx = np.zeros(len(pts), bool)
    for (a, b), m in zip(xr, ('fore', 'main')):
        inx |= (pts[:, 0] >= a) & (pts[:, 0] <= b) & (pts[:, 2] < zb[m])
    pl = pts[(pts[:, 3] == pc) & inx & (np.abs(pts[:, 1] - YC) >= 30)]
    nailed = 0; cols = 0
    for side, sgn in (('S', 1), ('P', -1)):
        q = pl[(pl[:, 1] - YC) * sgn > 0]
        for x in np.unique(q[:, 0]):
            c = q[q[:, 0] == x]; b = c[np.argmin(c[:, 2])]
            cols += 1; nailed += int(got[b[0], b[1] - sgn, b[2]] > 0)
    ch = load(os.path.join(ex, 'channels.list.txt'))
    g = np.zeros(tuple(ch[:, :3].max(0) + 2), bool); g[tuple(ch[:, :3].T)] = True
    out['chain_plates'] = {'cells': int(len(pl)), 'columns': cols, 'bottom_on_hull': nailed, 'channels_work_components_6': int(ndimage.label(g)[1]),
                           'channels_work_cells': int(len(ch))}
    # 繩：引擎 vs 我
    E = parse_ropes(os.path.join(ex, 'ropes.txt'))
    da = []; dl = []; miss = []
    for r in V['ropes']:
        e = E.get(r['name'])
        if not e: miss.append(r['name']); continue
        da.append(max(math.dist(e['a'], r['from_world']), math.dist(e['b'], r['to_world'])))
        dl.append(abs(e['len'] - r['length']))
    sh = [math.dist(E[r['name']]['a'], [r['from_world'][0] + 3, r['from_world'][1], r['from_world'][2]]) for r in V['ropes'][:5]]
    out['ropes'] = {'engine_ok': sum(1 for e in E.values() if e['state'] == 'ok'), 'listed': len(E), 'compared': len(da), 'missing': miss,
                    'max_endpoint_diff': round(max(da), 4), 'max_length_diff': round(max(dl), 4)}
    rev += [round(v, 2) for v in sh]
    # 淨空（EDT：空格心到最近實心格心）
    edt = ndimage.distance_transform_edt(got == 0)
    ce = plan['rigging']['clear_ends']; cl = {}
    for r in V['ropes']:
        if r['kind'] != 'stay': continue
        p0, p1 = np.array(r['from_world']), np.array(r['to_world']); L = np.linalg.norm(p1 - p0)
        v = [float(edt[tuple(int(math.floor(c)) for c in p0 + (p1 - p0) * t / L)]) for t in np.arange(ce + 3, L - ce - 3, 0.25)]
        cl[r['name']] = round(min(v), 3)
    out['stay_mid_clearance_cells'] = cl
    out['reverse_offset3'] = rev
    out['reverse_all_report_3'] = all(abs(v - 3) < 0.06 for v in rev)
    with open(os.path.join(d, 'verify_rigging_post.json'), 'w', encoding='utf-8', newline='\n') as fo:
        json.dump(out, fo, ensure_ascii=False, indent=2, sort_keys=True); fo.write('\n')
    print(json.dumps(out, ensure_ascii=False, indent=1))


if __name__ == '__main__':
    main()
