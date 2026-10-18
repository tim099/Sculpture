# 潮墓號 2026-10-18 添裝獨立規格複驗

審查者：fittings_spec_review。唯讀作品；只在本審查資料夾輸出。未讀取或匯入作者 draft_fittings.py，未使用作者 diagnostics、reserved 作為判定依據。

## 結果（落地前）

- PASS：22 個候選外部模型，19 個 deco 純裝飾、1 個 boat、2 個 light；沒有 deco 與功能 kind 混用。爐灶、繫纜柱、砲彈架符合 Shipbuilding §9.9 可隱藏裝飾例子；水桶、工具箱無功能標記，亦可作純裝飾。
- PASS：7 個來源均直接引用現有作品。7 件來源 work.json 的 meters_per_voxel 均為 0.05；船格 0.1，scale .5 的六類保持原尺寸；燈 scale .75 相當於來源物理尺寸放大 1.5 倍。沒有另造相同功能元件。
- PASS：從 source_<id>.txt 的實心格獨立重建各 cube（含繫纜柱 90°旋轉），22 件 occupied bounds 全部吻合。工作艇 occupied 長 85.5 船格 = 8.55 m，meta length_m 8.53，誤差 .02m 小於一船格，來源格量化可解釋。
- PASS：從 baseline_parts.json 七座梯子 foot/lo/hi/head 自建保留區，22 件未侵入梯子空間。另以船中線 y111..130 的 1.9m 通道獨立檢查，沒有新增物穿過中心道。
- PASS：每個變換後實心 cube 的中心與八個內縮角在 baseline_body.npz 查格，22 件共計 0 個原船實心命中。本項為指定取樣檢查，不宣稱連續幾何或動態帆索完整證書。
- PASS：兩燈來源有 base/wick/bail，轉換後點位可計算。P wick=(122.375,114.375,176.625)，S wick=(122.375,128.375,176.625)；都未被標 deco。
- PASS：獨立檢視 deck_plan 原圖，船首朝右、艇在右舷中段、桶箱成雙列、燈在艉樓；圖上中央橫向動線未被新輪廓切斷。再由原圖像素反讀 2.4 px/船格、原點 (-164,30)，22 個輪廓四邊各取中點，在 ±2px 範圍找到各類元件預期邊色；88/88 邊吻合，並非只讀 placement 敘述。

## Minor

1. 圖紙只有數字序號，缺元件名稱圖例、座標刻度與各層分開的平面。定位可以靠 placement.json 配讀，但單張圖不完全自足。建議補一張 index/name 表及 x/y 刻度。
2. 艉燈 occupied 1.125×1.125×2.7m，比來源原物理尺寸放大 1.5 倍，屬較醒目的大型燈。這不違反縮放規格，但應在心得記明是船尾裝飾比例的選擇，避免日後誤以為等比轉換。

## Unverified（等待落地）

- CLI 實際新增數、模型 path/frame、固定點與 meta 必須以新 parts 匯出核對。
- 原來 models/links/points 是否逐字保留，須與 after parts 對拍。
- 原船實心格與各部件是否保持，須新 export 或可信前後雜湊；不能用 placement 的自述取代。
- 新 deco 無其他部件掛靠要看新增後完整 rig/model 引用；目前舊船不可能先引用尚不存在的新 path，但仍須匯出確認。
- 遊戲匯入、deco 開關、夜景點光源、實際人物路線與帆索動態未驗；不得以此報告聲稱完成遊戲同步。

證據：review.py（獨立檢查器）、review_data.json（逐件結果與圖紙像素驗證）。

## 落地終審（after_parts.json 已提供）

**規格與資料落地 PASS，0 fail。**

- 原 models 169 → 191，確切新增 22 件。169 件舊模型逐欄位完全相等，沒有刪除或覆寫。
- baseline 除 models 外所有匯出欄位（含全部 links、points、size、meters_per_voxel、船級 meta）與 after 完全相等。
- 22 個新增模型各找到唯一對應 path；weather / forecastle / poop 所屬框及完整 path 均正確。
- 22 件 work 來源、occupied box、meta 全吻合獨立規格；所有來源固定點逐個對拍相等，包括兩燈 base/wick/bail、艇 ring-aft/ring-fwd、桶箱 base。
- 另唯讀三層甲板 models.json，逐件核對 CLI 落地後實際 at/pivot/rotate/scale，22 件全相等；包含繫纜柱 pivot=[0,41,0] 與 rotate z=90，非僅用對稱外框推測旋轉。
- placement SHA256 維持 `364cfd988c58dc365984ea07b10bc9362285f83c2757808b88e535a2097d06b1`。
- 更新後 deck_plan.png 已重新親看：補齊 01..22 名稱、座標、scale、x 軸刻度、朝向及燈 2.7m 放大註記。原兩項 minor 已處理，不再阻礙理解；上緣標題與最左兩個刻度略擠，僅屬排版。

仍不包含：遊戲同步／匯入、deco 開關實測、夜景點光實測、動態帆索完整掃描。parts 證明原有部件資料保留；船殼逐格前後 hash 與體素不變由主工作者的前後匯出負責，這份報告沒有拿 parts 相等冒充體素相等。

終審證據：after_review.py、after_review.json；`issues=[]`。
