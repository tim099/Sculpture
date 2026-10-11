# 階段六結果帳（作品＝設計）：events 重播 vs 「階段六前的現況 − post_trim ＋ 51 份清單（色 141）」逐格比
# 另外核對：階段六之後的 event 是不是剛好 4 刀 carve ＋ 每份清單一刀 stampvox、每刀記的清單 sha256 ＝ verify_frames_ends.json、placed ＝ 清單格數
# 用法：python -I -B ledger_stage6.py <階段六前最後一個 event，例 2026-10-11/023951_172_ec19bf.json>
import sys, os, glob, json, hashlib
import numpy as np
from scipy import ndimage
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
sys.stdout.reconfigure(encoding='utf-8')
from replay import replay
W = 'D:/Unity/Valhalla/Sculpture/works/basecamp-frigate-constitution-01m'
last_before = sys.argv[1]
files = sorted(glob.glob(os.path.join(W, 'events', '*', '*.json')))
names = [os.path.basename(os.path.dirname(f)) + '/' + os.path.basename(f) for f in files]
cut = names.index(last_before) + 1
before = replay(W, upto=names[cut]) if cut < len(names) else replay(W)
now = replay(W)
print('階段六前', len(before), '｜現在', len(now), '｜之後的 event', len(names) - cut)
v = json.load(open(W + '/design/verify_frames_ends.json', encoding='utf-8'))
pt = json.load(open(W + '/design/plan.json', encoding='utf-8'))['framing_ends']['stern']['post_trim']
trim = {k for k, c in before.items() if k[0] < pt['x_max'] and abs(k[1] - 160) <= 2 and
        ((c[0] == 177 and k[2] >= pt['sternpost_from_z']) or (c[0] == 173 and k[2] >= pt['inner_post_from_z']))}
want = {k: c[0] for k, c in before.items() if k not in trim}
lists = {}
for t in v['timbers']:
    # 清單在這個 repo 會被 autocrlf 以 CRLF 檢出，而事件與 verify 記的 sha256 是產生當下的 LF 位元組 ⇒ 先換回 LF 再算
    body = open(os.path.join(W, t['list']), 'rb').read().replace(b'\r\n', b'\n')
    cells = [tuple(map(int, l.split(',')[:4])) for l in body.decode('utf-8').splitlines() if l.strip() and not l.startswith('#')]
    lists[t['name']] = (hashlib.sha256(body).hexdigest(), cells)
    for x, y, z, c in cells:
        want[(x, y, z)] = c
got = {k: c[0] for k, c in now.items()}
miss = [k for k in want if k not in got]
extra = [k for k in got if k not in want]
diffc = [k for k in want if k in got and got[k] != want[k]]
print('結果帳：應有', len(want), '實有', len(got), '缺', len(miss), '多', len(extra), '顏色不同', len(diffc))
touched = sum(1 for k, c in before.items() if k not in trim and (k not in now or now[k][0] != c[0]))
print('階段六前的格（扣掉 post_trim）被動到', touched, '｜post_trim', len(trim))
# 每一刀
ops = {}
sha_ok = place_ok = 0
for f, nm in zip(files[cut:], names[cut:]):
    e = json.load(open(f, encoding='utf-8'))
    ops[e.get('op')] = ops.get(e.get('op'), 0) + 1
    if e.get('op') == 'stampvox':
        s = json.dumps(e, ensure_ascii=False)
        hit = [n for n, (h, cells) in lists.items() if h in s]
        if len(hit) == 1:
            sha_ok += 1
            if len(e['placed_colored']) == len(lists[hit[0]][1]):
                place_ok += 1
            else:
                print('  ⚠', nm, hit[0], 'placed', len(e['placed_colored']), '清單', len(lists[hit[0]][1]))
        else:
            print('  ⚠', nm, '對不到唯一一份清單的 sha256', hit)
print('之後的 event：', ops, '｜stampvox 對到清單 sha256', sha_ok, '／', len(lists), '｜placed ＝ 清單格數', place_ok)
# 結構
a = np.array(list(got.keys()), int)
mn = a.min(0) - 1
G = np.zeros(a.max(0) - mn + 2, bool)
G[tuple((a - mn).T)] = True
lab, n = ndimage.label(G)
cav = ndimage.binary_fill_holes(G) & ~G
print('face-connected 元件', n, '｜3D 封閉空腔', int(cav.sum()), '格')
