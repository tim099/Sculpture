# 蠍子號（1666 年的黎波里 galiot）研究報告（TASK-0023 步驟 3，2026-11-23）

Claude-Ojousama 整理。三個研究子代理（唯讀，2026-11-23 12:47–13:10 UTC）分頭讀已下載的掃描，原文照抄、換成公尺、標可信度；這份是三份報告的原文合本，前面加一張「本船用了哪一條」的總表。
子代理的機器可讀讀數（readings.json）、裁圖、逐頁轉錄在 Paperclip 工作目錄 `.work/FAR-92/scorpion/research/{italy_agent,frenchdutch_agent,barbary2_agent}/`（不進作品 repo）。

## 本船用了哪一條（plan.json 的 src 用這些代號）

| 項目 | 本船 | 依據（代號見 plan.json 的 sources） | 衝突與取捨 |
|---|---|---|---|
| 每舷槳座 | 20 | HAE f18r 1581 年 36 艘中位數 20；JAL（Dortières）20 bancs；AUB 16 或 20 | PAN 16–23、FOU／DAS 16–25、FUR 15；Dan 23–24 是 galère |
| 每槳人數 | 3 | HAE f16r、FOU p.49、DAS p.10、PAN p.148（18–22 banchi ⇒ 3） | FUR galeotta 2、AUB 1（17 世紀末法國）；HAE 說船尾段常 4 人 —— 沒做 |
| 船長／寬／深 | 35.1／4.7／1.7 m | JAL 轉引 Dortières：108 pieds／14 pieds 5 pouces／5 pieds 3 pouces（只讀 OCR，Jal 自己的公制換算對得上） | FUR「半艘 galea」22.8 m 放不下 15 座（子代理算過）；PAN 說北非的常跟 galea 一樣大（約 45 m） |
| 槳座間距 | 1.3 m | CRE 5 palmi 1.32 m、FUR 5½ palmi 1.39 m | 人的尺寸，不跟船縮 |
| 龍骨、兩柱 | 龍骨 0.768 L、兩柱各伸 0.116 L；艏柱高 1.44 倍深、艉柱 2.16 倍深 | FUR p.26、p.28（146＋22＋22 ＝ 190） | CRE 龍骨 0.71 L、DAS 0.78 L |
| 平面形狀 | V 線寬 0.64、X 站寬 0.51、船尾端 0.2 | FUR p.19–23 站寬（16／25、13¼／25、5／25） | 格子寬只能是奇數：X 站 0.51 或 0.56，取近的 |
| 舷外槳架 | 6.3 m（1.33 倍船寬） | CRE telaro 28 ÷ 甲板寬 21 | FUR 32／25 ＝ 1.28（推定） |
| 中央走道 | 0.5 m 寬、0.6 m 高 | FUR p.80 galeotta 2¼ palmi 寬、同高（0.57 m） | 格子奇數寬 5 格最接近 |
| 槳 | 8.2 m，舷內 2.6 m（0.32） | FUR 32%、CRE 31%；舷內 ＝ 槳栓到中央走道邊 | 槳全長史料沒有 galiote 的值 |
| 桅 | **1 根**，離船首 0.40 船身、甲板以上 16.0 m、直立 | FOU、DAS、PAN p.48、DAN p.308、JAL、AUB、NOO、NOO2、LUY 都單桅；位置 NOO 0.43、PAN／CRE 1/3；高 NOO 0.47 船身 | DEW 雙桅（小景，不採用）；FAR-87 規劃寫兩桅（推測）—— 改掉 |
| 帆桁 | 31.5 m（0.9 船身） | NOO 1.05、NOO2 0.79、FUR 185／180、CRE 50 cubiti／58 | 取中間 |
| spur | 伸出 4.2 m（0.12 船身） | NOO 0.12、FUR 0.125、CRE 0.138 | LUY 0.24、DEW 0.22 誇張 |
| 船首 | 低平台（跟中央走道同高），不做高 rambade | HAE f17r「no lleuan … arrumbadas」、DAN「sans chasteau de prouë」、PAN p.48 不設 rembate；NOO、LUY 畫的低平台 | — |
| 砲 | 8l ×1（中線）＋ pierrier ×2 | FUR p.80 三門：中間最大、兩旁 Kammerstücklin（後膛、打鏈彈霰彈）；HAE cañón de crujía；DAN、FOU 一門 coursier；AUB 2–3 pierriers | FAR-87 規劃約 9 門 —— 沒有史料，拿掉 |
| 船尾 | 骨架加布的拱篷、艉燈 | DAN 船尾艙可拆、FUR Poppa 小一點、LUY 拱頂篷與大艉燈 | NOO 看不到篷 |
| 吃水 | 1.1 m | 設計決定（史料沒寫） | — |

## 單位
- Furttenbach 的 palmo：p.19「10 Zöll von einem Nürnberger Werckschuch」；紐倫堡工尺 303.86 mm（Doursther 1840 p.414）⇒ 0.2532 m。
- Crescentio：拿坡里 palmo 0.26367 m（Tavole 1877 p.447）。
- pied de roi 0.32484 m（Doursther p.408）；馬賽 pan 0.2516 m（Doursther p.375）。

## 主要衝突（照實寫，之後再定）
- 1666 年的黎波里 galiot 沒有直接的文字證據：DAN p.315 說的黎波里 1618 年起改用帆船；本船的規格是用 HAE（阿爾及爾 1581）、JAL（法國 17 世紀末）、NOO（的黎波里港外的槳帆船畫）推的。
- galeota 與 galère 常被混用（DAN 把 HAE 的 galeota 名單抄成 galères）。
- 單桅／雙桅：文字一致單桅；只有 DEW 小景雙桅。

---

## 子報告：italy_agent

### 義大利、德國造船書與度量衡表：galea／galeotta 的讀數（italy_agent，2026-11-23 12:47–13:10 UTC）

> 子代理寫 report.md、sources.md 被寫檔工具擋下，報告全文在它的最後回覆裡；Claude-Ojousama 原樣存成這個檔（13:11 UTC）。
> 機器可讀版：`readings.json`（79 筆）；逐頁轉錄：`furt_p19-24.md`、`furt_p25-31.md`、`furt_p52-59.md`；裁圖：`crops/`。

