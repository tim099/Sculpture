# 階段十一讀數（掛帆之後）：讀引擎匯出的 OBJ（模擬過的帆網格）、sub=sails 的輸出。
# 用法：python -I -X utf8 -B check_sails.py <design 資料夾> <匯出資料夾>
#   匯出資料夾裡：ship.obj（export format=obj：帆是 o sail_<i> # <名字>，頂點 v x z y —— 第一個帆角 head_p 對過）、sails.txt（sub=sails）
#   · 布碰撞：每面帆模擬後的頂點與三角形重心，落在實心（stage10 的格＋帆桁模型）的數 —— 按作品分；跳過離釘住的邊 < 1.2 格的點（邊本來就貼著帆桁／stay）。
#   · 方帆離桅：模擬後布點到那根桅的格（EDT）最近距離。
#   · 引擎讀數：每面帆的 ok、最鼓、牽繩條數；sails_broken、ropes_broken。
#   · 反向對照：把布整份往桅那邊（−x）推 3 格 ⇒ 方帆離桅的最近距離少 3（夠遠的那幾面）。
import sys, os, json, re, math
import numpy as np
from scipy import ndimage

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from draft_running import Run
from draft_sails import seg_dist


def read_obj(path):
    # 同名的 o 要合併：有貼圖的帆按顏色拆成幾個物件（旗 ＝ sail_8／9／10 都叫 ensign）—— 🩸 v1 用名字當鍵直接覆寫，只剩最後那塊 24 點的金喙
    S = {}; cur = None; V = []; F = []; vbase = 0; nv = 0
    def put(name, V, F):
        V, F = np.array(V), np.array(F) - 1
        if name in S:
            V0, F0 = S[name]; S[name] = (np.vstack([V0, V]), np.vstack([F0, F + len(V0)]) if len(F) else F0)
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
    r = Run(d)
    world = {k: v > 0 for k, v in r.W.items()}
    from draft_yards import rot
    for nm, P in r.Y.items():
        g = np.zeros_like(world['hull'])
        for c in r.yard_cells[nm][:, :3] + np.asarray(P['origin']):
            g[tuple(int(math.floor(v)) for v in rot([c[i] + 0.5 for i in range(3)], P['at'], P['rotate'][1], P['rotate'][2]))] = True
        world['yard:' + nm] = g
    O = read_obj(os.path.join(ex, 'ship.obj'))
    out = {'cloth_hits': {}, 'mast_clearance': {}, 'mesh': {}}
    edt = {m: ndimage.distance_transform_edt(~world['mast_' + m]) for m in ('fore', 'main')}
    for sl in VS['sails']:
        V, F = O[sl['name']]
        W = [np.array(w) for w in sl['corners_world']]; n = len(W)
        bound = [int(b) for b in sl['bind'].split(',') if b != '']
        pts = np.vstack([V, V[F].mean(1)]) if len(F) else V
        keep = [p for p in pts if not any(seg_dist(p, W[b], W[(b + 1) % n]) < 1.2 for b in bound)]
        hit = {}
        for p in keep:
            c = tuple(int(math.floor(x)) for x in p)
            for k, v in world.items():
                if v[c]: hit[k] = hit.get(k, 0) + 1
        out['cloth_hits'][sl['name']] = hit
        out['mesh'][sl['name']] = {'verts': int(len(V)), 'tris': int(len(F)), 'checked': len(keep),
                                   'corner0_dev': round(float(min(np.linalg.norm(V - W[0], axis=1))), 3)}
        m = sl['name'].split('-')[0]
        if m in ('fore', 'main') and sl['name'] in ('fore-course', 'fore-topsail', 'fore-topgallant', 'main-topsail'):
            def clr(dx):
                best = 1e9
                for p in keep:
                    c = tuple(int(math.floor(x)) for x in (p[0] - dx, p[1], p[2]))
                    best = min(best, float(edt[m][c]))
                return round(best, 3)
            out['mast_clearance'][sl['name']] = {'min_edt': clr(0), 'pushed_3_toward_mast': clr(3)}
    txt = open(os.path.join(ex, 'sails.txt'), encoding='utf-8').read()
    eng = {}
    for m in re.finditer(r'^- ✓ `([^`]+)`［(\w+)］ (?:四邊形|三角帆).*?最鼓 ([-\d.]+).*?(?:牽繩 (\d+) 條)?｜色', txt, re.M):
        eng[m.group(1)] = {'state': m.group(2), 'billow': float(m.group(3)), 'ropes': int(m.group(4) or 0)}
    out['engine'] = eng
    out['broken'] = {k: int(v) for k, v in re.findall(r'🔢 (sails_broken|ropes_broken) = (\d+)', txt)}
    rev = [v['min_edt'] - v['pushed_3_toward_mast'] for v in out['mast_clearance'].values() if v['min_edt'] > 4]
    out['reverse_offset3'] = [round(x, 3) for x in rev]
    with open(os.path.join(d, 'verify_sails_post.json'), 'w', encoding='utf-8', newline='\n') as fo:
        json.dump(out, fo, ensure_ascii=False, indent=2, sort_keys=True); fo.write('\n')
    print(json.dumps(out, ensure_ascii=False, indent=1))


if __name__ == '__main__':
    main()
