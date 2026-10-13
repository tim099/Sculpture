# 餘燼號 階段十六 wardroom（軍官室；plan.json wardroom_build；自由設計，Tim「房間也自由發揮吧」）
#   上層砲甲板船尾（地板 105、天花板 128；舷側砲架在 |dy| ≥ 23；船尾追擊砲 x 108–128；中線每 16 格一根柱 x 140／156／172／188；後桅 x 200–206 穿過）：
#   · 前艙壁 x 232–233（第 2、3 門砲之間），正中一扇雙開門（|dy| ≤ 4）；壁板 177、每 8 格一根 136 壁柱、頂一條金
#   · 中線長桌 x 144–184、|dy| ≤ 5、桌面 z 113（柱子從桌面穿過 —— 撞到的格不放）；兩側長椅 |dy| 8–9（暗紅椅墊）
#   · 桌子上方吊一盞小的「餘燼之心」（金籠＋琥珀火芯，吊在天花板下）
#   每一格只放在現況（組裝件＋砲模型的格）是空氣的地方；撞到的照部位記數。⇒ masks/wardroom/wardroom.vox.txt（世界座標、at 0,0,0）、verify_wardroom.json
# 用法：python -I draft_wardroom.py <design 資料夾>
import sys, os, json, hashlib, collections
import numpy as np
from scipy import ndimage

D = os.path.abspath(sys.argv[1])
sys.path.insert(0, D)
from draft_ladders import existing_links, export_hidden  # noqa: E402
import place_guns as PG                                  # noqa: E402

YC = 160


