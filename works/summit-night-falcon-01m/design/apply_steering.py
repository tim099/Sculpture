# 階段十六：照 verify_steering.json 下 CLI —— 舵柄（舵子作品）、舵柄口（船殼、船尾裝飾）、導索塊與繩孔（後甲板）、舵輪座底板繩孔、固定點、舵索 6 段
# 用法：python -I -X utf8 -B apply_steering.py <design 資料夾> <步驟>
#   步驟：voxels（每件作品 mark stage16 begin → 照 stamp_order 落／刻 → end；舵輪座底板刻孔）｜anchors｜ropes
#   · voxels 只跑一次（carvevox 帶原色守門，重跑會被擋）；anchors／ropes 用 overwrite=1；⛔ 失敗整段印出來
import sys, os, json, re, subprocess

sys.stdout.reconfigure(encoding='utf-8')
D, step = os.path.abspath(sys.argv[1]), sys.argv[2]
V = json.load(open(os.path.join(D, 'verify_steering.json'), encoding='utf-8'))
PRE = 'summit-night-falcon-01m'
ASM = PRE + '-assembly'
WORK = {'rudder': PRE + '-rudder', 'quarter': PRE + '-deck-quarter', 'hull': PRE, 'stern_deco': PRE + '-stern-deco', 'wheel': PRE + '-wheel'}
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
if step == 'voxels':
    jobs = list(V['stamp_order'].items()) + [('stand', [{'name': 'rope_holes', 'op': 'carvevox', 'file': V['stand_holes']['file'], 'voxels': V['stand_holes']['voxels']}])]
    for key, L in jobs:
        w = V['stand_holes']['work'] if key == 'stand' else WORK[key]
        cli(['op=work', 'sub=mark', 'persona=summit', 'work=' + w, 'name=stage16', 'phase=begin', 'note=階段十六：舵柄與舵索'])
        for o in L:
            rc, out = cli(['op=' + o['op'], 'persona=summit', 'work=' + w, 'voxels=' + os.path.join(D, o['file']).replace('\\', '/'), 'at=0,0,0',
                           'expect_pixels=%d' % o['voxels'], 'draft=0'])
            m = re.search(r'🔢 placed = (\d+)', out)
            print(key, o['name'], o['op'], o['voxels'], 'placed', m.group(1) if m else '?')
        cli(['op=work', 'sub=mark', 'persona=summit', 'work=' + w, 'name=stage16', 'phase=end', 'note=階段十六'])
elif step == 'anchors':
    for key, L in V['anchors'].items():
        for a in L:
            cli(['op=work', 'sub=anchor', 'persona=summit', 'work=' + WORK[key], 'name=' + a['name'], 'at=' + xyz(a['at']), 'overwrite=1', 'note=階段十六 舵索'])
    print('anchors', sum(len(L) for L in V['anchors'].values()))
elif step == 'ropes':
    for r in V['ropes']:
        cli(['op=work', 'sub=rope', 'persona=summit', 'work=' + ASM, 'name=' + r['name'], 'from=' + r['from'], 'to=' + r['to'], 'overwrite=1',
             'slack=%g' % r['slack'], 'color=' + r['color'], 'thickness=%g' % r['thickness'], 'group=' + r['group'], 'note=舵索（階段十六）'])
    print('ropes', len(V['ropes']))
else:
    raise SystemExit('步驟？ voxels|anchors|ropes')
print(step, 'ok', ok, 'bad', bad)
