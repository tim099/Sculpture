# 新圖紙 S：藥庫的兩件補給元件（0.05 m／格；模型 scale 0.5）—— 遊戲當火藥桶用（模型 meta kind=powder），取用點的三個桶會輪流擺這兩種樣子（Blockside 23_powder.js makeStations）。
#   Tim 2026-10-18：「彈藥箱可以有不同外觀(但實際上都能補彈)」。
# 1. amphora  希臘火陶罐：平底、圓肩、細頸、兩個把手，赭陶色，肩上一道深色帶，瀝青封口（⚠ 樣子是設計：史料只說希臘火裝在罐子裡運）。
# 2. boltbox  弩箭箱：木箱（深色包邊）、上面露出一排箭桿與鐵箭頭。
#   座標：x、y 水平（箱子沿 x 長），z 0 ＝ 底面；固定點 pivot ＝ 底面正中（擺法 at ＝ 落點）。
# 用法：python -I -X utf8 -B draft_stores.py ⇒ lists/st_<名>.txt、verify_stores.json
import os, sys, json, math
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import dro

D = dro.D
CLAY, CLAY_D, PITCH, WOOD, WOOD_D, IRON = 200, 164, 36, 136, 100, 73   # rgb332：赭陶（r6 g2 b0）、深陶（r5 g1 b0）、瀝青、木、深木、鐵


def amphora():
    S = [9, 9, 13]; cx = cy = 4.5; cells = {}
    prof = {0: 2.2, 1: 2.8, 2: 3.3, 3: 3.6, 4: 3.8, 5: 3.9, 6: 3.9, 7: 3.8, 8: 3.4, 9: 2.6, 10: 1.6, 11: 1.3, 12: 1.7}
    for z, r in prof.items():
        for x in range(S[0]):
            for y in range(S[1]):
                d = math.hypot(x + 0.5 - cx, y + 0.5 - cy)
                if d <= r:
                    c = CLAY_D if z == 7 else PITCH if z == 12 and d <= 1.0 else CLAY
                    cells[(x, y, z)] = c
    for sx in (0, 8):                                   # 把手：肩到頸的一個小環（x 兩側）
        for z in (8, 9, 10):
            cells[(sx, 4, z)] = CLAY
        cells[(1 if sx == 0 else 7, 4, 11)] = CLAY
    return S, cells


def boltbox():
    S = [11, 7, 8]; cells = {}
    for x in range(S[0]):
        for y in range(S[1]):
            for z in range(5):
                edge = x in (0, S[0] - 1) or y in (0, S[1] - 1) or z in (0, 4)
                n = (x in (0, S[0] - 1)) + (y in (0, S[1] - 1)) + (z in (0, 4))
                if edge:
                    cells[(x, y, z)] = WOOD_D if n >= 2 else WOOD
    for y in (2, 4):                                    # 一排箭：從箱口斜斜露出來（沿 x），鐵頭在 x 大的那一端
        for x in range(1, S[0] - 1):
            z = 5 + (1 if x > 6 else 0)
            cells[(x, y, z)] = IRON if x >= S[0] - 2 else WOOD
    return S, cells


def main():
    R = {}
    for name, fn in (('amphora', amphora), ('boltbox', boltbox)):
        S, cells = fn()
        path = os.path.join(D, 'lists', 'st_%s.txt' % name)
        n = dro.write_list(path, cells, '持火號 補給元件 %s（draft_stores.py；0.05 m）' % name)
        R[name] = {'size': S, 'cells': n, 'file': 'lists/st_%s.txt' % name, 'anchors': {'pivot': [S[0] // 2, S[1] // 2, 0]}}
    json.dump(R, open(os.path.join(D, 'verify_stores.json'), 'w', encoding='utf-8', newline='\n'), ensure_ascii=False, indent=1)
    print(json.dumps(R, ensure_ascii=False))


if __name__ == '__main__':
    main()