class Ward:
    def __init__(s):
        plan = json.load(open(os.path.join(D, 'plan.json'), encoding='utf-8'))
        s.P = plan['wardroom_build']
        have = set(existing_links(s.P['assembly']))
        s.hidden = [h for h in s.P['hide_links'] if h in have]
        a = export_hidden(s.P['assembly'], s.hidden)
        assert len(a) == s.P['assembly_voxels'], ('組裝件現況對不上', len(a))
        s.A = {(int(x), int(y), int(z)) for x, y, z, c in a if 95 <= x <= 260 and 95 <= z <= 135}
        GB = plan['guns_build']
        s.G = set()
        for r in json.load(open(os.path.join(D, 'guns_placement.json'), encoding='utf-8'))['rows']:
            if r['deck'] != 'upper' or r['at'][0] > 280:
                continue
            t = GB['types'][r['type']]
            src = os.path.join(D, t['cells']) if t['cells'].startswith('masks/') else t['cells']
            g = PG.Gun(r['type'], t['work'], PG.load_cells(src), t['scale'], t['pivot'], t['muzzle'], t['meta'])
            s.G |= set(map(tuple, np.floor(g.world(g.samples, r['at'], r['phi'], r['side'] == 'P')).astype(int).tolist()))
        s.solid = s.A | s.G
        s.cells, s.part = {}, {}
        s.hit = collections.Counter()

    def put(s, k, c, part):
        if k in s.solid:
            s.hit[part] += 1
            return
        s.cells[k] = c
        s.part[k] = part

    def ceil(s, x, y, z0):
        """往上第一個實心（找不到 ⇒ None：頭上是露天，v1 當成 z0＋30 ⇒ 艙壁長到上甲板上面 88 格浮空）"""
        z = z0
        while (x, y, z) not in s.A and z < z0 + 30:
            z += 1
        return z if (x, y, z) in s.A else None

    def half(s, x, z):
        lo = hi = YC
        while (x, hi + 1, z) not in s.A and hi - YC < 60:
            hi += 1
        while (x, lo - 1, z) not in s.A and YC - lo < 60:
            lo -= 1
        return lo, hi

    def build(s):
        P, K = s.P, s.P['colors']
        f = P['floor_z']
        # 前艙壁
        bx = P['bulkhead_x']
        door = P['door_half']
        for x in bx:
            for z in range(f, f + 30):
                lo, hi = s.half(x, z)
                if hi - lo < 4 or hi - YC >= 60 or YC - lo >= 60:
                    continue                                       # 兩舷沒碰到牆 ⇒ 不是艙裡
                for y in range(lo, hi + 1):
                    cz = s.ceil(x, y, f)
                    if cz is None or z > cz - 1:
                        continue
                    top = cz - 1
                    dy = y - YC
                    if abs(dy) <= door and z < f + P['door_h']:
                        continue                                   # 門洞
                    if abs(dy) == door + 1 and z < f + P['door_h'] + 1 or (abs(dy) <= door + 1 and z == f + P['door_h']):
                        s.put((x, y, z), K['frame'], 'door')        # 門框
                        continue
                    gz = P.get('gold_z')                           # v2：金線統一一個高度（v1 照每一欄的天花板 ⇒ 中段 127、兩旁 125、外側被擋掉沒有）
                    if gz is None:
                        c = K['gold'] if z == top else (K['frame'] if dy % 8 == 0 else K['panel'])
                    else:
                        c = K['gold'] if z == gz else (K['panel'] if z > gz or dy % 8 else K['frame'])
                    s.put((x, y, z), c, 'bulkhead')
        # 長桌
        x0, x1 = P['table']['x']
        th = P['table']['half']
        tz = P['table']['top_z']
        for x in range(x0, x1 + 1):
            for dy in range(-th, th + 1):
                y = YC + dy
                s.put((x, y, tz), K['table'], 'table')
                edge = abs(dy) == th or x in (x0, x1)
                if edge:
                    s.put((x, y, tz - 1), K['frame'], 'table')     # 桌裙
        for x in (x0 + 1, x1 - 1) + tuple(range(x0 + 10, x1 - 5, 10)):
            for dy in (-th + 1, th - 1):
                for z in range(f, tz - 1):
                    s.put((x, YC + dy, z), K['frame'], 'table-leg')
        # 長椅
        bh = P['bench']
        for sg in (-1, 1):
            for x in range(x0 + 1, x1):
                for d in bh['dy']:
                    s.put((x, YC + sg * d, bh['seat_z']), K['cushion'], 'bench')
                if (x - x0) % 8 == 1:
                    for d in bh['dy']:
                        for z in range(f, bh['seat_z']):
                            s.put((x, YC + sg * d, z), K['frame'], 'bench-leg')
            for x in range(x0 + 1, x1):                                # 椅背（外側那一欄，從椅面那一層起 ⇒ 面貼面接上；v1 從上一層起只有斜角相碰、312 格浮空）
                for z in range(bh['seat_z'], bh['seat_z'] + 5):
                    s.put((x, YC + sg * (max(bh['dy']) + 1), z), K['frame'] if z < bh['seat_z'] + 4 else K['gold'], 'bench-back')
        # 吊燈（小的餘燼之心）
        L = P['lamp']
        lx, ly = L['x'], YC
        top = s.ceil(lx, ly, tz + 1)
        assert top is not None, '吊燈上面沒有天花板'
        cz1 = top - L['chain']
        cz0 = cz1 - L['cage_h'] + 1
        for z in range(cz1 + 1, top):
            s.put((lx, ly, z), K['gold'], 'lamp-chain')
        r = L['cage_half']
        for x in range(lx - r, lx + r + 1):
            for y in range(ly - r, ly + r + 1):
                for z in range(cz0, cz1 + 1):
                    ex = (abs(x - lx) == r) + (abs(y - ly) == r) + (z in (cz0, cz1))
                    if ex >= 2 or (z == cz1 and (x == lx or y == ly)):
                        s.put((x, y, z), K['gold'], 'lamp-cage')        # 籠子的稜＋籠頂金十字（v1 籠頂正中是空的 ⇒ 吊鍊接不到籠子，同船長室 v1）
                    elif ex == 0 and abs(x - lx) <= L['core_half'] and abs(y - ly) <= L['core_half']:
                        s.put((x, y, z), K['amber'] if (x, y) == (lx, ly) else K['flame'], 'lamp-core')
        for z in range(cz0 + 1, cz1):                                  # 中軸（火芯接到籠頂）
            if (lx, ly, z) not in s.cells:
                s.put((lx, ly, z), K['amber'], 'lamp-core')

    def verify(s):
        v = {'cells': len(s.cells), 'by_part': dict(collections.Counter(s.part.values())), 'hit': dict(s.hit),
             'colors': {str(c): n for c, n in collections.Counter(s.cells.values()).items()},
             'mirror_mismatch': sum(1 for (x, y, z), c in s.cells.items() if s.cells.get((x, 2 * YC - y, z)) != c)}
        keys = list(s.A) + list(s.cells)
        lo = np.min(np.array(keys), 0) - 1
        hi = np.max(np.array(keys), 0) + 2
        B = np.zeros(tuple(hi - lo), bool)
        for k in keys:
            B[tuple(np.array(k) - lo)] = True
        lab, n = ndimage.label(B)
        base = set(lab[tuple(np.array(k) - lo)] for k in s.A)
        fl = [k for k in s.cells if lab[tuple(np.array(k) - lo)] not in base]
        v['floating'] = {'n': len(fl), 'by_part': dict(collections.Counter(s.part[k] for k in fl)), 'first': [list(k) for k in fl[:5]]}
        v['expect_assembly_after'] = s.P['assembly_voxels'] + len(s.cells)
        return v

    def write(s, v):
        p = os.path.join(D, 'masks', 'wardroom', 'wardroom.vox.txt')
        os.makedirs(os.path.dirname(p), exist_ok=True)
        rows = sorted((k[0], k[1], k[2], c) for k, c in s.cells.items())
        open(p, 'w', encoding='utf-8', newline='\n').write('# wardroom —— 餘燼號 軍官室（世界座標、at 0,0,0；%d 格）\n' % len(rows) + '\n'.join('%d,%d,%d,%d' % r for r in rows) + '\n')
        v['file'] = {'cells': len(rows), 'sha256': hashlib.sha256(open(p, 'rb').read()).hexdigest()}
        json.dump(v, open(os.path.join(D, 'verify_wardroom.json'), 'w', encoding='utf-8', newline='\n'), ensure_ascii=False, indent=1)


def main():
    sys.stdout.reconfigure(encoding='utf-8')
    W = Ward()
    W.build()
    v = W.verify()
    W.write(v)
    print(json.dumps(v, ensure_ascii=False))


if __name__ == '__main__':
    main()
