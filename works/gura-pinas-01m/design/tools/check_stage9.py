# 出處：calli-cosecha-01m/design/tools/check_stage9.py（收穫號，照抄後改成藍鯊號 —— TASK-0967）
# 階段九（TASK-0598）讀數：彈藥庫與甲板物件 —— 一律從作品讀（子作品匯出、anchors.json、models.json、組裝件 links.json、CLI `work sub=models`）
#   ① 結果帳：彈藥庫、小艇架 子作品 vs 清單（缺／多／色差）
#   ② 彈藥庫：關聯 meta kind=magazine、pos、powder_lb ＝ 作品裡的火藥桶數 × 100；固定點 blast（空氣）、door（空氣、腳下實心）
#   ③ 遊戲要的 kind 一件都不缺：magazine（關聯）、powder、wheel、binnacle、capstan、boat（模型）—— 缺哪一種、哪一件沒有 kind 都列出來
#   ④ 模型：CLI 狀態、參數 ＝ 設計、撞組裝件實心的樣本、腳下 12 格內有沒有實心（遊戲 10_ship.js:47 的判法：外框中心往下）
#   用法：python -I -X utf8 tools/check_stage9.py <design> [--drop=<模型名或 link:<關聯名>>]（反向對照：讀完作品之後當作那一件沒有 kind）
import json, os, re, subprocess, sys, math
import numpy as np
sys.stdout.reconfigure(encoding='utf-8')
design = sys.argv[1]
drop = next((a.split('=', 1)[1] for a in sys.argv[2:] if a.startswith('--drop=')), None)
sys.path.insert(0, design)
sys.path.insert(0, os.path.join(design, 'tools'))
from wio import export_list, key
from gunsim import Grid, Gun
WORKS = os.environ.get('SCULPT_WORKS') or os.path.dirname(os.path.dirname(os.path.abspath(design)))   # worktree 只放 design/ ⇒ 作品資料讀共用的那一份
GB = json.load(open(os.path.join(design, 'plan.json'), encoding='utf-8'))['gear_build']
PL = json.load(open(os.path.join(design, 'gear_placement.json'), encoding='utf-8'))
ASM = GB['assembly']

# ① 結果帳
for spec, f in ((GB['magazine'], 'magazine'), (GB['skids'], 'skids')):
    W = export_list(spec['work'], None)
    D = np.loadtxt(os.path.join(design, 'masks', 'gear', f + '.vox.txt'), delimiter=',', comments='#', dtype=np.int32, ndmin=2, encoding='utf-8')
    cw, cd = dict(zip(key(W).tolist(), W[:, 3].tolist())), dict(zip(key(D).tolist(), D[:, 3].tolist()))
    print('① %-26s 作品 %5d、設計 %5d、缺 %d、多 %d、色差 %d' % (spec['work'], len(cw), len(cd), len(set(cd) - set(cw)), len(set(cw) - set(cd)), sum(1 for k in set(cd) & set(cw) if cd[k] != cw[k])))

# 從作品讀模型與關聯 meta
hosts = sorted({r['host'] for r in PL['models']})
models = {}
cli_ok = {}
for h in hosts:
    for m in json.load(open(os.path.join(WORKS, h, 'models.json'), encoding='utf-8'))['models']:
        models[m['name']] = dict(m, host=h)
    out = subprocess.run(['senate', 'cmd', 'sculpture', '--arg', 'op=work', '--arg', 'sub=models', '--arg', 'work=' + h], capture_output=True, text=True, encoding='utf-8', errors='replace').stdout
    for l in out.splitlines():
        mm = re.match(r'- (\S) `([^`]+)`［(\w+)］', l)
        if mm:
            cli_ok[mm.group(2).split('/')[-1]] = mm.group(3)
links = {l['name']: l for l in json.load(open(os.path.join(WORKS, ASM, 'links.json'), encoding='utf-8'))['links']}
if drop:
    if drop.startswith('link:'):
        links[drop[5:]] = dict(links[drop[5:]], meta={k: v for k, v in (links[drop[5:]].get('meta') or {}).items() if k != 'kind'})
    else:
        models[drop] = dict(models[drop], meta={k: v for k, v in (models[drop].get('meta') or {}).items() if k != 'kind'})
