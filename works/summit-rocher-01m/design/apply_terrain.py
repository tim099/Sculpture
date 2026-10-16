# 岩堡港 地形與碼頭落格（TASK-0580 第三階段）：照 masks/terrain/<件>.vox.txt 下 CLI。
# 用法：python -I -X utf8 -B apply_terrain.py <design 資料夾> <步驟> [件 ...]（件：terrain、quay、walls（terrain.py 產）、rock、battery（fort.py 產）；不給 ⇒ terrain、quay）
#   步驟：create（已存在 ⇒ 只補 meters_per_voxel 與 tags）
#         stamp（匯出現況跟清單比：多的 carvevox、少的或色不同的 stampvox overwrite；每刀最多 CHUNK 格 —— 引擎單刀上限 1,000,000）
#         check（只讀引擎匯出：缺／多／色差；stats structure=1 的元件數與封閉空腔）
import sys, os, json, re, subprocess

sys.stdout.reconfigure(encoding='utf-8')
D, step = os.path.abspath(sys.argv[1]), sys.argv[2]
R = json.load(open(os.path.join(D, 'verify_terrain.json'), encoding='utf-8'))
if os.path.exists(os.path.join(D, 'verify_fort.json')):
    R.update({k: v for k, v in json.load(open(os.path.join(D, 'verify_fort.json'), encoding='utf-8')).items() if k in ('rock', 'battery')})
MASKDIR = {'terrain': 'terrain', 'quay': 'terrain', 'walls': 'terrain', 'rock': 'fort', 'battery': 'fort'}
parts = sys.argv[3:] or ['terrain', 'quay']
PARENT = 'summit-rocher-01m'
TMP = os.path.join(os.path.dirname(D), 'exports', 'terrain')
os.makedirs(TMP, exist_ok=True)
CHUNK = 500000
TITLE = {'terrain': '岩堡港｜地形（沙灘、坡、鎮的平台與街；表層殼，平滑渲染）', 'quay': '岩堡港｜石砌碼頭與兩座木棧橋',
         'walls': '岩堡港｜擋土牆（鎮的平台與街切進坡的地方）＋ Rue du Fort 出鎮的石階',
         'rock': '岩堡港｜岩堡的岩（9 m）、鑿岩石階、木梯、岩頂的鴿舍',
         'battery': '岩堡港｜岩堡平台的胸牆、砲眼與門（砲是外部模型）'}
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
        for k, c in cells:
            f.write('%d,%d,%d,%d\n' % (k[0], k[1], k[2], c))


def wid(p):
    return PARENT + '-' + p


def export(p):
    path = os.path.join(TMP, wid(p) + '.list.txt').replace('\\', '/')
    rc, _ = cli(['op=export', 'format=list', 'work=' + wid(p), 'out=' + path])
    return rd(path) if rc == 0 else None


for p in parts:
    mask = os.path.join(D, 'masks', MASKDIR[p], p + '.vox.txt')
    if step == 'create':
        rc, _ = cli(['op=work', 'sub=show', 'work=' + wid(p)], quiet_fail=True)
        if rc:
            cli(['op=work', 'sub=create', 'persona=summit', 'id=' + wid(p), 'title=' + TITLE[p], 'size=' + ','.join(str(v) for v in R[p]['bbox']), 'parent_work=' + PARENT])
        cli(['op=work', 'sub=update', 'persona=summit', 'work=' + wid(p), 'meters_per_voxel=0.1', 'tags=sub'])
        print('create', wid(p))
    elif step == 'stamp':
        cur, want = export(p), rd(mask)
        carve = sorted((k, c) for k, c in cur.items() if k not in want)
        add = sorted((k, c) for k, c in want.items() if cur.get(k) != c)
        for nm, cells, args in (('carve', carve, ['op=carvevox']), ('stamp', add, ['op=stampvox', 'overwrite=1'])):
            for i in range(0, len(cells), CHUNK):
                part = cells[i:i + CHUNK]
                path = os.path.join(TMP, '%s.%s.%d.vox.txt' % (wid(p), nm, i // CHUNK)); dump(path, part)
                rc, out = cli(args + ['persona=summit', 'work=' + wid(p), 'voxels=' + path.replace('\\', '/'), 'at=0,0,0', 'expect_pixels=%d' % len(part), 'draft=0', 'share=0'])
                m = re.search(r'placed\s*=\s*(\d+)', out)
                print(p, nm, i // CHUNK, len(part), 'rc', rc, 'placed', m.group(1) if m else '?', flush=True)
                if rc:
                    raise SystemExit('停：%s 第 %d 刀失敗' % (nm, i // CHUNK))
        print(p, '現況 %d → 清單 %d｜刻 %d、補／換色 %d' % (len(cur), len(want), len(carve), len(add)))
    elif step == 'check':
        cur, want = export(p), rd(mask)
        miss = sum(1 for k in want if k not in cur)
        extra = sum(1 for k in cur if k not in want)
        diff = sum(1 for k, c in want.items() if k in cur and cur[k] != c)
        rc, out = cli(['op=stats', 'work=' + wid(p), 'structure=1'])
        nums = dict(re.findall(r'🔢 (\w+) = (\S+)', out))
        keys = [k for k in nums if re.search(r'compon|cavit|voxel|count', k)]
        print(p, '作品 %d 格｜缺 %d 多 %d 色差 %d｜' % (len(cur), miss, extra, diff) + '  '.join('%s=%s' % (k, nums[k]) for k in keys))
    else:
        raise SystemExit('步驟？ create|stamp|check')
print(step, 'ok', ok, 'bad', bad)
