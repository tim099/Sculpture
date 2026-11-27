# 利劍號 研究報告合本（2026-11-24，Paperclip FAR-92）

兩份子報告：圖紙與畫（plans_agent）、文字記載（texts_agent 與三個子代理）。原始讀數檔、頁圖、量測程式在 Paperclip 工作目錄 `.work/FAR-92/sayf/research/`。

---

# al-Sayf（1666 年阿爾及爾 xebec）：船圖量測報告（plans_agent）

> 這份是 plans_agent 回覆的全文（它的寫檔工具擋下 .md，由 Claude-Ojousama 2026-11-24 13:43 UTC 照它的回覆原樣另存）。讀數檔 `readings.json`（136 條，每條有 period 欄）是它自己寫的。
> 換算：1 瑞典呎 = 0.2969 m，1 pied du roi = 0.3248 m，1 codo de ribera = 0.5747 m（1 codo = 24 pulgadas 是它的假設）。A、B 兩節是 18 世紀資料（1749–1790），只有 C 節是 17 世紀。

## 重點
1. 沒有任何 1666 年的 xebec 船圖。有完整比例尺和尺寸表的 chebec／xebec 船圖最早只到 1749 年（Navarro）和 1768 年（Chapman）。Jouve 1679 只有 tartane 和 polacre，寫意畫、沒有尺寸。
2. Chapman 1768 Pl. LVIII No.17「Algerisk Chebeque」：Sjöhistoriska museet 4000 px 版畫。比例尺 20.50 px／瑞典呎（英呎尺交叉驗證）。圖上量兩垂線間距 130.8 呎，尺寸表 130 1/3 呎，差 0.4%；吃水與表上 9 2/3 呎一致。
3. 18 世紀四張船圖格局一致：三桅（後桅 0.07–0.11 Lpp、主桅 0.48–0.52、前桅 0.93–0.97 前傾 4–15°）；長喙、懸空的船尾平台、舷側大幅外飄；腰部砲門與小槳門交錯。
4. 桅桁比例在 Navarro 1749 與法國 OR 2452 兩份獨立資料幾乎一樣：主桅 ≈ 0.65 L、前桅 ≈ 0.58–0.60 L、後桅 ≈ 0.27–0.35 L；主帆桁 ≈ 1.04–1.13 L、前帆桁 ≈ 0.94–0.97 L、後帆桁 ≈ 0.42–0.48 L。Chapman 沒畫桅高與帆桁。
5. 1660 年代的畫：Nooms 的 Salé 槳帆船（SK-A-1399，1662–68）是雙桅（前桅在船首、主桅約 0.45–0.5 L），可見槳每舷約 14–16 支，沒看到砲與尾平台。同期三桅加長喙的拉丁帆船也有，但都是不帶槳的 settee（Nooms 的 Tripoli 遠景船、Casembrot 的 settee 素描）。1669–71 年畫面裡的阿爾及爾戰船（Mary Rose 之役、Bugia 之役）都是橫帆船。

## A. Chapman 1768，Pl. LVIII No.17（18 世紀）
- 版畫：https://mm.dimu.org/image/042uK3KjAwHx?dimension=max（Europeana /916109/smm_sm_object_ArchitecturanLVIII）。
- 原圖說：「16 st. 6 Pundige Canoner på sidorne, 4 st. 12 Pundige Canoner förut och 8 st. 3 Pundige på Skanzen, samt 30 st. Svåra Dunder-bössor」。
- 尺寸表：1971 年 Coles 復刻本 p.68（archive.org `architecturanava0000fred`，leaf n132）：「Length between perpendiculars 1301/3ft, Breadth moulded 251/4ft, Draught 92/3ft, Guns 28 … Pairs of oars 9」。

| 項目 | 數值 | 依據 |
|---|---|---|
| Lpp | 38.70 m（圖上量 38.83 m） | 表＋圖 |
| 型寬（水線處） | 7.50 m（body plan 7.81 m） | 表＋圖 |
| 吃水 | 2.87 m | 表＋圖 |
| 全長：尾平台尖到喙部構材收攏處 | 50.0 m | 圖 |
| 全長：含尾端撐桿與船首雕像 | 51.8 m | 圖 |

