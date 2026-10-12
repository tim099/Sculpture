"""
憲法號雙舵輪（TASK-0507 外部模型測試件）—— 0.02 m／格的子作品，用「作品當模型」縮 0.2 掛進組裝件。

座標（子作品自己的）：x ＝ 沿船長（輪軸方向，船頭 +x）、y ＝ 橫向、z 上；z 0 ＝ 甲板面上第一層。
輪軸中心線 y 52.0、z 56.0（連續座標；格子對 y 52 左右對稱）。

尺寸（⚠ 未查證，照一般巡防艦比例；查到的只有「雙舵輪、在 quarterdeck」—— USS Constitution Museum）：
- 輪：外緣半徑 42 格（0.84 m，輪徑約 1.7 m）、輪緣徑向 4 格、厚 4 格；輪幅 10 根（模型論壇說，未查證），把手伸到半徑 50。
- 輪軸離甲板 56 格（1.12 m）；兩根支柱夾著鼓輪（drum），兩個輪在支柱外側。

輸出：masks/wheel/wheel.vox.txt（stampvox 清單，at 0,0,0）、rig_points_wheel.json（固定點）。
"""
import json, math, os, sys

HERE = os.path.dirname(os.path.abspath(__file__))
SIZE = (100, 104, 104)
CY, CZ = 52.0, 56.0

WOOD = 141      # 輪、鼓輪：淺木色
DARK = 136      # 支柱
BASE = 104      # 底座
BRASS = 212     # 輪轂端蓋
IRON = 36       # 輪軸、鼓輪鐵箍

WHEELS = [(8, 11), (88, 91)]          # 輪緣的 x 範圍（含）
HUBS = [(6, 13), (86, 93)]
R_RIM_IN, R_RIM_OUT = 38.0, 42.0
R_HUB = 6.0
N_SPOKE = 10
R_HANDLE = 50.0
STANCH = [(18, 25), (74, 81)]
DRUM = (27, 72)
R_DRUM = 9.0


def dist_to_seg2(py, pz, ay, az, by, bz):
    vy, vz = by - ay, bz - az
    t = max(0.0, min(1.0, ((py - ay) * vy + (pz - az) * vz) / (vy * vy + vz * vz)))
    qy, qz = ay + t * vy, az + t * vz
    return math.hypot(py - qy, pz - qz), t


def cell(x, y, z):
    px, py, pz = x + 0.5, y + 0.5, z + 0.5
    dy, dz = py - CY, pz - CZ
    r = math.hypot(dy, dz)
    for (h0, h1), (w0, w1) in zip(HUBS, WHEELS):
        xc = (w0 + w1 + 1) / 2.0
        # 輪轂（外側端面一圈黃銅）
        if h0 <= x <= h1 and r <= R_HUB:
            outer = h0 if h0 < 50 else h1
            return BRASS if x == outer else WOOD
        # 輪緣
        if w0 <= x <= w1 and R_RIM_IN <= r <= R_RIM_OUT:
            return WOOD
        # 輪幅與把手（圓柱，沿徑向；king spoke 朝正上）
        if abs(px - xc) <= 2.2:
            for k in range(N_SPOKE):
                th = math.pi / 2 + 2 * math.pi * k / N_SPOKE
                ey, ez = math.cos(th), math.sin(th)
                d, t = dist_to_seg2(dy, dz, ey * (R_HUB - 1), ez * (R_HUB - 1), ey * R_HANDLE, ez * R_HANDLE)
                s = (R_HUB - 1) + t * (R_HANDLE - R_HUB + 1)
                if s <= R_RIM_OUT:
                    rad = 1.6
                else:
                    u = (s - R_RIM_OUT) / (R_HANDLE - R_RIM_OUT)
                    rad = 1.2 + 0.9 * math.sin(math.pi * min(1.0, u * 0.95))   # 把手中段鼓起
                if d <= rad and math.hypot(d, px - xc) <= rad + 0.6:
                    return WOOD
    # 鼓輪（兩頭鐵箍）
    if DRUM[0] <= x <= DRUM[1] and r <= R_DRUM:
        return IRON if (x - DRUM[0] in (1, 2) or DRUM[1] - x in (1, 2)) else WOOD
    # 支柱：底寬 12、往上收到 8；頂上一塊帽；輪軸從中間穿過
    for s0, s1 in STANCH:
        if s0 <= x <= s1:
            if 0 <= z <= 62:
                half = 6.0 - 2.0 * z / 62.0
                if abs(py - CY) <= half:
                    return DARK
            if 63 <= z <= 66 and abs(py - CY) <= 5.5 and s0 - 1 <= x <= s1 + 1:
                return DARK
        if s0 - 3 <= x <= s1 + 3 and 0 <= z <= 2 and abs(py - CY) <= 8.0:
            return BASE
    # 輪軸
    if 4 <= x <= 95 and r <= 2.5:
        return IRON
    return 0


def main():
    out = []
    for x in range(SIZE[0]):
        for z in range(SIZE[2]):
            for y in range(SIZE[1]):
                c = cell(x, y, z)
                if c:
                    out.append((x, y, z, c))
    # 左右對稱檢查（y ↔ 103 − y）
    s = {(x, y, z): c for x, y, z, c in out}
    asym = sum(1 for (x, y, z), c in s.items() if s.get((x, 103 - y, z)) != c)
    d = os.path.join(HERE, 'masks', 'wheel')
    os.makedirs(d, exist_ok=True)
    with open(os.path.join(d, 'wheel.vox.txt'), 'w', encoding='utf-8', newline='\n') as f:
        f.write('# 憲法號雙舵輪（draft_wheel.py）x,y,z,color —— at 0,0,0\n')
        for x, y, z, c in out:
            f.write(f'{x},{y},{z},{c}\n')
    # 固定點：鼓輪下側兩點（舵索從這裡往下穿過甲板）、兩個輪轂外端
    pts = {
        'drum-rope-a': [36, 45, 49],
        'drum-rope-b': [63, 58, 49],
        'hub-aft': [6, 51, 55],
        'hub-fore': [93, 51, 55],
    }
    with open(os.path.join(HERE, 'rig_points_wheel.json'), 'w', encoding='utf-8') as f:
        json.dump(pts, f, ensure_ascii=False, indent=1)
    cnt = {}
    for *_, c in out:
        cnt[c] = cnt.get(c, 0) + 1
    print('voxels', len(out), 'colors', cnt, 'asym', asym)


if __name__ == '__main__':
    main()
