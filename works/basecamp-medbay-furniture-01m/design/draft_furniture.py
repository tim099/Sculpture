# 醫療艙家具組（TASK-0569；Tim 2026-10-15「TASK-0569 全包 GO」）
#   三件子作品（0.05 m／格，放上船 scale 0.5）＋ 固定點 ＋ 放進目錄作品（本作品，0.1 m）的模型擺法 ⇒
#   masks/<件>.vox.txt（子作品座標）、furniture_placement.json、verify_furniture.json
# 用法：python -I draft_furniture.py <design 資料夾>
# 外框：bed、table 照遊戲設定檔 Blockside/src/config/game.json `furniture`（0.1 m 格：19×8×6、18×8×8）；medkit 照實物（RMG TOA0127）7×5×5 格 0.05 m（設定檔是 5×4×4）——
#   遊戲照它算佔地（0.5 m 一格的俯視格子），模型外框 ⇒ 貼齊它（×2 ＝ 0.05 m 格）。尺寸出處見 notes（查得到的照史料，查不到的照一般比例並註明）。
# meta（放上船時寫在模型上）：kind=furniture、item=<設定檔的代號>（36_rooms.js shipRooms 用的就是這兩個鍵）。
# 固定點（TASK-0568「崗位物件」：位子從模型上的固定點讀）：
#   bed   lie（躺的位子：毯子面中間）、head（枕頭：頭的那一端）
#         ⚠ 史實：那個年代軍艦的病人睡吊在樑上的帆布 cot（EB 1810「COTT」：約 5 ft 長、2–3 ft 寬，而且寫的是軍官用），沒有立地的病床 ⇒
#         這張照遊戲外框（1.9×0.8×0.6 m）與一般比例，是遊戲的抽象（甲板格子上要放得下、會被打壞）。
#   table lie（檯面中間）、work-1／work-2（船醫、助手站的位子：檯子兩側長邊外的地板格，z 0 ＝ 腳踩的那一層）
#   medkit 沒有位子。
# 顏色（RGB332）：照遊戲佔位方塊的材質色挑最近的（36_rooms.js FURN_MATS）——木 104、枕頭 218；帆布 182（v1 用 214 渲染偏粉紅）；
#   其他：毯子 109（灰褐）、tarpaulin 109、黃銅 212、鐵 146、繩 172、桃花心木 132。⛔ 藥箱不畫紅十字（1864 年以後的符號，這個年代沒有）。
import sys, os, json

WOOD, CANVAS, PILLOW, BLANKET, BRASS = 104, 182, 218, 109, 212         # v2 改色：v1 帆布 214 渲染偏粉紅、毯子 74 太藍 ⇒ 帆布 182（米灰）、毯子 109（灰褐羊毛）
TARP = 109                                                          # 手術台頂那層是 tarpaulin（上了焦油的帆布）⇒ 深色
DARK, IRON, ROPE, MAHOGANY = 36, 146, 172, 132                     # 箱蓋縫、鐵件、繩、桃花心木（#922400）


def box(c, x0, x1, y0, y1, z0, z1, col, over=True):
    for x in range(x0, x1 + 1):
        for y in range(y0, y1 + 1):
            for z in range(z0, z1 + 1):
                if over or (x, y, z) not in c:
                    c[(x, y, z)] = col


def bed():
    """38×16×12（1.9×0.8×0.6 m）。頭在 +x。"""
    c = {}
    for x0 in (0, 36):
        for y0 in (0, 14):
            box(c, x0, x0 + 1, y0, y0 + 1, 0, 7, WOOD)                 # 四腳
    box(c, 0, 37, 0, 0, 6, 7, WOOD); box(c, 0, 37, 15, 15, 6, 7, WOOD)   # 側框
    box(c, 0, 37, 0, 15, 8, 8, WOOD)                                  # 床板
    box(c, 1, 36, 1, 14, 9, 10, CANVAS)                               # 帆布床墊
    box(c, 2, 27, 1, 14, 11, 11, BLANKET)                             # 毯子（蓋到胸口）
    box(c, 30, 35, 3, 12, 11, 11, PILLOW)                             # 枕頭
    box(c, 37, 37, 0, 15, 0, 11, WOOD)                                # 床頭板（到外框頂）
    box(c, 0, 0, 0, 15, 0, 9, WOOD)                                   # 床尾板（矮一點）
    pts = {'lie': (18, 7, 11), 'head': (33, 7, 11)}
    return c, pts, (38, 16, 12)


