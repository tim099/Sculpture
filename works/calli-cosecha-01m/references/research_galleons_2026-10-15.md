# Spanish galleons: dimensions and appearance (research notes for a voxel model at 0.1 m/voxel)

Source markers used below:
- **[READ]**: I fetched the page or document and read the figure in it.
- **[SNIPPET]**: I saw the figure only in a search-engine summary, not on the page.
- **[MY CALC]**: my own unit conversion or arithmetic. It is not in the source.
- **[UNVERIFIED]**: general knowledge that I did not confirm against a source in this session.

Where sources disagree, the values are listed side by side and not averaged.

---

## 0. Best single source: the Spanish Ordenanzas (1607 / 1613 / 1618)

**Source [READ]:** F. Fernández-González, *The Spanish Regulations for Shipbuilding (Ordenanzas) of the Seventeenth Century*, 2009 Naval History Symposium, USNA. PDF via https://oa.upm.es/id/eprint/1878/contents

This is the most useful data for drawing lines. It gives official dimension tables per beam class and a translation of the 1618 articles.

**Units in that paper:**
- Shipbuilder's cubit (codo de ribera / real) = **0.57468 m**. The 1618 notes give **0.57864 m** ("codo real = 33/32 codo").
- Commercial codo = **0.55723 m**.
- Tonelada = 8 cubic codos.

The voxel conversions below use 0.57468 m [MY CALC].

### 0.1 Late-16th-century galleons (Table 1, in royal cubits of 0.57468 m) [READ]

| Year / class | Tons | Length | Keel | Breadth | Floor→hold beams | Hold beams→deck | 1st 'tweendeck | 2nd 'tweendeck |
|---|---|---|---|---|---|---|---|---|
| 1568 P. Menéndez | 240 | 44 | 30 | 12 | 4 | 3.5 | 3.5 | – |
| 1582 small (×7) | 420 | 52 | 34 | 15 | 6 | 3.5 | 3.5 | – |
| 1582 large (×2) | 550 | 56 | 36 | 16 | 4 | 3.5 | 3.5 | 3.75 |
| 1589 small | 574 | 54 | 34 | 17 | 4 | 3.5 | 3.5 | – |
| 1589 medium | 742 | 59 | 38 | 18.5 | 4 | 4 | 3.5 | 3.5 |
| 1589 large | 974 | 64 | 42 | 20.5 | 4 | 5 | 3.5 | 3.5 |

- 'Tweendeck height of 3.5 codos ≈ **2.0 m** [MY CALC].
- 1589 large galleon in metres [MY CALC]: L 36.8 m, keel 24.1 m, B 11.8 m.

### 0.2 Ordenanzas of 1618 (Table 4, cubits of 0.57468 m) [READ]

| Breadth (codos) | 14 | 15 | 16 | 17 | 19 | 20 | 21 | 22 |
|---|---|---|---|---|---|---|---|---|
| Tonnage | 409½ (sic) | 371½ | 444½ | 530 | 721¾ | 840 | 946½ | 1074¾ |
| Floor (flat of floor) | 7 | 7½ | 8 | 8½ | 9½ | 10 | 10½ | 11 |
| Depth of hold | 6½ | 7 | 7½ | 8 | 9 | 9½ | 10 | 10½ |
| Keel | 38 | 40 | 42 | 44 | 48 | 49 | 51 | 53 |
| Length | 48 | 50½ | 53 | 56 | 61½ | 63 | 66 | 68 |
| Rake of stem | 7 | 7¼ | 7¾ | 8 | 9 | 9½ | 10 | 10 |
| Rake of stern | 3 | 3¼ | 3¼ | 4 | 4½ | 4½ | 5 | 5 |
| Rising aft | 4⅔ | 5 | 5⅓ | 5⅔ | 6⅓ | 6⅔ | 7 | 7⅓ |
| Transom (width) | 7¼ | 7¾ | 8¼ | 8¾ | 9¾ | 10 | 10½ | 11 |
| Rise of floor | 13/16 | 7/8 | 15/16 | 1 | 1⅛ | 1 3/16 | 1¼ | 1 5/16 |
| Wale sheer aft / fwd | 2¼ / 1¾ | 2¼ / 1¾ | 2¼ / 1¾ | 2¼ / 1¾ | 2¼ / 1¾ | 2¼ / 1¾ | 2½ / 2 | 2½ / 2 |

