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
