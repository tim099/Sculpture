# 階段七（TASK-0489）的檢查工具：外板清單 vs 作品
#   python -I check_planking.py pre    雕之前：清單逐格對作品現況（overwrite 清單只能蓋到該蓋的顏色、一般清單只能落在空格）、清單互斥、鏡像、
#                                      合起來的模型不漏水＋反向對照（拿掉幾格外板要報得出漏）、連通
#   python -I check_planking.py post   雕完：結果帳（階段七前 ＋ 清單 ⇒ 應有，跟 events 重播逐格比）、不漏水、連通、空腔
import sys, os, glob, json, hashlib
sys.stdout.reconfigure(encoding="utf-8")
import numpy as np
from scipy import ndimage
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from replay import replay                 # noqa: E402
import draft_planking as DP               # noqa: E402

W = 'D:/Unity/Valhalla/Sculpture/works/basecamp-frigate-constitution-01m'
DES = W + '/design'
mode = sys.argv[1]
V = json.load(open(DES + '/verify_planking.json', encoding='utf-8'))
P = json.load(open(DES + '/plan.json', encoding='utf-8'))['planking']
FIRST7 = None


def load_list(f):
    out = []
    for line in open(f, encoding='utf-8'):
        if line.strip() and not line.startswith('#'):
            out.append(tuple(int(v) for v in line.split(',')))
    return out


lists = {L['name']: (L, load_list(os.path.join(DES, L['file']))) for L in V['lists']}
rep = {}
ok = True


def check(name, cond, detail=''):
    global ok
    rep[name] = {'ok': bool(cond), 'detail': detail}
    ok &= bool(cond)
    print(('✓ ' if cond else '✗ ') + name + ('  ' + str(detail) if detail != '' else ''))


# ───────── 清單本身 ─────────
allc = {}
for n, (L, cells) in lists.items():
    # git 的 autocrlf 在別台 checkout 會變 CRLF；清單是用 LF 雕的（事件記的 sha256 也是 LF）⇒ 先轉回 LF 再算（同 ledger_stage6.py）
    raw = open(os.path.join(DES, L['file']), 'rb').read().replace(bytes([13, 10]), bytes([10]))
    check('%s sha256 ＝ verify' % n, hashlib.sha256(raw).hexdigest() == L['sha256'])
    keys = [c[:3] for c in cells]
    check('%s 格數 %d、沒有重複' % (n, len(cells)), len(set(keys)) == len(keys) == L['cells'])
    for k in keys:
        allc.setdefault(k, []).append(n)
dup = {k: v for k, v in allc.items() if len(v) > 1}
check('清單之間互斥', not dup, len(dup))
mir = sum(1 for (x, y, z) in allc if (x, 2 * DP.YC - y, z) not in allc)
check('兩舷鏡像', mir == 0, mir)
col_of = {c[:3]: c[3] for _, cells in lists.values() for c in cells}

if mode == 'pre':
    vox = {k: v[0] for k, v in replay(W).items()}
    pre = vox
    sc = set(P['paint']['structure_colors'])
    for n, (L, cells) in lists.items():
        cur = [vox.get(c[:3]) for c in cells]
        if n == 'dub':
            bad = sum(1 for v in cur if v != 141)
            check('dub：每一格現在都是肋骨（141）', bad == 0, bad)
        elif n == 'paint_struct':
            bad = sum(1 for v in cur if v not in sc)
            check('paint_struct：每一格現在都是龍骨／艏艉柱／deadwood／gripe 的顏色', bad == 0, bad)
        else:
            bad = sum(1 for v in cur if v is not None)
            check('%s：每一格現在都是空的' % n, bad == 0, bad)
    after = dict(vox)
    after.update(col_of)