gear = {n: m for n, m in models.items() if n in {r['name'] for r in PL['models']}}
print('   模型（從作品讀，本階段的）%d、設計 %d；CLI 狀態 ok %d／其他 %s' % (len(gear), len(PL['models']), sum(1 for n in gear if cli_ok.get(n) == 'ok'),
      [n for n in gear if cli_ok.get(n) != 'ok']))

# ② 彈藥庫
mag_links = [l for l in links.values() if (l.get('meta') or {}).get('kind') == 'magazine']
A = export_list(ASM, None, links=None)
G = Grid(A)
an = {a['name']: a['at'] for a in json.load(open(os.path.join(WORKS, GB['magazine']['work'], 'anchors.json'), encoding='utf-8'))['anchors']}
n_powder = sum(1 for m in gear.values() if m['host'] == GB['magazine']['work'] and (m.get('meta') or {}).get('kind') == 'powder')
for l in mag_links:
    me = l['meta']
    print('② 彈藥庫 `%s`：pos %s、powder_lb %s（作品裡的火藥桶 %d × 100 ＝ %d）' % (l['name'], me.get('pos'), me.get('powder_lb'), n_powder, n_powder * 100))
for nm in ('blast', 'door'):
    a = an.get(nm)
    print('   固定點 %s %s：空氣 %s%s' % (nm, a, a is not None and not G.solid(*a), ('、腳下實心 %s' % G.solid(a[0], a[1], a[2] - 1)) if nm == 'door' and a else ''))

# ③ kind 一件都不缺
need = ['powder', 'wheel', 'binnacle', 'capstan', 'boat']
have = {}
for m in gear.values():
    have.setdefault((m.get('meta') or {}).get('kind'), []).append(m['name'])
missing = [k for k in need if not have.get(k)] + ([] if mag_links else ['magazine'])
nokind = sorted(n for n, m in gear.items() if 'kind' not in (m.get('meta') or {})) + ['link:' + n for n in ('彈藥庫',) if 'kind' not in (links[n].get('meta') or {})]
print('③ 缺的種類 %s；沒有 kind 的 %d %s；各種 %s' % (missing, len(nokind), nokind[:5], {k: len(v) for k, v in sorted(have.items(), key=lambda kv: str(kv[0]))}))

# ④ 模型：參數 ＝ 設計、碰撞、腳
diff, coll, nofoot = [], {}, []
cache = {}
for r in PL['models']:
    m = gear.get(r['name'])
    if not m:
        diff.append((r['name'], 'missing'))
        continue
    want = {'at': r['at'], 'pivot': r['pivot'], 'rotate': [0, 0, r['rotate']], 'scale': [r['scale']] * 3, 'work': r['work'], 'host': r['host']}
    for k, v in want.items():
        got = m[k]
        if (isinstance(v, list) and not np.allclose(np.array(got, float), np.array(v, float), atol=1e-6)) or (not isinstance(v, list) and got != v):
            diff.append((r['name'], k, got, v))
    if m['work'] not in cache:
        cache[m['work']] = export_list(m['work'], None)
    g = Gun(r['name'], {'work': m['work'], 'scale': m['scale'][0], 'pivot': m['pivot'], 'meta': {}}, cache[m['work']], {}, 0.2)
    k = int(G.hit(g.world(g.samples, m['at'], m['rotate'][2], False)).sum())
    if k:
        coll[r['name']] = k
    lo, hi = g.bbox(m['at'], m['rotate'][2], False)
    cx, cy, fz = int(math.floor((lo[0] + hi[0]) / 2)), int(math.floor((lo[1] + hi[1]) / 2)), int(math.floor(lo[2])) - 1
    if not any(G.solid(cx, cy, fz - d) for d in range(0, 13)):
        nofoot.append(r['name'])
print('④ 參數 ≠ 設計 %d %s；撞實心 %d %s；腳下 12 格內沒有實心 %d %s' % (len(diff), diff[:3], len(coll), dict(list(coll.items())[:5]), len(nofoot), nofoot[:5]))