- 外飄：中剖面半寬 離基線 2.76 m（約水線）3.90 m；3.62 m 處 4.32；4.50 m 處 4.91；欄杆帽（5.08 m）5.30 ⇒ 甲板處全寬約 8.9 m、舷牆頂全寬 10.6 m。
- 高度（離水線，中段）：甲板舷邊 0.95；舷牆頂 2.37（往船首升到 2.66）；後甲板欄杆頂 3.8–4.4；船首欄杆接艏柱處 3.37；艏柱頭頂 4.32。
- 喙部：艏垂線往前 5.91 m（含船首雕像 6.95 m），喙尖離水線 3.59 m。
- 尾平台：艉垂線往後懸空 5.30 m（最外撐桿 6.05 m）；平台欄杆頂離水線 5.76 m、平台底面 4.82 m。尾視圖 D：平台欄杆寬 4.39 m、兩側翼板跨度 10.47 m；船尾 4 個追擊砲門。後甲板長 6.07 m，艏樓長 5.6 m。
- 桅（只畫桅樁）：後桅 艉垂線往前 3.55 m（0.092 Lpp）徑 0.32 m 約 1.5° 向後；主桅 18.58 m（0.480）徑 0.64 m 垂直；前桅 36.13 m（0.931）徑 0.45 m 約 3.7° 向前。
- 槳：每舷 9 個槳門與砲門交錯；平均間距 2.32 m（個別約 1.8–2.6）；分佈在 0.25–0.73 Lpp；槳門約 0.25 m 見方；槳門中心離水線 1.60 m、離甲板 0.65 m。
- 砲：腰部每舷 8 門 6 磅，間距 2.32 m，主桅附近空一段；砲門 0.67 m 見方，下緣離水線 1.43 m。艏樓 4 門 12 磅（圖上看得到 1 管）。後甲板 8 門 3 磅（舷牆 6 個矩形開口加 3 個圓孔，哪些是砲門沒標，低信心）。另有 30 支重型火繩槍。
- 附帶 Pl. LX No.8 法國 felucca（10 對槳）：Lpp 13.0 m、寬 2.62、吃水 0.77；槳樁間距 0.87 m。

## B. 其他 18 世紀船圖
1. Navarro《Album del Marqués de la Victoria》Ms.2463-017「Plano de los Jaueques … Cartagena … 1749」（https://bibliotecavirtual.defensa.gob.es/BVMDefensa/es/catalogo_imagenes/imagen_id.do?idImagen=3268625&formato=jpg）：船長 60 codos = 34.48；寬 8.48；深 3.07；龍骨 29.88；後甲板 11.49；砲門下緣離水線 1.29。主桅 22.41、主拉丁帆桁 39.08；前桅 20.11、前帆桁 33.33；後桅 9.20、後帆桁 14.37；橫帆桁 主 21.26、上桅帆 13.79、前 18.97。圖上加量：兩垂線間距 62.3 codos；桅位 後 0.093、主 0.513（前傾約 5°）、前 0.964（前傾約 15°）；每舷 11 個方形砲門，間距約 2.0 m，沒看到另外的槳門。
2. 法國「Plan d'un Chebeck de 24 Canons du 6」（Sjöhistoriska OR 2452，未註年代；https://mm.dimu.org/image/03348TDuFptW?dimension=max、桅桁表 …FptX）：長 115 pieds = 37.35 m；水線寬 7.71；吃水 2.35；外飄後最寬 9.48。主桅 24.12（徑 0.69）、前桅 22.33、後桅 12.99；主拉丁帆桁 38.98、前 35.08、後 17.86；橫帆桁 主 19.49、前 17.86、主上桅帆 17.54。每舷 12 個大砲門與 12 個小槳門交錯，間距約 2.17 m。桅位 後約 0.07、主約 0.49、前約 0.97（低信心）。
3. 「Neapolitainsk Schebeck」Naples 1760-04-14（OR 2464；https://mm.dimu.org/image/03348TDuFq3F?dimension=max）：長 35.92；寬 8.24；艙深 2.52；船尾吃水 2.67；外飄後最寬 10.45。每舷 8 門 4 磅、後甲板每舷 4 門 3 磅、船首 2 門 12 磅＋2 門 6 磅、20 門迴旋小砲。每舷 8 砲門＋9 槳門，槳門間距 2.59 m。桅位 後 0.106、主 0.501、前 0.964（前傾約 6°）。
4. 次要：Danish galley「Dragon」1776（OR 2336）116′6″／29′1″／9′2″（單位不確定）；Romme 1792 p.156「Chebek」：「12 à 22 canons… trois à quatre cent tonneaux」。
- 找過沒拿到：Pâris《Souvenirs de marine》（目錄列 Pl. 25、78、88–90 是 chebec，沒可用掃描）；Toulon 的 chebec 船圖（SHD 連線被拒、Gallica 403）；Jouve 1679 沒有 chebec。

