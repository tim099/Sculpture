威尼斯 1666 的住宅（Tim 2026-11-15「威尼斯可以建造專門風格的住宅房屋(可以參考文獻資料與現存古蹟)」；TASK-1291 那一張單上加的）。

- 產生程式在 design/：common.py（調色盤、regalzier、抹灰、伊斯特拉石線腳、barbacani、石陽台、屋頂木平台、煙囪、井欄）、vparts.py（自己的六件部件）、venice_low.py（低密度三型＋配色、淺版、小版）、venice_dense.py（中、高密度四型＋配色）、build.py、apply.py（抄自 kaguya-cpl-housing-1453）。
  重產：python -I -X utf8 -B build.py <design>；落格：apply.py <design> create／stamp／anchors／links／models／check；先跑 _probe.py（出框、撞格、浮空）。
- 照史料改過的（第一版是照印象做的）：裸磚的一樓 ⇒ regalzier（紅灰泥畫白磚縫；裸磚多半是 19 世紀剝落後的樣子）；灰泥剝落拿掉；轉角隅石拿掉（一般住宅不做）；煙囪帽改陶的倒錐、口徑約煙道兩倍；A 型改成立面正中一根煙囪（NTA 附錄 A 型 g3）。
- 〔推〕沒出處、照建議值：層高（一樓 3.3、樓上 3.0 m，同 kaguya、crest 的套）、屋頂坡度 0.33、窗板顏色（綠、深褐、灰藍）。

---

以下是史料整理（小幫手 2026-11-15 查的，每條附出處；〔推〕沒出處、〔摘〕只讀到摘要）：

# 威尼斯 16–17 世紀一般住宅：有出處的建築事實（給 1666 年城鎮 voxel 房子用）

> 標記：每條結尾是出處。〔推〕＝找不到可引用的出處，是依其他事實推的；〔摘〕＝只讀到搜尋摘要，原頁連不上（403／拒連），內容沒有親眼對過原文。
> 最有用的一份是 **威尼斯市政府舊城區規劃（VPRG Città Antica）NTA 附錄 1** 的「19 世紀前基礎住宅單元」類型表（下文簡稱 **NTA-A1**）——它把 Trincanato／Maretto 一系的類型學整理成法定描述：單元寬、進深、層數、樓梯位置、煙囪位置、立面開窗列數。它只用「cell（cellula）」當單位，**沒有給公尺數**。
> Trincanato《Venezia minore》（1948）原書線上讀不到（archive.org 版限借閱、IUAV 的評介 PDF 403），只能確認它的範圍：Castello 與 Dorsoduro、160 張 12–18 世紀建築圖。https://archive.org/details/guidetovenetiand0000trin

---

## 1. 層數、層高、面寬／進深、底層用途、樓梯

