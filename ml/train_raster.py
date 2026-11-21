# -*- coding: utf-8 -*-
"""Trenink raster-GBM na CPU: klasifikace typu strechy + regrese vysky hrebene/okapu.
Vstup: ml/patches/*.npz (ndsm 64x64, valid_mask, stats[6], label_roof, z_eave, z_ridge).
Priznaky: stats + ndsm snizeny na 8x8 (prumerovani) + podil validnich pixelu.
Varianty: S-RUIAN (vse) vs BEZ-RUIAN (bez stats[4]=area z footprintu).
Evaluace: leave-one-out (N~12), confusion matrix, MAE, top-5 importance.
Vystup: ml/gb_roof.pkl, ml/gb_ridge.pkl, ml/gb_eave.pkl (naucene na vsech datech).
Beh: python ml/train_raster.py
"""
import glob
import json
import os
import pickle

import numpy as np
from sklearn.ensemble import GradientBoostingClassifier, GradientBoostingRegressor
from sklearn.metrics import confusion_matrix

PATCH_DIR = os.path.join(os.path.dirname(__file__), "patches")
OUT_DIR = os.path.dirname(os.path.abspath(__file__))
NAMES = ["flat(0)", "gable(1)", "hip/complex(2)"]
STAT_NAMES = ["n_points", "density", "zstd", "height", "area_RUIAN", "roofplanes"]


def downsample8(a):
    # Prumer 64x64 -> 8x8 (bloky 8x8); robustni k malemu N, jen 64 feat.
    h, w = a.shape
    bh, bw = h // 8, w // 8
    return a[:8 * bh, :8 * bw].reshape(8, bh, 8, bw).mean(axis=(1, 3))


def load_all(patch_dir=PATCH_DIR, labels_path=None):
    """labels_path: ml/gt_krav59.json (Geoflow-GT) nebo ml/gt_brno.json.
    Bez nej se pouzije heuristicky label_roof z patchu (deterministicka funkce
    zstd -> label leakage, jen pro overeni pipeline, NE pro zavery)."""
    files = sorted(glob.glob(os.path.join(patch_dir, "*.npz")))
    gt = {}
    if labels_path and os.path.exists(labels_path):
        gt = json.load(open(labels_path, encoding="utf-8"))
        print(f"GT labely: {labels_path} ({len(gt)} zaznamu)")
    else:
        print("POZOR: heuristicke labely (leakage ze zstd) - jen overeni pipeline")
    rows = []
    for f in files:
        d = np.load(f, allow_pickle=True)
        bid = os.path.splitext(os.path.basename(f))[0]
        ndsm = np.asarray(d["ndsm"], dtype=np.float32)
        valid = np.asarray(d["valid_mask"], dtype=np.float32)
        stats = np.asarray(d["stats"], dtype=np.float32).ravel()
        assert ndsm.shape == (64, 64) and stats.shape == (6,), f"{f}: spatny tvar"
        small = downsample8(ndsm).ravel()  # 64 feat
        frac = float(valid.mean())  # podil validnich pixelu
        x_full = np.concatenate([stats, small, [frac]])  # 71 feat
        if bid in gt and gt[bid].get("roof_type_gt") is not None:
            y = int(gt[bid]["roof_type_gt"])
            z_r = float(gt[bid].get("ridge_rel") or d["z_ridge"])
            src = "GT"
        else:
            y = int(d["label_roof"])
            z_r = float(d["z_ridge"])
            src = "heur"
        rows.append(dict(
            id=bid,
            x_full=x_full, y=y,
            z_ridge=z_r, z_eave=float(d["z_eave"]),
            src=src,
        ))
    return rows


def feat_names():
    return STAT_NAMES + [f"ndsm_{i//8}x{i%8}" for i in range(64)] + ["valid_frac"]


def make_clf():
    # Melke stromy + malo vzorku: nizky depth, min_samples_split=2 aby vubec delil.
    return GradientBoostingClassifier(n_estimators=100, max_depth=2,
                                      min_samples_split=2, min_samples_leaf=1,
                                      random_state=42)


def make_reg():
    return GradientBoostingRegressor(n_estimators=100, max_depth=2,
                                     min_samples_split=2, min_samples_leaf=1,
                                     random_state=42)


def loo_classify(X, y):
    # Leave-one-out: pro kazdy vzorek trenuj na zbytku, predikuj ten jeden.
    # Pri malem N muze fold obsahovat jen 1 tridu -> pak predikuj vetsinovou.
    from collections import Counter
    n = len(y)
    pred = np.zeros(n, dtype=int)
    for i in range(n):
        m = np.ones(n, bool)
        m[i] = False
        if len(set(y[m].tolist())) < 2:
            pred[i] = Counter(y[m].tolist()).most_common(1)[0][0]
            continue
        clf = make_clf()
        clf.fit(X[m], y[m])
        pred[i] = clf.predict(X[i : i + 1])[0]
    return pred


