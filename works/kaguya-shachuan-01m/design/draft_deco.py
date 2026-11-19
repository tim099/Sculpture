# 沙船 步驟 6（TASK-1313）：裝飾與窗玻璃 —— 船尾窗玻璃（material=glass）、披水板、方艏彩繪牌額、船尾牌飾、護舷（deco=1）
#   出處：kaguya-guineaman-01m/design/draft_deco.py ＋ draft_stern_glass.py
#   用法：python -I -X utf8 draft_deco.py <design 資料夾>
import sys, os, json, math
import numpy as np
from scipy import ndimage

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import lines as HL
from draft_lines import build as hull_build
from draft_decks import load_carved_hull

sys.stdout.reconfigure(encoding='utf-8')


def main():
    design = sys.argv[1] if len(sys.argv) > 1 and not sys.argv[1].startswith('--') else HERE
    plan = HL.load_plan(design)
    L, _, S, x0, ylo = hull_build(plan, None)
    YC = L.YC
    H_col = load_carved_hull(design, x0, ylo, S.shape)
    occ_hull = H_col > 0

    # ── 1. 船尾窗玻璃（確保 6 連通、不重疊船殼與甲板）──
    # 讀入步驟 4 預留的 glass.vox.txt，並補齊斜艉柱上下換行時的斜角連接格（Ship_Materials §9.5）
    g_raw = np.loadtxt(os.path.join(design, 'masks', 'ports', 'glass.vox.txt'), delimiter=',', comments='#', dtype=int, ndmin=2)
    glass_set = {(int(x), int(y), int(z)): int(c) for x, y, z, c in g_raw}
    # 檢查上下兩排 (z 與 z+1) 若 x 不同，補 (min(x_pair), y, z_upper) 或 (max(x_pair), y, z_lower) 以保持 6 連通
    by_yz = {(y, z): x for (x, y, z) in glass_set}
    extra_g = {}
    for (y, z), x in by_yz.items():
        if (y, z + 1) in by_yz:
            x2 = by_yz[(y, z + 1)]
            if x2 != x:
                # 若不重合船殼，補 (x2, y, z) 使 6 連通
                if not occ_hull[x2 - x0, y - ylo, z]:
                    extra_g[(x2, y, z)] = 155
                elif not occ_hull[x - x0, y - ylo, z + 1]:
                    extra_g[(x, y, z + 1)] = 155
    glass_set.update(extra_g)
    # 驗證無重疊、每扇窗各成 1 個 6 連通元件（共 2 塊）
    g_arr = np.zeros(S.shape, bool)
    for (x, y, z) in glass_set:
        assert not occ_hull[x - x0, y - ylo, z], f'玻璃重疊船殼 ({x},{y},{z})'
        g_arr[x - x0, y - ylo, z] = True
    _, n_glass_comp = ndimage.label(g_arr)

    os.makedirs(os.path.join(design, 'masks', 'deco'), exist_ok=True)
    gp = os.path.join(design, 'masks', 'deco', 'stern_glass.vox.txt')
    with open(gp, 'w', encoding='utf-8', newline='\n') as f:
        f.write('# 沙船 船尾窗玻璃（步驟 6，6 連通，material=glass）x,y,z,color\n')
        for (x, y, z), c in sorted(glass_set.items()):
            f.write(f'{x},{y},{z},{c}\n')

    # ── 2. 披水板（leeboard，局部座標 0..21 x 0..2 x 0..22，2.2 m 長 × 2.3 m 高）──
    # 形狀：經典上窄下寬的刀板形（頂部軸頭 x=6..14，下段展寬至 0..21）
    lb_vox = []
    for z in range(23):
        t = z / 22.0
        # 下半部寬 22 格，上半部漸收至 10 格
        half_len = 11.0 - 6.0 * (t ** 1.3)
        x_lo = int(round(10.5 - half_len))
        x_hi = int(round(10.5 + half_len))
        for x in range(max(0, x_lo), min(22, x_hi + 1)):
            for y in (0, 1):
                # 外側表面為木條拼板（136 為主、68 橫帶加固、頂端 196 朱紅飾邊）
                if z >= 21:
                    col = 196
                elif z in (3, 10, 17):
                    col = 68
                else:
                    col = 136
                lb_vox.append((x, y, z, col))
    lb_path = os.path.join(design, 'masks', 'deco', 'leeboard.vox.txt')
    with open(lb_path, 'w', encoding='utf-8', newline='\n') as f:
        f.write('# 沙船 披水板（局部座標，pivot=(11,0,22)）x,y,z,color\n')
        for x, y, z, c in lb_vox:
            f.write(f'{x},{y},{z},{c}\n')

    # 計算披水板在組裝件中的安全 y 位置（貼於船腰外緣、0 重疊）
    lb_plan = plan['leeboards']
    # 量 x=134..156, z=5..27 右舷（+y）最外緣
    y_max_hull = 0
    for x in range(lb_plan['x0'], lb_plan['x1'] + 1):
        for z in range(5, 29):
            ys = np.nonzero(occ_hull[x - x0, :, z])[0]
            if len(ys):
                y_max_hull = max(y_max_hull, int(ys.max() + ylo))
    dy_lb = (y_max_hull - YC) + 1  # 緊貼最寬處外 1 格

    # ── 3. 方艏彩繪牌額與艏角（deco_bow，局部座標寬 y: 0..16, x: 0..2, z: 0..8）──
    # 沿方艏逐層外緣（bow_x_by_z[z] + 1）貼齊斜艏柱，避免 z>=30 前傾與船殼 x=244 重疊穿模
    bow_vox = []
    bow_x_by_z = {}
    for z in range(25, 36):
        xs = np.nonzero(occ_hull[:, YC - ylo, z])[0]
        if len(xs):
            bow_x_by_z[z] = int(xs.max() + x0)
    bow_at_x = min(bow_x_by_z.get(z, 243) + 1 for z in range(26, 35))
    for z in range(9):
        dx = (bow_x_by_z.get(26 + z, 243) + 1) - bow_at_x
        for y in range(17):
            dy = abs(y - 8)
            if z in (0, 8) or dy == 8:
                col = 248  # 金邊框
            elif dy <= 2 and 2 <= z <= 6:
                col = 248 if (dy == 1 and z in (3, 5)) else 196  # 朱紅底嵌金虎紋
            else:
                col = 196 if (z % 2 == 0) else 68
            bow_vox.append((dx, y, z, col))
    # 兩側頭伏獅延伸木角（y=0,1,15,16 往前多伸 1 格）
    for z_h, col_h in ((7, 136), (8, 248)):
        dx = (bow_x_by_z.get(26 + z_h, 244) + 1) - bow_at_x
        for y in (0, 1, 15, 16):
            bow_vox.append((dx + 1, y, z_h, col_h))
    bow_path = os.path.join(design, 'masks', 'deco', 'deco_bow.vox.txt')
    with open(bow_path, 'w', encoding='utf-8', newline='\n') as f:
        f.write('# 沙船 方艏彩繪牌額（局部座標，pivot=(0,8,0)，貼齊斜艏柱 0 重疊）x,y,z,color\n')
        for x, y, z, c in bow_vox:
            f.write(f'{x},{y},{z},{c}\n')

    # ── 4. 船尾牌飾（deco_stern，局部座標 x: 0..1, y: 0..16, z: 0..4，貼齊斜艉柱）──
    stern_x_by_z = {}
    for z in range(33, 41):
        xs = np.nonzero(occ_hull[:, YC - ylo, z])[0]
        if len(xs):
            stern_x_by_z[z] = int(xs.min() + x0)
    stern_at_x = min(stern_x_by_z.get(z, 40) - 1 for z in range(34, 39))
    stern_vox = []
    for z in range(5):
        dx = (stern_x_by_z.get(34 + z, 40) - 1) - stern_at_x
        for y in range(17):
            dy = abs(y - 8)
            if z in (0, 4) or dy == 8:
                col = 248  # 金框
            elif dy in (2, 3, 5) and z in (1, 2, 3):
                col = 248  # 金色篆飾
            else:
                col = 36   # 黑漆牌底
            stern_vox.append((dx, y, z, col))
    stern_path = os.path.join(design, 'masks', 'deco', 'deco_stern.vox.txt')
    with open(stern_path, 'w', encoding='utf-8', newline='\n') as f:
        f.write('# 沙船 船尾牌飾（局部座標，pivot=(0,8,0)，貼齊斜艉柱 0 重疊）x,y,z,color\n')
        for x, y, z, c in stern_vox:
            f.write(f'{x},{y},{z},{c}\n')

    # 計算方艏、方艉與護舷的實際貼面位置

    # 護舷（共用 kiara-tunis-sandal-01m-fender，size 3×1×4，min=[1,1,1] max=[3,1,4]）
    # 掛於船腰前後（x=114、x=196），貼在最寬處外側 1 格
    fenders = []
    for fx in (114, 196):
        ys = np.nonzero(occ_hull[fx - x0, :, 22])[0]
        y_out_s = int(ys.max() + ylo) + 1
        y_out_p = int(ys.min() + ylo) - 1
        fenders.append({'name': f'護舷-S-{fx}', 'at': [fx, y_out_s, 23.0], 'rotate': [0, 0, 0]})
        fenders.append({'name': f'護舷-P-{fx}', 'at': [fx, y_out_p, 23.0], 'rotate': [0, 0, 180]})

    placement = {
        'glass': {'cells': len(glass_set), 'components_6': int(n_glass_comp)},
        'leeboards': {
            'cells': len(lb_vox),
            'S': {'at': [145.0, float(YC + dy_lb), 27.0], 'pivot': [11.0, 0.0, 22.0], 'mirror': 'none'},
            'P': {'at': [145.0, float(YC - dy_lb), 27.0], 'pivot': [11.0, 1.0, 22.0], 'mirror': 'none'},
        },
        'deco_bow': {'cells': len(bow_vox), 'at': [float(bow_at_x), float(YC + 0.5), 26.0], 'pivot': [0.0, 8.5, 0.0]},
        'deco_stern': {'cells': len(stern_vox), 'at': [float(stern_at_x), float(YC + 0.5), 34.0], 'pivot': [0.0, 8.5, 0.0]},
        'fenders': fenders,
    }
    with open(os.path.join(design, 'deco_placement.json'), 'w', encoding='utf-8', newline='\n') as f:
        json.dump(placement, f, ensure_ascii=False, indent=2)
    print(json.dumps(placement, ensure_ascii=False))


if __name__ == '__main__':
    main()