- **A 型（單 cell 面寬）**：面寬 1 個 cell，進深 1–3 個 cell，**高 2–3 層**，整戶上下樓 duplex／triplex；**單跑直梯貼著一道無窗的承重牆**（側牆或後牆）；前後兩面開窗；以「單排或雙排線性連續」排成一排（schiera）。https://www.comune.venezia.it/sites/default/files/cartanet/VPRG_Citta_Antica/NTA_Appendice_1.pdf
- **A1 型**：單 cell 旁邊加一條窄的樓梯 cell（寬度常常剛好只夠放樓梯），立面變成 3 列開口，其中一列是門＋樓梯間；2–3 層，可以每層一戶（simplex），由樓梯各自進出。同上 NTA-A1
- **B 型（雙 cell 面寬）**：通常是兩個 A 型併成的；面寬 2 cell、進深 1–3 cell、2–3 層、單跑梯（有時放在專用的樓梯 cell）；立面 **4 列開口**。同上 NTA-A1
- **B1 型**：兩個 cell 中間夾一條窄樓梯 cell，立面 **5 列開口、正中那列是大門**；常常在樓梯那一軸開一個老虎窗（abbaino）。同上 NTA-A1
- **底層用途**：這幾型的法規都允許底層作「手工作坊、零售商店、公共營業（酒館等）」，上面幾層住人——就是 bottega／作坊在下、住家在上的老格局。同上 NTA-A1
- Calle del Paradiso（Castello，靠近 Rialto 那段大多是 16 世紀）：**底層原本就是店鋪／作坊**，上層住家由 barbacani 挑出。https://capturingvenice.blogspot.com/2014/07/calle-del-paradiso-castello.html
- **Castello 一棟 17 世紀下半的獨戶 casa a schiera：2 層**，水平連續排列。〔摘〕https://catalogo.cultura.gov.it/detail/ArchitecturalOrLandscapeHeritage/0500195778
- **商人宅的樓層順序**（以 Palazzo Donà，1610–12 為例）：底層是大穿堂（androne／sottoportego）加服務空間——井、caneva（酒窖食物間）、magazeni（柴與貨的倉庫）、洗衣間、緊鄰 **cavana（貢多拉船塢）** 的廁所 → 夾層（mezà，辦公＋住）→ 主層（piano nobile，中間是 portego 大廳）→ 閣樓（soffitta：房間、廚房、廁所）。https://oajournals.fupress.net/index.php/oi/article/download/7933/7931/7810
- **樓板全是木頭**（為了減輕地基負擔，幾乎不用磚拱）：單向密排梁，梁與梁的間距大約 1:1；梁上鋪木板，再打一層 terrazzo 地面；梁斷面寬高比約 1:3；用落葉松（larice）、冷杉、松木。同上 Ceriani Sebregondi
- **長度單位**：文中 30 piedi＝10.41 m ⇒ **1 威尼斯尺（piede）≈ 0.347 m**（≈ 3.5 voxel）。Donà 宅用的梁長 6.6–10.75 m；大廳 sottoportego 約 6.6 × 34 m。同上
- 哥德式商人宅：地面層由門廊進 androne（倉儲兼營業）；大樓梯通往上面幾層住家，**上層天花相對低**；後面有**開放式室外樓梯**下到小中庭，中庭有井口。https://en.wikipedia.org/wiki/Venetian_Gothic_architecture
- 層高的公尺數：沒找到出處。建議值：底層／magazzino 約 3.0–3.5 m，夾層約 2.2–2.6 m，主層約 3.5–4.5 m，一般住層約 2.7–3.0 m；cell 面寬約 4–6 m（≈ 12–17 尺）。〔推〕

## 2. 牆面：磚、灰泥、顏色、伊斯特拉石

