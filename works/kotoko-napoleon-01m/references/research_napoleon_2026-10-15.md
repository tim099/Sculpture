# Le Napoléon (1850) — research notes for a 0.1 m/voxel model

Compiled 2026-10-15, web research only (~25 min). Every figure carries its source. Tags used:
- **[read]**: I opened the page and read it.
- **[snippet only, not read]**: the figure came from a search-result summary and I did not open the page.
- **[my measurement]**: I estimated it from a photo or print; it is not a published figure.

Main secondary sources:
- **SS = Shipscribe**, https://shipscribe.com/marvap/133a.html (Napoléon class page). It follows Winfield & Roberts, *French Warships in the Age of Sail 1786–1861* (Seaforth 2015). **[read]**
- **WP-en**, https://en.wikipedia.org/wiki/French_ship_Napoléon_(1850), infobox and text. **[read]**
- **WP-fr**, https://fr.wikipedia.org/wiki/Napoléon_(1850), infobox. **[read]**
- **NE = naval-encyclopedia**, https://naval-encyclopedia.com/industrial-era/1860-fleets/france/napoleon-1850.php. **[read]** It is internally inconsistent; treat as low reliability.
- **MF = militaryfactory**, https://www.militaryfactory.com/ships/detail.php?ship_id=Napoleon-I. **[read]** It cites no sources; low reliability.

---

## 1. Principal dimensions

| Quantity | Value | Source |
|---|---|---|
| Length on deck (gun deck) | **71.46 m** (234 ft 5 in) | SS |
| Length at waterline | **71.23 m** (233 ft 8 in) | SS |
| Length (type not stated, probably overall incl. figurehead/bowsprit heel) | **77.8 m** (255 ft 3 in) | WP-en / WP-fr infobox, also NE table |
| Length (type not stated) | "about 240 ft (73 m)" | Scientific American Supplement No. 481, 21 Mar 1885, as quoted in WP-en and WP-fr |
| Length | 239.6 ft (73.03 m) | MF |
| Keel length | **not found** | — |
| Moulded breadth | **16.22 m** (53 ft 3 in) | SS |
| Extreme breadth | **16.80 m** (55 ft 1 in) | SS |
| Breadth (type not stated) | 17 m (55 ft 9 in) | WP-en / WP-fr ("maître-bau 17 m") |
| Breadth | 55 ft (17 m) | Sci. Am. 1885 quote (WP-en); also NE body text |
| Depth of hold (creux) | **not found** | — |
| Draught, mean | **7.86 m** (25 ft 9 in) | SS |
| Draught, maximum | **8.26 m** (27 ft 1 in) | SS |
| Draught (type not stated) | 8.4 m (27 ft 7 in) | WP-en / WP-fr |
| Draught | 26.4 ft (8.05 m) | MF |
| Draught | 27 ft | NE body text |
| Draught "à pleine charge" | 8.45 m | **[snippet only, not read]**, search summary, source page not identified |
| Draught fore/aft, light/loaded, separately | **not found** | — |
| Displacement | **5,120 t** | SS, WP-en, WP-fr, NE table |
| Displacement | "5,000 tons" | Sci. Am. 1885 quote (WP-en); NE body text |
| Displacement | ~5,040 t | **[snippet only, not read]**, search summary |
| Tonnage (tonneaux de jauge) | **not found** | — |

