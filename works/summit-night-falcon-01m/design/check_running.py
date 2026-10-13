# 階段十讀數（落格之後）：讀引擎匯出的東西 —— 組裝件 export list、sub=ropes 的輸出（兩份：預設角、fore course 轉 θ 之後）。
# 用法：python -I -X utf8 -B check_running.py <design 資料夾> <匯出資料夾> <θ 度>
#   匯出資料夾裡：assembly.list.txt、ropes.txt（預設角）、ropes_turned.txt（fore course 轉 θ 之後）
#   · 結果帳：nf_state.state_after('stage10') vs 組裝件 export。
#   · pins（從圖紙取的探針）：組裝件裡 pin 色、在舷牆 rail 高度上下 2 格內、|dy| ≥ 12 的直條，按舷數根數；兩舷一樣多、每根 5 格。
#   · 繩：引擎解出來的兩端與長度 vs 我算的（階段十的 44 條）；階段九的 207 條也再比一次（新固定點不能動到舊繩）。
#   · 綁模型：fore course 轉 θ 後，掛在它上面的繩那一端（引擎）vs 我用 rot() 轉的預期；其他繩的兩端不能動。
#   · footrope 下垂：引擎讀數 vs 拋物線估計。
#   · 反向對照：pin 探針 x 偏 3、繩預期端點偏 3 ⇒ 報 3。
import sys, os, json, re, math
import numpy as np

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from draft_lines import YC
from nf_state import state_after, NX, NY, NZ
from draft_yards import rot


def load(p):
    return np.loadtxt(p, delimiter=',', dtype=int, comments='#', ndmin=2)


def parse(path):
    R = {}
    # 🩸 v1 拿「長」比我的直線長 ⇒ footrope（slack 1.03）差 1.65 —— 比的是兩種量 ⇒ 改比引擎印的「直線」
    pat = re.compile(r'^- ✓ `([^`]+)`［(\w+)］ (.*?) \(([-\d.]+),([-\d.]+),([-\d.]+)\) → (.*?) \(([-\d.]+),([-\d.]+),([-\d.]+)\)｜長 [\d.]+（直線 ([\d.]+).*?最大下垂 ([\d.]+)')
    for l in open(path, encoding='utf-8'):
        m = pat.match(l.strip())
        if m:
            g = m.groups()
            R[g[0]] = {'state': g[1], 'a': [float(v) for v in g[3:6]], 'b': [float(v) for v in g[7:10]], 'len': float(g[10]), 'sag': float(g[11])}
    return R


def pin_probe(got, plan, V, dx=0):
    # 🩸 v1 只認 pin 色 104 —— 104 也是舷牆頂蓋（階段九才記過同一個病，一小時內又寫一次）⇒ 認形狀：
    #    rail 色那一格（rail_z）上下各兩格都是 pin 色、在 rail 的 x 範圍裡
    pc, rc = plan['belaying']['colors']['pin'], plan['belaying']['colors']['rail']
    out = {}
    for sd, sg in (('S', 1), ('P', -1)):
        n = 0; xs = 0
        for k, r in V['rails'].items():
            if not k.startswith('pinrail'): continue
            z = r['rail_z']
            for x in range(r['x'][0], r['x'][1] + 1):
                for dy in range(12, 40):
                    y = YC + sg * dy
                    if got[x, y, z] == rc and all(got[x, y, z + t] == pc for t in (-2, -1, 1, 2)):
                        n += 1; xs += x + dx
        out[sd] = {'pins': n, 'x_sum': xs}
    return out


