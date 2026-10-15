# 潮墓號 — 給 ame 的遊戲匯入交付

Tim 2026-10-15 授權完成造船，並通知 ame 加入遊戲。

匯入作品 `sirius-tidegrave-01m-assembly`，建議遊戲 ID `tidegrave`、名稱「潮墓號」。
交付檔 `tidegrave_import_20261015.vxk`，精確 SHA256、格數、部件數見
`import_manifest.json`。請勿再拿歷史 candidate_20261014/20261015 當最新檔。

正常匯入命令（由 ame 在自己的 Blockside 工作區執行）：

```powershell
python -I src/admin.py import --work sirius-tidegrave-01m-assembly --id tidegrave --name 潮墓號
python -I src/admin.py verify
python -I src/admin.py shipcheck --id tidegrave
```

CLI 每次匯出會改 `exported_at`。新匯出與交付檔的比較須對 body、完整 rig、
parts/meta/ends 逐值核對，不能把只有時間不同誤報為幾何變更。

## 作者提供的實測尺寸與結構

- 0.1 m/格；+X 船頭、-Y 左舷、y120.5 是連續座標鏡面。
- 船殼設計跨度 x100..620（52m），最大名義寬 13.4m；艏斜桅伸至 x748.5。
- `waterline_z=52`，甲板走路高度 lower66、upper91、weather116、quarter139、
  poop165、forecastle139。forecastle 與 quarter 同高但不相連。
- 三桅 x205.5、355.5、510.5；桅頂 z405.5、510.5、465.5，平台 z265、300、280。
- 54門砲：48門24l舷砲、6門18chase固定艏砲。沒有旋轉三聯砲機能。
- 舵輪 at(198.5,143.5,139)，不在中線；舵手請按舵輪實際 bbox/XY/Z 找站位。
- 七梯均有 foot/lo/hi/head；既有18格高×7格寬實體淨空修復與14梯端證據仍保留。
- 兩彈藥庫各24桶、2400lb；六甲板meta完整；未隔成額外醫療艙，不把空間虛標成房間。
- 新增共用 bower 錨2件（basecamp來源、scale1），ring/crown/flukes隨模型變換；
  船殼上 hawse-P(560,94,150)、hawse-S(560,146,150)，短錨索連到實際錨環。
  錨的實體／既有模型／繩路檢查見 anchor_placement.json。

`geo/cfg/crew/names/rooms/lamps` 屬遊戲配置，由 ame 依最新介面填。
本次已在隔離版套用 `game_integration/suggested_ship.json` 及
`game_integration/23_powder.patch` 跑過最新遊戲：**0 errors / 2 warnings**，
54砲全滿編、352船員、左右錨/ring/hawse與7梯均可讀。兩警告是陸戰隊11/12、
chase-2 的取用點與砲尾在尋路格上不連通（送藥手目前照直線走）。請在正式匯入時
調整站位/取用點；原報告 `shipcheck_tidegrave.md` 保留，不刪警告冒稱全過。

`23_powder.patch` 修正艏艉向砲的送藥手出生位置：砲口可能伸出甲板，改用砲尾後方；
正橫舷砲沿用原規則。這份補丁與配置目前只套在隔離副本，正式Blockside由ame覆核採用。
未套補丁與geo的同一份船曾報6 errors / 7 warnings，不能只匯入模型而漏接配置。

舊 fixture 的 geo 僅可作初值：spar[114,140]、marines[180,215]、center155、aim90、
aimZ[30,480]、deckAim[74,106]、rigAim[210,410]。這些值沒有跟最新遊戲站位全域回歸，
不要直接視為最終配置。特別是官員與舵手須能站在高艉樓／偏中線的舵輪旁。

## 程式與驗收交界

ame 已以 Blockside ebd55ff 接入 Sirius 的固定點／局部接觸／首次展帆修正，
並補風速上限。請沿用 ame 最新程式，不覆蓋回本次早期凍結的30檔。
`nav_deck_candidate` 是舊隔離候選，僅供參考，不直接套 patch；最新遊戲仍須核對
同高甲板梯端選層、偏中線舵輪站位及舵手補位。

Tim 選擇手動動態驗收，TASK-0603/0546 尚未簽完整PASS。正常1.5ms預算仍有自由布
局部穿透：jib-halyard 對 fore-topgallant、mizzen-lateen 對自身 sheet-P。
凍結短測見 `../task0603/manual_final_smoke/REPORT.md`；物理與渲染固定點各1302次
檢查最大誤差0。完整20場景沒有重跑，500繩任意非同步角組合亦未全域簽收。
這些後續由手動結果與 TASK-0603 追蹤，不把 shipcheck 成功等同所有碰撞通過。

目前格子1,034,323、連通1、封閉空腔0、鏡像缺格/異色0、link overlap/clipped0。
重匯兩次除 exported_at 外內容相同，VXK對CLI list逐格逐色相同，一格改色負向能失敗。
這是目前狀態的可重現匯出；未宣稱所有歷史階段的初建腳本可直接安全重跑。

歷史證據與圖紙保持原樣。新的錨與接觸修正，不搬動既有帆固定點，也不改船殼格子。
