# TASK-0588 三叉戟砲重配 —— 落格／撤除工具
#   remove：撤掉船頭三層斜放的三叉戟砲 6 門（階段十三）與中砲甲板兩門 18 磅船尾追擊砲（連同它們的砲索 10 條、環 6 個）；
#           船頭斜砲門封回（照階段十三的刻除清單把船殼原樣貼回，清單帶刻之前的顏色）；三叉戟砲的墊木拿掉（顏色守門）
#   之後的新擺法由 draft_relayout.py 從撤完的現況算，落格走本檔的 build／models 步驟。
#   用法：python -I -X utf8 tools/apply_relayout.py <design> remove|build|models
import json, os, re, subprocess, sys, time

sys.stdout.reconfigure(encoding='utf-8')
D, step = os.path.abspath(sys.argv[1]), sys.argv[2]
NOTE = 'TASK-0588 三叉戟砲重配'
MARK = '三叉戟重配'
retried = 0


def run(*a):
    return subprocess.run(['senate', 'cmd', 'sculpture'] + [x for kv in a for x in ('--arg', kv)], capture_output=True, text=True, encoding='utf-8', errors='replace')


def cli(*a, ok_missing=False):
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
        raise SystemExit('✗ ' + ' '.join(a[:6]))
    return r.stdout


def nlines(p):
    return sum(1 for l in open(p, encoding='utf-8') if l.strip() and not l.startswith('#'))


def num(out, key):
    m = re.search(r'🔢 (?:%s) = ([\d,]+)' % key, out)
    if not m:
        print(out[-1200:])
        return -1
    return int(m.group(1).replace(',', ''))


fp = lambda f: os.path.join(D, f).replace(os.sep, '/')
xyz = lambda v: ','.join('%g' % c for c in v)
ASM = 'gura-tridente-01m-assembly'

VB = json.load(open(os.path.join(D, 'verify_bowchase.json'), encoding='utf-8'))
VF = json.load(open(os.path.join(D, 'verify_gunfittings.json'), encoding='utf-8'))
if step == 'remove':
    old_guns = [(r['host_work'], r['model']) for r in VB['trident']] + \
               [('gura-tridente-01m-deck-middle', '追擊砲-船尾-P'), ('gura-tridente-01m-deck-middle', '追擊砲-船尾-S')]
    # ① 繩（組裝件）：兩門船尾追擊砲的 breeching／tackle／train
    ropes = [r['name'] for r in VF['ropes'] if '.追擊砲-船尾-' in r['name']]
    assert len(ropes) == 10, ropes
    for n in ropes:
        cli('op=work', 'sub=unrope', 'persona=gura', 'work=' + ASM, 'name=' + n, 'note=' + NOTE)
    print('✓ 繩', len(ropes))
    # ② 模型
    for w, m in old_guns:
        cli('op=work', 'sub=unmodel', 'persona=gura', 'work=' + w, 'name=' + m, 'note=' + NOTE)
        print('✓ 拿掉模型', w, m)
    # ③ 環：固定點拿掉、環那一格刻掉（顏色守門 73）
    rings = [a for a in VF['anchors'] if '追擊砲-船尾-' in a['gun']]
    assert len(rings) == 6
    gw = rings[0]['work']
    lst = os.path.join(D, 'masks', 'relayout', 'rings_carve.vox.txt')
    os.makedirs(os.path.dirname(lst), exist_ok=True)
    with open(lst, 'w', encoding='utf-8', newline='\n') as f:
        f.write('# TASK-0588 船尾追擊砲的環（%s 子作品座標，x,y,z,color 顏色守門）\n' % gw)
        for a in rings:
            f.write('%d,%d,%d,73\n' % tuple(a['at']))
    cli('op=work', 'sub=mark', 'persona=gura', 'work=' + gw, 'name=' + MARK, 'phase=begin')
    for a in rings:
        cli('op=work', 'sub=unanchor', 'persona=gura', 'work=' + gw, 'name=' + a['name'], 'note=' + NOTE)
    out = cli('op=carvevox', 'persona=gura', 'work=' + gw, 'voxels=' + lst.replace(os.sep, '/'), 'at=0,0,0', 'expect_pixels=6')
    n = num(out, 'carved|removed|placed')
    cli('op=work', 'sub=mark', 'persona=gura', 'work=' + gw, 'name=' + MARK, 'phase=end', 'note=' + NOTE + '：船尾追擊砲的環')
    print('✓ 環', n, '／ 6')
    # 🩸 第一次跑這裡 regex 沒抓到 carvevox 的欄位（-1）、斷言停下；格子已刻（匯出回讀 6 格都不在、固定點 0）⇒ 後面兩步拆成 remove2
