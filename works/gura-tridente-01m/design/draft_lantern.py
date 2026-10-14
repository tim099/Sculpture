# 三叉戟號 階段五（TASK-0558）船尾燈：自己的子作品（0.05 m／格）＋兩盞模型站在 taffrail 上（|dy| 40）
#   八角燈：金腳、金杯、琥珀玻璃＋金框柱、黑頂金肋、金尖；固定點 base（腳底）、wick（火焰中心：遊戲在這裡放點光源）、bail（頂）
#   輸入：plan.json（stern_deco.lantern、stern_deco.colors）＋「階段五之前」的組裝件（找 taffrail 頂）
#   輸出：masks/lantern/lantern.vox.txt（子作品座標）、lantern_placement.json（子作品框、固定點、兩盞模型的 at／pivot／scale）、verify_lantern.json
#   用法：python -I -X utf8 draft_lantern.py <design> [--base=<快取.npy>]
import sys, os, json, math
import numpy as np

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import hull_lines as HL
import deco_base as DB

YC = 200
N = 17                     # 框 17×17（中心第 8 格）
H = 36


def octagon(dx, dy):
    return max(abs(dx), abs(dy), (abs(dx) + abs(dy)) / math.sqrt(2.0))


def main():
    sys.stdout.reconfigure(encoding='utf-8')
    design = sys.argv[1]
    cache = next((a.split('=', 1)[1] for a in sys.argv[2:] if a.startswith('--base=')), None)
    plan = HL.load_plan(design)
    LT = plan['stern_deco']['lantern']
    C = plan['stern_deco']['colors']
    GOLD, DARK, AMBER = C['trim'], C['dark'], C['amber']
    c0 = N // 2
    cells = {}

    def disk(z, r, col, ring=None):
        for x in range(N):
            for y in range(N):
                d = octagon(x - c0, y - c0)
                if d <= r:
                    cells[(x, y, z)] = col if ring is None or d <= r - 1 else ring

    for z, r in ((0, 1.5), (1, 2.2)):                                  # 腳
        disk(z, r, GOLD)
    for z in range(2, 6):                                              # 杯
        disk(z, 3 + (z - 2), GOLD)
    for z in (6, 7):
        disk(z, 7.2, GOLD)                                             # 底圈
    for z in range(8, 24):                                             # 燈身：琥珀玻璃、八個角一根金柱、中間一道金腰
        for x in range(N):
            for y in range(N):
                dx, dy = x - c0, y - c0
                d = octagon(dx, dy)
                if d > 6.5:
                    continue
                ang = math.degrees(math.atan2(dy, dx)) % 45.0
                post = d > 5.5 and (ang < 8 or ang > 37)
                cells[(x, y, z)] = GOLD if post or z in (15, 16) and d > 5.5 else AMBER
    for z in (24, 25):
        disk(z, 7.2, GOLD)                                             # 頂圈
    for k, z in enumerate(range(26, 32)):                              # 圓頂：黑、八道金肋
        r = 6.5 * math.sqrt(max(0.0, 1 - ((k + 1) / 7.0) ** 2)) + 0.6
        for x in range(N):
            for y in range(N):
                dx, dy = x - c0, y - c0
                d = octagon(dx, dy)
                if d > r:
                    continue
                rib = (dx == 0 or dy == 0 or abs(dx) == abs(dy)) and d > 0.5
                cells[(x, y, z)] = GOLD if rib else DARK
    for z in range(32, H):                                             # 金尖
        for x in range(N):
            for y in range(N):
                if octagon(x - c0, y - c0) <= (1.2 if z < 34 else 0.4):
                    cells[(x, y, z)] = GOLD
    anchors = {'base': [c0, c0, 0], 'wick': [c0, c0, 15], 'bail': [c0, c0, H - 1]}
    # 對稱讀數（x、y 兩個方向）
    asym = sum(1 for (x, y, z) in cells if (2 * c0 - x, y, z) not in cells or (x, 2 * c0 - y, z) not in cells)

    # ── 站哪：taffrail 頂（|dy| 40 那一欄、船尾那一段牆最上面那格）──
    G = np.load(cache) if cache and os.path.exists(cache) else DB.base_grid()
    S = G > 0
    models = {}
    for nm, sgn in (('lantern-P', -1), ('lantern-S', 1)):
        y = YC + sgn * LT['dy']
        col = S[40:130, y, :]
        zt = int(np.nonzero(col.any(0))[0].max())
        xs = np.nonzero(col[:, zt])[0] + 40
        xm = (xs.min() + xs.max() + 1) / 2.0                           # 牆頂那一段的中點（格邊座標）
        models[nm] = {'at': [round(xm, 2), y + 0.5, zt + 1], 'pivot': [c0 + 0.5, c0 + 0.5, 0], 'scale': LT['scale'],
                      'taffrail_top': {'z': zt, 'x': [int(xs.min()), int(xs.max())]},
                      'meta': {'kind': 'light'}}
    org, size = [0, 0, 0], [N, N, H]
    n, h = DB.write_local(os.path.join(design, 'masks', 'lantern', 'lantern.vox.txt'), cells, org, '# 三叉戟號 船尾燈（0.05 m／格，子作品座標）\n')
    place = {'lantern': {'at': org, 'size': size, 'meters_per_voxel': 0.05, 'anchors': anchors}, 'models': models}
    with open(os.path.join(design, 'lantern_placement.json'), 'w', encoding='utf-8', newline='\n') as f:
        json.dump(place, f, ensure_ascii=False, indent=1)
    by = {int(c): int(m) for c, m in zip(*np.unique(np.array(list(cells.values())), return_counts=True))}
    R = {'cells': n, 'sha256': h, 'by_color': by, 'asym_xy': asym, 'placement': place}
    with open(os.path.join(design, 'verify_lantern.json'), 'w', encoding='utf-8', newline='\n') as f:
        json.dump(R, f, ensure_ascii=False, indent=1)
    print(json.dumps(R, ensure_ascii=False))


if __name__ == '__main__':
    main()
