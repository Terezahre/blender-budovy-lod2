# Wiki Log

## [2026-11-23] build | 15 vikýřů západního svahu ID-1465 (5+2+8)
- Disposition: New
- Raw: raw/pl/2026-11-23-vikyre15.md
- Updated: wiki/pl/vikyre-15.md, wiki/index.md
- 15 obdélníků (horní 5 + dolní 2+8), top=q95 LiDARu, boolean 15/15 (Blender 5.3),
  nm=0 (89 vrcholů pasu s res>0.15 srovnáno na rovinu: pryč i stromový trn
  u dvojshluku a vlny kolem horních vikýřů),
  RMSE jádra 0.522->0.546, pásy 0.898->0.843, rendery před/po.
- Ponaučení: SZ boule = koruna stromu (ne vikýře); přímý mapping LiDAR<->orto sedí;
  Geoflow jehly přesahují topy -> boolean nutný.

## [2026-11-23] fix | Srovnán východní okap (curl u hrany pryč)
- 28 vrcholů (s 4.0..6.3, res>0.15) na východní rovinu; XY beze změny ->
  pokrytí 1.0, nm=0 (watertight); řez v t=2 max +0.11 m; RMSE vše 3.234->2.985.
- Příčina curlu: žlabové body + Geoflow přehnutí na hraně footprintu.

## [2026-11-21] ingest | Skutečný Geoflow běh 0.3.6 + srovnání
- Disposition: New
- Raw: raw/geoflow/2026-11-21-geof-run.md
- Updated: wiki/geoflow/skutecny-beh.md

## [2026-11-21] build | Three.js prohlížeč viewer_3d.html
- Disposition: New
- 7 budov Geoflow LoD2.2, geometrie vložená v HTML, S-JTSK offset v UI (2026-11-21: jen Geoflow, bez přepínače cest)

## [2026-11-21] build | Geoflow dialog (.bat + HTA JavaScript)
- Disposition: New; Update (9 rucnich parametru: planarita, complexity, raster)
- geoflow_dialog.bat + geoflow_dialog.hta: vstup, výstup, ID, profil + 9 číselných polí
- Nove globaly flowchartu: r_max_arr_complexity (400), r_raster_cellsize (0.05)

## [2026-11-21] ingest | Celomapový scan sedlovek + Geoflow-only
- Disposition: New; Update (vysledky-pilot.md)
- Raw: raw/pipeline/2026-11-21-scan-sedlovky.md
- Updated: wiki/pipeline/sedlovky.md
- Finále = 7× Geoflow LoD2.2 (B01–B04, G1–G3); vlastní cesta odstavena do output/ours/

## [2026-11-21] ingest | CityJSON výstup + Blender roundtrip
- Disposition: New
- Raw: raw/pipeline/2026-11-21-cityjson.md
- Updated: wiki/pipeline/cityjson.md
- Finále: 7× CityJSON 2.0 (EPSG:5514) + OBJ; run_cityjson.py pro všech 9 budov

## [2026-11-21] ingest | Střechy: placatění, G3 recept, globalizace CityJSON
- Disposition: New
- Raw: raw/geoflow/2026-11-21-strechy.md
- Updated: wiki/geoflow/strechy.md
- DETAIL flowchart + DETAIL_GABLE jen pro G3; G2 split negativní (ploché poloviny)

## [2026-11-21] ingest | ZABAGED footprinty (konec blobů)
- Disposition: New
- Raw: raw/pipeline/2026-11-21-zabaged.md
- Updated: wiki/pipeline/zabaged.md
- 1495 budov KRAV59; Z3 (RMSE 0.104) → 8. finální; Z1/Z2 REJECT; OSM blokováno (406)

