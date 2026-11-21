# -*- coding: utf-8 -*-
"""Experiment 5: maly CNN na raw 64x64 patchi (torch CPU, lokalne).
Vstup: 2 kanaly (ndsm/30 clip, valid_mask) + tabularni vetev.
Varianty: S-RUIAN (stats + shape) vs BEZ-RUIAN (jen DSM: stats bez area + zadny shape).
Architektura: 3x conv(16-32-64) + maxpool -> 8x8x64 -> FC128 -> 3 tridy.
Trenink: 5-fold stratifikovany, 25 epoch, Adam, balanced class weights, batch 32.
Cas na i5: desitky minut (pozadi).
"""
import sys
import os
import numpy as np

sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__))))
from train_raster import load_all  # noqa: E402

import torch
import torch.nn as nn
from sklearn.model_selection import StratifiedKFold
from sklearn.metrics import confusion_matrix, accuracy_score

torch.manual_seed(42)
torch.set_num_threads(4)


class TinyCNN(nn.Module):
    def __init__(self, n_tab):
        super().__init__()
        self.conv = nn.Sequential(
            nn.Conv2d(2, 16, 3, padding=1), nn.ReLU(), nn.MaxPool2d(2),   # 32
            nn.Conv2d(16, 32, 3, padding=1), nn.ReLU(), nn.MaxPool2d(2),  # 16
            nn.Conv2d(32, 64, 3, padding=1), nn.ReLU(), nn.MaxPool2d(2),  # 8
        )
        self.fc = nn.Sequential(nn.Linear(64 * 8 * 8 + n_tab, 128), nn.ReLU(),
                                nn.Linear(128, 3))

    def forward(self, img, tab):
        h = self.conv(img).flatten(1)
        return self.fc(torch.cat([h, tab], dim=1))


def run_variant(Ximg, Xtab, y, vname, epochs=25, batch=32):
    Ximg = np.asarray(Ximg, dtype=np.float32)
    Xtab = np.asarray(Xtab, dtype=np.float32)
    y = np.asarray(y)
    skf = StratifiedKFold(n_splits=5, shuffle=True, random_state=42)
    pred = np.zeros_like(y)
    cls_w = torch.tensor([len(y) / max((y == c).sum(), 1) for c in range(3)],
                         dtype=torch.float32)
    for tr, te in skf.split(Ximg, y):
        net = TinyCNN(Xtab.shape[1])
        opt = torch.optim.Adam(net.parameters(), lr=3e-3)
        lossf = nn.CrossEntropyLoss(weight=cls_w)
        t_img = torch.tensor(Ximg[tr]).float()
        t_tab = torch.tensor(Xtab[tr]).float()
        t_y = torch.tensor(y[tr]).long()
        net.train()
        for _ in range(epochs):
            for i in range(0, len(tr), batch):
                s = slice(i, i + batch)
                opt.zero_grad()
                lossf(net(t_img[s], t_tab[s]), t_y[s]).backward()
                opt.step()
        net.eval()
        with torch.no_grad():
            p = net(torch.tensor(Ximg[te]).float(),
                    torch.tensor(Xtab[te]).float()).argmax(1).numpy()
        pred[te] = p
    cm = confusion_matrix(y, pred, labels=[0, 1, 2])
    rec = [cm[i, i] / max(cm[i].sum(), 1) for i in range(3)]
    print(f"{vname}: acc={accuracy_score(y, pred):.3f} "
          f"recall f/g/h={rec[0]:.2f}/{rec[1]:.2f}/{rec[2]:.2f}", flush=True)
    print(f"  CM:\n{cm}", flush=True)
    return pred


def main():
    import geopandas as gpd
    import glob
    rows = [r for r in load_all("ml/patches_brno", "ml/gt_brno.json") if r["src"] == "GT"]
    files = {os.path.splitext(os.path.basename(f))[0]: f
             for f in glob.glob("ml/patches_brno/*.npz")}
    y = np.array([r["y"] for r in rows])
    imgs, tabs = [], []
    for r in rows:
        d = np.load(files[r["id"]])
        ndsm = np.nan_to_num(d["ndsm"], nan=0.0) / 30.0
        imgs.append(np.stack([ndsm, d["valid_mask"]]))
        tabs.append(r["x_full"])
    Ximg = np.stack(imgs).astype(np.float32)
    Xtab0 = np.stack(tabs).astype(np.float32)
    fp = gpd.read_file(os.path.join("ml", "data_brno", "footprints.geojson"))
    fp = fp.set_index(fp["fid_zbg"].astype(str))
    from exp4_shape_mlp import shape_row
    S = np.nan_to_num(np.array([shape_row(fp.loc[r["id"]].geometry) for r in rows]),
                      nan=0.0, posinf=0.0, neginf=0.0).astype(np.float32)
    NO_RUIAN = [0, 1, 2, 3, 5]
    print(f"N={len(y)}", flush=True)
    run_variant(Ximg, np.concatenate([Xtab0, S], axis=1), y, "S-RUIAN(CNN+tvar)")
    run_variant(Ximg, np.concatenate([Xtab0[:, NO_RUIAN], Xtab0[:, 6:]], axis=1),
                y, "BEZ-RUIAN(CNN jen DSM)")


if __name__ == "__main__":
    main()