TABLE_Y0 = 8                                                          # 檯子在作品裡往 +y 讓 8 格，兩側站人的點才在作品範圍內


def table():
    """36×16×16（1.8×0.8×0.8 m，外框照遊戲設定檔）。作品 36×32×16，檯子在 y 8–23。
    v2：海戰時的手術台 ＝ 幾個 midshipman 的海員箱綁在一起、蓋帆布（USNI Proceedings 1935 轉述 —— 只讀到搜尋摘要，二手）。
    ⇒ 四個箱子 2×2（每個 18×8×14 格 ＝ 0.9×0.4×0.7 m；⚠ 照一般比例：查到的箱子是 19 世紀末 RMG 的 1.04×0.71×0.61 m、
    摘要裡的 18 世紀將官箱 0.98×0.47×0.41 m，都不是本尊）；頂上帆布 1 格、四邊垂下 2 格；兩道繩綁（長邊方向）。"""
    c, y0 = {}, TABLE_Y0
    for i, xa in enumerate((0, 18)):
        for j, ya in enumerate((0, 8)):
            box(c, xa, xa + 17, y0 + ya, y0 + ya + 7, 0, 13, WOOD)    # 箱身（deal，漆深色）
            box(c, xa, xa + 17, y0 + ya, y0 + ya + 7, 13, 13, DARK)   # 箱蓋那一圈的縫
            for x in (xa, xa + 17):                                   # 鐵包角（兩端四條豎邊）
                for y in (y0 + ya, y0 + ya + 7):
                    box(c, x, x, y, y, 0, 12, IRON)
            for x in (xa + 4, xa + 13):                               # 兩道鐵箍
                box(c, x, x, y0 + ya, y0 + ya + 7, 0, 12, IRON)
    box(c, 0, 35, y0, y0 + 15, 14, 14, TARP)                           # tarpaulin 頂
    box(c, 0, 35, y0, y0, 11, 13, TARP); box(c, 0, 35, y0 + 15, y0 + 15, 11, 13, TARP)   # 長邊垂下
    box(c, 0, 0, y0, y0 + 15, 11, 13, TARP); box(c, 35, 35, y0, y0 + 15, 11, 13, TARP)   # 短邊垂下
    box(c, 2, 33, y0 + 2, y0 + 13, 15, 15, CANVAS)                     # 摺起來墊在上面的一層（人躺的地方）
    for y in (y0 + 3, y0 + 12):
        box(c, 0, 35, y, y, 15, 15, ROPE)                              # 繩：上面兩道（沿長邊）
        box(c, 0, 0, y, y, 0, 14, ROPE); box(c, 35, 35, y, y, 0, 14, ROPE)   # 繞到兩頭往下
    pts = {'lie': (18, y0 + 7, 15), 'work-1': (18, y0 - 4, 0), 'work-2': (18, y0 + 19, 0)}
    return c, pts, (36, 32, 16)


def medkit():
    """7×5×5（0.35×0.25×0.25 m）。照 RMG TOA0127（19 世紀初、據稱來自特拉法加時納爾遜艦隊的船醫）：
    240 × 350 × 230 mm、桃花心木、黃銅包角、drop handles、黃銅蓋板 ⇒ 0.05 m 格取整 7×5×5（多 1–2 cm）。
    ⚠ 比遊戲設定檔的 medkit 5×4×4（0.1 m 格 ＝ 0.5×0.4×0.4 m）小 —— 設定檔要不要改是 ame 的。
    v1 是照設定檔的 10×8×8、紅蓋（遊戲佔位的顏色）⇒ v2 照實物。"""
    c = {}
    box(c, 0, 6, 0, 4, 0, 3, MAHOGANY)                                 # 箱身
    box(c, 0, 6, 0, 4, 4, 4, MAHOGANY)                                 # 蓋
    box(c, 2, 4, 1, 3, 4, 4, BRASS)                                   # 黃銅蓋板
    for x in (0, 6):
        for y in (0, 4):
            box(c, x, x, y, y, 0, 4, BRASS)                           # 包角
    box(c, 0, 0, 2, 2, 3, 3, BRASS); box(c, 6, 6, 2, 2, 3, 3, BRASS)   # 兩頭提把
    return c, {}, (7, 5, 5)


