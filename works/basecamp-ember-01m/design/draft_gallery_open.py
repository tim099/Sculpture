# 餘燼號 quarter gallery 開窗（plan.json gallery_open；Tim 2026-10-13「窗戶部分可以直接開孔 這樣可以看到內部結構」）
#   量到：gallery 子作品（右舷一件、另一舷 mirror=y 關聯）是實心的黑塊，只有外面一層琥珀玻璃（245，330 格）⇒ 只拿掉玻璃看進去是黑的。
#   改法：① 玻璃全拿掉（開孔）② 上下兩層掏空成小房間（牆留 1 格：只拿掉六個鄰居都是 gallery 的格，而且 z 在那一層的地板與天花板之間）
#        ③ 每一層在背後的船殼牆開一道門（下層 → 上層砲甲板船尾、上層 → 船長室；實船的 quarter gallery 從船長室進去）：
#           門的 (x, z) 範圍裡，從 gallery 背後那一格往船裡走，船殼實心一路刻到碰到空氣；兩舷（P 舷是 y ↔ 320 − y）。
#   ⇒ masks/gallery/{gallery_carve,hull_carve}.vox.txt（carvevox，帶顏色守門）、verify_gallery_open.json
# 用法：python -I draft_gallery_open.py <design 資料夾>
import sys, os, json, hashlib, collections
import numpy as np
from scipy import ndimage

D = os.path.abspath(sys.argv[1])
sys.path.insert(0, D)
import draft_profile as DP                               # noqa: E402
from draft_ladders import existing_links, export_hidden  # noqa: E402
from draft_ports import export_mark                      # noqa: E402

YC = 160


