# 台灣帆竹筏 Tek-pái（1666 年期）造船筆記與規格對照（TASK-1312）

- **主作品（組裝件）**：`pinnacle-tekpai-01m-assembly`（`台灣帆竹筏`，`tags: ship,taiwan,tekpai,asia,1666`，`140 × 101 × 110`，`0.1 m/格`）
- **船殼作品**：`pinnacle-tekpai-01m`（`台灣帆竹筏 船殼`，`tags: sub`，`140 × 101 × 40`，`0.1 m/格`）
- **遊戲代號**：`tekpai`（`Blockside` `external/Blockside` ＋ `Blocksail` `world/fleet.js`）

## 1. 關鍵高度與幾何讀數（供 Blockside `ships[].geo` 與對照）

| 項目 | 體素座標（0.1 m/格） | 公尺 | 備註 |
|---|---|---|---|
| 設計水線 `waterline_z` | `z = 3` | 0.30 m | 主竹排 `z=0..2` 浸水（5,873 格，DWL 排水 6.02 t） |
| 船殼全長 LOA（`x`） | `18 .. 123`（106 格） | 10.6 m | 史料《海東賸語》三至四丈 |
| 最大船寬 Beam（`y`） | `35 .. 65`（31 格，`yc=50`） | 3.1 m | 史料《海東賸語》闊約一丈 |
| 雙翹頂點（艉／艏） | 艉 `z=8`（18,50）／艏 `z=10`（123,50） | 0.9 m／1.1 m | 雙端烤彎起翹 |
| 主筏面地板第一層空氣 `floor` | `24:7,33:7,34:5,98:5,99:6,105:6` | 0.5–0.7 m | `甲板-main`（`kind=deck, level=0, thick=1`） |
| 防潮木桶艙圍板頂 | `z = 8`（`x=50..74, y=44..56`） | 0.8 m | 竹編拱棚最高至 `z=14`（deco=1） |
| 單竹主桅 `桅-main` | `x=82, y=50, z=3..78` | 7.6 m | `kind=mast, mast=main` |
| 竹帆上桁／下桁 `pivot` | 上 `z=68.5`（`course`）／下 `z=24.5`（`lower`） | 6.85 m／2.45 m | 同掛 `sail=main, mast=main`，`rotate=0,0,-18°` |

## 2. 帆裝三段張帆表（`Ship_Rigging` §9.1）

| 帆裝段 | 張開的帆 | 備註 |
|---|---|---|
| `0` 全收 | （無） | 上下雙橫桁方帆：`lower` 向上收捲於 `course` 下方 |
| `1` 收帆 | `main`（`sail=course, set=1`） | 單帆船設 `set=1`，確保收帆與戰鬥帆均張開 |
| `2` 戰鬥帆 | `main` | 同上 |
| `3` 滿帆 | `main` | 同上 |
| 常駐旗幟 | `pennant`（`kind=flag, flag=pennant, nation=none`） | 桅頂朱紅金邊三角旗（不收、不算推力） |

## 3. 重量帳與材質評估（`Ship_Materials` §9.5）

- 結構總格數：`10,643` 格（船殼 `8,260` ＋ 甲板 `2,304` ＋ 主桅 `79`）
- 若採實心 `oak`（比重 0.70）：空載重 `7.45 t` ＞ DWL=3 排水量 `6.02 t`，會沉過設計水線
- 採竹木中空管腔混合材質 **`oak*0.55`**（等效密度 `0.385 t/m³`）套用於 `hull`／`甲板-main`／`桅-main`：
  - Blockside `admin.py disp`：`空載 4.1／標準 5／滿載 6 噸；載重 1 噸（16%）`
  - 完美貼合《TASK-1312》3–5 噸級定位與 `waterline_z=3`（0.30 m 吃水）

## 4. 共用元件複用與新建清單（`Ship_Setup` §2.1）

