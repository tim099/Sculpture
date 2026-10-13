# 憲法號 階段三十五 chesstrees：照 verify_chesstrees.json 下 CLI
#   -chesstrees-side 子作品（一舷 S、0.1 m、parent 船殼、tags sub、固定框 370×40×24；已在 ⇒ 不重建不重落）
#   → 組裝件關聯 chesstrees（at ＝ 固定框）、chesstrees-鏡像（mirror=y、at.y ＝ 321 − at.y − 40）
# 用法：python -I chesstrees_apply.py <design 資料夾>
# ⚠ 寫入偶爾 IOException（TASK-0534）⇒ 只對那一句重試，最多 3 次；中文／英文系統訊息都要認
import sys, os, json, subprocess, time
sys.stdout.reconfigure(encoding='utf-8')
D = os.path.abspath(sys.argv[1])
V = json.load(open(os.path.join(D, 'verify_chesstrees.json'), encoding='utf-8'))
HULL = 'basecamp-frigate-constitution-01m'
ASM = HULL + '-assembly'
W = HULL + '-chesstrees-side'
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


def xyz(v):
    return ','.join('%d' % c for c in v)


vox = os.path.join(D, 'masks', 'chesstrees', 'chesstrees_side.vox.txt').replace('\\', '/')
if run(['op=work', 'sub=show', 'work=' + W]).returncode == 0:
    print('· %s 已在 ⇒ 不重建' % W)
else:
    cli(['op=work', 'sub=create', 'persona=basecamp', 'id=' + W, 'title=憲法號 chesstrees（一舷；1931 plan 24474）', 'size=' + xyz(V['frame_size']),
         'parent_work=' + HULL, 'tags=sub'])
    cli(['op=work', 'sub=update', 'persona=basecamp', 'work=' + W, 'meters_per_voxel=0.1'])
    cli(['op=stampvox', 'persona=basecamp', 'work=' + W, 'voxels=' + vox, 'at=0,0,0', 'expect_pixels=%d' % V['cells']])
links = run(['op=work', 'sub=links', 'work=' + ASM]).stdout
for name, at, mirror in (('chesstrees', V['frame_at'], ''), ('chesstrees-鏡像', V['mirror_at'], 'y')):
    if '`%s`' % name in links:
        print('· 關聯 %s 已在' % name)
        continue
    args = ['op=work', 'sub=link', 'persona=basecamp', 'work=' + ASM, 'name=' + name, 'source_work=' + W, 'at=' + xyz(at),
            'note=chesstrees：fore sheet、lower studdingsail boom、main brace（階段三十五；1931 plan 24474）']
    if mirror:
        args.append('mirror=' + mirror)
    cli(args)
print('ok %d / bad %d / 重試 %d' % (ok, bad, retried))
