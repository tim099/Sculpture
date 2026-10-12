"""
憲法號第二批砲（階段二十八，TASK-0478；外部模型 TASK-0507）—— 0.05 m／格的子作品，用「作品當模型」縮 0.5 掛進組裝件。

1812 年的配置（美國海軍 NHHC 與 USS Constitution Museum 一致的版本）：spar deck 24 門 32 磅 carronade、船頭一門 18 磅長砲（chase gun）、
gun deck 30 門 24 磅長砲（已做，0.1 m 子作品 -gun-24）。⚠ 別的來源有 20／22 門 carronade、兩門 24 磅 bow chaser —— 記錄不全（Wikipedia 也這麼說）。

座標（兩件子作品各自的，同 -gun-24 的慣例）：x ＝ 砲的寬（沿船長；軸在 AX 那一格的格心 ⇒ 左右對稱）、y ＝ 砲身方向（砲口 +y）、
z 上，z 0 ＝ 甲板面上第一層。

尺寸：
- 32 磅 carronade：⚠ 推算。砲身約 7 倍口徑（6.4" ⇒ 約 45" ≈ 1.15 m）；整組（slide＋skid）照 Chapelle《The American Sailing Navy》p.516 的
  42 磅（約 112"×50"×29"，模型商引）× (32/42)^(1/3) ≈ 0.91 ⇒ 約 2.6 × 1.15 × 0.7 m。沒有耳軸：砲身底下一個 loop 用螺栓掛在 slide 上；
  slide 前端用 fighting bolt 樞接在砲門下檻、後端兩個小輪在甲板上橫移（瞄準）。後膛半球形；cascabel 後面一支升降螺桿。
- 18 磅長砲：⚠ 推算。9 ft（2.74 m）；外徑照 24 磅那門（-gun-24 plan.guns.gun.note）按口徑比例縮（5.3"／5.8"）；truck carriage 同 24 磅的比例。

輸出：masks/guns2/carronade32.vox.txt、masks/guns2/long18.vox.txt（stampvox 清單，at 0,0,0）、rig_points_guns2.json（固定點）。
"""
import json, math, os

HERE = os.path.dirname(os.path.abspath(__file__))
BLACK, CARR, IRON, QUOIN, WOOD2 = 36, 132, 36, 136, 104


class Part:
    def __init__(s, size):
        s.W, s.L, s.H = size
        s.cells = {}
        s.points = {}

    def put(s, x, y, z, c, over=False):
        if not (0 <= x < s.W and 0 <= y < s.L and 0 <= z < s.H):
            raise ValueError(('框外', x, y, z))
        if (x, y, z) in s.cells and not over:
            return
        s.cells[(x, y, z)] = c

    def box(s, x0, x1, y0, y1, z0, z1, c, over=False):
        for x in range(x0, x1 + 1):
            for y in range(y0, y1 + 1):
                for z in range(z0, z1 + 1):
                    s.put(x, y, z, c, over)

    def tube(s, AX, AZ, y0, prof, c, bore_r=0.0, bore_depth=0.0, over=False):
        """沿 y 的旋轉體：prof ＝ [(s, r), …]（s ＝ 從 y0 起算的連續座標，分段線性）；格心落在半徑內就放。"""
        smax = prof[-1][0]
        for y in range(s.L):
            t = y + 0.5 - y0
            if not (0 <= t < smax):
                continue
            r = None
            for (a, ra), (b, rb) in zip(prof, prof[1:]):
                if a <= t < b:
                    r = ra + (rb - ra) * (t - a) / (b - a) if b > a else rb
                    break
            if r is None:
                continue
            R = int(math.ceil(r)) + 1
            for dx in range(-R, R + 1):
                for dz in range(-R, R + 1):
                    d = math.hypot(dx, dz)
                    if d <= r + 1e-9:
                        if bore_r > 0 and t > smax - bore_depth and d <= bore_r:
                            continue                     # 砲口：挖空
                        s.put(AX + dx, y, AZ + dz, c, over)

    def wheel(s, cx, cy, cz, r, axis, thick, c):
        """輪子：axis ＝ 'x'（輪面在 yz、沿 y 滾）或 'y'（輪面在 xz、沿 x 滾）；中心是連續座標。"""
        for x in range(s.W):
            for y in range(s.L):
                for z in range(s.H):
                    px, py, pz = x + 0.5, y + 0.5, z + 0.5
                    if axis == 'x':
                        if abs(px - cx) <= thick / 2 and math.hypot(py - cy, pz - cz) <= r:
                            s.put(x, y, z, c, True)
                    else:
                        if abs(py - cy) <= thick / 2 and math.hypot(px - cx, pz - cz) <= r:
                            s.put(x, y, z, c, True)

    def asym(s, AX):
        return sum(1 for (x, y, z), c in s.cells.items() if s.cells.get((2 * AX - x, y, z)) != c)

    def write(s, path, title):
        os.makedirs(os.path.dirname(path), exist_ok=True)
        with open(path, 'w', encoding='utf-8', newline='\n') as f:
            f.write('# ' + title + '（draft_guns2.py）x,y,z,color —— at 0,0,0\n')
            for (x, y, z), c in sorted(s.cells.items()):
                f.write(f'{x},{y},{z},{c}\n')


