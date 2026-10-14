# 三叉戟號 TODO

## 下一步：階段六 桅與帆桁（TASK-0559）
- 桅的截面用 `layout.mast_hit`（甲板孔就是它開的）；桅高、帆桁長照 plan.masts（本船 1793 表）；帆桁一開始就是一根一件子作品＋模型（造船規格 §5）。
- 艏斜桅：根部 (690, 172)、仰角 32°，會切過船頭舷牆頂（x 718–721、z ≈ 184–196）⇒ 開孔；gammoning 綁 knee 上緣靠艏柱那段；bobstay 的固定點已經在 `-head-knee`（`bobstay-1／2／3`）。
- 船尾燈、徽在 taffrail 上（z 207 起）—— 後桅的 boom 往後伸時避開。

## 再之後
- 索具與帆（TASK-0560）、砲（TASK-0561：四層，砲種代碼跟 ame 對）、彈藥庫與甲板物件（TASK-0562）、匯進遊戲（TASK-0563）。
- 艏斜桅尖端會到 x ≈ 980；組裝件 x 1100 夠用。
- 匯進遊戲（TASK-0563）前：每一層甲板關聯照造船規格 §9.3 標 `kind=deck`（level、name、floor、thick；`decks.py` 量）；本船沒有隔出來的艙房（§9.2 不適用，除非之後加）。
- 父層 Valhalla 的 Sculpture 指標還沒 bump。
