# 中期、晚期拜占庭的「十字形平面」教堂（cross-in-square）：一個參數表 ⇒ 一座（或並排幾座）教堂的量體。用 byz.py 的形狀。
#   座標（公尺）：x ＝ 從西面看左 → 右（北 → 南）、y ＝ 西 → 東（y 0 ＝ 正面）、z 往上。每一個量體都可以不給（不給 ⇒ 不蓋）。
#   參數表的欄（全是公尺）：
#     naos: {x: [x0, x1], y: [y0, y1], z: 角落四格的簷口高, arm_w: 十字臂寬, arm_z: 十字臂的簷口高, roof: 'gable'|'barrel', rise}
#     dome: {cx, cy, r: 鼓座外接圓半徑, n: 鼓座面數, z0: 鼓座底, h: 鼓座高, win: 窗數, rise: 穹頂高, ribs: 鉛皮接縫數}
#     apses: [{cx, r, facets, z, win: 窗數}]（貼在 naos 東牆 y1；中間大、兩側小）
#     bays: [{x: [], y: [], z, roof: 'shed'|'gable'|'flat'|'dome', high: '+x'…, dome: {…}}]（前廊、外前廊、側堂、迴廊…：長方的一塊）
#     door: [{x, w, h}]（西牆 y 0 的門；也可以 {y: , side: 'x0'|'x1'} 開在側牆）
#   回傳：屋頂件、主體件各自 add 進 M。
import math
import byz
from byz import BANDED, BRICK, LEAD, TILE, MARBLE, GOLD, STONE


def _dome(M, D, roof_lay, body_lay, wall_mat):
    cx, cy, r, n, z0, h = D['cx'], D['cy'], D['r'], D.get('n', 8), D['z0'], D['h']
    M.add(M.ngon(cx, cy, r, n, z0, z0 + h, rot=D.get('rot', 90 + 180.0 / n)), wall_mat, body_lay)
    rr = r * math.cos(math.pi / n)
    M.add(M.dome(cx, cy, z0 + h, rr, D.get('rise', rr), ribs=D.get('ribs', D.get('win', n))), LEAD, roof_lay)
    nw = D.get('win', n)
    if nw:
        ww = min(0.9, 2 * rr * math.sin(math.pi / nw) * 0.45)
        M.win(M.ring_windows(cx, cy, rr - 1.2, r + 0.6, z0 + 0.6, z0 + h - 0.4, [D.get('rot', 90 + 180.0 / n) + 360.0 * (k + 0.5) / nw for k in range(nw)], ww / 2))
    if D.get('cross'):
        top = z0 + h + D.get('rise', rr)
        t = max(0.15, M.mpv * 0.51)                  # 十字的半粗：至少一格（0.4 m／格時 0.15 會整根落空）
        M.add(M.box(cx - t, cx + t, cy - t, cy + t, top - 0.4, top + 2.0), GOLD, roof_lay)
        M.add(M.box(cx - t, cx + t, cy - 0.6, cy + 0.6, top + 1.2, top + 1.2 + max(0.3, M.mpv)), GOLD, roof_lay)


def _roof(M, x0, x1, y0, y1, z, kind, rise, axis, lay, mat=TILE, high='+x'):
    if kind == 'gable':
        M.add(M.gable(x0, x1, y0, y1, z, rise, axis), mat, lay)
    elif kind == 'barrel':
        M.add(M.barrel(x0, x1, y0, y1, z, axis, rise), mat, lay)
    elif kind == 'shed':
        M.add(M.shed(x0, x1, y0, y1, z, z + rise, high), mat, lay)
    elif kind == 'flat':
        M.add(M.box(x0, x1, y0, y1, z, z + 0.4), mat, lay)
    elif kind == 'hip':
        M.add(M.hip(x0, x1, y0, y1, z, rise, 0.45), mat, lay)


