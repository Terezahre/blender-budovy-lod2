# Geoflow-bundle — fakta z README a flowchartů

> Source: geoflow-bundle/README.md a flowcharts/gfc-lod13/*.json (lokální klon)
> Collected: 2026-11-20
> Published: Unknown

- Nástroj pro automatickou rekonstrukci 3D budov z mračna, bez manuálních zásahů.
- Výstupy: LoD1.2, LoD1.3, LoD2.2 (refined LoD specifikace 3D geoinformation group TU Delft).
- Vstupní mračno: letecký LiDAR (preferován), klasifikované (minimálně ground + building), dostatečná hustota (dobré výsledky s 8–10 pts/m2 v 3D BAG), včetně ground bodů kolem budovy pro určení podlahy, formát LAS/LAZ.
- Vstupní 2D polygon: jednoduchý polygon jedné budovy, nejlépe roofprint, formát GeoPackage / Shapefile / PostGIS.
- Spuštění: `geof flowchart.json`, `--help` ukazuje volby; convenience skript `lod22-reconstruct --input_footprint=my_footprint.gpkg --input_pointcloud=my_pointcloud.las`.
- Flowchart rekonstrukce: `flowcharts/gfc-brecon/single/reconstruction.json`; výstup standardně CityJSON + OBJ + GPKG do `output`.
- Windows: doporučena CLI verze (instalátor z Releases); flowcharty gfc-lod13 obsahují uzly DetectPlanes, DetectLines, AlphaShape, BuildArrFromLines, OptimiseArrangmentGrid, ArrExtruder (LoD2 flag), Validator (Val3dity), PC2MeshQuality, OBJVecWriter (precision 3).
- Výchozí globály gfc-lod13 (reconstruct_one.json / runner.json): plane_detect__epsilon 0.2, plane_detect__k 15, plane_detect__min_points 15, plane_detect__normal_angle 0.75, normal_estimate__k 5 (reconstruct_one) resp. 8 (runner), line_detect__epsilon 0.4, line_detect__min_points_lower 5, line_detect__min_points_upper 10, lod13__step_height 3.0, optimisation_data_term 7.0, max_arr_complexity 400, SegmentRasterise cellsize 0.05, megapixel_limit 600.
- PointCloudSplitter: class A 2 (ground), class B 6 (building).
- LASInPolygons: buffer 1.0, cellsize 50.0, ground_percentile 0.05.
