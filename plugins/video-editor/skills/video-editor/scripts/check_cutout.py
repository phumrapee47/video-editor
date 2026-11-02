"""Flag cut-outs whose subject touches the image border, which usually means a crop sliced through the subject.

Usage: python -I check_cutout.py <cut1.png> [<cut2.png> ...]
A subject that fills a border row or column was most likely cut by cropping the source photo; pick a wider crop,
mask only the distracting element, or choose another photo. (Lesson from the Pompeii clip: a cast was cut in half.)
"""
import sys
import numpy as np
from PIL import Image

for path in sys.argv[1:]:
    a = np.array(Image.open(path).convert("RGBA").split()[3]) > 40
    h, w = a.shape
    edges = {"top": a[0].mean(), "bottom": a[-1].mean(), "left": a[:, 0].mean(), "right": a[:, -1].mean()}
    cut = {k: round(float(v) * 100) for k, v in edges.items() if v > 0.05}
    print(("CUT  " if cut else "ok   ") + path + ("  subject touches: " + ", ".join(f"{k} {v}%" for k, v in cut.items()) if cut else ""))
