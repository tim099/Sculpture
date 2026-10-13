# 夜隼號 TODO

## ✅ 拍板（2026-10-13，Tim：「都交由妳決定（這是妳的作品）」⇒ summit 定）
- 舷高：**水線以下不動**（淺吃水是船設「錯了劇情會垮」那一條）；**水線以上**補輪廓 —— 後甲板（船尾抬約 1 m）＋舷牆＋船頭欄杆。⛔ 不整體加高：舷越高重心越高，對淺吃水的船是錯的方向。
- 《桅頂的賭注》000 話（三桅、船身漆字）：維持 v1 凍結、不重畫 —— 錯記在分鏡註記與《夜隼號造船記》000 序；重畫會把這筆帳從畫面上抹掉，還要 gura 多付一話。

## ✅ 階段二（2026-10-13 午）：線形 v2（舷牆、後甲板）＋ 骨架與肋骨落格 24,225 格 —— 見 notes.md
- [x] 做法：照真船順序（骨架 → 肋骨 → 外板），不做實心殼
- [x] plan.json 加後甲板段、舷牆 ⇒ 線形 v2，跟定稿圖再比一次（船腰對上；後甲板定稿圖仍高約兩成半，照拍板不追）

## ✅ 階段三（2026-10-13 午）：插板槽、外板、頂蓋、結構塗裝 —— 54,820 格，見 notes.md
- [x] 外板（漏水 0）、插板槽（中線、兩桅之間）、船底 254／船身 36、頂蓋 104

## ✅ 階段四（2026-10-13 午）：砲門 12、clamp、甲板子作品兩件、組裝件 —— 組裝件 77,092 格，見 notes.md

## 下一步
- [ ] **內板（ceiling）**：等 @ame —— 肋骨之間的縫封成空腔要填實還是留空（對轟的破壞與匯出）。先不做
- [ ] 砲門那一列的色帶（定稿圖兩條淺線）—— spray
- [x] 船尾窗廊、船尾窗、船尾燈、隼形船首像（階段五）
- [x] 船頭欄杆、舵、開窗（階段六）
- [ ] knightheads、cathead（錨要掛）
- [ ] 舵改外部模型＋pivot（給遊戲轉）；舵輪接舵柱頂（隼徽記被剝後的疤）
- [ ] 斷口艙壁：門／欄杆（breastwork rail）；後甲板舷牆上半是欄杆（定稿圖）
- [x] 桅、艏斜桅、channels（階段七）
- [x] 帆桁（階段八：6 件子作品＋外部模型；固定點 84 在 verify_yards.json 的 placements[].anchors）
- [x] 靜索（階段九：channels v2＋下 deadeye＋chain plates；繩 207 —— shrouds、backstays、futtock、topmast／topgallant shrouds、stays 6＋bobstay、上 deadeye＋lanyards、ratlines）
- [x] 繫繩點＋動索（階段十：fife rails＋bitts＋main sheet horse、舷牆 pin rails 12 根／舷、pins fife 20＋舷牆 80（兩舷）；動索 44 —— lifts、footropes、braces＋falls、halyards、gaff peak halyard＋vangs、topping lifts、main sheet）
- [x] 帆（階段十一：方帆 4、gaff 主帆、三角帆 3；主桅加一根不掛帆的下桁；帆腳索 20；預設風 4.5,−1.5,0）
- [ ] 帆的鼓度：方帆最鼓 ≈ 寬的 32–35%（kotoko 說真的方帆約一到兩成）—— 旋鈕是風，等 Tim 看 stage11_sails_yaw45 與 _wind2.4 選
- [ ] brace 角：帆桁都正橫（rz 0）；要轉時 course 下角的 sheet／tack 落在船上的 pin，轉很大會被拉歪（Shipbuilding §7）
- [ ] 旗：候選圖在 summit-night-falcon-01m-flag（⛔ 不是定稿）—— 掛在主桅 truck
- [ ] 砲（外部模型、退到零碰撞）、插板（外部模型，pivot）
- [ ] 甲板拱度沒做（平的）；艙口梯

## 之後會撞到的（先記）
- 插板放下會伸出龍骨底 ⇒ 插板做成會轉的外部模型（pivot），組裝件框往下加
- 空間 X 384：量了 —— boom 尾端 x 43.6（框從 0 起）、jib-boom 到 x 358；三角帆在 stay 上，不會比 jib-boom 更前
- 砲門與甲板高度一起規劃（Shipbuilding §3）；channels 跟砲門一起排
- 砲、帆桁、舵輪一開始就做外部模型
- 舵輪：隼徽記被剝後的疤（007 起）
- 旗：候選圖在 summit-night-falcon-01m-flag（⛔ 不是定稿）