## C. 1700 年以前的畫（只能量比例）
1. Nooms「Gezicht op Salee」1662–68，SK-A-1399（https://id.rijksmuseum.nl/20027354）：槳帆船雙桅拉丁帆，前桅 0.01–0.04 L、主桅 0.44–0.52 L；主桅高 0.38–0.54 L；主帆桁 0.63–0.70 L；可見槳 14–16 支，間距約 0.047 L。「是 Salé 海盜船」是推論，博物館說明只提荷蘭艦隊。
2. Nooms「Gezicht op Tripolis」SK-A-1398 遠景小船：三桅拉丁帆，喙長 0.10 L；前桅 0.08 L 前傾約 15°；主桅 0.51 L 高約 0.65 L；後桅 0.85 L 高約 0.29 L；看不到槳；主桅上小帆是不是橫帆看不出來。信心低到中。
3. Casembrot「Three studies of Mediterranean settee」NMM PAD8358（https://www.rmg.co.uk/collections/objects/rmgc-object-112509；作者 1650–75 在 Messina）：西西里／義大利商船。三桅：前桅在艏柱前傾約 25°、主桅 0.35 L、後桅 0.86 L；長喙 0.22 L；舷上緣 18–20 個小拱形開口。
4. Van de Velde the Younger NMM PAE5304（1694?）「Turkish vessel」雙桅拉丁帆，透視嚴重，信心低。
5. 反證：1669 Mary Rose 之役、1671 Bugia 之役畫的阿爾及爾戰船都是橫帆船。

## D. 給設計者（設計判斷，不是讀數）
- 船體可沿用 Chapman No.17 的形狀、比例縮小；1666 年的船應比 1768 年那艘（38.7 m）小。
- 桅：三桅版照 18 世紀（後 0.09、主 0.48–0.51、前 0.93–0.96 前傾）；雙桅版照 Nooms 1660 年代的槳帆船。三桅加長喙在 1660 年代存在，但只見於不帶槳的 settee。
- 桅桁比例：主桅 0.65 L、主帆桁 1.05–1.13 L、前帆桁 0.95 L、後桅 0.3 L（18 世紀，兩份獨立資料一致）。
- 槳：18 世紀每舷 9 個槳門、間距約 2.3 m、離水線約 1.6 m、與砲門交錯；1660 年代槳帆船可見 14–16 支。

## 檔案
`readings.json`（136 條）、`readings_A.json`、`readings_BC.json`；`make_readings_A.py`、`make_readings_BC.py`、`annotate_chapman.py`、`gridcrop.py`；`sources/`（25 檔）；`crops/`（59 檔，總覽標註圖 `A_Chapman_PlLVIII_No17_profile_annotated.jpg`）。

---

# 利劍號（1666 Algiers「xebec」）文字證據報告（texts_agent）

> texts_agent 和它的三個子代理（英文記載 1640–1704、名稱最早出現處、阿爾及爾艦隊 1650–1680）的回覆，由 Claude-Ojousama 2026-11-24 14:26 UTC 整理另存（它們的寫檔工具擋下 .md）。讀數檔 `readings.json`（54 條）是 texts_agent 自己寫的。頁圖：`sources/`（主代理）、`sources/names/`（名稱）、`sources/fleet/`（艦隊、英文記載）。pied de roi = 0.32484 m。

