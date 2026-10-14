# 《潮墓號》階段 0/1/2 獨立唯讀審核 — 2026-10-14

範圍 TASK-0541 / TASK-0543 / TASK-0544；作品 `D:/Unity/Valhalla/Sculpture/works/sirius-tidegrave-01m`。所有輸出只在本資料夾。未修改作品、未呼叫修改 CLI、未 import 作者模組（設計模組也未 import）。讀作者 source 僅用來理解座標及指出限制；重播、差帳、像素讀取、洪泛均獨立實作。

## 結論

| 驗收項目 | 結果 | 證據 |
|---|---|---|
| 階段0原創參數總圖、來源分類 | pass / 限定 | plan.json 有 design_decision/reference provenance；圖紙 hash 對 verify_general；獨立重算十站兩高度最大差 0.00004677 格（報告四位小數捨入） |
| 階段0直接反向對照 | unverified / 未宣稱通過 | verify_general 已明確撤回 datum shift；後續實物骨架、殼的3格對照可重建，不冒充階段0圖纸自身實物驗證 |
| 骨架逐事件結果帳 | pass | 4筆事件重播118405格；對 skeleton.vox.txt 缺0 / 多0 / 異色0 |
| 骨架圖紙占用帳 | pass | 從原色PNG像素出發18014個 side 投影點，缺0、多0；不是從遮罩選探針 |
| 骨架結構 / 真實反向對照 | pass | 6鄰接1元件、封閉空腔0、鏡像缺格/異色0；PNG探針(105,100)，整份actual資產X+3後最近距離3 |
| 初始船殼結果帳 | pass | 549603新格，合計668008；對 skeleton+shell.vox.txt 缺0、多0、異色0 |
| 船殼圖紙占用帳 | pass | 從PNG像素57519個 side 投影點出發，缺0、多0 |
| 船殼真實反向對照 | pass / 限定 | 舊(109,100)探針只移shell子集合報3；移完整actual報0，被骨架投影擋住。另選圖紙孤立點(100,150)，移完整actual X+3報3。具體值在 audit.json |
| 48舷砲門 | pass / 射線限定 | frame correction carve6480格，修正帳缺多異色0；12位置×2砲層×2船側共48條中心外向射線無阻塞。未宣稱48洞全截面皆符合16格尺寸 |
| 階段2水線下完整 | pass / 浸水範圍 | correction沒有刪z<52格。独立 z<52 exterior 6鄰接洪泛不能到艙內(350,120,40)，封閉水下空氣1397278格 |
| 現況主件水線下完整 | pass / 浸水範圍 | tiller後較階段2少4685格，x105..134 y118..122 z6..51；但相同洪泛仍不到內艙，封閉水下空氣保持1397278。格損不是漏水證據。此檢查不包含轉舵掃掠 |
| PNG材質顏色帳 | fail / minor | 骨架與船殼所有非背景像素都是(36,36,85)；正確RGB332的109及73應不同。build_structure.sheet 用 uint8 陣列乘255溢位，故圖紙幾何可靠、顏色不可識別 |
| 原圖史實線形偏差 | unverified / 不適用 | plan已明示線形為原創設計決定，未宣稱描圖；本審核不把museum參考當量測原圖 |

結案前建議修正 raster 算色的 dtype（乘法前转至少uint16），重產 skeleton/shell cell_plan/construction，重新簽圖紙顏色帳。若選擇接受，需明列為只驗占用幾何的minor，不能宣稱圖紙材質色一致。不要重 stamp 已完成作品。

## 可從 tracked 檔重建的舊證據

Git root 是 `D:/Unity/Valhalla/Sculpture`，不是 Valhalla 父層。以下已用 git ls-files 確認 tracked，無須依赖已消失的 scratchpad verifier：

- `works/sirius-tidegrave-01m/events/2026-10-13/*.json`：逐格 placed_colored/carved_voxels，是此次真實事件重播來源。
- `design/skeleton.vox.txt`, `design/shell.vox.txt`, `design/ports_frame_correction.vox.txt`：結果帳比較來源。
- `design/skeleton_cell_plan.png`, `design/shell_cell_plan.png`：圖紙像素帳來源。
- `design/plan.json`, `design/general_arrangement.png`, `design/verify_general.json`, `design/verify_skeleton.json`, `design/verify_shell.json`, `design/verify_ports_correction.json`：原創數值、圖紙與舊簽帳。

注意 `shell_missing.vox.txt` 現在為空，已不符合 stamp事件當時source sha；不能用空的現況missing檔重建歷史。事件自身逐格payload及完整 `shell.vox.txt` 足以重建。其餘 source SHA 比較在 audit.json；source檔被續作覆蓋不等於事件內容失真。

## 檔案與可重跑方法

`audit.py` → `audit.json`：逐事件 / 格色帳 / 圖紙像素 / 真實X+3 / 結構 / 鏡像 / 參數重算。`water_flood.py` → `water_flood.json`：x90..630、y40..200、z0..51浸水域；外水seed為四側及底部，水線頂面不seed。程式可用系統 Python 重跑，不寫作品目錄。

本輪也目視讀過總圖與早期 shell_yaw45。它們作為觀察補充，不代替上述數值證據。
