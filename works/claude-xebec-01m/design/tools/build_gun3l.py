# 利劍號 步驟 9（TASK-0022）：3 磅砲通用部件落格 —— 建子作品（parent 船殼、tags=sub、0.05 m）、stampvox、固定點、作品預設 meta kind=gun, gun=3l
#   出處：crest-001-daniuchuan-01m/design/tools/build_gun_types.py 的 emit_gun（建、記 0.05、落格、固定點、預設 meta 的順序）＋本船 tools/build_masts.py 的 cli／voxels（只認 exit 0、已有就跳過）。
#   輸入：design/draft_gun3l.py 的 masks/gun3l/gun-3l.vox.txt、verify_gun3l.json；plan.json gun3l（work、title）。
#   用法：python -I -X utf8 tools/build_gun3l.py   · 重跑安全：作品已有正確格數就不重落；固定點 overwrite=1；meta 是合併。
import json, os, re, subprocess, sys

sys.stdout.reconfigure(encoding='utf-8')
HERE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(HERE, 'tools'))
import wio
P = 'persona=Claude-Ojousama'
T = 'claude-xebec-01m'
G = json.load(open(os.path.join(HERE, 'plan.json'), encoding='utf-8'))['gun3l']
V = json.load(open(os.path.join(HERE, 'verify_gun3l.json'), encoding='utf-8'))
W = G['work']
VOX = os.path.join(HERE, 'masks', 'gun3l', 'gun-3l.vox.txt')
NOTE = '步驟 9（TASK-0022；design/draft_gun3l.py，Ship_Guns §4.3）'


def cli(*args):
    r = subprocess.run([wio.SENATE, 'cmd', 'sculpture'] + [x for a in args for x in ('--arg', a)], capture_output=True, text=True, encoding='utf-8', errors='replace')
    out = r.stdout + r.stderr
    line = next((l for l in out.splitlines() if l.startswith('✓') or l.startswith('✗')), out.strip().splitlines()[-1] if out.strip() else '')
    print('  exit=%d %s' % (r.returncode, line[:200]), flush=True)
    if r.returncode != 0:
        print(out[-1500:])
        sys.exit(1)
    return out


def voxels(work):
    r = subprocess.run([wio.SENATE, 'cmd', 'sculpture', '--arg', 'op=stats', '--arg', 'work=' + work, '--arg', 'links=none'], capture_output=True, text=True, encoding='utf-8', errors='replace')
    if r.returncode != 0:
        return None
    m = re.search(r'total_voxels = (\d+)', r.stdout + r.stderr)
    return int(m.group(1)) if m else None


n = sum(1 for l in open(VOX, encoding='utf-8') if l.strip() and not l.startswith('#'))
assert n == V['cells'], (n, V['cells'])
have = voxels(W)
if have is None:
    cli('op=work', 'sub=create', P, 'work=' + W, 'title=' + G['title'], 'size=%d,%d,%d' % tuple(V['size']), 'parent_work=' + T, 'tags=sub')
    cli('op=work', 'sub=update', P, 'work=' + W, 'meters_per_voxel=0.05')
    have = 0
if have == n:
    print('· %s 已經有 %d 格' % (W, n))
elif have == 0:
    cli('op=stampvox', P, 'work=' + W, 'voxels=' + os.path.abspath(VOX).replace('\\', '/'), 'at=0,0,0', 'expect_pixels=%d' % n, 'draft=0', 'share=0')
else:
    raise SystemExit('✗ %s 有 %d 格，不是 0 也不是 %d' % (W, have, n))
for an, at in sorted(V['anchors'].items()):
    cli('op=work', 'sub=anchor', P, 'work=' + W, 'name=' + an, 'at=%d,%d,%d' % tuple(at), 'overwrite=1', 'note=' + NOTE)
cli('op=work', 'sub=meta', P, 'work=' + W, 'part=work', 'meta=' + json.dumps({'kind': 'gun', 'gun': '3l'}, separators=(',', ':')), 'note=' + NOTE + '：通用部件預設 meta')
print(cli('op=stats', 'work=' + W, 'links=none', 'structure=1', 'mirror=x:%d' % (V['size'][0] // 2))[-1500:])
