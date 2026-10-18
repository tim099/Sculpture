# 新圖紙 05：舷側舵（pēdalion：舵葉＋舵桿 auchēn＋舵柄 oiax；ref §5）—— S 舷一件子作品（整船的框），P 舷用同一件鏡像。
#   舵桿直立穿過 fittings 的舵箱（軸 ＝ 舵箱中心那一條垂直線），舵葉在下、往船尾伸；舵柄在舵桿頂、往船內伸過舷牆。
#   尺寸 design（ref 沒有）：舵桿 4.2 m、舵葉 2.0 × 0.5 m、舵柄 1.3 m；舵葉下緣 z 2（比艉部船底低一點）。
# 用法：python -I -X utf8 -B draft_steer.py ⇒ lists/rudder.txt、verify_steer.json
import os, sys, json, math
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import dro

D = dro.D
C = dro.C
YC = dro.YC
U = json.load(open(os.path.join(D, 'verify_upper.json'), encoding='utf-8'))
g = U['_geo']['rudder']
AX, AO, ZB = g['x'], g['o'], g['zb']        # 舵軸那一格的 x、離中線、舵橫樑底
AY = YC + AO
cx, cy = AX + 0.5, AY + 0.5                  # 舵軸（連續座標）
cells = {}
Z_BOT, Z_TOP = 2, ZB + 11                    # 舵桿頂在舵箱上面
for z in range(Z_BOT + 14, Z_TOP + 1):       # 舵桿（r 1.3）
    for x in range(AX - 2, AX + 3):
        for y in range(AY - 2, AY + 3):
            if math.hypot(x + 0.5 - cx, y + 0.5 - cy) <= 1.3:
                cells[(x, y, z)] = C['beam']
for z in range(Z_BOT, Z_BOT + 21):           # 舵葉：往船尾（−x）伸，下寬上窄；厚 2 格（y AY, AY+1 → 對稱取 AY-1..AY）
    t = (z - Z_BOT) / 20
    w = int(round(5 - 2 * t))                # 0.5 m → 0.3 m
    for x in range(AX - w, AX + 2):
        for y in (AY - 1, AY, AY + 1) if x >= AX - 1 else (AY,):
            cells[(x, y, z)] = C['beam'] if z > dro.PLAN['waterline_z'] else C['bottom']
for z in range(Z_BOT + 14, Z_BOT + 21):      # 舵桿與舵葉接頭的鐵箍
    for x in range(AX - 2, AX + 3):
        for y in range(AY - 2, AY + 3):
            if (x, y, z) not in cells and math.hypot(x + 0.5 - cx, y + 0.5 - cy) <= 1.6 and z in (Z_BOT + 15, Z_BOT + 19):
                cells[(x, y, z)] = C['iron']
# 舵柄：舵桿頂往船內（−y）伸 13 格、在 z Z_TOP-1
for y in range(AY - 14, AY - 1):
    cells[(AX, y, Z_TOP - 1)] = C['beam']
    if y > AY - 12:
        cells[(AX, y, Z_TOP - 2)] = C['beam'] if (AX, y, Z_TOP - 2) not in cells else cells[(AX, y, Z_TOP - 2)]
# 不能跟舵箱（fittings）、船殼重疊 —— 舵是模型、本來就不跟格子算重疊，但要「退到零碰撞」（模型的格不在實心格裡）
def load(path):
    out = set()
    for ln in open(os.path.join(D, path), encoding='utf-8'):
        if ln[0] == '#':
            continue
        x, y, z, c = map(int, ln.split(','))
        out.add((x, y, z))
    return out
solid = load('lists/hull.txt') | load('lists/fittings.txt') | load('lists/deck_main.txt')
hit = sorted(k for k in cells if k in solid)
n = dro.write_list(os.path.join(D, 'lists', 'rudder.txt'), cells, '持火號 舷側舵 S（整船的框；draft_steer.py）')
hinge = (cx, cy, float(Z_BOT))
an = {'stock-top': (AX, AY, Z_TOP), 'hinge-bot': (AX, AY, Z_BOT), 'tiller-end': (AX, AY - 13, Z_TOP - 1)}
R = {'file': 'lists/rudder.txt', 'cells': n, 'collide_cells': len(hit), 'collide_sample': hit[:10], 'anchors': an,
     'hinge_S': hinge, 'hinge_P': (cx, dro.YM - (cy - dro.YM), float(Z_BOT)), 'pivot': (cx, cy, float(Z_BOT)), 'max_deg': 35}
json.dump(R, open(os.path.join(D, 'verify_steer.json'), 'w', encoding='utf-8'), ensure_ascii=False, indent=1, sort_keys=True)
print(json.dumps({k: R[k] for k in ('cells', 'collide_cells', 'collide_sample', 'hinge_S', 'hinge_P')}, ensure_ascii=False))