def main():
    import argparse
    ap = argparse.ArgumentParser()
    ap.add_argument("--labels", default=os.path.join(OUT_DIR, "gt_krav59.json"),
                    help="GT labely (default ml/gt_krav59.json); 'none' = heuristika")
    ap.add_argument("--patches", default=PATCH_DIR)
    a = ap.parse_args()
    lab = None if a.labels == "none" else a.labels
    rows = load_all(a.patches, lab)
    # jen vzorky s GT labelem se hodnoti (heuristicke se netestuji na GT)
    rows = [r for r in rows if r["src"] == "GT"] if lab else rows
    n = len(rows)
    print(f"Patchu: {n}")
    ids = [r["id"] for r in rows]
    X_full = np.stack([r["x_full"] for r in rows])
    y = np.array([r["y"] for r in rows])
    z_ridge = np.array([r["z_ridge"] for r in rows])
    z_eave = np.array([r["z_eave"] for r in rows])
    print("Tridy:", {int(k): int((y == k).sum()) for k in sorted(set(y.tolist()))})

    NO_RUIAN = [0, 1, 2, 3, 5]  # indexy stats bez area(stats[4])
    X_noru = np.concatenate([X_full[:, NO_RUIAN], X_full[:, 6:]], axis=1)

    # (a) Klasifikace LOO pro obe varianty.
    p_full = loo_classify(X_full, y)
    p_noru = loo_classify(X_noru, y)
    acc_full = float((p_full == y).mean())
    acc_noru = float((p_noru == y).mean())
    print(f"LOO presnost S-RUIAN:  {acc_full:.3f} ({int((p_full==y).sum())}/{n})")
    print(f"LOO presnost BEZ-RUIAN: {acc_noru:.3f} ({int((p_noru==y).sum())}/{n})")
    print("Confusion matrix S-RUIAN (radky=true, sloupce=pred):")
    print(confusion_matrix(y, p_full, labels=[0, 1, 2]))
    print("Confusion matrix BEZ-RUIAN:")
    print(confusion_matrix(y, p_noru, labels=[0, 1, 2]))
    for i, (t, a, b) in enumerate(zip(y, p_full, p_noru)):
        flag = "" if (a == t and b == t) else "  <-- chyba"
        print(f"  {ids[i]}: true={t} s_ruian={a} bez_ruian={b}{flag}")

    # (b) Regrese vysky LOO (plne priznaky).
    pr, pe = np.zeros(n), np.zeros(n)
    for i in range(n):
        m = np.ones(n, bool)
        m[i] = False
        rr, re_ = make_reg(), make_reg()
        rr.fit(X_full[m], z_ridge[m])
        re_.fit(X_full[m], z_eave[m])
        pr[i] = rr.predict(X_full[i : i + 1])[0]
        pe[i] = re_.predict(X_full[i : i + 1])[0]
    mae_r, mae_e = float(np.abs(pr - z_ridge).mean()), float(np.abs(pe - z_eave).mean())
    print(f"LOO MAE z_ridge: {mae_r:.3f} m | z_eave: {mae_e:.3f} m")

    # Importance: model na vsech datech (plne priznaky).
    clf = make_clf().fit(X_full, y)
    fn = feat_names()
    top = np.argsort(clf.feature_importances_)[::-1][:5]
    print("Top-5 importance (klasifikace, S-RUIAN):")
    for j in top:
        print(f"  {fn[j]}: {clf.feature_importances_[j]:.3f}")

    # Uloz modely naucene na vsech datech.
    with open(os.path.join(OUT_DIR, "gb_roof.pkl"), "wb") as f:
        pickle.dump({"model": clf, "feat_names": fn, "variant": "S-RUIAN"}, f)
    with open(os.path.join(OUT_DIR, "gb_ridge.pkl"), "wb") as f:
        pickle.dump({"model": make_reg().fit(X_full, z_ridge), "feat_names": fn}, f)
    with open(os.path.join(OUT_DIR, "gb_eave.pkl"), "wb") as f:
        pickle.dump({"model": make_reg().fit(X_full, z_eave), "feat_names": fn}, f)
    print("Ulozeno: ml/gb_roof.pkl, ml/gb_ridge.pkl, ml/gb_eave.pkl")

    # Zaver: vitez jednim radkem (vcetne remizy).
    if abs(acc_full - acc_noru) < 1e-9:
        print(f"REMIZA: S-RUIAN i BEZ-RUIAN {acc_full*100:.1f} % - area z RUIAN zatim nepridava.")
    elif acc_full > acc_noru:
        print(f"VITEZ: S-RUIAN (+{(acc_full-acc_noru)*100:.1f} p.b. nad BEZ-RUIAN).")
    else:
        print(f"VITEZ: BEZ-RUIAN (+{(acc_noru-acc_full)*100:.1f} p.b. nad S-RUIAN).")


if __name__ == "__main__":
    main()
