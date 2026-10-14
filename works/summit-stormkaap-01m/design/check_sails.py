# 階段十讀數（掛帆之後；從夜隼號 check_sails.py 改）：讀引擎匯出的 OBJ（模擬過的帆網格）、格子清單、sub=sails 的輸出。
# 用法：python -I -X utf8 -B check_sails.py <design 資料夾> <匯出資料夾>
#   匯出資料夾裡：ship.obj（export format=obj ropes=0：帆是 o sail_<i> # <名字>，有貼圖的按顏色拆成好幾塊、同名合併；頂點 v x z y）、
#                 ship_list.txt（export format=list：引擎組好的格子）、sails.txt（work sub=sails）
#   · 布碰撞：每面帆模擬後的頂點與三角形重心，落在實心的數 —— 兩條路分開數：
#       ① 設計那一側（draft_running.Run 的標籤表：船＋桅＋channels＋fife＋帆桁轉好）⇒ 按件分；帆桁是模型，只有這條路看得到
#       ② 引擎的格子清單（不經設計程式）⇒ 只有一個數
#     跳過離釘住的邊 < 1.2 格的點（邊本來就貼著帆桁）。
#   · 已知答案：拿模擬之前的平的布（verify_sails.json corners_world，60×60 取樣）用同一支數法數 ⇒ 要等於 draft_sails 記的 flat_cloth_hits。
#   · 離桅：模擬後布點所在那一格到自己那根桅（meta mast；bowsprit ＝ 斜桅）最近的桅格（格心距離，同 EDT）。
#   · 引擎讀數：每面帆的 ok、最鼓、牽繩條數；sails_broken、ropes_broken。
#   · 反向對照：把方帆的布整份往桅那邊（−x）推 3 格 ⇒ 離桅最近距離少 3（夠遠的那幾面）。
import sys, os, json, re, math
import numpy as np
from scipy.spatial import cKDTree

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import draft_running
from draft_running import Run
from draft_sails import seg_dist

draft_running.LINKKEY.update({'channels': 'channels_S', 'channels-鏡像': 'channels_P'})


def read_obj(path):
    # 同名的 o 要合併（有貼圖的帆按顏色拆成好幾個物件）
    S = {}; cur = None; V = []; F = []; vbase = 0; nv = 0
    def put(name, V, F):
        V, F = np.array(V, float).reshape(-1, 3), np.array(F, int).reshape(-1, 3) - 1
        if name in S:
            V0, F0 = S[name]; S[name] = (np.vstack([V0, V]), np.vstack([F0, F + len(V0)]))
        else:
            S[name] = (V, F)
    for l in open(path, encoding='utf-8'):
        if l.startswith('o '):
            if cur: put(cur, V, F)
            m = re.match(r'o sail_\d+ # (.+)', l.strip()); cur = m.group(1) if m else None; V = []; F = []; vbase = nv
        elif l.startswith('v '):
            nv += 1
            if cur:
                x, z, y = map(float, l.split()[1:4]); V.append((x, y, z))
        elif l.startswith('f ') and cur:
            F.append([int(t.split('/')[0]) - vbase for t in l.split()[1:4]])
    if cur: put(cur, V, F)
    return S


