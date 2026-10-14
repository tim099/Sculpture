# 三叉戟號 TODO

## 下一步：階段九 遊戲必要零件（TASK-0562）
- 階段八砲已落格驗收（notes.md 階段八）；砲種 12l、6l 等 ame 加進遊戲砲種表（不加也能玩，照 24 磅算）。
- 彈藥庫前後兩間（orlop 底下的貨艙，後 x 236–296、前 x 562–632，自己鋪天花板）＋火藥桶（憲法號 -powder-barrel）；舵輪（憲法號雙舵輪）、羅經櫃、絞盤、小艇（餘燼號那幾件）。
- 之後：§9.3 甲板 meta（kind=deck）、匯出 vxk 進遊戲（TASK-0563）；砲具與砲索（§4.4）。

## 再之後
- 彈藥庫與甲板物件（TASK-0562）、匯進遊戲（TASK-0563）。
- jib-boom 尖 x 953、z 344（組裝件 x 1100 夠用）；之後若加 flying jib-boom 再量一次。
- 匯進遊戲（TASK-0563）前：每一層甲板關聯照造船規格 §9.3 標 `kind=deck`（level、name、floor、thick；`decks.py` 量）；本船沒有隔出來的艙房（§9.2 不適用，除非之後加）。
- 父層 Valhalla 的 Sculpture 指標還沒 bump。
