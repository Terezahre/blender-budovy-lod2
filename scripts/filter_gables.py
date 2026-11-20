# -*- coding: utf-8 -*-
"""Filtrace pravych sedlovych strech: 2+ SIKME roviny, rel<9 m, plocha<600 m2."""
import json
c = json.load(open("buildings/gable_candidates.json", encoding="utf-8"))
good = []
for r in c:
    s = sorted([n for k, n in r["kinds"] if k == "S"], reverse=True)
    if len(s) >= 2 and s[1] >= 25 and r["rel"] <= 9.0 and r["w"] * r["h"] <= 600:
        bal = s[1] / max(s[0], 1)
        good.append((bal, s[0] + s[1], r))
good.sort(key=lambda t: (t[0], t[1]), reverse=True)
print(f"{'tile':>8} {'cl':>5} {'n':>5} {'rozmer':>9} {'rel':>5}  S-roviny balance")
for bal, tot, r in good[:20]:
    print(f"{str(r['tile']):>8} {r['cl']:>5} {r['n']:>5} {r['w']:>4.0f}x{r['h']:<4.0f} {r['rel']:>5.1f}  {r['kinds']} bal={bal:.2f}")
print("TOTAL", len(good))