## [2026-11-20] ingest | Data KRAV59 + Geoflow + PolyFit + Blender + pilotní výsledky
- Disposition: New
- Raw: raw/laz-dmp1g/2026-11-20-krav59-dmp1g.md
- Raw: raw/geoflow/2026-11-20-geoflow-bundle.md
- Raw: raw/polyfit/2026-11-20-polyfit-format-a-vahy.md
- Raw: raw/blender/2026-11-20-blender43-headless.md
- Raw: raw/pipeline/2026-11-20-pilot-vysledky.md
- Updated: wiki/laz-dmp1g/krav59-data.md
- Updated: wiki/laz-dmp1g/klastrovani.md
- Updated: wiki/geoflow/profily-parametru.md
- Updated: wiki/geoflow/rekonstrukce-postup.md
- Updated: wiki/polyfit/fallback.md
- Updated: wiki/blender/validace.md
- Updated: wiki/pipeline/vysledky-pilot.md

## [2026-11-22] ml | Pilot trenovani: Brno + raster-U-Net cesta (CPU)
- Disposition: New
- Rozhodnuto: hybrid (sit jen parametry/segmentace, geometrie dal Geoflow+Blender), raster 0.5m patche, lokalni CPU (i5/21GB, bez NVIDIA).
- Pripraveno: scripts/fetch_brno.py (Brno-stred bbox, 991 ZABAGED budov stazeno do ml/data_brno/), ml/make_patches.py (12 patchu z KRAV59 -> ml/patches/), ml/baseline_sklearn.py (RandomForest LOO presnost 0.50 na 12 vzorcich, nejdulezitejsi zstd+height).
- GT: Brno LOD2 (TopGis, data.brno.cz) + DMP1G LAZ (atom.cuzk.cz) se stahuji rucne po 1 dlazdici (FETCH_LOG.md); label z LOD2 nahradi heuristiku zstd.
- Next: rucni stazeni 1-2 DMP dlazdic + Brno LOD2 SHP, pak U-Net s RUIAN (krok 2), pak bez RUIAN (krok 3).

## [2026-11-22] ml | Brno pilot: DSM stazeno, 957 patchu, domain-gap nalezen
- Disposition: New
- DSM/DTM Brno 2x2 km (OMI ImageServer DMP2025/DMT2019, 8x TIFF 2000x2000 F32, ~134 MB, CC BY) -> ml/data_brno/dsm/ (gitignored).
- ml/make_patches_brno.py: 957 nDSM patchu s footprint-maskou (interior semantika = KRAV59 body.las); vyska median 16.7 m, max 57.6 m.
- Nalez: prahy zstd 1.2/2.5 z agents.md (kalibrovane na ridke DMP1G body) neplati pro husty DSM (median zstd 3.65) -> heuristika rika 570x hip, model z KRAV59 rika 697x gable. Prahy jsou sensor-dependent.
- Trenink s GT: ml/train_raster.py --labels ml/gt_krav59.json (8 vzorku, 7:1 gable) LOO 7/8 trivialne; MAE ridge 3.83 m (outlier panelak), eave 0.31 m. Ceka na Brno GT.
- SceneServer query vraci prazdne (overeno GET+POST); pudorys FeatureServer = interiery, ne GT. GT cesta = rucni Polygon-Z SHP (ml/pair_brno.py --mode brno pripraven, schema STRECHA_KOD overeno).
- Dalsi: rucni download Polygon-Z SHP Brno-stred -> ml/gt_brno.json -> retrain na stovkach vzorku.

## [2026-11-22] ml | Prvni trening na Brno GT: baseline 46 %, hip selhava
- Disposition: New
- N=914 (947 GT - 33 bez patchu; 957 patchu - 43 bez GT). Tridy: 360 flat / 372 gable / 182 hip.
- train_raster.py LOO: S-RUIAN 46.1 % vs BEZ-RUIAN 46.6 % (sance 33 %); hip recall ~5 % (9/182) - model hip temer nepredikuje.
- Regrese: MAE hrebene 5.63 m (spatne), okapu 1.20 m (OK). Top feature: area_RUIAN 0.159, zstd jen 0.033 (konec leakage).
- Zaver: GBM na rucnich priznacich = referencni cara, ne finalni model. RUIAN area zatim nepomaha (v ramci sumu).
- Bezi: ml/exp2_balanced.py (HGB balanced + hierarchie flat|gable-vs-hip, stratifikovany 5-fold).
- Dalsi: lepsi priznaky (pocet rovin RANSAC-lite, symetrie), pripadne maly MLP; U-Net az po vycerpani CPU moznosti.

