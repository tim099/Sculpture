# 三叉戟號 TODO

## 下一步：階段八 砲（TASK-0561，設計完成、等 ame 確認代碼）
- 設計與讀數在 notes.md 階段八；`draft_guns.py` 已算好 138 門＋墊木 84 格（verify_guns.json）。
- ame 回覆砲種代碼（酒館 seq 24438）之後：代碼有改就改 plan `guns.types.*.code` 重跑 draft；然後
  1. 每層有墊木的甲板子作品打標記 `階段八墊木:begin` → `tools/apply_guns.py <design> pads` → `:end`
  2. `tools/apply_guns.py <design> models`
  3. `tools/check_stage8.py <design>`（墊木結果帳、parts、獨立碰撞、砲口、輪子、反向對照）、過程圖、notes 讀數、勾單。

## 再之後
- 彈藥庫與甲板物件（TASK-0562）、匯進遊戲（TASK-0563）。
- jib-boom 尖 x 953、z 344（組裝件 x 1100 夠用）；之後若加 flying jib-boom 再量一次。
- 匯進遊戲（TASK-0563）前：每一層甲板關聯照造船規格 §9.3 標 `kind=deck`（level、name、floor、thick；`decks.py` 量）；本船沒有隔出來的艙房（§9.2 不適用，除非之後加）。
- 父層 Valhalla 的 Sculpture 指標還沒 bump。
