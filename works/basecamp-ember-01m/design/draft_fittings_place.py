# 餘燼號 階段十八 擺甲板屬具（plan.json fittings_build）—— 羅經櫃、主絞盤當外部模型掛在甲板-spar（同舵輪）
#   擺法同舵輪／砲：y 固定中線、轉角 0；x 每 0.5 格試；z ＝ 腳印裡甲板頂的最高 ＋ 1；
#   模型每格格心＋八角縮 0.2 不落在「組裝件＋spar 的 carronade＋已經擺好的模型（舵輪、前一件）」實心裡；
#   腳印每一欄正下方要是甲板（不蓋在艙口上）；外框不准進「保留區」（梯子在上甲板的 foot／head 前後、留給舵手站的地方）。
#   羅經櫃：從舵輪外框前緣 ＋ 走道 起往船頭搜，取第一個（最靠舵輪）。
#   主絞盤：search_x 範圍全搜，列出放得下的（四周 clear 格內甲板以上淨空），取中間那一個（pick mid）。
#     v1 不要淨空、取最靠主桅 ⇒ x 333、絞盤頭貼著主桅 fife rail、後面是梯口（人與插桿都沒地方）⇒ 加 clear 5（0.5 m）⇒ 只剩前甲板 594.5..622.5。
#   ⇒ fittings_placement.json、verify_fittings_place.json
# 用法：python -I draft_fittings_place.py <design 資料夾>
import sys, os, json
import numpy as np

D = os.path.abspath(sys.argv[1])
sys.path.insert(0, D)
from draft_ladders import export_hidden  # noqa: E402
import place_guns as PG                   # noqa: E402

sys.stdout.reconfigure(encoding='utf-8')
plan = json.load(open(os.path.join(D, 'plan.json'), encoding='utf-8'))
P = plan['fittings_build']
a = export_hidden(P['assembly'], [])
assert len(a) == P['assembly_voxels'], ('組裝件現況對不上', len(a))
G = PG.grid(a)
DECK = G.copy()                                    # 判「正下方是甲板」只看格子（模型不算地板）
GB = plan['guns_build']
for r in json.load(open(os.path.join(D, 'guns_placement.json'), encoding='utf-8'))['rows']:
    if r['deck'] != 'spar':
        continue
    t = GB['types'][r['type']]
    src = os.path.join(D, t['cells']) if t['cells'].startswith('masks/') else t['cells']
    g = PG.Gun(r['type'], t['work'], PG.load_cells(src), t['scale'], t['pivot'], t['muzzle'], t['meta'])
    w = np.floor(g.world(g.samples, r['at'], r['phi'], r['side'] == 'P')).astype(int)
    G[w[:, 0] - PG.X0, w[:, 1], w[:, 2] - PG.Z0] = True


def mark_model(m):
    w = np.floor(m['gun'].world(m['gun'].samples, m['at'], 0, False)).astype(int)
    G[w[:, 0] - PG.X0, w[:, 1], w[:, 2] - PG.Z0] = True


# 已經在甲板上的舵輪
WP = json.load(open(os.path.join(D, 'wheel_placement.json'), encoding='utf-8'))
WB = plan['wheel_build']
wheel = {'gun': PG.Gun('wheel', WB['source_work'], PG.load_cells(WB['source_work']), WB['scale'], WB['pivot'], WB['pivot'], {}), 'at': WP['at']}
mark_model(wheel)

# 保留區：梯子在上甲板（spar）的 foot／head 前後 keep_x、兩側 keep_y；舵輪外框前 helm_gap（舵手站的地方）
LP = json.load(open(os.path.join(D, 'verify_ladder_points_%s.json' % P['assembly']), encoding='utf-8'))
keep = []
for L in LP['ladders']:
    for k in ('foot', 'head'):
        x, y, z = L[k]
        if abs(z - P['deck_stand_z']) <= 1:
            keep.append(([x - P['keep_x'], y - P['keep_y']], [x + 1 + P['keep_x'], y + 1 + P['keep_y']], '%s.%s' % (L['ladder'], k)))
wb = WP['box']
keep.append(([wb[0][0], wb[0][1]], [wb[1][0] + P['helm_gap'], wb[1][1]], '舵輪＋舵手'))


def in_keep(lo, hi):
    return [n for (k0, k1, n) in keep if lo[0] < k1[0] and hi[0] > k0[0] and lo[1] < k1[1] and hi[1] > k0[1]]


def deck_top(x, y):
    zs = np.nonzero(DECK[x - PG.X0, y, P['search_z'][0] - PG.Z0:P['search_z'][1] - PG.Z0 + 1])[0]
    return int(zs.max()) + P['search_z'][0] if len(zs) else None


