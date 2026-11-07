# TASK-1257 走路檢查：照組裝件現況（門是模型、不擋人）找站得住的格（那格空、腳下實心、頭上 HEAD 格空），
#   相鄰四格、一步高低差 ≤ STEP 格就連；每一組 起點 → 終點 走不走得到、走不走得回來。
#   · 尋路的規則（頭上 1.2 m、一步 0.3 m）＝ --step=3（預設）；第一人稱（往上 0.6 m、往下 0.8 m）＝ --fp
#   · 反向對照 --plug=<組名>：把那一組的門洞（或梯子）用實心堵起來 ⇒ 那一組要走不到
#   用法：python -I -X utf8 tools/walk_access.py <design> [--fp] [--plug=<組名>]
import sys, os, json, subprocess, tempfile
from collections import deque
import numpy as np

sys.stdout.reconfigure(encoding='utf-8')
D = os.path.abspath(sys.argv[1])
FP = '--fp' in sys.argv
UP, DOWN = (6, 8) if FP else (3, 3)
HEAD = 12
plug = next((a.split('=', 1)[1] for a in sys.argv[2:] if a.startswith('--plug=')), None)
with tempfile.TemporaryDirectory() as d:
    out = os.path.join(d, 'a.txt').replace('\\', '/')
    subprocess.run(['senate', 'cmd', 'sculpture', '--arg', 'op=export', '--arg', 'format=list', '--arg', 'work=gura-tridente-01m-assembly', '--arg', 'out=' + out],
                   capture_output=True, check=True)
    A = np.loadtxt(out, delimiter=',', comments='#', dtype=np.int32)
NZ = 260
A = A[A[:, 2] < NZ]
g = np.zeros((1100, 400, NZ), bool)
g[A[:, 0], A[:, 1], A[:, 2]] = True
# 起點、終點：（站的那一格）；門洞那幾格（堵的反向對照）
PAIRS = {
    '船尾門-middle': ((95, 200, 117), (78, 200, 117), ((84, 92), (197, 203), (117, 131))),
    '船尾門-upper': ((92, 200, 140), (74, 200, 140), ((80, 88), (197, 203), (140, 154))),
    '船尾門-spar': ((88, 200, 163), (70, 200, 163), ((76, 84), (197, 203), (163, 177))),
    '船頭門-P': ((700, 190, 142), (723, 190, 149), ((712, 719), (188, 192), (149, 162))),
    '船頭門-S': ((700, 210, 142), (723, 210, 149), ((712, 719), (208, 212), (149, 162))),
    'poop 門-P': ((220, 184, 160), (234, 184, 160), ((228, 228), (182, 186), (160, 175))),
    'poop 門-S': ((220, 216, 160), (234, 216, 160), ((228, 228), (214, 218), (160, 175))),
    'gallery 小艙-middle': ((100, 235, 117), (100, 266, 117), None),
    'gallery 小艙-upper': ((100, 235, 140), (100, 263, 140), None),
    'gallery 小艙-spar': ((100, 235, 163), (80, 256, 163), None),
    'orlop → 貨艙平台（後艙口梯）': ((290, 200, 68), (330, 230, 31), ((300, 312), (196, 204), (31, 66))),
    'orlop → 貨艙平台（主艙口梯）': ((520, 210, 67), (470, 230, 31), ((477, 500), (196, 204), (31, 66))),
    '貨艙平台 → 後彈藥庫': ((330, 230, 31), (270, 200, 31), ((296, 296), (198, 202), (31, 45))),
    '貨艙平台 → 前彈藥庫': ((470, 230, 31), (600, 200, 31), ((562, 562), (198, 202), (31, 45))),
    '貨艙平台 → 艙底': ((420, 230, 31), (380, 200, 9), ((383, 400), (196, 204), (9, 30))),
}
for pg in (plug.split(',') if plug else []):          # 逗號分開 ⇒ 一起堵（船頭兩扇互為繞路）
    sl = PAIRS[pg][2]
    g[sl[0][0]:sl[0][1] + 1, sl[1][0]:sl[1][1] + 1, sl[2][0]:sl[2][1] + 1] = True


def stand(x, y, z):
    return 0 < z < NZ - HEAD and not g[x, y, z] and g[x, y, z - 1] and not g[x, y, z:z + HEAD].any()


def near(x, y, z):
    for dz in range(0, 9):
        for zz in (z - dz, z + dz):
            if stand(x, y, zz):
                return (x, y, zz)
    return None


def reach(a, b, lim=400000):
    q, seen = deque([a]), {a}
    while q:
        c = q.popleft()
        if c == b:
            return True
        x, y, z = c
        for dx, dy in ((1, 0), (-1, 0), (0, 1), (0, -1)):
            for dz in range(-DOWN, UP + 1):
                n = (x + dx, y + dy, z + dz)
                if n not in seen and stand(*n):
                    seen.add(n)
                    q.append(n)
        if len(seen) > lim:
            return None
    return False


res = {}
for nm, (a, b, _) in PAIRS.items():
    sa, sb = near(*a), near(*b)
    if not sa or not sb:
        res[nm] = '起點／終點站不住 %s %s' % (sa, sb)
        continue
    res[nm] = {'去': reach(sa, sb), '回': reach(sb, sa), 'from': sa, 'to': sb}
print(json.dumps({'rule': 'fp' if FP else 'nav', 'up': UP, 'down': DOWN, 'head': HEAD, 'plug': plug}, ensure_ascii=False))
for nm, r in res.items():
    print(' ', nm, r)
