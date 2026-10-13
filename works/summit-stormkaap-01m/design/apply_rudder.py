# 階段六 a：舵 —— 建子作品、貼格（走 apply_stamps.py --key rudder／hull）、固定點 stock-top、組裝件的外部模型（kind=rudder）。
# 用法：python -I -X utf8 -B apply_rudder.py <design 資料夾> <步驟>
#   步驟：create（parent＝船殼、tags sub、0.1 m）｜anchors（overwrite=1）｜model（overwrite=1；照 verify_rudder.json 的 model）
import sys, os, json, subprocess

sys.stdout.reconfigure(encoding='utf-8')
D, step = os.path.abspath(sys.argv[1]), sys.argv[2]
plan = json.load(open(os.path.join(D, 'plan.json'), encoding='utf-8'))
V = json.load(open(os.path.join(D, 'verify_rudder.json'), encoding='utf-8'))
PRE = plan['work']; ASM = PRE + '-assembly'; RW = PRE + '-rudder'
F = plan['frame']; SIZE = '%d,%d,%d' % (F['NX'], F['NY'], F['NZ_work'])
ok = bad = 0
xyz = lambda v: ','.join('%g' % c for c in v)


def cli(args, quiet_fail=False):
    global ok, bad
    r = subprocess.run(['senate', 'cmd', 'sculpture'] + sum([['--arg', a] for a in args], []), capture_output=True, text=True, encoding='utf-8', errors='replace')
    if r.returncode:
        if not quiet_fail:
            bad += 1; print('✗ rc=%d' % r.returncode, ' '.join(args[:5])); print((r.stdout + r.stderr)[-900:])
    else:
        ok += 1
    return r.returncode, r.stdout


if step == 'create':
    rc, _ = cli(['op=work', 'sub=show', 'work=' + RW], quiet_fail=True)
    if rc == 0: print('已有', RW)
    else: cli(['op=work', 'sub=create', 'persona=summit', 'id=' + RW, 'title=風暴角號｜舵（外部模型的來源）', 'size=' + SIZE, 'parent_work=' + PRE, 'tags=sub']); print('建立', RW)
    cli(['op=work', 'sub=update', 'persona=summit', 'work=' + RW, 'meters_per_voxel=0.1'])
elif step == 'anchors':
    for name, at in V['anchors'].items():
        cli(['op=work', 'sub=anchor', 'persona=summit', 'work=' + RW, 'name=' + name, 'at=' + xyz(at), 'overwrite=1',
             'note=舵柱頂（遊戲 10_ship.js：舵的「腳」從這一點找旁邊最近的船尾格）'])
elif step == 'model':
    m = V['model']
    cli(['op=work', 'sub=model', 'persona=summit', 'work=' + ASM, 'name=' + m['name'], 'source_work=' + RW, 'at=' + xyz(m['at']),
         'pivot=' + xyz(m['pivot']), 'rotate=0,0,0', 'scale=%g' % m['scale'], 'overwrite=1', 'meta=' + json.dumps(m['meta'], ensure_ascii=False, sort_keys=True),
         'note=舵（階段六：外部模型；轉軸 ＝ 艉柱後緣那條線，見 meta hinge_*／axis_*）'])
else:
    raise SystemExit('步驟？ create|anchors|model')
print(step, 'ok', ok, 'bad', bad)
