# -*- coding: utf-8 -*-
"""Priznaky poctu rovin strechy (RANSAC-lite, CPU, numpy).
Myselek: sedlova = 2 roviny delene 1 hřebenem (existuje smer rezu s malym zbytkem),
valbova = 4 roviny (zadny jednoduchy rez nevysvetli), plocha = 1 rovina.
Vystup per patch: rmse1 (1 rovina), rmse2 (nejlepsi 2-rovina ze 4 smeru),
ratio = rmse2/rmse1, darek = rmse1 (plocha mala).
"""
import numpy as np


def plane_rmse(xyz):
    """Nejmensi ctverce roviny z = ax+by+c; vrati RMSE. Prazdne -> nan."""
    if len(xyz) < 6:
        return float("nan")
    A = np.column_stack([xyz[:, 0], xyz[:, 1], np.ones(len(xyz))])
    coef, *_ = np.linalg.lstsq(A, xyz[:, 2], rcond=None)
    return float(np.sqrt(np.mean((A @ coef - xyz[:, 2]) ** 2)))


def roof_plane_features(xx, yy, zz):
    """xx, yy, zz: 1D pole vnitrnich pixelu (stejne delky)."""
    m = np.isfinite(zz)
    xx, yy, zz = xx[m], yy[m], zz[m]
    if len(zz) < 12:
        return dict(rmse1=np.nan, rmse2=np.nan, ratio=np.nan, n=int(len(zz)))
    xyz = np.column_stack([xx, yy, zz])
    rmse1 = plane_rmse(xyz)
    best = np.inf
    splits = [xx < np.median(xx), yy < np.median(yy),
              (xx - xx.mean()) < (yy - yy.mean()),
              (xx - xx.mean()) < -(yy - yy.mean())]
    for s in splits:
        if s.sum() < 6 or (~s).sum() < 6:
            continue
        r1 = plane_rmse(xyz[s])
        r2 = plane_rmse(xyz[~s])
        r = np.sqrt((r1 ** 2 * s.sum() + r2 ** 2 * (~s).sum()) / len(xyz))
        best = min(best, r)
    rmse2 = best if np.isfinite(best) else np.nan
    ratio = rmse2 / rmse1 if rmse1 and rmse1 > 1e-9 else np.nan
    return dict(rmse1=rmse1, rmse2=rmse2, ratio=ratio, n=int(len(zz)))
