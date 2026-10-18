# 階段二讀數（TASK-0698）：
#   ① 結果帳：每件子作品（export format=list links=none）vs 清單；船殼（mark=船尾塗裝:end）vs 階段一清單＋塗裝 —— 缺／多／色差
#   ② 重疊：作品那側每兩件之間（含船殼）重疊幾格
#   ③ 梯子四點（組裝件 export format=parts，遊戲讀的那一份）vs ladder_points.json；那一格空、腳下實心
#   用法：python -I -X utf8 tools/check_upper.py
import os, sys, json, subprocess, tempfile
import numpy as np

HERE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(HERE, 'tools'))
sys.stdout.reconfigure(encoding='utf-8')
import wio

HULL = 'apex-one-reale-01m'
SUBS = [('deck-main', 'deck'), ('apostis', 'apostis'), ('rambade', 'rambade'), ('ladders-rambade', 'ladders'), ('eperon', 'eperon'), ('stern', 'stern')]


def ledger(work_arr, design_arr):
    kw, kd = wio.key(work_arr), wio.key(design_arr)
    cw = dict(zip(kw.tolist(), work_arr[:, 3].tolist()))
    cd = dict(zip(kd.tolist(), design_arr[:, 3].tolist()))
    return len(cw), len(cd), len(set(cd) - set(cw)), len(set(cw) - set(cd)), sum(1 for k in set(cd) & set(cw) if cd[k] != cw[k]), set(cw)


sets = {}
hull_d = wio.load_lists(os.path.join(HERE, 'masks', 'hull'))
paint = np.loadtxt(os.path.join(HERE, 'masks', 'paint', 'stern.vox.txt'), delimiter=',', comments='#', dtype=np.int32, ndmin=2, encoding='utf-8')
pd = dict(zip(wio.key(paint).tolist(), paint[:, 3].tolist()))
hk = wio.key(hull_d)
hull_d = hull_d.copy()
hull_d[:, 3] = [pd.get(k, c) for k, c in zip(hk.tolist(), hull_d[:, 3].tolist())]
w = wio.export_list(HULL, '船尾塗裝:end')
n_w, n_d, mi, ex, cd, s = ledger(w, hull_d)
sets['船殼'] = s
print('① 船殼（＋船尾塗裝）：作品 %d ／ 設計 %d ⇒ 缺 %d、多 %d、色差 %d' % (n_w, n_d, mi, ex, cd))
tot = [0, 0, 0]
for suf, lst in SUBS:
    w = wio.export_list('%s-%s' % (HULL, suf), None)
    d = np.loadtxt(os.path.join(HERE, 'masks', 'upper', lst + '.vox.txt'), delimiter=',', comments='#', dtype=np.int32, ndmin=2, encoding='utf-8')
    n_w, n_d, mi, ex, cd, s = ledger(w, d)
    sets[suf] = s
    print('   %-16s 作品 %7d ／ 設計 %7d ⇒ 缺 %d、多 %d、色差 %d' % (suf, n_w, n_d, mi, ex, cd))
names = list(sets)
ov = [(a, b, len(sets[a] & sets[b])) for i, a in enumerate(names) for b in names[i + 1:]]
print('② 重疊（作品那側，兩兩）：合計 %d 格%s' % (sum(o[2] for o in ov), ''.join('；%s×%s %d' % o for o in ov if o[2])))
with tempfile.TemporaryDirectory() as dd:
    out = os.path.join(dd, 'p.json').replace('\\', '/')
    r = subprocess.run(['senate', 'cmd', 'sculpture', '--arg', 'op=export', '--arg', 'format=parts', '--arg', 'work=%s-assembly' % HULL, '--arg', 'out=' + out],
                       capture_output=True, text=True, encoding='utf-8', errors='replace')
    parts = json.load(open(out, encoding='utf-8'))
pts = json.load(open(os.path.join(HERE, 'ladder_points.json'), encoding='utf-8'))
allk = set().union(*sets.values())
found = {}
for ln in parts['links']:                                  # 每條關聯的固定點（組裝件座標）
    for nm_, at_ in (ln.get('points') or {}).items():
        found[ln['path'] + '/' + nm_] = at_
bad = 0
n = 0
for nm, p4 in pts.items():
    for k, at in p4.items():
        n += 1
        key = next((f for f in found if f.endswith('%s.%s' % (nm, k))), None)
        g = found.get(key)
        x, y, z = at
        k3 = lambda x, y, z: (x * 1000 + y) * 1000 + z
        ok = g is not None and [int(np.floor(v)) for v in g] == at and k3(x, y, z) not in allk and k3(x, y, z - 1) in allk
        bad += 0 if ok else 1
        if not ok:
            print('   ✗ %s.%s 設計 %s 遊戲那份 %s' % (nm, k, at, g))
print('③ 梯子點：%d 點、跟設計差或站不住 %d（parts 裡找到的固定點 %d 個）' % (n, bad, len(found)))
