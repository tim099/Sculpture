# 拿破崙號 階段十三讀數（自己寫的；只讀引擎的匯出）：
#   ① 組裝件結果帳：之前那一份（--before <list>）＋ 梯子 − 圍欄 ↔ 現在（links=all），缺 0、多 0、色差 0
#   ② parts：梯子關聯 meta kind=ladders、24 個固定點跟 engine_access_points.json 差 0
#   ③ 第一人稱連通：照現在的作品重算（draft_engine_access.reach）—— 掉得進去、回不來 0
#   用法：python -I -X utf8 tools/check_engine_access.py <design> --before <階段十三之前的 list>
import sys, os, json, subprocess, tempfile
import numpy as np

sys.stdout.reconfigure(encoding='utf-8')
D = os.path.abspath(sys.argv[1])
sys.path.insert(0, D)
import draft_engine_access as E

ASM = 'kotoko-napoleon-01m-assembly'
before = sys.argv[sys.argv.index('--before') + 1]


def load(p):
    A = np.loadtxt(p, delimiter=',', comments='#', dtype=np.int32, ndmin=2, encoding='utf-8')
    return {(x, y, z): c for x, y, z, c in A.tolist()}


def lst(p):
    return {(x, y, z): c for x, y, z, c in (tuple(map(int, l.split(','))) for l in open(p, encoding='utf-8') if l.strip() and l[0] != '#')}


tmp = tempfile.mkdtemp()
now_p = os.path.join(tmp, 'now.txt').replace('\\', '/')
parts_p = os.path.join(tmp, 'parts.json').replace('\\', '/')
for a in (['op=export', 'format=list', 'work=' + ASM, 'out=' + now_p, 'links=all'], ['op=export', 'format=parts', 'work=' + ASM, 'out=' + parts_p]):
    r = subprocess.run(['senate', 'cmd', 'sculpture'] + sum([['--arg', x] for x in a], []), capture_output=True, text=True, encoding='utf-8', errors='replace')
    if r.returncode:
        raise SystemExit(r.stdout[-800:] + r.stderr[-800:])
want = load(before)
for k in lst(os.path.join(D, 'masks', 'engine_access', 'coaming_carve.vox.txt')):
    want.pop(k)
want.update(lst(os.path.join(D, 'masks', 'engine_access', 'ladders.vox.txt')))
now = load(now_p)
R = {'want': len(want), 'now': len(now), 'missing': sum(1 for k in want if k not in now), 'extra': sum(1 for k in now if k not in want),
     'color_diff': sum(1 for k, c in want.items() if k in now and now[k] != c)}
P = json.load(open(parts_p, encoding='utf-8'))
parts = P['links']
lad = [p for p in parts if (p.get('path') or '').endswith('梯子-機艙')]
pts = json.load(open(os.path.join(D, 'engine_access_points.json'), encoding='utf-8'))
R['link'] = [{'path': p.get('path'), 'meta': p.get('meta')} for p in lad]
if lad:
    got = lad[0].get('points') or {}
    diff = []
    for nm, v in pts.items():
        for pk, q in v['points'].items():
            g = got.get('%s.%s' % (nm, pk))
            if g is None or max(abs(float(a) - (b + 0.5)) for a, b in zip(g, q)) > 1e-6 and max(abs(float(a) - b) for a, b in zip(g, q)) > 1e-6:
                diff.append(('%s.%s' % (nm, pk), g, q))
    R['points'] = {'want': 4 * len(pts), 'got': sum(1 for k in got if k.split('.')[0] in pts), 'diff': diff}
G = E.export_grid(now_p)
S = G > 0
x0, x1, zt = E.ROOM
st = E.stand_map(S, x0, x1, zt)
lp = [v['points'] for v in pts.values()]
starts = [v['points']['head'] for v in pts.values() if v['top'] == 'deck']
up = E.reach(st, x0, starts, lp, back=True)
dn = E.reach(st, x0, starts, lp)
R['reach'] = {'reachable_from_deck': len(dn), 'back_to_deck': len(up), 'reachable_but_not_back': len(dn - up)}
print(json.dumps(R, ensure_ascii=False))
