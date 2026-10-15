# 拿破崙號 TODO

## 現況（2026-10-15 下午）
- 十個階段都做完：船殼、砲門與塗裝、甲板梯子、船頭船尾與煙囪螺旋槳、桅與帆桁、索具與帆、砲 90 門、彈藥庫／舵／甲板零件／艙房／錨、匯出 vxk。
- 暫存副本的匯入檢查 ✗ 0、⚠ 1（geo）—— 正式匯進遊戲由 ame 做（`admin.py import --work kotoko-napoleon-01m-assembly --id napoleon --name 拿破崙號`）。

## 等遊戲那側
- `ships[].geo`（notes 階段十有量好的高度）、`cfg`（蒸汽：史料 12.14 kn 連續、13.86 kn 最高 ⇒ `cfg.base`）、`crew`、`names`。
- 匯入要材質（煙囪 iron）⇒ PATH 上的 senate 要是 646eb3a 之後的 build（`publish/senate.exe` 09:02 那顆沒有）。
- ⚠ faux-pont 的 floor meta 中間是機艙（沒有地板）—— 遊戲照折線看不出來，看要不要拆成兩段。
- 螺旋槳在遊戲裡只是外觀（沒有對應的 kind）。

## 之後可以做（沒人要求前不做）
- 砲具與砲索、rammer／sponge、shot garland（三叉戟號的階段十～十二）。
- 船尾四分之一的白帶有一點零碎。
- `design/tools/check_stage5.py` 還照舊關聯 `煙囪` 讀 —— 階段九拆成 `煙囪-後`／`煙囪-前` 之後要改成讀這兩條才能重跑。
