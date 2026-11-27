# 蠍子號 步驟 9 落格（TASK-0023）：兩根迴旋砲柱 stampvox 進船首平台子作品（masks/guns/posts.vox.txt；v2）、三門砲的外部模型掛在船首平台子作品（guns_placement.json）—— 8l 一個、pierrier 兩門各兩個（砲＋座，座 kind=gunmount mount_of）。
#   出處：海鷗號 claude-felucca-01m/design/tools/build_guns.py（模型那一段；這艘沒有砲柱）。
#   用法：python -I -X utf8 tools/build_guns.py   · 只認 exit 0；overwrite=1 ⇒ 重跑安全。
import json, os, subprocess, sys

sys.stdout.reconfigure(encoding='utf-8')
HERE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(HERE, 'tools'))
import wio
P = 'persona=Claude-Ojousama'
NOTE = '步驟 9（TASK-0023；design/draft_guns.py）'
GP = json.load(open(os.path.join(HERE, 'guns_placement.json'), encoding='utf-8'))


def cli(*args):
    r = subprocess.run([wio.SENATE, 'cmd', 'sculpture'] + [x for a in args for x in ('--arg', a)], capture_output=True, text=True, encoding='utf-8', errors='replace')
    out = r.stdout + r.stderr
    line = next((l for l in out.splitlines() if l.startswith('✓') or l.startswith('✗')), out.strip().splitlines()[-1] if out.strip() else '')
    print('  exit=%d %s' % (r.returncode, line[:200]), flush=True)
    if r.returncode != 0:
        print(out[-1500:])
        sys.exit(1)
    return out


POSTS = os.path.join(HERE, 'masks', 'guns', 'posts.vox.txt')
want = [tuple(map(int, l.split(','))) for l in open(POSTS, encoding='utf-8') if l.strip() and not l.startswith('#')]
have = {tuple(r[:3]): int(r[3]) for r in wio.export_list(GP['hosts']['bow'], None).tolist()}
todo = [w for w in want if have.get(w[:3]) != w[3]]
if todo:
    assert len(todo) == len(want), ('砲柱只落了一部分？', len(todo), len(want))
    r = subprocess.run([sys.executable, '-I', '-X', 'utf8', os.path.join(HERE, 'tools', 'stamp_lists.py'), GP['hosts']['bow'], '0', POSTS], capture_output=True, text=True, encoding='utf-8')
    print(r.stdout.strip())
    if r.returncode:
        sys.exit(1)
else:
    print('· 砲柱已經落過（%d 格）' % len(want))
for g in GP['models']:
    cli('op=work', 'sub=model', P, 'work=' + GP['hosts'][g['host']], 'name=' + g['name'], 'source_work=' + g['work'],
        'at=%g,%g,%g' % tuple(g['at']), 'pivot=%g,%g,%g' % tuple(g['pivot']), 'scale=%g' % g['scale'], 'rotate=%g,%g,%g' % tuple(g['rotate']),
        'mirror=none', 'meta=' + json.dumps(g['meta'], ensure_ascii=False, separators=(',', ':')), 'overwrite=1', 'note=' + NOTE)
