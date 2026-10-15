# 收穫號 TODO

## 下一步：彈藥庫與甲板物件（TASK-0598）
- 砲已上船（階段八，notes）：44 門外部模型、零碰撞、砲口在船殼外；**階段八還沒提交**（Sculpture 65e9c70 只到階段七）。
- 主甲板砲門加高了一格（船殼改了，標記 `主甲板砲門加高`）；船殼的設計帳現在由 `design/tools/hull_expected.py` 組。
- 彈藥庫在底艙（orlop 只鋪中段 x 190–430 就是留給它的）、火藥桶沿用現有元件（components kind=powder）；舵輪、羅經櫃、絞盤、小艇也先查 components。
- ⚠ 甲板物件別擋砲班：遊戲砲班站在砲兩側外擴 3 格、砲尾後面 10 格內（Blockside/src/js/40_crew.js makeCrew）。

## 再之後
- TASK-0599 匯進 Blockside：交船前跑 shipcheck（砲班站不站得滿、開場就掉的、meta）。
- ⚠ lateen 的 meta 等 ame（seq 24767）。
- 砲索與砲具（造船規格 §4.4）還沒做，要不要做看 Tim。
