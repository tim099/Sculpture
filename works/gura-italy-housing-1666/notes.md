義大利 1666 的通用城市住宅（Tim 2026-11-15：「是否可以參考菜單概念（可以混合多地區菜單） 讓住宅也可以混合多風格 例如 威尼斯可以混義大利風格住宅？（或其他通用風格） 讓種類更豐富」⇒ 選 A：新雕一套通用義大利住宅；TASK-1291）。

- 遊戲那一側：Blocksail 的風格 `italy`（world/areas.js TOWN_STYLES，fall es）；威尼斯那一筆 `houseMix: { venice: 7, italy: 3 }`（TOWN_BUILD §2.2）；tools/townmodels.py 的 gura-italy-housing-1666。
- 產生程式在 design/：icommon.py（調色盤、牆、粗面石、畫上去的白框白線、石樓層線、深木屋簷 gronda、煙囪、涼廊、井、院牆）、iparts.py（七件部件）、italy.py（低三型＋淺版小版、中高四型、超高五種、配色）、build.py、apply.py（抄自 gura-venice-housing-1666）。
  重產：python -I -X utf8 -B build.py <design>；先跑 _probe.py（出框、撞格、浮空）；落格：apply.py <design> create／stamp／anchors／links／models／check。
- 兩種地方做法混在同一套：托斯卡納（筒瓦四坡＋深木屋簷、serena 石框、跪窗、粗面石、頂樓涼廊）與利古里亞（窄而高、畫白框白線、深色基座帶、黑石板門框、石板頂、一樓拱頂店鋪）。
- 照史料避開的時代錯置：百葉 persiane（18 世紀末起）⇒ 實心木窗板 scuri；機製瓦（1841）⇒ 筒瓦；超高不超過 7 層（熱那亞今天的 7～8 層有一部分是 18～19 世紀加蓋）；18 世紀才流行的粉藍、粉綠不用。
- 第一版撞過的：頂樓窗頂到深木屋簷（木椽、木板底）⇒ 頂樓天花上面多留 0.6 m 的牆（屋簷底下那一段）；石板色 109／145 偏橄欖綠 ⇒ 110／146（藍灰）。
- 〔推〕沒出處、照建議值：層高（一樓 3.7、樓上 3.2 m；超高一樓 3.9、樓上 3.0 m）、屋簷深 0.8～1.2 m、窗 0.9 × 1.7 m。

---

以下是史料整理（小幫手 2026-11-15 查的；沒標記 ＝ 讀過全文、〔摘〕＝ 只讀到搜尋摘要、〔推〕＝ 沒有出處的推論）。
沒讀到的：Mantovan、Disegnarecon 的 Ghetto 論文、Calabi／Concina《La città degli Ebrei》、Vecchiattini 2022 ⇒ Ghetto 的樓層淨高、熱那亞單一地塊的面寬都沒有實測公尺數。

## 總結論
- 熱那亞 1666 年 caruggi 兩旁多半 5～6 層；今天常見的 6～7 層（偶有 8）有一部分是 18～19 世紀加蓋 1～2 層。https://www.acompagna.org/rivista/2016/1/p16.pdf ⇒ 超高上限 7 層〔推〕。
- 單一地塊很窄：佛羅倫斯中世紀地塊面寬 9 braccia ≈ 5.25 m（https://www.yourwaytoflorence.com/db/brunell/houses.htm）；熱那亞一個 tavola ≈ 35 m²、臨街窄往裡深（Poleggi，https://memoriedigitaliliguri.it/Docs/Biblioteca_Digitale/SB/396b22c37e8bbc6c44c30828fc127900/Estratti/8eee4b2a5a839d707d029f91b0638b5b.pdf）⇒ 寬的超高拼 2～4 個 4.5～6 m 的開間、各自一色、高低差一層〔推〕。
- 時代錯置：百葉 persiane 18 世紀末、19 世紀才普及（https://it.wikipedia.org/wiki/Persiana_(architettura)）；機製瓦 1841 年 Gilardoni 專利（https://fr.wikipedia.org/wiki/Tuile_m%C3%A9canique）。