## [2026-11-22] ml | Experiment 2: balanced modely, hip porad tezky
- HGB balanced: acc 0.44-0.47, hip recall 0.18-0.20 (3x lepsi nez base 0.07, za cenu celkove acc).
- Hierarchie flat|gable-vs-hip: hip recall az 0.23 (BEZ-RUIAN), acc 0.46.
- BEZ-RUIAN >= S-RUIAN ve vsech variantach -> RUIAN area jako samotny priznak nepomaha.
- Bezi exp3: priznaky poctu rovin (rmse1/rmse2/ratio, RANSAC-lite) + HGB balanced.

## [2026-11-22] ml | Experiment 3: priznaky rovin nepomohly (plateau 0.47)
- rmse1/rmse2/ratio (RANSAC-lite, 4 smery rezu): median ratio 0.777 - 2-rovina jen mirne lepsi nez 1-rovina.
- Vysledek: S-RUIAN 0.458 (hip 0.17) / BEZ-RUIAN 0.470 (hip 0.19). Zadny skok oproti exp2.
- Interpretace: DSM 0.5 m obsahuje kominy/klimatizace/vytahove sachte (LOD2 je modeluje od 3 m obvodu) -> rezidualni sum kazi rovinné fity; ruční priznaky plati strop.
- Bezi exp4: TVAROVE priznaky footprintu (protahlost, pravouhlost, kompaktnost - podstata RUIAN prioru) + MLP; S-RUIAN(tvar+DSM) vs BEZ-RUIAN(jen DSM). To je ferovy test krok 2 vs 3.

## [2026-11-22] ml | Experiment 4: tvar footprintu + MLP (strop 0.47 potvrzen)
- S-RUIAN(tvar+DSM)+HGB 0.464 (hip 0.21); S-RUIAN+MLP 0.454 (hip 0.29 - nejlepsi hip dosud).
- BEZ-RUIAN+HGB 0.465 (hip 0.18); BEZ-RUIAN+MLP 0.426 (hip 0.19).
- Zaver pilotu: rucni priznaky + melke modely maji strop ~0.46-0.47. RUIAN tvar mirne lepsi na hip recall (0.29 vs 0.19 u MLP), celkove v sumu.
- Krok 2 vs 3: s RUIAN prior je lepsi smer, ale rozhodne az silnejsi model.
- Dalsi: maly CNN na raw 64x64 patchi (torch CPU, lokalne) - konci rucni featury.

## [2026-11-22] ml | CNN na raw patchi: stale 0.46 (sum je v datech, ne v modelu)
- S-RUIAN(CNN+tvar) 0.461 (hip 0.19); BEZ-RUIAN(CNN jen DSM) 0.444 (hip 0.29).
- I konvoluce na celem 64x64 patchi neprolomily strop -> signal je slaby / labely zasumene.
- Hypotezy sumu: smisene STRECHA_KOD v budove, prestavby 2023-25, spatny join v radovkach.
- Bezi exp5: filtr purity==1.0 [& rok<=2023] -> pokud acc vyskoci, je to kuraci dat, ne model.

## [2026-11-22] ml | Experiment 5: cistota GT pomaha malo (+3 p.b.), gable kolabuje
- purity median 0.87, podil 1.0 jen 0.42; rok>2023 zadny (LOD2 2020-23 vs DSM 2025 ok).
- purity==1.0 (N=386): 0.497/0.487, ale gable recall 0.55->0.31 - cisty subset meni skladbu trid, neni to ciste vitezstvi.
- Zaver: sum v labely vysvetluje cast, ne strop. Samotna uloha '1 typ na budovu' je sporna (58 % budov smisenych).
- Pivot: regresni hlava (okap MAE 1.2 m) -> ml/predict_params.py doporucuje Geoflow profil+toml. Pretrenovani modelu na Brno GT bezi (ulozene gb_*.pkl).

