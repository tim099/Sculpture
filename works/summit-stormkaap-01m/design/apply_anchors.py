# 錨：照 verify_anchors.json 下 CLI（夜隼號、風暴角號共用；照 design 資料夾認船）
# 用法：python -I -X utf8 -B apply_anchors.py <design> <步驟>
#   步驟：create（吊錨架子作品）｜stamp（落格，只跑一次；讀回 placed）｜link（組裝件兩條關聯：右舷、左舷 mirror=y）
#        ｜models（船殼作品放兩隻錨：共用元件、pivot ＝ ring、meta kind=anchor）｜hawse（船殼固定點 hawse-S／P）
#   ⛔ 失敗那一行整段印出來
import sys, os, json, re, subprocess

sys.stdout.reconfigure(encoding='utf-8')
D, step = os.path.abspath(sys.argv[1]), sys.argv[2]
V = json.load(open(os.path.join(D, 'verify_anchors.json'), encoding='utf-8'))
PRE = V['ship']; ASM = PRE + '-assembly'; C = V['cathead']
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
    rc, _ = cli(['op=work', 'sub=show', 'work=' + C['work']], quiet_fail=True)
    if rc == 0: print('已有', C['work'])
    else: cli(['op=work', 'sub=create', 'persona=summit', 'id=' + C['work'], 'title=' + C['title'], 'size=' + xyz(C['frame_size']), 'parent_work=' + PRE, 'tags=sub']); print('建立', C['work'])
    cli(['op=work', 'sub=update', 'persona=summit', 'work=' + C['work'], 'meters_per_voxel=0.1'])
elif step == 'stamp':
    rc, out = cli(['op=stampvox', 'persona=summit', 'work=' + C['work'], 'voxels=' + os.path.join(D, C['file']).replace(chr(92), '/'), 'at=0,0,0',
                   'expect_pixels=%d' % C['voxels'], 'draft=0'])
    m = re.search(r'🔢 placed = (\d+)', out)
    print('stamp', C['work'], 'voxels', C['voxels'], 'placed', m.group(1) if m else '?')
elif step == 'link':
    for L in C['links']:
        args = ['op=work', 'sub=link', 'persona=summit', 'work=' + ASM, 'name=' + L['name'], 'source_work=' + C['work'], 'at=' + xyz(L['at']), 'overwrite=1',
                'note=吊錨架（錨掛在端下；%s）' % ('左舷 mirror=y' if L['mirror'] else '右舷')]
        if L['mirror']: args.append('mirror=' + L['mirror'])
        cli(args)
elif step == 'models':
    for M in V['models']:
        cli(['op=work', 'sub=model', 'persona=summit', 'work=' + PRE, 'name=' + M['name'], 'source_work=' + V['source'], 'at=' + xyz(M['at']),
             'pivot=' + xyz(V['pivot']), 'rotate=0,0,0', 'scale=%g' % V['scale'], 'overwrite=1', 'meta=' + json.dumps(V['meta'], ensure_ascii=False, sort_keys=True),
             'note=錨（共用元件 basecamp 憲法號 -anchor；pivot ＝ ring，掛在吊錨架端下；scale %g ⚠ 照排水量估算）' % V['scale']])
elif step == 'hawse':
    for nm, at in sorted(V['hawse'].items()):
        cli(['op=work', 'sub=anchor', 'persona=summit', 'work=' + PRE, 'name=' + nm, 'at=' + xyz(at), 'overwrite=1',
             'note=錨鏈孔（鐵鍊從船殼出來的地方；造船規格 §9 anchor）'])
else:
    raise SystemExit('步驟？')
print(step, 'ok', ok, 'bad', bad)
