"""
餘燼號 階段十 下層砲甲板的 32 磅長砲（一門；0.05 m／格的子作品，當外部模型 scale 0.5 掛上船）
—— 照憲法號 draft_guns2.py 的 long18（同一個 Part 類別、同一套座標與配色）照口徑放大：
   ⚠ 推算：32 磅長砲口徑 6.4"（18 磅 5.3"）⇒ 外徑 × 約 1.2；砲身 9.5 ft（2.9 m ⇒ 58 格；18 磅 9 ft 55 格）；
   truck carriage 長 1.75 m、寬 1.05 m（18 磅 1.55／0.95）；前輪 r 5.1、後輪 r 4.5；軸離甲板 1.125 m。
座標：x ＝ 砲的寬（沿船長；軸在 AX 那一格的格心 ⇒ 左右對稱）、y ＝ 砲身方向（砲口 +y）、z 0 ＝ 甲板面上第一層。
輸出：masks/guns/long32.vox.txt（stampvox 清單，at 0,0,0）、guns_points.json（固定點與讀數）。
用法：python -I draft_gun32.py <design 資料夾>
"""
import json, os, sys, importlib.util

D = os.path.abspath(sys.argv[1]) if len(sys.argv) > 1 else os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, D)
import draft_profile as DP   # noqa: E402

spec = importlib.util.spec_from_file_location('con_guns2', os.path.join(DP.CON_DESIGN, 'draft_guns2.py'))
G2 = importlib.util.module_from_spec(spec)
spec.loader.exec_module(G2)
Part, BLACK, CARR, IRON, QUOIN = G2.Part, G2.BLACK, G2.CARR, G2.IRON, G2.QUOIN


def long32():
    """32 磅長砲＋truck carriage（0.05 m／格）。框 31 × 74 × 31。"""
    P = Part((31, 74, 31))
    AX, AZ = 15, 22
    yb = 8                                        # base ring 的後面
    # 外徑（格，0.05 m）：base ring r 5.5；第一段 reinforce 5.2→5.0；第二段 4.6→4.4；chase 3.8→3.4；砲口頸 3.2、swell 4.1
    prof = [(0, 5.5), (2.4, 5.5), (2.4, 5.2), (20.0, 5.0), (20.0, 4.6), (32.0, 4.4), (32.0, 3.8), (51.0, 3.4), (51.0, 3.2),
            (53.5, 3.2), (53.5, 4.1), (56.5, 4.1), (56.5, 3.7), (58.0, 3.7)]
    P.tube(AX, AZ, yb, prof, BLACK, bore_r=1.7, bore_depth=9)
    P.tube(AX, AZ, yb - 3, [(0, 1.7), (3.0, 1.7)], BLACK)       # cascabel 頸
    P.tube(AX, AZ, yb - 6, [(0, 2.6), (3.0, 2.6)], BLACK)       # cascabel 鈕
    P.box(AX, AX, yb - 6, yb - 4, AZ + 3, AZ + 3, BLACK)        # 鈕上的環
    TY = yb + 25                                  # 耳軸（base ring 前 25 格 ≈ 3/7）
    YF, LEN = 43, 35
    YR = YF - LEN + 1
    steps = [(0, 22), (12, 19), (19, 17), (26, 14)]
    for k in (8, 9, 10):                                         # cheek 3 格厚
        for sg in (-1, 1):
            x = AX + sg * k
            for y in range(YR, YF + 1):
                back = YF - y
                top = [h for b0, h in steps if back >= b0][-1]
                bot = 11 if 10 <= back <= 24 else 9
                for z in range(bot, top + 1):
                    P.put(x, y, z, CARR)
            for y in (TY - 1, TY, TY + 1):                       # cap square
                P.put(x, y, AZ + 2, IRON, True)
    for k in range(-10, 11):                                     # 耳軸
        for dz in (-1, 0, 1):
            P.put(AX + k, TY, AZ + dz, BLACK, True)
            P.put(AX + k, TY + (1 if dz == 0 else 0), AZ, BLACK, True)
    for (ya, r) in ((YF - 6, 5.1), (YR + 5, 4.5)):               # 輪軸＋輪子
        P.box(AX - 11, AX + 11, ya, ya + 1, 4, 5, CARR)
        for sg in (-1, 1):
            P.wheel(AX + sg * 12 + 0.5, ya + 1.0, r, r, 'x', 2.0, BLACK)
            P.box(AX + sg * 14, AX + sg * 14, ya, ya + 1, 5, 5, IRON, True)
    P.box(AX - 7, AX + 7, YR, YR + 17, 9, 9, CARR)               # 床板
    P.box(AX - 7, AX + 7, YR + 2, YR + 12, 10, AZ - 6, QUOIN)    # quoin
    P.box(AX - 7, AX + 7, YF - 2, YF, 9, 14, CARR)               # 前 transom
    P.points = {'muzzle': (AX, yb + 57, AZ), 'breech': (AX, yb, AZ), 'cascabel': (AX, yb - 6, AZ), 'train': (AX, YR, 9),
                'eye-aft': (AX - 11, YF - 18, 15), 'eye-fwd': (AX + 11, YF - 18, 15)}
    return P, AX


def main():
    sys.stdout.reconfigure(encoding='utf-8')
    P, AX = long32()
    os.makedirs(os.path.join(D, 'masks', 'guns'), exist_ok=True)
    P.write(os.path.join(D, 'masks', 'guns', 'long32.vox.txt'), '餘燼號 32 磅長砲（一門，0.05 m）')
    cnt = {}
    for c in P.cells.values():
        cnt[c] = cnt.get(c, 0) + 1
    # 固定點必須是實心格（muzzle 例外：內膛那一格）
    pts = {k: list(v) for k, v in P.points.items()}
    solid = {k: (tuple(v) in P.cells) for k, v in P.points.items()}
    out = {'long32': {'size': [P.W, P.L, P.H], 'voxels': len(P.cells), 'colors': cnt, 'asym': P.asym(AX), 'points': pts, 'point_on_solid': solid}}
    json.dump(out, open(os.path.join(D, 'guns_points.json'), 'w', encoding='utf-8', newline='\n'), ensure_ascii=False, indent=1)
    print(json.dumps(out, ensure_ascii=False))


if __name__ == '__main__':
    main()
