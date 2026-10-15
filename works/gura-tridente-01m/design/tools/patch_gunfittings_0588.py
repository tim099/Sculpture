# TASK-0588：verify_gunfittings.json 與 masks/gunfittings/middle.vox.txt 補成現況 —— 兩門船尾追擊砲拿掉了（apply_relayout.py remove：環 6、繩 10）
#   之後 check_gunfittings.py 量的就是現況的帳（缺 0 才算過）。三叉戟砲照階段十三不掛砲索（新的 6 門都沒有舷側砲門）。
#   用法：python -I -X utf8 tools/patch_gunfittings_0588.py <design>
import json, os, hashlib, sys

sys.stdout.reconfigure(encoding='utf-8')
D = os.path.abspath(sys.argv[1])
p = os.path.join(D, 'verify_gunfittings.json')
F = json.load(open(p, encoding='utf-8'))
gone = lambda s: '追擊砲-船尾-' in s
na, nr, ng = len(F['anchors']), len(F['ropes']), len(F['rows'])
F['anchors'] = [a for a in F['anchors'] if not gone(a['gun'])]
F['ropes'] = [r for r in F['ropes'] if not gone(r['name'])]
F['rows'] = [r for r in F['rows'] if not gone(r['gun'])]
rm = {(2, 41, 11), (2, 49, 11), (23, 45, 6), (2, 105, 11), (2, 113, 11), (23, 109, 6)}
for w in F['works']:
    if w['deck'] != '甲板-middle':
        continue
    fp = os.path.join(D, w['file'])
    lines = open(fp, encoding='utf-8').read().splitlines(True)
    keep = [l for l in lines if l.startswith('#') or not l.strip() or tuple(int(v) for v in l.split(',')[:3]) not in rm]
    assert len(lines) - len(keep) == 6, len(lines) - len(keep)
    keep[0] = keep[0].rstrip('\n') + '（TASK-0588：船尾追擊砲的 6 個環拿掉）\n'
    t = ''.join(keep)
    open(fp, 'w', encoding='utf-8', newline='\n').write(t)
    w['voxels'] -= 6
    w['sha256'] = hashlib.sha256(t.encode('utf-8')).hexdigest()
    w['title'] = '三叉戟號 砲具（中砲甲板）'
F['counts'].update({'ring_cells': F['counts']['ring_cells'] - 6, 'anchors': len(F['anchors']), 'ropes': len(F['ropes']), 'guns': F['counts']['guns'] - 2})
F['note'] = F.get('note', '') + '；TASK-0588：兩門船尾追擊砲拿掉（環 6、繩 10），三叉戟砲照階段十三不掛砲索'
with open(p, 'w', encoding='utf-8', newline='\n') as f:
    json.dump(F, f, ensure_ascii=False, indent=1)
    f.write('\n')
print('anchors %d → %d、ropes %d → %d、rows %d → %d' % (na, len(F['anchors']), nr, len(F['ropes']), ng, len(F['rows'])), F['counts'])
