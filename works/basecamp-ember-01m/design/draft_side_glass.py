# 餘燼號：船尾兩舷 quarterdeck 的開口補玻璃、quarter gallery 的門打通（TASK-0753；Tim 2026-10-20）
#   「餘燼號船尾側邊開口是否可以補玻璃窗?」「圖片左側的窗戶看進去是木板 是否可以打通到船內部」
#   ① gallery 的門（gallery_open：x 111–117、下層 z 107–121、上層 z 130–144）當初沒刻穿：船殼外板還剩 y 204–205（左舷 115–116）兩層 ⇒ 從 gallery 往裡看是木板。
#      ⇒ 門框裡、船殼作品自己的格，從 gallery 那一面往裡刻到空氣（≤ 7 格；途中碰到別的部件 ⇒ 那一欄不刻）。
#   ② 船長室兩舷的三個開口（沒有砲：第一門 carronade 在 x 225 起）：x 128–136、157–165、188–196，z 134–147 ⇒ 每欄在外板面往裡 1 格放 1 格玻璃（照船尾窗）；
#      外板面 ＝ 同一個 z、開口兩邊最近的船殼格的最外 y；那一格已經有東西（擋在開口裡的鐵條）⇒ 跳過。
#      子作品 basecamp-ember-01m-side-glass（組裝件座標 at=0,0,0），關聯 meta material=glass；色 245（琥珀，跟船尾窗一樣）。
# 讀：組裝件（export region=95..260,100..240,95..170 ⇒ 參數 1）、船殼作品同一範圍（參數 2）
# 寫：masks/glass/gallery_door_carve.vox.txt（carvevox，行尾顏色守門）、masks/glass/side_glass.vox.txt（stampvox at=0,0,0）
import os, sys

HERE = os.path.dirname(os.path.abspath(__file__))
YC, GLASS, WALL_MAX = 160, 245, 7
DOORS = [((111, 117), (107, 121)), ((111, 117), (130, 144))]
OPEN_X, OPEN_Z = [(128, 136), (157, 165), (188, 196)], (134, 147)


def cells(path):
    out = {}
    for ln in open(path, encoding='utf-8'):
        if ln.startswith('#') or not ln.strip():
            continue
        v = [int(t) for t in ln.split(',')]
        out[(v[0], v[1], v[2])] = v[3]
    return out


A, H = cells(sys.argv[1]), cells(sys.argv[2])


def side(sg):
    Y = (lambda d: YC + sg * d)
    carve, glass, read = {}, {}, {'door': 0, 'door_skip': 0, 'glass': 0, 'glass_skip': 0}
    for (x0, x1), (z0, z1) in DOORS:
        for x in range(x0, x1 + 1):
            for z in range(z0, z1 + 1):
                d = 47                                   # gallery 房間裡（y 207／左舷 113）往船裡找第一格
                while d > 30 and (x, Y(d), z) not in A:
                    d -= 1
                run = []
                while (x, Y(d), z) in H and len(run) <= WALL_MAX:
                    run.append((x, Y(d), z))
                    d -= 1
                if (x, Y(d), z) in A or len(run) > WALL_MAX or not run:
                    read['door_skip'] += 1
                    continue
                for p in run:
                    carve[p] = H[p]
                read['door'] += len(run)
    for x0, x1 in OPEN_X:
        for z in range(OPEN_Z[0], OPEN_Z[1] + 1):
            fr = []
            for xx in (x0 - 1, x0 - 2, x1 + 1, x1 + 2):
                ds = [d for d in range(30, 56) if (xx, Y(d), z) in H]
                if ds:
                    fr.append(max(ds))
            if not fr:
                continue
            d = min(fr) - 1
            for x in range(x0, x1 + 1):
                if any((x, Y(dd), z) in A for dd in range(d - 3, d + 4)):   # 這一欄不是開口（牆、鐵條）
                    read['glass_skip'] += 1
                    continue
                glass[(x, Y(d), z)] = GLASS
                read['glass'] += 1
    return carve, glass, read


C1, G1, r1 = side(1)
C2, G2, r2 = side(-1)
print('右舷', r1, '左舷', r2)
assert {(x, 2 * YC - y, z): c for (x, y, z), c in C2.items()} == C1, '門：兩舷不對稱'
assert {(x, 2 * YC - y, z): c for (x, y, z), c in G2.items()} == G1, '玻璃：兩舷不對稱'
C1.update(C2)
G1.update(G2)
os.makedirs(os.path.join(HERE, 'masks', 'glass'), exist_ok=True)
for name, D, note in (('gallery_door_carve.vox.txt', C1, 'quarter gallery 的門刻穿（carvevox，行尾顏色守門；船殼座標）'),
                      ('side_glass.vox.txt', G1, '船長室兩舷開口的玻璃（組裝件座標）')):
    with open(os.path.join(HERE, 'masks', 'glass', name), 'w', encoding='utf-8', newline='') as f:
        f.write('# %s（%d 格；TASK-0753）\n' % (note, len(D)))
        for (x, y, z), c in sorted(D.items()):
            f.write('%d,%d,%d,%d\n' % (x, y, z, c))
    print(name, len(D))
