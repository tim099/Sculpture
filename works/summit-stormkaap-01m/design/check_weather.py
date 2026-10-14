# 階段十七讀數：只讀引擎匯出。五件甲板 換色前（<pre>/deck-<名>.list.txt）vs 換色後（<post>/deck-<名>.list.txt）
#   每件：格數不變；換了色的格 ＝ 清單上的格、色 ＝ 清單上的色；清單外一格都沒變；104 剩幾格
# 用法：python -I -X utf8 -B check_weather.py <design> <pre 匯出資料夾> <post 匯出資料夾> [偏移 dx,dy,dz]   偏移 ＝ 反向對照（清單整批平移）
import sys, os, json

sys.stdout.reconfigure(encoding='utf-8')
D, PRE, POST = (os.path.abspath(a) for a in sys.argv[1:4])
off = tuple(int(v) for v in sys.argv[4].split(',')) if len(sys.argv) > 4 else (0, 0, 0)
V = json.load(open(os.path.join(D, 'verify_weather.json'), encoding='utf-8'))


def rd(p):
    return {tuple(map(int, l.split(',')[:3])): int(l.split(',')[3]) for l in open(p, encoding='utf-8') if l.strip() and not l.startswith('#')}


for d in V['decks']:
    tag = d['work'].rsplit('-', 1)[1]
    a, b = rd(os.path.join(PRE, 'deck-%s.list.txt' % tag)), rd(os.path.join(POST, 'deck-%s.list.txt' % tag))
    want = {(k[0] + off[0], k[1] + off[1], k[2] + off[2]): c for k, c in rd(os.path.join(D, d['file'])).items()}
    changed = {k for k in b if a.get(k) != b[k]} | (set(a) - set(b))
    print('%s：%d → %d 格｜換了色 %d、清單 %d｜換了色的都在清單裡 %s、清單上的色都對 %s｜104 剩 %d' % (
        d['link'], len(a), len(b), len(changed), len(want), changed <= set(want), all(b.get(k) == c for k, c in want.items()),
        sum(1 for c in b.values() if c == V['from'])))
