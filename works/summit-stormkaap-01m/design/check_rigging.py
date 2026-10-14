# 階段八讀數（落格之後）：讀引擎匯出的東西 —— 組裝件 export list、channels 子作品 export list、組裝件 sub=ropes 的輸出（存成文字檔）。
# 用法：python -I -X utf8 -B check_rigging.py <design 資料夾> <匯出資料夾>
#   匯出資料夾裡：assembly.list.txt、channels.list.txt、ropes.txt（senate cmd sculpture op=work sub=ropes 的 stdout）
#   從夜隼號 check_rigging.py（TASK-0529 階段九）改。
#   · 結果帳：（stage6a 的船 ∪ 三根桅與斜桅的清單 ∪ 新 channels（舊清單 − 刻 ＋ 貼）∪ 鏡像）vs 組裝件 export，含顏色；channels 子作品 export vs 新 channels。
#   · deadeye：⛔ 不只認顏色（104 也是甲板）—— 取「組裝件裡有、船殼／甲板／桅那些件都沒有」的格（＝ channels 那兩條關聯），再取 104。
#     按舷、按桅的 channel 範圍分群 ⇒ 每群的 x 中心。從 plan 取的檢查：顆數 ＝ deadeyes[m]、每顆 10 格、第一顆在桅孔 ＋ first_fwd、
#     相鄰間距 ≥ spacing、x±1 不碰任何上排砲門（±port_margin）。
#   · chain plate：channels 子作品裡、deadeye 那一欄、比外緣那一排最低格還低的格。最低那一格往中線一格要是實心（釘在船殼上）；不進任何砲門的開口。
#   · 繩：引擎解出來的兩端（印到 0.1）與長度（0.01）vs 我這邊算的 —— 兩條路解同一個端點（固定點格心、子繩比例）。
#   · 淨空：stays 中段每個取樣點離最近實心格心的距離（±5 格的窗裡找），最小值。
#   · 反向對照：deadeye 探針整份 x 偏 3 ⇒ 報 3；繩的預期端點偏 3 ⇒ 報 3。
import sys, os, json, re, math
import numpy as np
from scipy import ndimage

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from sk_state import state_after

MASTS = ('mizzen', 'main', 'fore')


def load(p):
    return np.loadtxt(p, delimiter=',', dtype=int, comments='#', ndmin=2)


def parse_ropes(path):
    R = {}
    pat = re.compile(r'^- ✓ `([^`]+)`［(\w+)］ (.*?) \(([-\d.]+),([-\d.]+),([-\d.]+)\) → (.*?) \(([-\d.]+),([-\d.]+),([-\d.]+)\)｜長 ([\d.]+)')
    for l in open(path, encoding='utf-8'):
        m = pat.match(l.strip())
        if m:
            g = m.groups()
            R[g[0]] = {'state': g[1], 'a': [float(v) for v in g[3:6]], 'b': [float(v) for v in g[7:10]], 'len': float(g[10])}
    return R


def deadeye_probe(cells, plan, V, ports, YC, dx=0):
    """cells：channels 那兩條關聯的格（N×4）。"""
    CV = plan['rigging']['channels_v2']; out = {}
    de = cells[cells[:, 3] == plan['rigging']['deadeye']['color']]
    mg = CV['port_margin']
    for m in MASTS:
        xa, xb = V['deadeyes'][m]['range']
        for side, sel in (('S', de[:, 1] > YC), ('P', de[:, 1] < YC)):
            c = de[sel & (de[:, 0] >= xa) & (de[:, 0] <= xb)]
            xs = np.unique(c[:, 0] + dx)
            groups = np.split(xs, np.nonzero(np.diff(xs) > 1)[0] + 1)
            got, n = [], []
            for g in groups:
                k = (c[:, 0] + dx >= g[0]) & (c[:, 0] + dx <= g[-1])
                got.append(float(np.mean(c[k][:, 0] + dx)) + 0.5); n.append(int(k.sum()))
            order = np.argsort(got)[::-1]; got = [got[i] for i in order]; n = [n[i] for i in order]
            first = math.floor(plan['masts']['list'][[x['name'] for x in plan['masts']['list']].index(m)]['x']) + CV['first_fwd_of_mast'] + 0.5
            port = [round(x, 3) for x in got if any(int(x - 0.5) + 1 >= p['x'][0] - mg and int(x - 0.5) - 1 <= p['x'][1] + mg for p in ports if p['row'] == 'upper')]
            out[m + '-' + side] = {'count': len(got), 'plan_count': CV['deadeyes'][m], 'x': [round(v, 3) for v in got], 'cells': n,
                                   'first_x_err': round(got[0] - first, 3), 'min_spacing': round(min(-np.diff(got)), 3) if len(got) > 1 else None,
                                   'in_front_of_upper_port': port}
    return out