#### 10 行重點
1. **Furttenbach 的 palmo 他自己有定義**，p.19 原文：「Ein Palmo … dessen Lenge betregt. 10. Zöll von einem Nürnberger Werckschuch」。Doursther p.414 的紐倫堡工尺是 303.86 mm，所以 1 palmo ≈ **0.2532 m**（中）。熱那亞 palmo 是 0.248083 m（Tavole p.321），差約 2%。
2. **Crescentio 明寫用拿坡里單位**，p.13：「cubiti (sono queste misure di cubiti & palmi Napoletani)」。palmo napoletano 取 0.263670 m（Tavole p.447，1840 年以前）。1 cubito ≈ 3 palmi 是代理用書內數字對帳推出來的（中-低）。
3. 普通 galea（Furttenbach）：船體 180 p＝**45.6 m**，書中示範的大船 190 p；sperone 22½ p＝5.7 m；龍骨 146 p＝37.0 m。數字讀得清楚（高），換成公尺是中。
4. 船殼最大寬 25 p＝**6.33 m**；深（肋材總高）8⅓ p＝2.11 m；槳架總寬推定為 32 p＝8.1 m（中，推定）。
5. 每舷 27 banchi，槳座間距 5½ p＝**1.39 m**；槳長 48½ p＝12.3 m，舷內段佔 32%。主桅 90 p＝22.8 m，主帆桁 185 p＝46.8 m，前桅 54 p，前帆桁 112 p。數字高，換算中。
6. Galeotta 原文（p.80）只講三件事：一律照「一半大」；corsia 2¼×2¼ p＝0.57 m（不照一半）；每舷 15 支槳、每支 2 人；船首 3 門砲。照一半推算：船體 90 p＝**22.8 m**、寬 12½ p＝3.17 m、深 1.06 m（低，推算）。
7. 但 15 支槳 × 5½ p＝82½ p，半艘 galea 的 90 p 船體放不下首尾。所以真正的 galeotta 應該比「半艘」長，Pantera 也說 galeotta 有 17–23 banchi。
8. **Pantera p.48（看過原圖）**：北非（Barbaria）的 galeotta 常常「grãdi come le galee ordinarie」，只是不裝 rembate、不立前桅，掛 galeotta 的名義是為了不被蘇丹徵調。**所以的黎波里那艘不一定是半艘大小。**
9. 圖版 Nr.3 比例尺是 50 palmi＝894.5 px（scan 00102，x 675→1569.5），即 17.89 px/palmo。量得船長 190.6、主桅 89、前桅 52.9、主帆桁 184.9 palmi，都跟正文吻合；只有前帆桁量成 98，跟正文 112 不合，以正文為準。
10. 兩本書換成公尺後幾乎一致：全長約 46 m、槳約 12 m、舷內段約 31%、槳座間距 1.32–1.39 m。吃水、乾舷、carrozza／tendale 的尺寸在已讀頁面都找不到（unverified）。

#### 主尺寸對照表
| 項目 | Furttenbach galea（palmi，×0.2532 m） | 半艘 galea（推算） | galeotta 原文 | Crescentio galea（拿坡里單位） |
|---|---|---|---|---|
| 船體長 | 180 p＝45.6 m（p.19） | 90 p＝22.8 m | 只說「一半大」 | 58 cubiti≈174 p＝45.9 m（p.23） |
| sperone | 22½ p＝5.70 m | 11¼ p | — | 24 p＝6.33 m（p.25） |
| 龍骨 | 146 p＝37.0 m（p.26） | 73 p | — | 41 cubiti＝32.4 m（p.13） |
| 最大寬 | 25 p＝6.33 m（p.19、p.31） | 12½ p＝3.17 m | — | 甲板橫樑 Lata 21 p＝5.54 m（p.22） |
| 槳架寬 | Giogo della Poppa 32 p＝8.10 m（大船 37 p）（p.23，推定） | 16 p＝4.05 m | — | telaro 28 p＝7.38 m（p.24） |
| 深 | 8⅓ p＝2.11 m（p.31）；艉柱總高 18 p（p.28） | 4⅙ p | — | Matera 到 cordone 6¼(?) p＋contoval 1½ p（p.23） |
| banchi／舷 | 27（p.54） | 13½ | **15**（不照一半） | 26（p.24） |
| 每槳人數 | 6（p.55） | — | **2** | — |
| 槳座間距 | 5½ p＝1.39 m（p.54） | — | — | 5 p＝1.32 m（p.24–25） |
| corsia | 外寬 3⅔、外高 4 p（p.20） | 1⅚ × 2 p | **2¼ × 2¼ p**（不照一半） | 內寬 3⅓(?) p；高：中部 2¼、首尾 3 p（p.22、24） |
| 槳 | 48½ p＝12.28 m，舷內 15½ p（p.55–57） | 24¼ p | — | 45½ p，舷外 31½、舷內 14 p（p.26） |
| 主桅／主帆桁 | 90／185 p（p.52） | 45／92½ p | — | 27／50 cubiti（p.25） |
| 前桅／前帆桁 | 54／112 p（p.52） | 27／56 p | — | 18／32 cubiti（p.26） |
| 船首砲 | 5 門（p.58） | — | **3 門** | — |

Galeotta 其他「不照一半」的地方（Furttenbach p.80）：
- 槳架上的 drapera 只要第二道。
- 船首不搭頂篷。
- Poppa「etwas kleiners」（小一點，沒說小一半）。
- 只有 2 個錨。

Bergantino（p.80–81）：「¼ 艘 galea」，船身 60 p、最寬 16 p，沒有 corsia，每舷 10 支槳、一支一人。60／16 這兩個數字沿用前人轉錄，代理沒重核原圖（中）。

Pantera 的其他數字：
- p.148：galeotta 16–18 banchi 每槳 2 人，18–22 banchi 每槳 3 人；fusta 和 bergantino 一槳一人；普通 galea 25–26 banchi，每槳至少 5 人。
- p.48：bergantino 8–16 banchi。
- p.47：主桅在「per la terza parte vicino alla prora」（距船首 1/3）。

