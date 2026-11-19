# Source: gura-pinas-01m/design/tools/build_gunfittings.py (Blue Shark, TASK-0967) -- rewritten for the Star (TASK-0019 step 9).
# Step 9 gun fittings: the sub-work (create + stamp + anchors ring-… / deck-…), the assembly link 砲具 (meta kind=gunfittings,
#   Ship_Guns 2.2: gun fittings are game meta), the gun tackle hung on the assembly (overwrite=1).
#   Usage: python -X utf8 tools/build_gunfittings.py <design>   (SENATE = wrapper path)
#   * the sub-work exists ⇒ not re-created / re-stamped (cell changes go through delta_apply); anchors, ropes overwrite=1.
import json, os, re, subprocess, sys

sys.stdout.reconfigure(encoding='utf-8')
design = os.path.abspath(sys.argv[1])
SENATE = os.environ.get('SENATE', 'senate')
PERSONA = 'Claude-Ojousama'
HULL = 'claude-baghlah-01m'
ASM = HULL + '-assembly'
NOTE = '步驟 9 砲具（TASK-0019；design/draft_gunfittings.py）'
WORKS = os.path.dirname(os.path.dirname(design))
FB = json.load(open(os.path.join(design, 'plan.json'), encoding='utf-8'))['gunfittings_build']
PTS = json.load(open(os.path.join(design, 'gunfittings_points.json'), encoding='utf-8'))['anchors']
ROPES = json.load(open(os.path.join(design, 'gun_ropes.json'), encoding='utf-8'))['ropes']


def cli(*args):
    r = subprocess.run([SENATE, 'cmd', 'sculpture'] + [a for kv in args for a in ('--arg', kv)], capture_output=True, text=True, encoding='utf-8', errors='replace')
    out = r.stdout + r.stderr
    if r.returncode:
        print(out[-1500:])
        raise SystemExit('✗ exit %d: %s' % (r.returncode, ' '.join(args[:6])))
    return out


w = FB['work']
if not os.path.exists(os.path.join(WORKS, w, 'work.json')):
    cli('op=work', 'sub=create', 'persona=' + PERSONA, 'work=' + w, 'title=' + FB['title'], 'parent_work=' + HULL, 'size=420,160,120', 'tags=sub')
    cli('op=work', 'sub=update', 'persona=' + PERSONA, 'work=' + w, 'meters_per_voxel=0.1')
    path = os.path.join(design, 'masks', 'gunfittings', 'gunfittings.vox.txt')
    n = sum(1 for l in open(path, encoding='utf-8') if l.strip() and not l.startswith('#'))
    out = cli('op=stampvox', 'persona=' + PERSONA, 'work=' + w, 'voxels=' + path, 'at=0,0,0', 'expect_pixels=%d' % n, 'share=0')
    m = re.search(r'placed\D{0,12}(\d[\d,]*)', out)
    got = int(m.group(1).replace(',', '')) if m else None
    if got != n:
        print(out[-1500:])
        raise SystemExit('✗ placed %s != %d' % (got, n))
    print('✓ created %s, stampvox %d' % (w, n), flush=True)
else:
    print('· exists', w)
for an, at in sorted(PTS.items()):
    cli('op=work', 'sub=anchor', 'persona=' + PERSONA, 'work=' + w, 'name=' + an, 'at=%d,%d,%d' % tuple(at), 'overwrite=1', 'note=' + NOTE + '：砲具的環')
print('✓ anchors %d' % len(PTS), flush=True)
links = json.load(open(os.path.join(WORKS, ASM, 'links.json'), encoding='utf-8'))
have = {l['name'] for l in (links if isinstance(links, list) else links.get('links', []))}
if FB['link'] not in have:
    cli('op=work', 'sub=link', 'persona=' + PERSONA, 'work=' + ASM, 'name=' + FB['link'], 'source_work=' + w, 'at=0,0,0',
        'meta=' + json.dumps(FB['link_meta'], separators=(',', ':')), 'note=' + NOTE)
    print('✓ link', FB['link'])
for i, r in enumerate(ROPES):
    cli('op=work', 'sub=rope', 'persona=' + PERSONA, 'work=' + ASM, 'name=' + r['name'], 'from=' + r['from'], 'to=' + r['to'], 'slack=%g' % r['slack'],
        'color=' + r['color'], 'thickness=%g' % r['thickness'], 'group=' + r['group'], 'overwrite=1', 'note=' + NOTE + '：砲索')
    if (i + 1) % 40 == 0:
        print('  ropes %d / %d' % (i + 1, len(ROPES)), flush=True)
print('✓ ropes %d' % len(ROPES))