else:
    vox_ev = replay(W)
    after = {k: v[0] for k, v in vox_ev.items()}
    # 階段七前 ＝ 第一個外板事件之前的重播
    names = sorted({v[1] for v in vox_ev.values()})
    shas = {L['sha256']: n for n, (L, _) in lists.items()}
    ev7 = []
    for f in sorted(glob.glob(W + '/events/*/*.json')):
        e = json.load(open(f, encoding='utf-8'))
        if e.get('op') == 'stampvox' and (e.get('source') or {}).get('sha256') in shas:
            ev7.append((os.path.basename(os.path.dirname(f)) + '/' + os.path.basename(f), shas[e['source']['sha256']], len(e['placed_colored']), e))
    check('外板事件 %d 刀、每份清單各一刀' % len(ev7), sorted(n for _, n, _, _ in ev7) == sorted(lists))
    for name, n, placed, e in ev7:
        check('%s placed %d ＝ 清單 %d' % (n, placed, lists[n][0]['cells']), placed == lists[n][0]['cells'])
    first = min(name for name, _, _, _ in ev7)
    pre = {k: v[0] for k, v in replay(W, upto=first).items()}
    expect = dict(pre)
    expect.update(col_of)
    miss = sum(1 for k in expect if k not in after)
    extra = sum(1 for k in after if k not in expect)
    diffc = sum(1 for k in expect if k in after and after[k] != expect[k])
    check('結果帳：應有 %d ／ 實有 %d' % (len(expect), len(after)), miss == extra == diffc == 0,
          {'缺': miss, '多': extra, '顏色不同': diffc})
    touched = sum(1 for k, c in pre.items() if after.get(k) != c and k not in col_of)
    check('階段七前的格（清單以外）被動到 0', touched == 0, touched)
    later = [f for f in sorted(glob.glob(W + '/events/*/*.json'))
             if os.path.basename(os.path.dirname(f)) + '/' + os.path.basename(f) > first]
    check('第一刀之後的事件只有外板那幾刀', len(later) == len(ev7) - 1, len(later))

# ───────── 結構：不漏水、反向對照、連通 ─────────
m = DP.Model(DES)
m.lines()
m.hull()
X0, NDY, NZ = DP.X0, DP.NDY, DP.NZ
NY = 2 * NDY - 1
solid = np.zeros((len(m.xs), NY, NZ), bool)
for (x, y, z) in after:
    solid[x - X0, y - DP.YC + NDY - 1, z] = True
Sf = DP.full(m.S)


def leaks(sol):
    zz = m.zs[None, None, :]
    top = np.where(m.xin, m.zt, NZ)[:, None, None]
    dom = np.broadcast_to(zz <= top, sol.shape)
    air = ~sol & dom
    lab, _ = ndimage.label(np.pad(air, 1, constant_values=True))
    lab = lab[1:-1, 1:-1, 1:-1]
    out = lab == lab[0, 0, 0]
    return np.argwhere(air & Sf & out)


lk = leaks(solid)
check('不漏水：肋骨頂以下，船內的空氣跟船外不相通', len(lk) == 0, len(lk))
# 反向對照：從外板清單挑 3 格（舷側、船底、船尾面各一）拿掉
probe = []
plank = [c for n, (L, cells) in lists.items() if n.startswith('plank') for c in cells]
pk = {c[:3] for c in plank}

def backed_by_air(c):
    """拿掉它會不會真的開一個洞：至少一個鄰格在船殼裡而且是空氣（背後是肋骨的格，拿掉也不漏 —— 那不是好探針）。"""
    x, y, z = c
    inner = outer = False                # 兩邊都要碰到空氣：背後是船艙、外面是船外（wales 那段外面還有一層，拿掉內層不漏 —— 那是對的）
    for d in ((1, 0, 0), (-1, 0, 0), (0, 1, 0), (0, -1, 0), (0, 0, 1), (0, 0, -1)):
        k = (x + d[0], y + d[1], z + d[2])
        i, j = k[0] - X0, k[1] - DP.YC + NDY - 1
        if 0 <= i < len(m.xs) and 0 <= j < NY and 0 <= k[2] < NZ and k not in after:
            if Sf[i, j, k[2]]:
                inner = True
            else:
                outer = True
    return inner and outer


for want in ((449, 100, 'side'), (300, 12, 'bottom'), (108, 110, 'stern')):
    cand = [c for c in pk if abs(c[0] - want[0]) <= 6 and c[1] > DP.YC and backed_by_air(c)]
    probe.append(min(cand, key=lambda c: abs(c[2] - want[1]) + abs(c[0] - want[0])))
hit = []
for (x, y, z) in probe:                  # 一次只拿掉一格 —— 三格一起拿，整個船艙都會漏，「報得出來」就變成必然
    holes = solid.copy()
    holes[x - X0, y - DP.YC + NDY - 1, z] = False
    hit.append(len(leaks(holes)) > 0)
check('反向對照：外板逐格拿掉 %s（背後是船艙空氣的格）⇒ 每一次都報漏' % probe, all(hit), hit)
lab, n = ndimage.label(solid)
check('全船 face-connected 元件 ＝ 1', n == 1, n)
rep['ok'] = ok
json.dump(rep, open(os.path.join(os.environ.get('TEMP', '.'), 'check_planking_%s.json' % mode), 'w', encoding='utf-8'), ensure_ascii=False, indent=1)
print('ALL OK' if ok else 'FAIL')