ITEMS = {'bed': ('病床', bed), 'table': ('手術台', table), 'medkit': ('藥箱', medkit)}
# 目錄作品（0.1 m）：三件並排、scale 0.5、pivot 0,0,0；站在一塊 Z 0 的木地板上（⚠ 沒有任何格的作品匯不出 .vxk ——
#   v1 目錄只有模型，export format=vxk 回「觀測區域內沒有任何 voxel」⇒ 鋪地板、模型抬到 Z 1）
CATALOG_AT = {'bed': [2, 2, 1], 'table': [24, 0, 1], 'medkit': [46, 4, 1]}
CATALOG_FLOOR = dict(x=(0, 63), y=(0, 23), z=0, color=136)


def main(design):
    out = os.path.join(design, 'masks')
    os.makedirs(out, exist_ok=True)
    place, ver = {}, {}
    for it, (name, fn) in ITEMS.items():
        c, pts, size = fn()
        xs, ys, zs = zip(*c)
        bb = [min(xs), min(ys), min(zs), max(xs), max(ys), max(zs)]
        for p in pts.values():
            assert all(0 <= p[i] < size[i] for i in range(3)), ('固定點在作品外', it, p)
        with open(os.path.join(out, it + '.vox.txt'), 'w', encoding='utf-8', newline='\n') as f:
            f.write('# %s（%s）：%d 格，子作品座標（0.05 m／格）\n' % (name, it, len(c)))
            for (x, y, z), col in sorted(c.items()):
                f.write('%d,%d,%d,%d\n' % (x, y, z, col))
        work = 'basecamp-medbay-furniture-01m-' + it
        place[it] = dict(work=work, title='醫療艙家具・%s（0.05 m／格；TASK-0569）' % name, size=list(size), cells=len(c), anchors={k: list(v) for k, v in pts.items()},
                         meta={'kind': 'furniture', 'item': it}, catalog_at=CATALOG_AT[it], scale=0.5)
        colors = {}
        for v in c.values():
            colors[str(v)] = colors.get(str(v), 0) + 1
        dims = [bb[3] - bb[0] + 1, bb[4] - bb[1] + 1, bb[5] - bb[2] + 1]
        ver[it] = dict(cells=len(c), bbox=bb, bbox_dims_005m=dims, bbox_dims_01m=[d / 2 for d in dims], colors=colors)
        print(it, len(c), 'bbox', dims, '⇒ 0.1 m', [d / 2 for d in dims], pts)
    F = CATALOG_FLOOR
    floor = [(x, y, F['z'], F['color']) for x in range(F['x'][0], F['x'][1] + 1) for y in range(F['y'][0], F['y'][1] + 1)]
    with open(os.path.join(out, 'catalog_floor.vox.txt'), 'w', encoding='utf-8', newline='\n') as f:
        f.write('# 目錄作品的地板（0.1 m／格）：%d 格\n' % len(floor))
        for r in floor:
            f.write('%d,%d,%d,%d\n' % r)
    place['_catalog_floor'] = dict(cells=len(floor))
    json.dump(place, open(os.path.join(design, 'furniture_placement.json'), 'w', encoding='utf-8'), ensure_ascii=False, indent=1)
    json.dump(ver, open(os.path.join(design, 'verify_furniture.json'), 'w', encoding='utf-8'), ensure_ascii=False, indent=1)


if __name__ == '__main__':
    sys.stdout.reconfigure(encoding='utf-8')
    main(sys.argv[1])
