# 階段九讀數（落格之後）：讀引擎匯出的東西 —— 組裝件 export list、fife rails 子作品 export list、組裝件 sub=ropes 的輸出、組裝件 export parts。
# 用法：python -I -X utf8 -B check_running.py <design 資料夾> <匯出資料夾>
#   匯出資料夾裡：assembly.list.txt、fife.list.txt、ropes.txt、parts.json
#   · 結果帳：（sk_world 的船＋桅＋channels ∪ fife 清單）vs 組裝件 export（含顏色）；fife 子作品 export vs 清單。
#   · pin（從 plan 取的探針）：每根桅 fife 的 rail 那一層 ＝ 那一欄甲板面 ＋ above_deck（甲板面從組裝件匯出量，⛔ 不讀 draft 的 rails）；
#     每個 pin 固定點：組裝件裡那一格是 pin 色、上面一格是空的、往下 up＋down 格都是 pin 色或 rail 色（一根完整的 pin）。
#     柱與 bitts：每一欄最下面那一格底下是實心（站在甲板上）。
#   · 帆桁上的新固定點：引擎轉過的點（parts 的 models[].points）vs draft 的 anchors_expect。
#   · 繩：引擎解出來的兩端（印到 0.1）與長度 vs draft 的（直線）。
#   · 反向對照：rail 那一層偏 3 ⇒ 報 3；繩的預期端點偏 3 ⇒ 報 3。
import sys, os, json, re, math
import numpy as np

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from sk_world import World, load


def parse_ropes(path):
    R = {}
    pat = re.compile(r'^- ✓ `([^`]+)`［(\w+)］ (.*?) \(([-\d.]+),([-\d.]+),([-\d.]+)\) → (.*?) \(([-\d.]+),([-\d.]+),([-\d.]+)\)｜長 ([\d.]+)（直線 ([\d.]+)')
    for l in open(path, encoding='utf-8'):
        m = pat.match(l.strip())
        if m:
            g = m.groups()
            R[g[0]] = {'state': g[1], 'a': [float(v) for v in g[3:6]], 'b': [float(v) for v in g[7:10]], 'len': float(g[10]), 'straight': float(g[11])}
    return R


