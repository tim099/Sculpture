# 醫療艙家具組（TASK-0569）

> Tim 2026-10-15「TASK-0569 全包 GO」—— 《憲法號對轟》醫療艙的裝飾物模型：病床、手術台、藥箱。委託作品（commission_ref TASK-0569，建立免費、已發 10 token）。
> 本作品（0.1 m／格）＝ **目錄**：三件以外部模型掛在一塊木地板上，匯出的 `exports/medbay_furniture.vxk` 就是給遊戲讀的那一份。
> 三件子作品（0.05 m／格、tags sub、parent ＝ 本作品）：`-bed`、`-table`、`-medkit`。放上船：`work sub=model` 來源指子作品、**scale 0.5**、meta 照下表。

## 規格（給遊戲的）
| 件 | 子作品 | 外框（0.1 m 格） | meta | 固定點（子作品座標，整數 ＝ 格心） |
|---|---|---|---|---|
| 病床 | `-bed` 38×16×12 | 19×8×6 ＝ 設定檔 | `kind=furniture, item=bed` | `lie` (18,7,11) 毯子面中間、`head` (33,7,11) 枕頭（頭在 +x） |
| 手術台 | `-table` 36×32×16（檯子在 y 8–23） | 18×8×8 ＝ 設定檔 | `kind=furniture, item=table` | `lie` (18,15,15) 檯面中間、`work-1` (18,4,0)、`work-2` (18,27,0)：兩側長邊外的地板格（腳踩那一層） |
| 藥箱 | `-medkit` 7×5×5 | **3.5×2.5×2.5**（設定檔 5×4×4） | `kind=furniture, item=medkit` | 沒有 |
- meta 的兩個鍵 ＝ 遊戲 36_rooms.js shipRooms 給佔位模型的那兩個；固定點名照 TASK-0568「崗位物件」（lie、work-n）。
- 手術台的子作品比檯子寬 16 格（兩側各 8），是為了讓 work-1／work-2 落在作品範圍內；**模型外框照格子算，仍是 18×8×8**（parts 匯出讀回）。

## 尺寸出處（研究 agent 2026-10-15，文字、沒下載、沒被擋）
- **病床**：那個年代軍艦病人睡的是**吊在樑上的帆布 cot**；查到的尺寸只有 Encyclopaedia Britannica 4th ed.（1810）「COTT」：約 5 ft 長、1 ft 深、2–3 ft 寬，而且寫的是軍官用。RMG ZBA0556 是一次大戰的運傷 cot（3030×1685 mm），太晚。
  ⇒ 立地的病床沒有出處 ⇒ **照遊戲外框（1.9×0.8×0.6 m）與一般比例**，是遊戲的抽象（甲板格子上放得下、會被打壞）。
- **手術台**：海戰時是**幾個 midshipman 的海員箱綁在一起、蓋帆布**（USNI Proceedings 1935 轉述 Adkin *Trafalgar* —— 只讀到搜尋摘要，二手）。
  ⇒ 四個箱子 2×2、tarpaulin 頂、垂邊、兩道繩、上面一層摺起來的帆布墊。箱子 0.9×0.4×0.7 m **照一般比例**：查到的箱子是 RMG 19 世紀末 1041×711×610 mm、摘要裡的 18 世紀將官箱 978×470×406 mm，都不是本尊。外框照遊戲 1.8×0.8×0.8 m。
- **藥箱**：**照實物** RMG TOA0127（19 世紀初、據稱是特拉法加時納爾遜艦隊某艘的船醫）240×350×230 mm、桃花心木、黃銅包角、drop handles、黃銅蓋板 ⇒ 0.05 m 格取整 7×5×5（多 1–2 cm）。
  ⚠ 比遊戲設定檔小（0.5×0.4×0.4 m）—— 設定檔要不要改是 ame 的。⛔ 不畫紅十字（1864 年以後的符號）。

## 讀數
- 子作品回讀 ＝ 遮罩逐格（含顏色）：病床 2,560、手術台 9,032、藥箱 175。目錄地板 1,536（模型抬到 Z 1）。
- 模型外框（目錄座標）：病床 (2,2,1)–(21,10,7)、手術台 (24,4,1)–(42,12,9)、藥箱 (46,4,1)–(49.5,6.5,3.5)；models_broken 0。
- **匯出** `exports/medbay_furniture.vxk`：1,536 格、模型 3、mesh 3、帶 meta 3、固定點 5、sha256 28e6a3e9…。
  **遊戲讀得到**：用 Blockside 的 `VoxelKit/voxelkit.js` 的 `VK.parse` 讀（解壓改 zlib —— node 20.11 的 DecompressionStream 不收 deflate-raw）⇒ 3 個模型、meta、固定點、三角形 132／228／72 都讀得出來。接進 `furnMesh`（現在是程式產生的佔位方塊）是遊戲那側。
- **放進空艙房零碰撞**（`design/tools/room_fit_check.py` ⇒ `design/verify_room_fit.json`）：憲法號 berth 右舷 7 號艙房（(270,181,61)–(289,208,74)，20×28×14 格），病床、手術台長邊沿 x 並排、藥箱旁邊；
  三件都在艙房內、跟船體實心格 **0 格**重疊。反向對照：病床往牆裡推 3 格 ⇒ **36 格**重疊（尺看得到不一致）。

## 改過的
- v1 照設定檔 10×8×8 的紅蓋藥箱、一張木桌當手術台 ⇒ v2 照研究：藥箱照 RMG 實物、手術台改成綁起來的海員箱。
- 顏色：v1 帆布 214 渲染偏粉紅、毯子 74 太藍 ⇒ 帆布 182、毯子與 tarpaulin 109。
- 目錄 v1 只有模型、沒有格 ⇒ `export format=vxk` 回「觀測區域內沒有任何 voxel」⇒ 鋪 Z 0 木地板。

## 檔案
`design/draft_furniture.py`（三件遮罩＋擺法）、`design/tools/furniture_apply.py`（下 CLI；子作品已在就不重建）、`design/tools/room_fit_check.py`、`design/furniture_placement.json`、`design/verify_furniture.json`、`design/verify_room_fit.json`、`overlays/catalog_v2.png`。
- ⚠ `exports/` 在 Sculpture 的 .gitignore（`.gitignore:11`）⇒ vxk 不進版控。換一台要重匯：
  `senate cmd sculpture --arg op=export --arg work=basecamp-medbay-furniture-01m --arg format=vxk --arg include=rig,models,parts,meta --arg out=<絕對路徑>`
