# 三叉戟號 TODO

## 下一步：階段七 索具與帆（TASK-0560）
- 帆名照帆桁 meta 的 `sail`：`<桅>-<course|topsail|topgallant|royal>`、`spanker`（gaff＋boom）；crossjack、spritsail 沒有帆；三角帆（jib、staysail）自己取名、`mast=bowsprit`。每面帆、帆自己的繩照造船規格 §9.1 標 meta。
- 帆角綁帆桁模型：`model:<桅關聯>/yard-<帆桁>/earing-P|S`（帆桁一轉帆跟著走）；topsail 以上的 sheet 綁下一根帆桁同舷的 earing。
- 先做 channels（上甲板砲門 x 128–698 那一排要讓開 —— 憲法號階段二十九的坑）、再拉靜索（shrouds、backstays、stays）、ratlines、動索；bobstay 綁 `船頭-knee/bobstay-1|2|3`。
- boom 的尾端 x 84、z 211：spanker 的 sheet 往 taffrail 綁。

## 再之後
- 砲（TASK-0561：四層，砲種代碼跟 ame 對）、彈藥庫與甲板物件（TASK-0562）、匯進遊戲（TASK-0563）。
- jib-boom 尖 x 953、z 344（組裝件 x 1100 夠用）；之後若加 flying jib-boom 再量一次。
- 匯進遊戲（TASK-0563）前：每一層甲板關聯照造船規格 §9.3 標 `kind=deck`（level、name、floor、thick；`decks.py` 量）；本船沒有隔出來的艙房（§9.2 不適用，除非之後加）。
- 父層 Valhalla 的 Sculpture 指標還沒 bump。
