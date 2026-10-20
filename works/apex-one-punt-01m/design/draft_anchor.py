# 蓬特號 新圖紙 06（TASK-0754）：石錨（青銅時代紅海的梯形石錨，一個繫繩孔；通用部件，0.05 m、模型 scale 0.5）＋擺在艏台上、錨鏈孔固定點
#   ⇒ masks/anchor/stone.vox.txt、anchor_placement.json、verify_anchor.json
#   用法：python -I -X utf8 draft_anchor.py
#   · 座標照憲法號的錨：錨身沿 +z、繫繩點（ring）在上；x ＝ 寬、y ＝ 厚。固定點 ring／crown／fluke-a／fluke-b。
#   · 量：模型格心＋八角不落在船的實心；腳下（z −1）是艏台地板。
import sys, os, json
import numpy as np

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import lines as HL
from draft_lines import V, SX, SY
from draft_oars import occupancy
from draft_deck import load_list

sys.stdout.reconfigure(encoding='utf-8')


def main():
    plan = HL.load_plan()
    K = {k: V(v) for k, v in plan['anchor'].items()}
    YC = plan['space']['yc']
    occ = occupancy(plan)
    H, wb, wt, th = K['h'], K['w_bottom'], K['w_top'], K['thick']
    cx = wb // 2
    cells = {}
    for z in range(H):
        hw = (wb - (wb - wt) * z / (H - 1)) / 2
        for x in range(wb + 1):
            if abs(x + 0.5 - (cx + 0.5)) <= hw:
                for y in range(th):
                    hole = (K['hole_z'][0] <= z <= K['hole_z'][1]) and abs(x - cx) <= K['hole_half']
                    if not hole:
                        cells[(x, y, z)] = K['color']
    size = [wb + 1, th, H]
    anchors = {'ring': [cx, th // 2, K['hole_z'][1]], 'crown': [cx, th // 2, 0], 'fluke-a': [0, th // 2, 0], 'fluke-b': [wb, th // 2, 0]}
    piv = [cx + 0.5, th / 2, 0]
    S = 0.5
    arr = np.array(list(cells.keys()), float)
    corners = np.array([[dx, dy, dz] for dx in (-.5, .5) for dy in (-.5, .5) for dz in (-.5, .5)])
    R = {'cells': len(cells), 'size': size, 'size_m': [round(v * 0.05, 2) for v in size], 'models': []}
    models = []
    for side, s in (('P', -1), ('S', 1)):
        at = [K['x'] + 0.5, YC + 0.5 + s * K['dy'], K['z']]
        pts = np.concatenate([arr + 0.5] + [arr + 0.5 + c for c in corners])
        W = (pts - piv) * S + at
        ci = np.floor(W).astype(int)
        hit = int(occ[ci[:, 0], ci[:, 1], ci[:, 2]].sum())
        under = np.floor(np.array(at) - [0, 0, 0.5]).astype(int)
        models.append({'name': 'anchor-' + side, 'at': at, 'pivot': piv, 'scale': S, 'meta': {'kind': 'anchor', 'anchor': 'stone'}})
        R['models'].append({'name': 'anchor-' + side, 'collide': hit, 'floor_below': bool(occ[tuple(under)])})
    # 錨鏈孔（船殼固定點）：艏台那一段舷頂最外面的格
    hull = load_list(os.path.join(HERE, 'masks', 'hull', 'hull.vox.txt')) > 0
    hawse = {}
    x = K['hawse_x']
    col = np.argwhere(hull[x])
    zt = col[:, 1].max()
    ys = col[col[:, 1] == zt][:, 0]
    hawse['hawse-S'] = [int(x), int(ys.max()), int(zt)]
    hawse['hawse-P'] = [int(x), int(ys.min()), int(zt)]
    R['hawse'] = hawse
    os.makedirs(os.path.join(HERE, 'masks', 'anchor'), exist_ok=True)
    with open(os.path.join(HERE, 'masks', 'anchor', 'stone.vox.txt'), 'w', encoding='utf-8', newline='\n') as f:
        f.write('# 石錨（draft_anchor.py）x,y,z,color —— 元件自己的座標（0.05 m）\n')
        f.write('\n'.join('%d,%d,%d,%d' % (x, y, z, c) for (x, y, z), c in sorted(cells.items(), key=lambda kv: (kv[0][2], kv[0][0], kv[0][1]))) + '\n')
    with open(os.path.join(HERE, 'anchor_placement.json'), 'w', encoding='utf-8', newline='\n') as f:
        json.dump({'size': size, 'anchors': anchors, 'models': models, 'hawse': hawse}, f, ensure_ascii=False, indent=1)
    with open(os.path.join(HERE, 'verify_anchor.json'), 'w', encoding='utf-8', newline='\n') as f:
        json.dump(R, f, ensure_ascii=False, indent=1)
    print(json.dumps(R, ensure_ascii=False))


if __name__ == '__main__':
    main()