Rules that apply to every class:
- Deck ½ codo above the depth of hold.
- Deck sheer: 1 codo aft, ½ codo forward.
- Halfdeck (alcázar) 3 codos high, bridge (puente) 3 codos high, breaks 1–1½ codos.
- Floor = Beam/2. Keel = 2×Beam + 10 (2×Beam + 9 from 20 codos up). Transom = Floor + ¼. Rising aft = ⅓ Breadth.
- The 18-codo column was garbled in the PDF text extraction, so I omitted it. The 1613 values for 18 codos are below.

**Worked example, 1618 navío of 20 codos [MY CALC]:**

| Item | Metres | Voxels (0.1 m) |
|---|---|---|
| Beam | 11.49 | 115 |
| Length | 36.20 | 362 |
| Keel | 28.16 | 282 |
| Depth of hold | 5.46 | 55 |
| Flat of floor | 5.75 | 57 |
| Rise of floor | 0.68 | 7 |
| Rake of stem | 5.46 | 55 |
| Rake of stern | 2.59 | 26 |
| Rising aft | 3.83 | — |
| Transom | 5.75 | — |
| Each castle / deck level (3 codos) | 1.72 | 17 |

The length checks out as keel + both rakes: 49 + 9.5 + 4.5 = 63 codos.

**1613 Ordenanzas (Table 3) [READ], selected columns:**

| Breadth | Tons (merchant / armada) | Floor | Depth | Keel | Length | Rake stem | Rising aft | Rise of floor |
|---|---|---|---|---|---|---|---|---|
| 17 | 539¼ / 555¼ | 8½ | 8½ | 46 | 58¾ | 8½ | 5⅔ | 1 1/16 |
| 18 | 632 / 651 | 9 | 9 | 48 | 61½ | 9 | 6 | 1⅛ |
| 20 | 833⅝ / 858⅝ | 10 | 10 | 51 | 66 | 10 | 6⅔ | 1¼ |
| 22 | 1073⅓ / 1105½ | 11 | 11 | 54 | 70½ | 11½ | 7 | 1⅜ |

Other 1613 values for these classes:
- Rake of stern: half of the stem rake (5 codos at 22).
- 'Tweendeck height: 3⅛–3¼ codos.
- Rise of floor: ⅔ as dead rise at the 3 midship timbers and ⅓ distributed along the rest.

**Midship section, tumblehome and quarter sections in 1613 [READ]:**
The table rows are misaligned in the extracted text. This is my best reading of the label-to-value mapping:
- Hold beams 3½ codos below the deck.
- Cuadra (after quarter section) at L/4 + 2 codos from the sternpost, with breadth there = Breadth − 2 codos.
- Mura (forward quarter section) at L/4 + 1 codo from the stem, with breadth there = Breadth − 1 codo.
- Breadth at the bridge (upper) deck = the same as at the hold beams. This is the tumblehome.
- Toptimbers "to be straightened for better shape."
- All sections shaped from one single mould (gálibo).

The 1618 Art. 22 says the same thing: "the Bridge closes as much as it opened from the Beams, which will be three cubits and a half from the Deck, and from the Bridge up has to straighten the Toptimber a little."

**Midship section recipe for the voxel lines [MY CALC from the above]:**
1. Flat floor ≈ B/2 wide.
2. Floor rises ≈ B/16 to the turn of the bilge.
3. Maximum breadth at about deck level, roughly hold depth + ½ codo.
4. Sides tumble home above that, so the bridge deck is about as narrow as the breadth 3½ codos below the main deck.
5. The upper toptimbers go nearly vertical.

**Mast steps, 1618 Art. 66–68 [READ]:**
- "The Maststep of the Main Mast is to be placed in the middle of the length of the Keel."
- "The Maststep of the Fore Mast is to be placed in the middle of the Rake of the Stem."
- The bowsprit step is on the main deck.

As fractions of length, for the 20-codo navío [MY CALC]:
- Mainmast ≈ 0.54 L from the bow (29/63 from the stern end).
- Foremast step ≈ 0.075 L from the bow.

The paper does not give the mizzen position. Mast and spar dimensions are in Art. 72–91 of the 1618 Ordenanzas, which the paper lists but does not translate.

Art. 5 of 1618 (13-codo navío) also says:
- "Forecastle at three cubits height, from the Break, and the same three cubits height the Castle aft."
- A flush bridge 3 codos above the main deck.

**Modifications of 1666 / 1679 (to reduce draft) [READ]:**

