"""威尼斯 galeazza（TASK-1302）步驟 6 落地：玻璃 ⇒ 子作品＋關聯（material=glass）；金飾 ⇒ 子作品＋外部模型（deco=1，可隱藏）。

用 apply_decks.py 的 cli()／component()；重跑安全（關聯、模型同名覆寫）。
"""
from pathlib import Path
import sys

D = Path(__file__).resolve().parent
sys.path.insert(0, str(D))
from apply_decks import ASM, cli, component


def main():
    M = D / 'masks/deco'
    glass = component('glass', '威尼斯加萊賽戰船 艉樓窗玻璃', [M / 'glass.vox.txt'])
    cli('work', sub='link', work=ASM, name='艉樓窗玻璃', source_work=glass, at='0,0,0', meta={'material': 'glass'})
    gilt = component('gilt', '威尼斯加萊賽戰船 金飾（聖馬可有翼獅、艏樓徽飾）', [M / 'gilt.vox.txt'])
    cli('work', sub='model', work=ASM, name='金飾', source_work=gilt, at='0,0,0', pivot='0,0,0', scale=1, meta={'deco': 1})
    print('ok', flush=True)


if __name__ == '__main__':
    main()