- 基本建材是**磚**，下面是石台＋木樁基礎；講究的立面才貼伊斯特拉石。https://en.wikipedia.org/wiki/Venetian_Gothic_architecture
- **regalzier**：中世紀建築**最常見的外牆灰泥**——薄薄一層紅色（赤鐵礦，刻意調成飽和紅）抹在石灰／石膏底灰上，再用白色橫豎線畫出假磚縫；表面還會塗亞麻仁油防水。15 世紀末在威尼斯市區退流行，但 16 世紀的民間建築還在用。https://conservation-science.unibo.it/article/download/3402/2759/8458
- **marmorino**：用大理石粉代替砂的白色石灰灰泥，用來模仿石材；**15 世紀末起**用在文藝復興建築，也用在「比較不重要的立面」；**17–18 世紀最普及**（約 4 mm 厚，底下一層 cocciopesto，潮濕的地方特別適合）。https://www.accademiavenezia.it/upload/docs/docenti/file/74/2004_Tiozzo_marmorino_intonaci_PAVAN_opuscolo.pdf
- marmorino／cocciopesto（碎磚粉＋石灰）灰泥用在內牆，「有時也用在外牆」。https://en.wikipedia.org/wiki/Venetian_Renaissance_architecture
- cocciopesto 是偏紅的顏色（碎紅磚粉）。https://historywalksvenice.com/article/daily-life-and-customs/cocciopesto/
- 哥德時期的薄灰泥常常畫有紅、綠、黃的幾何或花草紋樣（Carpaccio《Healing of a Madman》可以看到）。https://venice.jc-r.net/plaster-frescoes
- **伊斯特拉石**：緻密不透水的石灰岩，新採時是鹽白或淡黃，風化後變灰白，跟紅磚對比強烈；Sansovino（1580）說是從 Rovigno、Brioni 運來的。https://en.wikipedia.org/wiki/Istrian_stone
- 早期民用建築的**伊斯特拉石樓層線腳（cornice marcapiano）**只是裝飾、不承重；房子變大以後改成量產，幾乎**不做轉角件**；砌上牆之前會先上油漆（白色卷草、黑底）。〔摘〕https://sigecweb.beniculturali.it/sigec/item/print/ICCD10328725
- 公共水井的進水石（pilele）、井身底盤也是伊斯特拉石。https://it.wikipedia.org/wiki/Pozzo_veneziano
- 哪些部位用石頭：門框、窗框、窗台、樓層線腳、門檻、水門台階、陽台板與欄杆、簷口——磚造威尼斯的通則，但沒找到一份文獻逐項列出來；**一般住宅不做轉角隅石**（上一條「不做轉角件」間接支持）。〔推〕
- 顏色建議：磚／regalzier 的紅、cocciopesto 的粉紅帶赭、marmorino 的白到奶油色、伊斯特拉石的白灰；赭黃色牆在 1666 年可以用，但沒找到直接出處。〔推〕
- 19 世紀的威尼斯普遍是剝落見磚、頂多抹 cocciopesto 的樣子（Boito 等人讚美過）——**「裸磚」很多是後世的狀態**，1666 年應該以抹灰為主。https://www.insula.it/images/pdf/resource/quadernipdf/Q07-04.pdf

## 3. 窗

- **開窗列數**（NTA-A1 立面模型）：A 型是 2 列窗＋居中的門（g1）、3 列（g2）、或 2 列加**正中一根立面煙囪**（g3）；B 型 4 列；B1 型 5 列、中間那列是門；**Bg 型**的「sala」那一格開**雙聯窗（bifora）或三聯窗（trifora）**，立面 4–5 列，其中 2–3 列挨在一起；**C 型（三開間）**：中間的 sala 開**多聯窗（polifora）**，兩側各 2 列單窗，大門在中軸。https://www.comune.venezia.it/sites/default/files/cartanet/VPRG_Citta_Antica/NTA_Appendice_1.pdf
- portego（從水門通到陸門的中央大廳）通常靠多聯窗採光。https://en.wikipedia.org/wiki/Portego
- 樣式年代：哥德式尖拱／葱形拱（ogee）窗大約 14–15 世紀；文藝復興（15 世紀末–16 世紀）出現 **Serliana（中間一個圓拱、兩側較窄較矮的方窗）**，成為 portego 最流行的開口；17 世紀是巴洛克（Longhena）。https://imagesofvenice.com/?p=9168
- Ruskin 的「第四式」窗拱（頂端帶尖的拱）從 13 世紀用到 15 世紀中，只換線腳，是壽命最長的一型。https://www.lancaster.ac.uk/fass/ruskin/eSoV/texts/vol10/vol10p290.html
- 威尼斯的圓拱、尖拱窗比義大利其他城市用得更久；城市太擠，採光主要靠正立面，所以正面「窗比別處更多更大」。https://en.wikipedia.org/wiki/Venetian_Renaissance_architecture
- Carpaccio《Rialto 十字架聖物的奇蹟》（約 1494–96）：一排排緊鄰的房子，大多開**細高的哥德窗**。https://www.csmonitor.com/1981/0304/030408.html
- **陽台（poggiolo）**：威尼斯式陽台（伊斯特拉 Parenzo 的威尼斯哥德房子）放在立面中央或轉角，用獅頭托架撐著，一塊整石板，欄杆是圓或方的石柱（balaustrini）。這是殖民地的例子，套用到威尼斯本城屬推論。〔摘〕https://hrcak.srce.hr/file/353388
- 1666 年的一般住宅：主層中間 2–3 聯的圓拱或尖拱窗，其餘是方窗或單圓拱窗，配伊斯特拉石框＋石窗台；**木百葉（scuri）**多半漆深綠或褐色，或保持木色——這點沒找到 17 世紀的顏色出處，現行法規也沒有「威尼斯綠」的規定。〔推〕

