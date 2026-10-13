# 餘燼號 階段十七 舵輪（plan.json wheel_build；子物件重複用 ⇒ 憲法號 -wheel 當外部模型，掛在甲板-spar）
#   憲法號那時：pivot (50,52,0)、scale 0.2、z 0 ＝ 甲板面；舵索 2 條從 drum-rope-a／b 往下到甲板面（往下穿進甲板）。
#   餘燼號：後桅在 poop 底下（船長室）、poop 前緣 x ≈ 212，中線 x 213–227 是上 poop 的梯子 ⇒ 舵輪放在梯子前面的上甲板中線。
#   搜法：y 固定 160.5、轉角 0（跟憲法號同向）；x 從 search_x[0] 往船頭每 0.5 格試，z ＝ 腳下中線甲板頂 ＋ 1；
#   模型每一格的格心＋八個角往裡縮 0.2（place_guns 同一套）都不落在「組裝件＋甲板-spar 的砲模型」實心格裡 ⇒ 取最靠船尾的那一個。
#   舵索端點 ＝ 鼓輪固定點正下方的甲板面（憲法號同形）。⇒ wheel_placement.json、verify_wheel.json
# 用法：python -I draft_wheel.py <design 資料夾>
import sys, os, json
import numpy as np

D = os.path.abspath(sys.argv[1])
sys.path.insert(0, D)
from draft_ladders import export_hidden, existing_links  # noqa: E402
import place_guns as PG                                   # noqa: E402

sys.stdout.reconfigure(encoding='utf-8')
plan = json.load(open(os.path.join(D, 'plan.json'), encoding='utf-8'))
P = plan['wheel_build']
a = export_hidden(P['assembly'], [])
assert len(a) == P['assembly_voxels'], ('組裝件現況對不上', len(a))
G = PG.grid(a)
GB = plan['guns_build']
for r in json.load(open(os.path.join(D, 'guns_placement.json'), encoding='utf-8'))['rows']:
    if r['deck'] != 'spar':
        continue
    t = GB['types'][r['type']]
    src = os.path.join(D, t['cells']) if t['cells'].startswith('masks/') else t['cells']
    g = PG.Gun(r['type'], t['work'], PG.load_cells(src), t['scale'], t['pivot'], t['muzzle'], t['meta'])
    w = np.floor(g.world(g.samples, r['at'], r['phi'], r['side'] == 'P')).astype(int)
    G[w[:, 0] - PG.X0, w[:, 1], w[:, 2] - PG.Z0] = True

W = PG.Gun('wheel', P['source_work'], PG.load_cells(P['source_work']), P['scale'], P['pivot'], P['pivot'], {})
anc = {}
r = __import__('subprocess').run(['senate', 'cmd', 'sculpture', '--arg', 'op=work', '--arg', 'sub=anchors', '--arg', 'work=' + P['source_work']],
                                 capture_output=True, text=True, encoding='utf-8', errors='replace')
for line in r.stdout.splitlines():
    if '` ← ' in line and '@' in line:
        n = line.split('`')[1]
        anc[n] = [float(v) for v in line.rsplit('@', 1)[1].split()[0].split(',')]
assert all(k in anc for k in P['rope_anchors']), ('舵輪固定點讀不到', sorted(anc))

Y = P['y']


def deck_top(x, y):
    """(x,y) 這一欄、上甲板那一段的頂（search_z 範圍內最高的實心）"""
    zs = [z for z in range(P['search_z'][0], P['search_z'][1] + 1) if G[x - PG.X0, y, z - PG.Z0]]
    return max(zs) if zs else None


tried = []
best = None
x = P['search_x'][0]
while x <= P['search_x'][1]:
    top = deck_top(int(np.floor(x)), int(np.floor(Y)))
    if top is not None:
        at = (x, Y, top + 1)
        n = int(PG.hits(G, W.world(W.samples, at, 0, False)).sum())
        tried.append([x, top + 1, n])
        if n == 0:
            best = at
            break
    x += 0.5
assert best, ('搜不到放得下的位置', tried[-5:])

# 舵索：固定點世界座標 → 正下方甲板面（那一欄的甲板頂 ＋ 1）
ropes = []
for i, k in enumerate(P['rope_anchors']):
    p = W.world(np.array([anc[k]]) + 0.5, best, 0, False)[0]
    top = deck_top(int(np.floor(p[0])), int(np.floor(p[1])))
    ropes.append({'name': P['rope_names'][i], 'from': 'model:%s/%s/%s' % (P['link_path'], P['name'], k),
                  'to': '%.1f,%.1f,%.1f' % (p[0], p[1], top + 1), 'color': P['rope']['color'], 'thickness': P['rope']['thickness'],
                  'slack': P['rope']['slack'], 'group': P['rope']['group'], 'anchor_world': [round(float(v), 3) for v in p],
                  'length': round(float(p[2] - (top + 1)), 2)})

box = W.world(W.samples, best, 0, False)
out = {'name': P['name'], 'work': P['deck_work'], 'source_work': P['source_work'], 'at': [float(v) for v in best], 'pivot': P['pivot'],
       'scale': P['scale'], 'rotate': [0, 0, 0], 'box': [[round(float(v), 2) for v in box.min(0)], [round(float(v), 2) for v in box.max(0)]],
       'ropes': ropes}
json.dump(out, open(os.path.join(D, 'wheel_placement.json'), 'w', encoding='utf-8', newline='\n'), ensure_ascii=False, indent=1)
json.dump({'tried': tried, 'chosen': out['at'], 'hits_at_chosen': 0, 'model_cells': W.n, 'samples': len(W.samples)},
          open(os.path.join(D, 'verify_wheel.json'), 'w', encoding='utf-8', newline='\n'), ensure_ascii=False, indent=1)
print('舵輪 at', out['at'], 'box', out['box'])
print('試了', len(tried), '個 x；前幾個：', tried[:6])
for rp in ropes:
    print(rp['name'], rp['from'], '→', rp['to'], '長', rp['length'])
