# 階段十二（TASK-0624）讀數：砲具與砲索 —— 一律從作品讀（砲具子作品匯出、anchors.json、CLI `work sub=ropes` 的狀態與兩端座標、各甲板的 models.json）
#   ① 結果帳：砲具子作品 vs 清單
#   ② 固定點：每個都落在砲具的實心格上
#   ③ 砲索：組 guns/… 的條數、CLI 狀態不是 ok 的（ropes_broken）；每門砲五條（breeching ×2、tackle ×2、train）缺哪幾條
#   ④ 每條砲索的端點：砲那一端是那門砲來源作品有的固定點、環那一端是砲具子作品有的固定點（讀完作品之後，--drop 可以當作那個固定點不在）
#   用法：python -I -X utf8 tools/check_stage12.py <design> [--drop=<固定點名>]
import json, os, re, subprocess, sys, collections
import numpy as np
sys.stdout.reconfigure(encoding='utf-8')
design = sys.argv[1]
drop = next((a.split('=', 1)[1] for a in sys.argv[2:] if a.startswith('--drop=')), None)
sys.path.insert(0, os.path.join(design, 'tools'))
from wio import export_list, key
WORKS = os.path.dirname(os.path.dirname(os.path.abspath(design)))
FB = json.load(open(os.path.join(design, 'plan.json'), encoding='utf-8'))['gunfittings_build']
W = export_list(FB['work'], None)
D = np.loadtxt(os.path.join(design, 'masks', 'gunfittings', 'gunfittings.vox.txt'), delimiter=',', comments='#', dtype=np.int32, ndmin=2, encoding='utf-8')
cw, cd = dict(zip(key(W).tolist(), W[:, 3].tolist())), dict(zip(key(D).tolist(), D[:, 3].tolist()))
print('① 砲具 作品 %d、設計 %d、缺 %d、多 %d、色差 %d' % (len(cw), len(cd), len(set(cd) - set(cw)), len(set(cw) - set(cd)), sum(1 for k in set(cd) & set(cw) if cd[k] != cw[k])))
cells = set(map(tuple, W[:, :3].tolist()))
an = {a['name']: tuple(a['at']) for a in json.load(open(os.path.join(WORKS, FB['work'], 'anchors.json'), encoding='utf-8'))['anchors']}
if drop:
    an.pop(drop, None)
print('② 固定點 %d；不在實心格上 %d' % (len(an), sum(1 for v in an.values() if v not in cells)))
out = subprocess.run(['senate', 'cmd', 'sculpture', '--arg', 'op=work', '--arg', 'sub=ropes', '--arg', 'work=calli-cosecha-01m-assembly'], capture_output=True, text=True, encoding='utf-8', errors='replace').stdout
st = {}
for l in out.splitlines():
    m = re.match(r'- (\S) `([^`]+)`［(\w+)］ (\S+) \(', l)
    if m:
        st[m.group(2)] = m.group(3)
ropes = {}
for f in ('ropes.json',):
    for r in json.load(open(os.path.join(WORKS, 'calli-cosecha-01m-assembly', f), encoding='utf-8'))['ropes']:
        if (r.get('group') or '').startswith('guns/'):
            ropes[r['name']] = r
print('③ 砲索（組 guns/…，從作品讀）%d：%s；CLI 狀態不是 ok 的 %d %s' % (len(ropes), dict(collections.Counter(r['group'] for r in ropes.values())),
      sum(1 for n in ropes if st.get(n) != 'ok'), [n for n in ropes if st.get(n) != 'ok'][:4]))
guns = {}
for dk in ('main', 'puente', 'alcazar', 'castillo'):
    for m in json.load(open(os.path.join(WORKS, 'calli-cosecha-01m-deck-' + dk, 'models.json'), encoding='utf-8'))['models']:
        if (m.get('meta') or {}).get('kind') == 'gun':
            guns[m['name']] = m
need = ['breeching-aft', 'breeching-fwd', 'tackle-aft', 'tackle-fwd', 'train']
miss = {g: [s for s in need if '%s.%s' % (g, s) not in ropes] for g in guns}
miss = {g: v for g, v in miss.items() if v}
print('   每門五條：砲 %d、缺繩的 %d %s' % (len(guns), len(miss), dict(list(miss.items())[:4])))
src_an = {}
bad = []
for n, r in sorted(ropes.items()):
    for end in (r['from'], r['to']):
        if end.startswith('model:'):
            _, rest = end.split(':', 1)
            link, gun, p = rest.split('/')
            w = guns[gun]['work']
            if w not in src_an:
                src_an[w] = {a['name'] for a in json.load(open(os.path.join(WORKS, w, 'anchors.json'), encoding='utf-8'))['anchors']}
            if p not in src_an[w]:
                bad.append((n, end))
        else:
            link, p = end.split('/')
            if link != FB['link'] or p not in an:
                bad.append((n, end))
print('④ 端點對不上 %d %s' % (len(bad), bad[:6]))
