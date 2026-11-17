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

## 砲：32 門＋六種新砲（步驟 9，2026-11-16）
- Tim：「Build new gun types」⇒ 缺的威尼斯砲種一律做新的通用部件＋遊戲砲種（不拿別的口徑暫代）。
- 通用部件（draft_guns_venice.py ⇒ apply_gun_parts.py；0.05 m、模型 scale 0.5；座標照 Ship_Guns §4.1；青銅 168／箍 208、砲架 132）：
  | 代碼 | 作品 | 格 | 框 | 砲管 | 砲軸高 | 固定點 |
  |---|---|---|---|---|---|---|
  | ven20 cannone da 20 | -gun-ven20 | 3,029 | 15×54×24 | 2.6 m | 0.83 m | muzzle／breech／cascabel／train／trunnion／eye-aft／eye-fwd |
  | ven30c cannone da 30 | -gun-ven30c | 4,141 | 17×60×25 | 2.9 m | 0.83 m | 同上 |
  | ven14 colubrina da 14 | -gun-ven14 | 2,429 | 15×70×21 | 3.4 m | 0.73 m | 同上 |
  | ven30 colubrina da 30 | -gun-ven30 | 5,046 | 17×88×30 | 4.3 m | 1.13 m | 同上 |
  | ven3 falcone da 3 | -gun-ven3 | 1,181 | 11×40×19 | 1.9 m | 0.73 m | 同上 |
  | ven14p petriera da 14（叉架迴旋） | -gun-ven14p | 667 | 13×38×20 | 1.75 m | 0.73 m | muzzle／breech／cascabel／trunnion／pivot（作品 meta mount=turret） |
  每件 1 元件、空腔 0、x 鏡像差 0；遊戲數值在 plan.json guns.types（〔估〕）。50 磅（ven50）、6 磅（ven6）引用 meadow galea 的 corsiero、falcone。
- 32 門照 de Zuanne 1686（位置是設計）：艏樓下層 2 ven50（平行朝前、離中線 ±1.3 m）＋2 ven20（±36°）＋4 ven30c（側砲門 x 486／504）；艏樓頂 2 ven14（±18°）＋2 ven6（±45°）＋4 ven14p（±72°、x 510）；艉樓下艙 2 ven30（艉封板窗朝後）＋2 ven30c（x 128 側砲門）；艉樓平台 2 ven14（x 128）＋2 ven3（x 147）；兩舷舷牆頂 8 ven14p（槳與槳之間）。
- 為了砲改的船殼：艏樓裡舊船殼的舷頂與艏柱頭（z ≥ 32，1,364 格）刻掉（hull_cut_01）；艏樓下層前面四個砲門 z 36–45，50 磅兩門改成平行朝前（±12° 兩門在船裡撞在一起）；艉樓 x 128 側窗改成砲門（z 37–45、寬 7）；艉樓平台欄杆砲眼（x 125–131、145–149，z 55–58）；艉封板兩扇窗是 30 磅艉砲門、拿掉玻璃（玻璃 378 ⇒ 280）。
- 讀數（draft_place_guns.py、gun_layout.json）：32 門每一門的格心＋八角零碰撞（含先擺的砲）、砲口在牆外、砲口往前 4 m 射線碰到船 0；叉架迴旋砲每 5° 量：舷牆頂 8 門 ±70°、艏樓頂 ±72° 兩門 ±10°、x 510 兩門 ±20°。view：models_drawn 36（砲 32＋帆桁 3＋金飾 1）、models_broken 0。圖：stage06_guns_view.png。
- 遊戲砲種：Blockside 1c802fd（六種＋補 ven50／ven6 每發傷害）經 968a5af 合進 dev 並推（Tim 2026-11-16「Merge」）；Blocksail 4dc92be0 指標（沒推）。

