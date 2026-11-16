TASK-1302 威尼斯加萊賽戰船 galeazza（約 1666）。Tim 2026-11-16：「1302 GO 可以多查一些參考資料 希望造最大型 且船頭有圓形炮樓」。
原型：de Zuanne 1686（BL Add MS 38655）的 galeazza，29 passi × 25 piedi × 9 piedi（50.42 × 8.69 × 3.13 m），是查得到最大的 17 世紀威尼斯 galeazza。史料表在單上與 design/references/research_2026-11-16.md；附圖在 design/references/。
design/plan.json 每個數字標出處或「設計」。線形程式 lines.py 抄 meadow galea（同一套槳帆船線形）。

## 船殼 01＋02（2026-11-16）
- 船殼 01（draft_hull.py）：外殼兩格厚，109,697 格；平底＋飽滿圓舭，船尾頂留寬平台給艉樓。
- 船殼 02（draft_upper.py）：舷外槳架外緣縱樑（外伸 1.5 m，1592 galie grosse）＋1.6 m 高舷牆、25 個拱形槳門（每舷，x 160 起每 1.25 m）；圓形艏樓（半徑 5.8 m、與舷牆外緣齊、懸出艏柱 2.2 m；下層 4 個前砲門＋兩舷各 2 個側砲門、頂層胸牆 8 個砲眼；z 29–62）；艉樓側牆、艉封板與窗、平台下艙的前牆、紅頂金肋的拱頂艙；衝角（艏柱 → x 632，水線上）＋托衝角的膝材（經艏柱接到龍骨，Tim「撞角是否可以連接龍骨」）。114,716 格。
- 砲位（de Zuanne 32 門）：6 門 30 磅 cannone 舷側放不下（槳手站在槳架上）⇒ 4 門放艏樓下層側砲門、2 門放艉樓艙側窗（Furttenbach：艉樓下艙可並排兩門）；8 門 14 磅 petriera 是舷牆頂的迴旋砲（不開門）。
- 落格：缺 0／多 0／色差 0（224,413 格）、1 元件、封閉空腔 0、鏡像差 0；反向對照：設計推 +3 格 ⇒ 缺 47,634。兩支產生程式重跑同雜湊。
- 圖：sheet01_lines.png（線形）、sheet02_layout.png（側／俯＋槳位、桅位、艏樓砲門）、stage01_view.png。

## 甲板、corsia、划凳、梯子（步驟 5，2026-11-16）
- Tim：「保持水面上 繼續造甲板」⇒ 衝角不動。
- draft_decks.py ⇒ 子作品：-deck（主甲板板 z 31＋樑 z 29–30＋corsia 實心 z 32–37、兩頭一階 z 34）、-benches（每舷 25 張，凳面 z 34）、-deck-bow（艏樓頂 z 51＋樑）、-deck-stern（艉樓平台 z 51＋樑）、-ladder-bow／-ladder-stern（S 舷一座，P 舷 mirror=y 關聯）、-ladder-hold（corsia 中線往下到船底，貨艙梯）。apply_decks.py 落地。
- 甲板 meta：main level 0（floor 54:32–578:32、walk 走 corsia 頂、walk_y 154:166）、forecastle level 1、quarter level 2；梯子 kind=ladders＋`<名>.decks`。
- 梯子：每階升 3 格、往前 2 格（踏板＋豎板），艙口只開在站上去頭會撞樑的那幾階；head 在 hi 正前方 2 格。
- 讀數：組裝件匯出 337,842 格對設計（含兩座鏡像梯）缺 0／多 0／色差 0；元件 1、封閉空腔 0、鏡像差 0。check_ladders.py：5 座 foot／head 站得住、梯頂空柱 0、⑦ 不適用（head 在中線）；反向對照 head 抬 6 格 ⇒ 5／5 報。正式的 admin.py ladcheck 在步驟 14 匯入後跑。
- 圖：stage02_decks_view.png。

