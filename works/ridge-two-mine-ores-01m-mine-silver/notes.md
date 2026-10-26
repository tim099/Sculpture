礦坑的金礦款、銀礦款（TASK-1018；Tim 2026-10-27「4 加微調子模型」）。
- 基礎款：apex-one-industry-01m 的礦坑（design/industry.py mine()）整座照生，礦石換色：金 ＝ 含金石英（255 帶 248 金點）、銀 ＝ 暗灰銀礦（73 帶 219 銀光）。
- 加的：金 ⇒ 淘金槽（槽頭水桶、斜木槽、橫擋留金砂）＋三個淘金木盤（batea）；銀 ⇒ 石板院（patio）上的礦泥餅（torta，汞齊法）＋五個皮礦袋（zurrón）。
- 成品 meta recipes ＝ gold-ore／silver-ore ⇒ Blocksail townmodels 索引 ⇒ 遊戲照地塊配方挑這一款；variant b／c。
- 產生：design/ores.py ＋ build.py；落格 apply.py（create／stamp／anchors／links／models／check：缺 0 多 0 色差 0、元件 1）。
