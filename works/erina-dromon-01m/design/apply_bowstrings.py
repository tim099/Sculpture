# 弩弦落地（Tim 2026-10-18：「弩炮的弦是否可以改用繩索 並在開火時有動態」）：每座弩砲兩條繩 string-a → nock → string-b，
#   兩端寫明綁在那座弩砲上（model:<模型>/<固定點>，固定點在 erina-dromon-01m-ballista：draft_weapons.py）、拉直（slack 1）、meta kind=bowstring。
#   繩建在那座弩砲所在的子作品裡（艏樓／木塔），名字對得上模型。遊戲照 kind=bowstring 讓它跟著弩砲轉、放箭彈出、裝填拉回（Blockside 21_gunnery.js bowStep）。
# 用法：python -I -X utf8 -B apply_bowstrings.py
import os, sys, json
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import cli

HULL = 'erina-dromon-01m'
HOSTS = {HULL + '-forecastle': ['ballista-bow'], HULL + '-castles': ['ballista-castle-S', 'ballista-castle-P']}
for work, models in HOSTS.items():
    for m in models:
        for tag, a, b in (('a', 'string-a', 'nock'), ('b', 'nock', 'string-b')):
            name = '%s-弦-%s' % (m, tag)
            cli.run(['op=work', 'sub=rope', 'persona=erina', 'work=' + work, 'name=' + name, 'from=model:%s/%s' % (m, a), 'to=model:%s/%s' % (m, b),
                     'slack=1', 'thickness=0.15', 'color=#d8c8a0', 'overwrite=1', 'note=弩弦（apply_bowstrings.py）'], quiet=True)
            cli.run(['op=work', 'sub=meta', 'persona=erina', 'work=' + work, 'part=rope', 'name=' + name, 'meta=' + json.dumps({'kind': 'bowstring', 'anim': 'gun', 'rest': 'nock', 'fire': 'nock-fire'})], quiet=True)
            print('rope', work[len(HULL) + 1:], name)
