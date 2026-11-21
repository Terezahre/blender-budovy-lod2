# -*- coding: utf-8 -*-
"""Experiment 2: silnejsi CPU baseline na Brno GT (stratifikovany 5-fold, minuty).
Porovnava: (a) puvodni GBM, (b) GBM balanced, (c) hierarchicky flat-vs-rest -> gable-vs-hip.
Vstup: ml/patches_brno/*.npz + ml/gt_brno.json (stejne priznaky jako train_raster.py).
Cil: zvednout recall tridy hip/complex a overit, zda RUIAN area pomaha v 5-foldu.
"""
import sys
import os
import numpy as np

sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__))))
from train_raster import load_all, make_clf, feat_names  # noqa: E402

from sklearn.ensemble import HistGradientBoostingClassifier
from sklearn.metrics import confusion_matrix, accuracy_score
from sklearn.model_selection import StratifiedKFold


def skf_eval(X, y, make_model, seed=42):
    skf = StratifiedKFold(n_splits=5, shuffle=True, random_state=seed)
    pred = np.zeros_like(y)
    for tr, te in skf.split(X, y):
        m = make_model()
        m.fit(X[tr], y[tr])
        pred[te] = m.predict(X[te])
    return pred


def report(name, y, p):
    acc = accuracy_score(y, p)
    cm = confusion_matrix(y, p, labels=[0, 1, 2])
    rec = [cm[i, i] / max(cm[i].sum(), 1) for i in range(3)]
    print(f"{name}: acc={acc:.3f} recall flat/gable/hip="
          f"{rec[0]:.2f}/{rec[1]:.2f}/{rec[2]:.2f}")
    return acc


def main():
    rows = [r for r in load_all("ml/patches_brno", "ml/gt_brno.json") if r["src"] == "GT"]
    X = np.stack([r["x_full"] for r in rows])
    y = np.array([r["y"] for r in rows])
    print(f"N={len(y)}, tridy={sorted(set(y.tolist()))}")
    NO_RUIAN = [0, 1, 2, 3, 5]
    variants = {"S-RUIAN": X, "BEZ-RUIAN": np.concatenate([X[:, NO_RUIAN], X[:, 6:]], axis=1)}

    for vname, Xv in variants.items():
        print(f"--- {vname} ---")
        p_base = skf_eval(Xv, y, make_clf)
        a0 = report("GBM puvodni", y, p_base)
        p_bal = skf_eval(Xv, y, lambda: HistGradientBoostingClassifier(
            max_iter=300, max_depth=6, class_weight="balanced", random_state=42))
        a1 = report("HGB balanced", y, p_bal)
        # hierarchie: 0=flat vs {1,2}, pak 1 vs 2 jen na sikmych
        p_h = np.zeros_like(y)
        skf = StratifiedKFold(n_splits=5, shuffle=True, random_state=42)
        y_flat = (y == 0).astype(int)
        for tr, te in skf.split(Xv, y_flat):
            m1 = HistGradientBoostingClassifier(
                max_iter=300, max_depth=6, class_weight="balanced", random_state=42)
            m1.fit(Xv[tr], y_flat[tr])
            is_flat = m1.predict(Xv[te]) == 1
            p_h[te[is_flat]] = 0
            pitched_te = te[~is_flat]
            if len(pitched_te) == 0:
                continue
            # trenuj 1-vs-2 jen na sikmych z train foldu
            tr_pitched = tr[y[tr] != 0]
            if len(set(y[tr_pitched].tolist())) < 2:
                p_h[pitched_te] = 1
                continue
            m2 = HistGradientBoostingClassifier(
                max_iter=300, max_depth=6, class_weight="balanced", random_state=42)
            m2.fit(Xv[tr_pitched], (y[tr_pitched] == 2).astype(int))
            p_h[pitched_te] = np.where(m2.predict(Xv[pitched_te]) == 1, 2, 1)
        a2 = report("hierarchie flat|gable-vs-hip", y, p_h)
        print(f"  zaver {vname}: base={a0:.3f} balanced={a1:.3f} hier={a2:.3f}")


if __name__ == "__main__":
    main()
