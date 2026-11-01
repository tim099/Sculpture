# 杉心號 步驟 10（TASK-1152）：彈藥庫 ＝ 舵手腳前一塊墊板＋一個火藥桶（露天的獨木舟沒有艙房）⇒
#   masks/magazine/board.vox.txt、magazine_placement.json、verify_magazine.json
#   出處：apex-one-punt-01m 階段五的箭庫（一塊板＋桶模型、固定點 blast／door、關聯 meta kind=magazine）。
#   用法：python -I -X utf8 draft_magazine.py [--probe=dz=-1]   （probe ⇒ 桶上下移，量碰撞；⛔ 不寫檔）
#   · 桶一定要放（Ship_Magazine §8：遊戲照桶擺取用點；沒有桶 ⇒ 迴旋砲打完砲旁兩發就停）。
#   · 桶引用憲法號的 basecamp-frigate-constitution-01m-powder-barrel（0.02 m、scale 0.2、pivot 11,11,0 ＝ 底面正中）。
#   · 墊板讓火藥離開艙底的積水〔設計決定〕；墊板＋桶擺上去之後，走路格（同 draft_deck.py）要照樣 1 群。
import sys, os, json
import numpy as np

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import lines as HL
import draft_deck as DD
import draft_guns as DG

sys.stdout.reconfigure(encoding='utf-8')
SX, SY, SZ = 140, 101, 100
BARREL = 'basecamp-frigate-constitution-01m-powder-barrel'


def V(d):
    return d['v'] if isinstance(d, dict) and 'v' in d else d


def main():
    probe = {}
    for a in sys.argv[1:]:
        if a.startswith('--probe='):
            k, v = a[len('--probe='):].split('=')
            probe[k] = float(v)
    plan = HL.load_plan(HERE)
    L = HL.Lines(plan)
    M = V(plan['magazine'])
    YC = plan['space']['yc']
    H = DD.load_hull()
    S = L.solid(0, SX - 1, 39, 0)
    hollow = S & (H == 0)
    board = {}
    for x in range(M['board']['x'][0], M['board']['x'][1] + 1):
        for y in range(YC - M['board']['half_y'], YC + M['board']['half_y'] + 1):
            z = M['board']['z']
            assert hollow[x, y, z], ('墊板落在船殼上', x, y, z)
            board[(x, y, z)] = M['board']['color']
    post = [(DG.V(plan['guns'])['post']['x'], YC, z) for z in range(DG.V(plan['guns'])['post']['z0'], DG.V(plan['guns'])['post']['z1'] + 1)]
    occ = DG.solids(plan, post)
    for k in board:
        occ[k] = True
    at = [M['barrel_x'] + 0.5, YC + 0.5, M['board']['z'] + 1 + probe.get('dz', 0)]
    pivot = [11, 11, 0]
    cells = DG.export(BARREL)[:, :3].astype(float)
    hits = 0
    for off in [(0.5, 0.5, 0.5)] + [(dx, dy, dz) for dx in (0, 1) for dy in (0, 1) for dz in (0, 1)]:
        p = DG.place(cells + np.array(off), at, pivot, M['scale'], 0)
        k = np.floor(p).astype(int)
        hits += int(occ[k[:, 0], k[:, 1], k[:, 2]].sum())
    p = DG.place(cells + 0.5, at, pivot, M['scale'], 0)
    bb = [[round(float(v), 2) for v in p.min(0)], [round(float(v), 2) for v in p.max(0)]]
    # 墊板＋桶的外框都算擋路之後的走路格
    both = (H > 0)
    dl = np.loadtxt(os.path.join(HERE, 'masks', 'deck', 'deck_main.vox.txt'), delimiter=',', comments='#', dtype=np.int32, ndmin=2, encoding='utf-8')
    both[dl[:, 0], dl[:, 1], dl[:, 2]] = True
    walk_occ = np.zeros((SX, SY, 40), bool)
    walk_occ[:, :, :40] = both[:, :, :40]
    for k in board:
        walk_occ[k] = True
    lo, hi = np.floor(p.min(0)).astype(int), np.floor(p.max(0)).astype(int)
    walk_occ[lo[0]:hi[0] + 1, lo[1]:hi[1] + 1, lo[2]:min(hi[2] + 1, 40)] = True     # 桶的外框當實心（遊戲：不穿家具）
    fl = DD.bottom_floor(H, S)
    G = DD.walk_grid(walk_occ, S, fl)
    R = {'board_cells': len(board), 'barrel_at': at, 'barrel_bbox': bb, 'barrel_hits': hits, 'walk_groups': len(G), 'walk_main_m2': round(len(G[0]) * 0.01, 2),
         'walk_other_cells': [len(g) for g in G[1:6]]}
    if probe:
        print(json.dumps({'probe': probe, 'barrel_hits': hits}, ensure_ascii=False))
        return
    os.makedirs(os.path.join(HERE, 'masks', 'magazine'), exist_ok=True)
    with open(os.path.join(HERE, 'masks', 'magazine', 'board.vox.txt'), 'w', encoding='utf-8', newline='\n') as f:
        f.write('# 杉心號 彈藥庫的墊板（draft_magazine.py）x,y,z,color —— at 0,0,0\n')
        f.write(''.join('%d,%d,%d,%d\n' % (k[0], k[1], k[2], c) for k, c in sorted(board.items())))
    cx = (M['board']['x'][0] + M['board']['x'][1]) // 2
    out = {'host': 'basecamp-piragua-01m-magazine', 'link': '彈藥庫',
           'link_meta': {'kind': 'magazine', 'pos': 'aft', 'powder_lb': M['powder_lb'], 'id': 'magazine-1'},
           'anchors': {'blast': [cx, YC, M['board']['z'] + 3], 'door': [M['board']['x'][1] + 1, YC, M['board']['z']]},
           'models': [{'name': '桶-001', 'work': BARREL, 'at': at, 'pivot': pivot, 'scale': M['scale'], 'rotate': [0, 0, 0],
                       'meta': {'kind': 'powder', 'powder_lb': M['powder_lb'], 'id': 'powder-1'}}]}
    with open(os.path.join(HERE, 'magazine_placement.json'), 'w', encoding='utf-8', newline='\n') as f:
        json.dump(out, f, ensure_ascii=False, indent=1)
    with open(os.path.join(HERE, 'verify_magazine.json'), 'w', encoding='utf-8', newline='\n') as f:
        json.dump(R, f, ensure_ascii=False, indent=1)
    print(json.dumps(R, ensure_ascii=False))


if __name__ == '__main__':
    main()