def main():
    sys.stdout.reconfigure(encoding='utf-8')
    plan = json.load(open(os.path.join(D, 'plan.json'), encoding='utf-8'))
    F = plan['gallery_open']
    g = export_mark(F['gallery'], F['gallery_mark']) if F.get('gallery_mark') else export_hidden(F['gallery'], [])
    assert len(g) == F['gallery_voxels'], ('gallery 現況對不上', len(g))
    G = {(int(x), int(y), int(z)): int(c) for x, y, z, c in g}
    ax, ay, az = F['at_S']
    # ① 玻璃
    glass = {k for k, c in G.items() if c == F['glass']}
    # ② 掏空
    arr = np.array(sorted(G))
    shp = tuple(arr.max(0) + 3)
    S = np.zeros(shp, bool)
    S[tuple((arr + 1).T)] = True
    er = ndimage.binary_erosion(S, ndimage.generate_binary_structure(3, 1), border_value=0)
    hollow = set()
    for lv in F['levels']:
        lo, hi = lv['floor'] - az, lv['ceiling'] - az              # 世界 z → gallery 自己的 z
        for p in np.argwhere(er):
            k = tuple(int(v) - 1 for v in p)
            if lo < k[2] < hi and k not in glass:
                hollow.add(k)
    # 門那一塊的 gallery 背牆（掏空留下 1 格厚的牆貼著船殼）：門的每個 (x, z)，比掏空最小的 y 還靠船殼的 gallery 格也拿掉
    backwall = set()
    for lv in F['levels']:
        x0, x1 = lv['door_x']
        for x in range(x0, x1 + 1):
            for z in range(lv['door_z0'], lv['door_z0'] + lv['door_h']):
                lx, lz = x - ax, z - az
                hy = [k[1] for k in hollow if k[0] == lx and k[2] == lz]
                if not hy:
                    continue
                for k in G:
                    if k[0] == lx and k[2] == lz and k[1] < min(hy):
                        backwall.add(k)
    gcarve = sorted((k[0], k[1], k[2], G[k]) for k in glass | hollow | backwall)
    # ③ 門：船殼（標記之後的現況）
    h = DP.export_list(F['hull'], links='none')
    assert len(h) == F['hull_voxels'], ('船殼現況對不上', len(h))
    Hc = {(int(x), int(y), int(z)): int(c) for x, y, z, c in h}
    have = set(existing_links(F['assembly']))
    asm = export_hidden(F['assembly'], [])
    A = set(map(tuple, asm[:, :3].tolist()))
    hcarve, doors = {}, []
    for lv in F['levels']:
        x0, x1 = lv['door_x']
        z0 = lv['door_z0']
        z1 = z0 + lv['door_h'] - 1
        for side in (1, -1):
            n = 0
            stuck = []
            for x in range(x0, x1 + 1):
                for z in range(z0, z1 + 1):
                    # gallery 背後那一格（世界 y）：gallery 最小的 y ＋ at.y，往船裡一格起
                    y = ay + F['gallery_back_y'] - 1 if side > 0 else 320 - (ay + F['gallery_back_y'] - 1)
                    k0 = 0
                    while (x, y, z) not in Hc and k0 < 4:          # gallery 背後跟船殼之間若有一兩格空氣，先走到船殼
                        y -= side
                        k0 += 1
                    steps = 0
                    while (x, y, z) in Hc and steps < 12:
                        hcarve[(x, y, z)] = Hc[(x, y, z)]
                        n += 1
                        y -= side
                        steps += 1
                    # 刻完之後那一格要是空氣（不是別件作品）
                    if (x, y, z) in A and (x, y, z) not in Hc:
                        stuck.append((x, y, z))
            doors.append({'level': lv['name'], 'side': 'S' if side > 0 else 'P', 'x': [x0, x1], 'z': [z0, z1], 'hull_cells': n, 'blocked_behind': len(stuck), 'first_blocked': stuck[:3]})
    rows = sorted((k[0], k[1], k[2], c) for k, c in hcarve.items())
    # 連通：開完之後 gallery 裡的空氣接到船艙（量 S 舷：世界座標下 gallery 掏空的格 → 船裡）
    out = os.path.join(D, 'masks', 'gallery')
    os.makedirs(out, exist_ok=True)
    files = {}
    for nm, rr, note in (('gallery_carve', gcarve, 'gallery 子作品自己的座標：玻璃 ＋ 掏空'), ('hull_carve', rows, '船殼世界座標：兩舷的門')):
        p = os.path.join(out, nm + '.vox.txt')
        open(p, 'w', encoding='utf-8', newline='\n').write('# %s —— %s（carvevox 帶顏色守門；%d 格）\n' % (nm, note, len(rr)) + '\n'.join('%d,%d,%d,%d' % r for r in rr) + '\n')
        files[nm] = {'cells': len(rr), 'sha256': hashlib.sha256(open(p, 'rb').read()).hexdigest()}
    # 鏡像：門兩舷逐格對稱
    keys = set(hcarve)
    mir = sum(1 for (x, y, z) in keys if (x, 320 - y, z) not in keys)
    v = {'gallery': {'voxels': len(G), 'glass': len(glass), 'hollow': len(hollow), 'door_backwall': len(backwall), 'after': len(G) - len(gcarve),
                     'hollow_by_level': {lv['name']: sum(1 for k in hollow if lv['floor'] - az < k[2] < lv['ceiling'] - az) for lv in F['levels']},
                     'carve_colors': dict(collections.Counter(c for *_, c in gcarve))},
         'hull': {'voxels': len(Hc), 'carve': len(rows), 'colors': dict(collections.Counter(c for *_, c in rows)), 'mirror_missing': mir},
         'doors': doors, 'files': files,
         'expect_assembly_after': len(asm) - 2 * len(gcarve) - len(rows)}
    json.dump(v, open(os.path.join(D, 'verify_gallery_open.json'), 'w', encoding='utf-8', newline='\n'), ensure_ascii=False, indent=1)
    print(json.dumps(v, ensure_ascii=False))


if __name__ == '__main__':
    main()