## 結論
- 找不到 1666 年阿爾及爾有 xebec 的證據。1640–1730 年印的書裡，沒有一本把阿爾及爾的船叫 chebec、xebec、jabeque 或 sciabecco。
- 名稱 1666 年以前就有，但意思是小船：Zurara 1428（摩洛哥 Targa 附近的小型襲擊船，「hũa Fusta, e seis Enxabeques」，p.560）、1430（「hum Enxabeque com pescado」，漁船，p.567）；Calderón 約 1650–52〈El encanto sin encanto〉的遊樂小船；約 1677〈El segundo Scipión〉租來渡海的小船。
- 第一次和北非連上：1688 年 Ponza 海域「uno sciabecchino barbaresco」（的黎波里），但這是 Guglielmotti 1893 v.8 p.420 自己的用詞。和阿爾及爾直接連上：1740–50 年代（1743「xaveque Argelino」、1752「dos xabeques argelinos」，只看了搜尋摘要）。Devoulx 1869（*Revue africaine* 13，p.386、396）的阿爾及爾船籍紀錄從 1737 年開始，那年已有 2 艘 chebec（6 砲＋24 pierriers；4 砲＋14 pierriers）和一艘「vieux chebec」19 bancs、4 砲、8 pierriers。
- 字典：Covarrubias 1611 沒有；Fournier 1643、Guillet 1678、Dassié 1677、Aubin 1702／1747 都沒有 chebec 條目；RAE《Autoridades》1739 p.531「XABEQUE. Embarcacion à modo de una Galera, ò Fragata pequeña de remo, y vela… especialmente los Mallorquines, è Ibicencos」；法文最早 Savérien 1758 t.I p.244。
- Jal 1848 p.449、p.342：北非阿拉伯語把 chebek 叫「Brigantine／Brigantim」；「Le Chabek est ancien, non pas comme navire de guerre peut-être, mais comme navire de pêche」。⇒ texts_agent 的建議：把 1666 年的同類船當成大型 brigantin（這是推論，不是 17 世紀原文）。

