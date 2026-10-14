# 階段九 a：fife rails 子作品（框 ＝ 整艘船、parent ＝ 船殼、tags sub、0.1 m）—— 建、落格、pin 與 kevel 固定點、接進組裝件。
# 用法：python -I -X utf8 -B apply_belaying.py <design 資料夾> <步驟>
#   步驟：create（已有就略過）｜stamp（每刀讀回 placed）｜anchors（overwrite=1）｜link（overwrite=1）
#   · ⛔ 失敗那一行整段印出來（不要在呼叫端再 grep 掉）
import sys, os, json, re, subprocess

sys.stdout.reconfigure(encoding='utf-8')
D, step = os.path.abspath(sys.argv[1]), sys.argv[2]
plan = json.load(open(os.path.join(D, 'plan.json'), encoding='utf-8'))
V = json.load(open(os.path.join(D, 'verify_belaying.json'), encoding='utf-8'))
PRE = plan['work']; ASM = PRE + '-assembly'; FW = PRE + '-fiferails'
F = plan['frame']; SIZE = '%d,%d,%d' % (F['NX'], F['NY'], F['NZ_work'])
WORK = {'fife': FW, 'hull': PRE}
ok = bad = 0


def cli(args, quiet_fail=False):
    global ok, bad
    r = subprocess.run(['senate', 'cmd', 'sculpture'] + sum([['--arg', a] for a in args], []), capture_output=True, text=True, encoding='utf-8', errors='replace')
    if r.returncode:
        if not quiet_fail:
            bad += 1; print('✗ rc=%d' % r.returncode, ' '.join(args[:5])); print((r.stdout + r.stderr)[-900:])
    else:
        ok += 1
    return r.returncode, r.stdout


xyz = lambda v: ','.join('%d' % c for c in v)
if step == 'create':
    rc, _ = cli(['op=work', 'sub=show', 'work=' + FW], quiet_fail=True)
    if rc == 0: print('已有', FW)
    else: cli(['op=work', 'sub=create', 'persona=summit', 'id=' + FW, 'title=風暴角號｜三根桅腳的 fife rails（＋bitts、pins）', 'size=' + SIZE,
               'parent_work=' + PRE, 'tags=sub']); print('建立', FW)
    cli(['op=work', 'sub=update', 'persona=summit', 'work=' + FW, 'meters_per_voxel=0.1'])
elif step == 'stamp':
    for o in V['stamp_order']['fiferails']:
        path = os.path.join(D, o['file']).replace('\\', '/')
        rc, out = cli(['op=stampvox', 'persona=summit', 'work=' + FW, 'voxels=' + path, 'at=0,0,0', 'expect_pixels=%d' % o['voxels'], 'draft=0'])
        m = re.search(r'placed[^0-9]{0,8}([0-9,]+)', out)
        print('stamp', o['name'], 'voxels', o['voxels'], 'placed', m.group(1) if m else '?')
elif step == 'anchors':
    for key, L in V['anchors'].items():
        for a in L:
            cli(['op=work', 'sub=anchor', 'persona=summit', 'work=' + WORK[key], 'name=' + a['name'], 'at=' + xyz(a['at']), 'overwrite=1',
                 'note=%s（階段九 verify_belaying.json）' % a['kind']])
        print('anchors', WORK[key], len(L))
elif step == 'link':
    cli(['op=work', 'sub=link', 'persona=summit', 'work=' + ASM, 'name=fife-rails', 'source_work=' + FW, 'at=0,0,0', 'overwrite=1',
         'note=三根桅腳的 fife rails（階段九）'])
else:
    raise SystemExit('步驟？ create|stamp|anchors|link')
print(step, 'ok', ok, 'bad', bad)
