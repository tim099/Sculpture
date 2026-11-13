# 彈藥庫門對齊貨艙梯 下 CLI（2026-11-13；讀 verify_mag_door.json，draft_mag_door.py 產的）
#   步驟：cells（刻新門洞、補舊門洞、梯頂補一階；每刀讀回 carved／placed）｜anchors（彈藥庫 door、梯子 hold-mag.head；overwrite=1）
#   ⛔ cells 只跑一次；失敗那一行整段印出來
# 用法：python -I -X utf8 -B apply_mag_door.py <design> <步驟>
import sys, os, json, re, subprocess

sys.stdout.reconfigure(encoding='utf-8')
D, step = os.path.abspath(sys.argv[1]), sys.argv[2]
V = json.load(open(os.path.join(D, 'verify_mag_door.json'), encoding='utf-8'))
ok = bad = 0


def cli(args):
    global ok, bad
    r = subprocess.run(['senate', 'cmd', 'sculpture'] + sum([['--arg', a] for a in args], []), capture_output=True, text=True, encoding='utf-8', errors='replace')
    if r.returncode:
        bad += 1; print('✗ rc=%d' % r.returncode, ' '.join(args[:5])); print((r.stdout + r.stderr)[-900:])
    else:
        ok += 1
    return r.returncode, r.stdout


if step == 'cells':
    for name in ('magazine.carve.vox.txt', 'magazine.add.vox.txt', 'ladders-hold.add.vox.txt'):    # 先刻再補（同一件子作品：刻掉新門洞、補回舊門洞）
        f = V['files'][name]
        rc, out = cli(['op=' + f['op'], 'persona=summit', 'work=' + f['work'], 'voxels=' + os.path.join(D, f['path']).replace('\\', '/'), 'at=0,0,0', 'expect_pixels=%d' % f['cells'], 'draft=0'])
        m = re.search(r'🔢 (placed|carved) = (\d+)', out)
        print(f['op'], f['work'], name, '格', f['cells'], '讀回', m.group(0) if m else '?')
elif step == 'anchors':
    for a in V['anchors']:
        cli(['op=work', 'sub=anchor', 'persona=summit', 'work=' + a['work'], 'name=' + a['name'], 'at=' + ','.join(str(v) for v in a['at']), 'overwrite=1',
             'note=彈藥庫門對齊貨艙梯（draft_mag_door.py，2026-11-13）'])
        print('anchor', a['work'], a['name'], a['at'])
else:
    raise SystemExit('步驟？')
print(step, 'ok', ok, 'bad', bad)
