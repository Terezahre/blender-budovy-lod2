# -*- coding: utf-8 -*-
"""Doporučení Geoflow parametrů z naučeného modelu (hybridní uzávěr smyčky).
Vstup: ml/patches_brno/<fid>.npz (nebo ml/patches/<ID>.npz pro KRAV59).
Modely: ml/gb_roof.pkl, gb_ridge.pkl, gb_eave.pkl (naučené na Brno GT).
Vystup: profil (SIMPLE_FLAT/STANDARD_GABLE/COMPLEX_HIP) + navrh geof.toml hodnot
  a duvod (predikovana vyska okapu/hrebene, typ strechy).
Pouziti: python ml/predict_params.py --patch ml/patches_brno/12400478532927488.npz
"""
import os
import pickle
import sys

import numpy as np

sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__))))
from train_raster import downsample8  # noqa: E402

LABELS = {0: "SIMPLE_FLAT", 1: "STANDARD_GABLE", 2: "COMPLEX_HIP"}
PROFILE_PARAMS = {
    "SIMPLE_FLAT": dict(plane_detect__epsilon=0.25, plane_detect__min_points=20,
                         plane_detect__k=15, normal_estimate__k=8,
                         line_detect__epsilon=0.5, optimisation_data_term=5.0,
                         lod13__step_height=3.0, max_arr_complexity=400),
    "STANDARD_GABLE": dict(plane_detect__epsilon=0.20, plane_detect__min_points=15,
                           plane_detect__k=15, normal_estimate__k=8,
                           line_detect__epsilon=0.4, optimisation_data_term=7.0,
                           lod13__step_height=3.0, max_arr_complexity=400),
    "COMPLEX_HIP": dict(plane_detect__epsilon=0.15, plane_detect__min_points=10,
                        plane_detect__k=10, normal_estimate__k=5,
                        line_detect__epsilon=0.3, optimisation_data_term=9.0,
                        lod13__step_height=2.5, max_arr_complexity=800),
}


def featurize(npz_path):
    d = np.load(npz_path)
    stats = np.asarray(d["stats"], dtype=np.float32).ravel()
    small = downsample8(np.asarray(d["ndsm"], dtype=np.float32)).ravel()
    frac = float(np.asarray(d["valid_mask"]).mean())
    return np.concatenate([stats, small, [frac]]).reshape(1, -1)


def main():
    import argparse
    ap = argparse.ArgumentParser()
    ap.add_argument("--patch", required=True)
    ap.add_argument("--models", default="ml")
    a = ap.parse_args()
    X = featurize(a.patch)
    d = np.load(a.patch)
    roof = pickle.load(open(os.path.join(a.models, "gb_roof.pkl"), "rb"))
    ridge = pickle.load(open(os.path.join(a.models, "gb_ridge.pkl"), "rb"))
    t = int(roof["model"].predict(X)[0])
    h_ridge = float(ridge["model"].predict(X)[0])
    # okap: deterministicky percentil z DSM (bez ML - model by se ucil identitu)
    h_eave = float(np.nanpercentile(
        np.where(np.asarray(d["valid_mask"]).astype(bool),
                 np.asarray(d["ndsm"]), np.nan), 10))
    profile = LABELS[t]
    params = dict(PROFILE_PARAMS[profile])
    # vyska hrebene zpresnuje step_height: nizke budovy mensi krok
    if h_ridge < 6:
        params["lod13__step_height"] = 2.5
    print(f"patch: {a.patch}")
    print(f"predikce: typ={t} ({LABELS[t]}) vyska_budovy={h_ridge:.1f} m okap_DSM={h_eave:.1f} m")
    print("(holdout: acc typu 0.47, MAE vysky 4.9 m, okap z DSM percentilu - brat s rezervou)")
    print(f"profil: {profile}")
    for k, v in params.items():
        print(f"  {k} = {v}")


if __name__ == "__main__":
    main()
