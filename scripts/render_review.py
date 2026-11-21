from pathlib import Path
import fitz
from PIL import Image,ImageOps,ImageDraw
R=Path(__file__).resolve().parents[1];dest=R/'review';dest.mkdir(exist_ok=True)
d=fitz.open(R/'source/paper.pdf');print('PAGES',len(d))
for i,p in enumerate(d):
    pix=p.get_pixmap(matrix=fitz.Matrix(1.35,1.35));pix.save(dest/f'page_{i+1:02}.png')
    text=p.get_text();print(i+1,len(text),text[0:105].replace('\n',' | '))
    for w in p.get_text('words'):
        assert 0<=w[0]<=p.rect.width and w[2]<=p.rect.width+1 and w[1]>=0 and w[3]<=p.rect.height+1,(i,w)
for start in range(0,len(d),9):
    sheet=Image.new('RGB',(900,1320),'#cccccc');draw=ImageDraw.Draw(sheet)
    for n in range(start,min(start+9,len(d))):
        im=Image.open(dest/f'page_{n+1:02}.png').convert('RGB');im.thumbnail((294,413));x=(n-start)%3*300;y=(n-start)//3*440;sheet.paste(im,(x,y+22));draw.text((x+5,y+3),str(n+1),fill='black')
    sheet.save(dest/f'contact_{start+1:02}.png')
