# PolyFit — .vg formát, váhy, Python API

> Source: PolyFit/data/ReadMe-data.md, code/python/Examples/Example_1_reconstruction_oneshot.py, code/model/point_set_io.cpp (lokální klon)
> Collected: 2026-11-20
> Published: Unknown

- PolyFit: polygonální rekonstrukce z mračna (Nan + Wonka, ICCV 2017). Vstupem jsou předem extrahované rovinné segmenty ve formátu vg/bvg.
- ASCII .vg: `num_points: N` + souřadnice; `num_colors: N`; `num_normals: N`; `num_groups: M`; pro každou grupu `group_type: 0` (rovina), `num_group_parameters: 4`, `group_parameters: a b c d` (ax+by+cz+d=0), `group_label`, `group_color`, `group_num_point(s): N` + indexy bodů, `num_children: 0`.
- Čtení: `polyfit.read_point_set` umí pouze přípony vg/bvg (jinak "unknown file format").
- Rekonstrukce: `polyfit.reconstruct(point_cloud, polyfit.SCIP, data_fitting, model_coverage, model_complexity)`; GUROBI vyžaduje licenci. Uložení: `polyfit.save_mesh(filename, mesh)`.
- Referenční váhy z paperu: fitting 0.46, coverage 0.27, complexity 0.27 (široký rozsah vah dává stejné výsledky); pro data s hustým pozadím (sofa) 0.3/0.4/0.3. Example_1 používá 0.43/0.27/0.3.
- Ověření v tomto prostředí: toy_data.bvg (14 grup) → 490 kandidátních faces → 42 faces po optimalizaci (SCIP, váhy 0.43/0.27/0.3).
- Negativní výsledky na datech KRAV59: B03_row.vg (5 grup) → 7 kandidátů → 0 faces; B05_vez.vg (6 grup) → 22 kandidátů → 0 faces i při vahách (0.5,0.2,0.3), (0.6,0.25,0.15), (0.7,0.2,0.1), (0.8,0.15,0.05). Příčina: řídká data (~2 pts/m2), málo protínajících se rovin s bodovou podporou.
