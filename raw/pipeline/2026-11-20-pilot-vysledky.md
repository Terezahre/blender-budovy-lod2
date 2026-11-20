# Pilotní výsledky — 5 budov KRAV59 (naměřeno 2026-11-20)

> Source: buildings/*/meta.json, output/geoflow/*/report.json, output/verdicts.json (vlastní měření scripts/)
> Collected: 2026-11-20
> Published: Unknown

- Klastry (DBSCAN eps=2.5, min_samples=30, dlaždice x [-738000,-737500] y [-1039350,-1038850]): B01_flat cl=1, B02_gable cl=46, B03_row cl=171, B04_panelak cl=59, B05_vez cl=73.
- B01_flat: n=211, hustota 1.497/m2, zstd 0.771, výška nad terénem 3.41 m, footprint 140.9 m2, profil SIMPLE_FLAT, 1 rovina (horizontal), RMSE 0.056 m, verts/faces 18/20, verdikt PASS.
- B02_gable: n=229, hustota 1.748/m2, zstd 2.21, výška 9.11 m, footprint 131.0 m2, profil STANDARD_GABLE, 2 roviny (horizontal, horizontal), RMSE 0.219 m, verts/faces 16/18, verdikt PASS.
- B03_row: n=210, hustota 1.692/m2, zstd 2.525, výška 7.39 m, footprint 124.1 m2, profil COMPLEX_HIP, 1 rovina (horizontal), RMSE 0.592 m, verts/faces 16/18, verdikt REVIEW (RMSE nad prahem 0.5 m, geometrie čistá).
- B04_panelak: n=750, hustota 1.432/m2, zstd 9.227, výška 26.3 m, footprint 523.6 m2, profil SIMPLE_FLAT, 1 rovina (horizontal), RMSE 0.043 m, verts/faces 22/24, verdikt PASS.
- B05_vez: n=489, hustota 1.648/m2, zstd 11.111, výška 35.11 m, footprint 296.7 m2, profil COMPLEX_HIP, 2 roviny (horizontal, horizontal), RMSE 6.383 m, verts/faces 84/102, verdikt FAIL-skipped (slitý klastr, přesunuto do output/rejected/).
- Profily parametrů (z agents.md): SIMPLE_FLAT (eps 0.25, min_pts 20, k 15/8, line 0.5, data 5.0), STANDARD_GABLE (0.20, 15, 15/8, 0.4, 7.0), COMPLEX_HIP (0.15, 10, 10/5, 0.3, 9.0, step 2.5, max_arr 800). Žádná budova neměla hustotu pod 1.0 → SPARSE korekce se neuplatnila.
- Finální dodávka: output/final/B01_flat_LOD2_SJTSK.obj (1911 B), B02_gable (1741 B), B03_row (1687 B), B04_panelak (2224 B); vše S-JTSK EPSG:5514, CRS v hlavičce + meta.
- Geoflow CLI nebylo nainstalováno (Geoflow-2024.03.08-win64.exe je instalátor vyžadující admin práva, chyba WinError 740). Rekonstrukce běží kompatibilním postupem (RANSAC roviny → heightfield/stupně → validátor); per-building config.toml pro lod22-reconstruct jsou připraveny v buildings/*/config.toml.
