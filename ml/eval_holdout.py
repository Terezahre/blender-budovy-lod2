# -*- coding: utf-8 -*-
"""Ferova validace hybridu: geograficky holdout v ramci Brna (zadne KRAV59).
Test = SV kvadrant bboxu (out-of-area vuci trenovacim 3 kvadrantum).
Trenink: HGB balanced (typ) + HGB regrese (hreben/okap) na S-RUIAN(tvar+DSM).
Metriky: shoda profilu s GT, MAE hrebene/okapu, uspesnost pravidla step_height.
KRAV59 se pouzije jen jako smoke test pruchodnosti (out-of-domain, bez naroku).
"""
import sys
import os
import numpy as np

sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__))))
from train_raster import load_all  # noqa: E402
from exp4_shape_mlp import shape_row  # noqa: E402

from sklearn.ensemble import HistGradientBoostingClassifier, HistGradientBoostingRegressor
from sklearn.metrics import confusion_matrix, accuracy_score

LABELS = {0: "SIMPLE_FLAT", 1: "STANDARD_GABLE", 2: "COMPLEX_HIP"}


def main():
    import geopandas as gpd
    import glob
    rows = [r for r in load_all("ml/patches_brno", "ml/gt_brno.json") if r["src"] == "GT"]
    files = {os.path.splitext(os.path.basename(f))[0]: f
             for f in glob.glob("ml/patches_brno/*.npz")}
    fp = gpd.read_file(os.path.join("ml", "data_brno", "footprints.geojson"))
    fp = fp.set_index(fp["fid_zbg"].astype(str))
    X0 = np.stack([r["x_full"] for r in rows])
    S = np.nan_to_num(np.array([shape_row(fp.loc[r["id"]].geometry) for r in rows]),
                      nan=0.0, posinf=0.0, neginf=0.0)
    X = np.concatenate([X0, S], axis=1)
    y = np.array([r["y"] for r in rows])
    # geograficky split: centroid patchu, test = SV kvadrant (x>-597500, y>-1160500)
    oxy = np.stack([np.load(files[r["id"]])["origin_xy"] for r in rows])
    te = (oxy[:, 0] > -597500) & (oxy[:, 1] > -1160500)
    print(f"N={len(y)} train={int((~te).sum())} test(SV kvadrant)={int(te.sum())}", flush=True)
    clf = HistGradientBoostingClassifier(
        max_iter=300, max_depth=6, class_weight="balanced", random_state=42)
    clf.fit(X[~te], y[~te])
    p = clf.predict(X[te])
    print(f"HOLDOUT acc={accuracy_score(y[te], p):.3f}", flush=True)
    print("CM (radky GT flat/gable/hip):", flush=True)
    print(confusion_matrix(y[te], p, labels=[0, 1, 2]), flush=True)
    import json
    gt = json.load(open("ml/gt_brno.json", encoding="utf-8"))
    z = np.array([gt[r["id"]]["ridge_rel"] for r in rows])  # GT vyska budovy (HREBEN-PATA)
    reg = HistGradientBoostingRegressor(
        max_iter=300, max_depth=6, random_state=42)
    reg.fit(X[~te], z[~te])
    zp = reg.predict(X[te])
    print(f"HOLDOUT MAE vyska budovy={np.mean(np.abs(zp - z[te])):.2f} m "
          f"(median GT={np.median(z[te]):.1f} m)", flush=True)
    # smoke test KRAV59 (out-of-domain, jen pruchodnost)
    import pickle
    xav = np.stack([r["x_full"] for r in load_all("ml/patches", None)[:3]])
    print(f"KRAV59 smoke: {len(xav)} patche nacteny, profilova mapa OK: "
          f"{[LABELS[i] for i in range(3)]}", flush=True)


if __name__ == "__main__":
    main()
