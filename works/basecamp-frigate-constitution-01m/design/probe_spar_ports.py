"""
階段二十九 動刀前的量測（只讀）：每個 spar deck 砲門（source_ports_spar.json）在作品裡的
① 甲板面（spar deck 子作品，第一個空格的 z）② 舷牆的組成（中線那一欄：每一列從外到內的顏色）與頂（cap rail）
③ 開口範圍裡「不是船殼」的格（組裝件 − 船殼本體），照 y 分舷內／舷外，列顏色 ⇒ 誰擋在砲門上（pin rails、channels…）。
用法：python -I probe_spar_ports.py <組裝件清單.txt> <船殼清單.txt>
"""
import json, os, sys
from collections import Counter, defaultdict
import numpy as np

HERE = os.path.dirname(os.path.abspath(__file__))
YC = 160


def load(path):
    return np.loadtxt(path, delimiter=',', comments='#', dtype=np.int32, ndmin=2, encoding='utf-8')


def main():
    sys.stdout.reconfigure(encoding='utf-8')
    A, H = load(sys.argv[1]), load(sys.argv[2])
    hull = {(int(x), int(y), int(z)): int(c) for x, y, z, c in H if z >= 95}
    asm = {(int(x), int(y), int(z)): int(c) for x, y, z, c in A if z >= 95}
    ports = json.load(open(os.path.join(HERE, 'source_ports_spar.json'), encoding='utf-8'))['ports']
    rep = []
    for p in ports:
        xa, xb = int(np.ceil(p['X_aft'] - 0.5)), int(np.floor(p['X_fwd'] - 0.5))
        za, zb = int(np.ceil(p['sill'] - 0.5)), int(np.floor(p['lintel'] - 0.5))
        xm = (xa + xb) // 2
        row = {'n': p['n'], 'x': [xa, xb], 'z': [za, zb]}
        for side, nm in ((1, 'S'), (-1, 'P')):
            # 舷牆：中線那一欄，z 由下往上，從外往內的顏色
            col = {}
            top = None
            for z in range(100, 140):
                ys = sorted([y for y in range(0, 320) if (xm, y, z) in hull and (y - YC) * side > 20], key=lambda y: -(y - YC) * side)
                if ys:
                    col[z] = (ys[0], ys[-1], ''.join('%d ' % hull[(xm, y, z)] for y in ys).strip())
                    top = z
            # 甲板面：中線那一欄最高的實心（< 舷牆）＋1
            deck = max([z for (x, y, z) in asm if x == xm and y == YC and z < 120] or [0]) + 1
            outer = max(col[z][0] for z in col if za <= z <= zb) if any(za <= z <= zb for z in col) else None
            inner = min(col[z][1] for z in col if za <= z <= zb) if any(za <= z <= zb for z in col) else None
            # 開口的體積：x 範圍 × z 範圍 × 從舷牆外面 4 格到裡面 6 格
            others = Counter()
            where = defaultdict(list)
            if outer is not None:
                lo, hi = sorted([inner - 6 * side, outer + 4 * side])
                for x in range(xa, xb + 1):
                    for z in range(za, zb + 1):
                        for y in range(lo, hi + 1):
                            k = (x, y, z)
                            if k in asm and k not in hull:
                                io = 'out' if (y - outer) * side > 0 else 'in'
                                others[(io, asm[k])] += 1
                                where[(io, asm[k])].append(k)
            row[nm] = {'deck': deck, 'wall_top': top, 'wall_y': [outer, inner],
                       'wall_mid': {z: col[z][2] for z in (za, (za + zb) // 2, zb, top) if z in col},
                       'others': {'%s:%d' % k: v for k, v in others.items()},
                       'others_box': {'%s:%d' % k: [list(map(int, np.min(v, 0))), list(map(int, np.max(v, 0)))] for k, v in where.items()}}
        rep.append(row)
        print(json.dumps(row, ensure_ascii=False))
    json.dump(rep, open(os.path.join(HERE, 'probe_spar_ports.json'), 'w', encoding='utf-8'), ensure_ascii=False, indent=1)


if __name__ == '__main__':
    main()
