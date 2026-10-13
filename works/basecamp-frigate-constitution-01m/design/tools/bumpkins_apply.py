# 憲法號 階段四十一 bumpkins＋main brace：照 verify_bumpkins.json 下 CLI
#   0. -chesstrees-side 刻掉階段三十五放錯邊的 main brace chesstree（masks/bumpkins/chesstree_main_brace_carve.vox.txt，帶色守門、11 格）
#   1. -main-brace-bumpkin-side、-foretack-bumpkin-side 子作品（一舷 S、0.1 m、parent 船殼、tags sub）＋固定點
#   2. 組裝件關聯 main-brace-bumpkin／-鏡像、foretack-bumpkin／-鏡像（mirror=y、at.y ＝ 321 − at.y − 高）
#   3. 繩：main brace 兩舷各三段（standing／fall／lead，組 running/braces）、fore tack bumpkin guy 兩舷（組 standing/bumpkins）、
#      fore-course.tack-S 改綁 S 舷 bumpkin（上風那一舷；P 舷是下風，tack 照舊綁 pin）
#   已在的子作品不重建不重落、關聯／繩已在就跳過；tack-S 只有還綁在 pin 上時才改。
# 用法：python -I bumpkins_apply.py <design 資料夾>
# ⚠ 寫入偶爾 IOException（TASK-0534）⇒ 只對那一句重試，最多 3 次；中文／英文系統訊息都要認
import sys, os, json, subprocess, time, tempfile
sys.stdout.reconfigure(encoding='utf-8')
D = os.path.abspath(sys.argv[1])
V = json.load(open(os.path.join(D, 'verify_bumpkins.json'), encoding='utf-8'))
HULL = 'basecamp-frigate-constitution-01m'
ASM = HULL + '-assembly'
IOE = ('無法移除要被取代的檔案', 'Unable to remove the file to be replaced')
ok = bad = retried = 0
RUN = '#a08458'


def run(args):
    return subprocess.run(['senate', 'cmd', 'sculpture'] + sum([['--arg', a] for a in args], []), capture_output=True, text=True, encoding='utf-8', errors='replace')


def cli(args):
    global ok, bad, retried
    for k in range(4):
        r = run(args)
        if r.returncode and any(t in (r.stdout + r.stderr) for t in IOE) and k < 3:
            retried += 1
            time.sleep(0.5)
            continue
        break
    if r.returncode:
        bad += 1
        print('✗', ' '.join(args[:5]), (r.stdout + r.stderr)[-500:])
        raise SystemExit(1)
    ok += 1
    print('\n'.join(l for l in r.stdout.splitlines() if l.startswith('✓') or 'placed =' in l))


def xyz(v):
    return ','.join(('%.3f' % c).rstrip('0').rstrip('.') if isinstance(c, float) else '%d' % c for c in v)


def path(rel):
    return os.path.join(D, rel).replace('\\', '/')


# 0. 刻掉放錯邊的 chesstree（帶色守門；已刻過 ⇒ 守門對不上會整刀拒絕 ⇒ 先看那一格還在不在）
CH = HULL + '-chesstrees-side'
carve = path('masks/bumpkins/chesstree_main_brace_carve.vox.txt')
n = sum(1 for l in open(carve, encoding='utf-8') if l.strip())
exp = os.path.join(tempfile.mkdtemp(), 'chesstrees_now.txt').replace(os.sep, '/')
r = run(['op=export', 'work=' + CH, 'format=list', 'links=none', 'out=' + exp])
have = set(l.strip() for l in open(exp, encoding='utf-8') if l.strip() and not l.startswith('#')) if r.returncode == 0 else set()
os.remove(exp) if os.path.exists(exp) else None
want = set(l.strip() for l in open(carve, encoding='utf-8') if l.strip())
if want <= have:
    cli(['op=carvevox', 'persona=basecamp', 'work=' + CH, 'voxels=' + carve, 'at=0,0,0', 'expect_pixels=%d' % n])
elif not (want & have):
    print('· main brace chesstree 已刻掉')
else:
    raise SystemExit('✗ chesstree 只剩一部分 —— 先看清楚再動')