def carronade():
    """32 磅 carronade ＋ slide ＋ skid（0.05 m／格）。框 15 × 54 × 26。砲推到 skid 前端（run out）：砲口伸出 skid 前端 ⇒ 伸出砲門。"""
    P = Part((15, 54, 26))
    AX, AZ = 7, 19                     # 軸：格心 (7.5, *, 19.5) ⇒ 離甲板 0.975 m
    # ── skid（下層滑軌，2.0 m）：兩根側軌＋前後橫檔；前端坐在下檻前的樞軸墊上（fighting bolt），後端兩個小輪（沿船長橫移）──
    Y0, Y1 = 2, 41
    P.box(0, 2, Y0, Y1, 5, 8, CARR)    # 側軌（3 寬、4 高）
    P.box(12, 14, Y0, Y1, 5, 8, CARR)
    P.box(3, 11, Y0, Y0 + 2, 5, 8, CARR)          # 後橫檔
    P.box(3, 11, Y1 - 2, Y1, 5, 8, CARR)          # 前橫檔
    P.box(4, 10, Y1 - 6, Y1, 0, 4, WOOD2)         # 前端樞軸墊（fighting bolt 從這裡往下）
    P.box(7, 7, Y1 - 4, Y1 - 3, 5, 8, IRON, True) # fighting bolt 的頭
    for xc in (1.5, 13.5):                        # 後端小輪：輪面在 xz、沿 x 滾（橫移）
        P.wheel(xc, Y0 + 3.0, 2.5, 2.5, 'y', 2.0, BLACK)
    P.box(0, 14, Y0 + 2, Y0 + 3, 2, 2, IRON)      # 小輪的軸
    # ── slide（上層，坐在 skid 上、整組後座時往後滑，1.0 m；推到前端）──
    S0, S1 = 21, 40
    P.box(3, 11, S0, S1, 9, 12, CARR)
    P.box(3, 4, 29, 36, 13, 15, CARR)             # 兩片 lug cheek（夾住砲身底下的 loop）
    P.box(10, 11, 29, 36, 13, 15, CARR)
    P.box(3, 11, 32, 33, 14, 14, IRON, True)      # loop 的螺栓（沿 x 穿過）
    P.box(6, 8, S0 - 5, S0 - 1, 9, 11, CARR)      # 後面伸出去托升降螺桿的那一截
    # ── 砲身（1.15 m；後膛半球、往前收、砲口外翻）──
    yb = 25                                       # 後膛最後面 ⇒ 砲口 y 48（伸出 skid 前端 7 格 ≈ 0.35 m）
    prof = [(0, 0.8), (1.0, 2.6), (2.0, 3.5), (3.5, 4.3), (4.6, 4.6), (9.0, 4.6), (9.0, 4.9), (10.0, 4.9), (10.0, 4.4),
            (19.0, 3.6), (19.5, 3.3), (21.0, 3.3), (21.0, 3.9), (23.0, 3.9)]
    P.tube(AX, AZ, yb, prof, BLACK, bore_r=1.7, bore_depth=7)
    P.box(6, 8, 31, 34, 14, 15, BLACK)            # loop（砲身底下）
    P.tube(AX, AZ, yb - 2, [(0, 1.2), (2.0, 1.2)], BLACK)      # cascabel 頸
    P.tube(AX, AZ, yb - 4, [(0, 1.3), (0.5, 1.8), (1.5, 1.8), (2.0, 1.3)], BLACK)   # cascabel 鈕（圓）
    P.box(7, 7, yb - 3, yb - 3, AZ - 7, AZ - 2, IRON)          # 升降螺桿（鈕 → 下面那一截）
    P.box(7, 7, yb + 21, yb + 22, AZ + 4, AZ + 4, BLACK)       # 砲口上的準星
    P.points = {'muzzle': (AX, yb + 22, AZ), 'cascabel': (AX, yb - 4, AZ), 'pivot': (AX, Y1 - 3, 4),
                'eye-aft': (0, Y1 - 1, 7), 'eye-fwd': (14, Y1 - 1, 7)}
    return P, AX