#### 單位表（照抄表上數字）
| 單位 | 公尺值 | 出處 |
|---|---|---|
| palmo di Genova | 0,248083（「Tre Palmi fanno la Gua o Goa misura usata nei lavori marittimi」） | Tavole 1877 p.321，IA n316 |
| palmo di Genova | 249.1000 mm | Doursther 1840 p.374，n386 |
| palmo napoletano | 0,263670（1840 年以前）／0,264550（1840 年法定） | Tavole p.447，n437 |
| palmo napoletano | 262.0145 mm | Doursther p.375，n387 |
| palmo romano architettonico | 2,234218÷10＝0.2234218 | Tavole Roma，n606 |
| palmo romano architettonico | 223.4250 mm | Doursther p.375 |
| palmo romano mercantile | 1,991897÷8＝0.248987 | Tavole Roma，n606 |
| palmo romano 商用 | 249.0000 mm（du commerce）／212.0000 mm（des marchands） | Doursther p.375 |
| 紐倫堡 Stadtfuss | 303.86 mm | Doursther p.414，n426 |
| piede veneto | 347.74 mm（Paxos 條）／347.4 mm（Valvasone 條） | Doursther p.414、p.417；「Venise」本條沒下載，unverified |

Pantera 沒有寫 palmo 的種類，不確定。如果要換算，列羅馬的兩種值（建築用 0.2234、商用 0.2490）。

#### 來源
- Furttenbach 1629：BSB bsb10862644，頁面網址 `https://www.digitale-sammlungen.de/en/view/bsb10862644?page=<scan>`；Augsburg 藏本是 bsb11202702。
- Pantera 1614：IA bub_gb_QWc4VQj-kqIC、bub_gb_SSt-lVTlOd0C。
- Crescentio 1607：IA nauticamediterra00cres（印刷頁 p.13＝n28，p.22–27＝n37–n42）。
- Doursther 1840：IA dictionnaireuniv00douruoft（代理用 IA 搜尋查到，沒逐頁比對是不是同一份掃描，推定）。
- Tavole 1877：IA bub_gb_DmznAAAAMAAJ（同上，推定）。

---

## 子報告：frenchdutch_agent

### 法國、荷蘭造船書與辭典：galiote 的讀數（frenchdutch_agent，2026-11-23 12:49–13:01 UTC）

> 子代理寫 report.md 被寫檔工具擋下，報告全文在它的最後回覆裡；Claude-Ojousama 原樣存成這個檔（13:02 UTC）。
> 機器可讀版：`readings.json`（51 筆）；來源網址：`sources.md`；頁面裁圖：`pages/`。

#### 重點
1. galiote：Fournier 1643 p.49–50 和 Dassié 1677 p.10 寫的一樣，「16 jusques à 25 bancs … à trois hommes sur chacune」，只有主桅，帶小砲（兩處都對過圖，高）。
2. Aubin 1702 寫每舷 16 或 20 bancs、每槳 1 人、1 支桅、2–3 門 pierriers，水手兼當兵（只有 OCR，兩本一致，中）。同一詞條下的荷蘭 galjoot（85 piés）和 galiote à bombe 不是本船，已經排除。
3. galiote 的主尺寸只在 Jal 1848 找到，他轉引 Dortières：長 108 pieds = 35.08 m、寬 14 pieds 5 pouces = 4.68 m、深 5 pieds 3 pouces = 1.71 m（只有 OCR，但 Jal 自己的公制換算對得上，中）。同段的「70 rames」跟「20 bancs」對不起來，這個 70 未證實。
4. galère（Dassié，對過圖）：58 goües（約 22 toises）= 42.4 m，寬 3 toises = 5.85 m，高 1 toise = 1.95 m；平常 25 bancs、每槳 5 人；槳長 40 pieds 6 pouces = 13.16 m；coursier 寬 1.5 pied = 0.49 m；éperon 伸出 11 pieds 3 pouces = 3.65 m。
5. galère 的桅、桁和砲（Dassié p.135、p.154，對過圖）：主桅 30 goües ≈ 21.9 m，前桅 22 goües ≈ 16.1 m；antenne 由 peine 和 quart 兩根搭接，搭接長度原書沒寫；砲是 1 門 36 livres coursier、2 門 8 livres、2 門 4 livres、12 門 perriers。
6. 主桅位置：p.131 寫在 5 等分的第 2 份（只有 OCR）；p.117 寫 escasse 在第 17 banc 附近（對過圖）。從船首還是船尾算，原文沒寫。
7. 用 Jal 和 Dassié 的數字推算，galiote 大約是 galère 的 0.8–0.87 倍。但 Jal 說北非的 galiote 有 25–26 bancs、單桅，跟一般 galère 差不多大，所以的黎波里那艘的比例可能接近 1.0（這是代理的推論，不是原文）。
8. 北非：Fournier p.49 寫 Barbarie 的 galère「mettent souvent la Pouppe bas, & n'ont qu'un Canon de Coursie」（對過圖）。速度、砲位、每槳人數的數字都沒找到。
9. 單位：pied de roi 0.32484 m（Doursther p.408）、馬賽 pan 0.2515875 m（Doursther p.375），兩者都對過圖。Dassié 自己把 pan 算成 9 pouces de roi = 0.2436 m，比 Doursther 小約 3%。
10. 沒有數字、標為 unverified：pied de Marseille 和 Amsterdam voet（手上的 Doursther 頁裡沒有）、bancs 間距、apostis 舷外寬、galiote 的桅高。Witsen p.193 的槳數印成「1ò」，看不出是 10 還是 16。

#### 0. 單位
| 單位 | 值 | 原文 | 信心 |
|---|---|---|---|
| pied de roi | 0.32484 m | Doursther p.408（n420，對過圖）：「Le pied de roi, ancienne mesure de Paris, se divisait en 12 pouces = 144 lignes = 1728 points, et sa valeur légale est de 324.83938497 millimètres … 144 » 12.789 324.84」 | 高 |
| 馬賽 pan／palme | 0.2515875 m | Doursther p.375（n387，對過圖）：「MARSEILLE. Le pan ou palme = 8 menus = 9 pouces = 96 lignes . . 111.53 9.905 251.5875」 | 高 |
| Dassié 的 pan | 0.2436 m | Dassié p.121（對過圖）：「…goües, chacune estant composée de trois pans ou de trois palmes, & chaque pan revient à neuf pouces, de maniere que la cane de Provence estant de 8 pans, elle vaudra 6 pieds de Roy, ou une toise.」 | 高 |
| goüe | 0.7309 m（Dassié 算法）／0.7548 m（Doursther 算法） | 1 goüe = 3 pans | 高 |
| pied de Marseille | 未證實 | 手上的 Doursther 頁裡沒有 | — |
| Amsterdam voet | 未證實 | 手上的 Doursther 頁裡沒有 | — |