## 裝飾與窗玻璃（步驟 6，2026-11-16）
- draft_deco.py ⇒ 玻璃 378 格（子作品 -glass、關聯「艉樓窗玻璃」meta material=glass，色 155）：艉封板兩扇內側窗＋兩舷側窗 x 68／83／98／113；第 5 扇（x 128）是 30 磅 cannone 的砲門，不裝玻璃。
- 金飾 873 格（子作品 -gilt ⇒ 組裝件外部模型「金飾」meta deco=1，可隱藏）：艉樓拱頂艙後壁外的聖馬可有翼獅（紅底圓盾、金獅、光環、書）＋圓形艏樓正面兩門 50 磅砲門之間的金框紅心徽飾。依據：Grevenbroeck 鍍金艉樓、紅金旗；Coronelli 版畫的聖馬可盾；MSN 模型艏樓正面雕飾。
- 船名不做：17 世紀威尼斯 galeazza 以指揮官姓氏稱呼（Lo Basso p.130 前後），沒有船名板可依。
- 讀數：組裝件匯出 338,220 格（模型不在格子清單裡）對設計缺 0／多 0／色差 0；元件 1、封閉空腔 0、鏡像差 0；玻璃鏡像差 0；draft_deco 重跑同雜湊。圖：stage03_deco_view.png。

## 三桅與三角帆桁（步驟 7，2026-11-16）
- draft_masts.py ⇒ rig.json＋masks/rig/；apply_masts.py：每根下桅一件子作品（組裝件關聯 mast-main／mast-fore／mast-mizzen，meta kind=mast、mast=main｜fore｜mizzen），帆桁一件子作品 ⇒ 桅子作品裡的外部模型 yard-*（kind=yard、yard=gaff、rig=lateen、固定點 pivot／peak／fore、sail=<桅>-lateen）。
- 尺寸查不到 ⇒ 照 meadow galea 的相對座標放大（主 ×1.19、前 ×1.15、後 ×0.66），基準 corsia 頂 z 38：主桅頂 z 232、帆桁 34.4 m（轉軸 z 177）；前桅頂 z 194、20.8 m；後桅頂 z 146、19.1 m。主帆 clew 挪到 x 185 讓開後桅。
- 讀數：組裝件匯出 345,097 格對設計缺 0／多 0／色差 0；元件 1、封閉空腔 0、鏡像差 0；三根桅腳都踩在 corsia 頂、跟現況重疊 0；draft_masts 重跑同雜湊。圖：stage04_masts_view.png。

## 帆、索具、旗（步驟 8，2026-11-16）
- apply_rigging.py：三面三角帆（peak／tack 釘在帆桁模型的 peak／fore、clew free 由 sheet 拉住，帆布 #f2ead8 素白）；每根桅每舷 3 條 shroud（hound → 舷牆頂）＋ratlines 橫繩組（step 4，不標 climb：桅上沒有站得住的平台）；tack／sheet／halyard 各 3；艉樓旗桿（子作品 -flagstaff，關聯「艉旗桿」）掛聖馬可國旗（貼圖照抄 meadow galea 的 venice-ensign.png，meta flag=ensign、nation=venice）；三根帆桁 peak 各一面紅長旗（flag=pennant、nation=none；Grevenbroeck 帆桁頂的飄帶）。
- 帆裝三段（meta set）：
  | 帆裝 | 張哪幾面 |
  |---|---|
  | 收帆（1） | fore-lateen |
  | 戰鬥帆（2） | fore-lateen、main-lateen |
  | 滿帆（3） | fore-lateen、main-lateen、mizzen-lateen |
- 讀數：ropecheck 繩 189 條（含 ratlines 展開）兩端 378 個都綁好；view（風 4.5,−1.5,0）帆 7（3 帆＋4 旗）、sails_broken 0、ropes_broken 0、models_broken 0；link_overlap 0。圖：stage05_rig_view.png。
