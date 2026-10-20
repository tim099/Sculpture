# 越嶺號 階段四落格（TASK-0761）：新通用部件 bombardella（建作品、落格、固定點）⇒ 五個武器模型掛在 甲板-bow ⇒ 兩張弓的弓弦（繩＋meta）
#   用法：python -I -X utf8 tools/build_guns.py
import os, sys, json, re, subprocess

HERE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.stdout.reconfigure(encoding='utf-8')
P = 'persona=kotoko'
PL = json.load(open(os.path.join(HERE, 'guns_placement.json'), encoding='utf-8'))
HOST = PL['host_work']


def cli(*args, ok=(0,)):
    r = subprocess.run(['senate', 'cmd', 'sculpture'] + [x for a in args for x in ('--arg', a)], capture_output=True, text=True, encoding='utf-8', errors='replace')
    out = r.stdout + r.stderr
    line = next((l for l in out.splitlines() if l.startswith('✓') or l.startswith('✗')), out.strip().splitlines()[-1] if out.strip() else '')
    print('  exit=%d %s' % (r.returncode, line[:170]), flush=True)
    if r.returncode not in ok:
        print(out[-1500:])
        sys.exit(1)
    return out


c = PL['components']['bombardella']
W = c['work']
if subprocess.run(['senate', 'cmd', 'sculpture', '--arg', 'op=work', '--arg', 'sub=show', '--arg', 'work=' + W], capture_output=True).returncode:
    cli('op=work', 'sub=create', P, 'id=' + W, 'title=bombardella（15 世紀鍛鐵箍砲＋後膛藥室、固定在挖槽的木床上；通用部件，0.05 m）',
        'parent_work=kotoko-fusta-01m', 'size=%d,%d,%d' % tuple(c['size']), 'tags=sub')
    cli('op=work', 'sub=update', P, 'work=' + W, 'meters_per_voxel=0.05')
have = int(re.search(r'total_voxels = (\d+)', cli('op=stats', 'work=' + W)).group(1))
if have == 0:
    r = subprocess.run([sys.executable, '-I', '-X', 'utf8', os.path.join(HERE, 'tools', 'stamp_lists.py'), W, '0', os.path.join(HERE, 'masks', 'guns', 'bombardella.vox.txt')], text=True, encoding='utf-8')
    if r.returncode:
        sys.exit(1)
elif have != c['cells']:
    sys.exit('✗ %s 已有 %d 格 ≠ %d' % (W, have, c['cells']))
NOTE = {'muzzle': '砲口內膛那一格（空格）', 'breech': '砲尾（砲管後端、接藥室）', 'cascabel': '藥室後端（楔子頂住的地方）'}
for nm, at in c['anchors'].items():
    cli('op=work', 'sub=anchor', P, 'work=' + W, 'name=' + nm, 'at=%d,%d,%d' % tuple(at), 'overwrite=1', 'note=' + NOTE[nm])

for r in PL['rows']:
    cli('op=work', 'sub=model', P, 'work=' + HOST, 'name=' + r['name'], 'source_work=' + r['source_work'], 'at=%g,%g,%g' % tuple(r['at']),
        'pivot=%g,%g,%g' % tuple(r['pivot']), 'rotate=%g,%g,%g' % tuple(r['rotate']), 'scale=%g' % r['scale'], 'mirror=none', 'overwrite=1',
        'meta=' + json.dumps(r['meta'], ensure_ascii=False), 'note=階段四（draft_guns.py）')

rows = []
for r in PL['rows']:
    if r['comp'] != 'bow':
        continue
    for nm, a, b in (('弦-a', 'string-a', 'nock'), ('弦-b', 'nock', 'string-b')):
        name = '%s-%s' % (r['name'], nm)
        cli('op=work', 'sub=rope', P, 'work=' + HOST, 'name=' + name, 'from=model:%s/%s' % (r['name'], a), 'to=model:%s/%s' % (r['name'], b),
            'slack=1', 'thickness=0.15', 'color=#d8c8a0', 'group=guns/bowstrings', 'overwrite=1', 'note=階段四 弓弦（造船規格 §2.2 武器演出）')
        rows.append(('rope', name, {'kind': 'bowstring', 'anim': 'gun', 'rest': 'nock', 'fire': 'nock-fire'}))
f = os.path.join(HERE, 'guns_meta.tsv')
with open(f, 'w', encoding='utf-8', newline='\n') as fh:
    fh.write(''.join('%s\t%s\t%s\n' % (a, b, json.dumps(m, ensure_ascii=False)) for a, b, m in rows))
cli('op=work', 'sub=meta', P, 'work=' + HOST, 'file=' + f.replace('\\', '/'))
