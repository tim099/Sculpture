# 六層甲板 meta 獨立唯讀審核 — 2026-10-14

依 Sculpture_Shipbuilding.md §9.3；輸入為主agent新匯出的六子甲板VXK與measured.tsv。沒有修改作品、遊戲source或meta；未import作者/遊戲檢查程式。audit.py自行解VXK、逐柱量支撐/頂高，按現行35_decks.js及42_hands.js重算靜態端點歸層。此報告不宣稱遊戲runtime七條通道全部通過。

## 結論

**甲板高度及厚度量法 pass；六份meta直接接現行導航有同高甲板端點歸層 fail；舊七梯patch已過時。** 建議可以依這六層的真實高度標meta，但標後不能結清「七梯runtime通達」，需遊戲端修同高甲板選層並實測。

| deck / level | floor / 測量X範圍 | 本件實際X外框 | 結果 |
|---|---|---|---|
| lower / 0 | 66；124..583 | 124..586 | 高度pass；艏尖15柱未在floor範圍 |
| upper / 1 | 91；116..595 | 116..598 | 高度pass；艏尖15柱未在floor範圍 |
| weather / 2 | 116；109..605 | 109..609 | 高度pass；艏尖22柱未在floor範圍 |
| quarter / 3 | 139；104..240 | 104..240 | 高度及範圍pass |
| forecastle / 4 | 139；550..610 | 550..616 | 高度pass；艏尖24柱未在floor範圍 |
| poop / 5 | 165；104..180 | 104..180 | 高度及範圍pass |

六層thick=2符合絕大多數獨立柱連續2格地板。本件沒有舷牆混入高位讀數。quarter中確有兩根新導索柱，(225,106)/(225,134)頂的第一空氣為152；取樣dy±4/10/16/22/28不經dy±14，故沒有污染眾數floor。少數邊緣缺頂層而讀低一格（138/164等），眾數及中位數仍給正確樓板高度。詳細柱數見audit.json。

範圍minor：decks.py需要至少兩個指定dy樣本，尖細艏端因此被裁掉最多6格/0.6m。§9.3的floor範圍外代表「該層沒有甲板」，與這些24柱等實際幾何略不符；若要完整cutaway/層標籤覆蓋，建議floor端點延伸至本件實際地板X端點，保持相同Z。這些尾端寬度多不足1m、不是任何梯foot/head位置，不能據此推稱存在實際通行中斷，也不要當成已證明可走。

## 現行同高甲板問題（可由source與座標直接重現）

現行navLevels用相鄰deck的zmin/zmax中點切zr，重算得到：lower56..78、upper79..103、weather104..127、quarter128..139、forecastle140..152、poop153..185。

forecastle floor=139落在自己的zr140..152之外。makeHands仍呼叫lvOf(Ls,z)僅按高度選兩端層，故weather-forecastle.head=(575,120,139)被選成quarter。quarter的floor只在x104..240，它無法在x575附近提供navSnap；這條梯會在後續端點snap失敗時被略過。按35_decks.deckAt的(x,z)最近floor，該點正確歸forecastle。其餘13個foot/head與高度歸層一致。

不應靠把forecastle level改到poop之後或捏造高度來繞過；兩塊甲板真實同高。需要遊戲端對梯端點使用位置與deckFloor範圍選層，且相關職位/操舵選層也要覆蓋同高情形。舊patch中的position-aware精神仍有需要，但直接套舊patch不成立。

## cache與舊patch

當前navBuild cache key=`L.zr.join(',') + ':' + sh.models.length`，上述六層zr互異，**現況未發生quarter/forecastle cache共用**。若修同高range使兩者zr相同，這個key缺deck身份，將把不同X範圍/不同deckFloor的walkgrid共用；應加入deck.path/id，或確保不同deck永不共用。

舊nav_candidate/42_hands.patch依賴N.component/N.bestComponent和只保留最大元件的舊navBuild，現行已用navRegions提供N.reg/N.regs/N.bigCells並保留>=12點區域；舊patch不可直接套。當前的區域感知handRoute已能按「層:區域」走，應保留新版區域系統，僅針對現行deck meta選層缺口修補並重驗。

## 證據

- audit.json：六VXK來源hash、柱頂直方圖、meta、每層zr/cache前綴、七梯14端點逐點比較。
- audit.py：可重跑的獨立解碼與重算；只寫本資料夾。
- 導索柱高頂位置已自行解VXK確認，未只照measured.tsv自報。

未驗：改meta後的遊戲runtime、七梯踏板通達、動態破壞與碰撞。這些需後續fixture針對當前source與最後匯出實測。