#### 1. galiote

原文：
- Fournier p.49–50（對過圖）：「Galiote, est vne Galere de seize iusques à 25. Bancs ou Rames à trois hommes sur chacune, n'ont que l'Arbre de Maistre, & ne portent que de petits Canons」
- Dassié p.10（對過圖）：「Galiote, est une galere de 16 jusques à 25 bancs où rames à trois hommes sur chacune, elle n'a que l'arbre de mestre, & porte des petits canons.」
- Aubin 1702（只有 OCR，兩本一致）：「…petite galère propre à aller en course… Elle ne porte qu'un mât, & n'a que seize ou vingt bancs à chaque bande, avec un seul homme à chaque rame: elle n'est montée que de deux ou trois pierriers. Les matelots y sont soldats…」
- Jal 1848，約 p.759–760（只有 OCR）：
  - 「A la fin du XVIIe siècle, la Galiote avait, en France du moins, 20 bancs et un seul homme sur chaque rame…」
  - 「La Galiote à 70 rames avait, selon Dortières, 108 pieds de longueur (35m 08), 14 pieds 5 pouces (4m 68) de largeur, et 5 pieds 3 pouces (1m 70) de creux.」
  - 「Les Galiotes barbaresques étaient, elles, à 25 et 26 bancs … et ne portaient qu'un seul mât」
- 1831 年西班牙辭典（只有 OCR）：「Galera menor, que consta de diez y seis ó veinte remos por banda, y solo un hombre en cada uno.」
- Witsen p.193（對過圖）：「Van Galeotta of klein roei-zee-vaertuig, en Brigantino noch kleinder, lang 60 span zwijge insgelijx, dees hebben 1ò riemen op.」
  - 60 span 照語法可能只是講 Brigantino。用 Toscana palmo 0.2918 m 試算約 17.5 m，信心低。
  - 「1ò」是 10 還是 16，未證實。

| 項目 | 數值 | 來源（信心） |
|---|---|---|
| 長／寬／深 | 35.08 m／4.68 m／1.71 m | Jal 轉引 Dortières（中） |
| bancs | 16–25（Fournier、Dassié，高）；每舷 16 或 20（Aubin，中）；20（17 世紀末法國，中）；北非 25–26（中） | |
| 每槳人數 | 3 人（1643／1677）或 1 人（1702 和 17 世紀末法國） | |
| 桅 | 1 支 | 高 |
| 砲 | 小砲，或 2–3 門 pierriers | |
| 桅高、帆桁長、船員人數 | 未證實 | |

#### 2. galère（Dassié 1677，除另註外都對過圖）
- 長：「58 goües, ou environ 22 toises」= 42.39 m（22 toises = 42.88 m）
- 寬：「environ trois toises」= 5.85 m
- 高：「une toise」= 1.95 m
- 龍骨：102 pieds = 33.13 m（p.121）
- bancs：「d'ordinaire de 25 bancs」、「5 à chaque banc」（p.117）；定義是 24–30 bancs（p.10）
  - Fournier：「Les nostres ont d'ordinaire 26. Rames. Nostre Reale & celle d'Espagne en ont 28. ou 29. & celle du grand Turc 33.」
- 槳：「54 pans ou bien 40 pieds six pouces」= 13.16 m（p.119）
- coursier：「large d'environ un pied & demi」= 0.49 m（p.117）
- apostis 單根木料：40 pieds × 8 × 6 pouces（p.126）
  - 舷外寬原書沒寫，未證實。旁證是 baccalas 10 pieds（3.25 m），以及 p.132「E E … avec sa largeur, sçavoir une de ses parties」，也就是寬 = 長的 1/5，約 8.5 m（代理的解讀）。
- bancs 間距：沒找到。
- éperon：「sort au dehors onze pieds trois pouces」= 3.65 m；taille-mer 20 pieds（p.129）
- 主桅位置：p.131（只有 OCR）「D D Est une échelle divisée en 5 parties égales, & à la deuxième partie doit estre l'Arbre de Mestre.」；p.117「L'escasse … vers le 17 banc.」
- 桅和桁（p.135）：主桅 30 goües（21.93 m），周長粗端 60 pouces、細端 40 pouces；主桅 antenne：peine 30 + quart 27 goües；前桅 22 goües（16.08 m）；前桅 antenne：peine 30 + quart 22 goües；antenne du Treou 20 goües。兩根搭接的長度沒寫。
- 砲（p.154）：「UN canon de courcier du calibre de trente-six livres. Deux Bastardes du calibre de huit livres. Deux moyennes du calibre de quatre livres. … Douze perriers de fonte」
- 舵 25 pieds（p.129）
- rambades：約 4.5 pieds 高、每座 14 或 15 人（人數只有 OCR）
- 船員（只有 OCR，約 p.164）：180 forçats ou Turcs、80 mariniers de rame、92 soldats、30 mariniers de rambade
- Witsen 寫的是托斯卡納的 galley（只有 OCR，信心低）：190 span、25/26 bancs × 5 人、主桅 90 span、帆桁 185 span。

#### 3. 北非
- Fournier p.49（對過圖）：「Celles de Barbarie pour euiter le rencontre, & estre plus legeres, mettent souuent la Pouppe bas, & n'ont qu'vn Canon de Coursie.」
- Fournier 第 II 卷（只有 OCR）：鄂圖曼的 galère「beaucoup plus legeres que les nostres」；「Ses principales Galeres sortent d'ordinaire d'Alger, Tripoli…」
- Witsen p.192（只有 OCR）：「Turcksche Galeyen voeren maer een mast.」
- Jal：北非 galiote 25–26 bancs、單桅。他的出處是 Pantera，需要對原書。
- 北非 galiote 的速度、砲位、每槳人數，在這些書裡都沒找到。

#### 4. 比例
| 項目 | galiote | galère | 比值 |
|---|---|---|---|
| 長 | 35.08 m | 42.39 m | 約 0.83 |
| 寬 | 4.68 m | 5.85 m | 約 0.80 |
| 深 | 1.71 m | 1.95 m | 約 0.87 |
| bancs | 20 | 25 | 約 0.8 |

