# 直接出處：gura-pinas-01m/design/draft_galley.py（藍鯊號，TASK-0967）—— 作品 id、persona、尺寸、單號、船名換成康塞普西翁號（TASK-0969）；下面那行是藍鯊號那時寫的出處
# 康塞普西翁號 廚房爐灶（kombuis）—— TASK-0969 補做（Tim 2026-10-26「繼續 go」）
#   現有元件只有光榮號、拿破崙號的鐵製爐灶（1850 年代的 range）⇒ 1666 年的荷蘭船是磚砌的爐（kombuis：鉛盤上砌黃磚、上面鐵板放銅鍋、
#   磚煙囪穿過船艏樓甲板）⇒ 自己做一件 0.05 m 的子作品、掛在上甲板（verdek）子作品裡、scale 0.5。
#   · 模型座標（0.05 m）：x 照船的 x（爐口朝船尾 −x，廚師站那一面）、y 照船的 y、z 往上；pivot (15, 15, 0)
#   · 船艏樓甲板（z 82）在煙囪那一段開 3×3 的洞（甲板-castillo 子作品走差量）
#   輸出：masks/galley/galley.vox.txt（模型座標）、masks/galley/deck_hole.vox.txt（要從甲板-castillo 刻掉的格）、galley_placement.json、verify_galley.json
#   用法：python -I -X utf8 draft_galley.py <design>
import sys, os, json, math, hashlib
import numpy as np

sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), 'tools'))
from wio import export_list

BRICK, BRICK2, MORTAR = 213, 209, 146        # 黃磚（IJsselsteen）兩種、灰漿
LEAD, IRON, SOOT, EMBER, FLAME = 109, 73, 36, 240, 252
COPPER, COPPER_D = 200, 168
SIZE = (30, 30, 60)
PIVOT = (15, 15, 0)
AT = (469.5, 160.5, 62)                      # 爐的中心 x 469.5（船艏樓甲板橫樑 x 464／480 之間放得下煙囪）、中線、腳踩上甲板面（z 61 的上一格）
SCALE = 0.5
DECK_Z = 82


