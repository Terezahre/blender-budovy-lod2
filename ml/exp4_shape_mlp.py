# -*- coding: utf-8 -*-
"""Experiment 4: tvarove priznaky footprintu (podstata RUIAN prioru) + MLP (CPU).
Hypoteza: tvar pudorysu (protahlost, pravouhlost) koreluje s typem strechy
(dlouhy uzky dum = sedlova). To je presne to, co varianta BEZ-RUIAN nema.
Priznaky: area, obvod, bbox w/h, aspect, rectangularity (A/A_bbox),
kompaktnost (4*pi*A/P^2), konvexnost (A/A_convex).
Modely: HGB balanced + MLP (sklearn, CPU) na S-RUIAN (tvar+DSM) vs BEZ-RUIAN (jen DSM).
"""
import sys
import os
import numpy as np

sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__))))
from train_raster import load_all  # noqa: E402

from sklearn.ensemble import HistGradientBoostingClassifier
from sklearn.neural_network import MLPClassifier
from sklearn.preprocessing import StandardScaler
from sklearn.pipeline import make_pipeline
from sklearn.metrics import confusion_matrix, accuracy_score
from sklearn.model_selection import StratifiedKFold


def shape_row(geom):
    import math
    a = float(geom.area)
    p = float(geom.length)
    x0, y0, x1, y1 = geom.bounds
    w, h = max(x1 - x0, 1e-6), max(y1 - y0, 1e-6)
    bbox_a = w * h
    try:
        conv_a = float(geom.convex_hull.area)
    except Exception:
        conv_a = a
    return [a, p, w, h, max(w, h) / min(w, h), a / bbox_a,
            4 * math.pi * a / max(p * p, 1e-9), a / max(conv_a, 1e-9)]


def main():
    import geopandas as gpd
    rows = [r for r in load_all("ml/patches_brno", "ml/gt_brno.json") if r["src"] == "GT"]
    fp = gpd.read_file(os.path.join("ml", "data_brno", "footprints.geojson"))
    fp = fp.set_index(fp["fid_zbg"].astype(str))
    X0 = np.stack([r["x_full"] for r in rows])
    y = np.array([r["y"] for r in rows])
    S = np.array([shape_row(fp.loc[r["id"]].geometry) for r in rows])
    S = np.nan_to_num(S, nan=0.0, posinf=0.0, neginf=0.0)
    print(f"N={len(y)}, shape feats: {S.shape[1]}")
    NO_RUIAN = [0, 1, 2, 3, 5]
    variants = {"S-RUIAN(tvar+DSM)": np.concatenate([X0, S], axis=1),
                "BEZ-RUIAN(jen DSM)": np.concatenate([X0[:, NO_RUIAN], X0[:, 6:]], axis=1)}
    models = {
        "HGB-bal": lambda: HistGradientBoostingClassifier(
            max_iter=300, max_depth=6, class_weight="balanced", random_state=42),
        "MLP": lambda: make_pipeline(
            StandardScaler(),
            MLPClassifier(hidden_layer_sizes=(64, 32), alpha=0.01,
                          max_iter=800, random_state=42)),
    }
    for vname, Xv in variants.items():
        for mname, mk in models.items():
            skf = StratifiedKFold(n_splits=5, shuffle=True, random_state=42)
            pred = np.zeros_like(y)
            for tr, te in skf.split(Xv, y):
                m = mk()
                m.fit(Xv[tr], y[tr])
                pred[te] = m.predict(Xv[te])
            cm = confusion_matrix(y, pred, labels=[0, 1, 2])
            rec = [cm[i, i] / max(cm[i].sum(), 1) for i in range(3)]
            print(f"{vname} + {mname}: acc={accuracy_score(y, pred):.3f} "
                  f"recall f/g/h={rec[0]:.2f}/{rec[1]:.2f}/{rec[2]:.2f}")


if __name__ == "__main__":
    main()
