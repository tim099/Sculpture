# 憲法號 階段三十七 船尾 davits 與 whale gig：照 verify_stern_gig.json 下 CLI
#   -gig-davit-side 子作品（一舷、0.1 m）＋固定點 gig-davit.head → 組裝件關聯 gig-davits／gig-davits-鏡像
#   → 模型 小艇-gig（沿用 -whaleboat、rotate 0,0,90、scale 0.5 明寫、meta kind=boat）→ 吊索 2 條（組 boats/falls）
# 用法：python -I stern_gig_apply.py <design 資料夾>
# ⚠ 寫入偶爾 IOException（TASK-0534）⇒ 只對那一句重試，最多 3 次；中文／英文系統訊息都要認
import sys, os, json, subprocess, time
sys.stdout.reconfigure(encoding='utf-8')
D = os.path.abspath(sys.argv[1])
V = json.load(open(os.path.join(D, 'verify_stern_gig.json'), encoding='utf-8'))
HULL = 'basecamp-frigate-constitution-01m'
ASM = HULL + '-assembly'
WD = HULL + '-gig-davit-side'
IOE = ('無法移除要被取代的檔案', 'Unable to remove the file to be replaced')
ok = bad = retried = 0


def run(args):
    return subprocess.run(['senate', 'cmd', 'sculpture'] + sum([['--arg', a] for a in args], []), capture_output=True, text=True, encoding='utf-8', errors='replace')


def cli(args):
    global ok, bad, retried
    for k in range(4):
        r = run(args)
        if r.returncode and any(t in (r.stdout + r.stderr) for t in IOE) and k < 3:
            retried += 1
            time.sleep(0.5)
            continue
        break
    if r.returncode:
        bad += 1
        print('✗', ' '.join(args[:5]), (r.stdout + r.stderr)[-500:])
        raise SystemExit(1)
    ok += 1
    print('\n'.join(l for l in r.stdout.splitlines() if l.startswith('✓') or 'placed =' in l))


def num(v):
    return ('%.3f' % v).rstrip('0').rstrip('.') if isinstance(v, float) else '%d' % v


def xyz(v):
    return ','.join(num(c) for c in v)


DV = V['davit']
B = V['boat']
if run(['op=work', 'sub=show', 'work=' + WD]).returncode == 0:
    print('· %s 已在 ⇒ 不重建' % WD)
else:
    cli(['op=work', 'sub=create', 'persona=basecamp', 'id=' + WD, 'title=憲法號 船尾 davit（一舷；1931 plan 24474）', 'size=' + xyz(DV['frame_size']),
         'parent_work=' + HULL, 'tags=sub'])
    cli(['op=work', 'sub=update', 'persona=basecamp', 'work=' + WD, 'meters_per_voxel=0.1'])
    cli(['op=stampvox', 'persona=basecamp', 'work=' + WD, 'voxels=' + os.path.join(D, 'masks', 'stern_gig', 'gig_davit_side.vox.txt').replace('\\', '/'),
         'at=0,0,0', 'expect_pixels=%d' % DV['cells']])
have = run(['op=work', 'sub=anchors', 'work=' + WD]).stdout
for name, p in DV['anchors'].items():
    if '`%s`' % name not in have:
        cli(['op=work', 'sub=anchor', 'persona=basecamp', 'work=' + WD, 'name=' + name, 'at=' + xyz(p), 'note=davit 尖的滑車（吊索上端）'])
links = run(['op=work', 'sub=links', 'work=' + ASM]).stdout
for name, at, mirror in (('gig-davits', DV['frame_at'], ''), ('gig-davits-鏡像', DV['mirror_at'], 'y')):
    if '`%s`' % name in links:
        print('· 關聯 %s 已在' % name)
        continue
    args = ['op=work', 'sub=link', 'persona=basecamp', 'work=' + ASM, 'name=' + name, 'source_work=' + WD, 'at=' + xyz(at), 'note=船尾 davits（階段三十七）']
    if mirror:
        args.append('mirror=' + mirror)
    cli(args)
s = B['scale']
cli(['op=work', 'sub=model', 'persona=basecamp', 'work=' + ASM, 'name=小艇-gig', 'source_work=' + B['work'], 'at=' + xyz(B['at']),
     'pivot=' + xyz(B['pivot']), 'rotate=' + xyz(B['rotate']), 'scale=' + xyz([s, s, s]), 'overwrite=1',
     'meta=' + json.dumps({'kind': 'boat', 'boat': 'whale gig', 'length_m': 8.53}), 'note=28 ft whale gig（階段三十七；橫吊在船尾 davits）'])
other = 'ring-aft' if B['s_ring'] == 'ring-fwd' else 'ring-fwd'
ropes = run(['op=work', 'sub=ropes', 'work=' + ASM]).stdout
for name, link, ring in (('gig-fall-S', 'gig-davits', B['s_ring']), ('gig-fall-P', 'gig-davits-鏡像', other)):
    if '`%s`' % name in ropes:
        print('· 繩 %s 已在' % name)
        continue
    cli(['op=work', 'sub=rope', 'persona=basecamp', 'work=' + ASM, 'name=' + name, 'from=%s/gig-davit.head' % link, 'to=model:小艇-gig/' + ring,
         'slack=1', 'color=#a08458', 'thickness=0.35', 'group=boats/falls', 'note=船尾 gig 吊索（階段三十七）'])
print('ok %d / bad %d / 重試 %d' % (ok, bad, retried))
