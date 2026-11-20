# Celomapový scan sedlových střech KRAV59 (naměřeno 2026-11-21)

> Source: scripts/scan_map.py, buildings/gable_candidates.json (vlastní měření)
> Collected: 2026-11-21
> Published: Unknown

- Metoda: KRAV59 rozdělen na dlaždice 500 m (5×4), v každé DBSCAN (eps=2.5, min_samples=30), klastry 120–900 bodů, plocha 60–2500 m2, zstd 1.5–8.0, výška 3–15 m, pak RANSAC screen šikmých rovin (eps 0.20, min 12 bodů).
- Výsledek: 286 kandidátů s šikmými rovinami. Většina jsou falešně pozitivní: vysoké bloky (rel 8–15 m), kde RANSAC proloží šikmou rovinu fasádou. B06_sedlova (cl=164, 17×9 m, rel 12.7 m) je stejný případ — vysoký blok s plochou střechou, ne sedlovka.
- Pravé sedlovky = 2+ šikmé roviny, rel ≤ 9 m, plocha ≤ 600 m2, vyrovnané strany: 24 kandidátů.
- Vybrány top 3: G1_sedlova (tile (0,2) cl=1, 280 bodů, 14×15 m, rel 9.0 m, S114+S101), G2_sedlova (tile (3,3) cl=470, 300 bodů, 21×21 m, rel 6.59 m, S109+S100), G3_domek (tile (1,2) cl=281, 164 bodů, 9×10 m, rel 5.3 m, S61+S52).
- Geoflow LoD2.2 (COMPLEX_HIP, eps 0.15, data term 9.0): G1 RMSE 1.669 m pokrytí 0.95 (26v/48f), G2 RMSE 1.520 m pokrytí 0.97 (20v/36f), G3 RMSE 0.774 m pokrytí 0.97 (20v/36f); všechny manifold 0, validované S-JTSK OBJ + rendery. Sedlové střechy s hřebenem jsou ve všech třech modelech.
