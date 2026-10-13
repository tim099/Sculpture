# 階段四：建五件甲板子作品＋組裝件、組裝件的關聯（落格走 apply_stamps.py --key）。
# 用法：python -I -X utf8 -B apply_decks.py <design 資料夾> <步驟>
#   步驟：create（甲板子作品 parent＝船殼、tags sub；組裝件 parent＝船殼、不帶 sub —— 它是整艘船，觀測頁要列）｜link
#   · create 已存在 ⇒ 略過；每件都補 meters_per_voxel 0.1（造船規格 §1：組裝件和每件子作品都要記）。
#   · link：overwrite=1；船殼關聯帶 meta kind=ship、waterline_z（遊戲 05_hull.js 讀）。
import sys, os, json, subprocess

sys.stdout.reconfigure(encoding='utf-8')
D, step = os.path.abspath(sys.argv[1]), sys.argv[2]
plan = json.load(open(os.path.join(D, 'plan.json'), encoding='utf-8'))
PRE = plan['work']
ASM = PRE + '-assembly'
F = plan['frame']
SIZE = '%d,%d,%d' % (F['NX'], F['NY'], F['NZ_work'])
DECKS = [('lower', 'deck-lower', '風暴角號｜下甲板（overloop）', '甲板-下'),
         ('upper', 'deck-upper', '風暴角號｜上甲板（bovenoverloop）', '甲板-上'),
         ('half', 'deck-half', '風暴角號｜後甲板（halfdek）', '甲板-後'),
         ('kamp', 'deck-kampanje', '風暴角號｜艉樓甲板（kampanje）', '甲板-艉樓'),
         ('bak', 'deck-bak', '風暴角號｜艏樓甲板（bak）', '甲板-艏樓')]
ok = bad = 0


def cli(args, quiet_fail=False):
    global ok, bad
    r = subprocess.run(['senate', 'cmd', 'sculpture'] + sum([['--arg', a] for a in args], []), capture_output=True, text=True, encoding='utf-8', errors='replace')
    if r.returncode:
        if not quiet_fail:
            bad += 1
            print('✗ rc=%d' % r.returncode, ' '.join(args[:5])); print((r.stdout + r.stderr)[-900:])
    else:
        ok += 1
    return r.returncode, r.stdout


def ensure(wid, title, tags):
    rc, _ = cli(['op=work', 'sub=show', 'work=' + wid], quiet_fail=True)
    if rc == 0:
        print('已有', wid)
    else:
        a = ['op=work', 'sub=create', 'persona=summit', 'id=' + wid, 'title=' + title, 'size=' + SIZE, 'parent_work=' + PRE]
        if tags: a.append('tags=' + tags)
        cli(a); print('建立', wid)
    cli(['op=work', 'sub=update', 'persona=summit', 'work=' + wid, 'meters_per_voxel=0.1'])


if step == 'create':
    for k, suf, title, _ in DECKS: ensure(PRE + '-' + suf, title, 'sub')
    ensure(ASM, '風暴角號（組裝）', '')
elif step == 'link':
    cli(['op=work', 'sub=link', 'persona=summit', 'work=' + ASM, 'name=船殼', 'source_work=' + PRE, 'at=0,0,0', 'overwrite=1',
         'meta=' + json.dumps({'kind': 'ship', 'waterline_z': plan['lines']['dwl']}), 'note=船殼（龍骨、肋骨、外板、wales、砲門、clamp）'])
    for k, suf, title, ln in DECKS:
        cli(['op=work', 'sub=link', 'persona=summit', 'work=' + ASM, 'name=' + ln, 'source_work=' + PRE + '-' + suf, 'at=0,0,0', 'overwrite=1',
             'note=' + title + '（階段四）'])
else:
    raise SystemExit('步驟？ create|link')
print(step, 'ok', ok, 'bad', bad)
