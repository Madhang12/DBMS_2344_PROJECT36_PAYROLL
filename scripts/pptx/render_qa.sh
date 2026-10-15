#!/bin/bash
# usage: render_qa.sh <pptx> <outdir>   -> grid images of every slide (6 per grid) for visual QA
set -e
PPTX="$1"; OUT="$2"; mkdir -p "$OUT"; cd "$OUT"; rm -f ./*
cp "$PPTX" deck.pptx
python3 /mnt/skills/public/pptx/scripts/office/soffice.py --headless --convert-to pdf deck.pptx >/dev/null 2>&1
pdftoppm -jpeg -r 80 deck.pdf s
python3 - <<'PY'
from PIL import Image
import glob
fs=sorted(glob.glob('s-*.jpg'))
for g in range(0,len(fs),6):
    sheet=Image.new('RGB',(1600,1350),'white')
    for i,f in enumerate(fs[g:g+6]):
        sheet.paste(Image.open(f).resize((800,450)),((i%2)*800,(i//2)*450))
    sheet.save(f'grid{g//6+1}.jpg',quality=85)
print(len(fs),'slides')
PY
