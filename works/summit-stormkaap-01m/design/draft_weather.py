# 階段十七：甲板風化 —— 五層甲板子作品裡的 104（新木頭的亮橘褐：甲板板、墊木）換成三種舊木色，照「板」排：
#   沿船長的一條條板（y 每 plank_y 格一條）、每 butt_x 格一個接頭（每條錯開 butt_shift），每一段照權重挑一色（固定種子 ⇒ 重跑相同）。
#   Tim 2026-10-14 晚：「甲板風化 GO」（階段四留著的那一條：104 在燈下像新木頭，不像鬼船）。
# 現況 ＝ 引擎匯出的五件甲板（<exports>/deck-<名>.list.txt）；只換 104 那幾格，其他色一格不動。
# 輸出：masks/weather/<deck>.vox.txt（子作品座標＝世界；新色）、verify_weather.json（每件格數、各色格數、sha256）
# 用法：python -I -X utf8 -B draft_weather.py <design 資料夾> <exports 資料夾>
import sys, os, json, random, hashlib
from collections import Counter

sys.stdout.reconfigure(encoding='utf-8')
D = os.path.abspath(sys.argv[1]); EX = os.path.abspath(sys.argv[2])
plan = json.load(open(os.path.join(D, 'plan.json'), encoding='utf-8'))
W = plan['weather']
out = {'note': 'draft_weather.py（階段十七）—— 現況 ＝ 引擎匯出 %s 的五件甲板' % os.path.relpath(EX, os.path.dirname(D)).replace('\\', '/'),
       'from': W['from'], 'to_history': W.get('to_history', []), 'decks': []}
for link, work in W['decks'].items():
    tag = work.rsplit('-', 1)[1]
    cells = [tuple(map(int, l.split(','))) for l in open(os.path.join(EX, 'deck-%s.list.txt' % tag), encoding='utf-8') if l.strip() and not l.startswith('#')]
    pick = {}
    new = {}
    for x, y, z, c in cells:
        if c != W['from']:
            continue
        band = y // W['plank_y']
        seg = (x + band * W['butt_shift']) // W['butt_x']
        key = (band, seg)
        if key not in pick:
            rng = random.Random('%d:%s:%d:%d' % (W['seed'], tag, band, seg))
            pick[key] = rng.choices(W['to'], weights=W['weights'])[0]
        new[(x, y, z)] = pick[key]
    path = os.path.join(D, 'masks', 'weather', tag + '.vox.txt')
    os.makedirs(os.path.dirname(path), exist_ok=True)
    txt = '# 風暴角號 甲板風化（%s，draft_weather.py）x,y,z,color —— 子作品座標，at 0,0,0；這些格現在都是 %d\n' % (link, W['from']) + \
          ''.join('%d,%d,%d,%d\n' % (k + (c,)) for k, c in sorted(new.items()))
    open(path, 'w', encoding='utf-8', newline='\n').write(txt)
    cnt = Counter(new.values())
    out['decks'].append({'link': link, 'work': work, 'file': 'masks/weather/%s.vox.txt' % tag, 'cells': len(new), 'total': len(cells),
                         'colors': {str(k): v for k, v in sorted(cnt.items())}, 'sha256': hashlib.sha256(txt.encode('utf-8')).hexdigest()})
    print(link, 'total', len(cells), '換', len(new), dict(cnt))
with open(os.path.join(D, 'verify_weather.json'), 'w', encoding='utf-8', newline='\n') as f:
    json.dump(out, f, ensure_ascii=False, indent=1)
