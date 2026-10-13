# 階段二十：照 verify_binnacle.json 下 CLI —— 羅經櫃子作品（parent 甲板-後、0.02 m）、一刀落格、掛成甲板-後的外部模型（meta kind=binnacle）
# 用法：python -I -X utf8 -B apply_binnacle.py <design 資料夾> <步驟>
#   步驟：create｜stamp（只跑一次）｜model（overwrite=1）；⛔ 失敗整段印出來
import sys, os, json, re, subprocess

sys.stdout.reconfigure(encoding='utf-8')
D, step = os.path.abspath(sys.argv[1]), sys.argv[2]
V = json.load(open(os.path.join(D, 'verify_binnacle.json'), encoding='utf-8'))
PRE = 'summit-night-falcon-01m'
ok = bad = 0


def cli(args):
    global ok, bad
    r = subprocess.run(['senate', 'cmd', 'sculpture'] + sum([['--arg', a] for a in args], []), capture_output=True, text=True, encoding='utf-8', errors='replace')
    if r.returncode:
        bad += 1
        print('✗ rc=%d' % r.returncode, ' '.join(args[:5])); print((r.stdout + r.stderr)[-900:])
    else:
        ok += 1
    return r.returncode, r.stdout


xyz = lambda v: ','.join('%g' % c for c in v)
if step == 'create':
    rc, _ = cli(['op=work', 'sub=show', 'work=' + V['work']])
    if rc == 0:
        print('已有', V['work'])
    else:
        bad -= 1
        cli(['op=work', 'sub=create', 'persona=summit', 'id=' + V['work'], 'title=' + V['title'], 'size=' + xyz(V['size']), 'parent_work=' + PRE + '-deck-quarter', 'tags=sub'])
    cli(['op=work', 'sub=update', 'persona=summit', 'work=' + V['work'], 'meters_per_voxel=%g' % V['mpv']])
elif step == 'stamp':
    rc, out = cli(['op=stampvox', 'persona=summit', 'work=' + V['work'], 'voxels=' + os.path.join(D, V['file']['path']).replace('\\', '/'), 'at=0,0,0',
                   'expect_pixels=%d' % V['file']['cells'], 'draft=0'])
    m = re.search(r'🔢 placed = (\d+)', out)
    print('binnacle', V['file']['cells'], 'placed', m.group(1) if m else '?')
elif step == 'model':
    M = V['model']
    cli(['op=work', 'sub=model', 'persona=summit', 'work=' + V['host'], 'name=' + M['name'], 'source_work=' + V['work'], 'at=' + xyz(V['at']),
         'pivot=' + xyz(V['pivot']), 'rotate=0,0,0', 'scale=%g' % V['scale'], 'overwrite=1', 'meta=' + json.dumps(M['meta'], ensure_ascii=False, sort_keys=True),
         'note=羅經櫃（階段二十：pivot ＝ 底面中心；舵輪正前方中線）'])
else:
    raise SystemExit('步驟？ create|stamp|model')
print(step, 'ok', ok, 'bad', bad)
