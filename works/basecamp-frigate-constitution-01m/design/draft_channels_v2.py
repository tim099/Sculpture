"""
階段二十九 追加（Tim：「這幾個被纜線擋住了」）：channels 的 deadeye 改排到 spar deck 砲門之間 —— channels 子作品 v2。
v1：每根桅第一個 deadeye 在桅前 fwd 格、往船尾每 spacing（6–7）格一個 ⇒ channel 範圍裡的 spar deck 砲門（後桅 2、3；主桅 6–8；前桅 9–11）
    前面一定有 deadeye、lanyard、shroud。實船是把 deadeye 分組擠在砲門之間。
v2：數量與順序不變（固定點名字不變 ⇒ shroud／backstay 跟著走）；第一個放在離「桅前 fwd 格」最近、不擋砲門的整數格，
    之後往船尾每 SPACING（4）格一個，碰到砲門就跳到砲門後面。「擋」＝ deadeye 本體（x ± 1）或它上面那段 shroud
   （往 hounds 斜上去，z 111–125）落在砲門 x 範圍 ± MARGIN（1）裡。channel 的長度照新的 deadeye 範圍（同 v1 的規則）。
    chain plate 照 v1（避 gun deck 砲門）。
用法：python -I draft_channels_v2.py <組裝件清單（藏 channels、channels-鏡像、舵）.txt> <channels 子作品清單（自己的座標）.txt>
輸出：masks/channels/v2_carve.vox.txt、v2_add.vox.txt、rig_points_channels.json（覆寫）、verify_channels_v2.json
"""
import json, math, os, sys
import numpy as np

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import draft_channels as DC        # noqa: E402

SPACING = 4
MARGIN = 1
Z_BAND = (111, 125)


class Channels2(DC.Channels):
    def __init__(s, asm_path):
        s.design = HERE
        s.plan = json.load(open(os.path.join(HERE, 'plan.json'), encoding='utf-8'))
        s.P = s.plan['channels']
        a = np.loadtxt(asm_path, delimiter=',', comments='#', dtype=np.int32, ndmin=2, encoding='utf-8')
        m = a[(a[:, 0] >= DC.XA) & (a[:, 0] < DC.XB) & (a[:, 2] >= DC.ZA) & (a[:, 2] < DC.ZB)]
        s.G = np.zeros((DC.XB - DC.XA, 320, DC.ZB - DC.ZA), np.uint8)
        s.G[m[:, 0] - DC.XA, m[:, 1], m[:, 2] - DC.ZA] = m[:, 3]
        s.cells, s.kind, s.anchors, s.groups = {}, {}, [], []
        s.ports = [p['x'] for p in json.load(open(os.path.join(HERE, 'verify_spar_ports.json'), encoding='utf-8'))['ports']]

    def blocked(s, xi, M):
        hx, hz = M['hounds']
        z_top = s.P['z'][1] + 3
        for a, b in s.ports:
            if a - MARGIN <= xi + 1 and xi - 1 <= b + MARGIN:
                return True
            for z in range(Z_BAND[0], Z_BAND[1] + 1):
                x = xi + (hx - xi) * (z - z_top) / (hz - z_top)
                if a - MARGIN <= x <= b + MARGIN:
                    return True
        return False

    def deadeye_xs(s, M):
        n = M['shrouds'] + M['backstays']
        start = M['x_mast'] + M['fwd']
        first = min((x for x in range(int(start) - 6, int(start) + 7) if not s.blocked(x, M)), key=lambda x: abs(x - start))
        xs = [first]
        while len(xs) < n:
            x = xs[-1] - SPACING
            while s.blocked(x, M):
                x -= 1
            xs.append(x)
        return [float(x) for x in xs]

    def build(s):
        # 跟 v1 的 build 同一套（channel／deadeye／chain plate），只換 xs
        orig = {M['mast']: dict(M) for M in s.P['masts']}
        s.v2_xs = {}
        for M in s.P['masts']:
            s.v2_xs[M['mast']] = s.deadeye_xs(M)
        P = s.P
        col = P['colors']
        s.port_columns()
        s.plate_moves = []
        z0, z1 = P['z']
        W, R = P['width'], P['corner']
        for M in P['masts']:
            xs = s.v2_xs[M['mast']]
            xa, xb = int(math.floor(xs[-1] - 4)), int(math.ceil(xs[0] + 4))
            g = {'mast': M['mast'], 'x': [xa, xb], 'deadeyes': [round(x, 1) for x in xs], 'hull_dy': []}
            for x in range(xa, xb + 1):
                e = min(x - xa, xb - x)
                inset = R - math.sqrt(max(0.0, R * R - (R - e) ** 2)) if e < R else 0.0
                w = int(round(W - inset))
                for z in range(z0, z1 + 1):
                    hd = s.outer_dy(x, z)
                    for d in range(1, w + 1):
                        s.put((x, DC.YC + hd + d, z), col['channel'], 'channel')
                g['hull_dy'].append(s.outer_dy(x, z1))
            hx, hz = M['hounds']
            for i, xd in enumerate(xs):
                xi = int(round(xd))
                yo = DC.YC + s.outer_dy(xi, z1) + W
                for dx in (-1, 0, 1):
                    for dz in (0, 1, 2):
                        if abs(dx) == 1 and dz in (0, 2):
                            continue
                        for t in range(P['deadeye']['thick']):
                            s.put((xi + dx, yo - t, z1 + 1 + dz), col['deadeye'], 'deadeye')
                for side, sy in (('S', yo), ('P', 2 * DC.YC - yo)):
                    s.anchors.append({'name': '%s-channel.deadeye-%s%d' % (M['mast'], side, i + 1), 'owner': P['subwork']['id'], 'kind': 'deadeye', 'side': side,
                                      'world': [xi, sy, z1 + 3], 'for': 'shroud %d' % (i + 1) if i < M['shrouds'] else 'backstay %d' % (i + 1 - M['shrouds'])})
                k = (xd - hx) / (z1 - hz)
                zb = P['plate_to_z']
                xb2i = int(round(xd + (zb - z1) * k))
                mv = None
                for dlt in sorted(range(-10, 11), key=abs):
                    if s.plate_clear(xi, xb2i + dlt, z0 - 1, zb):
                        mv = dlt
                        break
                if mv is None:
                    zb2 = 105
                    xe = int(round(xi + (xb2i - xi) * (zb2 - (z0 - 1)) / (zb - (z0 - 1))))
                    s.line((xi, yo, z0 - 1), (xe, DC.YC + s.outer_dy(xe, zb2) + 1, zb2), col['plate'], 'plate')
                    s.plate_moves.append({'mast': M['mast'], 'i': i + 1, 'move': None, 'ends_z': zb2})
                else:
                    xb_ = xb2i + mv
                    s.line((xi, yo, z0 - 1), (xb_, DC.YC + s.outer_dy(xb_, zb) + 1, zb), col['plate'], 'plate')
                    if mv:
                        s.plate_moves.append({'mast': M['mast'], 'i': i + 1, 'move': mv})
            s.groups.append(g)
            print(M['mast'], 'v1', [round(orig[M['mast']]['x_mast'] + orig[M['mast']]['fwd'] - i * orig[M['mast']]['spacing'], 1) for i in range(len(xs))])
            print(M['mast'], 'v2', [int(x) for x in xs], 'channel', [xa, xb])


