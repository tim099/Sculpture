# 步驟 9a：建立明清專屬通用火砲元件（0.05 m／格）：紅夷大銅砲（hongyi）與發熕（fagong）
#   依 Ship_Guns §2.2 / §4.3：+Y 朝砲口、Y↔0 對稱中心在 X、輪底 Z=0、tags=sub、齊備 7 枚標準固定點
import json, math, os, re, sys
import numpy as np

HERE = os.path.dirname(os.path.abspath(__file__))
DESIGN = os.path.dirname(HERE)
WORKS = os.path.dirname(os.path.dirname(os.path.abspath(DESIGN)))
sys.path.insert(0, HERE)
from wio import cli, PERSONA, HULL

sys.stdout.reconfigure(encoding='utf-8')


def build_hongyi():
    """紅夷大銅砲：15×64×23（0.05 m ⇒ 0.75×3.20×1.15 m），鑄銅砲管＋朱漆四輪戰船砲架。"""
    sx, sy, sz = 15, 64, 23
    G = np.zeros((sx, sy, sz), np.uint8)
    cx, cz_bore = 7, 16
    BRONZE, BRONZE_DK, BRONZE_LT = 176, 140, 212
    RED, WOOD, IRON = 192, 104, 73

    # 1. 鑄銅長砲管（y=2..62；後粗前細錐度＋銘文箍環＋砲尾球＋實心銅砲耳）
    for y in range(4, 63):
        t = (y - 4) / 58.0
        r = 3.5 - 1.2 * t
        if y in (5, 16, 28, 42, 58, 61):
            r += 0.55  # 強化銅箍與砲口唇緣
        col = BRONZE_LT if y in (5, 28, 61) else (BRONZE_DK if t < 0.25 else BRONZE)
        for x in range(sx):
            for z in range(cz_bore - 5, sz):
                d = math.hypot(x - cx, z - cz_bore)
                if d <= r:
                    if y >= 56 and d <= 1.2:
                        continue  # 砲口深膛孔（留給 muzzle 空格）
                    G[x, y, z] = col
    # 砲尾圓珠 knob（cascabel y=1..3）
    for y in (1, 2, 3):
        for x in range(cx - 2, cx + 3):
            for z in range(cz_bore - 2, cz_bore + 3):
                if math.hypot(x - cx, z - cz_bore) <= (1.4 if y == 1 else 1.8):
                    G[x, y, z] = BRONZE_DK
    # 雙側青銅砲耳 trunnions（y=29..31, x=2..12, z=14..15）
    G[2:13, 29:32, 14:16] = BRONZE_LT

    # 2. 明鄭朱漆四輪船砲架（雙腮牆 x=3..4 & 10..11，底盤＋橫枕＋四只實木鐵箍車輪）
    for y in range(8, 41):
        # 階梯狀朱漆砲架側壁（後低前高）
        h_top = 16 if y >= 26 else (14 if y >= 18 else (12 if y >= 12 else 10))
        for z in range(4, h_top):
            col = RED if (y % 6 != 0 and z < h_top - 1) else IRON
            for x in (3, 4, 10, 11):
                G[x, y, z] = col
    # 橫貫砲架底枕與前後輪軸（z=3..7, x=5..9）
    G[5:10, 9:39, 4:7] = WOOD
    G[5:10, 32:38, 7:12] = WOOD
    G[5:10, 8:11, 5:8] = RED  # 砲尾尾枕 transom
    # 前軸 (y=34..36) 與後軸 (y=12..14) ＋ 四輪（輪底 z=0，半徑 3.2）
    G[0:15, 34:37, 2:5] = WOOD
    G[0:15, 12:15, 2:5] = WOOD
    for wy in (13, 35):
        r_w = 3.2 if wy == 35 else 2.8
        cw_z = 3
        for y in range(wy - 4, wy + 5):
            for z in range(0, 8):
                if math.hypot(y - wy, z - cw_z) <= r_w:
                    col_w = IRON if math.hypot(y - wy, z - cw_z) >= r_w - 0.9 else WOOD
                    for x in (1, 2, 12, 13):
                        G[x, y, z] = col_w
    # 鐵環點 eye-aft / eye-fwd / train 連接砲架（保單一連通元件）
    G[1:3, 23, 11] = IRON
    G[12:14, 23, 11] = IRON
    G[7, 8, 6] = IRON

    anchors = {
        'muzzle':   [7, 62, 16],
        'breech':   [7, 5, 16],
        'cascabel': [7, 1, 16],
        'train':    [7, 9, 6],
        'trunnion': [7, 30, 16],
        'eye-aft':  [1, 23, 11],
        'eye-fwd':  [13, 23, 11],
    }
    return f'{HULL}-gun-hongyi', '明鄭 紅夷大銅砲（汎用重砲，0.05 m）', (sx, sy, sz), G, anchors, {'kind': 'gun', 'gun': 'hongyi'}


