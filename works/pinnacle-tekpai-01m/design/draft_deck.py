# 台灣帆竹筏 Tek-pái 步驟 5：筏面、走路格與防潮木桶艙產生器（TASK-1312）
#   目標作品：pinnacle-tekpai-01m-deck-main（連結於 pinnacle-tekpai-01m-assembly 的 甲板-main）
#   規範：Ship_Decks §9.3（kind=deck, level=0, floor=地板上第一層空氣, thick=1）
import hashlib
import json
import os
import sys
from collections import deque
import numpy as np
from PIL import Image, ImageDraw, ImageFont
from scipy import ndimage

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import lines as HL

sys.stdout.reconfigure(encoding='utf-8')


def font(sz):
    for f in ('C:/Windows/Fonts/msjh.ttc', 'C:/Windows/Fonts/msyh.ttc', 'C:/Windows/Fonts/arial.ttf'):
        if os.path.exists(f):
            return ImageFont.truetype(f, sz)
    return ImageFont.load_default()


def rgb(i):
    return ((int(i) >> 5 & 7) * 255 // 7, (int(i) >> 2 & 7) * 255 // 7, (int(i) & 3) * 255 // 3)


def load_hull(SX, SY, SZ):
    arr = np.loadtxt(os.path.join(HERE, 'masks', 'hull_voxels.vox.txt'), delimiter=',', comments='#', dtype=np.int32, ndmin=2, encoding='utf-8')
    H = np.zeros((SX, SY, SZ), dtype=np.uint8)
    H[arr[:, 0], arr[:, 1], arr[:, 2]] = arr[:, 3].astype(np.uint8)
    return H


def build_deck(plan, H, dz_probe=0):
    SX, SY, SZ = H.shape
    YC = int(plan['space']['yc'])
    D = np.zeros((SX, SY, SZ), dtype=np.uint8)

    c_slat = 181      # 日曬竹柵板 (#b6b655)
    c_slat_trim = 140 # 邊框深黃木條 (#916d00)
    c_tub_wall = 172  # 檜木桶艙圍板 (#b66d00)
    c_tub_floor = 173 # 艙內乾燥鋪板 (#b66d55)
    c_collar = 104    # 深木壓條與桅座 (#6d4800)

    # 1. 舯部墊高竹木柵格平台 (x=34..98, y=38..62, z=4+dz_probe)
    #    坐落於橫擔 z=3 之上（第 0 層空隙不與船殼重疊）；預留 (82, 50) 桅孔
    z_mid = 4 + dz_probe
    for x in range(34, 99):
        for y in range(38, 63):
            if x == 82 and y == YC:
                continue  # 單竹桅穿孔
            if H[x, y, z_mid] != 0:
                continue
            if y in (38, 62) or x in (34, 98):
                D[x, y, z_mid] = c_slat_trim
            elif (x % 6 == 0) or (abs(y - YC) % 4 == 0):
                D[x, y, z_mid] = c_slat_trim
            else:
                D[x, y, z_mid] = c_slat

    # 2. 艉舵手墊高踏台 (x=24..33, y=44..56, z=6+dz_probe) —— 避開船殼格子
    z_aft = 6 + dz_probe
    for x in range(24, 34):
        for y in range(44, 57):
            if H[x, y, z_aft] == 0 and D[x, y, z_aft] == 0:
                D[x, y, z_aft] = c_slat_trim if (y in (44, 56) or x == 24) else c_slat

    # 3. 艏前操作台 (x=99..105, y=44..56, z=5+dz_probe)
    z_fwd = 5 + dz_probe
    for x in range(99, 106):
        for y in range(44, 57):
            if H[x, y, z_fwd] == 0 and D[x, y, z_fwd] == 0:
                D[x, y, z_fwd] = c_slat_trim if (y in (44, 56) or x == 105) else c_slat

    # 4. 單竹桅座護箍 (x=80..84, y=48..52, z=5+dz_probe；中心 82,50 留空插桅)
    z_mstep = 5 + dz_probe
    for x in range(80, 85):
        for y in range(48, 53):
            if x == 82 and y == YC:
                continue
            if abs(x - 82) <= 1 and abs(y - YC) <= 1:
                D[x, y, z_mstep] = c_collar
            elif (x in (80, 84) or y in (48, 52)) and H[x, y, z_mstep] == 0:
                D[x, y, z_mstep] = c_slat_trim

    # 5. 中央防潮木桶艙 (x=50..74, y=44..56)：
    #    兩側保留 y=38..43（左舷 0.6 m）與 y=57..62（右舷 0.6 m）暢通走道
    tx0, tx1 = 50, 74
    ty0, ty1 = 44, 56
    z_tfloor = 5 + dz_probe
    z_twall_hi = 7 + dz_probe
    # 內底板
    for x in range(tx0 + 1, tx1):
        for y in range(ty0 + 1, ty1):
            if H[x, y, z_tfloor] == 0:
                D[x, y, z_tfloor] = c_tub_floor
    # 四週圍板（前後左右牆 z = 5..7），四角加深木柱
    for x in range(tx0, tx1 + 1):
        for y in range(ty0, ty1 + 1):
            is_edge = (x in (tx0, tx1) or y in (ty0, ty1))
            if not is_edge:
                continue
            is_corner = (x in (tx0, tx1) and y in (ty0, ty1))
            for z in range(z_tfloor, z_twall_hi + 1):
                if H[x, y, z] == 0:
                    if is_corner or z == z_twall_hi:
                        D[x, y, z] = c_collar
                    else:
                        D[x, y, z] = c_tub_wall

    floor_str = f"24:{z_aft+1},33:{z_aft+1},34:{z_mid+1},98:{z_mid+1},99:{z_fwd+1},105:{z_fwd+1}"
    return D, floor_str


def interp_floor(floor_str, x):
    pts = []
    for tok in floor_str.split(','):
        xs, zs = tok.split(':')
        pts.append((float(xs), float(zs)))
    if x < pts[0][0] or x > pts[-1][0]:
        return None
    for i in range(len(pts) - 1):
        x0, z0 = pts[i]
        x1, z1 = pts[i + 1]
        if x0 <= x <= x1:
            if x1 == x0:
                return z0
            return z0 + (z1 - z0) * ((x - x0) / (x1 - x0))
    return pts[-1][1]


def check_walkable(H, D, floor_str):
    comb = np.where(D > 0, D, H) > 0
    SX, SY, SZ = comb.shape
    nav_z = np.full((SX, SY), -1, dtype=np.int32)

    # 依 Ship_Decks §9.3：人站高度 z_air 在 floor 上下 [-2..+3] 內且頭頂 ≥1.2 m (12 格) 為空
    for x in range(SX):
        fz = interp_floor(floor_str, x)
        if fz is None:
            continue
        for y in range(SY):
            best = None
            for z_air in range(1, SZ - 12):
                if not comb[x, y, z_air - 1]:
                    continue
                if comb[x, y, z_air : z_air + 12].any():
                    continue
                if -2.5 <= (z_air - fz) <= 3.5:
                    if best is None or abs(z_air - fz) < abs(best - fz):
                        best = z_air
            if best is not None and (D[x, y, best - 1] > 0 or (38 <= y <= 62 and H[x, y, best - 1] > 0 and D[x, y, :].any() == False and any(D[nx, y, :].any() for nx in (x - 1, x + 1) if 0 <= nx < SX))):
                nav_z[x, y] = best

    # BFS 計算走路格連通性（四鄰高差 <= 3 格）
    pts = set(zip(*np.where(nav_z > 0)))
    seen = set()
    comps = []
    for p in sorted(pts):
        if p in seen:
            continue
        q = deque([p])
        seen.add(p)
        comp = []
        while q:
            cx, cy = q.popleft()
            comp.append((cx, cy))
            cz = nav_z[cx, cy]
            for dx, dy in ((1, 0), (-1, 0), (0, 1), (0, -1)):
                nx, ny = cx + dx, cy + dy
                if (nx, ny) in pts and (nx, ny) not in seen:
                    if abs(int(nav_z[nx, ny]) - int(cz)) <= 3:
                        seen.add((nx, ny))
                        q.append((nx, ny))
        comps.append(comp)
    comps.sort(key=len, reverse=True)
    return nav_z, comps


def write_vox_list(D, out_path):
    os.makedirs(os.path.dirname(out_path), exist_ok=True)
    xs, ys, zs = np.nonzero(D)
    lines = ['# Tek-pái deck-main voxels (x,y,z,color)']
    for x, y, z in zip(xs.tolist(), ys.tolist(), zs.tolist()):
        lines.append(f'{x},{y},{z},{int(D[x, y, z])}')
    content = '\n'.join(lines) + '\n'
    with open(out_path, 'w', encoding='utf-8', newline='\n') as f:
        f.write(content)
    return hashlib.sha256(content.encode('utf-8')).hexdigest()


def draw_sheet(H, D, nav_z, comps, out_png):
    SX, SY, SZ = D.shape
    img = Image.new('RGB', (1440, 760), (247, 243, 234))
    d = ImageDraw.Draw(img)
    ft = font(20)
    fs = font(13)
    d.text((28, 18), '台灣帆竹筏 Tek-pái 新圖紙 02：墊高筏面、防潮木桶艙與走路格連通 (步驟 5)', fill=(35, 30, 26), font=ft)
    d.text((28, 48), f'甲板總格數={int((D>0).sum())} | 可站走路格={int((nav_z>0).sum())} | 最大連通群={len(comps[0]) if comps else 0} 格（共 {len(comps)} 群）', fill=(60, 52, 46), font=fs)

    # 俯視疊加（船殼灰棕底 + 甲板木色 + 綠點＝最大走路格主群）
    s = 9
    ox, oy = 60, 110
    ymin, ymax = 32, 68
    main_set = set(comps[0]) if comps else set()
    for x in range(SX):
        for y in range(ymin, ymax + 1):
            zh = np.where(H[x, y, :] > 0)[0]
            zd = np.where(D[x, y, :] > 0)[0]
            rx0, ry0 = ox + x * s, oy + (y - ymin) * 9
            if len(zd):
                c = rgb(int(D[x, y, zd.max()]))
                d.rectangle([rx0, ry0, rx0 + s - 1, ry0 + 8], fill=c)
            elif len(zh):
                c = rgb(int(H[x, y, zh.max()]))
                # 柔化底色突出甲板
                c = (int(c[0] * 0.7 + 70), int(c[1] * 0.7 + 68), int(c[2] * 0.7 + 62))
                d.rectangle([rx0, ry0, rx0 + s - 1, ry0 + 8], fill=c)
            if (x, y) in main_set:
                d.rectangle([rx0 + 3, ry0 + 3, rx0 + 5, ry0 + 5], fill=(35, 145, 70))

    # 縱剖面 (y=50 中線 與 y=40 側走道)
    py_mid = 660
    d.text((60, 485), '縱剖面 y=40（左側走道一路貫通艏艉） / 舯木桶艙剖面 y=50', fill=(40, 40, 40), font=fs)
    for x in range(SX):
        for z in range(25):
            ch = H[x, 40, z]
            cd = D[x, 40, z]
            if cd or ch:
                c = rgb(int(cd if cd else ch))
                d.rectangle([ox + x * s, py_mid - (z + 1) * s, ox + (x + 1) * s - 1, py_mid - z * s - 1], fill=c)
    d.line([(ox, py_mid - 3 * s), (ox + SX * s, py_mid - 3 * s)], fill=(205, 55, 50), width=2)
    img.save(out_png, optimize=False)


def main():
    plan = HL.load_plan(HERE)
    SX, SY, SZ = plan['space']['hull']
    H = load_hull(SX, SY, SZ)
    D, floor_str = build_deck(plan, H, dz_probe=0)

    # 檢查與船殼零重疊
    overlap = int(((H > 0) & (D > 0)).sum())
    assert overlap == 0, f"甲板與船殼重疊 {overlap} 格"

    # 檢查走路格連通
    nav_z, comps = check_walkable(H, D, floor_str)
    # 反向對照：甲板高度故意 +3 格，走路格高度跟著 +3
    Dp, floor_p = build_deck(plan, H, dz_probe=3)
    nav_p, _ = check_walkable(H, Dp, floor_p)
    delta_nav = int(nav_p[60, 40] - nav_z[60, 40])
    assert delta_nav == 3, f"反向對照失敗：{delta_nav}"

    vox_path = os.path.join(HERE, 'masks_deck', 'deck_voxels.vox.txt')
    vox_sha = write_vox_list(D, vox_path)

    # 寫 decks_meta.tsv
    meta = {
        'kind': 'deck',
        'deck': 'main',
        'level': 0,
        'name': '主筏面與防潮木桶艙',
        'thick': 1,
        'floor': floor_str,
    }
    tsv_path = os.path.join(HERE, 'decks_meta.tsv')
    with open(tsv_path, 'w', encoding='utf-8', newline='\n') as f:
        f.write(f"link\t甲板-main\t{json.dumps(meta, ensure_ascii=False)}\n")

    sheet_path = os.path.join(HERE, 'sheet02_deck_v1.png')
    draw_sheet(H, D, nav_z, comps, sheet_path)

    rep = {
        'work': 'pinnacle-tekpai-01m-deck-main',
        'deck_voxels': int((D > 0).sum()),
        'overlap_with_hull': overlap,
        'floor_meta': floor_str,
        'walkable_cells': int((nav_z > 0).sum()),
        'walk_components': [len(c) for c in comps],
        'mirror_diff': int((D != D[:, ::-1, :]).sum()),
        'reverse_control_delta': delta_nav,
        'deck_voxels_sha256': vox_sha,
    }
    with open(os.path.join(HERE, 'verify_deck.json'), 'w', encoding='utf-8', newline='\n') as f:
        json.dump(rep, f, ensure_ascii=False, indent=2, sort_keys=True)
        f.write('\n')
    print(json.dumps(rep, ensure_ascii=False, indent=2))


if __name__ == '__main__':
    main()