None of the sources I read gave French pieds/pouces. The 1853 primary source (Dupuy de Lôme, *Note extraite du mémoire relatif à la construction du vaisseau à vapeur le Napoléon*, 19 pp. with tables, CNAM 4 Sa 29, https://cnum.cnam.fr/redir?4SA29, PDF https://cnum.cnam.fr/PDF/cnum_4SA29.pdf) contains tables of dimensions and trial data. However, its text layer is unreadable OCR garbage. Someone would need to read the page scans by eye; this is the best single path to authoritative numbers.

**Model evidence:** the Musée national de la Marine model 23 MG 8 is a 1/50 Toulon-arsenal model, c.1850, "plan Dupuy de Lôme". It measures L 127 cm × H 52 cm × W 25 cm (Commons file page, read). At 1/50 that is 63.5 m long and 12.5 m wide. Both figures are smaller than the published dimensions, so either the scale or the measurement basis (e.g. hull only, or base) is off. Do **not** scale from the model's catalogue dimensions.

**Voxel guidance (my suggestion, not sourced):** use the SS figures for the hull:
- 71.5 m on deck ≈ 715 voxels
- 16.2 m moulded / 16.8 m extreme beam ≈ 162–168 voxels
- ~8 m loaded draught ≈ 80 voxels

The 77.8 m figure is most plausibly an overall length including the head.

## 2. Armament

### As built (1852), per SS [read]

| Deck | Guns (both sides) | Per broadside |
|---|---|---|
| Gun deck (batterie basse) | 32 × 30-pdr No.1 + 4 × 22 cm No.1 shell guns (obusiers) = **36** | 18 |
| Upper deck (2e batterie / batterie haute) | 26 × 30-pdr No.2 + 4 × 22 cm No.2 shell guns = **30** | 15 |
| Spar deck (gaillards) | 14 × 16 cm shell guns = **14** ("possibly also 10 carronades") | 7 (+5) |
| Total | 80 (+10 carronades = 90) | |

- WP-en infobox gives the same three groups (32–30 pdr + 4–22 cm; 26–30 pdr + 4–22 cm; 14–16 cm) but does not assign them to decks.
- MF gives the same groups plus "10 × Carronades".
- Clerc-Rampal 1913 caption (FMIB 47776, Commons) says "portant 92 canons".
- A contemporary lithograph title (RMG / Frémy) says "100 canons". A RN officer's 1853 sketch is captioned "French 100-gun screw ship".
- The 90-gun rating is nominal.

### By 1862, per SS [read]

| Deck | Guns |
|---|---|
| Gun deck | 36 × 16 cm rifles |
| Upper deck | 34 × 30-pdr No.2 |
| Spar deck | 20 × 16 cm shell guns |

SS also says the "armament was redistributed several times in the 1850s".

### Gunports per side
These are **inferred** from the gun counts, not from a source:
- Lower deck: **18**
- Upper deck: **15**; by 1862 there were 34 guns there, which implies **17** ports
- Gaillards: **7**, possibly 10–12 with carronades

The museum model photo (see §7) shows two complete tiers of ports, with a few ports on the quarterdeck and forecastle bulwarks and an open waist. I did not count them reliably at the photo's resolution.

**Bow/stern chasers:** not found.

## 3. Deck arrangement

- **Gun decks:** two. Sources: WP-fr ("deux ponts de canons"); Sci. Am. 1885 quote ("with two gun decks"); NE ("two complete and one incomplete upper decks"). NE's "90 guns on 3 decks" counts the gaillards as the third.
- **Model photo [my observation]:** the spar deck is split into quarterdeck and forecastle with an open waist between them. There is no separate poop (dunette) visible.
- **Faux-pont, height between decks, engine-room station, coal bunkers:** **not found** in any readable source.
- **Endurance:** WP-en gives "9 days' worth of coal at full speed; 3 months' food". NE gives "around 1,500 nm with steam only".
- **Engine and boiler position (inference):** the two funnels sit either side of the mainmast (see §4), which suggests boiler spaces fore and aft of the mainmast step. Shaft-driven machinery would sit aft of the boilers. This is inference, not sourced.

## 4. Steam plant

**Original engine** (SS, WP-en) [read]
- 2-cylinder geared engine built by **Indret** (the state works)
- **960 nhp**; WP-en also gives "574 ihp", from Winfield & Roberts via WP

**Re-engined 1861** (SS) [read]
- **Mazeline** direct-acting engine, 900 nhp, **1,798 ihp**, 12.94 kn
- SS gives the reason: the gearing "created maintenance problems"

**Boilers:** number **not found**. MF says "1 x … coal-fired boiler", which is unreliable and probably a garbled infobox.

**Speed**

| Speed | Context | Source |
|---|---|---|
| 12.14 kn sustained | 30 Aug 1852, Toulon→Ajaccio, 119 nm | SS [read] |
| 13 kn | for short periods, same run | SS [read] |
| **13.86 kn** | 25 Sep 1852, Marseille–Toulon run | Commons description of FMIB 47776, from Clerc-Rampal, *La Mer* (Larousse 1913) p.159 [read, Commons page] |
| "nearly 14 knots" | not stated | Sci. Am. 1885 quote in WP-en |
| 13.8 kn (25.5 km/h) | after commissioning | WP-fr |
| 12.1 kn | not stated | WP-en / WP-fr infobox |

**Funnels**
- SS: "the only French ship of the line with **two funnels**" [read].
- Position, from images [my observation]:
  - Museum model 23 MG 8, Commons photo: one funnel just abaft the mainmast and one roughly midway between mainmast and foremast. Measured along the deck from the stern on the photo, the stations are about: mizzen 0.12 L, aft funnel 0.33 L, main 0.40 L, fore funnel 0.59 L, fore 0.78 L. These are approximate, from a side photo.
  - Le Breton lithograph (1850) and Figuier fig. 106: both show the same layout, two black funnels flanking the mainmast with the forward one between main and fore.
- **Telescopic?** No written source found. In the c.1860 photograph (Commons "Napoleon (1852).jpg") no funnels show above the bulwarks except a short stub between main and fore. That is consistent with lowering/telescopic funnels while under sail. This is my inference from the photo, not sourced.
- Colour: black in all coloured prints I viewed.

**Propeller**
- SS: "All but Napoléon and Algésiras had hoisting screws". So *Napoléon* had a **fixed (non-lifting) screw** with no screw well [read].
- Blades: MF says "1 x shaft 3-blade propeller" (unsourced, low reliability).
- Diameter and pitch: **not found**.
- The museum model shows an open screw aperture between sternpost and rudder post [my observation].

**Other**
- Sail area: **3,411 sq yd ≈ 2,852 m²** (SS [read]; MF repeats it).
- Complement: 910 (WP-en); 913 (SS class table).

## 5. Rig

- Three-masted full ship rig (NE: "3 masts squared full rig").
- Total sail area 3,411 sq yd ≈ 2,852 m² (SS).
- **No ship-specific mast, yard or bowsprit dimensions found.**
- **No generic French 1840s–50s masting rule found online** in the time available. Bonnefoux & Pâris, *Dictionnaire de marine à voile et à vapeur* (1847/1856) is the right reference (entries "mâture", "mât", "vergue"). It is on Gallica, but I did not locate the relevant page.
- **Workaround:** take mast positions and relative heights from:
  - the Commons model photo, for deck stations;
  - the Le Breton broadside lithograph and Figuier fig. 106, for rig proportions.
- **Mast stations [my measurement from the model photo]:** mizzen ≈ 0.12 L, main ≈ 0.40 L, fore ≈ 0.78 L from the stern along the deck. Bowsprit steeved up roughly 20–25° on the model, eyeballed.

## 6. Appearance

**Hull paint (observed in images)**
- Black hull with **two white bands** along the gun tiers and black port lids, i.e. a black-and-white "Nelson chequer". Seen in:
  - Le Breton lithograph (1850, RMG PAH9258 / Commons "Lebreton engraving-19.jpg")
  - Figuier fig. 106 (same Le Breton design)
  - the c.1860 photograph ("Napoleon (1852).jpg"), where white bands with dark ports are clearly visible on both tiers
- Ochre/yellow trim on the quarter galleries and rails in the coloured Le Breton print.
- The museum model shows the bands as light natural wood with black wales; it is a model finish, so read it as "light band".
- Lower hull below the wale: dark/black in the prints; natural wood on the model.

**Stern**
- **Rounded stern** with closed quarter galleries. WP-en caption on "Le_Napoleon_1852.png": "rounded stern visible". The Le Breton print shows the curved stern with an ochre/gold rail.

**Funnels:** black.

**Figurehead:** **not found**. No source describes it. The Quebec "Napoléon" figurehead (MNBAQ, c.1830) is unrelated.

**Name on stern:** not found.

**Flag:** French tricolour ensign at the mizzen gaff (prints).

## 7. Images and plans viewable online

### Original construction plans: none found online in free form

| Holding | Notes |
|---|---|
| **National Maritime Museum Greenwich, box FORB0004** | Contains "three plans for 'Napoleon' (1850)". Catalogue only, no images online, © Crown copyright. https://www.rmg.co.uk/collections/objects/rmgc-object-373437 |
| **Archives nationales / SHD, Atlas du génie maritime** | No online plate for *Napoléon* found. The 2nd series (1859–1889, SHD digital library) is too late. The 1st series was not located online. |
| **Reconstructed drawings** | Profile and 6 cutaways "Reconstructed from the original plans". Licence unknown, not free. Reddit r/WarshipPorn post: https://www.reddit.com/r/WarshipPorn/comments/ovujhn/drawings_of_the_worlds_first_steam_battleship/ (could not fetch). Mirrored on NE, e.g. https://naval-encyclopedia.com/wp-content/uploads/2018/03/plans-Napoleon1850-profile-1024x576.webp and …cutaway-1024x576.webp to …cutaway6-1024x576.webp, plus https://naval-encyclopedia.com/wp-content/uploads/2023/09/napoleon-schemeplan.jpg. Probably the most useful geometric reference, but copyright status is unclear. Use for reference only. |

### Free-licence images on Commons (category: https://commons.wikimedia.org/wiki/Category:Napoléon_(ship,_1852))

| # | File page | What it shows | Licence |
|---|---|---|---|
| A | https://commons.wikimedia.org/wiki/File:Napoleon-MnM_23_MG_8-IMG_6274.jpg | **Exact side view (port side, stern left) of the 1/50 Toulon arsenal model, MnM 23 MG 8, "plan Dupuy de Lôme"**. 3451×2133 px. Lower masts stumped, both funnels, both port tiers, screw aperture and rudder. **Best "profile" available.** | CC BY-SA 3.0 FR / 2.0 FR / CeCILL (photo by Rama) |
| B | https://commons.wikimedia.org/wiki/File:Lebreton_engraving-19.jpg | Le Breton & Bry coloured lithograph, 1850 (= RMG PAH9258). Starboard-quarter view under sail and steam. Paint scheme, funnels, full rig, stern. 4016×2456 px. | Public domain |
| C | https://commons.wikimedia.org/wiki/File:Napoleon_(1852).jpg | Photograph c.1860, near-broadside, at anchor with sails loosed. Hull bands, rig proportions, funnels lowered. 1116×711 px. | Public domain |
| D | https://commons.wikimedia.org/wiki/File:T1-_d235_-_Fig._106._%E2%80%94_Le_Napol%C3%A9on,_vaisseau_mixte_%C3%A0_h%C3%A9lice.png | Figuier, *Merveilles de la science* t.1, fig. 106 (after Le Breton). B&W engraving, 3/4 starboard view with both funnels. 2744×2039 px. | Public domain |
| E | https://commons.wikimedia.org/wiki/File:Le_Napoleon_1852.png | Clerc-Rampal 1913, two small views, rounded stern. 502×406 px. | Public domain |
| F | https://commons.wikimedia.org/wiki/File:FMIB_47776_Vaisseau_a_Helice_et_a_grande_vitesse_le_Napoleon,_de_960_chevaux,_portant_92_canons,_et_lance_le_15_mai_1850_a_Toulon,_sur_les.jpeg | F. Roux watercolour (Musée de la Marine), reproduced by Clerc-Rampal 1913. Caption gives 960 ch, 92 canons, 13.86 kn. | Public domain |
| G | https://commons.wikimedia.org/wiki/File:Napol%C3%A9on_1850.jpg | Frémy lithograph 1850 (NMM Greenwich). | CC0 |
| H | https://commons.wikimedia.org/wiki/File:Fartygsportr%C3%A4tt-Franskt_%C3%A5nglinjefartyg_-_Sj%C3%B6historiska_museet_-_O_04086.tif | Ship portrait, Sjöhistoriska museet. 3436×2546 px. | Public domain |
| I | https://commons.wikimedia.org/wiki/File:Illustreret_Tidende_1860_-_Anton_Melbye_-_Linjeskibet_Napoleon.png | Melbye painting reproduced in 1860. 2913×1888 px. | Public domain |
| J | https://commons.wikimedia.org/wiki/File:Napoleon-IMG_4886.JPG (and _4887, "Toulon harbour mg 5247.jpg") | Morel-Fatio 1852 painting, Musée d'Art de Toulon, plus details. | CC BY-SA 2.0 FR |
| K | https://commons.wikimedia.org/wiki/File:NapoleonWoodenPlanking.jpg | Actual hull planking section hit in the Crimean War. Planking thickness reference. | Public domain |

None of A–K is a measured draught (sheer plan, body plan, deck plan or sail plan).

## Conflicts & gaps

**Conflicts (kept side by side, not averaged)**
- **Length:** 71.23 m WL / 71.46 m deck (SS) vs 73 m / 240 ft (Sci. Am. 1885, MF) vs 77.8 m (WP infobox, NE). Probably different measurement bases: deck, perpendiculars, overall.
- **Beam:** 16.22 m moulded / 16.80 m extreme (SS) vs 17 m (WP) vs 17.01 m (MF).
- **Draught:** 7.86 m mean / 8.26 m max (SS) vs 8.4 m (WP) vs 8.05 m (MF) vs 8.45 m (snippet only).
- **Displacement:** 5,120 t (most sources) vs 5,000 t (Sci. Am. 1885) vs 5,040 t (snippet only).
- **Speed:** 12.14 kn sustained (SS) vs 13 kn peak (SS) vs 13.86 kn (Clerc-Rampal) vs 13.8 kn (WP-fr) vs 12.1 kn (WP infobox).
- **Guns:** 80 + 10 carronades = 90 (SS) vs "92 canons" (Clerc-Rampal) vs "100 canons" (contemporary lithograph/RN sketch).
- **Laying-down date:** 7 Jan 1848 (SS) vs 7 Feb 1848 (WP).
- **Launch date:** 16 May 1850 (SS, WP) vs "15 mai 1850" (Clerc-Rampal caption).
- **Retirement date:** stricken 6 Nov 1876 (SS, WP) vs "discarded November 1873" (NE).
- **Model:** 1/50 model catalogue dimensions (127 cm long, 25 cm wide) do not scale to the published dimensions.

**Not found**
- Keel length, depth of hold, tonnage (jauge), fore/aft and light/loaded draughts, original French-unit dimensions.
- Height between decks, faux-pont layout, engine-room and boiler stations, coal bunker layout, number of boilers.
- Propeller diameter and pitch (blade count only from an unreliable source).
- Written confirmation of telescopic funnels (photo suggests lowerable).
- Any mast, yard or bowsprit dimensions, and the generic French masting rule.
- Figurehead subject, name on stern, bow/stern chasers.
- Any free-licence original plan: profile, body plan, deck plan or sail plan.

**Best next steps to close the gaps**
1. Read the page images of Dupuy de Lôme's 1853 *Note … du vaisseau à vapeur le Napoléon* (CNAM 4 Sa 29). It has dimension and trial tables.
2. Winfield & Roberts 2015, p.~67 (cited by WP), or Roche, *Dictionnaire des bâtiments* vol. I, for metric dimensions and armament.
3. Ask NMM Greenwich (FORB0004) or SHD/Archives nationales for the Atlas du génie maritime plate.
4. Bonnefoux & Pâris, *Dictionnaire de marine à voile et à vapeur* (Gallica), for the masting rule.
