# 三叉戟號 TODO

## 下一步：階段八 砲（TASK-0561）
- 階段七已驗收（notes.md 階段七讀數；`tools/check_stage7.py`）。
- 先跟 ame 對砲種代碼：遊戲的 `GUNS`／`DMG` 是寫死的幾個鍵；本船上層 12 磅、第四層 8 磅＋obús 沒有對應 ⇒ 問要新增鍵（summit 提過 12l）還是照最近的砲種。對好之前不落砲。

## 再之後
- 彈藥庫與甲板物件（TASK-0562）、匯進遊戲（TASK-0563）。
- jib-boom 尖 x 953、z 344（組裝件 x 1100 夠用）；之後若加 flying jib-boom 再量一次。
- 匯進遊戲（TASK-0563）前：每一層甲板關聯照造船規格 §9.3 標 `kind=deck`（level、name、floor、thick；`decks.py` 量）；本船沒有隔出來的艙房（§9.2 不適用，除非之後加）。
- 父層 Valhalla 的 Sculpture 指標還沒 bump。
