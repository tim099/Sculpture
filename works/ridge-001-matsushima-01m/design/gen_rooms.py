# 艙房（造船規格 §9.2；照憲法號 draft_rooms.py 的「side」做法）：只產生右舷（y > YC），左舷用 mirror=y 的關聯。
#   每一段：縱向牆在 |y − YC| ＝ WALL（中間留走道：梯子、艙口、煙道都在走道裡），橫向牆每 ~SPAN 格一道，
#   牆 1 格厚、從甲板面到上一層甲板板底下，只填還空著的艙內空氣；每間在縱向牆上開一扇門（0.8 m 寬、2.0 m 高）。
#   每間的框（只框空氣）⇒ 固定點 <房名>.min／.max／.door（子作品＝整船的框、at 0,0,0，所以座標照抄）。
# 用法：python -I -X utf8 -B gen_rooms.py <gen 輸出>   ⇒ <gen 輸出>/part_rooms-<層>.txt、rooms.json
import sys, os, json
import numpy as np

out = sys.argv[1]
own = np.load(os.path.join(out, 'own.npy'))
names = json.load(open(os.path.join(out, 'own_names.json'), encoding='utf-8'))['names']
M = json.load(open(os.path.join(out, 'matsushima_meta.json'), encoding='utf-8'))
NX, NY, NZ = own.shape; YC = M['plan']['YC']; WALK = M['plan']['walk']
solid = own > 0
for nm in ('boilers', 'engine', 'shaft'):
    solid |= (own == names.index(nm) + 1)[:, ::-1, :]
hull = own == names.index('hull') + 1
WHITE = 255
SPAN, DOOR_W, DOOR_H = 45, 8, 20
# 段（設計決定，史料沒有艙內配置圖）：層、x 範圍、用途（只寫進 notes／房間表，遊戲不讀）
SEGS = [                                                                  # 層、x 範圍、縱向牆 |y − YC|（兩頭船窄、梯子都在中線上 ⇒ 走道窄一點）、用途
    ('lower', 70, 250, 18, '後段：糧食、帆布、備品庫'),
    ('lower', 360, 590, 38, '機艙兩舷：煤艙'),
    ('lower', 590, 720, 38, '鍋爐艙兩舷：煤艙'),
    ('lower', 720, 950, 18, '前段：備品庫、水兵的物品庫'),
    ('middle', 40, 252, 18, '後段：司令官、艦長、軍官艙'),
    ('middle', 355, 595, 38, '露砲台到砲列之間：准士官、下士官艙'),
    ('upper', 690, 880, 18, '船首樓底下：病室、藥品庫、備品庫'),
]
UPZ = {'lower': WALK['middle'], 'middle': WALK['upper'], 'upper': WALK['fc']}


def inner_y(x, z0, z1):
    """右舷：從 YC 往外走、第一格船殼之前的 y（每個 z 取最小；那一層外板有開口 ⇒ 不算那一層）。"""
    best = None
    for z in range(z0, z1 + 1):
        ys = np.nonzero(hull[x, YC:, z])[0]
        if not len(ys): continue
        y = YC + int(ys.min()) - 1
        best = y if best is None else min(best, y)
    return best


def top_z(x, y, z0):
    """(x, y) 這一柱從走路格往上第一格實心之前。"""
    col = np.nonzero(solid[x, y, z0:])[0]
    return z0 + int(col.min()) - 1 if len(col) else None


walls = {}
rooms = {}
for deck, xa, xb, WALL, use in SEGS:
    z0 = WALK[deck]
    key = 'rooms-' + deck
    W = walls.setdefault(key, set()); R = rooms.setdefault(key, [])
    n = max(1, round((xb - xa) / SPAN)); xs = [round(xa + (xb - xa) * i / n) for i in range(n + 1)]
    for i in range(n):
        x0, x1 = xs[i] + 1, xs[i + 1] - 1                                # 房間內 x（兩端是橫向牆）
        yo = min(inner_y(x, z0, UPZ[deck] - 1) or YC for x in range(x0 - 1, x1 + 2))
        if yo - (YC + WALL) < 12: continue                               # 太窄（< 1.2 m）不做
        zt = min(top_z(x, y, z0) or z0 for x in range(x0, x1 + 1) for y in range(YC + WALL + 1, yo + 1))
        if zt - z0 < 15: continue                                        # 頭上不夠 1.5 m
        # 牆：兩道橫向（x0−1、x1+1）＋ 縱向（y ＝ YC＋WALL），只填空氣、在船殼裡
        for x in (x0 - 1, x1 + 1):
            yx = inner_y(x, z0, zt) or yo
            for y in range(YC + WALL, yx + 1):
                for z in range(z0, zt + 1):
                    if not solid[x, y, z]: W.add((x, y, z))
        def clear(d):                                                    # 門外（走道那一側）8 格寬、往外 0.8 m 都站得住（遊戲照這個量門）：腳下實心、頭上 1.4 m 空
            return all(solid[x, YC + WALL - j, z0 - 1] and not solid[x, YC + WALL - j, z0:z0 + 14].any() for x in range(d, d + DOOR_W) for j in range(1, 9))
        c0 = (x0 + x1) // 2 - DOOR_W // 2
        cand = [c0 + k * s_ for k in range(0, (x1 - x0) // 2) for s_ in ((1, -1) if k else (1,)) if x0 + 1 <= c0 + k * s_ <= x1 - DOOR_W]
        dx0 = next((d for d in cand if clear(d)), c0)                    # 門外是梯子口 ⇒ 往旁邊挪（中甲板 6 號：lm-mid 的梯子頂）
        for x in range(x0, x1 + 1):
            for z in range(z0, zt + 1):
                if dx0 <= x < dx0 + DOOR_W and z < z0 + DOOR_H: continue   # 門洞
                if not solid[x, YC + WALL, z]: W.add((x, YC + WALL, z))
        box = ((x0, YC + WALL + 1, z0), (x1, yo, zt))
        sub = solid[x0:x1 + 1, YC + WALL + 1:yo + 1, z0:zt + 1]
        R.append({'name': str(len(R) + 1), 'wall': WALL, 'min': list(box[0]), 'max': list(box[1]), 'door': [dx0 + DOOR_W // 2, YC + WALL, z0],
                  'size_m': [round((x1 - x0 + 1) / 10, 1), round((yo - YC - WALL) / 10, 1), round((zt - z0 + 1) / 10, 1)],
                  'solid_in_box': int(sub.sum()), 'use': use})
for key, W in walls.items():
    with open(os.path.join(out, 'part_%s.txt' % key), 'w', encoding='utf-8', newline='\n') as f:
        f.write('# 松島號 %s —— x,y,z,color（框 %d×%d×%d、關聯 at 0,0,0；只有右舷，左舷 mirror=y）\n' % (key, NX, NY, NZ))
        for x, y, z in sorted(W): f.write('%d,%d,%d,%d\n' % (x, y, z, WHITE))
json.dump({'segs': SEGS, 'span': SPAN, 'door': [DOOR_W, DOOR_H], 'rooms': rooms, 'cells': {k: len(v) for k, v in walls.items()}},
          open(os.path.join(out, 'rooms.json'), 'w', encoding='utf-8', newline='\n'), ensure_ascii=False, indent=1)
for key, R in rooms.items():
    print('%s：%d 間、牆 %d 格' % (key, len(R), len(walls[key])))
    for r in R: print('  %s  %s → %s  %s m  實心 %d  %s' % (r['name'], r['min'], r['max'], r['size_m'], r['solid_in_box'], r['use']))