北非的大型 galiote 可能接近 1.0（推論）。

---

## 子報告：barbary2_agent

### 北非記載與同時代的畫：galeota 的讀數（barbary2_agent，2026-11-23 12:47–13:10 UTC）

> 子代理寫 report.md 被寫檔工具擋下，報告全文在它的最後回覆裡；Claude-Ojousama 原樣存成這個檔（13:11 UTC）。
> 機器可讀版：`readings.json`（47 條）；來源：`sources.md`；裁圖：`crops/`（檔名有 `_grid` 的都標了原圖像素座標）。網路只用了 GET：IA 兩本書確認了書名年份，BnF 回 403 沒確認到。

#### 重點
1. Haedo 1612 f15v（頁面圖確認）：galeota 每舷 14–24 bancos，bergantín（＝fragata）8–13。
2. Haedo f16r：每槳 3 人，很多船在船尾那段是 4 人。f16v：士兵＝2×每舷 bancos，20 bancos 就是 40 人。
3. Haedo f17r：galeota「no lleuan … arrumbadas」，也就是不設船首高平台。
4. Haedo f18r 的 1581 年阿爾及爾名單：36 艘、15–24 bancos，中位數 20，最常見 22 和 18。
5. Dan 1649 p.308：北非 galère 只有一根桅、一門船首中線砲（coursier）、沒有船首堡、23–24 bancs、划手 200 人、士兵 100 人，船尾艙常拆掉。這是 galère 的數字，不是 galiot。
6. Tripoli：Dan p.307 說只有 1 艘 galère、很少出航。p.315 說從前最多 25 艘劫船、現在 7–8 艘，以前只用 brigantins 和 frégates，1618 年起改帆船。Narbrough 1676 也只看到帆船。在地文字沒有直接講 1666 年 Tripoli galiot 的句子。
7. Nooms 的 Tripoli 畫（SK-A-1398）：單桅；主桅在 0.43 船身；桅高 0.47 船身；帆桁 1.05 船身；spur 0.12 船身；看不到拱頂船尾篷。
8. Nooms 的阿爾及爾畫（SK-A-1396）三艘都是單桅，每舷可見約 16–18 支槳。Luyken 1684「Barbarÿsche Galeÿen」：單桅、約 23–24 支槳、船首一門砲、有大的拱頂船尾篷和艉燈，但 spur 0.24、桅高 0.62，都畫得比較誇張。
9. 建議：每舷 18–20 槳；每槳 3 人；1 根桅；主桅在 0.40–0.45 船身；桅高約 0.45–0.5；帆桁約 0.9–1.0；spur 約 0.12–0.15；船首低平台加一門中線砲；船尾做輕的、可拆的拱頂篷。
10. 衝突：De Wit 1670–72 的 Tripoli 小景是雙桅（前桅前傾約 5°）；Dan 把 Haedo 1581 的 galeota 名單抄成「galères」、年份寫成 1588；兩人的 brigantin 級距也對不上（Dan 15 bancs，Haedo 8–13）。舷外槳架每張圖都是側視，量不到。

#### A. 文字（原文照抄；只依 OCR 的標「OCR」）

#### A1. 船型規格
| 來源・頁 | 原文 | 數值 | 信心 |
|---|---|---|---|
| Haedo f15v，Cap. XXI（頁面圖確認） | 「Los vajeles de que vsan para andar en corso, son galeotas ligeras, o vergãtines, a que llaman ellos fragatas: el vergantin es de ocho hasta treze vancos, o remos por vanda, y la galeota de catorze hasta veyntyquatro.」 | galeota 每舷 14–24；bergantín／fragata 8–13 | 高 |
| Haedo f16r（頁面圖確認） | 「porq casi todos lleuan a tres por cada remo, y muchos a quatro ( alomenos en el quartel de Popa)」 | 每槳 3 人，船尾段 4 人 | 高 |
| Haedo f16r→f16v（頁面圖確認） | 「…que junto a cada vanco sobre las vallesteras, va vna vancada o asiento hecho de madera, sobre el qual van assentados dos soldados en cada vno: demanera que lleuando vna galeota veynte remos o vancos por vãda, lleua otras que tantas vancadas, y en ellas quarenta soldados」 | 士兵＝2×每舷 bancos | 高 |
| Haedo f16v–f17r（頁面圖確認） | 「segun traen sus galeotas tan listas, tan en orden, y tan ligeras」；「…para poder bien correr y prohejar, que por esso no lleuan en ellos arrumbadas, ni permiten que vna espada, ni arcabuz vaya colgada, ni arriba sobre cubierta」 | 船很輕快；不設 arrumbadas | 原文高；把 arrumbada 解讀成船首平台是中 |
| Haedo f18r，Cap. XXII「…en Argel el año 1581」（逐條核對頁面圖） | 「1 El Rey Iafer, renegado Vngaro, vna de veyntyquatro vancos. … 5 Morato Raez el grande, renegado Albanes, dos de veyntiquatro vancos. … 21 El Cayde Mahamet, judio de nacion, vna de quinze vancos.」 | 15 bancos×2 艘、18×10、19×1、20×8、22×11、23×1、24×3；平均 20.2 | 高 |
| Haedo f18v，Cap. XXIII（頁面圖確認） | 「OTROS Cossarios ay de fragatas, que son vergantines, de ocho hasta treze vancos … todos lleuan sus armas, arcabuzes, o buenos arcos o flechas … aura como veynte, o veynticinco.」 | fragata 的划手是自由人，兼打仗；約 20–25 艘 | 高 |
| Haedo，Epitome de los Reyes Cap. XXVI §1，1589 年的事（OCR） | 「[OCR] vna galera de veynte y tres bancos, llamada la Serena … la galeota,la qual auia facadofucra el cañón de cruxia」 | galeota 有一門中線砲（cañón de crujía） | 中，頁碼未定 |
| Dan p.307 底–p.308（頁面圖確認） | 「…celles des Corsaires sont plus petites, & n'ont qu'vn arbre, & qu'vn canon de coursier, sans espalier, ou fort peu … & sans chasteau de prouë. Elles ne laissent pas toutesfois d'estre de vingt-trois à vingt-quatre bancs, mais grandement pressez, & où la chiourme, qui est de deux cens esclaues…」 | galère：單桅、一門砲、23–24 bancs、200 名划手（每槳約 4.2 人） | 高 |
| Dan p.308（頁面圖確認） | 「…à démonter la chambre de poupe, quand ils voyent que le vent les incommode; & … cent bons soldats armez de mousquets, de cimeterres, & d'arcs」 | 船尾艙可拆；士兵 100 人 | 高 |
| Dan p.307（OCR） | 「En Alger … quatre, en l'an mille six cens trente-quatre; deux … de vingt-quatre bancs, & les deux autres de vingt-trois, auec vn brigantin de quinze bancs, & huit fregates de cinq à six bancs」 | 1634 年阿爾及爾：4 艘 galère、1 艘 brigantin（15 bancs）、8 艘 frégate（5–6 bancs） | 高 |

