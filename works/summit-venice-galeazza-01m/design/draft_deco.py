"""威尼斯 galeazza（TASK-1302）步驟 6：窗的玻璃＋可隱藏的金飾（Ship_Fittings §9.9、Ship_Materials「窗的玻璃」）。

- 玻璃（關聯 meta material=glass）：艉樓艉封板與兩舷側窗的窗洞裡、最外那一層 1 格厚，後面是艙裡的空氣；
  ⛔ 第 5 扇側窗（x 128）是 30 磅 cannone 的砲門，不裝玻璃。
- 金飾（外部模型 meta deco=1，可隱藏）：
  ① 艉樓拱頂艙後壁（x 64–65，面向船尾）外面的聖馬可有翼獅浮雕：紅底圓盾（x 63）＋金色獅（x 62）。
     Grevenbroeck 約 1750 彩圖鍍金艉樓、紅金旗；聖馬可獅是威尼斯國徽（Coronelli 版畫左上角的盾）。
  ② 圓形艏樓正面（兩門 50 磅砲門之間）的金色卷框徽飾（紅心＋金框），MSN 模型艏樓正面有雕飾。
- 船名：不做。17 世紀威尼斯 galeazza 以指揮官姓氏稱呼（Lo Basso 2003 p.130 前後：Morosini、Corner、Pisani、Basadonna），沒有船名板可依。
輸出 masks/deco/glass.vox.txt、masks/deco/gilt.vox.txt；只放現況（船殼＋甲板）沒有的格。
"""
import hashlib
import json
import math
from pathlib import Path
import sys

import numpy as np

D = Path(__file__).resolve().parent
sys.path.insert(0, str(D))
from lines import Lines, load_plan

GLASS, GOLD, GOLD2, RED = 155, 212, 208, 160
TRANSOM_GLASS = False   # 步驟 9：艉封板兩扇窗是 30 磅 colubrina 的艉砲門（de Zuanne 艉 2 colubrina da 30），不裝玻璃


