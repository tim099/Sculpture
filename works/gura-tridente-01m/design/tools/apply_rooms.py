# TASK-0581 落格：照 verify_rooms.json —— 艙房子作品（S 舷一件，0.1 m、parent 船殼、tags sub）→ stampvox（讀回 placed）→ 固定點 <名>.min／.max／.door
#   → 甲板-orlop 子作品裡兩條關聯（艙房 at frame_at；艙房-鏡像 mirror=y）＋ meta kind=rooms（造船規格 §9.2）
#   用法：python -I -X utf8 tools/apply_rooms.py <design>
import json, os, re, subprocess, sys, time

sys.stdout.reconfigure(encoding='utf-8')
D = os.path.abspath(sys.argv[1])
V = json.load(open(os.path.join(D, 'verify_rooms.json'), encoding='utf-8'))
retried = 0


def run(*a):
    return subprocess.run(['senate', 'cmd', 'sculpture'] + [x for kv in a for x in ('--arg', kv)], capture_output=True, text=True, encoding='utf-8', errors='replace')


def cli(*a):
    global retried
    for k in range(5):
        r = run(*a)
        out = r.stdout + r.stderr
        if r.returncode and any(t in out for t in ('IOException', '無法移除要被取代的檔案', 'Unable to remove the file to be replaced')) and k < 4:
            retried += 1
            time.sleep(0.5)
            continue
        break
    if r.returncode:
        print(out[-1200:])
        raise SystemExit('✗ ' + ' '.join(a[:5]))
    return r.stdout


xyz = lambda v: ','.join('%g' % c for c in v)
W = V['work']
if run('op=work', 'sub=show', 'work=' + W).returncode != 0:
    cli('op=work', 'sub=create', 'persona=gura', 'id=' + W, 'title=' + V['title'], 'size=' + xyz(V['frame_size']), 'parent_work=gura-tridente-01m', 'tags=sub')
    cli('op=work', 'sub=update', 'persona=gura', 'work=' + W, 'meters_per_voxel=0.1')
have = int(re.search(r'🔢 total_voxels = (\d+)', cli('op=stats', 'work=' + W)).group(1))
if have == 0:
    out = cli('op=stampvox', 'persona=gura', 'work=' + W, 'voxels=' + os.path.join(D, V['file']).replace(os.sep, '/'), 'at=0,0,0', 'expect_pixels=%d' % V['voxels'], 'share=0')
    n = int(re.search(r'🔢 placed = (\d+)', out).group(1))
    if n != V['voxels']:
        raise SystemExit('✗ placed %d ≠ %d' % (n, V['voxels']))
elif have != V['voxels']:
    raise SystemExit('✗ 已有 %d 格 ≠ %d' % (have, V['voxels']))
print('✓', W, V['voxels'])
for a in V['anchors']:
    cli('op=work', 'sub=anchor', 'persona=gura', 'work=' + W, 'name=' + a['name'], 'at=' + xyz(a['at']), 'overwrite=1', 'note=空艙房（造船規格 §9.2；draft_rooms.py）')
print('✓ 固定點', len(V['anchors']))
meta = json.dumps({'kind': 'rooms'})
cli('op=work', 'sub=link', 'persona=gura', 'work=' + V['host_work'], 'name=' + V['link'], 'source_work=' + W, 'at=' + xyz(V['frame_at']), 'overwrite=1',
    'note=orlop 艙房 S 舷（TASK-0581）', 'meta=' + meta)
cli('op=work', 'sub=link', 'persona=gura', 'work=' + V['host_work'], 'name=' + V['link_mirror'], 'source_work=' + W, 'at=' + xyz(V['at_mirror']), 'mirror=y',
    'overwrite=1', 'note=orlop 艙房 P 舷（鏡像；TASK-0581）', 'meta=' + meta)
print('✓ 關聯', V['link'], V['frame_at'], V['link_mirror'], V['at_mirror'], 'IOException 重試', retried)