## 底艙、彈藥庫、艙蓋、艉燈、羅經櫃（步驟 10，2026-11-17）
- 底艙梯改站在底艙地板上（draft_decks.py：梯腳 z 2 ⇒ z 6，原本落在中線那道一格寬的縫裡）；梯井往船尾移 4 格 ⇒ -deck 差分刻 70／-ladder-hold 重落 245 格，兩件改完匯出逐格等於新清單。
- draft_hold.py ⇒ apply_hold.py：
  - 底艙地板（子作品 -hold，關聯「甲板-hold」meta kind=deck、deck=hold、level −1、floor 100:6,454:6）：船殼裡 z ≤ 5 的空氣填實當壓艙、最上一格鋪板，20,009 格；頭頂到樑底 2.3 m。梯子「梯子-底艙」meta 補 hold.decks=hold,main。
  - 彈藥庫（子作品 -magazine，關聯「彈藥庫」meta kind=magazine、powder_lb 600）：艏樓正下方的底艙，x 455 橡木＋x 456 銅皮兩格厚艙壁、門洞 5 格寬（z 8–25）、松木地板 z 7；3,113 格。固定點 blast (487,160,21)、door (455,160,8)。
    火藥桶 6 個（憲法號 powder-barrel，scale 0.2，meta kind=powder、powder_lb 100）：底是 V 形（x 474 在 z 8 只剩 |dy| ≤ 3）⇒ 擠在靠門那 1.5 m：兩舷各兩桶＋中線兩桶；每桶量過腳下全實心、桶身全空氣。
    ⚠ 位置是設計：加萊賽彈藥庫實際在哪沒查到；照 meadow galea 放艏部（大砲都在艏樓）。
  - 底艙梯口艙蓋（子作品 -hold-hatch，16×7×1 局部座標；外部模型「底艙艙蓋」掛在 -deck，meta kind=door、open=up）：梯井每邊大一格、平貼 corsia 頂上一格 z 38；hinge-a (0,0,0) → hinge-b (15,0,0) 沿 +x、板往 +y ⇒ 往上掀。
  - 艉燈三盞（組裝件外部模型，三叉戟號船尾燈 scale 0.5、meta kind=light）：Tim 2026-11-17「艉燈可以加(不用按照參考圖)」⇒ 威尼斯旗艦式三盞 fanò（設計）：「艉燈-中」立在拱頂艙頂 (66.5,160.5,83)、「艉燈-P」「艉燈-S」立在艉欄杆兩角 (56.5,137.5／183.5,59)。⚠ +y 是 S 舷。
  - 羅經櫃（夜隼號 binnacle，scale 0.2、kind=binnacle）：-deck-stern 艉樓平台中線 x 140.5（舵手站的平台）。
  - 不放的（照實）：小艇（槳帆船的 schifo 多半拖在船後，Grevenbroeck 圖上甲板沒有艇 —— 拖的說法沒查出處）、絞盤（沒查到加萊賽起錨用不用絞盤）、廚房爐灶（槳帆船 fogon 的位置沒查到；划凳區的格子要不要算走路格沒量）。
- 讀數：組裝件匯出 366,358 格 ＝ 改前 composed 343,325 ＋ 地板 20,009 ＋ 彈藥庫 3,113 − 甲板 70 − 梯子 19（沒有被裁或重疊）；元件 1、封閉空腔 0、y 鏡像差 0；models_drawn 47（36 ＋ 桶 6 ＋ 艙蓋 1 ＋ 燈 3 ＋ 羅經櫃 1）、models_broken 0。
  check_ladders.py：5 座 foot／head 站得住；反向對照 head 抬 6 格 ⇒ 5／5 報。draft_hold.py、draft_decks.py 重跑同雜湊。
- 圖：stage07_magazine_view.png（彈藥庫子作品＋桶）、stage07_stern_lanterns_night.png（夜景，三盞燈亮）。

