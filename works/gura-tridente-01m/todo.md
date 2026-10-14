# 三叉戟號 TODO

## 下一步：階段七收尾（TASK-0560，已套用、還沒驗收）
- 索具與帆已經落到組裝件（notes.md 階段七）；剩：`tools/check_stage7.py`（channels 結果帳、組裝件結果帳、繩／帆逐條 vs rigging_plan.json、帆自己的繩沒有 meta 0）、反向對照（拿掉一條 sheet 的 meta ⇒ 報 1，再加回）、draft_rigging.py 重跑逐位元組、過程圖、看帆形狀（course clew、三角帆、旗）細修、勾單提交（Fixes TASK-0560）。

## 再之後
- 砲（TASK-0561：四層，砲種代碼跟 ame 對）、彈藥庫與甲板物件（TASK-0562）、匯進遊戲（TASK-0563）。
- jib-boom 尖 x 953、z 344（組裝件 x 1100 夠用）；之後若加 flying jib-boom 再量一次。
- 匯進遊戲（TASK-0563）前：每一層甲板關聯照造船規格 §9.3 標 `kind=deck`（level、name、floor、thick；`decks.py` 量）；本船沒有隔出來的艙房（§9.2 不適用，除非之後加）。
- 父層 Valhalla 的 Sculpture 指標還沒 bump。
