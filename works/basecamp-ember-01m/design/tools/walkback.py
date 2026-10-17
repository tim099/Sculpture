# 第一人稱「走得到 減 走得回」—— 整艘船（kotoko draft_engine_access.py 的 reach 改成整艘、向量化）
#   走：四鄰那一柱、上 ≤ 6／下 ≤ 8 之內離腳最近的站位（同 81_fps.js fpStand；平手取高的）；頭上 7 格要空；跳不算；梯子 foot ↔ head 雙向。
#   起點：最上層那幾座梯子的 head（頂層甲板）。
#   用法：python -I -X utf8 walkback.py <組裝件> <list 匯出檔> <起點梯子作品,…> <梯子作品,…> [drop=<梯名>]
import sys, json, os
import numpy as np
from scipy.sparse import csr_matrix
from scipy.sparse.csgraph import breadth_first_order, connected_components

UP, DOWN, HEAD = 6, 8, 7
STARTZ = 0
WORKS = 'D:/Unity/Valhalla/Sculpture/works'


def main():
    sys.stdout.reconfigure(encoding='utf-8')
    asm, grid, top_works, lad_works = sys.argv[1], sys.argv[2], sys.argv[3].split(','), sys.argv[4].split(',')
    drop = [a.split('=', 1)[1] for a in sys.argv[5:] if a.startswith('drop=')]
    global UP, STARTZ
    for a in sys.argv[5:]:
        if a.startswith('up='):
            UP = int(a[3:])
        if a.startswith('startz='):
            STARTZ = int(a[7:])                              # 起點只取 head 在這個高度以上的梯子（頂層甲板）                                  # 嚴格版：只算這麼高以內的台階（3 ＝ 一般樓梯一階）
    A = np.loadtxt(grid, delimiter=',', comments='#', dtype=np.int32, ndmin=2, encoding='utf-8')
    A = A[(A[:, 0] >= 0) & (A[:, 1] >= 0) & (A[:, 2] >= 0)]
    mx = A[:, :3].max(0) + HEAD + 3
    S = np.zeros(tuple(mx), bool)
    S[A[:, 0], A[:, 1], A[:, 2]] = True
    # 站位：腳下實心、自己那格與頭上 HEAD−1 格空
    st = np.zeros_like(S)
    st[:, :, 1:] = S[:, :, :-1] & ~S[:, :, 1:]
    for h in range(1, HEAD):
        st[:, :, 1:-h] &= ~S[:, :, 1 + h:]
    st[:, :, -HEAD:] = False
    idx = -np.ones(S.shape, np.int64)
    P = np.argwhere(st)
    n = len(P)
    idx[tuple(P.T)] = np.arange(n)
    # 邊：每個方向、照偏好順序（|o| 小的先、平手高的先）找第一個站位
    offs = sorted(range(-DOWN, UP + 1), key=lambda o: (abs(o), -o))
    rows, cols = [], []
    for dx, dy in ((1, 0), (-1, 0), (0, 1), (0, -1)):
        nx, ny = P[:, 0] + dx, P[:, 1] + dy
        ok = (nx >= 0) & (nx < S.shape[0]) & (ny >= 0) & (ny < S.shape[1])
        todo = np.nonzero(ok)[0]
        for o in offs:
            if not len(todo):
                break
            z = P[todo, 2] + o
            zin = (z >= 0) & (z < S.shape[2])
            t = todo[zin]
            j = idx[nx[t], ny[t], z[zin]]
            hit = j >= 0
            rows.append(t[hit]); cols.append(j[hit])
            done = np.zeros(n, bool); done[t[hit]] = True
            todo = todo[~done[todo]]
    # 梯子
    def pts(work):
        an = json.load(open(os.path.join(WORKS, work, 'anchors.json'), encoding='utf-8'))['anchors']
        d = {}
        for a in an:
            if '.' in a['name'] and not a['name'].startswith('manrope'):
                k, p = a['name'].rsplit('.', 1)
                d.setdefault(k, {})[p] = a['at']
        return d

    def snap(p):
        x, y, z = p
        best = None
        for ddz in sorted(range(-3, 4), key=abs):
            for ddx in (0, 1, -1, 2, -2):
                for ddy in (0, 1, -1, 2, -2):
                    q = (x + ddx, y + ddy, z + ddz)
                    if all(0 <= q[i] < S.shape[i] for i in range(3)) and idx[q] >= 0:
                        c = abs(ddx) + abs(ddy) + abs(ddz)
                        if best is None or c < best[0]:
                            best = (c, int(idx[q]), q)
        return best
    ladders, snaps = {}, []
    for w in lad_works:
        for k, v in pts(w).items():
            if k in drop:
                continue
            a, b = snap(v['foot']), snap(v['head'])
            ladders[k] = (w, v, a, b)
            if a is None or b is None:
                snaps.append('%s：%s 找不到站位' % (k, 'foot' if a is None else 'head'))
                continue
            if a[0] or b[0]:
                snaps.append('%s：foot 挪 %d、head 挪 %d' % (k, a[0], b[0]))
            rows += [np.array([a[1], b[1]])]; cols += [np.array([b[1], a[1]])]
    r = np.concatenate(rows); c = np.concatenate(cols)
    M = csr_matrix((np.ones(len(r), np.int8), (r, c)), shape=(n, n))
    starts = []
    for w in top_works:
        for k, v in pts(w).items():
            if k in ladders and ladders[k][3] and ladders[k][3][2][2] >= STARTZ:
                starts.append(ladders[k][3][1])
    fwd = np.zeros(n, bool); back = np.zeros(n, bool)
    for s in starts:
        fwd[breadth_first_order(M, s, directed=True, return_predecessors=False)] = True
        back[breadth_first_order(M.T.tocsr(), s, directed=True, return_predecessors=False)] = True
    trap = fwd & ~back
    for a in sys.argv[5:]:
        if a.startswith('path='):                          # 從第一個起點走到這一格的路（每段只印 z 變了的地方）
            tgt = snap([int(v) for v in a[5:].split(',')])
            order, pred = breadth_first_order(M, starts[0], directed=True, return_predecessors=True)
            if tgt is None or pred[tgt[1]] < 0 and tgt[1] != starts[0]:
                print('path：走不到', tgt)
            else:
                seq, v = [], tgt[1]
                while v >= 0:
                    seq.append(tuple(int(t) for t in P[v])); v = pred[v]
                seq.reverse()
                keep = [seq[0]] + [seq[i] for i in range(1, len(seq)) if seq[i][2] != seq[i - 1][2] or abs(seq[i][0] - seq[i - 1][0]) + abs(seq[i][1] - seq[i - 1][1]) > 1] + [seq[-1]]
                print('path', len(seq), 'steps：', keep)
        if a.startswith('back='):                          # 從這一格走回起點的路
            tgt = snap([int(v) for v in a[5:].split(',')])
            order, pred = breadth_first_order(M.T.tocsr(), starts[0], directed=True, return_predecessors=True)
            seq, v = [], tgt[1]
            while v >= 0:
                seq.append(tuple(int(t) for t in P[v])); v = pred[v]
            keep = [seq[0]] + [seq[i] for i in range(1, len(seq)) if seq[i][2] != seq[i - 1][2] or abs(seq[i][0] - seq[i - 1][0]) + abs(seq[i][1] - seq[i - 1][1]) > 1] + [seq[-1]]
            print('back', len(seq), 'steps：', keep)
    out = {'asm': asm, 'stand_cells': int(n), 'ladders': len(ladders), 'starts': len(starts), 'snap_notes': snaps,
           'reachable': int(fwd.sum()), 'back': int(back.sum()), 'reachable_not_back': int(trap.sum()), 'drop': drop, 'up': UP}
    bands = [0, 40, 58, 80, 103, 10 ** 6]
    out['by_z'] = {'%d-%d' % (bands[i], bands[i + 1]): [int((fwd & (P[:, 2] >= bands[i]) & (P[:, 2] < bands[i + 1])).sum()),
                                                        int((trap & (P[:, 2] >= bands[i]) & (P[:, 2] < bands[i + 1])).sum())] for i in range(len(bands) - 1)}
    # 回不來的分群（同一張圖的無向連通）
    ti = np.nonzero(trap)[0]
    if len(ti):
        sub = M[ti][:, ti]
        k, lab = connected_components(sub, directed=False)
        groups = []
        for g in range(k):
            q = P[ti[lab == g]]
            groups.append({'cells': int(len(q)), 'x': [int(q[:, 0].min()), int(q[:, 0].max())], 'y': [int(q[:, 1].min()), int(q[:, 1].max())],
                           'z': [int(q[:, 2].min()), int(q[:, 2].max())]})
        groups.sort(key=lambda g: -g['cells'])
        out['groups'] = len(groups)
        out['top_groups'] = groups[:15]
    print(json.dumps(out, ensure_ascii=False, indent=1))


if __name__ == '__main__':
    main()