def try_at(m, x):
    gun = m['gun']
    c = np.array(gun.cells_raw, float)
    bot = c[c[:, 2] == c[:, 2].min()] + 0.5
    foot = {tuple(v) for v in np.floor(gun.world(bot, (x, P['y'], 0), 0, False)[:, :2]).astype(int).tolist()}
    tops = [deck_top(fx, fy) for fx, fy in foot]
    if any(t is None for t in tops):
        return None, 'no-deck'
    z = max(tops) + 1
    if min(tops) < z - 1 - P['max_gap']:
        return None, 'gap'                           # 腳印裡甲板高低差太大（腳懸空）
    at = (x, P['y'], z)
    W = gun.world(gun.samples, at, 0, False)
    lo, hi = W.min(0), W.max(0)
    k = in_keep(lo, hi)
    if k:
        return None, 'keep:' + '／'.join(k)
    n = int(PG.hits(G, W).sum())
    if n:
        return None, 'hit %d' % n
    c = m.get('clear', 0)                           # 四周 clear 格內、甲板頂 ＋2 以上不准有實心（留給人與插桿；v1 絞盤貼著 fife rail）
    if c:
        x0, x1 = int(np.floor(lo[0])) - c, int(np.ceil(hi[0])) + c
        y0, y1 = int(np.floor(lo[1])) - c, int(np.ceil(hi[1])) + c
        z0, z1 = z + 1, int(np.ceil(hi[2]))
        blk = G[x0 - PG.X0:x1 - PG.X0 + 1, y0:y1 + 1, z0 - PG.Z0:z1 - PG.Z0 + 1].sum()
        if blk:
            return None, 'crowd %d' % blk
    return {'at': [float(v) for v in at], 'box': [[round(float(v), 2) for v in lo], [round(float(v), 2) for v in hi]],
            'deck_tops': sorted(set(tops))}, 'ok'


out, ver = [], {}
for item in P['items']:
    cells = PG.load_cells(os.path.join(D, item['cells']))
    gun = PG.Gun(item['key'], item['work'], cells, P['scale'], item['pivot'], item['pivot'], {})
    gun.cells_raw = cells
    m = {'gun': gun, 'clear': item.get('clear', 0)}
    if item['key'] == 'binnacle':
        x0 = np.ceil((wb[1][0] + P['helm_gap'] + item['half_x']) * 2) / 2   # 對齊 0.5 格（不讓浮點尾巴進作品檔）
        xs = [x0 + 0.5 * i for i in range(int((item['search_x'][1] - x0) / 0.5) + 1)]
    else:
        xs = [item['search_x'][0] + 0.5 * i for i in range(int((item['search_x'][1] - item['search_x'][0]) / 0.5) + 1)]
    tried, okays = [], []
    for x in xs:
        r, why = try_at(m, x)
        tried.append([x, why])
        if r:
            okays.append((x, r))
            if item['pick'] == 'first':
                break
    assert okays, ('%s 放不下' % item['key'], tried[-8:])
    x, r = okays[0] if item['pick'] == 'first' else okays[-1] if item['pick'] == 'last' else okays[len(okays) // 2]   # mid ＝ 放得下的那些的中間
    m['at'] = r['at']
    mark_model(m)
    out.append({'name': item['name'], 'label': item['label'], 'work': P['deck_work'], 'source_work': item['work'], 'at': r['at'],
                'pivot': item['pivot'], 'scale': P['scale'], 'box': r['box'], 'deck_tops': r['deck_tops']})
    runs, cur = [], None                               # 放得下的 x 段（給人看）
    for xx, _ in okays:
        if cur and abs(xx - cur[1] - 0.5) < 1e-6:
            cur[1] = xx
        else:
            cur = [xx, xx]
            runs.append(cur)
    from collections import Counter
    ver[item['key']] = {'chosen_x': x, 'ok_runs': runs, 'tried': len(tried),
                        'why_not': dict(Counter(w.split(' ')[0] if w.startswith(('hit', 'crowd')) else w for _, w in tried if w != 'ok'))}
    print(item['label'], 'at', r['at'], 'box', r['box'], '放得下的段', runs)
    print('  不行的原因', ver[item['key']]['why_not'])

json.dump({'models': out}, open(os.path.join(D, 'fittings_placement.json'), 'w', encoding='utf-8', newline='\n'), ensure_ascii=False, indent=1)
json.dump({'keep': [[k0, k1, n] for k0, k1, n in keep], 'items': ver}, open(os.path.join(D, 'verify_fittings_place.json'), 'w', encoding='utf-8', newline='\n'),
          ensure_ascii=False, indent=1)