## 4. 屋頂

- 屋頂是 coppi（半錐形弧瓦）；義大利一般規範是 coppi 屋面坡度最少約 35%（約 19°）。這是全義大利通則，不是威尼斯專屬。https://laterizio.it/images/Manuals/Coperture/manuale-coperture-2025.pdf
- 威尼斯建築用屋架加檁條（capriate、tetto 木構）；Palazzo Donà 閣樓那層樓板就是屋架的拉桿。https://oajournals.fupress.net/index.php/oi/article/download/7933/7931/7810
- 坡度與形式：沒找到威尼斯專屬的出處。建議用低坡、**四坡（padiglione）或沿街的雙坡**，坡度約 25–35%，屋簷用木椽外挑或磚砌齒狀簷口，約 0.4–0.8 m。〔推〕
- **altana**（屋頂木平台）：**立在屋面的磚墩或柱上**，鋪木地板，圍木或鐵欄杆，從閣樓走窄梯（常是螺旋梯）上去；用來曬衣、乘涼、漂頭髮。https://imagesofvenice.com/?p=9872
- 最早相近的詞見於 **1224 年**（San Polo 的 Matteo Barbani 蓋了一座「atana」）；Carpaccio（1494）是最早畫出 altana 的畫之一；de' Barbari 1500 年的鳥瞰圖上「屋頂構造遍布全城」。https://gardeninvenice.blogspot.com/2013/02/le-altane-venetian-rooftop-terraces-in.html
- altana 是「立在柱墩上、架在斜屋頂上方的平台」，在全城都很普遍，不是少數幾棟才有。https://www.venecisima.com/post/life-on-the-roofs-of-venice-altanas
- 16 世紀女人在 altana 上把頭髮漂成「威尼斯金」（Tassini 1863 的記載）；Bellini、Carpaccio（1496）、Canaletto（1724）都畫過。https://it.wikipedia.org/wiki/Altana_(architettura)
- NTA 允許在 A、B 型立面中軸開老虎窗；**B1 型常常在樓梯那一軸本來就有老虎窗**。https://www.comune.venezia.it/sites/default/files/cartanet/VPRG_Citta_Antica/NTA_Appendice_1.pdf

## 5. 煙囪

