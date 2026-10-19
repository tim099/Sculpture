# 光榮號 TODO

- [x] 遊戲正式匯入（2026-10-18，Blockside 2fa8dcc 在 dev、已推測試站）：shipcheck ✗ 0 ⚠ 0；geo、cfg（base 12.3、pump 32、agile 1）、names 填了（notes「匯進遊戲」）。
- [ ] 發版到 main／origin —— 等 Tim 在測試站看過。
- [x] 機艙（階段十）：HRCR 主機、會轉的曲柄、軸、八座鍋爐、鐵地板 level −1、主艙口兩座梯子；金屬件 iron／boiler ＋ render=smooth。
- [x] 陳設（階段十一）：爐灶（自己的）、繫纜柱、繫索栓圍欄 ×2、砲彈架 ×4（拿破崙號元件），deco=1；舵與舵輪 spin。
- [x] 砲門蓋板（TASK-0719，2026-10-19）：一件子作品 `-portlid` 掛 34 次（砲甲板兩舷各 17；meta kind=portlid、lid_of、close_deg、house），開著／關上跟船、跟縮回的砲量過（notes「砲門蓋板」）；規格 §9.12。
- [ ] 砲門蓋板匯進遊戲（TASK-0719 J-1 第 6 步：Blockside `meta_kinds.json` 先有 `portlid` 那一列 ⇒ `reimport --id gloire`、`ids --id gloire`）；Tim 看一次（船尾 1、2 號關上會吃進船殼 1–2 格）。
- [ ] 全船預設材質照舊是橡木（鐵甲帶、煙囪、指揮塔、主機、軸另外標 iron；鍋爐 boiler）—— 不用改。
- [ ] 可以再做的外觀：艉樓舷側的一排小方窗（1863 照片）、指揮塔的走道翼與兩座梯子（史料）、砲具與砲索、1860 年的輕帆裝版本（另一個組裝件 preset 或另一艘）。
- [ ] 機艙還沒做：煤艙（675 t）、蒸汽管（kind=steampipe）、冷凝器與泵；主機的活塞桿與連桿不會動（spin 只會轉）。
- [ ] 1866–68 年改裝的砲（240 mm／194 mm）若要做成另一個版本：砲甲板 6 門 240 mm ＋ 上甲板 2 門 194 mm（RES）。
