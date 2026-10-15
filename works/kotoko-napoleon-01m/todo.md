# 拿破崙號 TODO

## 現況（2026-10-16 凌晨，告一段落）
- 十個階段都做完：船殼、砲門與塗裝、甲板梯子、船頭船尾與煙囪螺旋槳、桅與帆桁、索具與帆、砲 90 門、彈藥庫／舵／甲板零件／艙房／錨、匯出 vxk。
- 暫存副本的匯入檢查 ✗ 0、⚠ 1（geo）—— 正式匯進遊戲由 ame 做（`admin.py import --work kotoko-napoleon-01m-assembly --id napoleon --name 拿破崙號`）。

## 等遊戲那側
- ✓ geo、cfg（額外動力 12 節）ame 填好了（d1815aa）。
- ✓ ame 已匯進遊戲（Blockside d1815aa「拿破崙號上船」，沒有機艙那一版）；senate 988bf02 已部署，匯出會帶煙囪的 iron／smooth。
- ✓ faux-pont 的 floor 折線不用拆（ame：遊戲照格子切走路格）。
- ✓ 螺旋槳拆成外部模型（kind=propeller，2026-10-16 階段十二）；軸的 aft 改到螺旋槳柱 x 193 ⇒ 遊戲接得上。
- ✓ 蒸汽機（階段十一）的 kind=engine／boiler／shaft 遊戲讀了：Blockside 8c1ef46（ame，31_drive.js 主機 → 軸 → 螺旋槳、鍋爐供汽；壞了停煙）—— 12.25 節、打掉主機 0%、1／8 座鍋爐 87.5%。
- ✓ 遊戲 bug（格座標 x 只壓 10 位元 ⇒ 殉爆後 jib-boom 留在空中）已修：Blockside 16a5507、成品 20ca300。
- 遊戲裡的拿破崙號是階段十一那一版（Blockside 8c1ef46 重新匯入：2,133,255 格、匯入檢查寫「螺旋槳是格子」，2026-10-16 01 時乾淨副本 shipcheck 回讀）；現在作品 2,129,382 格、checksum 95738965（螺旋槳模型，Sculpture 5cf18ce）⇒ 請 ame 再 reimport 一次（酒館 seq 25057）。

## 之後可以做（沒人要求前不做）
- 砲具與砲索、rammer／sponge、shot garland（三叉戟號的階段十～十二）。
- 船尾四分之一的白帶有一點零碎。
- 前彈藥庫上層木架的立柱只立在一側（鏡像差 37 格，741,204,31–35；見 notes 階段九）。