## 舵、舵柄、錨（步驟 11，2026-11-17）
- draft_helm.py ⇒ apply_helm.py。
- 舵（子作品 -rudder 1,023 格，組裝件外部模型「舵」pivot ＝ at ＝ 鉸鏈點）：槳帆船的艉柱很斜（後緣 z 12 ⇒ z 36 從 x 77 退到 x 53）⇒ 舵葉前緣一層一層貼著艉柱後緣走，
  弦長 z 2 的 1.4 m 收到 z 28 的 0.6 m、厚 0.3 m（水線下 19 層）；z 29–38 舵桿；舵柄 z 37–38 從舵桿往船頭穿過艉封板、伸進艉樓下艙到 x 72（約 2.2 m）。沒有舵輪（槳帆船用舵柄；Ship_Helm：舵柄畫在舵上不用補）。
  舵柄口：艉封板在舵柄經過那一段刻 79 格（7 格寬、z 36–39，masks/upper/hull_cut_02.vox.txt），讓滿舵時舵柄擺得開。
  meta kind=rudder、hinge (90.94, 160.5, 2)、axis (−0.7865, 0, 0.6175)（斜 51.9°）、max_deg 30、turn_axis=hinge、spin=rudder／spin_k 30／±30／lag 0.3；固定點 stock-top (51,160,38)，旁邊 8 格內船尾格 564。
  ⚠ 鉸鏈是拿前緣擬合的一條直線；艉柱是彎的 ⇒ 前緣離那條線最多 5.4 格（Ship_Helm 那條「丟掉離線 1.5 格的層」在彎艉柱上會丟到只剩 9 層，所以只丟舵柄兩層）。只是畫面：滿舵時舵葉前緣會離開艉柱一點。
- 錨（kotoko 四爪錨 grapnel，scale 0.8 ⇒ 約 1.9 m 高；組裝件外部模型「錨-S」「錨-P」，meta kind=anchor、anchor=bower、hawse）：掛在圓形艏樓外牆、艏樓中心算起 64° 方向、牆外 3 格，環 z 48、錨冠 z 29.2（水線上 0.8 m），錨爪沿牆的切線；hawse 在牆面 z 40（下層甲板高）。
  ⚠ 大小是設計（加萊賽的錨重沒查到；meadow galea 用 0.65）；Grevenbroeck 圖上錨掛在船頭外側。
- 讀數：船殼 222,493 ⇒ 222,414（刻 79）；組裝件匯出 366,279 ＝ 366,358 − 79；元件 1、封閉空腔 0、y 鏡像差 0；models_drawn 50（＋舵 1＋錨 2）、models_broken 0；舵格與現況（扣掉舵柄口）重疊 0；錨身 9×9 取樣點在船裡 0；check_ladders 5／5。draft_helm.py 重跑同雜湊。
- 圖：stage08_rudder_view.png（舵子作品側面）、stage08_anchors_view.png（艏樓與 S 舷錨）。

## 槳（步驟 13，2026-11-17）
- draft_oars.py ⇒ apply_oars.py：每舷 25 支、每支 6 人、14 m（plan oars）。元件照 Tim「儘量用已有的元件」引用皇家號的 galère 槳 apex-one-reale-01m-oar（13.15 m、7 人），
  scale 0.5 × 14 / 13.15 ＝ 0.5323（⚠ 槳柄、槳葉跟著粗 6%）；元件格清單複製在 masks/oars/ 只拿來量。
- 擺法：組裝件外部模型 oar-S01…S25、oar-P01…P25；pivot 在拱形槳門洞底往上一格（z 39）、舷牆厚度正中（S y 218.0、P y 103.0 ＋ mirror=y，照皇家號 y → 321 − y）；x ＝ 槳位格中心（160 起每 1.25 m）。
  meta kind=oar、rowers 6、side、dip_deg 12、stroke_deg 每支照量的。
- 讀數：槳的格心＋八角落在船的實心 0 點（50 支）；反向對照 S01 沉 3 格 ⇒ 只有它報 31 點。槳葉中心在設計水線上 0.25 m（全部一樣：槳門同高；水線匯入時照排水量再定）。
  槳座旁 8 格內船的格 ≥ 686；槳手 300／300 照「往下 8 格內腳下實心、頭上 14 格空」站得住（第 2 位站在船殼舷頂內緣 z 33–34，其餘站甲板 z 32）。
