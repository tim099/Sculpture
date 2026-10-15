# 抄自三叉戟號 gura-tridente-01m/design/tools/check_decks.py（gura）；改：作品、層。
# 階段四讀數：每件甲板／梯子子作品的結果帳（匯出 vs 清單）、組裝件部件清單（export format=parts）裡的梯子點 vs 設計
#   用法：python -I -X utf8 tools/check_decks.py <design>
import json, os, subprocess, sys, tempfile
import numpy as np

sys.stdout.reconfigure(encoding='utf-8')
design = sys.argv[1]
sys.path.insert(0, os.path.join(design, 'tools'))
from wio import export_list, key  # noqa: E402

HULL = 'kaguya-gloire-01m'


def read(p):
    return np.loadtxt(p, delimiter=',', comments='#', dtype=np.int32, ndmin=2, encoding='utf-8')


tot = [0, 0, 0, 0]
for sub, folder in [('deck-%s' % k, 'decks') for k in ('orlop', 'lower', 'spar', 'poop', 'fcsle')] + \
                   [('ladders-%s' % k, 'ladders') for k in ('lower', 'spar', 'poop', 'fcsle')]:
    W = export_list('%s-%s' % (HULL, sub), None)
    D = read(os.path.join(design, 'masks', folder, sub.split('-', 1)[1] + '.vox.txt'))
    cw, cd = dict(zip(key(W).tolist(), W[:, 3].tolist())), dict(zip(key(D).tolist(), D[:, 3].tolist()))
    m, e = len(set(cd) - set(cw)), len(set(cw) - set(cd))
    c = sum(1 for k in set(cd) & set(cw) if cd[k] != cw[k])
    tot = [tot[0] + len(W), tot[1] + m, tot[2] + e, tot[3] + c]
    if m or e or c:
        print('✗', sub, m, e, c)
print('子作品結果帳：7 件、作品 %d 格、缺 %d、多 %d、色差 %d' % tuple(tot))
with tempfile.TemporaryDirectory() as d:
    out = os.path.join(d, 'p.json').replace('\\', '/')
    r = subprocess.run(['senate', 'cmd', 'sculpture', '--arg', 'op=export', '--arg', 'format=parts', '--arg', 'work=%s-assembly' % HULL, '--arg', 'out=' + out],
                       capture_output=True, text=True, encoding='utf-8', errors='replace')
    P = json.load(open(out, encoding='utf-8'))
want = json.load(open(os.path.join(design, 'ladder_points.json'), encoding='utf-8'))
got = {}
for l in P['links']:
    if (l.get('meta') or {}).get('kind') == 'ladders':
        for nm, xyz in (l.get('points') or {}).items():
            got[nm] = xyz
bad = 0
for nm, v in want.items():
    for pk, xyz in v['points'].items():
        g = got.get('%s.%s' % (nm, pk))
        if g is None or any(abs(g[i] - (xyz[i] + 0.5)) > 1e-6 for i in range(3)):
            bad += 1
print('梯子點（部件清單裡 kind=ladders 的關聯）：%d 座、%d 點、跟設計（格心）不同 %d' % (len({k.rsplit('.', 1)[0] for k in got}), len(got), bad))
