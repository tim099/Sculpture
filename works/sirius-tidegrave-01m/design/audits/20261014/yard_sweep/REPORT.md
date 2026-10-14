# 潮墓號帆桁掃掠補驗

目前已消除 crossjack／gaff 的木桁互穿；**帆索的 model-aware 避碰仍有四類未結項，TASK-0546 不宜全格簽收**。本 verifier 唯讀，未修改作品或遊戲。完整動態繩精測已停止，以下保留實測 scope。

## 快照與檢查範圍

- Before：`5e92885eb98c095b41f21d80e0f69e287206e55be7815fe27c6a4e8abc42f8d1`；1,036,066 格、checksum `bdd5856b`，已保存 `source.vxk`。
- After：`a5994eeeacbb1155776145e3ebc2e69bd743815b7574df45ca6eb58653bdaf73`；實際讀回 1,034,267 格，完整 checksum 在 `after.json`，保存 `source_after.vxk`。
- After 對 before 逐格逐色：只刪除 1,799 格，沒有新增或改色。只有 crossjack 模型的 origin／bbox／points 改變；298 條繩完全相同，兩條 `mizzen-topsail.sheet-P/S` 只有 pts 改變；只有 `mizzen-topsail` 帆 verts 改變；所有模型網格相同。
- 原先 voxel-only 後驗只證明繩／帆對 body 格的靜態讀數；此次新增 **模型實心幾何**、旋轉後的桁、以及實際遊戲綁端邏輯，兩者不能混成「全帆索通過」。

## 實際角度與方法

實讀遊戲 `30_rig_physics.js`，使用其原函式 `braceYards`，沒有採用註解近似值。方桁 absolute angle 為 ±0.70 rad（±40.107°）；gaff／boom 兩側穩態 0.14..1.40 rad（8.021°..80.214°），換邊過渡包含中間角度，因此木桁 body 掃完整 ±80.214°。作品角 square r0=−18°，故其額外 rot 範圍 −22.107°..+58.107°。速率上限 0.14 rad/s（8.021°/s）。物理關閉回作品角，也有檢查。

`BRACE_HYST` 實際值 2.7 rad（154.7°），註解寫 25°；未改遊戲，數值差異列為程式文件問題。

原始 source work events 重播成十桁實心單位格；按實際 pivot／r0 轉成 OBB。與匯出模型外框最大差 <0.005 格。桁對 body 用精確 OBB／單位盒 SAT；0.25° 取樣間再加最遠頂點位移界，保守涵蓋連續掃掠。所有 exact／包絡接觸都只在自身桅中央 sling／jaws 附著候選區（xy 半徑 ≤8 格、z 距 pivot ≤12 格），沒有遠端船殼或裝飾碰格。這個分類不宣稱木料結構工程驗收。

其餘 106 個非 yard 模型最高 z=159.8；最低 yard（boom）實體從 z204 起。繞 Z 不改高度，因此它們與桁全連續角度分離。

綁端採用遊戲原 `meshOcc`／`yardNear`，不是依繩名猜測；繩變形照 `yardRopes` 的弧長權重插值。Before 共 970 個實際函式產生的穩態／限速過渡狀態，做 1,245,641 次精確 capsule／source cube 測試。這是取樣狀態的真碰撞證據，不是自由布物理的連續時間通過證明。

## 已修正並後驗

Before 的 crossjack／gaff 在 350 個同時可達狀態相交。例如風 ψ=0° 時，crossjack=0°、gaff=−80.214°，在世界約 `(204.5,132.5,255.5)` 等格互穿，離中央附著區甚遠；ψ=−87° 時最多 28 個 crossjack source cubes 相交。

After crossjack 中心實讀 z224.5，實體 Z **223..226**；gaff **229..317**，boom **204..207**，間隔分別 3／16 格。因此即使三桁不同步、任意連續旋轉，木桁也不再相交。此結論是 Z 分離證明，不依賴重跑 970 個狀態。After 模型輸入等同已測的 z224.5 候選；遊戲 `yardNear` 對 gaff jaws `(205.5,120.5,230.5)` 正確認為 gaff。z226.5 雖有 1 格木料間隔，卻會誤認成 crossjack，所以最終採 z224.5。

兩條改變的 mizzen-topsail sheets 對 after body 的靜態完整 capsule 內段碰格皆 0。該帆對十桁的嚴格內三角碰撞為 0；帆頭邊仍附著 topsail yard。自由布掃掠與移位後 crossjack 對全部索具的 970 狀態表沒有重跑，列為未驗範圍。

## 四類未結項與最小後續方案

