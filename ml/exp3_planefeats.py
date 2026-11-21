# -*- coding: utf-8 -*-
"""Experiment 3: priznaky poctu rovin + vyvazene modely (CPU, minuty).
Vstup: ml/patches_brno/*.npz + ml/gt_brno.json.
Priznaky: puvodnich 71 (train_raster) + [rmse1, rmse2, ratio] z features_roof.py.
Hodnoceni: stratifikovany 5-fold; hlasime acc + recall hip + S-RUIAN vs BEZ-RUIAN.
"""
import sys
import os
import numpy as np

sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__))))
from train_raster import load_all  # noqa: E402
from features_roof import roof_plane_features  # noqa: E402

from sklearn.ensemble import HistGradientBoostingClassifier
from sklearn.metrics import confusion_matrix, accuracy_score
from sklearn.model_selection import StratifiedKFold

CELL = 0.5
SIZE = 64


def extra_feats(patch_path):
    d = np.load(patch_path)
    ox, oy = d["origin_xy"]
    gx = ox + (np.arange(SIZE) + 0.5) * CELL
    gy = oy + (np.arange(SIZE) + 0.5) * CELL
    GX, GY = np.meshgrid(gx, gy)
    m = d["valid_mask"].astype(bool)
    f = roof_plane_features(GX[m], GY[m], d["ndsm"][m])
    out = np.array([f["rmse1"], f["rmse2"], f["ratio"]], float)
    return np.nan_to_num(out, nan=0.0, posinf=0.0, neginf=0.0)


def main():
    import glob
    rows = [r for r in load_all("ml/patches_brno", "ml/gt_brno.json") if r["src"] == "GT"]
    files = sorted(glob.glob("ml/patches_brno/*.npz"))
    by_id = {os.path.splitext(os.path.basename(f))[0]: f for f in files}
    X0 = np.stack([r["x_full"] for r in rows])
    y = np.array([r["y"] for r in rows])
    E = np.stack([extra_feats(by_id[r["id"]]) for r in rows])
    print("extra priznaky: median rmse1=%.3f rmse2=%.3f ratio=%.3f" % tuple(np.median(E, axis=0)))
    X = np.concatenate([X0, E], axis=1)
    NO_RUIAN = [0, 1, 2, 3, 5]
    variants = {"S-RUIAN": X, "BEZ-RUIAN": np.concatenate([X[:, NO_RUIAN], X[:, 6:]], axis=1)}
    for vname, Xv in variants.items():
        skf = StratifiedKFold(n_splits=5, shuffle=True, random_state=42)
        pred = np.zeros_like(y)
        for tr, te in skf.split(Xv, y):
            m = HistGradientBoostingClassifier(
                max_iter=300, max_depth=6, class_weight="balanced", random_state=42)
            m.fit(Xv[tr], y[tr])
            pred[te] = m.predict(Xv[te])
        cm = confusion_matrix(y, pred, labels=[0, 1, 2])
        rec = [cm[i, i] / max(cm[i].sum(), 1) for i in range(3)]
        print(f"{vname}: acc={accuracy_score(y, pred):.3f} "
              f"recall flat/gable/hip={rec[0]:.2f}/{rec[1]:.2f}/{rec[2]:.2f}")
        print(f"  CM:\n{cm}")


if __name__ == "__main__":
    main()
