# 階段六讀數：① 桅、艏斜桅、帆桁子作品的結果帳（匯出 vs 清單）② 船殼：現在 ＝ 標記 艏斜桅開口:begin − 刻除清單 ③ 組裝件 ＝ 階段六之前 − 刻 ＋ 四根桅
#   ④ 遊戲讀的那一份（組裝件 export format=parts）：帆桁模型的固定點 vs 產生程式算的（verify_masts.json yard_points）、meta vs placement、state
#   用法：python -I -X utf8 tools/check_stage6.py <design> [--parts-only]
import json, os, subprocess, sys, tempfile
import numpy as np

sys.stdout.reconfigure(encoding='utf-8')
design = sys.argv[1]
sys.path.insert(0, design)
import deco_base as DB  # noqa: E402

HULL = 'gura-tridente-01m'


def read(p):
    return np.loadtxt(p, delimiter=',', comments='#', dtype=np.int32, ndmin=2, encoding='utf-8')


def key(a):
    return (a[:, 0].astype(np.int64) * 2000 + a[:, 1]) * 2000 + a[:, 2]


def ledger(a, b):
    da = dict(zip(key(a).tolist(), a[:, 3].tolist()))
    db = dict(zip(key(b).tolist(), b[:, 3].tolist()))
    return len(a), len(set(db) - set(da)), len(set(da) - set(db)), sum(1 for k in set(da) & set(db) if da[k] != db[k])


def parts_export():
    with tempfile.TemporaryDirectory() as d:
        out = os.path.join(d, 'p.json').replace('\\', '/')
        r = subprocess.run(['senate', 'cmd', 'sculpture', '--arg', 'op=export', '--arg', 'format=parts', '--arg', 'work=' + DB.ASM, '--arg', 'out=' + out],
                           capture_output=True, text=True, encoding='utf-8', errors='replace')
        if r.returncode != 0:
            raise SystemExit(r.stdout[-800:])
        return json.load(open(out, encoding='utf-8'))


pl = json.load(open(os.path.join(design, 'masts_placement.json'), encoding='utf-8'))
V = json.load(open(os.path.join(design, 'verify_masts.json'), encoding='utf-8'))
if '--parts-only' not in sys.argv:
    tot = [0, 0, 0, 0]
    rows = [(m['work'], os.path.join('masks', 'masts', k + '.vox.txt')) for k, m in pl['masts'].items()] + \
           [(y['work'], os.path.join('masks', 'yards', y['name'] + '.vox.txt')) for y in pl['yards']]
    bad = 0
    for work, lst in rows:
        n, m, e, c = ledger(DB.export_list(work, None), read(os.path.join(design, lst)))
        tot = [tot[0] + n, tot[1] + m, tot[2] + e, tot[3] + c]
        if m or e or c:
            bad += 1
            print('✗', work, m, e, c)
    print('子作品結果帳：%d 件（桅 4、帆桁 %d）、%d 格，缺 %d、多 %d、色差 %d' % (len(rows), len(pl['yards']), tot[0], tot[1], tot[2], tot[3]))
    carve = read(os.path.join(design, 'masks', 'masts', 'hull_carve.vox.txt'))
    H0 = DB.export_list(HULL, 'none', ('mark=艏斜桅開口:begin',))
    H1 = DB.export_list(HULL, 'none')
    keep = ~np.isin(key(H0), key(carve))
    print('船殼結果帳：現在 vs（艏斜桅開口:begin %d − 刻 %d）：%s、缺 %d、多 %d、色差 %d；刻之前那幾格的顏色對得上 %d／%d' % (
        (len(H0), len(carve)) + ledger(H1, H0[keep]) + (int(sum(1 for k, c in zip(key(carve).tolist(), carve[:, 3].tolist())
                                                                if dict(zip(key(H0).tolist(), H0[:, 3].tolist())).get(k) == c)), len(carve))))
    decks = ','.join(l for l in DB.BASE_LINKS.split(',') if l != '船殼')
    R5 = DB.export_list(DB.ASM, decks + ',' + DB.STAGE5_LINKS)
    M = [DB.export_list(m['work'], None) for m in pl['masts'].values()]
    E = np.concatenate([H0[keep], R5] + M)
    dup = len(E) - len(np.unique(key(E)))
    NOW = DB.export_list(DB.ASM, 'all')
    print('組裝件結果帳：設計 %d（船殼 %d ＋ 甲板與階段五 %d ＋ 桅 %d）↔ 組裝件 %d、缺 %d、多 %d、色差 %d；設計那一份自己重疊 %d' % (
        (len(E), int(keep.sum()), len(R5), sum(len(m) for m in M)) + ledger(NOW, E) + (dup,)))
P = parts_export()
by = {m['path']: m for m in P['models']}
worst, n, metabad, notok = 0.0, 0, 0, 0
for y in pl['yards']:
    link = pl['masts'][y['parent'].split('-')[-1] if 'mast-' in y['parent'] else 'bowsprit']['link']
    path = '%s/%s' % (link, y['model']['name'])
    m = by.get(path)
    if m is None:
        print('✗ 找不到模型', path)
        notok += 1
        continue
    if m.get('state') != 'ok':
        notok += 1
    if m.get('meta') != y['model']['meta']:
        metabad += 1
        print('✗ meta', path, m.get('meta'))
    for nm, xyz in V['yard_points'][y['name']].items():
        g = m['points'].get(nm)
        if g is None:
            worst = float('inf')
            print('✗ 少點', path, nm)
            continue
        worst = max(worst, max(abs(g[i] - xyz[i]) for i in range(3)))
        n += 1
print('帆桁模型（export format=parts，遊戲讀的那一份）：%d 根、%d 點、跟產生程式算的最大差 %.4f 格；meta 不同 %d；state 不是 ok %d；全部模型 %d' % (
    len(pl['yards']), n, worst, metabad, notok, len(P['models'])))
