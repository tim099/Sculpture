# 拿破崙號 共用：「這一階段之前」的船（從各階段的清單組，那幾份清單跟作品逐格相同 —— 各階段結果帳證過）⇒ 密集格子；子作品清單的寫法
#   write_local 抄自三叉戟號 gura-tridente-01m/design/deco_base.py（gura）。
import os, hashlib
import numpy as np

NX, NY = 1200, 400


def _read(p):
    return np.loadtxt(p, delimiter=',', comments='#', dtype=np.int32, ndmin=2, encoding='utf-8')


def _folder(design, sub):
    d = os.path.join(design, 'masks', sub)
    out = []
    for f in sorted(os.listdir(d)):
        if f.endswith('.vox.txt'):
            out.append(_read(os.path.join(d, f)))
    return np.concatenate(out) if out else np.zeros((0, 4), np.int32)


def hull_now(design):
    """船殼現在 ＝ 船殼清單 − 砲門刻 ＋ 換色（階段三結果帳證過 ＝ 作品 mark 砲門v2:end）。"""
    d = {}
    for x, y, z, c in _folder(design, 'hull').tolist():
        d[(x, y, z)] = c
    for x, y, z, c in _read(os.path.join(design, 'masks', 'ports', 'carve.vox.txt')).tolist():
        d.pop((x, y, z))
    for x, y, z, c in _read(os.path.join(design, 'masks', 'ports', 'paint.vox.txt')).tolist():
        d[(x, y, z)] = c
    return np.array([[x, y, z, c] for (x, y, z), c in sorted(d.items())], np.int32)


def stage_base(design, subs=('decks', 'ladders', 'deco'), nz=260):
    """回 (格子 uint8 [x, y, z]、船殼清單)：船殼現在 ＋ 指定那幾個資料夾的清單（世界座標）。"""
    H = hull_now(design)
    G = np.zeros((NX, NY, nz), np.uint8)
    for A in [H] + [_folder(design, s) for s in subs]:
        if len(A) == 0:
            continue
        A = A[A[:, 2] < nz]
        G[A[:, 0], A[:, 1], A[:, 2]] = A[:, 3]
    return G, H


def write_local(path, cells, origin, head):
    """清單寫成子作品自己的座標（世界 − 原點）；排序固定 ⇒ 重跑逐位元組相同。回 (格數, sha256)。"""
    os.makedirs(os.path.dirname(path), exist_ok=True)
    ox, oy, oz = origin
    with open(path, 'w', encoding='utf-8', newline='\n') as f:
        f.write(head)
        for (x, y, z) in sorted(cells):
            f.write('%d,%d,%d,%d\n' % (x - ox, y - oy, z - oz, cells[(x, y, z)]))
    return len(cells), hashlib.sha256(open(path, 'rb').read()).hexdigest()


def bbox(cells):
    """cells：{(x, y, z): 色} ⇒ (原點, 尺寸)。（抄三叉戟號 deco_base.bbox）"""
    a = np.array(list(cells.keys()))
    lo, hi = a.min(0), a.max(0)
    return [int(v) for v in lo], [int(v) for v in hi - lo + 1]


def mirror_at_y(at_y, size_y, yc=200):
    """一舷子作品的另一舷關聯（mirror=y 在自己的框裡翻）：格 y ↔ 2·yc − y ⇒ at.y ＝ 2·yc ＋ 1 − at.y − 高。（抄三叉戟號 deco_base.mirror_at_y）"""
    return 2 * yc + 1 - at_y - size_y
