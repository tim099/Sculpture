# 2026-10-15 潮墓號續造：吊索、支索、轉桁索與後桅帆頭

委託：Tim「繼續造船吧 GO」。Sirius接續TASK-0540／0546，所有實物改動走Senate CLI。

## 本輪資產

最新交付 `delivery/tidegrave_candidate_20261015.vxk`，SHA256 `76d945aca4f55556f5b952b7a5a3b4183cbe00a6f1b9d44f7359a56fd3bc5036`，398320 bytes。1,034,267格、checksum `4cb88a33`，302繩（原300全保留，新增2道robband）、10帆旗、116模型、19網格、17關聯。封裝對獨立CLI list逐格逐色0差；改一格反向checksum `31c2532c`。

本輪沒有加刪任何木料格、砲、梯子或模型；與前輪a599快照的voxel/color/order及全部模型網格相同。CLI結構1連通、空腔0、鏡像缺格/異色0、link overlap/clipped0；全部帆繩模型broken0。觀測圖 `../overlays/continued_rig_20261015.png`、總圖Rev06 `general_arrangement.png`，觀測側投影比較 `continued_20261015/rig_comparison.png`。

## 實修與過程

1. 前、主桅course lift改綁既有hounds；topsail lift改綁下一根桁以下的桅側實木格。8條繩原有粗細、色、分組與meta保留。
2. 12條main/fore shroud與4條backstay下端移至桅後舷牆實木；舊chain固定點保留給其他索。第一次路線造成四道最低ratline穿欄，獨立後驗抓到後將第一階比例.04提高至.065；主桅首批足點又穿高艉樓欄板，六個main足點向前1m，落在x245/265/285、z128的既有木料上。126條ratline全保留。
3. 10條上層brace改走鄰桅實體綁點，slack1，不再由上桁直落穿下桁。course brace原路保留。
4. 後桅topsail以兩道0.4m短robband，從原earing拉至source局部x8的帆頭點，讓帆離開桅身。只有這面帆兩個head位置改變；free clews、貼圖、其他角、fullness與meta保留。實作中CLI換corners會重設pin，整檔比對抓到後顯式補free，已記lesson。
5. 4條backstay上端由桅頂中心改到桅頂後側既有實木格，縮短沿桅附著接觸。此修正另有最終增量後驗。

## 獨立後驗的射程

報告與可重跑證據保存於 `continued_20261015/independent/REPORT.md`；最終輸入final_heads，前序快照與負向案例也保留。

- 8lift＋10brace各163個square-yard absolute角，body／十桁精測未見離開具體附著位置的穿越。自身臂端接觸弧長逐項保存，沒有泛豁免首尾三格。
- 16standing對十桁角度取樣無穿越；own square-yard全連續±.70rad的保守下界最小1.692607648格。最終4backstay另做163 square／323 gaff角增量檢查；桅端接觸縮為main≤2.936格、fore≤2.427格。
- 84道main/fore ratline靜態對body／十桁接觸0；實際game meshOcc/yardNear對standing/ratline端點沒有誤認桁，lift/brace只綁自身正確臂端。遊戲程式未改。
- mizzen-topsail完整正背面三角對body／十桁嚴格內部裁切正面積0，原(207,120,336)擦桅消失；兩sheet與兩robband對body0，只保留實際附著端接觸。
- 負向對照真實重現舊course lift穿topsail、topsail lift穿topgallant、shroud穿course及舊布面第96片的0.0123890263格²擦桅。

這些讀數沒有覆蓋全部302繩的model-aware動態、全部自由布連續動態、非同步各桁任意角組合、繩與所有非yard模型／彼此碰撞。TASK-0546最後一格及全船主單仍不冒簽完成。

## 接續入口

先讀本檔、CHECKPOINT及獨立REPORT。正式Blockside匯入與舊nav_deck_candidate覆核仍待遊戲端接入；舊候選不得直接套到搬家後持續變動的源碼。完整階段安全再生及各子單尚未簽清，不要盲跑build_structure.main/build_rig.main。repair_20261015_*是分階段有基線守門的修正工具，不是通用建船器；standing初始修法之後還有main_feet與backstay_heads修正，不能跳過後兩者。