def main():
    d, ex = sys.argv[1], sys.argv[2]
    plan = json.load(open(os.path.join(d, 'plan.json'), encoding='utf-8'))
    V = json.load(open(os.path.join(d, 'verify_rigging.json'), encoding='utf-8'))
    VM = json.load(open(os.path.join(d, 'verify_masts.json'), encoding='utf-8'))
    ports = json.load(open(os.path.join(d, 'verify_decks.json'), encoding='utf-8'))['ports']
    F = plan['frame']; NY, YC = F['NY'], F['YC']
    # 設計那一側
    want = {}
    for k, v in state_after(d, 'stage6a', nz=200).items():
        if k.endswith('_model'): continue
        for p in np.argwhere(v > 0): want[tuple(int(c) for c in p)] = int(v[tuple(p)])
    others = set(want)
    for k in ('mizzen', 'main', 'fore', 'bowsprit'):
        for r in load(os.path.join(d, VM['stamp_order'][k][0]['file'])): want[tuple(int(c) for c in r[:3])] = int(r[3]); others.add(tuple(int(c) for c in r[:3]))
    ch = {tuple(int(c) for c in r[:3]): int(r[3]) for r in load(os.path.join(d, VM['stamp_order']['channels'][0]['file']))}
    for o in V['stamp_order']['channels']:
        for r in load(os.path.join(d, o['file'])):
            k = tuple(int(c) for c in r[:3])
            if o['op'] == 'carvevox': assert ch.pop(k) == r[3]
            else: ch[k] = int(r[3])
    for k, c in ch.items():
        want[k] = c; want[(k[0], NY - 1 - k[1], k[2])] = c
    pts = load(os.path.join(ex, 'assembly.list.txt'))
    got = {tuple(int(c) for c in r[:3]): int(r[3]) for r in pts}
    out = {'ledger': {'design': len(want), 'work': len(got), 'missing': sum(1 for k in want if k not in got), 'extra': sum(1 for k in got if k not in want),
                      'color_diff': sum(1 for k, c in want.items() if k in got and got[k] != c)}}
    chw = {tuple(int(c) for c in r[:3]): int(r[3]) for r in load(os.path.join(ex, 'channels.list.txt'))}
    out['channels_work'] = {'design': len(ch), 'work': len(chw), 'diff': len(set(ch.items()) ^ set(chw.items()))}
    # deadeye：channels 那兩條關聯的格 ＝ 組裝件裡有、其他件都沒有
    chan_cells = np.array([k + (c,) for k, c in got.items() if k not in others])
    de = deadeye_probe(chan_cells, plan, V, ports, YC); de3 = deadeye_probe(chan_cells, plan, V, ports, YC, dx=3)
    out['deadeyes'] = de
    rev = [round(b - a, 3) for k in de for a, b in zip(de[k]['x'], de3[k]['x'])]
    # chain plates（channels 子作品，右舷）
    nailed = cols = in_port = cells = 0
    for m in MASTS:
        for x in de[m + '-S']['x']:
            xi = int(x - 0.5)
            col = [k for k in chw if k[0] == xi]
            ymax = max(k[1] for k in col)
            zbot = min(k[2] for k in col if k[1] == ymax)
            plate = [k for k in col if k[2] < zbot]
            cells += len(plate); cols += 1
            b = min(plate, key=lambda k: k[2])
            nailed += int((b[0], b[1] - 1, b[2]) in got)
            in_port += sum(1 for k in plate for p in ports if p['x'][0] <= k[0] <= p['x'][1] and p['z'][0] <= k[2] <= p['z'][1])
    g = np.zeros(tuple(np.array(list(chw)).max(0) + 2), bool); g[tuple(np.array(list(chw)).T)] = True
    out['chain_plates'] = {'cells_S': cells, 'columns_S': cols, 'bottom_on_hull': nailed, 'cells_in_port_openings': in_port,
                           'channels_work_components_6': int(ndimage.label(g)[1])}
    # 繩：引擎 vs 我
    E = parse_ropes(os.path.join(ex, 'ropes.txt'))
    da, dl, miss = [], [], []
    for r in V['ropes']:
        e = E.get(r['name'])
        if not e: miss.append(r['name']); continue
        da.append(max(math.dist(e['a'], r['from_world']), math.dist(e['b'], r['to_world'])))
        dl.append(abs(e['len'] - r['length']))
    sh = [math.dist(E[r['name']]['a'], [r['from_world'][0] + 3, r['from_world'][1], r['from_world'][2]]) for r in V['ropes'][:5]]
    out['ropes'] = {'engine_ok': sum(1 for e in E.values() if e['state'] == 'ok'), 'listed': len(E), 'compared': len(da), 'missing': miss,
                    'max_endpoint_diff': round(max(da), 4), 'max_length_diff': round(max(dl), 4)}
    rev += [round(v, 2) for v in sh]
    # stays 中段淨空（±5 格窗）
    ce = plan['rigging']['clear_ends']; cl = {}
    for r in V['ropes']:
        if r['kind'] != 'stay': continue
        p0, p1 = np.array(r['from_world']), np.array(r['to_world']); L = np.linalg.norm(p1 - p0); best = 9.0
        for t in np.arange(ce + 3, L - ce - 3, 0.25):
            q = p0 + (p1 - p0) * t / L; c0 = [int(math.floor(v)) for v in q]
            for dx in range(-5, 6):
                for dy in range(-5, 6):
                    for dz in range(-5, 6):
                        k = (c0[0] + dx, c0[1] + dy, c0[2] + dz)
                        if k in got:
                            dd = math.dist(q, (k[0] + 0.5, k[1] + 0.5, k[2] + 0.5))
                            if dd < best: best = dd
        cl[r['name']] = round(best, 3)
    out['stay_mid_clearance_cells'] = cl
    out['reverse_offset3'] = rev
    out['reverse_all_report_3'] = all(abs(v - 3) < 0.06 for v in rev)
    with open(os.path.join(d, 'verify_rigging_post.json'), 'w', encoding='utf-8', newline='\n') as fo:
        json.dump(out, fo, ensure_ascii=False, indent=2, sort_keys=True); fo.write('\n')
    print(json.dumps(out, ensure_ascii=False, indent=1))


if __name__ == '__main__':
    main()
