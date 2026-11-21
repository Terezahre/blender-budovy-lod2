# -*- coding: utf-8 -*-
"""CPU baseline: typ strechy ze statistik mracna (RandomForest, sklearn).

Bezi na studentskem PC v minutach, bez GPU/torch.
Vstup: ml/patches/*.npz (z ml/make_patches.py) nebo primo buildings/*/meta.json.
Vystup: presnost leave-one-out + feature importance + ulozene vahy baseline.

Cil: prekonat rucni prahy z agents.md (zstd<1.2 / <2.5) naucenym prahem.
Pozdeji se nahradi malym U-Netem (stale CPU), baseline zustane jako referencni cara.
"""
import glob
import json
import os

import numpy as np

LABELS = {0: "FLAT", 1: "GABLE", 2: "HIP/COMPLEX"}


def load_Xy(patch_dir="ml/patches"):
    files = sorted(glob.glob(os.path.join(patch_dir, "*.npz")))
    X, y, ids = [], [], []
    for f in files:
        d = np.load(f)
        X.append(d["stats"])
        y.append(int(d["label_roof"]))
        ids.append(os.path.splitext(os.path.basename(f))[0])
    if not X:
        # fallback: primo z meta.json (jde i bez patchu)
        for m in sorted(glob.glob(os.path.join("buildings", "*", "meta.json"))):
            meta = json.load(open(m, encoding="utf-8"))
            zstd = float(meta.get("zstd", meta.get("z_std", 0)))
            lab = 0 if zstd < 1.2 else (1 if zstd < 2.5 else 2)
            X.append([meta.get("n_points", 0), meta.get("density_pts_m2", meta.get("density", 0)),
                      zstd, meta.get("height_above_ground", meta.get("height_range", 0)),
                      meta.get("footprint_area_m2", 0), meta.get("roofplane_guess", 0)])
            y.append(lab)
            ids.append(meta.get("id", m))
    return np.array(X, float), np.array(y, int), ids


def main():
    from sklearn.ensemble import RandomForestClassifier
    from sklearn.model_selection import LeaveOneOut, cross_val_predict
    from sklearn.metrics import accuracy_score, confusion_matrix
    X, y, ids = load_Xy()
    print(f"vzorku: {len(y)}, trid: {sorted(set(y.tolist()))}")
    if len(y) < 3:
        print("Malo vzorku: nejdriv python ml/make_patches.py --src buildings")
        return
    clf = RandomForestClassifier(n_estimators=200, random_state=42, n_jobs=-1)
    pred = cross_val_predict(clf, X, y, cv=LeaveOneOut())
    acc = accuracy_score(y, pred)
    print(f"leave-one-out presnost: {acc:.2f}")
    print("confusion matrix (radky=GT, sloupce=pred):")
    print(confusion_matrix(y, pred))
    for i, p, t in zip(ids, pred, y):
        flag = "OK " if p == t else "MISS"
        print(f"  {flag} {i}: GT={LABELS[t]} pred={LABELS[p]}")
    clf.fit(X, y)
    os.makedirs("ml", exist_ok=True)
    try:
        import pickle
        pickle.dump(clf, open("ml/baseline_rf.pkl", "wb"))
        print("-> ml/baseline_rf.pkl")
    except Exception as e:
        print("ulozeni vah selhalo:", e)
    imp = sorted(zip(["n_points", "density", "zstd", "height", "area", "roofplane_guess"],
                     clf.feature_importances_), key=lambda t: -t[1])
    print("dulezitost priznaku:", [(k, round(float(v), 3)) for k, v in imp])


if __name__ == "__main__":
    main()