if step in ('remove', 'remove2'):
    # ④ 船頭斜砲門封回：階段十三的刻除清單（帶刻之前的顏色）原樣貼回船殼
    sec = VB['carve']
    cli('op=work', 'sub=mark', 'persona=gura', 'work=gura-tridente-01m', 'name=' + MARK, 'phase=begin')
    out = cli('op=stampvox', 'persona=gura', 'work=gura-tridente-01m', 'voxels=' + fp(sec['file']), 'at=0,0,0', 'expect_pixels=%d' % nlines(fp(sec['file'])), 'share=0', 'draft=0')
    n = num(out, 'placed')
    cli('op=work', 'sub=mark', 'persona=gura', 'work=gura-tridente-01m', 'name=' + MARK, 'phase=end', 'note=' + NOTE + '：船頭斜砲門封回')
    print('✓ 船殼貼回', n, '／', sec['cells'])
    assert n == sec['cells']
    # ⑤ 三叉戟砲的墊木（顏色守門：清單帶顏色）
    for work, P in sorted(VB['pads'].items()):
        cli('op=work', 'sub=mark', 'persona=gura', 'work=' + work, 'name=' + MARK, 'phase=begin')
        out = cli('op=carvevox', 'persona=gura', 'work=' + work, 'voxels=' + fp(P['file']), 'at=0,0,0', 'expect_pixels=%d' % P['voxels'])
        n = num(out, 'carved|removed|placed')
        cli('op=work', 'sub=mark', 'persona=gura', 'work=' + work, 'name=' + MARK, 'phase=end', 'note=' + NOTE + '：三叉戟砲墊木拿掉')
        print('✓ 墊木拿掉', work, n, '／', P['voxels'])
        assert n == P['voxels']
HULL = 'gura-tridente-01m'


def exists(work):
    return os.path.exists(os.path.join(os.path.dirname(os.path.dirname(D)), work, 'work.json'))   # D ＝ works/<作品>/design


if step == 'build':
    V = json.load(open(os.path.join(D, 'verify_relayout.json'), encoding='utf-8'))
    assert not V['problems'], V['problems']
    P = json.load(open(os.path.join(D, 'plan.json'), encoding='utf-8'))['relayout']
    # ① 船尾砲門（船殼）、陽台欄杆開口（顏色守門）
    for work, sec, nm in ((HULL, V['stern_carve'], '三叉戟船尾砲門'), (P['stern']['walk']['work'], V['walk_carve'], '三叉戟船尾砲門')):
        cli('op=work', 'sub=mark', 'persona=gura', 'work=' + work, 'name=' + nm, 'phase=begin')
        out = cli('op=carvevox', 'persona=gura', 'work=' + work, 'voxels=' + fp(sec['file']), 'at=0,0,0', 'expect_pixels=%d' % sec['cells'])
        n = num(out, 'carved|removed|placed')
        cli('op=work', 'sub=mark', 'persona=gura', 'work=' + work, 'name=' + nm, 'phase=end', 'note=' + NOTE)
        print('✓ 刻', work, n, '／', sec['cells'])
        assert n == sec['cells']
    # ② 船頭砲台、梯子：子作品（parent 船殼、sub、0.1 m、整船框 at 0,0,0）
    B = P['battery']
    for work, title, sec in ((B['work'], '三叉戟號 船頭砲台', V['battery']), (B['ladders']['work'], '三叉戟號 梯子（上到船頭砲台）', V['ladders'])):
        if not exists(work):
            cli('op=work', 'sub=create', 'persona=gura', 'id=' + work, 'title=' + title, 'parent_work=' + HULL, 'size=1100,400,800', 'tags=sub')
            cli('op=work', 'sub=update', 'persona=gura', 'work=' + work, 'meters_per_voxel=0.1')
            print('✓ 建立', work)
        out = cli('op=stampvox', 'persona=gura', 'work=' + work, 'voxels=' + fp(sec['file']), 'at=0,0,0', 'expect_pixels=%d' % sec['cells'], 'share=0', 'draft=0')
        n = num(out, 'placed')
        print('✓ 貼', work, n, '／', sec['cells'])
        assert n == sec['cells']
    for nm, v in sorted(V['ladder_points'].items()):
        for pk in ('foot', 'lo', 'hi', 'head'):
            cli('op=work', 'sub=anchor', 'persona=gura', 'work=' + B['ladders']['work'], 'name=%s.%s' % (nm, pk), 'at=%d,%d,%d' % tuple(v[pk]),
                'note=梯子點（draft_relayout.py：腳踩的那一格）')
    print('✓ 梯子固定點', 4 * len(V['ladder_points']))
    cli('op=work', 'sub=link', 'persona=gura', 'work=' + B['work'], 'name=梯子', 'source_work=' + B['ladders']['work'], 'at=0,0,0',
        'meta={"kind":"ladders"}', 'note=' + NOTE + '：從上甲板爬上砲台的梯子')
    cli('op=work', 'sub=link', 'persona=gura', 'work=' + ASM, 'name=' + B['link'], 'source_work=' + B['work'], 'at=0,0,0',
        'meta=' + json.dumps(V['battery_meta'], ensure_ascii=False, sort_keys=True), 'note=' + NOTE + '：船頭抬高砲台（遊戲 §9.3 甲板 meta）')
    print('✓ 關聯', B['link'], V['battery_meta'])