def build():
    v = {}
    put = lambda x, y, z, c: v.__setitem__((x, y, z), c)
    # 鉛盤（一格厚、比磚身每邊大一格）
    for x in range(0, 30):
        for y in range(1, 29):
            put(x, y, 0, LEAD)
    # 磚身 x 1..28、y 2..27、z 1..21；外表面一層照砌法：三格一皮、皮與皮之間灰漿、豎縫每 6 格錯半塊
    for x in range(1, 29):
        for y in range(2, 28):
            for z in range(1, 22):
                surf = x in (1, 28) or y in (2, 27) or z == 21
                if not surf:
                    put(x, y, z, BRICK)
                    continue
                course = (z - 1) // 3
                if (z - 1) % 3 == 2:
                    c = MORTAR
                else:
                    u = y if x in (1, 28) else x
                    c = MORTAR if (u + 3 * (course % 2)) % 6 == 0 else (BRICK2 if (u // 6 + course) % 3 == 0 else BRICK)
                put(x, y, z, c)
    # 爐口（船尾那一面 x 1）：拱形開口 y 9..20、z 3..13，往裡 9 格；裡面燻黑、底下炭火
    for x in range(1, 10):
        for y in range(9, 21):
            for z in range(3, 14):
                dy = (y - 14.5) / 6.0
                top = 10 + 3 * math.sqrt(max(0.0, 1 - dy * dy))
                if z <= top:
                    v.pop((x, y, z), None)
    for x in range(1, 11):
        for y in range(8, 22):
            for z in range(2, 15):
                k = (x, y, z)
                if k in v and any((x + dx, y + dy, z + dz) not in v for dx, dy, dz in ((1, 0, 0), (-1, 0, 0), (0, 1, 0), (0, -1, 0), (0, 0, 1), (0, 0, -1))) and x > 1:
                    v[k] = SOOT
    for x in range(3, 10):
        for y in range(10, 20):
            put(x, y, 3, EMBER if (x + y) % 3 else FLAME)
            if (x * 7 + y * 3) % 5 == 0:
                put(x, y, 4, FLAME)
    # 拱頂一圈立砌的磚
    for y in range(8, 22):
        dy = (y - 14.5) / 6.0
        top = 10 + 3 * math.sqrt(max(0.0, 1 - dy * dy))
        z = int(math.floor(top)) + 1
        if 2 <= z <= 15:
            put(1, y, z, BRICK2)
    # 頂上鐵板 z 22（煙囪那一段不鋪）
    for x in range(1, 29):
        for y in range(2, 28):
            if not (21 <= x <= 28 and 11 <= y <= 18):
                put(x, y, 22, IRON)
    # 銅鍋（大鍋放在爐口正上方那一段）：圓、直徑 12、高 8、外緣一圈深色口沿、鍋蓋
    cx, cy, r = 11.5, 14.5, 6.0
    for x in range(4, 20):
        for y in range(7, 23):
            d = math.hypot(x + 0.5 - cx - 0.5, y + 0.5 - cy - 0.5)
            for z in range(23, 31):
                rz = r - (0.8 if z == 23 else 0.0)
                if d <= rz:
                    if z == 30:
                        put(x, y, z, COPPER_D if d > r - 1.2 else COPPER)
                    elif d > rz - 1.0:
                        put(x, y, z, COPPER_D if z == 29 else COPPER)
                    else:
                        put(x, y, z, SOOT if z == 29 else COPPER)
    # 鍋蓋把手
    put(11, 14, 31, IRON); put(12, 14, 31, IRON); put(11, 15, 31, IRON); put(12, 15, 31, IRON)
    # 煙囪：磚 x 22..27、y 12..17（6×6）從 z 22 往上到 z 41（過甲板）、上面一段銅皮到 z 55、鐵帽 z 56..58
    for z in range(22, 59):
        for x in range(21, 29):
            for y in range(11, 19):
                inner = 23 <= x <= 26 and 13 <= y <= 16
                body = 22 <= x <= 27 and 12 <= y <= 17
                if z <= 41:
                    if body and not inner:
                        course = (z - 22) // 3
                        put(x, y, z, MORTAR if (z - 22) % 3 == 2 else (BRICK2 if (x + y + course) % 4 == 0 else BRICK))
                elif z <= 55:
                    if body and not inner:
                        put(x, y, z, COPPER if z % 6 else COPPER_D)
                else:
                    if not inner:
                        put(x, y, z, IRON)
    # 煙囪口裡面一點燻黑
    for x in range(23, 27):
        for y in range(13, 17):
            put(x, y, 50, SOOT)
    return v


def to_world(k):
    return tuple(AT[i] + (k[i] + 0.5 - PIVOT[i]) * SCALE for i in range(3))


def main():
    sys.stdout.reconfigure(encoding='utf-8')
    design = sys.argv[1]
    v = build()
    for k in v:
        assert all(0 <= k[i] < SIZE[i] for i in range(3)), k
    os.makedirs(os.path.join(design, 'masks', 'galley'), exist_ok=True)
    keys = sorted(v)
    with open(os.path.join(design, 'masks', 'galley', 'galley.vox.txt'), 'w', encoding='utf-8', newline='\n') as f:
        f.write('# 康塞普西翁號 廚房爐灶（模型座標 0.05 m；draft_galley.py）\n')
        for k in keys:
            f.write('%d,%d,%d,%d\n' % (k + (v[k],)))
    # 每個模型格在船上佔哪幾格（取樣格心＋八角）
    world = set()
    for k in keys:
        for dx in (0.05, 0.95):
            for dy in (0.05, 0.95):
                for dz in (0.05, 0.95):
                    p = [AT[i] + (k[i] + d - PIVOT[i]) * SCALE for i, d in enumerate((dx, dy, dz))]
                    world.add(tuple(int(math.floor(c)) for c in p))
    D = np.loadtxt(os.path.join(design, 'masks', 'decks', 'castillo.vox.txt'), delimiter=',', comments='#', dtype=np.int64, ndmin=2, encoding='utf-8')   # 從甲板的設計遮罩算（刻過之後重跑照樣同一份）
    hole = sorted(tuple(r) for r in D.tolist() if tuple(r[:3]) in world)
    with open(os.path.join(design, 'masks', 'galley', 'deck_hole.vox.txt'), 'w', encoding='utf-8', newline='\n') as f:
        f.write('# 船艏樓甲板讓煙囪過的洞（從甲板-castillo 刻掉；帶現在的顏色）\n')
        for r in hole:
            f.write('%d,%d,%d,%d\n' % tuple(r))
    A = export_list('apex-two-galeon-01m-assembly', None, links=None)
    occ = set(map(tuple, A[:, :3].tolist()))
    hit = sorted((world & occ) - set(tuple(r[:3]) for r in hole))
    # 腳下：最底一層模型格往下一格要是甲板
    foot = {(c[0], c[1]) for c in world if c[2] == AT[2]}
    unsupported = sorted(xy for xy in foot if (xy[0], xy[1], AT[2] - 1) not in occ)
    # 廚師站的那一面（船尾面）：外框外 2 格的中點，0.6 m 內要有腳下實心、頭上 12 格空的格
    xs = [c[0] for c in world]
    stand = (min(xs) - 2, 160, AT[2])
    ok_stand = (stand[0], stand[1], stand[2] - 1) in occ and all((stand[0], stand[1], z) not in occ for z in range(stand[2], stand[2] + 12))
    verify = {'model_cells': len(v), 'world_cells': len(world), 'world_box': [min(xs), max(xs), min(c[1] for c in world), max(c[1] for c in world), min(c[2] for c in world), max(c[2] for c in world)],
              'deck_hole': len(hole), 'hits_solid': len(hit), 'hits_sample': hit[:6], 'unsupported': len(unsupported), 'stand_aft': list(stand), 'stand_aft_ok': ok_stand,
              'colors': {str(c): sum(1 for x in v.values() if x == c) for c in sorted(set(v.values()))},
              'list_sha256': hashlib.sha256(open(os.path.join(design, 'masks', 'galley', 'galley.vox.txt'), 'rb').read()).hexdigest()}
    json.dump({'work': 'apex-two-galeon-01m-galley', 'deck_work': 'apex-two-galeon-01m-deck-puente', 'name': '爐灶', 'at': list(AT), 'pivot': list(PIVOT), 'scale': SCALE,
               'meta': {'kind': 'galley'}, 'size': list(SIZE)}, open(os.path.join(design, 'galley_placement.json'), 'w', encoding='utf-8'), ensure_ascii=False, indent=1)
    json.dump(verify, open(os.path.join(design, 'verify_galley.json'), 'w', encoding='utf-8'), ensure_ascii=False, indent=1)
    print(json.dumps(verify, ensure_ascii=False))


if __name__ == '__main__':
    main()
