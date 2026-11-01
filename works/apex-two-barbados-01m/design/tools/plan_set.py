# 改 plan.json 的一小段（TASK-1147）：先驗「原樣讀進來再寫出去 ＝ 原檔逐位元組」（格式穩定 ⇒ 整份重寫只動改到的那幾行），再套改動
#   用法：python -I -X utf8 tools/plan_set.py <design> <改動.py>
#   改動.py 裡有一個 edit(P) 函式，直接改 dict P；跑完印 diff 的行數
import sys, os, json, difflib, importlib.util

design, patch = sys.argv[1], sys.argv[2]
p = os.path.join(design, 'plan.json')
src = open(p, encoding='utf-8', newline='').read()
dump = lambda P: json.dumps(P, ensure_ascii=False, indent=1) + '\n'
P = json.loads(src)
if dump(P) != src:
    raise SystemExit('plan.json 的格式不是 json.dump(indent=1) ⇒ 整份重寫會動到沒改的行，改用文字插入')
spec = importlib.util.spec_from_file_location('patch', patch)
m = importlib.util.module_from_spec(spec)
spec.loader.exec_module(m)
m.edit(P)
out = dump(P)
d = [l for l in difflib.unified_diff(src.splitlines(), out.splitlines(), lineterm='', n=0) if l[:1] in '+-' and l[:3] not in ('+++', '---')]
open(p, 'w', encoding='utf-8', newline='').write(out)
print('改了 %d 行' % len(d))
for l in d[:40]:
    print(l[:160])