## [2026-11-22] ml | Hybrid DOKONCEN: predict_params + ferovy holdout (Brno, ne KRAV59)
- Holdout SV kvadrant (train 627 / test 287): acc 0.467, MAE vysky 4.86 m (median 13 m).
- Klicove srovnani: rucni prahy zstd z agents.md na BRNO DSM daji 0.325 (vse hazi hip) - neprenasi se mezi senzory. ML 0.467 = +14 p.b. bez rucni kalibrace.
- KRAV59 pouzito jen jako smoke test pruchodnosti (out-of-domain senzor+mesto, bez naroku na presnost).
- ml/predict_params.py: patch -> profil + geof.toml hodnoty (okap deterministicky z DSM, bez ML identity). Demo: 12400478532927488 -> COMPLEX_HIP (GT hip OK), vyska 20.2 vs 17.5 m.
- Limity (poctive): acc 0.47 nestaci na slepe rizeni Geoflow; pouzivat jako DOPORUCENI + vzdy Blender validace. Hreben MAE 4.9 m.

## [2026-11-22] ml | Brno Geoflow test bezi: ML vs rucni parametry (3 budovy)
- Vyber: flat/gable/hip, purity 1.0, SV kvadrant (puvodni holdout): 53006722360410112 / 53006713149718528 / 27822445704511488.
- Pseudo-LAS z DSM/DTM (mrizka 1 m, S-JTSK, class 6/2) - DMP LAZ pro Brno netreba.
- Predbezne (bez geof behu): ML profily gable+HIP+gable (2/3 GT), rucni zstd vsude COMPLEX_HIP (1/3) - heuristika na DSM selhava.
- Bezi: scripts/brno_geof_test.py --run (6x geof: 3 budovy x ml/manual) -> output/brno_geof/results.json (RMSE/pokryti/manifold).

## [2026-11-22] ml | (a) Geoflow na Brne: split hladin nutny, profil nerozhoduje
- Pseudo-LAS z DSM/DTM (mrizka 1 m + jitter, pf1): geof chodi, manifold 0, pokryti 1.00.
- Bez splitu: RMSE 20.1 / 5.7 / 1.9 m (ZABAGED polygony michaji 2 vyskove hladiny).
- Se splitem (gap>=3 m -> hull komponenty): 1.25+0.79 / 3.27 / 2.04+0.81 m.
- ML vs MANUAL profily daji BITOVE STEJNE meshe (dense data konverguji) - profil je druhorady; vyjimka: 23bodova nizka pristroavba (SIMPLE_FLAT selhal, COMPLEX_HIP prosel).
- Zaver: pro Brno pridat krok split_levels pred Geoflow; gap 3.0->2.0 (sedlovka ma spicku +2.6 m).
- Opravy: r_* globaly v TOML (prazdne behy), jitter proti degeneraci DetectLines, nm eval.

## [2026-11-22] ml | (a) HOTOVO: Geoflow na Brne funguje, zaver pro hybrid
- 3 budovy (flat/gable/hip, SV kvadrant) -> pseudo-LAS z DSM (1 m + jitter, pf1): vsech 10+ behu OK, manifold 0, pokryti 1.00.
- RMSE po splitu hladin: 1.25+0.79 / 3.27 / 2.04+0.81 m (pred splitem 20.1/5.7/1.9).
- ML vs MANUAL profily: bitove stejne meshe (i FLAT vs HIP na 227 bodech). Profil na outputu pri hustych datech nezalezi.
- Sedlovka 3.27 m: horni body (kominy/nastavby z DSM 2025) netvori rovinu; ani COMPLEX_HIP (9.0/800) nepomuze. LOD2 z fotogrametrie vidi vic nez lidar-hustota unese.
- Nove poznatky pro pipeline: r_* globaly (prazdne behy bez warningu), jitter nutny (grid degenerace), SIMPLE_FLAT pada na <25 bodech.
- Zaver (a): hybridni smycka uzavrena - predict_params doporucuje, Geoflow stavi, Blender validuje. Dalsi rezerva: vzorkovani 0.5 m pro male nastavby.