- **複用現有元件**：
  1. `basecamp-piragua-01m-oar` ×4（左右舷雙人／雙排共 4 支單人划槳，`scale=0.5, kind=oar, rowers=1`）
  2. `apex-one-punt-01m-anchor-stone` ×1（右舷石錨 `scale=0.5, kind=anchor, anchor=bower`，含 `ring`＋`hawse-S`）
  3. `summit-rocher-01m-crate` ×2、`summit-rocher-01m-barrel` ×1（木桶艙內貨品，`deco=1`）
  4. `basecamp-nightlamp-01m-lantern-01m` ×1（木桶艙前角漁火油燈 `scale=0.35, kind=light`）
- **因專屬竹筏特徵而新建**：
  - `pinnacle-tekpai-01m-deck-main`（墊高竹柵筏面＋防潮木桶艙）
  - `pinnacle-tekpai-01m-mast-main`／`yard-course`／`yard-lower`（帶竹節單竹主桅與雙竹帆桁）
  - `pinnacle-tekpai-01m-rudder`（竹筏長尾舵槳 ＋ 整合舵柄，`spin="rudder"`, model 名 `rudder-main` 避開 `metaRebase` 撞名）
  - `pinnacle-tekpai-01m-pole`（撐灘竹篙，預設 `render="pole"`＋`deco=1`）
  - `pinnacle-tekpai-01m-deco-awning`／`-deco-coil`／`-deco-fender`／`-bitt`（竹編拱棚、藤索圈、護舷墊、繫纜木樁，`deco=1`）

## 5. VXK 對帳指紋

- Sculpture 匯出 `pinnacle-tekpai-01m-assembly.vxk`：`10,643` 格、`checksum = c97f31c4`、`繩 13`、`帆 2`、`模型 24`（`網格 16 份`）
- Blockside `_cache/tekpai.vxk`（含 `ids` 發配 24 件模型＋3 件關聯 ID 後）：`config/vxk_lock.json` = `c:c765f4317d`
- Blockside 檢驗：`admin.py shipcheck --id tekpai` **`✗ 0　⚠ 0`**、`admin.py ladcheck --id tekpai` **`✗ 0　⚠ 0`**、`admin.py ropebind --id tekpai` 猜測 0 端／不靠 0 端

## 6. 硬骨帆的實體竹篾桿、船身改竹（TASK-1320，2026-11-18）

- Tim：「讓硬骨類似帆桁(有實體 帆會有一段黏在上面)」「用妳的台灣帆竹筏來做」「希望可以讓帆跟竹篾黏著」⇒ 規格寫在 Senate `Ship_Battens`。
- 新元件 `pinnacle-tekpai-01m-batten`（5×45×5、0.1 m、41 格竹＋竹節；固定點 pivot、arm-P、arm-S），主桅子作品掛 4 根 `batten-1..4`：
  meta `kind=yard, yard=batten, batten=m, sail=main, mast=main, rotate_z_deg=-18`；轉軸 z 59.7／50.9／42.1／33.3（`design/draft_battens.py`）。物件 id yard-3..6。
- 讀數：匯入檢查「竹篾」main：4／4 根有桿、綁住 84 點（4 列 × 21）、桿離那一列最遠 0.05 格；遊戲裡帆桁追風 56.9° 後竹篾列離桿最遠 0.044 格；落篷上帆桁往下 42.2 格、竹篾照比例疊下。
- 船身材質：Tim「另外船身材質可以改成竹子嗎」⇒ `hull`／`甲板-main`／`桅-main` 的 `oak*0.55` 換成 **`bamboo*0.55`**（`design/materials_meta.tsv`、`ship_meta.tsv`）。
  `bamboo` 是新加的材質（Blockside 材質表：比重 0.7（竹壁）、硬度 0.9、易燃 0.6；雕刻 `Sculpture/materials.json` 同 ID，只畫外觀）⇒ 比重跟橡木一樣，排水量不變（空載 4.1／標準 5／滿載 6 噸）；
  船殼硬度 ×0.55 → ×0.495（竹比橡木容易打穿，設計決定）、易燃 0.5 → 0.6。