Haedo 和 Dan 都沒寫 galeota 的桅數、砲數，也沒有速度數字或船身尺寸。

#### A2. 跟 Tripoli 有關的句子
- Dan p.307（OCR）：「A Tripoly de Barbarie, il n'y en a qu'vne; encore va-t'elle rarement en course.」——只有 1 艘 galère，很少出航。信心高。
- Dan p.315（頁面圖確認）：「…il y a eu autresfois jusques à vingt-cinq vaisseaux de course; mais il n'y en a que sept ou huict maintenant … Ils n'vsoient autresfois que de brigantins, & de fregates; mais en l'an mille six cens dix-huict, vn certain Renegat Grec, nommé MAMI RAYS, leur apprit à se seruir de vaisseaux ronds.」信心高。
- Dan p.253（OCR）：「…bien qu'elle soit la moins puissante de toutes en vaisseaux」——北非各城中 Tripoli 的船最少。
- Dan p.255（頁碼頁面圖確認，句子依 OCR）：講同一件事，但年份寫成 1619。Dan 自己 1618／1619 不一致。
- Dan p.254（OCR）：1638 年有 3 艘 Tripoli「vaisseaux」被馬爾他擄走，沒寫是什麼船型。
- Haedo f17r（頁面圖確認）：「…van con la pressa a Tunez, o a Viserta, o a los Gelues, o a Tripol」——Tripoli 是銷贓港。
- Haedo f17v（OCR，沒有這頁的頁面圖）：「y como en Argel ayvno,en Tripoi o- tro」——Tripoli 也有蘇丹派的海盜統領。
- Haedo，Dialogo segundo，1561 年的事（OCR）：「tres grueíTas galeotas de Tripol」——3 艘「粗大的」Tripoli galeotas。
- Narbrough 1676（EEBO A52619）：「four of the Tripoli Ships of War … which was all that were in the Port」；另外擄了一艘政府的「Samberkeene」。
- Ogilby 1670（Dapper 英譯，OCR 很亂）：1668 年阿爾及爾名單裡有「Two Sateer, ewo Gallies i4」。信心低。

#### B. 圖（像素量，都沒有比例尺，透視讓數字只能當「約」）

定義：「船身」＝船首柱到船尾，不含 spur；主桅位置從船首柱算。

#### B1. Nooms〈Gezicht op Tripolis〉1662–68，SK-A-1398（6752×3760）——唯一一張畫在 Tripoli 港外的槳帆船
- 方向與桅：船首朝右，高船尾在左，單桅。
- 船身與 spur：船尾柱頂約 (2210,3175)，船首端約 x 3450，船身 1240 px。spur 尖約 (3600,3368)，spur 長 0.12 船身。
- 主桅：桅腳約 (2915,3385)，在 0.43 船身。桅頂約 (2890,2800)，桅高 0.47 船身。桅頂略偏船尾，看不出前傾。
- 帆桁：兩端約 (2180,3010) 和 (3450,3300)，長 1.05 船身，約 2.2×桅高，帆捲在桁上。
- 槳：可見 12–14 支，照間距推到整個划槳區約 17–18 支，這只是推估。
- 其他：船首是低矮的暗色方塊平台，上面站 2 人；船尾看不到拱頂篷；燈和砲看不清；桅頂紅旗。
- 裁圖：`nooms1398_galley_grid.jpg`、`_bow_x2`、`_stern_oars_x2`

#### B2. Nooms〈Algiers 1662〉，SK-A-1396（7141×4068）
- 三艘都是單桅，船首都朝左。
- G1：全長約 1085 px（船首尖約 (2320,3545) 到船尾約 (3405,3470)）。主桅在 0.52 全長，桅高 0.34 全長，帆桁 0.79 全長（約 2.3×桅高）。spur 跟船首平台連在一起，分不出長度。
- 可見槳：G1 約 16±2 支，G2 約 17±2 支。
- 看不到拱頂船尾篷；桅頂紅旗。

#### B3. Luyken〈Barbarÿsche Galeÿen〉1684，RP-P-1896-A-19368-451（6380×3604）
- 這是 Dan 荷文版 p.299 的插圖；BnF btv1b2000020m f20 是同一塊版的另一份印本。
- 船首朝左，單桅、直立。
- 船身與 spur：spur 尖約 (1047,2620)，船首柱約 x 2000，船尾約 x 5917。spur 長 0.24 船身。
- 主桅與帆桁：主桅在 0.29 船身，桅高 0.62 船身。帆桁 (2043,2319)–(4426,672)，長 0.74 船身。
- 槳：用灰階自相關算出週期 66 px，每舷約 23–24 支。但槳區只佔船身 0.21–0.61，畫得很擠。
- 船首：低平台上一門中線砲，砲口約 (1833,2555)，沒有船首堡——跟 Dan 的文字一致。
- 船尾：拱頂 carrosse 長 0.245 船身，有窗；篷頂一盞大艉燈。

#### B4. De Wit〈Tripoli in Barbaria〉1670–72，NG-20-B 小景（量的是 1572×873 裁圖）
- 雙桅：前桅前傾約 5°，在 0.12 船身處；主桅在 0.55 船身處。
- spur 長 0.22 船身。
- 船尾是圓頂篷；船尾那個圓筒物是燈還是砲看不清。
- 信心低，小景可能是轉抄來的。