- 划槳掃掠（每 5° 掃 ±30°、槳葉抬 0／12°）：兩頭的槳柄（z 46–48）會掃到艉樓前牆 x 150、艏樓後牆 x 468 ⇒ 每支照 1° 找掃得開幾度寫進 stroke_deg：
  | 槳 | S／P 01 | 02 | 24 | 25 | 其餘 42 支 |
  |---|---|---|---|---|---|
  | stroke_deg | 9 | 24 | 22 | 5 | 30 |
  兩頭各一支只掃 5°／9°：Tim 2026-11-17「先保留小擺幅」⇒ 不拆樓牆、不少放凳。
- 靠泊沒驗（要進遊戲才量得到：槳伸出舷外 9 m）⇒ 步驟 13 那一格先不勾，步驟 14 一起量。
- view：models_drawn 100、models_broken 0、sails_broken 0、ropes_broken 0。圖：stage09_oars_view.png。

## 給遊戲的 meta 與匯入（步驟 14，2026-11-17）
- 船殼關聯 meta kind=ship、waterline_z=21；ropecheck 189 條、378 端全 ok。
- Blockside（Blocksail external/Blockside，自己的 worktree）`admin.py import --id galeazza` ⇒ `admin.py ids`（116 件發 id、寫回作品 Sculpture e8ef84c2）⇒ game.json ships[galeazza]：
  cfg.base 3.5（⚠ 估：加萊賽出名的慢）；geo spar [52,53]、qx 60、marines [0,0]、center 45、aim 36、aimZ [19,232]、deckAim [32,62]、rigAim [100,232]；crew top 0、marineGap 12；names Morosini／Corner／Pisani／Basadonna 的加萊賽、la nera、la rossa。
- 讀數：shipcheck ✗ 0、⚠ 15（第一輪 70）；ladcheck 5 座 ✗ 0、⚠ 4、甲板連通 ✗ 0；槳 50 支、槳手 300／300（遊戲算的，跟 draft_oars 一樣）；火藥 32／32 門走得到取用點（最遠 16.3 m）；
  舵跟著轉、操舵 舵 100%＋兩舷差動；艙蓋開口 70 格；showlod 41 型、預烘 50 型、srccheck 全過。ship_cards：509 t、52.9 m、一舷齊射 187。vxk_lock c:8794de1e6853af13e383ba378b625fcba0ab581c。
- 留著的 ⚠（看過、不改）：砲班 6 門缺 8 人（艏樓下層 50／20 磅、艉樓 3 磅）；樓梯 6 筆要從旁邊繞（梯腳背後是樓牆、艉樓梯頂前是 14 磅砲）；漏水：吃水再深 1.50 m（＋705 t）才從舵柄口進水。
- 合進 Blockside dev be052aa 並推（同時帶出 kiara f6ab413、pinnacle efa7df2）；Blocksail 896d49f1 指標＋battle.html 重套殼（⛔ 沒推）。

### 給遊戲那側填 geo 的高度（格 z，0.1 m）
| 什麼 | z |
|---|---|
| 設計水線 | 21 |
| 底艙地板第一層空氣 | 6（彈藥庫 8） |
| 主甲板第一層空氣 ／ corsia 頂 | 32 ／ 38 |
| 槳座 pivot | 39（槳葉中心 z 23.5） |
| 舷牆頂 | 48 |
| 艏樓頂、艉樓平台第一層空氣 | 52 |
| 艏樓胸牆頂 | 62 |
| 艉樓拱頂艙頂 | 82 |
| 帆桁轉軸（主／前／後；rig.json pivot_world_z） | 177／180／115 |
| 桅頂（主／前／後） | 232／194／146 |
| 船殼前後端 x | 52（艉）／632（衝角尖） |