def cross_in_square(M, P, body=1, roof=2, wall=BANDED):
    N = P.get('naos')
    if N:
        (x0, x1), (y0, y1) = N['x'], N['y']
        M.add(M.box(x0, x1, y0, y1, 0, N['z']), wall, body)
        cx, cy = (x0 + x1) / 2, (y0 + y1) / 2
        aw = N['arm_w'] / 2
        # 十字臂：比角落高，兩條（南北、東西）各自的山牆或筒形屋頂；角落四格平頂鋪瓦
        M.add(M.box(x0, x1, cy - aw, cy + aw, 0, N['arm_z']), wall, body)
        M.add(M.box(cx - aw, cx + aw, y0, y1, 0, N['arm_z']), wall, body)
        rm = N.get('roof_mat', TILE)
        _roof(M, x0, x1, y0, y1, N['z'], 'flat', 0, 'y', roof, rm)
        _roof(M, x0, x1, cy - aw, cy + aw, N['arm_z'], N.get('roof', 'gable'), N.get('rise', aw * 0.5), 'x', roof, rm)
        _roof(M, cx - aw, cx + aw, y0, y1, N['arm_z'], N.get('roof', 'gable'), N.get('rise', aw * 0.5), 'y', roof, rm)
        # 十字臂盡頭的三連窗（南北兩面）
        for side, xx in (('x0', x0), ('x1', x1)):
            for k in (-1, 0, 1):
                M.win(M.arch_open(xx, cy + k * aw * 0.55, N['arm_z'] - 3.6, N['arm_z'] - 0.9, min(1.0, aw * 0.4), normal='x', depth=2.4))
        # 角落格的窗
        for xx in (x0, x1):
            for yy in (y0 + (cy - aw - y0) / 2, y1 - (y1 - cy - aw) / 2):
                if N['z'] > 4.5:
                    M.win(M.arch_open(xx, yy, N['z'] - 3.2, N['z'] - 1.0, 0.8, normal='x', depth=2.4))
    for D in P.get('domes', []):
        _dome(M, D, roof, body, wall)
    for A in P.get('apses', []):
        ay = A.get('y', N['y'][1] if N else 0)
        M.add(M.apse(A['cx'], ay - 0.2, A['r'], A['facets'], 0, A['z']), wall, body)
        M.add(M.semidome(A['cx'], ay - 0.2, A['z'], A['r'] * math.cos(math.pi / (2 * A['facets'])) * 0.98, '+y'), A.get('roof_mat', TILE), roof)
        nw = A.get('win', 0)
        if nw:
            angs = [90 + (k - (nw - 1) / 2) * (180.0 / (A['facets'])) for k in range(nw)]
            M.win(M.ring_windows(A['cx'], ay, A['r'] - 1.4, A['r'] + 0.6, A.get('win_z0', A['z'] - 4.2), A['z'] - 0.8, angs, A.get('win_w', 0.7) / 2))
    for B in P.get('bays', []):
        (x0, x1), (y0, y1) = B['x'], B['y']
        M.add(M.box(x0, x1, y0, y1, 0, B['z']), B.get('mat', wall), body)
        if B.get('roof', 'shed') != 'none':
            _roof(M, x0, x1, y0, y1, B['z'], B.get('roof', 'shed'), B.get('rise', 1.2), B.get('axis', 'x'), roof, B.get('roof_mat', TILE), B.get('high', '+y'))
        for D in B.get('domes', []):
            _dome(M, D, roof, body, wall)
        for xc in B.get('arcade_x', []):          # 西面的拱廊或窗（外前廊）
            M.win(M.arch_open(xc, y0, B.get('arc_z0', 1.0), B.get('arc_z1', B['z'] - 1.0), B.get('arc_w', 1.6), normal='y', depth=2.4))
    for d in P.get('door', []):
        if 'side' in d:
            xx = P['naos']['x'][0] if d['side'] == 'x0' else P['naos']['x'][1]
            M.door(M.arch_open(xx, d['y'], 0, d['h'], d['w'], normal='x', depth=3.0))
        else:
            M.door(M.arch_open(d['x'], d.get('y', 0), 0, d['h'], d['w'], normal='y', depth=3.0))
