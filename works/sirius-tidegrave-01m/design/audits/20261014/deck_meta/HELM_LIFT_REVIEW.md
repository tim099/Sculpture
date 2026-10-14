# 舵手生成與梯子抬升追加審查

新增40_crew.patch與42_hands.patch中的CLIMB_LIFT=3已唯讀覆核，未修改作品或遊戲source。結論：**對潮墓號的窄範圍修補，靜態邏輯合理；最後runtime替補抵達與全身碰撞仍依各自實測結果簽收。**

## 舵手生成

舊40_crew生成以船中線CY±3及整船spar高度範圍找支撐，在右舷移位且樓高139的舵輪下仍可能找到floor116。只數2名ROLE.HELM不能證明站在舵輪旁。

新候選保留從wheel.bb[0]取船艉方向站位X，將Y改取wheel.c[1]，Z只允許wheel.bb[2]向下1至向上3格。仍呼叫既有standNear，保留實心支撐、14格頭空、blocked模型與taken避人檢查；找不到回null，由add拒絕生成，沒有回舊spar層的fallback。對本船wheel基底139、quarter第一空氣139的配置，這樣能排除floor116錯層。其他軍官、陸戰隊或桅頂生成未改動。

限制：standNear檢查的是點支撐和14格頭空，不能直接聲稱18/21格全身都無碰撞；也仍假設船艉方向為wheel.bb.minX後方，未新增任意旋轉舵輪通用站位。對潮墓號本輪未新增旋轉，沒有由此得到本船錯誤證據。

## CLIMB_LIFT 2→3

變更只抬升梯路lo/hi兩個中間點，foot/head及navSnap接地位置保持原樣，梯子實體與錨點沒有為了通過量尺而更改。L.steps仍由原lo/hi下方實體踏板取格，破壞判定未被放寬。與先刻好18高×7寬通道的方案相容；抬0.3m是人物爬梯腳路線調整，不是假稱腳始終接觸每級踏板。

但不能把這一數值推廣成所有船通過：抬高會增加頭頂與上層梯/天花板相碰的可能，因此只接受潮墓號七座梯的指定尺寸體掃掠結果。41_crew_art.js的CREW_H=2.1m（21格）是現行視覺人物高度；若18格機械體通過而21格sprite有重疊，需照實分開記錄。本文未把18格clearance冒充21格sprite無穿透。

小項：42_hands候選在mid計算旁的註解仍寫「抬0.2m」，常數已是3，應同步為0.3m並記其適用驗收範圍。

## 最後驗收需看到的證據

- 載入後兩舵手的實際home/pos在quarter支撐高度139、舵輪右舷附近，而非只看到角色總數2。
- 強制倒下兩位舵手後，callHands產生的helm job.lv對應deck=quarter（不能只報called總數）。
- 至少一位替補真正走完路線，到達job.spot後轉ROLE.HELM，存下位置及高度；queued/dispatched不等於補位完成。
- 七梯最新路線、CLIMB_LIFT3與最終VXK checksum相符的指定18h×7w守門結果；21格sprite未通過限制照實保留。

前一份CANDIDATE_REVIEW.md中游泳登船/無梯fallback/多站舵手的通用限制仍在，這兩個新增變更沒有宣稱解決它們。
