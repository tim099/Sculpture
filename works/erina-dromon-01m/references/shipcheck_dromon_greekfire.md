# 匯入檢查：持火號（dromon）

> `python -I admin.py shipcheck --id dromon` 產生；規則在 `js/75_shipcheck.js`。開一場（跟憲法號隔最遠、打不到）跑 2 秒量的。
> ✗ 錯誤 ＝ 遊戲裡壞掉；⚠ 警告 ＝ 能動，但照退路或預設跑。修法裡的「造船規格」＝ `senate cmd doc --arg op=show --arg name=Sculpture_Shipbuilding`。

| 砲 | 站不滿的砲 | 船員 | 模型 | 繩 | 帆 | 桅 | 彈藥庫 | 甲板 | 梯子 | 艙房 | 錨 | 水線 z |
|---|---|---|---|---|---|---|---|---|---|---|---|---|
| 1 | 0 門缺 0 人 | 62 | 25 | 16 | 3（＋陣營旗 2） | 2 | 1（取用點 2） | 4 | 4 | 0 | 左模型＋ring＋hawse、右模型＋ring＋hawse | 11 |

材質（TASK-0616）：全船預設 橡木（oak）69,022 格、48.3 噸

平滑渲染（關聯 meta render=smooth，TASK-0616）：—

火藥（送藥手：取用點 → 砲尾藥箱）：1／1 門走得到取用點；最遠 16.2 m（siphon，送一趟來回約 13.3 秒）

迴旋砲／砲塔（meta mount；沒標 ＝ 固定）：—

砲塔層（關聯 meta kind=turret；殼、上面的砲與模型、彈藥箱跟著轉，前方 front 對準瞄準方位，TASK-0659）：—

砲帶的裝甲（關聯 meta kind=armor、mount；跟著砲轉、一格一格打掉，TASK-0631）：—

門、艙蓋（模型 meta kind=door、固定點 hinge-a／hinge-b；不擋人、打掉了開口才進水，TASK-0638）：—

照參數轉的子物件（模型 meta spin；舵、舵輪跟著舵角轉，只是畫面，TASK-0640）：rudder-S（rudder × 35°、-35°～35°）；rudder-P（rudder × 35°、-35°～35°）

裝飾（模型 meta deco=1；載入時拿掉、畫質「裝飾」開著才畫，不算重量、不被打，TASK-0682）：—

額外動力（TASK-0630；輸出物件 份量；主機／軸／鍋爐 照造船規格 §9.6；槳 §9.10，TASK-0691）：—（沒有 cfg.base）

動力件（TASK-0653；關聯 meta kind=engine／boiler／shaft／steampipe 的格子清單，照剩幾成、通不通算）：—

會轉的體素件（螺旋槳模型 meta kind=propeller 的格子；跟著軸轉、一格一格打掉、推力照剩幾成，TASK-0653 第二段）：—

**✗ 0　⚠ 0**

✓ 沒有發現問題
