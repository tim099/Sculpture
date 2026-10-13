# 階段十二讀數：讀引擎匯出的東西 —— 組裝件 export list、export obj（模擬過的旗與帆）、sub=sails。
# 用法：python -I -X utf8 -B check_flag.py <design 資料夾> <匯出資料夾>
#   匯出資料夾裡：assembly.list.txt、ship.obj、sails.txt
#   · 結果帳：nf_state.state_after('stage12') vs 組裝件 export。
#   · 旗：模擬後的頂點落在實心（格、帆桁）的數（跳過離旗桿 < 1.2 格的點）；離其他帆的布最近幾格；旗的外框；離每一條繩最近幾格。
#   · 貼圖：組裝件 textures/ensign.png 跟來源逐位元組比。
#   · 反向對照：最近那條繩往旗的方向挪 3 格 ⇒ 最近距離少 3。
import sys, os, json, re, math, hashlib
import numpy as np

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from nf_state import state_after, NX, NY, NZ
from draft_running import Run
from check_sails import read_obj


def main():
    d, ex = sys.argv[1], sys.argv[2]
    VF = json.load(open(os.path.join(d, 'verify_flag.json'), encoding='utf-8'))
    W = state_after(d, 'stage12')
    want = np.zeros((NX, NY, NZ), np.int16)
    for k, v in W.items(): want = np.where(v > 0, v, want)
    pts = np.loadtxt(os.path.join(ex, 'assembly.list.txt'), delimiter=',', dtype=int, comments='#', ndmin=2)
    got = np.zeros((NX, NY, NZ), np.int16); got[pts[:, 0], pts[:, 1], pts[:, 2]] = pts[:, 3]
    out = {'ledger': {'design': int((want > 0).sum()), 'work': int(len(pts)), 'missing': int(((want > 0) & (got == 0)).sum()),
                      'extra': int(((got > 0) & (want == 0)).sum()), 'color_diff': int(((want > 0) & (got > 0) & (want != got)).sum())}}
    r = Run(d)
    from draft_yards import rot
    yards = np.zeros((NX, NY, NZ), bool)
    for nm, P in r.Y.items():
        for c in r.yard_cells[nm][:, :3] + np.asarray(P['origin']):
            yards[tuple(int(math.floor(v)) for v in rot([c[i] + 0.5 for i in range(3)], P['at'], P['rotate'][1], P['rotate'][2]))] = True
    O = read_obj(os.path.join(ex, 'ship.obj'))
    V, F = O['ensign']
    staff_x = VF['staff']['x'] + 0.5
    keep = [p for p in np.vstack([V, V[F].mean(1)]) if math.hypot(p[0] - staff_x, p[1] - 80.5) >= 1.2]
    hit = {}
    for p in keep:
        c = tuple(int(math.floor(x)) for x in p)
        if got[c]: hit['voxel'] = hit.get('voxel', 0) + 1
        if yards[c]: hit['yards'] = hit.get('yards', 0) + 1
    others = np.vstack([O[n][0] for n in O if n != 'ensign'])
    dmin = min(float(np.min(np.linalg.norm(others - p, axis=1))) for p in V[::3])
    # 離繩：旗的頂點到每一條繩（直線；靜索、動索 slack 1；帆腳索用引擎的端點也近似直線）最近的距離
    # 🩸 v1 拿旗的最低 z 比 main topgallant stay 起點的 z —— 最低點在旗尾（x 173）、stay 起點在桅邊（x 144），比的是兩個不同地方
    ropes = []
    for fn in ('verify_rigging.json', 'verify_running.json', 'verify_sails.json'):
        for x in json.load(open(os.path.join(d, fn), encoding='utf-8'))['ropes']:
            if x.get('from_world') and x.get('to_world'): ropes.append((x['name'], np.array(x['from_world']), np.array(x['to_world'])))
    def segd(P, a, b):
        ab = b - a; t = np.clip((P - a) @ ab / (ab @ ab), 0, 1); return np.linalg.norm(P - (a[None] + t[:, None] * ab[None]), axis=1)
    near = sorted(((float(segd(V, a, b).min()), n) for n, a, b in ropes))[:4]
    n0, a0, b0 = [x for x in ropes if x[0] == near[0][1]][0]
    dd = segd(V, a0, b0); i = int(dd.argmin()); ab = b0 - a0
    q = a0 + np.clip((V[i] - a0) @ ab / (ab @ ab), 0, 1) * ab; u = (V[i] - q) / np.linalg.norm(V[i] - q)
    shifted = float(segd(V, a0 + 3 * u, b0 + 3 * u).min())
    out['flag'] = {'verts': int(len(V)), 'checked': len(keep), 'hits': hit, 'min_dist_to_other_sails': round(dmin, 3),
                   'bbox_min': [round(float(v), 2) for v in V.min(0)], 'bbox_max': [round(float(v), 2) for v in V.max(0)],
                   'ropes_compared': len(ropes), 'nearest_ropes': [[n, round(x, 3)] for x, n in near]}
    out['reverse'] = {'nearest_rope_moved_3_toward_flag': round(near[0][0] - shifted, 3)}
    src = VF['sail']['texture']; dst = os.path.join(os.path.dirname(os.path.dirname(d)), 'summit-night-falcon-01m-assembly', 'textures', 'ensign.png')
    out['texture'] = {'same_bytes': hashlib.sha256(open(src, 'rb').read()).hexdigest() == hashlib.sha256(open(dst, 'rb').read()).hexdigest()}
    txt = open(os.path.join(ex, 'sails.txt'), encoding='utf-8').read()
    m = re.search(r'^- ✓ `ensign`［(\w+)］.*?最鼓 ([-\d.]+).*?平均位移 \(([^)]*)\)', txt, re.M)
    out['engine'] = {'state': m.group(1), 'billow': float(m.group(2)), 'mean_disp': m.group(3)} if m else None
    out['broken'] = {k: int(v) for k, v in re.findall(r'🔢 (sails_broken|ropes_broken|sail_count) = (\d+)', txt)}
    with open(os.path.join(d, 'verify_flag_post.json'), 'w', encoding='utf-8', newline='\n') as fo:
        json.dump(out, fo, ensure_ascii=False, indent=2, sort_keys=True); fo.write('\n')
    print(json.dumps(out, ensure_ascii=False, indent=1))


if __name__ == '__main__':
    main()
