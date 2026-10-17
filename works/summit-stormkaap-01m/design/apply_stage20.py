# 階段二十 下 CLI（TASK-0685）：往下通貨艙的梯子＋彈藥庫門口踏板／船長室 ↔ 船尾陽台的門／絞盤＋上甲板主艙口格柵
#   讀 verify_hold_ladders.json、verify_stern_door.json、verify_capstan_grating.json（三支 draft_* 產的）。
#   步驟：hold_create｜hold_stamp｜hold_link｜hold_anchors｜hold_ropes｜door_carve｜grat_create｜grat_stamp｜models
#   · 格的那幾步只跑一次（每刀讀回 placed）；其餘 overwrite=1。⛔ 失敗那一行整段印出來
# 用法：python -I -X utf8 -B apply_stage20.py <design> <步驟>
import sys, os, json, re, subprocess

sys.stdout.reconfigure(encoding='utf-8')
D, step = os.path.abspath(sys.argv[1]), sys.argv[2]
VH = json.load(open(os.path.join(D, 'verify_hold_ladders.json'), encoding='utf-8'))
VD = json.load(open(os.path.join(D, 'verify_stern_door.json'), encoding='utf-8'))
VG = json.load(open(os.path.join(D, 'verify_capstan_grating.json'), encoding='utf-8'))
PRE = 'summit-stormkaap-01m'; ASM = PRE + '-assembly'
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


def xyz(p):
    return ','.join('%g' % v for v in p)


def fwd(p):
    return os.path.join(D, p).replace('\\', '/')


def create(work, title, size, mpv):
    rc, _ = cli(['op=work', 'sub=show', 'work=' + work], quiet_fail=True)
    if rc == 0: print('已有', work)
    else: cli(['op=work', 'sub=create', 'persona=summit', 'id=' + work, 'title=' + title, 'size=' + xyz(size), 'parent_work=' + PRE, 'tags=sub']); print('建立', work)
    cli(['op=work', 'sub=update', 'persona=summit', 'work=' + work, 'meters_per_voxel=%g' % mpv])


def stamp(work, op, path, n):
    rc, out = cli(['op=' + op, 'persona=summit', 'work=' + work, 'voxels=' + fwd(path), 'at=0,0,0', 'expect_pixels=%d' % n, 'draft=0'])
    m = re.search(r'🔢 placed = (\d+)', out) or re.search(r'🔢 carved = (\d+)', out)
    print(op, work, path, 'voxels', n, '讀回', m.group(0) if m else '?')


if step == 'hold_create':
    create(VH['work'], VH['title'], [736, 261, 576], 0.1)
elif step == 'hold_stamp':
    stamp(VH['work'], 'stampvox', VH['file']['path'], VH['file']['cells'])
elif step == 'hold_link':
    cli(['op=work', 'sub=link', 'persona=summit', 'work=' + VH['link_in'], 'name=' + VH['link'], 'source_work=' + VH['work'], 'at=0,0,0', 'overwrite=1',
         'meta=' + json.dumps({'kind': 'ladders'}), 'note=階段二十 往下通貨艙的梯子（給遊戲 kind=ladders）＋彈藥庫門口踏板'])
elif step == 'hold_anchors':
    n = 0
    for a in VH['anchors']:
        cli(['op=work', 'sub=anchor', 'persona=summit', 'work=' + VH['work'], 'name=' + a['name'], 'at=' + xyz(a['at']), 'overwrite=1', 'note=' + a['note']]); n += 1
    for lid, P_ in sorted(VH['points'].items()):
        for k in ('foot', 'lo', 'hi', 'head'):
            assert P_[k] is not None, (lid, k)
            cli(['op=work', 'sub=anchor', 'persona=summit', 'work=' + VH['work'], 'name=%s.%s' % (lid, k), 'at=' + xyz(P_[k]), 'overwrite=1',
                 'note=梯子給遊戲的點（draft_hold_ladders.py；造船規格 §9）']); n += 1
    print('anchors', n)
elif step == 'hold_ropes':
    for r in VH['ropes']:
        cli(['op=work', 'sub=rope', 'persona=summit', 'work=' + ASM, 'name=' + r['name'], 'from=' + r['from'], 'to=' + r['to'], 'overwrite=1',
             'slack=%g' % r['slack'], 'color=' + r['color'], 'thickness=%g' % r['thickness'], 'group=' + r['group'], 'note=扶手繩（階段二十）'])
    print('ropes', len(VH['ropes']))
elif step == 'door_carve':
    for w, f in sorted(VD['files'].items()):
        stamp(w, 'carvevox', f['path'], f['cells'])
elif step == 'grat_create':
    g = VG['grating']; create(g['work'], g['title'], g['size'], g['mpv'])
elif step == 'grat_stamp':
    g = VG['grating']; stamp(g['work'], 'stampvox', g['file']['path'], g['file']['cells'])
elif step == 'models':
    for m in VG['models']:
        cli(['op=work', 'sub=model', 'persona=summit', 'work=' + m['host_work'], 'name=' + m['name'], 'source_work=' + m['work'], 'at=' + xyz(m['at']),
             'pivot=' + xyz(m['pivot']), 'rotate=0,0,0', 'scale=%g' % m['scale'], 'overwrite=1', 'meta=' + json.dumps(m['meta'], ensure_ascii=False, sort_keys=True),
             'note=階段二十（verify_capstan_grating.json）'])
        print('model', m['host_link'] + '/' + m['name'], xyz(m['at']))
else:
    raise SystemExit('步驟？')
print(step, 'ok', ok, 'bad', bad)
