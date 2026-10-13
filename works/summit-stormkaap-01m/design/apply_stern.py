# 階段五：建船尾裝飾、側窗廊、船頭三件子作品，接進組裝件（落格走 apply_stamps.py --key）。
# 用法：python -I -X utf8 -B apply_stern.py <design 資料夾> <步驟>
#   步驟：create（parent＝船殼、tags sub、meters_per_voxel 0.1；已有的略過）｜link（船尾；overwrite=1；側窗廊左舷 ＝ 同一件 mirror=y、at 0,0,0 ⇒ y ↔ 260 − y）｜link_head（船頭）
import sys, os, json, subprocess

sys.stdout.reconfigure(encoding='utf-8')
D, step = os.path.abspath(sys.argv[1]), sys.argv[2]
plan = json.load(open(os.path.join(D, 'plan.json'), encoding='utf-8'))
PRE = plan['work']; ASM = PRE + '-assembly'
F = plan['frame']; SIZE = '%d,%d,%d' % (F['NX'], F['NY'], F['NZ_work'])
PARTS = [('stern-deco', '風暴角號｜船尾裝飾（艉板窗、陽台、拱頂、Adamastor、艉燈）'),
         ('quarter-gallery', '風暴角號｜側窗廊（右舷；左舷走鏡像關聯）'),
         ('head', '風暴角號｜船頭 galjoen（knee、格柵、上下顎、骷髏獅子、追擊砲門的大嘴）')]
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


if step == 'create':
    for suf, title in PARTS:
        wid = PRE + '-' + suf
        rc, _ = cli(['op=work', 'sub=show', 'work=' + wid], quiet_fail=True)
        if rc == 0: print('已有', wid)
        else: cli(['op=work', 'sub=create', 'persona=summit', 'id=' + wid, 'title=' + title, 'size=' + SIZE, 'parent_work=' + PRE, 'tags=sub']); print('建立', wid)
        cli(['op=work', 'sub=update', 'persona=summit', 'work=' + wid, 'meters_per_voxel=0.1'])
elif step == 'link':
    cli(['op=work', 'sub=link', 'persona=summit', 'work=' + ASM, 'name=船尾裝飾', 'source_work=' + PRE + '-stern-deco', 'at=0,0,0', 'overwrite=1',
         'note=艉板窗、陽台、拱頂、Adamastor、艉燈（階段五）'])
    cli(['op=work', 'sub=link', 'persona=summit', 'work=' + ASM, 'name=側窗廊', 'source_work=' + PRE + '-quarter-gallery', 'at=0,0,0', 'overwrite=1',
         'note=右舷側窗廊（階段五）'])
    cli(['op=work', 'sub=link', 'persona=summit', 'work=' + ASM, 'name=側窗廊-鏡像', 'source_work=' + PRE + '-quarter-gallery', 'at=0,0,0', 'mirror=y', 'overwrite=1',
         'note=左舷側窗廊 ＝ 右舷那份 mirror=y（框同船殼 ⇒ y ↔ 260 − y）'])
elif step == 'link_head':
    cli(['op=work', 'sub=link', 'persona=summit', 'work=' + ASM, 'name=船頭', 'source_work=' + PRE + '-head', 'at=0,0,0', 'overwrite=1',
         'note=galjoen：knee、格柵、上下顎、骷髏獅子、追擊砲門的大嘴（階段五 b）'])
else:
    raise SystemExit('步驟？ create|link|link_head')
print(step, 'ok', ok, 'bad', bad)
