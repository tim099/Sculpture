# 餘燼號 階段十二 砲具：建兩件一舷子作品（下層／上層）→ 落格 → 關聯進甲板子作品（＋鏡像）→ 登記環的固定點 → 組裝件拉砲索
# 用法：python -I gunfittings_apply.py <design 資料夾>（重跑：子作品已在 ⇒ 不重建；關聯已在 ⇒ 不重掛；固定點／繩 overwrite=1）
#   ⚠ 寫入偶爾 IOException（無法移除要被取代的檔案；另開工作卡）⇒ 失敗的那一筆最多重試 3 次
import sys, os, json, subprocess, time
sys.stdout.reconfigure(encoding='utf-8')
D = os.path.abspath(sys.argv[1])
sys.path.insert(0, D)
from draft_ladders import existing_links   # noqa: E402

HULL = 'basecamp-ember-01m'
P = json.load(open(os.path.join(D, 'plan.json'), encoding='utf-8'))['gunfittings_build']
PTS = json.load(open(os.path.join(D, 'gunfittings_points.json'), encoding='utf-8'))['points']
ROPES = json.load(open(os.path.join(D, 'gun_ropes.json'), encoding='utf-8'))['ropes']
V = json.load(open(os.path.join(D, 'verify_gunfittings.json'), encoding='utf-8'))
ok = bad = retried = 0


def cli(args, show=False, tries=3):
    global ok, bad, retried
    for k in range(tries):
        r = subprocess.run(['senate', 'cmd', 'sculpture'] + sum([['--arg', a] for a in args], []), capture_output=True, text=True, encoding='utf-8', errors='replace')
        if r.returncode == 0:
            ok += 1
            if show:
                print('\n'.join(l for l in r.stdout.splitlines() if l.startswith('✓') or 'placed =' in l))
            return 0, r.stdout
        if 'IOException' in r.stdout + r.stderr and k < tries - 1:
            retried += 1
            time.sleep(0.5)
            continue
        bad += 1
        print('✗', ' '.join(args[:6]), (r.stdout + r.stderr)[-300:])
        return r.returncode, r.stdout


def xyz(v):
    return ','.join(('%g' % c) for c in v)


for dk in P['decks']:
    w = dk['id']
    rc, _ = cli(['op=work', 'sub=show', 'work=' + w], tries=1)
    if rc:
        bad -= 1
        cli(['op=work', 'sub=create', 'persona=basecamp', 'id=' + w, 'title=' + dk['title'], 'size=' + xyz(dk['box']['size']), 'parent_work=' + HULL, 'tags=sub'], show=True)
        cli(['op=work', 'sub=update', 'persona=basecamp', 'work=' + w, 'meters_per_voxel=0.1'])
        path = os.path.join(D, 'masks', 'gunfittings', dk['deck'] + '.vox.txt').replace('\\', '/')
        cli(['op=stampvox', 'persona=basecamp', 'work=' + w, 'voxels=' + path, 'at=0,0,0', 'expect_pixels=%d' % V['decks'][dk['deck']]['cells']], show=True)
    else:
        print('· 已在：' + w)
    have = set(existing_links(dk['link_in']))
    at = dk['box']['at']
    atm = [at[0], 321 - at[1] - dk['box']['size'][1], at[2]]
    for name, a, mir, note in ((dk['link'], at, '', '階段十二：砲具一舷'), (dk['mirror_link'], atm, 'y', '階段十二：砲具另一舷（mirror=y）')):
        if name in have:
            print('· 關聯已在：%s / %s' % (dk['link_in'], name))
            continue
        args = ['op=work', 'sub=link', 'persona=basecamp', 'work=' + dk['link_in'], 'name=' + name, 'source_work=' + w, 'at=' + xyz(a), 'note=' + note]
        if mir:
            args.append('mirror=' + mir)
        cli(args, show=True)
for p in PTS:
    cli(['op=work', 'sub=anchor', 'persona=basecamp', 'work=' + p['work'], 'name=' + p['name'], 'at=' + xyz(p['local']), 'overwrite=1', 'note=砲具的環（世界 %s）' % xyz(p['world'])])
for r in ROPES:
    cli(['op=work', 'sub=rope', 'persona=basecamp', 'work=' + P['assembly'], 'name=' + r['name'], 'from=' + r['from'], 'to=' + r['to'], 'overwrite=1',
         'slack=%g' % r['slack'], 'color=' + r['color'], 'thickness=%g' % r['thickness'], 'group=' + r['group'], 'note=砲索（階段十二）'])
print('ok %d / bad %d / 重試 %d' % (ok, bad, retried))
