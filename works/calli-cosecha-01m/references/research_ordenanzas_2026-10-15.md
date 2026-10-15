# Spanish galleon design parameters: Ordenanzas 1607/1613/1618, Palacio 1587, Cano 1611

Research date: 2026-10-15. Goal: sourced numbers for drawing a late-16th to mid-17th-century galleon at 0.1 m per voxel.

## How reliable each source is

| Tag | Source | What I did |
|---|---|---|
| **[FG]** | Francisco Fernández-González, *The Spanish Regulations for Shipbuilding (Ordenanzas) of the Seventeenth Century*, 2009 Naval History Symposium, USNA. UPM repository: https://oa.upm.es/id/eprint/1878/contents | **Read the full PDF**, all 26 pages. It includes Tables 1-5 and his translation of the 1618 articles. This is the main source for this report. |
| **[CIHCN]** | *Cuadernos de Historia Naval* 33, ch. 7, Armada Española: https://armada.defensa.gob.es/archivo/mardigitalrevistas/cuadernosihcn/33cuaderno/07cap.pdf | **Read the PDF**, pp. 35-36: the ratio table and the metrology box. |
| **[VIS]** | Ricardo Visiers Bañón, *Arqueología naval virtual: reconstrucción digital de la nao de 400 toneladas de la "Instrucción náutica" de García de Palacio (1587)*, UPM thesis paper: https://sectormaritimo.es/wp-content/uploads/2016/01/arqueologia-naval-virtual_1.pdf | **Read the full PDF**, 32 pages. It quotes Palacio's text with folio numbers. |
| **[CTL]** | Carmen Torres López, *La Instrucción Náutica de Diego García de Palacio (1587)*: https://catedranaval.com/wp-content/uploads/2021/01/instruccion-nautica-presentacion.pdf | **Read the PDF**. It is context only, with almost no numbers. |
| **[MP]** | Modelismo Naval Metodología blog, "Parte cuarta: la arboladura, jarcia y velas", 25 Jul 2018: https://modelismoperianes.wordpress.com/tag/proporciones-de-cuenta-y-medida/ | **Page read through a summarising fetch tool only**, not verbatim. This is a secondary source (a model-builder's paraphrase of Cano, Palacio and Escalante). Use with caution. |
| **[SNIP]** | Search-engine snippets | **Snippet only.** I did not read the page. These are marked inline. |

**Not reached:** the original Spanish text of the 1613 and 1618 mast articles (1618 art. 72-91). Todoavante.es refused the connection, the TAMU theses (Laanela on Palacio; Rodríguez Mendoza, *Standardization of Spanish Shipbuilding*, ETD-TAMU-2318) returned 403, and the Gladius artillery article had a certificate error. So **the 1618 Ordenanza's own mast and yard numbers are not in this report**. Only the treatise rules (Cano, Palacio, Escalante, all via [MP]) are given.

---

## 1. The codo: which value goes with which rule