def main():
    sys.stdout.reconfigure(encoding='utf-8')
    C = Channels2(sys.argv[1])
    C.build()
    box = C.P['subwork']['box']
    x0, y0, z0 = box['at']
    old = {}
    for x, y, z, c in np.loadtxt(sys.argv[2], delimiter=',', comments='#', dtype=np.int32, ndmin=2, encoding='utf-8'):
        old[(int(x), int(y), int(z))] = int(c)
    new = {(x - x0, y - y0, z - z0): c for (x, y, z), c in C.cells.items()}
    bad = [k for k in new if not (0 <= k[0] < box['size'][0] and 0 <= k[1] < box['size'][1] and 0 <= k[2] < box['size'][2])]
    if bad:
        raise SystemExit('有格在 channels 子作品的框外：%s' % bad[:5])
    carve = {k: v for k, v in old.items() if new.get(k) != v}
    add = {k: v for k, v in new.items() if old.get(k) != v}
    out = os.path.join(HERE, 'masks', 'channels')
    for name, d, head in (('v2_carve.vox.txt', carve, 'channels v1 要拿掉的格（自己的座標；行尾 ＝ 現在的顏色）'), ('v2_add.vox.txt', add, 'channels v2 要放的格（自己的座標）')):
        rows = sorted((x, y, z, c) for (x, y, z), c in d.items())
        open(os.path.join(out, name), 'w', encoding='utf-8', newline='\n').write('# %s（%d 格）\n' % (head, len(rows)) + '\n'.join('%d,%d,%d,%d' % r for r in rows) + '\n')
    rp = os.path.join(HERE, 'rig_points_channels.json')
    json.dump({'note': '下 deadeye 頂（給 TASK-0502 shrouds／backstays 的下端）；P ＝ y < 160、S ＝ y > 160；世界座標（v2：deadeye 排到 spar deck 砲門之間）', 'points': C.anchors},
              open(rp, 'w', encoding='utf-8', newline='\n'), ensure_ascii=False, indent=1)
    still = [(M['mast'], i + 1, x) for M in C.P['masts'] for i, x in enumerate(C.v2_xs[M['mast']]) if C.blocked(int(x), M)]
    v = {'spacing': SPACING, 'margin': MARGIN, 'xs': C.v2_xs, 'groups': C.groups, 'carve': len(carve), 'add': len(add), 'cells': len(C.cells), 'still_blocked': still, 'plate_moves': C.plate_moves}
    json.dump(v, open(os.path.join(HERE, 'verify_channels_v2.json'), 'w', encoding='utf-8'), ensure_ascii=False, indent=1)
    print(json.dumps({k: v[k] for k in ('carve', 'add', 'cells', 'still_blocked')}, ensure_ascii=False))


if __name__ == '__main__':
    main()
