"""Recolore une image aux couleurs de la charte : chaque plage de teinte -> une couleur cible,
en gardant la texture (luminosité relative). Les zones grises restent grises."""
import sys, numpy as np
from PIL import Image
def hex2(h): return np.array([int(h[i:i+2],16) for i in (1,3,5)],float)
def run(src, dst, rules, sat_min=0.22):
    im = np.asarray(Image.open(src).convert("RGB")).astype(float)
    hsv = np.asarray(Image.open(src).convert("RGB").convert("HSV")).astype(float)
    H = hsv[...,0]*360/255; S = hsv[...,1]/255; V = hsv[...,2]/255
    out = im.copy()
    for (h0,h1,target) in rules:
        m = (S>sat_min) & ((H>=h0)&(H<h1) if h0<h1 else ((H>=h0)|(H<h1)))
        if not m.any(): continue
        vref = np.median(V[m])
        t = hex2(target)
        k = np.clip(V[m]/vref, 0, 1.6)[:,None]
        # au-dessus de 1 on éclaircit vers le blanc, en dessous on assombrit
        col = np.where(k<=1, t*k, t + (255-t)*(k-1)/0.6)
        out[m] = np.clip(col,0,255)
        print(f"{h0}-{h1} -> {target}: {m.mean()*100:.1f}% des pixels")
    Image.fromarray(out.astype(np.uint8)).save(dst, quality=82, optimize=True, progressive=True)
if __name__ == "__main__":
    pass