elif step == 'models':
    V = json.load(open(os.path.join(D, 'verify_relayout.json'), encoding='utf-8'))
    for r in V['rows']:
        cli('op=work', 'sub=model', 'persona=gura', 'work=' + r['host_work'], 'name=' + r['model'], 'source_work=' + r['work'], 'at=' + xyz(r['at']),
            'pivot=' + xyz(r['pivot']), 'rotate=' + xyz(r['rotate']), 'scale=%g' % r['scale'], 'mirror=' + r['mirror'], 'overwrite=1',
            'meta=' + json.dumps(r['meta'], ensure_ascii=False, sort_keys=True), 'note=' + NOTE + '（draft_relayout.py）')
        # sub=model overwrite=1 的 meta 是合併（階段十三撞過）⇒ 先清空再寫完整的
        cli('op=work', 'sub=meta', 'persona=gura', 'work=' + r['host_work'], 'part=model', 'name=' + r['model'], 'meta=none')
        cli('op=work', 'sub=meta', 'persona=gura', 'work=' + r['host_work'], 'part=model', 'name=' + r['model'], 'meta=' + json.dumps(r['meta'], ensure_ascii=False, sort_keys=True))
        print('✓ 模型', r['host_link'], r['model'], r['at'])
elif step == 'verify':
    # verify_guns.json 補成現況：拿掉階段十三的三叉戟砲 6 門與兩門船尾追擊砲，加上新的 6 門
    V = json.load(open(os.path.join(D, 'verify_relayout.json'), encoding='utf-8'))
    p = os.path.join(D, 'verify_guns.json')
    VG = json.load(open(p, encoding='utf-8'))
    VG['rows'] = [r for r in VG['rows'] if r['type'] != 'trident' and not r['model'].startswith('追擊砲-船尾-')] + V['rows']
    VG['patched_by'] = VG.get('patched_by', '') + '；draft_relayout.py（TASK-0588）：三叉戟砲改成船頭砲台 2 門、船尾 4 門，船尾追擊砲拿掉'
    by = {}
    for r in VG['rows']:
        by[r['meta']['gun']] = by.get(r['meta']['gun'], 0) + 1
    VG['count'], VG['by_code'] = len(VG['rows']), dict(sorted(by.items()))
    with open(p, 'w', encoding='utf-8', newline='\n') as f:
        json.dump(VG, f, ensure_ascii=False, indent=1, sort_keys=True)
        f.write('\n')
    print('✓ verify_guns.json', VG['count'], VG['by_code'])
elif step not in ('remove', 'remove2'):
    raise SystemExit('步驟？ remove|remove2|build|models|verify')
print(step, 'IOException 重試', retried)
