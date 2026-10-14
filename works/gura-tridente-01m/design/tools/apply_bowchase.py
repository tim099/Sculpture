# TASK-0578 落格：照 verify_bowchase.json
#   hull：船殼打標記 船頭砲門:begin → carvevox 刻除清單（帶色，顏色守門）→ :end；船頭裝飾／knee 有刻的話同樣（各自標記）
#   pads：甲板子作品打標記 船頭砲墊木:begin → stampvox → :end
#   models：上砲甲板 砲-S18／P18 換回 12 磅（overwrite）、6 門三叉戟砲（掛在所在甲板子作品）
#   verify：把 verify_guns.json 補成現況（換掉那兩門＋三叉戟砲 6 門、types 加 trident）—— 之後的砲具、rammer／sponge、砲彈架、各讀數都讀這一份
#   用法：python -I -X utf8 tools/apply_bowchase.py <design> hull|pads|models|verify
import json, os, re, subprocess, sys, time

sys.stdout.reconfigure(encoding='utf-8')
D, step = os.path.abspath(sys.argv[1]), sys.argv[2]
V = json.load(open(os.path.join(D, 'verify_bowchase.json'), encoding='utf-8'))
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


def nlines(p):
    return sum(1 for l in open(p, encoding='utf-8') if l.strip() and not l.startswith('#'))


xyz = lambda v: ','.join('%g' % c for c in v)
fp = lambda f: os.path.join(D, f).replace(os.sep, '/')
if step == 'hull':
    for work, sec in (('gura-tridente-01m', V['carve']), (V['carve_head_side']['work'], V['carve_head_side']), (V['carve_knee']['work'], V['carve_knee'])):
        if not sec['cells']:
            print('·', work, '沒有要刻的')
            continue
        cli('op=work', 'sub=mark', 'persona=gura', 'work=' + work, 'name=船頭砲門', 'phase=begin')
        out = cli('op=carvevox', 'persona=gura', 'work=' + work, 'voxels=' + fp(sec['file']), 'at=0,0,0', 'expect_pixels=%d' % nlines(os.path.join(D, sec['file'])))
        m = re.search(r'🔢 (carved|placed) = (\d+)', out)
        n = int(m.group(2)) if m else -1
        cli('op=work', 'sub=mark', 'persona=gura', 'work=' + work, 'name=船頭砲門', 'phase=end', 'note=TASK-0578 船頭追擊砲門')
        print('✓ 刻', work, n, '／', sec['cells'])
        if n != sec['cells']:
            raise SystemExit('✗ 刻的格數不對')
elif step == 'pads':
    for work, P in sorted(V['pads'].items()):
        cli('op=work', 'sub=mark', 'persona=gura', 'work=' + work, 'name=船頭砲墊木', 'phase=begin')
        out = cli('op=stampvox', 'persona=gura', 'work=' + work, 'voxels=' + fp(P['file']), 'at=0,0,0', 'expect_pixels=%d' % P['voxels'], 'share=0', 'draft=0')
        n = int(re.search(r'🔢 placed = (\d+)', out).group(1))
        cli('op=work', 'sub=mark', 'persona=gura', 'work=' + work, 'name=船頭砲墊木', 'phase=end', 'note=TASK-0578')
        print('✓ 墊木', work, n, '／', P['voxels'])
        if n != P['voxels']:
            raise SystemExit('✗ 墊木格數不對')
elif step == 'models':
    for r in V['redo_broadside'] + V['trident']:
        cli('op=work', 'sub=model', 'persona=gura', 'work=' + r['host_work'], 'name=' + r['model'], 'source_work=' + r['work'], 'at=' + xyz(r['at']),
            'pivot=' + xyz(r['pivot']), 'rotate=' + xyz(r['rotate']), 'scale=%g' % r['scale'], 'mirror=' + r['mirror'], 'overwrite=1',
            'meta=' + json.dumps(r['meta'], ensure_ascii=False, sort_keys=True), 'note=TASK-0578（draft_bowchase.py）')
        # 🩸 sub=model overwrite=1 的 meta 是「合併」⇒ 砲-S18／P18 換回 12 磅時舊追擊砲的 arc=bow 留了下來（遊戲會當成船頭追擊砲）⇒ 先清空再寫完整的
        cli('op=work', 'sub=meta', 'persona=gura', 'work=' + r['host_work'], 'part=model', 'name=' + r['model'], 'meta=none')
        cli('op=work', 'sub=meta', 'persona=gura', 'work=' + r['host_work'], 'part=model', 'name=' + r['model'], 'meta=' + json.dumps(r['meta'], ensure_ascii=False, sort_keys=True))
        print('✓ 模型', r['host_link'], r['model'], r['type'], r['at'])
elif step == 'verify':
    p = os.path.join(D, 'verify_guns.json')
    VG = json.load(open(p, encoding='utf-8'))
    redo = {(r['host_link'], r['model']): r for r in V['redo_broadside']}
    VG['rows'] = [redo.get((r['host_link'], r['model']), r) for r in VG['rows'] if r['type'] != 'trident'] + V['trident']
    t0 = V['trident'][0]
    VG['types']['trident'] = {'work': t0['work'], 'code': t0['meta']['gun'], 'scale': t0['scale'], 'pivot': t0['pivot'], 'note': 'TASK-0578 三叉戟砲（draft_trident.py）'}
    VG['patched_by'] = 'draft_bowchase.py（TASK-0578）：上砲甲板 砲-S18／P18 換回 12 磅、加三叉戟砲 6 門 —— 這一份不再是 draft_guns.py 的直接輸出'
    by = {}
    for r in VG['rows']:
        by[r['meta']['gun']] = by.get(r['meta']['gun'], 0) + 1
    VG['count'], VG['by_code'] = len(VG['rows']), dict(sorted(by.items()))
    with open(p, 'w', encoding='utf-8', newline='\n') as f:
        json.dump(VG, f, ensure_ascii=False, indent=1, sort_keys=True)
        f.write('\n')
    print('✓ verify_guns.json', VG['count'], VG['by_code'])
else:
    raise SystemExit('步驟？ hull|pads|models|verify')
print(step, 'IOException 重試', retried)
