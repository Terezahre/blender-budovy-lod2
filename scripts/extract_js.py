# -*- coding: utf-8 -*-
import re
h = open("geoflow_dialog.hta", encoding="utf-8").read()
m = re.search(r'<script language="JScript">(.*?)</script>', h, re.S)
open(r"C:\Users\Tereza\AppData\Local\Temp\opencode\dlg.js", "w", encoding="utf-8").write(m.group(1))
print("script bytes:", len(m.group(1)))