## 1660–70 年代阿爾及爾艦隊（艦隊子代理，頁圖在 sources/fleet/）
- Dapper 1668 p.273–275：1659 年 22–23 艘、每艘 30–50 門砲、300–400 人；1662 年 4 月 15 艘 frigates 備便、3 艘剛下水、4 艘在船台，共 22 艘加 3 艘 galleys，另有 6 艘新船在船台。
- Ogilby 1670 p.238–239：1668 年名單 35 艘：23 艘有名有砲數（14–44 門）、「Two Satees, two Gallies」、6 艘在船台（26–40 門）、「Two Tartans ready to be Launch'd」。
- Spragge 1671（Bugia，1671-05-08）：燒掉 7 艘最好的戰艦（20–34 門）加 3 艘（熱那亞船、英國小船、一艘 Satea 都是戰利品）。
- Witsen 1671 p.274（Aubin 1702 p.428–429 照抄）：北非海盜船船頭圓、帆大、走得快。
- d'Arvieux（1674–75，1735 年版 v.5 p.263–265）：約 30 艘戰艦，最大 50 門、小的 10–12 門；3 艘槳帆船。
- Devoulx 1869 p.391–392（阿爾及爾本地文件）：1674 年 2 艘 saëttes、1 艘半甲板船、2 艘 frégates à rames、21 艘船；1675 年 2 caravelles、3 barques ou saëttes（chitia）、6 frégates à rames、24 艘船；1676 年 2 caravelles、5 frégates à rames、21 艘。他說 saëtte「ancien petit bâtiment à rames, très-léger, était devenu au XVIIe siècle un assez gros navire ne se servant d'avirons qu'exceptionnellement, comme les chebecs, et dont la mâture offrait un mélange de voiles carrées et de voiles triangulaires」，有的到 34 門砲（「comme les chebecs」是 Devoulx 1869 自己的比較）。
- Philips 1676 p.104–105、131–135：32 艘戰艦、3 艘槳帆船、幾艘 brigantine；名單 33 條，含「Settia Usuph Raise 80 8」「Settia Regip Raise 80 8」「A Carvel 150 16」，結尾「Seven Brigantines, and three Galleys」。沒有 settia 的噸位、帆裝、槳。
- Pitts 1704 p.117（1678 年被俘）：「a Frigatto as they call it, (i. e. a long sort of Vessel, with eleven or twelve Oars on each side; and with Sails Gally-like, fit only for the Summers Expeditions… having five or six Pattareroes」。
- 1669 Mary Rose 之役（Kempthorne／Hollar）、1670 Cape Spartel（Baltharpe：最小 30 門、200 噸以上）：阿爾及爾戰艦都是大帆船。
- Dan 1649 p.307、315（1634）：4 艘 galère（24／23 bancs）、1 艘 brigantin（15 bancs）、8 艘 frégate（5–6 bancs）；約 70 艘 navires、polacres、grandes barques，25–40 門砲。
- Grammont 1887：第一次寫到 chebek 是 1741 年（p.297）；1650–80 只寫 vaisseaux／navires。Plantet 1889：1650–1690 沒有 chebek。

## 可對照的小槳船（brigantin／frigatto）
- 每舷槳數：Haedo 1612 f15v 8–13（「vergãtines, a que llaman ellos fragatas」）；Fournier 1643 p.50 10／12／15；Aubin 1702 p.126 12–15；Dan 1634 年阿爾及爾 15 bancs；Pitts 11–12。每槳 1 人（Fournier、Guillet、Aubin、Savérien）。
- Guillet 1678 pt.3 p.69：「Brigantin est une espece de Galiotte… qui ne porte pas Couverte… n'a qu'un Homme à chaque rame. Chaque Matelot y est Soldat」。有沒有甲板資料互相衝突（Fournier 寫 sur couuerte）。
- Aubin 1702 p.431：地中海舊式 frégate「portoient couverte, & dont le bord… avoit des ouvertures, comme des sabords, pour passer les rames」⇒ 17 世紀已有「有甲板、舷牆開槳孔」的槳船。
- Guillet 1678 p.264 polacre：「porte Couverte, & va à Voiles & à Rames… quatre Canons, quelquefois de six… 25. à 30. Matelots」。
- Savérien 1758 p.162 brigantin：長 51 pi（16.57 m）、寬 7 pi 6 po（2.44）、深 3 pi（0.97）、槳凳間距 0.73 m；兩桅，主桅 L/2、主桁 L，前桅 ¾ 主桅、前桁 1.5 × 前桅。Jal 1848 p.342 威尼斯 brigantin 14 凳 16.9–18.2 × 2.9–3.1 m。

## 18 世紀以後的 xebec（只當上限參考）
- Falconer 1769：阿爾及爾 xebec 16–24 門砲、300–450 人（2/3 是士兵）；船尾外伸的欄杆平台、窄底、甲板拱度大、兩側格柵走道。
- Jal 1848 p.449：長寬比 1:4、長 éperon、船尾兩翼夾住的外伸平台、槳孔開在砲門之間。
- Laugier de Tassy 1725 p.262–265（1724 年）：約 20 艘 Vaisseaux（名單 24 艘、10–52 門，沒有 chebec），另有「plusieurs barques Latines, & au moins douze Bâtimens à rames chaque année」。
- 1733 的黎波里 28 門砲的 sciabecco（Guglielmotti v.9 p.79）；1831 西班牙 jabeque 最多 32 門。

## 未查
- 西班牙資料庫 CORDE／DHLE、Fernández Duro v.V（1652–1700）、加泰隆尼亞語 DECat／DCVB、Guglielmotti《Vocabolario》1889、Pâris、Gallica（Cloudflare 擋）、Google Books API（額度用完）。
- Narbrough 1676 的「Samberkeene」是什麼船型不明，不當 xebec 的證據。