| Version | Breadth | Keel | Length | Depth | Rise of floor |
|---|---|---|---|---|---|
| 700 t (1666) | 18½ | 53 | 65 | 8¾ | 1 |
| 500 t (1666) | 17½ | 50 | 62 | 8¼ | ¾ |
| 800 t (1679) | 19 | 55½ | 67½ | 9¼ | ⅔ |

In these versions keel and length grew by about 6 codos and the floor got flatter.

### 0.3 Length/beam ratios from Spanish treatises [READ]

Source: *Cuadernos del IHCN* no. 33, cap. 7. https://armada.defensa.gob.es/archivo/mardigitalrevistas/cuadernosihcn/33cuaderno/07cap.pdf. The table is garbled in the text layer.

| Source | Year | Length/beam | Keel/beam | Depth/beam |
|---|---|---|---|---|
| Escalante | 1575 | 3.18 | 2.28 | 0.65 |
| García de Palacio | 1587 | 3.33 (?) | 2.12 | – |
| Tomé Cano | 1611 | 3.30 | 2.56 | – |
| (row dated 1566, label unclear) | 1566 | 3.51 | 2.86 | – |
| Garrote | 1691 | 3.43 | 3 | 0.39 |

The same document says: "Por órdenes de 1628, 1666 y 1679 se limitó el tamaño de los galeones a 500 t."

---

## 1. Galeón Andalucía (replica, Fundación Nao Victoria)

**Built:** designed by Ignacio Fernández Vial, built at Punta Umbría (Huelva). Launched 30 Nov 2009, masts fitted early 2010.
Source: https://www.fundacionnaovictoria.org/el-galeon-andalucia/ [READ]

**Construction:** fibreglass hull and decks, sheathed with pine and iroko. Source: press dossier PDFs below [READ].

| Item | Value | Source |
|---|---|---|
| Length (eslora) | **48 m** | Press dossier, Vigo 2023, tech sheet page [READ] https://www.vigoe.es/wp-content/uploads/2023/03/dossier_prensa_gale_vigo.pdf |
| | **49 m** | Same Vigo dossier, narrative text [READ]. Also iomtoday.co.im [READ] |
| | **50 m** | Press dossier Cartagena 2019, tech sheet [READ] https://www.cartagena.es/gestion/documentos/37870.pdf |
| | **51 m** | es.wikipedia [READ] https://es.wikipedia.org/wiki/Galeón_Andalucía. Also armada.org: "eslora total 51 m, eslora de casco 38 m" [SNIPPET; the page itself returned an image] |
| | **160 ft (≈48.8 m)** | sailingshipsmaine.org [READ] https://sailingshipsmaine.org/el-galeon |
| | **162 ft** | UK port press [SNIPPET] |
| Hull length | **38 m** | armada.org [SNIPPET only] |
| Beam | **10 m** | Dossiers [READ] |
| | **10.12 m** | es.wikipedia [READ] |
| | **33 ft** (spec table) / **32 ft** (narrative) | sailingshipsmaine [READ] |
| Draft | **3 m** | Dossiers [READ] |
| | **3.40 m** | es.wikipedia [READ] |
| | **10 ft 6 in** | sailingshipsmaine [READ] |
| Air draft (masthead above waterline) | **37 m** | Dossiers [READ] |
| Rig height | **121 ft** (≈36.9 m [MY CALC]); main mast "about 120 ft" | sailingshipsmaine [READ] |
| Tonnage | **496 GT** ("Desplazamiento: 496 GT") | Dossiers [READ] |
| | **500 t** | Dossier narrative [READ] |
| Sail area | **930 m²** | Dossier tech sheet [READ] |
| | **"casi mil m²"** | Dossier narrative [READ] |
| | **10,010 ft²** (spec) / "almost 11,000 ft²" (narrative) | sailingshipsmaine [READ] |
| | **590 m²** | armada.org [SNIPPET] |
| Masts / sails | **3 palos / 7 velas** | Dossier tech sheet [READ] |
| | **4 palos / 6 velas** | Same dossier, narrative [READ] |
| | 4 masts, 6 sails | sailingshipsmaine and iomtoday [READ] |
| | 3 masts, 7 sails | es.wikipedia [READ] |
| Decks | "Seis cubiertas" | Dossiers [READ] |
| Engines | 2 × 380 HP | sailingshipsmaine [READ] |
| Crew | 15–35 | Dossier [READ] |
| Speed | Average 7 knots | Dossier [READ] |