#### B5. Dapper／Van Meurs〈De Stadt TRIPOLIS〉1668，RP-P-2018-3690
- 右前景那艘（被畫框切掉）：spur 長約 0.47×桅高，帆桁約 1.26×桅高；船首是方箱平台加欄杆；桅頂紅旗。
- 左邊那艘：單桅，船尾掛一面大紅旗。
- 中景：一艘雙桅小船。
- 信心低，是想像構圖。

#### B6. 只當造型參考（沒有標北非）
- Casembroot〈Turkse galei〉RP-P-BI-5627：雙桅，拱頂篷加大艉燈；透視太強，沒量比例。
- Hollar 1665：雙桅，拱頂篷加大艉燈；標題沒確認。
- Nooms 素描 Leiden PK-T-AW-1612：雙桅；標題和國籍都沒確認。
- Van de Velde 1676（Narbrough 在 Tripoli 燒船）：從縮圖看只有帆船和小艇，沒有槳帆船。

#### C. 設計建議表
| 項目 | 建議 | 依據；衝突並列 |
|---|---|---|
| 每舷槳數 | 18–20（最大 22） | Haedo：galeota 14–24，1581 年中位數 20；Nooms 兩張可見約 16–18。衝突：Luyken 約 23–24、Dan 23–24，那是 galère 的級距 |
| 每槳人數 | 3 人（船尾段 4 人） | Haedo f16r。衝突：Dan 的 galère 約 4.2 |
| 士兵 | 2×每舷 bancos | Haedo f16v；Dan 的 galère 是 100 人 |
| 桅數 | 1 根 | Dan p.308；Nooms 四艘；Luyken。衝突：De Wit、Dapper 中景是雙桅 |
| 主桅位置 | 0.40–0.45 船身 | Nooms 1398 是 0.43；Nooms 1396 是 0.52 全長；Luyken 0.29 船身（版畫壓縮） |
| 桅高／船身 | 約 0.45–0.5 | Nooms 1398 是 0.47；Nooms 1396 是 0.34 全長。衝突：Luyken 0.62、De Wit 0.83 |
| 帆桁／船身 | 約 0.9–1.0（約 2×桅高） | Nooms 1398 是 1.05；Nooms 1396 是 0.79 全長。衝突：Luyken 0.74（1.2×桅高） |
| spur／船身 | 約 0.12–0.15 | Nooms 1398 是 0.12。衝突：Luyken 0.24、De Wit 0.22 |
| 船首平台 | 低平台，不做高起的 rambade；中線一門砲 | Haedo f17r「no … arrumbadas」；Dan「qu'vn canon de coursier … sans chasteau de prouë」；Haedo 的「cañón de cruxia」；Luyken；Nooms 1398 |
| 船尾篷 | 輕的、可拆的拱頂篷（骨架加布） | Dan「démonter la chambre de poupe」；Nooms 兩張都看不到篷。衝突：Luyken 是大的木造 carrosse，De Wit 是圓頂篷 |
| 燈 | 船尾一盞（可以省略） | 只有 Luyken 畫得清楚 |
| 旗 | 桅頂紅旗；船尾可加大紅旗 | Nooms 1398、Nooms 1396、Dapper |
| 舷外槳架外伸 | 沒有依據 | 每張都是側視 |

#### 主要衝突
- **galeota 和 galère 混用。** Dan 把 Haedo 1581 的 galeota 名單抄成「galères」，年份寫成 1588。Luyken 那張圖配的就是 Dan 講 galère 的段落。所以 galiot 的槳數應該用 Haedo 的 14–24，不要用 Dan 的 23–24。
- **brigantin 的級距對不上。** Haedo 寫 bergantín 8–13 bancos；Dan 寫 1634 年的 brigantin 是 15 bancs、frégate 是 5–6 bancs。
- **1666 年 Tripoli 的 galiot 沒有直接證據。** 那時 Tripoli 的主力已經是帆船。這艘船的規格只能從 Haedo 的阿爾及爾資料和 Nooms 的 Tripoli 畫來推。

---

## 來源清單：frenchdutch_agent



| 書 | 版本 | IA identifier／網址 | 本次看過的頁面圖 |
|---|---|---|---|
| Dassié, *L'architecture navale* | Paris 1677 | larchitecturenav00dass（https://archive.org/details/larchitecturenav00dass）；另一本 bub_gb_D8oimSGFcu4C（只用 OCR） | p.9、p.10（sources/texts）；p.117 n146、p.119 n148、p.120 n149、p.121 n150（/tmp/gal）；p.126 n155、p.129 n158、p.132 n165、p.135 n168、p.154 n187（pages/） |
| Fournier, *Hydrographie* | Paris 1643 | bub_gb_TpiRM6s3KmAC | p.49、p.50（sources/texts） |
| Witsen, *Aeloude en hedendaegsche scheeps-bouw en bestier* | Amsterdam 1671 | aeloudeenhedenda00wits（JCB）；gri_33125008247716（Getty，只用 OCR 比對） | p.193 = n214（/tmp/gal/w_n214.jpg；裁圖 pages/witsen_p193_*.jpg） |
| Aubin, *Dictionnaire de Marine* | Amsterdam 1702 | bub_gb_KJ2Xb1rZUsEC；10871859bsb | 沒看圖，只用 OCR（兩本 OCR 互相比對） |
| Jal, *Glossaire nautique* | Paris 1848 | bub_gb_xZw_AAAAcAAJ | 沒看圖，只用 OCR（GALIOTE 詞條，約 p.759–760） |
| *Diccionario marítimo español* | Madrid 1831 | diccionariomarit00madruoft | 沒看圖，只用 OCR |
| Doursther, *Dictionnaire universel des poids et mesures* | Bruxelles 1840 | sources/units/Doursther1840_IA-n*.jpg | p.374 n386、p.375 n387、p.408 n420（另 n421/n426/n429 只看了概覽） |

頁面圖網址格式：`https://archive.org/download/<identifier>/page/n<N>_w1600.jpg`

## 來源清單：barbary2_agent



確認方式：IA 兩本用 `https://archive.org/metadata/<id>` GET 確認書名、年份（2026-11-23）。Rijksmuseum 網址照抄自 `/tmp/rijks/images_rijks_draft.md`（前一個代理查的 linked-data 紀錄），我這次沒有重新 GET。

#### 文字

