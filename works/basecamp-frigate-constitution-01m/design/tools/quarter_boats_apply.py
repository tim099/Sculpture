# 憲法號 階段三十六 quarter davits 與 whaleboat：照 verify_quarter_boats.json 下 CLI
#   -whaleboat 子作品（0.05 m、parent 船殼、tags sub）＋固定點 ring-aft／ring-fwd；-davits-side 子作品（一舷、0.1 m）＋固定點 davit-*.head
#   → 組裝件：關聯 davits／davits-鏡像、模型 小艇-S／小艇-P（scale 0.5 明寫、meta kind=boat）、吊索 4 條（組 boats/falls）
#   已在的子作品不重建不重落；關聯、繩已在就跳過；模型 overwrite=1。
# 用法：python -I quarter_boats_apply.py <design 資料夾>
# ⚠ 寫入偶爾 IOException（TASK-0534）⇒ 只對那一句重試，最多 3 次；中文／英文系統訊息都要認
import sys, os, json, subprocess, time
sys.stdout.reconfigure(encoding='utf-8')
D = os.path.abspath(sys.argv[1])
V = json.load(open(os.path.join(D, 'verify_quarter_boats.json'), encoding='utf-8'))
HULL = 'basecamp-frigate-constitution-01m'
ASM = HULL + '-assembly'
WB = HULL + '-whaleboat'
WD = HULL + '-davits-side'
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
    return ','.join(num(float(c)) if isinstance(c, float) else '%d' % c for c in v)


def path(rel):
    return os.path.join(D, rel).replace('\\', '/')


def subwork(W, title, size, mpv, vox, cells, anchors, note):
    if run(['op=work', 'sub=show', 'work=' + W]).returncode == 0:
        print('· %s 已在 ⇒ 不重建' % W)
    else:
        cli(['op=work', 'sub=create', 'persona=basecamp', 'id=' + W, 'title=' + title, 'size=' + xyz(size), 'parent_work=' + HULL, 'tags=sub'])
        cli(['op=work', 'sub=update', 'persona=basecamp', 'work=' + W, 'meters_per_voxel=' + num(mpv)])
        cli(['op=stampvox', 'persona=basecamp', 'work=' + W, 'voxels=' + path(vox), 'at=0,0,0', 'expect_pixels=%d' % cells])
    have = run(['op=work', 'sub=anchors', 'work=' + W]).stdout
    for name, p in anchors.items():
        if '`%s`' % name in have:
            print('· 固定點 %s 已在' % name)
            continue
        cli(['op=work', 'sub=anchor', 'persona=basecamp', 'work=' + W, 'name=' + name, 'at=' + xyz(p), 'note=' + note])


B = V['boat']
DV = V['davits']
subwork(WB, '憲法號 28 ft whaleboat（0.05 m／格；1931 plan 24474）', B['size'], 0.05, 'masks/quarter_boats/whaleboat.vox.txt', B['cells'], B['anchors'], '吊索的環（艏／艉）')
subwork(WD, '憲法號 quarter davits（一舷；1931 plan 24474）', DV['frame_size'], 0.1, 'masks/quarter_boats/davits_side.vox.txt', DV['cells'], DV['anchors'], 'davit 頭的滑車（吊索上端）')

links = run(['op=work', 'sub=links', 'work=' + ASM]).stdout
for name, at, mirror in (('davits', DV['frame_at'], ''), ('davits-鏡像', DV['mirror_at'], 'y')):
    if '`%s`' % name in links:
        print('· 關聯 %s 已在' % name)
        continue
    args = ['op=work', 'sub=link', 'persona=basecamp', 'work=' + ASM, 'name=' + name, 'source_work=' + WD, 'at=' + xyz(at),
            'note=quarter davits（階段三十六）']
    if mirror:
        args.append('mirror=' + mirror)
    cli(args)

s = B['scale']
meta = json.dumps({'kind': 'boat', 'boat': 'whaleboat', 'length_m': 8.53})
for side, at in (('S', B['at_s']), ('P', B['at_p'])):
    args = ['op=work', 'sub=model', 'persona=basecamp', 'work=' + ASM, 'name=小艇-' + side, 'source_work=' + WB, 'at=' + xyz(at),
            'pivot=' + xyz(B['pivot']), 'rotate=0,0,0', 'scale=' + xyz([s, s, s]), 'overwrite=1', 'meta=' + meta,
            'note=28 ft whaleboat（階段三十六；%s 舷，吊在 quarter davits）' % side]
    if side == 'P':
        args.append('mirror=y')
    cli(args)

ropes = run(['op=work', 'sub=ropes', 'work=' + ASM]).stdout
for side, link in (('S', 'davits'), ('P', 'davits-鏡像')):
    for end in ('aft', 'fwd'):
        name = 'boat-fall-%s-%s' % (side, end)
        if '`%s`' % name in ropes:
            print('· 繩 %s 已在' % name)
            continue
        cli(['op=work', 'sub=rope', 'persona=basecamp', 'work=' + ASM, 'name=' + name, 'from=%s/davit-%s.head' % (link, end),
             'to=model:小艇-%s/ring-%s' % (side, end), 'slack=1', 'color=#a08458', 'thickness=0.35', 'group=boats/falls',
             'note=quarter boat 吊索（階段三十六）'])
print('ok %d / bad %d / 重試 %d' % (ok, bad, retried))
