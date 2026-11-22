# 出處：basecamp-ember-01m/design/tools/walkback.py（照抄）：第一人稱「走得到 減 走得回」整艘船檢查
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
            STARTZ = int(a[7:])
    A = np.loadtxt(grid, delimiter=',', comments='#', dtype=np.int32, ndmin=2, encoding='utf-8')
    A = A[(A[:, 0] >= 0) & (A[:, 1] >= 0) & (A[:, 2] >= 0)]
    mx = A[:, :3].max(0) + HEAD + 3
    S = np.zeros(tuple(mx), bool)
    S[A[:, 0], A[:, 1], A[:, 2]] = True
    st = np.zeros_like(S)
    st[:, :, 1:] = S[:, :, :-1] & ~S[:, :, 1:]
    for h in range(1, HEAD):
        st[:, :, 1:-h] &= ~S[:, :, 1 + h:]
    st[:, :, -HEAD:] = False
    idx = -np.ones(S.shape, np.int64)
    P = np.argwhere(st)
    n = len(P)
    idx[tuple(P.T)] = np.arange(n)
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
    MT = M.T.tocsr()
    for s in starts:
        back[breadth_first_order(MT, s, directed=True, return_predecessors=False)] = True
    stuck = P[fwd & ~back]
    print('整艘船第一人稱（%s；up=%d down=%d head=%d%s）' % (asm, UP, DOWN, HEAD, ' drop=' + ','.join(drop) if drop else ''))
    print('  梯子 %d 座%s' % (len(ladders), ('（' + '；'.join(snaps) + '）') if snaps else '（foot/head 全對準站位）'))
    print('  起點：%d 處；可達 %d 格、能回 %d 格、**走不回來 %d 格**' % (len(starts), int(fwd.sum()), int((fwd & back).sum()), len(stuck)))
    if len(stuck):
        L = csr_matrix(M[fwd & ~back][:, fwd & ~back])
        _, lab = connected_components(L, directed=False, connection='weak')
        for g in np.unique(lab):
            Q = stuck[lab == g]
            print('  · 困區 %d（%d 格）：x %d..%d  y %d..%d  z %d..%d' % (
                int(g) + 1, len(Q), int(Q[:, 0].min()), int(Q[:, 0].max()),
                int(Q[:, 1].min()), int(Q[:, 1].max()), int(Q[:, 2].min()), int(Q[:, 2].max())))


if __name__ == '__main__':
    main()
