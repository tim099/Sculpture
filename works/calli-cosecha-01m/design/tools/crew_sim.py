# 砲班站位模擬（照 Blockside/src/js/40_crew.js makeCrew 的砲班那一段：standNear／standZ／blocked、站位表、taken 共用）—— 交船前在造船這側先量
#   讀：組裝件匯出（格子）＋ CLI `work sub=models work=<組裝件>`（每個模型的外框與 meta，含關聯）
#   ⚠ 是模擬、不是遊戲：砲的處理順序照 CLI 列的順序（遊戲照 .vxk 裡模型的順序）、砲班滿編照砲種表（game.json guns 的 crew）；最後照樣跑 shipcheck 為準
#   用法：python -I -X utf8 tools/crew_sim.py <design> [--only=<砲名前綴>]
import json, os, re, subprocess, sys, math
import numpy as np
sys.stdout.reconfigure(encoding='utf-8')
design = sys.argv[1]
only = next((a.split('=', 1)[1] for a in sys.argv[2:] if a.startswith('--only=')), None)
sys.path.insert(0, os.path.join(design, 'tools'))
from wio import export_list
VAL = os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(design)))))
GUNS = {g['code']: g for g in json.load(open(os.path.join(VAL, 'Blockside', 'src', 'config', 'game.json'), encoding='utf-8'))['guns'].values()}
ASM = 'calli-cosecha-01m-assembly'
A = export_list(ASM, None, links=None)
occ = set(map(tuple, A[:, :3].tolist()))
out = subprocess.run(['senate', 'cmd', 'sculpture', '--arg', 'op=work', '--arg', 'sub=models', '--arg', 'work=' + ASM], capture_output=True, text=True, encoding='utf-8', errors='replace').stdout
models = []
for l in out.splitlines():
    m = re.match(r'- (\S) `([^`]+)`［(\w+)］.*外框 \(([-\d.,]+)\)–\(([-\d.,]+)\)(?:｜meta (.*))?$', l)
    if m:
        meta = dict(kv.split('=', 1) for kv in (m.group(6) or '').split(', ') if '=' in kv)
        models.append({'name': m.group(2), 'bb': [float(v) for v in m.group(4).split(',')] + [float(v) for v in m.group(5).split(',')], 'meta': meta})
block = [m for m in models if m['meta'].get('kind') != 'powder']


def blocked(x, y, z):
    for m in block:
        b = m['bb']
        if math.floor(b[0]) - 1 <= x <= math.ceil(b[3]) + 1 and math.floor(b[1]) - 1 <= y <= math.ceil(b[4]) + 1 and b[2] - 3 <= z <= b[5]:
            return m['name']
    return None


def standZ(x, y, z0, z1, head):
    for z in range(z1, z0 - 1, -1):
        if (x, y, z - 1) not in occ or (x, y, z) in occ:
            continue
        if all((x, y, z + h) not in occ for h in range(1, head)):
            return z
    return -1


taken = set()
anchors_by = {}
rows = []
for m in models:
    if m['meta'].get('kind') != 'gun':
        continue
    code = m['meta'].get('gun')
    g = GUNS[code]
    typ = 'chase' if code == '18chase' else ('carr' if code == '32c' else 'long')
    b = [math.floor(v) for v in m['bb']]
    z0, z1 = (b[2] - 3, b[2] + 3) if typ == 'chase' else ((b[2] - 6, b[2] + 3) if typ == 'carr' else (b[2] - 8, b[2] + 3))
    side = m['meta'].get('side', 'S')
    sg = -1 if side == 'P' else 1
    cx = (b[0] + b[3]) // 2
    stern = m['meta'].get('port') == 'stern'
    if not stern:
        y0 = b[1] if sg > 0 else b[4]
        spots = [[b[0] - 3, y0 + 10 * sg], [b[3] + 3, y0 + 10 * sg], [b[0] - 3, y0 + 4 * sg], [b[3] + 3, y0 + 4 * sg], [b[0] - 2, y0 - 3 * sg], [b[3] + 2, y0 - 3 * sg], [cx, y0 - 6 * sg], [cx - 5, y0 - 10 * sg]]
    else:
        ex = -1                                                                  # 船尾追擊砲：砲口朝 −x
        x0 = b[0] if ex > 0 else b[3]
        cyg = (b[1] + b[4]) // 2
        spots = [[x0 + 10 * ex, b[1] - 3], [x0 + 10 * ex, b[4] + 3], [x0 + 4 * ex, b[1] - 3], [x0 + 4 * ex, b[4] + 3], [x0 - 3 * ex, b[1] - 2], [x0 - 3 * ex, b[4] + 2], [x0 - 6 * ex, cyg], [x0 - 10 * ex, cyg - 5]]
    n = min(g['crew'], 8)
    got, why = 0, []
    for i in range(n):
        sx, sy = spots[i]
        found = None
        reasons = {}
        for r in range(0, 5):
            for dy in range(-r, r + 1):
                for dx in range(-r, r + 1):
                    if max(abs(dx), abs(dy)) != r or found:
                        continue
                    k = (sx + dx, sy + dy)
                    if k in taken:
                        reasons['taken'] = reasons.get('taken', 0) + 1
                        continue
                    z = standZ(k[0], k[1], z0, z1, 14)
                    if z < 0:
                        reasons['不能站'] = reasons.get('不能站', 0) + 1
                        continue
                    bl = blocked(k[0], k[1], z)
                    if bl:
                        reasons[bl] = reasons.get(bl, 0) + 1
                        continue
                    found = k
        if found:
            taken.add(found)
            got += 1
        else:
            why.append({'spot': [sx, sy], 'reasons': reasons})
    rows.append((m['name'].split('/')[-1], code, got, n, g['min'], why))
short = [r for r in rows if r[2] < r[3]]
print('砲 %d；站不滿 %d：' % (len(rows), len(short)))
for r in short if not only else [r for r in rows if r[0].startswith(only)]:
    print('  %s（%s）%d／%d（最少 %d）%s' % (r[0], r[1], r[2], r[3], r[4], json.dumps(r[5], ensure_ascii=False)[:400]))
