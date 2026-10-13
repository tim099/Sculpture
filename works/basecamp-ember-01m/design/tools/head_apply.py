# 餘燼號 階段九 船頭：照 masks/head/ 下 CLI —— 建 knee／一舷裝飾／船首像三件子作品、落格、關聯進組裝件；
#   錨直接關聯憲法號那一隻（catted：ring 頂貼 cathead 某一格正下方，從端面往船裡試、兩舷都不撞的第一格）；
#   knee 登記 bobstay-1／2 固定點，組裝件拉 bobstay 兩條（另一端是艏斜桅已有的 bobstay-1／2）。
# 用法：python -I head_apply.py <design 資料夾> [--dry]（重跑：子作品已在 ⇒ 不重建；關聯／繩已在 ⇒ 不重掛）
import sys, os, json, subprocess
import numpy as np
sys.stdout.reconfigure(encoding='utf-8')
D = os.path.abspath(sys.argv[1])
DRY = '--dry' in sys.argv
sys.path.insert(0, D)
from draft_ladders import existing_links, export_hidden   # noqa: E402

HULL = 'basecamp-ember-01m'
H = json.load(open(os.path.join(D, 'plan.json'), encoding='utf-8'))['head_build']
ASM = H['assembly']
SW = H['subworks']
HD = os.path.join(D, 'masks', 'head')
ok = bad = 0


def cli(args, show=False):
    global ok, bad
    if DRY:
        print('DRY', ' '.join(args[:8]))
        return 0, ''
    r = subprocess.run(['senate', 'cmd', 'sculpture'] + sum([['--arg', a] for a in args], []), capture_output=True, text=True, encoding='utf-8', errors='replace')
    if r.returncode:
        bad += 1
        print('✗', ' '.join(args[:6]), (r.stdout + r.stderr)[-400:])
    else:
        ok += 1
        if show:
            print('\n'.join(l for l in r.stdout.splitlines() if l.startswith('✓') or 'placed =' in l))
    return r.returncode, r.stdout


def xyz(v):
    return ','.join('%d' % c for c in v)


def load(p):
    return np.loadtxt(p, delimiter=',', comments='#', dtype=np.int32, ndmin=2, encoding='utf-8')


# ── 錨的位置（先算，零寫入）──
have = set(existing_links(ASM))
hide = [h for h in H['hide_links'] if h in have]
a = export_hidden(ASM, hide)
assert len(a) == H['assembly_voxels'], ('組裝件現況對不上', len(a))
world = set(map(tuple, a[:, :3].tolist()))
knee = load(os.path.join(HD, 'knee.vox.txt'))
side = load(os.path.join(HD, 'side.vox.txt'))
fig = load(os.path.join(HD, 'figurehead.vox.txt'))
sb = SW['side']['box']
ax_, ay_, az_ = sb['at']
my = 321 - ay_ - sb['size'][1]
world |= set(map(tuple, knee[:, :3].tolist())) | set(map(tuple, fig[:, :3].tolist()))
side_S = {(int(x + ax_), int(y + ay_), int(z + az_)) for x, y, z, c in side}
side_P = {(int(x + ax_), int(sb['size'][1] - 1 - y + my), int(z + az_)) for x, y, z, c in side}
world |= side_S | side_P
side_col = {(int(x + ax_), int(y + ay_), int(z + az_)): int(c) for x, y, z, c in side}
anc = export_hidden(H['anchor']['work'], [])
aset = set(map(tuple, anc[:, :3].tolist()))
RING = (23, 16, 56)                                  # 憲法號：at 630,189,73 ＋ (23,16,56) ＝ cathead 端那格 (653,205,130) 正下方
assert RING in aset, '憲法號錨的 ring 頂不在 (23,16,56)'
A_SIZE = (47, 33, 58)
cats = sorted([k for k, c in side_col.items() if c in (36, 248) and k[1] > 175 and k[2] > 145], key=lambda k: (-k[1], -k[0]))
pick = None
tried = 0
for (cx, cy, cz) in cats:
    if (cx, cy, cz - 1) in world:
        continue
    at = (cx - RING[0], cy - RING[1], cz - 1 - RING[2])
    S = {(at[0] + x, at[1] + y, at[2] + z) for x, y, z in aset}
    atP = (at[0], 321 - A_SIZE[1] - at[1], at[2])
    P = {(atP[0] + x, atP[1] + (A_SIZE[1] - 1 - y), atP[2] + z) for x, y, z in aset}
    tried += 1
    if not (S & world) and not (P & world):
        pick = {'cathead_cell': [cx, cy, cz], 'at_S': list(at), 'at_P': list(atP), 'tried': tried}
        break