- **煙囪位置是類型特徵**：A 型「常有一根煙囪，在側面、後面或**正立面**」；A 型 g3 立面＝**煙囪居中、兩側各一列開口**；**Bg 型：煙囪在正立面、位於不挨在一起的那幾列窗中間**。也就是煙囪身沿著正立面往上爬，是很常見的立面元素。https://www.comune.venezia.it/sites/default/files/cartanet/VPRG_Citta_Antica/NTA_Appendice_1.pdf
- **煙囪帽（fumaiolo）**：大型陶質煙囪罐，頂上是**倒錐形帽**，用來攔住火星、防止火災（例：Ca' Dario，1480 年代）。https://en.wikipedia.org/wiki/Venetian_Renaissance_architecture
- 形狀種類：方或長方、圓、桶形或鐘形、**截頭倒錐**；有的兩三根煙道併成雙瓣、三瓣斷面；舊煙囪罐底部側壁有通氣孔，讓冷空氣進來把火星冷卻；煙囪身有外露、半外露、內藏三種，**半外露最常見**；Bellini、Carpaccio 畫的煙道都很細長。https://imagesofvenice.com/?p=9872
- Carpaccio 的 Rialto 畫面是一片「煙囪森林」——高煙道頂著大煙囪罐，旁邊夾著涼廊和 altane。https://www.csmonitor.com/1981/0304/030408.html
- Lupo（ArcHistoR 2016）：大運河沿岸 16–17 世紀宮殿正立面上的「方尖碑」其實是煙囪，是「Carpaccio 式煙囪」的古典化版本；Scamozzi 1615 年說方尖碑是煙囪的「all'antica」造型；當時有兩派做法——把煙囪藏起來，或把它當立面構圖的主角。https://doaj.org/article/4288014d39ab48c98503abe269c08bad
- 建議尺寸：倒錐帽口徑大約是煙道的 2–3 倍，帽高約 0.8–1.2 m，煙道斷面約 0.4–0.6 m 見方；立面煙囪身可以用 2–3 層磚托架挑出牆面 0.3–0.5 m。〔推〕

## 6. 其他元素

- **barbacani**：從牆身挑出的托架（木梁頭），讓樓上的面積比樓下大；Calle del Paradiso 的上層就是靠它撐出來的，那條街以**木造外挑屋簷**出名。https://www.italia.it/it/veneto/venezia/dove-mangiare/ristorante-ai-barbacani ・ https://en.wikipedia.org/wiki/Ponte_del_Paradiso ・ https://capturingvenice.blogspot.com/2014/07/calle-del-paradiso-castello.html
- barbacani 的木梁挑出長度大約 0.5–1.0 m、梁距大約 0.5–0.7 m。〔推〕
- **sotoportego**：在建築底層挖穿一個樓層高的通道，連接 calle、corte、campo、fondamenta；常是進出 corte 的唯一入口；裡面常有小神龕、伊斯特拉石或白大理石的宗教浮雕；另有兩種：直接開向水道（有頂的碼頭）、沿著水道走（有頂的 fondamenta，最少見）。https://it.wikipedia.org/wiki/Sotoportego
- **水門與 portego**：portego 通常連通水門與陸門，可能穿過中庭；商人宅底層有 cavana（船塢）。https://en.wikipedia.org/wiki/Portego ・ https://oajournals.fupress.net/index.php/oi/article/download/7933/7931/7810
- **井（pozzo alla veneziana）**：其實是雨水蓄水池，挖 5–6 m 深、內襯黏土、填濾砂；周圍 2 或 4 個伊斯特拉石進水口（pilele），地面往進水口傾斜；中央井筒上是 **vera da pozzo**（井欄，兼放滑輪）；多半在 campo 或 corte。1858 年有約 7,000 口（6,046 私井、180 公井）。https://it.wikipedia.org/wiki/Pozzo_veneziano
- 哥德宅後面有開放式室外梯，下到帶井口的小中庭。https://en.wikipedia.org/wiki/Venetian_Gothic_architecture
- **calle 寬度**：最窄不到 1 m（calletta），calle larga 3–4 m 以上；ramo 是死巷；路面 14 世紀末起鋪磚，**17 世紀末起換成粗面岩石板（masegni）**——1666 年大多還是磚鋪或夯土。https://en.wikipedia.org/wiki/Calle_(Venetian_street)

## 7. 一般排屋 vs. 商人小宅；中密度 vs. 高密度

