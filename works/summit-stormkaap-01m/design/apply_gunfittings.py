# 階段十四：照 verify_gunfittings.json 下 CLI —— 砲具子作品兩件（下砲甲板、上砲甲板）＋各掛在自己那層甲板的關聯 `砲具` ＋ 206 條砲索（組裝件）
# 從夜隼號 apply_gunfittings.py 改：兩件子作品、關聯掛在甲板子作品（不是組裝件）、不鏡像。
# 用法：python -I -X utf8 -B apply_gunfittings.py <design 資料夾> <步驟> [繩名 regex]
#   步驟：create（開子作品，parent 船殼、記 0.1 m、tags sub）｜stamp（每刀印 placed）｜anchors｜links（甲板子作品）｜ropes（組裝件，分組 guns/…）
#   · create 已存在 ⇒ 略過；anchors／links／ropes 用 overwrite=1 ⇒ 重跑一樣；⛔ 失敗整段印出來
import sys, os, json, re, subprocess

sys.stdout.reconfigure(encoding='utf-8')
D, step = os.path.abspath(sys.argv[1]), sys.argv[2]
flt = re.compile(sys.argv[3] if len(sys.argv) > 3 else '.')
V = json.load(open(os.path.join(D, 'verify_gunfittings.json'), encoding='utf-8'))
PRE = 'summit-stormkaap-01m'
ASM = PRE + '-assembly'
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
    for w in V['works']:
        rc, _ = cli(['op=work', 'sub=show', 'work=' + w['work']], quiet_fail=True)
        if rc == 0:
            print('已有', w['work'])
        else:
            cli(['op=work', 'sub=create', 'persona=summit', 'id=' + w['work'], 'title=' + w['title'], 'size=' + xyz(w['frame_size']), 'parent_work=' + PRE, 'tags=sub'])
            print('建立', w['work'])
        cli(['op=work', 'sub=update', 'persona=summit', 'work=' + w['work'], 'meters_per_voxel=0.1'])
elif step == 'stamp':
    for o in V['stamp_order']:
        path = os.path.join(D, o['file']).replace('\\', '/')
        rc, out = cli(['op=stampvox', 'persona=summit', 'work=' + o['work'], 'voxels=' + path, 'at=0,0,0', 'expect_pixels=%d' % o['voxels'], 'draft=0'])
        m = re.search(r'placed[^0-9]{0,8}([0-9,]+)', out)
        print('stamp', o['work'], o['voxels'], 'placed', m.group(1) if m else '?')
elif step == 'restamp':
    # 子作品已經有格 ⇒ 匯出它現在的格（引擎），跟 mask 比：多的 carvevox（帶原色守門）、少的 stampvox。暫存檔放 <design>/../exports/restamp/（不進版控）
    tmp = os.path.join(os.path.dirname(D), 'exports', 'restamp'); os.makedirs(tmp, exist_ok=True)
    for o in V['stamp_order']:
        cur_p = os.path.join(tmp, o['work'] + '.list.txt').replace('\\', '/')
        cli(['op=export', 'format=list', 'work=' + o['work'], 'out=' + cur_p])
        rd = lambda p: {tuple(map(int, l.split(',')[:3])): int(l.split(',')[3]) for l in open(p, encoding='utf-8') if l.strip() and not l.startswith('#')}
        cur, want = rd(cur_p), rd(os.path.join(D, o['file']))
        carve = {k: v for k, v in cur.items() if want.get(k) != v}
        add = {k: v for k, v in want.items() if cur.get(k) != v}
        for nm, cells, op in (('carve', carve, 'carvevox'), ('stamp', add, 'stampvox')):
            if not cells:
                continue
            p = os.path.join(tmp, '%s.%s.vox.txt' % (o['work'], nm)).replace('\\', '/')
            open(p, 'w', encoding='utf-8', newline='\n').write(''.join('%d,%d,%d,%d\n' % (k + (v,)) for k, v in sorted(cells.items())))
            rc, out = cli(['op=' + op, 'persona=summit', 'work=' + o['work'], 'voxels=' + p, 'at=0,0,0', 'expect_pixels=%d' % len(cells), 'draft=0'])
            print(o['work'], nm, len(cells), 'rc', rc)
        print(o['work'], '現況', len(cur), '→ 目標', len(want), '｜刻', len(carve), '補', len(add))
elif step == 'anchors':
    for a in V['anchors']:
        cli(['op=work', 'sub=anchor', 'persona=summit', 'work=' + a['work'], 'name=' + a['name'], 'at=' + xyz(a['at']), 'overwrite=1',
             'note=%s %s（階段十四 verify_gunfittings.json；世界座標 %s）' % (a['kind'], a['gun'], xyz(a['world']))])
    print('anchors', len(V['anchors']))
elif step == 'links':
    for w in V['works']:
        cli(['op=work', 'sub=link', 'persona=summit', 'work=' + w['link_in'], 'name=' + w['link'], 'source_work=' + w['work'], 'at=' + xyz(w['frame_at']),
             'overwrite=1', 'note=階段十四 砲具'])
        print('link', w['deck'] + '/' + w['link'], xyz(w['frame_at']))
elif step == 'ropes':
    n = 0
    for r in V['ropes']:
        if not flt.search(r['name']):
            continue
        n += 1
        cli(['op=work', 'sub=rope', 'persona=summit', 'work=' + ASM, 'name=' + r['name'], 'from=' + r['from'], 'to=' + r['to'], 'overwrite=1',
             'slack=%g' % r['slack'], 'color=' + r['color'], 'thickness=%g' % r['thickness'], 'group=' + r['group'], 'note=砲索（階段十四）'])
    print('ropes', n)
else:
    raise SystemExit('步驟？ create|stamp|restamp|anchors|links|ropes')
print(step, 'ok', ok, 'bad', bad)
