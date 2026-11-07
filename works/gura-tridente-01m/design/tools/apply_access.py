# TASK-1257 落格：照 masks/access/*.vox.txt、access_placement.json（draft_access.py 產）
#   船殼：刻（帶刻之前的顏色守門）→ 換色；gallery：刻；新子作品 -stern-glass／-deck-hold／-ladders-orlop／-ladders-hold（0.1 m、parent 船殼、tags sub）
#   → 關聯（組裝件 船尾窗玻璃 material=glass、甲板-hold 甲板 meta；甲板-orlop/梯子、甲板-hold/梯子 kind=ladders）→ 梯子固定點
#   → orlop 艙口圍欄開口、上砲甲板船頭門裡的兩階 → 門（模型 kind=door，門板引用藍鯊號 gura-pinas-01m-door）
#   每一刀標記 TASK-1257:begin／end；讀回格數對不上就停。
#   用法：python -I -X utf8 tools/apply_access.py <design>
import json, os, re, subprocess, sys, time

sys.stdout.reconfigure(encoding='utf-8')
D = os.path.abspath(sys.argv[1])
M = os.path.join(D, 'masks', 'access')
V = json.load(open(os.path.join(D, 'verify_access.json'), encoding='utf-8'))
PL = json.load(open(os.path.join(D, 'access_placement.json'), encoding='utf-8'))
MARK, NOTE = 'TASK-1257', 'TASK-1257 透明玻璃、貨艙平台與梯子、船頭與陽台的門（draft_access.py）'
retried = 0


def run(*a):
    return subprocess.run(['senate', 'cmd', 'sculpture'] + [x for kv in a for x in ('--arg', kv)], capture_output=True, text=True, encoding='utf-8', errors='replace')


def cli(*a):
    global retried
    for k in range(5):
        r = run(*a)
        out = r.stdout + r.stderr
        if r.returncode and any(t in out for t in ('IOException', '無法移除要被取代的檔案', 'Unable to remove the file to be replaced')) and k < 4:
            retried += 1
            time.sleep(0.5)
            continue
        break
    if r.returncode:
        print(out[-1500:])
        raise SystemExit('✗ ' + ' '.join(a[:5]))
    return r.stdout


xyz = lambda v: ','.join('%g' % c for c in v)
path = lambda f: os.path.join(M, f).replace(os.sep, '/')
num = lambda out, key: int(re.search(r'🔢 %s = (\d+)' % key, out).group(1))
cells = lambda f: V['files'][f]['cells']


def mark(work, phase, note=None):
    a = ['op=work', 'sub=mark', 'persona=gura', 'work=' + work, 'name=' + MARK, 'phase=' + phase]
    if note:
        a.append('note=' + note)
    cli(*a)


def carve(work, f):
    mark(work, 'begin')
    n0 = num(cli('op=stats', 'work=' + work), 'total_voxels')
    cli('op=carvevox', 'persona=gura', 'work=' + work, 'voxels=' + path(f), 'at=0,0,0', 'expect_pixels=%d' % cells(f), 'share=0')
    n = n0 - num(cli('op=stats', 'work=' + work), 'total_voxels')      # 讀回：刻前刻後的格數差
    if n != cells(f):
        raise SystemExit('✗ %s carved %d ≠ %d' % (work, n, cells(f)))
    return n


def stamp(work, f, overwrite=False):
    a = ['op=stampvox', 'persona=gura', 'work=' + work, 'voxels=' + path(f), 'at=0,0,0', 'expect_pixels=%d' % cells(f), 'share=0']
    if overwrite:
        a.append('overwrite=1')
    out = cli(*a)
    n = num(out, 'placed')
    if n != cells(f):
        raise SystemExit('✗ %s placed %d ≠ %d' % (work, n, cells(f)))
    return n


def new_work(wid, title):
    if run('op=work', 'sub=show', 'work=' + wid).returncode != 0:
        cli('op=work', 'sub=create', 'persona=gura', 'id=' + wid, 'title=' + title, 'size=1100,400,800', 'parent_work=gura-tridente-01m', 'tags=sub')
        cli('op=work', 'sub=update', 'persona=gura', 'work=' + wid, 'meters_per_voxel=0.1')
    return num(cli('op=stats', 'work=' + wid), 'total_voxels')


# ── 船殼、gallery ──
SKIP_HULL_CARVE = '--skip-hull-carve' in sys.argv         # 第一次跑在讀數鍵名那裡停了、刻已經落了（讀回 1,085,415 ＝ 1,101,062 − 15,647）
SKIP_GAL = '--skip-gallery-carve' in sys.argv             # 第二次跑同一個原因停在 gallery 刻之後（讀回 26,556 ＝ 41,405 − 14,849）
if '--resume-links' not in sys.argv:
    print('船殼 刻', 'skip' if SKIP_HULL_CARVE else carve('gura-tridente-01m', 'hull_carve.vox.txt'), '換色', stamp('gura-tridente-01m', 'hull_paint.vox.txt', overwrite=True))