def build_fagong():
    """明清發熕：13×52×21（0.05 m ⇒ 0.65×2.60×1.05 m），鐵箍圓柱長管＋輕便戰棚砲架。"""
    sx, sy, sz = 13, 52, 21
    G = np.zeros((sx, sy, sz), np.uint8)
    cx, cz_bore = 6, 14
    IRON_BODY, IRON_HOOP, IRON_DK = 73, 110, 37
    WOOD, RED = 104, 192

    # 1. 熟鐵合鑄帶箍長砲管（y=5..50；每 6 格一道突出鐵箍 — 發熕典型「熟鐵裹箍」外觀）
    for y in range(5, 51):
        t = (y - 5) / 45.0
        r = 2.7 - 0.7 * t
        hoop = (y % 6 == 0) or y in (6, 48, 50)
        if hoop:
            r += 0.5
        col = IRON_HOOP if hoop else (IRON_DK if t < 0.2 else IRON_BODY)
        for x in range(sx):
            for z in range(cz_bore - 4, sz):
                d = math.hypot(x - cx, z - cz_bore)
                if d <= r:
                    if y >= 45 and d <= 1.0:
                        continue
                    G[x, y, z] = col
    # 長方形鐵尾栓／尾握（cascabel y=2..4）
    G[cx - 1:cx + 2, 2:5, cz_bore - 1:cz_bore + 2] = IRON_DK
    G[2:11, 23:26, 12:14] = IRON_HOOP  # 鐵砲耳

    # 2. 戰棚中型朱漆木架（x=3 & 9 側頰，輪徑略小適應戰棚機動作戰）
    for y in range(8, 34):
        h_top = 14 if y >= 21 else (12 if y >= 14 else 10)
        for z in range(4, h_top):
            col = RED if (y % 5 != 0 and z < h_top - 1) else IRON_DK
            for x in (3, 9):
                G[x, y, z] = col
    G[4:9, 9:32, 4:7] = WOOD
    G[4:9, 26:31, 7:11] = WOOD
    G[4:9, 8:10, 5:8] = RED
    G[0:13, 28:31, 2:4] = WOOD
    G[0:13, 11:14, 2:4] = WOOD
    for wy in (12, 29):
        r_w = 2.7
        cw_z = 2
        for y in range(wy - 3, wy + 4):
            for z in range(0, 6):
                if math.hypot(y - wy, z - cw_z) <= r_w:
                    col_w = IRON_DK if math.hypot(y - wy, z - cw_z) >= r_w - 0.8 else WOOD
                    for x in (1, 2, 10, 11):
                        G[x, y, z] = col_w
    G[1:3, 20, 10] = IRON_HOOP
    G[10:12, 20, 10] = IRON_HOOP
    G[6, 9, 5] = IRON_HOOP

    anchors = {
        'muzzle':   [6, 50, 14],
        'breech':   [6, 6, 14],
        'cascabel': [6, 2, 14],
        'train':    [6, 9, 5],
        'trunnion': [6, 24, 14],
        'eye-aft':  [1, 20, 10],
        'eye-fwd':  [11, 20, 10],
    }
    return f'{HULL}-gun-fagong', '明清 發熕（汎用中砲，0.05 m）', (sx, sy, sz), G, anchors, {'kind': 'gun', 'gun': 'fagong'}


def emit_gun(w, title, size, G, anchors, work_meta):
    od = os.path.join(DESIGN, 'masks', 'guns')
    os.makedirs(od, exist_ok=True)
    p = os.path.join(od, f'{w}.vox.txt')
    idx = np.argwhere(G > 0)
    with open(p, 'w', encoding='utf-8', newline='\n') as f:
        f.write(f'# {title}\n')
        for x, y, z in idx:
            f.write(f'{x},{y},{z},{G[x, y, z]}\n')
    if not os.path.exists(os.path.join(WORKS, w, 'work.json')):
        cli('op=work', 'sub=create', f'persona={PERSONA}', f'work={w}', f'title={title}',
            f'parent_work={HULL}', f'size={size[0]},{size[1]},{size[2]}', 'tags=sub')
        cli('op=work', 'sub=update', f'persona={PERSONA}', f'work={w}', 'meters_per_voxel=0.05')
        cli('op=stampvox', f'persona={PERSONA}', f'work={w}',
            'voxels=' + os.path.abspath(p).replace('\\', '/'),
            'at=0,0,0', f'expect_pixels={len(idx)}', 'draft=0', 'share=0')
        for ak, av in anchors.items():
            cli('op=work', 'sub=anchor', f'persona={PERSONA}', f'work={w}',
                f'name={ak}', f'at={av[0]},{av[1]},{av[2]}', 'note=Ship_Guns §4.3')
        cli('op=work', 'sub=meta', f'persona={PERSONA}', f'work={w}', 'part=work',
            'meta=' + json.dumps(work_meta, ensure_ascii=False, separators=(',', ':')),
            'note=汎用火砲預設 meta')
        print(f'✓ 建立汎用砲：{w} ({len(idx)} cells)')
    else:
        print(f'· 已有：{w}')
    print(cli('op=stats', f'work={w}', 'structure=1', f'mirror=x:{size[0] // 2}'))


def main():
    for fn in (build_hongyi, build_fagong):
        emit_gun(*fn())


if __name__ == '__main__':
    main()