1. **低層 lift 穿上層桁。** Main／fore course lifts 直接拉到 `main/truck` z510.5／`fore/truck` z465.5，會穿兩層上桁；topsail lifts 也穿 topgallant。Before 共 12 個這類桁／lift 接觸對；初始作品角已存在。例 `main-course.lift-P` 穿 main topsail 世界約 `(338.50,68.19,374.5)`，沿繩約133／280格，屬中段，不能當端點。最小施工順序：course lifts 先改到現有 `main/hounds-P/S` z295.5、`fore/hounds-P/S` z275.5，兩者均在本桁頂與下一桁底之間；topsail lifts 新增實體桅側繩環，候選 main z420.5、fore z380.5（分別在377..459、342..419間）。這些是 **Z 安全區與施工候選**；固定點實體支持、桅側接觸、全部轉角及繩路仍須實修後驗，不能視為已通過。
2. **Standing rig／running brace 穿桁。** Main／fore shrouds 在 course 桁高度有離 pivot 約14..18格的真中段穿越，初始角即有，不屬 sling。例 `main-shroud-P0` 對 main course 世界約 `(349.94,103.38,249.5)`；fore 例 `(504.60,105.59,234.5)`。另 backstays／高層 braces 也有碰桁候選，逐對在 `rope_sweep.json`。先處理 main／fore course 的 chainplate／導索路線，讓索在該高度保持於整個 ±40.107° 桁包絡之外；可用「桅後方導索點＋實體支持」而非刪索。直線投影安全界可由 `|dx| > tan(0.70)*|dy| + (source桁半寬+繩半徑)/cos(0.70) + clearance` 初篩，再檢查支持與弧線；沒有宣稱某個尚未實測的新錨點已安全。
3. **Ratline 幾何誤綁。** `main-ratline-P-18` 第0端 `(349.9,103.62,248.74)`、`main-ratline-S-18` 最末端 `(361.1,137.1,248.74)` 被認為 main course；fore 對應端 `(504.9,105.86,234.34)`／`(516.1,133.46,234.34)` 被認為 fore course。這四端的 ends 都是 `rope:<mast>-shroud-.../0.72`，設計上附於 shroud，追風時卻被 `yardNear` 拉走。給遊戲作者的最小語意修正：`ropeYards` 先尊重 ends；以 `rope:` 指向 shroud 的端禁止由幾何 fallback 認領為 yard，保留母繩關係；缺少 ends 才 fallback。不要刪 ratline 實體。此處未修改遊戲。
4. **Mizzen topsail 舊有一格擦桅。** 嚴格內片仍碰 body `(207,120,336)`。精確三角形裁切證明 before 已存在：2片、合計0.35520854格²；after 剩1片、0.01238903格²，約 **1.24 cm²**。不是此次 crossjack 移位新增，也不能填0。下一步可從帆頭支離索／robband 與小幅布面離桅量處理，保留實體附著，重模擬後用同一 probe 驗；不刪桅格來消數字。

Before 表共115個有接觸的桁／繩對，76對含按「首末3格弧長」規則分類的內段候選；其中少數 own-sheet／boom-tip 延長附著可能需要人工分類，**76不是76項已判定缺陷**。10個 crossjack 接觸對因其移位而失效，不沿用為 after 數字；其餘幾何／曲線未改的證據保留。沒有宣稱 after 的全帆索 model-aware 避碰通過。

## 證據與可重跑檔案

`MANIFEST.json` 列每檔 bytes／SHA256。主要小型證據：`sweep_summary.json`、`rope_sweep.json`、`after.json`、`cloth_delta.json`、`crossjack_candidates.json`、`crossjack_binding_candidates.json`、`game_bindings.json`。

大型 `sweep.json` 原始長度 **26,844,588 bytes**，raw SHA256 **a5cf083516b3878594345c7b4d57073c91be4f794be14908da0b84950ae4a611**；可 gzip 收存，保留此 raw SHA。`body.npy`（16.6MB）、`input.json`、`after_input.json`、`states.json` 是可重建 cache，不必收進作品。

可攜重跑最小依賴：Python＋numpy、Node；兩份 `source*.vxk`、`yard_sources.json`、`guard_owners.json`、`vxk_decode.py`、`geometry.py`、`game_snapshot/` 與下列 scripts。Source yard cells 是當時 events 的獨立重播快照，含來源 event SHA；guard owners 是當時逐格查 events 的標籤快照。Portable decoder 明列 VoxelKit 解碼格式來源，未 import 作者 verifier。

```text
python -I -X utf8 rebuild_inputs.py
node game_bindings.js
python -I -X utf8 sweep.py
python -I -X utf8 rope_sweep.py
python -I -X utf8 after.py
python -I -X utf8 cloth_delta.py
```

前兩行及 sweep 會重建必要 caches；完整 rope_sweep 需數分鐘。本次不再執行完整重跑。候選可另跑 `candidate_crossjack.py --z 224.5` 與 `candidate_binding.js`。`game_snapshot/10_ship.js` 僅保存未變的 yardNear／ropeYards 原函式摘錄：完整檔案在審核期間因其他功能改動而換 hash，原全檔 hash 與摘錄界線寫在 `source_provenance.json`；另外兩個遊戲檔為原全檔快照。