for key, W, title, note in (
        ('quarter', HULL + '-main-brace-bumpkin-side', '憲法號 main brace bumpkin＋chesstree（一舷；1931 plan 24422／24474）', 'main brace'),
        ('bow', HULL + '-foretack-bumpkin-side', '憲法號 fore tack bumpkin（一舷；1931 plan 24422）', 'fore tack bumpkin')):
    g = V[key]
    vox = path('masks/bumpkins/%s.vox.txt' % ('main_brace_bumpkin_side' if key == 'quarter' else 'foretack_bumpkin_side'))
    if run(['op=work', 'sub=show', 'work=' + W]).returncode == 0:
        print('· %s 已在 ⇒ 不重建' % W)
    else:
        cli(['op=work', 'sub=create', 'persona=basecamp', 'id=' + W, 'title=' + title, 'size=' + xyz(g['frame_size']), 'parent_work=' + HULL, 'tags=sub'])
        cli(['op=work', 'sub=update', 'persona=basecamp', 'work=' + W, 'meters_per_voxel=0.1'])
        cli(['op=stampvox', 'persona=basecamp', 'work=' + W, 'voxels=' + vox, 'at=0,0,0', 'expect_pixels=%d' % g['cells']])
    have = run(['op=work', 'sub=anchors', 'work=' + W]).stdout
    for name, p in g['anchors'].items():
        if '`%s`' % name in have:
            print('· 固定點 %s 已在' % name)
            continue
        cli(['op=work', 'sub=anchor', 'persona=basecamp', 'work=' + W, 'name=' + name, 'at=' + xyz(p), 'note=' + note + '（階段四十一）'])
    links = run(['op=work', 'sub=links', 'work=' + ASM]).stdout
    base = 'main-brace-bumpkin' if key == 'quarter' else 'foretack-bumpkin'
    for name, at, mirror in ((base, g['frame_at'], ''), (base + '-鏡像', g['mirror_at'], 'y')):
        if '`%s`' % name in links:
            print('· 關聯 %s 已在' % name)
            continue
        args = ['op=work', 'sub=link', 'persona=basecamp', 'work=' + ASM, 'name=' + name, 'source_work=' + W, 'at=' + xyz(at),
                'note=' + title + '（階段四十一）']
        if mirror:
            args.append('mirror=' + mirror)
        cli(args)

ropes = run(['op=work', 'sub=ropes', 'work=' + ASM]).stdout
want = []
for sd, link, slack in (('S', 'main-brace-bumpkin', 1.001), ('P', 'main-brace-bumpkin-鏡像', 1.0)):   # S 上風 ⇒ brace 放一點；P 下風 ⇒ 拉直
    arm = 'model:主桅/yard-main-course/arm-' + sd
    want += [('main-brace-%s.standing' % sd, link + '/brace-eye', arm, slack, RUN, 0.5, 'running/braces', 'main brace 固定端（bumpkin 尖 → 帆桁端）'),
             ('main-brace-%s.fall' % sd, arm, link + '/brace-block', slack, RUN, 0.5, 'running/braces', 'main brace 回來那段（帆桁端 → bumpkin 滑車）'),
             ('main-brace-%s.lead' % sd, link + '/brace-block', link + '/chesstree', 1.0, RUN, 0.5, 'running/braces', 'main brace 進 chesstree')]
# 一律寫小數：整數會被當格心（v1 寫 164／157 ⇒ 讀成 164.5／157.5、兩舷差一格）
for sd, link, knee in (('S', 'foretack-bumpkin', '718.5,163.5,115.5'), ('P', 'foretack-bumpkin-鏡像', '718.5,157.5,115.5')):
    want.append(('foretack-bumpkin-%s.guy' % sd, link + '/guy', knee, 1.0, '#2b2620', 0.5, 'standing/bumpkins', 'fore tack bumpkin 的 guy（拉回 head knee；1931 #24422）'))
for name, a, b, slack, col, th, grp, note in want:
    if '`%s`' % name in ropes:
        print('· 繩 %s 已在' % name)
        continue
    cli(['op=work', 'sub=rope', 'persona=basecamp', 'work=' + ASM, 'name=' + name, 'from=' + a, 'to=' + b, 'slack=' + xyz([slack]),
         'color=' + col, 'thickness=' + xyz([th]), 'group=' + grp, 'note=' + note + '（階段四十一）'])

# fore-course.tack-S：pin → bumpkin（上風那一舷；tack 拉到船頭外面）
line = next((l for l in ropes.splitlines() if '`fore-course.tack-S`' in l), '')
if 'pinrail-13' in line:
    cli(['op=work', 'sub=unrope', 'persona=basecamp', 'work=' + ASM, 'name=fore-course.tack-S'])
    cli(['op=work', 'sub=rope', 'persona=basecamp', 'work=' + ASM, 'name=fore-course.tack-S', 'from=sail:fore-course/clew_s', 'to=foretack-bumpkin/tack',
         'slack=1', 'color=' + RUN, 'thickness=0.5', 'group=running/tacks',
         'note=fore course 上風 tack 拉到 fore tack bumpkin（階段四十一；原本綁 pinrail-13.pin-3 slack 0.8；改 bumpkin 後 0.8 會把帆角拉過去 ⇒ 1）'])
# ⚠ v1 照舊用 slack 0.8 ⇒ 直線 92.4 縮成 74、帆角被往船頭拉、fore course 變成漏斗 ⇒ 1（帆角讀數：綁 pin 時 613.2,209,156.2、綁 bumpkin 616.2,209.3,151.3）
else:
    print('· fore-course.tack-S 不是綁 pin（%s）⇒ 不動' % line[:120])
print('ok %d / bad %d / 重試 %d' % (ok, bad, retried))
