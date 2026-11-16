# 匯入檢查：威尼斯槳帆船（galea）

> `python -I admin.py shipcheck --id galea` 產生；規則在 `js/75_shipcheck.js`。開一場（跟憲法號隔最遠、打不到）跑 2 秒量的。
> ✗ 錯誤 ＝ 遊戲裡壞掉；⚠ 警告 ＝ 能動，但照退路或預設跑。修法裡的「造船規格」＝ `senate cmd doc --arg op=show --arg name=Sculpture_Shipbuilding`。

| 砲 | 站不滿的砲 | 船員 | 模型 | 繩 | 帆 | 桅 | 彈藥庫 | 甲板 | 梯子 | 艙房 | 錨 | 水線 z |
|---|---|---|---|---|---|---|---|---|---|---|---|---|
| 5 | 0 門缺 0 人 | 264 | 74 | 16 | 3（＋陣營旗 2） | 2 | 1（取用點 2） | 2 | 1 | 1 | 左模型＋ring＋hawse、右模型＋ring＋hawse | 13 |

材質（TASK-0616）：全船預設 橡木（oak）147,123 格、103 噸

平滑渲染（關聯 meta render=smooth，TASK-0616）：—

模型的材質反光（外部模型、裝飾的 meta material，只給畫面，TASK-0859）：—

火藥（送藥手：取用點 → 砲尾藥箱）：5／5 門走得到取用點；最遠 3.3 m（battery/falcone-P2，送一趟來回約 3.4 秒）

揚弾機（關聯／模型 meta kind=hoist、guns、trip、rounds，固定點 bottom／top；送藥手送到艙底接收處、吊上砲旁藥箱，TASK-0841）：—

迴旋砲／砲塔（meta mount；沒標 ＝ 固定）：—

砲塔層（關聯 meta kind=turret；殼、上面的砲與模型、彈藥箱跟著轉，前方 front 對準瞄準方位，TASK-0659）：—

砲帶的裝甲（關聯 meta kind=armor、mount；跟著砲轉、一格一格打掉，TASK-0631）：—

門、艙蓋（模型 meta kind=door、固定點 hinge-a／hinge-b；不擋人、打掉了開口才進水，TASK-0638）：1 扇：deck/hold-hatch（上下開、開口 142 格）

砲門蓋板（模型 meta kind=portlid、lid_of、固定點 hinge-a／hinge-b；本身是裝飾，交戰掀蓋推砲、沒事收砲闔蓋，只是畫面，TASK-0719）：—

後座（開火沿砲軸往裡退、裝填快好推出去；模型 meta recoil 格數，0 ＝ 不演；弩箭／火箭／石彈／希臘火不演；只是畫面）：沒有蓋板的砲 5 門（退 5–9 格）；有蓋板的 0 門（照 house）；不演：沒有；畫質「砲門的開關演出」每艘

自動裝彈機（砲模型 meta autoload、autoload_crew；砲班只要那幾個人、到齊就全速裝填，彈藥從揚弾機直接吊進來，TASK-0845）：—

砲身與砲座（座 ＝ 模型 meta kind=gunmount、mount_of；開火只退砲身、座跟著砲塔轉；砲 meta pitch ＋ 固定點 trunnion ⇒ 砲身照瞄準上下轉；只是畫面，TASK-0836）：—

照參數轉的子物件（模型 meta spin；舵、舵輪跟著舵角轉，只是畫面，TASK-0640）：rudder（rudder × 30°、-30°～30°）

裝飾（模型 meta deco=1；載入時拿掉、畫質「裝飾」開著才畫，不算重量、不被打，TASK-0682）：1 個模型（畫質「裝飾」開：畫）；不算重量、不被打

廚房（模型 meta kind=galley；廚師站在爐灶旁、預備水手當伙夫去領飯，TASK-0720）：—

額外動力（TASK-0630；輸出物件 份量；主機／軸／鍋爐 照造船規格 §9.6；槳 §9.10，TASK-0691）：槳 49 支（左舷 24、右舷 25）、槳手 196／196（每支 4 人）

動力件（TASK-0653；關聯 meta kind=engine／boiler／shaft／steampipe 的格子清單，照剩幾成、通不通算）：—

會轉的體素件（螺旋槳模型 meta kind=propeller 的格子；跟著軸轉、一格一格打掉、推力照剩幾成，TASK-0653 第二段）：—

操舵（TASK-0777；每支舵的鏈 舵令 ⇒ 舵輪／舵柄 meta kind=wheel／tiller（＋舵索 meta steer）⇒ 舵 kind=rudder、份量 helm_share；造船規格 §9.8.1）：舵令 ⇒ （舵柄在舵上）⇒ rudder 100%；差動：兩舷都有動力（舵令直接給兩舷，不經過舵輪）

樓梯自檢（TASK-0838；每座梯子的梯口有沒有洞、兩端站不站得住、走不走得出去；每座的座標與修法見 `reports/ladcheck_galea.md`）：1 座：全部 ✓（梯口的洞、兩端站不站得住、走不走得出去；繩梯不量）

甲板連通（TASK-1028；每層甲板的每一塊、艙底照梯子接不接得到）：2 層：都接得到（照尋路的走路格＋梯子）

超載極限（再多載幾噸、吃水再深幾 m 水會從原本就有的開口流進艙裡；門、砲門、槳門照遊戲的規矩算關著；js/75_leakcheck.js）：再多載 142 噸（吃水再深 0.70 m）⇒ 露天甲板（艙口、桅孔）（deck，左舷，離船尾 22 m）

**✗ 0　⚠ 1**

## ⚠ 警告

- **槳**：左右舷槳數不一樣（左 24、右 25）⇒ 全速時會往少的那一舷偏
  - 哪裡：`—`
  - 修法：兩舷照對稱擺，或確認是故意的
