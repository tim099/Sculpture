# 光榮號 砲門蓋板落格（TASK-0719；kaguya）—— 照 portlids_placement.json（draft_portlids.py 產生）：
#   ① 子作品 kaguya-gloire-01m-portlid（通用部件，0.1 m，parent 船殼、tags sub ⇒ 免費；同 apply_furnish.py 的開法）、stampvox 一刀（讀回 placed）、固定點 hinge-a／hinge-b；
#   ② 34 個外部模型掛在 kaguya-gloire-01m-deck-lower（砲所在那一層；名字配砲：砲門蓋-S04 ↔ 砲-S04），meta {"kind":"portlid","lid_of":"gun-7","close_deg":90,"house":6}。
#   ⛔ 物件 id（portlid-1…）不在這裡發：匯進遊戲時 Blockside `admin.py ids --id gloire` 發（造船規格 §12.2）。
#   用法：python -I -X utf8 tools/apply_portlids.py <design> [sub|models|all] [模型名 regex]
#   · 參考 apply_furnish.py、apply_guns.py；IOException 自動重試；⛔ 失敗那一行整段印出來
import json, os, re, subprocess, sys, time

sys.stdout.reconfigure(encoding='utf-8')
D = os.path.abspath(sys.argv[1])
step = sys.argv[2] if len(sys.argv) > 2 else 'all'
flt = re.compile(sys.argv[3] if len(sys.argv) > 3 else '.')
PL = json.load(open(os.path.join(D, 'portlids_placement.json'), encoding='utf-8'))
LID = PL['lid']
ok = retried = 0


def run(args):
    return subprocess.run(['senate', 'cmd', 'sculpture'] + sum([['--arg', a] for a in args], []), capture_output=True, text=True, encoding='utf-8', errors='replace')


def cli(args):
    global ok, retried
    for k in range(5):
        r = run(args)
        out = r.stdout + r.stderr
        if r.returncode and (r.returncode == 4 or any(t in out for t in ('IOException', '無法移除要被取代的檔案', 'Unable to remove the file to be replaced'))) and k < 4:   # 4 ＝ 拿不到鎖（別人正在用引擎）
            retried += 1
            time.sleep(0.5)
            continue
        break
    if r.returncode:
        print('✗ rc=%d' % r.returncode, ' '.join(args[:6]))
        print(out[-1200:])
        raise SystemExit(1)
    ok += 1
    return r.stdout


def num(v):
    return ('%.3f' % v).rstrip('0').rstrip('.') if isinstance(v, float) else '%d' % v


def xyz(v):
    return ','.join(num(c) for c in v)


if step in ('sub', 'all'):
    W = LID['work']
    vox = os.path.join(D, LID['file']).replace('\\', '/')
    if run(['op=work', 'sub=show', 'work=' + W]).returncode != 0:
        cli(['op=work', 'sub=create', 'persona=kaguya', 'id=' + W, 'title=' + LID['title'], 'size=' + xyz(LID['size']), 'parent_work=' + LID['parent_work'], 'tags=' + LID['tags']])
        cli(['op=work', 'sub=update', 'persona=kaguya', 'work=' + W, 'meters_per_voxel=%g' % LID['meters_per_voxel']])
    have = int(re.search(r'🔢 total_voxels = (\d+)', cli(['op=stats', 'work=' + W])).group(1))
    if have == 0:
        out = cli(['op=stampvox', 'persona=kaguya', 'work=' + W, 'voxels=' + vox, 'at=0,0,0', 'expect_pixels=%d' % LID['cells'], 'draft=0', 'share=0'])
        n = int(re.search(r'🔢 placed = (\d+)', out).group(1))
        if n != LID['cells']:
            raise SystemExit('✗ %s placed %d ≠ %d' % (W, n, LID['cells']))
    elif have != LID['cells']:
        raise SystemExit('✗ %s 已有 %d 格 ≠ %d' % (W, have, LID['cells']))
    for nm, at in sorted(LID['anchors'].items()):
        cli(['op=work', 'sub=anchor', 'persona=kaguya', 'work=' + W, 'name=' + nm, 'at=' + xyz(at), 'overwrite=1',
             'note=砲門蓋板的鉸鏈軸（上緣、貼船殼那一邊；造船規格 §9.12：從 hinge-a 看向 hinge-b 照右手定則正轉 ＝ 往上掀、反轉 close_deg ＝ 關上）'])
    print('✓ 子作品', W, LID['cells'], '格', LID['size'], '固定點', sorted(LID['anchors']))
if step in ('models', 'all'):
    n = 0
    for r in PL['rows']:
        if not flt.search(r['model']):
            continue
        cli(['op=work', 'sub=model', 'persona=kaguya', 'work=' + r['host_work'], 'name=' + r['model'], 'source_work=' + r['source_work'],
             'at=' + xyz(r['at']), 'pivot=' + xyz(r['pivot']), 'rotate=' + xyz(r['rotate']), 'scale=%g' % r['scale'], 'mirror=' + r['mirror'], 'overwrite=1',
             'meta=' + json.dumps(r['meta'], ensure_ascii=False, sort_keys=True),
             'note=光榮號 砲門蓋板 %s ↔ %s（TASK-0719 draft_portlids.py：畫開著、上緣鉸鏈；%s；kind=portlid 本身是裝飾）' % (
                 r['model'], r['gun_model'], 'S 舷 rotate rz' if r['side'] == 'S' else 'P 舷 rotate 180 − rz（⛔ mirror=y）')])
        n += 1
        if n % 10 == 0:
            print('  模型 %d' % n, flush=True)
    print('✓ 模型', n)
if step not in ('sub', 'models', 'all'):
    raise SystemExit('步驟？ sub|models|all')
print(step, 'ok', ok, 'IOException 重試', retried)