| Unit | Definition | Metres | Source |
|---|---|---|---|
| Codo castellano (common) | 2 pies = 32 dedos = 2/3 vara | **0.55766 m** | [CIHCN] p.36 (read) |
| Codo castellano | 2/3 vara, with vara = 835.9 mm | **0.55723 m** | [FG] p.15 units box (read) |
| Codo castellano | "557 mm" (Hormaechea et al.); "unos 56 cm" (Casado Soto) | 0.557 / 0.56 m | [VIS] p.7-8, notes 25 and 29 (read) |
| **Codo de ribera / codo real** (shipwright) | 2 pies + 1 dedo = 33 dedos = 2/3 vara + 1/32. Introduced by Philip II's arqueo order of **1590** | **0.57468 m** | [CIHCN] p.36 (read); [VIS] p.7 quotes the 1590 order (read) |
| Shipbuilders' / Royal cubit | Used for all of [FG] Tables 1-4 ("Shipbuilder cubit of 574,68 mm") | **0.57468 m** | [FG] pp.2, 10-12 (read) |
| Codo real (shipbuilders) | 33/32 codo, with vara = 835.9 mm | **0.57864 m** | [FG] p.15 units box (read). This is **internally inconsistent** with his own tables (0.57468), because it uses a different vara. |
| Codo of 1618 | "560 mm" | 0.560 m | [SNIP] forum post quoting Conway, *Cogs, Caravels and Galleons* (snippet only) |
| Implied by Borrero | 22 codos = 12.65 m | 0.575 m/codo | [SNIP] tDAR abstract, Borrero Londoño 2020 (snippet only) |
| Codo for masts in the 1613 Ordenanza | Art. 103 reportedly: "el codo ... que es de dos tercios de vara, medida castellana" | would be about 0.557 m | [SNIP] search summary of todoavante.es (snippet only; it conflicts with [FG]'s 0.57468 for the 1613 tables) |

**Which codo each rule uses:**
- **García de Palacio 1587:** codo castellano (2 pies = 2/3 vara). He writes "dos pies o dos tercias de vara hacen un codo" (fol. 89v, quoted in [VIS] p.7). Use about **0.557 m**.
- **Ordenanzas 1607/1613/1618:** codo de ribera / shipbuilder cubit. [FG] states **0.57468 m** for all of Tables 2-4. One unverified snippet says the 1613 text calls its mast codo "dos tercios de vara".
- **Tomé Cano 1611:** his rules are proportions of the manga, so the codo does not matter. He wrote after 1590, so the codo de ribera would apply.
- **Tonnage unit:** tonel or tonelada = 8 cubic codos de ribera = **1.5183 m³** (after 1590). The Andalusian tonelada de carga = 8 cubic codos castellanos = **1.3844 m³** ([CIHCN] p.36, read).

**All conversions below use 0.57468 m for the Ordenanzas and 0.55766 m for Palacio.** Voxel counts are at 0.1 m per voxel, rounded.

---

## 2. Ordenanzas of 1618: full rows for 3 tonnage classes

Source: [FG] Table 4, pp.12-14 (read). Units are codos de ribera (0.57468 m).
General notes from [FG] p.14 (read):
- All ships are called *navíos*.
- The widest breadth is at the Depth (puntal) height.
- Floor (plan) = Breadth / 2.
- Keel = 2 × Breadth + 10 (or 2 × Breadth + 9 from 20 codos up).
- Transom = Floor + 1/4.
- Rising aft = 1/3 Breadth.
- Rising forward = 1/3 of rising aft.
- Joba = rise of floor.
- The deck is 1/2 codo above the Depth.

**Arithmetic check.** In every row, Length = Keel + Rake stem + Rake stern (e.g. 44 + 8 + 4 = 56). So *Length* is length *de roda a codaste* on deck, and the stem rake is the larger one. [FG]'s note "Fore Rake = half the Stern post Rake" contradicts his own table, and probably has the labels reversed. Palacio also gives a stem rake twice the stern rake (see §4).

### 2a. Breadth 17 codos: 530 toneladas

| Item (Spanish) | Codos | Metres | Voxels |
|---|---|---|---|
| Manga (breadth) | 17 | 9.770 | 98 |
| Plan (floor width) | 8 1/2 | 4.885 | 49 |
| Puntal (depth of hold, at widest) | 8 | 4.597 | 46 |
| Main deck height | 8 1/2 (½ above depth) | 4.885 | 49 |
| Quilla (keel) | 44 | 25.286 | 253 |
| Eslora (length, roda to codaste) | 56 | 32.182 | 322 |
| Lanzamiento a proa (rake of stem) | 8 | 4.597 | 46 |
| Lanzamiento a popa (rake of sternpost) | 4 | 2.299 | 23 |
| Rasel aft (rising) | 5 2/3 | 3.257 | 33 |
| Rasel fwd (1/3 of aft) | 1 8/9 | 1.085 | 11 |
| Yugo (transom width) | 8 3/4 | 5.028 | 50 |
| Maderos de cuenta (main floors) | 37 | — | — |
| Astilla (rise of floor) | 1 | 0.575 | 6 |
| Joba fwd / aft (aft from timber #9) | 1 / 1/2 | 0.575 / 0.287 | 6 / 3 |
| Arrufadura (sheer) at deck, aft / fwd | 1 / 1/2 | 0.575 / 0.287 | 6 / 3 |
| Sheer at wales, aft / fwd | 2 1/4 / 1 3/4 | 1.293 / 1.006 | 13 / 10 |
| Contracodaste (counter sternpost) | 1/2+ | ≈0.29 | 3 |
| Alcázar (halfdeck), height | 3 | 1.724 | 17 |
| Puente (flush bridge, 2nd deck), above main deck | 3 | 1.724 | 17 |
| Quebrados (breaks) | 1 | 0.575 | 6 |

### 2b. Breadth 19 codos: 721 3/4 toneladas

| Item | Codos | Metres | Voxels |
|---|---|---|---|
| Manga | 19 | 10.919 | 109 |
| Plan | 9 1/2 | 5.459 | 55 |
| Puntal | 9 | 5.172 | 52 |
| Main deck height | 9 1/2 | 5.459 | 55 |
| Quilla | 48 | 27.585 | 276 |
| Eslora | 61 1/2 | 35.343 | 353 |
| Lanzamiento proa | 9 | 5.172 | 52 |
| Lanzamiento popa | 4 1/2 | 2.586 | 26 |
| Rasel aft / fwd | 6 1/3 / 2 1/9 | 3.640 / 1.213 | 36 / 12 |
| Yugo (transom) | 9 3/4 | 5.603 | 56 |
| Maderos de cuenta | 39 | — | — |
| Astilla (rise of floor) | 1 1/8 | 0.647 | 6 |
| Joba fwd / aft (from #10) | 1 1/8 / 9/16 | 0.647 / 0.323 | 6 / 3 |
| Sheer at deck aft / fwd | 1 / 1/2 | 0.575 / 0.287 | 6 / 3 |
| Sheer at wales aft / fwd | 2 1/4 / 1 3/4 | 1.293 / 1.006 | 13 / 10 |
| Contracodaste | 2/3 | 0.383 | 4 |
| Alcázar / Puente | 3 / 3 | 1.724 / 1.724 | 17 / 17 |
| Quebrados | 1 | 0.575 | 6 |

### 2c. Breadth 21 codos: 946 1/2 toneladas

| Item | Codos | Metres | Voxels |
|---|---|---|---|
| Manga | 21 | 12.068 | 121 |
| Plan | 10 1/2 | 6.034 | 60 |
| Puntal | 10 | 5.747 | 57 |
| Main deck height | 10 1/2 | 6.034 | 60 |
| Quilla | 51 | 29.309 | 293 |
| Eslora | 66 | 37.929 | 379 |
| Lanzamiento proa | 10 | 5.747 | 57 |
| Lanzamiento popa | 5 | 2.873 | 29 |
| Rasel aft / fwd | 7 / 2 1/3 | 4.023 / 1.341 | 40 / 13 |
| Yugo (transom) | 10 1/2 | 6.034 | 60 |
| Maderos de cuenta | 41 | — | — |
| Astilla | 1 1/4 | 0.718 | 7 |
| Joba fwd / aft (from #11) | 1 1/4 / 5/8 | 0.718 / 0.359 | 7 / 4 |
| Sheer at deck aft / fwd | 1 / 1/2 | 0.575 / 0.287 | 6 / 3 |
| Sheer at wales aft / fwd | 2 1/2 / 2 | 1.437 / 1.149 | 14 / 11 |
| Contracodaste | 2/3 | 0.383 | 4 |
| Alcázar / Puente | 3 / 3 | 1.724 / 1.724 | 17 / 17 |
| Quebrados | 1 | 0.575 | 6 |

### 2d. Other 1618 rows in the range (main dimensions only)

Source: [FG] Table 4 (read).

| Manga | Toneladas | Plan | Puntal | Quilla | Eslora | Rake stem / stern | Metres (M × Q × E) |
|---|---|---|---|---|---|---|---|
| 16 | 444 1/2 | 8 | 7 1/2 | 42 | 53 | 7 3/4 / 3 1/4 | 9.19 × 24.14 × 30.46 |
| 18 | 624 1/4 | 9 | 8 1/2 | 46 | 59 | 8 1/2 / 4 1/2 | 10.34 × 26.44 × 33.91 |
| 20 | 840 | 10 | 9 1/2 | 49 | 63 | 9 1/2 / 4 1/2 | 11.49 × 28.16 × 36.20 |
| 22 | 1074 3/4 | 11 | 10 1/2 | 53 | 68 | 10 / 5 | 12.64 × 30.46 × 39.08 |

(Anomaly as printed: the 14-codo row shows 409 1/2 t, more than the 15-codo row's 371 1/2. That is probably a typo in [FG] or the original.)

### 2e. 1618 articles on decks, castles and ports

Source: [FG] translation, pp.16-22 (read). Article numbers are his.

- **Art. 5** (13-codo example). Flush **bridge (puente) 3 codos above the main deck**. Two breaks on the bridge, fore and aft, **1 1/2 codos** high. **Forecastle 3 codos high** from the break, and **"the same three cubits height the Castle aft."** Hawse holes under the castle, as high as possible.
- **Note** ([FG] p.16): this flush bridge connecting alcázar and castillo *is* the second deck. A further bridge making a third deck was officially prohibited for the Indies fleets.
- **Art. 20.** Take a string the length of the ship and fold it into quarters. Lay L/4 along the stem rake; the last forward floor (orenga) goes where it ends, **1 codo** further forward. At the stern the same L/4, with the last orenga **2 codos** forward of where it ends.
- **Art. 21.** The section at the *mura* (about L/4 from the stem) has breadth = Breadth − 1 codo. The *quadra* (about L/4 from the sternpost) has Breadth − 2 codos. Aftmost orengas = 1/2 floor + a little.
- **Art. 22.** The sides close inward from the hold beams, which are **3 1/2 codos below the deck**, up to the bridge (tumblehome). Toptimbers are straightened a little above the bridge.
- **Art. 23.** The fashion pieces open the transom to **half the Breadth + 1/4 codo**. 2 to 2 1/2 codos lower down they open 1/4 codo more.
- **Art. 32.** Ships under 19 codos breadth have **one tier of hold beams at half the depth**. Ships of 20 codos and up have **two tiers, dividing the depth into thirds**.
- **Art. 42.** **Gun-port sill 1 codo above the deck. Port 1 1/4 codos square** (0.718 m, about 7 voxels).
- **Art. 45.** Espolón (beakhead) = **3/5 of the Breadth** beyond the stem. For 17 codos that is 10.2 codos = 5.86 m (my arithmetic).
- **Art. 46.** Helm port under the halfdeck break. Rowlock (whipstaff) at the same break. Galleries over the halfdeck break, with "all her artillery" playing underneath.
- **Art. 52.** First wale **1 codo below the main deck**. Second wale at the carling heads. Third wale **above the gun ports, 2 1/2 codos above the main deck**.
- **Art. 65-68.** Capstans on the bridge. **Mainmast step at the middle of the keel length. Foremast step at the middle of the stem rake.** Bowsprit step on the main deck.
- **Art. 69.** For ships of 15 codos and up: stern galleries at the halfdeck break, projecting at most **2/3 codo** at the sides.
- **Art. 16.** No sheer on the breaks and no cambered decks ("everything squared, leveled, for the guns to run better").
- **Fleet limits** ([FG] p.8): ships over **18 codos breadth and 8 1/2 codos depth** were excluded from the Indies fleets, as were ships with a flush bridge joined to the forecastle, side doubling, or a raised helm port.
- **Masts and spars:** 1618 art. 72-91 ([FG] p.9). **Not translated in [FG] and not obtained.**

---

## 3. Ordenanzas of 1613 and 1607, and 1666/1679 changes (for comparison)

### 1613 galleon rows

Source: [FG] Table 3, pp.11-12 (read). Codo 0.57468 m.

| Item | 17 codos | 18 codos | 20 codos | 22 codos |
|---|---|---|---|---|
| Toneladas, merchant / armada | 539 1/4 / 555 1/4 | 632 / 651 | 833 5/8 / 858 5/8 | 1073 1/3 / 1105 1/2 |
| Plan | 8 1/2 (4.885 m) | 9 (5.172) | 10 (5.747) | 11 (6.321) |
| Puntal | 8 1/2 (4.885) | 9 (5.172) | 10 (5.747) | 11 (6.321) |
| Quilla | 46 (26.435) | 48 (27.585) | 51 (29.309) | 54 (31.033) |
| Eslora | 58 3/4 (33.762) | 61 1/2 (35.343) | 66 (37.929) | 70 1/2 (40.515) |
| Rake stem | 8 1/2 (4.885) | 9 (5.172) | 10 (5.747) | 11 1/2 (6.609) |
| Rake stern ("la mitad", half the stem) | 4 1/4 (2.442) | 4 1/2 (2.586) | 5 (2.873) | 5 (2.873) |
| Rasel aft (fwd = 1/2) | 5 2/3 (3.257) | 6 (3.448) | 6 2/3 (3.831) | 7 (4.023) |
| 'Tweendeck height | 3 1/8 (1.796) | 3 1/6 (1.820) | 3 1/4 (1.868) | 3 1/4 (1.868) |
| Hold beams below deck | 3 1/2 (2.011) | same | same | same |
| Maderos de cuenta | 37 | 39 | 41 | 43 |

Other 1613 rules ([FG]):
- The widest breadth is at the depth for merchant ships, and **1/2 codo below it for armada ships** (the armada deck is 1/2 codo = 287.3 mm higher).
- Mura at L/4 + 1 from the stem, with breadth −1. Cuadra at L/4 + 2 from the sternpost, with breadth −2.
- Fleet limit 17 1/2 codos breadth and 8 1/2 depth.

Note: the 1613 18-codo row has the same keel and length as the 1618 19-codo row (my comparison).

### 1607 galleon rows

Source: [FG] Table 2, pp.10-11 (read).
- Depth is from the floor ceiling to the deck planking, at the breadth.
- Armada ships had the deck **1 codo** above the breadth.
- *Puente* (bridge) is cubits above the deck. *Alcázar* (halfdeck) is cubits above the bridge.
- Rising (rasel) is given at the stern; the stem rising is half of it.

| Toneladas | Manga | Puntal | Eslora | Quilla | Rasel | Puente | Alcázar |
|---|---|---|---|---|---|---|---|
| 487 1/8 | 15 | 8 | 52 | 40 | 5 1/2 | +3 | +3 |
| 567 7/8 | 16 | 8 3/4 | 57 | 42 | 5 3/4 | +3 | +3 |
| 669 3/8 | 17 | 9 1/4 | 60 | 43 | 6 | +3 | +3 |
| 755 | 18 | 9 1/2 | 62 | 44 | 6 1/2 | +3 | +3 |
| 897 3/8 | 19 | 10 | 65 | 47 | 6 3/4 | +3 | +3 |
| 1033 | 20 | 10 1/2 | 69 | 48 | 7 | +3 | +3 |
| 1184 5/8 | 21 | 11 | 72 | 51 | 7 1/4 | +3 | +3 |

Example in metres, 17 codos: 9.77 × 5.32 (depth) × 34.48 (length) × 24.71 (keel). The 1607 Ordenanza gives no rake figures.

### Galleons of 1582-1589

Source: [FG] Table 1, p.2 (read). Codos of 0.57468 m.
- HB = floor to hold beams.
- D1 = hold beams to deck.
- D2 = 1st 'tweendeck.
- D3 = 2nd 'tweendeck.

| Year / group | Tons | L | K | B | HB | D1 | D2 | D3 |
|---|---|---|---|---|---|---|---|---|
| 1582, 2 large | 550 | 56 | 36 | 16 | 4 | 3.5 | 3.5 | 3.75 |
| 1589, 4 small | 574 | 54 | 34 | 17 | 4 | 3.5 | 3.5 | — |
| 1589, 4 medium | 742 | 59 | 38 | 18.5 | 4 | 4 | 3.5 | 3.5 |
| 1589, 4 large | 974 | 64 | 42 | 20.5 | 4 | 5 | 3.5 | 3.5 |

So the deck spacing was **3.5 codos = 2.01 m (20 voxels)**.

### 1666 / 1679 changes to reduce draft

Source: [FG] Table 5, p.15 (read).

| | 1666, 500 t | 1666, 700 t | 1679, 800 t |
|---|---|---|---|
| Manga | 17 1/2 (10.057 m) | 18 1/2 (10.632) | 19 (10.919) |
| Plan | M/2 + 1/4 = 9 (5.172) | M/2 + 1/3 = 9 7/12 (5.507) | 9 3/4 (5.603) |
| Puntal | 8 1/4 (4.741) | 8 3/4 (5.028) | 9 1/4 (5.316) |
| Quilla | 50 (28.734) | 53 (30.458) | 55 1/2 (31.895) |
| Eslora | 62 (35.630) | 65 (37.354) | 67 1/2 (38.791) |
| Rakes as printed: "Stern" / "Stem" | 10 / 2 | 10 / 2 | 11 / 1 |
| Rasel aft / fwd | 6 / 2 1/4 | 6 1/3 / 2 1/3 | 7 1/4 / 2 1/2 |
| Yugo (transom) | 9 1/2 | 10 | 12 1/3 |
| Puente / Alcázar | 3 / 3 1/4 | 3 / 3 1/3 | 3 / 3 1/4 |

Caution: [FG] labels the 10-codo rake "Stern" and the 2-codo rake "Stem". That is the opposite of the 1613/1618 tables and of Palacio, so the labels are probably swapped. I am reporting them as printed.

[FG] p.10: under the 1618 rules the same beams would give 577, 689 and 721 t.

---

## 4. García de Palacio, *Instrucción náutica* (1587): the 400-tonelada nao

Source: Palacio's text as quoted in [VIS] pp.7-14 (read), with Palacio's folio numbers. Units are codos castellanos; converted at 0.55766 m.

| Item | Codos | Metres | Palacio quote / folio |
|---|---|---|---|
| Quilla (codaste to codillo de proa) | 34 | 18.96 | "treynta y quatro codos de quilla" (p.90) |
| Manga | 16 | 8.92 | "de manga, diez y seis, que es casi la mitad de la quilla" (p.90) |
| Puntal to main deck, without xareta | 11 1/2 | 6.41 | "onze codos y medio de puntal, que es el tercio de la dicha quilla" (p.90) |
| Puntal with xareta (grating deck) | 14 1/2 (+3) | 8.09 | p.90 |
| Hold beams (1st division) | 4 1/2 above keel | 2.51 | "en quatro codos y medio de puntal, que es la altura de tres pipas" (p.90v) |
| 1st deck | +3 above hold beams (= 7 1/2) | 1.67 / 4.18 | p.90v |
| Puente (2nd deck) | +3 more (= 10 1/2; 11 with beams) | 1.67 / 6.13 | p.90v. Elsewhere 11 1/2 (p.92v). [VIS] note 55 flags the 11 vs 11 1/2 discrepancy. |
| Rake aft ("roda de popa") | 5 2/3 (1/6 of keel) | 3.16 | p.92r |
| Rake fwd | double the aft, = 11 1/3 | 6.32 | p.92r |
| Eslora roda a roda | 51 1/3 | 28.62 | p.92r |
| Plan (master frame) | 5 1/3 (1/3 of manga) | 2.97 | p.92v |
| Master frame position | keel midpoint + 2 codos forward | 1.12 | p.92v |
| Aletas (stern fashion pieces) | seated on the codaste at 6 2/3, rising 12 more = 18 2/3 | 3.72 / 10.41 | p.92r |
| Dragante (≈ yugo, transom beam) | 7 2/3 ("casi la mitad que la nao tiene de manga") | 4.28 | p.92r |
| Astilla at fore redel / aft redel | 1 1/2 / 2 1/2 | 0.84 / 1.39 | p.92v |
| Breadth at aft redel (per text) | 14 | 7.81 | p.92v. [VIS] argues it is really the fore redel. |
| Wales | from 10 codos high amidships to 16 at the ends | 5.58 → 8.92 | [VIS] p.14 paraphrase |

Ratios: 51 1/3 : 34 : 16 gives 3.2 : 2.125 : 1 ([VIS] p.9). [CIHCN] p.35 lists Palacio as eslora/manga **3.23** and quilla/manga **2.12**.

[VIS]'s reconstruction: LOA 28.23 m, waterline length 24.84 m, beam 8.92 m, draft 4.18 m, Cb 0.496, Cp 0.606, Cm 0.818. His estimated capacity (346-363 t) is below Palacio's stated 400 ([VIS] pp.20, 27-28).

### Palacio's mast and yard rules

**Secondary source:** [MP] blog, through a summarising fetch only; not verified against Palacio's text. The example ship is the same 400 t nao, manga 16.

| Spar | Rule | Codos | Metres (0.55766) |
|---|---|---|---|
| Árbol mayor (mainmast) | "la misma que se tuviese desde el codillo de proa hasta el codaste"; example given as 46 | 46 | 25.65 |
| Trinquete (foremast) | = keel length | 34 | 18.96 |
| Bauprés | 1/5 less than the trinquete (blog says 28) | 28 | 15.61 |
| Mesana | same as the bauprés | 28 | 15.61 |
| Mastelero mayor (main topmast) | 1 1/2 manga | 24 | 13.38 |
| Verga mayor (main yard) | 2 1/3 manga (blog states "37 1/2") | 37 1/3 to 37 1/2 | 20.8 to 20.9 |
| Verga trinquete | 1/3 shorter than the main yard | ≈25 | ≈13.9 |
| Cebadera (spritsail yard) | 1/4 shorter than the fore yard | ≈18.7 | ≈10.4 |
| Verga de mesana | its mast + 1/3 | ≈37 | ≈20.8 |
| Main topsail yard (gavia) | = manga | 16 | 8.92 |
| Fore topsail yard | 1/5 less | 12.8 | 7.14 |
| Main top (cofa) circumference | = manga | 16 | 8.92 |

---

## 5. Tomé Cano, *Arte para fabricar, fortificar y aparejar naos* (1611)

### Hull

- Cano takes the **manga as the base measurement**: "Lo primero que se ofrece ... es la manga que ha de tener" (Cano 1611 fol. 14v, quoted in [VIS] p.3, read).
- Traditional rule **"as, dos, tres"**: manga 1, keel 2 × manga, eslora 3 × manga ([VIS] p.3, read). [CTL] p.8 note 14 (read) says Palacio departs from this "rígido y tradicional canon de as, dos, tres" only slightly.
- Cano's proportions, from [CIHCN] p.35 table (read): **eslora/manga 3.30, quilla/manga 2.56** (no puntal given).
- In metres, a manga of 17 codos de ribera (9.77 m) would give keel 43.5 codos (25.0 m) and eslora 56.1 codos (32.2 m). This is my arithmetic.
- Cano introduced the **joba**, following Juan de Veas ([FG] p.6; [VIS] p.4).

### Comparison table, [CIHCN] p.35 (read)

| Author | Date | Eslora/manga | Quilla/manga | Puntal/manga |
|---|---|---|---|---|
| Escalante | 1575 | 3.18 | 2.28 | 0.65 |
| García de Palacio | 1587 | 3.23 | 2.12 | — |
| Tomé Cano | 1611 | 3.30 | 2.56 | — |
| Ordenanzas de la Casa de Contratación | "1566" as printed (the text says 1613) | 3.51 | 2.86 | — |
| Garrote | 1691 | 3.43 | 3 | 0.39 |

For comparison, the 1618 Ordenanza (my arithmetic from [FG]) gives:
- 17 codos: eslora/manga 3.29, quilla/manga 2.59, puntal/manga 0.47.
- 21 codos: eslora/manga 3.14, quilla/manga 2.43.

### Cano's mast and yard rules

**Secondary source:** [MP] blog, summarised; not checked against Cano's text. All are proportions of the manga measured at the main deck. For mangas over 15 codos the lengths are "somewhat smaller" (the exact reduction was not obtained).

| Spar | Rule | Example, manga 17 codos de ribera (my arithmetic) |
|---|---|---|
| Árbol mayor | 2 1/2 × manga; thickness linked to 1/5 (the blog wording about girth is unclear) | 42.5 codos = 24.42 m |
| Trinquete | mainmast − 1 codo | 41.5 = 23.85 m |
| Bauprés | = trinquete | 41.5 = 23.85 m |
| Masteleros (topmasts) | 1/2 of their mast | main 21.25 = 12.21 m |
| Verga mayor, merchant | mainmast − 5% | 40.4 = 23.20 m |
| Verga mayor, warship | 2 1/4 × manga | 38.25 = 21.98 m |
| Verga trinquete | 1/5 shorter than the main yard | (warship) 30.6 = 17.59 m |
| Cebadera | 1/3 shorter than the fore yard | 20.4 = 11.72 m |
| Verga de gavia (topsail yard) | 2/5 of its mast | main 17 = 9.77 m |
| Cofa mayor | upper circumference = manga | 17 = 9.77 m |

### Escalante de Mendoza (1575) mast rules

Secondary source: [MP], summarised.
- Mast length = 3 × (distance from the step to the puente): 2 parts above the puente, 1 below.
- Topmasts are 1/3 shorter than their masts.
- Main yard ≈ 2 × manga + "a little".
- Fore yard is 1/3 shorter than the main yard.
- Cebadera = 1/2 the fore yard.

---

## 6. Gun decks and gun counts

There is **no official guns-per-tonnage table** in the sources I read. These are scattered data points:

- **Decks under the 1618 Ordenanza:** the main deck plus the flush **puente** (bridge) 3 codos above it is the second, upper gun deck. A third deck was **prohibited** for the Indies fleets (royal decree of 28 Aug 1628, relaxed 17 Oct 1628 provided the third deck was not completed). Even so, **Carrera galleons were three-deckers by 1640**, preferred over the open-waisted (*pozo*) type ([FG] p.9, read).
- **Gun ports:** sill 1 codo above the deck, 1 1/4 codos square (1618 art. 42, [FG] p.20, read).
- **Iron guns** came aboard **about 1630** ([FG] p.9, read).
- ***Nuestra Señora de Atocha*** (1620): **550 t, 20 bronze guns plus versos**; length about 34 m, beam about 10 m, draft about 4.3 m. [SNIP], Wikipedia and shipstamps snippets only. Sources differ: "20 till 24 guns".
- **1613 galleon of 17 codos:** "seis portas por banda en la primera batería" (6 ports per side on the lower battery). [SNIP], search summary only. The dimensions quoted with it (keel 46, eslora 58 3/4, manga 17, puntal 8 1/2) match the 1613 table.
- ***Nuestra Señora del Juncal*** (lost 1631): manga 19 codos, about 669 toneladas. [SNIP], from a truncated review. Casabán argues it was built to the 1618 Ordenanza; another reviewer says it was not.
- ***Nuestra Señora de la Concepción y las Ánimas*** (1688): **90 guns, three-decker**, among the last built to the 1618 rules ([FG] p.10, read). This is far outside the 500-1000 t class and is given for scale only.

---

## 7. Where the sources disagree (listed side by side, not averaged)

| Question | Version A | Version B |
|---|---|---|
| Shipwright codo | 0.57468 m ([FG] tables; [CIHCN]) | 0.57864 m ([FG] units box); 0.560 m (Conway, snippet); 2/3 vara ≈ 0.557 m (1613 art. 103, snippet) |
| Which rake is larger | Stem rake = 2 × stern rake (1618 and 1613 tables; Palacio 1587) | [FG] note "Fore Rake = half the Stern post Rake"; 1666/1679 table prints "Stern 10, Stem 2" |
| Palacio's main-deck height | 11 1/2 codos (fol. 90 and 92v) | 10 1/2 / 11 codos (fol. 90v deck-by-deck sum) |
| Palacio's main yard | 2 1/3 manga = 37 1/3 | "37 1/2" as printed in [MP] |
| Main yard rule | Cano (war): 2 1/4 manga; Cano (merchant): mainmast − 5% | Palacio: 2 1/3 manga; Escalante: ≈ 2 manga + |
| Mainmast rule | Cano: 2 1/2 × manga | Palacio: distance codillo de proa to codaste (46 codos in the example); Escalante: 3 × (step to puente); 1613 Ordenanza: based on keel length (rule not obtained) |
| 1618 14-codo tonnage | 409 1/2 t as printed | Out of sequence (15 codos = 371 1/2 t); probably a typo |
