# 階段六 b：桅、船首斜桅、channels —— 建子作品、固定點、接進組裝件（落格走 apply_stamps.py --key）。
# 用法：python -I -X utf8 -B apply_masts.py <design 資料夾> <步驟>
#   步驟：create（parent＝船殼、tags sub、0.1 m；已有的略過）｜anchors（overwrite=1）｜link（overwrite=1；channels 左舷 ＝ 同一件 mirror=y、at 0,0,0）
import sys, os, json, subprocess

sys.stdout.reconfigure(encoding='utf-8')
D, step = os.path.abspath(sys.argv[1]), sys.argv[2]
plan = json.load(open(os.path.join(D, 'plan.json'), encoding='utf-8'))
V = json.load(open(os.path.join(D, 'verify_masts.json'), encoding='utf-8'))
PRE = plan['work']; ASM = PRE + '-assembly'
F = plan['frame']; SIZE = '%d,%d,%d' % (F['NX'], F['NY'], F['NZ_work'])
PARTS = [('mizzen', 'mast-mizzen', '風暴角號｜後桅（＋後上桅、平台）', '後桅'),
         ('main', 'mast-main', '風暴角號｜主桅（＋主上桅、主上上桅、平台）', '主桅'),
         ('fore', 'mast-fore', '風暴角號｜前桅（＋前上桅、前上上桅、平台）', '前桅'),
         ('bowsprit', 'bowsprit', '風暴角號｜船首斜桅（＋斜桅頂桅）', '船首斜桅'),
         ('channels', 'channels', '風暴角號｜channels（右舷；左舷走鏡像關聯）', 'channels')]
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
    for key, suf, title, _ in PARTS:
        wid = PRE + '-' + suf
        rc, _ = cli(['op=work', 'sub=show', 'work=' + wid], quiet_fail=True)
        if rc == 0: print('已有', wid)
        else: cli(['op=work', 'sub=create', 'persona=summit', 'id=' + wid, 'title=' + title, 'size=' + SIZE, 'parent_work=' + PRE, 'tags=sub']); print('建立', wid)
        cli(['op=work', 'sub=update', 'persona=summit', 'work=' + wid, 'meters_per_voxel=0.1'])
elif step == 'anchors':
    for key, suf, title, _ in PARTS:
        for name, at in V['anchors'].get(key, {}).items():
            cli(['op=work', 'sub=anchor', 'persona=summit', 'work=' + PRE + '-' + suf, 'name=' + name, 'at=' + xyz(at), 'overwrite=1', 'note=階段六（帆桁、繩之後用）'])
elif step == 'link':
    for key, suf, title, ln in PARTS:
        cli(['op=work', 'sub=link', 'persona=summit', 'work=' + ASM, 'name=' + ln, 'source_work=' + PRE + '-' + suf, 'at=0,0,0', 'overwrite=1', 'note=' + title + '（階段六）'])
    cli(['op=work', 'sub=link', 'persona=summit', 'work=' + ASM, 'name=channels-鏡像', 'source_work=' + PRE + '-channels', 'at=0,0,0', 'mirror=y', 'overwrite=1',
         'note=左舷 channels ＝ 右舷那份 mirror=y（框同船殼 ⇒ y ↔ 260 − y）'])
else:
    raise SystemExit('步驟？ create|anchors|link')
print(step, 'ok', ok, 'bad', bad)
