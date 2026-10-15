# 拿破崙號 TODO

## 現況（2026-10-16 凌晨，告一段落）
- 十個階段都做完：船殼、砲門與塗裝、甲板梯子、船頭船尾與煙囪螺旋槳、桅與帆桁、索具與帆、砲 90 門、彈藥庫／舵／甲板零件／艙房／錨、匯出 vxk。
- 暫存副本的匯入檢查 ✗ 0、⚠ 1（geo）—— 正式匯進遊戲由 ame 做（`admin.py import --work kotoko-napoleon-01m-assembly --id napoleon --name 拿破崙號`）。

## 等遊戲那側
- ✓ geo、cfg（額外動力 12 節）ame 填好了（d1815aa）。
- ✓ ame 已匯進遊戲（Blockside d1815aa「拿破崙號上船」，沒有機艙那一版）；senate 988bf02 已部署，匯出會帶煙囪的 iron／smooth。
- ✓ faux-pont 的 floor 折線不用拆（ame：遊戲照格子切走路格）。
- ✓ 螺旋槳拆成外部模型（kind=propeller，2026-10-16 階段十二）；軸的 aft 改到螺旋槳柱 x 193 ⇒ 遊戲接得上。
- 蒸汽機（階段十一）標了 kind=engine／boiler／shaft。遊戲的動力第一版（Blockside 7307cf2，31_drive.js）讀的是螺旋槳模型（kind=propeller，作用點 hub，模型掉了 ⇒ 不出力）× 煙囪還在幾成；engine／boiler／shaft 在 Blockside HEAD、工作區、worktree 都 grep 不到（2026-10-16 午）—— 可是 ame 在 seq 25026 報過讀數（打掉主機 ⇒ 0%、1／8 座鍋爐 ⇒ 87.5%），多半還在她那側沒落地；問她，別猜。
- ✓ 遊戲 bug（格座標 x 只壓 10 位元 ⇒ 殉爆後 jib-boom 留在空中）已修：Blockside 16a5507、成品 20ca300。
- 遊戲裡的拿破崙號是沒有機艙那一版（d1815aa）；現在作品 2,129,382 格、checksum 95738965（機艙＋螺旋槳模型）⇒ ame 重新匯入（她說拆完就匯、開一場給 Tim 看）。

## 之後可以做（沒人要求前不做）
- 砲具與砲索、rammer／sponge、shot garland（三叉戟號的階段十～十二）。
- 船尾四分之一的白帶有一點零碎。
- 前彈藥庫上層木架的立柱只立在一側（鏡像差 37 格，741,204,31–35；見 notes 階段九）。
