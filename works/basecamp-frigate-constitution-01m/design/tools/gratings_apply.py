# 憲法號 階段四十 艙口格柵：照 verify_gratings.json 下 CLI
#   -grating-spar-main／-grating-gun-main 子作品（0.05 m、parent 船殼、tags sub）
#   → 外部模型 格柵-main 掛在該層甲板子作品（-deck-spar／-deck-gun；藏甲板一起藏）、scale 0.5 明寫、meta kind=grating
#   已在的子作品不重建不重落；模型 overwrite=1。
# 用法：python -I gratings_apply.py <design 資料夾>
# ⚠ 寫入偶爾 IOException（TASK-0534）⇒ 只對那一句重試，最多 3 次；中文／英文系統訊息都要認
import sys, os, json, subprocess, time
sys.stdout.reconfigure(encoding='utf-8')
D = os.path.abspath(sys.argv[1])
V = json.load(open(os.path.join(D, 'verify_gratings.json'), encoding='utf-8'))
HULL = 'basecamp-frigate-constitution-01m'
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


for key, deck, title, note in (
        ('spar_main', 'deck-spar', '憲法號 spar deck 船腰艙口格柵（0.05 m／格；1930 plan 19274）', 'spar deck 船腰艙口格柵（階段四十；船尾那段是梯口、不鋪）'),
        ('gun_main', 'deck-gun', '憲法號 gun deck main hatch 格柵（0.05 m／格；1930 plan 19274）', 'gun deck main hatch 格柵（階段四十）')):
    g = V[key]
    W = HULL + '-grating-' + key.replace('_', '-')
    if run(['op=work', 'sub=show', 'work=' + W]).returncode == 0:
        print('· %s 已在 ⇒ 不重建' % W)
    else:
        cli(['op=work', 'sub=create', 'persona=basecamp', 'id=' + W, 'title=' + title, 'size=' + xyz(g['size']), 'parent_work=' + HULL, 'tags=sub'])
        cli(['op=work', 'sub=update', 'persona=basecamp', 'work=' + W, 'meters_per_voxel=0.05'])
        cli(['op=stampvox', 'persona=basecamp', 'work=' + W, 'voxels=' + path('masks/gratings/%s.vox.txt' % key), 'at=0,0,0', 'expect_pixels=%d' % g['cells']])
    s = g['scale']
    cli(['op=work', 'sub=model', 'persona=basecamp', 'work=' + HULL + '-' + deck, 'name=格柵-main', 'source_work=' + W, 'at=' + xyz(g['at']),
         'pivot=' + xyz(g['pivot']), 'rotate=0,0,0', 'scale=' + xyz([s, s, s]), 'overwrite=1', 'meta=' + json.dumps({'kind': 'grating'}), 'note=' + note])
print('ok %d / bad %d / 重試 %d' % (ok, bad, retried))
