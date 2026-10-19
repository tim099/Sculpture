# 砲門蓋板落格（TASK-0736）—— 照 portlids_placement.json（draft_portlids.py 產生）；照光榮號 tools/apply_portlids.py（kaguya，TASK-0719）改；夜隼號、風暴角號共用（兩份檔逐位元組相同）。
#   ① 每件蓋板子作品（通用部件，0.1 m，parent 船殼、tags sub ⇒ 免費）：建立、stampvox 一刀（讀回 placed）、固定點 hinge-a／hinge-b；
#   ② 每片一個外部模型，掛在那門砲所在那一層甲板的子作品（名字配砲：砲門蓋-S3 ↔ 砲-S3），meta {"kind":"portlid","lid_of":<砲的物件 id>,"close_deg":…,"house":…}。
#   ⛔ 蓋板自己的物件 id（portlid-1…）不在這裡發：匯進遊戲時 Blockside `admin.py ids` 發（造船規格 §12.2）。
#   用法：python -I -X utf8 -B apply_portlids.py <design> [sub|models|all] [模型名 regex]
import json, os, re, subprocess, sys, time

sys.stdout.reconfigure(encoding='utf-8')
D = os.path.abspath(sys.argv[1])
step = sys.argv[2] if len(sys.argv) > 2 else 'all'
flt = re.compile(sys.argv[3] if len(sys.argv) > 3 else '.')
PL = json.load(open(os.path.join(D, 'portlids_placement.json'), encoding='utf-8'))
PERSONA = 'summit'
SHIP = {'summit-night-falcon-01m': '夜隼號', 'summit-stormkaap-01m': '風暴角號'}
ok = retried = 0


def run(args):
    return subprocess.run(['senate', 'cmd', 'sculpture'] + sum([['--arg', a] for a in args], []), capture_output=True, text=True, encoding='utf-8', errors='replace')


def cli(args):
    global ok, retried
    for k in range(5):
        r = run(args)
        out = r.stdout + r.stderr
        if r.returncode and (r.returncode == 4 or any(t in out for t in ('IOException', '無法移除要被取代的檔案', 'Unable to remove the file to be replaced'))) and k < 4:   # 4 ＝ 拿不到鎖
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


if step not in ('sub', 'models', 'all'):
    raise SystemExit('步驟？ sub|models|all')
if step in ('sub', 'all'):
    for W, L in sorted(PL['lids'].items()):
        vox = os.path.join(D, L['file']).replace('\\', '/')
        if run(['op=work', 'sub=show', 'work=' + W]).returncode != 0:
            cli(['op=work', 'sub=create', 'persona=' + PERSONA, 'id=' + W, 'title=' + L['title'], 'size=' + xyz(L['size']), 'parent_work=' + L['parent_work'], 'tags=' + L['tags']])
            cli(['op=work', 'sub=update', 'persona=' + PERSONA, 'work=' + W, 'meters_per_voxel=%g' % L['meters_per_voxel']])
        have = int(re.search(r'🔢 total_voxels = (\d+)', cli(['op=stats', 'work=' + W])).group(1))
        if have == 0:
            out = cli(['op=stampvox', 'persona=' + PERSONA, 'work=' + W, 'voxels=' + vox, 'at=0,0,0', 'expect_pixels=%d' % L['cells'], 'draft=0', 'share=0'])
            n = int(re.search(r'🔢 placed = (\d+)', out).group(1))
            if n != L['cells']:
                raise SystemExit('✗ %s placed %d ≠ %d' % (W, n, L['cells']))
        elif have != L['cells']:
            raise SystemExit('✗ %s 已有 %d 格 ≠ %d' % (W, have, L['cells']))
        for nm, at in sorted(L['anchors'].items()):
            cli(['op=work', 'sub=anchor', 'persona=' + PERSONA, 'work=' + W, 'name=' + nm, 'at=' + xyz(at), 'overwrite=1',
                 'note=砲門蓋板的鉸鏈軸（上緣、貼船殼那一邊；造船規格 §9.12：從 hinge-a 看向 hinge-b 照右手定則正轉 ＝ 往上掀、反轉 close_deg ＝ 關上）'])
        print('✓ 子作品', W, L['cells'], '格', L['size'], '固定點', sorted(L['anchors']))
if step in ('models', 'all'):
    n = 0
    WORKS = os.path.dirname(os.path.dirname(D))
    have_id = {}                                                        # 已經發過的物件 id（Blockside admin.py ids 寫回作品的）⇒ 重落時帶著，⛔ 整份 meta 覆寫會把它洗掉、下次重發就換號
    for h in sorted({r['host_work'] for r in PL['rows']}):
        for m in json.load(open(os.path.join(WORKS, h, 'models.json'), encoding='utf-8'))['models']:
            if (m.get('meta') or {}).get('id'):
                have_id[(h, m['name'])] = m['meta']['id']
    for r in PL['rows']:
        if not flt.search(r['model']):
            continue
        meta = dict(r['meta'])
        if (r['host_work'], r['model']) in have_id:
            meta['id'] = have_id[(r['host_work'], r['model'])]
        how = {'S': 'S 舷 rotate rz', 'P': 'P 舷 rotate 180 − rz（⛔ mirror=y）', 'A': '船尾 rotate 90 ＋ rz'}[r['side']]
        cli(['op=work', 'sub=model', 'persona=' + PERSONA, 'work=' + r['host_work'], 'name=' + r['model'], 'source_work=' + r['source_work'],
             'at=' + xyz(r['at']), 'pivot=' + xyz(r['pivot']), 'rotate=' + xyz(r['rotate']), 'scale=%g' % r['scale'], 'mirror=' + r['mirror'], 'overwrite=1',
             'meta=' + json.dumps(meta, ensure_ascii=False, sort_keys=True),
             'note=%s 砲門蓋板 %s ↔ %s（TASK-0736 draft_portlids.py：畫開著、上緣鉸鏈；%s；kind=portlid 本身是裝飾）' % (
                 SHIP[PL['lids'][r['source_work']]['parent_work']], r['model'], r['gun_model'], how)])
        n += 1
        if n % 10 == 0:
            print('  模型 %d' % n, flush=True)
    print('✓ 模型', n)
print(step, 'ok', ok, 'IOException 重試', retried)