def long18():
    """18 磅長砲＋truck carriage（0.05 m／格）。框 27 × 66 × 28。"""
    P = Part((27, 66, 28))
    AX, AZ = 13, 21                               # 軸離甲板 1.075 m
    yb = 7                                        # base ring 的後面
    # 外徑（格，0.05 m）：base ring 9.2 ⇒ r 4.6；第一段 reinforce r 4.4；耳軸處 r 3.8；chase 收到 r 2.9；砲口頸 r 2.7、swell r 3.4（照 24 磅 × 5.3/5.8）
    prof = [(0, 4.6), (2.0, 4.6), (2.0, 4.4), (19.0, 4.2), (19.0, 3.9), (30.0, 3.7), (30.0, 3.2), (48.0, 2.9), (48.0, 2.7),
            (50.5, 2.7), (50.5, 3.4), (53.5, 3.4), (53.5, 3.1), (55.0, 3.1)]
    P.tube(AX, AZ, yb, prof, BLACK, bore_r=1.4, bore_depth=8)
    P.tube(AX, AZ, yb - 2, [(0, 1.4), (2.0, 1.4)], BLACK)       # cascabel 頸
    P.tube(AX, AZ, yb - 5, [(0, 2.2), (3.0, 2.2)], BLACK)       # cascabel 鈕
    P.box(AX, AX, yb - 5, yb - 3, AZ + 3, AZ + 3, BLACK)        # 鈕上的環
    TY = yb + 23                                  # 耳軸（base ring 前 23 格 ≈ 3/7）
    # ── truck carriage（1.55 m 長、1.35 m 寬）──
    YF, LEN = 38, 31
    YR = YF - LEN + 1
    steps = [(0, 21), (11, 18), (17, 16), (23, 13)]               # cheek 頂（從前往後數 back 格）
    for k in (7, 8, 9):                                          # cheek 3 格厚
        for sg in (-1, 1):
            x = AX + sg * k
            for y in range(YR, YF + 1):
                back = YF - y
                top = [h for b0, h in steps if back >= b0][-1]
                bot = 10 if 9 <= back <= 21 else 8               # 兩軸之間底下拱起
                for z in range(bot, top + 1):
                    P.put(x, y, z, CARR)
            for y in (TY - 1, TY, TY + 1):                       # cap square
                P.put(x, y, AZ + 2, IRON, True)
    for k in range(-9, 10):                                      # 耳軸（沿 x 穿過 cheek）
        for dz in (-1, 0, 1):
            P.put(AX + k, TY, AZ + dz, BLACK, True)
            P.put(AX + k, TY + (1 if dz == 0 else 0), AZ, BLACK, True)
    for (ya, r) in ((YF - 5, 4.6), (YR + 4, 4.0)):               # 輪軸＋輪子（前 18"、後 16"）
        P.box(AX - 10, AX + 10, ya, ya + 1, 4, 5, CARR)
        for sg in (-1, 1):
            P.wheel(AX + sg * 11 + 0.5, ya + 1.0, r, r, 'x', 2.0, BLACK)
            P.box(AX + sg * 13, AX + sg * 13, ya, ya + 1, 5, 5, IRON, True)
    P.box(AX - 6, AX + 6, YR, YR + 15, 8, 8, CARR)               # 床板
    P.box(AX - 6, AX + 6, YR + 2, YR + 11, 9, AZ - 5, QUOIN)     # quoin（墊高後膛）
    P.box(AX - 6, AX + 6, YF - 2, YF, 8, 13, CARR)               # 前 transom
    P.points = {'muzzle': (AX, yb + 54, AZ), 'cascabel': (AX, yb - 5, AZ), 'train': (AX, YR, 8),
                'eye-aft': (AX - 10, YF - 16, 14), 'eye-fwd': (AX + 10, YF - 16, 14)}
    return P, AX


def main():
    out = {}
    for name, fn, title in (('carronade32', carronade, '憲法號 32 磅 carronade（slide carriage）'), ('long18', long18, '憲法號 18 磅長砲（chase gun）')):
        P, AX = fn()
        P.write(os.path.join(HERE, 'masks', 'guns2', name + '.vox.txt'), title)
        cnt = {}
        for c in P.cells.values():
            cnt[c] = cnt.get(c, 0) + 1
        out[name] = {'size': [P.W, P.L, P.H], 'voxels': len(P.cells), 'colors': cnt, 'asym': P.asym(AX), 'points': {k: list(v) for k, v in P.points.items()}}
        print(name, len(P.cells), cnt, 'asym', P.asym(AX))
    with open(os.path.join(HERE, 'rig_points_guns2.json'), 'w', encoding='utf-8') as f:
        json.dump(out, f, ensure_ascii=False, indent=1)


if __name__ == '__main__':
    main()
