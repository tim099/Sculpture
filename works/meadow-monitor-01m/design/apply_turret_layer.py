# 莫尼特號的砲塔改成砲塔層（TASK-0660；Blockside 27_turret.js，造船規格 §4.8）：
#   組裝件的「砲塔裝甲」「砲塔頂」兩條關聯＋主甲板的外部模型「砲塔」（一個模型帶兩門砲）⇒ 一條關聯「砲塔」（meta kind=turret）→ 新作品 -turret-assy：
#     關聯 裝甲（圓筒）、頂（格柵）＋外部模型 砲-a、砲-b（各一門 XI 吋 Dahlgren，固定在砲塔上）＋固定點 pivot（轉軸）、front（前方：砲口那一邊）。
#   格子一格不動（圓筒、頂原樣搬進子作品）；砲的擺法照原本那個模型（at 301.5,65.5,35、pivot 66.5,66.5,0、轉 90°、0.5 倍；砲-b 照 x 鏡像）。
# 用法：python -I -X utf8 apply_turret_layer.py
import sys, os, json, subprocess, shutil
S = shutil.which('senate'); PER = 'meadow'
WORKS = os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', '..')
A = 'meadow-monitor-01m-assembly'; NEW = 'meadow-monitor-01m-turret-assy'; DECK = 'meadow-monitor-01m-deck-main'
AT = (269, 33, 35)                                                       # 圓筒的關聯原本放在組裝件的哪裡 ⇒ 新作品的框放在這裡


def run(*a, ok_codes=(0,)):
    args = [S, 'cmd', 'sculpture']
    for k, v in a: args += ['--arg', '%s=%s' % (k, v)]
    p = subprocess.run(args, capture_output=True, text=True, encoding='utf-8', errors='replace')
    if p.returncode not in ok_codes: print((p.stdout + p.stderr)[-1500:]); sys.exit(1)
    return p.stdout


def names(wid, fn, key):
    f = os.path.join(WORKS, wid, fn)
    return [x['name'] for x in json.load(open(f, encoding='utf-8'))[key]] if os.path.exists(f) else []


if not os.path.exists(os.path.join(WORKS, NEW, 'work.json')):
    run(('op', 'work'), ('sub', 'create'), ('persona', PER), ('id', NEW), ('title', '莫尼特號 砲塔（砲塔層：圓筒＋頂＋兩門 XI 吋砲；跟著轉的一整座）'), ('parent_work', A), ('size', '65,65,30'), ('tags', 'sub'))
    print('＋ 建立', NEW)
run(('op', 'work'), ('sub', 'update'), ('persona', PER), ('work', NEW), ('meters_per_voxel', '0.1'), ('size', '65,65,30'), ('tags', 'sub'))

have = names(NEW, 'links.json', 'links')
for nm, src, at, meta in (('裝甲', 'meadow-monitor-01m-turret-armor', '0,0,0', {'material': 'iron', 'render': 'smooth'}),
                          ('頂', 'meadow-monitor-01m-turret-roof', '0,0,28', {'material': 'iron'})):
    a = [('op', 'work'), ('sub', 'link'), ('persona', PER), ('work', NEW), ('name', nm), ('source_work', src), ('at', at), ('meta', json.dumps(meta, ensure_ascii=False))]
    if nm in have: a.append(('overwrite', '1'))
    run(*a); print('  關聯', nm, '✓')

for nm, at, note in (('pivot', '32,32,0', '轉軸（格心 32.5,32.5）＝ 原本砲塔模型的 pivot 301.5,65.5'), ('front', '0,32,0', '前方：砲口那一邊（開局朝 −x，船尾）')):
    run(('op', 'work'), ('sub', 'anchor'), ('persona', PER), ('work', NEW), ('name', nm), ('at', at), ('note', note), ok_codes=(0, 1))
    print('  固定點', nm, '✓')

have = names(NEW, 'models.json', 'models')
for nm, mir in (('砲-a', ''), ('砲-b', 'x')):
    a = [('op', 'work'), ('sub', 'model'), ('persona', PER), ('work', NEW), ('name', nm), ('source_work', 'meadow-monitor-01m-turret-gun'),
         ('at', '%s,%s,0' % (301.5 - AT[0], 65.5 - AT[1])), ('pivot', '66.5,66.5,0'), ('rotate', '0,0,90'), ('scale', '0.5,0.5,0.5'),
         ('meta', json.dumps({'kind': 'gun', 'gun': '11d'}, ensure_ascii=False))]
    if mir: a.append(('mirror', mir))
    if nm in have: a.append(('overwrite', '1'))
    run(*a); print('  模型', nm, '✓')

al = names(A, 'links.json', 'links')
for nm in ('砲塔裝甲', '砲塔頂'):
    if nm in al: run(('op', 'work'), ('sub', 'unlink'), ('persona', PER), ('work', A), ('name', nm)); print('  拿掉關聯', nm)
a = [('op', 'work'), ('sub', 'link'), ('persona', PER), ('work', A), ('name', '砲塔'), ('source_work', NEW), ('at', '%d,%d,%d' % AT),
     ('meta', json.dumps({'kind': 'turret', 'arc': '-180,180', 'fire': '-174,174', 'rate': 16}, ensure_ascii=False))]
if '砲塔' in al: a.append(('overwrite', '1'))
run(*a); print('  關聯 砲塔（kind=turret）✓')
if '砲塔' in names(DECK, 'models.json', 'models'):
    run(('op', 'work'), ('sub', 'unmodel'), ('persona', PER), ('work', DECK), ('name', '砲塔')); print('  拿掉主甲板的模型 砲塔')
print('done')