- **低–中密度（一般排屋）**：A、A1、B、B1 型——2–3 層、面寬 1–2 cell（加樓梯 cell）、單跑梯、底層店或作坊、立面 2–5 列窗、煙囪常在正立面。https://www.comune.venezia.it/sites/default/files/cartanet/VPRG_Citta_Antica/NTA_Appendice_1.pdf
- **商人小宅（palazzetto）**：Bg 型（2 cell、**2–4 層**、有一格是穿透前後的「sala」並開雙聯／三聯窗、樓梯在 sala 裡，或用螺旋梯、「leonardesca」雙跑梯）、**C 型（3 開間、中央 sala 開多聯窗、樓梯在側面專用 cell、常有夾層和可用的閣樓、常帶一個 corte）**。同上 NTA-A1
- **高密度**：D 型「a blocco」——正立面 ≥5 cell，加樓梯 cell，**≥4 層**，四面採光，正面有好幾個大門，有好幾組（常對稱）樓梯，**各層是一戶一戶的公寓（in linea）**。同上 NTA-A1
- Maretto 的類型史（從目錄判斷應是 P. Maretto《La casa veneziana nella storia della città》）：哥德 casa a schiera 是「三個世紀連續排屋的基礎」；16 世紀把排屋「升格」為 **palazzetti a schiera**（S. Giustina、Albanesi）；16 世紀初有**疊成四戶出租、用 leonardesca 雙跑梯的雙併宅**（Castelforte S. Rocco）；Case Cappello 是投機用的四戶鏡像雙併；16–18 世紀大量出現「casa in linea」；**Ghetto Nuovissimo 是密度的極限**。https://ce.visuallibrary.net/download/pdf/306386.pdf
- **Marinarezza（Corte Colonne／Schiavona，Castello，緊鄰 Arsenale 一帶的造船廠）**：**15 世紀末的排屋**，三排平行，每條 calle-corte 兩排面對面；屬 Ospitale del Comun，是 16 世紀初 Procuratie de Citra 約 200 棟救濟屋的一部分，**免費給威尼斯水手和有功的外國人住**；臨 Riva 的兩座大拱門建於 **1645**。〔摘〕https://sigecweb.beniculturali.it/sigec/item/print/ICCD12006888 ・ https://www.arte.it/location/marinarezza-1156
- Maretto 把 Corti Colonne（「Marinaresca」）稱作「第一個多尺度規劃的文藝復興連排建築群」。https://ce.visuallibrary.net/download/pdf/306386.pdf
- **Corte Nova（Castello，S. Lorenzo 附近）**：國家文化遺產目錄收有「Casa a schiera in Castello 2031–2032／Corte Nova」〔摘〕；Maretto 把 Corte Nuova S. Lorenzo 列為「延續哥德遺產的排屋」；由 17 世紀的 sotoportego 從 Calle Zorzi 進入（兼作還願小禮拜堂，傳說 1630 年瘟疫時這裡倖免）。〔摘〕https://catalogo.cultura.gov.it/detail/ArchitecturalOrLandscapeHeritage/0500195831 ・ https://ce.visuallibrary.net/download/pdf/306386.pdf ・ https://www.savevenice.org/project/sotoportego-di-corte-nova
- **救濟出租屋（pro Amore Dei）**：Scuole Grandi（大兄弟會）在 16 世紀蓋、也管理給窮人的住宅（免租或低租），例如 Corte San Rocco、Corte San Marco；採**排屋＋標準化平面**。https://www.epfl.ch/labs/tpod/governing-through-housing-the-scuole-grandi-and-urban-welfare-in-16th-century-venice/
- **Ghetto**：建築「高得出奇，最高 8 層」，因為人口擠只能往上加——是 1666 年的高密度上限參考。https://it.wikipedia.org/wiki/Ghetto_di_Venezia
- 市中心擁擠，所以傾向往高蓋、舊房子常加層。https://en.wikipedia.org/wiki/Venetian_Renaissance_architecture
- 建議遊戲分級：
  - 低密度：A／A1，2–3 層，面寬約 5 m。
  - 中密度：B／B1／Bg，3 層，面寬約 8–11 m。
  - 商人小宅：C 型三開間，3 層＋夾層＋altana，面寬約 12–16 m，中央 polifora。
  - 高密度：D 型或 Ghetto 式，5–8 層，面寬 ≥ 20 m，多部樓梯。
  〔推〕