def main():
    d, ex = sys.argv[1], sys.argv[2]
    w = World(d, with_yards=False)
    plan = w.plan; B = plan['belaying']; YC = w.YC
    BL = json.load(open(os.path.join(d, 'verify_belaying.json'), encoding='utf-8'))
    RV = json.load(open(os.path.join(d, 'verify_running.json'), encoding='utf-8'))
    fife = {tuple(int(c) for c in r[:3]): int(r[3]) for r in load(os.path.join(d, BL['stamp_order']['fiferails'][0]['file']))}
    want = dict(fife)
    for k, v in w.color.items():
        for p in np.argwhere(v > 0): want[tuple(int(c) for c in p)] = int(v[tuple(p)])
    for k, a in w.mast.items():
        for r in a: want[tuple(int(c) for c in r[:3])] = int(r[3])
    for k, c in w.channels.items():
        want[k] = c; want[(k[0], w.NY - 1 - k[1], k[2])] = c
    got = {tuple(int(c) for c in r[:3]): int(r[3]) for r in load(os.path.join(ex, 'assembly.list.txt'))}
    out = {'ledger': {'design': len(want), 'work': len(got), 'missing': sum(1 for k in want if k not in got), 'extra': sum(1 for k in got if k not in want),
                      'color_diff': sum(1 for k, c in want.items() if k in got and got[k] != c)}}
    fw = {tuple(int(c) for c in r[:3]): int(r[3]) for r in load(os.path.join(ex, 'fife.list.txt'))}
    out['fife_work'] = {'list': len(fife), 'work': len(fw), 'diff': len(set(fife.items()) ^ set(fw.items()))}
    # 甲板面（從組裝件量）：那一欄（中線外 10 格）由上往下第一個「甲板色 104 而且下面是實心」的格 —— 只看 z < rail，⛔ 不讀 draft
    C = B['colors']; Mp = {m['name']: m for m in plan['masts']['list']}
    deck_cols = {'mizzen': 'half', 'main': 'upper', 'fore': 'bak'}

    def deck_z(x):
        # 那一欄中線外 10 格：甲板那幾件（不含 fife 自己）的最高格 —— 用組裝件格扣掉 fife 清單，⛔ 不用 draft 的 rails
        zs = [k[2] for k in got if k[0] == x and k[1] == YC + 10 and k not in fife and k[2] < 200]
        return max(zs) + 1

    def rail_probe(dz=0):
        R = {}
        for m in ('mizzen', 'main', 'fore'):
            G = B['fife'][m]; xm = int(Mp[m]['x']); xa = xm - G['aft_of_mast']
            row = [k[2] + dz for k, c in fife.items() if k[0] == xa and k[1] == YC + 1 and c == C['rail']]
            R[m] = {'rail_z': max(row), 'plan': deck_z(xm) + B['fife']['above_deck']}
            R[m]['err'] = R[m]['rail_z'] - R[m]['plan']
        return R
    rp = rail_probe(); rp3 = rail_probe(3)
    out['fife_rail_height'] = rp
    rev = [rp3[m]['err'] - rp[m]['err'] for m in rp]
    # pins
    P = B['pin']; bad_pins = []
    for a in BL['anchors']['fife']:
        x, y, z = a['world']
        ok = got.get((x, y, z)) == C['pin'] and (x, y, z + 1) not in got and all(got.get((x, y, z - k)) in (C['pin'], C['rail']) for k in range(P['up'] + P['down'] + 1))
        if not ok: bad_pins.append(a['name'])
    # 柱、bitts 站在甲板上
    # 🩸 第一版認 bitt 色 ⇒ rail 也是 136（同色）⇒ 懸在空中的 rail 被算成柱，報 236／320 沒站在甲板上（尺壞了，不是 fife 壞了）
    #    ⇒ 柱 ＝ 往下伸過 pin 底（rail − down）的那幾欄 —— 用形狀認，⛔ 不用顏色
    floating = 0; cols = {}
    for (x, y, z), c in fife.items(): cols[(x, y)] = min(cols.get((x, y), 999), z)
    rz = {m: rp[m]['rail_z'] for m in rp}
    def rail_of(x):
        for m in ('mizzen', 'main', 'fore'):
            G = B['fife'][m]; xm = int(Mp[m]['x'])
            if xm - G['aft_of_mast'] - 1 <= x <= xm + G['fwd_of_mast'] + B['fife']['bitt'] + 1: return rz[m]
    cols = {k: z for k, z in cols.items() if z < rail_of(k[0]) - P['down']}
    for (x, y), z in cols.items():
        if (x, y, z - 1) not in got or (x, y, z - 1) in fife: floating += 1
    out['pins'] = {'checked': len(BL['anchors']['fife']), 'bad': bad_pins}
    out['posts'] = {'columns': len(cols), 'not_on_deck': floating}
    # 帆桁上的新固定點：引擎 vs draft
    parts = json.load(open(os.path.join(ex, 'parts.json'), encoding='utf-8'))
    eng = {}
    for mdl in parts['models']:
        pts = dict(mdl['points']) if isinstance(mdl['points'], list) else mdl['points']
        for n, p in pts.items(): eng['model:%s/%s' % (mdl['path'], n)] = p
    dv = [math.dist(eng[k], v) for k, v in RV['anchors_expect'].items() if k in eng]
    out['yard_points'] = {'expected': len(RV['anchors_expect']), 'found': len(dv), 'max_dev': round(max(dv), 4)}
    # 繩
    E = parse_ropes(os.path.join(ex, 'ropes.txt'))
    da, dl, miss = [], [], []
    for r in RV['ropes']:
        e = E.get(r['name'])
        if not e: miss.append(r['name']); continue
        da.append(max(math.dist(e['a'], r['from_world']), math.dist(e['b'], r['to_world'])))
        dl.append(abs(e['straight'] - r['length']))
    sh = [math.dist(E[r['name']]['a'], [r['from_world'][0] + 3, r['from_world'][1], r['from_world'][2]]) for r in RV['ropes'][:5]]
    out['ropes'] = {'running_listed': len(RV['ropes']), 'engine_ok_all': sum(1 for e in E.values() if e['state'] == 'ok'), 'engine_listed_all': len(E),
                    'missing': miss, 'max_endpoint_diff': round(max(da), 4), 'max_straight_length_diff': round(max(dl), 4)}
    rev += [round(v, 2) for v in sh]
    out['reverse_offset3'] = rev
    out['reverse_all_report_3'] = all(abs(v - 3) < 0.06 for v in rev)
    with open(os.path.join(d, 'verify_running_post.json'), 'w', encoding='utf-8', newline='\n') as fo:
        json.dump(out, fo, ensure_ascii=False, indent=2, sort_keys=True); fo.write('\n')
    print(json.dumps(out, ensure_ascii=False, indent=1))


if __name__ == '__main__':
    main()
