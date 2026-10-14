# 新候選追加覆核

範圍：build_deck_nav_candidate.py、nav_deck_candidate/42_hands.patch及prepare_deck_meta.py。仍唯讀作品與遊戲source。來源hash在candidate_review.json；候選JS hash `28866a14e3e7724b6d933bfb23b3db2dc62493b637f40ed641b665d38b3b8c20`。本輪為靜態獨立審查及VXK再解碼；baseline/候選runtime由主agent另跑，這裡不冒充runtime pass。

## 已解決／可接受

- **pass** navLevelAt不依虛構zr改高度；先用deckFloor(x)限制該甲板真的存在，再要求點Z與floor相差≤3，並用實際navSnap支撐及|qZ−pZ|≤3比較。quarter無法在x575取得floor，forecastle可以，修正原本head誤歸quarter的根因。
- **pass** 有meta但找不到合理floor/snap時回−1，沒有偷偷回高度lvOf、也不把錯層混成通路。只有整份Ls皆無deck meta的舊匯出才保留舊lvOf退路。makeHands先建完所有L.N後才呼叫，沒有未初始化N讀取。
- **pass** navRegions、N.reg/N.regs/N.bigCells與區域路由保留，不再用舊patch擴層架構。
- **pass** cache key增加deck.path，能區分同高度或同zr但不同X floor範圍的甲板。
- **pass** 補砲/送藥手改用D.meta身份；10_ship.gunDecksMeta將同一hullDecks物件引用存D.meta，navLevels也取同一hullDecks快取，因此目前引用比較成立。找不到身份回−1且被reach gate拒絕，沒有高度fallback掩蓋錯誤。
- **pass** 操舵補位起始選層改位置。對潮墓號目前兩舵手同位置/層的配置合理。
- **pass** prepare_deck_meta延伸floor只處理已簽過的flat層，且讀floor−1實心格求X min/max，未讓導索柱頂改Z。我用自己的VXK解碼逐件重算，六個appliedFloor端點全部精確等於實物floor−1支撐範圍，Z仍66/91/116/139/139/165，thick仍2。前報告的尖端裁切minor已解決（僅標籤/cutaway覆蓋，未承諾尖端可走）。

## 還存在的路徑與範圍限制

1. **43_swim.board仍未改height-only選層**：用sh.deckZ[sh.weatherDeck][0]→lvOf。對其他「最高砲甲板恰為同高兩塊之一」的船，仍可能選錯甲板並無法爬回。潮墓號最高砲甲板是weather floor116，與quarter/forecastle139不同高，這不是本船已證失敗；若候選要宣稱通用同高甲板支援，需另修或明列未覆蓋。
2. **無梯子的home fallback仍height-only**：42_hands的`if(home<0) lvOf(...最低砲甲板zr[0])`未動。潮墓號候選若7梯接上便不走該分支；對最低砲甲板本身同高拆成兩塊、又沒有成功梯的船，身份fallback更可靠。候選runtime應核對home的實際deck身份，不能只數levels。
3. **舵手仍全用hd[0]一次選層**：替補for迴圈的每個hd[j].home沿用第一位的lvh；多處不同層操舵站時仍可能錯配。潮墓號目前兩舵手同站位不受此限制。要通用化應逐hd[j]選層，並檢查目標region可達。
4. **evacuate用zr判「上一層」**：不變的quarter128..139/forecastle140..152會把幾何同高的forecastle視作quarter上方。當前drownCheck對高於最低砲層的人直接落水，不走封閉低艙evacuate，所以沒有本船同高逃生失敗證據；未宣稱通用疏散正確。

以上是剩餘通用路徑，不應用來否定已針對潮墓號修正的梯子端點。也不能因10秒無例外就把它們當已驗。

建議runtime至少核對：7條梯名稱齊全、weather-forecastle.hi正指forecastle、6個deck身份都有walkgrid且forecastle/quarter不共用N、home為lower、舵手被替補時job.lv為quarter、同高region之間只能經梯/合法同層region路徑移動。10秒觀察若沒有觸發舵手缺額，僅能驗初始化與正常走動，不能簽操舵補位分支。