## 層數、面寬、進深
- 佛羅倫斯 15 世紀一般住宅 2～5 層、後面小院；入口後一段寬約 1 m 的直梯每層重複。（yourwaytoflorence houses）
- Via del Prato 成排住宅（1570 年代末）：59 戶連成約 450 m、地上 3 層、後有帶井的小院，租給工匠。https://piazzadeicavalieri.sns.it/en/buildings-and-monuments/piazza-dei-cavalieri/urban-development-16th-19th-centuries/the-terraced-houses/
- Ammannati 的 Via degli Alfani 住宅（1577–84）：3 層、每層 9 扇窗、連續的出挑簷口。（同上）
- Palazzo Guadagni（約 1502–06）4 層、頂層是開敞的 loggia。https://it.wikipedia.org/wiki/Palazzo_Guadagni
- 里窩那 Venezia Nuova（1629 起）：面向運河的商人宅與倉庫，運河層是地窖倉庫。https://it.wikipedia.org/wiki/Venezia_Nuova ・ https://portusonline.org/fossi-di-livorno-the-canals-at-the-heart-of-the-history-form-and-layout-of-the-city/
- 熱那亞由下往上：拱頂店鋪＋夾層 → caminata 大廳 → 臥室 → 頂層僕人房與廚房；一樓臨街幾乎連續的拱頂店鋪 volta、旁邊一扇上樓的門。https://gup.unige.it/sites/gup.unige.it/files/pagine/Le_logge_medievali_di_Genova_ebook.pdf
- Tafur（1435–39）「房子都像塔，4 到 5 層或更多」〔摘〕；Rough Guides：caruggi 兩側通常 6 或 7 層（https://roughguides.com/italy/liguria/genoa）。

## 牆面與顏色
- 利古里亞：抹灰 14～15 世紀出現；彩繪立面 15 世紀中起擴散、全盛 16 世紀中到整個 17 世紀；最簡單的是單色牆＋細白帶當樓層線、框住門窗；雙色是下段深色基座帶；也畫假窗、假百葉。https://www.boero.it/wp-content/uploads/2021/10/piano-del-colore-boero-per-finale-ligure.pdf
- 黑白條紋只有 Doria、Spinola、Grimaldi、Fieschi 四家能每層都做 ⇒ 一般住宅不用。https://en.wikipedia.org/wiki/Historic_center_of_Genoa
- 托斯卡納：pietra forte 黃褐（宮殿立面）、pietra serena 灰到淡藍灰（門窗框、托架、柱）。https://www.yourwaytoflorence.com/db/brunell/material.htm ・ https://it.wikipedia.org/wiki/Pietra_serena
- 外牆色：中世紀石灰白配紅赭；複雜的加黃赭、綠土；18 世紀才轉向粉綠、粉藍、淡粉、淡黃 ⇒ 1666 用石灰白、黃赭、紅赭、土色。https://www.ingenio-web.it/articoli/intonaci-decorati-storici-riconoscere-motivi-colori-e-datazione/

## 窗、門、店鋪
- 跪窗（finestra inginocchiata）：Michelangelo 起、Palazzo Medici 首例；窗台架在托架上、通常裝鐵柵、頂上山牆 —— 宅邸一樓的等級。https://it.wikipedia.org/wiki/Finestra_inginocchiata
- 1666 年用實心木板窗 scuri〔推〕；鐵柵窗 inferriate〔推〕。
- 熱那亞 17 世紀大門：石門框厚 14～18 cm、淨寬 150～200 cm、淨高 300～425 cm。https://www.archcalc.cnr.it/indice/PDF26/31_Decri_et_al..pdf ；黑石板雕刻門框、樓梯玄關 15～18 世紀流行（Finale PDF）。

## 屋頂、煙囪
- 筒瓦：托斯卡納 coppo 與平瓦 embrice 交替；坡度至少約 30%。https://it.wikipedia.org/wiki/Coppo
- 熱那亞的 ardesia 石板頂（abbadini）久了褪成均勻淺灰。https://www.acompagna.org/rivista/2014/3/p13.pdf ・ https://it.wikipedia.org/wiki/Ardesia
- 佛羅倫斯木屋簷與出挑撐木（material.htm）；Guadagni 頂層 loggia 上寬大出挑的屋簷；現行規範要求椽子用簡單不雕形的樣式（https://www.comune.arezzo.it/sites/default/files/statuti_regolamenti/files/pdf/allegato_a2_centro_storico.pdf）。屋簷深 0.8～1.8 m〔推〕。
- 煙囪：方形煙道、頂上小雙坡帽（托斯卡納筒瓦、熱那亞石板）〔推〕。

## 威尼斯第 4 級（Ghetto；寫在 gura-venice-housing-1666 的那五件）
- 「七到八層高」、往上加（https://www.myjewishlearning.com/article/a-brief-history-of-the-venice-ghetto/）；「有些六層，在威尼斯前所未有」（https://europeforvisitors.com/venice/articles/venice_ghetto.htm）；最高 8 層（https://it.wikipedia.org/wiki/Ghetto_di_Venezia）。
- 加層時把天花板壓低（europeforvisitors）；部分天花板約 1.8 m〔摘：https://muse.jhu.edu/books/9780299180232/9780299180232-25.pdf〕；外牆薄、樓梯陡〔摘〕。
- 小公寓一再分割、用木隔間減輕地基負荷；很多戶沒有廁所或壁爐；密度至少是威尼斯其他地方的兩倍（myjewishlearning）。
