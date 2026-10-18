# 光榮號 機艙落格：照 engine_placement.json —— 每件一個子作品（0.1 m、parent 船殼、tags sub；已在且格數對 ⇒ 不重落）→ stampvox（讀回 placed）
#   → 固定點 → 組裝件關聯（at ＝ 外框最小角、meta）；曲柄 ⇒ 組裝件外部模型（at ＝ pivot ＝ 轉軸格心、scale 1、meta kind=gear spin=rpm）
#   抄自拿破崙號 kotoko-napoleon-01m/design/tools/apply_engine.py（kotoko）；光榮號改：persona、四件（加曲柄模型）、鍋爐一組。
#   用法：python -I -X utf8 tools/apply_engine.py <design>
import json, os, re, subprocess, sys, time

sys.stdout.reconfigure(encoding='utf-8')
D = os.path.abspath(sys.argv[1])
HULL, ASM = 'kaguya-gloire-01m', 'kaguya-gloire-01m-assembly'
PL = json.load(open(os.path.join(D, 'engine_placement.json'), encoding='utf-8'))
ok = retried = 0


def run(args):
    return subprocess.run(['senate', 'cmd', 'sculpture'] + sum([['--arg', a] for a in args], []), capture_output=True, text=True, encoding='utf-8', errors='replace')


def cli(args):
    global ok, retried
    for k in range(5):
        r = run(args)
        out = r.stdout + r.stderr
        if r.returncode and any(t in out for t in ('IOException', '無法移除要被取代的檔案', 'Unable to remove the file to be replaced')) and k < 4:
            retried += 1
            time.sleep(0.5)
            continue
        break
    if r.returncode:
        print('✗ rc=%d' % r.returncode, ' '.join(args[:6]))
        print(out[-1200:])
        raise SystemExit(1)
    ok += 1
    return r.stdout


xyz = lambda v: ','.join('%g' % c for c in v)
for k in ('shaft', 'engine', 'crank', 'boilers'):
    P = PL[k]
    W = P['work']
    vox = os.path.join(D, 'masks', 'engine', k + '.vox.txt').replace(os.sep, '/')
    if run(['op=work', 'sub=show', 'work=' + W]).returncode != 0:
        cli(['op=work', 'sub=create', 'persona=kaguya', 'id=' + W, 'title=' + P['title'], 'size=' + xyz(P['size']), 'parent_work=' + HULL, 'tags=sub'])
        cli(['op=work', 'sub=update', 'persona=kaguya', 'work=' + W, 'meters_per_voxel=0.1'])
    have = int(re.search(r'🔢 total_voxels = (\d+)', cli(['op=stats', 'work=' + W])).group(1))
    if have == 0:
        out = cli(['op=stampvox', 'persona=kaguya', 'work=' + W, 'voxels=' + vox, 'at=0,0,0', 'expect_pixels=%d' % P['cells'], 'share=0'])
        n = int(re.search(r'🔢 placed = (\d+)', out).group(1))
        if n != P['cells']:
            raise SystemExit('✗ %s placed %d ≠ %d' % (W, n, P['cells']))
    elif have != P['cells']:
        raise SystemExit('✗ %s 已有 %d 格 ≠ %d' % (W, have, P['cells']))
    for name, v in sorted(P['anchors'].items()):
        cli(['op=work', 'sub=anchor', 'persona=kaguya', 'work=' + W, 'name=' + name, 'at=' + xyz(v), 'overwrite=1',
             'note=機艙（draft_engine.py）'])
    if P.get('model'):
        cli(['op=work', 'sub=model', 'persona=kaguya', 'work=' + ASM, 'name=' + P['link'], 'source_work=' + W, 'at=' + xyz(P['model_at']), 'pivot=' + xyz(P['pivot']),
             'rotate=0,0,0', 'scale=1', 'overwrite=1', 'meta=' + json.dumps(P['meta'], ensure_ascii=False, sort_keys=True),
             'note=機艙：曲柄（會轉的外部模型：遊戲照螺旋槳轉速繞 spin-a → spin-b 轉）'])
        print('✓', k, W, P['cells'], '格', '模型', P['link'], P['model_at'], P['meta'])
        continue
    cli(['op=work', 'sub=link', 'persona=kaguya', 'work=' + ASM, 'name=' + P['link'], 'source_work=' + W, 'at=' + xyz(P['at']), 'overwrite=1',
         'note=機艙：%s' % P['title'], 'meta=' + json.dumps(P['meta'], ensure_ascii=False, sort_keys=True)])
    print('✓', k, W, P['cells'], '格', '關聯', P['link'], P['at'], P['meta'])
print('ok', ok, 'IOException 重試', retried)
