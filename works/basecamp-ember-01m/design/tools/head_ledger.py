# 餘燼號 階段九 結果帳：組裝件現在（links=all）vs 設計（藏起本階段關聯的現況 ＋ knee ＋ 兩舷裝飾 ＋ 船首像 ＋ 兩隻錨）
# 用法：python -I head_ledger.py <design 資料夾>
import sys, os, json
import numpy as np
sys.stdout.reconfigure(encoding='utf-8')
D = os.path.abspath(sys.argv[1])
sys.path.insert(0, D)
from draft_ladders import export_hidden   # noqa: E402

H = json.load(open(os.path.join(D, 'plan.json'), encoding='utf-8'))['head_build']
HD = os.path.join(D, 'masks', 'head')


def load(p):
    return np.loadtxt(p, delimiter=',', comments='#', dtype=np.int32, ndmin=2, encoding='utf-8')


want = {}
for x, y, z, c in export_hidden(H['assembly'], H['hide_links']):
    want[(x, y, z)] = c
for x, y, z, c in load(os.path.join(HD, 'knee.vox.txt')):
    want[(x, y, z)] = c
for x, y, z, c in load(os.path.join(HD, 'figurehead.vox.txt')):
    want[(x, y, z)] = c
sb = H['subworks']['side']['box']
ax, ay, az = sb['at']
my = 321 - ay - sb['size'][1]
for x, y, z, c in load(os.path.join(HD, 'side.vox.txt')):
    want[(x + ax, y + ay, z + az)] = c
    want[(x + ax, sb['size'][1] - 1 - y + my, z + az)] = c
pk = json.load(open(os.path.join(HD, 'anchor_pick.json'), encoding='utf-8'))
for x, y, z, c in export_hidden(H['anchor']['work'], []):
    sx, sy, sz = pk['at_S']
    want[(x + sx, y + sy, z + sz)] = c
    px, py, pz = pk['at_P']
    want[(x + px, 33 - 1 - y + py, z + pz)] = c
have = {(x, y, z): c for x, y, z, c in export_hidden(H['assembly'], [])}
miss = [k for k in want if k not in have]
extra = [k for k in have if k not in want]
cdiff = [k for k in want if k in have and have[k] != want[k]]
r = {'design': len(want), 'work': len(have), 'missing': len(miss), 'extra': len(extra), 'color_diff': len(cdiff),
     'first': {'missing': [list(map(int, k)) for k in miss[:5]], 'extra': [list(map(int, k)) for k in extra[:5]], 'color_diff': [list(map(int, k)) for k in cdiff[:5]]}}
print(json.dumps(r, ensure_ascii=False))
json.dump(r, open(os.path.join(D, 'verify_head_ledger.json'), 'w', encoding='utf-8', newline='\n'), ensure_ascii=False, indent=1)
