# 蘇士奎哈納號（crest-001，TASK-0697）：本檔抄自光榮號 kaguya-gloire-01m/design/tools/apply_propeller.py（kaguya）—— 下面註解裡的「蘇士奎哈納號」原文是光榮號，改過的地方另外註明
# 蘇士奎哈納號 螺旋槳改成外部模型（Tim 2026-10-15：「螺旋槳拆成子模組，讓遊戲中螺旋槳跟著前進速度旋轉」）
#   子作品 -screw 本來是關聯（格子組進船裡）⇒ 改成外部模型（同舵的做法：子作品用整船的框、at ＝ pivot ＝ 轉軸中心），遊戲拿得到它的網格、轉軸與固定點。
#   meta（給遊戲的約定，寫進造船規格 §9 propeller）：kind=propeller、axis_x／y／z（轉軸方向，組裝件座標；推船往前時的旋轉照右手定則繞 +axis）、
#     blades、diameter_m。固定點（子作品裡）：hub（轉軸中心那一格）、shaft-fwd（軸往前接到船殼那一格）。
#   用法：python -I -X utf8 tools/apply_propeller.py <design>
import json, os, subprocess, sys

sys.stdout.reconfigure(encoding='utf-8')
D = os.path.abspath(sys.argv[1])
plan = json.load(open(os.path.join(D, 'plan.json'), encoding='utf-8'))
HULL = 'crest-001-susquehanna-01m'
SUB, ASM = HULL + '-screw', HULL + '-assembly'
pr, sc, YC = plan['propeller'], plan['deco']['screw'], plan['space']['yc']


def cli(*a, ok=(0,)):
    r = subprocess.run(['senate', 'cmd', 'sculpture'] + [x for kv in a for x in ('--arg', kv)], capture_output=True, text=True, encoding='utf-8', errors='replace')
    if r.returncode not in ok:
        print((r.stdout + r.stderr)[-1200:])
        raise SystemExit('✗ ' + ' '.join(a[:4]))
    return r.returncode


bx = (sc['blade_x'][0] + sc['blade_x'][1] + 1) / 2.0                  # 葉片那一段的中心（x 151–155 ⇒ 153.5）
hub = [bx, YC + 0.5, pr['hub_z'] + 0.5]                               # 轉軸中心（格心座標）
cli('op=work', 'sub=anchor', 'persona=crest-001', 'work=' + SUB, 'name=hub', 'at=%d,%d,%d' % (int(bx), YC, pr['hub_z']), 'note=轉軸中心（葉片中段、軸線上那一格）')
cli('op=work', 'sub=anchor', 'persona=crest-001', 'work=' + SUB, 'name=shaft-fwd', 'at=%d,%d,%d' % (sc['shaft_x'][1], YC, pr['hub_z']), 'note=軸往前接到螺旋槳柱（船殼）那一格')
meta = {'kind': 'propeller', 'axis_x': 1, 'axis_y': 0, 'axis_z': 0, 'blades': pr['blades'], 'diameter_m': round(pr['diameter'] * plan['meters_per_cell'], 2)}
rc = cli('op=work', 'sub=unlink', 'persona=crest-001', 'work=' + ASM, 'name=螺旋槳', ok=(0, 2))
print('關聯 螺旋槳', '拿掉' if rc == 0 else '本來就沒有')
cli('op=work', 'sub=model', 'persona=crest-001', 'work=' + ASM, 'name=螺旋槳', 'source_work=' + SUB, 'at=%g,%g,%g' % tuple(hub), 'pivot=%g,%g,%g' % tuple(hub),
    'rotate=0,0,0', 'scale=1', 'overwrite=1', 'meta=' + json.dumps(meta), 'note=螺旋槳（外部模型：遊戲照航速繞 axis 轉）')
print('✓ 模型 螺旋槳 at／pivot', hub, meta)
