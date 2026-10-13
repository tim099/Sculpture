# 潮墓號參考與來源界線

## 電影外形：親看三張 Disney Archives 模型照片

來源：Rick Lorentz, Walt Disney Archives, [D23, 2020-07-07](https://d23.com/pirates-of-the-caribbean-flying-dutchman-models/)。文章明說外型參考荷蘭 fluyt 與瑞典 Vasa；照片版權仍屬原權利人，下載僅在 scratchpad 作設計觀察，不收入作品庫。

- 全景微縮模型：`900w-600h_02_WDA_POTC_FlyingDutchman-Barnacles_ModelMiniature_003.jpg`。觀察：船尾高且突出、甲板兩頭高於中部、三桅帆裝、顏色為骨黃灰；沒有據此量出確切真船公尺數。
- 艏部半吋模型：`900w-600h_04_WDA_POTC_FlyingDutchman-Model-47_011.jpg`。觀察：兩組三管以三角排列、砲口朝前，尖頂欄板與海蝕凸紋。新船以六門固定普通追擊砲呈現三聯輪廓，不宣稱旋轉砲遊戲功能存在。
- 艉部半吋模型：`900w-600h_08_WDA_POTC_FlyingDutchman-Model-55_005.jpg`。觀察：下方寬半圓迴廊、中央高拱、向外分枝的冠。潮墓號的破星盤與潮痕為 Sirius 設計。

## 歷史结构參考（不是原船線圖描摹）

- [Vasa museum 官方模型頁](https://www.vasamuseet.se/en/visit/exhibitions/vasa-model)，1:10模型照片 `vasa_model_ccby.jpg`：Anneli Karlsson/Vasamuseet/SMMTF，CC-BY（依来源頁標示；未指定版本）。保存原圖署名。親看：雙砲層、三層高尾鏡、兩側迴廊、艉窗與構件層次。
- [Vasa 官方尺寸FAQ](https://faq.vasamuseet.se/category/45/article/4707?lang=en)：甲板四層通長，歷史頭頂空間遠小於潮墓號遊戲用2.5m層距；桅高為研究重建估值。这里只借结构概念，不把其數字當新船驗收值。
- [Vasa 事故研究](https://www.vasamuseet.se/en/explore/vasa-history/disaster)：上重下輕與過窄的水下體積。不直接搬其穩性；新船更寬船腹與遊戲壓艙仍需實測，不宣稱真船安全。
- [Batavialand 官方 Batavia 問答](https://www.batavialand.nl/en/zien-en-doen/het-schip-batavia/vraag-en-antwoord/)：復建船柱間長45.28m、寬10.5m、最大吃水5.10m、三桅十帆。館方承認非精確複製；本船52m/13.4m是重新設計。
- [Rijksmuseum Prins Willem1651 模型](https://id.rijksmuseum.nl/200401032)：同時代館藏模型NG-NM-11911，58砲，物件影像公有領域；本次尚未下載或親看，僅作後續尾鏡細節入口。
- [Rijksmuseum研究文章](https://bulletin.rijksmuseum.nl/article/view/9672)：PDF尚未逐頁讀，本次不從它取線形數值。

## 確認過的遊戲介面

2026-10-13 讀 `ArtGallery/HtmlGames/_build/ame_constitution_broadside/js/05_hull.js` 與 `10_ship.js`：0.1m／格需跟已載船相同；設計水線從 `kind=ship, waterline_z`；砲用 `kind=gun,gun=24l|18chase` 與 muzzle/breech；帆桁用 pivot、kind=yard、mast、sail；新帆與繩帶meta且匯出ends。

露天站位、鏡頭與瞄準區間仍需要船型清單 `geo`；完整資產交付時會提供該船建議值及來源。構造本身先驗收，遊戲程式由其作者串接。
