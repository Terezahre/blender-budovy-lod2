# -*- coding: utf-8 -*-
"""Debug PolyFit: nejprve toy_data, pak nase .vg po krocich."""
import sys
import polyfit

polyfit.initialize()

for f in ["PolyFit/data/toy_data.bvg", "output/polyfit/B03_row.vg"]:
    print("=" * 60)
    print("SOUBOR:", f)
    try:
        pc = polyfit.read_point_set(f)
    except Exception as e:
        print("read exception:", e)
        continue
    if not pc:
        print("read vratil None")
        continue
    groups = pc.groups()
    print("pocet grup:", len(groups) if groups else 0)
    hyp = polyfit.HypothesisGenerator(pc)
    hyp.refine_planes()
    mesh = hyp.generate()
    if not mesh:
        print("generate: zadne kandidatky")
        continue
    print("kandidatnich faces:", mesh.size_of_facets())
    hyp.compute_confidences(mesh, False)
    sel = polyfit.FaceSelection(pc, mesh)
    sel.optimize(hyp, polyfit.SCIP, 0.43, 0.27, 0.3)
    print("po optimalizaci faces:", mesh.size_of_facets())
