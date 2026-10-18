# 投石機的繩落地（Tim 2026-10-18：「接著做投石機吧(同時把一些零件換成繩索)」）—— 以前畫成格子的拉繩、握環、投袋繩換成繩：
#   拉繩 ×3：投臂短臂前端的鐵箍（model:mangonel-arm/pull-N）→ 拉繩手手上（model:mangonel/grip-N）；meta kind=gunrope anim=gun rest=grip-N fire=grip-N-fire
#     ⇒ 遊戲（Blockside 26_gunanim.js）：上端跟著投臂甩、下端照開火進度從 grip-N（拉好）拉到 grip-N-fire（拉到底）再回來。
#   投袋繩 ×2：長臂尾端（model:mangonel-arm/sling）→ 投袋兩側（pouch-a／pouch-b）；meta kind=gunrope anim=gun（不寫 rest／fire）⇒ 兩端都在投臂上、只跟著投臂甩。
#   繩都建在投石機所在的子作品（assembly）裡；固定點在 erina-dromon-01m-mangonel／-mangonel-arm（draft_weapons.py）。
# 用法：python -I -X utf8 -B apply_mangonel_ropes.py
import os, sys, json
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import cli

WORK = 'erina-dromon-01m-assembly'
ROPES = []
for i in (1, 2, 3):
    ROPES.append(('mangonel-拉繩-%d' % i, 'model:mangonel-arm/pull-%d' % i, 'model:mangonel/grip-%d' % i, 0.12, '#c9b48a',
                  {'kind': 'gunrope', 'anim': 'gun', 'rest': 'grip-%d' % i, 'fire': 'grip-%d-fire' % i}, '拉繩'))
for t in ('a', 'b'):
    ROPES.append(('mangonel-投袋繩-%s' % t, 'model:mangonel-arm/sling', 'model:mangonel-arm/pouch-%s' % t, 0.1, '#b89c6a',
                  {'kind': 'gunrope', 'anim': 'gun'}, '投袋繩'))
for name, a, b, th, col, meta, what in ROPES:
    cli.run(['op=work', 'sub=rope', 'persona=erina', 'work=' + WORK, 'name=' + name, 'from=' + a, 'to=' + b,
             'slack=1', 'thickness=%g' % th, 'color=' + col, 'overwrite=1', 'note=投石機的%s（apply_mangonel_ropes.py）' % what], quiet=True)
    cli.run(['op=work', 'sub=meta', 'persona=erina', 'work=' + WORK, 'part=rope', 'name=' + name, 'meta=' + json.dumps(meta, ensure_ascii=False)], quiet=True)
    print('rope', name, a, '→', b)
