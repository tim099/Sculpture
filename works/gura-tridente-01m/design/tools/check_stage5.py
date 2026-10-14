# 階段五讀數：① 每件子作品的結果帳（匯出 vs 清單）② 組裝件的結果帳：階段五之前（deco_base.BASE_LINKS）＋ 每件照 placement 的 at（鏡像那幾條照 mirror=y 在框裡翻）＋ 錨 ＝ 組裝件現在（links 全開）
#   用法：python -I -X utf8 tools/check_stage5.py <design>
import json, os, sys
import numpy as np

sys.stdout.reconfigure(encoding='utf-8')
design = sys.argv[1]
sys.path.insert(0, design)
import deco_base as DB  # noqa: E402

HULL = 'gura-tridente-01m'
PARTS = [('walk', 'stern-walk', 'masks/stern/walk.vox.txt', 'stern_placement.json', [False]),
         ('gallery', 'quarter-gallery', 'masks/stern/gallery.vox.txt', 'stern_placement.json', [False, True]),
         ('deco', 'stern-deco', 'masks/stern/deco.vox.txt', 'stern_placement.json', [False]),
         ('rudder', 'rudder', 'masks/rudder/rudder.vox.txt', 'rudder_placement.json', [False]),
         ('knee', 'head-knee', 'masks/head/knee.vox.txt', 'head_placement.json', [False]),
         ('side', 'head-side', 'masks/head/side.vox.txt', 'head_placement.json', [False, True]),
         ('figurehead', 'figurehead', 'masks/head/figurehead.vox.txt', 'head_placement.json', [False]),
         ('lantern', 'lantern', 'masks/lantern/lantern.vox.txt', 'lantern_placement.json', [])]


def read(p):
    return np.loadtxt(p, delimiter=',', comments='#', dtype=np.int32, ndmin=2, encoding='utf-8')


def ledger(a, b):
    da = dict(zip(DB_key(a).tolist(), a[:, 3].tolist()))
    db = dict(zip(DB_key(b).tolist(), b[:, 3].tolist()))
    miss = len(set(db) - set(da))
    extra = len(set(da) - set(db))
    col = sum(1 for k in set(da) & set(db) if da[k] != db[k])
    return len(a), miss, extra, col


def DB_key(a):
    return (a[:, 0].astype(np.int64) * 2000 + a[:, 1]) * 2000 + a[:, 2]


tot = [0, 0, 0, 0]
expect = []
for key, tail, lst, pfile, links in PARTS:
    work = '%s-%s' % (HULL, tail)
    W = DB.export_list(work, None)
    D = read(os.path.join(design, lst))
    n, m, e, c = ledger(W, D)
    tot = [tot[0] + n, tot[1] + m, tot[2] + e, tot[3] + c]
    print('%s %-28s 作品 %6d、缺 %d、多 %d、色差 %d' % ('✓' if not (m or e or c) else '✗', work, n, m, e, c))
    pl = json.load(open(os.path.join(design, pfile), encoding='utf-8'))[key]
    sy = pl['size'][1]
    for mir in links:
        at = pl['at_mirror'] if mir else pl['at']
        P = D.copy()
        if mir:
            P[:, 1] = sy - 1 - P[:, 1]
        P[:, :3] += np.array(at)
        expect.append(P)
print('子作品結果帳：%d 件、%d 格，缺 %d、多 %d、色差 %d' % (len(PARTS), tot[0], tot[1], tot[2], tot[3]))
an = json.load(open(os.path.join(design, 'head_placement.json'), encoding='utf-8'))['anchor']
A = DB.export_list(an['work'], None)
for side, mir in (('S', False), ('P', True)):
    P = A.copy()
    if mir:
        P[:, 1] = an['size'][1] - 1 - P[:, 1]
    P[:, :3] += np.array(an[side])
    expect.append(P)
base = DB.export_list(DB.ASM, DB.BASE_LINKS)
E = np.concatenate([base] + expect)
ke = DB_key(E)
dup = len(ke) - len(np.unique(ke))
NOW = DB.export_list(DB.ASM, 'all')
n, m, e, c = ledger(NOW, E)
print('組裝件結果帳（階段五之前 %d ＋ 本階段 %d）：組裝件 %d、缺 %d、多 %d、色差 %d；設計那一份自己重疊 %d' % (len(base), len(E) - len(base), n, m, e, c, dup))
