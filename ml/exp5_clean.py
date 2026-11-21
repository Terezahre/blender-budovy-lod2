# -*- coding: utf-8 -*-
"""Experiment 5: vliv cistoty GT (purity segmentu, rok porizeni) na presnost.
Hypoteza: strop 0.47 neni strop modelu, ale strop SUMU v labely
(smisene STRECHA_KOD v ramci budovy, prestavby mezi LOD2 2020-23 a DSM 2025,
spatny join v radovkach).
Postup: filtruj gt_brno.json na purity==1.0 (prip. >=0.8) a rok<=2023,
pak HGB balanced 5-fold na S-RUIAN(tvar+DSM) vs BEZ-RUIAN.
"""
import sys
import os
import numpy as np

sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__))))
from train_raster import load_all  # noqa: E402
from exp4_shape_mlp import shape_row  # noqa: E402

from sklearn.ensemble import HistGradientBoostingClassifier
from sklearn.metrics import confusion_matrix, accuracy_score
from sklearn.model_selection import StratifiedKFold


def evaluate(Xv, y, vname):
    skf = StratifiedKFold(n_splits=5, shuffle=True, random_state=42)
    pred = np.zeros_like(y)
    for tr, te in skf.split(Xv, y):
        m = HistGradientBoostingClassifier(
            max_iter=300, max_depth=6, class_weight="balanced", random_state=42)
        m.fit(Xv[tr], y[tr])
        pred[te] = m.predict(Xv[te])
    cm = confusion_matrix(y, pred, labels=[0, 1, 2])
    rec = [cm[i, i] / max(cm[i].sum(), 1) for i in range(3)]
    print(f"{vname}: N={len(y)} acc={accuracy_score(y, pred):.3f} "
          f"recall f/g/h={rec[0]:.2f}/{rec[1]:.2f}/{rec[2]:.2f}", flush=True)


def main():
    import json
    import geopandas as gpd
    gt = json.load(open("ml/gt_brno.json", encoding="utf-8"))
    rows = [r for r in load_all("ml/patches_brno", "ml/gt_brno.json") if r["src"] == "GT"]
    fp = gpd.read_file(os.path.join("ml", "data_brno", "footprints.geojson"))
    fp = fp.set_index(fp["fid_zbg"].astype(str))
    X0 = np.stack([r["x_full"] for r in rows])
    S = np.nan_to_num(np.array([shape_row(fp.loc[r["id"]].geometry) for r in rows]),
                      nan=0.0, posinf=0.0, neginf=0.0)
    pur = np.array([gt[r["id"]].get("purity", 0) for r in rows])
    rok = np.array([gt[r["id"]].get("rok", 9999) for r in rows])
    print(f"purity: median={np.median(pur):.2f} podil 1.0={(pur == 1.0).mean():.2f} "
          f"rok>2023={(rok > 2023).sum()}", flush=True)
    NO_RUIAN = [0, 1, 2, 3, 5]
    for pname, m in [("vse", pur >= 0), ("purity==1.0", pur == 1.0),
                     ("purity==1.0 & rok<=2023", (pur == 1.0) & (rok <= 2023))]:
        y = np.array([r["y"] for r, ok in zip(rows, m) if ok])
        if len(y) < 30 or len(set(y.tolist())) < 2:
            print(f"{pname}: malo dat ({len(y)}), preskakuji", flush=True)
            continue
        Xf = np.concatenate([X0[m], S[m]], axis=1)
        Xb = np.concatenate([X0[m][:, NO_RUIAN], X0[m][:, 6:]], axis=1)
        print(f"--- filtr: {pname} ---", flush=True)
        evaluate(Xf, y, "S-RUIAN(tvar+DSM)")
        evaluate(Xb, y, "BEZ-RUIAN(jen DSM)")


if __name__ == "__main__":
    main()
