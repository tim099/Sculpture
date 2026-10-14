# 岩堡港 房屋落格（TASK-0580）：照 masks/houses/<配色>.vox.txt 下 CLI —— 每個配色一件子作品。
# 用法：python -I -X utf8 -B apply_houses.py <design 資料夾> <步驟> [配色 ...]（不給 ⇒ verify_houses.json 裡全部）
#   步驟：create（已存在 ⇒ 只補 meters_per_voxel 與 tags）
#         stamp（匯出子作品現在的格、跟清單比：多的 carvevox 帶原色守門、少的或色不同的 stampvox overwrite ⇒ 第一次 ＝ 整份貼上，重跑只補差）
#         check（只讀引擎匯出：跟清單逐格比 缺／多／色差；stats structure=1 的元件數與封閉空腔）
import sys, os, json, re, subprocess

sys.stdout.reconfigure(encoding='utf-8')
D, step = os.path.abspath(sys.argv[1]), sys.argv[2]
R = json.load(open(os.path.join(D, 'verify_houses.json'), encoding='utf-8'))
plan = json.load(open(os.path.join(D, 'plan.json'), encoding='utf-8'))
want_vars = sys.argv[3:] or sorted(R.keys())
PARENT = 'summit-rocher-01m'
TMP = os.path.join(os.path.dirname(D), 'exports', 'houses')
os.makedirs(TMP, exist_ok=True)
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


def rd(p):
    return {tuple(map(int, l.split(',')[:3])): int(l.split(',')[3]) for l in open(p, encoding='utf-8') if l.strip() and not l.startswith('#')}


def dump(path, cells):
    with open(path, 'w', encoding='utf-8', newline='\n') as f:
        for k, c in sorted(cells.items()):
            f.write('%d,%d,%d,%d\n' % (k[0], k[1], k[2], c))


def wid(var):
    return PARENT + '-house-' + var.lower()


def title(var):
    typ = R[var]['meta']['type']
    v = plan['houses'][typ]['variants'][var]
    return '岩堡港｜房屋 %s（%s；牆 %s、百葉 %s、屋頂 %s）' % (var, plan['houses'][typ]['label'], v['wall'], v['shutter'], v['roof'])


def export(var):
    p = os.path.join(TMP, wid(var) + '.list.txt').replace('\\', '/')
    rc, _ = cli(['op=export', 'format=list', 'work=' + wid(var), 'out=' + p])
    return rd(p) if rc == 0 else None


for var in want_vars:
    mask = os.path.join(D, 'masks', 'houses', var + '.vox.txt')
    if step == 'create':
        rc, _ = cli(['op=work', 'sub=show', 'work=' + wid(var)], quiet_fail=True)
        if rc:
            cli(['op=work', 'sub=create', 'persona=summit', 'id=' + wid(var), 'title=' + title(var), 'size=' + ','.join(str(v) for v in R[var]['bbox']), 'parent_work=' + PARENT])
        cli(['op=work', 'sub=update', 'persona=summit', 'work=' + wid(var), 'meters_per_voxel=0.1', 'tags=sub'])
        print('create', wid(var))
    elif step == 'stamp':
        cur, want = export(var), rd(mask)
        carve = {k: c for k, c in cur.items() if k not in want}
        add = {k: c for k, c in want.items() if cur.get(k) != c}
        for nm, cells, args in (('carve', carve, ['op=carvevox']), ('stamp', add, ['op=stampvox', 'overwrite=1'])):
            if not cells:
                continue
            p = os.path.join(TMP, '%s.%s.vox.txt' % (wid(var), nm)); dump(p, cells)
            rc, out = cli(args + ['persona=summit', 'work=' + wid(var), 'voxels=' + p.replace('\\', '/'), 'at=0,0,0', 'expect_pixels=%d' % len(cells), 'draft=0', 'share=0'])
            m = re.search(r'placed\s*=\s*(\d+)', out)
            print(var, nm, len(cells), 'rc', rc, 'placed', m.group(1) if m else '?')
        print(var, '現況 %d → 清單 %d｜刻 %d、補／換色 %d' % (len(cur), len(want), len(carve), len(add)))
    elif step == 'check':
        cur, want = export(var), rd(mask)
        miss = sum(1 for k in want if k not in cur)
        extra = sum(1 for k in cur if k not in want)
        diff = sum(1 for k, c in want.items() if k in cur and cur[k] != c)
        rc, out = cli(['op=stats', 'work=' + wid(var), 'structure=1'])
        nums = dict(re.findall(r'🔢 (\w+) = (\S+)', out))
        keys = [k for k in nums if re.search(r'compon|cavit|voxel|count', k)]
        print(var, '作品 %d 格｜缺 %d 多 %d 色差 %d｜' % (len(cur), miss, extra, diff) + '  '.join('%s=%s' % (k, nums[k]) for k in keys))
    else:
        raise SystemExit('步驟？ create|stamp|check')
print(step, 'ok', ok, 'bad', bad)
