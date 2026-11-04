鹽田的沼澤鹽款、礦坑的鹽岩款（TASK-1199；Tim 2026-11-04「另外變體可以參考金礦 銀礦坑 外型稍微改變(子模組替換)」）。
- 沼澤鹽田：基礎款 kotoko-grainsea-01m 的鹽田（design/grainsea.py saltpan()）整座照生 —— 鹽換成灰的海灣鹽（sel gris：182 帶 146），池埂頂上一叢一叢鹽沼的草（76、44）。variant b、meta recipes salt-marsh。
- 鹽岩礦：基礎款 apex-one-industry-01m 的礦坑（design/industry.py mine()）整座照生 —— 礦石換成岩鹽（250 淡橘白、246 偏粉、255 亮面）；前院右半邊兩垛鹽磚（0.6 × 0.4 × 0.3 m、三層交錯）、五個鹽袋。variant d、meta recipes rock-salt。
- 成品 meta recipes ⇒ Blocksail townmodels 索引 ⇒ 遊戲照地塊配方挑這一款（同 ridge-two-mine-ores-01m）。
- 產生：design/salt.py ＋ build.py；落格 apply.py（create／stamp／anchors／links／models／check：缺 0 多 0 色差 0；沼澤鹽田元件 7 ＝ 基礎款也是 7、鹽岩礦元件 1）。
- 史料〔通論，沒翻原典〕：大西洋岸的鹽沼耙出來的鹽帶灰；岩鹽在礦裡鑿成塊運出（卡多納、維利奇卡）—— 塊的大小、垛法是設計。
