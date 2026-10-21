# TASK-0550 裝飾獨立唯讀複驗 — 2026-10-21

輸出根：`D:/Unity/Valhalla/scratchpad/sirius-tidegrave/acceptance_20261021/ornament/`。依 Sculpture_Blueprint_Build §6.6；未 import 作者檢查器或設計模組，未更動作品、既有程式或任務。只讀 events、原設計清單、cache、links/models、PNG 與既有報告。cache 僅作交叉比較，實物幾何由 events 獨立重播。`audit.py`、`models.py`、`design_sheet.py` 可直接以 Python -X utf8 重跑。

## 結果

| 項目 | 實測 | 判定與範圍 |
|---|---|---|
| 當前裝飾 | 三筆事件 31405 + 340 + 23 = **31768 格**；bbox 83..682 / 52..188 / 34..231 | 與 20261014 acceptance_notes 的 31768 格一致 |
| 結果帳 | events 對 cache，以及三份原設計 union：缺 0、多 0、異色 0 | 可簽。三份清單各無重疊，順序及 SHA 保存在報告 |
| 左右鏡像 | y ↔ 240-y，缺格 0、異色 0 | 可簽 |
| 空腔 | 裝飾局部 6 鄰接空氣洪泛，封閉空腔 0 | 可簽；不是防水體積檢查 |
| 連通與接船 | 裝飾自身 **219 元件**，219/219 各直接 face 接到現況其他 link 格；接觸格 2743，無根元件 0；與其他 link 重疊 0 | 可簽；219 是子件分散元件，不能誤寫成整船浮空 |
| 模型避碰 | **239/239 模型、31 source 作品**，逐來源 voxel cube 真轉換；與裝飾正體積碰撞模型 0、pair 0；unverified 0 | 僅當前 neutral 靜態外部模型，未涵蓋動畫、帆面及繩管 |
| 舊圖紙 | `design/ornament_stern_cell_plan.png` 5954 非背景像素，正好等初建 31405 格投影；對當前投影少 44 像素；正確 RGB332 材質帳差 **5998 像素** | 舊圖只可作初建歷史圖。uint8 乘255的溢位仍在此圖，不能冒充現況完整圖紙 |
| 新設計 union 圖 | 後視5998、側視4164、俯視4909像素；各從 PNG 像素出發對事件投影缺 0、多 0、異色 0 | 三視原創細格圖；不是從實物 cache 回填假設計 |

其餘 link 作品由現況 events 重播，16 links 合計 1001579 格，加裝飾後 1033347，與 root 提供的現況 CLI 共用匯出數一致。來源三份清單為 `ornament.vox.txt`、`ornament_root_correction.vox.txt`、`raised_flag_staff.vox.txt`，各新增 31405、340、23 格。`ornament_plan.json` 的 new_voxels=31405 明確只是初建值，並非當前值。

模型轉換依雕刻文件公式 `at + Rz Ry Rx · (scale ⊙ mirror(p-pivot))`，再加所在 link 平移；全部 source events 均可重播，逐 source 與 cache 占用差 0，沒有 nested links/models 需要額外展開。以模型每顆實際 source cube 轉換後的外接球查找裝飾 cube，所有 baseline pair 距離已超過半徑和，故 narrow SAT 不需執行；這是逐 source cube 幾何的排除，不是只看整模型 bbox。任意轉角的碰撞 classifier 為 OBB vs unit-AABB 15軸 SAT，排除面接觸（1e-8）。

## 真正負向對照

- 固定舊圖紙像素 probe `(Y,Z)=(87,164)`；把**全部實物後視投影** Z+3，最近格中心距離由 0 報 **3.0**。移的是實物，不是 datum。
- 把實物一格改色，結果帳報異色 **1**；刪一個非中線格，鏡像缺格報 **1**。
- 加 `(0,0,0)` 浮空格，連通元件 **219 → 220**。
- 在實物 occupancy 中加入以 `(200,120,200)` 為空心中心的26格小殼，空腔 **0 → 1**。
- 把當前**整個舵 source 模型 7428 格**平移 `(-8,-48,168)`，經同一個 broadphase / SAT 路徑，查到 **38 個正體積碰撞 pair**。baseline 模型保持不動。單純貼面對照回 false，完全重合回 true。

## 圖紙、視覺與逐格簽收限制

新圖紙由三份原設計清單 union 生成，保留來源順序與 SHA，不讀 cache 作設計。後視PNG hash `571014e84c6dcc21eeb0aca5c394ce0e5c564c26e4499236e8332e93726bf6a2`。後視契約：column=Y、row=239-Z，沿 X 最大 palette index 投影；另有側視 XZ、俯視 XY，各取被折疊軸的最大 palette index。0.1 m/格，鏡面 y=120、Z=0龍骨底、X+朝艏。獨立像素帳是從生成 PNG 的非背景像素出發對事件投影核對，亦檢查事件投影多出格與顏色。本輪未重算所有原創幾何參數；原創細圖可讀與逐參數重新建模是不同的要求。

`ornament_design_union_side_annotated.png`、`ornament_design_union_top_annotated.png` 有座標與尺度；`ornament_design_union_bow_detail_X560_704.png` 顯示齒狀艏欄的X向升降、牙齒與下托，亦標尺度與datum。這些是設計union格圖，不是render。對應未加圖框的raw PNG有完整像素帳，避免註字被當部件像素。側視圖已目視檢查，艏齒輪廓清晰。

舊 PNG 的44個缺圖座標與對應當前 voxel 在 `drawing_extra_pixels.json`。`readback_projection_rgb332_x3.png`、`readback_projection_extra44_red_x3.png` 是**事件實物讀回示意圖**，後者紅點表示舊圖未畫的44像素；兩者不冒充原設計。與此不同，新 `ornament_design_union_stern_cell_plan.png` 由凍結設計清單生成。

唯讀目視了既有 `design/continued_stern_20261014.png`、`overlays/ornament_stern.png`、`overlays/ornament_bow.png`：艉廊、高拱、珊瑚枝、旗竿、艏端牙形輪廓及側殼海蝕附著可辨認；破星盤與艉窗在全景中尺寸偏小，建議近艉圖再簽其細節。來源界線見 `design/references/README.md`：電影模型觀察高艉廊／尖頂／分枝冠，破星盤與潮痕為 Sirius 原創。這是核對現有 provenance 敘述，本輪未重新瀏覽外部來源照片。過程日記存在於 `journal/20261014_validation.md`，已照實說明為事後重建紀錄，不冒稱遺失的當日逐步心得。

TASK-0550 三個驗收格：

1. **細圖／來源界線：可簽。** 原創來源界線可讀；新增設計 union 後/側/俯三視細圖與艏齒放大圖有完整格與色帳、尺度與datum。未宣稱另做一份全參數重建。
2. **多角度可辨／全接船：連通可簽，細節視覺待近圖。** 219/219 元件直接接船證據完整；破星盤與艉窗的可辨性不能由 occupancy帳代簽。
3. **結果帳／對稱／空腔／模型避碰／複驗／日記：可在本報告的靜態 scope 內簽。** 證據完整；動態帆索與運行動畫另案，不把此項延伸為全船動態全過。

具體原始讀數：`report.json`、`models_report.json`、`design_sheet_report.json`。沒有對既有 20261014 報告做靜默修正。