## 交船（步驟 15，2026-11-17；Tim「1302 交船 GO」）
Ship_Game §10 換一艘船時的檢查表逐條對（✓ ＝ 有讀數；— ＝ 這艘不適用；⚠ ＝ 沒做或沒量，照實留著）：
| 條目 | 結果 |
|---|---|
| ropecheck | ✓ 189 條、378 端全 ok |
| 名稱、sub、meters_per_voxel、模型 scale | ✓ 組裝件「威尼斯加萊賽戰船」、船殼「… 船殼」帶 sub；28 件作品都記了 mpv、每個模型明寫 scale |
| 用已有的元件 | ✓ 火藥桶、羅經櫃、艉燈、四爪錨、槳、ven50／ven6 都引用；新做的：六種威尼斯砲（砲種表沒有）、舵（照本船斜艉柱）、艙蓋（照本船梯井） |
| 槳帆船 | ✓ 50 支、左右一樣、pivot／blade／seat、碰撞 0、cfg.base 3.5（⚠ 估）、槳手 300／300 |
| 槳從舷牆槳門伸出（§9.10.2） | ✓ 槳門真的開了洞、pivot 洞底＋1；跟 32 門砲的模型外框量過：靜止＋划動各姿勢 0 點（反向對照：同一支槳搬到 wp-S1 下方 0、抬到砲的高度 153） |
| 撞角 | — 衝角在水線上、不做衝撞（Tim「保持水面上」），不標 kind=ram |
| 爐灶 | — 沒放（fogon 位置沒查到） |
| 缺的砲種做成通用部件 | ✓ 六種，Blockside 砲種表 1c802fd |
| 模型＋meta | ✓ 砲、帆桁、火藥桶、羅經櫃、燈、錨、槳、舵、艙蓋都有 kind |
| 舵 | ✓ kind=rudder＋stock-top＋spin；操舵：舵柄在舵上 100%＋兩舷差動。⚠ 遊戲裡 __game.lostModels(0) 本小姐沒開一場量 |
| kind=ship、waterline_z、高度表 | ✓（上一節） |
| 梯子、樓梯自檢 | ✓ 5 座 ✗ 0；⚠ 4 座「正前方擋住要繞」看過、不改 |
| ratlines 繩梯 | — 三角帆桅沒有桅頂平台 ⇒ 沒標 climb |
| 彈藥庫火藥桶 | ✓ 6 桶；火藥 32／32 門走得到取用點 |
| 甲板 kind=deck、walk | ✓ 4 層（hold／main＋corsia walk／forecastle／quarter）、甲板連通 ✗ 0 |
| 三角帆桁 | ✓ yard=gaff＋rig=lateen＋fore |
| 材質 | ⚠ 彈藥庫的銅皮只是顏色（168），沒拆成 material 關聯；全船預設橡木 256 t |
| 窗的玻璃 | ✓ material=glass 280 格 |
| 空艙房 | — 沒有 |
| 砲零碰撞、迴旋砲角度 | ✓ 步驟 9 |
| 門與艙蓋 | ✓ 底艙艙蓋，開口 70 格 |
| 砲門蓋板 | ⚠ 沒做：艏樓、艉樓的砲門沒有蓋板（加萊賽的砲門有沒有蓋沒查到）；匯入檢查漏水那一行最先進水的是舵柄口（吃水再深 1.5 m） |
| 繩、帆端點；帆的 meta；帆裝三段 | ✓ broken 0；三段表在步驟 8。⚠ 遊戲裡 W／S 每一段本小姐沒看過 |
| 1 元件、空腔 0、link_overlap 0、鏡像 | ✓ |
| 產生程式重跑逐位元組相同 | ✓ 每一支 draft_*.py |
| vxk 跟遊戲那側對 checksum | ✓ 共用 _cache 的 galeazza.vxk 指紋 ＝ vxk_lock c:8794de1e6853af13e383ba378b625fcba0ab581c |
| shipcheck | ✓ ✗ 0、⚠ 15（每一筆在步驟 14 看過） |
| 靠泊 | ✓ Tim 在 Blockside dev 實測（2026-11-17「測試ok 辛苦了」） |
