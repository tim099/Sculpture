# 階段十一讀數（掛旗之後）：讀引擎匯出的 OBJ（模擬過的旗＋帆＋繩管子）、格子清單、sub=sails。
# 用法：python -I -X utf8 -B check_flags.py <design 資料夾> <匯出資料夾>
#   匯出資料夾裡：ship_ropes.obj（export format=obj，繩照畫：o rope_<i> # <名字>）、ship_list.txt（format=list）、sails.txt（work sub=sails）
#   · 結果帳：旗桿每一格在引擎格子清單裡、顏色一樣；多出來的格數 ＝ 旗桿格數。
#   · 旗布（模擬後的頂點＋三角形重心；離 hoist 那條邊 < 1.2 格的不算）：落在實心 —— 引擎格子（船、桅、旗桿…）一個數＋設計標籤表（多看得到帆桁模型）按件分。
#   · 離別的帆（模擬後網格）最近、離繩（OBJ 管子的頂點）最近：距離與名字。
#   · 已知答案：船尾旗整份往下 30 格 ⇒ 落在實心的數要 > 0；繩的 KD 樹拿某條繩自己的頂點去查 ⇒ 0；三角帆拿自己的網格查 ⇒ 0。
import sys, os, json, re, math
import numpy as np
from scipy.spatial import cKDTree

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from sk_world import World
from draft_sails import seg_dist


def read_obj(path):
    S, R = {}, {}; cur = None; kind = None; V = []; F = []; vbase = 0; nv = 0
    def put():
        if not cur: return
        A, B = np.array(V, float).reshape(-1, 3), np.array(F, int).reshape(-1, 3) - 1
        D = S if kind == 'sail' else R
        if cur in D:
            A0, B0 = D[cur]; D[cur] = (np.vstack([A0, A]), np.vstack([B0, B + len(A0)]))
        else:
            D[cur] = (A, B)
    for l in open(path, encoding='utf-8'):
        if l.startswith('o '):
            put()
            m = re.match(r'o (sail|rope)_\d+ # (.+)', l.strip())
            cur, kind = (m.group(2), m.group(1)) if m else (None, None); V = []; F = []; vbase = nv
        elif l.startswith('v '):
            nv += 1
            if cur:
                x, z, y = map(float, l.split()[1:4]); V.append((x, y, z))
        elif l.startswith('f ') and cur:
            F.append([int(t.split('/')[0]) - vbase for t in l.split()[1:4]])
    put()
    return S, R


def main():
    d, ex = sys.argv[1], sys.argv[2]
    VF = json.load(open(os.path.join(d, 'verify_flags.json'), encoding='utf-8'))
    w = World(d, with_yards=True); lab, names = w.lab, w.names
    a = np.loadtxt(os.path.join(ex, 'ship_list.txt'), delimiter=',', dtype=int, comments='#', ndmin=2)
    eng = np.zeros(lab.shape, bool); eng[tuple(a[:, :3].T)] = True
    col = {tuple(r[:3]): int(r[3]) for r in a}
    out = {'ledger': {}, 'cloth_hits_engine': {}, 'cloth_hits_design': {}, 'nearest_sail': {}, 'nearest_rope': {}, 'mesh': {}, 'known_answer': {}}
    for k, o in VF['stamp'].items():
        rows = np.loadtxt(os.path.join(d, o['file']), delimiter=',', dtype=int, ndmin=2)
        out['ledger'][k] = {'cells': len(rows), 'in_engine': sum(1 for r in rows if col.get(tuple(r[:3])) == r[3])}
    out['ledger']['engine_voxels'] = int(len(a))
    S, R = read_obj(os.path.join(ex, 'ship_ropes.obj'))
    rv = np.vstack([v for v, _ in R.values()]); rn = np.concatenate([[n] * len(v) for n, (v, _) in R.items()])
    rtree = cKDTree(rv)
    others = {n: cKDTree(np.vstack([v, v[f].mean(1)]) if len(f) else v) for n, (v, f) in S.items() if n not in VF['staff']}

    def count(pts):
        he, hd = 0, {}
        for p in pts:
            c = tuple(int(math.floor(x)) for x in p)
            if eng[c]: he += 1
            if lab[c]: hd[names[lab[c]]] = hd.get(names[lab[c]], 0) + 1
        return he, hd
    for fl in VF['sails']:
        nm = fl['name']; V, F = S[nm]
        W = [np.array(x) for x in fl['corners_world']]
        pts = np.vstack([V, V[F].mean(1)])
        keep = np.array([p for p in pts if seg_dist(p, W[3], W[0]) >= 1.2])
        he, hd = count(keep)
        out['cloth_hits_engine'][nm] = he; out['cloth_hits_design'][nm] = hd
        dmin = {n: float(t.query(keep)[0].min()) for n, t in others.items()}
        best = sorted(dmin.items(), key=lambda x: x[1])[:2]
        out['nearest_sail'][nm] = [[n, round(v, 2)] for n, v in best]
        dr, ir = rtree.query(keep)
        j = int(np.argmin(dr))
        out['nearest_rope'][nm] = {'rope': str(rn[ir[j]]), 'dist': round(float(dr[j]), 2), 'at': [round(float(x), 1) for x in keep[j]]}
        out['mesh'][nm] = {'verts': int(len(V)), 'tris': int(len(F)), 'checked': int(len(keep)),
                           'corner0_dev': round(float(min(np.linalg.norm(V - W[0], axis=1))), 3),
                           'bbox': [[round(float(x), 1) for x in keep.min(0)], [round(float(x), 1) for x in keep.max(0)]]}
        if nm == 'ensign':
            out['known_answer']['ensign_down30_engine_hits'] = count(keep - [0, 0, 30])[0]
    r0 = next(iter(R)); out['known_answer']['rope_self_dist'] = round(float(rtree.query(R[r0][0][:5])[0].max()), 3)
    out['known_answer']['lateen_self_dist'] = round(float(others['mizzen-lateen'].query(S['mizzen-lateen'][0][:5])[0].max()), 3)
    txt = open(os.path.join(ex, 'sails.txt'), encoding='utf-8').read()
    out['engine'] = {m.group(1): m.group(2) for m in re.finditer(r'^- ✓ `([^`]+)`［(\w+)］', txt, re.M) if m.group(1) in VF['staff']}
    out['broken'] = {k: int(v) for k, v in re.findall(r'🔢 (sails_broken|ropes_broken) = (\d+)', txt)}
    with open(os.path.join(d, 'verify_flags_post.json'), 'w', encoding='utf-8', newline='\n') as fo:
        json.dump(out, fo, ensure_ascii=False, indent=2, sort_keys=True); fo.write('\n')
    print(json.dumps(out, ensure_ascii=False, indent=1))


if __name__ == '__main__':
    main()
