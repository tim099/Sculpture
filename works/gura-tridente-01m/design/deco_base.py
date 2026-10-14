# 三叉戟號 階段五（TASK-0558）共用：「這一階段之前」的組裝件（船殼＋甲板＋梯子）⇒ 密集格子；子作品清單（自己的框、局部座標）的讀寫
#   產生程式只讀這一份 ⇒ 階段五的關聯加上去之後重跑，讀到的還是同一份（逐位元組相同）。
import os, re, subprocess, tempfile, hashlib
import numpy as np

ASM = 'gura-tridente-01m-assembly'
BASE_LINKS = '船殼,甲板-orlop,甲板-lower,甲板-middle,甲板-upper,甲板-spar,甲板-poop'   # 點名甲板 ⇒ 底下的梯子照開關一起組
NX, NY, NZ = 1100, 400, 260                                                            # 階段五的東西都在 z < 260


def export_list(work, links, extra=()):
    """links ＝ None ⇒ 不帶 links（沒有關聯的作品給 links= 會被擋）。"""
    with tempfile.TemporaryDirectory() as d:
        out = os.path.join(d, 'a.txt').replace('\\', '/')
        r = subprocess.run(['senate', 'cmd', 'sculpture', '--arg', 'op=export', '--arg', 'format=list', '--arg', 'work=' + work,
                            '--arg', 'out=' + out] + (['--arg', 'links=' + links] if links else []) + [a for kv in extra for a in ('--arg', kv)],
                           capture_output=True, text=True, encoding='utf-8', errors='replace')
        if r.returncode != 0 or not os.path.exists(out):
            raise SystemExit('匯出失敗：' + (r.stdout + r.stderr)[-800:])
        return np.loadtxt(out, delimiter=',', comments='#', dtype=np.int32, ndmin=2, encoding='utf-8')


def work_size(work):
    """作品的框（關聯翻面在這個框裡翻 —— ⛔ 不是格子的 max ＋ 1：憲法號 -anchor 格子到 y 30、框 33，用錯會差 2 格）。"""
    r = subprocess.run(['senate', 'cmd', 'sculpture', '--arg', 'op=work', '--arg', 'sub=show', '--arg', 'work=' + work],
                       capture_output=True, text=True, encoding='utf-8', errors='replace')
    v = {}
    for k in ('size_x', 'size_y', 'size_z'):
        m = re.search(r'"%s"\s*:\s*(\d+)' % k, r.stdout)
        if not m:
            raise SystemExit('讀不到 %s 的 %s' % (work, k))
        v[k] = int(m.group(1))
    return v['size_x'], v['size_y'], v['size_z']


def base_grid():
    """階段五之前的組裝件 ⇒ uint8 [x, y, z]（0 ＝ 空）。"""
    A = export_list(ASM, BASE_LINKS)
    assert A[:, 2].max() < NZ
    G = np.zeros((NX, NY, NZ), np.uint8)
    G[A[:, 0], A[:, 1], A[:, 2]] = A[:, 3]
    return G


def bbox(cells):
    """cells：{(x, y, z): 色} ⇒ (原點, 尺寸)。"""
    a = np.array(list(cells.keys()))
    lo, hi = a.min(0), a.max(0)
    return [int(v) for v in lo], [int(v) for v in hi - lo + 1]


def write_local(path, cells, origin, head):
    """清單寫成子作品自己的座標（世界 − 原點）；排序固定 ⇒ 重跑逐位元組相同。回 (格數, sha256)。"""
    os.makedirs(os.path.dirname(path), exist_ok=True)
    ox, oy, oz = origin
    with open(path, 'w', encoding='utf-8', newline='\n') as f:
        f.write(head)
        for (x, y, z) in sorted(cells):
            f.write('%d,%d,%d,%d\n' % (x - ox, y - oy, z - oz, cells[(x, y, z)]))
    return len(cells), hashlib.sha256(open(path, 'rb').read()).hexdigest()


def mirror_at_y(at_y, size_y, yc=200):
    """一舷子作品的另一舷關聯（mirror=y 在自己的框裡翻）：格 y ↔ 2·yc − y ⇒ at.y ＝ 2·yc ＋ 1 − at.y − 高。"""
    return 2 * yc + 1 - at_y - size_y


STAGE5_LINKS = '船尾陽台,後廊-S,後廊-P,船尾名牌與徽,舵,船頭-knee,船頭裝飾,船頭裝飾-鏡像,船首像,錨-S,錨-P'


def grid_of(arrays, nz=NZ):
    G = np.zeros((NX, NY, nz), np.uint8)
    for A in arrays:
        if len(A) == 0:
            continue
        assert A[:, 2].max() < nz
        G[A[:, 0], A[:, 1], A[:, 2]] = A[:, 3]
    return G


def stage6_base(hull_mark, nz=800):
    """階段六之前：船殼（讀標記 hull_mark 那一刻；標記還沒打 ⇒ 讀現在）＋ 甲板（含梯子）＋ 階段五的部件。回 (格子, 船殼清單, 船殼讀的是哪一刻)。"""
    try:
        H = export_list('gura-tridente-01m', 'none', ('mark=' + hull_mark,))
        when = hull_mark
    except SystemExit:
        H = export_list('gura-tridente-01m', 'none')
        when = 'now（標記 %s 還沒打）' % hull_mark
    decks = ','.join(l for l in BASE_LINKS.split(',') if l != '船殼')
    R = export_list(ASM, decks + ',' + STAGE5_LINKS)
    return grid_of([H, R], nz), H, when


MAST_LINKS = '主桅,前桅,後桅,艏斜桅'


def stage7_base(nz=260):
    """階段七之前：船殼（現在）＋ 甲板 ＋ 階段五 ＋ 四根桅（channels 那兩條關聯不讀 ⇒ 套用之後重跑讀到的還是同一份）。"""
    A = export_list(ASM, BASE_LINKS + ',' + STAGE5_LINKS + ',' + MAST_LINKS)
    return grid_of([A[A[:, 2] < nz]], nz)

