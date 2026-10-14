# 階段八（風暴角號；從夜隼號 apply_rigging.py 改）：照 verify_rigging.json 下 CLI —— channels v2（刻／貼）、固定點、繩
# 用法：python -I -X utf8 -B apply_rigging.py <design 資料夾> <步驟> [名字 regex]
#   步驟：channels（標記 stage8 begin → carvevox（帶原色守門）→ stampvox → 標記 stage8 end；每刀印 placed）｜anchors｜ropes
#   · anchors／ropes 用 overwrite=1 ⇒ 重跑一樣；繩照清單順序下（ratlines 是子繩，掛在 shrouds 上 ⇒ shrouds 在前）
#   · ⛔ 失敗那一行整段印出來（不要在呼叫端再 grep 掉）
import sys, os, json, re, subprocess

sys.stdout.reconfigure(encoding='utf-8')
D, step = os.path.abspath(sys.argv[1]), sys.argv[2]
flt = re.compile(sys.argv[3] if len(sys.argv) > 3 else '.')
V = json.load(open(os.path.join(D, 'verify_rigging.json'), encoding='utf-8'))
PRE = 'summit-stormkaap-01m'
WORK = {'mast_mizzen': PRE + '-mast-mizzen', 'mast_fore': PRE + '-mast-fore', 'mast_main': PRE + '-mast-main', 'bowsprit': PRE + '-bowsprit', 'head': PRE + '-head', 'channels': PRE + '-channels'}
ASM = PRE + '-assembly'
ok = bad = 0


def cli(args):
    global ok, bad
    r = subprocess.run(['senate', 'cmd', 'sculpture'] + sum([['--arg', a] for a in args], []), capture_output=True, text=True, encoding='utf-8', errors='replace')
    if r.returncode:
        bad += 1
        print('✗ rc=%d' % r.returncode, ' '.join(args[:5]))
        print((r.stdout + r.stderr)[-900:])
    else:
        ok += 1
    return r.returncode, r.stdout


def xyz(v):
    return ','.join('%d' % c for c in v)


if step == 'channels':
    W = WORK['channels']
    cli(['op=work', 'sub=mark', 'persona=summit', 'work=' + W, 'name=stage8', 'phase=begin', 'overwrite=1', 'note=階段八 channels v2（照 deadeye 重排、避開砲門、加 deadeye 與 chain plates）之前'])
    for o in V['stamp_order']['channels']:
        path = os.path.join(D, o['file']).replace('\\', '/')
        rc, out = cli(['op=' + o['op'], 'persona=summit', 'work=' + W, 'voxels=' + path, 'at=0,0,0', 'expect_pixels=%d' % o['voxels'], 'draft=0'])
        m = re.search(r'(placed|carved|removed)[^0-9]{0,8}([0-9,]+)', out)
        print(o['op'], o['name'], 'voxels', o['voxels'], m.group(0) if m else '（回傳沒有 placed／carved 字樣 —— 看下面那幾行）')
        if not m:
            print('\n'.join(l for l in out.splitlines() if l.startswith('🔢') or l.startswith('✓'))[-800:])
    cli(['op=work', 'sub=mark', 'persona=summit', 'work=' + W, 'name=stage8', 'phase=end', 'overwrite=1', 'note=階段八 channels v2 之後'])

elif step == 'anchors':
    for key, L in V['anchors'].items():
        n = 0
        for a in L:
            if not flt.search(a['name']): continue
            cli(['op=work', 'sub=anchor', 'persona=summit', 'work=' + WORK[key], 'name=' + a['name'], 'at=' + xyz(a['at']), 'overwrite=1',
                 'note=%s（verify_rigging.json；世界座標 %s）' % (a['kind'], xyz(a['world']))])
            n += 1
        print('anchors', WORK[key], n)

elif step == 'ropes':
    n = 0
    for r in V['ropes']:
        if not flt.search(r['name']): continue
        cli(['op=work', 'sub=rope', 'persona=summit', 'work=' + ASM, 'name=' + r['name'], 'from=' + r['from'], 'to=' + r['to'], 'overwrite=1',
             'slack=%g' % r['slack'], 'color=' + r['color'], 'thickness=%g' % r['thickness'], 'group=' + r['group'], 'note=' + r['kind'] + '（階段八）'])
        n += 1
    print('ropes', n)
else:
    raise SystemExit('步驟？ channels|anchors|ropes')
print(step, 'ok', ok, 'bad', bad)