**Deck plan.** The dossier tech sheet [READ] gives these areas:

| Deck | Area |
|---|---|
| Toldilla (poop) | 13.56 m² |
| Tolda (quarterdeck / half-deck) | 9 m² |
| Castillo (forecastle) | 41.75 m² |
| Cubierta principal (main / upper deck) | 86 m² |
| Cubierta de artillería (gun deck) | 96 m² |
| Bodega (hold) | 70 m² |
| Total usable area | > 320 m² |

- sailingshipsmaine [READ] lists the decks as: forecastle, main deck, noble area, quarter deck, poop deck, gun deck and hold.
- iomtoday [READ] says there are three levels (upper, middle, lower) at both bow and stern, with replica cannons on the lower decks.

**Rig composition [UNVERIFIED, from photos I remember; not confirmed in any text this session]:**
- Fore and main masts: course + topsail.
- Mizzen and bonaventure: lateen.
- Spritsail under the bowsprit.

That makes 7 sails on 4 masts (6 if the spritsail isn't counted), which would explain the "4 palos / 6 velas" vs "7 velas" difference. Check against photos before using it.

**Mast heights and individual sail areas:** I found no source. Only the 37 m air draft and 121 ft rig height above are available.

**Photos:** Commons category https://commons.wikimedia.org/wiki/Category:Galeón_Andalucía_(ship,_2010) [READ]. It has 15 port-visit subcategories plus bow and rigging files, and a subcategory on how the square sails attach to the yards.

---

## 2. San José (1698, sunk 1708)

**Source [READ]:** https://en.wikipedia.org/wiki/Spanish_galleon_San_José

| Item | Value (codos) |
|---|---|
| Length (lower deck) | 71.00 |
| Keel | 60.18 |
| Beam | 21.91 |
| Depth of hold | 10 |
| Draught (estimated) | 11.75 |
| Burthen | 1,051 tons |

**Guns:** 64 in total.
- Lower gundeck: 26 × 18-pdr.
- Middle gundeck: 26 × 10-pdr.
- Quarterdeck and forecastle: 12 × 6-pdr.

**Decks:** lower gundeck, middle gundeck, quarterdeck and forecastle.

**Builder:** designed by Francisco Antonio Garrote. Contractor Pedro de Aróstegui, Mapil yard, Usurbil (Gipuzkoa). Laid down 1697, launched 1698.

**Codo conflict.** Wikipedia's footnote says *"A 'codo común' (=418 mm)"*. Fernández-González [READ] gives 0.5747–0.5786 m for the shipbuilder's codo. Both conversions [MY CALC]:

| | codo = 0.418 m | codo = 0.5747 m |
|---|---|---|
| Length | 29.7 m | 40.8 m |
| Keel | 25.2 m | 34.6 m |
| Beam | 9.16 m | 12.59 m |
| Depth | 4.18 m | 5.75 m |
| Draught | 4.91 m | 6.75 m |

My view [MY CALC / judgement]:
- The 0.5747 m figures fit a two-decker with 13 ports a side per deck. They also match the 1618 table for a 22-codo breadth: keel 53, length 68.
- A 30 m ship cannot carry 13 broadside ports a side.

The designer should choose. I have not averaged the two.

---

## 3. Nuestra Señora de Atocha (1620)

**Source [READ]:** https://en.wikipedia.org/wiki/Nuestra_Señora_de_Atocha

| Item | Infobox | Body text |
|---|---|---|
| Length | 34 m (111 ft 7 in) | "overall length of 112 feet" |
| Beam | 10 m (32 ft 10 in) | "a beam of 34 feet" (conflicts with the infobox) |
| Draught | 4.3 m | 14 ft |

Other figures from the same article:
- 550 toneladas.
- Armament: 20 heavy guns plus 4–8 versos.
- Complement 90 / crew 110.
- Hull of mahogany, "constructed (rather poorly)".
- Rig: fore and main square, mizzen lateen, spritsail.
- No superstructure records survive. The article says she likely had a high sterncastle, low waist and high forecastle.

Other figures:
- Builder: yard of Alonso Ferrera, Havana, 1619–20 [SNIPPET].
- 33.5 × 10.1 × 4.3 m, 550 t: shipstamps forum [SNIPPET].
- 120 ft, 600 t: another forum post, unsourced [SNIPPET].

I found no keel length in codos.

---

## 4. Manila galleons

**Santísima Trinidad y Nuestra Señora del Buen Fin (1751)** [READ] https://en.wikipedia.org/wiki/Santísima_Trinidad_y_Nuestra_Señora_del_Buen_Fin
- Length 167 ft 6 in (51.05 m, gundeck). Beam 50 ft 6 in (15.39 m). Draught 30 ft 6 in (9.30 m).
- Burthen "at most 2,200"; carrying capacity 2,000 tons in the text.
- Guns: 70 (infobox) vs 60 (text).
- Full-rigged ship.
- en.wikipedia "Manila galleon" [READ] gives 51.5 m length.
- Built at the Bagatao / Sorsogon yard [SNIPPET].

**San Diego (sunk 14 Dec 1600)** [READ] https://en.wikipedia.org/wiki/San_Diego_(ship)
- Length 115 ft (35 m), 300 tons.
- 14 bronze guns, taken from the Manila fortress.
- The wreck mound is "25 meters long, 8 meters wide, and 3 meters high". That is the site, not the hull.
- No beam or keel figures. A "≈25 m" length that appears elsewhere is probably a confusion with the mound [SNIPPET].

**Concepción (wrecked 1638)** [READ, en.wikipedia "Manila galleon"]
- 43–49 m long, about 2,000 tons.

---

## 5. Red Bay San Juan (1565, site 24M)

I could not reach a primary source within the time limit, so all of this section is weak.

| Item | Value | Source |
|---|---|---|
| Keel | 14.75 m | shipstamps.co.uk forum [SNIPPET; page returned 403] |
| Length | ~22 m | Same forum [SNIPPET] |
| Beam | 7.5 m | Same forum [SNIPPET] |
| Draught | 3–3.5 m | Same forum [SNIPPET] |
| Proportions | breadth : keel : length = 1 : 2 : 3 | Same forum [SNIPPET] |
| Replica (Albaola, launched Pasaia 7 Nov 2025): eslora | 28 m | ondavasca / Forbes Nautik [SNIPPET] |
| Replica: manga | 7.5 m | Same [SNIPPET] |
| Replica: puntal | 6 m | Same [SNIPPET] |
| Replica: rig and decks | 3 masts, 3 decks | Noticias de Navarra [SNIPPET] |
| Tonnage | 200 t | Noticias de Navarra [SNIPPET] |
| | 240 t, "fifty-two foot" | yachtingtimesmagazine [SNIPPET] |
| | ~300 t | heritage / JW articles [SNIPPET] |

Notes on these figures:
- The 22 m and 28 m lengths probably measure different things: hull/deck length vs overall including the beak and stern overhang. This is not confirmed.
- The 52 ft figure is likely an error.

**Hull lines (floor rise, tumblehome, midship shape):** not obtained.

The authoritative source is Parks Canada, *The Underwater Archaeology of Red Bay*, vol. 3 "The 24M Hull" (Grenier, Bernier, Stevens eds., 2007). It is a free PDF of **188 MB**:
https://publications.gc.ca/collections/collection_2025/pc/R62-389-2007-3-eng.pdf
Vol. 4 ("Rigging, vessel use") is 219 MB: …/R62-389-2007-4-eng.pdf. The catalogue page is https://publications.gc.ca/site/eng/9.946496/publication.html [READ].

I did not download either file because of their size; that needs the user's go-ahead. Until then, use the Ordenanza rules in section 0 for the midship section.

---

## 6. Rig, castles, decoration (general)

**Rig:**
- en.wikipedia "Galleon" [READ] https://en.wikipedia.org/wiki/Galleon
  - Three or four masts: fore and main square-rigged ("square sails and topsails"), mizzen lateen.
  - Larger galleons often had a fourth lateen mast, the bonaventure.
  - Galleons were "classed as 1-, 2- or 3-deckers".
  - A square tuck stern, and a beakhead "below the level of the forecastle".
- worldhistory.org [READ] https://www.worldhistory.org/Spanish_Galleon/
  - Up to three square sails per mast on fore and main.
  - Bonaventure carries one lateen, smaller than the mizzen.
  - One or two small square sails at the bowsprit (spritsail).
  - Its claim that the mizzen carries "two square sails and one lateen" looks doubtful for Spanish practice; treat it with care.
- Topgallants: used only on the largest ships, and late [UNVERIFIED].

**Proportions and guns:** worldhistory.org [READ]
- Length:beam 3:1–4:1. Typical length 30–45 m, beam 12–15 m.
- Atlantic galleons 500–1,000 t; Manila galleons up to 2,000 t.
- Heavy guns below deck behind lidded ports, sometimes on several tiers, plus bow and stern chasers and swivels on the upper deck.
- The forecastle was set back from the prow.

**Castles:**
- 1618 Ordenanzas [READ]: forecastle 3 codos (≈1.72 m [MY CALC]) above the break; aft castle the same 3 codos; halfdeck (alcázar) 3 codos; bridge 3 codos above the main deck.
- Per Art. 69, galleries are allowed only on ships of 15+ codos, at the halfdeck break, "small", projecting at most ⅔ codo at the sides.
- Galeón Andalucía has three levels at both bow and stern [READ, iomtoday] and named decks toldilla, tolda and castillo [READ, dossier].

**Beakhead (espolón) length:** no figure found. A usable proxy is the 1618 stem rake of 7–10 codos (4–5.7 m [MY CALC]). The beak projects beyond that, and I have no number for it.

**Gunports per deck:**
- San José: 26 guns per gundeck, i.e. 13 ports a side on each of two decks, plus 12 on the castles [READ].
- Atocha: 20 heavy guns, i.e. roughly 10 a side on a single gundeck [READ].
- Typical port spacing: not found.

**Paint and decoration (weakly sourced):**
- Gilded stern additions. Ships were named after saints, painted on the stern. Royal galleons carried a crowned golden lion figurehead [READ, worldhistory.org].
- Galleries were commonly shown red with gold or ochre stiles. Rails were gold or ochre on better ships, red or dark on others. Hull planking was mostly bare or tarred wood with a white underwater coating against shipworm. Only expensive ships carried large painted areas [SNIPPET, modelshipworld forum, not authoritative].
- A general 17th-century painting guide (not Spanish-specific) gives black lower wales and hull, a yellow-ochre band, and "gold colour" = yellow over white. It notes a 1691 Spanish galleon may show white upper works [SNIPPET]: https://timberandsail.com/wp-content/uploads/how-to-paint-historically-accurate-17th-18th-century-ships.pdf
- Stern lanterns (1 to 3, with the flagship carrying 3) [UNVERIFIED; no source found this session].

---

## 7. Freely viewable plans, drawings and photos

1. https://commons.wikimedia.org/wiki/File:Plano_del_galeón_Nuestra_Señora_de_la_Mar,_que_naufragó_en_el_golfo_de_la_Bermuda.jpg
   - A 1695 Archivo General de Indias gouache plan showing a full side view of a real Spanish galleon (862½ tons) with boats around it.
   - The best period depiction of hull and castles I found. CC BY-SA 4.0 scan [READ].
2. https://commons.wikimedia.org/wiki/Category:Galleons_of_Spain
   - 22 files plus subcategories (Atocha, Juncal, Covadonga, the San Salvador replica, a Vroom painting from 1601, a model photo at Museo San Telmo, an engraving of a Spanish galleon engaging a Dutch ship) [READ].
3. https://commons.wikimedia.org/wiki/Category:Galeón_Andalucía_(ship,_2010)
   - Many CC photos of the replica from bow and side, with rigging detail and how the yards are attached. Good for colour and stern carving reference [READ].
4. Parks Canada Red Bay vol. 3, free PDF, 188 MB (link in section 5). This should contain the measured 24M hull lines and frame drawings. Not downloaded.

Also noted:
- Museo Naval Madrid has a model of the galleon *Nuestra Señora de la Concepción y de las Ánimas* (1687–1705), built in 2000 from a 1688 construction manuscript, 238.5 cm long [SNIPPET]. No public image link found.

---

## 8. Other sources to follow up (not read)

- J. L. Casabán, "La construcción naval en el siglo XVII y el diseño de N. S. del Juncal" (2021). A 1618-Ordenanza reconstruction of a 1622–23 galleon.
- Casabán, *The Twelve Apostles* dissertation (Texas A&M). Reconstruction of the 1589 galleons.
- *Standardization of Spanish Shipbuilding: Ordenanzas … 1607, 1613, 1618* (Texas A&M thesis): https://tdl-ir.tdl.org/handle/1969.1/ETD-TAMU-2318
- *Reconstruction of Seventeenth Century Iberian Rigging* (tDAR): https://core.tdar.org/document/457340/reconstruction-of-seventeeth-century-iberian-rigging. Likely holds mast and yard proportions.