mark('gura-tridente-01m', 'end', NOTE + '：船尾窗玻璃拿出來、窗後面刻穿、gallery 小艙打通舷側、陽台與船頭門洞、門框金') if '--resume-links' not in sys.argv else None
print('gallery 刻', 'skip' if SKIP_GAL else carve('gura-tridente-01m-quarter-gallery', 'gallery_carve.vox.txt'))
mark('gura-tridente-01m-quarter-gallery', 'end', NOTE + '：每一層掏成小艙、窗玻璃拿出來')

# ── 新子作品 ──
for wid, title, f in (('gura-tridente-01m-stern-glass', '三叉戟號 船尾窗玻璃', 'glass.vox.txt'),
                      ('gura-tridente-01m-deck-hold', '三叉戟號 甲板 貨艙', 'deck_hold.vox.txt'),
                      ('gura-tridente-01m-ladders-orlop', '三叉戟號 梯子（上到orlop）', 'ladders_orlop.vox.txt'),
                      ('gura-tridente-01m-ladders-hold', '三叉戟號 梯子（上到貨艙）', 'ladders_hold.vox.txt')):
    have = new_work(wid, title)
    if have == 0:
        stamp(wid, f)
    elif have != cells(f):
        raise SystemExit('✗ %s 已有 %d 格 ≠ %d' % (wid, have, cells(f)))
    print('✓', wid, cells(f))
for wid, lads in PL['ladders'].items():
    for nm, L in lads.items():
        for k, p in L['points'].items():
            cli('op=work', 'sub=anchor', 'persona=gura', 'work=' + wid, 'name=%s.%s' % (nm, k), 'at=' + xyz(p), 'overwrite=1', 'note=梯子（造船規格 §9；draft_access.py）')
print('✓ 梯子固定點')
cli('op=work', 'sub=link', 'persona=gura', 'work=gura-tridente-01m-assembly', 'name=船尾窗玻璃', 'source_work=gura-tridente-01m-stern-glass', 'at=0,0,0', 'overwrite=1',
    'note=' + NOTE, 'meta=' + json.dumps({'material': 'glass'}))
cli('op=work', 'sub=link', 'persona=gura', 'work=gura-tridente-01m-assembly', 'name=甲板-hold', 'source_work=gura-tridente-01m-deck-hold', 'at=0,0,0', 'overwrite=1',
    'note=' + NOTE + '：兩間彈藥庫之間的平台', 'meta=' + json.dumps(PL['deck_meta'], ensure_ascii=False, separators=(',', ':')))
cli('op=work', 'sub=link', 'persona=gura', 'work=gura-tridente-01m-deck-orlop', 'name=梯子', 'source_work=gura-tridente-01m-ladders-orlop', 'at=0,0,0', 'overwrite=1',
    'note=' + NOTE + '：貨艙平台 → orlop', 'meta=' + json.dumps({'kind': 'ladders'}))
cli('op=work', 'sub=link', 'persona=gura', 'work=gura-tridente-01m-deck-hold', 'name=梯子', 'source_work=gura-tridente-01m-ladders-hold', 'at=0,0,0', 'overwrite=1',
    'note=' + NOTE + '：艙底 → 貨艙平台', 'meta=' + json.dumps({'kind': 'ladders'}))
print('✓ 關聯')

# ── orlop 圍欄開口、船頭門裡的兩階 ──
print('orlop 圍欄 刻', carve('gura-tridente-01m-deck-orlop', 'orlop_carve.vox.txt'))
mark('gura-tridente-01m-deck-orlop', 'end', NOTE + '：艙口圍欄在貨艙梯頭那一段開口')
mark('gura-tridente-01m-deck-upper', 'begin')
print('上砲甲板 兩階', stamp('gura-tridente-01m-deck-upper', 'upper_steps.vox.txt'))
mark('gura-tridente-01m-deck-upper', 'end', NOTE + '：船頭門裡的兩階')

# ── 門 ──
DP = PL['doors']
for r in DP['rows']:
    cli('op=work', 'sub=model', 'persona=gura', 'work=' + r['host'], 'name=' + r['name'], 'source_work=' + DP['work'], 'at=' + xyz(r['at']), 'pivot=' + xyz(DP['pivot']),
        'rotate=0,0,%g' % r['rotate'], 'scale=' + xyz(r['scale']), 'overwrite=1', 'meta=' + json.dumps(r['meta'], ensure_ascii=False, separators=(',', ':')),
        'note=%s 門：%s、往外開' % (MARK, r['why']))
print('✓ 門 %d 扇' % len(DP['rows']), 'IOException 重試', retried)