def lion(w=29, h=25):
    """聖馬可有翼獅（側面、向右、前掌按著翻開的書、頭上光環）：回傳 {(u, v)}，u 0..w−1 往右、v 0..h−1 往上。"""
    pts = set()

    def ell(cu, cv, ru, rv):
        for u in range(w):
            for v in range(h):
                if ((u - cu) / ru) ** 2 + ((v - cv) / rv) ** 2 <= 1.0:
                    pts.add((u, v))

    ell(13, 8, 7.5, 3.6)                 # 身體
    ell(21, 12, 3.4, 3.4)                # 頭＋鬃
    ell(24, 11, 1.8, 1.2)                # 口鼻
    for u, v in ((7, 0), (7, 1), (7, 2), (7, 3), (9, 1), (9, 2), (9, 3), (17, 0), (17, 1), (17, 2), (17, 3), (19, 1), (19, 2), (19, 3)):
        pts.add((u, v))                  # 四條腿
    for k in range(9):                   # 尾巴：從臀往後上捲
        pts.add((5 - k // 2, 8 + k // 3))
    pts |= {(1, 11), (1, 12), (2, 12)}
    for k in range(11):                  # 翅膀：從背往後上斜張開的扇形（前緣一條、往後四排羽毛漸長）
        for j in range(2 + k // 2):
            pts.add((16 - k + j, 11 + k))
    return pts


def book():
    return {(u, v) for u in range(22, 28) for v in range(2, 6)}


def halo(cu=21, cv=12, r=5.4):
    return {(u, v) for u in range(29) for v in range(25) if abs(math.hypot(u - cu, v - cv) - r) < 0.6 and v > cv}


def main():
    plan = load_plan(D)
    L = Lines(plan)
    YC = plan['space']['yc']
    NX, NY, NZ = plan['space']['hull']
    lay = {k: v['v'] for k, v in plan['layout'].items()}
    occ = np.zeros((NX, NY, NZ), bool)
    for p in ['masks/hull/hull_01.vox.txt', 'masks/upper/upper_01.vox.txt'] + sorted(str(p) for p in (D / 'masks/decks').glob('*.vox.txt')):
        a = np.loadtxt(D / p, delimiter=',', dtype=np.int32)
        occ[a[:, 0], a[:, 1], a[:, 2]] = True
    sc, bc = lay['stern_castle'], lay['bow_castle']
    hb = lambda x, z: float(L.hb(x + 0.5, z + 0.5))
    sx0 = int(next(x for x in range(int(L.x_sh), NX) if hb(x, L.z_side) >= 2))

    glass = {}
    # 艉封板窗：x sx0（最外一層），窗洞照 draft_upper（|dy−10|≤3、|dy−24|≤3、z 40..46），只在艉封板寬度裡
    for y in range(NY):
        dy = abs(y - YC)
        if not (abs(dy - 10) <= 3 or abs(dy - 24) <= 3):
            continue
        for z in range(40, 47):
            if TRANSOM_GLASS and dy <= hb(sx0, L.z_side) and not occ[sx0, y, z] and not occ[sx0 + 2, y, z]:
                glass[(sx0, y, z)] = GLASS
    # 側窗：x ＝ sx0+14 起每 15 格、|x−xw| ≤ 2、z 40..46；玻璃放在牆最外那層（dy ＝ HB），後面那層（HB−1）是洞
    gunport_x = sx0 + 74                # 第 5 扇（x 128）：30 磅 cannone 的砲門，跟 draft_upper 的窗序同一把尺
    for xw in range(sx0 + 14, sc['x_front'] - 8, 15):
        if xw == gunport_x:
            continue
        for x in range(xw - 2, xw + 3):
            HB = int(math.floor(hb(x, L.z_side)))
            for side in (1, -1):
                y = YC + side * HB
                for z in range(40, 47):
                    if z > L.sheer(x + 0.5) and not occ[x, y, z]:
                        glass[(x, y, z)] = GLASS

    gilt = {}
    # ① 有翼獅：艙後壁 x 64，外面 x 63 紅盾、x 62 金獅；面在 y–z 平面，從船尾看（−x 往 +x 看）獅頭朝 +y
    cab = sc['cabin']
    xb = cab['x0']
    zc, R = sc['deck_z'] + 13, 13.5
    for y in range(YC - 14, YC + 15):
        for z in range(zc - 14, zc + 15):
            if math.hypot(y - YC, z - zc) <= R and z > sc['deck_z']:
                gilt[(xb - 1, y, z)] = RED
    for u, v in lion() | book() | halo():
        y, z = YC - 14 + u, zc - 12 + v
        gilt[(xb - 2, y, z)] = GOLD if (u, v) not in book() else GOLD2
    # ② 艏樓正面徽飾：圓心 (cx, YC)、半徑 r 的最外一格再往外 1 格；|dy| ≤ 6、z 44..50（兩層砲門之間的金帶下）
    cx, r = bc['cx'], bc['r']
    for y in range(YC - 6, YC + 7):
        dyy = y - YC
        xo = int(math.floor(cx + 0.5 + math.sqrt(max(0.0, (r + 0.5) ** 2 - dyy * dyy)) - 0.5))
        while occ[xo + 1, y, 46]:
            xo += 1
        for z in range(44, 50):
            e = ((dyy) / 6.5) ** 2 + ((z - 46.5) / 3.6) ** 2
            if e <= 1.0:
                gilt[(xo + 1, y, z)] = RED if e < 0.35 else GOLD

    clash = [k for k in list(glass) + list(gilt) if occ[k]]
    assert not clash, clash[:5]
    out = D / 'masks/deco'
    out.mkdir(parents=True, exist_ok=True)
    stats = {'glass': len(glass), 'gilt': len(gilt),
             'glass_mirror_diff': sum(1 for (x, y, z) in glass if (x, 2 * YC - y, z) not in glass)}
    for name, cells in (('glass', glass), ('gilt', gilt)):
        body = ''.join(f'{x},{y},{z},{c}\n' for (x, y, z), c in sorted(cells.items())).encode('ascii')
        (out / f'{name}.vox.txt').write_bytes(body)
        stats[name + '_sha16'] = hashlib.sha256(body).hexdigest()[:16]
    (D / 'verify_deco.json').write_text(json.dumps(stats, ensure_ascii=False, indent=1) + '\n', encoding='utf-8')
    print(json.dumps(stats, ensure_ascii=False))


if __name__ == '__main__':
    main()