## [2026-11-22] ml | KOREKCE: 5 z 8 finalnich modelu je fakticky LOD1
- Novy scripts/audit_roofplanes.py (shlukovani normal, 10 stupnu): B02/B03/G2/G3/Z3 maji 1 stresni rovinu (plosky vrsek) prestoze profil rika sedlova/valbova. Skutecne LOD2 je jen G1 (2 roviny); B01/B04 spravne ploche.
- Brno Geoflow modely: vsech 7 vystupu 1 rovina (vcetne hip 27822445704511488b).
- Pricina: DetectLines nenajde hrebenni primky (ridke DMP1G / jitterovana mrizka) -> aranzma bez vnitrnich linii -> plosky vrsek. Validace (manifold, planarita, Val3dity) uroven LOD nekontroluje.
- Dopad na tvrzeni: 'finale = 8x LoD2.2' je prestrelene; plati pro G1 (+ ploche B01/B04). Zbytek = LOD1 geometrie v LOD2 obalu.
- Dalsi: audit_roofplanes.py jako brana validace (odmitnout plosky vrsek pri sikmem profilu); resit detekci linii (hustsi data, prahy).

## [2026-11-22] ml | Overena hypoteza vrstveni LOD1/LOD2: vyvracena
- B02 OBJ: jeden objekt, zadne grupy; LOD12 = cisty 2-vyskovy blok (297.18/302.89), LOD22 = ploska + 17cm 'sum' (302.75-302.92), zadny hreben. Funkcne LOD1, zadne vrstveni.
- Zaver auditu tim sili: aranzma bez hrebenove linie = 1 bunka + sum vyskoveho pole.

## [2026-11-22] ml+PL | Varssky pilot komplet: Geoflow LOD2 + decimace + three.js viewer
- LAZ 12 pts/m2 (5.6M bodu) + GUGiK LoD2 (139k budov, CC BY 4.0); parovani pres WFS skorowidz (scripts/pair_warszawa.py).
- Testovaci budova 1030: 9018 bodu -> Geoflow COMPLEX_HIP -> 340v/676f, 4 stresni roviny, RMSE 3.23 m, nm=0. Prvni skutecne LOD2 z pipeline.
- Decimace (scripts/blender_simplify.py, headless): 676 -> 140 tri (-79 %), manifold 0, planar dissolve 0.5deg + kolaps.
- viewer_pl.html: GT_LoD2 (48 tri) / GEOFLOW (676) / SIMPLE (140) k prepinani, EPSG:2180.

## [2026-11-22] ml | Decimace s 5cm branou: planar 140 tri je konecna
- Hausdorff gate (symetricky, numpy): uz ratio 0.8 hybe o 60 cm -> zadny kolaps neprojde 5 cm. Planar dissolve = konecna pri 5 cm.
- Zjisteni: smart/ultralehke verze ztratily zdi (smart: jen strecha 119-129 m, Hmax 17 m). Slepa decimace (light24, 24 tri, plny rozsah 110-129) lepsi nez chranena.
- Pouziti: ultra-lehke jen kde staci silueta; pro tvar drzet planar 140 tri.

## [2026-11-22] PL | Ortofoto Varsavy + pozor na poradi os EPSG:2180
- GUGiK ORTO WMS (StandardResolution, layer Raster) chodi pres curl.exe; WMS 1.3.0 vyzaduje BBOX v poradi os (Y,X) vuci LAZ (prvni dotaz vratil les).
- render/warszawa_orto.jpg: budova potvrzena vizualne.

## [2026-11-22] PL | Overen preklop ortofoto-GT-LiDAR (mapovani C)
- GUGiK ORTO WMS vraci snimek severem DOLU (radek 0 = jih); spravne mapovani: u=vychod, v=sever odspodu (varianta C ze 4 testu).
- GT footprint sedi na budove v ortofotu (potvrzeno vizualne). Pripraveno pro korekci vikýru.