def main():
    d, ex = sys.argv[1], sys.argv[2]
    VS = json.load(open(os.path.join(d, 'verify_sails.json'), encoding='utf-8'))
    smeta = {m[1]: m[2] for m in VS['meta'] if m[0] == 'sail'}
    r = Run(d); lab, names = r.w.lab, r.w.names
    NX, NY, NZ = lab.shape
    eng = np.zeros(lab.shape, bool)
    a = np.loadtxt(os.path.join(ex, 'ship_list.txt'), delimiter=',', dtype=int, comments='#', ndmin=2)
    eng[tuple(a[:, :3].T)] = True
    trees = {m: cKDTree(np.argwhere(lab == r.w.code('mast_' + m if m != 'bowsprit' else 'bowsprit'))) for m in ('mizzen', 'main', 'fore', 'bowsprit')}

    def inside(c):
        return 0 <= c[0] < NX and 0 <= c[1] < NY and 0 <= c[2] < NZ

    def count(pts):
        hd, he, out = {}, 0, 0
        for p in pts:
            c = tuple(int(math.floor(x)) for x in p)
            if not inside(c): out += 1; continue
            v = lab[c]
            if v: hd[names[v]] = hd.get(names[v], 0) + 1
            if eng[c]: he += 1
        return hd, he, out

    O = read_obj(os.path.join(ex, 'ship.obj'))
    out = {'cloth_hits_design': {}, 'cloth_hits_engine': {}, 'outside_frame': {}, 'mast_clearance': {}, 'mesh': {}, 'flat_known_answer': {}}
    for sl in VS['sails']:
        nm = sl['name']; V, F = O[nm]
        W = [np.array(w) for w in sl['corners_world']]; n = len(W)
        bound = [int(b) for b in sl['bind'].split(',') if b != '']
        far = lambda p: not any(seg_dist(p, W[b], W[(b + 1) % n]) < 1.2 for b in bound)
        pts = np.vstack([V, V[F].mean(1)]) if len(F) else V
        keep = [p for p in pts if far(p)]
        hd, he, o = count(keep)
        out['cloth_hits_design'][nm] = hd; out['cloth_hits_engine'][nm] = he; out['outside_frame'][nm] = o
        out['mesh'][nm] = {'verts': int(len(V)), 'tris': int(len(F)), 'checked': len(keep),
                           'corner0_dev': round(float(min(np.linalg.norm(V - W[0], axis=1))), 3)}
        # 已知答案：平的布（同 draft_sails 的取樣）
        flat = []
        if n == 4:
            for u in np.linspace(0, 1, 60):
                for v in np.linspace(0, 1, 60):
                    flat.append((1 - u) * (1 - v) * W[0] + u * (1 - v) * W[1] + u * v * W[2] + (1 - u) * v * W[3])
        else:
            for u in np.linspace(0, 1, 60):
                for v in np.linspace(0, 1 - u, max(2, int(60 * (1 - u)))):
                    flat.append(W[0] + u * (W[1] - W[0]) + v * (W[2] - W[0]))
        fd, fe, _ = count([p for p in flat if far(p)])
        out['flat_known_answer'][nm] = {'design': fd, 'recorded': VS['flat_cloth_hits'][nm], 'same': fd == VS['flat_cloth_hits'][nm], 'engine': fe}
        m = smeta[nm]['mast']

        def clr(dx):
            q = np.floor(np.array(keep) - [dx, 0, 0])
            return round(float(trees[m].query(q)[0].min()), 3)
        out['mast_clearance'][nm] = {'mast': m, 'min': clr(0), 'pushed_3_toward_mast': clr(3) if smeta[nm]['sail'] != 'gaff' and m != 'bowsprit' else None}
    txt = open(os.path.join(ex, 'sails.txt'), encoding='utf-8').read()
    eg = {}
    for mm in re.finditer(r'^- ✓ `([^`]+)`［(\w+)］ (?:四邊形|三角帆).*?最鼓 ([-\d.]+).*?(?:牽繩 (\d+) 條)?｜色', txt, re.M):
        eg[mm.group(1)] = {'state': mm.group(2), 'billow': float(mm.group(3)), 'ropes': int(mm.group(4) or 0)}
    out['engine'] = eg
    out['broken'] = {k: int(v) for k, v in re.findall(r'🔢 (sails_broken|ropes_broken) = (\d+)', txt)}
    out['reverse_offset3'] = {k: round(v['min'] - v['pushed_3_toward_mast'], 3) for k, v in out['mast_clearance'].items() if v['pushed_3_toward_mast'] is not None and v['min'] > 4}
    with open(os.path.join(d, 'verify_sails_post.json'), 'w', encoding='utf-8', newline='\n') as fo:
        json.dump(out, fo, ensure_ascii=False, indent=2, sort_keys=True); fo.write('\n')
    print(json.dumps(out, ensure_ascii=False, indent=1))


if __name__ == '__main__':
    main()