print('錨：', pick)
assert pick, '找不到兩舷都不撞的位置'

if DRY:
    print('（--dry：只算到這裡）')
    sys.exit(0)

# ── 子作品 ──
files = {'knee': ('knee.vox.txt', '1024,320,800', len(knee)), 'side': ('side.vox.txt', xyz(sb['size']), len(side)),
         'figurehead': ('figurehead.vox.txt', '1024,320,800', len(fig))}
for key, (fname, size, n) in files.items():
    E = SW[key]
    w = E['id']
    rc, out = cli(['op=work', 'sub=show', 'work=' + w])
    if rc:
        bad -= 1
        cli(['op=work', 'sub=create', 'persona=basecamp', 'id=' + w, 'title=' + E['title'], 'size=' + size, 'parent_work=' + HULL, 'tags=sub'], show=True)
        cli(['op=work', 'sub=update', 'persona=basecamp', 'work=' + w, 'meters_per_voxel=0.1'])
        path = os.path.join(HD, fname).replace('\\', '/')
        cli(['op=stampvox', 'persona=basecamp', 'work=' + w, 'voxels=' + path, 'at=0,0,0', 'expect_pixels=%d' % n], show=True)
    else:
        print('· 已在：' + w)

# ── 關聯 ──
links = [(SW['knee']['link'], SW['knee']['id'], [0, 0, 0], '', '階段九：knee of the head（憲法號新圖紙 13 照換算）'),
         (SW['side']['link'], SW['side']['id'], sb['at'], '', '階段九：船頭裝飾一舷（cheeks、卷草、火焰紋章、hawse、rails、cathead）'),
         (SW['side']['mirror_link'], SW['side']['id'], [ax_, my, az_], 'y', '階段九：船頭裝飾另一舷（mirror=y）'),
         (SW['figurehead']['link'], SW['figurehead']['id'], [0, 0, 0], '', '階段九：船首像「浴火的鳳凰」（原創）'),
         ('錨-S', H['anchor']['work'], pick['at_S'], '', '階段九：S 舷 bower anchor —— 直接引用憲法號那一隻；catted，ring 頂貼 cathead 端下方'),
         ('錨-P', H['anchor']['work'], pick['at_P'], 'y', '階段九：P 舷 bower anchor（mirror=y）')]
have = set(existing_links(ASM))
for name, w, at, mirror, note in links:
    if name in have:
        print('· 關聯已在：' + name)
        continue
    args = ['op=work', 'sub=link', 'persona=basecamp', 'work=' + ASM, 'name=' + name, 'source_work=' + w, 'at=' + xyz(at), 'note=' + note]
    if mirror:
        args.append('mirror=' + mirror)
    cli(args, show=True)

# ── bobstay ──
for an in json.load(open(os.path.join(HD, 'knee_anchors.json'), encoding='utf-8')):
    cli(['op=work', 'sub=anchor', 'persona=basecamp', 'work=' + SW['knee']['id'], 'name=' + an['name'], 'at=' + xyz(an['at']), 'overwrite=1',
         'note=bobstay（憲法號 knee 的同名點照換算 %s → knee 中線那一層最前面那格）' % an['from_constitution']])
    cli(['op=work', 'sub=rope', 'persona=basecamp', 'work=' + ASM, 'name=' + an['name'], 'from=%s/%s' % (SW['knee']['link'], an['name']),
         'to=艏斜桅/' + an['name'], 'overwrite=1', 'slack=1', 'color=#2b2620', 'thickness=1', 'group=standing/stays', 'note=bobstay（階段九；同憲法號）'], show=True)
json.dump(pick, open(os.path.join(D, 'masks', 'head', 'anchor_pick.json'), 'w', encoding='utf-8', newline='\n'), ensure_ascii=False, indent=1)
print('ok %d / bad %d' % (ok, bad))
