# 拿破崙號 階段十四（Tim 2026-10-16：「照計畫先做司爐艙：……機艙鋪地板標 level -1……」）：機艙的鐵地板（floor plates）—— 自己寫的
#   史料（研究 agent 2026-10-16，推、信心中）：機艙與司爐艙的地板是鐵板（部分格柵），蓋在艙底水上、可以掀開。
#   板面 z FLOOR（站在 FLOOR＋1 ＝ 鍋爐底 z 13）；x 330–650（faux-pont 沒鋪的那一段）、船殼裡面（每個 (x, z) 從中線往兩舷走到第一格實心）、
#   那一欄船底比板面低的地方才鋪；已經有格的不放（鍋爐座、主機底座、軸承座、主桅、梯子）。
#   排水孔：(x, y) 都是 10 的倍數那一格不鋪 ⇒ 板底下的艙底跟機艙通著（不然整片板底下是封死的空腔）；仍被封住的小空腔 ⇒ 照實報、填進板（同 draft_engine 封腔）。
#   現況 ＝ 組裝件 links=all，藏 `甲板-lower/梯子-機艙`（梯子之後照新地板重算）、`甲板-engine`（本件）。
#   輸出：masks/engine_floor/floor.vox.txt（世界座標，at 0,0,0）、verify_engine_floor.json；deck meta 的 floor 折線寫在 verify 裡
#   用法：python -I -X utf8 draft_engine_floor.py <design>
import sys, os, json, hashlib
import numpy as np
from scipy import ndimage

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import mio

NX, NY, NZ = 1200, 400, 120
YC = 200
X0, X1 = 330, 650
FLOOR = 12
PLATE = 73
HOLE = 10


def main():
    sys.stdout.reconfigure(encoding='utf-8')
    D = os.path.abspath(sys.argv[1])
    hide = '甲板-lower/梯子-機艙,甲板-engine'
    try:
        A = mio.export_list(mio.ASM, 'all', ('hide_links=' + hide,))
    except SystemExit:
        A = mio.export_list(mio.ASM, 'all', ('hide_links=甲板-lower/梯子-機艙',))
    A = A[A[:, 2] < NZ]
    occ = np.zeros((NX, NY, NZ), bool)
    occ[A[:, 0], A[:, 1], A[:, 2]] = True
    cells = {}
    holes = 0
    for x in range(X0, X1 + 1):
        z = FLOOR
        for y in range(116, 285):
            if occ[x, y, z]:
                continue
            col = np.nonzero(occ[x, y, :FLOOR])[0]
            if not len(col):
                continue                                              # 底下沒有船底（船外）
            # 船殼裡面：z FLOOR 這一層往兩舷都還碰得到實心（船殼牆）；外面那一片是船外
            if not (occ[x, y:, z].any() and occ[x, :y + 1, z].any()):
                continue
            if x % HOLE == 0 and y % HOLE == 0:
                holes += 1
                continue
            cells[(x, y, z)] = PLATE
    # 只留跟中線那一片連著的（兩舷船殼牆裡的縫不算）
    M = np.zeros((X1 - X0 + 1, NY), bool)
    for (x, y, z) in cells:
        M[x - X0, y] = True
    lab, n = ndimage.label(M)
    sizes = ndimage.sum(M, lab, range(1, n + 1))
    keep = 1 + int(np.argmax(sizes)) if n else 0
    dropped = 0
    for (x, y, z) in list(cells):
        if lab[x - X0, y] != keep:
            del cells[(x, y, z)]
            dropped += 1
    # 封住的空腔：板放上去之後新多出來的
    sl = slice(X0 - 5, X1 + 6)
    U0 = occ[sl].copy(); U1 = U0.copy()
    for (x, y, z) in cells:
        U1[x - (X0 - 5), y, z] = True
    newcav = (ndimage.binary_fill_holes(U1) & ~U1) & ~(ndimage.binary_fill_holes(U0) & ~U0)
    labc, nc = ndimage.label(newcav)
    sealed = []
    for i in range(1, nc + 1):
        q = np.argwhere(labc == i)
        sealed.append([int(q[0][0]) + X0 - 5, int(q[0][1]), int(q[0][2]), int(len(q))])
        if len(q) <= 200:
            for (x, y, z) in q:
                cells[(int(x) + X0 - 5, int(y), int(z))] = PLATE
    big = [s for s in sealed if s[3] > 200]
    xs = sorted({x for (x, y, z) in cells})
    R = {'cells': len(cells), 'holes': holes, 'dropped_not_connected': dropped, 'sealed_small': [s for s in sealed if s[3] <= 200], 'big_cavities': big,
         'overlap_base': sum(1 for k in cells if occ[k]), 'asym': sum(1 for (x, y, z) in cells if (x, 400 - y, z) not in cells),
         'x': [xs[0], xs[-1]] if xs else None,
         'deck_meta': {'kind': 'deck', 'deck': 'engine', 'level': -1, 'name': '機艙', 'floor': '%d:%d,%d:%d' % (xs[0], FLOOR + 1, xs[-1], FLOOR + 1) if xs else '', 'thick': 1}}
    od = os.path.join(D, 'masks', 'engine_floor')
    os.makedirs(od, exist_ok=True)
    p = os.path.join(od, 'floor.vox.txt')
    with open(p, 'w', encoding='utf-8', newline='\n') as f:
        f.write('# 拿破崙號 機艙鐵地板（板面 z %d；世界座標，at 0,0,0）\n' % FLOOR)
        for k in sorted(cells):
            f.write('%d,%d,%d,%d\n' % (k + (cells[k],)))
    R['sha256'] = hashlib.sha256(open(p, 'rb').read()).hexdigest()
    with open(os.path.join(D, 'verify_engine_floor.json'), 'w', encoding='utf-8', newline='\n') as f:
        json.dump(R, f, ensure_ascii=False, indent=1)
    print(json.dumps(R, ensure_ascii=False))


if __name__ == '__main__':
    main()
