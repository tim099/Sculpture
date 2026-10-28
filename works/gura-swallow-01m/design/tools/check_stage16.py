# 抄來的（燕子號 TASK-0968）：出處 gura-flyingfish-01m/design/tools/check_stage16.py（飛魚號；作品 id、船名、單號已換）
# 抄來的（飛魚號 TASK-0971）：出處 ame-labelle-01m/design/tools/check_stage16.py（拉貝爾號；作品 id、persona、船名、作品尺寸已換）
# 燕子號 步驟 16 補做（TASK-0968）讀數：每件從作品匯出讀回，跟 draft_fit.py 的設計對帳
#   用法：python -I -X utf8 tools/check_stage16.py <design> <落格前的組裝件清單（export format=list）>
#   · 結果帳：組裝件 ＝ 落格前 ＋ 絞盤 ＋ 艙壁（缺 0、多 0、色差 0）
#   · 部件（export parts）：三片艙蓋、爐灶的外框與 meta；絞盤、艙房的關聯 meta 與固定點
#   · 繩梯：assembly ropes.json 的橫繩組 climb／foot／head
import sys, os, json, subprocess, tempfile
import numpy as np

sys.stdout.reconfigure(encoding='utf-8')
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from wio import export_list, key

design, before = sys.argv[1], sys.argv[2]
WORKS = os.path.dirname(os.path.dirname(os.path.abspath(design)))
PL = json.load(open(os.path.join(design, 'fit_placement.json'), encoding='utf-8'))
V = json.load(open(os.path.join(design, 'verify_fit.json'), encoding='utf-8'))
ASM = 'gura-swallow-01m-assembly'
bad = 0


def ok(c, what, got=''):
    global bad
    bad += 0 if c else 1
    print(('  ✓ ' if c else '  ✗ ') + what + ('：%s' % (got,) if got != '' else ''))


B = np.loadtxt(before, delimiter=',', comments='#', dtype=np.int32, ndmin=2)
ld = lambda p: np.loadtxt(os.path.join(design, p), delimiter=',', comments='#', dtype=np.int32, ndmin=2)
add = [ld(PL[k]['mask']) for k in ('windlass', 'room')]
for h in PL['hatches']:
    if h.get('link'):                                      # 走得過去的蓋子：子作品自己的座標 ＋ at
        a = ld(h['mask']).copy(); a[:, :3] += np.array(h['at'], np.int32); add.append(a)
add.append(ld('masks/decks/main.vox.txt'))                 # 主甲板（井前端兩角留成甲板 ⇒ 比落格前多 4 格；其餘跟落格前相同）
want = {}
for arr in [B] + add:
    want.update(zip(key(arr).tolist(), arr[:, 3].tolist()))
A = export_list(ASM, None, links=None)
got = {k: c for k, c in zip(key(A).tolist(), A[:, 3].tolist())}
miss = sum(1 for k in want if k not in got)
extra = sum(1 for k in got if k not in want)
diff = sum(1 for k in want if k in got and got[k] != want[k])
print('結果帳（組裝件 %d ＝ 落格前 %d ＋ 本步 %d）' % (len(got), len(B), len(want) - len(B)))
ok(miss == 0 and extra == 0 and diff == 0, '缺／多／色差', '%d／%d／%d' % (miss, extra, diff))

with tempfile.TemporaryDirectory() as d:
    out = os.path.join(d, 'p.json').replace('\\', '/')
    subprocess.run(['senate', 'cmd', 'sculpture', '--arg', 'op=export', '--arg', 'format=parts', '--arg', 'work=' + ASM, '--arg', 'out=' + out], capture_output=True)
    P = json.load(open(out, encoding='utf-8'))
M = {m['path']: m for m in P['models']}
L = {l['path']: l for l in P['links']}
print('部件')
for h in PL['hatches']:
    if h.get('link'):
        l = L.get('甲板-main/' + h['name'])
        ok(l is not None and '甲板-main/' + h['name'] not in M, h['name'] + ' 是關聯（不是門模型）', l and l['meta'])
        continue
    m = M.get('甲板-main/' + h['name'])
    ok(m is not None and [round(v, 3) for v in m['box']] == V[h['name']]['box'] and m['meta'].get('kind') == 'door' and m['meta'].get('open_deg') == h['meta']['open_deg'],
       h['name'] + ' 外框＝設計、kind=door', m and (m['box'], m['meta']))
    pts = (m or {}).get('points') or {}
    ok('hinge-a' in pts and 'hinge-b' in pts, h['name'] + ' 鉸鏈點（組裝件座標）', {k: pts.get(k) for k in ('hinge-a', 'hinge-b')})
g = M.get('甲板-main/爐灶')
ok(g is not None and [round(v, 2) for v in g['box']] == V['廚房']['box'] and g['meta'].get('kind') == 'galley' and 'deco' not in g['meta'], '爐灶 外框＝設計、kind=galley、沒有 deco', g and (g['box'], g['meta']))
w = L.get(PL['windlass']['link'])
ok(w is not None, '關聯 絞盤', w and w['meta'])
r = L.get('甲板-hold/' + PL['room']['link'])
ok(r is not None and r['meta'].get('kind') == 'rooms', '關聯 甲板-hold/艙房 kind=rooms', r and r['meta'])
rp = (r or {}).get('points') or {}
for k, v in PL['room']['anchors'].items():
    ok(k in rp and [int(c - 0.5) for c in rp[k]] == v, '艙房固定點 ' + k, rp.get(k))
print('繩梯')
R = {x['name']: x for x in json.load(open(os.path.join(WORKS, ASM, 'ropes.json'), encoding='utf-8'))['ratlines']}
for c in PL['ratlines']:
    x = R.get(c['name'], {})
    ok(x.get('climb') is True and x.get('foot') == ','.join(map(str, c['foot'])) and x.get('head') == ','.join(map(str, c['head'])), c['name'] + ' climb／foot／head', (x.get('climb'), x.get('foot'), x.get('head')))
print('問題 %d' % bad)
