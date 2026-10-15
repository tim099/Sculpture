# 拿破崙號 TODO

## 現況（2026-10-15 下午）
- 十個階段都做完：船殼、砲門與塗裝、甲板梯子、船頭船尾與煙囪螺旋槳、桅與帆桁、索具與帆、砲 90 門、彈藥庫／舵／甲板零件／艙房／錨、匯出 vxk。
- 暫存副本的匯入檢查 ✗ 0、⚠ 1（geo）—— 正式匯進遊戲由 ame 做（`admin.py import --work kotoko-napoleon-01m-assembly --id napoleon --name 拿破崙號`）。

## 等遊戲那側
- ✓ geo、cfg（額外動力 12 節）ame 填好了（d1815aa）。
- ✓ ame 已匯進遊戲（Blockside d1815aa「拿破崙號上船」，沒有機艙那一版）；senate 988bf02 已部署，匯出會帶煙囪的 iron／smooth。
- ✓ faux-pont 的 floor 折線不用拆（ame：遊戲照格子切走路格）。
- 螺旋槳在遊戲裡只是外觀（沒有對應的 kind）。
- 蒸汽機（階段十一）標了 kind=engine／boiler／shaft —— 遊戲還沒讀；「引擎壞了 ⇒ 額外動力消失、煙停」的規則由 ame 接（建議判法在 notes 與造船規格 §9）。
- ✓ 遊戲 bug（格座標 x 只壓 10 位元 ⇒ 殉爆後 jib-boom 留在空中）已修：Blockside 16a5507、成品 20ca300。
- 遊戲裡的拿破崙號是沒有機艙那一版（d1815aa）；加了機艙之後 2,133,255 格、checksum 1066745730 ⇒ 要不要 reimport 由 ame 決定（酒館 seq 24986）。

## 之後可以做（沒人要求前不做）
- 砲具與砲索、rammer／sponge、shot garland（三叉戟號的階段十～十二）。
- 船尾四分之一的白帶有一點零碎。
- `design/tools/check_stage5.py` 還照舊關聯 `煙囪` 讀 —— 階段九拆成 `煙囪-後`／`煙囪-前` 之後要改成讀這兩條才能重跑。
