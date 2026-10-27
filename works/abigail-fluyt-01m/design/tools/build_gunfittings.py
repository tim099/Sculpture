# 階段十二落格：砲具子作品（貼＋固定點 ring-／deck-…）、組裝件關聯 砲具、砲索（掛在組裝件，overwrite=1）
#   用法：python -I -X utf8 tools/build_gunfittings.py <design>
#   · 子作品已存在 ⇒ 不重建、不重貼（改格子走 delta_apply）；固定點、繩 overwrite=1；關聯同名 ⇒ ok 2
import json, os, re, subprocess, sys

sys.stdout.reconfigure(encoding='utf-8')
design = sys.argv[1]
HULL = 'abigail-fluyt-01m'
ASM = HULL + '-assembly'
WORKS = os.path.dirname(os.path.dirname(os.path.abspath(design)))
FB = json.load(open(os.path.join(design, 'plan.json'), encoding='utf-8'))['gunfittings_build']
PTS = json.load(open(os.path.join(design, 'gunfittings_points.json'), encoding='utf-8'))['anchors']
ROPES = json.load(open(os.path.join(design, 'gun_ropes.json'), encoding='utf-8'))['ropes']
bad = []


def cli(*args, ok=(0,)):
    r = subprocess.run(['senate', 'cmd', 'sculpture'] + [a for kv in args for a in ('--arg', kv)], capture_output=True, text=True, encoding='utf-8', errors='replace')
    if r.returncode not in ok:
        bad.append((' '.join(args[:6]), (r.stdout + r.stderr)[-300:]))
    return r.stdout + r.stderr


w = FB['work']
if not os.path.exists(os.path.join(WORKS, w, 'work.json')):
    cli('op=work', 'sub=create', 'persona=Abigail', 'work=' + w, 'title=' + FB['title'], 'parent_work=' + HULL, 'size=800,320,640', 'tags=sub')
    cli('op=work', 'sub=update', 'persona=Abigail', 'work=' + w, 'meters_per_voxel=0.1')
    path = os.path.join(design, 'masks', 'gunfittings', 'gunfittings.vox.txt')
    n = sum(1 for l in open(path, encoding='utf-8') if l.strip() and not l.startswith('#'))
    out = cli('op=stampvox', 'persona=Abigail', 'work=' + w, 'voxels=' + os.path.abspath(path).replace('\\', '/'), 'at=0,0,0', 'expect_pixels=%d' % n, 'share=0')
    m = re.search(r'placed\D{0,12}(\d[\d,]*)', out)
    if not m or int(m.group(1).replace(',', '')) != n:
        raise SystemExit('✗ placed ≠ %d：%s' % (n, out[-800:]))
    print('✓ 建立 %s（%d 格）' % (w, n), flush=True)
for i, (an, at) in enumerate(sorted(PTS.items())):
    cli('op=work', 'sub=anchor', 'persona=Abigail', 'work=' + w, 'name=' + an, 'at=%d,%d,%d' % tuple(at), 'overwrite=1', 'note=砲具的環（階段十二 TASK-0624；draft_gunfittings.py）')
print('✓ 固定點 %d' % len(PTS), flush=True)
cli('op=work', 'sub=link', 'persona=Abigail', 'work=' + ASM, 'name=' + FB['link'], 'source_work=' + w, 'at=0,0,0', 'note=階段十二（TASK-0624）', ok=(0, 2))
for i, r in enumerate(ROPES):
    cli('op=work', 'sub=rope', 'persona=Abigail', 'work=' + ASM, 'name=' + r['name'], 'from=' + r['from'], 'to=' + r['to'], 'slack=%g' % r['slack'],
        'color=' + r['color'], 'thickness=%g' % r['thickness'], 'group=' + r['group'], 'overwrite=1', 'note=階段十二 砲索（TASK-0624）')
    if (i + 1) % 40 == 0:
        print('  繩 %d／%d' % (i + 1, len(ROPES)), flush=True)
print('✓ 繩 %d；失敗 %d' % (len(ROPES), len(bad)))
for b in bad[:10]:
    print('✗', b)