def main():
    d, ex, th = sys.argv[1], sys.argv[2], float(sys.argv[3])
    plan = json.load(open(os.path.join(d, 'plan.json'), encoding='utf-8'))
    V = json.load(open(os.path.join(d, 'verify_running.json'), encoding='utf-8'))
    V9 = json.load(open(os.path.join(d, 'verify_rigging.json'), encoding='utf-8'))
    VB = json.load(open(os.path.join(d, 'verify_belaying.json'), encoding='utf-8'))
    VY = {p['member']: p for p in json.load(open(os.path.join(d, 'verify_yards.json'), encoding='utf-8'))['placements']}
    W = state_after(d, 'stage10')
    want = np.zeros((NX, NY, NZ), np.int16)
    for k, v in W.items(): want = np.where(v > 0, v, want)
    pts = load(os.path.join(ex, 'assembly.list.txt'))
    got = np.zeros((NX, NY, NZ), np.int16); got[pts[:, 0], pts[:, 1], pts[:, 2]] = pts[:, 3]
    out = {'ledger': {'design': int((want > 0).sum()), 'work': int(len(pts)), 'missing': int(((want > 0) & (got == 0)).sum()),
                      'extra': int(((got > 0) & (want == 0)).sum()), 'color_diff': int(((want > 0) & (got > 0) & (want != got)).sum())}}
    pp = pin_probe(got, plan, VB); pp3 = pin_probe(got, plan, VB, dx=3)
    nside = len(VB['anchors']['side']); nfife = sum(1 for a in VB['anchors']['fife'] if a['kind'] == 'pin')
    out['pins'] = {'probe': pp, 'side_anchors_per_side': nside, 'fife_pin_anchors': nfife}
    rev = [(pp3[s]['x_sum'] - pp[s]['x_sum']) / pp[s]['pins'] for s in ('S', 'P')]
    E = parse(os.path.join(ex, 'ropes.txt')); ET = parse(os.path.join(ex, 'ropes_turned.txt'))
    def cmp(ropes):
        da = dl = 0.0; miss = []
        for r in ropes:
            e = E.get(r['name'])
            if not e: miss.append(r['name']); continue
            da = max(da, math.dist(e['a'], r['from_world']), math.dist(e['b'], r['to_world'])); dl = max(dl, abs(e['len'] - r['length']))
        return round(da, 4), round(dl, 4), miss
    a10 = cmp(V['ropes']); a9 = cmp(V9['ropes'])
    out['ropes'] = {'engine_total': len(E), 'engine_ok': sum(1 for e in E.values() if e['state'] == 'ok'),
                    'stage10': {'n': len(V['ropes']), 'max_endpoint_diff': a10[0], 'max_length_diff': a10[1], 'missing': a10[2]},
                    'stage9_again': {'n': len(V9['ropes']), 'max_endpoint_diff': a9[0], 'max_length_diff': a9[1], 'missing': a9[2]}}
    # 綁模型：fore course 轉 θ
    P = VY['fore-course']; key = 'model:%s/%s/' % (P['link'], P['model'])
    moved = []; still = 0.0; exp_dev = 0.0
    for r in V['ropes'] + V9['ropes']:
        e, t = E.get(r['name']), ET.get(r['name'])
        for end, w in (('a', r['from']), ('b', r['to'])):
            if w.startswith(key):
                q = rot(r['from_world'] if end == 'a' else r['to_world'], P['at'], P['rotate'][1], th)
                exp_dev = max(exp_dev, math.dist(t[end], q)); moved.append(r['name'] + ':' + end)
            else:
                still = max(still, math.dist(t[end], e[end]))
    out['turn_test'] = {'theta': th, 'ends_on_fore_course': len(moved), 'max_dev_vs_rot': round(exp_dev, 4), 'max_move_of_other_ends': round(still, 4)}
    rev.append(math.dist([E[V['ropes'][0]['name']]['a'][0] + 3] + E[V['ropes'][0]['name']]['a'][1:], V['ropes'][0]['from_world']) -
               math.dist(E[V['ropes'][0]['name']]['a'], V['ropes'][0]['from_world']))
    # footrope 下垂
    fs = [(r['name'], r['sag_est'], E[r['name']]['sag']) for r in V['ropes'] if r['kind'] == 'footrope']
    out['footrope_sag'] = {'engine_max': max(f[2] for f in fs), 'engine_min': min(f[2] for f in fs), 'est_max': max(f[1] for f in fs)}
    out['reverse_offset3'] = [round(v, 3) for v in rev]
    out['reverse_all_report_3'] = all(abs(v - 3) < 0.11 for v in rev)
    with open(os.path.join(d, 'verify_running_post.json'), 'w', encoding='utf-8', newline='\n') as fo:
        json.dump(out, fo, ensure_ascii=False, indent=2, sort_keys=True); fo.write('\n')
    print(json.dumps(out, ensure_ascii=False, indent=1))


if __name__ == '__main__':
    main()