| 簡稱 | 書目 | 識別碼／網址 | 本機檔 |
|---|---|---|---|
| Haedo 1612 | Diego de Haedo (Antonio de Sosa)，《Topographia, e historia general de Argel》，Valladolid: Diego Fernández de Córdova y Oviedo, 1612（內容寫 1578–81 年前後的阿爾及爾） | IA `topographiaehist00ha`（Boston Public Library）https://archive.org/details/topographiaehist00ha （metadata 已確認：1612） | `sources/northafrica/haedo_1612_f15v…f18v.jpg`；OCR `/tmp/haedo/topographiaehist00ha.txt` |
| Dan 1649 | Pierre Dan，《Histoire de Barbarie, et de ses corsaires》，Paris: P. Rocolet, 1649（第 2 版） | IA `histoiredebarbar00danp`（Fisher Library, Univ. of Toronto）https://archive.org/details/histoiredebarbar00danp （metadata 已確認：1649） | `sources/northafrica/dan_1649_p253/254/255/307/308/315.jpg`；OCR `/tmp/dl/dan_danp.txt` |
| Narbrough 1676 | Sir John Narbrough，《A Particular Narrative of the Burning in the Port of Tripoli, Four Men of War…》，London: Tho. Newcomb, 1676 | EEBO/TCP `A52619`（https://quod.lib.umich.edu/e/eebo/A52619.0001.001 ；沒有重新 GET） | `/tmp/dl/narbrough_A52619.txt` |
| Ogilby 1670 | John Ogilby，《Africa: being an accurate description…》，London 1670（Dapper 1668 英譯） | IA 上找到的版本：`bim_early-english-books-1641-1700_africa-being-an-accurat_ogilby-john_1670`（advancedsearch GET 找到）。**注意**：本機 OCR `/tmp/dl/ogilby.txt` 開頭是「ENGLISH ATLAS: Tome the First」，不確定是不是同一份掃描 | `/tmp/dl/ogilby.txt` |
| Katib Çelebi | Kâtib Çelebi，《Tuhfat al-kibar fi asfar al-bihar》（1656 撰）；J. Mitchell 英譯《The History of the Maritime Wars of the Turks》，London 1831 | IA `historymaritime00elgoog`、`10218753bsb`（advancedsearch GET 找到；不確定本機 OCR 是哪一份，開頭是 Google 掃描聲明） | `/tmp/dl/katib1831.txt` |

#### 圖像

| 本機檔 | 作者／年代 | 館藏／編號 | 網址 |
|---|---|---|---|
| `images/Nooms_1662-1668_SK-A-1398.jpg` | Reinier Nooms (Zeeman)，1662–68，油畫 | Rijksmuseum SK-A-1398「Gezicht op Tripolis」 | https://id.rijksmuseum.nl/20027353 ；IIIF https://iiif.micr.io/vhwxo/full/max/0/default.jpg |
| `images/Nooms_1662-1668_SK-A-1396.jpg` | Nooms，1662–68，油畫 | Rijksmuseum SK-A-1396「Gezicht op Algiers met … 'De Liefde', 1662」 | https://id.rijksmuseum.nl/20027351 ；IIIF https://iiif.micr.io/nAPLf/full/max/0/default.jpg |
| `images/Luyken_1684_RP-P-1896-A-19368-451.jpg` | Jan Luyken，1684，蝕刻（Dan 荷文版《Historie van Barbaryen》dl.1 p.299） | Rijksmuseum RP-P-1896-A-19368-451「Barbarÿsche Galeÿen」 | https://id.rijksmuseum.nl/200222787 ；IIIF https://iiif.micr.io/ZumJe/full/max/0/default.jpg |
| `/tmp/scorpion_cdn/Dan_1684_BnF-btv1b2000020m-f20.jpg` | 同一塊 Luyken 版（另一份印本） | BnF Gallica btv1b2000020m f20 | https://gallica.bnf.fr/ark:/12148/btv1b2000020m/f20 （GET 回 403，未能確認） |
| `images/Luyken_1684_RP-P-1896-A-19368-394.jpg` | Luyken，1684（Dan 荷文版 p.246） | Rijksmuseum RP-P-1896-A-19368-394「Tripoli」 | https://id.rijksmuseum.nl/200222700 |
| `images/DeWit_1670-1672_NG-20-B.jpg`（＋`_crop-Tripoli`） | 佚名刻工，出版者 Frederik de Wit，1670–72 | Rijksmuseum NG-20-B（地圖邊框城市小景） | https://id.rijksmuseum.nl/200319017 ；IIIF https://iiif.micr.io/qkAHr/full/max/0/default.jpg |
| `images/Dapper-VanMeurs_1668_RP-P-2018-3690.jpg` | 佚名，Jacob van Meurs 出版，Dapper《Naukeurige Beschrijvinge der Afrikaensche Gewesten》1668 | Rijksmuseum RP-P-2018-3690「De Stadt TRIPOLIS」 | https://id.rijksmuseum.nl/200738524 ；IIIF https://iiif.micr.io/QEsjO/full/max/0/default.jpg |
| `/tmp/scorpion_sd/Dapper_1668_IA-gri_33125009359999-n435-n436-Tripolis_joined.jpg` | 同一張 Dapper 1668 版畫（未上色、書中原頁） | IA `gri_33125009359999` n435–436 | https://archive.org/details/gri_33125009359999 （沒有重新 GET） |
| `images/Casembroot_1603-1658_RP-P-BI-5627.jpg` | Abraham Casembroot，≤1658（墨西拿系列） | Rijksmuseum RP-P-BI-5627「Turkse galei op zee」 | https://id.rijksmuseum.nl/200169441 |
| `/tmp/scorpion_cdn/Nooms_17thC_Leiden-PK-T-AW-1612.jpg` | Nooms，17 世紀，素描 | Leiden University Libraries PK-T-AW-1612（標題未確認） | 未確認 |
| `/tmp/scorpion_cdn/Hollar_1665_UofT-Hollar1171-P1276.jpg` | Wenceslaus Hollar，1665，蝕刻 | Univ. of Toronto Hollar 1171（Pennington P1276） | 未確認 |
| `/tmp/scorpion_vdv/VandeVeldeElder_1676_PAH1854.jpg`、`…RCIN406557.jpg` | Van de Velde 父，1676（Narbrough 在 Tripoli 燒船） | NMM PAH1854；Royal Collection RCIN 406557 | 未確認；從縮圖看只有帆船和小艇，沒有槳帆船 |

