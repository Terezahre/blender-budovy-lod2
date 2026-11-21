# Wiki Log

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
