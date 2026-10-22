# TASK-0680：照 verify_organ_engine.json 下 CLI —— 子作品 -organ-engine（0.1 m、整船的框）＋組裝件關聯 `管風琴`（kind=engine）＋拿掉階段十八那台裝飾模型
# 用法：python -I -X utf8 -B apply_organ_engine.py <design 資料夾> <步驟>
#   步驟：create（已存在 ⇒ 略過）｜stamp（stampvox 整份清單，at 0,0,0）｜anchors（core、tend-1）｜model（組裝件外部模型 管風琴 at 0,0,0、meta；TASK-0793 前是 link）｜unmodel（甲板-後 的外部模型 管風琴）
import sys, os, json, subprocess

sys.stdout.reconfigure(encoding='utf-8')
D, step = os.path.abspath(sys.argv[1]), sys.argv[2]
V = json.load(open(os.path.join(D, 'verify_organ_engine.json'), encoding='utf-8'))
ASM, HALF = 'summit-stormkaap-01m-assembly', 'summit-stormkaap-01m-deck-half'
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


xyz = lambda v: ','.join('%g' % c for c in v)
if step == 'create':
    rc, _ = cli(['op=work', 'sub=show', 'work=' + V['work']], quiet_fail=True)
    if rc == 0:
        print('已有', V['work'])
    else:
        cli(['op=work', 'sub=create', 'persona=summit', 'id=' + V['work'], 'title=' + V['title'], 'size=736,261,576', 'parent_work=summit-stormkaap-01m', 'tags=sub'])
    cli(['op=work', 'sub=update', 'persona=summit', 'work=' + V['work'], 'meters_per_voxel=0.1'])
elif step == 'stamp':
    p = os.path.join(D, V['file']).replace('\\', '/')
    rc, out = cli(['op=stampvox', 'persona=summit', 'work=' + V['work'], 'voxels=' + p, 'at=0,0,0', 'expect_pixels=%d' % V['cells'], 'draft=0'])
    print(out[-600:])
elif step == 'anchors':
    for nm, at in V['anchors'].items():
        cli(['op=work', 'sub=anchor', 'persona=summit', 'work=' + V['work'], 'name=' + nm, 'at=' + xyz(at), 'overwrite=1',
             'note=TASK-0680 ' + ('琴身正中（遊戲判主機的中心）' if nm == 'core' else '琴師站的那一格（腳下實心、頭上 12 格空）')])
elif step == 'model':
    # TASK-0793（ame 2026-10-21）起組裝件放的是自帶格子的外部模型，不是關聯；同名已存在 ⇒ CLI 擋下，先 unmodel 再跑
    cli(['op=work', 'sub=model', 'persona=summit', 'work=' + ASM, 'name=' + V['link'], 'source_work=' + V['work'], 'at=0,0,0', 'pivot=0,0,0', 'scale=1',
         'meta=' + json.dumps(V['meta'], ensure_ascii=False, sort_keys=True),
         'note=TASK-0680 管風琴就是魔法動力源（kind=engine）（TASK-0793：關聯換成自帶格子的模型，ame 2026-10-21）'])
elif step == 'link':
    raise SystemExit('⛔ link 步驟已停用：管風琴從 TASK-0793 起是外部模型，重建關聯會跟同名模型撞名 ⇒ 用 model')
elif step == 'unmodel':
    cli(['op=work', 'sub=unmodel', 'persona=summit', 'work=' + HALF, 'name=管風琴'])
else:
    raise SystemExit('步驟？ create|stamp|anchors|model|unmodel')
print(step, 'ok', ok, 'bad', bad)
