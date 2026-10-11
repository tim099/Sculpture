# 把 design/rig_points_*.json 的固定點登記進子作品（work sub=anchor，免費、不動 voxel）
# 用法：python -I register_anchors.py <design 資料夾> <rig_points 檔名> [--dry]
#   · 子作品照 owner；座標換成子作品自己的（plan.json 裡有 box.at 的扣掉 at，其餘 at 0,0,0）
#   · 經鏡像關聯來的那一舷（有 via）不登記 —— 它是同一個固定點翻過去
import sys, os, json, subprocess
sys.stdout.reconfigure(encoding='utf-8')

design, fn = sys.argv[1], sys.argv[2]
dry = '--dry' in sys.argv
plan = json.load(open(os.path.join(design, 'plan.json'), encoding='utf-8'))
AT = {}
for sec in plan.values():
    if isinstance(sec, dict):
        for sw in ([sec.get('subwork')] + list((sec.get('subworks') or {}).values())):
            if isinstance(sw, dict) and sw.get('id') and isinstance(sw.get('box'), dict):
                AT[sw['id']] = sw['box']['at']
pts = json.load(open(os.path.join(design, fn), encoding='utf-8'))['points']
ok = bad = 0
for p in pts:
    if p.get('via'):
        continue
    at = AT.get(p['owner'], [0, 0, 0])
    loc = [p['world'][i] - at[i] for i in range(3)]
    args = ['senate', 'cmd', 'sculpture', '--arg', 'op=work', '--arg', 'sub=anchor', '--arg', 'persona=basecamp', '--arg', 'work=' + p['owner'],
            '--arg', 'name=' + p['name'], '--arg', 'at=%d,%d,%d' % tuple(loc), '--arg', 'overwrite=1',
            '--arg', 'note=%s（%s；世界 %d,%d,%d）' % (p['kind'], fn, *p['world'])]
    if dry:
        print(' '.join(args[4:]))
        continue
    r = subprocess.run(args, capture_output=True, text=True, encoding='utf-8', errors='replace')
    if r.returncode:
        bad += 1
        print('✗', p['name'], (r.stdout + r.stderr)[-300:])
    else:
        ok += 1
print('anchors ok', ok, 'bad', bad)
