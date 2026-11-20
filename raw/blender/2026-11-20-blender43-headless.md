# Blender 4.3 headless validace — zjištění

> Source: Blender 4.3.2 (build 2024-12-17), scripts/blender_validate.py, měření 2026-11-20
> Collected: 2026-11-20
> Published: Unknown

- Blender interně float32: S-JTSK souřadnice (~-738000) se musí před importem centrovat (offset = min. roh), po exportu se offset v textu OBJ vrátí. Geometrie se nemění.
- Cleanup: merge-by-distance 1 mm, delete loose, recalc normals; metriky non-manifold hran před/po, loose verts, degenerované faces.
- Stínování: flat shading pro všechny polygony (hladké stínování četlo LOD2 roviny jako bubliny).
- Render náhledů: CYCLES na CPU, 32 samplů, 1280x720, transparent film; kamera bounding-sphere fit (směr (1,-1,0.7), vzdálenost 2.2x maxdim, lens 28). Relativní render-cesta se v background módu ztratila → používat absolutní cestu.
- Blender 4.3 `bpy.ops.wm.obj_export` nemá argument `export_triangulated`.
- N-gony: vlastní write_obj musel zapisovat celé polygony (ořez `fa[:3]` vyráběl díry — audit ukázal 16 boundary hran u B01).
- Výsledky validace finálních OBJ (verts/faces/nonmanifold): B01_flat 18/20/0, B02_gable 16/18/0, B03_row 16/18/0, B04_panelak 22/24/0, B05_vez 84/102/0; degenerované faces 0 všude.
- Normály (UP/DOWN/WALL): B01 1/1/18, B02 1/1/16, B03 1/1/16, B04 1/1/22, B05 9/9/84.
