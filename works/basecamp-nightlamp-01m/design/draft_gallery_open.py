# 夜燈號 quarter gallery 挖空（TASK-0753；Tim 2026-10-20：「船尾側面也可以改用玻璃嗎」→「夜燈號」）
#   gallery 的窗早就是玻璃（子作品 -stern-glass），但玻璃後面是實心的黑（5 格以上）⇒ 透過去只看到黑。
#   照餘燼號 gallery_open（Tim 2026-10-13「窗戶部分可以直接開孔 這樣可以看到內部結構」）：上下兩層各掏成一間小房間、背後的船殼開一道門通到船尾艙。
# 規則（右舷算，左舷 y' ＝ 320 − y 照算一次、比對兩舷一樣）：
#   · gallery 的格 ＝ 每個 (x, z) 從船外往裡走：玻璃（-stern-glass）、色 36／73 的格，碰到別的色 ＝ 船殼外板 ⇒ 停。
#   · 房間：x 74–94（兩端各留牆）、下層 z 116–135、上層 z 142–157；窗那一欄只留玻璃，窗間的柱留最外兩層（2 格厚的牆），裡面的黑全刻。
#   · 門：x 82–86（中間那扇窗後面）、下層 z 116–130、上層 z 142–156：從 gallery 那一面往船裡刻船殼外板，碰到空氣（≤ 7 格）才刻；途中碰到別的部件（甲板…）或刻不穿 ⇒ 那一欄不刻。
# 讀：船殼作品（export work=basecamp-nightlamp-01m region=60..110,90..230,95..175 ⇒ 參數 1）、組裝件同一範圍（參數 2）、玻璃清單（參數 3）
# 寫：masks/stern/gallery_open_carve.vox.txt（carvevox，行尾顏色守門）
import os, sys

HERE = os.path.dirname(os.path.abspath(__file__))
YC, GAL = 160, (36, 73)
ROOMS = [('下層', 116, 135, 116, 130), ('上層', 142, 157, 142, 156)]
X_ROOM, X_DOOR, WALL_MAX = (74, 94), (82, 86), 7


def cells(path):
    out = {}
    for ln in open(path, encoding='utf-8'):
        if ln.startswith('#') or not ln.strip():
            continue
        v = [int(t) for t in ln.split(',')]
        out[(v[0], v[1], v[2])] = v[3] if len(v) > 3 else 1
    return out


H, A, G = cells(sys.argv[1]), cells(sys.argv[2]), set(cells(sys.argv[3]))


def side(sg):
    """sg ＝ +1 右舷、−1 左舷 ⇒ {格: 色}（要刻的）、讀數。"""
    Y = (lambda d: YC + sg * d)
    carve, read = {}, {'room': 0, 'door': 0, 'door_skip': 0}
    for name, rz0, rz1, dz0, dz1 in ROOMS:
        for x in range(X_ROOM[0], X_ROOM[1] + 1):
            for z in range(rz0, rz1 + 1):
                col = []                                   # 從船外往裡：gallery 的格
                d = 75
                while d > 0 and (x, Y(d), z) not in H and (x, Y(d), z) not in G:
                    d -= 1
                while d > 0 and ((x, Y(d), z) in G or H.get((x, Y(d), z)) in GAL):
                    col.append(d)
                    d -= 1
                hull_d = d                                 # 船殼外板最外那一格
                keep = 1 if col and (x, Y(col[0]), z) in G else 2   # 窗那一欄：只留玻璃；窗間的柱：最外兩層留著
                for dd in col[keep:]:
                    p = (x, Y(dd), z)
                    if p in G:
                        continue
                    carve[p] = H[p]
                    read['room'] += 1
                if X_DOOR[0] <= x <= X_DOOR[1] and dz0 <= z <= dz1 and len(col) > 2:
                    run, dd = [], hull_d
                    while (x, Y(dd), z) in H and len(run) <= WALL_MAX:
                        run.append((x, Y(dd), z))
                        dd -= 1
                    if (x, Y(dd), z) in A or len(run) > WALL_MAX:   # 碰到別的部件、或刻不穿
                        read['door_skip'] += 1
                        continue
                    for p in run:
                        carve[p] = H[p]
                        read['door'] += 1
    return carve, read


S, rs = side(1)
P, rp = side(-1)
mir = {(x, 2 * YC - y, z): c for (x, y, z), c in P.items()}
print('右舷', rs, '左舷', rp, '兩舷對稱：', mir == S)
assert mir == S, '兩舷不對稱'
allc = dict(S)
allc.update(P)
out = os.path.join(HERE, 'masks', 'stern', 'gallery_open_carve.vox.txt')
with open(out, 'w', encoding='utf-8', newline='') as f:
    f.write('# quarter gallery 挖空＋門（carvevox，行尾顏色守門；%d 格，船殼座標；TASK-0753）\n' % len(allc))
    for (x, y, z), c in sorted(allc.items()):
        f.write('%d,%d,%d,%d\n' % (x, y, z, c))
print('寫', len(allc), '格 ⇒', out)
