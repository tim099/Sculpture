# 2026-10-21 舵實體支承與設備簽收補件

原舵上端離船體2.5格，既有meta不能代替實體支承。本次增加固定環座與同軸活動短軸／止推肩，原7428格舵不改。肩下表面落在環座上表面，形成向上承壓面；固定座嵌接4個船格，短軸嵌接8個原舵格，這是明示接頭，不冒稱所有模型兩兩重疊為零。

## 驗證與讀回

- `DESIGN.md`、`proposal.json`是事前設計；4800/3528來源格、20格原色109守門清單與meta一同保存。來源1cm，父船10cm；顯式scale0.1。
- `independent_check.py`與`independent_report.json`是另一個subagent獨立公式／事件回播，非另一persona。新活動件完整360度包絡與接觸面證明；原舵±30度保守區間SAT，244區間呼叫、無實碰或未解區間。負控：去肩即承壓面積0，恢復孔格會命中7個軸圓柱候選。
- 獨立報告保留原文：它完成時父代理已刻孔，故`carve_guard_bad`列20個已空位置，且status仍寫proposal only。這項不是失敗後改成通過。落地前後的完整VXK逐格對照由父代理另外執行，見`after_readback.json`：指定20格原色守門完全吻合、沒有其他增格或改色、水線以下完全一致。獨立代理沒有執行落地後驗，不混稱為其結果。
- `after_readback.py`比較前一批`../acceptance_20261021/shared/current.vxk`與本件`after_bearing.vxk`：1033347→1033327格；239原模型（含網格）逐值未變，新增2；502繩與10帆逐值未變。實際來源事件回播4800/3528、模型變換、轉軸與控制meta吻合。
- `after_structure.md`是CLI落地讀數：單一連通、封閉空腔0、左右缺格／異色0、關聯重疊／裁切0。
- `spin_readback.cjs/json`在Node VM執行當前未修改的Blockside `26_spin.js`，餵實際匯出meta；舵與活動肩兩件成功綁定，固定座不轉，六組舵輸入均同軸同心同角。去掉活動軸meta的負控產生1個匯入警告。此為遊戲轉動函式的窄測，沒有執行完整載入器／畫面。
- `magazine_*`補齊雙庫各24桶、每庫2400磅、完整室內包絡、7×21×2門洞、門框與爆心meta；舊設備逐件避碰／支承、60個穿甲板孔、繩組與Credit在`../acceptance_20261021/hardware/`及既有`equipment_parts`，正式本機遊戲接入歷史證據在`../delivery/formal_game_20261016/RESULT.md`。

## 接續與限制

`after_bearing.vxk` SHA256：9a5780caee1df71a635e0b34b376933ec30e94996467a35e042c3b408959286b。它是本次作者交付候選，未替換Blockside已匯入資產，也未發布。原模型與繩帆完整保留；遊戲端下次匯入應使用本件並再跑verify/shipcheck。bearing_section.png是局部施工剖面，不是渲染或材料強度測試。

TASK-0549設備階段依本次證據可簽；TASK-0546最後一格與0540整船主單仍開著。0603雖由Tim於10-19後台結單，不能據此宣稱全部布料動態案例通過；維持Tim手動動態驗收邊界，不復開0603，也不代簽最後一格。

重跑腳本沿用原scratch絕對路徑與前批輸入；離線重跑須先將快照配置到所記路徑，不宣稱這是通用成船再生器。新件為Sirius自製；既有wheel/capstan/powder Credit basecamp、binnacle Credit summit不變。
